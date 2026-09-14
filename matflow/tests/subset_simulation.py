"""Module containing functions to run a subset simulation on a simple toy model, used as a
validation of the MatFlow implementation."""

import copy
from datetime import datetime
import pickle
from pathlib import Path
from typing import Callable

from matplotlib import pyplot as plt
import numpy as np
from scipy.stats import norm, multivariate_normal, uniform
from scipy.special import log_expit
from numpy.exceptions import AxisError
from hpcflow.sdk.log import TimeIt

import matflow as mf

from .subset_simulation_result import (
    LevelSamplingResult,
    DALevelSamplingResult,
    ACSLevelSamplingResult,
    SubsetSimulationResult,
    rms_jump_distances,
)


@TimeIt.decorator
def sample_direct_MC(
    dimension,
    num_samples,
    seed: int = None,
    spawn_key: tuple[int] | None = None,
    mimic_matflow: bool = False,
):
    if mimic_matflow:
        # convoluted to mimic the MatFlow implementation where individual samples
        # are separate elements, with distinct RNG spawn keys.
        # TODO: this can be avoided once we support multi-element Python scripts in MatFlow
        samples = []
        for sample_idx in range(num_samples):
            spawn_key_ = tuple([*spawn_key, sample_idx])
            seed_seq = np.random.SeedSequence(seed, spawn_key=spawn_key_)
            rng = np.random.default_rng(seed_seq)
            pi = multivariate_normal(mean=np.zeros(dimension), cov=None, seed=rng)
            samples.append(np.atleast_1d(pi.rvs()))
        return np.array(samples)
    else:
        # simpler and considerably faster!
        rng = np.random.default_rng(seed)
        pi = multivariate_normal(mean=np.zeros(dimension), cov=None, seed=rng)
        return pi.rvs(num_samples)


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


def get_y_star_max_system(target_pf: float, dimension: int) -> float:
    """Analytic failure threshold for a 'weakest-link' (series-system) toy model: the
    system response is the maximum over `dimension` iid standard normal components, so
    P(max(X) <= y) = Phi(y)**dimension, giving an exact threshold for a target failure
    probability.
    """
    return norm.ppf((1 - target_pf) ** (1 / dimension))


def get_approx_pf_random_walk(sigma, dimension, y_star):
    # if a sufficiently fine random walk, we assume Brownian motion, plus a continuity
    # correction:
    return 2 * (1 - norm.cdf((y_star + 0.5826 * sigma) / (sigma * np.sqrt(dimension))))


def get_approx_y_star_random_walk(sigma, dimension, target_pf):
    z = norm.ppf(1 - target_pf / 2)
    return sigma * (np.sqrt(dimension) * z - 0.5826)


def make_voxel_grouping(dimension: int, block_size: int):
    """Partition `dimension` fine grid points into contiguous blocks of `block_size`
    (the last block may be smaller), representing a coarser mesh voxelisation."""
    if block_size < 1:
        raise ValueError("block_size must be >= 1")
    n_blocks = int(np.ceil(dimension / block_size))
    return np.repeat(np.arange(n_blocks), block_size)[:dimension]


def voxel_block_average(x, group_idx):
    """Coarse-grain `x` (..., dimension) by averaging within each block defined by
    `group_idx`, broadcasting each block's mean back over its fine positions (so fine
    and coarse fields live in the same space)."""
    x = np.asarray(x)
    out = np.empty_like(x, dtype=float)
    for block_idx in range(group_idx.max() + 1):
        mask = group_idx == block_idx
        out[..., mask] = x[..., mask].mean(axis=-1, keepdims=True)
    return out


def weakest_link_performance_fine(x, y_star):
    """'Fine mesh' weakest-link performance: the system fails if the peak local
    response (max over all `dimension` fine grid points) exceeds `y_star` -- e.g. a
    localised stress/strain concentration triggering failure anywhere in the domain.
    """
    return np.max(x, axis=-1) - y_star


def weakest_link_performance_coarse(x, y_star, group_idx):
    """'Coarse mesh' weakest-link performance: as `weakest_link_performance_fine`, but
    evaluated on a block-averaged (coarser-voxelised) version of the field. Averaging
    smooths out sub-block fluctuations, so the coarse peak response never exceeds the
    fine one (`max(block_average(x)) <= max(x)`, by convexity of the mean) -- exactly
    mirroring how a coarser FE mesh smooths out local stress/strain concentrations
    relative to a finer one. This guarantees the coarse model can only *underestimate*
    peak failure severity relative to the fine model, never overestimate it, so
    `estimate_conservative_threshold_coarse`'s margin is always well-defined and finite
    (no risk of unbounded extrapolation error, unlike a curve-fit surrogate).
    """
    x_coarse = voxel_block_average(x, group_idx)
    return np.max(x_coarse, axis=-1) - y_star


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


def generate_next_state(x, proposal, rng):
    """
    Proposal must be a symmetric distribution centred on zero.
    """

    dim = len(x)
    current_state = x
    xi = np.empty(dim)

    xi_hat = np.atleast_1d(current_state + proposal.rvs(size=dim, random_state=rng))
    accept_ratios = np.divide(*norm.pdf([xi_hat, current_state]))

    accept_idx = rng.random(len(accept_ratios)) < np.minimum(1, accept_ratios)

    xi[accept_idx] = xi_hat[accept_idx]
    xi[~accept_idx] = current_state[~accept_idx]
    mcmc_accept_rate = np.mean(accept_idx)

    return xi, mcmc_accept_rate


def generate_next_state_CS(x, prop_std, rng):
    rho = np.sqrt(1 - prop_std**2)
    return norm.rvs(loc=x * rho, scale=prop_std, random_state=rng)


def generate_next_state_ACS(x, prop_std, lambda_, rng):
    a_star = 0.44
    sigma = np.minimum(1, lambda_ * prop_std)
    rho = np.sqrt(1 - sigma**2)
    return norm.rvs(loc=x * rho, scale=sigma, random_state=rng)


def generate_next_level_samples(
    performance,
    num_chains,
    num_states,
    dimension,
    chain_seeds,
    chain_g,
    all_x,
    all_g,
    level_idx,
    master_seed,
    threshold,
    proposal,
    transformation: Callable | None = None,
    debug: bool = False,
) -> LevelSamplingResult:

    subset_accept_arr = np.zeros((num_chains, num_states - 1)).astype(bool)
    component_accept_arr = np.zeros((num_chains, num_states - 1))

    for chain_index in range(num_chains):

        # proceed this Markov chain until all states have been generated
        all_x[chain_index, 0] = chain_seeds[chain_index]
        all_g[chain_index, 0] = chain_g[chain_index]

        chain_rng = None
        for state_idx in range(1, num_states):

            # RNG seed sequence for Markov chains:
            if state_idx == 1:
                # spawn key to match the task ID in the matflow workflow
                spawn_key = (4, level_idx, chain_index)
                chain_rng = np.random.default_rng(
                    np.random.SeedSequence(master_seed, spawn_key=spawn_key)
                )

            x = all_x[chain_index, state_idx - 1]
            g = all_g[chain_index, state_idx - 1]

            trial_x, mcmc_accept_rate = generate_next_state(
                x=x,
                proposal=proposal,
                rng=chain_rng,
            )
            component_accept_arr[chain_index, state_idx - 1] = mcmc_accept_rate
            trial_x_t = transformation(trial_x) if transformation else trial_x
            trial_g = performance(trial_x_t)

            current_x = x
            current_g = g
            is_ss_accept = trial_g > threshold
            subset_accept_arr[chain_index, state_idx - 1] = is_ss_accept
            new_x = trial_x if is_ss_accept else current_x
            new_g = trial_g if is_ss_accept else current_g

            all_x[chain_index, state_idx] = new_x
            all_g[chain_index, state_idx] = new_g

    subset_accept = np.mean(subset_accept_arr).item()
    num_fine_evals = num_chains * (num_states - 1)
    component_acceptance_rate = np.mean(component_accept_arr).item()
    jump_distances = rms_jump_distances(all_x)
    mean_jump_distance = np.mean(jump_distances).item()
    outer_move_rate = np.mean(jump_distances > 0).item()

    return LevelSamplingResult(
        x=all_x,
        g=all_g,
        component_acceptance_rate=component_acceptance_rate,
        subset_acceptance_rate=subset_accept,
        mean_jump_distance=mean_jump_distance,
        jump_distances=jump_distances,
        outer_move_rate=outer_move_rate,
        num_fine_evals=num_fine_evals,
    )


def generate_next_level_samples_CS(
    performance,
    num_chains,
    num_states,
    dimension,
    chain_seeds,
    chain_g,
    all_x,
    all_g,
    level_idx,
    master_seed,
    threshold,
    prop_std,
    transformation: Callable | None = None,
    debug: bool = False,
) -> LevelSamplingResult:
    """Conditional sampling algorithm for generating states in the subset simulation level
    (aka subset infinity).

    """
    subset_accept_arr = np.zeros((num_chains, num_states - 1)).astype(bool)
    for chain_index in range(num_chains):

        # proceed this Markov chain until all states have been generated
        all_x[chain_index, 0] = chain_seeds[chain_index]
        all_g[chain_index, 0] = chain_g[chain_index]

        chain_rng = None
        for state_idx in range(1, num_states):

            # RNG seed sequence for Markov chains:
            if state_idx == 1:
                # spawn key to match the task ID in the matflow workflow
                spawn_key = (4, level_idx, chain_index)
                chain_rng = np.random.default_rng(
                    np.random.SeedSequence(master_seed, spawn_key=spawn_key)
                )

            x = all_x[chain_index, state_idx - 1]
            g = all_g[chain_index, state_idx - 1]

            trial_x = generate_next_state_CS(
                x=x,
                prop_std=prop_std,
                rng=chain_rng,
            )
            trial_x_t = transformation(trial_x) if transformation else trial_x
            trial_g = performance(trial_x_t)

            current_x = x
            current_g = g

            is_accept = trial_g > threshold
            subset_accept_arr[chain_index, state_idx - 1] = is_accept
            new_x = trial_x if is_accept else current_x
            new_g = trial_g if is_accept else current_g

            all_x[chain_index, state_idx] = new_x
            all_g[chain_index, state_idx] = new_g

    subset_accept = np.mean(subset_accept_arr).item()
    num_fine_evals = num_chains * (num_states - 1)
    jump_distances = rms_jump_distances(all_x)
    mean_jump_distance = np.mean(jump_distances).item()
    outer_move_rate = np.mean(jump_distances > 0).item()

    return LevelSamplingResult(
        x=all_x,
        g=all_g,
        component_acceptance_rate=1.0,
        subset_acceptance_rate=subset_accept,
        mean_jump_distance=mean_jump_distance,
        jump_distances=jump_distances,
        outer_move_rate=outer_move_rate,
        num_fine_evals=num_fine_evals,
    )


def generate_next_level_samples_ACS(
    performance,
    num_chains,
    num_states,
    dimension,
    chain_seeds,
    chain_g,
    all_x,
    all_g,
    level_idx,
    master_seed,
    threshold,
    chains_per_update,
    transformation: Callable | None = None,
    prop_std=1.0,
    lambda_=1.0,
    debug: bool = False,
) -> ACSLevelSamplingResult:
    """Adaptive conditional sampling algorithm for generating states in the subset
    simulation level (aka adaptive subset infinity).

    Parameters
    ----------
    chains_per_update
        The number of Markov chains (as a fraction of the number of samples per level)
        that will run before lambda_ is updated. As an integer number, known as `Na`
        elsewhere.
    prop_std
        Initial variance of the proposal distribution.
    lambda_
        Initial scaling parameter.

    """

    A_STAR = 0.44

    num_chains_per_update = int(chains_per_update * num_chains)
    assert float(num_chains_per_update) == chains_per_update * num_chains

    num_batches = int(num_chains / num_chains_per_update)
    batch_avgs = []  # mean acceptance for each batch

    for batch_idx in range(num_batches):

        sigma = np.minimum(1, lambda_ * prop_std)
        rho = np.sqrt(1 - sigma**2)

        is_accept_arr = np.zeros((num_chains_per_update, num_states - 1)).astype(bool)
        for batch_chain_idx in range(num_chains_per_update):

            chain_index = batch_chain_idx + (batch_idx * num_chains_per_update)

            # proceed this Markov chain until all states have been generated
            all_x[chain_index, 0] = chain_seeds[chain_index]
            all_g[chain_index, 0] = chain_g[chain_index]

            chain_rng = None
            for state_idx in range(1, num_states):

                # RNG seed sequence for Markov chains:
                if state_idx == 1:
                    # spawn key to match the task ID in the matflow workflow
                    spawn_key = (4, level_idx, chain_index)
                    chain_rng = np.random.default_rng(
                        np.random.SeedSequence(master_seed, spawn_key=spawn_key)
                    )

                x = all_x[chain_index, state_idx - 1]
                g = all_g[chain_index, state_idx - 1]

                trial_x = norm.rvs(loc=x * rho, scale=sigma, random_state=chain_rng)
                trial_x_t = transformation(trial_x) if transformation else trial_x
                trial_g = performance(trial_x_t)

                current_x = x
                current_g = g

                is_accept = trial_g > threshold
                is_accept_arr[batch_chain_idx, state_idx - 1] = is_accept

                new_x = trial_x if is_accept else current_x
                new_g = trial_g if is_accept else current_g

                all_x[chain_index, state_idx] = new_x
                all_g[chain_index, state_idx] = new_g

        accept_batch_avg = np.mean(is_accept_arr)
        batch_avgs.append(accept_batch_avg)

        zeta = 1 / np.sqrt(batch_idx + 1)
        lambda_ *= np.exp(zeta * (accept_batch_avg - A_STAR))

    subset_accept = np.mean(batch_avgs).item()
    num_fine_evals = num_chains * (num_states - 1)

    jump_distances = rms_jump_distances(all_x)
    mean_jump_distance = np.mean(jump_distances).item()
    outer_move_rate = np.mean(jump_distances > 0).item()

    return ACSLevelSamplingResult(
        lambda_=lambda_,
        mcmc_acceptance_rate=1.0,
        subset_acceptance_rate=subset_accept,
        mean_jump_distance=mean_jump_distance,
        jump_distances=jump_distances,
        outer_move_rate=outer_move_rate,
        num_fine_evals=num_fine_evals,
    )


def weakest_link_coarse_gradient_xt(x_t, group_idx):
    """Analytic gradient of `weakest_link_performance_coarse` (i.e. of
    `max(block_average(x_t)) - y_star`) with respect to `x_t` (the *transformed*/
    physical-space input), for a single state vector `x_t` (1D, shape (dimension,)).

    The block-average-then-max function is piecewise linear: within the block that
    currently achieves the max, d(max)/d(x_t_i) = 1/block_size for every fine index i
    in that block (since averaging distributes the derivative equally across the
    block), and 0 for indices in any other block. Ties (multiple blocks achieving the
    same max) are broken by taking the first such block -- a measure-zero event for
    continuous inputs, so this doesn't affect correctness in practice.
    """
    x_t = np.asarray(x_t)
    x_avg = voxel_block_average(x_t, group_idx)
    max_block = np.argmax(x_avg)  # first occurrence on ties
    mask = group_idx == max_block
    block_size = mask.sum()
    grad = np.zeros_like(x_t, dtype=float)
    grad[mask] = 1.0 / block_size
    return grad


def cumsum_transformation_adjoint(grad_xt):
    """Adjoint (transpose-Jacobian action) for `transformation = lambda x:
    np.cumsum(x, axis=-1)`. Since cumsum is linear with Jacobian J_ij = 1 if j <= i
    else 0, J^T @ v is a *reversed* cumulative sum -- maps a gradient computed in the
    transformed ("physical") space back to the original (untransformed) sampling
    space. Required whenever a proposal/gradient-based correction is computed in
    transformed space but applied to untransformed states (as in
    `generate_next_level_samples_MLDA_gradient`/`_spsa`).
    """
    grad_xt = np.asarray(grad_xt)
    return np.cumsum(grad_xt[::-1])[::-1]


def log_surrogate_weight(g_coarse, threshold, temperature):
    """Note temperature should be of a similar order of magnitude to `g_coarse` and
    `threshold`."""
    z = (g_coarse - threshold) / temperature
    return log_expit(z)


def generate_coarse_subchain(
    x,
    gc,
    performance_coarse,
    proposal,
    log_surrogate_weight,
    threshold,
    temperature,
    transformation,
    num_inner_states,
    rng,
    chain_idx,
    debug=False,
):
    current_sub_chain_x = np.asarray(x).copy()
    current_sub_chain_gc = gc

    inner_accepts = 0
    mmh_component_acceptance_sum = 0.0

    debug_data = {}
    if debug:
        debug_data["current_sub_chain_x"] = []
        debug_data["trial_x"] = []
        debug_data["trial_gc"] = []
        debug_data["rng_states"] = []

    for _ in range(num_inner_states):

        if debug:
            debug_data["rng_states"].append(rng.bit_generator.state["state"])

        trial_x, mmh_component_acceptance = generate_next_state(
            x=current_sub_chain_x, proposal=proposal, rng=rng
        )
        mmh_component_acceptance_sum += mmh_component_acceptance

        if debug:
            debug_data["current_sub_chain_x"].append(current_sub_chain_x)
            debug_data["trial_x"].append(trial_x)

        if np.array_equal(trial_x, current_sub_chain_x):
            continue

        trial_x_t = transformation(trial_x) if transformation else trial_x
        trial_gc = performance_coarse(trial_x_t)

        if debug:
            debug_data["trial_gc"].append(trial_gc)

        log_s_current = log_surrogate_weight(current_sub_chain_gc, threshold, temperature)
        log_s_trial = log_surrogate_weight(trial_gc, threshold, temperature)
        log_alpha = min(0.0, log_s_trial - log_s_current)

        random_num = rng.random()
        is_accept = np.log(random_num) < log_alpha

        if is_accept:
            current_sub_chain_x = trial_x
            current_sub_chain_gc = trial_gc
            inner_accepts += 1

    return (
        current_sub_chain_x,
        current_sub_chain_gc,
        inner_accepts,
        mmh_component_acceptance_sum,
        debug_data,
    )


def generate_next_level_samples_DA(
    performance,
    performance_coarse,
    num_chains,
    num_states,
    dimension,
    chain_seeds,
    chain_g,
    all_x,
    all_g,
    level_idx,
    master_seed,
    threshold,
    proposal,
    log_surrogate_weight: Callable,
    transformation: Callable | None = None,
    temperature=1.0,
    num_inner_states: int = 1,
    spawn_key: tuple[int] | None = None,
    debug: bool = False,
) -> DALevelSamplingResult:
    """Fixed-length subchain surrogate transition for Subset Simulation.

    This is the randomised-length subchain surrogate transition (RST) algorithm but with a
    fixed length subchain. For num_inner_states=1, this should be identical to
    ``generate_next_level_samples_DA_single_inner``.

    Each outer transition:

        current x
            |
            v
        num_inner_states coarse-MH steps
            |
            v
        endpoint psi
            |
            v
        one fine evaluation (unless psi == x)
            |
            v
        fine correction
            |
            v
        new x

    The inner MH kernel targets the coarse surrogate

        pi_C(x) ∝ phi(x) * log_surrogate_weight(g_c(x)).

    The endpoint is then corrected to the fine target.
    """

    num_outer_trials = num_chains * (num_states - 1)

    # ------------------------------------------------------------
    # Per-outer-transition diagnostics
    # ------------------------------------------------------------

    # Fraction of inner coarse-MH proposals accepted.
    inner_accept_rate_arr = np.zeros((num_chains, num_states - 1), dtype=float)

    # Number of accepted coarse moves within each inner subchain.
    inner_accept_count_arr = np.zeros((num_chains, num_states - 1), dtype=int)

    # Whether the final endpoint differs from the outer current state.
    endpoint_move_arr = np.zeros((num_chains, num_states - 1), dtype=bool)

    # Whether the expensive fine model was evaluated.
    fine_eval_arr = np.zeros((num_chains, num_states - 1), dtype=bool)

    # Whether the endpoint passed the fine subset condition.
    fine_subset_pass_arr = np.zeros((num_chains, num_states - 1), dtype=bool)

    # Whether the final fine correction accepted the endpoint.
    fine_accept_arr = np.zeros((num_chains, num_states - 1), dtype=bool)

    # Whether the accepted endpoint is above the coarse threshold.
    endpoint_coarse_subset_pass_arr = np.zeros((num_chains, num_states - 1), dtype=bool)

    # Final coarse surrogate acceptance log probability.
    fine_log_alpha_arr = np.full((num_chains, num_states - 1), np.nan, dtype=float)

    # ------------------------------------------------------------
    # Store coarse performance at outer states
    # ------------------------------------------------------------

    all_gc = np.full((num_chains, num_states), np.nan, dtype=float)
    total_mmh_component_acceptance = 0.0

    debug_data = {}
    if debug:
        debug_data["chain_data"] = []

    for chain_index in range(num_chains):
        if debug:
            debug_data["chain_data"].append({"state_data": []})

        # --------------------------------------------------------
        # Initial state
        # --------------------------------------------------------

        seed_x = chain_seeds[chain_index]

        all_x[chain_index, 0] = seed_x
        all_g[chain_index, 0] = chain_g[chain_index]

        seed_x_t = transformation(seed_x) if transformation else seed_x

        seed_gc = performance_coarse(seed_x_t)
        all_gc[chain_index, 0] = seed_gc

        # --------------------------------------------------------
        # RNG for this chain
        # --------------------------------------------------------

        # `4` is usually the task insert ID of the generate_next_state task:
        spawn_key_ = tuple([*(spawn_key or (4,)), level_idx, chain_index])
        chain_rng = np.random.default_rng(
            np.random.SeedSequence(
                master_seed,
                spawn_key=spawn_key_,
            )
        )

        # --------------------------------------------------------
        # Generate outer states
        # --------------------------------------------------------

        for state_idx in range(1, num_states):

            if debug:
                debug_data["chain_data"][chain_index]["state_data"].append({})
                debug_dat_cs_ij = debug_data["chain_data"][chain_index]["state_data"][
                    state_idx - 1
                ]

            current_x = all_x[chain_index, state_idx - 1]
            current_g = all_g[chain_index, state_idx - 1]
            current_gc = all_gc[chain_index, state_idx - 1]

            # ----------------------------------------------------
            # Run the coarse subchain
            # ----------------------------------------------------

            (
                psi,
                psi_gc,
                n_inner_accepts,
                mmh_component_acceptance_sum,
                sub_chain_debug_data,
            ) = generate_coarse_subchain(
                x=current_x,
                gc=current_gc,
                performance_coarse=performance_coarse,
                proposal=proposal,
                log_surrogate_weight=log_surrogate_weight,
                threshold=threshold,
                temperature=temperature,
                transformation=transformation,
                num_inner_states=num_inner_states,
                rng=chain_rng,
                chain_idx=chain_index,
                debug=debug,
            )
            total_mmh_component_acceptance += mmh_component_acceptance_sum

            if debug:
                debug_dat_cs_ij["generate_coarse_subchain_data"] = sub_chain_debug_data
                debug_dat_cs_ij["psi"] = psi

            inner_accept_count_arr[chain_index, state_idx - 1] = n_inner_accepts

            inner_accept_rate_arr[chain_index, state_idx - 1] = (
                n_inner_accepts / num_inner_states if num_inner_states > 0 else np.nan
            )

            # ----------------------------------------------------
            # Did the coarse subchain actually move?
            # ----------------------------------------------------

            endpoint_moved = not np.array_equal(psi, current_x)

            endpoint_move_arr[chain_index, state_idx - 1] = endpoint_moved

            if not endpoint_moved:

                # The subchain ended where it started.
                # No fine evaluation is necessary.
                new_x = current_x
                new_g = current_g
                new_gc = current_gc

                if debug:
                    debug_dat_cs_ij["psi_g"] = None

            else:

                # ------------------------------------------------
                # Endpoint coarse diagnostics
                # ------------------------------------------------

                endpoint_coarse_subset_pass_arr[chain_index, state_idx - 1] = (
                    psi_gc > threshold
                )

                # ------------------------------------------------
                # Fine evaluation
                # ------------------------------------------------

                fine_eval_arr[chain_index, state_idx - 1] = True

                psi_t = transformation(psi) if transformation else psi

                psi_g = performance(psi_t)

                if debug:
                    debug_dat_cs_ij["psi_g"] = psi_g

                # ------------------------------------------------
                # Fine subset test
                # ------------------------------------------------

                fine_subset_pass = psi_g > threshold
                fine_subset_pass_arr[chain_index, state_idx - 1] = fine_subset_pass

                if not fine_subset_pass:

                    # The fine target is zero here.
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

                    log_s_current = log_surrogate_weight(
                        current_gc,
                        threshold,
                        temperature,
                    )

                    log_s_psi = log_surrogate_weight(
                        psi_gc,
                        threshold,
                        temperature,
                    )

                    log_alpha_fine = min(0.0, log_s_current - log_s_psi)
                    random_num = chain_rng.random()
                    fine_log_alpha_arr[chain_index, state_idx - 1] = log_alpha_fine
                    fine_accept = np.log(random_num) < log_alpha_fine

                    fine_accept_arr[chain_index, state_idx - 1] = fine_accept

                    if fine_accept:
                        new_x = psi
                        new_g = psi_g
                        new_gc = psi_gc
                    else:
                        new_x = current_x
                        new_g = current_g
                        new_gc = current_gc

            if debug:
                debug_dat_cs_ij["new_x"] = new_x
                debug_dat_cs_ij["new_g"] = new_g
                debug_dat_cs_ij["new_gc"] = new_gc

            # ----------------------------------------------------
            # Store outer state
            # ----------------------------------------------------

            all_x[chain_index, state_idx] = new_x
            all_g[chain_index, state_idx] = new_g
            all_gc[chain_index, state_idx] = new_gc

    # ============================================================
    # Aggregate diagnostics
    # ============================================================

    n_inner_proposals = num_chains * (num_states - 1) * num_inner_states

    n_inner_accepts = int(inner_accept_count_arr.sum())
    n_fine_evals = int(fine_eval_arr.sum())
    n_fine_subset_pass = int(fine_subset_pass_arr.sum())
    n_fine_accepts = int(fine_accept_arr.sum())
    n_endpoint_moves = int(endpoint_move_arr.sum())

    component_acceptance_rate = (
        total_mmh_component_acceptance / n_inner_proposals
        if n_inner_proposals > 0
        else np.nan
    ).item()

    coarse_acceptance_rate = (
        n_inner_accepts / n_inner_proposals if n_inner_proposals > 0 else np.nan
    )

    endpoint_move_rate = (
        n_endpoint_moves / num_outer_trials if num_outer_trials > 0 else np.nan
    )

    fine_eval_rate = n_fine_evals / num_outer_trials if num_outer_trials > 0 else np.nan

    # Of the endpoints actually evaluated with the fine model, how many satisfy the fine
    # subset condition?
    fine_subset_pass_rate = (
        n_fine_subset_pass / n_fine_evals if n_fine_evals > 0 else np.nan
    )

    # Of the endpoints in the fine subset, how many pass the final delayed-acceptance
    # correction?
    fine_correction_acceptance_rate = (
        n_fine_accepts / n_fine_subset_pass if n_fine_subset_pass > 0 else np.nan
    )

    # Fraction of outer transitions that actually change the stored state.
    outer_move_rate = (
        n_fine_accepts / num_outer_trials if num_outer_trials > 0 else np.nan
    )

    # Among endpoints in the fine subset, how many are also above the coarse threshold?
    coarse_given_fine = (
        np.sum(endpoint_coarse_subset_pass_arr & fine_subset_pass_arr)
        / n_fine_subset_pass
        if n_fine_subset_pass > 0
        else np.nan
    )

    jump_distances = rms_jump_distances(all_x)
    mean_jump_distance = np.mean(jump_distances).item()

    # One coarse evaluation for each chain seed plus one per# inner proposal.
    num_coarse_evals = num_chains + n_inner_proposals

    outer_move_rate_2 = np.mean(jump_distances > 0).item()
    assert outer_move_rate == outer_move_rate_2

    return DALevelSamplingResult(
        x=all_x,
        g=all_g,
        component_acceptance_rate=component_acceptance_rate,
        subset_acceptance_rate=fine_subset_pass_rate,
        mean_jump_distance=mean_jump_distance,
        num_fine_evals=n_fine_evals,
        num_coarse_evals=num_coarse_evals,
        jump_distances=jump_distances if debug else None,
        debug_data=debug_data if debug else None,
        coarse_acceptance_rate=coarse_acceptance_rate,
        endpoint_move_rate=endpoint_move_rate,
        fine_eval_rate=fine_eval_rate,
        fine_subset_pass_rate=fine_subset_pass_rate,
        fine_correction_acceptance_rate=fine_correction_acceptance_rate,
        outer_move_rate=outer_move_rate,
        coarse_given_fine=coarse_given_fine,
        all_gc=all_gc,
        coarse_acceptance_rates=(inner_accept_rate_arr if debug else None),
        coarse_acceptance_counts=(inner_accept_count_arr if debug else None),
        endpoint_moves=(endpoint_move_arr if debug else None),
        fine_evals=(fine_eval_arr if debug else None),
        fine_subset_passes=(fine_subset_pass_arr if debug else None),
        fine_correction_accepts=(fine_accept_arr if debug else None),
        fine_log_alpha=(fine_log_alpha_arr if debug else None),
        endpoint_coarse_subset_passes=(
            endpoint_coarse_subset_pass_arr if debug else None
        ),
    )


def generate_next_level_samples_DA_single_inner(
    performance,
    performance_coarse,
    num_chains,
    num_states,
    dimension,
    chain_seeds,
    chain_g,
    all_x,
    all_g,
    level_idx,
    master_seed,
    threshold,
    proposal,
    log_surrogate_weight: Callable,
    transformation: Callable | None = None,
    temperature=1.0,
    debug: bool = False,
):
    """Delayed-acceptance modified Metropolis algorithm for subset simulation.

    Set log_surrogate_weight to a constant callable to reproduce vanilla subset simulation.

    """

    stage1_accept_arr = np.zeros((num_chains, num_states - 1)).astype(bool)
    stage2_accept_arr = np.zeros((num_chains, num_states - 1)).astype(bool)
    fine_subset_pass_arr = np.zeros((num_chains, num_states - 1)).astype(bool)
    coarse_subset_pass_arr = np.zeros((num_chains, num_states - 1), dtype=bool)
    fine_all_arr = np.zeros((num_chains, num_states - 1), dtype=bool)

    all_gc = np.ones((num_chains, num_states)) * np.nan

    for chain_index in range(num_chains):

        # proceed this Markov chain until all states have been generated
        seed_x = chain_seeds[chain_index]
        all_x[chain_index, 0] = seed_x
        all_g[chain_index, 0] = chain_g[chain_index]

        seed_x_t = transformation(seed_x) if transformation else seed_x
        seed_gc = performance_coarse(seed_x_t)
        all_gc[chain_index, 0] = seed_gc

        chain_rng = None
        for state_idx in range(1, num_states):

            # RNG seed sequence for Markov chains:
            if state_idx == 1:
                # spawn key to match the task ID in the matflow workflow
                spawn_key = (4, level_idx, chain_index)
                chain_rng = np.random.default_rng(
                    np.random.SeedSequence(master_seed, spawn_key=spawn_key)
                )

            # current state
            current_x = all_x[chain_index, state_idx - 1]
            current_g = all_g[chain_index, state_idx - 1]
            current_gc = all_gc[chain_index, state_idx - 1]

            trial_x, mcmc_accept_rate = generate_next_state(
                x=current_x,
                proposal=proposal,
                rng=chain_rng,
            )

            trial_x_t = transformation(trial_x) if transformation else trial_x
            trial_gc = performance_coarse(trial_x_t)
            coarse_subset_pass = trial_gc > threshold

            # diagnostic only: evaluate the expensive model for every proposal:
            trial_g_diagnostic = performance(trial_x_t)
            fine_subset_pass_diagnostic = trial_g_diagnostic > threshold
            fine_all_arr[chain_index, state_idx - 1] = fine_subset_pass_diagnostic

            coarse_subset_pass_arr[chain_index, state_idx - 1] = coarse_subset_pass

            log_s_current = log_surrogate_weight(current_gc, threshold, temperature)
            log_s_trial = log_surrogate_weight(trial_gc, threshold, temperature)

            log_alpha1 = min(0.0, log_s_trial - log_s_current)
            stage1_accept = np.log(chain_rng.random()) < log_alpha1

            if not stage1_accept:

                # no fine evaluation
                new_x = current_x
                new_g = current_g
                new_gc = current_gc

                fine_subset_pass = False
                stage2_accept = False

            else:

                # stage 2: expensive model
                trial_g = performance(trial_x_t)
                fine_subset_pass = trial_g > threshold

                if not fine_subset_pass:
                    new_x = current_x
                    new_g = current_g
                    new_gc = current_gc
                    stage2_accept = False

                else:
                    log_alpha2 = min(0.0, log_s_current - log_s_trial)
                    stage2_accept = np.log(chain_rng.random()) < log_alpha2
                    if stage2_accept:
                        new_x = trial_x
                        new_g = trial_g
                        new_gc = trial_gc
                    else:
                        new_x = current_x
                        new_g = current_g
                        new_gc = current_gc

            all_x[chain_index, state_idx] = new_x
            all_g[chain_index, state_idx] = new_g
            all_gc[chain_index, state_idx] = new_gc

            stage1_accept_arr[chain_index, state_idx - 1] = stage1_accept
            stage2_accept_arr[chain_index, state_idx - 1] = stage2_accept
            fine_subset_pass_arr[chain_index, state_idx - 1] = fine_subset_pass

    coarse_accept = np.mean(stage1_accept_arr).item()
    mcmc_accept = np.mean(fine_subset_pass_arr).item()
    fine_eval_rate = np.mean(stage1_accept_arr).item()
    num_trials = num_chains * (num_states - 1)

    fine_pass = fine_all_arr
    coarse_pass = coarse_subset_pass_arr

    p_coarse = np.mean(coarse_pass)
    n_fine_pass = np.sum(fine_pass)
    n_both_pass = np.sum(fine_pass & coarse_pass)

    p_stage1_accept = np.mean(stage1_accept_arr).item()

    # probability the coarse model in failure domain, given the fine model is also in the
    # failure domain; if this is high, the coarse model is a good approximation
    p_coarse_given_fine = n_both_pass / n_fine_pass if n_fine_pass > 0 else np.nan

    return {
        "mcmc_accept": mcmc_accept,
        "coarse_accept_arr": stage1_accept_arr,
        "coarse_accept": coarse_accept,
        "fine_eval_rate": fine_eval_rate,
        "num_fine_evals": int(stage1_accept_arr.sum()),
        "num_coarse_evals": num_trials + num_chains,
        "p_coarse": p_coarse,
        "n_fine_pass": n_fine_pass,
        "n_both_pass": n_both_pass,
        "p_coarse_given_fine": p_coarse_given_fine,
        "p_stage1_accept": p_stage1_accept,
    }


def subset_simulation(
    performance,
    dimension=200,
    p_0=0.1,
    num_samples=100,
    num_levels=10,
    master_seed=None,
    sampling_method=generate_next_level_samples,
    sampling_method_kwargs=None,
    transformation: Callable | None = None,
    mimic_matflow: bool = False,
    debug: bool = False,
) -> SubsetSimulationResult:
    """Estimate failure probability using Subset Simulation.

    ``num_levels`` includes the initial direct-Monte-Carlo level. Therefore,
    ``num_levels=1`` performs direct Monte Carlo only and does not invoke
    ``sampling_method``.

    The ``level_idx`` passed to ``sampling_method`` identifies the transition
    from level ``level_idx`` to level ``level_idx + 1``.
    """

    if num_levels < 1:
        raise ValueError("num_levels must be at least 1")

    # ------------------------------------------------------------------
    # Level 0: direct Monte Carlo
    # ------------------------------------------------------------------

    x = sample_direct_MC(
        dimension,
        num_samples,
        seed=master_seed,
        spawn_key=(0,),
        mimic_matflow=mimic_matflow,
    )
    x_t = transformation(x) if transformation else x
    g = performance(x_t)

    x_original = x.copy() if debug else None

    sampling_method_kwargs = copy.deepcopy(sampling_method_kwargs or {})
    sampling_method_kwargs.setdefault("performance", performance)

    # ------------------------------------------------------------------
    # Simulation-level results
    # ------------------------------------------------------------------

    thresholds: list[float] = []
    level_covs: list[float] = []
    levels: list[LevelSamplingResult] = []
    num_failed_per_level: list[int] = []

    num_fine_evals_total = num_samples
    num_coarse_evals_total = 0

    debug_data = {"level_data": []} if debug else None

    chain_seeds = None
    chain_g = None
    all_x = None
    all_g = None

    pf = np.nan

    # ------------------------------------------------------------------
    # Analyse each available simulation level
    # ------------------------------------------------------------------

    for level_idx in range(num_levels):
        num_failed = int(np.sum(g > 0))
        num_failed_per_level.append(num_failed)

        num_chains = int(len(g) * p_0)
        num_states = int(num_samples / num_chains)

        g_unsorted = g.copy()

        # Sort with the points closest to failure first.
        sort_idx = np.argsort(g)[::-1]
        g = g[sort_idx]
        x = x[sort_idx, :]

        threshold = float((g[num_chains - 1] + g[num_chains]) / 2)
        thresholds.append(threshold)

        indicator = np.reshape(
            g_unsorted > np.minimum(threshold, 0),
            (num_chains, num_states),
        ).astype(int)

        level_pf = np.mean(indicator).item()

        chain_seeds = x[:num_chains]
        chain_g = g[:num_chains]

        pf = p_0**level_idx * num_failed / num_samples

        if level_idx == 0:
            level_cov = np.sqrt((1 - level_pf) / (num_samples * level_pf)).item()
        else:
            level_cov = estimate_cov(
                indicator,
                level_pf,
            ).item()

        level_covs.append(level_cov)

        if debug:
            debug_data["level_data"].append(
                {
                    "level_idx": level_idx,
                    "threshold": threshold,
                    "level_pf": level_pf,
                    "level_cov": level_cov,
                    "num_failed": num_failed,
                    "chain_seeds": chain_seeds,
                    "chain_g": chain_g,
                }
            )

        # --------------------------------------------------------------
        # The current level has reached the failure domain.
        # --------------------------------------------------------------

        if threshold > 0:
            cov = np.sqrt(np.sum(np.square(level_covs))).item()

            return SubsetSimulationResult(
                pf=pf,
                cov=cov,
                converged=True,
                thresholds=np.array(thresholds),
                level_covs=np.array(level_covs),
                levels=levels,
                num_fine_evals=num_fine_evals_total,
                num_coarse_evals=num_coarse_evals_total,
                num_failed_per_level=np.array(num_failed_per_level),
                x_original=x_original,
                final_chain_seeds=(chain_seeds if debug else None),
                final_chain_g=(chain_g if debug else None),
                final_all_x=(all_x if debug else None),
                final_all_g=(all_g if debug else None),
                debug_data=debug_data,
            )

        # --------------------------------------------------------------
        # No further level is permitted.
        #
        # In particular, num_levels == 1 reaches this point after
        # analysing only the direct-MC samples.
        # --------------------------------------------------------------

        if level_idx == num_levels - 1:
            break

        # --------------------------------------------------------------
        # Generate simulation level level_idx + 1.
        # --------------------------------------------------------------

        all_x = np.full(
            (num_chains, num_states, dimension),
            np.nan,
        )
        all_g = np.full(
            (num_chains, num_states),
            np.nan,
        )

        level_result = sampling_method(
            num_chains=num_chains,
            num_states=num_states,
            dimension=dimension,
            chain_seeds=chain_seeds,
            chain_g=chain_g,
            all_x=all_x,
            all_g=all_g,
            level_idx=level_idx,
            master_seed=master_seed,
            threshold=threshold,
            debug=debug,
            transformation=transformation,
            **sampling_method_kwargs,
        )

        if not isinstance(level_result, LevelSamplingResult):
            raise TypeError(
                "sampling_method must return a "
                "LevelSamplingResult instance; "
                f"got {type(level_result).__name__}"
            )

        levels.append(level_result)

        # Carry ACS adaptation state into the next transition.
        if isinstance(level_result, ACSLevelSamplingResult):
            sampling_method_kwargs["lambda_"] = level_result.lambda_

        num_fine_evals_total += level_result.num_fine_evals
        num_coarse_evals_total += level_result.num_coarse_evals

        if debug:
            debug_data["level_data"][level_idx][
                "sampling_method_data"
            ] = level_result.debug_data

        # Use the returned result as the authoritative sample state.
        all_x = level_result.x
        all_g = level_result.g

        x = level_result.x.reshape(
            num_samples,
            dimension,
        )
        g = level_result.g.reshape(num_samples)

    # ------------------------------------------------------------------
    # The maximum permitted number of levels was reached.
    # ------------------------------------------------------------------

    return SubsetSimulationResult(
        pf=pf,
        cov=None,
        converged=False,
        thresholds=np.array(thresholds),
        level_covs=np.array(level_covs),
        levels=levels,
        num_fine_evals=num_fine_evals_total,
        num_coarse_evals=num_coarse_evals_total,
        num_failed_per_level=np.array(num_failed_per_level),
        x_original=x_original,
        final_chain_seeds=(chain_seeds if debug else None),
        final_chain_g=(chain_g if debug else None),
        final_all_x=(all_x if debug else None),
        final_all_g=(all_g if debug else None),
        debug_data=debug_data,
    )


def get_stats(
    all_pf,
    all_cov,
    all_sus_acc=None,
    all_mcmc_acc=None,
    all_num_fine_evals=None,
    all_num_coarse_evals=None,
    all_false_coarse_rejection_rates=None,
):

    pf_mean = np.mean(all_pf).item()
    cov_empirical = np.std(all_pf) / pf_mean
    cov_estimate = np.mean(all_cov)
    cov_estimate_std = np.std(all_cov)

    stats = {
        "pf": all_pf,
        "cov": all_cov,
        "pf_mean": pf_mean,
        "cov_empirical": cov_empirical,
        "cov_estimate": cov_estimate,
        "cov_estimate_std": cov_estimate_std,
        "all_sus_accept": all_sus_acc,
        "all_mcmc_accept": all_mcmc_acc,
    }
    if all_num_fine_evals is not None:
        stats["all_num_fine_evals"] = all_num_fine_evals
        stats["num_fine_evals_mean"] = np.mean(all_num_fine_evals).item()

    if all_num_coarse_evals is not None:
        stats["all_num_coarse_evals"] = all_num_coarse_evals
        stats["num_coarse_evals_mean"] = np.mean(all_num_coarse_evals).item()

    if all_false_coarse_rejection_rates:
        stats["all_false_coarse_rejection_rates"] = all_false_coarse_rejection_rates
        stats["false_coarse_rejection_rate_mean"] = np.mean(
            all_false_coarse_rejection_rates
        ).item()
    return stats


def run_repeats(
    performance,
    num_samples,
    sampling_method,
    sampling_method_kwargs=None,
    num_repeats=100,
    dimension=200,
    p_0=0.1,
    num_levels=10,
    seed=None,
    mimic_matflow=False,
    max_retries=5,
    transformation: Callable | None = None,
):
    seeds = np.random.SeedSequence(seed).generate_state(num_repeats)
    all_pf = []
    all_cov = []
    all_sus_acc = []
    all_mcmc_acc = []
    all_num_fine_evals = []
    all_num_coarse_evals = []
    all_false_coarse_rejection_rates = []
    num_retries_total = 0
    for repeat_idx in range(num_repeats):
        pc = (100 * (repeat_idx + 1)) // num_repeats
        if pc % 1 == 0:
            print(
                f"\rrunning {num_repeats} repeats with N={num_samples}...{pc:3d}%", end=""
            )
        seed_i = seeds[repeat_idx]
        for attempt in range(max_retries):
            result = subset_simulation(
                performance=performance,
                dimension=dimension,
                p_0=p_0,
                num_samples=num_samples,
                num_levels=num_levels,
                sampling_method=sampling_method,
                sampling_method_kwargs=sampling_method_kwargs,
                master_seed=seed_i,
                transformation=transformation,
                mimic_matflow=mimic_matflow,
                debug=True,
            )
            if "cov" in result:
                break
            # rare stochastic failure to converge in `num_levels` levels -- retry this
            # repeat with a fresh seed instead of losing the whole run_repeats call.
            num_retries_total += 1
            seed_i = np.random.SeedSequence().generate_state(1)[0]
        else:
            raise RuntimeError(
                f"Failed to estimate pf in {num_levels} levels after {max_retries} "
                f"retries (repeat_idx={repeat_idx})."
            )
        all_pf.append(result["pf"])
        all_cov.append(result["cov"])
        all_sus_acc.append(result["subset_accepts"])
        all_mcmc_acc.append(result["mcmc_accepts"])
        all_num_fine_evals.append(result["num_fine_evals"])
        all_num_coarse_evals.append(result["num_coarse_evals"])

        # subset level zero only:
        if result["false_coarse_rejection_rates"]:
            all_false_coarse_rejection_rates.append(
                result["false_coarse_rejection_rates"][0]
            )

    print()
    if num_retries_total:
        print(
            f"(note: {num_retries_total} repeat(s) needed a retry due to "
            f"max-levels-exceeded failures)"
        )
    return get_stats(
        all_pf,
        all_cov,
        all_sus_acc,
        all_mcmc_acc,
        all_num_fine_evals,
        all_num_coarse_evals,
        all_false_coarse_rejection_rates,
    )


def dist_to_str(dist):
    """Return a string representation of a distribution."""
    args = ",".join(
        [str(i) for i in dist.args] + [f"{k}={v}" for k, v in dist.kwds.items()]
    )
    return f"{dist.dist.name}({args})"


def run_convergence(
    performance,
    converge_label: str,
    fixed_num: int,
    series: list[int],
    sampling_method: Callable,
    sampling_method_kwargs: dict,
    num_levels: int = 10,
    mimic_matflow: bool = False,
):
    """Run a convergence test on the toy model subset simulation, for either number of samples per level, N, or number of repeats, R.

    Parameters
    ----------
    converge_label
        Either "N" (num samples) or "R" (num repeats)
    fixed_num
        The size of the non-varying parameter (i.e. num_repeats if converge_label is "N")
    series
        List of integers corresponding to the `converge_label` quantity
    next_state
        The callable to use to generate the next state
    next_state_kwargs
        Keyword arguments to pass to the next state callable.
    """

    fixed_str = (
        f"{'R' if converge_label == 'N' else 'N'}{fixed_num}"  # e.g. N200 or R100 etc
    )
    direct_results = {
        "data": {},
        "sampling_method": sampling_method.__name__,
        "sampling_method_kwargs": sampling_method_kwargs,
        "converge_label": converge_label,
        "fixed_num": fixed_num,
        "series": series,
    }
    for num in series:
        run_kwargs_i = {
            "performance": performance,
            "sampling_method": sampling_method,
            "sampling_method_kwargs": sampling_method_kwargs,
            "mimic_matflow": mimic_matflow,
            "num_levels": num_levels,
        }
        if converge_label == "N":
            run_kwargs_i["num_samples"] = num
            run_kwargs_i["num_repeats"] = fixed_num
        elif converge_label == "R":
            run_kwargs_i["num_repeats"] = num
            run_kwargs_i["num_samples"] = fixed_num
        direct_results["data"][num] = run_repeats(**run_kwargs_i)

    if "proposal" in sampling_method_kwargs:
        kwargs_str = dist_to_str(sampling_method_kwargs["proposal"])
    else:
        kwargs_str = f"{sampling_method_kwargs['prop_std']:.2f}"

    if "chains_per_update" in sampling_method_kwargs:
        kwargs_str += f"_NaFrac{sampling_method_kwargs['chains_per_update']:.1f}"

    if "lambda_" in sampling_method_kwargs:
        kwargs_str += f"_lambda{sampling_method_kwargs['lambda_']:.2f}"

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    file_name = f"toy_model_runs_{converge_label}_converge_{fixed_str}_{sampling_method.__name__}_std{kwargs_str}_mimic{str(int(mimic_matflow))}_{timestamp}.pkl"
    with Path(file_name).open("wb") as fh:
        pickle.dump(direct_results, fh)

    return file_name


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


def plot_many_pf_num_samples_from_files(pkls, quantile_range=0.95, yscale="log"):
    results = {}
    for label, pkl in pkls.items():
        with Path(pkl).open("rb") as fh:
            results[label] = pickle.load(fh)
    plot_many_pf_num_samples(results, quantile_range=quantile_range, yscale=yscale)


def plot_many_pf_num_samples(
    all_results_dct,
    quantile_range,
    xlim=None,
    xscale="linear",
    ylim=None,
    yscale="linear",
    target_pf=1e-4,
):

    plt.figure(figsize=(5, 4))

    all_x = {k: [] for k in all_results_dct.keys()}
    all_y = {k: [] for k in all_results_dct.keys()}
    all_lower = {k: [] for k in all_results_dct.keys()}
    all_upper = {k: [] for k in all_results_dct.keys()}

    polys = []

    for idx, (label, all_results) in enumerate(all_results_dct.items()):

        if idx == 0:
            converge_label = all_results["converge_label"]
            fixed_num = all_results["fixed_num"]
            title = f"{'num_repeats' if converge_label == 'N' else 'num_samples'}={fixed_num!r}"
            xlabel = "Num samples, N" if converge_label == "N" else "Num repeats, R"
        else:
            assert all_results["converge_label"] == converge_label
            assert all_results["fixed_num"] == fixed_num

        all_data = all_results["data"]
        for N, data in all_data.items():
            pf_srt = sorted(data["pf"])
            _x0 = (1 - quantile_range) / 2
            _x1 = _x0 + quantile_range
            lower = np.quantile(pf_srt, _x0)
            upper = np.quantile(pf_srt, _x1)

            all_x[label].append(N)
            all_y[label].append(data["pf_mean"])
            all_lower[label].append(lower)
            all_upper[label].append(upper)

        polys.append(
            plt.fill_between(
                x=all_x[label],
                y1=all_lower[label],
                y2=all_upper[label],
                alpha=0.5,
                label=label,
            )
        )

    for idx, (label, all_results) in enumerate(all_results_dct.items()):
        all_data = all_results["data"]
        plt.scatter(
            x=all_x[label],
            y=all_y[label],
            marker="o",
            color=polys[idx].get_facecolor()[0],
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )

    plt.hlines(
        y=target_pf,
        xmin=min(all_data),
        xmax=max(all_data),
        color="gray",
        label="Target",
    )
    plt.xlabel(xlabel)
    plt.ylabel("Prob. of failure, pf")
    plt.title(title)
    plt.legend()
    if ylim:
        plt.ylim(ylim)
    if xlim:
        plt.xlim(xlim)
    plt.yscale(yscale)
    plt.xscale(xscale)


def plot_pf_num_samples(
    all_results, quantile_range, xlim=None, xscale="linear", ylim=None, yscale="linear"
):

    converge_label = all_results["converge_label"]
    fixed_num = all_results["fixed_num"]
    title = f"{'num_repeats' if converge_label == 'N' else 'num_samples'}={fixed_num!r}"
    xlabel = "Num samples, N" if converge_label == "N" else "Num repeats, R"

    all_x = []
    all_y = []
    all_lower = []
    all_upper = []

    all_data = all_results["data"]
    for N, data in all_data.items():

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
        y=1e-4, xmin=min(all_data), xmax=max(all_data), color="gray", label="Target"
    )
    plt.xlabel(xlabel)
    plt.ylabel("Prob. of failure, pf")
    plt.title(title)
    plt.legend()
    if ylim:
        plt.ylim(ylim)
    if xlim:
        plt.xlim(xlim)
    plt.yscale(yscale)
    plt.xscale(xscale)


def plot_cov_estimates(all_results, ylim=None, yscale="linear"):

    converge_label = all_results["converge_label"]
    fixed_num = all_results["fixed_num"]
    title = f"{'num_repeats' if converge_label == 'N' else 'num_samples'}={fixed_num!r}"
    xlabel = "Num samples, N" if converge_label == "N" else "Num repeats, R"

    all_x = []
    cov_empirical = []
    cov_estimated = []
    cov_estimated_std = []

    all_data = all_results["data"]
    for N, data in all_data.items():
        all_x.append(N)
        cov_empirical.append(data["cov_empirical"])
        cov_estimated.append(data["cov_estimate"])
        cov_estimated_std.append(data["cov_estimate_std"])

    plt.figure(figsize=(5, 4))
    plt.plot(all_x, cov_empirical, label="empirical CoV")
    plt.errorbar(x=all_x, y=cov_estimated, yerr=cov_estimated_std, label="estimated CoV")
    plt.xlabel(xlabel)
    plt.ylabel("CoV")
    plt.title(title)
    plt.legend()
    if ylim:
        plt.ylim(ylim)
    plt.yscale(yscale)


def plot_pf_dist(all_results, target_pf):
    all_data = all_results["data"]
    converge_label = all_results["converge_label"]
    fixed_num = all_results["fixed_num"]
    title = f"{'num_repeats' if converge_label == 'N' else 'num_samples'}={fixed_num!r}"

    fig, axs = plt.subplots(
        1, len(all_data), figsize=(len(all_data) * 2.5, 3), sharex=True, sharey=True
    )
    for idx, (N, data) in enumerate(all_data.items()):
        ax_t = f"Num samples, N={N}" if converge_label == "N" else f"Num repeats, R={N}"
        axs[idx].hist(np.log10(data["pf"]))
        axs[idx].set_title(ax_t)
        axs[idx].axvline(np.log10(target_pf), color="gray")

    # One label for the whole figure
    fig.supxlabel("log10(Prob. of failure)")
    fig.supylabel("Frequency")
    plt.title(title)
    plt.tight_layout()


def plot_cov_dist(all_results):
    all_data = all_results["data"]
    converge_label = all_results["converge_label"]
    fixed_num = all_results["fixed_num"]
    title = f"{'num_repeats' if converge_label == 'N' else 'num_samples'}={fixed_num!r}"
    fig, axs = plt.subplots(
        1, len(all_data), figsize=(len(all_data) * 2.5, 3), sharex=True, sharey=True
    )
    for idx, (N, data) in enumerate(all_data.items()):
        ax_t = f"Num samples, N={N}" if converge_label == "N" else f"Num repeats, R={N}"
        axs[idx].hist(data["cov"])
        axs[idx].set_title(ax_t)

    # One label for the whole figure
    fig.supxlabel("CoV")
    fig.supylabel("Frequency")
    plt.title(title)
    plt.tight_layout()
