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


@pytest.mark.parametrize("generator", ["seeds", "variates"])
def test_voronoi_material_indices_int32(generator: str) -> None:
    """Both Voronoi generators preserve labels while halving int64 grid storage."""
    import numpy as np

    pytest.importorskip("damask")
    pytest.importorskip("damask_parse")
    from matflow.data.scripts.damask.generate_volume_element_voronoi import (
        generate_volume_element_voronoi,
    )
    from matflow.data.scripts.damask.generate_volume_element_voronoi_variates import (
        generate_volume_element_voronoi_variates,
    )
    from matflow.param_classes.seeds import MicrostructureSeeds
    from statistics import NormalDist

    positions = np.array([[0.25, 0.5, 0.5], [0.75, 0.5, 0.5]])
    if generator == "seeds":
        seeds = MicrostructureSeeds(
            position=positions, box_size=np.ones(3), phase_label="Mg"
        )
        result = generate_volume_element_voronoi(
            microstructure_seeds=seeds,
            VE_grid_size=[4, 2, 2],
            homog_label="SX",
            orientations=None,
            scale_morphology=None,
            scale_update_size=False,
            periodic=True,
        )
    else:
        uniform_variates = np.concatenate(
            [positions.ravel(), np.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.8])]
        )
        result = generate_volume_element_voronoi_variates(
            x=np.array(
                [NormalDist().inv_cdf(float(value)) for value in uniform_variates]
            ),
            VE_grid_size=[4, 2, 2],
            VE_size=[1.0, 1.0, 1.0],
            phase_label="Mg",
            homog_label="SX",
            scale_morphology=None,
            scale_update_size=False,
        )
    indices = result["volume_element"]["element_material_idx"]
    expected = np.zeros((4, 2, 2), dtype=np.int32)
    expected[2:] = 1
    assert indices.dtype == np.dtype(np.int32)
    np.testing.assert_array_equal(indices, expected)
