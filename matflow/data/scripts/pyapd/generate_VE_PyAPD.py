from __future__ import annotations
import os
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike
from damask_parse.utils import validate_volume_element, validate_orientations
import PyAPD

from matflow.param_classes.orientations import Orientations


def generate_VE_PyAPD(
    num_grains: int,
    VE_grid_size: ArrayLike,
    VE_size: ArrayLike,
    phase_label: str,
    homog_label: str,
    orientations: Orientations | None,
    random_seed: int | None | Literal["resource_value"] = "resource_value",
):
    if random_seed == "resource_value":
        seed = int(os.environ["MATFLOW_RUN_RANDOM_SEED"])
    else:
        seed = random_seed

    VE_size = np.asarray(VE_size)
    VE_grid_size = np.asarray(VE_grid_size)

    mat_idx, apd_obj = generate_voxel_microstructure(
        grid_size=VE_grid_size,
        n_grains=num_grains,
        seed=seed,
    )

    oris = resolve_orientations(orientations, num_grains)
    ori_idx = np.arange(num_grains)
    const_phase_lab = np.array([phase_label])[np.zeros(num_grains, dtype=int)]

    volume_element = {
        "size": VE_size.tolist(),
        "grid_size": VE_grid_size.tolist(),
        "orientations": oris,
        "element_material_idx": mat_idx,
        "constituent_material_idx": np.arange(num_grains),
        "constituent_material_fraction": np.ones(num_grains),
        "constituent_phase_label": const_phase_lab,
        "constituent_orientation_idx": ori_idx,
        "material_homog": np.full(num_grains, homog_label),
    }
    volume_element = validate_volume_element(volume_element)
    return {"volume_element": volume_element}


def resolve_orientations(orientations, num_grains):
    if orientations is None:
        orientations = Orientations.from_random(num_grains)
        assert orientations is not None

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

    return validate_orientations(oris)


def generate_voxel_microstructure(
    grid_size,
    n_grains,
    anisotropy=0.0,
    optimize_weights=False,
    lloyd_iterations=0,
    seed=None,
    heuristic_weights=True,
    device=None,
):
    """
    Generate a voxelized anisotropic power diagram microstructure using PyAPD.

    Parameters
    ----------
    grid_size : tuple
        Output voxel grid dimensions.
        Examples:
            (256,256)     -> 2D
            (128,128,128) -> 3D

    n_grains : int
        Number of grains/seeds.

    anisotropy : float
        Controls anisotropy threshold.
        0.0 = isotropic power diagram
        1.0 = strong anisotropy allowed

    optimize_weights : bool
        If True, adjusts weights to improve volume balance.

    lloyd_iterations : int
        Number of Lloyd relaxation iterations.

    seed : int or None
        Random seed.

    heuristic_weights : bool
        Use PyAPD heuristic weight initialization.

    device : str or None
        "cpu" or "cuda".

    Returns
    -------
    labels : ndarray
        Integer grain labels with shape == grid_size.

    apd : PyAPD.apd_system
        Full APD object for further manipulation.
    """

    D = len(grid_size)

    if D not in [2, 3]:
        raise ValueError("grid_size must be 2D or 3D")

    # Create APD system
    apd = PyAPD.apd_system(
        N=n_grains,
        D=D,
        heuristic_W=heuristic_weights,
    )

    # Optional reproducibility
    if seed is not None:
        apd.seed = seed

    # Optional device selection
    if device is not None:
        apd.device = device

    # Set anisotropy level
    apd.ani_thres = anisotropy

    # Override pixel grid directly
    apd.pixel_params = list(grid_size)

    # Build voxel centers
    apd.assemble_pixels()

    # Optional optimization of weights
    if optimize_weights:
        apd.find_optimal_W()

    # Optional Lloyd relaxation
    for _ in range(lloyd_iterations):
        apd.Lloyds_algorithm(verbosity_level=0)

    # Compute APD assignment
    assignments = apd.assemble_apd()

    # Move GPU tensor to CPU before NumPy conversion
    if hasattr(assignments, "detach"):
        assignments = assignments.detach().cpu().numpy()

    # Convert to voxel grid
    labels = np.array(assignments).reshape(grid_size)

    return labels, apd
