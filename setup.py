#!/usr/bin/env python

import imp
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    sys.exit("Sorry, Python < 3.6 is not supported")

# read the contents of the README file
with open("README.rst", encoding="utf-8") as f:
    README = f.read()

VERSION = imp.load_source("", "minis_validation/version.py").__version__

setup(
    name="minis-validation",
    author="bbp-ou-nse",
    author_email="bbp-ou-nse@groupes.epfl.ch",
    version=VERSION,
    description="Validation of spontaneous minis",
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://bbpteam.epfl.ch/documentation/projects/minis-validation",
    project_urls={
        "Tracker": "https://bbpteam.epfl.ch/project/issues/projects/NSETM/issues",
        "Source": "ssh://bbpcode.epfl.ch/nse/minis-validation",
    },
    license="BBP-internal-confidential",
    entry_points={'console_scripts': ['minis-validation=minis_validation.cli:cli']},
    install_requires=[
        'numpy>=1.14',
        'pandas>=0.25',
        'matplotlib>=3.1.1',
        'h5py>=3',
        'click>=6.7',
        'pyyaml>=5.1',
        'dask[distributed,bag]>=2.0',
        'dask_mpi>=2.0',
        'neuron>=7.8',
        'bluepy>0.14,<1.0',
        'bluepy-configfile>=0.1.10',
        'bglibpy>=4.3',
    ],
    packages=find_packages(),
    python_requires=">=3.7",
    extras_require={"docs": ["sphinx", "sphinx-bluebrain-theme"]},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
