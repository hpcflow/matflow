from __future__ import annotations
from damask import seeds
from damask import Rotation
import numpy as np
from numpy.typing import ArrayLike


def seeds_from_random(
    VE_size: ArrayLike,
    num_grains: int,
    phase_label: str,
    orientation_coordinate_system=None,
) -> dict:
    """
    Generate a random arrangement of seeds for microstructure.
    """

    VE_size = np.array(VE_size)
    position = seeds.from_random(VE_size, num_grains)
    rotation = Rotation.from_random(shape=(num_grains,))
    out = {
        "microstructure_seeds": {
            "position": position,
            "orientations": {
                "data": rotation.quaternion,
                "representation": {
                    "type": "quaternion",
                    "quat_order": "scalar_vector",
                },
                "unit_cell_alignment": {
                    "x": "a",
                    "y": "b_star",
                    "z": "c",
                },
            },
            "box_size": VE_size,
            "random_seed": None,
            "phase_label": phase_label,
        }
    }
    return out
