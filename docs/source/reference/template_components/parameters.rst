Parameters
==========

.. jinja:: first_ctx

  {% for i in parameters %}

  {{i.typ}}
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  {% if i._validation %}

  .. raw:: html
    :file: {{ tree_files.get(i.typ) }}

  {% endif %}


  {% set param_task_map_i = parameter_task_schema_map.get(i.typ) %}

  {% if param_task_map_i[0] -%}
  Input of: {% for inp_task in param_task_map_i[0] -%}
    :ref:`{{ inp_task }} <reference/template_components/task_schemas:{{ inp_task }}>`{% if not loop.last %}, {% endif -%}
    {% endfor %}
  {% endif %}

  {% if param_task_map_i[1] -%}
  Output of: {% for out_task in param_task_map_i[1] -%}
    :ref:`{{ out_task }} <reference/template_components/task_schemas:{{ out_task }}>`{% if not loop.last %}, {% endif -%}
    {% endfor %}
  {% endif %}

  {% if i._value_class %}
  Constructors:

  * :meth:`{{ i._value_class.__qualname__ }} <{{ i._value_class.__module__ }}.{{ i._value_class.__qualname__ }}>`

  {% for cls_method in get_classmethods(i._value_class) %}

  * :meth:`{{ i._value_class.__qualname__ }}.{{ cls_method }} <{{ i._value_class.__module__ }}.{{ i._value_class.__qualname__ }}.{{ cls_method }}>`

  {% endfor %}

  {% endif %}

  {% endfor %}
