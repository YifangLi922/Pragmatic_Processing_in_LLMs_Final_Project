"""Module 5: join model results (module 4) against gold + retained families
(module 2) into per-model scoreboards (plan section 5, Module 5).

Scoring convention (documented here because it's a real methodological
choice, not an obvious default):
  - A record whose API call errored (rate limit, timeout, bad request, cost
    guard block) is EXCLUDED from scoring -- that's an infrastructure
    failure, not a signal about the model's language ability. Counted
    separately as n_errored so it stays visible.
  - A record where the call succeeded but no letter could be parsed out of
    the response IS SCORED AS INCORRECT (not excluded) -- failing to produce
    a usable answer in the required format is itself a meaningful failure
    for this task, matching the plan's literal correct = (model_answer_semantic
    == gold_semantic) definition (None != any gold_semantic). Counted
    separately as n_unparseable so the reader can see how much of the
    reported error rate is "picked the wrong option" vs. "didn't follow the
    format" and re-derive an excluded-instead-of-wrong version if they'd
    rather report it that way.
  - Items whose family wasn't retained (module 2 exclusion) or whose gold is
    undefined are excluded from scoring entirely -- they're not part of the
    frozen confirmatory set.
"""

from collections import defaultdict


def build_scoreboard(
    items: list[dict],
    model_results: list[dict],
    gold_results: list,
    family_decisions: list,
) -> tuple[dict[str, list[dict]], list[dict]]:
    """`items` = module 1 output (for option_semantics per item_id).
    `model_results` = module 4 output records (any number of models mixed
    together is fine -- they get split out by model_name).
    `gold_results`, `family_decisions` = evaluate_families() output (module 2).

    Returns (scored_by_model, skipped). `scored_by_model` maps model_name to
    a list of scored records (each model-result record plus gold_semantic,
    correct, and option_semantics). `skipped` lists every excluded record
    with a reason, across all models.
    """
    option_semantics_by_item = {it["item_id"]: it.get("option_semantics", {}) for it in items}
    gold_by_item = {g.item_id: g.gold_semantic for g in gold_results if g.gold_semantic is not None}
    retained_families = {d.family_id for d in family_decisions if d.retained}

    scored_by_model: dict[str, list[dict]] = defaultdict(list)
    skipped: list[dict] = []

    for rec in model_results:
        item_id = rec["item_id"]
        model_name = rec["model_name"]
        family_id = rec.get("family_id")

        if family_id not in retained_families:
            skipped.append({"model_name": model_name, "item_id": item_id, "reason": "family_not_retained"})
            continue
        gold = gold_by_item.get(item_id)
        if gold is None:
            skipped.append({"model_name": model_name, "item_id": item_id, "reason": "undefined_gold"})
            continue
        if rec.get("error"):
            skipped.append({"model_name": model_name, "item_id": item_id, "reason": "call_error", "detail": rec["error"]})
            continue

        model_semantic = rec.get("model_answer_semantic")
        scored_by_model[model_name].append(
            {
                **rec,
                "gold_semantic": gold,
                "option_semantics": option_semantics_by_item.get(item_id, {}),
                "correct": model_semantic == gold,
                "unparseable": model_semantic is None,
            }
        )

    return dict(scored_by_model), skipped
