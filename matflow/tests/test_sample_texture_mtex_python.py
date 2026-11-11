from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any, Literal
from unittest.mock import patch
import warnings

import numpy as np
import pytest

import matflow as mf
from matflow.param_classes.orientations import (
    LatticeDirection,
    Orientations,
    QuatOrder,
    UnitCellAlignment,
)

mtex = pytest.importorskip("mtex", reason="Python MTEX is an optional task dependency")

from matflow.data.scripts.mtex.sample_texture_EBSD import (
    EBSDRotation,
    sample_texture_EBSD,
)


@pytest.fixture(params=["ctf", "crc"])
def ebsd_file(tmp_path: Path, request: pytest.FixtureRequest) -> Path:
    angles = np.array([[10, 20, 30], [40, 50, 60], [0, 0, 0], [70, 80, 90]])
    phases = [1, 2, 0, 1]
    if request.param == "ctf":
        path = tmp_path / "texture.ctf"
        header = (
            "Channel Text File\n"
            "XCells\t2\nYCells\t2\nXStep\t1\nYStep\t1\n"
            "Phases\t2\n"
            "4;4;4\t90;90;90\tAl\t11\t225\n"
            "3;3;5\t90;90;120\tMg\t9\t194\n"
            "Phase\tX\tY\tBands\tError\tEuler1\tEuler2\tEuler3\tMAD\tBC\tBS\n"
        )
        rows = [
            "\t".join(str(v) for v in [phase, i % 2, i // 2, 8, 0, *euler, 0.1, 100, 100])
            for i, (phase, euler) in enumerate(zip(phases, angles))
        ]
        path.write_text(header + "\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    else:
        path = tmp_path / "texture.crc"
        header = (
            "[Job]\nXCells=2\nYCells=2\nGridDistX=1\nGridDistY=1\n"
            "[Fields]\nCount=3\nField1=3\nField2=4\nField3=5\n"
            "[Phases]\nCount=2\n"
            "[Phase1]\nStructureName=Al\nLaueGroup=11\n"
            "a=4\nb=4\nc=4\nAlpha=90\nBeta=90\nGamma=90\n"
            "[Phase2]\nStructureName=Mg\nLaueGroup=9\n"
            "a=3\nb=3\nc=5\nAlpha=90\nBeta=90\nGamma=120\n"
        )
        path.with_suffix(".cpr").write_text(header, encoding="utf-8", newline="\n")
        data = np.zeros(4, dtype=[("phase", "i1"), ("angles", "<f4", (3,))])
        data["phase"] = phases
        data["angles"] = np.deg2rad(angles)
        data.tofile(path)
    return path


def sample_file(path: Path, **kwargs) -> dict:
    path_key = "CTF_file_path" if path.suffix == ".ctf" else "CRC_file_path"
    return sample_texture_EBSD(
        **{
            path_key: path,
            "specimen_symmetry": "cubic",
            "EBSD_phase": "Al",
            "num_orientations": 12,
            **kwargs,
        }
    )


def read_sampling_progress(workflow_path: Path) -> list[str]:
    submissions = workflow_path / "artifacts" / "submissions"
    return [
        line
        for log_type in ("std", "stdout")
        for path in submissions.glob(f"*/js_std/*/*_{log_type}.log")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("Sampling orientation sets:")
    ]


@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.parametrize("log_name", ["js_0_std.log", "js_0_stdout.log"])
def test_read_sampling_progress(tmp_path: Path, log_name: str) -> None:
    log_dir = tmp_path / "artifacts" / "submissions" / "0" / "js_std" / "0"
    log_dir.mkdir(parents=True)
    (log_dir / log_name).write_text(
        "Other output\n"
        "Sampling orientation sets: 0/1 complete\n"
        "Sampling orientation sets: 1/1 complete\n",
        encoding="utf-8",
        newline="\n",
    )
    (log_dir / "js_0_stderr.log").write_text(
        "Sampling orientation sets: not stdout\n", encoding="utf-8", newline="\n"
    )
    assert read_sampling_progress(tmp_path) == [
        "Sampling orientation sets: 0/1 complete",
        "Sampling orientation sets: 1/1 complete",
    ]


@pytest.mark.parametrize("phase", ["Al", "Mg"])
def test_sample_texture_real_readers(
    ebsd_file: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")
    first = sample_file(ebsd_file, EBSD_phase=phase)["orientations"]
    second = sample_file(ebsd_file, EBSD_phase=phase)["orientations"]
    ori = Orientations(**first)
    assert ori.data.shape == (12, 4)
    assert np.all(np.isfinite(ori.data))
    np.testing.assert_allclose(np.linalg.norm(ori.data, axis=1), 1)
    np.testing.assert_array_equal(first["data"], second["data"])
    assert ori.representation.quat_order is QuatOrder.SCALAR_VECTOR
    alignment = (
        UnitCellAlignment(
            x=LatticeDirection.A, y=LatticeDirection.B, z=LatticeDirection.C
        )
        if phase == "Al"
        else UnitCellAlignment(
            x=LatticeDirection.A_STAR, y=LatticeDirection.B, z=LatticeDirection.C
        )
    )
    assert ori.unit_cell_alignment == alignment
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "5678")
    third = sample_file(ebsd_file, EBSD_phase=phase)["orientations"]
    assert not np.allclose(first["data"], third["data"])


@pytest.mark.parametrize(
    "transform",
    [
        "euler_to_spatial",
        "convertEuler2SpatialReferenceFrame",
        "spatial_to_euler",
        "convertSpatial2EulerReferenceFrame",
        None,
    ],
)
@pytest.mark.parametrize("keep", [None, "keep_XY", "keep_euler"])
def test_sample_texture_frames_and_rotation(
    ebsd_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    transform: str | None,
    keep: Literal["keep_XY", "keep_euler"] | None,
) -> None:
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")
    rotation: EBSDRotation = {"euler_angles_deg": [15, 25, 35]}
    if keep is not None:
        rotation[keep] = True
    with patch.object(
        mtex, "calcDensity", side_effect=lambda source, halfwidth: source
    ) as density:
        with patch.object(
            mtex, "discreteSample", side_effect=lambda source, n, rng: source
        ):
            result = sample_file(
                ebsd_file,
                num_orientations=2,
                EBSD_reference_frame_transformation=transform,
                EBSD_rotation=rotation,
            )

    expected = mtex.rotation.byEuler(
        np.array([10, 70]) * mtex.degree,
        np.array([20, 80]) * mtex.degree,
        np.array([30, 90]) * mtex.degree,
    )
    if transform in ("euler_to_spatial", "convertEuler2SpatialReferenceFrame"):
        expected = mtex.rotation.byAxisAngle(mtex.vector3d(0, 1, 0), np.pi) * expected
    if keep != "keep_euler":
        expected = (
            mtex.rotation.byEuler(*(np.array([15, 25, 35]) * mtex.degree)) * expected
        )
    source = density.call_args.args[0]
    np.testing.assert_allclose(source.data, expected.data, atol=1e-7)
    assert source.SS.sym.name == mtex.specimenFrame("cubic").sym.name
    np.testing.assert_allclose(
        result["orientations"]["data"], expected.inv().data, atol=1e-7
    )


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"num_orientations": 0}, "positive integer"),
        ({"num_orientations": -1}, "positive integer"),
        ({"sampling_method": "bad"}, "sampling_method"),
        ({"EBSD_reference_frame_transformation": "bad"}, "reference frame"),
        ({"EBSD_rotation": {"euler_angles_deg": [1, 2]}}, "three finite angles"),
        ({"EBSD_rotation": {"euler_angles_deg": [1, 2, np.nan]}}, "three finite angles"),
        (
            {
                "EBSD_rotation": {
                    "euler_angles_deg": [0, 0, 0],
                    "keep_XY": True,
                    "keep_euler": True,
                }
            },
            "not both",
        ),
        ({"EBSD_phase": "missing"}, "phase"),
    ],
)
def test_sample_texture_invalid_inputs(ebsd_file: Path, kwargs: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        sample_file(ebsd_file, **kwargs)


@pytest.mark.parametrize("halfwidth", [0, -1, 181, np.nan, np.inf, -np.inf, True])
def test_sample_texture_invalid_halfwidth(ebsd_file: Path, halfwidth: float) -> None:
    with pytest.raises(ValueError, match="kernel_halfwidth_deg"):
        sample_file(ebsd_file, kernel_halfwidth_deg=halfwidth)


@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.parametrize(
    "count", [0, -1, True, False, 1.5, "1", np.int64(0), np.int64(-1), np.bool_(True)]
)
def test_sample_texture_invalid_set_count(ebsd_file: Path, count: object) -> None:
    with pytest.raises(
        ValueError, match="num_orientation_sets must be a positive integer"
    ):
        sample_file(ebsd_file, num_orientation_sets=count)


@pytest.mark.parametrize("count", [1, 3])
def test_sample_texture_sets(
    ebsd_file: Path, monkeypatch: pytest.MonkeyPatch, count: int
) -> None:
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")
    with patch.object(mtex, "calcDensity", wraps=mtex.calcDensity) as density:
        first = sample_file(ebsd_file, num_orientation_sets=count)["orientations"]
    density.assert_called_once()
    second = sample_file(ebsd_file, num_orientation_sets=count)["orientations"]
    assert len(first) == count
    for member, repeated in zip(first, second):
        assert Orientations(**member).data.shape == (12, 4)
        np.testing.assert_array_equal(member["data"], repeated["data"])
    for member in first[1:]:
        assert not np.array_equal(first[0]["data"], member["data"])
    single = sample_file(ebsd_file)["orientations"]
    np.testing.assert_array_equal(first[0]["data"], single["data"])


@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.parametrize(
    "kwargs", [{}, {"num_orientation_sets": None}], ids=["omitted", "none"]
)
@pytest.mark.parametrize("sampling_method", ["discreteSample", "optimalSample"])
def test_sample_texture_single_set_without_progress(
    ebsd_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    kwargs: dict[str, None],
    sampling_method: Literal["discreteSample", "optimalSample"],
) -> None:
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")
    with (
        patch.object(mtex, "calcDensity", side_effect=lambda source, halfwidth: source),
        patch.object(
            mtex, "discreteSample", side_effect=lambda source, n, rng: source
        ) as sample,
        patch.object(
            mtex, "optimalSample", side_effect=lambda density, sampled: sampled
        ) as optimize,
    ):
        result = sample_file(
            ebsd_file, num_orientations=2, sampling_method=sampling_method, **kwargs
        )

    sample.assert_called_once()
    assert optimize.call_count == (1 if sampling_method == "optimalSample" else 0)
    assert isinstance(result["orientations"], dict)
    assert Orientations(**result["orientations"]).data.shape == (2, 4)
    assert "Sampling orientation sets:" not in capsys.readouterr().out


@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.parametrize("count", [1, 3, np.int8(127)])
@pytest.mark.parametrize("sampling_method", ["discreteSample", "optimalSample"])
def test_sample_texture_progress(
    ebsd_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    count: int | np.integer,
    sampling_method: Literal["discreteSample", "optimalSample"],
) -> None:
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")

    class FlushTrackingStream(StringIO):
        flushed_text = ""

        def flush(self) -> None:
            self.flushed_text = self.getvalue()
            super().flush()

    stream = FlushTrackingStream()
    progress_before_sample: list[list[str]] = []

    def progress_lines(text: str) -> list[str]:
        return [
            line
            for line in text.splitlines()
            if line.startswith("Sampling orientation sets:")
        ]

    def discrete_sample(source: Any, n: int, rng: np.random.Generator) -> Any:
        progress_before_sample.append(progress_lines(stream.flushed_text))
        return source

    with (
        redirect_stdout(stream),
        patch.object(mtex, "calcDensity", side_effect=lambda source, halfwidth: source),
        patch.object(mtex, "discreteSample", side_effect=discrete_sample),
        patch.object(
            mtex, "optimalSample", side_effect=lambda density, sampled: sampled
        ) as optimize,
    ):
        result = sample_file(
            ebsd_file,
            num_orientations=2,
            num_orientation_sets=count,
            sampling_method=sampling_method,
        )

    assert len(result["orientations"]) == count
    assert optimize.call_count == (count if sampling_method == "optimalSample" else 0)
    expected_progress = [
        f"Sampling orientation sets: {index}/{count} complete"
        for index in range(int(count) + 1)
    ]
    assert progress_before_sample == [
        expected_progress[: index + 1] for index in range(int(count))
    ]
    assert progress_lines(stream.flushed_text) == expected_progress


@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.parametrize("sampling_method", ["discreteSample", "optimalSample"])
def test_sample_texture_progress_on_failure(
    ebsd_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    sampling_method: Literal["discreteSample", "optimalSample"],
) -> None:
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")
    sample_count = 0

    def discrete_sample(source: Any, n: int, rng: np.random.Generator) -> Any:
        nonlocal sample_count
        sample_count += 1
        if sampling_method == "discreteSample" and sample_count == 2:
            raise RuntimeError("deliberate sampling failure")
        return source

    def optimal_sample(density: Any, sampled: Any) -> Any:
        if sample_count == 2:
            raise RuntimeError("deliberate sampling failure")
        return sampled

    with (
        patch.object(mtex, "calcDensity", side_effect=lambda source, halfwidth: source),
        patch.object(mtex, "discreteSample", side_effect=discrete_sample),
        patch.object(mtex, "optimalSample", side_effect=optimal_sample),
        pytest.raises(RuntimeError, match="deliberate sampling failure"),
    ):
        sample_file(
            ebsd_file,
            num_orientations=2,
            num_orientation_sets=3,
            sampling_method=sampling_method,
        )

    assert sample_count == 2
    assert [
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("Sampling orientation sets:")
    ] == [
        "Sampling orientation sets: 0/3 complete",
        "Sampling orientation sets: 1/3 complete",
    ]


def test_sample_texture_optimal_sets(
    ebsd_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")
    monkeypatch.setenv("MATFLOW_RUN_NUM_THREADS", "1")
    kwargs = {"sampling_method": "optimalSample", "num_orientation_sets": 2}
    first = sample_file(ebsd_file, **kwargs)["orientations"]
    second = sample_file(ebsd_file, **kwargs)["orientations"]
    assert len(first) == 2
    for member, repeated in zip(first, second):
        data = Orientations(**member).data
        assert data.shape == (12, 4)
        assert np.all(np.isfinite(data))
        np.testing.assert_allclose(np.linalg.norm(data, axis=1), 1)
        np.testing.assert_array_equal(member["data"], repeated["data"])
    assert not np.allclose(first[0]["data"], first[1]["data"])
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "5678")
    third = sample_file(ebsd_file, sampling_method="optimalSample")["orientations"]
    assert not np.allclose(first[0]["data"], third["data"])


@pytest.mark.parametrize("halfwidth", [None, 5.0, 25.0])
def test_sample_texture_halfwidth(
    ebsd_file: Path, monkeypatch: pytest.MonkeyPatch, halfwidth: float | None
) -> None:
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")
    kwargs = {} if halfwidth is None else {"kernel_halfwidth_deg": halfwidth}
    with patch.object(mtex, "calcDensity", wraps=mtex.calcDensity) as density:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sample_file(ebsd_file, specimen_symmetry="1", **kwargs)
    assert not any("halfwidth" in str(warning.message) for warning in caught)
    assert density.call_args.kwargs["halfwidth"] == pytest.approx(
        (10.0 if halfwidth is None else halfwidth) * np.pi / 180
    )


def test_sample_texture_requires_one_file() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        sample_texture_EBSD("cubic", "Al", 12)
    with pytest.raises(ValueError, match="exactly one"):
        sample_texture_EBSD(
            "cubic", "Al", 12, CTF_file_path="a.ctf", CRC_file_path="a.crc"
        )


def test_crc_requires_cpr(ebsd_file: Path) -> None:
    if ebsd_file.suffix != ".crc":
        pytest.skip("CRC-specific error")
    ebsd_file.with_suffix(".cpr").unlink()
    with pytest.raises(ValueError, match="no .cpr beside"):
        sample_file(ebsd_file)


@pytest.mark.parametrize("num_threads", [None, "3"])
def test_sample_texture_threads(
    ebsd_file: Path, monkeypatch: pytest.MonkeyPatch, num_threads: str | None
) -> None:
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")
    if num_threads is None:
        monkeypatch.delenv("MATFLOW_RUN_NUM_THREADS", raising=False)
    else:
        monkeypatch.setenv("MATFLOW_RUN_NUM_THREADS", num_threads)
    with patch.object(mtex, "setMTEXpref") as set_pref:
        sample_file(ebsd_file, specimen_symmetry="1")
    if num_threads is None:
        set_pref.assert_not_called()
    else:
        set_pref.assert_called_once_with("threads", 3)


@pytest.mark.parametrize("file_type", ["CTF", "CRC"])
@pytest.mark.parametrize("sampling_method", ["discreteSample", "optimalSample"])
def test_sample_texture_schema(file_type: str, sampling_method: str) -> None:
    template = mf.WorkflowTemplate.from_YAML_string(
        "name: sample_texture_python\n"
        "tasks:\n"
        f"  - schema: sample_texture_from_{file_type}_file_mtex_python\n"
        "    inputs:\n"
        f"      {file_type}_file_path: texture.{file_type.lower()}\n"
        "      specimen_symmetry: cubic\n"
        "      EBSD_phase: Al\n"
        "      num_orientations: 12\n"
        f"      sampling_method: {sampling_method}\n"
        "      EBSD_euler_correction:\n"
        "        euler_angles_deg: [0, 180, 0]\n"
    )
    assert template.tasks[0].all_schema_outputs[0].parameter.typ == "orientations"
    schema = mf.task_schemas.get(f"sample_texture_from_{file_type}_file_mtex_python")
    assert schema.outputs[0].multiplicity == "<<input:num_orientation_sets>>"
    count_input = next(
        item for item in schema.inputs if item.parameter.typ == "num_orientation_sets"
    )
    assert count_input.default_value.value is None
    method_input = next(
        item for item in schema.inputs if item.parameter.typ == "sampling_method"
    )
    assert method_input.default_value.value == "discreteSample"
    action = schema.actions[0]
    assert set(action.script_data_in) == {
        f"inputs.{file_type}_file_path",
        "inputs.specimen_symmetry",
        "inputs.EBSD_phase",
        "inputs.num_orientations",
        "inputs.num_orientation_sets",
        "inputs.sampling_method",
        "inputs.kernel_halfwidth_deg",
        "inputs.EBSD_reference_frame_transformation",
        "inputs.EBSD_rotation",
        "inputs.EBSD_euler_correction",
    }
    assert all(value["format"] == "direct" for value in action.script_data_in.values())
    assert action.script_data_out == {"outputs.orientations": {"format": "direct"}}


@pytest.mark.parametrize("angles", [[0, 0, 0], [0, 180, 0], [90, 180, 270], [15, 25, 35]])
@pytest.mark.parametrize("transform", ["euler_to_spatial", None, "spatial_to_euler"])
def test_explicit_import_correction(ebsd_file, monkeypatch, angles, transform):
    """The same physical correction wins over every legacy selection, before map rotation."""
    monkeypatch.setenv("MATFLOW_RUN_RANDOM_SEED", "1234")
    raw = mtex.rotation.byEuler(
        np.array([10, 70]) * mtex.degree,
        np.array([20, 80]) * mtex.degree,
        np.array([30, 90]) * mtex.degree,
    )
    correction = mtex.rotation.byEuler(*(np.array(angles) * mtex.degree))
    after = mtex.rotation.byEuler(*(np.array([17, 29, 41]) * mtex.degree))
    with patch.object(mtex, "calcDensity", side_effect=lambda source, halfwidth: source):
        with patch.object(
            mtex, "discreteSample", side_effect=lambda source, n, rng: source
        ):
            result = sample_file(
                ebsd_file,
                num_orientations=2,
                EBSD_reference_frame_transformation=transform,
                EBSD_euler_correction={"euler_angles_deg": angles},
                EBSD_rotation={"euler_angles_deg": [17, 29, 41], "keep_XY": True},
            )
    actual = result["orientations"]["data"]
    expected = (after * correction * raw).inv().data
    # q and -q describe the same rotation.
    np.testing.assert_allclose(np.abs(np.sum(actual * expected, axis=1)), 1, atol=1e-7)


@pytest.mark.parametrize(
    "correction",
    [
        {},
        {"euler_angles_deg": [1, 2]},
        {"euler_angles_deg": [1, 2, np.nan]},
        {"euler_angles_deg": "invalid"},
        "invalid",
    ],
)
def test_invalid_import_correction(ebsd_file, correction):
    with pytest.raises(ValueError, match="EBSD_euler_correction.*three finite angles"):
        sample_file(ebsd_file, EBSD_euler_correction=correction)


@pytest.mark.integration
@pytest.mark.parametrize("angles", [[0, 0, 0], [0, 180, 0], [90, 180, 270]])
def test_matlab_explicit_import_correction(
    ebsd_file, tmp_path, angles, require_matlab_env
):
    """A narrow sampled texture must remain near independently corrected source rotations."""
    import yaml

    file_type = ebsd_file.suffix[1:].upper()
    inputs = {
        f"{file_type}_file_path": str(ebsd_file),
        "specimen_symmetry": "1",
        "EBSD_phase": "Al",
        "num_orientations": 64,
        "kernel_halfwidth_deg": 2.0,
        "EBSD_euler_correction": {"euler_angles_deg": angles},
        "EBSD_rotation": {"euler_angles_deg": [17, 29, 41], "keep_XY": True},
    }
    template = mf.WorkflowTemplate.from_YAML_string(
        yaml.safe_dump(
            {
                "name": "matlab_import_correction",
                "resources": {"any": {"random_seed": 1234, "num_threads": 1}},
                "tasks": [
                    {
                        "schema": f"sample_texture_from_{file_type}_file_mtex",
                        "inputs": inputs,
                    }
                ],
            }
        )
    )
    workflow = mf.Workflow.from_template(template, path=tmp_path)
    workflow.submit(wait=True, add_to_known=False)
    reopened = mf.Workflow(workflow.path)
    assert all(run.status.name == "success" for run in reopened.get_all_EARs())
    value = reopened.tasks[0].elements[0].outputs.orientations.value
    actual = value.data.copy()
    actual[:, 1:] *= -1
    cs = mtex.crystalFrame("cubic")
    actual = mtex.orientation(actual, cs, mtex.specimenFrame("1"))
    source = mtex.rotation.byEuler(
        np.array([10, 70]) * mtex.degree,
        np.array([20, 80]) * mtex.degree,
        np.array([30, 90]) * mtex.degree,
    )
    correction = mtex.rotation.byEuler(*(np.asarray(angles) * mtex.degree))
    after = mtex.rotation.byEuler(*(np.array([17, 29, 41]) * mtex.degree))
    expected = mtex.orientation((after * correction * source).data, cs, actual.SS)
    distances = np.minimum(actual.angle(expected[0]), actual.angle(expected[1]))
    assert np.max(distances) < 15 * mtex.degree


@pytest.mark.integration
@pytest.mark.parametrize("halfwidth", [None, 25.0])
@pytest.mark.parametrize(
    "count, explicit_count",
    [(None, False), (None, True), (1, True), (3, True)],
    ids=["default", "none", "one", "three"],
)
def test_sample_texture_workflow(
    ebsd_file: Path,
    tmp_path: Path,
    halfwidth: float | None,
    count: int | None,
    explicit_count: bool,
) -> None:
    file_type = ebsd_file.suffix[1:].upper()
    template = mf.WorkflowTemplate.from_YAML_string(
        "name: sample_texture_python\n"
        "resources:\n"
        "  any:\n"
        "    random_seed: 1234\n"
        "tasks:\n"
        f"  - schema: sample_texture_from_{file_type}_file_mtex_python\n"
        "    inputs:\n"
        f"      {file_type}_file_path: '{ebsd_file}'\n"
        "      specimen_symmetry: '1'\n"
        "      EBSD_phase: Al\n"
        "      num_orientations: 12\n"
        + (
            f"      num_orientation_sets: {count if count is not None else 'null'}\n"
            if explicit_count
            else ""
        )
        + ("" if halfwidth is None else f"      kernel_halfwidth_deg: {halfwidth}\n")
    )
    template.tasks.append(
        mf.Task(
            mf.TaskSchema(
                objective="consume_orientation_set",
                inputs=[mf.SchemaInput("orientations")],
            )
        )
    )
    workflow = mf.Workflow.from_template(template, path=tmp_path)
    assert workflow.tasks[1].num_elements == (count or 1)
    workflow.submit(wait=True, add_to_known=False)
    expected_progress = (
        []
        if count is None
        else [
            f"Sampling orientation sets: {index}/{count} complete"
            for index in range(count + 1)
        ]
    )
    assert read_sampling_progress(Path(workflow.path)) == expected_progress
    output = workflow.tasks[0].elements[0].outputs.orientations.value
    reopened = mf.Workflow(workflow.path)
    persisted = reopened.tasks[0].elements[0].outputs.orientations.value
    if count is None:
        assert isinstance(output, Orientations)
        assert isinstance(persisted, Orientations)
        assert persisted == output
        members = [output]
    else:
        assert isinstance(output, list)
        assert isinstance(persisted, list)
        assert len(output) == len(persisted) == count
        members = [Orientations(**data) for data in output]
        assert [Orientations(**data) for data in persisted] == members
    for member in members:
        assert member.data.shape == (12, 4)
        np.testing.assert_allclose(np.linalg.norm(member.data, axis=1), 1)
    for idx, element in enumerate(reopened.tasks[1].elements):
        assert element.inputs.orientations.value == members[idx]
