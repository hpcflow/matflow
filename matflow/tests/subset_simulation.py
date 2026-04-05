"""Module containing functions to run a subset simulation on a simple toy model, used as a
validation of the MatFlow implementation."""

from matplotlib import pyplot as plt
import numpy as np
from scipy.stats import norm, multivariate_normal
from numpy.exceptions import AxisError


def sample_direct_MC(
    dimension, num_samples, seed: int = None, spawn_key: tuple[int] | None = None
):
    """This is convoluted to mimic the MatFlow implementation where individual samples
    are separate elements, with distinct RNG spawn keys."""
    samples = []
    for sample_idx in range(num_samples):
        seed_seq = np.random.SeedSequence(seed, spawn_key=tuple([*spawn_key, sample_idx]))
        rng = np.random.default_rng(seed_seq)
        pi = multivariate_normal(mean=np.zeros(dimension), cov=None, seed=rng)
        samples.append(np.atleast_1d(pi.rvs()))
    return np.array(samples)


def model(x):
    try:
        return np.sum(x, axis=1)
    except AxisError:
        return np.sum(x)


def get_y_star(p_f, dimension):
    return np.sqrt(dimension) * norm.ppf(1 - p_f)


def system_analysis_toy_model(x, dimension: int, target_pf: float):
    """`x` is within the failure domain if the return is greater than zero."""
    y_star = get_y_star(target_pf, dimension)
    g_i = model(x) - y_star
    return g_i


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


def subset_simulation(
    dimension=200,
    target_pf=1e-4,
    p_0=0.1,
    num_samples=100,
    num_levels=10,
    prop_std=0.1,
    master_seed=None,
):

    x = sample_direct_MC(dimension, num_samples, seed=master_seed, spawn_key=(0,))
    g = system_analysis_toy_model(x, dimension, target_pf=target_pf)

    level_covs = []
    for level_idx in range(num_levels):
        num_failed = int(np.sum(g > 0))
        num_chains = int(len(g) * p_0)
        num_states = int(num_samples / num_chains)
        g_unsrt = g.copy()

        # sort responses
        srt_idx = np.argsort(g)[::-1]  # sort by closest-to-failure first
        g = g[srt_idx]
        x = x[srt_idx, :]

        threshold = (g[num_chains - 1] + g[num_chains]) / 2

        # failure probability at this level:
        indicator = np.reshape(
            g_unsrt > np.minimum(threshold, 0), (num_chains, num_states)
        ).astype(int)
        level_pf = np.mean(indicator)

        chain_seeds = x[:num_chains]
        chain_g = g[:num_chains]

        pf = p_0**level_idx * num_failed / num_samples
        if level_idx == 0:
            level_cov = np.sqrt((1 - level_pf) / (num_samples * level_pf))
        else:
            level_cov = estimate_cov(indicator, level_pf)
        level_covs.append(level_cov)

        if is_finished := threshold > 0:
            cov = np.sqrt(sum(np.pow(level_covs, 2))).item()
            return pf, cov

        all_x = np.ones((num_chains, num_states, dimension)) * np.nan
        all_g = np.ones((num_chains, num_states)) * np.nan

        for chain_index in range(num_chains):

            # proceed this Markov chain until all states have been generated
            all_x[chain_index, 0] = chain_seeds[chain_index]
            all_g[chain_index, 0] = chain_g[chain_index]

            rng_state = None
            for state_idx in range(1, num_states):

                # RNG seed sequence for Markov chains:
                # note: this could be moved out of the state loop, but in this position
                # it matches the MatFlow implementation
                spawn_key = (4, level_idx, chain_index)
                chain_rng = np.random.default_rng(
                    np.random.SeedSequence(master_seed, spawn_key=spawn_key)
                )

                if rng_state is not None:
                    chain_rng.bit_generator.state = rng_state

                x = all_x[chain_index, state_idx - 1]
                g = all_g[chain_index, state_idx - 1]

                dim = len(x)
                current_state = x
                xi = np.empty(dim)

                proposal = norm(loc=current_state, scale=prop_std)
                xi_hat = np.atleast_1d(proposal.rvs(random_state=chain_rng))

                # accept_ratios = np.divide(*norm.pdf([xi_hat, current_state]))
                accept_ratios = np.exp(-0.5 * (xi_hat**2 - current_state**2))

                accept_idx = chain_rng.random(len(accept_ratios)) < np.minimum(
                    1, accept_ratios
                )

                xi[accept_idx] = xi_hat[accept_idx]
                xi[~accept_idx] = current_state[~accept_idx]

                trial_x = xi

                trial_g = system_analysis_toy_model(
                    trial_x, dimension, target_pf=target_pf
                )

                current_x = x
                current_g = g

                is_accept = trial_g > threshold
                new_x = trial_x if is_accept else current_x
                new_g = trial_g if is_accept else current_g

                all_x[chain_index, state_idx] = new_x
                all_g[chain_index, state_idx] = new_g

                rng_state = chain_rng.bit_generator.state

        g = all_g.reshape((num_samples))
        x = all_x.reshape((num_samples, dimension))


def get_stats(all_pf, all_cov):

    pf_mean = np.mean(all_pf).item()
    cov_empirical = np.std(all_pf) / pf_mean
    cov_estimate = np.mean(all_cov)
    cov_estimate_std = np.std(all_cov)

    return {
        "pf": all_pf,
        "cov": all_cov,
        "pf_mean": pf_mean,
        "cov_empirical": cov_empirical,
        "cov_estimate": cov_estimate,
        "cov_estimate_std": cov_estimate_std,
    }


def run_repeats(num_samples, prop_std=1.0, num_repeats=100):
    all_pf = []
    all_cov = []
    for repeat_idx in range(num_repeats):
        pc = (100 * (repeat_idx + 1)) // num_repeats
        if pc % 1 == 0:
            print(
                f"\rrunning {num_repeats} repeats with N={num_samples}...{pc:3d}%", end=""
            )
        pf, cov = subset_simulation(
            dimension=200,
            target_pf=1e-4,
            p_0=0.1,
            num_samples=num_samples,
            num_levels=10,
            prop_std=prop_std,
        )
        all_pf.append(pf)
        all_cov.append(cov)
    print()
    return get_stats(all_pf, all_cov)


def get_toy_model_results_from_matflow_workflows(root_path):
    """
    Parameters
    ----------
    root_path
        A directory containing only (zipped) workflows that are toy-model subset
        simulation run repeats.
    """
    all_pf = []
    all_cov = []
    for wk_path in root_path.glob("subset_simulation_toy_model_*"):
        wk = mf.Workflow(wk_path)
        iter_final = wk.tasks.collate_results.elements[0].latest_iteration_non_skipped
        all_pf.append(iter_final.get("outputs.pf"))
        all_cov.append(iter_final.get("outputs.cov"))

    return get_stats(all_pf, all_cov)


def plot_pf_num_samples(all_results, quantile_range, num_samples=None, num_repeats=None):
    """
    Specify exactly one of `num_samples` and `num_repeats`. The non-specified is taken to
    be the varying key in `all_results`.
    """

    if sum(i is not None for i in (num_samples, num_repeats)) != 1:
        raise ValueError("Specify num_samples or num_repeats")

    all_x = []
    all_y = []
    all_lower = []
    all_upper = []

    for N, data in all_results.items():

        pf_srt = sorted(data["pf"])
        _x0 = (1 - quantile_range) / 2
        _x1 = _x0 + quantile_range
        lower = np.quantile(pf_srt, _x0)
        upper = np.quantile(pf_srt, _x1)

        all_x.append(N)
        all_y.append(data["pf_mean"])
        all_lower.append(lower)
        all_upper.append(upper)

    plt.figure(figsize=(5, 4))
    plt.fill_between(
        x=all_x, y1=all_lower, y2=all_upper, alpha=0.5, label=f"CI: {quantile_range}"
    )
    plt.scatter(x=all_x, y=all_y, marker="o", label="Mean")
    plt.hlines(
        y=1e-4, xmin=min(all_results), xmax=max(all_results), color="gray", label="Target"
    )
    # plt.xscale("log")
    plt.yscale("log")
    plt.xlabel(f"{'Num samples, N' if num_repeats else 'Num repeats, R'}")
    plt.ylabel("Prob. of failure, pf")
    plt.title(f"{num_repeats=!r}" if num_repeats else f"{num_samples=!r}")
    plt.legend()


def plot_cov_estimates(results, ylim=None, num_repeats=None, num_samples=None):
    """
    Specify exactly one of `num_samples` and `num_repeats`. The non-specified is taken to
    be the varying key in `all_results`.
    """
    if sum(i is not None for i in (num_samples, num_repeats)) != 1:
        raise ValueError("Specify num_samples or num_repeats")

    all_x = []
    cov_empirical = []
    cov_estimated = []
    cov_estimated_std = []

    for N, data in results.items():

        all_x.append(N)
        cov_empirical.append(data["cov_empirical"])
        cov_estimated.append(data["cov_estimate"])
        cov_estimated_std.append(data["cov_estimate_std"])

    plt.figure(figsize=(5, 4))
    plt.plot(all_x, cov_empirical, label="empirical CoV")
    plt.errorbar(x=all_x, y=cov_estimated, yerr=cov_estimated_std, label="estimated CoV")
    plt.xlabel(f"{'Num samples, N' if num_repeats else 'Num repeats, R'}")
    plt.ylabel("CoV")
    plt.title(f"{num_repeats=!r}" if num_repeats else f"{num_samples=!r}")
    plt.legend()
    if ylim:
        plt.ylim(ylim)


def plot_pf_dist(results, target_pf):
    fig, axs = plt.subplots(
        1, len(results), figsize=(len(results) * 2.5, 3), sharex=True, sharey=True
    )
    for idx, (N, data) in enumerate(results.items()):
        axs[idx].hist(np.log10(data["pf"]))
        axs[idx].set_title(f"Num. samples, N={N}")
        axs[idx].axvline(np.log10(target_pf), color="gray")

    # One label for the whole figure
    fig.supxlabel("log10(Prob. of failure)")
    fig.supylabel("Frequency")
    plt.tight_layout()


def plot_cov_dist(results):
    fig, axs = plt.subplots(
        1, len(results), figsize=(len(results) * 2.5, 3), sharex=True, sharey=True
    )
    for idx, (N, data) in enumerate(results.items()):
        axs[idx].hist(data["cov"])
        axs[idx].set_title(f"Num. samples, N={N}")

    # One label for the whole figure
    fig.supxlabel("CoV")
    fig.supylabel("Frequency")
    plt.tight_layout()
