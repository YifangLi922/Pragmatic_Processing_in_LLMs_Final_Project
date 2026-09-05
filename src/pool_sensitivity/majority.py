"""Per-item, per-pool majority vote (spec sections 2 and 4).

No-option handling reuses resolve_vote() from the Econ diagnostic
(src/diagnostic/core.py) rather than reimplementing it -- this script fixes
mode "A" (choice-first: a pool member who checked "no valid option" but
still gave an answer is counted at that answer) everywhere, per spec
section 2. Mode B is the diagnostic script's own robustness check and is
out of scope here.

pool_majority() is a fresh implementation, not diagnostic.core.reference_majority():
that function's "unique top label of a Counter" shortcut only equals a
strict majority because it's always applied to a fixed 3-member pool (2-1
and 3-0 splits both happen to clear >50% automatically). This module's pools
range from 3 to 5 members, where a unique plurality is not necessarily a
strict majority -- e.g. 2 votes out of a 4-cast or 5-cast pool is a unique
top label but not "> half" -- so the ">half of votes cast" arithmetic is
done explicitly here instead, per spec section 4.
"""

from collections import Counter

from src.diagnostic.core import resolve_vote

# A single cast vote (everyone else in the pool abstained) is "计票人不足"
# per spec section 4 -- explicitly not a majority, regardless of the fact
# that one vote is trivially "more than half" of one vote.
MIN_CAST_FOR_MAJORITY = 2


def pool_majority(cast_votes: list[str]) -> tuple[str | None, bool]:
    """`cast_votes` must already have abstentions filtered out. Strict
    majority = more than half of the votes actually cast. Ties (including
    an even-pool 2-2 split), 1-1-1 splits, and "计票人不足" (fewer than 2
    cast) all come back as no-majority -- no tie-break rule is applied.
    """
    if len(cast_votes) < MIN_CAST_FOR_MAJORITY:
        return None, False
    counts = Counter(cast_votes)
    top_label, top_n = counts.most_common(1)[0]
    if top_n > len(cast_votes) / 2:
        return top_label, True
    return None, False


def condition_majority(item: dict, pool_members: list[str], mode: str = "A") -> dict:
    """One (item, pool) result. Always returns majority_count/pool_size/margin
    alongside majority_label/has_majority -- the empirical-gold table (spec
    section 7/8) wants these for every condition, not just the ones that end
    up gold-shifted.

    `pool_size` here is the number of pool members who actually cast a vote
    on this item (abstentions excluded per section 2), not the pool's fixed
    membership count -- that's what actually determines whether a majority
    is a landslide or a squeaker, and it can vary item-to-item.
    """
    by_id = {a["annotator_id"]: a for a in item["annotations"]}
    cast_votes = [v for v in (resolve_vote(by_id.get(pid), mode) for pid in pool_members) if v is not None]

    label, has_majority = pool_majority(cast_votes)

    ranked_counts = [n for _, n in Counter(cast_votes).most_common()]
    majority_count = ranked_counts[0] if ranked_counts else 0
    second_count = ranked_counts[1] if len(ranked_counts) > 1 else 0

    return {
        "majority_label": label,
        "has_majority": has_majority,
        "majority_count": majority_count,
        "pool_size": len(cast_votes),
        "margin": majority_count - second_count,
    }
