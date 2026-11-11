"""Ordered input orientation assignment when parsing Dream3D volume elements."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

import matflow as mf
from matflow.param_classes.orientations import (
    LatticeDirection,
    OrientationRepresentation,
    Orientations,
    UnitCellAlignment,
)

h5py = pytest.importorskip("h5py")
pytest.importorskip("damask_parse")

from matflow.data.scripts.dream_3D.parse_dream_3D_volume_element import (
    parse_dream_3D_volume_element,
)


@pytest.fixture
def dream3d_file(tmp_path: Path) -> Path:
    path = tmp_path / "pipeline.dream3d"
    with h5py.File(path, "w") as file:
        volume = file.create_group("DataContainers/SyntheticVolumeDataContainer")
        geometry = volume.create_group("_SIMPL_GEOMETRY")
        geometry["DIMENSIONS"] = [3, 1, 1]
        geometry["SPACING"] = [0.5, 1.0, 1.0]
        cells = volume.create_group("CellData")
        cells["FeatureIds"] = np.array([[[[1], [2], [3]]]], dtype=np.int32)
        ensemble = volume.create_group("CellEnsembleData")
        ensemble["PhaseName"] = np.array([[b"Unknown"], [b"Al"], [b"Cu"]])
        ensemble["CrystalStructures"] = np.array([[999], [1], [1]], dtype=np.uint32)
        grains = volume.create_group("Grain Data")
        grains["Phases"] = np.array([0, 1, 1, 1], dtype=np.int32)
        grains["EulerAngles"] = np.zeros((4, 3), dtype=np.float32)
    return path


def orientations(
    data: list[list[float]] | np.ndarray,
    representation: dict[str, Any] | None = None,
    alignment: UnitCellAlignment | None = None,
) -> Orientations:
    return Orientations(
        data=np.asarray(data),
        representation=OrientationRepresentation(
            **(representation or {"type": "quaternion", "quat_order": "scalar_vector"})
        ),
        unit_cell_alignment=alignment
        or UnitCellAlignment(
            x=LatticeDirection.A, y=LatticeDirection.B, z=LatticeDirection.C
        ),
    )


def test_direct_assignment_is_ordered_and_does_not_modify_file(
    dream3d_file: Path,
) -> None:
    supplied = orientations(np.eye(4))
    before_data = supplied.data.copy()
    before_file = dream3d_file.read_bytes()

    result = parse_dream_3D_volume_element(str(dream3d_file), supplied)

    np.testing.assert_array_equal(result["orientations"]["quaternions"], np.eye(4)[:3])
    np.testing.assert_array_equal(result["constituent_orientation_idx"], [0, 1, 2])
    np.testing.assert_array_equal(result["element_material_idx"][:, 0, 0], [0, 1, 2])
    np.testing.assert_array_equal(supplied.data, before_data)
    assert dream3d_file.read_bytes() == before_file
    assert result["size"] == [1.5, 1.0, 1.0]
    assert result["orientations"]["unit_cell_alignment"] == {"x": "a"}


@pytest.mark.parametrize("direct", [True, False])
def test_without_input_preserves_native_orientations(
    dream3d_file: Path, direct: bool
) -> None:
    result = parse_dream_3D_volume_element(
        str(dream3d_file), assign_orientations_directly=direct
    )
    np.testing.assert_array_equal(
        result["orientations"]["quaternions"], [[1, 0, 0, 0]] * 3
    )


def test_disabled_ignores_insufficient_input(dream3d_file: Path) -> None:
    supplied = orientations([[0, 1, 0, 0]])
    result = parse_dream_3D_volume_element(
        str(dream3d_file), supplied, assign_orientations_directly=False
    )
    np.testing.assert_array_equal(
        result["orientations"]["quaternions"], [[1, 0, 0, 0]] * 3
    )


@pytest.mark.parametrize("count", [0, 2])
def test_insufficient_orientations_raise(dream3d_file: Path, count: int) -> None:
    supplied = orientations(np.tile([1.0, 0, 0, 0], (count, 1)))
    with pytest.raises(
        ValueError, match=rf"Insufficient.*'Al'.*{count} supplied, 3 grains"
    ):
        parse_dream_3D_volume_element(str(dream3d_file), supplied)


@pytest.mark.parametrize(
    "representation,data,expected",
    [
        (
            {"type": "quaternion", "quat_order": "vector_scalar"},
            [[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0]],
            [[0, 0, 1, 0], [0, 0, 0, 1], [0, 1, 0, 0]],
        ),
        (
            {"type": "euler", "euler_is_degrees": True, "euler_definition": "bunge"},
            [[0, 0, 0], [90, 0, 0], [0, 90, 0]],
            [
                [1, 0, 0, 0],
                [2**-0.5, 0, 0, -(2**-0.5)],
                [2**-0.5, -(2**-0.5), 0, 0],
            ],
        ),
        (
            {"type": "euler", "euler_is_degrees": False, "euler_definition": "bunge"},
            [[0, 0, 0], [np.pi / 2, 0, 0], [0, np.pi / 2, 0]],
            [
                [1, 0, 0, 0],
                [2**-0.5, 0, 0, -(2**-0.5)],
                [2**-0.5, -(2**-0.5), 0, 0],
            ],
        ),
    ],
)
def test_orientation_representations(
    dream3d_file: Path,
    representation: dict[str, Any],
    data: list[list[float]],
    expected: list[list[float]],
) -> None:
    supplied = orientations(
        data,
        representation=representation,
        alignment=UnitCellAlignment(x=LatticeDirection.A),
    )
    result = parse_dream_3D_volume_element(str(dream3d_file), supplied)
    np.testing.assert_allclose(
        result["orientations"]["quaternions"], expected, atol=1e-14
    )


def test_first_phase_only_in_grain_id_order(dream3d_file: Path) -> None:
    with h5py.File(dream3d_file, "r+") as file:
        file["DataContainers/SyntheticVolumeDataContainer/Grain Data/Phases"][...] = [
            0,
            1,
            2,
            1,
        ]
    supplied = orientations([[0, 1, 0, 0], [0, 0, 1, 0]])
    result = parse_dream_3D_volume_element(str(dream3d_file), supplied)
    np.testing.assert_array_equal(
        result["orientations"]["quaternions"],
        [[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]],
    )
    np.testing.assert_array_equal(result["constituent_phase_label"], ["Al", "Cu", "Al"])


def test_hexagonal_alignment_is_converted(dream3d_file: Path) -> None:
    with h5py.File(dream3d_file, "r+") as file:
        file[
            "DataContainers/SyntheticVolumeDataContainer/CellEnsembleData/CrystalStructures"
        ][1] = 0
    supplied = orientations(
        [[1, 0, 0, 0]] * 3, alignment=UnitCellAlignment.from_hex_convention_MTEX()
    )
    result = parse_dream_3D_volume_element(str(dream3d_file), supplied)
    np.testing.assert_allclose(
        result["orientations"]["quaternions"],
        [[np.cos(np.pi / 12), 0, 0, np.sin(np.pi / 12)]] * 3,
        atol=1e-14,
    )
    assert result["orientations"]["unit_cell_alignment"] == {"x": "a"}


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, 0.0])
def test_invalid_quaternions_raise(dream3d_file: Path, bad_value: float) -> None:
    supplied = orientations([[bad_value, 0, 0, 0]] * 3)
    with pytest.raises(ValueError, match="finite|nonzero"):
        parse_dream_3D_volume_element(str(dream3d_file), supplied)


def test_schema_wires_default_to_parser() -> None:
    template = mf.WorkflowTemplate.from_YAML_string(
        """
name: test_direct_orientation_assignment
tasks:
  - schema: generate_volume_element_from_statistics
"""
    )
    schema = template.tasks[0].schemas[0]
    option = next(
        i for i in schema.inputs if i.parameter.typ == "assign_orientations_directly"
    )
    assert option.default_value is not None
    assert option.default_value.value is True
    parser = schema.actions[-1].output_file_parsers[0]
    assert parser.inputs == ["orientations", "assign_orientations_directly"]


def test_nonunit_quaternions_are_normalized_without_mutation(dream3d_file: Path) -> None:
    supplied = orientations([[0, 2, 0, 0]] * 3)
    result = parse_dream_3D_volume_element(str(dream3d_file), supplied)
    np.testing.assert_array_equal(
        result["orientations"]["quaternions"], [[0, 1, 0, 0]] * 3
    )
    np.testing.assert_array_equal(supplied.data, [[0, 2, 0, 0]] * 3)


def test_unsupported_hexagonal_alignment_raises(dream3d_file: Path) -> None:
    with h5py.File(dream3d_file, "r+") as file:
        file[
            "DataContainers/SyntheticVolumeDataContainer/CellEnsembleData/CrystalStructures"
        ][1] = 0
    supplied = orientations(
        [[1, 0, 0, 0]] * 3, alignment=UnitCellAlignment(z=LatticeDirection.C)
    )
    with pytest.raises(NotImplementedError, match="unit cell alignment"):
        parse_dream_3D_volume_element(str(dream3d_file), supplied)


@pytest.mark.integration
def test_workflow_default_and_odf_opt_out(tmp_path: Path) -> None:
    if not any(env.name == "dream_3D_env" for env in mf.envs):
        pytest.skip("Requires a configured dream_3D_env.")
    data = np.random.default_rng(42).normal(size=(100, 4))
    data /= np.linalg.norm(data, axis=1, keepdims=True)
    template = mf.WorkflowTemplate.from_YAML_string(
        f"""
name: direct_orientation_assignment
tasks:
  - schema: generate_volume_element_from_statistics
    save_files: [dream_3D_hdf5_file]
    inputs: &ve_inputs
      grid_size: [8, 8, 8]
      size: [1, 1, 1]
      phase_statistics:
        - type: primary
          name: Al
          crystal_structure: cubic
          volume_fraction: 1.0
          size_distribution:
            ESD_mean: 0.5
            ESD_log_stddev: 0.05
            num_bins: 10
      orientations:
        data: {data.tolist()}
        representation: {{type: quaternion, quat_order: scalar_vector}}
        unit_cell_alignment: {{x: a, y: b, z: c}}
  - schema: generate_volume_element_from_statistics
    save_files: [dream_3D_hdf5_file]
    inputs:
      <<: *ve_inputs
      assign_orientations_directly: false
"""
    )
    workflow = mf.Workflow.from_template(template, path=tmp_path)
    workflow.submit(wait=True, add_to_known=False, status=False)
    assert all(run.status.name == "success" for run in workflow.get_all_EARs())
    for task_idx, direct in enumerate((True, False)):
        element = workflow.tasks[task_idx].elements[0]
        assert element.inputs.assign_orientations_directly.value is direct
        actual = element.outputs.volume_element.value["orientations"]["quaternions"]
        task_artifacts = (
            Path(str(workflow.path)) / "artifacts" / "tasks" / f"t_{task_idx}"
        )
        files = list(task_artifacts.rglob("pipeline.dream3d"))
        assert len(files) == 1
        path = files[0]
        native = parse_dream_3D_volume_element(str(path))["orientations"]["quaternions"]
        if direct:
            np.testing.assert_allclose(actual, data[: len(actual)], atol=1e-14)
            assert not np.allclose(actual, native)
        else:
            np.testing.assert_array_equal(actual, native)
