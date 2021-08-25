from pathlib import Path
import pandas as pd
import pytest
import shutil

from minis_validation import simulation, analysis

TEST_DATA_DIR = Path(__file__).parent / 'data'


@pytest.fixture(scope='session')
def simulation_output():
    output = TEST_DATA_DIR / 'output'
    shutil.rmtree(output, ignore_errors=True)
    simulation.run(TEST_DATA_DIR / 'BlueConfig',
                   TEST_DATA_DIR / 'frequencies.csv',
                   TEST_DATA_DIR / 'job-configs',
                   output,
                   mpi=False,
                   num_cells=2,
                   target_file=TEST_DATA_DIR / 'user.target')
    analysis.analyze_jobs(TEST_DATA_DIR / 'job-configs', output)
    return output


def _assert_job_output(job_output_dir):
    assert job_output_dir.is_dir()
    frequencies = pd.read_csv(TEST_DATA_DIR / 'frequencies.csv', sep='\t')['MINIS_FREQ']
    expected_files = {f'traces_freq{frequency:.3f}.h5' for frequency in frequencies}
    assert expected_files == {file.name for file in job_output_dir.glob('*.h5')}
    assert (job_output_dir / 'analysis').is_dir()
    assert (job_output_dir / 'analysis' / 'frequencies.png').is_file()


def test_simulate_analyze(simulation_output):
    assert (simulation_output / 'job_results.csv').is_file()
    _assert_job_output(simulation_output / 'PC_Exc')
    _assert_job_output(simulation_output / 'PC_Inh')
