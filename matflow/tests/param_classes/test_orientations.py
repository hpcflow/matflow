"""Test `Orientations` and related classes.

"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from matflow.tests.utils import make_test_data_YAML_workflow

if TYPE_CHECKING:
    from matflow.param_classes.orientations import Orientations


def test_orientations_yaml_init(
    null_config, tmp_path: Path, orientations_1: Orientations
):
    wk = make_test_data_YAML_workflow("define_orientations.yaml", path=tmp_path)
    orientations = wk.tasks.define_orientations.elements[0].inputs.orientations.value
    assert orientations == orientations_1
