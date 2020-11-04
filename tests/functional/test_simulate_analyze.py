import os
from pathlib import Path
import pandas as pd

TEST_DATA_DIR = Path(__file__).parent / 'data'


def assert_job_output(job_output_dir):
    assert job_output_dir.is_dir()
    frequencies = pd.read_csv(TEST_DATA_DIR / 'frequencies.csv', sep='\t')['MINIS_FREQ']
    expected_files = {f'traces_freq{frequency:.3f}.h5' for frequency in frequencies}
    assert expected_files == {file.name for file in job_output_dir.glob('*.h5')}
    assert (job_output_dir / 'analysis').is_dir()
    assert (job_output_dir / 'analysis' / 'frequencies.png').is_file()


def test_simulate_analyze():
    output = os.getenv('MINIS_VALIDATION_OUTPUT')
    assert output is not None, 'environment variable MINIS_VALIDATION_OUTPUT must be set'
    output = Path(output)
    assert (output / 'job_results.csv').is_file()
    assert_job_output(output / 'PC_Exc')
    assert_job_output(output / 'PC_Inh')
