Configuration how-tos
---------------------

Get and set config items
~~~~~~~~~~~~~~~~~~~~~~~~

.. jinja:: first_ctx

    The configuration file is used to store settings that control the behavior, 
    such as the machine name, the log level, and the location of the template component source files. 
    These can also be set and retrieved using the CLI or Python API.

    .. tab-set::

        .. tab-item:: CLI

            Using the config sub-command in the |app_name| CLI, we can get configuration items like this:
        
            .. code-block:: console

                {{ app_package_name }} config get machine

            Items can be set like this:

            .. code-block:: console

                {{ app_package_name }} config set machine my-machine-name

        .. tab-item:: Python API

            In the Python API, we can interact with the |app_name| configuration as below. Note that we must call :meth:`config.save <hpcflow.sdk.config.config.Config.save>` to make the config changes persistent, otherwise any changes made will only be temporary.

            .. code-block:: python

                import {{ app_module }} as {{ app_docs_import_conv }}

                # print the value of the `machine` item:
                print({{ app_docs_import_conv }}.config.machine)

                # set the value of the `machine` item:
                {{ app_docs_import_conv }}.config.machine = "my-machine-name"

                # optionally save the changes to the config file:
                {{ app_docs_import_conv }}.config.save()

            If you want to change a configuration item temporarily (just for the current session), you can also provide configuration item values to `load_config` and `reload_config`, like this:

            .. code-block:: python

                import {{ app_module }} as {{ app_docs_import_conv }}

                # modify the log console level just for this session:
                {{ app_docs_import_conv }}.load_config(log_console_level="debug")

    See the configuration :ref:`reference documentation <reference/config_file:Configuration file>` for a listing of configurable items.

    Reset the config to default values
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Usually, when |app_name| is invoked, the first thing it does is load the configuration file. However, if you have updated to a newer, incompatible version, sometime your existing configuration file will fail validation. In this case, you can reset the configuration file to its default value.

.. jinja:: first_ctx

    .. tab-set::

        .. tab-item:: CLI

            Reset configuration to the default value by running the following CLI command:
            
            .. code-block:: console

                {{ app_package_name }} manage reset-config

        .. tab-item:: Python API

            Within the Python API, the config can be reset like this:

            .. code-block:: python

                import {{ app_module }} as {{ app_docs_import_conv }}

                {{ app_docs_import_conv }}.reset_config()

    .. warning::
        
        Resetting the configuration will remove any custom configuration you had, including pointers to template component source files (like environment source files). If you want to make a copy of the old file before resetting, you can retrieve its file path like this: :code:`{{ app_package_name }} manage get-config-path`, with the CLI, or, :code:`{{ app_docs_import_conv }}.get_config_path()`, with the Python API.

Clear the known-submissions file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. jinja:: first_ctx

    The known-submissions file is used to track running and recent workflow, and is used by the :code:`{{ app_docs_import_conv }}.show` / :code:`{{ app_package_name }} show` command. Sometimes you might need to clear this file, which can be done like this:

    .. tab-set::

        .. tab-item:: CLI
            
            .. code-block:: console

                {{ app_package_name }} manage clear-known-subs

        .. tab-item:: Python API
            
            Within the Python API, the equivalent command is:

            .. code-block:: python

                import {{ app_module }} as {{ app_docs_import_conv }}

                {{ app_docs_import_conv }}.clear_known_submissions_file()
