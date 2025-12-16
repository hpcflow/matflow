import numpy as np

ROOT_EPS = np.sqrt(np.finfo(np.float64).eps)


def define_perturbations(trial_params):
    return np.abs(trial_params) * 0.01
    # return ROOT_EPS * (np.abs(trial_params) + 1)


def get_new_model_parameters(trial_params, perturbations):
    """Get sets of parameters at which to evaluate the model.

    Each row is a separate set of parameters, with the first row being the unperturbed
    parameters.
    """
    p_perturbed = np.tile(trial_params, (len(trial_params), 1)) + np.diag(perturbations)
    return np.vstack((trial_params, p_perturbed))


def perturb_parameters(p_0, p_i, p_scales):
    # print(f"perturb_parameters: {p_0[:]=!r}")

    if p_i is not None:
        # already scaled
        # print(f"perturb_parameters: {p_i[:]=!r}")
        # print(f"perturb_parameters: {p_scales[:]=!r}")
        trial_params = np.asarray(p_i)
    else:
        # first iteration; need to scale
        p_scales = p_0
        trial_params = np.ones(len(p_0))

    p_delta = define_perturbations(trial_params)
    # print(f"perturb_parameters: {p_delta=!r}")

    p_perturbed = get_new_model_parameters(trial_params, p_delta)
    # print(f"perturb_parameters: {trial_params=!r}")
    # print(f"perturb_parameters: {p_perturbed=!r}")
    return {
        "p_scales": np.asarray(p_scales),
        "p_perturbed": p_perturbed,
        "perturbations": p_delta,
        "p_i": trial_params,
    }
