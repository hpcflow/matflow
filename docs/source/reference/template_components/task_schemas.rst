.. _task_schemas:

Task schemas
============

.. jinja:: first_ctx

   {% for k, v in task_schema_actions_html.items() %}

   {{ k }}
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   
   {% for name, v2 in v.items() %}

   {% if name %}
   
   {{ name }}
   ---------------------------------------------------------------------------------------
   {% endif %}
   
   .. raw:: html
      :file: {{ v2.file_path }}

   {% endfor %}

   {% endfor %}
