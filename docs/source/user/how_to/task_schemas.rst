Task schemas
------------

Action command strings
======================

An action command string, ``COMMAND_STRING``, determines what the action should actually run, and is specified within a task schema definition like this (where schema inputs/outputs have been omitted for brevity):

.. tab-set::

    .. tab-item:: YAML

        .. code-block:: yaml

            objective: t1
            inputs: ...
            outputs: ...
            actions:
              - environments:
                  any: python_env
                commands:
                  - command: COMMAND_STRING

    .. tab-item:: Python

        .. code-block:: python

            ts1 = hf.TaskSchema(
                objective="t1",
                inputs=...,
                outputs=...,
                actions=[
                    hf.Action(
                        environments=[hf.ActionEnvironment("python_env", scope="any")],
                        commands=[hf.Command("COMMAND_STRING")],
                    )
                ]
            )

Action command strings may contain the following variables:

- ``<<executable:EXE_NAME>>`` where ``EXE_NAME`` is the label of an environment executable that is defined within the action's environment.
- ``<<parameter:PARAM_NAME>>`` where ``PARAM_NAME`` is an input or output parameter type of the task schema that contains the action.
- ``<<args>>``, which corresponds to the list of items in the ``args`` attribute of the command, and will be formatted as a space-separated list.
- ``<<VAR_NAME:VAR_VALUE>>`` where ``VAR_NAME`` and ``VAR_VALUE`` correspond to items in the ``variables`` attribute of the command. This is used internally (when running scripts, for example, to pass information about the script name and path), but is typically not used when defining commands.

Parameter flow within task schemas
==================================

In addition to an actual implementation of the task, task schemas also define a mapping between input and output types. Within a task schema, multiple actions can use those inputs and outputs in different ways. For a simple example, a task schema with one input, ``p1``, and one output, ``p2``, might include a single action that consumes the schema input and produces the schema output:

.. tab-set::

    .. tab-item:: YAML

        .. code-block:: yaml
        
            objective: t1
            inputs:
              - parameter: p1
            outputs:
              - parameter: p2
            actions:
             - commands:
                 - command: echo $((<<parameter:p1>> + 1))
                   stdout: <<parameter:p2>>

    .. tab-item:: Python

        .. code-block:: python

            ts1 = hf.TaskSchema(
                objective="t1",
                inputs=[hf.SchemaInput("p1")],
                outputs=[hf.SchemaInput("p2")],
                actions=[
                    hf.Action(
                        commands=[
                            hf.Command(
                                command="echo $((<<parameter:p1>> + 1))",
                                stdout="<<parameter:p2>>"
                            )
                        ],
                    ),
                ],
            )

It is useful to understand the difference between task schema inputs and outputs, and action-level inputs and outputs. Task schema inputs and outputs are those parameters defined in the ``inputs`` and ``outputs`` attributes of the task schema. In particular, these are represented by the ``SchemaInput`` and ``SchemaOutput`` objects. ``SchemaInput`` objects, in their most basic form, simply point to a parameter type, e.g. ``p1``. However, they may also include other information, such as a default value, and whether the parameter can be used in multiple labelled forms, which is a useful facility when inputs of the same type that originate from different tasks (or element sets) should be distinguished.

As checked during task schema validation, it's a requirement that the schema-level inputs and outputs are compatible with the actions of the that task schema. This means that the constituent actions of the task schema consume and produce parameters in a way that is commensurate with their parent task schema. For example, in the simple case of a task schema that has a single action with a command string ``echo <<parameter:p1>>``, the task schema must include an schema input of the ``p1`` parameter type. Conversely, if the task schema includes an input ``p1``, then it must be consumed by one of the task schema's actions.

But what constitutes action-level inputs (or consumers) and outputs (or producers)? The simplest examples to demonstrate this are those seen above, where we define a command string that includes references to an input parameter (e.g. ``command="echo $((<<parameter:p1>> + 1))"``), and we use the ``stdout`` command attribute to map the shell standard output from the command string back to an output parameter (e.g. ``stdout="<<parameter:p2>>"``). So in this case the action level inputs and outputs are ``p1`` and ``p2`` respectively. However, action level inputs and outputs can also be defined from scripts. Currently, the action-level inputs and outputs for script actions are simply set to those from the task schema, but this will be refined in future to improve validation (since a script may not require all inputs of a task schema, and/or it might not generate all task schema outputs).

.. note::

   Don't worry about getting this wrong! |app_name| will tell you if you are trying to define a task schema whose actions are not compatible with the schema's inputs and outputs.

It's important to note that in the examples above, we use the substitution syntax ``<<parameter:INPUT_OR_OUTPUT_TYPE>>`` within the command string and the standard output string (``stdout``). We use the term ``parameter`` because we can reference both inputs and outputs within actions. We do this in the following example, where the task schema input ``p1`` is used in the first action to generate the task schema output ``p2``, but we additionally include a second action which uses (as an action-level input) the task schema output ``p2``:

.. tab-set::

    .. tab-item:: YAML

        .. code-block:: yaml

            objective: t1
            inputs:
            - parameter: p1
            outputs:
            - parameter: p2
            actions:
            - commands:
                - command: echo $((<<parameter:p1>> + 1))
                  stdout: <<parameter:p2>>
            - commands:
                - command: echo <<parameter:p2>> # note: schema output `p2` used as an action input

    .. tab-item:: Python

        .. code-block:: python

            ts1 = hf.TaskSchema(
                objective="t1",
                inputs=[hf.SchemaInput("p1")],
                outputs=[hf.SchemaInput("p2")],
                actions=[
                    hf.Action(
                        commands=[
                            hf.Command(
                                command="echo <<parameter:p1>>",
                                stdout="<<parameter:p2>>",
                            )
                        ]
                    ),
                    hf.Action(  # note: schema output `p2` used as an action input
                        commands=[
                            hf.Command(command="echo <<parameter:p2>>")
                        ]
                    ),
                ],
            )

Additionally, an action may output a parameter that is *not* a task schema output, as long as it is used as an input in a downstream action within the same task schema, as in this example, where the task schema converts its input ``p1`` to its output ``p3`` via an intermediate parameter ``p2``, which is an *output* of the first action, and an *input* of the second action:

.. tab-set::

    .. tab-item:: YAML

        .. code-block:: yaml

            objective: t1
            inputs:
            - parameter: p1
            outputs:
            - parameter: p3
            actions:
            - commands:
                - command: echo $((<<parameter:p1>> + 1))
                  stdout: <<parameter:p2>> # note: action output `p2` is not a schema-level output
            - commands:
                - command: echo $((<<parameter:p2>> + 1))
                  stdout: <<parameter:p3>>

    .. tab-item:: Python

        .. code-block:: python

            ts1 = hf.TaskSchema(
                objective="t1",
                inputs=[hf.SchemaInput("p1")],
                outputs=[hf.SchemaInput("p3")],
                actions=[
                    hf.Action(
                        commands=[
                            hf.Command(
                                command="echo $((<<parameter:p1>> + 1))",
                                stdout="<<parameter:p2>>",  # note: action output `p2` is not a schema-level output
                            )
                        ]
                    ),
                    hf.Action(
                        commands=[
                            hf.Command(
                                command="echo $((<<parameter:p2>> + 1))",
                                stdout="<<parameter:p3>>",
                            )
                        ]
                    ),
                ],
            )

Show information about a task schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the Python API, use the `info` property of a task schema object to print information such as the input and output parameters of the schema: :code:`TaskSchema.info`.
