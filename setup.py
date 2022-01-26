#!/usr/bin/env python
import importlib.util

from setuptools import setup, find_packages

spec = importlib.util.spec_from_file_location(
    "minis_validation.version",
    "minis_validation/version.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
VERSION = module.__version__

# read the contents of the README file
with open("README.rst", "r", encoding="utf-8") as f:
    README = f.read()

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
        'numpy>=1.14,<2',
        'pandas>=0.25,<2',
        'matplotlib>=3.1.1',
        'h5py>=3,<4',
        'click>=7,<8',
        'pyyaml>=5.1,<6',
        'types-PyYAML>=5.1,<6',
        # 2021.8.1 excluded due to https://github.com/dask/distributed/issues/5292
        'dask[distributed,bag]>=2.0,!=2021.8.1',
        'dask_mpi>=2.0',
        'neuron>=7.8',
        'bluepy>=2,<3',
        'bluepy-configfile>=0.1.10,<1',
        'bglibpy>=4.4,<5',
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
