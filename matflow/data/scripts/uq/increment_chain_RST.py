import os

import numpy as np
from scipy.special import log_expit


def log_surrogate_weight(g_coarse, threshold, temperature):
    """Note temperature should be of a similar order of magnitude to `g_coarse` and
    `threshold`."""
    z = (g_coarse - threshold) / temperature
    return log_expit(z)


def increment_chain_RST(
    endpoint_moved,
    x,
    g,
    gc,
    all_x,
    all_g,
    all_gc,
    all_accept,
    threshold,
    temperature,
    rng,
    num_inner_states,
    fine_eval_count,
    coarse_eval_count,
):
    """
    Increment the outer Markov chain with either the proposal from the end of the coarse
    model sub-chain, or with the current outer state.

    Parameters
    ----------
    x
        New proposed state; the final proposed state of the sub-chain.
    g
        Fine model evaluation of the new proposed state.
    gc
        Coarse model evaluation of the new proposed state.
    all_x
        Markov chain states so far.
    all_g
        Fine model evaluations for each of the Markov chain states so far.

    """

    loop_idx = {
        loop_name: int(loop_idx)
        for loop_name, loop_idx in (
            item.split("=")
            for item in os.environ["MATFLOW_ELEMENT_ITER_LOOP_IDX"].split(";")
        )
    }

    if loop_idx["markov_chain_state"] == 0:
        # initial iteration of the outer Markov chain, for this subset level
        all_gc = np.array([g["coarse_initial"]])
        fine_eval_count = 0
        coarse_eval_count = 1  # initial coarse evaluation, once per subset level chain

    coarse_eval_count += num_inner_states

    current_gc = all_gc[-1]
    current_x = all_x[-1]
    current_g = all_g[-1]
    fine_accept = False

    if not endpoint_moved:
        new_x = current_x
        new_g = current_g
        new_gc = current_gc

    else:
        fine_eval_count += 1

        g_fine = g["fine"]
        g = g_fine

        fine_subset_pass = g > threshold

        if not fine_subset_pass:

            # fine target is zero here
            new_x = current_x
            new_g = current_g
            new_gc = current_gc

        else:

            # ------------------------------------------------
            # Final RST correction
            #
            # alpha_F =
            # min(1, pi_C(current_x) / pi_C(psi))
            #
            # The phi terms cancel, leaving:
            #
            # alpha_F =
            # min(1, s(current_x) / s(psi))
            # ------------------------------------------------

            log_s_current = log_surrogate_weight(current_gc, threshold, temperature)
            log_s_psi = log_surrogate_weight(gc, threshold, temperature)

            log_alpha_fine = min(0.0, log_s_current - log_s_psi)

            random_num = rng.random()
            fine_accept = np.log(random_num) < log_alpha_fine

            if fine_accept:
                new_x = x[:]  # convert to Numpy array
                new_g = g
                new_gc = gc
            else:
                new_x = current_x
                new_g = current_g
                new_gc = current_gc

    all_x = np.vstack([all_x, new_x[None]])
    all_g = np.append(all_g, np.array(new_g))
    all_gc = np.append(all_gc, np.array(new_gc))
    all_accept = np.append(all_accept, np.array(fine_accept))

    return {
        "x": new_x,
        "g": new_g,
        "gc": new_gc,
        "all_x": all_x,
        "all_g": all_g,
        "all_gc": all_gc,
        "all_accept": all_accept,
        "rng": rng,
        "fine_eval_count": fine_eval_count,
        "coarse_eval_count": coarse_eval_count,
    }
