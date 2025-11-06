import numpy as np

from cipher_parse import (
    CIPHERInput,
    MaterialDefinition,
    InterfaceDefinition,
    PhaseTypeDefinition,
    CIPHERGeometry,
)


def generate_phase_field_input_from_volume_element(
    volume_element,
    materials,
    interfaces,
    phase_type_map,
    size,
    components,
    outputs,
    solution_parameters,
    random_seed,
    interface_binning,
    keep_3D,
    combine_phases=None,
):
    mats = []
    for mat_i in materials:
        if "phase_types" in mat_i:
            mat_i["phase_types"] = [
                PhaseTypeDefinition(**j) for j in mat_i["phase_types"]
            ]
        mat_i = MaterialDefinition(**mat_i)
        mats.append(mat_i)

    interfaces = [InterfaceDefinition(**int_i) for int_i in interfaces]

    geom = _volume_element_to_cipher_geometry(
        volume_element=volume_element,
        cipher_materials=mats,
        cipher_interfaces=interfaces,
        phase_type_map=phase_type_map,
        size=size,
        random_seed=random_seed,
        keep_3D=keep_3D,
        combine_phases=combine_phases,
    )

    inp = CIPHERInput(
        geometry=geom,
        components=components,
        outputs=outputs,
        solution_parameters=solution_parameters,
    )

    if interface_binning:
        inp.bin_interfaces_by_misorientation_angle(**interface_binning)

    phase_field_input = inp.to_JSON(keep_arrays=True)

    return {"phase_field_input": phase_field_input}


def _volume_element_to_cipher_geometry(
    volume_element,
    cipher_materials,
    cipher_interfaces,
    combine_phases,
    phase_type_map=None,
    size=None,
    random_seed=None,
    keep_3D=False,
):

    uq, inv = np.unique(volume_element["constituent_phase_label"], return_inverse=True)
    cipher_phases = {i: np.where(inv == idx)[0] for idx, i in enumerate(uq)}
    orientations = volume_element["orientations"]["quaternions"]
    orientations = np.array(orientations)

    # we need P=-1, because that's what DAMASK Rotation object assumes, which
    # we use when/if finding the disorientations for the
    # misorientation_matrix:
    if volume_element["orientations"]["P"] == 1:
        # multiple vector part by -1 to get P=-1:
        if volume_element["orientations"]["quat_component_ordering"] == "scalar-vector":
            quat_vec_idx = [1, 2, 3]
        else:
            quat_vec_idx = [0, 1, 2]
        orientations[:, quat_vec_idx] *= -1

    for mat_name_i in cipher_phases:
        phases_set = False
        if phase_type_map:
            phase_type_name = phase_type_map[mat_name_i]
        else:
            phase_type_name = mat_name_i
        for mat in cipher_materials:
            for phase_type_i in mat.phase_types:
                if phase_type_i.name == phase_type_name:
                    phase_i_idx = cipher_phases[mat_name_i]
                    phase_type_i.phases = phase_i_idx
                    phase_type_i.orientations = orientations[phase_i_idx]
                    phases_set = True
                    break
            if phases_set:
                break

        if not phases_set:
            raise ValueError(
                f"No defined material/phase-type for VE phase {mat_name_i!r}"
            )

    voxel_phase = volume_element["element_material_idx"]
    size = volume_element["size"] if size is None else size
    if voxel_phase.ndim == 3 and voxel_phase.shape[2] == 1 and not keep_3D:
        voxel_phase = voxel_phase[..., 0]
        size = size[:2]

    geom = CIPHERGeometry(
        voxel_phase=voxel_phase,
        size=size,
        materials=cipher_materials,
        interfaces=cipher_interfaces,
        random_seed=random_seed,
        combine_phases=combine_phases,
    )
    return geom
