"""Test `MicrostructureSeeds`.

"""

from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING

from matflow.tests.utils import make_test_data_YAML_workflow

if TYPE_CHECKING:
    from matflow.param_classes.seeds import MicrostructureSeeds


def test_orientations_yaml_init(
    null_config, tmp_path: Path, seeds_1: MicrostructureSeeds
):
    wk = make_test_data_YAML_workflow("define_seeds.yaml", path=tmp_path)
    seeds = wk.tasks.define_microstructure_seeds.elements[
        0
    ].inputs.microstructure_seeds.value
    assert seeds == seeds_1
