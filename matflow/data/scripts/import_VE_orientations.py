import matflow as mf
from damask_parse.utils import validate_orientations


def import_VE_orientations(
    workflow_path, iteration_ID, task_name, element_idx, iteration_idx, input_or_output
):
    wk = mf.Workflow(workflow_path)
    if iteration_ID is not None:
        parent = wk.get_element_iterations_from_IDs([iteration_ID])[0]
    else:
        task = getattr(wk.tasks, task_name)
        parent = task.elements[element_idx]
        if iteration_idx is not None:
            parent = parent.iterations[iteration_idx]

    if input_or_output == "input":
        oris = parent.inputs.volume_element.value["orientations"]
    elif input_or_output == "output":
        oris = parent.outputs.volume_element.value["orientations"]

    # convert Zarr arrays to numpy arrays (TODO: should be able to encode Zarr arrays directly!)

    # see `LatticeDirection` enum:
    align_lookup = {
        "a": "A",
        "b": "B",
        "c": "C",
        "a*": "A_STAR",
        "b*": "B_STAR",
        "c*": "C_STAR",
    }
    unit_cell_alignment = {
        "x": align_lookup[oris["unit_cell_alignment"]["x"]],
        "y": align_lookup[oris["unit_cell_alignment"]["y"]],
        "z": align_lookup[oris["unit_cell_alignment"]["z"]],
    }
    type_lookup = {
        "quat": "QUATERNION",
        "euler": "EULER",
    }
    type_ = type_lookup[oris["type"]]

    oris_repr = {"type": type_}
    if type_ == "QUATERNION":
        oris_repr["quat_order"] = (
            oris["quat_component_ordering"].upper().replace("-", "_")
        )
    elif type_ == "EULER":
        oris_repr["euler_is_degrees"] = oris["euler_degrees"]

    oris = {
        "data": oris["quaternions"][:],
        "unit_cell_alignment": unit_cell_alignment,
        "representation": oris_repr,
    }
    return {"orientations": oris}
