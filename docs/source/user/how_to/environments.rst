.. jinja:: first_ctx

    Environment how-tos
    -------------------

    Actions within {{ app_package_name }} task schemas can declare dependencies on particular {{ app_package_name }} environments. For a task schema to be used within a runnable workflow, these environments must be defined on the user's machine (e.g. in a YAML file, that is pointed to in the app configuration via the ``environment_sources`` key).

    Use multiple versions of the same software
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Disambiguating between {{ app_package_name }} environments with the same name
    #############################################################################

    Sometimes it's useful to have available multiple versions of the same external software. For example, when a new release of that software becomes available, you might like to use the new release whilst still having the older version available for comparison. To facilitate this in {{ app_package_name }}, environments can be associated with arbitrary key-value metadata, under the ``specifiers`` attribute. A common ``specifier`` would be a ``version`` string. When the environment is defined in a YAML file, it might look like this:

    .. code-block:: yaml

        - name: my_env
          specifiers:
            version: 1.2.3-alpha
          executables:
            - label: my_executable
              instances:
                - command: my_executable.exe
                  parallel_mode: null
                  num_cores:
                    start: 1
                    stop: 4
        
    In this way, we can then also define another ``my_env`` environment with a different version specifier (or any other simple arbitrary key-value pairs).

    Using environment specifiers within task schemas
    ################################################

    Environment specifiers within action environments
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Environment specifiers can be used within task schema actions to tell {{ app_package_name }} to only use an environment that matches those specifiers. For example, in this YAML task schema definition, the sole action requires an environment named ``my_env``.

    .. code-block:: yaml

        - objective: my_task
          inputs:
            - parameter: p1
          outputs:
            - parameter: p2
          actions:
            - environments:
                - scope:
                    type: any
                  environment: my_env                    
              commands:
                - command: echo "$((<<parameter:p1>> + 100))"
                  stdout: <<parameter:p2>>

    If we wanted to also match against specifiers, we could write the task schema like this, where the ``environment`` key within ``actions -> environments`` is now a mapping that must include the ``name`` key, and may include any arbitrary environment specifiers:

    .. code-block:: yaml

        - objective: my_task
          inputs:
            - parameter: p1
          outputs:
            - parameter: p2
          actions:
            - environments:
                - scope:
                    type: any
                  environment:
                    name: my_env
                    version: 1.2.3-alpha                        
              commands:
                - command: echo "$((<<parameter:p1>> + 100))"
                  stdout: <<parameter:p2>>

    However, usually it is not necessary to add specifiers to the task schema actions, because doing so restricts the applicability of the schema.

    Passing environment specifiers to action scripts
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    We can also pass the selected environment specifiers to a script using the ``script_pass_env_spec`` option that is available for actions, input-file generators, and output file parsers:

    .. code-block:: yaml

        - objective: my_task
          inputs:
            - parameter: p1
            - parameter: p2
          outputs:
            - parameter: p3
          actions:
            - script: <<script:path/to/script.py>>
              script_data_in: direct
              script_data_out: direct
              script_exe: python_script
              script_pass_env_spec: true # <--- include an argument `env_spec` with the inputs passed to the script
              environments:
                - scope:
                    type: any
                  environment: my_env

    In this example, the user might write their workflow template like this:


    .. code-block:: yaml

        tasks:
          - schema: my_task
            environments:
              my_env:
                version: 1.2.3-alpha
            inputs:
              p1: 101
              p2: 201
            
    ...in which case, the script's snippet function would receive an additional argument, ``env_spec``, with the value: ``{"name": "my_env", "version": "1.2.3-alpha"}``.

    Environment specifiers within script paths
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    .. _environment_specifiers_in_script_paths:

    Specifier values can be referenced within script paths within action definitions. For example, here we expect the script to exist in a sub-directory named according to the ``version`` specifier of the environment:

    .. code-block:: yaml

        - objective: my_other_task
          inputs:
            - parameter: p1
          outputs:
            - parameter: p2
          actions:
            - environments:
                - scope:
                    type: any
                  environment: my_other_env
              script: <<script:path/to/<<env:version>>/script.py>>                
              script_exe: python_script

    Defining environment presets
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Task schemas may include an ``environment_presets`` block, which should be a mapping between environment preset names, and a block of environment specifiers to use for that preset. In the example below, we define three environment presets. The first one, with only an empty string as its name, will be used by default if no environment preset is selected by the user in their workflow template (using the task ``env_preset`` key). The other two presets are named `stable` and `latest`, and correspond to using different versions the the environment ``my_other_env``.

    .. code-block:: yaml

        - objective: my_other_task
          inputs:
            - parameter: p1
          outputs:
            - parameter: p2
          actions:
            - environments:
                - scope:
                    type: any
                  environment: my_other_env
              script: <<script:path/to/<<env:version>>/script.py>>                
              script_exe: python_script
          environment_presets:
            "":
              my_other_env:
                version: "1.2.2"
            stable:
              my_other_env:
                version: "1.2.2"
            latest:
              my_other_env:
                version: 1.2.3-alpha

    Selecting environment specifiers within workflow templates
    ##########################################################

    For the end-user, there are multiple ways to select environment specifiers within their workflow template. At the task level, there are three ways to change which environments are selected:

    #. Using the ``env_preset`` key if available. This should be a string corresponding to the presets defined in the task schema via the ``environment_presets`` block (presets may not be defined, however!). For example: 

       .. code-block:: yaml

        tasks:
          - schema: my_other_task
            env_preset: stable
            inputs:
              p1: 101

    #. Using the ``environments`` key. This should be a block that maps environment names to specifiers that should be used when matching against the environments defined on the submit machine. For example, in the YAML workflow template below, we specify that for all actions of the ``my_other_task`` schema that require the ``my_other_env`` environment, we should choose the environment definition that has a ``version`` specifier set to ``"1.2.2"``.

       .. code-block:: yaml

          tasks:
            - schema: my_other_task
              environments:
                my_other_env:
                  version: "1.2.2"
              inputs:
                p1: 101
            
    #. Using the ``resources`` key. This provides the greatest degree of control, but is more verbose. Using the ``resources`` block, we can select different environment specifiers for different action scopes. In the example below we select the environment specifiers for the ``any`` action scope (which applies to all actions), but this could be refined if required:

       .. code-block:: yaml

          tasks:
            - schema: my_other_task
              resources:
                any:
                  environments:
                    my_other_env:
                      version: "1.2.2"
              inputs:
                p1: 101

    Environment specifiers can also be chosen at the workflow-template level, using similar keys:

    #. Using the template-level ``env_presets`` (note: plural) key. This should be a string or a list of strings. For each task, the first applicable template-level ``env_preset`` is applied if no task-level ``env_preset`` or ``environments`` are specified.

       .. code-block:: yaml

           env_presets: stable
           tasks:
             - schema: my_other_task
               inputs:
                 p1: 101

    #. Using the template-level ``environments`` key. This has the same format as the task-level ``environments`` key; namely a mapping between environment names and specifiers that should be used for that environment.

       .. code-block:: yaml
 
           environments:
             my_other_env:
               version: "1.2.2"              
           tasks:
             - schema: my_other_task
               inputs:
                 p1: 101

    #. Using the template-level ``resources`` key.

       .. code-block:: yaml
 
           resources:
             any:
               environments:
                 my_other_env:
                   version: "1.2.2"              
           tasks:
             - schema: my_other_task
               inputs:
                 p1: 101

    Environment specifiers within sequences
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Sequences can be used with paths ``env_preset`` and starting with ``environments`` (and ``resources.any.environments``) to generate multiple task elements that use different environment specifiers:
    
    .. code-block:: yaml
          
        tasks:
          - schema: my_other_task
            inputs:
              p1: 101 
            sequences:
              - path: env_preset
                values: 
                  - stable
                  - latest


    .. code-block:: yaml
          
        tasks:
          - schema: my_other_task
            inputs:
              p1: 101 
            sequences:
              - path: environments.my_other_env.version
                values: 
                  - "1.2.2"
                  - 1.2.3-alpha


    .. code-block:: yaml
          
        tasks:
          - schema: my_other_task
            inputs:
              p1: 101 
            sequences:
              - path: resources.any.environments.my_other_env.version
                values: 
                  - "1.2.2"
                  - 1.2.3-alpha
