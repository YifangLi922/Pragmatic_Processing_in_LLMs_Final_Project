"""Loaders + the precondition check the user asked for before computing
anything comparing main_results to the ablation: same model roster, same
item set, and the same gold_letter per item in both (a proxy for "the same
option order/shuffle" -- gold_letter's position encodes exactly that, and
both files were built from the same frozen CSVs via the same loader, so a
mismatch here would mean something upstream drifted between the two runs).
"""

import csv


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_margin_lookup(frozen_dataset_path: str) -> dict[str, int]:
    """item_id -> margin, confirmatory set only (frozen_dataset.csv)."""
    return {row["item_id"]: int(row["margin"]) for row in read_csv(frozen_dataset_path)}


def load_confirmatory_shortcut_families(ablation_item_summary_path: str) -> set[str]:
    """family_ids with shortcut_risk=True in the confirmatory set, per the
    ablation's own item summary -- not hardcoded, so it can't silently drift
    from whatever the ablation actually found.
    """
    rows = read_csv(ablation_item_summary_path)
    return {
        row["family_id"] for row in rows if row["set"] == "confirmatory" and row["shortcut_risk"] == "True"
    }


class PreconditionError(Exception):
    pass


def check_preconditions(main_rows: list[dict], ablation_rows: list[dict]) -> None:
    """Raises PreconditionError with a full explanation if models, items, or
    gold_letter (option-order proxy) don't match between the two runs.
    Never silently computes a delta on top of a mismatch.
    """
    problems = []

    main_models = {r["model"] for r in main_rows}
    ablation_models = {r["model"] for r in ablation_rows}
    if main_models != ablation_models:
        problems.append(
            f"model sets differ: main only={main_models - ablation_models}, "
            f"ablation only={ablation_models - main_models}"
        )

    main_items = {r["item_id"] for r in main_rows}
    ablation_items = {r["item_id"] for r in ablation_rows}
    if main_items != ablation_items:
        problems.append(
            f"item sets differ: main only={main_items - ablation_items}, "
            f"ablation only={ablation_items - main_items}"
        )

    main_gold = {r["item_id"]: r["gold_letter"] for r in main_rows}
    ablation_gold = {r["item_id"]: r["gold_letter"] for r in ablation_rows}
    mismatched = [
        item_id for item_id in (main_gold.keys() & ablation_gold.keys())
        if main_gold[item_id] != ablation_gold[item_id]
    ]
    if mismatched:
        problems.append(f"gold_letter (option-order proxy) differs on {len(mismatched)} items: {mismatched[:10]}")

    if problems:
        raise PreconditionError(
            "main_results and ablation_results are not comparable -- refusing to compute a delta:\n"
            + "\n".join(f"- {p}" for p in problems)
        )
