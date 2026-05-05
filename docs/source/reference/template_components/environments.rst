Environments
============

.. jinja:: first_ctx

   {% for i in environments %}

   {{i.name}}
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   {{i.documentation}}
   {% endfor %}
