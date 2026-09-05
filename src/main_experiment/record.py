"""The main experiment's record shape -- a `record_builder` for
src.llm_query.runner.run_items(), matching the exact schema the user
specified: gold/hit/parse-failure already joined in per row (unlike the
ablation, which keeps the runner's native schema and joins gold in a
separate analysis pass). `item` must be one of src.ablation.sources'
loaded items, which already carry `set`, `gold_letter`, `gold_semantic`.

Same raw_response convention as the ablation's analysis step: an API error
is written into raw_response (clearly prefixed) rather than dropped, so
nothing is silently lost from the one file meant to store everything.
"""

import datetime as _dt


def build_main_record(item, model_cfg, prompt, run_date, temperature, response, answer_letter) -> dict:
    option_semantics = item.get("option_semantics", {})
    parsed_choice_semantic = option_semantics.get(answer_letter) if answer_letter else None
    raw_response = response.raw_response if not response.error else f"[ERROR] {response.error}"

    return {
        "set": item["set"],
        "family_id": item["family_id"],
        "item_id": item["item_id"],
        "condition": item["particle_condition"],
        "model": model_cfg["name"],
        "raw_response": raw_response,
        "parsed_choice_letter": answer_letter,
        "parsed_choice_semantic": parsed_choice_semantic,
        "gold_letter": item["gold_letter"],
        "gold_semantic": item["gold_semantic"],
        "hit_gold": answer_letter == item["gold_letter"],
        "parse_failed": answer_letter is None,
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }
