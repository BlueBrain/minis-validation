"""utilities module."""

TIME, VOLTAGE, CURRENT = 0, 1, 2


def parse_slurm_args(slurm_args):
    """Parse processed slurm arguments.

    Args:
        slurm_args: tuple of slurm arguments
    """
    result = {}
    for key, value in slurm_args:
        try:
            parsed_value = int(value)
        except ValueError:
            parsed_value = value

        result["slurm_" + key.replace("-", "_")] = parsed_value

    return result
