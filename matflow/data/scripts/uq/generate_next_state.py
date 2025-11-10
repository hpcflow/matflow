import logging

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm


def set_up_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    fh = logging.FileHandler("script.log")
    fh_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s:%(filename)s: %(message)s"
    )
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)
    return logger


def generate_next_state(x, prop_std):
    """Generate the next candidate state in a modified Metropolis algorithm.

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
    dim = len(x)
    current_state = x
    rng = np.random.default_rng()
    xi = np.empty(dim)

    proposal = norm(loc=current_state, scale=prop_std)
    xi_hat = np.atleast_1d(proposal.rvs())
    accept_ratios = np.divide(*norm.pdf([xi_hat, current_state]))
    accept_idx = rng.random(len(accept_ratios)) < np.minimum(1, accept_ratios)

    xi[accept_idx] = xi_hat[accept_idx]
    xi[~accept_idx] = current_state[~accept_idx]

    return {"x": xi}
