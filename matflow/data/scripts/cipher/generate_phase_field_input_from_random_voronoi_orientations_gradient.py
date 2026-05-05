import numpy as np

from cipher_parse.utilities import read_shockley, sample_from_orientations_gradient
from cipher_parse import (
    CIPHERInput,
    MaterialDefinition,
    InterfaceDefinition,
    PhaseTypeDefinition,
)


def generate_phase_field_input_from_random_voronoi_orientations_gradient(
    materials,
    interfaces,
    num_phases,
    grid_size,
    size,
    components,
    outputs,
    solution_parameters,
    orientation_gradient,
    random_seed,
    is_periodic,
    interface_binning,
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

    if orientation_gradient:
        phase_centroids = inp.geometry.get_phase_voxel_centroids()
        ori_range, ori_idx = sample_from_orientations_gradient(
            phase_centroids=phase_centroids,
            max_misorientation_deg=orientation_gradient["max_misorientation_deg"],
        )
        oris = np.zeros((phase_centroids.shape[0], 4))
        oris[ori_idx] = ori_range
        inp.geometry.phase_orientation = oris

        new_phase_ori = np.copy(inp.geometry.phase_orientation)

        if "add_highly_misoriented_grain" in orientation_gradient:
            add_HMG = orientation_gradient["add_highly_misoriented_grain"]
            if add_HMG is True:
                phase_idx = np.argmin(
                    np.sum(
                        (phase_centroids - (inp.geometry.size * np.array([0.3, 0.5])))
                        ** 2,
                        axis=1,
                    )
                )
            else:
                phase_idx = add_HMG

            # consider a fraction to be misoriented by (1 == max_misorientation_deg)
            if "highly_misoriented_grain_misorientation" in orientation_gradient:
                HMG_misori = orientation_gradient[
                    "highly_misoriented_grain_misorientation"
                ]
            else:
                HMG_misori = 1.0

            new_ori = ori_range[int(HMG_misori * (ori_range.shape[0] - 1))]
            new_phase_ori[phase_idx] = new_ori

        inp.geometry.phase_orientation = new_phase_ori

    if interface_binning:
        inp.bin_interfaces_by_misorientation_angle(**interface_binning)

    phase_field_input = inp.to_JSON(keep_arrays=True)

    return {"phase_field_input": phase_field_input}
