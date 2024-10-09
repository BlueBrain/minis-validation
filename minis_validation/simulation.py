"""Simulations of a cell with spontaneous minis."""

import itertools
import logging
from datetime import timedelta
from multiprocessing import Process
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import h5py
import numpy as np
import pandas as pd
import submitit
import yaml
from bluecellulab.circuit.config import SonataSimulationConfig
from bluecellulab.circuit.config.sections import ConnectionOverrides
from bluepysnap import Circuit, Simulation

L = logging.getLogger(__name__)


def _get_config_output(output: Path, config_file: Path) -> Path:
    """Returns path to the output of job config file within ``output``."""
    return output / config_file.stem.split("config_")[1]


def _get_config_minis_type(config_file: Path) -> str:
    """Extracts minis type from job config filename."""
    return config_file.stem.split("_")[-1]


def _parse_trace_filename(filename: str) -> Tuple[str, int]:
    """Parse population name and node id from trace file name."""
    population, node_id, _ = filename.rsplit("_", 2)
    return population, int(node_id)


def _get_gids(cells: Dict, circuit: Circuit, num_cells: int):
    """Selects GIDs to simulate.

    Args:
        cells: cells specification from job config for bluepysnap's ``circuit.nodes.ids``
        sonata_config_file: Sonata config file
        num_cells: Number of cells to simulate
        gids: List of GIDs that override simulations cells

    Returns:
        List[int]: selected GIDs
    """
    gids = circuit.nodes.ids(cells)
    if len(gids) > num_cells:
        gids.sample(num_cells, inplace=True)
    return gids


def _write_traces(frequency, output_dir: Path, logging_level: int = logging.INFO):
    """Writes ``traces`` from ``run`` to their corresponding HDF5 files. One file per trace."""
    logging.basicConfig(level=logging_level, format="%(asctime)s - %(levelname)s - %(message)s")
    job_logger = logging.getLogger(__name__)

    trace_files = list(output_dir.glob(f"*_{frequency:.3f}.npz"))
    job_logger.info(
        "Writing %d traces of %s and frequency %f",
        len(trace_files),
        output_dir,
        frequency,
    )
    try:
        with h5py.File(output_dir / f"traces_freq{frequency:.3f}.h5", "w") as h5f:
            for trace_file in trace_files:
                population, node_id = _parse_trace_filename(trace_file.stem)

                data = np.load(str(trace_file))
                group = h5f.create_group(f"traces/{population}/a{node_id}")
                group.attrs.create("node_id", node_id)
                group["trace"] = data["trace"]
                group["events"] = data["events"]
        # remove files in a separate step after all of them have been successfully processed
        for trace_file in trace_files:
            trace_file.unlink()
    except Exception:  # pylint: disable=broad-except
        L.exception("Exception at writing traces of %s and frequency %f", output_dir, frequency)


def _run_simulation(
    gid_frequency: Tuple,
    output_dir: Path,
    sonata_simulation_config_file: Path,
    minis_type: str,
    t_stop: float,
    record_dt: float,
    dt: float = 0.025,
    hold_V: Optional[float] = None,
    enable_ttx: bool = False,
    seed: Optional[int] = None,
    forward_skip: Optional[float] = None,
    logging_level: int = logging.INFO,
):
    # pylint: disable=too-many-arguments, disable=too-many-locals, import-outside-toplevel
    """Simulates a single neuron by its GID with given function arguments.

    All arguments here are parameters of the simulation

    Args:
        gid_frequency: GID and minis frequency. They are passed as Tuple because ``dask`` can't
            pass multiple iterable args.
        output_dir: folder where to save simulation results
        sonata_simulation_config_file: Sonata simulation config file
        minis_type: synapse type of minis. Either "Inh" or "Exc"
        t_stop: time of simulation
        record_dt: recording time interval
        dt: simulation time interval
        hold_V: voltage level of the voltage clamp in mV
        enable_ttx: use TTX in simulation
        seed: simulation base seed
        forward_skip: first simulation time to skip
        logging_level: logging level to use by the workers
    """
    logging.basicConfig(level=logging_level, format="%(asctime)s - %(levelname)s - %(message)s")
    job_logger = logging.getLogger(__name__)

    import bluecellulab

    if logging_level < logging.INFO:
        bluecellulab.set_verbose(50)

    gid, frequency = gid_frequency
    job_logger.info(
        "Running a gid %s, minis type %s and frequency %.3f", gid, minis_type, frequency
    )

    sonata_simulation_config = SonataSimulationConfig(str(sonata_simulation_config_file))
    sonata_simulation_config.add_connection_override(
        ConnectionOverrides(
            source="Inhibitory",
            target="Mosaic",
            weight=1.0,
            spont_minis=float(frequency) if minis_type == "Inh" else 0.0,
        )
    )
    sonata_simulation_config.add_connection_override(
        ConnectionOverrides(
            source="Excitatory",
            target="Mosaic",
            weight=1.0,
            spont_minis=float(frequency) if minis_type == "Exc" else 0.0,
        )
    )

    ssim = bluecellulab.CircuitSimulation(
        sonata_simulation_config,
        record_dt=record_dt,
        base_seed=seed,
        rng_mode="Random123",
    )

    ssim.instantiate_gids([gid], add_synapses=True, add_minis=True, add_projections=True)
    cell = ssim.cells[gid]
    if enable_ttx:
        cell.enable_ttx()
    # enable voltage clamp if requested
    if hold_V is not None:
        cell.add_voltage_clamp(
            stop_time=t_stop, level=hold_V, rs=0.0001, current_record_name="v_clamp"
        )

    # store events for minis
    mini_nc_vectors = {}
    for syn_id, netcon in cell.syn_mini_netcons.items():
        mini_nc_vectors[syn_id] = bluecellulab.neuron.h.Vector()
        netcon.record(mini_nc_vectors[syn_id])
    ssim.run(t_stop=t_stop, dt=dt, show_progress=False, forward_skip_value=forward_skip)

    # get time and soma voltage
    cell_time = cell.get_time()
    cell_voltage = cell.get_soma_voltage()

    if hold_V is not None:
        cell_current = cell.get_recording("v_clamp")
        assert len(cell_current) == len(cell_time), "Unexpected I(t) length"
    else:  # get zeros
        cell_current = np.zeros(len(cell_time))

    # get time-sorted minis events
    events = np.array(
        sorted(
            ((t, syn_id[1]) for syn_id, nc_vectors in mini_nc_vectors.items() for t in nc_vectors)
        )
    )
    if events.size == 0:
        events = np.empty((0, 2))
    job_logger.info(
        "Saving results for a gid %s, minis type %s and frequency %.3f",
        gid,
        minis_type,
        frequency,
    )
    trace = np.vstack((cell_time, cell_voltage, cell_current)).T
    np.savez_compressed(
        output_dir / f"{gid.population}_{gid.id}_{frequency:.3f}.npz",
        trace=trace,
        events=events,
    )


def _run_simulation_batch(gids_frequencies, *args, **kwargs):
    for gid_frequency in gids_frequencies:
        _run_simulation(gid_frequency, *args, **kwargs)


def _run_simulation_fork(*args, **kwargs):
    p = Process(target=_run_simulation_batch, args=args, kwargs=kwargs)
    p.start()
    p.join()


def run(
    sonata_simulation_config_file: Path,
    frequencies_file: Path,
    jobs_configs_dir: Path,
    output: Path,
    log_dir: str,
    slurm_args: Dict[str, Union[str, int]],
    num_cells: int = 1000,
    target: Optional[str] = None,
    seed: Optional[int] = None,
    duration: Optional[float] = None,
    forward_skip: Optional[float] = None,
    timeout_s: int = 3600,
    batch_size: int = 100,
):
    # pylint: disable=too-many-arguments,too-many-locals
    """Run minis simulations and save results to ``output`` as HDF5.

    Args:
        sonata_simulation_config_file: Path to a Sonata simulation file
        frequencies_file: Path to a CSV file with chosen mini frequencies to simulate. Its only
            column must have the name 'MINIS_FREQ'.
        jobs_configs_dir: Path to a folder with YAML files describing experiment conditions.
            Read more details about it in Documentation of this project. The compiled Documentation
            is at https://bbpteam.epfl.ch/documentation/m.html#minis-validation.
        output: Path to a folder where to store results of simulations
        log_dir: Path to a folder where to store logs
        slurm_args: SLURM arguments
        num_cells: Number of cells to simulate
        target: Override '$target' of simulations
        seed: Pseudo-random generator seed
        duration: Override duration of simulations
        forward_skip: Override ForwardSkip value of simulations
        timeout_s: Time to live for simulation workers in seconds
        batch_size: Batch size to be processed in each job.
    """
    if seed is None:
        seed = 0
    np.random.seed(seed)
    executor: submitit.Executor
    if slurm_args:
        L.info("Using SLURM executor.")
        if "slurm_time" in slurm_args:
            raise KeyError(
                "Use `timeout_s` argument instead of `slurm_time`. "
                "It will be synchronized automatically."
            )
        slurm_time = str(timedelta(seconds=timeout_s))
        executor = submitit.AutoExecutor(
            folder=log_dir + "/%j",
        )
        executor.update_parameters(
            **slurm_args,
            slurm_time=slurm_time,
        )
    else:
        L.info("Using local executor.")
        executor = submitit.LocalExecutor(
            folder=log_dir + "/%j",
        )

    executor.update_parameters(
        timeout_min=timeout_s // 60,
    )

    frequencies = pd.read_csv(frequencies_file, sep="\t")["MINIS_FREQ"].tolist()
    config_files = list(jobs_configs_dir.glob("config_*.yaml"))
    assert len(config_files) > 0, (
        f"No job configs at {jobs_configs_dir}. Config files must"
        f' follow the pattern: "config_<CELL_TYPE>_<SYN_MINIS>"'
    )

    sonata_simulation = Simulation(sonata_simulation_config_file)
    circuit = sonata_simulation.circuit

    jobs = []
    # executor.batch uses Slurm job array to submit all jobs at once
    with executor.batch():
        for config_file in config_files:
            with config_file.open() as f:
                config = yaml.load(f, Loader=yaml.SafeLoader)
            if duration is not None:
                config["protocol"]["t_stop"] = duration
            if forward_skip is not None:
                config["protocol"]["forward_skip"] = forward_skip
            if target is not None:
                config["cells"]["$target"] = target

            config_gids = _get_gids(
                cells=config["cells"],
                circuit=circuit,
                num_cells=num_cells,
            )
            config_output = _get_config_output(output, config_file)
            config_output.mkdir(exist_ok=True, parents=True)

            gids_frequencies = itertools.product(config_gids, frequencies)
            while batch := tuple(itertools.islice(gids_frequencies, batch_size)):
                job = executor.submit(
                    _run_simulation_fork,
                    gids_frequencies=list(batch),
                    output_dir=config_output,
                    sonata_simulation_config_file=sonata_simulation_config_file,
                    minis_type=_get_config_minis_type(config_file),
                    seed=seed,
                    **config["protocol"],
                )
                jobs.append(job)

    # wait for jobs to finish
    _ = [job.result() for job in jobs]
    L.info("Simulations have finished. Saving HDF5 reports.")

    jobs = []
    with executor.batch():
        for config_file in config_files:
            config_output = _get_config_output(output, config_file)
            for frequency in frequencies:
                job = executor.submit(
                    _write_traces,
                    frequency=frequency,
                    output_dir=config_output,
                )
                jobs.append(job)

    # wait for jobs to finish
    _ = [job.result() for job in jobs]
    L.info("Minis-validation is finished. HDF5 reports have been saved.")
