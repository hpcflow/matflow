Environments
############

`matlab_env`
~~~~~~~~~~~~


* There are two ways of running tasks that use MTEX. Scripts can either be compiled and then the compiled application can be run, or the script can be run directly.
* This is controlled by the `compile` input parameter, which is `False` by default. When `compile` is `False`, the `run_mtex` executable must be defined in the `matlab_env`. When `compile` is `True`, the `compile_mtex` and `run_compiled_mtex` exectuables must both be fined in the `matlab_env`.
* In the examples below, all executables are defined, meaning MTEX tasks can be run with `compile=True` or `compile=False`.
* For direct script execution (`compiled=False`), the MATLAB `-batch` switch is used, and is documented here for `Windows <https://uk.mathworks.com/help/matlab/ref/matlabwindows.html>`_, `MacOS <https://uk.mathworks.com/help/matlab/ref/matlabmacos.html>`_, and `Linux <https://uk.mathworks.com/help/matlab/ref/matlablinux.html>`_.
* Note: use of the `compile_mtex` executable requires that the Matlab Compiler add-on is installed, which can be performed via the Add-on explorer within the Matlab GUI.
* TODO: This is currently tested only on Windows

Example environment definition - Windows
----------------------------------------

.. code-block:: yaml

  - name: matlab_env
    executables:

      - label: run_mtex
        instances:
          - command: |
              & 'C:\path\to\matlab.exe' -batch "addpath('<<script_dir>>'); <<script_name_no_ext>> <<args>>"
            num_cores: 1
            parallel_mode: null

      - label: compile_mtex
        instances:
          - command: |
              $mtex_path = 'C:\path\to\mtex\folder'
              & 'C:\path\to\mcc.bat' -R -singleCompThread -m "<<script_path>>" <<args>> -o matlab_exe -a "$mtex_path/data" -a "$mtex_path/plotting/plotting_tools/colors.mat"
            num_cores: 1
            parallel_mode: null

      - label: run_compiled_mtex
        instances:
          - command: .\matlab_exe.exe <<args>>
            num_cores: 1
            parallel_mode: null

Example environment definition - Linux/MacOS
--------------------------------------------

.. code-block:: yaml

  - name: matlab_env
    setup: |
      # set up commands (e.g. `module load ...`)
    executables:
    
      - label: run_mtex
        instances:
          - command: |
              /path/to/matlab -batch "addpath('<<script_dir>>'); <<script_name_no_ext>> <<args>>"
            num_cores: 1
            parallel_mode: null

      - label: compile_mtex
        instances:
          - command: |
              MTEX_PATH="/path/to/MTEX/folder"
              /path/to/mcc -R -singleCompThread -m "<<script_path>>" <<args>> -o matlab_exe -a "$MTEX_PATH/data" -a "$MTEX_PATH/plotting/plotting_tools/colors.mat"
            num_cores: 1
            parallel_mode: null

      - label: run_compiled_mtex
        instances:
          - command: |
              MATLAB_DIR=/path/to/matlab/runtime/directory
              ./matlab_exe $MATLAB_DIR <<args>>
            num_cores: 1
            parallel_mode: null

`dream_3D_env`
~~~~~~~~~~~~~~

Two executables are required:

* `dream_3D_runner`: this is the pipeline runner which processes a pipeline.json file.
* `python_script`: this is used to generate the `pipeline.json` file using a Python script.

Example environment definition - Linux/MacOS
--------------------------------------------

.. code-block:: yaml

  - name: dream_3D_env
    executables:
      - label: dream_3D_runner
        instances:
          - command: /path/to/DREAM3D-directory/bin/PipelineRunner
            num_cores: 1
            parallel_mode: null
      - label: python_script
        instances:
          - command: python "<<script_path>>" <<args>>
            num_cores: 1
            parallel_mode: null

Example environment definition - Windows
----------------------------------------

.. code-block:: yaml

  - name: dream_3D_env
    executables:
      - label: dream_3D_runner
        instances:
          - command: "& 'C:\\path\\to\\DREAM3D-directory\\PipelineRunner.exe'"
            num_cores: 1
            parallel_mode: null
      - label: python_script
        instances:
          - command: python "<<script_path>>" <<args>>
            num_cores: 1
            parallel_mode: null


`defdap_env`
~~~~~~~~~~~~

- The included DefDap scripts currently work only with DefDAP version 0.93.4 and up to Numpy version 1.23.5.

`damask_parse`
~~~~~~~~~~~~~~

We used our CentOS docker image (https://github.com/orgs/hpcflow/packages/container/package/centos7-poetry) to produce a "relocatable" conda environment for the `damask_parse` MatFlow environment, using conda-pack. Using the CentOS image is required because of glibc compatibilities.

In the container:

* Install Miniconda via the bash installation script: https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html
* Initialise conda for use in the shell: :code:`conda init`
* Reload .bashrc: :code:`source ~/.bashrc`
* Install conda pack: :code:`conda install conda-pack`
* Create a new conda environment that contains :code:`damask-parse` and :code:`matflow`: :code:`conda create -n matflow_damask_parse_v3a7_env python=3.10`
* Install :code:`libGL` for VTK (required by the damask python package) :code:`yum install mesa-libGL`
* Activate the environment: :code:`conda activate matflow_damask_parse_v3a7_env`
* Add packages via pip: :code:`pip install matflow-new damask-parse`
* Deactivate the environment: :code:`conda deactivate`
* Pack the environment into a tarball: :code:`conda pack matflow_damask_parse_v3a7_env`
* Save the resulting compressed file outside of the container and transfer to the target machine

On the target machine:

* Unpack the environment:
  
  .. code-block:: bash
    
      mkdir matflow_damask_parse_v3a7_env
      tar -xzf matflow_damask_parse_v3a7_env.tar.gz -C matflow_damask_parse_v3a7_env

* Activate the environment: :code:`source matflow_damask_parse_v3a7_env/bin/activate`
* Run: :code:`conda-unpack`
* The environment can now be activated as normal using the :code:`source` command above.

Resources:

* https://conda.github.io/conda-pack/index.html
* https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html
* https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands
* https://github.com/conda/conda-pack/issues/160


Example environment definition
------------------------------

.. code-block:: yaml

    name: damask_parse_env
    setup: |    
      conda activate matflow_damask_parse_env
    executables:
      - label: python
        instances:
          - command: python
            num_cores: 1
            parallel_mode: null

`damask`
~~~~~~~~

Example environment definition
------------------------------

.. code-block:: yaml

    name: damask_env
    executables:
      - label: damask_grid
        instances:
          - command: docker run --rm --interactive --volume ${PWD}:/wd --env OMP_NUM_THREADS=1 eisenforschung/damask-grid:3.0.0-alpha7
            parallel_mode: null
            num_cores: 1
