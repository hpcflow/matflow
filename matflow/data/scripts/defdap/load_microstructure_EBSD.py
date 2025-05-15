"""Functions copied from matflow-defdap package."""
from __future__ import annotations
from pathlib import Path

import defdap.ebsd as ebsd
from defdap.quat import Quat
import numpy as np
from numpy.typing import NDArray
from scipy.stats import mode
from scipy.ndimage import zoom


def load_microstructure_EBSD(
    EBSD: dict,
    root_path: str,
    scaling_factor: float,
) -> dict:
    ebsd_map = _load_EBSD_map(
        root_path=root_path,
        ebsd_filename=EBSD["filename"],
        ebsd_boundary_tol=EBSD.get("boundary_tol", 10),
        ebsd_min_grain_size=EBSD.get("min_grain_size", 10),
    )

    EBSD_image = _get_EBSD_image(ebsd_map, scaling_factor)

    return {"microstructure_image": EBSD_image}


def _load_EBSD_map(
    root_path: str, ebsd_filename: str, ebsd_boundary_tol: float, ebsd_min_grain_size: int
) -> ebsd.Map:
    "Load EBSD map and detect grains."

    ebsd_map = ebsd.Map(Path(root_path).joinpath(ebsd_filename))

    # check for non-indexed points
    if np.count_nonzero(ebsd_map.phaseArray == 0) != 0:
        raise ValueError("EBSD map contains non-indexed points.")

    ebsd_map.buildQuatArray()

    ebsd_map.findBoundaries(boundDef=ebsd_boundary_tol)
    ebsd_map.findGrains(minGrainSize=ebsd_min_grain_size)
    ebsd_map.calcGrainAvOris()

    return ebsd_map


def _get_EBSD_image(ebsd_map: ebsd.Map, scaling_factor: float) -> dict:
    # Construct an array of Euler angles
    grain_quats = np.empty((len(ebsd_map), 4))

    # Transformation orientations from EBSD orientation reference frame
    # to EBSD spatial reference frame
    frame_transform = Quat.fromAxisAngle(np.array((1, 0, 0)), np.pi)

    if ebsd_map.crystalSym == "hexagonal":
        # Convert hex convention from y // a2 of EBSD map to x // a1 for DAMASK
        hex_transform = Quat.fromAxisAngle(np.array([0, 0, 1]), -np.pi / 6)
        for i, grain in enumerate(ebsd_map):
            grain_quats[i] = (hex_transform * grain.refOri * frame_transform).quatCoef

    else:
        for i, grain in enumerate(ebsd_map):
            grain_quats[i] = (grain.refOri * frame_transform).quatCoef

    # Filter out -2 (too small grains) values in the grain image
    grain_image = ebsd_map.grains
    _remove_small_grain_points(grain_image)

    # scale down image if needed
    if scaling_factor != 1:
        grain_image = zoom(
            grain_image, scaling_factor, order=0, prefilter=False, mode="nearest"
        )

    # downstream expects grain numbering to start at 0 not 1
    grain_image -= 1

    # set grain IDs as contiguous range:
    uniq, inv = np.unique(grain_image.reshape(-1, order="C"), return_inverse=True)
    grain_quats = grain_quats[uniq]
    grain_image = np.reshape(inv, grain_image.shape, order="C")
    grain_phases = np.array([grain.phaseID.item() for grain in ebsd_map])[uniq]

    EBSD_image = {
        "orientations": {
            "type": "quat",
            "unit_cell_alignment": {"x": "a"},
            "quaternions": grain_quats,
            "P": 1,  # DefDAP uses P=+1 (e.g see `defdap.quat.Quat.__mul__`)
            "quat_component_ordering": "scalar-vector",
        },
        "grains": grain_image,
        "scale": ebsd_map.scale,
        "phase_labels": [phase.name for phase in ebsd_map.phases],
        "grain_phases": grain_phases,
    }

    return EBSD_image


def _select_area(
    i: int, j: int, grain_image: NDArray, kind: str | None = None
) -> tuple[NDArray, int]:
    on_edge = 0

    if kind == "4_closest":
        area = []
        if i != 0:
            area.append(grain_image[i - 1, j])
            on_edge += 1
        elif i != grain_image.shape[0] - 1:
            area.append(grain_image[i + 1, j])
            on_edge += 1

        if j != 0:
            area.append(grain_image[i, j - 1])
            on_edge += 1
        elif j != grain_image.shape[1] - 1:
            area.append(grain_image[i, j + 1])
            on_edge += 1

        area = np.array(area)

    else:
        i_min, i_max = 1, 1
        j_min, j_max = 1, 1

        if i == 0:
            i_min = 0
            on_edge += 1
        elif i == grain_image.shape[0] - 1:
            i_max = 0
            on_edge += 1

        if j == 0:
            j_min = 0
            on_edge += 1
        elif j == grain_image.shape[1] - 1:
            j_max = 0
            on_edge += 1

        # select 3x3 region around point
        area = grain_image[i - i_min : i + i_max + 1, j - j_min : j + j_max + 1]

    return area, on_edge


def _remove_small_grain_points(grain_image: NDArray, max_iterations: int = 200):
    # num_neighbours - must have at least this many pixels surrounding
    # start checking for 8 neighbours, then 7 until 2
    for num_neighbours in range(8, 0, -1):
        print(
            f"Starting iterations with at least {num_neighbours} equal "
            f"neighbour pixels"
        )

        force = num_neighbours == 1

        num_bad_prev = 0
        iteration = 0
        while True:
            num_bad = np.count_nonzero(grain_image == -2)
            if num_bad == 0:
                # No bad values left, done
                print("All bad points removed.")
                return
            elif num_bad == num_bad_prev:
                # Not removing any more
                print("Number of bad points is not decreasing!")
                break
            if iteration > max_iterations:
                print("Max iterations.")
                break

            iteration += 1
            if force:
                print("All bad points must die! Picking largest neighbour.")
            else:
                print("Starting iteration {}, num bad: {}".format(iteration, num_bad))

            grain_image_new = np.copy(grain_image)
            for i, j in zip(*np.where(grain_image == -2)):
                kind = "4_closest" if force else None
                area, on_edge = _select_area(i, j, grain_image, kind=kind)
                area = area.flatten()
                area = area[area > 0]  # remove -1 and -2

                if force:
                    sizes = [np.count_nonzero(grain_image == k) for k in area]
                    grain_image_new[i, j] = area[np.argsort(sizes)[-1]]

                else:
                    mode_vals, mode_counts = mode(area, keepdims=True)
                    for mode_val, mode_count in zip(mode_vals, mode_counts):
                        if mode_count >= num_neighbours:
                            grain_image_new[i, j] = mode_val
                            break

            num_bad_prev = num_bad
            # [:, :] required to update the array passed in
            grain_image[:, :] = grain_image_new
