.. jinja:: first_ctx

    Loops
    -----

    Loops in {{ app_package_name }} can be used when you want to iterate over one or more parameters.

    .. admonition:: Loops versus sequences
      :class: hint

      If you simply want to run a task multiple times with potentially different parametrisations, you can do this with a sequence. Loops are used when there should exist some dependency between the different "repeats" (or iterations) of a given task (or subset of tasks).

    A basic loop workflow
    ~~~~~~~~~~~~~~~~~~~~~

    Consider a task schema that takes one input parameter, ``p1``, and outputs the same parameter, ``p1``, with it's value incremented by 1:

    .. code-block:: yaml

      objective: my_task
      inputs: 
        - parameter: p1
      outputs:
        - parameter: p1
      actions:
        - commands:
            - command: echo $(( <<parameter:p1>> + 1 ))
              stdout: <<int(parameter:p1)>>

    Note that this task schema's output parameter is the same as its input parameter. In other words, it is a parameter-modifying schema, with respect to the parameter ``p1``. This means if we use this schema in a workflow, we can define a loop that iterates the parameter ``p1``:

    .. code-block:: yaml

      loops:
        - name: my_loop
          tasks: [0]
          num_iterations: 2      
      tasks:
        - schema: my_task
          inputs:
            p1: 101

    In the example workflow template above, we define a loop called ``my_loop`` that loops over the task with index 0 (the only task, in this case) two times. Since no default value for the input parameter ``p1`` is provided in the task schema, we must provide a "local" value in the template. This value will be used for the first iteration of the loop, but for subsequent iterations, the ``p1`` input value will be sourced from the output of the previous iteration.

    This workflow will progress in the following way:
    
    ========  ====================  ==================  ===================
    Task      loop iteration index  ``p1`` input value  ``p1`` output value
    ========  ====================  ==================  ===================
    my_task   0                     101                 102
    my_task   1                     102                 103
    ========  ====================  ==================  ===================
