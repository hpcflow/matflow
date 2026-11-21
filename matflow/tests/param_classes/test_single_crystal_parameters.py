from pathlib import Path

import numpy as np
import pytest

import matflow as mf
from matflow.param_classes import BestSingleCrystalParameters, SingleCrystalParameters


def test_perturbation():
    params = SingleCrystalParameters(
        phases={"Al": {"xi_0_sl": [30e6]}},
        perturbations={"path": ["Al", "xi_0_sl", 0], "multiplicative": 1.05},
    )
    assert params.phases == {"Al": {"xi_0_sl": [30e6 * 1.05]}}


def test_perturbation_list():
    params = SingleCrystalParameters(
        phases={"Al": {"xi_0_sl": [30e6]}},
        perturbations=[
            {"path": ["Al", "xi_0_sl", 0], "multiplicative": 1.05},
            {"path": ["Al", "xi_0_sl", 0], "multiplicative": 1.05},
        ],
    )
    assert params.phases == {"Al": {"xi_0_sl": [30e6 * 1.05 * 1.05]}}


def test_perturbation_init_to_dict():
    params = SingleCrystalParameters(
        phases={"Al": {"xi_0_sl": [30e6]}},
        perturbations={"path": ["Al", "xi_0_sl", 0], "multiplicative": 1.05},
    )
    SingleCrystalParameters(**params.to_dict())


@pytest.mark.parametrize(
    ("value", "multiplier", "bounds", "expected"),
    [
        (10.0, 1.05, [None, 10.25], 10.25),
        (10.0, 1.05, [5.0, 10.0], 9.5),
        (10.0, 0.95, [10.0, None], 10.5),
    ],
)
def test_bounded_perturbation(
    value: float, multiplier: float, bounds: list[float | None], expected: float
) -> None:
    params = SingleCrystalParameters(
        phases={"Al": {"xi_0_sl": [value]}},
        perturbations={
            "path": ["Al", "xi_0_sl", 0],
            "multiplicative": multiplier,
            "bounds": bounds,
        },
    )

    assert params.phases["Al"]["xi_0_sl"][0] == pytest.approx(expected)
    assert params.base["Al"]["xi_0_sl"] == [value]


@pytest.mark.parametrize(
    ("value", "multiplier", "bounds", "message"),
    [
        (10.0, 1.05, [11.0, 20.0], "below its lower bound"),
        (10.0, 1.05, [1.0, 9.0], "above its upper bound"),
        (10.0, 1.05, [10.0, 10.0], "lower bound must be less"),
        (10.0, 1.0, [5.0, 20.0], "Cannot perturb"),
    ],
)
def test_invalid_bounded_perturbation(
    value: float, multiplier: float, bounds: list[float | None], message: str
) -> None:
    params = SingleCrystalParameters(
        phases={"Al": {"xi_0_sl": [value]}},
        perturbations={
            "path": ["Al", "xi_0_sl", 0],
            "multiplicative": multiplier,
            "bounds": bounds,
        },
    )

    with pytest.raises(ValueError, match=message):
        _ = params.phases


@pytest.mark.parametrize("bounds", [None, [20e6, 30.75e6], [20e6, 30e6]])
@pytest.mark.parametrize(
    ("tolerance", "converged"),
    [(None, False), (14_999.0, False), (15_000.0, True), (15_001.0, True)],
)
def test_fitting_jacobian_uses_simulated_perturbation(
    bounds: list[float | None] | None,
    tolerance: float | None,
    converged: bool,
    capsys: pytest.CaptureFixture[str],
) -> None:
    pytest.importorskip("formable")
    from formable.levenberg_marquardt import LMFitter

    from matflow.data.scripts.formable.fit_single_crystal_parameters import (
        fit_single_crystal_parameters,
    )

    base = {"Al": {"xi_0_sl": [30e6]}}
    params = [
        SingleCrystalParameters(phases=base),
        SingleCrystalParameters(
            phases=base,
            perturbations={
                "path": ["Al", "xi_0_sl", 0],
                "multiplicative": 1.05,
                "bounds": bounds,
            },
        ),
    ]
    strain = np.array([0.0, 0.01, 0.02, 0.03, 0.04])
    responses = []
    for param in params:
        strain_tensor = np.zeros((len(strain), 3, 3))
        strain_tensor[:, 0, 0] = strain
        responses.append(
            {
                "volume_data": {
                    "vol_avg_strain": {"data": strain_tensor},
                    "vol_avg_stress": {
                        "data": strain_tensor * param.phases["Al"]["xi_0_sl"][0]
                    },
                }
            }
        )

    result = fit_single_crystal_parameters(
        VE_response={"iteration_0": {"value": responses}},
        single_crystal_parameters={"iteration_0": {"value": params}},
        tensile_test={
            "true_strain": strain,
            "true_stress": strain * 31e6,
            "plastic_range": [0.01, 0.04],
        },
        fitting_error_tolerance=tolerance,
    )

    assert result["is_converged"] is converged
    history = result["fitting_history"]
    assert len(history) == 1
    assert history[0]["accepted"] is True
    fitter = LMFitter.from_dict(result["levenberg_marquardt_fitter"])
    assert fitter.fitting_params[0].perturbation == pytest.approx(0.05)
    opt = fitter.optimisations[0]
    np.testing.assert_allclose(opt.jacobian[:, 0], 30e6 * opt.get_sim_strain(0))
    next_trial_value = result["single_crystal_parameters"]["phases"]["Al"]["xi_0_sl"][0]
    assert history[0]["measured_error"] == pytest.approx(opt.actual_error)
    assert history[0]["trial_parameters"] == opt.fitting_params
    assert history[0]["next_trial_parameters"]["Al__xi_0_sl__0"] == pytest.approx(
        next_trial_value
    )
    best_parameter_value = BestSingleCrystalParameters(
        **result["best_single_crystal_parameters"]
    )
    best_measured_value = best_parameter_value.phases["Al"]["xi_0_sl"][0]
    assert best_measured_value == pytest.approx(opt.fitting_params["Al__xi_0_sl__0"])
    if bounds != [20e6, 30e6]:
        assert next_trial_value != pytest.approx(opt.fitting_params["Al__xi_0_sl__0"])

    diagnostics = capsys.readouterr().out
    assert "measured baseline MAE=" in diagnostics
    assert "status=accepted" in diagnostics
    assert "trial parameters=" in diagnostics
    assert "best measured parameters=" in diagnostics
    assert "next trial parameters=" in diagnostics
    assert f"is_converged={converged}" in diagnostics


def test_fitting_requires_unperturbed_parameter_simulation() -> None:
    pytest.importorskip("formable")

    from matflow.data.scripts.formable.fit_single_crystal_parameters import (
        fit_single_crystal_parameters,
    )

    params = SingleCrystalParameters(
        phases={"Al": {"xi_0_sl": [30e6]}},
        perturbations={
            "path": ["Al", "xi_0_sl", 0],
            "multiplicative": 1.05,
        },
    )

    with pytest.raises(ValueError, match="null-perturbation simulation is required"):
        fit_single_crystal_parameters(
            VE_response={},
            single_crystal_parameters={"iteration_0": {"value": [params]}},
            tensile_test={},
        )


def test_fitting_requires_a_simulated_iteration() -> None:
    pytest.importorskip("formable")

    from matflow.data.scripts.formable.fit_single_crystal_parameters import (
        fit_single_crystal_parameters,
    )

    params = SingleCrystalParameters(phases={"Al": {"xi_0_sl": [30e6]}})

    with pytest.raises(ValueError, match="At least one fitting simulation is required"):
        fit_single_crystal_parameters(
            VE_response={},
            single_crystal_parameters={"iteration_0": {"value": [params]}},
            tensile_test={},
        )


def test_fitting_reports_rejected_trial_separately_from_best_parameters(
    capsys: pytest.CaptureFixture[str],
) -> None:
    pytest.importorskip("formable")

    from matflow.data.scripts.formable.fit_single_crystal_parameters import (
        fit_single_crystal_parameters,
    )

    base = {"Al": {"xi_0_sl": [30e6]}}
    params = [
        SingleCrystalParameters(phases=base),
        SingleCrystalParameters(
            phases=base,
            perturbations={
                "path": ["Al", "xi_0_sl", 0],
                "multiplicative": 1.05,
            },
        ),
    ]
    strain = np.array([0.0, 0.01, 0.02, 0.03, 0.04])

    def make_responses(parameter_values: list[float]) -> list[dict]:
        responses = []
        for parameter_value in parameter_values:
            strain_tensor = np.zeros((len(strain), 3, 3))
            strain_tensor[:, 0, 0] = strain
            responses.append(
                {
                    "volume_data": {
                        "vol_avg_strain": {"data": strain_tensor},
                        "vol_avg_stress": {"data": strain_tensor * parameter_value},
                    }
                }
            )
        return responses

    result = fit_single_crystal_parameters(
        VE_response={
            "iteration_0": {"value": make_responses([30e6, 31.5e6])},
            "iteration_1": {"value": make_responses([20e6, 21e6])},
        },
        single_crystal_parameters={"iteration_0": {"value": params}},
        tensile_test={
            "true_strain": strain,
            "true_stress": strain * 31e6,
            "plastic_range": [0.01, 0.04],
        },
        fitting_error_tolerance=15_000.0,
    )

    fitter_data = result["levenberg_marquardt_fitter"]
    best_value = result["best_single_crystal_parameters"]["phases"]["Al"]["xi_0_sl"][0]
    next_trial_value = result["single_crystal_parameters"]["phases"]["Al"]["xi_0_sl"][0]
    assert best_value == pytest.approx(30e6)
    assert next_trial_value != pytest.approx(best_value)
    assert len(fitter_data["optimisations"]) == 1
    assert result["is_converged"] is True
    history = result["fitting_history"]
    assert [iteration["accepted"] for iteration in history] == [True, False]
    assert history[1]["measured_error"] > history[0]["measured_error"]
    assert history[1]["best_measured_error"] == history[0]["measured_error"]
    assert history[1]["trial_parameters"]["Al__xi_0_sl__0"] == pytest.approx(
        history[0]["next_trial_parameters"]["Al__xi_0_sl__0"]
    )
    assert history[-1]["next_trial_parameters"]["Al__xi_0_sl__0"] == pytest.approx(
        next_trial_value
    )

    diagnostics = capsys.readouterr().out
    assert "Fitting iteration 1:" in diagnostics
    assert "Fitting iteration 2:" in diagnostics
    assert "status=rejected" in diagnostics


@pytest.mark.parametrize("tolerance", [-1.0, float("nan"), float("inf")])
def test_fitting_rejects_invalid_error_tolerance(tolerance: float) -> None:
    pytest.importorskip("formable")
    from matflow.data.scripts.formable.fit_single_crystal_parameters import (
        fit_single_crystal_parameters,
    )

    with pytest.raises(ValueError, match="must be finite and non-negative"):
        fit_single_crystal_parameters({}, {}, {}, fitting_error_tolerance=tolerance)


def test_fitting_demo_terminates_on_measured_convergence() -> None:
    workflow_path = (
        Path(__file__).parents[2]
        / "data"
        / "workflows"
        / "fit_single_crystal_parameters.yaml"
    )
    template = mf.WorkflowTemplate.from_YAML_string(
        "name: fitting_convergence_test\n" + workflow_path.read_text(encoding="utf-8")
    )
    loop = template.loops[0]
    assert loop.num_iterations == 7
    assert loop.termination_task_insert_ID == 4
    assert loop.termination is not None
    assert loop.termination.path == "outputs.is_converged"
    assert loop.termination._valida_check(True)
    assert not loop.termination._valida_check(False)
    assert "is_converged" in template.tasks[-1].all_schema_output_types
    assert "fitting_history" in template.tasks[-1].all_schema_output_types
    tolerance = next(
        inp.value
        for inp in template.tasks[-1].element_sets[0].inputs
        if inp.parameter.typ == "fitting_error_tolerance"
    )
    assert tolerance == 2e6
