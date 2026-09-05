"""Readers for the pool_sensitivity_output/ CSVs this freeze step joins
against. Kept separate from build.py so the join logic is testable against
plain dicts without touching the filesystem.
"""

import csv


def read_grid(path: str) -> dict[str, dict]:
    """family_id -> {"core3_class": str, "stable_keep_all_pools": bool}"""
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["family_id"]: {
                "core3_class": row["core3_class"],
                "stable_keep_all_pools": row["stable_keep_all_pools"] == "True",
            }
            for row in csv.DictReader(f)
        }


def read_empirical_gold(path: str) -> dict[tuple[str, str], dict]:
    """(family_id, condition) -> {"gold_semantic": str, "gold_shifted": bool, "margin": int}.
    Families excluded from this file (EXCLUDE_BROKEN under core3) simply
    have no key here -- callers must not fall back to a default for them.
    """
    with open(path, newline="", encoding="utf-8") as f:
        return {
            (row["family_id"], row["condition"]): {
                "gold_semantic": row["majority_label"],
                "gold_shifted": row["gold_shifted"] == "True",
                "margin": int(row["margin"]),
            }
            for row in csv.DictReader(f)
        }


def read_core3_collapse_pairs(path: str) -> dict[str, dict]:
    """family_id -> {"collapse_pair": str, "collapse_label": str}, core3 rows only."""
    with open(path, newline="", encoding="utf-8") as f:
        return {
            row["family_id"]: {"collapse_pair": row["collapse_pair"], "collapse_label": row["collapse_label"]}
            for row in csv.DictReader(f)
            if row["pool"] == "core3"
        }


def read_gold_shifted(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
