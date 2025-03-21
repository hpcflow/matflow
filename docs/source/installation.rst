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

    ******************
    {{ app_name }} CLI
    ******************

    The {{ app_name }} CLI can be installed on Linux, macOS, and Windows through a terminal
    or shell prompt:

    .. tab-set::

        .. tab-item:: Linux/macOS

            Open a terminal, paste the command shown below and press enter.

            .. code-block:: bash

                (touch tmp.sh && curl -fsSL https://raw.githubusercontent.com/hpcflow/install-scripts/main/src/install-{{ app_package_name }}.sh > tmp.sh && bash tmp.sh --prerelease --path --univlink) ; rm tmp.sh

        .. tab-item:: Windows

            Open a Powershell terminal, paste the command shown below and press enter.

            .. code-block:: powershell

                & $([scriptblock]::Create((New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/hpcflow/install-scripts/main/src/install-{{ app_package_name }}.ps1'))) -PreRelease -UnivLink

    .. admonition:: What does this script do?
        :class: note dropdown
        
        The above command downloads a `script from the {{ app_name }} GitHub repository <https://github.com/hpcflow/install-scripts/blob/5b47fa287aaef8d4b7c7970116f13b72b674ed77/src/install-matflow.sh>`_ and runs it. The script does the following:

        #. It downloads the latest prerelease version of {{ app_name }} zip archived in a single folder.
        #. The archive is extracted and the folder placed in an accessible location. The location depends on the operating system. In Linux it is ``~/.local/share/{{ app_package_name }}``. In macOS it is ``~/Library/Application Support/{{ app_package_name }}``. In Windows it is ``Username\AppData\Local\{{ app_package_name }}``.
        #. A symbolic link (Linux/macOS) or an alias pointing to the file is created. This allows {{ app_name }} to be run by entering a simple command.
        #. A command is added to ``.bashrc``/``.zshrc`` (linux/macOS) or the Powershell profile (Windows) that allows {{ app_name }} to be run from any folder.

        If the script detects that the version of {{ app_name }} it is trying to install is already there, it will stop 
        running and exit.

    To check if the installation was successful, run the following command in your terminal:

    .. code-block:: bash

        {{ app_name }} --version

    This should print the version of {{ app_name }} that was installed, and will give an error if the installation was not successful.


    .. hint::
      
      If you are installing {{ app_name }} on an HPC resource, check that you can connect
      to the internet first. You might need to load a proxy module, for example.

    *****************************
    {{ app_name }} Python package
    *****************************

    We recommend you `create a virtual Python environment <https://docs.python.org/3/tutorial/venv.html>`_ to work with MatFlow to separate versions for different projects and avoid dependency conflicts.
    Check that you have the correct environment activated by confirming that the name of the environment appears in brackets in your prompt.

    {{ app_name }} is compatible with Python versions {{ supported_python }}.
    We recommend using the newest version available to you.

    Using pip
    ==========================

    Use pip to install the Python package from PyPI::

      pip install {{ dist_name }}

    Using conda
    ===========

    Coming soon!

    ********************************
    Download CLI binaries (advanced)
    ********************************

    Binaries are available in two formats, corresponding to the two different formats that
    PyInstaller `can generate <https://pyinstaller.org/en/stable/usage.html#what-to-generate>`_:

    * A single executable file containing everything.
    * A folder containing an executable and supporting files.

    Click below to download the {{ app_name }} binary for your platform:

    .. raw:: html

        {{ download_links_table_html }}

    *************
    Release notes
    *************

    Release notes for this version ({{app_version}}) are `available on GitHub <https://github.com/{{ github_user }}/{{ github_repo }}/releases/tag/v{{ app_version }}>`_.
    Use the version switcher in the top-right corner of the page to download/install other versions.
