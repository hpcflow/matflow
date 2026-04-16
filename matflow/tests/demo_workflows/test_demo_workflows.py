from matplotlib import pyplot as plt
import pytest
from hpcflow.sdk.core.enums import EARStatus

import matflow as mf
from matflow.tests.subset_simulation import generate_next_state, subset_simulation


@pytest.mark.demo_damask_workflows
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


@pytest.mark.demo_damask_workflows
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
        wait=True,
        resources={"random_seed": seed},
    )
    final_iter = wk.tasks.collate_results.elements[0].latest_iteration_non_skipped
    pf = final_iter.get("outputs.pf")
    cov = final_iter.get("outputs.cov")

    # run via single function implementation:
    pf_sf, cov_sf = subset_simulation(
        dimension=200,
        target_pf=1e-4,
        p_0=0.1,
        num_samples=100,
        num_levels=7,
        next_state=generate_next_state,
        next_state_kwargs={
            "prop_std": 1.0,
        },
        master_seed=seed,
        mimic_matflow=True,
    )

    assert pf == pf_sf
    assert cov == cov_sf


@pytest.mark.demo_mtex_workflows
def test_sample_orientations(tmp_path):
    wk = mf.make_and_submit_demo_workflow(
        "sample_orientations_CTF_file",
        path=tmp_path,
        status=False,
        add_to_known=False,
        wait=True,
        config={"log_file_level": "debug"},
        resources={"write_app_logs": True},
    )
    runs = wk.get_all_EARs()
    assert all(run.status is EARStatus.success for run in runs)

    # TODO: maybe run all MTEX demos on linux only, and then a single dummy script on
    # windows and mac, just to check matlab and mtex are configured correctly.
    # could have an option to run the full MTEX demo suite on windows and mac if desired.
