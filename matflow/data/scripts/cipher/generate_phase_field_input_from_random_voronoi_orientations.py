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
