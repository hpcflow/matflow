import os

import numpy as np


def increment_chain_inner(x, g, all_x, all_g, all_x_inner, all_g_inner, threshold):

    loop_idx = {
        loop_name: int(loop_idx)
        for loop_name, loop_idx in (
            item.split("=")
            for item in os.environ["MATFLOW_ELEMENT_ITER_LOOP_IDX"].split(";")
        )
    }

    if loop_idx["inner_markov_chain"] == 0:
        # first "inner" iteration, need to set initial value:
        all_x_inner = np.array(all_x[-1])[None]
        all_g_inner = np.array([all_g[-1]])

    current_x = all_x_inner[-1]
    current_g = all_g_inner[-1]

    if g is None:
        # failed system analysis, reject the state:
        is_accept = False
        print(f"Increment chain inner: failed system analysis, rejecting state.")
    else:
        trial_x = x[:]  # convert to numpy array
        trial_g = g
        is_accept = trial_g > threshold

    new_x = trial_x if is_accept else current_x
    new_g = trial_g if is_accept else current_g

    all_x_inner = np.vstack([all_x_inner, new_x[None]])
    all_g_inner = np.append(all_g_inner, np.array(new_g))

    return {
        "x": new_x,
        "all_x_inner": all_x_inner,
        "all_g_inner": all_g_inner,
    }
