"""Human concordance: a second, structurally different human baseline from
loo_baseline.py's LOO accuracy.

For each item, concordance is the fraction of the three core3 annotators
whose answer_semantic matches gold -- averaged within condition across the
20 frozen confirmatory families. This asks the same question model accuracy
does ("what fraction of answerers picked gold?") on every item, including
2:1 splits.

LOO asks a different question: for a held-out annotator, does the *majority
of the other two* (this fold's temporary gold) match the held-out person's
answer? On a 2:1 item, the held-out member is, by construction, either in
the majority (scored against the other two, who by definition agree with
each other but that pair's own accuracy against real gold is not itself
checked here) or in the minority (guaranteed a miss for that fold). So LOO
systematically scores every 2:1 split as at least one miss, while
concordance would score it as 2/3. Report both -- concordance is the one
comparable to model accuracy.
"""

from collections import defaultdict


def item_concordance(item: dict, gold_semantic: str) -> float | None:
    annotations = item["annotations"]
    if not annotations:
        return None
    n_match = sum(1 for a in annotations if a.get("answer_semantic") == gold_semantic)
    return n_match / len(annotations)


def core3_concordance(items: list[dict], gold_by_item: dict[str, str]) -> dict[str, dict]:
    """`items` = filter.restrict_to_core3_keep_families() output (core3
    annotations only, keep families only). `gold_by_item` = item_id ->
    gold_semantic (frozen_dataset.csv). Returns {"overall": {...}, "bare":
    {...}, "ba": {...}, "ma": {...}}, each {"accuracy": mean per-item
    concordance, "n_items": how many items fed that mean}.
    """
    by_condition: dict[str, list[float]] = defaultdict(list)
    for item in items:
        gold = gold_by_item.get(item["item_id"])
        if gold is None:
            continue
        value = item_concordance(item, gold)
        if value is None:
            continue
        by_condition[item["particle_condition"]].append(value)
        by_condition["overall"].append(value)

    return {
        condition: {
            "accuracy": sum(values) / len(values) if values else None,
            "n_items": len(values),
        }
        for condition, values in by_condition.items()
    }
