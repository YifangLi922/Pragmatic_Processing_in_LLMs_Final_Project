"""Module 3: Fleiss' kappa (plan section 6, "一致度 (Fleiss' kappa 等)").

Uses the generalized form (varying raters per item), which reduces to the
textbook fixed-4-rater formula when every item has exactly 4 valid ratings.
Real annotation data can have the occasional dropped/unparseable answer, and
this shouldn't crash the whole computation.
"""

from collections import Counter

CATEGORIES = ("statement", "confirmation", "neutral", "distractor")


def fleiss_kappa(items: list[dict], categories: tuple[str, ...] = CATEGORIES) -> float | None:
    """`items` each need an `annotations` list of dicts with `answer_semantic`.
    Items left with fewer than 2 valid ratings are skipped (kappa needs at
    least 2 raters per item). Returns None if fewer than 2 items remain.
    """
    per_item_counts = []
    for item in items:
        votes = [a["answer_semantic"] for a in item["annotations"] if a.get("answer_semantic") in categories]
        if len(votes) < 2:
            continue
        per_item_counts.append(Counter(votes))

    if len(per_item_counts) < 2:
        return None

    total_ratings = sum(sum(c.values()) for c in per_item_counts)
    category_totals = {cat: sum(c.get(cat, 0) for c in per_item_counts) for cat in categories}
    p_j = {cat: category_totals[cat] / total_ratings for cat in categories}
    p_e_bar = sum(p**2 for p in p_j.values())

    p_i_values = []
    for counts in per_item_counts:
        n_i = sum(counts.values())
        sum_sq = sum(counts.get(cat, 0) ** 2 for cat in categories)
        p_i_values.append((sum_sq - n_i) / (n_i * (n_i - 1)))
    p_bar = sum(p_i_values) / len(p_i_values)

    if p_e_bar == 1.0:
        # Every rating in the whole dataset fell in one category: chance
        # agreement is total, so kappa is only defined as perfect (all raters
        # agreed on everything) or, degenerately, undefined -- report 1.0
        # since p_bar == p_e_bar == 1.0 in that case, 0.0 otherwise.
        return 1.0 if p_bar == 1.0 else 0.0
    return (p_bar - p_e_bar) / (1 - p_e_bar)
