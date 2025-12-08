import numpy as np
from damask_parse.utils import validate_volume_element
from subsurface import Shuffle


def cluster_orientations(volume_element, alpha_file_path, gamma_file_path, n_iterations):

    # Convert zarr arrays to numpy arrays using existing code
    volume_element = validate_volume_element(volume_element)

    quaternions = volume_element["orientations"]["quaternions"]
    material_index = volume_element["element_material_idx"]

    # Replace subsets of quaternion values with those from files
    alpha = np.load(alpha_file_path)
    random_alpha_subset = alpha[np.random.choice(alpha.shape[0], size=200, replace=False)]
    quaternions[150:350] = np.array([list(x) for x in random_alpha_subset])
    gamma = np.load(gamma_file_path)
    random_gamma_subset = gamma[np.random.choice(gamma.shape[0], size=200, replace=False)]
    quaternions[500:700] = np.array([list(x) for x in random_gamma_subset])
    np.random.shuffle(quaternions)

    # Shuffle orientations
    # orientations_shuffled_vol,misorientation_init = Shuffle(material_index, quaternions,0,exclude=[],minimize=True,return_full=True)
    orientations_shuffled_vol, misorientation = Shuffle(
        material_index,
        quaternions,
        n_iterations,
        exclude=[],
        minimize=True,
        return_full=True,
    )

    # Replace quaternions in volume element
    volume_element["orientations"]["quaternions"] = np.array(
        [list(x) for x in orientations_shuffled_vol]
    )

    return {"volume_element": volume_element}
