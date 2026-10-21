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

    r_0 = p_i * (1 - p_i)

    if np.isclose(r_0, 0.0):
        # i.e. p_i is 1.0
        return 0.0

    rho = r / r_0

    gamma = 2 * sum(
        (1 - (k + 1) * num_chains / N) * rho[k] for k in range(num_states - 1)
    )

    delta = np.sqrt((1 - p_i) / (p_i * N) * (1 + gamma))

    return delta


def rms_jump_distances(all_x: np.ndarray, diff_axis) -> np.ndarray:
    """RMS jump distance between consecutive stored chain states."""
    dx = np.diff(all_x, axis=diff_axis)
    return np.linalg.norm(dx, axis=-1) / np.sqrt(dx.shape[-1])


def collate_results(
    g,
    x,
    p_0,
    all_g,
    all_x,
    all_accept,
    level_cov,
    total_fine_eval_count,
    total_coarse_eval_count,
    fine_eval_count,
    coarse_eval_count,
    fine_eval_rates,
    num_components_accepted,
    num_components_proposed,
):

    # all iterations of g are passed just to get the level index:
    # TODO: in future set and read loop_idx from environment variable?

    level_idx = sorted(g.items(), key=lambda x: int(x[0].split("_")[1]))[-1][1][
        "loop_idx"
    ]["levels"]

    if fine_eval_rates is None:
        fine_eval_rates = []

    g = g["iteration_0"]["value"]
    num_samples = len(g)
    num_chains = int(num_samples * p_0)
    num_states = int(num_samples / num_chains)

    if all_g:
        # from multiple Markov chains:
        g_unsrt = np.concatenate([i[:] for i in all_g])
        all_all_accept = []
        for iter_dat in all_accept.values():
            if iter_dat["value"]:
                all_all_accept.append(np.vstack([i[:] for i in iter_dat["value"]]))
        outer_move_rate = np.mean(all_all_accept, axis=(1, 2))
        x = []
        jump_distances = []
        for i in all_x:
            x.append(i[:])
            jump_distances.extend(rms_jump_distances(i, diff_axis=0))
        x = np.vstack(x)

        # sum over chains:
        num_components_accepted = sum(num_components_accepted)
        num_components_proposed = sum(num_components_proposed)
        component_acceptance_rate = num_components_accepted / num_components_proposed

        jump_distances = np.array(jump_distances)
        mean_jump_distance = np.mean(jump_distances).item()

        # sum across chains:
        fine_eval_count = np.sum(fine_eval_count)

        # excluding seed points, from previous level:
        total_states = num_chains * (num_states - 1)

        if coarse_eval_count[0] is not None:
            # e.g. for delayed acceptance variant; sum across chains:
            coarse_eval_count = int(np.sum(coarse_eval_count))
            total_coarse_eval_count += coarse_eval_count
        else:
            coarse_eval_count = None
    else:
        # from initial direct Monte Carlo samples:
        g_unsrt = np.array(g)
        x = np.vstack([i[:] for i in x])
        outer_move_rate = None
        total_states = num_samples
        fine_eval_count = g_unsrt.size
        mean_jump_distance = None
        component_acceptance_rate = None

    fine_eval_count = int(fine_eval_count)
    total_fine_eval_count += fine_eval_count

    # consider missing data in `g` by copying from non-missing data:
    bad_bool = g_unsrt == None
    if np.any(bad_bool):
        bad_idx = np.where(bad_bool)[0]
        print(
            f"Collate results: missing {len(bad_idx)} system performance "
            f"evaluation(s) at indices: {bad_idx!r}."
        )
        good_idx = np.where(~bad_bool)[0]
        replace_idx = good_idx[: len(bad_idx)]
        replace_g = g_unsrt[replace_idx]
        replace_x = x[replace_idx]
        x[bad_idx] = replace_x
        g_corrected = np.empty(len(g_unsrt))
        g_corrected[good_idx] = g_unsrt[good_idx]
        g_corrected[bad_idx] = replace_g
        g_unsrt = g_corrected

    num_failed = int(np.sum(g_unsrt > 0))

    # rate of fine evaluations for the previous level:
    fine_eval_rate = fine_eval_count / total_states
    fine_eval_rates.append(fine_eval_rate)

    # sort responses
    srt_idx = np.argsort(g_unsrt)[::-1]  # sort by closest-to-failure first
    g = g_unsrt[srt_idx]
    x = x[srt_idx, :]

    threshold = (g[num_chains - 1] + g[num_chains]) / 2

    # indicator function:
    g_2D = np.reshape(g_unsrt, (num_chains, num_states))
    indicator = (g_2D > np.minimum(threshold, 0)).astype(int)

    # failure probability at this level:
    level_pf = np.mean(indicator)

    chain_seeds = x[:num_chains]
    chain_g = g[:num_chains]

    is_finished = (threshold > 0).item()

    pf = p_0**level_idx * num_failed / num_samples

    # all previous level CoVs:
    all_level_cov = []
    del level_cov["iteration_0"]
    for iter_dat in level_cov.values():
        all_level_cov.append(iter_dat["value"])

    if all_g:
        # from multiple Markov chains:
        level_cov = estimate_cov(indicator, level_pf)
    else:
        # from initial direct Monte Carlo samples:
        level_cov = np.sqrt((1 - level_pf) / (num_samples * level_pf))
    all_level_cov.append(level_cov)

    cov = np.sqrt(sum(np.pow(all_level_cov, 2))).item()

    print(
        f"collate_results summary for level index {level_idx}\n"
        f"---------------------------------------------------\n"
        f"is_finished: {is_finished}\n"
        f"pf: {pf}\n"
        f"cov: {cov}\n"
        f"threshold: {threshold.item()!r}\n"
        f"num_samples: {num_samples!r}\n"
        f"num_chains: {num_chains!r}\n"
        f"num_failed: {num_failed!r}\n"
        f"outer_move_rate: {outer_move_rate if outer_move_rate is not None else '-'}\n"
        f"total_fine_eval_count: {total_fine_eval_count!r}\n"
        f"total_coarse_eval_count: {total_coarse_eval_count!r}\n"
        f"level_pf: {level_pf.item()!r}\n"
        f"level_cov: {level_cov.item()!r}\n"
        f"level_fine_eval_count: {fine_eval_count!r}\n"
        f"level_fine_eval_rate: {fine_eval_rate!r}\n"
        f"level_coarse_eval_count: {coarse_eval_count if coarse_eval_count is not None else '-'}\n"
        f"fine_eval_rates: {fine_eval_rates!r}\n"
        f"component_acceptance_rate: {component_acceptance_rate if component_acceptance_rate is not None else '-'}\n"
        f"mean_jump_distance: {mean_jump_distance if mean_jump_distance is not None else '-'}\n"
        "\n",
    )

    return {
        "chain_seeds": chain_seeds,
        "chain_g": chain_g,
        "threshold": threshold,
        "num_chains": num_chains,
        "num_failed": num_failed,
        "level_pf": level_pf,
        "level_cov": level_cov,
        "level_fine_eval_count": fine_eval_count,
        "level_fine_eval_rate": fine_eval_rate,
        "level_coarse_eval_count": coarse_eval_count,
        "fine_eval_rates": fine_eval_rates,
        "pf": pf,
        "is_finished": is_finished,
        "outer_move_rate": outer_move_rate,
        "cov": cov,
        "total_fine_eval_count": total_fine_eval_count,
        "total_coarse_eval_count": total_coarse_eval_count,
        "component_acceptance_rate": component_acceptance_rate,
        "mean_jump_distance": mean_jump_distance,
    }
