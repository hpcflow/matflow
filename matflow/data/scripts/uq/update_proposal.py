import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm


def update_proposal(lambda_, all_accept, all_x, all_g):
    """Adaptively update the proposal variance according to the acceptance rate of one or
    more Markov chains so far.
    """

    if all_g is not None:
        # stack from multiple chains (elements):
        all_x = np.array([i[:] for i in all_x])
        all_g = np.vstack([i[:] for i in all_g])
        all_accept = np.vstack([i[:] for i in all_accept])

    lambda_latest_iter = sorted(lambda_.items(), key=lambda x: int(x[0].split("_")[1]))[
        -1
    ][1]
    batch_idx = lambda_latest_iter["loop_idx"]["proposal_update"]
    lambda_ = lambda_latest_iter["value"]

    print(f"{lambda_latest_iter=!r}")
    print(f"{lambda_=!r}")

    if all_accept is None:
        # first iteration
        return {
            "lambda_": lambda_,
            "all_x": all_x,
            "all_g": all_g,
            "all_accept": all_accept,
        }

    A_STAR = 0.44

    num_accepts = all_accept.size
    num_chains_per_update = all_accept.shape[0]
    num_accepts_per_batch = int(num_accepts / batch_idx)
    batch_accept_col_idx = -int(num_accepts_per_batch / num_chains_per_update)

    # TODO: should include initial sample in batch_accept probably?
    batch_accept = all_accept[:, batch_accept_col_idx:]
    batch_accept_mean = np.mean(batch_accept)

    lambda_ = lambda_ * np.exp(
        (1 / np.sqrt(batch_idx + 1)) * (batch_accept_mean - A_STAR)
    )

    return {"lambda_": lambda_, "all_x": all_x, "all_g": all_g, "all_accept": all_accept}
