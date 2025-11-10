import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm


def generate_next_state_ACS(x, prop_std, lambda_):
    """Generate the next candidate state using adaptive conditional sampling (a.k.a
    adaptive subset-infinity)

    Parameters
    ----------
    x
        Current state on which the candidate state will depend.

    Returns
    -------
    dict:
        x:
            Generated candidate state.
    """

    x = x[:]  # convert to numpy array
    sigma = np.minimum(1, lambda_ * prop_std)
    rho = np.sqrt(1 - sigma**2)

    return {"x": norm.rvs(loc=x * rho, scale=sigma)}
