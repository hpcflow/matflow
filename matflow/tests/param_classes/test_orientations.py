"""Test `Orientations` and related classes."""

from __future__ import annotations
from pathlib import Path
import sys
import requests
from typing import TYPE_CHECKING
import pytest

from matflow.tests.utils import make_test_data_YAML_workflow

if TYPE_CHECKING:
    from matflow.param_classes.orientations import Orientations


def test_orientations_yaml_init(
    tmp_path: Path,
    orientations_1: Orientations,
    orientations_2: Orientations,
):
    wk = make_test_data_YAML_workflow("define_orientations.yaml", path=tmp_path)
    orientations_t1 = wk.tasks.define_orientations_1.elements[0].inputs.orientations.value
    orientations_t2 = wk.tasks.define_orientations_2.elements[0].inputs.orientations.value
    assert orientations_t1 == orientations_1
    assert orientations_t2 == orientations_2
