"""
Configuration and standard fixtures for PyTest.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pytest
import matflow as mf
from matflow.param_classes.load import LoadCase, LoadStep
from matflow.param_classes.orientations import (
    EulerDefinition,
    LatticeDirection,
    OrientationRepresentation,
    OrientationRepresentationType,
    Orientations,
    UnitCellAlignment,
    QuatOrder,
)
from matflow.param_classes.seeds import MicrostructureSeeds


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration-like workflow submission tests",
    )


def pytest_configure(config: pytest.Config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration-like workflow submission test to run",
    )
    mf.run_time_info.in_pytest = True


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    if config.getoption("--integration"):
        # --integration in CLI: only run these tests
        for item in items:
            if "integration" not in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="remove --integration option to run")
                )
    else:
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(reason="add --integration option to run")
                )


def pytest_unconfigure(config: pytest.Config):
    mf.run_time_info.in_pytest = False


@pytest.fixture
def null_config(tmp_path: Path):
    if not mf.is_config_loaded:
        mf.load_config(config_dir=tmp_path)
    mf.run_time_info.in_pytest = True


@pytest.fixture
def new_null_config(tmp_path: Path):
    mf.load_config(config_dir=tmp_path)
    mf.load_template_components(warn=False)
    mf.run_time_info.in_pytest = True


@pytest.fixture
def load_case_1() -> LoadCase:
    """A load case object to compare to that generated in `define_load.yaml`."""
    return LoadCase(
        steps=[
            LoadStep(
                total_time=100,
                num_increments=200,
                target_def_grad_rate=np.ma.masked_array(
                    data=np.array(
                        [
                            [1e-3, 0, 0],
                            [0, 0, 0],
                            [0, 0, 0],
                        ]
                    ),
                    mask=np.array(
                        [
                            [False, False, False],
                            [False, True, False],
                            [False, False, True],
                        ]
                    ),
                ),
                stress=np.ma.masked_array(
                    data=np.array(
                        [
                            [0, 0, 0],
                            [0, 0.0, 0],
                            [0, 0, 0.0],
                        ]
                    ),
                    mask=np.array(
                        [
                            [True, True, True],
                            [True, False, True],
                            [True, True, False],
                        ]
                    ),
                ),
            )
        ]
    )


@pytest.fixture
def orientations_1() -> Orientations:
    """An orientations object to compare to that generated in task index 0 of
    `define_orientations.yaml`."""
    return Orientations(
        data=np.array(
            [
                [0, 0, 0],
                [0, 45, 0],
            ]
        ),
        unit_cell_alignment=UnitCellAlignment(x=LatticeDirection.A),
        representation=OrientationRepresentation(
            type=OrientationRepresentationType.EULER,
            euler_definition=EulerDefinition.BUNGE,
            euler_is_degrees=True,
        ),
    )


@pytest.fixture
def orientations_2() -> Orientations:
    """An orientations object to compare to that generated in task index 1 of
    `define_orientations.yaml` (the demo data file `quaternions.txt`)."""
    return Orientations(
        data=np.array(
            [
                [
                    0.979576633518360,
                    -0.011699484277401,
                    -0.031022749430343,
                    0.198318758946959,
                ],
                [
                    0.051741844582538,
                    0.964477514397002,
                    0.258166574789950,
                    0.021352409770402,
                ],
                [
                    0.051741844582538,
                    0.964477514397002,
                    0.258166574789950,
                    0.021352409770402,
                ],
            ]
        ),
        unit_cell_alignment=UnitCellAlignment(
            x=LatticeDirection.A,
            y=LatticeDirection.B,
            z=LatticeDirection.C,
        ),
        representation=OrientationRepresentation(
            type=OrientationRepresentationType.QUATERNION,
            quat_order=QuatOrder.VECTOR_SCALAR,
        ),
    )


@pytest.fixture
def seeds_1(orientations_1: Orientations) -> MicrostructureSeeds:
    """A microstructure seeds object to compare to that generated in `define_seeds.yaml`."""
    return MicrostructureSeeds(
        position=np.array(
            [
                [0.3, 0.2, 0.1],
                [0.5, 0.4, 0.3],
            ]
        ),
        box_size=np.array([1.0, 1.0, 1.0]),
        phase_label="phase_1",
        orientations=orientations_1,
    )
