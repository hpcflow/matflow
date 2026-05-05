"""Functions copied from matflow-defdap package."""
from __future__ import annotations
from pathlib import Path
from typing import Any

import defdap.ebsd as ebsd
import defdap.hrdic as hrdic
from defdap.quat import Quat
import numpy as np
from numpy.typing import NDArray
from scipy.stats import mode
from scipy.ndimage import zoom


def load_microstructure_EBSD_DIC(
    DIC: dict,
    EBSD: dict,
    root_path: str,
    transform_type: str,
    scaling_factor: float,
    find_grains_algorithm: str,
) -> dict:
    ebsd_map = _load_EBSD_map(
        root_path=root_path,
        ebsd_filename=EBSD["filename"],
        ebsd_boundary_tol=EBSD.get("boundary_tol", 10),
        ebsd_min_grain_size=EBSD.get("min_grain_size", 10),
    )
    dic_map = _load_DIC_map(
        root_path=root_path,
        dic_filename=DIC["filename"],
        dic_crop=DIC.get("crop", None),
        dic_scale=DIC.get("scale", None),
    )
    _link_EBSD_DIC_maps(
        ebsd_map=ebsd_map,
        dic_map=dic_map,
        dic_homog_points=DIC["homog_points"],
        dic_min_grain_size=DIC.get("min_grain_size", 10),
        ebsd_homog_points=EBSD["homog_points"],
        transform_type=transform_type,
        find_grains_algorithm=find_grains_algorithm,
    )
    DIC_image = _get_DIC_image(dic_map, scaling_factor)

    return {"microstructure_image": DIC_image}


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


def _load_DIC_map(
    root_path: str, dic_filename: str, dic_crop: list[int] | None, dic_scale: float | None
) -> hrdic.Map:
    "Load in DIC, crop and set scale."

    dic_map = hrdic.Map(root_path, dic_filename)
    if dic_crop is not None:
        dic_map.setCrop(
            xMin=dic_crop[0], xMax=dic_crop[1], yMin=dic_crop[2], yMax=dic_crop[3]
        )
    if dic_scale is not None:
        dic_map.setScale(dic_scale)

    return dic_map


def _link_EBSD_DIC_maps(
    ebsd_map: ebsd.Map,
    dic_map: hrdic.Map,
    dic_homog_points: NDArray,
    dic_min_grain_size: int,
    ebsd_homog_points: NDArray,
    transform_type: str,
    find_grains_algorithm: str,
) -> None:
    dic_map.homogPoints = dic_homog_points
    ebsd_map.homogPoints = ebsd_homog_points
    dic_map.linkEbsdMap(ebsd_map, transformType=transform_type)

    dic_map.findGrains(minGrainSize=dic_min_grain_size, algorithm=find_grains_algorithm)


def _get_DIC_image(dic_map: hrdic.Map, scaling_factor: float) -> dict[str, Any]:
    # Construct an array of Euler angles
    grain_quats = np.empty((len(dic_map), 4))

    # Transformation orientations from EBSD orientation reference frame
    # to EBSD spatial reference frame
    frame_transform = Quat.fromAxisAngle(np.array((1, 0, 0)), np.pi)

    if dic_map.ebsdMap.crystalSym == "hexagonal":
        # Convert hex convention from y // a2 of EBSD map to x // a1 for DAMASK
        hex_transform = Quat.fromAxisAngle(np.array([0, 0, 1]), -np.pi / 6)
        for i, grain in enumerate(dic_map):
            grain_quats[i] = (
                hex_transform * grain.ebsdGrain.refOri * frame_transform
            ).quatCoef

    else:
        for i, grain in enumerate(dic_map):
            grain_quats[i] = (grain.ebsdGrain.refOri * frame_transform).quatCoef

    # Filter out -1 (grain boundary points) and -2 (too small grains)
    # values in the grain image
    grain_image = dic_map.grains
    _remove_boundary_points(grain_image)
    _remove_small_grain_points(grain_image)
    _remove_boundary_points(grain_image)
    _remove_boundary_points(grain_image, force_remove=True)

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

    DIC_image = {
        "orientations": {
            "type": "quat",
            "unit_cell_alignment": {"x": "a"},
            "quaternions": grain_quats,
            "P": 1,  # DefDAP uses P=+1 (e.g see `defdap.quat.Quat.__mul__`)
            "quat_component_ordering": "scalar-vector",
        },
        "grains": grain_image,
    }
    try:
        DIC_image["scale"] = dic_map.scale
    except ValueError:
        pass

    return DIC_image


def _select_area(i: int, j: int, grain_image: NDArray) -> tuple[NDArray, int]:
    i_min, i_max = 1, 1
    j_min, j_max = 1, 1

    on_edge = 0

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


def _remove_boundary_points(
    grain_image: NDArray, *, force_remove: bool = False, max_iterations: int = 200
) -> None:
    num_bad_prev = 0
    iteration = 0
    while True:
        num_bad = np.count_nonzero(grain_image == -1)
        if num_bad == 0:
            # No bad values left, done
            print("All bad points removed.")
            break
        elif num_bad == num_bad_prev:
            # Not removing any more
            print("Number of bad points is not decreasing!")
            break
        if iteration > max_iterations:
            print("Max iterations.")
            break

        iteration += 1
        print("Starting iteration {}, num bad: {}".format(iteration, num_bad))

        grain_image_new = np.copy(grain_image)

        # because of how boundaries are defined, best to take from -ve side
        for i, j in zip(*np.where(grain_image == -1)):
            if (
                i != 0
                and j != 0
                and grain_image[i - 1, j] > 0
                and grain_image[i, j - 1] > 0
            ):
                # if both left and above pixels defined, check the diagonal
                if grain_image[i - 1, j - 1] == grain_image[i - 1, j]:
                    grain_image_new[i, j] = grain_image[i - 1, j]

                elif grain_image[i - 1, j - 1] == grain_image[i, j - 1]:
                    grain_image_new[i, j] = grain_image[i, j - 1]

                else:
                    # give up, try in next iteration

                    if force_remove:
                        area, on_edge = _select_area(i, j, grain_image)
                        area = area.flatten()
                        area = area[np.where(area > 0)]  # remove -1 and -2

                        mode_vals, mode_counts = mode(area, keepdims=True)
                        for mode_val, mode_count in zip(mode_vals, mode_counts):
                            #         mode_val, mode_count = mode_vals[0], mode_counts[0]
                            #                         if mode_count >= num_neighbours:
                            grain_image_new[i, j] = mode_val
                            break

            elif i != 0 and grain_image[i - 1, j] > 0:
                grain_image_new[i, j] = grain_image[i - 1, j]

            elif j != 0 and grain_image[i, j - 1] > 0:
                grain_image_new[i, j] = grain_image[i, j - 1]

            # give up, try in next iteration

        num_bad_prev = num_bad
        # [:, :] required to update the array passed in
        grain_image[:, :] = grain_image_new


def _remove_small_grain_points(
    grain_image: NDArray, *, max_iterations: int = 200
) -> None:
    # num_neighbours - must have at least this many pixels surrounding
    # start checking for 8 neighbours, then 7 until 2
    for num_neighbours in list(range(8, 1, -1)):
        print(f"Starting iterations with at least {num_neighbours} equal neighbours")

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
            print("Starting iteration {}, num bad: {}".format(iteration, num_bad))

            grain_image_new = np.copy(grain_image)

            for i, j in zip(*np.where(grain_image == -2)):
                area, on_edge = _select_area(i, j, grain_image)
                area = area.flatten()
                area = area[np.where(area > 0)]  # remove -1 and -2

                mode_vals, mode_counts = mode(area, keepdims=True)
                for mode_val, mode_count in zip(mode_vals, mode_counts):
                    if mode_count >= num_neighbours:
                        grain_image_new[i, j] = mode_val
                        break

            num_bad_prev = num_bad
            # [:, :] required to update the array passed in
            grain_image[:, :] = grain_image_new
