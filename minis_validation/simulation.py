"""Simulations of a cell with spontaneous minis."""
import itertools
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from multiprocessing import Process
import time

from dask import bag
from dask.distributed import Client
from dask_mpi import initialize
import numpy as np
import pandas as pd
import h5py
import yaml
from bluepy.v2 import Circuit
from bluepy_configfile.configfile import BlueConfig

L = logging.getLogger(__name__)


def _get_config_output(output: Path, config_file: Path) -> Path:
    """Returns path to the output of job config file within ``output``."""
    return output / config_file.stem.split('config_')[1]


def _get_config_minis_type(config_file: Path) -> str:
    """Extracts minis type from job config filename."""
    return config_file.stem.split('_')[-1]


def _get_gids(cells: Dict,
              blue_config_file: Path,
              num_cells: int,
              target_file: Path = None,
              gids: List[int] = None) -> List[int]:
    """Selects GIDs to simulate.

    Args:
        cells: cells specification from job config for Bluepy's ``circuit.cells.ids``
        blue_config_file: BlueConfig file to get GIDs from
        num_cells: Number of cells to simulate
        target_file: user specified target file for BlueConfig
        gids: List of GIDs that override simulations cells

    Returns:
        List: selected GIDs
    """
    if gids is None:
        with blue_config_file.open() as f:
            blue_config = BlueConfig(f)
        if target_file is not None:
            blue_config.Run.update({'TargetFile': str(target_file.resolve())})
        circuit = Circuit(blue_config)
        gids = circuit.cells.ids(cells)
    if len(gids) > num_cells:
        return np.random.choice(gids, size=num_cells, replace=False)
    return gids


def _write_traces(frequency, output_dir: Path):
    """Writes ``traces`` from ``run`` to their corresponding HDF5 files. One file per trace."""
    trace_files = list(output_dir.glob(f'*_{frequency:.3f}.npz'))
    L.info('Writing %d traces of %s and frequency %f', len(trace_files), output_dir, frequency)
    try:
        with h5py.File(output_dir / f'traces_freq{frequency:.3f}.h5', 'w') as h5f:
            for trace_file in trace_files:
                gid = int(trace_file.stem.split('_')[0])
                data = np.load(str(trace_file))
                group = h5f.create_group(f'traces/a{gid}')
                group.attrs['gid'] = gid
                group['trace'] = data['trace']
                group['events'] = data['events']
        # remove files in a separate step after all of them have been successfully processed
        for trace_file in trace_files:
            trace_file.unlink()
    except Exception:  # pylint: disable=broad-except
        L.exception('Exception at writing traces of %s and frequency %f', output_dir, frequency)


def _run_simulation(gid_frequency: Tuple,
                    output_dir: Path,
                    blue_config_file: Path,
                    minis_type: str,
                    t_stop: float,
                    record_dt: float,
                    dt: float = 0.025,
                    hold_V: float = None,
                    enable_ttx: bool = False,
                    seed: int = None,
                    calcium: float = None,
                    forward_skip: float = None):
    # pylint: disable=too-many-arguments, disable=too-many-locals, import-outside-toplevel
    """Simulates a single neuron by its GID with given function arguments.

    All arguments here are parameters of the simulation

    Args:
        gid_frequency: GID and minis frequency. They are passed as Tuple because ``dask`` can't
            pass multiple iterable args.
        output_dir: folder where to save simulation results
        blue_config_file: simulation BlueConfig
        minis_type: synapse type of minis. Either "Inh" or "Exc"
        t_stop: time of simulation
        record_dt: recording time interval
        dt: simulation time interval
        hold_V: voltage level of the voltage clamp in mV
        enable_ttx: use TTX in simulation
        seed: simulation base seed
        calcium: simulation extracellular calcium
        forward_skip: first simulation time to skip
    """
    import bglibpy
    if L.getEffectiveLevel() < logging.INFO:
        bglibpy.set_verbose(50)

    gid, frequency = gid_frequency
    L.info('Running a gid %i, minis type %s and frequency %.3f', gid, minis_type, frequency)

    ssim = bglibpy.SSim(
        str(blue_config_file), record_dt=record_dt, base_seed=seed, rng_mode='Random123')
    ssim.extracellular_calcium = calcium  # override calcium

    ssim.bc.add_section('Connection',
                        'SpontMinis_Inh',
                        f'Source Inhibitory\n'
                        f'Destination Mosaic\n'
                        f'SpontMinis {frequency if minis_type == "Inh" else 0.0}\n'
                        f'Weight 1.0\n')
    ssim.bc.add_section('Connection',
                        'SpontMinis_Exc',
                        f'Source Excitatory\n'
                        f'Destination Mosaic\n'
                        f'SpontMinis {frequency if minis_type == "Exc" else 0.0}\n'
                        f'Weight 1.0\n')
    ssim.connection_entries = ssim.bc.typed_sections('Connection')

    ssim.instantiate_gids([gid], add_synapses=True, add_minis=True)
    cell = ssim.cells[gid]
    if enable_ttx:
        cell.enable_ttx()
    # enable voltage clamp if requested
    if hold_V is not None:
        cell.add_voltage_clamp(stop_time=t_stop, level=hold_V, rs=0.0001,
                               current_record_name='v_clamp')

    # store events for minis
    mini_nc_vectors = {}
    for syn_id, netcon in cell.syn_mini_netcons.items():
        mini_nc_vectors[syn_id] = bglibpy.neuron.h.Vector()
        netcon.record(mini_nc_vectors[syn_id])
    ssim.run(t_stop=t_stop, dt=dt, show_progress=False, forward_skip_value=forward_skip)

    # get time and soma voltage
    cell_time = cell.get_time()
    cell_voltage = cell.get_soma_voltage()

    if hold_V is not None:
        cell_current = cell.get_recording('v_clamp')
        assert len(cell_current) == len(cell_time), 'Unexpected I(t) length'
    else:  # get zeros
        cell_current = np.zeros(len(cell_time))

    # get time-sorted minis events
    events = np.array(sorted(((t, syn_id[1])
                              for syn_id, nc_vectors in mini_nc_vectors.items()
                              for t in nc_vectors)))
    if events.size == 0:
        events = np.empty((0, 2))
    L.info('Saving results for a gid %i, minis type %s and frequency %.3f',
           gid, minis_type, frequency)
    trace = np.vstack((cell_time, cell_voltage, cell_current)).T
    np.savez_compressed(output_dir / f'{gid}_{frequency:.3f}.npz', trace=trace, events=events)


def _run_simulation_fork(*args, **kwargs):
    p = Process(target=_run_simulation, args=args, kwargs=kwargs)
    p.start()
    p.join()


def run(blue_config_file: Path,
        frequencies_file: Path,
        jobs_configs_dir: Path,
        output: Path,
        num_cells: int = 1000,
        target_file: Path = None,
        target: str = None,
        seed: int = None,
        gids: List[int] = None,
        duration: float = None,
        forward_skip: float = None):
    # pylint: disable=too-many-arguments,too-many-locals
    """Run minis simulations and save results to ``output`` as HDF5.

    Args:
        blue_config_file: Path to a BlueConfig file
        frequencies_file: Path to a CSV file with chosen mini frequencies to simulate. Its only
            column must have the name 'MINIS_FREQ'.
        jobs_configs_dir: Path to a folder with YAML files describing experiment conditions.
            Read more details about it in Documentation of this project. The compiled Documentation
            is at https://bbpteam.epfl.ch/documentation/m.html#minis-validation.
        output: Path to a folder where to store results of simulations
        num_cells: Number of cells to simulate
        target_file: Path to a target file to override 'TargetFile' of ``blue_config_file``
        target: Override '$target' of simulations
        seed: Pseudo-random generator seed
        gids: List of GIDs that override simulations cells
        duration: Override duration of simulations
        forward_skip: Override ForwardSkip value of simulations
    """
    if seed is None:
        seed = 0
    np.random.seed(seed)

    # dask.distributed logging requires a manual override
    logging.getLogger('distributed').setLevel(L.getEffectiveLevel())
    initialize()
    client = Client()

    frequencies = pd.read_csv(frequencies_file, sep='\t')['MINIS_FREQ'].tolist()
    config_files = list(jobs_configs_dir.glob('config_*.yaml'))
    assert len(config_files) > 0, f'No job configs at {jobs_configs_dir}. Config files must' \
                                  f' follow the pattern: "config_<CELL_TYPE>_<SYN_MINIS>"'

    b = bag.from_sequence([])
    for config_file in config_files:
        with config_file.open() as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
        if duration is not None:
            config['protocol']['t_stop'] = duration
        if forward_skip is not None:
            config['protocol']['forward_skip'] = forward_skip
        if target is not None:
            config['cells']['$target'] = target

        config_gids = _get_gids(config['cells'], blue_config_file, num_cells, target_file, gids)
        config_output = _get_config_output(output, config_file)
        config_output.mkdir(exist_ok=True, parents=True)

        b = bag.concat([b, bag.from_sequence(itertools.product(config_gids, frequencies))
                       .map(_run_simulation_fork,
                            output_dir=config_output,
                            blue_config_file=blue_config_file,
                            minis_type=_get_config_minis_type(config_file),
                            seed=seed,
                            **config['protocol'])])
    b.compute()

    L.info('Simulations have finished. Saving HDF5 reports.')

    b = bag.from_sequence([])
    for config_file in config_files:
        config_output = _get_config_output(output, config_file)
        b = bag.concat([b, bag.from_sequence(frequencies).map(_write_traces,
                                                              output_dir=config_output)])
    b.compute()
    L.info('Minis-validation is finished. HDF5 reports have been saved.')
    time.sleep(10)
    client.retire_workers()
