:orphan:

.. _install:

.. jinja:: first_ctx

    ############
    Installation
    ############

    There are two ways of using {{ app_name }}:

    * The {{ app_name }} command-line interface (CLI)
    * The {{ app_name }} Python package

    Both of these options allow workflows to be designed and executed. The {{ app_name }} CLI
    is recommended for beginners and strongly recommended if you want to
    run {{ app_name }} on a cluster. The Python package allows workflows to be
    designed and explored via the Python API and is recommended for users
    comfortable working with Python. If you are interested in contributing to
    the development of {{ app_name }}, the Python package is the place to start.

    The CLI and the Python package can be used simultaneously.

    Using pip
    ==========================

    The recommended way to install MatFlow is to
    use pip to install the Python package from PyPI::

      pip install {{ dist_name }}

    This installs the python package, which also gives the CLI version of MatFlow.



    **************
    Release notes
    **************

    Release notes for this version ({{app_version}}) are `available on GitHub <https://github.com/{{ github_user }}/{{ github_repo }}/releases/tag/v{{ app_version }}>`_.
    Use the version switcher in the top-right corner of the page to download/install other versions.


    Alternative installation methods
    ================================
    Although *not currently recommended*,
    advanced users may wish to use one of the :ref:`alternative installation methods <alternative_install>`.


    #############
    Configuration
    #############

    MatFlow uses a config file to control details of how it executes workflows.
    A :ref:`default config file <default_config>` will be created the first time you submit a workflow.
    This will work without modification on a personal machine,
    however if you are using MatFlow on HPC you will likely need to make some
    modifications to describe the job scheduler, and settings for multiple cores,
    and to point to your MatFlow environments file.

    `Some examples <https://github.com/hpcflow/matflow-configs>`_ are given
    for the University of Manchester's CSF.

    The path to your config file can be found using ``matflow manage get-config-path``,
    or to open the config file directly, use ``matflow open config``.

    #############
    Environments
    #############

    Matflow has the concept of environments, similar to python virtual environments.
    These are required so that tasks can run using the specific software they require.
    Your MatFlow environments must be defined in your environments (YAML) file before MatFlow
    can run workflows, and this environment file must be pointed to in the config file
    via the ``environment_sources`` key.
    Once this has been done,
    your environment file can be be opened using ``matflow open env-source``.

    You may wish to modify this template environments file for your own computer,
    in particular the ``setup`` sections for each environment.

    .. code-block:: yaml

	- name: damask_parse_env
	  setup: |
	    source /full/path/to/.venv/bin/activate
	  executables:
	    - label: python_script
	      instances:
		- command: python <<script_name>> <<args>>
		  num_cores:
		    start: 1
		    stop: 32
		  parallel_mode: null

	- name: formable_env
	  setup: |
	    source /full/path/to/.venv/bin/activate
	  executables:
	    - label: python_script
	      instances:
		- command: python <<script_name>> <<args>>
		  num_cores:
		    start: 1
		    stop: 32
		  parallel_mode: null

	- name: defdap_env
	  setup: |
	    source /full/path/to/.venv/bin/activate
	  executables:
	    - label: python_script
	      instances:
		- command: python <<script_name>> <<args>>
		  num_cores:
		    start: 1
		    stop: 32
		  parallel_mode: null

	- name: damask_env
	  setup: |
	    module load mpi/intel-18.0/openmpi/4.1.0
	    IMG_PATH=/full/path/to/DAMASK-docker-images/damask-grid_3.0.0-alpha7.sif
	    export HDF5_USE_FILE_LOCKING=FALSE
	  executables:
	    - label: damask_grid
	      instances:
		- command: singularity run $IMG_PATH
		  num_cores: 1
		  parallel_mode: null
		- command: mpirun -n $NSLOTS singularity run $IMG_PATH
		  num_cores:
		    start: 2
		    stop: 32
		  parallel_mode: null

	- name: matlab_env
	  setup: |
	    module load apps/binapps/matlab/R2019a
	    module load apps/binapps/matlab/third-party-toolboxes/mtex/5.3
	  executables:

	    - label: compile_mtex
	      instances:
		- command: compile-mtex <<script_name>> <<args>>
		  num_cores: 1
		  parallel_mode: null

	    - label: run_compiled_mtex
	      instances:
		- command: ./run_<<script_name>>.sh $MATLAB_HOME <<args>>
		  num_cores: 1
		  parallel_mode: null

	    - label: run_mtex
	      instances:
	      - command: matlab -singleCompThread -batch "<<script_name_no_ext>> <<args>>"
		num_cores: 1
		parallel_mode: null
	      - command: matlab -batch "<<script_name_no_ext>> <<args>>"
		num_cores:
		  start: 2
		  stop: 16
		parallel_mode: null

	- name: python_env
	  executables:
	    - label: python_script
	      instances:
		- command: python <<script_name>> <<args>>
		  num_cores:
		    start: 1
		    stop: 32
		  parallel_mode: null

	- name: dream_3D_env
	  executables:
	  - label: dream_3D_runner
	    instances:
	    - command: /full/path/to/dream3d/DREAM3D-6.5.171-Linux-x86_64/bin/PipelineRunner
	      num_cores: 1
	      parallel_mode: null
	  - label: python_script
	    instances:
	      - command: python <<script_name>> <<args>>
		num_cores: 1
		parallel_mode: null
