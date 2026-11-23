from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import numpy as np


def plot(
    x: Sequence,
    y: Sequence,
    *,
    xlabel: str = "",
    ylabel: str = "",
    xscale="linear",
    yscale="linear",
    label: str | None = None,
    title: str | None = None,
    width: float = 3.4,  # inches; ~single journal column
    aspect: float = 0.72,
    fontsize: float = 8,
    linewidth: float = 1.2,
    marker: str | None = None,
    filename: str | Path | None = None,
    ax: Axes | None = None,
    **kwargs,
) -> tuple[Figure, Axes]:
    """Create a publication-quality x-y line plot."""

    if ax is None:
        fig, ax = plt.subplots(
            figsize=(width, width * aspect),
            constrained_layout=True,
        )
    else:
        fig = ax.figure

    ax.plot(
        x,
        y,
        label=label,
        linewidth=linewidth,
        marker=marker,
        **kwargs,
    )

    ax.set_xlabel(xlabel, fontsize=fontsize)
    ax.set_ylabel(ylabel, fontsize=fontsize)
    ax.set(
        xscale=xscale,
        yscale=yscale,
    )

    if title:
        ax.set_title(title, fontsize=fontsize)

    ax.tick_params(
        axis="both",
        which="major",
        direction="in",
        top=True,
        right=True,
        labelsize=fontsize - 1,
        width=0.8,
        length=3.5,
    )
    ax.tick_params(
        axis="both",
        which="minor",
        direction="in",
        top=True,
        right=True,
        width=0.6,
        length=2,
    )

    ax.minorticks_on()

    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    if label:
        ax.legend(
            frameon=False,
            fontsize=fontsize - 1,
        )

    if filename is not None:
        fig.savefig(
            filename,
            dpi=600,
            bbox_inches="tight",
        )

    return fig, ax


def level_plot(
    x,
    y,
    *,
    xlabel="",
    ylabel="",
    title=None,
    xscale="linear",
    yscale="linear",
    markersize=5,
    cmap="Blues",
    min_shade=0.45,
    max_shade=0.95,
    legend=True,
    ax=None,
    width: float = 3.4,  # inches; ~single journal column
    aspect: float = 0.72,
):
    """
    Plot variable-length arrays of y-values at each x-position.

    y[j][i] is the value at x[j] for level index i.

    Increasing level index is represented by increasingly dark markers.

    Parameters
    ----------
    x : array-like
        X positions.

    y : sequence of array-like
        y[j] contains values at x[j]. Arrays may have different lengths.

    xlabel, ylabel : str
        Axis labels.

    title : str, optional
        Plot title.

    xscale, yscale : str
        Axis scales ("linear", "log", etc.).

    markersize : float
        Marker size.

    cmap : str
        Sequential Matplotlib colormap.

    min_shade, max_shade : float
        Range of the colormap to use.

    legend : bool
        Whether to show the level-index legend.

    ax : matplotlib.axes.Axes, optional
        Existing axes to plot on.

    Returns
    -------
    fig, ax
        Matplotlib Figure and Axes.
    """

    x = np.asarray(x)
    y = [np.asarray(yj) for yj in y]

    if len(x) != len(y):
        raise ValueError("x and y must have the same length")

    if len(y) == 0:
        raise ValueError("y must contain at least one array")

    max_levels = max(len(yj) for yj in y)

    if ax is None:
        fig, ax = plt.subplots(
            figsize=(width, width * aspect),
            constrained_layout=True,
        )
    else:
        fig = ax.figure

    # ---------------------------------------------------------
    # Colours
    # level 0 = light
    # higher levels = progressively darker
    # ---------------------------------------------------------

    colormap = plt.get_cmap(cmap)

    shades = np.linspace(
        min_shade,
        max_shade,
        max_levels,
    )

    colors = [colormap(s) for s in shades]

    # ---------------------------------------------------------
    # Arrows
    # Show direction from level 0 -> highest available level
    # ---------------------------------------------------------

    # Connect levels within each proposal scale
    for xj, yj in zip(x, y):
        if len(yj) < 2:
            continue

        ax.plot(
            [xj] * len(yj),
            yj,
            color="0.80",
            linewidth=0.8,
            zorder=1,
        )

    # ---------------------------------------------------------
    # Points
    # Plot once per level so colour/legend remain consistent
    # ---------------------------------------------------------

    for idx in range(max_levels):

        xi = []
        yi = []

        for xj, yj in zip(x, y):
            if idx < len(yj):
                xi.append(xj)
                yi.append(yj[idx])

        ax.plot(
            xi,
            yi,
            linestyle="none",
            marker="o",
            markersize=markersize,
            markerfacecolor=colors[idx],
            markeredgecolor=colors[idx],
            label=f"{idx}",
            zorder=2,
        )

    # ---------------------------------------------------------
    # Axes
    # ---------------------------------------------------------

    ax.set(
        xlabel=xlabel,
        ylabel=ylabel,
        title=title,
        xscale=xscale,
        yscale=yscale,
    )

    ax.tick_params(
        which="both",
        direction="in",
        top=True,
        right=True,
    )

    ax.minorticks_on()

    # ---------------------------------------------------------
    # Legend
    # ---------------------------------------------------------

    if legend:
        ax.legend(
            title="Level index",
            frameon=False,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            borderaxespad=0,
            handletextpad=0.4,
            labelspacing=0.3,
        )

    return fig, ax


def plot_proposal_scale_study_data_DAMASK_CP(
    data,
    *,
    Ns=None,
    width=2.4,
    aspect=0.85,
):
    """
    Plot proposal-scale study results.

    Columns correspond to N.
    Rows correspond to:
        1. outer move rate
        2. jump distance
        3. component acceptance rate
    """

    if Ns is None:
        Ns = sorted(data.keys())

    metrics = [
        ("outer_moves", "Mean outer move rate"),
        ("jumps", "Mean jump distance"),
        # ("comps",       "Mean component acceptance rate"),
    ]

    nrows = len(metrics)
    ncols = len(Ns)

    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(width * ncols, width * aspect * nrows),
        sharex="col",
        sharey="row",  # same y-range within each row
        squeeze=False,
        constrained_layout=True,
    )

    for col, N in enumerate(Ns):

        for row, (key, ylabel) in enumerate(metrics):

            ax = axes[row, col]

            level_plot(
                x=data[N]["scales"],
                y=data[N][key],
                ax=ax,
                legend=False,
            )

            # Column headings
            if row == 0:
                ax.set_title(rf"$N = {N}$")

            # Y labels only on left column
            if col == 0:
                ax.set_ylabel(ylabel)
            else:
                ax.set_ylabel("")

    # ---------------------------------------------------------
    # One legend for the entire figure
    # ---------------------------------------------------------

    handles, labels = axes[0, 0].get_legend_handles_labels()

    fig.legend(
        handles,
        labels,
        title="Level index",
        frameon=False,
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
    )
    fig.supxlabel("Proposal scale")

    return fig, axes


def plot_cov_comparison(
    x: Sequence,
    cov_mean: Sequence,
    cov_empirical: Sequence,
    *,
    xlabel: str = r"Num. samples per level, $N$",
    ylabel: str = "Coefficient of variation",
    xscale: str = "linear",
    yscale: str = "linear",
    title: str | None = None,
    width: float = 3.4,
    aspect: float = 0.72,
    fontsize: float = 8,
    linewidth: float = 1.2,
    filename: str | Path | None = None,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Compare mean estimated and empirical CoV across sample counts."""

    x = np.asarray(x)
    cov_mean = np.asarray(cov_mean)
    cov_empirical = np.asarray(cov_empirical)

    if not (len(x) == len(cov_mean) == len(cov_empirical)):
        raise ValueError("Input arrays must have the same length.")

    # Ensure lines connect points in increasing sample-count order.
    idx = np.argsort(x)
    x = x[idx]
    cov_mean = cov_mean[idx]
    cov_empirical = cov_empirical[idx]

    if ax is None:
        fig, ax = plt.subplots(
            figsize=(width, width * aspect),
            constrained_layout=True,
        )
    else:
        fig = ax.figure

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    for y, label, color, marker in [
        (cov_mean, "Mean estimated CoV", colors[0], "o"),
        (cov_empirical, "Empirical CoV", colors[1], "s"),
    ]:
        ax.plot(
            x,
            y,
            color=color,
            linewidth=linewidth,
            marker=marker,
            markersize=4.5,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=1.0,
            label=label,
        )

    ax.set_xlabel(xlabel, fontsize=fontsize)
    ax.set_ylabel(ylabel, fontsize=fontsize)
    ax.set(xscale=xscale, yscale=yscale)

    if title:
        ax.set_title(title, fontsize=fontsize)

    ax.tick_params(
        axis="both",
        which="major",
        direction="in",
        top=True,
        right=True,
        labelsize=fontsize - 1,
        width=0.8,
        length=3.5,
    )
    ax.tick_params(
        axis="both",
        which="minor",
        direction="in",
        top=True,
        right=True,
        width=0.6,
        length=2,
    )
    ax.minorticks_on()

    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    legend = ax.legend(
        fontsize=fontsize - 1,
        frameon=True,
        fancybox=False,
        framealpha=1,
        edgecolor="0.7",
    )
    legend.get_frame().set_linewidth(0.6)

    if filename is not None:
        fig.savefig(filename, dpi=600, bbox_inches="tight")

    return fig, ax


def plot_pf_num_samples(
    all_results: dict,
    quantile_range: float = 0.95,
    *,
    target_pf: float | None = 1e-4,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    xscale: str = "linear",
    yscale: str = "linear",
    xlabel: str | None = None,
    ylabel: str = r"Failure probability, $P_F$",
    title: str | None = None,
    width: float = 3.4,
    aspect: float = 0.72,
    fontsize: float = 8,
    linewidth: float = 1.2,
    marker: str = "o",
    color: str | None = None,
    alpha: float = 0.18,
    filename: str | Path | None = None,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """
    Plot mean failure probability and empirical quantile intervals
    against sample count or repeat count.

    Expected structure
    ------------------
    all_results = {
        "converge_label": "N" or "R",
        "fixed_num": ...,
        "data": {
            x_value: {
                "pf": [...],
                "pf_mean": ...,
            },
            ...
        },
    }

    The shaded interval contains the central `quantile_range`
    fraction of the repeated failure-probability estimates.
    """

    if not 0 < quantile_range < 1:
        raise ValueError("quantile_range must lie between 0 and 1.")

    converge_label = all_results["converge_label"]
    fixed_num = all_results["fixed_num"]
    all_data = all_results["data"]

    if converge_label not in ("N", "R"):
        raise ValueError("converge_label must be 'N' or 'R'.")

    if xlabel is None:
        xlabel = (
            r"Number of samples, $N$"
            if converge_label == "N"
            else r"Number of repeats, $R$"
        )

    if title is None:
        fixed_label = "R" if converge_label == "N" else "N"
        title = rf"${fixed_label}={fixed_num}$"

    # Sort by x-value.
    x = np.asarray(sorted(all_data), dtype=float)

    q_lower = (1.0 - quantile_range) / 2.0
    q_upper = 1.0 - q_lower

    means = []
    lowers = []
    uppers = []

    for value in sorted(all_data):
        data = all_data[value]
        pf = np.asarray(data["pf"], dtype=float)

        means.append(data["pf_mean"])
        lowers.append(np.quantile(pf, q_lower))
        uppers.append(np.quantile(pf, q_upper))

    means = np.asarray(means)
    lowers = np.asarray(lowers)
    uppers = np.asarray(uppers)

    if ax is None:
        fig, ax = plt.subplots(
            figsize=(width, width * aspect),
            constrained_layout=True,
        )
    else:
        fig = ax.figure

    if color is None:
        color = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]

    # Empirical central quantile interval.
    ax.fill_between(
        x,
        lowers,
        uppers,
        color=color,
        alpha=alpha,
        linewidth=0,
        label=f"{quantile_range:.0%} quantile",
        zorder=1,
    )

    # Mean failure probability.
    ax.plot(
        x,
        means,
        color=color,
        linewidth=linewidth,
        marker=marker,
        markersize=4.5,
        markerfacecolor="white",
        markeredgecolor=color,
        markeredgewidth=1.0,
        label="Mean",
        zorder=3,
    )

    # Reference failure probability.
    if target_pf is not None:
        ax.axhline(
            target_pf,
            color="0.4",
            linestyle="--",
            linewidth=0.9,
            label="Reference",
            zorder=2,
        )

    ax.set_xlabel(xlabel, fontsize=fontsize)
    ax.set_ylabel(ylabel, fontsize=fontsize)
    ax.set(
        xscale=xscale,
        yscale=yscale,
        xlim=xlim,
        ylim=ylim,
    )

    if title:
        ax.set_title(title, fontsize=fontsize)

    ax.tick_params(
        axis="both",
        which="major",
        direction="in",
        top=True,
        right=True,
        labelsize=fontsize - 1,
        width=0.8,
        length=3.5,
    )
    ax.tick_params(
        axis="both",
        which="minor",
        direction="in",
        top=True,
        right=True,
        width=0.6,
        length=2,
    )

    ax.minorticks_on()

    for spine in ax.spines.values():
        spine.set_linewidth(0.8)

    legend = ax.legend(
        loc="best",
        fontsize=fontsize - 1,
        frameon=True,
        fancybox=False,
        framealpha=1.0,
        edgecolor="0.7",
        handlelength=1.6,
        handletextpad=0.5,
        labelspacing=0.3,
    )
    legend.get_frame().set_linewidth(0.6)

    if filename is not None:
        fig.savefig(
            filename,
            dpi=600,
            bbox_inches="tight",
        )

    return fig, ax


def plot_convergence_vs_num_samples(
    num_samples,
    pf_means,
    pf_repeats,
    cov_means,
    cov_std,
    cov_empiricals,
    *,
    reference_pf=None,
    quantile_range=0.95,
    width=3.4,
    aspect=0.72,
    fontsize=10,
    linewidth=1.0,
    markersize=4.5,
    band_alpha=0.18,
    pf_ylim: tuple[float, float] | None = None,
):
    """
    Two-panel convergence plot.

    Top: mean failure probability with empirical quantile band.
    Bottom: mean estimated CoV versus empirical CoV.

    pf_repeats : sequence of sequences
        Individual failure-probability estimates for each N.
    """

    N = np.asarray(num_samples, dtype=float)
    pf = np.asarray(pf_means, dtype=float)
    cov = np.asarray(cov_means, dtype=float)
    cov_std = np.asarray(cov_std, dtype=float)
    cov_emp = np.asarray(cov_empiricals, dtype=float)

    if not (len(N) == len(pf) == len(pf_repeats) == len(cov) == len(cov_emp)):
        raise ValueError("All inputs must have the same number of N values.")

    if not 0 < quantile_range < 1:
        raise ValueError("quantile_range must be between 0 and 1.")

    order = np.argsort(N)

    N = N[order]
    pf = pf[order]
    cov = cov[order]
    cov_std = cov_std[order]
    cov_emp = cov_emp[order]

    qlo = (1 - quantile_range) / 2
    qhi = 1 - qlo

    lower = np.array([np.quantile(np.asarray(pf_repeats[i]), qlo) for i in order])
    upper = np.array([np.quantile(np.asarray(pf_repeats[i]), qhi) for i in order])

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    blue, orange = colors[:2]

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(width, 2 * width * aspect),
        sharex=True,
        constrained_layout=True,
    )

    # ---- Top: failure probability ----

    ax = axes[0]

    ax.fill_between(
        N,
        lower,
        upper,
        color=blue,
        alpha=band_alpha,
        linewidth=0,
        label=f"{quantile_range:.0%} quantile",
        zorder=1,
    )

    ax.plot(
        N,
        pf,
        color=blue,
        linewidth=linewidth,
        marker="o",
        markersize=markersize,
        markerfacecolor="white",
        markeredgewidth=1.0,
        label="Mean",
        zorder=3,
    )
    ax.ticklabel_format(
        **{
            "axis": "y",
            "style": "sci",
            "scilimits": (0, 0),
            "useMathText": True,
        }
    )
    if pf_ylim is not None:
        axes[0].set_ylim(*pf_ylim)

    if reference_pf is not None:
        ax.axhline(
            reference_pf,
            color="0.45",
            linestyle="--",
            linewidth=0.9,
            label="Reference",
            zorder=2,
        )

    ax.set_ylabel(r"$P_F$", fontsize=fontsize)

    ax.legend(
        loc="upper right",
        fontsize=fontsize - 1,
        frameon=True,
        fancybox=False,
        edgecolor="0.7",
        framealpha=1,
        handlelength=1.6,
        handletextpad=0.4,
        labelspacing=0.25,
        borderpad=0.3,
    )

    # ---- Bottom: CoV comparison ----

    ax = axes[1]

    ax.errorbar(
        N,
        cov,
        yerr=cov_std,
        color=blue,
        linewidth=linewidth,
        marker="o",
        markersize=markersize,
        markerfacecolor="white",
        markeredgewidth=1.0,
        label="Estimated CoV",
    )

    ax.plot(
        N,
        cov_emp,
        color=orange,
        linewidth=linewidth,
        marker="s",
        markersize=markersize,
        markerfacecolor="white",
        markeredgewidth=1.0,
        label="Empirical CoV",
    )

    ax.set_xlabel(r"Number of samples, $N$", fontsize=fontsize)
    ax.set_ylabel(r"$\mathrm{CoV}$", fontsize=fontsize)

    ax.legend(
        loc="best",
        fontsize=fontsize - 1,
        frameon=True,
        fancybox=False,
        edgecolor="0.7",
        framealpha=1,
        handlelength=1.6,
        handletextpad=0.4,
        labelspacing=0.25,
        borderpad=0.3,
    )

    # ---- Common publication styling ----

    for ax in axes:
        ax.tick_params(
            axis="both",
            which="major",
            direction="in",
            top=True,
            right=True,
            labelsize=fontsize - 1,
            width=0.8,
            length=3.5,
        )

        ax.tick_params(
            axis="both",
            which="minor",
            direction="in",
            top=True,
            right=True,
            width=0.6,
            length=2,
        )

        ax.minorticks_on()

        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

    return fig, axes


from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def plot_convergence_comparison(
    studies: dict,
    *,
    panels="both",  # "pf" or "both"
    reference_pf=None,
    quantile_range=0.95,
    pf_ylim=None,
    cov_ylim=None,
    width=3.4,
    aspect=None,
    fontsize=10,
    linewidth=1.0,
    markersize=4.5,
    band_alpha=0.12,
    band_zorder=None,
    filename: str | Path | None = None,
) -> tuple[Figure, np.ndarray]:
    """
    Compare multiple SubsetSimulationNumSamplesConvergence studies.

    Parameters
    ----------
    studies : dict[str, SubsetSimulationNumSamplesConvergence]
        Mapping from method label to completed convergence study.

    panels : {"pf", "both"}
        Whether to show only failure-probability convergence or
        both failure probability and CoV convergence.

    reference_pf : float, optional
        Reference failure probability.

    quantile_range : float
        Central empirical quantile interval across repeats.

    Notes
    -----
    Assumes each study result has a `pf` attribute containing
    the individual repeat-level failure-probability estimates.
    Change `result.pf` below if your attribute has another name.
    """

    if panels not in ("pf", "both"):
        raise ValueError("panels must be 'pf' or 'both'.")

    if not 0 < quantile_range < 1:
        raise ValueError("quantile_range must lie between 0 and 1.")

    if not studies:
        raise ValueError("Provide at least one convergence study.")

    n_panels = 1 if panels == "pf" else 2

    if aspect is None:
        aspect = 0.75 if n_panels == 1 else 1.35

    fig, axes = plt.subplots(
        n_panels,
        1,
        figsize=(width, width * aspect),
        sharex=n_panels > 1,
        constrained_layout=True,
        squeeze=False,
    )
    axes = axes[:, 0]

    ax_pf = axes[0]
    ax_cov = axes[1] if n_panels == 2 else None

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    markers = ["o", "s", "^", "D", "v", "P", "X", "h"]

    qlo = (1 - quantile_range) / 2
    qhi = 1 - qlo

    method_handles = []

    if not isinstance(band_alpha, dict):
        band_alpha = {label: band_alpha for label in studies}

    for i, (label, study) in enumerate(studies.items()):
        if study.results is None:
            raise ValueError(f"Study '{label}' has no results.")

        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]

        N = np.asarray(study.num_samples, dtype=float)
        order = np.argsort(N)
        N = N[order]

        pf = np.asarray(study.pf_means, dtype=float)[order]

        pf_repeats = [np.asarray(study.results[j].pf, dtype=float) for j in order]

        lower = np.array([np.quantile(values, qlo) for values in pf_repeats])
        upper = np.array([np.quantile(values, qhi) for values in pf_repeats])

        # Failure-probability quantile interval.
        ax_pf.fill_between(
            N,
            lower,
            upper,
            color=color,
            alpha=band_alpha.get(label, 0.1),
            linewidth=0,
            zorder=(band_zorder or {}).get(label, 1),
        )

        # Mean failure probability.
        ax_pf.plot(
            N,
            pf,
            color=color,
            linewidth=linewidth,
            marker=marker,
            markersize=markersize,
            markerfacecolor="white",
            markeredgewidth=1.0,
            zorder=3,
        )

        if ax_cov is not None:
            cov_mean = np.asarray(study.cov_means, dtype=float)[order]

            cov_emp = np.asarray(study.cov_empiricals, dtype=float)[order]

            # Mean internally estimated CoV.
            ax_cov.plot(
                N,
                cov_mean,
                color=color,
                linestyle="--",
                linewidth=linewidth,
                marker=marker,
                markersize=markersize,
                markerfacecolor="white",
                markeredgewidth=1.0,
            )

            # Empirical CoV across independent repeats.
            ax_cov.plot(
                N,
                cov_emp,
                color=color,
                linestyle="-",
                linewidth=linewidth,
                marker=marker,
                markersize=markersize,
                markerfacecolor=color,
                markeredgewidth=1.0,
            )

        method_handles.append(
            Line2D(
                [0],
                [0],
                color=color,
                marker=marker,
                markerfacecolor="white",
                linewidth=linewidth,
                markersize=markersize,
                label=label,
            )
        )

    # Reference failure probability.
    if reference_pf is not None:
        ax_pf.axhline(
            reference_pf,
            color="0.4",
            linestyle=":",
            linewidth=0.9,
            zorder=2,
        )

    ax_pf.set_ylabel(r"$P_F$", fontsize=fontsize)
    ax_pf.ticklabel_format(
        axis="y",
        style="sci",
        scilimits=(0, 0),
        useMathText=True,
    )

    if pf_ylim is not None:
        ax_pf.set_ylim(*pf_ylim)

    if ax_cov is not None:
        ax_cov.set_ylabel(r"$\mathrm{CoV}$", fontsize=fontsize)

        if cov_ylim is not None:
            ax_cov.set_ylim(*cov_ylim)

        ax_cov.set_xlabel(
            r"Number of samples, $N$",
            fontsize=fontsize,
        )
    else:
        ax_pf.set_xlabel(
            r"Number of samples, $N$",
            fontsize=fontsize,
        )

    # Method legend on the top panel.
    method_legend = ax_pf.legend(
        handles=method_handles,
        loc="upper right",
        fontsize=fontsize - 1,
        frameon=True,
        fancybox=False,
        edgecolor="0.7",
        framealpha=1.0,
        handlelength=1.6,
        handletextpad=0.4,
        labelspacing=0.25,
        borderpad=0.3,
    )
    method_legend.get_frame().set_linewidth(0.6)

    # Separate legend explaining line styles.
    if ax_cov is not None:
        style_handles = [
            Line2D(
                [0],
                [0],
                color="0.3",
                linestyle="--",
                label="Estimated CoV",
            ),
            Line2D(
                [0],
                [0],
                color="0.3",
                linestyle="-",
                label="Empirical CoV",
            ),
        ]

        style_legend = ax_cov.legend(
            handles=style_handles,
            loc="upper right",
            fontsize=fontsize - 1,
            frameon=True,
            fancybox=False,
            edgecolor="0.7",
            framealpha=1.0,
            handlelength=1.6,
            handletextpad=0.4,
            labelspacing=0.25,
            borderpad=0.3,
        )
        style_legend.get_frame().set_linewidth(0.6)

    # Publication styling.
    for ax in axes:
        ax.tick_params(
            axis="both",
            which="major",
            direction="in",
            top=True,
            right=True,
            labelsize=fontsize - 1,
            width=0.8,
            length=3.5,
        )
        ax.tick_params(
            axis="both",
            which="minor",
            direction="in",
            top=True,
            right=True,
            width=0.6,
            length=2,
        )
        ax.minorticks_on()

        for spine in ax.spines.values():
            spine.set_linewidth(0.8)

    if filename is not None:
        fig.savefig(
            filename,
            dpi=600,
            bbox_inches="tight",
        )

    return fig, axes
