.. jinja:: first_ctx

  Writing custom workflows
  ########################

  {{ app_name }} has a number of built-in :ref:`workflows <def_workflow>`, which use combinations of the
  built-in :ref:`task schemas <def_task_schema>`.
  It is quite possible to mix and match these task schema into new workflows,
  and indeed to write your own task schemas to achieve a particular task.


  Workflow files
  --------------

  In-built {{ app_name }} workflows are split up over a few different files,
  but for development, your workflow code can all go in one yaml file.
  The workflow template has a top-level key ``template_components``
  underneath which come the ``task_schema``, ``environments`` and ``command_files`` keys.

  The workflow itself goes under a different top-level `tasks` key.

  Components of a task schema
  ---------------------------

  Required keys
  *****************
  - ``objective`` (this is a name or label for the schema)
  - ``actions`` (what the task schema actually "does")

  Optional keys
  *****************
  - ``inputs``
  - ``outputs``

  {{ app_name }} syntax
  ---------------------

  If you want to reference parameters in the action of your task schema,
  it should be done using this syntax:
  ``<<parameter:your_parameter_name>>``.

  Similarly, commands defined in an environment can be used like this:
  ``<<executable:your_executable>>``, and files defined as :ref:`command_files <def_command_files>`
  are referenced using ``<<file:your_command_file>>`` e.g.

  .. code-block:: console

      actions:
      - commands:
        - command: <<executable:abaqus>> job=sub_script_check input=<<file:new_inp_file>> interactive


  Note that while command files can be referenced in an action, they cannot be referenced in this way as an input to a task schema.

  Python scripts however are executed slightly differently, and run the
  function defined in your python file which has the same name as the python file.
  The ``<<script:...`` syntax adds some extra processing so you can call the
  function in your python file with arguments, and pass any returned values back to matflow e.g:

  .. code-block:: console

      actions:
      - script: <<script:/full/path/to/my_script.py>>


  where ``my_script.py`` would start with a function definition like this:

  .. code-block:: python

      def my_script():
      ...



  Passing variables around a workflow
  -----------------------------------

  Python scripts that are run by top-level actions and which return values directly
  (i.e. instead of saving to a file) should return a dictionary of values,
  containing keys matching the output parameters defined in the task schema.
  e.g.

  .. code-block:: python

      return {output_parameter_1: values, output_parameter_2: other_values}


  In order for the dictionaries returned from tasks to be accessible to other tasks,
  the task schemas needs to set the input and output type accordingly:

  .. code-block:: yaml

      ...
        actions:
        - script: <<script:/full/path/to/my_script.py>>
          script_data_in: direct
          script_data_out: direct


  It might however be more appropriate to save results to files instead.

  In addition to passing variables directly,
  tasks can read parameters from (and save to) various file formats including JSON and HDF5.

  An example of passing variables directly and via json files is given below.
  {{ app_name }} writes the input parameters into a json file ``js_0_act_0_inputs.json``,
  and the output into a file ``js_0_act_0_outputs.json``.
  These file names are generated automatically,
  and {{ app_name }} keeps track of where the various parameters are stored.
  So if any parameters saved in json files (or passed directly) are needed as input for another function,
  {{ app_name }} can pass them directly or via json as specified in the task schema.
  An example is given of both combinations.

  To run this example, create a ``read_save_workflow.yaml`` file with the contents below,
  along with the ``json_in_json_out.py``, ``json_in_direct_out.py``, and ``mixed_in_direct_out.py`` files.

  .. literalinclude:: read_save_workflow.yaml
        :language: yaml


  .. literalinclude:: json_in_json_out.py
        :language: python


  .. literalinclude:: json_in_direct_out.py
        :language: python


  .. literalinclude:: mixed_in_json_out.py
        :language: python

  The particular variables names used to pass parameters using json/HDF5 depend on
  which language is being used.
  For example using MATLAB uses this syntax ``inputs_JSON_path``, ``outputs_HDF5_path``
  instead of the python equivalents ``_input_files`` and ``_output_files``.
  See the MTEX examples for more details.

  Writing a workflow
  ----------------------------

  A workflow is just a list of tasks, which are run like this

  .. code-block:: yaml

      tasks:
      - schema: my_task_schema
        inputs:
          my_input: input_value


  A task can find output variables from previous tasks, and use them
  as inputs. There is generally no need specify them explicitly,
  but this can be done by using the ``input_sources`` key within a task
  to tell {{ app_name }} where to obtain input values for a given input parameter,
  in combination with the dot notation e.g.

  .. code-block:: yaml

      - schema: print
        # Explicitly reference output parameter from a task
        input_sources:
          string_to_print: task.my_other_task_schema


  When running a workflow with {{ app_name }}, the required files are copied into a directory
  that {{ app_name }} creates, and any output files are saved into the ``execute`` directory.
  If you want to keep any of theses files, you should tell {{ app_name }} to copy them to the ``artifacts``
  directory using ``save_files``:

  .. code-block:: yaml

      task_schemas:
      - objective: my_task_schema
        inputs:
        - parameter: my_input
        outputs:
        - parameter: my_output
        actions:
        - environments: ...
          commands: ...
          save_files:
          - my_command_file


  Example workflow
  -----------------

  .. _command_files_example_workflow:

  Here we have an example workflow which illustrates use of command files.
  To run this example, create a ``command_files_example.yaml`` file with the contents below,
  along with the ``generate_input_file.py`` and ``process_input_file.py`` files.

  Modify the paths to the python scripts under the ``action`` keys to give the full path
  to your files.

  You can then run the workflow using ``{{ app_package_name }} go command_files_example.yaml``.


  .. literalinclude:: command_files_example.yaml
        :language: yaml


  .. literalinclude:: generate_input_file.py
        :language: python


  .. literalinclude:: process_input_file.py
        :language: python
