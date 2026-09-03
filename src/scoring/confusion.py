"""Module 5: confusion matrix per condition (plan section 5, Module 5).

For each particle condition, tallies what semantic label the model's answers
actually fell into -- the plan is specifically interested in patterns like
+ba -> neutral (read like a ma-question) or +ba -> statement (particle
ignored), which this surfaces directly as counts.
"""

_SEMANTICS = ("statement", "confirmation", "neutral", "distractor")


def confusion_matrix(scored_records: list[dict]) -> dict:
    result = {}
    for condition in ("bare", "ba", "ma"):
        subset = [r for r in scored_records if r["particle_condition"] == condition]
        counts = {sem: 0 for sem in _SEMANTICS}
        counts["unparseable"] = 0
        for r in subset:
            sem = r.get("model_answer_semantic")
            if sem in counts:
                counts[sem] += 1
            else:
                counts["unparseable"] += 1
        result[condition] = {"n": len(subset), "counts": counts}
    return result
