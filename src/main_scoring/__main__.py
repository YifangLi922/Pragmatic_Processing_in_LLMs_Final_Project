"""CLI: score the main experiment (condition accuracy, margin-stratified
accuracy, target-sentence delta vs. the ablation, confusion matrices).
Tables only -- no plots, no aggregate interpretation beyond what's listed.

--output-dir gets five subfolders (condition_accuracy/,
margin_stratified_accuracy/, target_sentence_delta/, confusion_matrices/,
design_gold_following/), one per numbered section below, plus
main_scoring_summary.md at its top level.

Usage:
    python -m src.main_scoring \\
        --main-results intermediate_outputs/main_experiment/main_results.csv \\
        --ablation-results intermediate_outputs/ablation/ablation_results.csv \\
        --ablation-item-summary intermediate_outputs/ablation/ablation_item_summary.csv \\
        --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \\
        --frozen-exploratory intermediate_outputs/frozen_dataset/frozen_exploratory.csv \\
        --output-dir results/main_scoring
"""

import argparse
import os

from .accuracy import condition_accuracy_table, margin_stratified_accuracy, margin_stratified_accuracy_by_model
from .confusion import confusion_matrices_by_model
from .delta import (
    build_delta_rows,
    count_missing_ablation_answer,
    count_missing_ablation_answer_by_condition,
    prior_correction_table,
    update_precision_by_condition,
    update_precision_comparison,
    used_target_summary,
    used_target_summary_by_condition,
)
from .design_gold_following import design_gold_following_table
from .report import (
    render_summary,
    write_condition_accuracy,
    write_confusion_variant,
    write_design_gold_following,
    write_margin_accuracy,
    write_margin_accuracy_by_model,
    write_prior_correction,
    write_update_precision,
    write_update_precision_by_condition,
    write_used_target,
    write_used_target_by_condition,
)
from .sources import (
    PreconditionError,
    check_preconditions,
    load_confirmatory_shortcut_families,
    load_margin_lookup,
    load_shifted_ma_items,
    read_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Score the main experiment against gold + the context-only ablation.")
    parser.add_argument("--main-results", required=True)
    parser.add_argument("--ablation-results", required=True)
    parser.add_argument("--ablation-item-summary", required=True)
    parser.add_argument("--frozen-dataset", required=True)
    parser.add_argument("--frozen-exploratory", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    condition_accuracy_dir = os.path.join(args.output_dir, "condition_accuracy")
    margin_dir = os.path.join(args.output_dir, "margin_stratified_accuracy")
    delta_dir = os.path.join(args.output_dir, "target_sentence_delta")
    confusion_dir = os.path.join(args.output_dir, "confusion_matrices")
    design_gold_dir = os.path.join(args.output_dir, "design_gold_following")
    for subdir in (condition_accuracy_dir, margin_dir, delta_dir, confusion_dir, design_gold_dir):
        os.makedirs(subdir, exist_ok=True)

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
    write_condition_accuracy(confirmatory_accuracy, os.path.join(condition_accuracy_dir, "condition_accuracy_confirmatory.csv"))
    write_condition_accuracy(exploratory_accuracy, os.path.join(condition_accuracy_dir, "condition_accuracy_exploratory.csv"))

    # ---- 2. margin-stratified accuracy (confirmatory only) ----
    margin_lookup = load_margin_lookup(args.frozen_dataset)
    confirmatory_rows = [r for r in main_rows if r["set"] == "confirmatory"]
    margin_accuracy = margin_stratified_accuracy(confirmatory_rows, margin_lookup)
    margin_accuracy_by_model = margin_stratified_accuracy_by_model(confirmatory_rows, margin_lookup)
    write_margin_accuracy(margin_accuracy, os.path.join(margin_dir, "margin_stratified_accuracy.csv"))
    write_margin_accuracy_by_model(
        margin_accuracy_by_model, os.path.join(margin_dir, "margin_stratified_accuracy_by_model.csv")
    )

    # ---- 3. target-sentence delta ----
    shortcut_families = load_confirmatory_shortcut_families(args.ablation_item_summary)

    delta_confirmatory = build_delta_rows(main_rows, ablation_rows, "confirmatory")
    delta_exploratory = build_delta_rows(main_rows, ablation_rows, "exploratory")

    missing_confirmatory = count_missing_ablation_answer(main_rows, ablation_rows, "confirmatory")
    missing_exploratory = count_missing_ablation_answer(main_rows, ablation_rows, "exploratory")

    used_target_confirmatory = used_target_summary(delta_confirmatory, missing_confirmatory)
    used_target_exploratory = used_target_summary(delta_exploratory, missing_exploratory)

    raw_confirmatory_by_model = {r["model"]: (r["n_valid_overall"], r["accuracy_overall"]) for r in confirmatory_accuracy}
    raw_exploratory_by_model = {r["model"]: (r["n_valid_overall"], r["accuracy_overall"]) for r in exploratory_accuracy}

    update_precision_confirmatory = update_precision_comparison(delta_confirmatory, raw_confirmatory_by_model, shortcut_families)
    update_precision_exploratory = update_precision_comparison(delta_exploratory, raw_exploratory_by_model, None)

    used_target_rows = [{"set": "confirmatory", **r} for r in used_target_confirmatory] + [
        {"set": "exploratory", **r} for r in used_target_exploratory
    ]
    update_precision_rows = [{"set": "confirmatory", **r} for r in update_precision_confirmatory] + [
        {"set": "exploratory", **r} for r in update_precision_exploratory
    ]
    write_used_target(used_target_rows, os.path.join(delta_dir, "used_target_by_model.csv"))
    write_update_precision(update_precision_rows, os.path.join(delta_dir, "update_precision_comparison.csv"))

    # ---- 3b. target-sentence delta, split by condition (both-answered pairs only, per cell) ----
    missing_confirmatory_by_condition = count_missing_ablation_answer_by_condition(main_rows, ablation_rows, "confirmatory")
    missing_exploratory_by_condition = count_missing_ablation_answer_by_condition(main_rows, ablation_rows, "exploratory")

    used_target_confirmatory_by_condition = used_target_summary_by_condition(delta_confirmatory, missing_confirmatory_by_condition)
    used_target_exploratory_by_condition = used_target_summary_by_condition(delta_exploratory, missing_exploratory_by_condition)

    def _raw_accuracy_by_condition(accuracy_table: list[dict]) -> dict[tuple[str, str], tuple[int, float | None]]:
        lookup = {}
        for row in accuracy_table:
            for condition in ("bare", "ba", "ma"):
                lookup[(row["model"], condition)] = (row[f"n_valid_{condition}"], row[f"accuracy_{condition}"])
        return lookup

    raw_confirmatory_by_model_condition = _raw_accuracy_by_condition(confirmatory_accuracy)
    raw_exploratory_by_model_condition = _raw_accuracy_by_condition(exploratory_accuracy)

    update_precision_confirmatory_by_condition = update_precision_by_condition(delta_confirmatory, raw_confirmatory_by_model_condition)
    update_precision_exploratory_by_condition = update_precision_by_condition(delta_exploratory, raw_exploratory_by_model_condition)

    used_target_by_condition_rows = [{"set": "confirmatory", **r} for r in used_target_confirmatory_by_condition] + [
        {"set": "exploratory", **r} for r in used_target_exploratory_by_condition
    ]
    update_precision_by_condition_rows = [
        {"set": "confirmatory", **r} for r in update_precision_confirmatory_by_condition
    ] + [{"set": "exploratory", **r} for r in update_precision_exploratory_by_condition]

    write_used_target_by_condition(used_target_by_condition_rows, os.path.join(delta_dir, "used_target_by_model_condition.csv"))
    write_update_precision_by_condition(
        update_precision_by_condition_rows, os.path.join(delta_dir, "update_precision_by_model_condition.csv")
    )

    # ---- 3c. prior-correction: split each (model, condition) by whether the ablation answer already equaled gold ----
    prior_correction_confirmatory = prior_correction_table(delta_confirmatory)
    prior_correction_exploratory = prior_correction_table(delta_exploratory)
    prior_correction_rows = [{"set": "confirmatory", **r} for r in prior_correction_confirmatory] + [
        {"set": "exploratory", **r} for r in prior_correction_exploratory
    ]
    write_prior_correction(prior_correction_rows, os.path.join(delta_dir, "prior_correction_by_model_condition.csv"))

    # ---- 4. confusion matrices (confirmatory only) ----
    matrices = confusion_matrices_by_model(confirmatory_rows)
    write_confusion_variant(matrices, "raw", os.path.join(confusion_dir, "confusion_matrix_confirmatory_counts.csv"))
    write_confusion_variant(matrices, "rownorm", os.path.join(confusion_dir, "confusion_matrix_confirmatory_rownorm.csv"))

    # ---- 5. design-gold following (exploratory shifted "ma" items, qualitative) ----
    shifted_ma_items = load_shifted_ma_items(args.frozen_exploratory)
    exploratory_rows_all = [r for r in main_rows if r["set"] == "exploratory"]
    design_gold_following = design_gold_following_table(exploratory_rows_all, shifted_ma_items)
    write_design_gold_following(design_gold_following, os.path.join(design_gold_dir, "design_gold_following_exploratory.csv"))

    # ---- summary ----
    summary = render_summary(
        precondition_ok, precondition_detail,
        confirmatory_accuracy, exploratory_accuracy,
        margin_accuracy,
        used_target_confirmatory, update_precision_confirmatory,
        used_target_exploratory, update_precision_exploratory,
        len(shortcut_families),
        {model: m["n_scored"] for model, m in matrices.items()},
        design_gold_following,
    )
    with open(os.path.join(args.output_dir, "main_scoring_summary.md"), "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Scoring complete: {len(confirmatory_accuracy)} models, output written to {args.output_dir}")


if __name__ == "__main__":
    main()
