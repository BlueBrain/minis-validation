"""Command line interface."""

import logging
from pathlib import Path
from typing import Optional, Tuple

import click

from minis_validation import analysis, simulation
from minis_validation.util import parse_slurm_args


@click.group()
@click.option(
    "-v", "--verbose", count=True, default=0, help="-v for WARNING, -vv for INFO, -vvv for DEBUG"
)
def cli(verbose):
    """CLI entry point."""
    level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 3)]
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@cli.command(
    short_help="Carry simulations with various minis frequencies, for details see"
    "docstring of ``minis_validation.simulation.run`` function."
)
@click.argument("sonata_simulation_config", type=click.Path(exists=True, dir_okay=False))
@click.argument("frequencies", type=click.Path(exists=True, dir_okay=False))
@click.argument("jobs_configs_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("output", type=click.Path(exists=False, file_okay=False))
@click.option(
    "--log-dir",
    type=str,
    required=False,
    default="logs",
    show_default=True,
    help="Name of a directory to save logs to; on a shared file system",
)
@click.option(
    "--timeout-s",
    type=int,
    required=False,
    default=3600,
    show_default=True,
    help="Time to live for simulation workers in seconds",
)
@click.option(
    "--batch-size",
    type=int,
    required=False,
    default=100,
    show_default=True,
    help="Batch size to be processed in each job.",
)
@click.option("-n", "--num-cells", type=int, help="Number of cells to simulate")
@click.option(
    "-t",
    "--target",
    type=str,
    required=False,
    default=None,
    help='Override "$target" of simulations',
)
@click.option(
    "-s", "--seed", type=int, default=None, required=False, help="Pseudo-random generator seed"
)
@click.option(
    "-d",
    "--duration",
    type=float,
    default=None,
    required=False,
    help="Override duration of simulations",
)
@click.option(
    "--forward-skip",
    type=float,
    default=5000,
    required=False,
    show_default=True,
    help='Override "ForwardSkip" value of simulations',
)
@click.option(
    "--slurm",
    multiple=True,
    type=(str, str),
    required=False,
    help="""
It is possible to add many SLURM configuration values.
See submitit documentation (https://github.com/facebookincubator/submitit)
for full list of values and README for hints.
DO NOT include the `slurm` prefix.
Mandatory: `--slurm account` and `--slurm partition`
    """,
)
def simulate(
    sonata_simulation_config: str,
    frequencies: str,
    jobs_configs_dir: str,
    output: str,
    log_dir: str,
    timeout_s: int,
    batch_size: int,
    num_cells: int,
    slurm: Tuple[Tuple[str, str], ...],
    target: Optional[str] = None,
    seed: Optional[int] = None,
    duration: Optional[float] = None,
    forward_skip: Optional[float] = None,
):
    # pylint: disable=too-many-arguments, too-many-locals
    """CLI for ``minis_validation.simulation.run`` function.

    SONATA_SIMULATION_CONFIG is a path to a Sonata simulation file

    FREQUENCIES is a path to a CSV file with chosen mini frequencies to simulate

    JOBS_CONFIGS_DIR is a path to a folder with YAML files describing experiment conditions

    OUTPUT is a path to a folder where to store results of simulations
    """
    assert not Path(output).exists(), f"Can't output to existing folder: {output}"
    simulation.run(
        sonata_simulation_config_file=Path(sonata_simulation_config),
        frequencies_file=Path(frequencies),
        jobs_configs_dir=Path(jobs_configs_dir),
        output=Path(output),
        log_dir=log_dir,
        num_cells=num_cells,
        target=target,
        seed=seed,
        duration=duration,
        forward_skip=forward_skip,
        slurm_args=parse_slurm_args(slurm),
        timeout_s=timeout_s,
        batch_size=batch_size,
    )


@cli.command(
    short_help="Analyze single job results, for details see docstring "
    "of ``minis_validation.analysis.analyze_job`` function."
)
@click.argument("job_config_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("job_traces_dir", type=click.Path(exists=True, file_okay=False))
def analyze_job(job_config_file: str, job_traces_dir: str):
    """CLI for ``minis_validation.analysis.analyze_job`` function.

    JOB_CONFIG_FILE is a path to a job YAML config file

    JOB_TRACES_DIR is a path to a folder where stored simulations of a single job config
    """
    analysis.analyze_job(Path(job_config_file), Path(job_traces_dir))


@cli.command(
    short_help="Analyze all jobs results, for details see docstring "
    "of ``minis_validation.analysis.analyze_jobs`` function."
)
@click.argument("jobs_configs_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("jobs_traces_dir", type=click.Path(exists=True, file_okay=False))
def analyze_jobs(jobs_configs_dir: str, jobs_traces_dir: str):
    """CLI for ``minis_validation.analysis.analyze_jobs`` function.

    JOBS_CONFIGS_DIR is a path to a folder with YAML files describing experiment conditions

    JOBS_TRACES_DIR is a path to a folder where stored results of all jobs simulations
    """
    job_results = analysis.analyze_jobs(Path(jobs_configs_dir), Path(jobs_traces_dir))
    print(job_results)
