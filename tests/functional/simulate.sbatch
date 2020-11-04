#!/bin/bash
#SBATCH --job-name=minis-validation-simulate-hippocampus-test
#SBATCH --account=proj44
#SBATCH --nodes=8
#SBATCH --time=01:00:00
#SBATCH -C nvme|cpu
#SBATCH --partition=prod
#SBATCH --exclusive
#SBATCH --tasks-per-node=36
#SBATCH --mem=0
#SBATCH --output=minis-validation-simulate-hippocampus-test-out-%j
#SBATCH --error=minis-validation-simulate-hippocampus-test-err-%j

export DASK_DISTRIBUTED__LOGGING__DISTRIBUTED="critical"
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

module purge
module load archive/2020-09 neurodamus-hippocampus/0.4 py-dask-mpi/2.0.0
unset PMI_RANK

srun minis-validation simulate \
tests/functional/data/BlueConfig \
tests/functional/data/frequencies.csv \
tests/functional/data/job-configs/ \
$MINIS_VALIDATION_OUTPUT \
-n 10 \
-T tests/functional/data/user.target
