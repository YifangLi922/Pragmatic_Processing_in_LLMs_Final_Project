"""Condition accuracy (task 1) and margin-stratified accuracy (task 2).
Every denominator is parse_failed=False rows only.
"""

CONDITIONS = ("bare", "ba", "ma")

# Human-readable labels for the margins that actually occur in a pool_core3
# (3-member) reference pool -- see frozen_dataset/freeze_report.md for the
# derivation. Any other value is labeled generically rather than crashing.
MARGIN_LABELS = {
    3: "3:0 (unanimous, all 3 cast)",
    2: "2:0 (unanimous, 1 abstention)",
    1: "2:1 (majority, all 3 cast)",
}


def _valid(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["parse_failed"] != "True"]


def _accuracy(rows: list[dict]) -> tuple[int, float | None]:
    valid = _valid(rows)
    n = len(valid)
    if n == 0:
        return 0, None
    n_hit = sum(1 for r in valid if r["hit_gold"] == "True")
    return n, n_hit / n


def condition_accuracy_table(rows: list[dict], set_name: str) -> list[dict]:
    """One row per model: n_valid/accuracy overall + per condition, for the
    given set ("confirmatory" or "exploratory").
    """
    set_rows = [r for r in rows if r["set"] == set_name]
    models = sorted({r["model"] for r in set_rows})

    table = []
    for model in models:
        model_rows = [r for r in set_rows if r["model"] == model]
        n_overall, acc_overall = _accuracy(model_rows)
        row = {"model": model, "n_valid_overall": n_overall, "accuracy_overall": acc_overall}
        for condition in CONDITIONS:
            cond_rows = [r for r in model_rows if r["condition"] == condition]
            n_cond, acc_cond = _accuracy(cond_rows)
            row[f"n_valid_{condition}"] = n_cond
            row[f"accuracy_{condition}"] = acc_cond
        table.append(row)
    return table


def margin_stratified_accuracy(rows: list[dict], margin_lookup: dict[str, int]) -> list[dict]:
    """Pooled across all models: one row per margin value that actually
    occurs among confirmatory items. `rows` must already be filtered to
    set=="confirmatory".
    """
    by_margin: dict[int, list[dict]] = {}
    for r in rows:
        margin = margin_lookup.get(r["item_id"])
        if margin is not None:
            by_margin.setdefault(margin, []).append(r)

    n_items_by_margin: dict[int, set[str]] = {}
    for item_id, margin in margin_lookup.items():
        n_items_by_margin.setdefault(margin, set()).add(item_id)

    table = []
    for margin in sorted(by_margin, reverse=True):
        margin_rows = by_margin[margin]
        n_valid, accuracy = _accuracy(margin_rows)
        table.append(
            {
                "margin": margin,
                "margin_label": MARGIN_LABELS.get(margin, f"margin={margin}"),
                "n_items": len(n_items_by_margin.get(margin, set())),
                "n_valid": n_valid,
                "accuracy": accuracy,
            }
        )
    return table


def margin_stratified_accuracy_by_model(rows: list[dict], margin_lookup: dict[str, int]) -> list[dict]:
    """Same as margin_stratified_accuracy but broken out per model."""
    models = sorted({r["model"] for r in rows})
    table = []
    for model in models:
        model_rows = [r for r in rows if r["model"] == model]
        for stratum in margin_stratified_accuracy(model_rows, margin_lookup):
            table.append({"model": model, **stratum})
    return table
