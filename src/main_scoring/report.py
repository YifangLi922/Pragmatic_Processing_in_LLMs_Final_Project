"""CSV writers + the one markdown summary for main-experiment scoring."""

import csv

from src.diagnostic.metrics import SEMANTIC_LABELS

CONDITION_ACCURACY_FIELDS = [
    "model",
    "n_valid_overall",
    "accuracy_overall",
    "n_valid_bare",
    "accuracy_bare",
    "n_valid_ba",
    "accuracy_ba",
    "n_valid_ma",
    "accuracy_ma",
]

MARGIN_FIELDS = ["margin", "margin_label", "n_items", "n_valid", "accuracy"]
MARGIN_BY_MODEL_FIELDS = ["model", *MARGIN_FIELDS]

USED_TARGET_FIELDS = [
    "set",
    "model",
    "n_valid_pairs",
    "n_used_target",
    "used_target_rate",
    "n_excluded_no_ablation_answer",
]

UPDATE_PRECISION_FIELDS = [
    "set",
    "model",
    "n_valid_raw",
    "accuracy_raw",
    "n_updates",
    "update_precision",
    "n_updates_sensitivity",
    "update_precision_sensitivity",
]

DESIGN_GOLD_FOLLOWING_FIELDS = ["model", "n_shifted_items", "n_matches_design_gold", "design_gold_following_rate"]

USED_TARGET_BY_CONDITION_FIELDS = [
    "set",
    "model",
    "condition",
    "n_valid_pairs",
    "n_used_target",
    "used_target_rate",
    "n_excluded_no_ablation_answer",
]

UPDATE_PRECISION_BY_CONDITION_FIELDS = [
    "set",
    "model",
    "condition",
    "n_valid_raw",
    "accuracy_raw",
    "n_updates",
    "update_precision",
]

PRIOR_CORRECTION_FIELDS = ["set", "model", "condition", "group", "n_items", "accuracy"]


def _write_rows(path: str, fields: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_condition_accuracy(rows: list[dict], path: str) -> None:
    _write_rows(path, CONDITION_ACCURACY_FIELDS, rows)


def write_margin_accuracy(rows: list[dict], path: str) -> None:
    _write_rows(path, MARGIN_FIELDS, rows)


def write_margin_accuracy_by_model(rows: list[dict], path: str) -> None:
    _write_rows(path, MARGIN_BY_MODEL_FIELDS, rows)


def write_used_target(rows: list[dict], path: str) -> None:
    _write_rows(path, USED_TARGET_FIELDS, rows)


def write_update_precision(rows: list[dict], path: str) -> None:
    _write_rows(path, UPDATE_PRECISION_FIELDS, rows)


def write_design_gold_following(rows: list[dict], path: str) -> None:
    _write_rows(path, DESIGN_GOLD_FOLLOWING_FIELDS, rows)


def write_used_target_by_condition(rows: list[dict], path: str) -> None:
    _write_rows(path, USED_TARGET_BY_CONDITION_FIELDS, rows)


def write_update_precision_by_condition(rows: list[dict], path: str) -> None:
    _write_rows(path, UPDATE_PRECISION_BY_CONDITION_FIELDS, rows)


def write_prior_correction(rows: list[dict], path: str) -> None:
    _write_rows(path, PRIOR_CORRECTION_FIELDS, rows)


def write_confusion_variant(matrices_by_model: dict, variant: str, path: str) -> None:
    rows = []
    for model in sorted(matrices_by_model):
        matrix = matrices_by_model[model][variant]
        for gold in SEMANTIC_LABELS:
            rows.append({"model": model, "gold_semantic": gold, **matrix[gold]})
    _write_rows(path, ["model", "gold_semantic", *SEMANTIC_LABELS], rows)


def _fmt_pct(value: float | None) -> str:
    return f"{value:.1%}" if value is not None else "n/a"


def render_summary(
    precondition_ok: bool,
    precondition_detail: str,
    confirmatory_accuracy: list[dict],
    exploratory_accuracy: list[dict],
    margin_accuracy: list[dict],
    used_target_confirmatory: list[dict],
    update_precision_confirmatory: list[dict],
    used_target_exploratory: list[dict],
    update_precision_exploratory: list[dict],
    shortcut_family_count: int,
    confusion_n_scored: dict[str, int],
    design_gold_following: list[dict],
) -> str:
    lines = ["# Main experiment scoring summary", ""]

    lines.append("## Precondition check (main_results vs. ablation_results)")
    lines.append("")
    lines.append("PASS" if precondition_ok else "FAILED")
    lines.append("")
    lines.append(precondition_detail)
    lines.append("")

    lines.append("## 1. Condition accuracy -- confirmatory (60 items)")
    lines.append("")
    lines.append("| model | n_valid | accuracy | bare (n) | ba (n) | ma (n) |")
    lines.append("|---|---|---|---|---|---|")
    for row in confirmatory_accuracy:
        lines.append(
            f"| {row['model']} | {row['n_valid_overall']} | {_fmt_pct(row['accuracy_overall'])} | "
            f"{_fmt_pct(row['accuracy_bare'])} ({row['n_valid_bare']}) | "
            f"{_fmt_pct(row['accuracy_ba'])} ({row['n_valid_ba']}) | "
            f"{_fmt_pct(row['accuracy_ma'])} ({row['n_valid_ma']}) |"
        )
    lines.append("")

    lines.append("## 1. Condition accuracy -- exploratory (18 items, NOT comparable to confirmatory)")
    lines.append("")
    lines.append(
        "Exploratory families have two conditions sharing the same human-majority gold by construction "
        "(that's why they're COLLAPSE, not KEEP) -- a higher accuracy here reflects that structural "
        "baseline, not stronger model performance."
    )
    lines.append("")
    lines.append("| model | n_valid | accuracy | bare (n) | ba (n) | ma (n) |")
    lines.append("|---|---|---|---|---|---|")
    for row in exploratory_accuracy:
        lines.append(
            f"| {row['model']} | {row['n_valid_overall']} | {_fmt_pct(row['accuracy_overall'])} | "
            f"{_fmt_pct(row['accuracy_bare'])} ({row['n_valid_bare']}) | "
            f"{_fmt_pct(row['accuracy_ba'])} ({row['n_valid_ba']}) | "
            f"{_fmt_pct(row['accuracy_ma'])} ({row['n_valid_ma']}) |"
        )
    lines.append("")

    lines.append("## 2. Margin-stratified accuracy -- confirmatory, pooled across models")
    lines.append("")
    lines.append("| margin | n_items | n_valid | accuracy |")
    lines.append("|---|---|---|---|")
    for row in margin_accuracy:
        lines.append(f"| {row['margin_label']} | {row['n_items']} | {row['n_valid']} | {_fmt_pct(row['accuracy'])} |")
    lines.append("")
    lines.append(
        "Per-model breakdown in margin_stratified_accuracy_by_model.csv. Note there are three margin "
        "values in the real data (3:0, 2:1, and 2:0-with-one-abstention), not just the two named in the "
        "request -- all three are reported rather than folding the third into either named bucket."
    )
    lines.append("")

    lines.append("## 3. Target-sentence delta (used_target) and update_precision")
    lines.append("")
    lines.append(
        f"**Note:** the ablation's confirmatory shortcut_risk set has **{shortcut_family_count} families**, "
        "not the 8 mentioned in the request -- verified directly against ablation_item_summary.csv "
        "(F01/F04/F14/F15/F16/F20/F23/F24/F30/F34/F36). Using the verified 11 for the sensitivity column "
        "below rather than silently matching an assumed 8."
    )
    lines.append("")
    lines.append(
        "**used_target denominator is both-answered pairs only.** A model that refused to answer the "
        "ablation (no target sentence) gives no baseline judgment to compare against -- that's excluded "
        "from the denominator entirely (`n_excluded_no_ablation_answer`), not counted as "
        "used_target=True. An earlier version of this table counted it as True, which inflated "
        "gemma-4-31b's and mistral-small-3-24b's rates since they refuse most often in the ablation."
    )
    lines.append("")
    lines.append(
        "**update_precision is not a corrected accuracy.** It's the accuracy *only on the items where "
        "the model changed its answer* once shown the target sentence -- a distinct question (\"when the "
        "model updates on the sentence, is the update usually right?\") reported side by side with raw "
        "accuracy, never as a replacement for it."
    )
    lines.append("")
    lines.append("### confirmatory")
    lines.append("")
    lines.append("| model | n_valid_pairs | used_target_rate | n_excluded_no_ablation_answer |")
    lines.append("|---|---|---|---|")
    for row in used_target_confirmatory:
        lines.append(
            f"| {row['model']} | {row['n_valid_pairs']} | {_fmt_pct(row['used_target_rate'])} | "
            f"{row['n_excluded_no_ablation_answer']} |"
        )
    lines.append("")
    lines.append("| model | accuracy_raw (n) | update_precision (n) | update_precision_sensitivity (n) |")
    lines.append("|---|---|---|---|")
    for row in update_precision_confirmatory:
        lines.append(
            f"| {row['model']} | {_fmt_pct(row['accuracy_raw'])} ({row['n_valid_raw']}) | "
            f"{_fmt_pct(row['update_precision'])} ({row['n_updates']}) | "
            f"{_fmt_pct(row['update_precision_sensitivity'])} ({row['n_updates_sensitivity']}) |"
        )
    lines.append("")

    lines.append("### exploratory (own used_target rate; no sensitivity column -- see note above)")
    lines.append("")
    lines.append("| model | n_valid_pairs | used_target_rate | n_excluded_no_ablation_answer |")
    lines.append("|---|---|---|---|")
    for row in used_target_exploratory:
        lines.append(
            f"| {row['model']} | {row['n_valid_pairs']} | {_fmt_pct(row['used_target_rate'])} | "
            f"{row['n_excluded_no_ablation_answer']} |"
        )
    lines.append("")
    lines.append("| model | accuracy_raw (n) | update_precision (n) |")
    lines.append("|---|---|---|")
    for row in update_precision_exploratory:
        lines.append(
            f"| {row['model']} | {_fmt_pct(row['accuracy_raw'])} ({row['n_valid_raw']}) | "
            f"{_fmt_pct(row['update_precision'])} ({row['n_updates']}) |"
        )
    lines.append("")

    lines.append(
        "used_target_rate and update_precision broken out by condition (bare/ba/ma), one row per "
        "(model, condition), both-answered-pairs denominator per cell: see "
        "`used_target_by_model_condition.csv` and `update_precision_by_model_condition.csv`."
    )
    lines.append("")
    lines.append(
        "**Raw condition accuracy conflates two different things.** Splitting each (model, condition)'s "
        "both-answered items by whether the *ablation* answer already equaled gold (prior_correct) or not "
        "(prior_incorrect), and reporting each group's own main-experiment accuracy separately, is what "
        "actually measures \"used the target sentence to fix a wrong judgment\" -- only the prior_incorrect "
        "group's accuracy answers that question. See `prior_correction_by_model_condition.csv`."
    )
    lines.append("")

    lines.append("## 4. Confusion matrices -- confirmatory, per model")
    lines.append("")
    lines.append("Full 4x4 raw-count and row-normalized matrices are in confusion_matrix_confirmatory_counts.csv "
                  "and confusion_matrix_confirmatory_rownorm.csv (rows=gold_semantic, cols=model choice). "
                  "n_scored (parse_failed=False) per model:")
    lines.append("")
    for model in sorted(confusion_n_scored):
        lines.append(f"- {model}: {confusion_n_scored[model]}")
    lines.append("")

    lines.append("## 5. Design-gold following on shifted exploratory items (qualitative, n=4 families)")
    lines.append("")
    lines.append(
        "For the 4 exploratory families whose \"ma\" condition gold shifted from design (neutral) to "
        "empirical (confirmation) -- F11/F12/F13/F33 -- what fraction of each model's choice on that "
        "condition equals the *design* gold (neutral) rather than the *empirical* gold the model is "
        "actually scored against. F06/F18 are excluded: their \"ma\" gold never shifted, so they can't "
        "speak to this question. Only 4 items -- report as a qualitative pattern, not a statistic."
    )
    lines.append("")
    lines.append("| model | n_shifted_items | n_matches_design_gold | design_gold_following_rate |")
    lines.append("|---|---|---|---|")
    for row in design_gold_following:
        lines.append(
            f"| {row['model']} | {row['n_shifted_items']} | {row['n_matches_design_gold']} | "
            f"{_fmt_pct(row['design_gold_following_rate'])} |"
        )
    lines.append("")

    return "\n".join(lines)
