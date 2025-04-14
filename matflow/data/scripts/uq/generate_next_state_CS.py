import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm


def generate_next_state_CS(x, prop_std):
    """Generate the next candidate state using conditional sampling (a.k.a
    subset-infinity)

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
    rho = np.sqrt(1 - prop_std**2)

    return {"x": norm.rvs(loc=x * rho, scale=prop_std)}
