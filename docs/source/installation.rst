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
