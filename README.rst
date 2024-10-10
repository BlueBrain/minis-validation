minis-validation
================

Validation of spontaneous minis.


Installation
------------

minis-validation can be installed using `pip`:

.. code:: bash

    pip install minis-validation

Compiled mechanisms are required to run simulations in minis-validation.
Please refer to the `documentation of BlueCelluLab <https://bluecellulab.readthedocs.io/>`_
for a `guide on how to compile mechanisms <https://bluecellulab.readthedocs.io/en/latest/compiling-mechanisms.html>`_.


Usage
-----

It is recommended to run the project on a platform supporting SLURM to take advantage of parallelism.
However it is possible to run it without SLURM.

CLI
^^^

The recommended usage is via the command line interface.

To run minis-validation with the test data use this command:

.. code:: bash

    # using SLURM
    minis-validation -vv simulate         \
        tests/data/simulation_config.json \
        tests/data/frequencies.csv        \
        tests/data/job-configs/           \
        out                               \
        -n 1000                           \
        --log-dir log_dir                 \
        --timeout-s 28800                 \
        --slurm account proj30            \
        --slurm partition prod            \
        --slurm array-parallelism 200

    # using local executor
    minis-validation -vv simulate         \
        tests/data/simulation_config.json \
        tests/data/frequencies.csv        \
        tests/data/job-configs/           \
        out                               \
        -n 1000                           \
        --log-dir log_dir                 \
        --timeout-s 28800


`-vv` options stands for verbosity of log output.
There are 3 different values for it: `-v`, `-vv`, `-vvv`. `-v` is for showing only warnings and errors.
`-vv` additionally to `-v` shows info messages. `-vvv` additionally shows debug messages.
By default `-v` is used.
This flag is usually used right after the main command and before the supplementary command.
The main command is `minis-validation`, the supplementary command is `simulate`.

SLURM configuration
"""""""""""""""""""

Many SLURM config values may be passed in the command line using the ``--slurm`` option.
See the full list in `submitit <https://github.com/facebookincubator/submitit>`__, specifically the arguments of ``SlurmExecutor._make_sbatch_string()``.

Note: the slurm keys must be provided without ``slurm`` prefix, and they should be separated by dashes instead of underscores.

Note: the value of `--timeout-s` is converted to the right format and passed to SLURM as ``time``, so you should not specify ``--slurm time``.

Mandatory arguments:
``--slurm account``, ``--slurm partition``

Recommended arguments:
 * `--slurm array-parallelism` - number of tasks to run concurrently
 * `--slurm cpus-per-task` - number of CPUs per task
 * `--slurm mem` - amount of memory over all
 * `--slurm mem-per-cpu` - amount of memory per CPU

Note: `--slurm mem` and `--slurm mem-per-cpu` are mutually exclusive

So far we have no guidelines for the values. They have to be tuned for each circuit.
Feel free to submit a PR with your findings.

For all options and arguments of `simulate` command see its help:

.. code:: bash

    minis-validation simulate --help

``/path/to/job-configs/`` must contain job config files. Each file is a YAML file of the `following
format <job_config.html>`_.
``/path/to/frequencies.csv`` is a file that contains frequencies to simulate. `An example
<frequencies.html>`_.

To run analysis of all simulations, e.g. of all jobs configs:

.. code:: bash

    minis-validation -vv analyze-jobs /path/to/job-configs/ /path/to/output_of_simulate/

To run analysis of single job config:

.. code:: bash

    minis-validation -vv analyze-job /path/to/job-configs/job-config-file /path/to/output_of_simulate/job-folder/

Important to remember that analysis skips the 1st second of simulations. For all options and
arguments of analysis commands see their help:

.. code:: bash

    minis-validation analyze-job --help
    minis-validation analyze-jobs --help


Acknowledgements
================

The development of this software was supported by funding to the Blue Brain Project, a research center of the École polytechnique fédérale de Lausanne (EPFL), from the Swiss government’s ETH Board of the Swiss Federal Institutes of Technology.

This project/research received funding from the European Union’s Horizon 2020 Framework Programme for Research and Innovation under the Framework Partnership Agreement No. 650003 (HBP FPA).

For license see LICENSE.txt.

Copyright (c) 2020-2024 Blue Brain Project/EPFL
