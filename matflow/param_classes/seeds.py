"""
Schemes for describing seeds for growing crystals.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing_extensions import Self, TypeGuard

import numpy as np
from numpy.typing import NDArray, ArrayLike
from hpcflow.sdk.core.parameters import ParameterValue
from matflow.param_classes.orientations import Orientations


@dataclass
class MicrostructureSeeds(ParameterValue):
    """
    The seeds for crystalline microstructure.
    """

    _typ = "microstructure_seeds"

    #: The positions of the seeds.
    position: NDArray
    #: The size of box containing the seeds.
    box_size: NDArray
    #: Label for the phase.
    phase_label: str
    #: Orientation data.
    orientations: Orientations | None = None
    #: Seed for the random number generator, if used.
    random_seed: int | None = None

    @staticmethod
    def __is_dict(value) -> TypeGuard[dict[str, Any]]:
        # TypeGuard, not TypeIs; gets the correct type semantics
        return isinstance(value, dict)

    def __post_init__(self) -> None:
        self.box_size = np.asarray(self.box_size)
        self.position = np.asarray(self.position)
        if self.__is_dict(self.orientations):
            self.orientations = Orientations(**self.orientations)
        elif not self.orientations:
            self.orientations = Orientations.from_random(number=self.num_seeds)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.position.shape == other.position.shape
            and np.allclose(self.position, other.position)
            and self.box_size.shape == other.box_size.shape
            and np.allclose(self.box_size, other.box_size)
            and self.orientations == other.orientations
            and self.phase_label == other.phase_label
            and self.random_seed == other.random_seed
        )

    @classmethod
    def from_JSON_like(
        cls, position: ArrayLike, orientations: dict | None = None, **kwargs
    ) -> Self:
        """For custom initialisation via YAML or JSON."""
        # TODO: is this needed?
        if orientations:
            orient = Orientations.from_JSON_like(**orientations)
        else:
            orient = None
        return cls(position=np.asarray(position), orientations=orient, **kwargs)

    @property
    def num_seeds(self) -> int:
        """
        The number of seeds.
        """
        return self.position.shape[0]

    @staticmethod
    def __normalize_orientations(
        orientations: Orientations | dict[str, Any] | None
    ) -> Orientations | None:
        if orientations is None:
            return None
        if isinstance(orientations, dict):
            return Orientations(**orientations)
        return orientations

    @classmethod
    def from_random(
        cls,
        num_seeds: int,
        box_size: NDArray,
        phase_label: str,
        *,
        random_seed: int | None = None,
        orientations: Orientations | dict[str, Any] | None = None,
    ) -> Self:
        """
        Generate a random microstructure.

        Parameters
        ----------
        num_seeds
            The number of seeds for the microstructure.
        box_size
            The size of box containing the microstructure.
        phase_label
            Label for the microstructure.
        random_seed
            Seed for the random number generator.
        orientations
            Orientation information. If omitted, random.
        """
        # TODO: ensure unique seeds points wrt to grid cells
        box_size = np.asarray(box_size)
        rng = np.random.default_rng(seed=random_seed)
        position = rng.random((num_seeds, box_size.size)) * box_size
        return cls(
            position=position,
            box_size=box_size,
            phase_label=phase_label,
            orientations=cls.__normalize_orientations(orientations),
            random_seed=random_seed,
        )

    @classmethod
    def from_file(
        cls,
        path: str,
        box_size: NDArray,
        phase_label: str,
        *,
        number: int | None = None,
        start_index: int = 0,
        delimiter: str = " ",
    ) -> Self:
        """
        Load a microstructure definition from a text file.

        Parameters
        ----------
        path
            Path to the file to load from.
        box_size
            The size of box containing the microstructure.
        phase_label
            Label for the microstructure.
        number
            Number of seeds to read from the file.
        start_index
            The line number of the file that the seeds start at.
            Allows skipping headers.
        delimiter
            The delimiter separating values in the file.
            Defaults to space, but commas and tabs are also sensible
            (and correspond to CSV and TSV files respectively).
        """
        data: list[list[float]] = []
        with Path(path).open("rt") as fh:
            for idx, line in enumerate(fh):
                line = line.strip()
                if not line or idx < start_index:
                    continue
                elif len(data) < number if number is not None else True:
                    data.append([float(i) for i in line.split(delimiter)])
        if number is not None and len(data) < number:
            raise ValueError("Not enough seed points in the file.")

        return cls(
            position=np.asarray(data),
            box_size=box_size,
            phase_label=phase_label,
        )

    def show(self) -> None:
        """
        Plot the microstructure.

        Note
        ----
        Requires matplotlib to be installed and configured.
        """
        from matplotlib import pyplot as plt

        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")
        ax.scatter(
            self.position[:, 0],
            self.position[:, 1],
            self.position[:, 2],
        )
        plt.show()
