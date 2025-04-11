################################################
Tutorial: Install MatFlow on your local machine
################################################

This tutorial will guide you through the process of installing MatFlow on your local machine (laptop or desktop), creating and running some example workflows.
This tutorial is intended for users who are new to MatFlow and want to understand the setup and terminology.
Most workflows used in your research will be too large to run on your local machine, 
but this tutorial will help you understand the basics of how MatFlow works before you move to setting it up on a cluster.

Step 1: Set up a Python environment
====================================

The first step is to set up a Python environment on your local machine.

**If you have not already installed Python**, you can download the latest version of Python from the `Python website <https://www.python.org/downloads/>`_.
Follow the instructions on the website for your operating system.

**If you have already installed Python**, you can check the version of Python installed on your machine by running
``python --version``.

Check that your version matches one of the ones upported by MatFlow. 
You can find the supported versions in the `MatFlow PyPI package description <https://pypi.org/project/matflow-new/>`_.
.. TODO: when matflow-new PR #320 is merged this can point to the install page instead of the PyPI package description.
If your version is not supported, you may need to update to a newer version of Python.

Next, you will need to set up a virtual environment to install MatFlow and its dependencies.
A virtual environment is a self-contained directory that contains a particular version of Python with the all libraries and dependencies you install.
This allows you to install packages without affecting the system Python installation or other projects,
and when you run a command inside that environment you are certain which versions are being used.

To create a virtual environment, you can use the `venv <https://docs.python.org/3/library/venv.html>`_ module that comes with Python.
Follow the instructions in the `Python Packaging Guide <https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#create-and-use-virtual-environments>`_ to create and activate a virtual environment.
The convention is to call your environment ``.venv``, but you can call it whatever you like.
We recommend calling it ``matflow-env`` to make it clear that this environment is for MatFlow.

When the environment is activated, you should see the name of the virtual environment in brackets in your terminal prompt.
Whenever you are working with Python in the terminal, you can check if it is accessing your system installation of Python or a virtual environemnt by running ``which python``.
This will print out the path to the Python executable it is calling, so currently the path should be inside the virtual environment folder you just created.

Step 2: Install MatFlow
=======================

Once you have created and activated a Python environment (check for the environment name in brackets in your prompt), you can install MatFlow using pip by running
``pip install matflow-new``.

This will install the latest version of MatFlow from the Python Package Index (PyPI), and all the dependencies it needs.
Once it has finished, check that MatFlow has been installed correctlyby running
``matflow --version``.

This should print the version of MatFlow that you have installed.
If you see an error message saying it doesn't recognise "matflow" as a command name, check that you have activated the correct virtual environment and that you have installed MatFlow correctly.

Step 3: Configure MatFlow for your machine
========================================

Now that you have installed MatFlow, you need to set it up for your machine.
MatFlow uses a configuration file to store information about the machine you are running on, such as the number of cores available and the locations of important folders.
This will be stored in your user home directory so that it can be read by MatFlow no matter what project you are working on, or what folder you are working in.

The configuration file is called `config.yml` and is stored in the `~/.matflow-new` directory (`~` is a shortcut for your user home directory, and the `.` at the start of the filename indicates that this is a hidden folder).
When you first install MatFlow, the directory and file will not exist.
You can either make it yourself or run ``matflow init`` to create the ``~/.matflow-new`` directory and a ``config.yml`` file inside it with the minimum default settings.
