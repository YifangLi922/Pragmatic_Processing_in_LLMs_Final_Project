"""Rendering layer for the five poster figures. Thin over data.py's pure
shaping -- this is the only file that imports matplotlib. Every figure is
untitled (per the brief, titles live in the write-up) and written as both
PNG (300dpi) and PDF.

Uses the non-interactive Agg backend since this runs headless.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from .style import (  # noqa: E402
    CONDITION_COLORS,
    CONDITION_ORDER,
    MODEL_ORDER,
    NEUTRAL_BAR_COLOR,
    SEMANTIC_LABELS,
    SEMANTIC_ORDER,
    apply_poster_style,
)


def _save(fig, output_path: str) -> None:
    fig.savefig(f"{output_path}.png", dpi=300)
    fig.savefig(f"{output_path}.pdf")
    plt.close(fig)


def _present_models(*data_dicts) -> list[str]:
    present = set()
    for d in data_dicts:
        present |= set(d)
    return [m for m in MODEL_ORDER if m in present]


def plot_condition_accuracy(condition_accuracy: dict, human_baseline: dict, output_path: str) -> None:
    """Figure 1: model x condition accuracy, confirmatory set, with a
    human-reference band per condition spanning the LOO-concordance range.
    """
    apply_poster_style()
    models = _present_models(condition_accuracy)
    n_cond = len(CONDITION_ORDER)
    width = 0.8 / n_cond
    x = list(range(len(models)))

    fig, ax = plt.subplots(figsize=(13, 7.5))

    for condition in CONDITION_ORDER:
        band = human_baseline.get(condition, {})
        if band.get("loo") is not None and band.get("concordance") is not None:
            lo, hi = sorted((band["loo"] * 100, band["concordance"] * 100))
            ax.axhspan(lo, hi, color=CONDITION_COLORS[condition], alpha=0.15, zorder=0)

    for c_idx, condition in enumerate(CONDITION_ORDER):
        positions = [xi + (c_idx - (n_cond - 1) / 2) * width for xi in x]
        values = [(condition_accuracy[m][condition]["accuracy"] or 0) * 100 for m in models]
        ax.bar(positions, values, width=width, color=CONDITION_COLORS[condition], zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, ha="right")
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 100)

    condition_handles = [Patch(facecolor=CONDITION_COLORS[c], label=c) for c in CONDITION_ORDER]
    reference_handle = Patch(facecolor="gray", alpha=0.3, label="human reference range (LOO–concordance)")
    ax.legend(handles=[*condition_handles, reference_handle], loc="lower center", ncol=4, frameon=True)

    fig.tight_layout()
    _save(fig, output_path)


def plot_confusion_grid(confusion_by_model: dict, output_path: str) -> None:
    """Figure 2: 2x3 grid of row-normalized confusion matrices, one per
    model, sharing one colorbar. Rows/cols fixed to
    ASSERT/TENTATIVE/NEUTRAL/DISTRACTOR.
    """
    apply_poster_style()
    models = _present_models(confusion_by_model)
    labels = [SEMANTIC_LABELS[s] for s in SEMANTIC_ORDER]

    fig, axes = plt.subplots(2, 3, figsize=(17, 10.5), gridspec_kw={"wspace": 0.6, "hspace": 0.55})
    axes_flat = axes.ravel()
    im = None

    for ax, model in zip(axes_flat, models):
        model_matrix = confusion_by_model[model]
        matrix = np.array(
            [[model_matrix.get(gold, {}).get(choice) for choice in SEMANTIC_ORDER] for gold in SEMANTIC_ORDER],
            dtype=float,
        )
        im = ax.imshow(matrix, cmap="cividis", vmin=0, vmax=1)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=12)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=12)
        ax.set_title(model, fontsize=15, pad=8)
        for i in range(len(labels)):
            for j in range(len(labels)):
                value = matrix[i, j]
                if np.isnan(value):
                    continue
                color = "white" if value > 0.6 else "black"
                ax.text(j, i, f"{value * 100:.0f}%", ha="center", va="center", color=color, fontsize=12)

    for ax in axes_flat[len(models):]:
        ax.axis("off")

    fig.subplots_adjust(left=0.06, right=0.90, top=0.93, bottom=0.10)
    cbar_ax = fig.add_axes((0.93, 0.15, 0.015, 0.7))
    fig.colorbar(im, cax=cbar_ax, label="row-normalized fraction (gold → model choice)")
    _save(fig, output_path)


def plot_ba_ma_scatter(condition_accuracy: dict, human_baseline: dict, output_path: str) -> None:
    """Figure 3: ba vs. ma accuracy scatter, one point per model, y=x
    reference line, optional dashed human-concordance reference lines. No
    fit line and no correlation coefficient (n=6).
    """
    apply_poster_style()
    models = _present_models(condition_accuracy)

    pad = 4
    fig, ax = plt.subplots(figsize=(7.5, 7.5))
    ax.plot([-pad, 100 + pad], [-pad, 100 + pad], linestyle="--", color="gray", linewidth=1.5, zorder=1, label="y = x")

    for model in models:
        x = (condition_accuracy[model]["ba"]["accuracy"] or 0) * 100
        y = (condition_accuracy[model]["ma"]["accuracy"] or 0) * 100
        ax.scatter(x, y, s=130, color=NEUTRAL_BAR_COLOR, edgecolor="black", linewidth=1, zorder=3)
        ax.annotate(model, (x, y), textcoords="offset points", xytext=(8, 6), fontsize=12)

    ba_concordance = human_baseline.get("ba", {}).get("concordance")
    ma_concordance = human_baseline.get("ma", {}).get("concordance")
    if ba_concordance is not None:
        ax.axvline(ba_concordance * 100, linestyle=":", color=CONDITION_COLORS["ba"], linewidth=1.5,
                   label="human concordance (ba)")
    if ma_concordance is not None:
        ax.axhline(ma_concordance * 100, linestyle=":", color=CONDITION_COLORS["ma"], linewidth=1.5,
                   label="human concordance (ma)")

    # Padded past [0, 100] so a point sitting exactly at 0 or 100 (several
    # models hit 100 on ba or ma) doesn't have its marker clipped by the
    # axes border -- ticks stay pinned to the natural 0/20/.../100 grid.
    ax.set_xlim(-pad, 100 + pad)
    ax.set_ylim(-pad, 100 + pad)
    ax.set_xticks(range(0, 101, 20))
    ax.set_yticks(range(0, 101, 20))
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("ba accuracy (%)")
    ax.set_ylabel("ma accuracy (%)")
    ax.legend(loc="lower right", fontsize=11)

    fig.tight_layout()
    _save(fig, output_path)


def plot_used_target_by_condition(used_target: dict, output_path: str) -> None:
    """Figure 4: used_target rate by model x condition, confirmatory set,
    with n (both-answered pairs) labeled above each bar.
    """
    apply_poster_style()
    models = _present_models({m for (m, _c) in used_target})
    n_cond = len(CONDITION_ORDER)
    width = 0.8 / n_cond
    x = list(range(len(models)))

    fig, ax = plt.subplots(figsize=(13, 7.5))

    for c_idx, condition in enumerate(CONDITION_ORDER):
        positions = [xi + (c_idx - (n_cond - 1) / 2) * width for xi in x]
        cells = [used_target.get((m, condition), {"rate": None, "n": 0}) for m in models]
        values = [(cell["rate"] or 0) * 100 for cell in cells]
        bars = ax.bar(positions, values, width=width, color=CONDITION_COLORS[condition])
        for bar, cell in zip(bars, cells):
            ax.text(
                bar.get_x() + bar.get_width() / 2, bar.get_height() + 2, f"n={cell['n']}",
                ha="center", va="bottom", fontsize=9,
            )

    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, ha="right")
    ax.set_ylabel("used_target rate (%)")
    ax.set_ylim(0, 110)

    condition_handles = [Patch(facecolor=CONDITION_COLORS[c], label=c) for c in CONDITION_ORDER]
    ax.legend(handles=condition_handles, loc="upper right", ncol=3)

    fig.tight_layout()
    _save(fig, output_path)


def plot_design_gold_following(design_gold_following: dict, output_path: str) -> None:
    """Figure 5: design-gold following rate on the shifted exploratory
    items. Deliberately small and visually subordinate to figures 1-4;
    n=4 families is called out prominently since this is qualitative.
    """
    apply_poster_style()
    models = _present_models(design_gold_following)
    values = [(design_gold_following[m]["rate"] or 0) * 100 for m in models]
    y = list(range(len(models)))

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.barh(y, values, color=NEUTRAL_BAR_COLOR, edgecolor="black")
    ax.set_yticks(y)
    ax.set_yticklabels(models, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("design-gold following rate (%)", fontsize=13)

    # Placed outside the data area (reserved right margin) so it can never
    # sit on top of a bar regardless of which bars are long that run.
    fig.subplots_adjust(right=0.68)
    ax.text(
        1.06, 0.5, "n = 4 families,\nqualitative", transform=ax.transAxes, ha="left", va="center",
        fontsize=13, fontweight="bold",
        bbox={"boxstyle": "round", "facecolor": "#F0E442", "alpha": 0.85, "edgecolor": "black"},
    )

    _save(fig, output_path)
