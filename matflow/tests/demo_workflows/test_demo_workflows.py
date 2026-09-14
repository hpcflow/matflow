from functools import partial

from matplotlib import pyplot as plt
import pytest

from scipy.stats import norm
from hpcflow.sdk.core.enums import EARStatus
import numpy as np

import matflow as mf
from matflow.subset_simulation.subset_simulation import (
    log_surrogate_weight,
    generate_next_level_samples_DA,
    get_approx_y_star_random_walk,
    make_voxel_grouping,
    subset_simulation,
    generate_next_level_samples,
    system_analysis_toy_model,
    weakest_link_performance_coarse,
    weakest_link_performance_fine,
)


@pytest.mark.demo_workflows
def test_damask_input_files(tmp_path, save_fig, reference_array_data):
    """Test submission and check the stress-strain curve from a simple DAMASK workflow,
    with specific input files provided.

    Note this test must be run with a `--with-env-source /path/to/envs.yaml` option that
    points to an environment file with definitions for:
     - `damask_env`
     - `damask_parse_env`

    """
    mf.print_envs()
    mf.config._show(metadata=True)
    wk = mf.make_demo_workflow("damask_input_files", path=tmp_path)
    wk.submit(wait=True, add_to_known=False)

    runs = wk.get_all_EARs()
    assert all(run.status is EARStatus.success for run in runs)

    VE_response = wk.tasks.simulate_VE_loading_damask.elements[
        0
    ].outputs.VE_response.value
    STRAIN_KEY = "vol_avg_equivalent_strain"
    STRESS_KEY = "vol_avg_equivalent_stress"
    stress = VE_response["phase_data"][STRESS_KEY]["data"][:]
    strain = VE_response["phase_data"][STRAIN_KEY]["data"][:]

    fig, ax = plt.subplots()
    ax.plot(strain, stress)
    ax.set_xlabel(STRAIN_KEY)
    ax.set_ylabel(STRESS_KEY)

    # save figure to the --fig-dir (if passed, otherwise within `--basetemp`); and if run
    # with `--save-reference`, also save to the reference data folder:
    save_fig(fig, name="stress_strain.png")

    # save reference data (if run with `--save-reference`) or check it matches existing:
    reference_array_data(
        {"stress": stress, "strain": strain},
        name="stress_strain.npz",
        rtol=1e-10,
    )


@pytest.mark.demo_workflows
@pytest.mark.skip(reason="takes too long")
def test_subset_simulation_toy_model_prediction(tmp_path):
    """Validate the MatFlow subset simulation implementation for a toy model.

    Note this test must be run with a `--with-env-source /path/to/envs.yaml` option that
    points to an environment file with definitions for:
     - `damask_parse_env`

    """

    seed = 1234

    # run via a MatFlow workflow:
    wk = mf.make_and_submit_demo_workflow(
        "subset_simulation_toy_model",
        path=tmp_path,
        status=False,
        add_to_known=False,
        resources={"random_seed": seed},
    )

    performance = partial(system_analysis_toy_model, dimension=200, target_pf=1e-4)

    # run via single function implementation:
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

    wk.wait()
    final_iter = wk.tasks.collate_results.elements[0].latest_iteration_non_skipped
    pf = final_iter.get("outputs.pf")
    cov = final_iter.get("outputs.cov")
    outer_move_rate = final_iter.get("outputs.outer_move_rate")
    mean_jump = final_iter.get("outputs.mean_jump_distance")
    comp_accept = final_iter.get("outputs.component_acceptance_rate")

    # TODO: also verify same result with `subset_simulation_toy_model_external`, once
    # that can be submitted without a ridiculous number of processes.

    # note the actual values are tested in ``test_subset_simulation``
    assert pf == result.pf
    assert cov == result.cov
    assert np.allclose(outer_move_rate, result.outer_move_rates)
    assert np.isclose(mean_jump, result.mean_jump_distances[-1])
    assert np.isclose(comp_accept, result.component_acceptance_rates[-1])


@pytest.mark.demo_workflows
@pytest.mark.skip(reason="takes too long")
def test_subset_simulation_toy_model_DA_prediction(tmp_path):
    """Validate the MatFlow delayed acceptance subset simulation implementation for a toy
    model.

    Note this test must be run with a `--with-env-source /path/to/envs.yaml` option that
    points to an environment file with definitions for:
     - `damask_parse_env`

    """

    seed = 123
    NUM_LEVELS = 4

    # run via a MatFlow workflow:
    wk = mf.make_and_submit_demo_workflow(
        "subset_simulation_toy_model_DA",
        path=tmp_path,
        status=False,
        add_to_known=False,
        resources={"random_seed": seed},
    )

    proposal = norm()
    dimension = 200
    block_size = 10
    target_pf = 1e-4

    COST_RATIO = 1 / block_size

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
        num_levels=NUM_LEVELS,
        master_seed=seed,
        sampling_method=generate_next_level_samples_DA,
        sampling_method_kwargs={
            "proposal": proposal,
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

    wk.wait()

    final_iter = wk.tasks.collate_results.elements[0].iterations[-1]
    pf = final_iter.get("outputs.pf")
    cov = final_iter.get("outputs.cov")
    outer_move_rate = final_iter.get("outputs.outer_move_rate")
    mean_jump = final_iter.get("outputs.mean_jump_distance")
    comp_accept = final_iter.get("outputs.component_acceptance_rate")

    # note the actual values are tested in ``test_subset_simulation``
    assert pf == result.pf
    assert cov == result.cov
    assert np.allclose(outer_move_rate, result.outer_move_rates)
    assert np.isclose(mean_jump, result.mean_jump_distances[-1])
    assert np.isclose(comp_accept, result.component_acceptance_rates[-1])
