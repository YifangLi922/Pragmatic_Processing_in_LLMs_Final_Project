"""Pure aggregation for the context-only ablation: per-(item,model) result
rows, per-item cross-model summary, and the exploratory-only collapse-pair
modal-choice check. No I/O here -- report.py handles file writing.
"""

import json
from collections import Counter

# "≥2/3 of models" is a proportion of n_models, not a literal "2 of 3" --
# with the main roster's 6 models this means >= 4 of 6. Applied identically
# to both sets (confirmatory/exploratory); only the *interpretation* of a
# high rate differs between them (see the two markdown reports).
SHORTCUT_THRESHOLD = 2 / 3


def load_query_records(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_result_rows(records: list[dict], items_by_id: dict[str, dict]) -> list[dict]:
    """One row per (item, model) query record, joined with that item's gold
    and set. `raw_response` carries the API error message (clearly prefixed)
    when the call itself failed, rather than silently leaving it blank.
    """
    rows = []
    for record in records:
        item = items_by_id[record["item_id"]]
        parsed_letter = record["model_answer_letter"]
        raw_response = record["raw_response"] if not record["error"] else f"[ERROR] {record['error']}"
        rows.append(
            {
                "set": item["set"],
                "family_id": item["family_id"],
                "item_id": item["item_id"],
                "condition": item["particle_condition"],
                "model": record["model_name"],
                "raw_response": raw_response,
                "parsed_choice_letter": parsed_letter,
                "parsed_choice_semantic": record["model_answer_semantic"],
                "gold_letter": item["gold_letter"],
                "gold_semantic": item["gold_semantic"],
                "hit_gold": parsed_letter == item["gold_letter"],
                "parse_failed": parsed_letter is None,
            }
        )
    return rows


def _modal_choice(letters: list[str]) -> tuple[str | None, int]:
    """Most common non-null letter; ties broken alphabetically (an explicit,
    documented rule rather than incidental dict/Counter ordering). Empty
    input (every model failed to parse on this item) -> (None, 0).
    """
    counts = Counter(letters)
    if not counts:
        return None, 0
    max_n = max(counts.values())
    winner = min(letter for letter, n in counts.items() if n == max_n)
    return winner, max_n


def build_item_summary_rows(result_rows: list[dict]) -> list[dict]:
    """One row per item, aggregated across every model queried for it.
    n_models is the denominator for both `converged` and `shortcut_risk` --
    a parse failure counts against both (it's neither a convergence nor a
    gold hit), it just doesn't shrink the denominator.
    """
    by_item: dict[str, list[dict]] = {}
    for row in result_rows:
        by_item.setdefault(row["item_id"], []).append(row)

    summary = []
    for item_id, rows in by_item.items():
        n_models = len(rows)
        n_hit_gold = sum(1 for r in rows if r["hit_gold"])
        letters = [r["parsed_choice_letter"] for r in rows if r["parsed_choice_letter"] is not None]
        modal_choice, modal_count = _modal_choice(letters)
        summary.append(
            {
                "set": rows[0]["set"],
                "family_id": rows[0]["family_id"],
                "item_id": item_id,
                "condition": rows[0]["condition"],
                "n_models": n_models,
                "n_hit_gold": n_hit_gold,
                "hit_rate": (n_hit_gold / n_models) if n_models else None,
                "modal_choice": modal_choice,
                "modal_choice_count": modal_count,
                "converged": ((modal_count / n_models) >= SHORTCUT_THRESHOLD) if n_models else False,
                "shortcut_risk": ((n_hit_gold / n_models) >= SHORTCUT_THRESHOLD) if n_models else False,
            }
        )
    return summary


def build_collapse_pair_check(item_summary_rows: list[dict], collapse_lookup: dict[str, dict]) -> list[dict]:
    """Exploratory-only: for each collapsed family (e.g. F12's "ba=ma"),
    does the ablation's modal choice agree between the two conditions that
    collapsed under the reference pool? Answers "does context alone push
    models toward the same collapse the human reference pool showed."
    """
    by_family_condition = {
        (row["family_id"], row["condition"]): row for row in item_summary_rows if row["set"] == "exploratory"
    }

    rows = []
    for family_id, detail in collapse_lookup.items():
        cond1, _, cond2 = detail["collapse_pair"].partition("=")
        row1 = by_family_condition.get((family_id, cond1))
        row2 = by_family_condition.get((family_id, cond2))
        cond1_modal = row1["modal_choice"] if row1 else None
        cond2_modal = row2["modal_choice"] if row2 else None
        rows.append(
            {
                "family_id": family_id,
                "collapse_pair": detail["collapse_pair"],
                "collapse_label": detail["collapse_label"],
                "cond1_modal": cond1_modal,
                "cond2_modal": cond2_modal,
                "same_modal": cond1_modal is not None and cond1_modal == cond2_modal,
            }
        )
    rows.sort(key=lambda r: r["family_id"])
    return rows
