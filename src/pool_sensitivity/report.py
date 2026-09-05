"""CSV writers for the pool-sensitivity outputs (spec section 8). Thin,
dumb serialization layer -- no logic lives here.
"""

import csv


def _write_rows(path: str, fieldnames: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_pool_sensitivity_grid(rows: list[dict], path: str) -> None:
    _write_rows(
        path,
        [
            "family_id",
            "core3_class",
            "econ_class",
            "bwl_class",
            "all5_class",
            "stable_keep_all_pools",
            "family_gold_shifted",
            "core3_class_detail",
        ],
        rows,
    )


def write_collapse_breakdown(rows: list[dict], path: str) -> None:
    _write_rows(path, ["family_id", "pool", "collapse_type", "collapse_pair", "collapse_label"], rows)


def write_empirical_gold_core3(rows: list[dict], path: str) -> None:
    _write_rows(
        path,
        [
            "family_id",
            "condition",
            "has_majority",
            "majority_label",
            "design_gold_label",
            "gold_shifted",
            "majority_count",
            "pool_size",
            "margin",
        ],
        rows,
    )


def write_gold_shifted_families(rows: list[dict], path: str) -> None:
    _write_rows(path, ["family_id", "condition", "design_gold_label", "empirical_gold_label", "margin"], rows)
