from dataclasses import dataclass, fields, is_dataclass
from typing import Any
import numpy as np
from numpy.typing import NDArray


def rms_jump_distances(all_x: np.ndarray) -> np.ndarray:
    """RMS jump distance between consecutive stored chain states."""
    dx = np.diff(all_x, axis=1)
    return np.linalg.norm(dx, axis=-1) / np.sqrt(dx.shape[-1])


@dataclass
class LevelSamplingResult:
    """Result of generating one conditional Subset Simulation level."""

    #: Sampled states.
    x: np.ndarray

    #: Performance function evaluations associated with each of the sampled states.
    g: np.ndarray

    #: Average component acceptance rate from Modified Metropolis Hastings, inclusive of
    #: proposals that subsequently fail the subset condition.
    component_acceptance_rate: float

    #: Fraction of stored outer-chain transitions that change state.
    outer_move_rate: float

    #: Fraction of candidate states that pass the fine-model subset condition.
    subset_acceptance_rate: float

    #: Average distance between adjacent states in the outer chain (a subset rejection
    #: produces a zero jump distance).
    mean_jump_distance: float

    #: Number of (fine) evaluations.
    num_fine_evals: int

    #: Number of coarse evaluations, if any were performed.
    num_coarse_evals: int = 0

    # optional detailed diagnostics.
    jump_distances: np.ndarray | None = None
    debug_data: dict[str, Any] | None = None


@dataclass
class ACSLevelSamplingResult(LevelSamplingResult):
    lambda_: float = 1.0


@dataclass
class DALevelSamplingResult(LevelSamplingResult):
    """Result of generating one delayed-acceptance conditional level."""

    #: Fraction of individual coarse-MH proposals accepted by the
    #: coarse surrogate target.
    coarse_acceptance_rate: float = np.nan

    #: Fraction of outer transitions for which the coarse subchain endpoint
    #: differs from the current outer-chain state.
    endpoint_move_rate: float = np.nan

    #: Fraction of outer transitions requiring a fine-model evaluation.
    fine_eval_rate: float = np.nan

    #: Fraction of fine-evaluated candidate endpoints that pass the
    #: fine-model subset condition.
    fine_subset_pass_rate: float = np.nan

    #: Fraction of candidate endpoints that pass the fine subset condition
    #: and are subsequently accepted by the final DA correction.
    fine_correction_acceptance_rate: float = np.nan

    #: Among endpoints in the fine subset, fraction that are also above the
    #: coarse threshold.
    coarse_given_fine: float = np.nan

    #: Coarse performance-function values associated with the stored
    #: outer-chain states.
    all_gc: np.ndarray | None = None

    # Optional detailed diagnostics.
    coarse_acceptance_rates: np.ndarray | None = None
    coarse_acceptance_counts: np.ndarray | None = None
    endpoint_moves: np.ndarray | None = None
    fine_evals: np.ndarray | None = None
    fine_subset_passes: np.ndarray | None = None
    fine_correction_accepts: np.ndarray | None = None
    fine_log_alpha: np.ndarray | None = None
    endpoint_coarse_subset_passes: np.ndarray | None = None


@dataclass(repr=False)
class SubsetSimulationResult:
    pf: float
    cov: float | None
    converged: bool

    thresholds: NDArray
    level_covs: NDArray
    levels: list[LevelSamplingResult]

    num_fine_evals: int
    num_coarse_evals: int
    num_failed_per_level: NDArray

    # Debugging/state data omitted from repr.
    x_original: NDArray | None = None
    final_chain_seeds: NDArray | None = None
    final_chain_g: NDArray | None = None
    final_all_x: NDArray | None = None
    final_all_g: NDArray | None = None
    debug_data: dict[str, Any] | None = None

    @property
    def component_acceptance_rates(self) -> NDArray:
        return np.array([level.component_acceptance_rate for level in self.levels])

    @property
    def subset_acceptance_rates(self) -> NDArray:
        return np.array([level.subset_acceptance_rate for level in self.levels])

    @property
    def mean_jump_distances(self) -> NDArray:
        return np.array([level.mean_jump_distance for level in self.levels])

    @property
    def outer_move_rates(self) -> NDArray:
        return np.array([level.outer_move_rate for level in self.levels])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SubsetSimulationResult):
            return NotImplemented

        if type(self) is not type(other):
            return False

        return all(
            _values_equal(
                getattr(self, field.name),
                getattr(other, field.name),
            )
            for field in fields(self)
        )

    def __repr__(self) -> str:
        cls_name = type(self).__name__
        cov_str = f"{self.cov:.4f}" if self.cov is not None else "None"
        return (
            f"{cls_name}(\n"
            f"    pf={self.pf:.4e},\n"
            f"    cov={cov_str},\n"
            f"    converged={self.converged!r},\n"
            f"    thresholds={self.thresholds!r},\n"
            f"    level_covs={self.level_covs!r},\n"
            f"    num_conditional_levels={len(self.levels)},\n"
            f"    component_acceptance_rates={self.component_acceptance_rates!r},\n"
            f"    subset_acceptance_rates={self.subset_acceptance_rates!r},\n"
            f"    outer_move_rates={self.outer_move_rates!r},\n"
            f"    mean_jump_distances={self.mean_jump_distances!r},\n"
            f"    num_fine_evals={self.num_fine_evals!r},\n"
            f"    num_coarse_evals={self.num_coarse_evals!r},\n"
            f"    num_failed_per_level={self.num_failed_per_level!r},\n"
            f")"
        )


def _values_equal(left: Any, right: Any) -> bool:
    """Compare nested result data, including NumPy arrays and NaNs."""

    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        if not (isinstance(left, np.ndarray) and isinstance(right, np.ndarray)):
            return False

        return np.array_equal(
            left,
            right,
            equal_nan=True,
        )

    if is_dataclass(left) or is_dataclass(right):
        if not (is_dataclass(left) and is_dataclass(right) and type(left) is type(right)):
            return False

        return all(
            _values_equal(
                getattr(left, field.name),
                getattr(right, field.name),
            )
            for field in fields(left)
        )

    if isinstance(left, dict) or isinstance(right, dict):
        if not (
            isinstance(left, dict)
            and isinstance(right, dict)
            and left.keys() == right.keys()
        ):
            return False

        return all(_values_equal(left[key], right[key]) for key in left)

    if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        if type(left) is not type(right) or len(left) != len(right):
            return False

        return all(_values_equal(a, b) for a, b in zip(left, right))

    # Treat NaN diagnostics as equal.
    if (
        isinstance(left, (float, np.floating))
        and isinstance(right, (float, np.floating))
        and np.isnan(left)
        and np.isnan(right)
    ):
        return True

    return bool(left == right)
