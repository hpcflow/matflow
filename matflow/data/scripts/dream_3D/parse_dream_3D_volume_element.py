import h5py
import numpy as np

from damask_parse.utils import validate_volume_element


def parse_dream_3D_volume_element(dream_3D_hdf5_file: str):
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
        constituent_phase_label = [
            phase_names[i][0].decode() for i in constituent_phase_idx
        ]
        eulers = synth_vol["Grain Data"]["EulerAngles"][()][1:]

    vol_elem = {
        "grid_size": grid_size,
        "size": size,
        "element_material_idx": element_material_idx,
        "constituent_material_idx": np.arange(num_grains),
        "constituent_phase_label": constituent_phase_label,
        "material_homog": ["SX"] * num_grains,
        "orientations": _process_dream3D_euler_angles(eulers),
    }
    return validate_volume_element(vol_elem)


def _process_dream3D_euler_angles(euler_angles, degrees: bool = False) -> dict:
    orientations = {
        "type": "euler",
        "euler_degrees": degrees,
        "euler_angles": euler_angles,
        "unit_cell_alignment": {"x": "a"},
    }
    return orientations
