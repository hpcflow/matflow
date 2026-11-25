import os

import numpy as np
from scipy.special import log_expit


def log_surrogate_weight(g_coarse, threshold, temperature):
    """Note temperature should be of a similar order of magnitude to `g_coarse` and
    `threshold`."""
    z = (g_coarse - threshold) / temperature
    return log_expit(z)


def increment_sub_chain(
    x,
    g,
    all_x,
    all_gc,
    sub_chain_x,
    sub_chain_g_coarse,
    sub_chain_accept,
    threshold,
    temperature,
    num_inner_accepts,
    rng,
):
    """Increment the sub-chain.

    ``x`` and ``g`` are the proposed state (via MMH) and the coarse model evaluation at
    that proposed state, respectively.

    ``all_x`` is the outer Markov chain states, whose final element is used as first
    element in the sub-chain.

    ``g_coarse_initial`` is the coarse model evaluation at the initial state of the
    sub-chain, which become the first element in the sub_chain_g_coarse array.

    """

    loop_idx = {
        loop_name: int(loop_idx)
        for loop_name, loop_idx in (
            item.split("=")
            for item in os.environ["MATFLOW_ELEMENT_ITER_LOOP_IDX"].split(";")
        )
    }
    if loop_idx["sub_chain"] == 0:
        num_inner_accepts = 0

    g_coarse = g["coarse"]
    g_coarse_initial = g["coarse_initial"]
    g = g_coarse

    if loop_idx["sub_chain"] == 0:
        # initial iteration
        sub_chain_x = np.array([all_x[-1]])
        if loop_idx["markov_chain_state"] == 0:
            sub_chain_g_coarse = np.array([g_coarse_initial])
        else:
            sub_chain_g_coarse = np.array([all_gc[-1]])
        sub_chain_accept = np.array([])

    current_sub_chain_x = sub_chain_x[-1]
    current_sub_chain_gc = sub_chain_g_coarse[-1]
    trial_x = x[:]  # convert to numpy array
    trial_gc = g

    if trial_gc is None:
        # simulation failed for some reason; reject
        chain_idx = int(os.environ["MATFLOW_ELEMENT_IDX"])
        print(
            f"Increment sub-chain: system analysis failed for chain index {chain_idx}, "
            f"Markov chain iteration index {loop_idx.get('markov_chain_state')}, coarse "
            f"sub-chain iteration index {loop_idx.get('sub_chain')!r}; rejecting the "
            f"state!"
        )
        is_accept = False
        new_x = current_sub_chain_x
        new_gc = current_sub_chain_gc

    else:

        log_s_current = log_surrogate_weight(current_sub_chain_gc, threshold, temperature)
        log_s_trial = log_surrogate_weight(trial_gc, threshold, temperature)
        log_alpha = min(0.0, log_s_trial - log_s_current)

        random_num = rng.random()
        is_accept = np.log(random_num) < log_alpha

        new_x = trial_x if is_accept else current_sub_chain_x
        new_gc = trial_gc if is_accept else current_sub_chain_gc
        if is_accept:
            num_inner_accepts += 1

    sub_chain_x = np.vstack([sub_chain_x, new_x[None]])
    sub_chain_g_coarse = np.append(sub_chain_g_coarse, np.array(new_gc))
    sub_chain_accept = np.append(sub_chain_accept, np.array(is_accept))

    return {
        "x": new_x,
        "g": new_gc,
        "sub_chain_x": sub_chain_x,
        "sub_chain_g_coarse": sub_chain_g_coarse,
        "sub_chain_accept": sub_chain_accept,
        "num_inner_accepts": num_inner_accepts,
        "rng": rng,
        "all_x": all_x[
            :
        ],  # TODO: this is workaround to ensure all_x is iterated in increment_chain_RST
        "all_gc": (
            all_gc[:] if all_gc is not None else None
        ),  # TODO: this is workaround to ensure all_gc is iterated in increment_chain_RST
    }
