Command files
=============

.. jinja:: first_ctx

   {% for i in command_files %}

   {{i.label}}
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   {{i.documentation}}
   {% endfor %}
