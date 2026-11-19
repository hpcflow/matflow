.. jinja:: first_ctx

    Secrets
    -------

    {{ app_name }} can store secrets like usernames and passwords for third party services that require authentication.

    .. warning::
        
        Do not store secrets like usernames, passwords, and API keys within environment definitions. These definitions are copied into workflow metadata and so would be distributed with the workflow, if shared.

    Managing secrets
    ~~~~~~~~~~~~~~~~

    Secrets can be retrieved, set, and deleted as follows:

    .. tab-set::

        .. tab-item:: CLI

            Using the ``manage secrets`` sub-command in the |app_name| CLI, we can set a new secret like this:
        
            .. code-block:: console

                {{ app_package_name }} manage secrets set KEY VALUE

            To update the value of an existing secret, use the `--overwrite` flag:

            .. code-block:: console

                {{ app_package_name }} manage secrets set KEY VALUE --overwrite

            Items can be retrieved like this:

            .. code-block:: console

                {{ app_package_name }} manage secrets get KEY

            All currently defined secrets can be listed like this (with values hidden):

            .. code-block:: console

                {{ app_package_name }} manage secrets list

            To show all secret keys and their secret values, use the `--values` or `-v` option:

            .. code-block:: console

                {{ app_package_name }} manage secrets list --values

            To delete a secret:
            
            .. code-block:: console

                {{ app_package_name }} manage secrets delete KEY


        .. tab-item:: Python API

            .. code-block:: python
                
                import {{ app_module }} as {{ app_docs_import_conv }}

                # set the value of the `KEY` secret:
                {{ app_docs_import_conv }}.set_secret("KEY", "VALUE")

                # update the existing value of the `KEY` secret:
                {{ app_docs_import_conv }}.set_secret("KEY", "VALUE", overwrite=True)

                # retrieve a secret's value:
                print({{ app_docs_import_conv }}.get_secret("KEY"))

                # print all secret keys:
                {{ app_docs_import_conv }}.print_secrets()

                # print all secrets keys and their secret values:
                {{ app_docs_import_conv }}.print_secrets(include_values=True)

                # delete a secret
                {{ app_docs_import_conv }}.delete_secret("KEY")

    .. note::

        {{ app_name }} does not encrypt secrets as there is not a straightforward way to do so across all platforms, and for typical use cases (like running on HPC systems). Instead, {{ app_name }} stores secrets in a file with appropriate permissions set such that the file can only be read (or written to) by the current user. The secrets file is stored within the app's user data directory.

    Using secrets
    ~~~~~~~~~~~~~

    You can expose secrets as shell environment variables by specifying a list of secret keys (i.e. the names of the secrets you wish to include) in the environment definition, via the ``secrets`` argument. (As stated above, secrets values should not be stored within environment definition ``setup`` or ``command`` blocks.). For example, such an environment definition might look like this in YAML:

    .. code-block:: yaml

        - name: my_env
          secrets:
            - MY_SECRET
          executables:
            - label: my_executable
              instances:
                - command: my_executable.exe
                  parallel_mode: null
                  num_cores:
                    start: 1
                    stop: 4

    where ``MY_SECRET`` is the key to a secret stored by |app_name|, such that if you run ``{{ app_package_name }} manage secrets get MY_SECRET``, the secret's value would be printed.
