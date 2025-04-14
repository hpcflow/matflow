Writing custom workflows
########################

MatFlow has a number of built-in :ref:`workflows <def_workflow>`, which use combinations of the
built-in :ref:`task schemas <def_task_schema>`. 
It is quite possible to mix and match these task schema into new workflows,
and indeed to write your own task schemas to achieve a particular task.


Workflow files
---------------
In-built matflow workflows are split up over a few different files,
but for development, your workflow code can all go in one yaml file.
The workflow template has a top-level key ``template_components``
underneath which come the ``task_schema``, ``environments`` and ``command_files`` keys.

The workflow itself goes under a different top-level `tasks` key.

Components of a task schema
----------------------------

Required keys
*****************
- ``objective`` (this is a name or label for the schema)
- ``actions`` (what the task schema actually "does")

Optional keys
*****************
- ``inputs``
- ``outputs``

Matflow syntax
--------------
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
--------------------------------------------------------
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
MatFlow writes the input parameters into a json file ``js_0_act_0_inputs.json``,
and the output into a file ``js_0_act_0_outputs.json``.
These file names are generated automatically,
and MatFlow keeps track of where the various parameters are stored.
So if any parameters saved in json files (or passed directly) are needed as input for another function,
MatFlow can pass them directly or via json as specified in the task schema.
An example is given of both combinations.

To run this example, create a ``workflow.yaml`` file with the contents below,
along with the ``json_in_json_out.py``, ``json_in_direct_out.py``, and ``mixed_in_direct_out.py`` files.


.. code-block:: yaml

    # workflow.yaml
    template_components:
      task_schemas:
      - objective: read_and_save_using_json
        inputs:
        - parameter: p1
        - parameter: p2
        actions:
        - script: <<script:/full/path/to/json_in_json_out.py>>
          script_data_in: json
          script_data_out: json
          script_exe: python_script
          environments:
          - scope:
              type: any
            environment: python_env
        outputs:
        - parameter: p3
      - objective: read_json_from_another_task
        inputs:
        - parameter: p3
        actions:
        - script: <<script:/full/path/to/json_in_direct_out.py>>
          script_data_in: json
          script_data_out: direct
          script_exe: python_script
          environments:
          - scope:
              type: any
            environment: python_env
        outputs:
        - parameter: p4
      - objective: pass_mixed_from_another_task
        inputs:
        - parameter: p3
        - parameter: p4
        actions:
        - script: <<script:/full/path/to/mixed_in_direct_out.py>>
          script_data_in:
            p3: direct # previously saved as json in task read_and_save_using_json
            p4: json # previously saved directly in task read_json_from_another_task
          script_data_out: direct
          script_exe: python_script
          environments:
          - scope:
              type: any
            environment: python_env
        outputs:
        - parameter: p5

    tasks:
    - schema: read_and_save_using_json
      inputs:
        p1: 1
        p2: 2
    - schema: read_json_from_another_task
    - schema: pass_mixed_from_another_task


.. code-block:: python

    # json_in_json_out.py
    import json

    def json_in_json_out(_input_files, _output_files):
        with open(_input_files["json"]) as json_data:
            inputs = json.load(json_data)
        p1 = inputs["p1"]
        p2 = inputs["p2"]

        p3 = p1 + p2
        with open(_output_files["json"], 'w') as f:
            json.dump({"p3": p3}, f)


.. code-block:: python

    # json_in_direct_out.py
    import json

    def json_in_direct_out(_input_files):
        with open(_input_files["json"]) as json_data:
            inputs = json.load(json_data)
        p3 = inputs["p3"]
        p4 = p3 + 1

        print(f"{p3=}")
        print(f"{p4=}")

        return {"p4": p4}


.. code-block:: python

  # mixed_in_json_out.py
  import json

  def mixed_in_direct_out(p3, _input_files):
      with open(_input_files["json"]) as json_data:
          inputs = json.load(json_data)
      p4 = inputs["p4"]
      p5 = p3 + p4

      print(f"{p3=}")
      print(f"{p4=}")
      print(f"{p5=}")

      return {"p5": p5}

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
to tell MatFlow where to obtain input values for a given input parameter,
in combination with the dot notation e.g.

.. code-block:: yaml

    - schema: print
      # Explicitly reference output parameter from a task
      input_sources:
        string_to_print: task.my_other_task_schema


When running a workflow with Matflow, the required files are copied into a directory
that Matflow creates, and any output files are saved into the ``execute`` directory.
If you want to keep any of theses files, you should tell MatFlow to copy them to the ``artifacts``
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
To run this example, create a ``workflow.yaml`` file with the contents below,
along with the ``generate_input_file.py`` and ``process_input_file.py`` files.

Modify the paths to the python scripts under the ``action`` keys to give the full path
to your files.

You can then run the workflow using ``matflow go workflow.yaml``.

.. code-block:: yaml

    # workflow.yaml
    template_components:
      task_schemas:
      - objective: process_data
        inputs:
        - parameter: input_data
        - parameter: path
          default_value: input_file.json
        actions:
        - script: <<script:/path/to/generate_input_file.py>>
          script_data_in: direct
          script_exe: python_script
          save_files: # A copy of any command files listed here will be saved in the the artifacts directory
          - my_input_file
          environments:
          - scope:
              type: any
            environment: python_env
        - script: <<script:/path/to/process_input_file.py>>
          script_exe: python_script
          environments:
          - scope:
              type: any
            environment: python_env
          save_files:
          - processed_file

      command_files:
      - label: my_input_file
        name:
          name: input_file.json
      - label: processed_file
        name:
          name: processed_file.json


    tasks:
    - schema: process_data
      inputs:
        input_data: [1, 2, 3, 4]
        path: input_file.json

.. code-block:: python

    # generate_input_file.py
    import json
    def generate_input_file(path: str, input_data: list):
        """Generate an input file"""
        with open(path, "w") as f:
            json.dump(input_data, f, indent=2)

.. code-block:: python

    # process_input_file.py
    import json
    def process_input_file():
        """Process an input file.

        This could be a materials science simulation for example.
        """
        with open("input_file.json", "r") as f:
            data = json.load(f)
        data = [item * 2 for item in data]
        with open("processed_file.json", "w") as f:
            json.dump(data, f, indent=2)
