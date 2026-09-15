from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np

from matflow.tests.utils import _values_equal


def rms_jump_distances(all_x: np.ndarray) -> np.ndarray:
    """RMS jump distance between consecutive stored chain states."""
    dx = np.diff(all_x, axis=1)
    return np.linalg.norm(dx, axis=-1) / np.sqrt(dx.shape[-1])


@dataclass
class _ChainAccumulator:
    """Mutable internal storage used while generating one chain."""

    x: np.ndarray
    g: np.ndarray
    next_state_idx: int = 1

    num_components_accepted: int = 0
    num_components_proposed: int = 0

    num_subset_trials: int = 0
    num_subset_accepts: int = 0
    num_outer_moves: int = 0

    jump_distance_sum: float = 0.0
    num_fine_evals: int = 0
    num_coarse_evals: int = 0

    @property
    def current_x(self) -> np.ndarray:
        """Most recently stored chain state."""
        return self.x[self.next_state_idx - 1]

    @property
    def current_g(self) -> float:
        """Fine performance value of the current state."""
        return float(self.g[self.next_state_idx - 1])

    @property
    def is_complete(self) -> bool:
        """Whether the target number of states has been generated."""
        return self.next_state_idx == self.x.shape[0]

    @property
    def num_transitions(self) -> int:
        """Number of outer-chain transitions generated so far."""
        return self.next_state_idx - 1

    def append_transition(
        self,
        trial_x: np.ndarray,
        trial_g: float,
        threshold: float,
        *,
        num_components_accepted: int = 0,
        num_components_proposed: int = 0,
        fine_evaluated: bool = True,
    ) -> None:
        """Apply and store one proposed transition."""

        if self.is_complete:
            raise ValueError("Cannot append to a completed chain.")

        current_x = self.current_x
        current_g = self.current_g

        subset_accepted = trial_g > threshold

        if subset_accepted:
            new_x = trial_x
            new_g = trial_g
        else:
            new_x = current_x
            new_g = current_g

        outer_moved = not np.array_equal(new_x, current_x)

        jump_distance = np.linalg.norm(new_x - current_x) / np.sqrt(current_x.size)

        self.x[self.next_state_idx] = new_x
        self.g[self.next_state_idx] = new_g
        self.next_state_idx += 1

        self.num_components_accepted += num_components_accepted
        self.num_components_proposed += num_components_proposed
        self.num_subset_accepts += int(subset_accepted)
        self.num_subset_trials += 1
        self.num_outer_moves += int(outer_moved)
        self.jump_distance_sum += jump_distance
        self.num_fine_evals += int(fine_evaluated)

    def finalise(self, *, retain_jump_distances: bool = True) -> MarkovChainResult:
        """Create a result from the completed chain."""

        if not self.is_complete:
            raise RuntimeError("Cannot finalise an incomplete chain.")

        jump_distances = rms_jump_distances(self.x[np.newaxis, ...])[0]

        return MarkovChainResult(
            x=self.x,
            g=self.g,
            num_components_accepted=(self.num_components_accepted),
            num_components_proposed=(self.num_components_proposed),
            num_subset_accepts=(self.num_subset_accepts),
            num_subset_trials=self.num_transitions,
            num_outer_moves=self.num_outer_moves,
            jump_distance_sum=self.jump_distance_sum,
            num_fine_evals=self.num_fine_evals,
            num_coarse_evals=self.num_coarse_evals,
            jump_distances=(jump_distances if retain_jump_distances else None),
        )


@dataclass
class _DAChainAccumulator(_ChainAccumulator):
    """Mutable internal storage for one delayed-acceptance chain."""

    gc: np.ndarray | None = None

    num_coarse_accepts: int = 0
    num_coarse_proposals: int = 0
    num_endpoint_moves: int = 0
    num_fine_subset_passes: int = 0
    num_fine_correction_accepts: int = 0
    num_coarse_and_fine_subset_passes: int = 0

    def append_DA_transition(
        self,
        *,
        new_x,
        new_g,
        new_gc,
        num_components_accepted,
        num_components_proposed,
        num_coarse_accepts,
        num_coarse_proposals,
        endpoint_moved,
        fine_evaluated,
        fine_subset_pass,
        fine_correction_accept,
        coarse_subset_pass,
    ) -> None:
        """Store one completed delayed-acceptance transition."""

        if self.is_complete:
            raise ValueError("Cannot append to a completed chain.")

        current_x = self.current_x

        outer_moved = not np.array_equal(
            new_x,
            current_x,
        )
        jump_distance = np.linalg.norm(new_x - current_x) / np.sqrt(current_x.size)

        self.x[self.next_state_idx] = new_x
        self.g[self.next_state_idx] = new_g
        self.gc[self.next_state_idx] = new_gc
        self.next_state_idx += 1

        self.num_components_accepted += num_components_accepted
        self.num_components_proposed += num_components_proposed

        self.num_subset_accepts += int(fine_subset_pass)
        self.num_subset_trials += int(fine_evaluated)
        self.num_outer_moves += int(outer_moved)
        self.jump_distance_sum += jump_distance

        self.num_fine_evals += int(fine_evaluated)
        self.num_coarse_evals += num_coarse_proposals
        self.num_coarse_accepts += num_coarse_accepts
        self.num_coarse_proposals += num_coarse_proposals
        self.num_endpoint_moves += int(endpoint_moved)
        self.num_fine_subset_passes += int(fine_subset_pass)
        self.num_fine_correction_accepts += int(fine_correction_accept)
        self.num_coarse_and_fine_subset_passes += int(
            coarse_subset_pass and fine_subset_pass
        )

    def finalise(
        self,
        *,
        retain_jump_distances=True,
    ) -> DAMarkovChainResult:
        """Create a result from a completed DA chain."""

        if not self.is_complete:
            raise RuntimeError("Cannot finalise an incomplete chain.")

        jump_distances = rms_jump_distances(self.x[np.newaxis, ...])[0]

        return DAMarkovChainResult(
            x=self.x,
            g=self.g,
            gc=self.gc,
            num_components_accepted=(self.num_components_accepted),
            num_components_proposed=(self.num_components_proposed),
            num_subset_accepts=(self.num_subset_accepts),
            num_subset_trials=self.num_subset_trials,
            num_outer_moves=self.num_outer_moves,
            jump_distance_sum=self.jump_distance_sum,
            num_fine_evals=self.num_fine_evals,
            num_coarse_evals=self.num_coarse_evals,
            num_coarse_accepts=self.num_coarse_accepts,
            num_coarse_proposals=(self.num_coarse_proposals),
            num_endpoint_moves=self.num_endpoint_moves,
            num_fine_subset_passes=(self.num_fine_subset_passes),
            num_fine_correction_accepts=(self.num_fine_correction_accepts),
            num_coarse_and_fine_subset_passes=(self.num_coarse_and_fine_subset_passes),
            jump_distances=(jump_distances if retain_jump_distances else None),
        )


@dataclass(eq=False, repr=False)
class MarkovChainResult:
    """Result of generating one completed conditional Markov chain."""

    #: Stored chain states, with shape ``(states, dimensions)``.
    x: np.ndarray

    #: Fine performance values associated with the stored states.
    g: np.ndarray

    #: Total number of accepted MMH component proposals.
    num_components_accepted: int

    #: Total number of attempted MMH component proposals.
    num_components_proposed: int

    #: Number of candidates passing the fine-model subset condition.
    num_subset_accepts: int

    #: Number of candidates tested against the fine-model subset condition.
    num_subset_trials: int

    #: Number of stored outer-chain transitions that change state.
    num_outer_moves: int

    #: Sum of RMS distances between adjacent stored chain states.
    jump_distance_sum: float

    #: Number of fine performance-function evaluations.
    num_fine_evals: int

    #: Number of coarse performance-function evaluations.
    num_coarse_evals: int = 0

    #: Per-transition RMS jump distances, if retained.
    jump_distances: np.ndarray | None = None

    def __post_init__(self) -> None:
        if self.x.ndim != 2:
            raise ValueError(
                "x must have shape (states, dimensions); " f"got shape {self.x.shape}."
            )

        if self.g.ndim != 1:
            raise ValueError("g must have shape (states,); " f"got shape {self.g.shape}.")

        if self.x.shape[0] != self.g.shape[0]:
            raise ValueError(
                "x and g must contain the same number of states; "
                f"got {self.x.shape[0]} and {self.g.shape[0]}."
            )

        if self.jump_distances is not None and self.jump_distances.shape != (
            self.num_transitions,
        ):
            raise ValueError(
                "jump_distances must have shape "
                f"({self.num_transitions},); got "
                f"{self.jump_distances.shape}."
            )

    @property
    def num_states(self) -> int:
        """Number of stored states, including the initial chain seed."""
        return self.x.shape[0]

    @property
    def dimension(self) -> int:
        """Dimension of each Markov-chain state."""
        return self.x.shape[1]

    @property
    def num_transitions(self) -> int:
        """Number of attempted outer-chain transitions."""
        return max(self.num_states - 1, 0)

    @property
    def component_acceptance_rate(self) -> float:
        """Return the average MMH component acceptance rate.

        The rate includes component proposals belonging to candidate states
        that subsequently fail the Subset Simulation condition.
        """
        if self.num_components_proposed == 0:
            return np.nan

        return self.num_components_accepted / self.num_components_proposed

    @property
    def subset_acceptance_rate(self) -> float:
        """Return the fraction of candidates passing the fine subset condition."""
        if self.num_subset_trials == 0:
            return np.nan

        return self.num_subset_accepts / self.num_subset_trials

    @property
    def outer_move_rate(self) -> float:
        """Return the fraction of stored outer transitions that change state."""
        if self.num_transitions == 0:
            return np.nan

        return self.num_outer_moves / self.num_transitions

    @property
    def mean_jump_distance(self) -> float:
        """Return the mean RMS distance between adjacent stored states.

        Rejected outer transitions contribute a zero jump distance.
        """
        if self.num_transitions == 0:
            return np.nan

        return self.jump_distance_sum / self.num_transitions

    def __eq__(self, other: object) -> bool:
        """Compare chain results, including their NumPy arrays."""
        if not isinstance(other, MarkovChainResult):
            return NotImplemented

        if type(self) is not type(other):
            return False

        return all(
            _values_equal(getattr(self, field.name), getattr(other, field.name))
            for field in fields(self)
        )

    def __repr__(self) -> str:
        """Return a compact representation that omits stored arrays."""
        return (
            f"{type(self).__name__}(\n"
            f"    num_states={self.num_states},\n"
            f"    dimension={self.dimension},\n"
            f"    num_transitions={self.num_transitions},\n"
            f"    component_acceptance_rate={self.component_acceptance_rate!r},\n"
            f"    subset_acceptance_rate={self.subset_acceptance_rate!r},\n"
            f"    outer_move_rate={self.outer_move_rate!r},\n"
            f"    mean_jump_distance={self.mean_jump_distance!r},\n"
            f"    num_fine_evals={self.num_fine_evals},\n"
            f"    num_coarse_evals={self.num_coarse_evals},\n"
            f")"
        )


@dataclass(eq=False, repr=False)
class DAMarkovChainResult(MarkovChainResult):
    """Result of generating one delayed-acceptance Markov chain."""

    gc: np.ndarray | None = None

    num_coarse_accepts: int = 0
    num_coarse_proposals: int = 0
    num_endpoint_moves: int = 0
    num_fine_subset_passes: int = 0
    num_fine_correction_accepts: int = 0
    num_coarse_and_fine_subset_passes: int = 0

    @property
    def coarse_acceptance_rate(self) -> float:
        """Fraction of inner coarse-MH proposals accepted."""
        if self.num_coarse_proposals == 0:
            return np.nan
        return self.num_coarse_accepts / self.num_coarse_proposals

    @property
    def endpoint_move_rate(self) -> float:
        """Fraction of coarse subchains whose endpoint moved."""
        if self.num_transitions == 0:
            return np.nan
        return self.num_endpoint_moves / self.num_transitions

    @property
    def fine_eval_rate(self) -> float:
        """Fraction of outer transitions requiring a fine evaluation."""
        if self.num_transitions == 0:
            return np.nan
        return self.num_fine_evals / self.num_transitions

    @property
    def fine_subset_pass_rate(self) -> float:
        """Fraction of fine-evaluated endpoints in the fine subset."""
        if self.num_fine_evals == 0:
            return np.nan
        return self.num_fine_subset_passes / self.num_fine_evals

    @property
    def fine_correction_acceptance_rate(self) -> float:
        """Fraction of fine-subset endpoints accepted by DA correction."""
        if self.num_fine_subset_passes == 0:
            return np.nan
        return self.num_fine_correction_accepts / self.num_fine_subset_passes

    @property
    def coarse_given_fine(self) -> float:
        """Fraction of fine-subset endpoints also in the coarse subset."""
        if self.num_fine_subset_passes == 0:
            return np.nan
        return self.num_coarse_and_fine_subset_passes / self.num_fine_subset_passes
