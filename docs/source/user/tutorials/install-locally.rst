.. jinja:: first_ctx

  ######################################################
  Tutorial: Install {{ app_name }} on your local machine
  ######################################################

  This tutorial will guide you through the process of installing {{ app_name }} on your local machine (laptop or desktop), creating and running some example workflows.
  This tutorial is intended for users who are new to {{ app_name }} and want to understand the setup and terminology.
  Most workflows used in your research will be too large to run on your local machine,
  but this tutorial will help you understand the basics of how {{ app_name }} works before you move to setting it up on a cluster.

  Step 1: Set up a Python environment
  ====================================

  The first step is to set up a Python environment on your local machine.

  **If you have not already installed Python**, you can download the latest version of Python from the `Python website <https://www.python.org/downloads/>`_.
  Follow the instructions on the website for your operating system.

  **If you have already installed Python**, you can check the version of Python installed on your machine by running
  ``python --version``.

  Check that your version matches one of the ones supported by {{ app_name }}.
  You can find the supported Python versions in the :ref:`installation instructions <def_python_versions>`.
  If your version is not supported, you may need to update to a newer version of Python.

  Next, you will need to set up a virtual environment to install {{ app_name }} and its dependencies.
  A virtual environment is a self-contained directory that contains a particular version of Python with the all libraries and dependencies you install.
  This allows you to install packages without affecting the system Python installation or other projects,
  and when you run a command inside that environment you are certain which versions are being used.

  To create a virtual environment, you can use the `venv <https://docs.python.org/3/library/venv.html>`_ module that comes with Python.
  Follow the instructions in the `Python Packaging Guide <https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments>`_ to create and activate a virtual environment.
  The convention is to call your environment ``.venv``, but you can call it whatever you like.
  We recommend calling it ``{{ app_module }}-env`` to make it clear that this environment is for {{ app_name }}.

  When the environment is activated, you should see the name of the virtual environment in brackets in your terminal prompt.
  Whenever you are working with Python in the terminal, you can check if it is accessing your system installation of Python or a virtual environemnt by running ``which python``.
  This will print out the path to the Python executable it is calling, so currently the path should be inside the virtual environment folder you just created.

  Step 2: Install {{ app_name }}
  ==============================

  Once you have created and activated a Python environment (check for the environment name in brackets in your prompt), you can install {{ app_name }} using pip by running
  ``pip install --pre {{ dist_name }}``.

  This will install the latest version of {{ app_name }} from the Python Package Index (PyPI), and all the dependencies it needs.
  Once it has finished, check that {{ app_name }} has been installed correctly by running
  ``{{ app_module }} --version``.

  This should print the version of {{ app_name }} that you have installed.
  If you see an error message saying it doesn't recognise "{{ app_module }}" as a command name, check that you have activated the correct virtual environment and that you have installed {{ app_name }} correctly.

  Step 3: Configure {{ app_name }} for your machine
  =================================================

  Now that you have installed {{ app_name }}, you need to set it up for your machine.
  {{ app_name }} uses a configuration file to store information about the machine you are running on, such as the number of cores available and the locations of important folders.
  This will be stored in your user home directory so that it can be read by {{ app_name }} no matter what project you are working on, or what folder you are working in.

  The configuration file is called ``config.yaml`` and is stored in the ``~/.{{ app_module }}-new`` directory (``~`` is a shortcut for your user home directory, and the ``.`` at the start of the filename indicates that this is a hidden folder).
  When you first install {{ app_name }}, the directory and file will not exist.
  You can either make it yourself or run ``{{ app_module }} init`` to create the ``~/.{{ app_module }}-new`` directory and a ``config.yaml`` file inside it with the minimum default settings.

  Step 4: Define workflow
  ========================

  Now that you have installed {{ app_name }} and set up the configuration file, you can start defining :ref:`workflows<def_workflow>`.
  {{ app_name }} uses a YAML file to define the workflow, which is a text file that describes the steps in the workflow and the parameters for each step.
  The workflow file is stored in the directory where you want to run the workflow.

  Step 5: Run the workflow
  ========================

  Once you have defined the workflow, you can run it using the command
  ``{{ app_module }} go <workflow_file>``.

  Step 6: Monitor the workflow
  ============================

  You can monitor the progress of the workflow by running
  ``{{ app_module }} show``.
  This will show you the status of each step in the workflow, including whether it is running, completed, or failed.
  You can also view the log files generated during the run by running
  ``{{ app_module }} logs <workflow_file>``.
  This will show you the log files for each step in the workflow, including any error messages or warnings that were generated during the run.


  Step 6: View the results
  ========================

  Once the workflow has finished running, you can view the results in the output directory specified in the workflow file.
  The output directory will contain the results of each step in the workflow, as well as any log files generated during the run.
