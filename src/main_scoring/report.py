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
    "n_used_target_ablation_parse_failed",
    "n_used_target_real_alternative",
]

PURIFIED_ACCURACY_FIELDS = [
    "set",
    "model",
    "n_valid_raw",
    "accuracy_raw",
    "n_valid_purified",
    "accuracy_purified",
    "n_valid_sensitivity",
    "accuracy_sensitivity",
]


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


def write_purified_accuracy(rows: list[dict], path: str) -> None:
    _write_rows(path, PURIFIED_ACCURACY_FIELDS, rows)


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
    purified_confirmatory: list[dict],
    used_target_exploratory: list[dict],
    purified_exploratory: list[dict],
    shortcut_family_count: int,
    confusion_n_scored: dict[str, int],
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

    lines.append("## 3. Target-sentence delta (used_target)")
    lines.append("")
    lines.append(
        f"**Note:** the ablation's confirmatory shortcut_risk set has **{shortcut_family_count} families**, "
        "not the 8 mentioned in the request -- verified directly against ablation_item_summary.csv "
        "(F01/F04/F14/F15/F16/F20/F23/F24/F30/F34/F36). Using the verified 11 for the sensitivity column "
        "below rather than silently matching an assumed 8."
    )
    lines.append("")
    lines.append("### confirmatory")
    lines.append("")
    lines.append("| model | n_valid_pairs | used_target_rate | (of which: ablation parse-failed / real alternative) |")
    lines.append("|---|---|---|---|")
    for row in used_target_confirmatory:
        lines.append(
            f"| {row['model']} | {row['n_valid_pairs']} | {_fmt_pct(row['used_target_rate'])} | "
            f"{row['n_used_target_ablation_parse_failed']} / {row['n_used_target_real_alternative']} |"
        )
    lines.append("")
    lines.append("| model | accuracy_raw (n) | accuracy_purified (n) | accuracy_sensitivity (n) |")
    lines.append("|---|---|---|---|")
    for row in purified_confirmatory:
        lines.append(
            f"| {row['model']} | {_fmt_pct(row['accuracy_raw'])} ({row['n_valid_raw']}) | "
            f"{_fmt_pct(row['accuracy_purified'])} ({row['n_valid_purified']}) | "
            f"{_fmt_pct(row['accuracy_sensitivity'])} ({row['n_valid_sensitivity']}) |"
        )
    lines.append("")

    lines.append("### exploratory (own used_target rate; no sensitivity column -- see note above)")
    lines.append("")
    lines.append("| model | n_valid_pairs | used_target_rate | (of which: ablation parse-failed / real alternative) |")
    lines.append("|---|---|---|---|")
    for row in used_target_exploratory:
        lines.append(
            f"| {row['model']} | {row['n_valid_pairs']} | {_fmt_pct(row['used_target_rate'])} | "
            f"{row['n_used_target_ablation_parse_failed']} / {row['n_used_target_real_alternative']} |"
        )
    lines.append("")
    lines.append("| model | accuracy_raw (n) | accuracy_purified (n) |")
    lines.append("|---|---|---|")
    for row in purified_exploratory:
        lines.append(
            f"| {row['model']} | {_fmt_pct(row['accuracy_raw'])} ({row['n_valid_raw']}) | "
            f"{_fmt_pct(row['accuracy_purified'])} ({row['n_valid_purified']}) |"
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

    return "\n".join(lines)
