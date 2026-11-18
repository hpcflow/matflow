from __future__ import annotations
import json
from typing import Any, TYPE_CHECKING
import numpy as np
from formable.levenberg_marquardt import (
    FittingParameter,
    LMFitterOptimisation,
    LMFitter,
)
from formable.tensile_test import TensileTest

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from matflow.param_classes.single_crystal_parameters import SingleCrystalParameters


def fit_single_crystal_parameters(
    VE_response: dict,
    single_crystal_parameters: dict,
    tensile_test: dict,
    initial_damping: list[float] | None = None,
    fitting_error_tolerance: float | None = None,
) -> dict[str, Any]:
    """Fit parameters, optionally checking the best measured MAE against a Pa limit."""

    if fitting_error_tolerance is not None and (
        not np.isfinite(fitting_error_tolerance) or fitting_error_tolerance < 0
    ):
        raise ValueError("fitting_error_tolerance must be finite and non-negative.")

    # Generate FittingParameter objects:
    fitting_params = []
    null_perturbation_idx = None
    params: SingleCrystalParameters
    for idx, params in enumerate(single_crystal_parameters["iteration_0"]["value"]):
        if params.perturbations:
            perturb = params.perturbations[0]
            path = perturb["path"]
            name = "__".join([str(i) for i in path])
            value = _get_by_path(params.base, path)

            fitting_param_i = FittingParameter(
                name=name,
                values=[value],
                address=path,
                perturbation=perturb["multiplicative"] - 1.0,
                bounds=perturb.get("bounds"),
            )
            fitting_params.append(fitting_param_i)
        else:
            # The null-perturbation does not correspond to a FittingParameter:
            null_perturbation_idx = idx

    if null_perturbation_idx is None:
        raise ValueError("A null-perturbation simulation is required for fitting.")

    # Collect volume element responses:
    tensile_tests_by_iteration = []
    for iteration_idx, all_vol_elem_resp in VE_response.items():
        # take x-normal component of tensors; comparable to experimental data
        # TODO: allow for non-x-direction and more generally rotated load cases
        tensile_tests = []
        for vol_elem_resp in all_vol_elem_resp["value"]:
            true_stress_tensor = vol_elem_resp["volume_data"]["vol_avg_stress"]["data"]
            true_strain_tensor = vol_elem_resp["volume_data"]["vol_avg_strain"]["data"]
            tensile_tests.append(
                TensileTest(
                    true_stress=true_stress_tensor[..., 0, 0],
                    true_strain=true_strain_tensor[..., 0, 0],
                )
            )

        # Need to reorder if null-perturbation is not first:
        num_sims_per_iteration = len(single_crystal_parameters["iteration_0"]["value"])
        if null_perturbation_idx != 0:
            non_null_pert_idx = list(
                set(range(num_sims_per_iteration)) - {null_perturbation_idx}
            )
            tensile_tests = [tensile_tests[null_perturbation_idx]] + [
                tensile_tests[i] for i in non_null_pert_idx
            ]

        tensile_tests_by_iteration.append(tensile_tests)

    if not tensile_tests_by_iteration:
        raise ValueError("At least one fitting simulation is required.")

    # Generate fitter object:
    base_params = single_crystal_parameters["iteration_0"]["value"][0].base
    lm_fitter = LMFitter(
        exp_tensile_test=TensileTest(**tensile_test),
        single_crystal_parameters=base_params,
        fitting_params=fitting_params,
        initial_damping=initial_damping,
    )

    # Add simulated tests:
    for iteration_idx, tensile_tests in enumerate(tensile_tests_by_iteration, 1):
        trial_parameters = _get_fitting_parameter_values(lm_fitter.fitting_params, -1)
        trial_opt = LMFitterOptimisation(lm_fitter, tensile_tests)
        measured_error = float(
            np.mean(np.abs(trial_opt.get_exp_stress() - trial_opt.get_sim_stress(0)))
        )
        accepted = lm_fitter.add_simulated_tensile_tests(tensile_tests)

        best_opt = min(
            lm_fitter.optimisations,
            key=lambda opt: opt.actual_error,
        )
        best_parameters = {
            name: float(value) for name, value in best_opt.fitting_params.items()
        }
        next_trial_parameters = _get_fitting_parameter_values(
            lm_fitter.fitting_params, -1
        )
        print(
            f"Fitting iteration {iteration_idx}: "
            f"measured baseline MAE={measured_error / 1e6:.3f} MPa; "
            f"status={'accepted' if accepted else 'rejected'}; "
            f"trial parameters={json.dumps(trial_parameters, sort_keys=True)}; "
            f"best measured parameters="
            f"{json.dumps(best_parameters, sort_keys=True)}; "
            f"best measured MAE={best_opt.actual_error / 1e6:.3f} MPa; "
            f"next trial parameters="
            f"{json.dumps(next_trial_parameters, sort_keys=True)}; "
            f"next damping={lm_fitter.optimisations[-1].damping_factor:g}",
            flush=True,
        )

    best_opt = min(
        lm_fitter.optimisations,
        key=lambda opt: opt.actual_error,
    )
    best_single_crystal_parameters = lm_fitter.get_new_single_crystal_params(
        best_opt.index
    )
    optimised_single_crystal_parameters = lm_fitter.get_new_single_crystal_params(-1)
    is_converged = bool(
        fitting_error_tolerance is not None
        and best_opt.actual_error <= fitting_error_tolerance
    )
    acceptable_error = (
        f"{fitting_error_tolerance / 1e6:g} MPa"
        if fitting_error_tolerance is not None
        else "not configured"
    )
    print(
        f"Fitting convergence: is_converged={is_converged}; "
        f"best measured MAE={best_opt.actual_error / 1e6:.3f} MPa; "
        f"acceptable MAE={acceptable_error}",
        flush=True,
    )

    outputs = {
        "single_crystal_parameters": {"phases": optimised_single_crystal_parameters},
        "best_single_crystal_parameters": {"phases": best_single_crystal_parameters},
        "levenberg_marquardt_fitter": lm_fitter.to_dict(),
        "is_converged": is_converged,
    }
    return outputs


def _get_by_path(root: list | dict, path: list) -> Any:
    """Get a nested dict or list item according to its "key path"

    Parameters
    ----------
    root : dict or list
        Can be arbitrarily nested.
    path : list of str
        The address of the item to get within the `root` structure.

    Returns
    -------
    sub_data : any
    """

    sub_data: Any = root
    for key in path:
        sub_data = sub_data[key]

    return sub_data


def _get_fitting_parameter_values(
    fitting_params: list[FittingParameter], index: int
) -> dict[str, float]:
    return {
        param.name: float(param.values[index] * param.scale) for param in fitting_params
    }
