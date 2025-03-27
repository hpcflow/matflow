.. jinja:: first_ctx

    Meta-tasks
    ----------

    Meta-tasks allow us to group multiple tasks together so they can be referenced as a whole. Within a YAML workflow template, for example, this allows us to invoke a group of tasks multiple times without having to write out the task parametrisations multiple times. There are three parts to using a meta-task: 

    1. A *meta-task schema* must be defined in the template components (this could be built in to {{ app_package_name }}, or could be included in a separate template components file, or could be included within a ``template_components`` block of the YAML workflow template file). A meta-task schema is like a normal task schema, in that is has an objective (indicating what it aims to do), and a list of input and output parameters. However, unlike a normal task schema, a meta-task schema does not need an implementation, since this will be provided by the constitutive tasks of the meta-task.

    2. A *meta-task* must be defined in the workflow template, which maps a meta-task objective to a list of tasks that should be invoked, in order, when the meta-task is called within the task list of the workflow template.

    3. The meta-task is included in the workflow template task list (potentially multiple times).

    Simple example
    ~~~~~~~~~~~~~~

    Below is a complete workflow template (in the YAML format) that includes a meta-task schema called ``system_analysis``. This meta-task has a single input, ``p2``, and a single output ``p4``, and is comprised of two tasks ``s1`` and ``s2``. Note that these task schemas must provide inputs and outputs that are compatible with the meta-task. In this case, the parameter ``p2`` of the meta task is also an input of the task ``s1``, and the task ``s2`` has an output ``p4``, which is an output parameter of the meta task. Also note that the meta task is referenced by its objective in the ``tasks`` list of the workflow template, in the same way that normal tasks are referenced. In this case, the first and third items in the ``tasks`` list are normal tasks, but the second item is a reference to the ``system_analysis`` meta task. All tasks in this example are implemented using simple shell commands that sum two numbers together. Finally, note that the meta task is parametrised via the constitutive tasks within the ``meta_tasks`` block.

    .. code-block:: yaml

        template_components:
          task_schemas:
            - objective: s0
              inputs: 
                - parameter: p1
              outputs:
                - parameter: p2
              actions:
                - commands:
                  - command: echo "$((<<parameter:p1>> + 1))"
                    stdout: <<int(parameter:p2)>>

            - objective: s1
              inputs: 
                - parameter: p2
                - parameter: p2b
              outputs:
                - parameter: p3
              actions:
                - commands:
                  - command: echo "$((<<parameter:p2>> + <<parameter:p2b>>))"
                    stdout: <<int(parameter:p3)>>

            - objective: s2
              inputs: 
                - parameter: p3
              outputs:
                - parameter: p4
              actions:
                - commands:
                  - command: echo "$((<<parameter:p3>> + 1))"
                    stdout: <<int(parameter:p4)>>

            - objective: s3
              inputs: 
                - parameter: p4
              outputs:
                - parameter: p5
              actions:
                - commands:
                  - command: echo "$((<<parameter:p4>> + 1))"
                    stdout: <<int(parameter:p5)>>

          meta_task_schemas:
            - objective: system_analysis
              inputs:
                - parameter: p2
              outputs:
                - parameter: p4

        meta_tasks:
          system_analysis:
            - schema: s1
              inputs:
                p2b: 220
            - schema: s2
          
        tasks:
          - schema: s0
            inputs:
              p1: 100
          - schema: system_analysis
          - schema: s3

    Meta-tasks using the Python API
    ###############################

    Meta-tasks are most useful when defining workflow templates via YAML or JSON files or strings, because they allow us to repeat a task parametrisation without requiring us to write out that parametrisation multiple times. When using the Python API, we can use Python variables to the same effect, so meta-tasks are not as useful. However, for the sake of completeness, the above example could be written using the Python API like so:

    .. code-block:: python

        # normal task schemas:
        s0 = hf.TaskSchema(
            objective="s0",
            inputs=[hf.SchemaInput("p1")],
            outputs=[hf.SchemaOutput("p2")],
            actions=[
                hf.Action(
                    commands=[
                        hf.Command(
                            command='echo "$((<<parameter:p1>> + 1))"',
                            stdout="<<int(parameter:p2)>>",
                        )
                    ]
                )
            ],
        )
        s1 = hf.TaskSchema(
            objective="s1",
            inputs=[hf.SchemaInput("p2")],
            outputs=[hf.SchemaOutput("p3")],
            actions=[
                hf.Action(
                    commands=[
                        hf.Command(
                            command='echo "$((<<parameter:p2>> + 1))"',
                            stdout="<<int(parameter:p3)>>",
                        )
                    ]
                )
            ],
        )
        s2 = hf.TaskSchema(
            objective="s2",
            inputs=[hf.SchemaInput("p3")],
            outputs=[hf.SchemaOutput("p4")],
            actions=[
                hf.Action(
                    commands=[
                        hf.Command(
                            command='echo "$((<<parameter:p3>> + 1))"',
                            stdout="<<int(parameter:p4)>>",
                        )
                    ]
                )
            ],
        )
        s3 = hf.TaskSchema(
            objective="s3",
            inputs=[hf.SchemaInput("p4")],
            outputs=[hf.SchemaOutput("p5")],
            actions=[
                hf.Action(
                    commands=[
                        hf.Command(
                            command='echo "$((<<parameter:p4>> + 1))"',
                            stdout="<<int(parameter:p5)>>",
                        )
                    ]
                )
            ],
        )

        # meta-task schema:
        ms = hf.MetaTaskSchema(
            objective="system_analysis",
            inputs=[hf.SchemaInput("p2")],
            outputs=[hf.SchemaOutput("p4")],
        )

        # meta-task:
        m1 = hf.MetaTask(
            schema=ms,
            tasks=[
                hf.Task(schema=s1),
                hf.Task(schema=s2),
            ],
        )

        # workflow template tasks list, include the meta-task above:
        tasks = [
            hf.Task(schema=s0, inputs={"p1": 100}),
            m1,
            hf.Task(schema=s3),
        ]

        # persistent workflow object:
        wk = hf.Workflow.from_template_data(
            template_name="meta_task_workflow",
            tasks=tasks,
        )

    Customising task parametrisation
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Sometimes it can be useful to modify the parametrisation of a meta-task's constitutive tasks each time the meta-task is used within a workflow's task list. To do this, all available task parametrisation keys can be specified under a mapping key corresponding to the individual task schemas within the meta-task. For example, in the below workflow template, the ``system_analysis`` meta-task has one constitutive task, named ``s1``. To apply customised ``inputs``, ``resources`` and ``sequences`` (i.e. different from any specified under the ``meta_tasks`` block), we can use these keys as normal within the ``tasks`` list item keys, but their values must be specified under an ``s1`` key. Any inputs specified will *update* those specified in the ``meta_tasks`` list. In other words, inputs values for other inputs types that are provided in the ``meta_tasks`` block will remain. However, for all other keys (e.g. ``resources`` and ``sequences```), data written in the ``task list`` will overwrite any specified in the ``meta_tasks`` list.

    .. code-block:: yaml

        name: test_metatask_multi_element_sets_custom_parametrisation
        template_components:
          task_schemas:
            - objective: s1
              inputs: 
                - parameter: p1
                - parameter: p2
              outputs:
                - parameter: p3
              actions:
                - commands:
                  - command: echo "$((<<parameter:p1>> + <<parameter:p2>>))"
                    stdout: <<int(parameter:p3)>>

          meta_task_schemas:
            - objective: system_analysis
              inputs:
                - parameter: p1
                - parameter: p2
              outputs:
                - parameter: p3

        meta_tasks:
          system_analysis:
            - schema: s1
              inputs:
                p1: 100
                p2: 200
                
        tasks:
          - schema: system_analysis
            resources:
              s1: # applies to the schema `s1`
                any:
                  num_cores: 2          
            inputs:
              s1: # applies to the schema `s1`
                p1: 102
            sequences:
              s1: # applies to the schema `s1`
                - path: inputs.p2
                  values: [300, 301]
