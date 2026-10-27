from pathlib import Path

import pytest

import matflow as mf


@pytest.mark.parametrize("file_type", ["CTF", "CRC"])
@pytest.mark.parametrize("halfwidth", [None, 25.0])
@pytest.mark.parametrize("execution_mode", ["script", "compile", "precompiled"])
def test_sample_texture_matlab_schema(
    file_type: str, halfwidth: float | None, execution_mode: str
) -> None:
    schema_name = f"sample_texture_from_{file_type}_file_mtex"
    template = mf.WorkflowTemplate.from_YAML_string(
        "name: sample_texture_matlab\n"
        "tasks:\n"
        f"  - schema: {schema_name}\n"
        "    inputs:\n"
        f"      execution_mode: {execution_mode}\n"
        f"      {file_type}_file_path: texture.{file_type.lower()}\n"
        "      specimen_symmetry: '1'\n"
        "      EBSD_phase: Al\n"
        "      num_orientations: 12\n"
        + ("" if halfwidth is None else f"      kernel_halfwidth_deg: {halfwidth}\n")
    )
    assert template.tasks[0].all_schema_outputs[0].parameter.typ == "orientations"
    schema = mf.task_schemas.get(schema_name)
    assert schema.outputs[0].multiplicity is None
    inputs = {item.parameter.typ: item for item in schema.inputs}
    defaults = {
        name: item.default_value.value
        for name, item in inputs.items()
        if item.default_value is not None
    }
    assert defaults["kernel_halfwidth_deg"] == 10.0
    assert "num_orientation_sets" not in inputs
    assert defaults["execution_mode"] == "script"
    assert defaults["EBSD_reference_frame_transformation"] == "euler_to_spatial"
    assert defaults["EBSD_rotation"] is None

    expected_inputs = {f"inputs.{name}": {"format": "json"} for name in inputs}
    expected_outputs = {"outputs.orientations": {"format": "hdf5"}}
    assert len(schema.actions) == 4
    for action in schema.actions[1:3]:
        assert action.script_data_in == expected_inputs
        assert action.script_data_out == expected_outputs
    assert schema.actions[3].program_data_in == expected_inputs
    assert schema.actions[3].program_data_out == expected_outputs
