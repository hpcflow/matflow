import os

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm


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


def generate_next_state_CS(x, prop_std, rng, chain_index):
    """Generate the next candidate state using conditional sampling (a.k.a
    subset-infinity)

    Parameters
    ----------
    x
        Current state on which the candidate state will depend.
    prop_std
        Proposal distribution standard deviation.
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
    rho = np.sqrt(1 - prop_std**2)
    return {"x": norm.rvs(loc=x * rho, scale=prop_std, random_state=rng), "rng": rng}
