Advanced workflow concepts
###########################

Resources
----------

Requesting resources can be done using a ``resources`` block, either for the whole workflow at the top level,

.. code-block:: yaml

    resources:
    any:
      scheduler: sge # Setting the scheduler is not normally needed because a
                     # `default_scheduler` will be set in the config file.
      scheduler_args:
        shebang_args: --login
        options:
          -l: short


or at the task level

.. code-block:: yaml

  - schema: simulate_VE_loading_damask
    resources:
      any:
      # This will use two cores for input file generators and output file parsers
      num_cores: 2
      main:
      # Use 16 cores for the "main" part of the task (the simulation in this case)
      num_cores: 16
    inputs:
        ...


We can see from above that it is possible to request resources for subsets of the actions
in a task schema. A full list of the different options you can select resources for is given below.

- ``input_file_generator``
- ``output_file_parser``
- ``processing`` (a shortcut for ``input_file_generator`` +  ``output_file_parser``)
- ``main`` (the main part of the action i.e. not ``processing``)
- ``any`` (anything not already specified with any of the above options)

These are used to choose resources (done at the workflow/task level),
and also the same values can be used within the schema to select an ``environment``
by ``scope`` e.g.

.. code-block:: yaml

    actions:
    - environments:
    - scope:
        type: processing
        environment: damask_parse_env
    - scope:
        type: main
        environment: damask_env


MatFlow is then looking for a match within your environment definitions for the requested
resources, and will run the command which matches those resources.

There are lots of :ref:`resource options <reference/_autosummary/matflow.ResourceSpec:matflow.ResourceSpec>`
available that can be requested.

Scheduler arguments can be passed like this e.g. to target high memory nodes:

.. code-block:: yaml

    resources:
    any:
      num_cores: 10
      SGE_parallel_env: smp.pe
      scheduler_args:
        options:
          -l: mem512

Anything specified under `options` is passed directly to the scheduler as a jobscript command (i.e. isn't processed by MatFlow at all).

If you have set resource options at the top level (for the whole workflow), but would like to "unset" them for a particular task,

you can pass an empty dictionary:

.. code-block:: yaml

  - schema: simulate_VE_loading_damask
    resources:
      main:
      num_cores: 16
      scheduler_args:
          options: {} # "Clear" any previous options which have been set.
    inputs:


Task sequences
----------------

Matflow can run tasks over a set of independent input values.
For this, you use a ``sequence``, and a ``nesting_order`` to control the nesting of the loops
but you can also "zip" two or more lists of inputs by using the same level of nesting.
Lower values of ``nesting_order`` act like the "outer" loop.

.. code-block:: yaml

    tasks:
    - schema: my_schema
    sequences:
    - path: inputs.conductance_value
    values:
    - 0
    - 100
    - 200
    nesting_order: 0

Groups
-------

To combine outputs from multiple elements, you can use a ``group`` in a task schema:

.. code-block:: yaml

  - objective: my_task_schema
    inputs:
    - parameter: p2
        group: my_group

combined with a ``groups`` entry in the task itself.

.. code-block:: yaml

  - schema: my_task_schema
    groups:
    - name: my_group


Then whichever parameters are linked with the group in the task schema will be received by the task as a list.


Here is an example workflow using sequences and groups that you might wish to run to solidify your understanding

.. code-block:: yaml

    # groups_workflow.yaml

    template_components:
      task_schemas:
        - objective: s1
          inputs:
            - parameter: p1
          outputs:
            - parameter: p2
          actions:
            - commands:
                - command: echo $(( <<parameter:p1>> + 1 )) # This is printed to stdout
                - command: echo $(( <<parameter:p1>> + 1 )) # This is captured as p2
                  stdout: <<int(parameter:p2)>>
        - objective: s2
          inputs:
            - parameter: p2
              group: my_group
          outputs:
            - parameter: p3
          actions:
            - commands:
                - command: echo <<parameter:p2>> # This one is printed to stdout
                - command: echo $(( <<sum(parameter:p2)>> )) # This is captured as p3
                  stdout: <<int(parameter:p3)>>
    tasks:
      - schema: s1
        sequences:
          - path: inputs.p1
            values: [1, 2]
        groups:
          - name: my_group
      - schema: s2


Task schema shortcuts
---------------------

Input file generators
~~~~~~~~~~~~~~~~~~~~~

``input_file_generators`` is a convenience shortcut for a python script which generates an input file
for a subsequent action within a task. It's more compact, easier to reference, and has more interaction options.
The first parameter in the input generator (python) function definition must be "path",
which is the file path to ``input_file``, the file you want to create.
Given this is a Matflow input file, the path is just the file name which will be created in the
execute directory.
The ``input_file`` must point to the label of a file in ``command_files``.
``from_inputs`` defines which of the task schema inputs are required for each of the ``input_file_generators``.

.. code-block:: yaml


    task_schemas:
    - objective: my_task_schema
    actions:
    - input_file_generators:
      - input_file: my_command_file
        from_inputs:
        - my_input_1
        - my_input_2
        script: <<script:/full/path/to/generate_input_file.py>>

An example is given in [advanced_workflow.yaml](advanced_workflow.yaml), along with the alternative code which would be needed

to achieve the same result without an input file generator.

Output file parsers
~~~~~~~~~~~~~~~~~~~

``output_file_parsers`` is a shortcut for a python script which processes output files
from previous steps.
The function in the python script must have parameters for each of the files listed
in ``from_files``, and this function should return data in a dictionary.
The output file parser script can also have parameters for any of the task schema inputs,
and these are listed under an ``inputs`` key.
If you want to save results to a file, this can be done in the python function too,
but the function should return a dict. This can be hard-coded in the function,
or via an ``inputs: [path_to_output_file]`` line in the output file parser,
and it will come after the output files in the function signature.

The "name" of the ``output_file_parsers`` is the parameter returned i.e.

.. code-block:: yaml

    output_file_parsers:
      return_parameter: # This should be listed as an output parameter for the task schema
        from_files:
        - command_file1
        - command_file2
        script: <<script:your_processing_script.py>>
        save_files:
        - command_file_you_want_to_save
        inputs:
        - input1
        - input2

The output_file_parser script that is run as the action should return one variable,
rather than a dictionary. This is different behaviour to
a "main" action script.
i.e. ``return the_data`` rather than ``return {"return_parameter": the_data}``.
This is because an output file parser only has one named output parameter,
so a dictionary isn't needed to distinguish different output parameters.

The :ref:`previous example <command_files_example_workflow>` has been reworked and
expanded below to demonstrate ``input_file_generators`` and ``output_file_parsers``.

.. code-block:: yaml

    # workflow.yaml

    template_components:
      task_schemas:
      - objective: process_some_data
        inputs:
        - parameter: input_data
        outputs:
        - parameter: parsed_output
        actions:
        - input_file_generators:
          - input_file: my_input_file
            from_inputs:
            - input_data
            script: <<script:/full/path/to/generate_input_file.py>>
          environments:
          - scope:
              type: any
            environment: python_env
          script_exe: python_script
          script: <<script:/full/path/to/process_input_file.py>>
          save_files:
          - processed_file
          output_file_parsers:
            parsed_output:
              from_files:
              - my_input_file
              - processed_file
              script: <<script:/full/path/to/parse_output.py>>
              save_files:
                - parsed_output

This workflow uses the same python scripts as before, with the addition of

.. code-block:: python

    # parse_output.py

    import json
    def parse_output(my_input_file: str, processed_file: str):
        """Do some post-processing of data files.

        In this instance, we're just making a dictionary containing both the input
        and output data.
        """
        with open(my_input_file, "r") as f:
            input_data = json.load(f)
        with open(processed_file, "r") as f:
            processed_data = json.load(f)

        combined_data = {"input_data": input_data, "output_data": processed_data}
        # Save file so we can look at the data
        with open("parsed_output.json", "w") as f:
            json.dump(combined_data, f, indent=2)

        return {"parsed_output": combined_data}
