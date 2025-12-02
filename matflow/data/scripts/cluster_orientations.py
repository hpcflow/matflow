import numpy as np
from damask_parse.utils import validate_volume_element, validate_orientations


def cluster_orientations(volume_element):

    # Convert zarr arrays to numpy arrays using existing code
    new_volume_element = validate_volume_element(volume_element)

    return {"volume_element": new_volume_element}
