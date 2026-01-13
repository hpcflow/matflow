import numpy as np
from damask_parse.utils import validate_volume_element
from subsurface import Shuffle
import matplotlib.pyplot as plt


def cluster_orientations(
    volume_element,
    alpha_file_path,
    gamma_file_path,
    n_iterations,
    alpha_start_index,
    alpha_stop_index,
    gamma_start_index,
    gamma_stop_index,
):
    """Method to rearrange a list of orientations by minimising the misorientation between neighbouring orientations."""

    # Convert zarr arrays to numpy arrays using existing code
    volume_element = validate_volume_element(volume_element)

    quaternions = volume_element["orientations"]["quaternions"]
    material_index = volume_element["element_material_idx"]
    material_index_2d = material_index[:, :, 0]
    material_index_3d = np.stack(
        (material_index_2d, material_index_2d, material_index_2d), axis=-1
    )

    # Replace subsets of quaternion values with those from files
    alpha = np.load(alpha_file_path)
    random_alpha_subset = alpha[
        np.random.choice(
            alpha.shape[0], size=alpha_stop_index - alpha_start_index, replace=False
        )
    ]
    quaternions[alpha_start_index:alpha_stop_index] = np.array(
        [list(x) for x in random_alpha_subset]
    )
    gamma = np.load(gamma_file_path)
    random_gamma_subset = gamma[
        np.random.choice(
            gamma.shape[0], size=gamma_stop_index - gamma_start_index, replace=False
        )
    ]
    quaternions[gamma_start_index:gamma_stop_index] = np.array(
        [list(x) for x in random_gamma_subset]
    )
    np.random.shuffle(quaternions)

    # Shuffle orientations
    orientations_shuffled_vol, misorientation_init = Shuffle(
        material_index_3d, quaternions, 0, exclude=[], minimize=True, return_full=True
    )
    orientations_shuffled_vol, misorientation = Shuffle(
        material_index_3d,
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

    plt.hist(misorientation)
    plt.hist(misorientation_init, color="r", alpha=0.5)
    plt.legend(["Initial", "shuffled"], fontsize=5)
    plt.xlabel("Misorientation")
    plt.ylabel("Number of grains")
    plt.savefig("misorientation.png")

    return {"volume_element": volume_element}
