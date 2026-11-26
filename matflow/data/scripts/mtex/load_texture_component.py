from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import mtex  # type: ignore[import-untyped]
import numpy as np

def load_texture_component(
    file_path: str | Path,
    grid_resolution: float,
    num_orientations: int,
    index: int,
    sampling_method: Literal["discreteSample", "optimalSample"] = "discreteSample",
    crystal_symmetry: str = 'm-3m',
    specimen_symmetry: str = '1'
) -> dict:
    """Build an ODF for texture components and sample one orientation set.
    Sampling advances a single generator seeded from the run's random seed.
    Texture component halfwidths and grid resolution should be given in degrees.
    """

    CS = mtex.crystalFrame(crystal_symmetry)
    SS =  mtex.specimenFrame(specimen_symmetry)

    components = mtex.equispacedSO3Grid(CS=CS, SS=SS,resolution=grid_resolution*mtex.degree)

    N = len(components)

    print('Number of texture components:',N)

    component_data = np.loadtxt(file_path,delimiter=',')

    halfwidths = component_data[index,0:N]
    weights = component_data[index,N:]

    ODF = weights[-1] * mtex.uniformODF(CS,SS)

    for n in range(N): 
        if halfwidths[n] != 0:
            ODF = ODF + weights[n] * mtex.unimodalODF(center=components[n],halfwidth=halfwidths[n]*mtex.degree)

    rng = np.random.default_rng(int(os.environ["MATFLOW_RUN_RANDOM_SEED"]))

    sampled = mtex.discreteSample(ODF, num_orientations, rng=rng)

    if sampling_method == "optimalSample":
        sampled = mtex.optimalSample(ODF, sampled)

    data = np.array(sampled.data, dtype=float, copy=True).reshape(num_orientations, 4)
    data[:, 1:] *= -1

    unit_cell_alignment = {"x": "a", "y": "b", "z": "c"}

    orientations_out = (
            {
                "data": data,
                "representation": {"type": "quaternion", "quat_order": "scalar_vector"},
                "unit_cell_alignment": unit_cell_alignment,
            }
        )

    return {"orientations": orientations_out}