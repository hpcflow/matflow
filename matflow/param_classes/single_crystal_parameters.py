"""
Parameters for a single crystal.
"""
from __future__ import annotations
import copy
from typing_extensions import Self, TypedDict

from hpcflow.sdk.core.parameters import ParameterValue
from hpcflow.sdk.core.utils import get_in_container, set_in_container
from matflow.param_classes.orientations import Orientations


class Perturbation(TypedDict):
    """
    A single perturbation to apply.
    """

    #: Where to apply the perturbation to.
    path: list[str | int]
    #: The multiplicative perturbation to apply.
    multiplicative: float


class SingleCrystalParameters(ParameterValue):
    """
    Parameter relating to the phases in a single crystal.

    Parameters
    ----------
    phases
        The data used to create the bulk phases.
    perturbations
        The perturbations to apply to the phases.
    """

    _typ = "single_crystal_parameters"

    def __init__(
        self,
        phases: dict[str, dict[str, list[float]]],
        perturbations: Perturbation | list[Perturbation] | None = None,
    ):
        self._base = phases
        if perturbations is not None:
            self._perturbations = (
                perturbations if isinstance(perturbations, list) else [perturbations]
            )
        else:
            self._perturbations = []
        # assigned (perturbations applied) on first access
        self._phases: dict[str, dict[str, list[float]]] | None = None

    def __getitem__(self, name: str) -> dict[str, list[float]]:
        """Dict-like retrieval of the parameters for a given phase, with perturbations
        applied."""
        return self.phases[name]

    def to_dict(self):
        out = {k.lstrip("_"): v for k, v in super().to_dict().items() if k != "_phases"}
        out["phases"] = out.pop("base")
        return out

    def as_base(self) -> Self:
        """Return a copy where `base` includes the perturbations."""
        return self.__class__(phases=self.phases)

    @property
    def base(self) -> dict[str, dict[str, list[float]]]:
        """
        The initial data used to create the bulk phases.
        """
        return self._base

    @property
    def phases(self) -> dict[str, dict[str, list[float]]]:
        """
        The data used to create the bulk phases, with perturbations applied.
        """
        if not self._phases:
            phases = copy.deepcopy(self._base)

            perturbations = self._perturbations
            if not isinstance(perturbations, list):
                perturbations = [perturbations]

            for pert_i in perturbations:
                if not pert_i:
                    continue
                scale = pert_i["multiplicative"]
                new_val = get_in_container(phases, pert_i["path"]) * scale
                set_in_container(phases, pert_i["path"], new_val)
            self._phases = phases
        return self._phases

    @property
    def perturbations(self) -> list[Perturbation]:
        """
        The perturbations to apply to the phases.
        """
        return self._perturbations
