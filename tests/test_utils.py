from minis_validation.util import parse_slurm_args


def test_parse_slurm_args():
    slurm_args = (("account", "proj30"), ("partition", "prod"), ("cpus-per-task", "2"))
    result = parse_slurm_args(slurm_args)

    assert result == {
        "slurm_account": "proj30",
        "slurm_partition": "prod",
        "slurm_cpus_per_task": 2
    }
