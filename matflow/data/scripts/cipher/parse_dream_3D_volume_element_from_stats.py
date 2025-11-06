import h5py
import copy
import numpy as np

from damask_parse.utils import validate_orientations, validate_volume_element
from matflow.param_classes.orientations import Orientations


def parse_dream_3D_volume_element_from_stats(
    dream_3D_hdf5_file,
    phase_statistics,
    orientations,
    RNG_seed,
):
    orientations_phase_1 = orientations["phase_1"]
    orientations_phase_2 = orientations["phase_2"]

    # TODO: make it work.
    print(f"phase_statistics: {phase_statistics}")
    print(f"ori phase 1: {orientations_phase_1}")
    print(f"ori phase 2: {orientations_phase_2}")

    with h5py.File(dream_3D_hdf5_file, mode="r") as fh:
        synth_vol = fh["DataContainers"]["SyntheticVolumeDataContainer"]
        grid_size = synth_vol["_SIMPL_GEOMETRY"]["DIMENSIONS"][()]
        resolution = synth_vol["_SIMPL_GEOMETRY"]["SPACING"][()]
        size = [i * j for i, j in zip(resolution, grid_size)]

        # make zero-indexed:
        # (not sure why FeatureIds is 4D?)
        element_material_idx = synth_vol["CellData"]["FeatureIds"][()][..., 0] - 1
        element_material_idx = element_material_idx.transpose((2, 1, 0))

        num_grains = element_material_idx.max() + 1
        phase_names = synth_vol["CellEnsembleData"]["PhaseName"][()][1:]
        constituent_phase_idx = synth_vol["Grain Data"]["Phases"][()][1:] - 1
        constituent_phase_label = np.array(
            [phase_names[i][0].decode() for i in constituent_phase_idx]
        )
    old_format_orientations_phase_1 = _convert_orientations_to_old_matflow_format(
        orientations_phase_1
    )
    old_format_orientations_phase_2 = _convert_orientations_to_old_matflow_format(
        orientations_phase_2
    )

    ori_1 = validate_orientations(old_format_orientations_phase_1)
    ori_2 = validate_orientations(old_format_orientations_phase_2)
    oris = copy.deepcopy(ori_1)  # combined orientations

    phase_labels = [i["name"] for i in phase_statistics]
    phase_labels_idx = np.ones(constituent_phase_label.size) * np.nan
    for idx, i in enumerate(phase_labels):
        phase_labels_idx[constituent_phase_label == i] = idx
    assert not np.any(np.isnan(phase_labels_idx))
    phase_labels_idx = phase_labels_idx.astype(int)

    _, counts = np.unique(phase_labels_idx, return_counts=True)

    num_ori_1 = ori_1["quaternions"].shape[0]
    num_ori_2 = ori_2["quaternions"].shape[0]
    sampled_oris_1 = ori_1["quaternions"]
    sampled_oris_2 = ori_2["quaternions"]

    rng = np.random.default_rng(seed=RNG_seed)

    # If there are more orientations than phase label assignments, choose a random subset:
    if num_ori_1 != counts[0]:
        try:
            ori_1_idx = rng.choice(a=num_ori_1, size=counts[0], replace=False)
        except ValueError as err:
            raise ValueError(
                f"Probably an insufficient number of `orientations_phase_1` "
                f"({num_ori_1} given for phase {phase_labels[0]!r}, whereas {counts[0]} "
                f"needed). Caught ValueError is: {err}"
            )
        sampled_oris_1 = sampled_oris_1[ori_1_idx]
    if num_ori_2 != counts[1]:
        try:
            ori_2_idx = rng.choice(a=num_ori_2, size=counts[1], replace=False)
        except ValueError as err:
            raise ValueError(
                f"Probably an insufficient number of `orientations_phase_2` "
                f"({num_ori_2} given for phase {phase_labels[1]!r}, whereas {counts[1]} "
                f"needed). Caught ValueError is: {err}"
            )
        sampled_oris_2 = sampled_oris_2[ori_2_idx]

    ori_idx = np.ones(num_grains) * np.nan
    for idx, i in enumerate(counts):
        ori_idx[phase_labels_idx == idx] = np.arange(i) + np.sum(counts[:idx])

    if np.any(np.isnan(ori_idx)):
        raise RuntimeError("Not all phases have an orientation assigned!")
    ori_idx = ori_idx.astype(int)

    oris["quaternions"] = np.vstack([sampled_oris_1, sampled_oris_2])

    volume_element = {
        "size": size,
        "grid_size": grid_size,
        "orientations": oris,
        "element_material_idx": element_material_idx,
        "constituent_material_idx": np.arange(num_grains),
        "constituent_material_fraction": np.ones(num_grains),
        "constituent_phase_label": constituent_phase_label,
        "constituent_orientation_idx": ori_idx,
        "material_homog": np.full(num_grains, "SX"),
    }
    volume_element = validate_volume_element(volume_element)
    return volume_element


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
