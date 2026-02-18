from matflow.param_classes.orientations import Orientations
import numpy as np

from cipher_parse import (
    CIPHERInput,
    MaterialDefinition,
    InterfaceDefinition,
    PhaseTypeDefinition,
)


def generate_phase_field_input_from_random_voronoi_orientations(
    materials,
    interfaces,
    num_phases,
    grid_size,
    size,
    components,
    outputs,
    solution_parameters,
    random_seed,
    is_periodic,
    orientations,
    interface_binning,
    combine_phases,
):
    try:
        quats = orientations["quaternions"]
    except TypeError:
        # Convert to old matflow format
        orientations =  _convert_orientations_to_old_matflow_format(orientations)
        quats = orientations["quaternions"]

    # initialise `MaterialDefinition`, `InterfaceDefinition` and
    # `PhaseTypeDefinition` objects:
    mats = []
    for mat_idx, mat_i in enumerate(materials):
        if "phase_types" in mat_i:
            mat_i["phase_types"] = [
                PhaseTypeDefinition(**j) for j in mat_i["phase_types"]
            ]
        else:
            mat_i["phase_types"] = [PhaseTypeDefinition()]

        if mat_idx == 0:
            # add oris to the first defined phase type of the first material:
            mat_i["phase_types"][0].orientations = quats

        mat_i = MaterialDefinition(**mat_i)
        mats.append(mat_i)

    interfaces = [InterfaceDefinition(**int_i) for int_i in interfaces]

    inp = CIPHERInput.from_random_voronoi(
        materials=mats,
        interfaces=interfaces,
        num_phases=num_phases,
        grid_size=grid_size,
        size=size,
        components=components,
        outputs=outputs,
        solution_parameters=solution_parameters,
        random_seed=random_seed,
        is_periodic=is_periodic,
        combine_phases=combine_phases,
    )

    if interface_binning:
        inp.bin_interfaces_by_misorientation_angle(**interface_binning)

    phase_field_input = inp.to_JSON(keep_arrays=True)

    return {"phase_field_input": phase_field_input}


# This code is copied from dream3D/generate_volume_element_statistics.py
def _convert_orientations_to_old_matflow_format(orientations: Orientations):
    # see `LatticeDirection` enum:
    align_lookup = {
        "A": "a",
        "B": "b",
        "C": "c",
        "A_STAR": "a*",
        "B_STAR": "b*",
        "C_STAR": "c*",
    }
    unit_cell_alignment = {
        "x": align_lookup[orientations.unit_cell_alignment.x.name],
        "y": align_lookup[orientations.unit_cell_alignment.y.name],
        "z": align_lookup[orientations.unit_cell_alignment.z.name],
    }
    type_lookup = {
        "QUATERNION": "quat",
        "EULER": "euler",
    }
    type_ = type_lookup[orientations.representation.type.name]
    oris = {
        "type": type_,
        "unit_cell_alignment": unit_cell_alignment,
    }

    if type_ == "quat":
        quat_order = orientations.representation.quat_order.name.lower().replace("_", "-")
        oris["quaternions"] = np.array(orientations.data)
        oris["quat_component_ordering"] = quat_order
    elif type_ == "euler":
        oris["euler_angles"] = np.array(orientations.data)
        oris["euler_degrees"] = orientations.representation.euler_is_degrees

    return oris
