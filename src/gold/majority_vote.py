"""Module 2: majority-vote gold definition (plan section 6.1).

Gold is the 4 annotators' majority vote on the *semantic* label
(statement/confirmation/neutral/distractor), never the designer's expected
answer and never the raw answer letter (letters get reshuffled per item by
option_order, so voting must happen after that's already been translated to
semantics -- this module assumes it's handed data in that shape).
"""

from collections import Counter
from dataclasses import dataclass


@dataclass
class GoldResult:
    item_id: str
    gold_semantic: str | None  # None when there's no unique majority (e.g. a 2:2 tie)
    consensus_strength: str  # "4:0" / "3:1" / "2:1:1" / "2:2" / ...
    vote_counts: dict


def majority_vote(item: dict) -> GoldResult:
    """`item` needs `item_id` and `annotations` (dicts with `answer_semantic`).
    Rows with a missing/unparseable answer_semantic don't count as a vote.
    """
    votes = [a["answer_semantic"] for a in item["annotations"] if a.get("answer_semantic")]
    counts = Counter(votes)
    ranked = counts.most_common()  # [(semantic, n), ...] sorted by n desc

    if not ranked:
        return GoldResult(item["item_id"], None, "0:0", dict(counts))

    top_count = ranked[0][1]
    tied_for_top = [sem for sem, n in ranked if n == top_count]
    strength = _consensus_label(ranked)

    if len(tied_for_top) > 1:
        return GoldResult(item["item_id"], None, strength, dict(counts))

    return GoldResult(item["item_id"], ranked[0][0], strength, dict(counts))


def _consensus_label(ranked: list[tuple[str, int]]) -> str:
    counts = [n for _, n in ranked]
    if len(counts) == 1:
        return f"{counts[0]}:0"
    return ":".join(str(n) for n in counts)


def consensus_tier(consensus_strength: str) -> str:
    """"strong" (4:0/3:1) / "weak" (2:1:1) / "undefined" (2:2, scattered ties,
    or no votes at all) -- used by the family exclusion rules.
    """
    if consensus_strength in ("4:0", "3:1"):
        return "strong"
    if consensus_strength == "2:1:1":
        return "weak"
    return "undefined"
