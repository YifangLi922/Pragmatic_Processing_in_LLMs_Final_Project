"""Module 3: leave-one-annotator-out (LOO) human baseline (plan section 6.3).

For each of the annotators in turn, the majority vote of the *other* three
becomes that fold's temporary gold, and the held-out annotator is scored
against it. Items where the other three have no majority are skipped for
that fold only (not counted in that fold's denominator). Per plan: compute
each fold's accuracy first, then average the folds -- not one pooled
accuracy over all scored items, since folds can skip different items.
Reported overall and split by particle_condition, as the plan requires.
"""

from collections import Counter


def _majority_of(votes: list[str]) -> str | None:
    if not votes:
        return None
    counts = Counter(votes)
    top_count = counts.most_common(1)[0][1]
    winners = [v for v, n in counts.items() if n == top_count]
    return winners[0] if len(winners) == 1 else None


def _fold_accuracy(items: list[dict], held_out: str) -> float | None:
    correct = 0
    scored = 0
    for item in items:
        annotations_by_id = {a["annotator_id"]: a for a in item["annotations"]}
        if held_out not in annotations_by_id:
            continue
        other_votes = [
            a["answer_semantic"]
            for aid, a in annotations_by_id.items()
            if aid != held_out and a.get("answer_semantic")
        ]
        temp_gold = _majority_of(other_votes)
        if temp_gold is None:
            continue
        scored += 1
        if annotations_by_id[held_out].get("answer_semantic") == temp_gold:
            correct += 1
    return (correct / scored) if scored > 0 else None


def _compute_for(items: list[dict], annotator_ids: list[str]) -> dict:
    fold_accuracies = [
        acc for acc in (_fold_accuracy(items, held_out) for held_out in annotator_ids) if acc is not None
    ]
    return {
        "accuracy": sum(fold_accuracies) / len(fold_accuracies) if fold_accuracies else None,
        "n_folds_used": len(fold_accuracies),
        "n_folds_total": len(annotator_ids),
    }


def loo_human_baseline(items: list[dict]) -> dict[str, dict]:
    """Returns {"overall": {...}, "bare": {...}, "ba": {...}, "ma": {...}}."""
    annotator_ids = sorted({a["annotator_id"] for item in items for a in item["annotations"]})

    result = {"overall": _compute_for(items, annotator_ids)}
    for condition in sorted({item["particle_condition"] for item in items}):
        subset = [item for item in items if item["particle_condition"] == condition]
        result[condition] = _compute_for(subset, annotator_ids)
    return result
