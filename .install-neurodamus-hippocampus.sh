#!/usr/bin/env bash
# The tests for minis-validation require an installation of the hippocampus mod files
# that were compiled with the installed NEURON, and its dependencies.
# (see .compile_mod, .install_common_mods.sh and .install_neurodamus.sh)
# and by looking at how BlueBrain's spack installs the mods
set -euxo pipefail

BASE=$1

DONE=$BASE/.installed_hippocampus_mod_files
if [[ -f $DONE ]]; then
    echo "Already installed mod files"
    exit
fi

rm -rf "$BASE"
mkdir -p "$BASE"

GIT_BASE=git@bbpgitlab.epfl.ch:hpc/sim

pushd "$BASE"

git clone -q --depth 1 $GIT_BASE/neurodamus-core.git

MODELS=("hippocampus" "mousify" "neocortex" "thalamus")

for MODEL in "${MODELS[@]}"; do
    echo "Cloning models for $MODEL"
    git clone -q --depth 1 --recursive $GIT_BASE/models/$MODEL.git
done

for MODEL in "${MODELS[@]}"; do
    echo "Downloading models for $MODEL"
    pushd $MODEL
    ./fetch_common.bash
    popd
done

for MODEL in "${MODELS[@]}"; do
    echo "Compiling models for $MODEL"
    nrnivmodl $MODEL/mod
done

popd
touch "$DONE"
