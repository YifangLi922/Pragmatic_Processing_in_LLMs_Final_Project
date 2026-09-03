"""Module 5: assemble one scorecard per model (plan section 5, Module 5).

Ties together join.build_scoreboard with accuracy/pair_family_success/
confusion/logprob_shift into the "各模型成绩单" the plan asks for.
"""

from .accuracy import condition_accuracy
from .confusion import confusion_matrix
from .join import build_scoreboard
from .logprob_shift import semantic_probability_profile
from .pair_family_success import family_success, family_success_by_family, pair_success


def build_scorecard(model_name: str, scored_records: list[dict], skipped_for_model: list[dict]) -> dict:
    n_errored = sum(1 for s in skipped_for_model if s["reason"] == "call_error")
    n_excluded_by_dataset = len(skipped_for_model) - n_errored
    n_unparseable = sum(1 for r in scored_records if r["unparseable"])

    return {
        "model_name": model_name,
        "n_scored": len(scored_records),
        "n_unparseable": n_unparseable,
        "n_errored": n_errored,
        "n_excluded_by_dataset": n_excluded_by_dataset,
        "condition_accuracy": condition_accuracy(scored_records),
        "pair_success": pair_success(scored_records),
        "family_success": family_success(scored_records),
        "family_success_detail": family_success_by_family(scored_records),
        "confusion_matrix": confusion_matrix(scored_records),
        "logprob_shift": semantic_probability_profile(scored_records),
    }


def build_all_scorecards(
    items: list[dict],
    model_results: list[dict],
    gold_results: list,
    family_decisions: list,
) -> dict:
    scored_by_model, skipped = build_scoreboard(items, model_results, gold_results, family_decisions)

    skipped_by_model: dict[str, list[dict]] = {}
    for s in skipped:
        skipped_by_model.setdefault(s["model_name"], []).append(s)

    all_model_names = sorted(set(scored_by_model) | set(skipped_by_model))
    scorecards = {
        model_name: build_scorecard(model_name, scored_by_model.get(model_name, []), skipped_by_model.get(model_name, []))
        for model_name in all_model_names
    }
    return {"scorecards": scorecards, "skipped": skipped}
