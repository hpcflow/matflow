"""Test generation of volume elements."""

from __future__ import annotations
from pathlib import Path

import pytest

from matflow.tests.utils import assert_values_equal, make_test_data_YAML_workflow


@pytest.mark.demo_workflows
def test_generate_VE_from_voronoi_1(tmp_path: Path, ve_1: dict):
    """
    Note this test must be run with a `--with-env-source /path/to/envs.yaml` option that
    points to an environment file with definitions for:
     - `damask_parse_env`

    """
    wk = make_test_data_YAML_workflow("generate_VE.yaml", path=tmp_path)
    wk.submit(wait=True)
    ve = wk.tasks.generate_volume_element_from_voronoi.elements[
        0
    ].outputs.volume_element.value
    assert_values_equal(ve, ve_1, rtol=1e-6)
