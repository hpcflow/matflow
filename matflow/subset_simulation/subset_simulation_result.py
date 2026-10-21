from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Any, ClassVar, TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray
from hpcflow.sdk.core.parameters import ParameterValue

from matflow.tests.utils import _values_equal

if TYPE_CHECKING:
    from matflow.subset_simulation.subset_simulation import MarkovChainResult


from dataclasses import dataclass
from functools import cached_property
from typing import Any

import numpy as np


@dataclass(repr=False)
class LevelSamplingResult:
    """Result of generating one conditional Subset Simulation level."""

    #: Results for the individual Markov chains used to generate this level.
    chains: tuple[MarkovChainResult, ...]

    #: Optional algorithm-specific debugging information.
    debug_data: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.chains:
            raise ValueError("LevelSamplingResult requires at least one chain.")

    @cached_property
    def x(self) -> np.ndarray:
        """Sampled states, arranged as ``(chains, states, dimensions)``."""
        return np.stack([chain.x for chain in self.chains], axis=0)

    @cached_property
    def g(self) -> np.ndarray:
        """Fine performance values associated with the sampled states."""
        return np.stack([chain.g for chain in self.chains], axis=0)

    @property
    def num_chains(self) -> int:
        """Number of Markov chains used to generate the level."""
        return len(self.chains)

    @property
    def num_states(self) -> int:
        """Total number of stored states across all chains."""
        return sum(chain.num_states for chain in self.chains)

    @property
    def num_transitions(self) -> int:
        """Total number of attempted outer-chain transitions."""
        return sum(chain.num_transitions for chain in self.chains)

    @property
    def num_components_accepted(self) -> int:
        """Total number of MMH component proposals accepted."""
        return sum(chain.num_components_accepted for chain in self.chains)

    @property
    def num_components_proposed(self) -> int:
        """Total number of MMH component proposals attempted."""
        return sum(chain.num_components_proposed for chain in self.chains)

    @property
    def component_acceptance_rate(self) -> float:
        """Return the aggregate MMH component acceptance rate.

        The rate includes MMH component proposals belonging to candidate
        states that subsequently fail the Subset Simulation condition.
        """
        if self.num_components_proposed == 0:
            return np.nan
        return self.num_components_accepted / self.num_components_proposed

    @property
    def num_subset_accepts(self) -> int:
        """Total number of candidates passing the fine subset condition."""
        return sum(chain.num_subset_accepts for chain in self.chains)

    @property
    def num_subset_trials(self) -> int:
        """Total number of candidates tested against the fine subset condition."""
        return sum(chain.num_subset_trials for chain in self.chains)

    @property
    def subset_acceptance_rate(self) -> float:
        """Return the fraction of candidates passing the fine subset condition."""
        if self.num_subset_trials == 0:
            return np.nan
        return self.num_subset_accepts / self.num_subset_trials

    @property
    def num_outer_moves(self) -> int:
        """Total number of stored outer-chain transitions that change state."""
        return sum(chain.num_outer_moves for chain in self.chains)

    @property
    def outer_move_rate(self) -> float:
        """Return the fraction of stored outer-chain transitions that move."""
        if self.num_transitions == 0:
            return np.nan
        return self.num_outer_moves / self.num_transitions

    @property
    def jump_distance_sum(self) -> float:
        """Sum of RMS jump distances over all outer-chain transitions."""
        return sum(chain.jump_distance_sum for chain in self.chains)

    @property
    def mean_jump_distance(self) -> float:
        """Return the mean RMS distance between adjacent stored states.

        Rejected outer transitions contribute a zero jump distance.
        """
        if self.num_transitions == 0:
            return np.nan
        return self.jump_distance_sum / self.num_transitions

    @cached_property
    def jump_distances(self) -> np.ndarray | None:
        """Return per-transition RMS jump distances, if retained.

        The resulting array has shape ``(chains, transitions)``. The value is
        ``None`` if detailed jump distances were not retained for every chain.
        """
        if any(chain.jump_distances is None for chain in self.chains):
            return None
        return np.stack([chain.jump_distances for chain in self.chains], axis=0)

    @property
    def num_fine_evals(self) -> int:
        """Total number of fine performance-function evaluations."""
        return sum(chain.num_fine_evals for chain in self.chains)

    @property
    def num_coarse_evals(self) -> int:
        """Total number of coarse performance-function evaluations."""
        return sum(chain.num_coarse_evals for chain in self.chains)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(\n"
            f"    num_chains={self.num_chains},\n"
            f"    num_states={self.num_states},\n"
            f"    num_transitions={self.num_transitions},\n"
            f"    component_acceptance_rate={self.component_acceptance_rate!r},\n"
            f"    subset_acceptance_rate={self.subset_acceptance_rate!r},\n"
            f"    outer_move_rate={self.outer_move_rate!r},\n"
            f"    mean_jump_distance={self.mean_jump_distance!r},\n"
            f"    num_fine_evals={self.num_fine_evals},\n"
            f"    num_coarse_evals={self.num_coarse_evals},\n"
            f")"
        )


@dataclass(repr=False)
class ACSLevelSamplingResult(LevelSamplingResult):
    """Result of one adaptive conditional sampling level."""

    #: Updated proposal scaling parameter.
    lambda_: float = 1.0


@dataclass(repr=False)
class DALevelSamplingResult(LevelSamplingResult):
    """Result of one delayed-acceptance conditional level."""

    @property
    def coarse_acceptance_rate(self) -> float:
        """Fraction of all inner coarse-MH proposals accepted."""
        proposed = sum(chain.num_coarse_proposals for chain in self.chains)
        if proposed == 0:
            return np.nan

        return sum(chain.num_coarse_accepts for chain in self.chains) / proposed

    @property
    def endpoint_move_rate(self) -> float:
        """Fraction of coarse subchains whose endpoints moved."""
        if self.num_transitions == 0:
            return np.nan

        return (
            sum(chain.num_endpoint_moves for chain in self.chains) / self.num_transitions
        )

    @property
    def fine_eval_rate(self) -> float:
        """Fraction of outer transitions requiring fine evaluation."""
        if self.num_transitions == 0:
            return np.nan

        return self.num_fine_evals / self.num_transitions

    @property
    def fine_subset_pass_rate(self) -> float:
        """Fraction of fine-evaluated endpoints in the fine subset."""
        if self.num_fine_evals == 0:
            return np.nan

        return (
            sum(chain.num_fine_subset_passes for chain in self.chains)
            / self.num_fine_evals
        )

    @property
    def fine_correction_acceptance_rate(self) -> float:
        """Fraction of fine-subset endpoints accepted by correction."""
        num_subset_passes = sum(chain.num_fine_subset_passes for chain in self.chains)
        if num_subset_passes == 0:
            return np.nan

        return (
            sum(chain.num_fine_correction_accepts for chain in self.chains)
            / num_subset_passes
        )

    @property
    def coarse_given_fine(self) -> float:
        """Fraction of fine-subset endpoints also in the coarse subset."""
        num_subset_passes = sum(chain.num_fine_subset_passes for chain in self.chains)
        if num_subset_passes == 0:
            return np.nan

        return (
            sum(chain.num_coarse_and_fine_subset_passes for chain in self.chains)
            / num_subset_passes
        )

    @cached_property
    def gc(self) -> np.ndarray:
        """Stored coarse values with shape ``(chains, states)``."""
        return np.stack(
            [chain.gc for chain in self.chains],
            axis=0,
        )


@dataclass(repr=False)
class SubsetSimulationResult(ParameterValue):

    _typ: ClassVar[str] = "subset_simulation_result"

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

    @property
    def num_conditional_levels(self) -> int:
        return len(self.levels)

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
            f"    num_conditional_levels={self.num_conditional_levels},\n"
            f"    component_acceptance_rates={self.component_acceptance_rates!r},\n"
            f"    subset_acceptance_rates={self.subset_acceptance_rates!r},\n"
            f"    outer_move_rates={self.outer_move_rates!r},\n"
            f"    mean_jump_distances={self.mean_jump_distances!r},\n"
            f"    num_fine_evals={self.num_fine_evals!r},\n"
            f"    num_coarse_evals={self.num_coarse_evals!r},\n"
            f"    num_failed_per_level={self.num_failed_per_level!r},\n"
            f")"
        )
