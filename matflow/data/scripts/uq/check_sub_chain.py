import os

import numpy as np


def check_sub_chain(
    all_x,
    sub_chain_x,
    sub_chain_g_coarse,
    num_inner_accepts,
    num_inner_states,
    threshold,
):
    """
    Check if the sub-chain has moved.
    """

    chain_idx = int(os.environ["MATFLOW_ELEMENT_IDX"])

    inner_accept_count = num_inner_accepts
    inner_accept_rate = (
        num_inner_accepts / num_inner_states if num_inner_states > 0 else None
    )

    psi = sub_chain_x[-1]
    # if chain_idx == 5:
    #     print(f"check_sub_chain: {psi.sum()=!r}")
    psi_gc = sub_chain_g_coarse[-1]

    current_x = all_x[-1]

    # did the coarse sub-chain actually move (meaning we need to run the fine model)?
    endpoint_moved = not np.array_equal(psi, current_x)
    endpoint_coarse_subset_pass = psi_gc > threshold

    return {
        "x": psi,
        "gc": psi_gc,
        "endpoint_moved": endpoint_moved,
        "endpoint_coarse_subset_pass": endpoint_coarse_subset_pass.item(),
        "inner_accept_count": inner_accept_count,
        "inner_accept_rate": inner_accept_rate,
    }
