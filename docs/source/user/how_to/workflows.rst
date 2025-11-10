Workflow how-tos
----------------

Generating a persistent workflow from a workflow template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. jinja:: first_ctx

    If you have a workflow template object in Python :code:`wkt`, you can generate a new persistent workflow via the :func:`{{ app_package_name }}.app.Workflow.from_template` function:

    .. code-block:: python

        import {{ app_module }} as {{ app_docs_import_conv }}

        wk = {{ app_docs_import_conv }}.Workflow.from_template(wkt)

    In the CLI, if you have a workflow template YAML file, you can generate a new persistent workflow like this:

    .. code-block:: console

        {{ app_package_name }} make /path/to/workflow/template.yaml

    There are several options for telling |app_name| about the format of the template, and controlling how the workflow is generated. For instance, to specify the workflow name, use the :code:`--name` option.  See the CLI reference documentation for more details.
    


Loading workflows
~~~~~~~~~~~~~~~~~

We support paths like:

* `/path/to/workflow` for local zarr or json
* `/path/to/workflow.zip` for local zarr-zip
* `/path/to/workflow.json` for local json-single # TODO
* `ssh://user@host/path/to/workflow` for remote zarr
* `ssh://user@host/path/to/workflow.zip` for remote zarr-zip
* `ssh://user@host/path/to/workflow.json` for remote json
* `https://sandbox.zenodo.org/record/1210144/files/workflow.zip` for zenodo zarr-zip

You can convert a zarr store to an archived zarr-zip store using `Workflow.zip()`.
