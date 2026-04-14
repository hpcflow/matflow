"""
Configuration and standard fixtures for PyTest.
"""

from __future__ import annotations
import copy
import itertools
from pathlib import Path
import re
import numpy as np
import pytest
from click.testing import CliRunner
from hpcflow.sdk.core.utils import get_file_context

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


def has_marker(item, name):
    return any(m.name == name for m in item.iter_markers())


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):

    all_markers = ("unit", "integration", "demo_workflows")

    run_unit = config.getoption("--unit")
    run_integration = config.getoption("--integration")
    run_damask = config.getoption("--demo-damask-workflows")
    run_mtex = config.getoption("--demo-mtex-workflows")

    # if no flags are passed, default to unit tests:
    if not (run_unit or run_integration or run_damask or run_mtex):
        run_unit = True

    for item in items:

        # assign default marker if none
        if not any(has_marker(item, marker) for marker in all_markers):
            item.add_marker(pytest.mark.unit)

        is_unit = has_marker(item, "unit")
        is_integration = has_marker(item, "integration")
        is_damask = has_marker(item, "demo_damask_workflows")
        is_mtex = has_marker(item, "demo_mtex_workflows")

        if not (
            (run_unit and is_unit)
            or (run_integration and is_integration)
            or (run_damask and is_damask)
            or (run_mtex and is_mtex)
        ):
            item.add_marker(pytest.mark.skip(reason="skipped by selected test groups"))


@pytest.fixture(scope="session", autouse=True)
def isolated_app_config(tmp_path_factory, pytestconfig):
    """Pytest session-scoped fixture to apply a new default config for tests, and then
    restore the original config after testing has completed."""
    mf.run_time_info.in_pytest = True
    original_config_dir = mf.config.config_directory
    original_config_key = mf.config.config_key

    # honour config overrides provided via top-level CLI options `--with-config`:
    overrides = copy.deepcopy(mf.config._overrides)

    mf.unload_config()
    new_config_dir = tmp_path_factory.mktemp("app_config")
    mf.load_config(config_dir=new_config_dir, overrides=overrides)

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
    mf.load_config(
        config_dir=original_config_dir,
        config_key=original_config_key,
        overrides=overrides,
    )
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


def sanitize_nodeid(nodeid: str) -> str:
    """Return a sanitized pytest node ID that can be used as a legal file name on all
    platforms."""
    s = nodeid.replace("::", "__")
    s = re.sub(r'[<>:"/\\|?*\[\]]+', "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


@pytest.fixture(scope="session")
def fig_dir(tmp_path_factory, pytestconfig):
    fig_dir = pytestconfig.getoption("--fig-dir")
    if fig_dir:
        path = Path(fig_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    return tmp_path_factory.mktemp("figures")


@pytest.fixture
def nodeid_str(request) -> str:
    return sanitize_nodeid(request.node.nodeid)


@pytest.fixture
def nodename_str(request) -> str:
    return sanitize_nodeid(request.node.name)


@pytest.fixture
def fig_output_dir(fig_dir):
    fig_dir.mkdir(parents=True, exist_ok=True)
    return fig_dir


@pytest.fixture
def save_fig(fig_output_dir, nodeid_str):
    """Fixture to save a matplotlib figure to the figure output directory, optionally
    with a custom file name."""
    counter = itertools.count(1)

    def _save(fig, name=None):
        if name is None:
            name = f"{nodeid_str}_figure_{next(counter)}.png"
        fig.suptitle(name, fontsize="small")
        fig.savefig(fig_output_dir / name)

    return _save


@pytest.fixture
def save_fig(fig_output_dir, reference_dir_for_test, pytestconfig):
    """Save a matplotlib figure.

    - If --save-reference: save into reference_dir
    - Otherwise: save into fig_output_dir (temporary/artifact)
    """
    counter = itertools.count(1)
    save = pytestconfig.getoption("--save-reference")
    reference_dir_for_test.mkdir(parents=True, exist_ok=True)

    def _handle(fig, name=None):
        if name is None:
            name = f"figure_{next(counter)}.png"

        fig.suptitle(name, fontsize="small")

        fig_path = fig_output_dir / name
        fig_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(fig_path)

        if save:
            ref_path = reference_dir_for_test / name
            ref_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(ref_path)

    return _handle


@pytest.fixture
def reference_dir_for_test(nodename_str):
    with get_file_context("matflow.tests.data.reference") as file_path:
        return file_path / nodename_str


@pytest.fixture
def reference_array_data(reference_dir_for_test, pytestconfig):
    save = pytestconfig.getoption("--save-reference")
    reference_dir_for_test.mkdir(parents=True, exist_ok=True)
    recorded_any = False

    def _handle(data, *, name, rtol=1e-6, atol=1e-12):
        nonlocal recorded_any
        ref_path = reference_dir_for_test / name

        if save:
            if name.endswith(".npz"):
                np.savez(ref_path, **data)
            else:
                np.save(ref_path, data)

            recorded_any = True
            return

        if not ref_path.exists():
            pytest.fail(
                f"Missing reference data: {ref_path}\n"
                "Run with --save-reference to create it."
            )

        ref = np.load(ref_path)
        if name.endswith(".npz"):
            for key, arr in data.items():
                if key not in ref:
                    pytest.fail(f"Missing key '{key}' in {ref_path}")

                np.testing.assert_allclose(
                    arr,
                    ref[key],
                    rtol=rtol,
                    atol=atol,
                    err_msg=f"{key} mismatch in {ref_path}",
                )

            # optional: check for unexpected keys
            extra = set(ref.files) - set(data.keys())
            if extra:
                pytest.fail(f"Unexpected keys {extra} in {ref_path}")

        else:
            np.testing.assert_allclose(data, ref, rtol=rtol, atol=atol)

    yield _handle

    # teardown
    if save and recorded_any:
        pytest.skip("reference data recorded")


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
