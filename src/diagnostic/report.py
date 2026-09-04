"""CSV writers for the diagnostic (spec section 9's file list + section 10's
item-level schema). Kept separate from metrics.py so the aggregation logic
stays pure/testable and this stays a thin, dumb serialization layer.
"""

import csv

from .metrics import ALL_SLICES, SEMANTIC_LABELS


def _write_rows(path: str, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_condition_summary(rows: list[dict], path: str) -> None:
    _write_rows(path, ["condition", "total_n", "reference_n", "coverage", "agreement_n", "agreement_rate"], rows)


def write_reference_marginals(rows: list[dict], path: str) -> None:
    _write_rows(path, ["condition", *SEMANTIC_LABELS, "reference_valid_n"], rows)


def write_disagreement_directions(rows: list[dict], path: str) -> None:
    _write_rows(
        path,
        ["condition", "reference_label", "target_label", "count", "share_among_disagreements", "within_reference_rate", "low_n"],
        rows,
    )


def write_confusion_variant(matrices_by_condition: dict, variant: str, path_for_condition) -> None:
    """`variant` is "raw" or "rownorm". Writes one CSV per condition (incl.
    overall) using path_for_condition(condition) -> filepath.
    """
    for condition in ALL_SLICES:
        matrix = matrices_by_condition[condition][variant]
        rows = [{"reference_label": ref, **matrix[ref]} for ref in SEMANTIC_LABELS]
        _write_rows(path_for_condition(condition), ["reference_label", *SEMANTIC_LABELS], rows)


def write_item_level(records: list[dict], reference_pool: list[str], path: str) -> None:
    ref_cols = []
    for rid in reference_pool:
        ref_cols.append(f"{rid}_semantic")
        ref_cols.append(f"{rid}_no_option_flag")
    fieldnames = [
        "family_id",
        "item_id",
        "condition",
        *[f"{rid}_semantic" for rid in reference_pool],
        "reference_label",
        "reference_valid",
        "target_semantic",
        "agree",
        "disagreement_direction",
        "target_naturalness",
        "target_hesitation",
        "target_no_option_flag",
        *[f"{rid}_no_option_flag" for rid in reference_pool],
    ]
    _write_rows(path, fieldnames, records)


def write_cross_annotator_summary(rows: list[dict], path: str) -> None:
    fieldnames = [
        "annotator",
        "mode",
        "bare_cov",
        "bare_agr",
        "ba_cov",
        "ba_agr",
        "ma_cov",
        "ma_agr",
        "overall_cov",
        "overall_agr",
    ]
    _write_rows(path, fieldnames, rows)
