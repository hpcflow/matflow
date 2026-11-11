from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import mtex  # type: ignore[import-untyped]
import numpy as np
from numpy.typing import ArrayLike
from typing_extensions import NotRequired, TypedDict


class EBSDRotation(TypedDict):
    """Rigid map rotation with optional preservation of positions or orientations.

    ``keep_XY`` preserves map positions while rotating orientations.
    ``keep_euler`` preserves orientations while rotating map positions.
    With neither flag set, both are rotated; the flags cannot both be true.
    """

    euler_angles_deg: ArrayLike
    keep_XY: NotRequired[bool]
    keep_euler: NotRequired[bool]


class EBSDEulerCorrection(TypedDict):
    """Import rotation from the file's Euler frame to the map frame (Bunge degrees)."""

    euler_angles_deg: ArrayLike


def sample_texture_EBSD(
    specimen_symmetry: str,
    EBSD_phase: str,
    num_orientations: int,
    EBSD_reference_frame_transformation: str | None = "euler_to_spatial",
    EBSD_rotation: EBSDRotation | None = None,
    CTF_file_path: str | Path | None = None,
    CRC_file_path: str | Path | None = None,
    kernel_halfwidth_deg: float = 10.0,
    num_orientation_sets: int | None = None,
    sampling_method: Literal["discreteSample", "optimalSample"] = "discreteSample",
    EBSD_euler_correction: EBSDEulerCorrection | None = None,
) -> dict:
    """Estimate one EBSD density and sample one or more orientation sets.

    With ``num_orientation_sets=None``, return one set without printing progress.
    Otherwise, return a list of that many sets and print completed/total counts.
    Sampling advances a single generator seeded from the run's random seed.
    ``optimalSample`` optimizes each seeded random sample to better match the density.
    """
    if (CTF_file_path is None) == (CRC_file_path is None):
        raise ValueError("Specify exactly one of CTF_file_path and CRC_file_path.")
    if sampling_method not in ("discreteSample", "optimalSample"):
        raise ValueError("sampling_method must be 'discreteSample' or 'optimalSample'.")
    if (
        not isinstance(num_orientations, (int, np.integer))
        or isinstance(num_orientations, bool)
        or num_orientations <= 0
    ):
        raise ValueError("num_orientations must be a positive integer.")
    if num_orientation_sets is not None and (
        not isinstance(num_orientation_sets, (int, np.integer))
        or isinstance(num_orientation_sets, bool)
        or num_orientation_sets <= 0
    ):
        raise ValueError("num_orientation_sets must be a positive integer or None.")
    if (
        isinstance(kernel_halfwidth_deg, bool)
        or not np.isfinite(kernel_halfwidth_deg)
        or not 0 < kernel_halfwidth_deg <= 180
    ):
        raise ValueError("kernel_halfwidth_deg must be finite and in (0, 180] degrees.")

    transform = EBSD_reference_frame_transformation
    if EBSD_euler_correction is not None:
        try:
            angles = np.asarray(EBSD_euler_correction["euler_angles_deg"], dtype=float)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "EBSD_euler_correction must specify three finite angles in euler_angles_deg."
            ) from exc
        if angles.shape != (3,) or not np.all(np.isfinite(angles)):
            raise ValueError(
                "EBSD_euler_correction.euler_angles_deg must contain three finite angles."
            )
        correction = mtex.rotation.byEuler(*(angles * mtex.degree))
    elif transform in ("euler_to_spatial", "convertEuler2SpatialReferenceFrame"):
        correction = None
    elif transform in (
        None,
        "",
        "spatial_to_euler",
        "convertSpatial2EulerReferenceFrame",
    ):
        # None would request MTEX's default Oxford correction; identity preserves Euler angles.
        correction = mtex.rotation.id
    else:
        raise ValueError(f"Unknown EBSD reference frame transformation: {transform!r}")

    file_path = CTF_file_path if CTF_file_path is not None else CRC_file_path
    ebsd = mtex.loadEBSD(
        file_path,
        interface="ctf" if CTF_file_path is not None else "crc",
        grid=False,
        eulerCorrection=correction,
    )
    if EBSD_rotation is not None:
        angles = np.asarray(EBSD_rotation["euler_angles_deg"], dtype=float)
        if angles.shape != (3,) or not np.all(np.isfinite(angles)):
            raise ValueError(
                "EBSD_rotation.euler_angles_deg must contain three finite angles."
            )
        rot = mtex.rotation.byEuler(*(angles * mtex.degree))
        ebsd = ebsd.rotate(
            rot,
            keepXY=EBSD_rotation.get("keep_XY", False),
            keepEuler=EBSD_rotation.get("keep_euler", False),
        )

    source = ebsd[EBSD_phase].orientations
    if source.size == 0 or not np.all(np.isfinite(source.data)):
        raise ValueError(f"Phase {EBSD_phase!r} has no finite indexed orientations.")
    source.SS = mtex.specimenFrame(specimen_symmetry)

    if num_threads := os.environ.get("MATFLOW_RUN_NUM_THREADS"):
        # MTEX otherwise counts logical CPUs on Windows, oversubscribing FINUFFT.
        mtex.setMTEXpref("threads", int(num_threads))

    rng = np.random.default_rng(int(os.environ["MATFLOW_RUN_RANDOM_SEED"]))
    density = mtex.calcDensity(source, halfwidth=kernel_halfwidth_deg * mtex.degree)
    alignment = source.CS.alignment()
    if not alignment:
        unit_cell_alignment = {"x": "a", "y": "b", "z": "c"}
    else:
        unit_cell_alignment = {
            axis.lower(): direction.replace("*", "_star")
            for axis, direction in (item.split("||") for item in alignment)
        }
        if set(unit_cell_alignment) != {"x", "y", "z"}:
            raise ValueError(
                f"The crystal frame alignment cannot be represented by MatFlow: {alignment}"
            )

    orientation_sets = []
    if num_orientation_sets is not None:
        print(f"Sampling orientation sets: 0/{num_orientation_sets} complete", flush=True)

    for set_index in range(1 if num_orientation_sets is None else num_orientation_sets):
        # always use discreteSample first, to ensure the RNG is used (otherwise we'd get
        # the same orientations for each set):
        sampled = mtex.discreteSample(density, num_orientations, rng=rng)
        if sampling_method == "optimalSample":
            sampled = mtex.optimalSample(density, sampled)
        # MTEX maps crystal to specimen; MatFlow stores the inverse quaternion.
        data = np.array(sampled.data, dtype=float, copy=True).reshape(num_orientations, 4)
        data[:, 1:] *= -1
        orientation_sets.append(
            {
                "data": data,
                "representation": {"type": "quaternion", "quat_order": "scalar_vector"},
                "unit_cell_alignment": unit_cell_alignment,
            }
        )
        if num_orientation_sets is not None:
            print(
                f"Sampling orientation sets: {set_index + 1}/{num_orientation_sets} "
                f"complete",
                flush=True,
            )
    orientations_out = (
        orientation_sets[0] if num_orientation_sets is None else orientation_sets
    )
    return {"orientations": orientations_out}
