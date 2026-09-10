"""Shared style constants for the five poster figures: fixed model/condition/
semantic ordering (must be identical across every figure) and a colorblind-
safe palette (Okabe-Ito). No titles are set here -- per the report brief,
every figure's title lives in the write-up, not on the image.
"""

MODEL_ORDER = [
    "deepseek-r1-0528",
    "deepseek-v3",
    "gemini-3-flash-preview",
    "gemma-4-31b",
    "mistral-small-3-24b",
    "qwen3-next-80b",
]

CONDITION_ORDER = ["bare", "ba", "ma"]

# Okabe-Ito colorblind-safe palette, one color per condition -- reused (same
# color, low alpha) for that condition's human-reference band in figure 1.
CONDITION_COLORS = {
    "bare": "#0072B2",  # blue
    "ba": "#E69F00",  # orange
    "ma": "#009E73",  # bluish green
}

# Row/column order for the confusion-matrix heatmaps and the label text
# shown on them (data columns are statement/confirmation/neutral/distractor
# -- SEMANTIC_ORDER below is deliberately in that exact order so no
# reindexing is needed anywhere the CSVs are read).
SEMANTIC_ORDER = ["statement", "confirmation", "neutral", "distractor"]
SEMANTIC_LABELS = {
    "statement": "ASSERT",
    "confirmation": "TENTATIVE",
    "neutral": "NEUTRAL",
    "distractor": "DISTRACTOR",
}

NEUTRAL_BAR_COLOR = "#56B4E9"  # sky blue, single-series figures (fig 5)


def apply_poster_style() -> None:
    """Poster-legible defaults: no titles are set anywhere (kept in the
    write-up per the brief), so this only needs to cover axis/tick/legend
    text sizes and line weights.
    """
    import matplotlib

    matplotlib.rcParams.update(
        {
            "font.size": 14,
            "axes.labelsize": 16,
            "axes.titlesize": 16,
            "xtick.labelsize": 13,
            "ytick.labelsize": 13,
            "legend.fontsize": 12,
            "figure.dpi": 100,
            "axes.linewidth": 1.2,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "savefig.bbox": "tight",
        }
    )
