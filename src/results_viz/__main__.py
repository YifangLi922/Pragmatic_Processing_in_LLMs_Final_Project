"""CLI: render the five poster figures from results/main_scoring and
results/human_baseline_core3. Confirmatory set only throughout (figures 1,
2, 3, 4) -- confirmatory and exploratory accuracy are not comparable (see
main_scoring_summary.md), so they never share a figure. Figure 5 is the one
exploratory-derived figure, and is qualitative by construction (n=4
families).

Each figure gets its own subfolder under --output-dir (fig1_condition_accuracy/,
fig2_confusion_grid/, ...), holding both its .png and .pdf.

Usage:
    python -m src.results_viz \\
        --main-scoring-dir results/main_scoring \\
        --human-baseline-dir results/human_baseline_core3 \\
        --output-dir results/figures
"""

import argparse
import csv
import os

from .data import (
    load_by_condition_metric,
    load_condition_accuracy,
    load_confusion_rownorm,
    load_design_gold_following,
    load_human_baseline_comparison,
)
from .figures import (
    plot_ba_ma_scatter,
    plot_condition_accuracy,
    plot_confusion_grid,
    plot_design_gold_following,
    plot_used_target_by_condition,
)


def _read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the five poster figures (PNG @300dpi + PDF).")
    parser.add_argument("--main-scoring-dir", required=True)
    parser.add_argument("--human-baseline-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    condition_accuracy = load_condition_accuracy(
        _read_csv(os.path.join(args.main_scoring_dir, "condition_accuracy", "condition_accuracy_confirmatory.csv"))
    )
    human_baseline = load_human_baseline_comparison(
        _read_csv(os.path.join(args.human_baseline_dir, "human_baseline_comparison.csv"))
    )
    confusion_by_model = load_confusion_rownorm(
        _read_csv(os.path.join(args.main_scoring_dir, "confusion_matrices", "confusion_matrix_confirmatory_rownorm.csv"))
    )
    used_target = load_by_condition_metric(
        _read_csv(os.path.join(args.main_scoring_dir, "target_sentence_delta", "used_target_by_model_condition.csv")),
        set_name="confirmatory",
        rate_field="used_target_rate",
        n_field="n_valid_pairs",
    )
    design_gold_following = load_design_gold_following(
        _read_csv(os.path.join(args.main_scoring_dir, "design_gold_following", "design_gold_following_exploratory.csv"))
    )

    def _fig_path(name: str) -> str:
        fig_dir = os.path.join(args.output_dir, name)
        os.makedirs(fig_dir, exist_ok=True)
        return os.path.join(fig_dir, name)

    plot_condition_accuracy(condition_accuracy, human_baseline, _fig_path("fig1_condition_accuracy"))
    plot_confusion_grid(confusion_by_model, _fig_path("fig2_confusion_grid"))
    plot_ba_ma_scatter(condition_accuracy, human_baseline, _fig_path("fig3_ba_vs_ma_scatter"))
    plot_used_target_by_condition(used_target, _fig_path("fig4_used_target_by_condition"))
    plot_design_gold_following(design_gold_following, _fig_path("fig5_design_gold_following"))

    print(f"5 figures (PNG @300dpi + PDF) written to {args.output_dir}/, one subfolder per figure")


if __name__ == "__main__":
    main()
