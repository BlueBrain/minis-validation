"""Command line interface."""
from pathlib import Path
import logging
import click
from minis_validation import simulation, analysis


@click.group()
@click.option('-v', '--verbose', count=True, default=0,
              help='-v for WARNING, -vv for INFO, -vvv for DEBUG')
def cli(verbose):
    """CLI entry point."""
    level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 3)]
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)s %(name)s: %(message)s')


def _format_to_cli(doc):
    return doc.replace(u'\n', u'\n\n')


@cli.command(short_help='Carry simulations with various minis frequencies',
             help=_format_to_cli(simulation.run.__doc__))
@click.argument('blue_config', type=click.Path(exists=True, dir_okay=False))
@click.argument('frequencies', type=click.Path(exists=True, dir_okay=False))
@click.argument('jobs_configs_dir', type=click.Path(exists=True, file_okay=False))
@click.argument('output', type=click.Path(exists=False, file_okay=False))
@click.option('-n', '--num-cells', type=int)
@click.option('-T', '--target-file',
              type=click.Path(exists=True, dir_okay=False), default=None)
@click.option('-t', '--target', type=str, required=False, default=None)
@click.option('-s', '--seed', type=int, default=None, required=False)
@click.option('-g', '--gids', type=str, default=None, required=False,
              help='List of GIDs separated by comma to manually set required cells to simulate.'
                   'Multiple gids: --gids=345,543. Single gid: --gids=345.')
@click.option('-d', '--duration', type=float, default=None, required=False)
@click.option('--forward-skip', type=float, default=5000, required=False)
def simulate(blue_config: str,
             frequencies: str,
             jobs_configs_dir: str,
             output: str,
             num_cells: int,
             target_file: str = None,
             target: str = None,
             seed: int = None,
             gids: str = None,
             duration: float = None,
             forward_skip: float = None):
    # pylint: disable=too-many-arguments
    """CLI for ``simulation.run`` function."""
    simulation.run(Path(blue_config),
                   Path(frequencies),
                   Path(jobs_configs_dir),
                   Path(output),
                   num_cells,
                   None if target_file is None else Path(target_file),
                   target,
                   seed,
                   gids if gids is None else list(map(int, gids.split(','))),
                   duration,
                   forward_skip)


@cli.command(short_help='Analyze single job results',
             help=_format_to_cli(analysis.analyze_job.__doc__))
@click.argument('job_config_file', type=click.Path(exists=True, dir_okay=False))
@click.argument('job_traces_dir', type=click.Path(exists=True, file_okay=False))
def analyze_job(job_config_file: str, job_traces_dir: str):
    """CLI for ``analysis.analyze_job`` function."""
    analysis.analyze_job(Path(job_config_file), Path(job_traces_dir))


@cli.command(short_help='Analyze all jobs results',
             help=_format_to_cli(analysis.analyze_jobs.__doc__))
@click.argument('jobs_configs_dir', type=click.Path(exists=True, file_okay=False))
@click.argument('jobs_traces_dir', type=click.Path(exists=True, file_okay=False))
def analyze_jobs(jobs_configs_dir: str, jobs_traces_dir: str):
    """CLI for ``analysis.analyze_jobs`` function."""
    job_results = analysis.analyze_jobs(Path(jobs_configs_dir), Path(jobs_traces_dir))
    print(job_results)
