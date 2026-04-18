import logging
import os

import numpy as np
import scipy.stats


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


def _init_rng(chain_index, loop_idx):
    """Initialise the random number generator, which must happen once for each Markov
    chain."""
    random_seed = int(os.environ["MATFLOW_RUN_RANDOM_SEED"])
    spawn_key_str = os.environ["MATFLOW_RUN_RNG_SPAWN_KEY"]
    task_iID = int(os.environ["MATFLOW_TASK_INSERT_ID"])
    spawn_key = tuple(int(i) for i in spawn_key_str.split(",")) if spawn_key_str else ()
    spawn_key = tuple([*spawn_key, task_iID, loop_idx["levels"], chain_index])
    rng = np.random.default_rng(
        np.random.SeedSequence(
            random_seed,
            spawn_key=spawn_key,
        )
    )
    return rng


def generate_next_state(x, proposal, rng, chain_index):
    """Generate the next candidate state in a modified Metropolis algorithm.

    Parameters
    ----------
    x
        Current state on which the candidate state will depend.
    proposal
        Type and arguments to a Scipy distribution that should be used as the proposal.
        The proposal must be a symmetrical distribution, centred on zero.
    rng
        Random number generator to be used in this function.
    chain_index
        Index of the Markov chain within the subset simulation level loop.

    Returns
    -------
    dict:
        x:
            Generated candidate state.
        rng:
            Random number generator to be used in the next invocation of this function,
            for this chain.
    """

    dist_type = proposal.pop("type")
    prop_dist = getattr(scipy.stats, dist_type)(**proposal)

    loop_idx = {
        loop_name: int(loop_idx)
        for loop_name, loop_idx in (
            item.split("=")
            for item in os.environ["MATFLOW_ELEMENT_ITER_LOOP_IDX"].split(";")
        )
    }

    if loop_idx["markov_chain_state"] == 0:
        # new chain, so want a new RNG:
        rng = _init_rng(chain_index, loop_idx)

    x = x[:]  # convert to numpy array
    dim = len(x)
    current_state = x
    xi = np.empty(dim)

    xi_hat = np.atleast_1d(current_state + prop_dist.rvs(size=dim, random_state=rng))
    accept_ratios = np.divide(*scipy.stats.norm.pdf([xi_hat, current_state]))
    accept_idx = rng.random(len(accept_ratios)) < np.minimum(1, accept_ratios)

    xi[accept_idx] = xi_hat[accept_idx]
    xi[~accept_idx] = current_state[~accept_idx]

    return {"x": xi, "rng": rng}
