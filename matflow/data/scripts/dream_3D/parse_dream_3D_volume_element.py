from __future__ import annotations

from typing import Any

import h5py
import numpy as np
from numpy.typing import NDArray

from damask_parse.utils import validate_volume_element

from matflow.param_classes.orientations import Orientations
from matflow.data.scripts.dream_3D.generate_volume_element_statistics import (
    _convert_orientations_to_old_matflow_format,
    _orientations_in_dream3d_frame,
)


def parse_dream_3D_volume_element(
    dream_3D_hdf5_file: str,
    orientations: Orientations | None = None,
    assign_orientations_directly: bool = True,
) -> dict[str, Any]:
    """Read Dream3D morphology and optionally assign input orientations to phase one.

    Input rows are used in grain-ID order, skipping grains of other phases. Without
    input orientations, or with direct assignment disabled, use Dream3D orientations.
    The source file is always read-only.
    """
    if not isinstance(assign_orientations_directly, bool):
        raise TypeError("assign_orientations_directly must be a boolean.")

    crystal_structure = None
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
        if assign_orientations_directly and orientations is not None:
            crystal_structure = synth_vol["CellEnsembleData"]["CrystalStructures"][()][
                1
            ].item()

    vol_elem = {
        "grid_size": grid_size,
        "size": size,
        "element_material_idx": element_material_idx,
        "constituent_material_idx": np.arange(num_grains),
        "constituent_phase_label": constituent_phase_label,
        "material_homog": ["SX"] * num_grains,
        "orientations": _process_dream3D_euler_angles(eulers),
    }
    volume_element = validate_volume_element(vol_elem)
    if assign_orientations_directly and orientations is not None:
        phase_grains = np.flatnonzero(constituent_phase_idx == 0)
        num_required = len(phase_grains)
        source = _convert_orientations_to_old_matflow_format(orientations)
        data = np.asarray(orientations.data)
        if not np.all(np.isfinite(data)):
            raise ValueError("Input orientations must contain only finite values.")
        structure_names = {0: "hexagonal", 1: "cubic"}
        if crystal_structure not in structure_names:
            raise ValueError(
                "Direct orientation assignment requires cubic or hexagonal "
                f"crystal structure for the first phase, got {crystal_structure}."
            )
        if source["type"] == "quat" and np.any(np.linalg.norm(data, axis=-1) == 0):
            raise ValueError("Input quaternions must have nonzero norm.")
        source = _orientations_in_dream3d_frame(
            source, structure_names[crystal_structure]
        )
        num_available = len(source["quaternions"])
        if num_available < num_required:
            raise ValueError(
                f"Insufficient input orientations for phase {phase_names[0][0].decode()!r}: "
                f"{num_available} supplied, {num_required} grains require orientations."
            )
        volume_element["orientations"]["quaternions"][phase_grains] = source[
            "quaternions"
        ][:num_required]
    return volume_element


def _process_dream3D_euler_angles(
    euler_angles: NDArray, degrees: bool = False
) -> dict[str, Any]:
    orientations = {
        "type": "euler",
        "euler_degrees": degrees,
        "euler_angles": euler_angles,
        "unit_cell_alignment": {"x": "a"},
    }
    return orientations
