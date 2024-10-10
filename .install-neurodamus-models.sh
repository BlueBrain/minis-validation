#!/usr/bin/env bash
# The tests for minis-validation require an installation of the thalamus mod files
set -euxo pipefail

BASE=$1

DONE=$BASE/.installed_hippocampus_mod_files
if [[ -f $DONE ]]; then
    echo "Already installed mod files"
    exit
fi

rm -rf "$BASE"
mkdir -p "$BASE"

pushd "$BASE"

echo "Cloning models"
git clone -q --depth 1 --recursive https://github.com/BlueBrain/neurodamus-models/

echo "Compiling models"
nrnivmodl neurodamus-models/thalamus/mod

popd
touch "$DONE"
