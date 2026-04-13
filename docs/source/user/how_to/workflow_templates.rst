Workflow templates how-tos
--------------------------

.. jinja:: first_ctx

    Loading workflow templates
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Workflow template YAML files can be loaded from remote sources by providing :func:`{{ app_package_name }}.app.WorkflowTemplate.from_YAML_file` with an fsspec URL. For example, to load a workflow template YAML file from a GitHub repository, use the following format:

    .. code-block:: python

        import {{ app_module }} as {{ app_docs_import_conv }}

        wkt = {{ app_docs_import_conv }}.WorkflowTemplate.from_YAML_file()

    Updating values in a workflow template file
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    When constructing a workflow template from a (YAML or JSON) file or string, we can provide updates to the data of the template which are applied before the template is loaded. In particular, we can provide updates to the template-level resources block (for the ``any`` scope) like this:

    .. tab-set::

        .. tab-item:: CLI

            For making the a demo workflow with modified resources:

            .. code-block:: console
                
                {{ app_package_name }} demo-workflow make DEMO_WORKFLOW_NAME --resource random_seed 1234

            For making and submitting a demo workflow with modified resources:

            .. code-block:: console
                
                {{ app_package_name }} demo-workflow go DEMO_WORKFLOW_NAME --resource random_seed 1234

        .. tab-item:: Python API

            .. code-block:: python
                
                import {{ app_module }} as {{ app_docs_import_conv }}

                # for making a demo workflow with modified resources:
                wk = {{ app_docs_import_conv }}.make_and_submit_demo_workflow(
                    "DEMO_WORKFLOW_NAME", 
                    resources={"random_seed": 1234},
                )

                # for making and submitting a demo workflow with modified resources:
                wk = {{ app_docs_import_conv }}.make_and_submit_demo_workflow(
                    "DEMO_WORKFLOW_NAME", 
                    resources={"random_seed": 1234},
                )

    This also works for non-demo workflow templates as well. Workflow-specific configuration items ``config`` can also be updates in a similar way.

    We can also update arbitrary data within the template in the following way, using a mapping of "paths" within the template data to the new values that should be applied at those "paths":

    .. code-block:: python
        
        import {{ app_module }} as {{ app_docs_import_conv }}

        # for making a demo workflow with a modified input value for the first task
        wkt = {{ app_docs_import_conv }}.make_and_submit_demo_workflow(
            "DEMO_WORKFLOW_NAME", 
            updates={("tasks", 0, "inputs"): 99},
        )
