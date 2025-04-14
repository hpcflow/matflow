import numpy as np


def estimate_cov(indicator, p_i: float) -> float:
    """Estimate the coefficient of variation at a given conditional level of the subset
    simulation."""

    num_chains, num_states = indicator.shape
    N = num_chains * num_states  # samples per level

    # covariance sequence (estimated), Eq. 29
    r = np.zeros(num_states - 1)
    for k in range(num_states - 1):
        r_k = 0
        for l in range(num_states - (k + 1)):
            i_1 = indicator[:, l]
            i_2 = indicator[:, l + k + 1]
            r_k_i = np.dot(i_1, i_2)
            r_k += r_k_i
        r[k] = (r_k / (N - (k + 1) * num_chains)) - p_i**2

    r_0 = np.sum(indicator**2) / N - p_i**2  # autocovariance at lag zero (exact)
    r_0 = p_i * (1 - p_i)

    rho = r / r_0

    gamma = 2 * sum(
        (1 - (k + 1) * num_chains / N) * rho[k] for k in range(num_states - 1)
    )

    delta = np.sqrt((1 - p_i) / (p_i * N) * (1 + gamma))

    return delta


def collate_results(g, x, p_0, all_g, all_x, all_accept):

    # all iterations of g are passed just to get the level index:
    # TODO: in future set and read loop_idx from environment variable?

    level_idx = sorted(g.items(), key=lambda x: int(x[0].split("_")[1]))[-1][1][
        "loop_idx"
    ]["levels"]

    g = g["iteration_0"]["value"]
    num_samples = len(g)

    if all_g:
        # from multiple Markov chains:
        g = np.concatenate([i[:] for i in all_g])
        accept = np.vstack([i[:] for i in all_accept])
        x = np.vstack([i[:] for i in all_x])
        accept_rate = np.mean(accept)
    else:
        # from initial direct Monte Carlo samples:
        g = np.array(g)
        x = np.vstack([i[:] for i in x])
        accept_rate = None

        # consider missing data in `g` by copying from non-missing data:
        bad_bool = g == None
        if np.any(bad_bool):
            bad_idx = np.where(bad_bool)[0]
            print(
                f"Collate results: missing {len(bad_idx)} system performance "
                f"evaluation(s) at indices: {bad_idx!r}."
            )
            good_idx = np.where(~bad_bool)[0]
            replace_idx = good_idx[: len(bad_idx)]
            replace_g = g[replace_idx]
            replace_x = x[replace_idx]
            x[bad_idx] = replace_x
            g_corrected = np.empty(len(g))
            g_corrected[good_idx] = g[good_idx]
            g_corrected[bad_idx] = replace_g
            g = g_corrected

    num_failed = int(np.sum(g > 0))
    num_chains = int(len(g) * p_0)
    num_states = int(num_samples / num_chains)

    # sort responses
    srt_idx = np.argsort(g)[::-1]  # sort by closest-to-failure first
    g = g[srt_idx]
    x = x[srt_idx, :]

    threshold = (g[num_chains - 1] + g[num_chains]) / 2

    # failure probability at this level:
    fail_bool = g > 0
    level_pf = np.mean(fail_bool) if threshold > 0 else p_0

    chain_seeds = x[:num_chains]
    chain_g = g[:num_chains]

    is_finished = (num_failed / num_samples) >= p_0

    pf = p_0**level_idx * num_failed / num_samples

    if all_g:
        # from multiple Markov chains:
        indicator = np.reshape(
            g > np.minimum(threshold, 0), (num_chains, num_states)
        ).astype(int)
        level_cov = estimate_cov(indicator, level_pf)
    else:
        # from initial direct Monte Carlo samples:
        level_cov = np.sqrt((1 - level_pf) / (num_samples * level_pf))

    return {
        "chain_seeds": chain_seeds,
        "chain_g": chain_g,
        "threshold": threshold,
        "num_chains": num_chains,
        "num_failed": num_failed,
        "level_pf": level_pf,
        "level_cov": level_cov,
        "pf": pf,
        "is_finished": is_finished,
        "accept_rate": accept_rate,
    }
