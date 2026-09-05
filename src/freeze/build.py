"""Row construction for frozen_dataset.csv / frozen_exploratory.csv, per the
field list the user specified (context_text, target_sentence, option_A-D,
option_semantic_map, gold_semantic, gold_letter, design_gold_semantic,
gold_shifted, margin, stable_keep_all_pools).
"""

from src.pool_sensitivity.pools import CONDITIONS

_LETTERS = ("A", "B", "C", "D")


def _option_semantic_map(option_semantics: dict) -> str:
    return "|".join(f"{letter}:{option_semantics[letter]}" for letter in _LETTERS)


def _gold_letter(option_semantics: dict, gold_semantic: str) -> str:
    for letter, role in option_semantics.items():
        if role == gold_semantic:
            return letter
    raise ValueError(f"no option maps to gold_semantic {gold_semantic!r} in {option_semantics!r}")


def build_row(item: dict, gold: dict, stable_keep_all_pools: bool) -> dict:
    gold_semantic = gold["gold_semantic"]
    return {
        "family_id": item["family_id"],
        "item_id": item["item_id"],
        "condition": item["particle_condition"],
        "context_text": item["context"],
        "target_sentence": item["sentence"],
        "option_A": item["options"]["A"],
        "option_B": item["options"]["B"],
        "option_C": item["options"]["C"],
        "option_D": item["options"]["D"],
        "option_semantic_map": _option_semantic_map(item["option_semantics"]),
        "gold_semantic": gold_semantic,
        "gold_letter": _gold_letter(item["option_semantics"], gold_semantic),
        "design_gold_semantic": item["gold_semantic_designed"],
        "gold_shifted": gold["gold_shifted"],
        "margin": gold["margin"],
        "stable_keep_all_pools": stable_keep_all_pools,
    }


def build_frozen_rows(items: list[dict], grid: dict, gold_lookup: dict, target_class: str) -> list[dict]:
    """Only items whose family's grid core3_class == target_class are
    included (e.g. "KEEP" for the confirmatory set, "COLLAPSE" for the
    structural-collapse exploratory set). Ordered by (family_id, condition).
    """
    rows = []
    for item in items:
        family_id = item["family_id"]
        if grid.get(family_id, {}).get("core3_class") != target_class:
            continue
        gold = gold_lookup[(family_id, item["particle_condition"])]
        rows.append(build_row(item, gold, grid[family_id]["stable_keep_all_pools"]))
    rows.sort(key=lambda r: (r["family_id"], CONDITIONS.index(r["condition"])))
    return rows


def build_exploratory_rows(items: list[dict], grid: dict, gold_lookup: dict, collapse_lookup: dict) -> list[dict]:
    rows = build_frozen_rows(items, grid, gold_lookup, target_class="COLLAPSE")
    for row in rows:
        detail = collapse_lookup[row["family_id"]]
        row["collapse_pair"] = detail["collapse_pair"]
        row["collapse_label"] = detail["collapse_label"]
    return rows
