import shutil
from pathlib import Path

import pandas as pd
import pytest

from minis_validation import analysis, simulation

TEST_DATA_DIR = Path(__file__).parent / "data"


def test_simulate_analyze(tmp_path):
    output = tmp_path / "output"
    log_dir = tmp_path / "log"

    simulation.run(
        TEST_DATA_DIR / "simulation_config.json",
        TEST_DATA_DIR / "frequencies.csv",
        TEST_DATA_DIR / "job-configs",
        output,
        num_cells=2,
        log_dir=str(log_dir),
        timeout_s=1200,
        slurm_args={},
    )
    _print_job_logs(log_dir)

    analysis.analyze_jobs(TEST_DATA_DIR / "job-configs", output)

    assert (output / "job_results.csv").is_file()
    _assert_job_output(output / "PC_Exc")
    _assert_job_output(output / "PC_Inh")


def _assert_job_output(job_output_dir):
    assert job_output_dir.is_dir()
    frequencies = pd.read_csv(TEST_DATA_DIR / "frequencies.csv", sep="\t")["MINIS_FREQ"]
    expected_files = {f"traces_freq{frequency:.3f}.h5" for frequency in frequencies}
    assert expected_files == {file.name for file in job_output_dir.glob("*.h5")}
    assert (job_output_dir / "analysis").is_dir()
    assert (job_output_dir / "analysis" / "frequencies.png").is_file()


def _print_job_logs(log_dir):
    print("=== Standard output of jobs ==")
    standard_paths = log_dir.glob("**/*.out")
    for standard_path in standard_paths:
        with open(standard_path, "r") as f:
            print(f.read(), end="")
            print("=" * 30)
    print("==== Error output of jobs ====")
    error_paths = log_dir.glob("**/*.err")
    for error_path in error_paths:
        with open(error_path, "r") as f:
            print(f.read(), end="")
            print("=" * 30)
