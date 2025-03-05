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

      pip install {{ dist_name }}=="{{ app_version }}"

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
