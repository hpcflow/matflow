from __future__ import annotations
import os
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike

from matflow.param_classes.load import LoadCase, LoadStep


def generate_load_cases_random_exponential(
    num_load_cases: int,
    total_time: float | int,
    num_steps: int,
    num_increments: int = 1,
    conserve_volume: bool = True,
    seed: int | None | Literal["resource_value"] = "resource_value",
    max_tries: int | None = None,
    k_range: ArrayLike = (0, 0.1),
    delta_f_range: ArrayLike = (-0.1, 0.1),
) -> dict[str, list[LoadCase] | float]:
    """Sample component-wise monotonic exponential deformation-gradient paths.

    Each candidate follows ``F(t) = I + deltaF * (1 - exp(-k*t))``, with
    independent components sampled uniformly from ``k_range`` for ``k`` and
    ``delta_f_range`` for ``deltaF``. If requested, normalise each gradient to unit
    determinant before checking monotonicity of every component.

    The path includes the identity at time zero and ``num_steps`` subsequent
    samples. Each subsequent sample defines the target of a load step of duration
    ``total_time / num_steps``, with ``num_increments`` increments per step.

    Parameters
    ----------
    num_load_cases : int
        Number of accepted load cases to generate. Must be a positive integer.
    total_time : float | int
        Total simulation time for each load case. Must be positive and finite.
    num_steps : int
        Number of equally spaced load steps per load case. Must be a positive integer.
        Each step targets the deformation gradient at its end time.
    num_increments : int, optional
        Number of simulation increments within each load step. Must be a positive integer.
        By default, 1.
    conserve_volume : bool, optional
        Normalise each sampled deformation gradient to unit determinant before checking
        component-wise monotonicity. By default, True.
    seed : int | None, optional
        Seed for reproducible random sampling. By default, None.
    max_tries : int | None, optional
        Maximum total number of candidate paths sampled across all load cases, including
        accepted and rejected paths. Must be a positive integer if specified. By default,
        None, which uses ``100 * num_load_cases``. Raises RuntimeError if too few load
        cases are accepted within this limit.
    k_range : array-like, optional
        Finite (min, max) sampling bounds for every component of ``k``. Must be
        non-negative and ordered. By default, (0, 0.1).
    delta_f_range : array-like, optional
        Finite, ordered (min, max) sampling bounds for every component of ``deltaF``. By
        default, (-0.1, 0.1). Equal bounds fix the sampled value for either range.
        Candidates with non-positive or non-finite determinants are rejected.

    Returns
    -------
    dict
        ``load_case`` contains the accepted load cases. ``monotonicity`` is the fraction
        of attempted paths found to be monotonic (accepted cases divided by total
        attempts), between 0 and 1.
    """

    if seed == "resource_value":
        seed = int(os.environ["MATFLOW_RUN_RANDOM_SEED"])
    else:
        seed = seed
    rng = np.random.default_rng(seed)

    for name, value in (
        ("num_load_cases", num_load_cases),
        ("num_steps", num_steps),
        ("num_increments", num_increments),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer.")

    if not np.isfinite(total_time) or total_time <= 0:
        raise ValueError("total_time must be positive and finite.")

    if max_tries is None:
        max_tries = 100 * num_load_cases

    if isinstance(max_tries, bool) or not isinstance(max_tries, int) or max_tries < 1:
        raise ValueError("max_tries must be a positive integer.")

    ranges = {}
    for name, bounds in (("k_range", k_range), ("delta_f_range", delta_f_range)):
        err_msg = f"{name} must contain finite, ordered (min, max) bounds."
        try:
            bounds = np.asarray(bounds, dtype=float)
        except (TypeError, ValueError) as exc:
            raise ValueError(err_msg) from exc
        if (
            bounds.shape != (2,)
            or not np.all(np.isfinite(bounds))
            or bounds[0] > bounds[1]
        ):
            raise ValueError(err_msg)
        ranges[name] = bounds
    if ranges["k_range"][0] < 0:
        raise ValueError("k_range bounds must be non-negative.")

    times = np.linspace(0, total_time, num_steps + 1)
    load_cases: list[LoadCase] = []
    for num_tries in range(1, max_tries + 1):

        k = rng.uniform(*ranges["k_range"], size=(3, 3))
        delta_f = rng.uniform(*ranges["delta_f_range"], size=(3, 3))
        gradients = np.eye(3) + delta_f * (
            1 - np.exp(-k * times[:, np.newaxis, np.newaxis])
        )
        determinants = np.linalg.det(gradients)

        if not np.all(np.isfinite(determinants) & (determinants > 0)):
            continue

        if conserve_volume:
            gradients /= np.cbrt(determinants)[:, np.newaxis, np.newaxis]

        # check each component always increasing or always decreasing:
        differences = np.diff(gradients, axis=0)
        if not np.all(
            np.all(differences <= 0, axis=0) | np.all(differences >= 0, axis=0)
        ):
            continue

        load_cases.append(
            LoadCase(
                steps=[
                    LoadStep(
                        total_time=total_time / num_steps,
                        num_increments=num_increments,
                        target_def_grad=np.ma.masked_array(gradient, mask=False),
                        stress=np.ma.masked_array(np.zeros((3, 3)), mask=True),
                    )
                    for gradient in gradients[1:]
                ]
            )
        )
        if len(load_cases) == num_load_cases:
            monotonicity = len(load_cases) / num_tries
            print(
                f"Generated {len(load_cases)} load cases; monotonicity rate was: "
                f"{monotonicity}."
            )
            return {
                "load_case": load_cases,
                "monotonicity": monotonicity,
            }

    raise RuntimeError(
        "Could not sample enough monotonic load cases within " f"{max_tries} attempts."
    )
