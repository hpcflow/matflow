from __future__ import annotations

from contextlib import contextmanager
import os
from typing import Any, Iterator

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import mtex  # type: ignore[import-untyped]
import numpy as np

from matflow.param_classes.orientations import (
    OrientationRepresentationType,
    Orientations,
    QuatOrder,
)


def _mtex_orientations(orientations: Orientations, crystal_symmetry: str) -> Any:
    if orientations.representation.type is not OrientationRepresentationType.QUATERNION:
        raise ValueError("MTEX plotting requires quaternion orientations.")
    data = np.array(orientations.data, dtype=float, copy=True)
    if (
        data.ndim != 2
        or data.shape[1] != 4
        or data.shape[0] == 0
        or not np.all(np.isfinite(data))
        or np.any(np.linalg.norm(data, axis=1) == 0)
    ):
        raise ValueError(
            "orientations.data must contain finite, nonzero (N, 4) quaternions."
        )
    if orientations.representation.quat_order is QuatOrder.VECTOR_SCALAR:
        data = np.roll(data, 1, axis=1)
    elif orientations.representation.quat_order is not QuatOrder.SCALAR_VECTOR:
        raise ValueError("orientations must specify a quaternion component order.")
    # MatFlow stores the inverse of MTEX's crystal-to-specimen rotation.
    data[:, 1:] *= -1

    alignment = []
    for axis in ("x", "y", "z"):
        direction = getattr(orientations.unit_cell_alignment, axis)
        if direction is None:
            raise ValueError(
                "orientations must specify all three unit-cell alignment axes."
            )
        name = direction.name.lower().replace("_star", "*")
        alignment.append(f"{axis.upper()}||{name}")
    cs = mtex.crystalFrame(crystal_symmetry, alignment=alignment)
    return mtex.orientation(data, cs, mtex.specimenFrame("1"))


def _reference_direction(name: str) -> Any:
    if name not in ("x", "y", "z"):
        raise ValueError(f"Unknown IPF reference direction: {name!r}; use x, y or z.")
    return mtex.vector3d(*np.eye(3)[("x", "y", "z").index(name)])


@contextmanager
def _figure() -> Iterator[Any]:
    figure = mtex.newMtexFigure()
    try:
        yield figure
    finally:
        plt.close(figure.fig)


def _annotate_axes(cs: Any) -> None:
    labels = ["x", "y", "z"]
    extra = []
    for name in ("a", "b", "c"):
        direction = getattr(cs, f"{name}Axis")
        unit = direction.normalize().data
        matches = np.flatnonzero(np.all(np.isclose(np.eye(3), unit, atol=1e-10), axis=1))
        if matches.size:
            labels[int(matches[0])] += f"/{name}"
        else:
            extra.append((direction, name))
    mtex.annotate(mtex.vector3d(np.eye(3)), label=labels, backgroundColor="white")
    for direction, name in extra:
        mtex.annotate(
            mtex.vector3d(direction.data), label=[name], backgroundColor="white"
        )


def plot_orientations(
    orientations: Orientations,
    crystal_symmetry: str,
    use_contours: bool,
    pole_figure_directions: list[list[float]] | None = None,
    IPF_reference_direction: str = "z",
    IPF_reference_directions: list[str] | None = None,
    colourbar_limits: list[float] | None = None,
    use_one_colourbar: bool = False,
) -> None:
    """Write pole figures or inverse pole figures and, for scatter plots, an IPF key.

    Supplying ``pole_figure_directions`` selects pole figures; otherwise plot inverse
    pole figures for ``IPF_reference_directions`` (z by default). Inputs are passed
    directly by the corresponding schemas; no orientation handoff files are used.
    """
    ori = _mtex_orientations(orientations, crystal_symmetry)
    reference = _reference_direction(IPF_reference_direction)
    if pole_figure_directions is not None:
        indices = np.asarray(pole_figure_directions, dtype=float)
        if (
            indices.ndim != 2
            or indices.shape[1] != 3
            or indices.shape[0] == 0
            or not np.all(np.isfinite(indices))
            or np.any(np.linalg.norm(indices, axis=1) == 0)
        ):
            raise ValueError(
                "pole_figure_directions must contain finite, nonzero triplets."
            )
        directions = [mtex.Miller(*h, ori.CS) for h in indices]
        plot = mtex.plotPF
        filename = "pole_figure.png"
    else:
        names = ["z"] if IPF_reference_directions is None else IPF_reference_directions
        if not names:
            raise ValueError("IPF_reference_directions must not be empty.")
        directions = [_reference_direction(name) for name in names]
        plot = mtex.plotIPF
        filename = "inverse_pole_figure.png"

    if colourbar_limits is not None:
        limits = np.asarray(colourbar_limits, dtype=float)
        if (
            limits.shape != (2,)
            or not np.all(np.isfinite(limits))
            or limits[0] >= limits[1]
        ):
            raise ValueError(
                "colourbar_limits must contain two finite, increasing values."
            )
    if num_threads := os.environ.get("MATFLOW_RUN_NUM_THREADS"):
        mtex.setMTEXpref("threads", int(num_threads))

    key = mtex.ipfColorKey(ori.CS, ipfDirection=reference)
    with _figure() as figure:
        options = {
            "antipodal": True,
            "how2plot": mtex.plottingConvention(),
        }
        if use_contours:
            color_range = (
                colourbar_limits
                if colourbar_limits is not None
                else "equal"
                if use_one_colourbar
                else "individual"
            )
            plot(ori, directions, contourf=True, colorRange=color_range, **options)
            figure.colorbar(multiple=not use_one_colourbar)
        elif pole_figure_directions is not None:
            plot(ori, key.orientation2color(ori), directions, **options)
        else:
            plot(ori, directions, **options)
        if pole_figure_directions is not None:
            _annotate_axes(ori.CS)
        mtex.saveFigure(filename, fig=figure)

    if not use_contours:
        with _figure() as figure:
            key.plot(how2plot=mtex.plottingConvention())
            mtex.saveFigure("IPF_key.png", fig=figure)
