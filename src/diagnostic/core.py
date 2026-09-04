"""Per-item diagnostic logic (spec sections 4-6, 10).

Everything here operates on the semantic labels module 1 already derived
(src/reconstruct/semantics.py: statement/confirmation/neutral/distractor --
the spec's ASSERT/TENTATIVE/NEUTRAL/DISTRACTOR are the same four categories
under different names; this module reuses module 1's vocabulary rather than
introducing a second one). Input records are module 1's reconstructed items
(data/reconstructed_5ann.json): each item has "annotations", a list of
{annotator_id, answer_semantic, naturalness, hesitation, no_valid_option}.

BWL is intentionally never passed in as a target or as a reference_pool
member by callers -- see spec section 2. Nothing here special-cases BWL;
the exclusion is the driver's responsibility.
"""

from collections import Counter


def resolve_vote(annotation: dict | None, mode: str) -> str | None:
    """One reference-pool member's vote for majority-vote purposes.

    Spec section 4's two no-option cases collapse into one rule: whenever
    answer_semantic is None (true abstention, or simply unanswered), the
    annotator casts no vote regardless of mode -- there's nothing to
    tally either way. The only place `mode` matters is the "checked
    no-option but still gave an answer" case (no_valid_option=1 with a
    real answer_semantic): mode "A" (primary) counts that answer at face
    value, mode "B" (robustness) discards it as if they'd abstained.
    """
    if annotation is None:
        return None
    choice = annotation.get("answer_semantic")
    if choice is None:
        return None
    if annotation.get("no_valid_option") and mode == "B":
        return None
    return choice


def reference_majority(votes: list[str | None]) -> tuple[str | None, bool]:
    """Spec section 6 step 2. `votes` are already mode-resolved (None = no vote).

    Valid only for a genuine 2-of-N or N-of-N majority among the votes cast.
    A single vote cast (the other two abstained) is explicitly called out in
    the spec as invalid ("计票人数不足以形成多数，如两人弃权"), and a
    1-1-1 or a 1-1 tie among votes cast has no unique top label either --
    both come out invalid here via the same `len(tied) == 1` check applied
    to at-least-two cast votes.
    """
    cast = [v for v in votes if v is not None]
    if len(cast) < 2:
        return None, False
    counts = Counter(cast)
    top_label, top_n = counts.most_common(1)[0]
    tied = [label for label, n in counts.items() if n == top_n]
    if len(tied) == 1:
        return top_label, True
    return None, False


def diagnose_item(item: dict, target: str, reference_pool: list[str], mode: str) -> dict:
    """Spec section 6 (scoring) + section 10 (item-level table fields).

    Edge case not spelled out verbatim in the spec (reference_valid=True but
    the target itself has no answer_semantic -- happens for Materials, who
    has 13 true abstentions): counted as a non-agreement (agree=False) since
    section 7.1 defines reference_n purely from reference validity, so it
    must stay in the agreement denominator; but it gets no
    disagreement_direction and is excluded from confusion matrices, since
    those only have columns for actual semantic labels, not "no answer".
    This is a deliberate, locked-in reading -- see the diagnostic README.
    """
    by_id = {a["annotator_id"]: a for a in item["annotations"]}
    ref_annotations = [by_id.get(rid) for rid in reference_pool]
    ref_votes = [resolve_vote(ra, mode) for ra in ref_annotations]
    reference_label, reference_valid = reference_majority(ref_votes)

    target_ann = by_id.get(target)
    target_semantic = target_ann["answer_semantic"] if target_ann else None

    if not reference_valid:
        agree = None
        direction = None
    elif target_semantic is None:
        agree = False
        direction = None
    else:
        agree = target_semantic == reference_label
        direction = None if agree else f"{reference_label}->{target_semantic}"

    record = {
        "family_id": item["family_id"],
        "item_id": item["item_id"],
        "condition": item["particle_condition"],
        "reference_label": reference_label,
        "reference_valid": reference_valid,
        "target_semantic": target_semantic,
        "agree": agree,
        "disagreement_direction": direction,
        "target_naturalness": target_ann.get("naturalness") if target_ann else None,
        "target_hesitation": bool(target_ann["hesitation"]) if target_ann else None,
        "target_no_option_flag": bool(target_ann["no_valid_option"]) if target_ann else None,
    }
    for rid, ra in zip(reference_pool, ref_annotations):
        record[f"{rid}_semantic"] = ra["answer_semantic"] if ra else None
        record[f"{rid}_no_option_flag"] = bool(ra["no_valid_option"]) if ra else None
    return record


def run_diagnostic(items: list[dict], target: str, reference_pool: list[str], mode: str) -> list[dict]:
    """All 108 items (36 families) for one (target, reference_pool, mode)
    combination -- the unit of work the spec's driver (section 8) repeats
    4 x 2 = 8 times.
    """
    return [diagnose_item(item, target, reference_pool, mode) for item in items]
