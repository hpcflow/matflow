"""Utility functions to assist testing."""

from functools import partial

from hpcflow.sdk.core.test_utils import (
    make_test_data_YAML_workflow,
    make_test_data_YAML_workflow_template,
)

import matflow as mf


make_test_data_YAML_workflow = partial(
    make_test_data_YAML_workflow, app=mf, pkg="matflow.tests.data"
)

make_test_data_YAML_workflow_template = partial(
    make_test_data_YAML_workflow_template, app=mf, pkg="matflow.tests.data"
)
