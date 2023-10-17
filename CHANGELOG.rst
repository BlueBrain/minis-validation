Changelog
=========

Version 0.1.0
-------------
- Upgrade to sonata config
- Switch to submitit from dask
- Switch to Bluecellulab from bglibpy

Version 0.0.6
-------------
- Add new option ``mpi`` for ``minis_validation.simulation.run``. It allows to choose whether
  to run parallel simulations with mpi or not.
- [NSETM-2061] Remove usage of blueconfig (require bglibpy>=4.9.5)
- Add explicit support and tests for python 3.10

Version 0.0.5
-------------
- Tighter dependencies restrictions on Dask dependencies

Version 0.0.4
-------------
- [NSETM-1412] Use partition size of 1 to boost parallel running of simulations with Dask
- Remove neurom as dependency
- Update bluepy dependency to version 2.0, h5py to 3.0

Version 0.0.3
-------------
- Fix bluepy dependency with respect to functional tests
- Use projections in simulations

Version 0.0.2
-------------
- Fix setup dependencies with respect to spack

Version 0.0.1
-------------
- First working version
