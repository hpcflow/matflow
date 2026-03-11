from matplotlib import pyplot as plt
import pytest
from hpcflow.sdk.core.enums import EARStatus

import matflow as mf


@pytest.mark.demo_workflows
def test_damask_input_files(tmp_path, save_fig, reference_data):
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
    save_fig(fig)

    # TODO: save reference figure and check it matches via matplotlib?

    # save reference data (if run with `--save-reference`) or check it matches existing:
    # skip the first few increments, where relatively large differences are observed
    reference_data(stress, name="stress.npy", rtol=1e-10)
    reference_data(strain, name="strain.npy", rtol=1e-10)
