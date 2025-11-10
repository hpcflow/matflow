.. jinja:: first_ctx

    Resources
    ---------

    Shell and scheduler arguments
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    When submitting a workflow, {{ app_name }} generates jobscripts that are submitted to
    the scheduler (if using one), or invoked directly (if not). Depending on how the
    scheduler is configured by your HPC administrators, you may need to add extra
    arguments to the shebang line of the jobscript. A shebang line usually looks something
    like this:

    .. code-block:: bash

        #!/bin/bash

    For example, on an HPC system, you might need to execute the job submission script via
    a bash *login* shell, meaning the first line in your jobscript should look like this:

    .. code-block:: bash
    
        #!/bin/bash --login

    To achieve this in {{ app_name }}, we can edit the configuration's `shells` block to
    look like this (note this excerpt is not a valid configuration on its own!):

    .. code-block:: yaml

      config:        
        shells:
          bash:
            defaults:
              executable_args: [--login]

    In this way, we ensure that wherever a ``bash`` shell command is constructed (such as
    when constructing the shebang line for a jobscript), ``--login`` will be appended to
    the shell executable command.

    We can also modify the shell executable path like this:

    .. code-block:: yaml

      config:
        shells:
          bash:
            defaults:
              executable: /bin/bash # /bin/bash is the default value
              executable_args: [--login]

    Additionally, there is one other place where the shell command is constructed, which
    is when {{ app_name }} invokes a commands file to execute a run. Typically, the shell
    command that you set in the above configuration change is sufficient. However, if you
    need these two scenarios to use different shell executables or executable arguments,
    you can additionally modify the scheduler's ``shebang_executable`` default value in
    the configuration (which overrides the ``shell`` configuration) like this:

    .. code-block:: yaml

      config:
        shells:
          bash:
            defaults:
              executable_args: [--login] # applied when invoking command files
        schedulers:
          sge:
            defaults:
              shebang_executable: [/path/to/bash/executable, arg_1, arg_2] # applied to scheduler shebang only

    Note that in this case (for ``shebang_exectuable``), the shell executable path must
    also be specified, in addition to the shell arguments.
