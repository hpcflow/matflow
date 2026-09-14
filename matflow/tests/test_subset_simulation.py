from functools import partial

import numpy as np
from scipy.stats import norm

from matflow.subset_simulation.subset_simulation import (
    generate_next_level_samples,
    generate_next_level_samples_DA,
    get_approx_y_star_random_walk,
    log_surrogate_weight,
    make_voxel_grouping,
    subset_simulation,
    system_analysis_toy_model,
    weakest_link_performance_coarse,
    weakest_link_performance_fine,
)


def test_subset_simulation_toy_model():
    seed = 1234
    performance = partial(system_analysis_toy_model, dimension=200, target_pf=1e-4)
    result = subset_simulation(
        dimension=200,
        performance=performance,
        p_0=0.1,
        num_samples=100,
        num_levels=7,
        sampling_method=generate_next_level_samples,
        sampling_method_kwargs={
            "proposal": norm(scale=1.0),
        },
        master_seed=seed,
        mimic_matflow=True,
    )
    assert result.converged
    assert result.num_conditional_levels == 3
    assert np.isclose(result.pf, 1.3000e-04)
    assert np.isclose(result.cov, 0.9559503335693211)
    assert np.allclose(result.outer_move_rates, [0.51111111, 0.3, 0.25555556])


def test_subset_simulation_toy_model_DA():
    seed = 123

    dimension = 200
    block_size = 10
    target_pf = 1e-4

    y_star = get_approx_y_star_random_walk(
        sigma=1, dimension=dimension, target_pf=target_pf
    )

    group_idx = make_voxel_grouping(dimension, block_size)

    performance = partial(weakest_link_performance_fine, y_star=y_star)
    performance_coarse = partial(
        weakest_link_performance_coarse, y_star=y_star, group_idx=group_idx
    )

    result = subset_simulation(
        performance=performance,
        dimension=dimension,
        p_0=0.1,
        num_samples=100,
        num_levels=4,
        master_seed=seed,
        sampling_method=generate_next_level_samples_DA,
        sampling_method_kwargs={
            "proposal": norm(),
            "temperature": 1,  # should be of a similar order of magnitude to threshold
            "performance_coarse": performance_coarse,
            "log_surrogate_weight": log_surrogate_weight,
            # "log_surrogate_weight": lambda *args, **kwargs: 1,
            "num_inner_states": 3,
            "spawn_key": (5,),
        },
        transformation=lambda x: np.cumsum(x, axis=-1),  # random walk model
        debug=True,
        mimic_matflow=True,
    )
    assert result.converged
    assert result.num_conditional_levels == 3
    assert np.isclose(result.pf, 1.1000e-04)
    assert np.isclose(result.cov, 0.6454545454545455)
    assert np.allclose(result.outer_move_rates, [0.64444444, 0.42222222, 0.35555556])
