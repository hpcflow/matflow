import matflow as mf


def import_VE(
    workflow_path, task_name, element_idx, iteration_idx, iteration_ID, input_or_output
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
        VE = parent.inputs.volume_element.value
    elif input_or_output == "output":
        VE = parent.outputs.volume_element.value

    # convert Zarr arrays to numpy arrays (TODO: should be able to encode Zarr arrays directly!)
    # TODO: only works for quat orientations!
    VE = {
        "size": list(VE["size"]),
        "grid_size": VE["grid_size"][:],
        "orientations": {
            "type": VE["orientations"]["type"],
            "quaternions": VE["orientations"]["quaternions"][:],
            "quat_component_ordering": VE["orientations"]["quat_component_ordering"],
            "unit_cell_alignment": VE["orientations"]["unit_cell_alignment"],
            "use_max_precision": VE["orientations"]["use_max_precision"],
            "P": VE["orientations"]["P"],
        },
        "element_material_idx": VE["element_material_idx"][:],
        "constituent_material_idx": VE["constituent_material_idx"][:],
        "constituent_material_fraction": VE["constituent_material_fraction"][:],
        "constituent_phase_label": VE["constituent_phase_label"][:],
        "constituent_orientation_idx": VE["constituent_orientation_idx"][:],
        "material_homog": VE["material_homog"][:],
    }
    return {"volume_element": VE}
