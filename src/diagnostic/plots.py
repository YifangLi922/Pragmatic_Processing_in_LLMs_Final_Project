"""Confusion-matrix heatmaps for the diagnostic (spec section 9's .png files).
Non-interactive Agg backend, same convention as src/stats/plots.py -- this
runs headless.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from .metrics import SEMANTIC_LABELS  # noqa: E402


def plot_confusion_heatmap(raw_matrix: dict[str, dict[str, int]], title: str, output_path: str) -> None:
    matrix = [[raw_matrix[ref][tgt] for tgt in SEMANTIC_LABELS] for ref in SEMANTIC_LABELS]
    max_val = max((max(row) for row in matrix), default=0) or 1

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    im = ax.imshow(matrix, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(SEMANTIC_LABELS)), labels=SEMANTIC_LABELS, rotation=30, ha="right")
    ax.set_yticks(range(len(SEMANTIC_LABELS)), labels=SEMANTIC_LABELS)
    ax.set_xlabel("target's answer")
    ax.set_ylabel("reference-pool majority")
    ax.set_title(title)
    for i in range(len(SEMANTIC_LABELS)):
        for j in range(len(SEMANTIC_LABELS)):
            ax.text(
                j, i, matrix[i][j], ha="center", va="center",
                color="white" if matrix[i][j] > max_val / 2 else "black",
            )
    fig.colorbar(im, ax=ax, label="count")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
