from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from hpcflow.sdk.core.parameters import ParameterValue
from matflow.param_classes.orientations import Orientations


@dataclass
class MicrostructureSeeds(ParameterValue):
    _typ = "microstructure_seeds"

    position: np.ndarray
    box_size: np.ndarray
    phase_label: str
    orientations: Optional[Orientations] = None
    random_seed: Optional[int] = None

    def __post_init__(self):
        self.box_size = np.asarray(self.box_size)
        self.position = np.asarray(self.position)
        if self.orientations:
            if not isinstance(self.orientations, Orientations):
                self.orientations = Orientations(**self.orientations)
        else:
            self.orientations = Orientations.from_random(number=self.num_seeds)

    def __eq__(self, other: object) -> bool:
        if (
            isinstance(other, self.__class__)
            and self.position.shape == other.position.shape
            and np.allclose(self.position, other.position)
            and self.box_size.shape == other.box_size.shape
            and np.allclose(self.box_size, other.box_size)
            and self.orientations == other.orientations
            and self.phase_label == other.phase_label
            and self.random_seed == other.random_seed
        ):
            return True
        return False

    @classmethod
    def from_JSON_like(cls, position, orientations=None, **kwargs):
        """For custom initialisation via YAML or JSON."""
        # TODO: is this needed?
        if orientations:
            orientations = Orientations.from_JSON_like(**orientations)
        return cls(position=np.asarray(position), orientations=orientations, **kwargs)

    @property
    def num_seeds(self):
        return self.position.shape[0]

    @classmethod
    def from_random(
        cls,
        num_seeds,
        box_size,
        phase_label,
        random_seed=None,
        orientations=None,
    ):
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
        path,
        box_size,
        phase_label,
        number=None,
        start_index=0,
        delimiter=" ",
    ):
        data = []
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

    def show(self):
        from matplotlib import pyplot as plt

        fig = plt.figure()
        ax = fig.add_subplot(projection="3d")
        ax.scatter(
            self.position[:, 0],
            self.position[:, 1],
            self.position[:, 2],
        )
        plt.show()
