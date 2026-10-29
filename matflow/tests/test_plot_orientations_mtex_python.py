from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

import matflow as mf
from matflow.param_classes.orientations import (
    LatticeDirection,
    OrientationRepresentation,
    Orientations,
    QuatOrder,
    UnitCellAlignment,
)

mtex = pytest.importorskip("mtex", reason="Python MTEX is an optional task dependency")

from matflow.data.scripts.mtex.plot_orientations import (
    _mtex_orientations,
    plot_orientations,
)
from matflow.tests.test_sample_texture_mtex_python import ebsd_file

import matplotlib.pyplot as plt
from PIL import Image


@pytest.fixture
def orientations() -> Orientations:
    data = np.random.default_rng(42).normal(size=(24, 4))
    data /= np.linalg.norm(data, axis=1, keepdims=True)
    return Orientations(
        data=data,
        representation=OrientationRepresentation.quaternion(),
        unit_cell_alignment=UnitCellAlignment(
            x=LatticeDirection.A, y=LatticeDirection.B, z=LatticeDirection.C
        ),
    )


@pytest.mark.parametrize("order", list(QuatOrder))
@pytest.mark.parametrize("symmetry", ["cubic", "hexagonal"])
def test_orientation_conversion(
    orientations: Orientations, order: QuatOrder, symmetry: str
) -> None:
    expected = orientations.data.copy()
    expected[:, 1:] *= -1
    if order is QuatOrder.VECTOR_SCALAR:
        orientations.data = np.roll(orientations.data, -1, axis=1)
    orientations.representation = OrientationRepresentation.quaternion(order)
    if symmetry == "hexagonal":
        orientations.unit_cell_alignment = UnitCellAlignment(
            x=LatticeDirection.A_STAR, y=LatticeDirection.B, z=LatticeDirection.C
        )
    original = orientations.data.copy()
    result = _mtex_orientations(orientations, symmetry)
    np.testing.assert_allclose(result.data, expected)
    np.testing.assert_array_equal(orientations.data, original)
    if symmetry == "hexagonal":
        assert result.CS.alignment() == ["X||a*", "Y||b", "Z||c"]
    else:
        assert result.CS.alignment() == []
    assert result.SS.sym.name == mtex.specimenFrame("1").sym.name


@pytest.mark.parametrize("data", [[], [[0, 0, 0, 0]], [[np.nan, 0, 0, 1]], [[1, 0, 0]]])
def test_invalid_quaternions(orientations: Orientations, data: list) -> None:
    orientations.data = np.asarray(data)
    with pytest.raises(ValueError, match="nonzero.*quaternions"):
        _mtex_orientations(orientations, "cubic")


def test_unsupported_representation(orientations: Orientations) -> None:
    orientations.representation = OrientationRepresentation.euler()
    with pytest.raises(ValueError, match="requires quaternion"):
        _mtex_orientations(orientations, "cubic")


def test_missing_alignment(orientations: Orientations) -> None:
    orientations.unit_cell_alignment.x = None
    with pytest.raises(ValueError, match="all three"):
        _mtex_orientations(orientations, "cubic")


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"pole_figure_directions": []}, "pole_figure_directions"),
        ({"pole_figure_directions": [[0, 0, 0]]}, "pole_figure_directions"),
        ({"pole_figure_directions": [[1, 2]]}, "pole_figure_directions"),
        ({"pole_figure_directions": [[0, np.inf, 1]]}, "pole_figure_directions"),
        ({"IPF_reference_direction": "bad"}, "reference direction"),
        ({"IPF_reference_directions": []}, "must not be empty"),
        ({"IPF_reference_directions": ["bad"]}, "reference direction"),
        ({"colourbar_limits": [1.0, 0.0]}, "colourbar_limits"),
        ({"colourbar_limits": [0.0, np.nan]}, "colourbar_limits"),
    ],
)
def test_invalid_plot_options(
    orientations: Orientations, kwargs: dict, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        plot_orientations(orientations, "cubic", False, **kwargs)


def assert_png(path: Path) -> None:
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.width > 100 and image.height > 100
        pixels = np.asarray(image.convert("RGB"))
    assert np.std(pixels) > 5


@pytest.mark.parametrize("inverse", [False, True])
@pytest.mark.parametrize("contours", [False, True])
@pytest.mark.parametrize("symmetry", ["cubic", "hexagonal"])
def test_render_figures(
    orientations: Orientations,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    inverse: bool,
    contours: bool,
    symmetry: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MATFLOW_RUN_NUM_THREADS", "1")
    if symmetry == "hexagonal":
        orientations.unit_cell_alignment.x = LatticeDirection.A_STAR
    before = plt.get_fignums()
    with patch.object(mtex, "setMTEXpref", wraps=mtex.setMTEXpref) as threads:
        plot_orientations(
            orientations,
            symmetry,
            contours,
            pole_figure_directions=None if inverse else [[0, 0, 1], [1, 1, 1]],
            IPF_reference_directions=["x", "z"],
        )
    threads.assert_called_once_with("threads", 1)
    assert plt.get_fignums() == before
    assert_png(tmp_path / ("inverse_pole_figure.png" if inverse else "pole_figure.png"))
    if contours:
        assert not (tmp_path / "IPF_key.png").exists()
    else:
        assert_png(tmp_path / "IPF_key.png")


@pytest.mark.parametrize("one_bar", [False, True])
@pytest.mark.parametrize("limits", [None, [0.0, 5.0]])
def test_colourbar_options(
    orientations: Orientations,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    one_bar: bool,
    limits: list[float] | None,
) -> None:
    monkeypatch.chdir(tmp_path)
    figures = []
    save = mtex.saveFigure

    def capture(filename, fig):
        figures.append(fig)
        save(filename, fig=fig)

    with patch.object(mtex, "saveFigure", side_effect=capture):
        plot_orientations(
            orientations,
            "cubic",
            True,
            pole_figure_directions=[[0, 0, 1], [1, 1, 1]],
            colourbar_limits=limits,
            use_one_colourbar=one_bar,
        )
    assert len(figures) == 1
    assert len(figures[0].colorbars) == (1 if one_bar else 2)
    ranges = [ax._mtexSphericalPlot.mappable.get_clim() for ax in figures[0].children]
    if limits is not None:
        assert all(value == tuple(limits) for value in ranges)
    elif one_bar:
        assert ranges[0] == ranges[1]


def test_figure_closed_after_error(
    orientations: Orientations, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    before = plt.get_fignums()
    with patch.object(mtex, "saveFigure", side_effect=OSError("cannot write figure")):
        with pytest.raises(OSError, match="cannot write"):
            plot_orientations(orientations, "cubic", False)
    assert plt.get_fignums() == before


@pytest.mark.parametrize("method", ["pole_figure", "inverse_pole_figure"])
def test_plot_schema(method: str) -> None:
    schema = mf.task_schemas.get(f"visualise_orientations_{method}_mtex_python")
    inputs = {item.parameter.typ for item in schema.inputs}
    assert "execution_mode" not in inputs
    action = schema.actions[0]
    assert set(action.script_data_in) == {f"inputs.{name}" for name in inputs}
    assert all(value["format"] == "direct" for value in action.script_data_in.values())
    assert action.script_exe == "python_script"


@pytest.mark.integration
@pytest.mark.parametrize("contours", [False, True])
def test_sample_and_plot_workflow(
    ebsd_file: Path, tmp_path: Path, contours: bool
) -> None:
    file_type = ebsd_file.suffix[1:].upper()
    template = mf.WorkflowTemplate.from_YAML_string(
        "name: sample_and_plot_python\n"
        "resources:\n"
        "  any:\n"
        "    random_seed: 1234\n"
        "tasks:\n"
        f"  - schema: sample_texture_from_{file_type}_file_mtex_python\n"
        "    inputs:\n"
        f"      {file_type}_file_path: '{ebsd_file}'\n"
        "      specimen_symmetry: '1'\n"
        "      EBSD_phase: Al\n"
        "      num_orientations: 24\n"
        "      num_orientation_sets: 2\n"
        "  - schema: visualise_orientations_pole_figure_mtex_python\n"
        "    inputs:\n"
        "      crystal_symmetry: cubic\n"
        "      pole_figure_directions: [[0, 0, 1], [1, 1, 1]]\n"
        f"      use_contours: {str(contours).lower()}\n"
        "  - schema: visualise_orientations_inverse_pole_figure_mtex_python\n"
        "    inputs:\n"
        "      crystal_symmetry: cubic\n"
        "      IPF_reference_directions: [x, z]\n"
        f"      use_contours: {str(contours).lower()}\n"
    )
    workflow = mf.Workflow.from_template(template, path=tmp_path)
    assert workflow.tasks[1].num_elements == workflow.tasks[2].num_elements == 2
    workflow.submit(wait=True, add_to_known=False)
    for run in workflow.get_all_EARs():
        assert run.status.name == "success"
    reopened = mf.Workflow(workflow.path)
    for run in reopened.get_all_EARs()[1:]:
        files = run.output_files
        if run.action.output_files[0].label == "mtex_pole_figures":
            path = files.mtex_pole_figures.value
        else:
            path = files.mtex_inverse_pole_figures.value
        assert_png(Path(path))
        if not contours:
            assert_png(Path(files.mtex_IPF_key.value))
