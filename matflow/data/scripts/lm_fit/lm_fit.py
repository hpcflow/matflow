import numpy as np


def solve_new_trial_parameters(
    damping_factors, jacobian, y_ref, y_unperturbed, trial_params
):
    # print(f"solve_new_trial_parameters: {damping_factors=!r}")
    # print(f"solve_new_trial_parameters: {jacobian=!r}")
    # print(f"solve_new_trial_parameters: {y_ref=!r}")
    # print(f"solve_new_trial_parameters: {y_unperturbed=!r}")
    # print(f"solve_new_trial_parameters: {trial_params=!r}")
    y_diff = y_ref - y_unperturbed
    b = np.hstack([y_diff, np.zeros(jacobian.shape[1])])

    kappas = []
    errors = []
    for damping in damping_factors:

        A = np.vstack([jacobian, np.sqrt(damping) * np.eye(jacobian.shape[1])])
        kappa, *_ = np.linalg.lstsq(A, b, rcond=None)
        kappas.append(kappa)
        errors.append(np.sum(np.abs(y_diff - jacobian @ kappa)))

    best_idx = np.argmin(errors)
    best_kappa = kappas[best_idx]
    new_damping = damping_factors[best_idx]

    return (trial_params + best_kappa, new_damping)


def approximate_jacobian(perturbations, y_unperturbed, y_perturbed):
    """
    Parameters
    ----------
    perturbations
        Perturbation for each parameter
    y_unperturbed
        Vector of the unperturbed model response.
    y_perturbed:
        Array of column vectors where each column corresponds to the model response where
        one parameter has been perturbed.

    """
    # print(f"approximate_jacobian: {perturbations[:]=!r}")
    # print(f"approximate_jacobian: {y_unperturbed[:]=!r}")
    # print(f"approximate_jacobian: {y_perturbed[:]=!r}")
    return (y_perturbed - y_unperturbed[:, None]) / perturbations


def get_trial_damping_factors(current_damping=None):
    base = np.array([0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0])
    return base * current_damping if current_damping is not None else base


def lm_fit(
    system_response,
    reference_response,
    perturbations,
    damping,
    p_i,
    p_scales,
    stop_tol,
):
    # print(f"lm_fit: {stop_tol=!r}")
    # print(f"lm_fit: {perturbations=!r}")
    # print(f"lm_fit: {p_scales=!r}")
    # print(f"lm_fit: {damping=!r}")
    # print(f"lm_fit: {p_i=!r}")
    # print(f"lm_fit: {reference_response=!r}")
    # print(f"lm_fit: {system_response=!r}")

    y_unpert = system_response[0][:]
    y_pert = np.asarray([resp[:] for resp in system_response[1:]])

    jac_approx = approximate_jacobian(perturbations, y_unpert, y_pert.T)
    # print(f"lm_fit: {jac_approx=!r}")
    p_i_next, new_damping = solve_new_trial_parameters(
        damping_factors=get_trial_damping_factors(damping),
        jacobian=jac_approx,
        y_ref=reference_response,
        y_unperturbed=y_unpert,
        trial_params=p_i,
    )
    print(f"lm_fit: {p_i[:]=!r}")
    print(f"lm_fit: {p_i_next[:]=!r}")
    print(f"lm_fit: {p_scales[:]=!r}")
    p_scales = p_scales[0] if isinstance(p_scales, list) else p_scales
    fit_params = p_scales * p_i_next
    is_converged = bool(np.linalg.norm(p_i_next - p_i) < stop_tol)
    # print(f"lm_fit: (2) {p_scales=!r}")
    print(f"lm_fit: {fit_params=!r}; {new_damping=!r} {is_converged=!r}")
    return {
        "p_i": p_i_next,
        "fit_parameters": fit_params,
        "damping": new_damping,
        "is_converged": is_converged,
    }
