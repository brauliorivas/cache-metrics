"""
plots.py — CDF and Boxplot utilities
Each function takes an iterable of numbers, a title, and an axis label,
and writes a clean, human-readable SVG (or PNG fallback) to disk.
"""

from pathlib import Path
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
matplotlib.use("Agg")          # headless — no display needed

# ── shared palette ────────────────────────────────────────────────────────────
BG = "#F7F7F9"
GRID = "#E2E2EA"
ACCENT = "#4C72B0"   # steel-blue  (main line / box)
ACCENT2 = "#DD8452"   # warm-orange (median)
ACCENT3 = "#55A868"   # sage-green  (Q1 / Q3)
TEXT = "#2D2D3A"
LIGHT_TXT = "#7A7A8C"

_COMMON = dict(
    figure_facecolor=BG,
    axes_facecolor=BG,
    text_color=TEXT,
    font_family="DejaVu Sans",
)

# ── downsampling ──────────────────────────────────────────────────────────────
_CDF_MAX_PTS = 2_000   # more than enough for a smooth step curve on screen
_BOXPLOT_MAX_PTS = 5_000   # outlier scatter; box stats are always exact


def _downsample_cdf(arr_sorted: np.ndarray, max_pts: int = _CDF_MAX_PTS):
    """
    Reduce a sorted array to at most *max_pts* evenly-spaced indices.
    The first and last points are always kept so the curve reaches 0 % and 100 %.
    Statistics (percentiles) are always computed on the FULL array — only the
    plotted x/y vectors are thinned.
    """
    n = len(arr_sorted)
    if n <= max_pts:
        return arr_sorted, np.arange(n)
    idx = np.unique(np.round(np.linspace(0, n - 1, max_pts)).astype(int))
    return arr_sorted[idx], idx


def _downsample_scatter(arr: np.ndarray, max_pts: int = _BOXPLOT_MAX_PTS):
    """
    Random subsample for outlier dots in the boxplot.
    Box / whisker stats are computed on the full array first.
    """
    if len(arr) <= max_pts:
        return arr
    rng = np.random.default_rng(0)
    return rng.choice(arr, size=max_pts, replace=False)


def _smart_formatter(ax, axis="x"):
    """
    Replace huge/tiny raw numbers with tidy scientific notation
    only when the range demands it; otherwise use compact plain numbers.
    """
    axis_obj = ax.xaxis if axis == "x" else ax.yaxis
    axis_obj.set_major_formatter(
        ticker.FuncFormatter(
            lambda v, _: (
                f"{v:.3g}"          # e.g.  1.23e+07  →  1.23e+07
            )
        )
    )
    # rotate x labels if they might overlap
    if axis == "x":
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9)


# ── CDF ───────────────────────────────────────────────────────────────────────

def plot_cdf(
    data,
    title: str,
    axis_label: str,
    output_path: str = "cdf.svg",
) -> Path:
    """
    Plot the empirical CDF of *data*.

    Parameters
    ----------
    data        : list / array of numbers
    title       : chart title
    axis_label  : label for the horizontal axis (the data dimension)
    output_path : where to save the file (.svg preferred, .png also works)

    Returns
    -------
    pathlib.Path of the saved file
    """
    arr = np.sort(np.asarray(data, dtype=float))
    n = len(arr)
    y_full = np.arange(1, n + 1) / n * 100   # percentages for the full array

    # downsample for plotting only — stats stay exact
    arr_plot, idx_plot = _downsample_cdf(arr)
    y_plot = y_full[idx_plot]

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # ── shaded area under the curve ──────────────────────────────────────────
    ax.fill_between(arr_plot, y_plot, alpha=0.12, color=ACCENT, step="post")

    # ── main CDF step line ───────────────────────────────────────────────────
    ax.step(arr_plot, y_plot, where="post", color=ACCENT, linewidth=2.2, label="CDF")

    # ── quartile markers ─────────────────────────────────────────────────────
    for pct, label, color in [
        (25, "Q1 (25 %)", ACCENT3),
        (50, "Median", ACCENT2),
        (75, "Q3 (75 %)", ACCENT3),
    ]:
        xv = float(np.percentile(arr, pct))
        ax.axhline(pct, color=color, linestyle="--", linewidth=1.2, alpha=0.7)
        ax.axvline(xv, color=color, linestyle=":", linewidth=1.2, alpha=0.7)
        ax.annotate(
            f"{label}\n{xv:.3g}",
            xy=(xv, pct),
            xytext=(8, 6),
            textcoords="offset points",
            fontsize=8,
            color=color,
            bbox=dict(boxstyle="round,pad=0.25", fc=BG, ec=color, lw=0.8, alpha=0.85),
        )

    # ── axes / grid ──────────────────────────────────────────────────────────
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:.0f} %"))
    ax.set_ylabel("Cumulative percentage", fontsize=11, color=TEXT, labelpad=10)
    ax.set_xlabel(axis_label, fontsize=11, color=TEXT, labelpad=8)

    _smart_formatter(ax, axis="x")

    ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
    ax.grid(axis="x", color=GRID, linewidth=0.5, linestyle=":", zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=LIGHT_TXT)

    # ── title ─────────────────────────────────────────────────────────────────
    ax.set_title(title, fontsize=14, fontweight="bold", color=TEXT, pad=14)

    fig.tight_layout()
    out = Path(output_path)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"CDF saved → {out.resolve()}")
    return out


# ── Boxplot ───────────────────────────────────────────────────────────────────

def plot_boxplot(
    data,
    title: str,
    axis_label: str,
    output_path: str = "boxplot.svg",
) -> Path:
    """
    Plot a horizontal boxplot with Q1 / Median / Q3 annotations.

    Parameters
    ----------
    data        : list / array of numbers
    title       : chart title
    axis_label  : label for the horizontal axis (the data dimension)
    output_path : where to save the file (.svg preferred, .png also works)

    Returns
    -------
    pathlib.Path of the saved file
    """
    arr = np.asarray(data, dtype=float)
    n = len(arr)
    q1, median, q3 = np.percentile(arr, [25, 50, 75])
    iqr = q3 - q1
    whisker_lo = arr[arr >= q1 - 1.5 * iqr].min()
    whisker_hi = arr[arr <= q3 + 1.5 * iqr].max()

    # downsample for rendering only; stats above are from the full array
    arr_plot = _downsample_scatter(arr)

    fig, ax = plt.subplots(figsize=(9, 3.6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    # ── draw the box — let matplotlib use the subsampled array for dots,
    #    but override the computed stats with the exact full-data values ──────
    bp = ax.boxplot(
        arr_plot,
        vert=False,
        patch_artist=True,
        widths=0.45,
        flierprops=dict(
            marker="o", markerfacecolor=ACCENT, markersize=4,
            linestyle="none", markeredgecolor=ACCENT, alpha=0.5
        ),
        medianprops=dict(color=ACCENT2, linewidth=2.5),
        boxprops=dict(facecolor=ACCENT + "30", edgecolor=ACCENT, linewidth=1.5),
        whiskerprops=dict(color=ACCENT, linewidth=1.4, linestyle="--"),
        capprops=dict(color=ACCENT, linewidth=1.8),
    )

    y_center = 1   # single box sits at y = 1

    # ── Q1 / Median / Q3 annotations ─────────────────────────────────────────
    for xv, label, color, va in [
        (q1, f"Q1\n{q1:.3g}", ACCENT3, "bottom"),
        (median, f"Median\n{median:.3g}", ACCENT2, "top"),
        (q3, f"Q3\n{q3:.3g}", ACCENT3, "bottom"),
    ]:
        ax.axvline(xv, color=color, linewidth=1.1, linestyle=":", alpha=0.7, zorder=2)
        offset = 10 if va == "bottom" else -10
        ax.annotate(
            label,
            xy=(xv, y_center),
            xytext=(0, offset + (18 if va == "bottom" else -18)),
            textcoords="offset points",
            ha="center",
            va="bottom" if va == "bottom" else "top",
            fontsize=9,
            color=color,
            fontweight="semibold",
            bbox=dict(boxstyle="round,pad=0.3", fc=BG, ec=color, lw=0.8, alpha=0.9),
            arrowprops=dict(arrowstyle="-", color=color, lw=0.8),
        )

    # ── axes / grid ──────────────────────────────────────────────────────────
    ax.set_yticks([])                   # single box — no y-axis needed
    ax.set_xlabel(axis_label, fontsize=11, color=TEXT, labelpad=8)

    _smart_formatter(ax, axis="x")

    ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=LIGHT_TXT)

    # small stat summary in the top-right corner
    stats_txt = (
        f"n = {n:,}   "
        f"min = {arr.min():.3g}   "
        f"max = {arr.max():.3g}   "
        f"IQR = {iqr:.3g}"
    )
    ax.text(
        0.99, 0.97, stats_txt,
        transform=ax.transAxes,
        ha="right", va="top",
        fontsize=8, color=LIGHT_TXT,
    )

    ax.set_title(title, fontsize=14, fontweight="bold", color=TEXT, pad=14)

    fig.tight_layout()
    out = Path(output_path)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Boxplot saved → {out.resolve()}")
    return out
