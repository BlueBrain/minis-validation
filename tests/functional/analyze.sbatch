#!/bin/bash
#SBATCH --job-name=minis-validation-analyze-hippocampus-test
#SBATCH --account=proj44
#SBATCH --nodes=1
#SBATCH --time=01:00:00
#SBATCH -C nvme|cpu
#SBATCH --partition=prod
#SBATCH --tasks-per-node=1
#SBATCH --mem=0
#SBATCH --output=minis-validation-analyze-hippocampus-test-out-%j
#SBATCH --error=minis-validation-analyze-hippocampus-test-err-%j

module purge
module load archive/2020-09 neurodamus-hippocampus/0.4 py-dask-mpi/2.0.0
unset PMI_RANK

minis-validation analyze-jobs tests/functional/data/job-configs/ $MINIS_VALIDATION_OUTPUT
