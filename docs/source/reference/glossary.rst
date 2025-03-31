Glossary
========

API
---

Application programming interface. MatFlow's API allows us to design and execute workflows from within a Python interpreter or Jupyter notebook.

.. _def_command_files:

Command files
-------------
If you want to refer to any files that are used as inputs or output,
they should be listed under ``command_files`` in the workflow file

.. code-block:: console

    command_files:
      - label: new_inp_file
        name:
          name: friction_conductance.inp


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

.. _def_task:

Tasks
-------------
These are actual usages of a :ref:`task schema <def_task_schema>`, run with defined inputs.

.. _def_task_schema:

Task schema
-------------
This is a template for a task you want to run,
with definitions of the input and outputs that are expected.

Matflow has many :ref:`built-in task schemas <task_schemas>`, but you may want to
write your own.

.. _def_workflow:

Workflow
--------

A pipeline that processes data in some way.
A workflow is a list of tasks that run one after the other.


.. _def_workflow_template:

Workflow template
------------------

A workflow template parameterises a workflow,
providing the required input values for the task schemas of the workflow.
However, it doesn't actually run the :ref:`workflow <def_workflow>`.
A workflow template is usually just the list of tasks,
but can optionally include matflow environment,
the :ref:`task schemas <def_task_schema>`, and the :ref:`command files <def_command_files>`.
