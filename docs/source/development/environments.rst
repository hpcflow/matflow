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



`dream_3D_env`
~~~~~~~~~~~~~~

Two executables are required:

* `dream_3D_runner`: this is the pipeline runner which processes a pipeline.json file.
* `python_script`: this is used to generate the `pipeline.json` file using a Python script.




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
* Add packages via pip: :code:`pip install matflow damask-parse`
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
