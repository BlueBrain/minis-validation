minis-validation
================

Validation of spontaneous minis.


Installation
------------

Until the project is available via modules on BB5, the only way is to install via pip.

.. code:: bash

    pip install --index-url https://bbpteam.epfl.ch/repository/devpi/bbprelman/dev/+simple/ minis-validation

When available as a module.

.. code:: bash

    module load unstable minis-validation

Usage
-----
Currently the project can be used only on BB5!

Cli
^^^
The recommended usage is via the command line interface API. To run simulations of minis with
different sets of parameters:

.. code:: bash

    minis-validation -vv simulate \
      /path/to/BlueConfig \
      /path/to/frequencies.csv \
      /path/to/job-configs/ \
      /path/to/output/ \
      -n 1000 \
      -T /path/to/user.target

`-vv` options stands for verbosity of log output. There are 3 different values for it: `-v`, `-vv`,
`-vvv`. `-v` is for showing only warnings and errors. `-vv` additionally to `-v` shows info
messages. `-vvv` additionally shows debug messages. By default `-v` is used. This flag is common to
all NSE projects, and is usually used right after the main command and before the supplementary
command. The main command is `minis-validation`, the supplementary command is `simulate`.

For all options and arguments of `simulate` command see its help:

.. code:: bash

    minis-validation simulate --help

``/path/to/job-configs/`` must contain job config files. Each file is a yaml file of the following
format :ref:`ref-job-config`.
``/path/to/frequencies.csv`` a file that contains frequencies to simulate :ref:`ref-frequencies`.

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

BB5
^^^
For now the project can only be used on BB5 as it requires a lot of computational resources, and
uses a special cluster software library Dask for running simulations.
An example of srun for `simulate` command:

.. code:: bash

    module load unstable
    module load neurodamus-hippocampus # This `neurodamus` is an example. Choose appropriate `neurodamus` for your circuit.
    module load py-minis-validation
    # unset PMI_RANK  # you might need this command to disable Neuron mechanisms try to load MPI

    srun -Aproj30 -N8 -t=24:00:00 --cpus-per-task=2 --exclusive minis-validation -vv simulate \
    /path/to/BlueConfig \
    /path/to/frequencies.csv \
    /path/to/job-configs/ \
    /path/to/output/ \
    -n 1000 \
    -T /path/to/user.target


An example of sbatch script for `simulate` command:
.. code:: bash

    #!/bin/bash
    #SBATCH --job-name=minis-validation-simulate
    #SBATCH --account=<your_project>
    #SBATCH --nodes=16
    #SBATCH --time=24:00:00
    #SBATCH --cpus-per-task=2
    #SBATCH -C cpu
    #SBATCH --mem=0
    #SBATCH --partition=prod
    #SBATCH --exclusive
    #SBATCH --output=minis-validation-simulate_out_%j
    #SBATCH --error=minis-validation-simulate_err_%j

    module purge
    module load archive/2020-09 neurodamus-neocortex/0.3 # This `neurodamus` is an example. Choose appropriate `neurodamus` for your circuit.
    module load py-minis-validation
    unset PMI_RANK  # by default Neuron mechanism try to load MPI, we have to disable it
    export DASK_DISTRIBUTED__WORKER__USE_FILE_LOCKING=False
    export DASK_DISTRIBUTED__WORKER__MEMORY__TARGET=False  # don't spill to disk
    export DASK_DISTRIBUTED__WORKER__MEMORY__SPILL=False  # don't spill to disk
    export DASK_DISTRIBUTED__WORKER__MEMORY__PAUSE=0.80  # pause execution at 80% memory use
    export DASK_DISTRIBUTED__WORKER__MEMORY__TERMINATE=0.95  # restart the worker at 95% use
    export DASK_DISTRIBUTED__WORKER__MULTIPROCESSING_METHOD=spawn
    export DASK_DISTRIBUTED__WORKER__DAEMON=True
    # Reduce dask profile memory usage/leak (see https://github.com/dask/distributed/issues/4091)
    export DASK_DISTRIBUTED__WORKER__PROFILE__INTERVAL=10000ms  # Time between statistical profiling queries
    export DASK_DISTRIBUTED__WORKER__PROFILE__CYCLE=1000000ms  # Time between starting new profile


    srun minis-validation -vv simulate \
    /path/to/BlueConfig \
    /path/to/frequencies.csv \
    /path/to/job-configs/ \
    /path/to/output/ \
    -n 1000 \
    -T /path/to/user.target

The above script will launch running of simulations on a cluster of 16 nodes orchestrated by Dask.
For 5 job configs and 16 frequencies, it takes around 12 hours to finish. For analysis commands
there is no need to sbatch. On an allocation of one node with `--mem=0`, it takes around 20-30
minutes to analyze all jobs results.