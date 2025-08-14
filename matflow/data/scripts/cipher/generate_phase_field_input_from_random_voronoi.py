from cipher_parse import (
    CIPHERInput,
    MaterialDefinition,
    InterfaceDefinition,
    PhaseTypeDefinition,
)


def generate_phase_field_input_from_random_voronoi(
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
    combine_phases,
):
    # initialise `MaterialDefinition`, `InterfaceDefinition` and
    # `PhaseTypeDefinition` objects:
    mats = []
    for mat_i in materials:
        if "phase_types" in mat_i:
            mat_i["phase_types"] = [
                PhaseTypeDefinition(**j) for j in mat_i["phase_types"]
            ]
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
    phase_field_input = inp.to_JSON(keep_arrays=True)

    return {"phase_field_input": phase_field_input}
