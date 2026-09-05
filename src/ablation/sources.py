"""Read the two frozen CSVs into the item shape src.llm_query.runner expects,
joining in the one field the freeze step didn't carry (`question` -- the
per-item prompt line, e.g. "小周说这句话时，最接近下面哪种态度？"; it varies
by item because it names the speaker, so it can't be hardcoded) from
data/reconstructed_5ann.json by item_id. Nothing here re-derives semantics:
option_semantic_map is parsed back into a dict, not recomputed from option
text.
"""

import csv
import json

_LETTERS = ("A", "B", "C", "D")


def parse_option_semantic_map(raw: str) -> dict[str, str]:
    """"A:distractor|B:neutral|C:statement|D:confirmation" -> dict. This is
    parsing the already-computed mapping frozen_dataset.csv carries, not
    re-deriving letter->semantic from option text.
    """
    result = {}
    for pair in raw.split("|"):
        letter, _, role = pair.partition(":")
        result[letter] = role
    missing = [letter for letter in _LETTERS if letter not in result]
    if missing:
        raise ValueError(f"option_semantic_map {raw!r} is missing letters {missing}")
    return result


def load_question_lookup(reconstructed_path: str) -> dict[str, str]:
    with open(reconstructed_path, encoding="utf-8") as f:
        items = json.load(f)
    return {item["item_id"]: item["question"] for item in items}


def _base_ablation_item(row: dict, set_name: str, question_lookup: dict[str, str]) -> dict:
    """`sentence` is carried through even though build_context_only_prompt()
    never reads it -- this same loader is reused by the main experiment
    (src.main_experiment), which needs it for build_prompt(). Keeping one
    loader for both means the two runs are guaranteed to see the exact same
    item set/order/text, which is what makes them comparable item-for-item.
    """
    option_semantics = parse_option_semantic_map(row["option_semantic_map"])
    return {
        "item_id": row["item_id"],
        "family_id": row["family_id"],
        "particle_condition": row["condition"],
        "context": row["context_text"],
        "sentence": row["target_sentence"],
        "question": question_lookup[row["item_id"]],
        "options": {letter: row[f"option_{letter}"] for letter in _LETTERS},
        "option_semantics": option_semantics,
        # Ablation-only bookkeeping, ignored by src.llm_query.runner but read
        # back by src.ablation.analysis / src.main_experiment when joining
        # the query results.
        "set": set_name,
        "gold_letter": row["gold_letter"],
        "gold_semantic": row["gold_semantic"],
        "collapse_pair": row.get("collapse_pair"),
        "collapse_label": row.get("collapse_label"),
    }


def load_frozen_items(csv_path: str, set_name: str, question_lookup: dict[str, str]) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return [_base_ablation_item(row, set_name, question_lookup) for row in csv.DictReader(f)]


def load_ablation_items(frozen_dataset_path: str, frozen_exploratory_path: str, reconstructed_path: str) -> list[dict]:
    """The combined confirmatory + exploratory item list, one run's worth,
    each item tagged with its `set` for downstream split reporting.
    """
    question_lookup = load_question_lookup(reconstructed_path)
    confirmatory = load_frozen_items(frozen_dataset_path, "confirmatory", question_lookup)
    exploratory = load_frozen_items(frozen_exploratory_path, "exploratory", question_lookup)
    return confirmatory + exploratory
