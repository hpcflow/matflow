"""Used to test submission of a workflow via a python script (this script)."""

import importlib
import sys
from tempfile import gettempdir

app_import_str = sys.argv[1]
app = importlib.import_module(app_import_str)

wk_yaml = """
name: workflow_1
template_components:
  task_schemas:
    - objective: test_t1_conditional_OS_in_place
      inputs:
        - parameter: p1
      outputs:
        - parameter: p2
      actions:
        - rules:
            - path: resources.os_name
              condition: { value.equal_to: posix }
          environments:
            - scope:
                type: any
              environment: null_env
          commands:
            - command: echo "$((<<parameter:p1>> + 100))"
              stdout: <<parameter:p2>>
        - rules:
            - path: resources.os_name
              condition: { value.equal_to: nt }
          environments:
            - scope:
                type: any
              environment: null_env
          commands:
            - command: Write-Output ((<<parameter:p1>> + 100))
              stdout: <<parameter:p2>>
tasks:
  - schema: test_t1_conditional_OS_in_place
    inputs:
      p1: 101
"""
wk = app.Workflow.from_YAML_string(YAML_str=wk_yaml, path=gettempdir())
wk.submit(wait=True)
assert wk.tasks[0].elements[0].outputs.p2.value == "201"
