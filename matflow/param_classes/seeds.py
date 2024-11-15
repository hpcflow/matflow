from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing_extensions import Self

import numpy as np
from numpy.typing import NDArray
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

    def __post_init__(self) -> None:
        self.box_size = np.asarray(self.box_size)
        self.position = np.asarray(self.position)
        if not self.orientations:
            self.orientations = Orientations.from_random(number=self.num_seeds)
        elif not isinstance(self.orientations, Orientations):
            self.orientations = Orientations(**self.orientations)

    @classmethod
    def from_JSON_like(cls, position, orientations=None, **kwargs):
        """For custom initialisation via YAML or JSON."""
        # TODO: is this needed?
        if orientations:
            orientations = Orientations.from_JSON_like(**orientations)
        return cls(position=np.asarray(position), orientations=orientations, **kwargs)

    @property
    def num_seeds(self) -> int:
        """
        The number of seeds.
        """
        return self.position.shape[0]

    @classmethod
    def from_random(
        cls,
        num_seeds: int,
        box_size: NDArray,
        phase_label: str,
        *,
        random_seed: int | None = None,
        orientations: Orientations | None = None,
    ) -> Self:
        """
        Generate a random microstructure.
        """
        # TODO: ensure unique seeds points wrt to grid cells
        box_size = np.asarray(box_size)
        rng = np.random.default_rng(seed=random_seed)
        position = rng.random((num_seeds, box_size.size)) * box_size
        return cls(
            position=position,
            box_size=box_size,
            phase_label=phase_label,
            orientations=orientations,
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
