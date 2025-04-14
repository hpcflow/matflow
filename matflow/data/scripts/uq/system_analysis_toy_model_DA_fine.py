import os
import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm


def _to_physical_space(dist, variates):
    """Convert random variables defined in standard normal space to some other
    continuous distribution space."""
    return dist.ppf(norm.cdf(variates, loc=0, scale=1))


def to_physical_space(dists, variates):
    """Convert random variables sampled from the standard normal space to the specified
    distribution spaces.

    Parameters
    ----------
    dists
        List of SciPy frozen distribution instances
    variates
        Standard-normally distributed random variates. Outer dimension must
        match length of `dists` list.
    """
    funcs = [_lookup.get(i.dist.name, ("", _to_physical_space))[1] for i in dists]
    assert len(funcs) == len(variates)
    inputs_t = np.empty_like(variates)
    for idx, (func_i, ins_i) in enumerate(zip(funcs, variates)):
        inputs_t[idx] = func_i(dists[idx], ins_i)
    return inputs_t


_lookup = {}


def model(x):
    return np.tanh(x)


def system_analysis_toy_model_DA_fine(
    x: NDArray, x_0: float, stddev: float, y_star: float
):
    """`x` is within the failure domain if the return is greater than zero."""
    x = x[:]  # convert to numpy array; random variate in standard normal space

    # mock a failure:
    if os.environ["MATFLOW_RUN_ID"] in ("100", "2632"):
        print(f"run ID {os.environ['MATFLOW_RUN_ID']}! returning!")
        raise ValueError("bad!")

    input_dist = norm(loc=x_0, scale=stddev)
    x_t = to_physical_space([input_dist], x)

    g_i = np.squeeze(y_star - model(x_t)).item()
    return {"g": g_i}
