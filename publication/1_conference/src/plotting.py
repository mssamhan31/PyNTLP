"""Figure generation for the paper (Gold tier).

Fig1 - the problem: one timestamp across days, events mixed into the backbone
Fig2 - positioning: practicality vs physical representativeness
Fig3 - mechanism: how event frequency and event size reshape the across-day
       distribution, and where each rule cuts it
Fig4 - recoverability map over the (p, kappa) grid (full width)
Fig5 - accuracy against kappa and the truncation noise floor (single column)

Fig5 is a COLUMN figure on purpose. A full-width figure becomes a one-column
island between two continuous section breaks; Word balances the two-column run
before each break, so an island that will not fit in what is left of the page
moves on and strands the remainder. A column figure has no island and flows into
exactly that space.

Every figure is authored at its FINAL printed width (one IEEE column or the full
page, per config.FIG_COL_W_IN / FIG_FULL_W_IN) so that whatever inserts it never
has to rescale it. That is why no savefig call passes bbox_inches="tight": tight
bounding boxes crop the canvas to its content, so the saved file comes out
narrower than the width it is placed at and gets scaled back up - silently
changing every type size in the figure. Constrained layout does the same job
without touching the canvas size.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import NullFormatter

import config
import estimators
import synth

UNIT = "kW"

# --- Type sizes ----------------------------------------------------------
# True point sizes at final printed width. IEEE wants figure text no smaller
# than roughly the caption size; 7-8 pt at 3.30"/7.00" is the practical floor.
BASE_FS = 8
LABEL_FS = 8
PANEL_FS = 8
TICK_FS = 7
LEGEND_FS = 7

# --- Okabe-Ito colour-blind-safe palette ---------------------------------
# Each series is distinguished by colour AND marker AND dash pattern, so the
# figures stay readable in greyscale print.
OKABE_ORANGE = "#E69F00"
OKABE_SKY = "#56B4E9"
OKABE_GREEN = "#009E73"
OKABE_BLUE = "#0072B2"
OKABE_VERMILLION = "#D55E00"

TRUE_C = "#000000"          # ground truth is always black
NOISE_FLOOR_C = "#666666"   # analytic reference curves are grey

STYLE = {
    "fixed_q_0.1": dict(color=OKABE_ORANGE, marker="^", ls=(0, (1, 1.2)),
                        label="Fixed $q=0.1$"),
    "fixed_q_0.2": dict(color=OKABE_SKY, marker="s", ls=(0, (4, 1.5)),
                        label="Fixed $q=0.2$"),
    "fixed_q_0.3": dict(color=OKABE_BLUE, marker="v", ls=(0, (5, 1, 1, 1)),
                        label="Fixed $q=0.3$"),
    "estimated_aqf": dict(color=OKABE_VERMILLION, marker="o", ls="-",
                          label="AQF"),
    "oracle_aqf": dict(color=OKABE_GREEN, marker="D", ls=(0, (3, 1, 1, 1, 1, 1)),
                       label="Oracle-$q$"),
}
PLOT_ORDER = ["fixed_q_0.1", "fixed_q_0.2", "fixed_q_0.3", "estimated_aqf", "oracle_aqf"]

# The strongest fixed baseline by mean |R_F - 1| (1.55 vs 2.08 for q=0.2).
# The maps and slice plots compare against this one rather than q=0.2 so the
# method is shown beating the best available alternative, not a soft target.
STRONGEST_FIXED_Q = "fixed_q_0.3"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": BASE_FS,
        "axes.titlesize": BASE_FS,
        "axes.labelsize": LABEL_FS,
        "legend.fontsize": LEGEND_FS,
        "xtick.labelsize": TICK_FS,
        "ytick.labelsize": TICK_FS,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.7,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "lines.linewidth": 1.1,
        "lines.markersize": 3.0,
        "legend.frameon": False,
        "legend.handlelength": 2.6,
        "legend.columnspacing": 1.2,
        "legend.handletextpad": 0.5,
        "figure.dpi": config.FIG_DPI,
    }
)


# =========================================================================
# Helpers
# =========================================================================
def _panel(ax, letter: str, x: float = 0.025, y: float = 0.97) -> None:
    """Panel identifier inside the axes. Figures carry no titles - the caption
    does that job - so (a)/(b)/(c) is how the text refers to a panel."""
    ax.text(x, y, f"({letter})", transform=ax.transAxes, ha="left", va="top",
            fontsize=PANEL_FS, fontweight="bold", zorder=6,
            bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none", alpha=0.75))


def _tag(ax, text: str, x: float = 0.975, y: float = 0.97) -> None:
    """Short parameter tag (e.g. kappa = 3), top-right so it clears panel labels."""
    ax.text(x, y, text, transform=ax.transAxes, ha="right", va="top", fontsize=TICK_FS)


def _save(fig, name: str) -> None:
    """Save at exact canvas size. No bbox_inches - see the module docstring."""
    fig.savefig(config.GOLD_FIGURES_DIR / name, dpi=config.FIG_DPI)
    plt.close(fig)


def _load_gold() -> pd.DataFrame:
    return pd.read_csv(config.GOLD_TABLES_DIR / "recoverability_summary.csv")


def _mark_identifiable(ax, orientation: str = "x", label: bool = False) -> None:
    """Shade / rule the region where Ashman's D clears the identifiability bar.

    This is the region in which the method's own diagnostic says its fit can be
    trusted, so it is where the paper's central claim applies.
    """
    k = config.KAPPA_IDENTIFIABLE
    if orientation == "x":
        ax.axvline(k, color=TRUE_C, ls=(0, (2, 2)), lw=0.8, zorder=1)
        ax.axvspan(k, config.KAPPA_GRID.max() + 0.3, color="0.5", alpha=0.10,
                   lw=0, zorder=0)
        if label:
            ax.text(k + 0.12, 0.965, f"identifiable  $\\hat D \\geq {config.D_THRESH:g}$",
                    transform=ax.get_xaxis_transform(), ha="left", va="top",
                    fontsize=TICK_FS, color="0.25")
    else:
        ax.axhline(k, color=TRUE_C, ls=(0, (2, 2)), lw=0.9, zorder=4)
        if label:
            ax.text(0.30, k + 0.10, f"$\\hat D = {config.D_THRESH:g}$",
                    transform=ax.get_yaxis_transform(), ha="left", va="bottom",
                    fontsize=TICK_FS, color=TRUE_C, zorder=6,
                    bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none",
                              alpha=0.75))


# =========================================================================
# Fig 1 - conceptual decomposition
# =========================================================================
def fig1_decomposition() -> None:
    """The problem, on one scenario: the meter reports only the sum.

    Single panel. The across-day histogram that used to sit here now appears
    three times in the mechanism figure, under different conditions.
    """
    days_df = synth.generate_days(
        p=0.3, kappa=3.0, sigma=config.SIGMA, backbone_b=config.BACKBONE_B,
        days=40, seed=999,
    )
    fig, ax = plt.subplots(figsize=(config.FIG_COL_W_IN, 1.72), layout="constrained")
    ax.plot(days_df["day"], days_df["l"], color=TRUE_C, lw=0.9, label="Observed $L$")
    ax.axhline(config.BACKBONE_B, color=TRUE_C, ls="--", lw=1.0, label="Backbone $B$")
    event_days = days_df[days_df["z"] == 1]
    for _, row in event_days.iterrows():
        ax.vlines(row["day"], config.BACKBONE_B, row["l"], color=OKABE_VERMILLION,
                  alpha=0.45, lw=0.9)
    ax.scatter(event_days["day"], event_days["l"], color=OKABE_VERMILLION, zorder=3,
               s=9, label="Event day")
    ax.set_xlabel("Day index")
    ax.set_ylabel(f"Load ({UNIT})")
    ax.margins(y=0.10)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3, fontsize=LEGEND_FS,
              borderaxespad=0.0)
    _save(fig, "fig1_decomposition.png")


# =========================================================================
# Fig 2 - positioning of the candidate methods
# =========================================================================
def fig2_positioning() -> None:
    """Where each family of methods sits on practicality vs representativeness.

    Hand-authored: this is a positioning argument, not a measurement.
    """
    fig, ax = plt.subplots(figsize=(config.FIG_COL_W_IN, 1.95), layout="constrained")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axvline(0.5, color="0.85", lw=0.8, zorder=0)
    ax.axhline(0.5, color="0.85", lw=0.8, zorder=0)

    # The bottom-right label is right-aligned so it ends beside its own marker
    # instead of drifting toward the middle, where it read as one block with the
    # "Fixed quantile" label.
    points = [
        ("Bottom-up\nappliance model", 0.16, 0.82, "#7B6BA8", (7, -14), "left"),
        ("Single shiftable\nfraction", 0.88, 0.20, OKABE_ORANGE, (-9, -4), "right"),
        ("Fixed\nquantile", 0.52, 0.47, OKABE_SKY, (7, -16), "left"),
        ("AQF\n(this paper)", 0.74, 0.74, OKABE_GREEN, (-34, 9), "left"),
    ]
    for text, x, y, colour, off, ha in points:
        ax.scatter([x], [y], s=42, color=colour, zorder=3, edgecolor="white",
                   linewidth=0.9)
        ax.annotate(text, (x, y), textcoords="offset points", xytext=off,
                    fontsize=TICK_FS, color=TRUE_C, linespacing=1.25, ha=ha)

    ax.set_xlabel("Practical at scale  $\\rightarrow$")
    ax.set_ylabel("Physically representative  $\\rightarrow$")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_color("0.7")
    _save(fig, "fig2_positioning.png")


# =========================================================================
# Fig 3 - mechanism
# =========================================================================
def fig3_mechanism() -> None:
    """How event frequency and event size reshape what the meter records.

    (a) to (b) isolates the effect of event size at fixed frequency; (b) to (c)
    the effect of frequency at fixed size. Drawn from a large sample so the cuts
    show where each rule sits asymptotically, not one draw's sampling noise.
    """
    n_show = 4000
    q_baseline = float(STRONGEST_FIXED_Q.rsplit("_", 1)[1])
    specs = [(0.3, 1.0), (0.3, 3.0), (0.6, 3.0)]

    fig, axes = plt.subplots(1, 3, figsize=(config.FIG_FULL_W_IN, 1.58),
                             layout="constrained")
    drawn = []
    for p, kappa in specs:
        df = synth.generate_days(p, kappa, config.SIGMA, config.BACKBONE_B,
                                 n_show, seed=7)
        drawn.append((p, kappa, df["l"].to_numpy()))
    lo = min(v.min() for _, _, v in drawn)
    hi = max(v.max() for _, _, v in drawn)
    bins = np.linspace(lo, hi, 70)

    for c, (ax, (p, kappa, load)) in enumerate(zip(axes, drawn)):
        ax.hist(load, bins=bins, color="0.82", edgecolor="white", linewidth=0.2,
                density=True)
        b_fixed = estimators.fixed_quantile_backbone(load, q_baseline)
        b_aqf = estimators.fixed_quantile_backbone(load, estimators.aqf_quantile(p, kappa))
        # Staggered widths: the cuts nearly coincide in some panels, and equal
        # widths would hide the one underneath.
        ax.axvline(config.BACKBONE_B, color=TRUE_C, lw=2.2, label="True backbone $B$")
        ax.axvline(b_fixed, color=STYLE[STRONGEST_FIXED_Q]["color"], ls=(0, (4, 1.5)),
                   lw=1.4, label=STYLE[STRONGEST_FIXED_Q]["label"])
        ax.axvline(b_aqf, color=OKABE_VERMILLION, ls="-", lw=0.9, label="AQF $q^*$")
        ax.set_xlim(lo, hi)
        ax.set_yticks([])
        _panel(ax, "abc"[c])
        _tag(ax, f"$p={p:g}$,  $\\kappa={kappa:g}$")
        ax.set_xlabel(f"Load ({UNIT})")
    axes[0].set_ylabel("Density")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside upper center", ncol=3, fontsize=LEGEND_FS)
    _save(fig, "fig3_mechanism.png")


# =========================================================================
# Fig 4 - recoverability map
# =========================================================================
def fig4_recoverability() -> None:
    """Recovery ratio over the (p, kappa) grid: fixed q, AQF, oracle-q."""
    gold = _load_gold()
    panels = [
        (STRONGEST_FIXED_Q, "Best fixed quantile ($q=0.3$)"),
        ("estimated_aqf", "AQF (this paper)"),
        ("oracle_aqf", "Oracle-$q$ (knows true $p,\\kappa$)"),
    ]
    pivots = {v: gold[gold["estimator_variant"] == v]
              .pivot(index="kappa", columns="p", values="r_f_mean").sort_index()
              for v, _ in panels}
    all_vals = np.concatenate([np.log2(p.values).ravel() for p in pivots.values()])
    # R_F reaches 35 in the sparse-event corner; capping the red end at 8 keeps
    # the informative range visible instead of washing it out.
    norm = TwoSlopeNorm(vmin=float(all_vals.min()), vcenter=0.0, vmax=np.log2(8.0))

    fig, axes = plt.subplots(1, 3, figsize=(config.FIG_FULL_W_IN, 1.62), sharey=True,
                             layout="constrained")
    mesh = None
    for i, (ax, (variant, title)) in enumerate(zip(axes, panels)):
        piv = pivots[variant]
        vals = np.log2(piv.values)
        mesh = ax.pcolormesh(piv.columns, piv.index, vals, norm=norm, cmap="RdBu_r",
                             shading="auto", rasterized=True)
        ax.contour(piv.columns, piv.index, vals, levels=[0.0], colors=[TRUE_C],
                   linewidths=1.0)
        _mark_identifiable(ax, orientation="y", label=(i == 0))
        ax.set_xlabel("Event frequency $p$")
        ax.set_title(title, fontsize=TICK_FS, pad=3)
        _panel(ax, "abc"[i])
    axes[0].set_ylabel("$\\kappa = A/\\sigma$")

    ticks_rf = [0.5, 1, 2, 4, 8]
    cbar = fig.colorbar(mesh, ax=axes, fraction=0.030, pad=0.015, extend="max")
    cbar.set_ticks(np.log2(ticks_rf))
    cbar.set_ticklabels([f"{t:g}" for t in ticks_rf])
    cbar.set_label("$R_F$", fontsize=LABEL_FS)
    cbar.ax.tick_params(labelsize=TICK_FS)
    cbar.outline.set_linewidth(0.5)
    _save(fig, "fig4_recoverability_map.png")


def fig5_curves() -> None:
    """Accuracy against kappa, and the noise floor against p - one column.

    Single column on purpose: this figure flows inside the text column instead
    of forming a full-width island, so it fills space an island would strand.
    """
    gold = _load_gold()
    gold = gold.assign(abs_rf_dev=(gold["r_f_mean"] - 1.0).abs())

    fig, axes = plt.subplots(3, 1, figsize=(config.FIG_COL_W_IN, 3.55),
                             layout="constrained")

    for i, (ax, col, how, ylab) in enumerate([
            (axes[0], "abs_rf_dev", "median", "Median $|R_F-1|$"),
            (axes[1], "mae_b_mean", "mean", "Mean $MAE_B$ (" + UNIT + ")")]):
        agg = gold.pivot_table(index="kappa", columns="estimator_variant",
                               values=col, aggfunc=how)
        for variant in PLOT_ORDER:
            st = STYLE[variant]
            ax.plot(agg.index, agg[variant], color=st["color"], marker=st["marker"],
                    ls=st["ls"], label=st["label"])
        _mark_identifiable(ax, orientation="x", label=(i == 0))
        ax.set_yscale("log")
        ax.set_ylabel(ylab)
        ax.set_xlim(config.KAPPA_GRID.min() - 0.2, config.KAPPA_GRID.max() + 0.2)
        ax.margins(y=0.20)
        _panel(ax, "ab"[i])
    axes[1].set_xlabel("$\\kappa = A/\\sigma$")

    ax = axes[2]
    kappa_fixed = 3.0
    for variant in [STRONGEST_FIXED_Q, "estimated_aqf", "oracle_aqf"]:
        sub = gold[(gold["estimator_variant"] == variant)
                   & (np.isclose(gold["kappa"], kappa_fixed))].sort_values("p")
        st = STYLE[variant]
        ax.plot(sub["p"], sub["r_f_mean"], color=st["color"], marker=st["marker"],
                ls=st["ls"])
    p_dense = np.linspace(config.P_GRID.min(), config.P_GRID.max(), 200)
    ax.plot(p_dense,
            1.0 + (1.0 - p_dense) * config.NOISE_FLOOR_PER_DAY / (p_dense * kappa_fixed),
            color=NOISE_FLOOR_C, ls=(0, (1, 1)), lw=1.3, marker="",
            label="Noise floor")
    ax.axhline(1.0, color=TRUE_C, lw=0.7, zorder=1)
    ax.set_yscale("log")
    # This panel spans well under one decade, so matplotlib decides for itself
    # whether to label the minor ticks - and the heuristic differs by version,
    # which crowds the axis with overlapping "2x10^0"-style labels. Suppress them
    # explicitly so the panel renders identically whatever matplotlib is installed.
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel("Event frequency $p$")
    ax.set_ylabel("$R_F$")
    ax.margins(y=0.18)
    # Tag sits left of centre: the legend occupies the upper right of this panel.
    _tag(ax, f"$\\kappa={kappa_fixed:g}$", x=0.22)
    _panel(ax, "c")
    ax.legend(loc="upper right", fontsize=LEGEND_FS - 0.5)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside upper center", ncol=3, fontsize=LEGEND_FS - 0.5)
    _save(fig, "fig5_curves.png")


# =========================================================================
FIGURES = [
    ("fig1_decomposition.png", config.FIG_COL_W_IN, fig1_decomposition),
    ("fig2_positioning.png", config.FIG_COL_W_IN, fig2_positioning),
    ("fig3_mechanism.png", config.FIG_FULL_W_IN, fig3_mechanism),
    ("fig4_recoverability_map.png", config.FIG_FULL_W_IN, fig4_recoverability),
    ("fig5_curves.png", config.FIG_COL_W_IN, fig5_curves),
]


def make_all_figures() -> None:
    config.ensure_dirs()
    for _, _, fn in FIGURES:
        fn()
    print(f"Figures written to {config.GOLD_FIGURES_DIR}")


def check_widths() -> bool:
    """Assert every PNG is exactly its intended printed width.

    If this fails, Word will rescale the image on insert and the carefully set
    point sizes in the figure will not be the sizes that reach the page.
    """
    from PIL import Image

    ok = True
    for name, width_in, _ in FIGURES:
        path = config.GOLD_FIGURES_DIR / name
        expected = round(width_in * config.FIG_DPI)
        with Image.open(path) as im:
            actual = im.size[0]
        flag = "OK " if actual == expected else "BAD"
        ok &= actual == expected
        print(f"  {flag} {name:32s} {actual:5d} px (expected {expected})")
    return ok


if __name__ == "__main__":
    make_all_figures()
    check_widths()
