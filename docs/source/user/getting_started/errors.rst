.. jinja:: first_ctx

  Common errors
  #############

  Certain errors have cropped up multiple times for {{ app_name }} users.
  Here's some advice for those errors.

  Submitting a workflow
  -----------------------------

  If you get an error which (often) starts with

  .. code-block:: console

      ERROR {{ app_module }}.persistence: batch update exception!

  and ends with something like

  .. code-block:: console

      File "hpcflow/sdk/app.py", line 1150, in read_known_submissions_file
      File "hpcflow/sdk/app.py", line 1122, in _parse_known_submissions_line
      ValueError: not enough values to unpack (expected 8, got 6)

  This is usually caused by updating the {{ app_name }} version.
  Leftover submissions info causes the newer {{ app_name }} version to get confused.
  The fix? ``{{ app_package_name }} manage clear-known-subs``.
  This will delete the known submissions file, and the next time you submit a workflow,
  {{ app_name }} will create a new one.

  Analysing an old workflow
  --------------------------

  If you attempt to install an older version of MatFlow (e.g. for analysis of a workflow
  created using an older version of MatFlow),  you might run into something like this:

  .. code-block:: console

      ---------------------------------------------------------------------------
      TypeError                                 Traceback (most recent call last)
      Cell In[1], line 1
      ----> 1 import matflow as mf
            3 import numpy as np
            4 import matplotlib.pyplot as plt

      File ~\projects\matflow\Lib\site-packages\matflow\__init__.py:15
           12 __dir__ = sdk_app.get_app_module_dir()
           14 # set app-level config options:
      ---> 15 config_options = ConfigOptions(
           16     directory_env_var="MATFLOW_CONFIG_DIR",
           17     default_directory="~/.matflow",
           18     sentry_DSN="https://2463b288fd1a40f4bada9f5ff53f6811@o1180430.ingest.sentry.io/6293231",
           19     sentry_traces_sample_rate=1.0,
           20     sentry_env="main" if "a" in __version__ else "develop",
           21     default_known_configs_dir="github://hpcflow:matflow-configs@main",
           22 )
           24 # load built in template components:
           25 template_components = sdk_app.App.load_builtin_template_component_data(
           26     "matflow.data.template_components"
           27 )

      TypeError: ConfigOptions.__init__() got an unexpected keyword argument 'sentry_DSN'


  The problem is the version of hpcflow-new2 has historically not been constrained to be whatever it was at the time of a given MatFlow release.
  The example above was using matflow version  0.3.0a110 and hpcflow-new2 version 0.2.0a178 ,
  but if we look at the `dependencies of that version of MatFlow <https://github.com/hpcflow/matflow/blob/v0.3.0a110/pyproject.toml>`_,
  we can see it requires hpcflow version 0.2.0a147. The specification of this dependency has since been updated
  such that current releases of MatFlow specify a particular version of hpcFlow.
  So, to get the correct version of hpcflow (for the case above), you can do: ``pip install hpcflow-new2==0.2.0a147``.


  Debugging
  ##########

  Sometimes it is necessary to debug a task schema.
  This is often easier done outside of {{ app_name }}, and one approach is to use a failed workflow run to extract the inputs
  that were passed to the task schema, and run the rest of the code in a python script.
  This can be achieved like this:

  .. code-block:: python

      import matflow as mf
      wk = mf.Workflow("./path_to_failed_workflow/")
      inputs = wk.tasks.failed_task_name.elements[0].iterations[0].action_runs[0].get_py_script_func_kwargs()
      output = failed_task_name(**inputs)

  For this approach you will need to define the functions in the `failed_task_schema` script locally, i.e. copy them from {{ app_name }}.
 
