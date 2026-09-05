"""Task 4: per-model confusion matrix on the confirmatory set (rows=gold
semantic, cols=model's parsed choice). Reuses the label set/order from
src.diagnostic.metrics rather than redefining the same four strings again.
"""

from src.diagnostic.metrics import SEMANTIC_LABELS


def confusion_matrices_by_model(rows: list[dict]) -> dict[str, dict]:
    """`rows` should already be filtered to set=="confirmatory". Returns
    {model: {"raw": {gold: {choice: n}}, "rownorm": {...}, "n_scored": int}}.
    parse_failed rows are excluded (no column to place them in).
    """
    models = sorted({r["model"] for r in rows})
    result = {}
    for model in models:
        scored = [r for r in rows if r["model"] == model and r["parse_failed"] != "True"]
        raw = {gold: {choice: 0 for choice in SEMANTIC_LABELS} for gold in SEMANTIC_LABELS}
        for r in scored:
            gold = r["gold_semantic"]
            choice = r["parsed_choice_semantic"]
            if gold in raw and choice in raw[gold]:
                raw[gold][choice] += 1
        rownorm = {}
        for gold in SEMANTIC_LABELS:
            row_total = sum(raw[gold].values())
            rownorm[gold] = {choice: (raw[gold][choice] / row_total if row_total else None) for choice in SEMANTIC_LABELS}
        result[model] = {"raw": raw, "rownorm": rownorm, "n_scored": len(scored)}
    return result
