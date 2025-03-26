Glossary
========

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
A workflow template consists of the matflow environment,
the :ref:`task schemas <def_task_schema>`, and the :ref:`command files <def_command_files>`.
