import numpy as np
from scipy.stats import norm, uniform
from damask import Grid
from damask_parse.utils import validate_volume_element, validate_orientations


def quat_sample_random(rand_nums):
    """Generate random uniformly distributed unit quaternions.

    Parameters
    ----------
    rand_nums : ndarray of shape (N, 3)

    Returns
    -------
    quats : ndarray of shape (N, 4)

    References
    ----------
    https://stackoverflow.com/a/44031492/5042280
    https://web.archive.org/web/20220517133017/http://planning.cs.uiuc.edu/node198.html

    """
    return np.array(
        [
            np.sqrt(1 - rand_nums[:, 0]) * np.sin(2 * np.pi * rand_nums[:, 1]),
            np.sqrt(1 - rand_nums[:, 0]) * np.cos(2 * np.pi * rand_nums[:, 1]),
            np.sqrt(rand_nums[:, 0]) * np.sin(2 * np.pi * rand_nums[:, 2]),
            np.sqrt(rand_nums[:, 0]) * np.cos(2 * np.pi * rand_nums[:, 2]),
        ]
    ).T


def _to_standard_normal_space(dist, variates):
    """Convert random variables defined in some non-standard-normal continuous
    distribution space to a standard normal distribution space."""
    return norm.ppf(dist.cdf(variates), loc=0, scale=1)


def _to_physical_space(dist, variates):
    """Convert random variables defined in standard normal space to some other
    continuous distribution space."""
    return dist.ppf(norm.cdf(variates, loc=0, scale=1))


def standard_normal_to_uniform_space(dist, variates):
    min_, max_ = dist.support()
    return norm.cdf(variates, loc=0, scale=1) * (max_ - min_) + min_


def uniform_to_standard_normal_space(dist, variates):
    min_, max_ = dist.support()
    return norm.ppf(((variates - min_) / (max_ - min_)), loc=0, scale=1)


def to_physical_space(dists, variates):
    """Convert random variables sampled from the standard normal space to the specified
    distribution spaces.

    Parameters
    ----------
    dists
        List of SciPy frozen distribution instances
    variates
        Standard-normally distributed random variates. Outer dimension must
        match length of `dists` list.
    """
    funcs = [_lookup.get(i.dist.name, ("", _to_physical_space))[1] for i in dists]
    assert len(funcs) == len(variates)
    inputs_t = np.empty_like(variates)
    for idx, (func_i, ins_i) in enumerate(zip(funcs, variates)):
        inputs_t[idx] = func_i(dists[idx], ins_i)
    return inputs_t


_lookup = {
    "uniform": (uniform_to_standard_normal_space, standard_normal_to_uniform_space),
}


def generate_volume_element_voronoi_variates(
    x,
    VE_grid_size,
    VE_size,
    phase_label,
    homog_label,
    scale_morphology,
    scale_update_size,
):

    random_variates = x
    print(f"generate RVE: {random_variates.shape=}")

    num_vars = len(x)
    inputs = [uniform() for _ in range(num_vars)]
    uniform_vars = to_physical_space(inputs, random_variates)

    num_grains_ = num_vars / 6  # three for seed point (x, y, z), three for quaternion
    assert num_grains_ % 1 == 0
    num_grains = int(num_grains_)

    seeds = uniform_vars[: 3 * num_grains].reshape((num_grains, 3))
    ori_numbers = uniform_vars[3 * num_grains :].reshape((num_grains, 3))
    quats = quat_sample_random(ori_numbers)

    grid_obj = Grid.from_Voronoi_tessellation(
        cells=np.array(VE_grid_size),
        size=np.array(VE_size),
        seeds=seeds,
        periodic=True,
    )

    if scale_morphology is not None:
        scale_morphology = np.array(scale_morphology)

        original_cells = grid_obj.cells
        new_cells = original_cells * scale_morphology
        grid_scaled = grid_obj.scale(new_cells)

        if scale_update_size:
            original_size = grid_obj.size
            new_size = original_size * scale_morphology
            grid_scaled.size = new_size

        grid_obj = grid_scaled

    unit_cell_alignment = {
        "x": "a",
        "y": "b*",
        "z": "c",
    }
    oris = {
        "type": "quat",
        "unit_cell_alignment": unit_cell_alignment,
        "quaternions": quats,
        "quat_component_ordering": "scalar-vector",
    }

    oris = validate_orientations(oris)

    const_phase_lab = np.array([phase_label])[np.zeros(num_grains, dtype=int)]
    ori_idx = np.arange(num_grains)

    volume_element = {
        "size": grid_obj.size.astype(float).tolist(),
        "grid_size": grid_obj.cells.tolist(),
        "orientations": oris,
        "element_material_idx": grid_obj.material,
        "constituent_material_idx": np.arange(num_grains),
        "constituent_material_fraction": np.ones(num_grains),
        "constituent_phase_label": const_phase_lab,
        "constituent_orientation_idx": ori_idx,
        "material_homog": np.full(num_grains, homog_label),
    }
    return {"volume_element": validate_volume_element(volume_element)}
