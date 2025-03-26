Demo workflows
----------------
A good way to get started with MatFlow is to run one of the built-in workflows.
This will also test your installation, configuration, and some of your environments.

Submit a workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. jinja:: first_ctx

    MatFlow comes with some demo workflows, which can be listed using

    .. code-block:: console

        matflow demo-workflow --list
    

    We can run the following command to copy the in-built workflow file to the current directory
    (note the final dot at the end),
    
    .. code-block:: console
        
        matflow demo-workflow copy modify_volume_element_grid_size .

    which we can then use to submit the workflow.
    
    .. code-block:: console

        matflow go modify_volume_element_grid_size.yaml
    
    This small workflow should complete in less than 30s.
    Note that there is also a convenience shortcut for the demo workflows which combines
    the copy-then-submit pattern we saw above:    

    .. code-block:: console

        matflow demo-workflow go modify_volume_element_grid_size

    However, in general workflows would first be created in a yaml file which is then submitted using 
    ``matflow go WORKFLOW_FILE``.

Check the status of a workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After submitting a workflow, you can check whether it has run successfully using

.. code-block:: console
    
    matflow show -f

For clarification of the output, a legend can be shown using 

.. code-block:: console

    matflow show --legend


Cancel a workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you might want to cancel a workflow that is running. Use

.. code-block:: console
    
    matflow cancel WORKFLOW_REF

where ``WORKFLOW_REF`` is either the path to the workflow directory, 
or the ID of the workflow displayed by ``matflow show``.
