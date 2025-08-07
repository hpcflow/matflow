.. jinja:: first_ctx

  Advanced workflow concepts
  ###########################

  Resources
  ----------

  Requesting resources can be done using a ``resources`` block, either for the whole workflow at the top level,

  .. code-block:: yaml

      resources:
      any:
        scheduler_args:
          directives:
            --time: 1:00:00
            --partition: multicore

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


  {{ app_name }} is then looking for a match within your environment definitions for the requested
  resources, and will run the command which matches those resources.

  There are lots of :ref:`resource options <reference/_autosummary/{{ app_module }}.ResourceSpec:{{ app_module }}.ResourceSpec>`
  available that can be requested.

  Scheduler arguments can be passed like this e.g. to set a time limit of 1 hour

  .. code-block:: yaml

      resources:
      any:
        scheduler_args:
          directives:
            --time: 1:00:00
        num_cores: 10

  Anything specified under `directives` is passed directly to the scheduler as a jobscript command (i.e. isn't processed by {{ app_name }} at all).

  If you have set resource options at the top level (for the whole workflow), but would like to "unset" them for a particular task,
  you can pass an empty dictionary:

  .. code-block:: yaml

    - schema: simulate_VE_loading_damask
      resources:
        main:
          num_cores: 16
          scheduler_args:
            directives: {} # "Clear" any previous directives which have been set.


  Task sequences
  ----------------

  {{ app_name }} can run tasks over a set of independent input values.
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


  .. literalinclude:: groups_workflow.yaml
        :language: YAML


  Task schema shortcuts
  ---------------------

  Input file generators
  ~~~~~~~~~~~~~~~~~~~~~

  ``input_file_generators`` is a convenience shortcut for a python script which generates an input file
  for a subsequent action within a task. It's more compact, easier to reference, and has more interaction options.
  The first parameter in the input generator (python) function definition must be "path",
  which is the file path to ``input_file``, the file you want to create.
  Given this is a {{ app_name }} input file, the path is just the file name which will be created in the
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
  expanded below to demonstrate ``input_file_generators`` and ``output_file_parsers``,
  along with the alternative code which would be needed to achieve the same result
  as the input file generator:

  .. literalinclude:: advanced_workflow.yaml
        :language: yaml


  This workflow uses the same python scripts as before, with the addition of ``parse_output.py``:

  .. literalinclude:: parse_output.py
        :language: python
