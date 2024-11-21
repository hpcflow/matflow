from __future__ import annotations
from typing import Any
import numpy as np
from formable.levenberg_marquardt import (
    FittingParameter,
    LMFitterOptimisation,
    LMFitter,
)
from formable.tensile_test import TensileTest


def fit_single_crystal_parameters(
    VE_response: dict,
    single_crystal_parameters: dict,
    tensile_test: dict,
    initial_damping: list[float] | None = None,
) -> dict[str, Any]:
    """Perform Levenberg-Marquardt optimisation."""

    # Generate FittingParameter objects:
    fitting_params = []
    null_perturbation_idx = None
    for idx, params in enumerate(single_crystal_parameters["iteration_0"]["value"]):
        if params.perturbations:
            path = params.perturbations["path"]
            name = "__".join([str(i) for i in path])
            value = get_by_path(params.base, path)

            fitting_param_i = FittingParameter(
                name=name,
                values=[value],
                address=path,
                perturbation=params.perturbations["multiplicative"],
            )
            fitting_params.append(fitting_param_i)
        else:
            # The null-perturbation does not correspond to a FittingParameter:
            null_perturbation_idx = idx

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

    # Generate fitter object:
    base_params = single_crystal_parameters["iteration_0"]["value"][0].base
    lm_fitter = LMFitter(
        exp_tensile_test=TensileTest(**tensile_test),
        single_crystal_parameters=base_params,
        fitting_params=fitting_params,
        initial_damping=initial_damping,
    )

    # Add simulated tests:
    for tensile_tests in tensile_tests_by_iteration:
        lm_fitter.add_simulated_tensile_tests(tensile_tests)

    optimised_single_crystal_parameters = lm_fitter.get_new_single_crystal_params(-1)

    outputs = {
        "single_crystal_parameters": {"phases": optimised_single_crystal_parameters},
        "levenberg_marquardt_fitter": lm_fitter.to_dict(),
    }
    return outputs


def get_by_path(root, path):
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

    sub_data = root
    for key in path:
        sub_data = sub_data[key]

    return sub_data


def get_hydrostatic_tensor(tensor):
    """Returns the hydrostatic tensor from an input stress strain tensor

    Parameters
    ----------
    tensor : ndarray of shape array (..., 3, 3)

    Returns
    -------
    (..., 3, 3) array hydrostatic stress on the diagonal of tensor with 0 in shear values

    """

    hydro = np.zeros_like(tensor)
    hydro[..., [0, 1, 2], [0, 1, 2]] = (np.trace(tensor, axis1=-2, axis2=-1) / 3)[
        ..., None
    ]
    return hydro


def get_von_mises(s, tensor):
    """Returns the equivalent value of stress or strain tensor

    Parameters
    ----------
    tensor : ndarray of shape (..., 3, 3)
        Tensor of which to get the von Mises equivalent.
    s : float
        Scaling factor: 3/2 for stress, 2/3 for strain.

    Returns
    -------
    Von Mises equivalent value of tensor.

    """

    deviatoric = tensor - get_hydrostatic_tensor(tensor)

    return np.sqrt(s * np.sum(deviatoric**2.0, axis=(-2, -1)))


def get_von_mises_stress(stress):
    return get_von_mises(3 / 2, stress)


def get_von_mises_strain(strain):
    return get_von_mises(2 / 3, strain)
