"""
Configuration and standard fixtures for PyTest.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pytest
from click.testing import CliRunner
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


@pytest.fixture(scope="session", autouse=True)
def isolated_app_config(tmp_path_factory, pytestconfig):
    """Pytest session-scoped fixture to apply a new default config for tests, and then
    restore the original config after testing has completed."""
    mf.run_time_info.in_pytest = True
    original_config_dir = mf.config.config_directory
    original_config_key = mf.config.config_key
    mf.unload_config()
    new_config_dir = tmp_path_factory.mktemp("app_config")
    mf.load_config(config_dir=new_config_dir)

    if pytestconfig.getoption("--configure-python-env"):
        # for setting up a Python env using the currently active virtual/conda env:
        mf.env_configure_python(use_current=True, save=True)
        mf.print_envs()
        mf.show_env(label="python")

    if env_src_file := pytestconfig.getoption("--with-env-source"):
        # for including envs (e.g. Python) from an existing env source file:
        mf.config.append("environment_sources", env_src_file)
        mf.config.save()
        mf.print_envs()
        mf.show_env(label="python")

    yield
    mf.unload_config()
    mf.load_config(config_dir=original_config_dir, config_key=original_config_key)
    mf.run_time_info.in_pytest = False


@pytest.fixture()
def modifiable_config(tmp_path: Path):
    """Pytest fixture to provide a fresh config which can be safely modified within the
    test without affecting other tests."""
    config_dir = mf.config.config_directory
    config_key = mf.config.config_key
    mf.unload_config()
    mf.load_config(config_dir=tmp_path)
    yield
    mf.unload_config()
    mf.load_config(config_dir=config_dir, config_key=config_key)


@pytest.fixture()
def reload_template_components():
    """Pytest fixture to reload the template components at the end of the test."""
    yield
    mf.reload_template_components()


@pytest.fixture
def unload_config():
    mf.unload_config()


@pytest.fixture
def cli_runner():
    """Pytest fixture to ensure the current config directory and key are used when
    invoking the CLI."""
    runner = CliRunner()
    common_args = [
        "--config-dir",
        str(mf.config.config_directory),
        "--config-key",
        mf.config.config_key,
    ]

    # to avoid warnings about config already loaded, we unload first (the CLI command
    # will immediately reload it):
    mf.unload_config()

    def invoke(args=None, cli=None, **kwargs):
        all_args = common_args + (args or [])
        cli = cli or mf.app.cli
        return runner.invoke(cli, args=all_args, **kwargs)

    return invoke


def pytest_generate_tests(metafunc):
    repeats_num = int(metafunc.config.getoption("--repeat"))
    if repeats_num > 1:
        metafunc.fixturenames.append("tmp_ct")
        metafunc.parametrize("tmp_ct", range(repeats_num))


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
