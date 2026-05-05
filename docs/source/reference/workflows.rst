Demo workflows
==============

.. jinja:: first_ctx

   These workflow templates are included in {{ app_name }} as demonstrations. You can copy
   a demo workflow template to somewhere accessible using the CLI like this:

   .. code-block:: console

      {{ app_package_name }} demo-workflow copy WORKFLOW_NAME DESTINATION

   where :code:`WORKFLOW_NAME` is the name of one of the demo workflows, and :code:`DESTINATION` is the
   target copy location, which can be a directory (e.g. :code:`"."` for the current
   working directory, or a full file path).

   In the Python API, we can copy a demo workflow template file like this:

   .. code-block:: python

       import {{ app_module }} as {{ app_docs_import_conv }}

       {{ app_docs_import_conv }}.copy_demo_workflow(name, dst)


   {% for i in demo_workflows.values() %}

   {{i.obj.name}}
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   {% if i.obj.doc %}
   {% for para_j in i.obj.doc %}

   {{ para_j }}

   {% endfor %}

   {% endif %}

   .. admonition:: {{ i.file_name }}
      :class: dropdown code-dropdown

      .. include:: {{ i.file_path }}
         :code: yaml

   {% endfor %}
