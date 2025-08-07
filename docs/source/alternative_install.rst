:orphan:

.. _alternative_install:

.. jinja:: first_ctx

    #################################
    Alternative installation methods
    #################################

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
        
        The above command downloads a script from the {{ app_name }} GitHub repository and runs it. The script does the following:

        #. It downloads the latest prerelease version of {{ app_name }} zip archived in a single folder.
        #. The archive is extracted and the folder placed in an accessible location. The location depends on the operating system. In Linux it is ``/.local/share/{{ app_package_name }}``. In macOS it is ``~/Library/Application Support/{{ app_package_name }}``. In Windows it is ``Username\AppData\Local\{{ app_package_name }}``.
        #. A symbolic link (Linux/macOS) or an alias pointing to the file is created. This allows {{ app_name }} to be run by entering a simple command.
        #. A command is added to ``.bashrc``/``.zshrc`` (linux/macOS) or the Powershell profile (Windows) that allows {{ app_name }} to be run from any folder.

        If the script detects that the version of {{ app_name }} it is trying to install is already there, it will stop 
        running and exit.



    .. hint::
      
      If you are installing {{ app_name }} on an HPC resource, check that you can connect
      to the internet first. You might need to load a proxy module, for example.

    
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

    .. note::
      
      These two installation methods (via the shell command above or via manually downloading a binary executable) do not require any system dependencies like Python. However, the Linux versions do require a minimum version of the GNU C library (GLIBC). Currently, this minimum version is 2.28 (dated 2018). To find out which version of GLIBC you have, run ``ldd --version`` on your Linux machine.
