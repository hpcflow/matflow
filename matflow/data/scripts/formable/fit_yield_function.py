from __future__ import annotations
from pathlib import Path
from formable import LoadResponse, LoadResponseSet
import numpy as np
from numpy.typing import NDArray


def fit_yield_function(
    yield_function_name: str,
    yield_point_criteria: dict,
    VE_response: dict,
    fit_yield_fixed_parameters: dict,
    fit_yield_initial_parameters: dict,
    fit_yield_opt_parameters: dict,
) -> dict:
    """
    Parameters
    ----------
    yield_function_name : str
    yield_point_criteria : dict
    VE_response: dict
    fit_yield_fixed_parameters : dict
    fit_yield_initial_parameters: dict
    fit_yield_opt_parameters : dict
        Optimisation parameters. Dict with any of the keys:
            default_bounds : list of length two, optional
                The bounds applied to all non-fixed yield function parameters by
                default.
            bounds : dict, optional
                Dict of bounds for individual named parameters. These bounds take
                precedence over `default_bounds`.
            **kwargs : dict
                Other parameters to be passed to the SciPy least_squares function.

    """

    uniaxial_response = VE_response["uniaxial"]
    multiaxial_responses = VE_response["multiaxial"]

    # Generate LoadResponse objects:
    eq_vol_avg_plastic_strain = _get_von_mises_strain(
        uniaxial_response["volume_data"]["vol_avg_plastic_strain"]["data"]
    )
    uni_resp = LoadResponse(
        stress=uniaxial_response["volume_data"]["vol_avg_stress"]["data"][:],
        equivalent_plastic_strain=eq_vol_avg_plastic_strain,
    )
    multi_resp = []
    for resp_dat in multiaxial_responses:
        eq_vol_avg_plastic_strain_i = _get_von_mises_strain(
            resp_dat["volume_data"]["vol_avg_plastic_strain"]["data"]
        )
        multi_resp.append(
            LoadResponse(
                stress=resp_dat["volume_data"]["vol_avg_stress"]["data"][:],
                equivalent_plastic_strain=eq_vol_avg_plastic_strain_i,
            )
        )
    response_set = LoadResponseSet(multi_resp)
    response_set.calculate_yield_stresses(yield_point_criteria)
    response_set.fit_yield_function(
        yield_function_name,
        uniaxial_response=uni_resp,
        initial_params=fit_yield_initial_parameters,
        opt_params=fit_yield_opt_parameters,
        **(fit_yield_fixed_parameters or {}),
    )
    fitted_yield_functions = response_set.to_dict()

    return {"fitted_yield_functions": fitted_yield_functions}


def _get_hydrostatic_tensor(tensor: NDArray) -> NDArray:
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


def _get_von_mises(s: float, tensor: NDArray) -> NDArray:
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

    deviatoric = tensor - _get_hydrostatic_tensor(tensor)

    return np.sqrt(s * np.sum(deviatoric**2.0, axis=(-2, -1)))


def _get_von_mises_stress(stress: NDArray) -> NDArray:
    return _get_von_mises(3 / 2, stress)


def _get_von_mises_strain(strain: NDArray) -> NDArray:
    return _get_von_mises(2 / 3, strain)
