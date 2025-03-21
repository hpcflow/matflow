Glossary
========


API
---

Application programming interface. MatFlow's API allows us to design and execute workflows from within a Python interpreter or Jupyter notebook.

CLI
---

Command line interface. The CLI is typically how we interact with MatFlow on HPC systems.

cluster
-------

See HPC

DAMASK
------

Fortran package for multi-physics crystal plasticity simulation. 
Official documentation and installation [on their webpage](https://damask-multiphysics.org/)

DAMASK-parse
------------

Python package to translate input and output files between formats needed for DAMASK and MatFlow. 
Download from the [GitHub repository](https://github.com/LightForm-group/damask-parse)

defdap
------

Python library for deformation data analysis. Used to define/manipulate orientations as Euler angles or quaternions. 
See [official documentation](https://defdap.readthedocs.io/en/latest/) or [GitHub repository](https://github.com/MechMicroMan/DefDAP).

Environment/virtual environment
-------------------------------

An environment is an isolated set of installed software. 
Using environments allows you to have multiple copies of the same software installed in different environments so you can run different versions, or to run two pieces of software with competing dependencies on the same machine. 
Using and sharing environments helps make your work reproducible because someone can use the same environment on a different machine and be sure they have the same versions of everything.

formable
--------

Python package for formability analysis in materials science. Used to create loadcases in DAMASK format. 
Download from the [GitHub repository](https://github.com/LightForm-group/formable)

HPC
---

High-performance computer/computing

HPCFlow
-------

The underlying workflow management tool that MatFlow uses to interface with your computing resources or scheduler. 
MatFlow exists as a layer on top of HPCFlow that focuses on common workflows and tools within computational materials science.

loadcase
--------

Numerical description of how the simulated material is loaded (stretched, compressed, rolled, ...). 
A corresponding MatFlow parameter is documented [here](https://docs.matflow.io/stable/reference/template_components/parameters.html#load-case).

MatFlow
-------

MatFlow is a computational workflow management package for materials science.

workflow
--------

A pipeline that processes data in some way.
