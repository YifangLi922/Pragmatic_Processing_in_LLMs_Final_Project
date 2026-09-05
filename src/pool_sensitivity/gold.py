"""Empirical gold from pool_core3's majority vote + design-gold shift
detection (spec section 7). Fixed to pool_core3 -- this is the "main pool"
the spec designates for gold, independent of which pool a family's
KEEP/COLLAPSE/NO_CONSENSUS classification happens to use.
"""

from .majority import condition_majority
from .pools import POOLS

CORE3_POOL = POOLS["core3"]


def empirical_gold_row(item: dict) -> dict:
    """One row per (family, condition). `gold_shifted` is only ever True
    when has_majority is True -- a condition with no majority has no
    empirical gold to compare, so it can't be "shifted", only undefined.
    """
    result = condition_majority(item, CORE3_POOL, mode="A")
    design_label = item["gold_semantic_designed"]
    gold_shifted = result["has_majority"] and result["majority_label"] != design_label
    return {
        "family_id": item["family_id"],
        "condition": item["particle_condition"],
        "has_majority": result["has_majority"],
        "majority_label": result["majority_label"],
        "design_gold_label": design_label,
        "gold_shifted": gold_shifted,
        "majority_count": result["majority_count"],
        "pool_size": result["pool_size"],
        "margin": result["margin"],
    }


def shifted_row(gold_row: dict) -> dict:
    """Projection of a gold_shifted empirical_gold_row into the
    gold_shifted_families.csv schema (spec section 8)."""
    return {
        "family_id": gold_row["family_id"],
        "condition": gold_row["condition"],
        "design_gold_label": gold_row["design_gold_label"],
        "empirical_gold_label": gold_row["majority_label"],
        "margin": gold_row["margin"],
    }
