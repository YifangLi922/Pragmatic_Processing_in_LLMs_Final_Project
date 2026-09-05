"""CLI: score the main experiment (condition accuracy, margin-stratified
accuracy, target-sentence delta vs. the ablation, confusion matrices).
Tables only -- no plots, no aggregate interpretation beyond what's listed.

Usage:
    python -m src.main_scoring \\
        --main-results main_experiment_output/main_results.csv \\
        --ablation-results ablation_output/ablation_results.csv \\
        --ablation-item-summary ablation_output/ablation_item_summary.csv \\
        --frozen-dataset frozen_dataset/frozen_dataset.csv \\
        --output-dir main_scoring_output
"""

import argparse
import os

from .accuracy import condition_accuracy_table, margin_stratified_accuracy, margin_stratified_accuracy_by_model
from .confusion import confusion_matrices_by_model
from .delta import build_delta_rows, purified_accuracy_comparison, used_target_summary
from .report import (
    render_summary,
    write_condition_accuracy,
    write_confusion_variant,
    write_margin_accuracy,
    write_margin_accuracy_by_model,
    write_purified_accuracy,
    write_used_target,
)
from .sources import PreconditionError, check_preconditions, load_confirmatory_shortcut_families, load_margin_lookup, read_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Score the main experiment against gold + the context-only ablation.")
    parser.add_argument("--main-results", required=True)
    parser.add_argument("--ablation-results", required=True)
    parser.add_argument("--ablation-item-summary", required=True)
    parser.add_argument("--frozen-dataset", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    main_rows = read_csv(args.main_results)
    ablation_rows = read_csv(args.ablation_results)

    try:
        check_preconditions(main_rows, ablation_rows)
        precondition_ok, precondition_detail = True, (
            f"Model rosters match ({len({r['model'] for r in main_rows})} models), item sets match "
            f"({len({r['item_id'] for r in main_rows})} items), and gold_letter agrees on every item -- "
            "main and ablation are comparable item-for-item."
        )
    except PreconditionError as exc:
        precondition_ok, precondition_detail = False, str(exc)
        print(precondition_detail)
        print("\nStopping: refusing to compute the delta analysis on non-comparable data.")
        with open(os.path.join(args.output_dir, "main_scoring_summary.md"), "w", encoding="utf-8") as f:
            f.write(f"# Main experiment scoring summary\n\n## Precondition check FAILED\n\n{precondition_detail}\n")
        return

    # ---- 1. condition accuracy ----
    confirmatory_accuracy = condition_accuracy_table(main_rows, "confirmatory")
    exploratory_accuracy = condition_accuracy_table(main_rows, "exploratory")
    write_condition_accuracy(confirmatory_accuracy, os.path.join(args.output_dir, "condition_accuracy_confirmatory.csv"))
    write_condition_accuracy(exploratory_accuracy, os.path.join(args.output_dir, "condition_accuracy_exploratory.csv"))

    # ---- 2. margin-stratified accuracy (confirmatory only) ----
    margin_lookup = load_margin_lookup(args.frozen_dataset)
    confirmatory_rows = [r for r in main_rows if r["set"] == "confirmatory"]
    margin_accuracy = margin_stratified_accuracy(confirmatory_rows, margin_lookup)
    margin_accuracy_by_model = margin_stratified_accuracy_by_model(confirmatory_rows, margin_lookup)
    write_margin_accuracy(margin_accuracy, os.path.join(args.output_dir, "margin_stratified_accuracy.csv"))
    write_margin_accuracy_by_model(
        margin_accuracy_by_model, os.path.join(args.output_dir, "margin_stratified_accuracy_by_model.csv")
    )

    # ---- 3. target-sentence delta ----
    shortcut_families = load_confirmatory_shortcut_families(args.ablation_item_summary)

    delta_confirmatory = build_delta_rows(main_rows, ablation_rows, "confirmatory")
    delta_exploratory = build_delta_rows(main_rows, ablation_rows, "exploratory")

    used_target_confirmatory = used_target_summary(delta_confirmatory)
    used_target_exploratory = used_target_summary(delta_exploratory)

    raw_confirmatory_by_model = {r["model"]: (r["n_valid_overall"], r["accuracy_overall"]) for r in confirmatory_accuracy}
    raw_exploratory_by_model = {r["model"]: (r["n_valid_overall"], r["accuracy_overall"]) for r in exploratory_accuracy}

    purified_confirmatory = purified_accuracy_comparison(delta_confirmatory, raw_confirmatory_by_model, shortcut_families)
    purified_exploratory = purified_accuracy_comparison(delta_exploratory, raw_exploratory_by_model, None)

    used_target_rows = [{"set": "confirmatory", **r} for r in used_target_confirmatory] + [
        {"set": "exploratory", **r} for r in used_target_exploratory
    ]
    purified_rows = [{"set": "confirmatory", **r} for r in purified_confirmatory] + [
        {"set": "exploratory", **r} for r in purified_exploratory
    ]
    write_used_target(used_target_rows, os.path.join(args.output_dir, "used_target_by_model.csv"))
    write_purified_accuracy(purified_rows, os.path.join(args.output_dir, "purified_accuracy_comparison.csv"))

    # ---- 4. confusion matrices (confirmatory only) ----
    matrices = confusion_matrices_by_model(confirmatory_rows)
    write_confusion_variant(matrices, "raw", os.path.join(args.output_dir, "confusion_matrix_confirmatory_counts.csv"))
    write_confusion_variant(matrices, "rownorm", os.path.join(args.output_dir, "confusion_matrix_confirmatory_rownorm.csv"))

    # ---- summary ----
    summary = render_summary(
        precondition_ok, precondition_detail,
        confirmatory_accuracy, exploratory_accuracy,
        margin_accuracy,
        used_target_confirmatory, purified_confirmatory,
        used_target_exploratory, purified_exploratory,
        len(shortcut_families),
        {model: m["n_scored"] for model, m in matrices.items()},
    )
    with open(os.path.join(args.output_dir, "main_scoring_summary.md"), "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Scoring complete: {len(confirmatory_accuracy)} models, output written to {args.output_dir}")


if __name__ == "__main__":
    main()
