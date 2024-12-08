"""Utility functions to assist testing."""

from importlib import resources

import matflow as mf


def make_test_data_YAML_workflow(workflow_name, path, **kwargs):
    """Generate a workflow whose template file is defined in the test data directory."""
    # TODO: re-use this function in hpcflow, rather than defining it again here.
    pkg = "matflow.tests.data"
    try:
        script_ctx = resources.as_file(resources.files(pkg).joinpath(workflow_name))
    except AttributeError:
        # < python 3.9; `resource.path` deprecated since 3.11
        script_ctx = resources.path(pkg, workflow_name)

    with script_ctx as file_path:
        return mf.Workflow.from_YAML_file(YAML_path=file_path, path=path, **kwargs)
