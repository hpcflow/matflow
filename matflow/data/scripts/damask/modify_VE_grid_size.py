from __future__ import annotations
import numpy as np
from numpy.typing import ArrayLike
from scipy.ndimage import zoom
from damask_parse.utils import validate_volume_element


def modify_VE_grid_size(volume_element: dict, new_grid_size: ArrayLike) -> dict:
    """
    Alter the grid size of a volume element.
    """
    new_grid_size = np.array(new_grid_size)
    zoom_factor = np.array(new_grid_size) / volume_element["grid_size"]
    new_elem_mat_idx = zoom(volume_element["element_material_idx"], zoom_factor, order=0)

    volume_element["grid_size"] = new_grid_size
    volume_element["element_material_idx"] = new_elem_mat_idx

    volume_element = validate_volume_element(volume_element)
    volume_element["grid_size"] = tuple(int(i) for i in volume_element["grid_size"])
    volume_element["size"] = tuple(float(i) for i in volume_element["size"])
    out = {"volume_element": volume_element}

    return out
