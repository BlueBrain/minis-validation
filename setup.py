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
        "Source": "ssh://bbpgitlab.epfl.ch/nse/minis-validation",
    },
    license="BBP-internal-confidential",
    entry_points={'console_scripts': ['minis-validation=minis_validation.cli:cli']},
    install_requires=[
        'numpy>=1.14,<2',
        'pandas>=2.0.2',
        'matplotlib>=3.1.1',
        'h5py>=3,<4',
        'click>=8.1.3',
        'tqdm==4.64.1',
        'submitit>=1.4.5,<2',
        'pyyaml>=6.0',
        'types-PyYAML>=6.0.12.10',
        'libsonata>=0.1.20,<1.0.0',
        'bluepysnap>=1.0.6,<2.0.0',
        'bluecellulab>=1.5.2',
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
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
)
