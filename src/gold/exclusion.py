"""Module 2: family-level exclusion (plan section 6.2).

A family enters the confirmatory gold set only if all three hold:
  1. the three conditions' gold_semantic values are pairwise distinct
  2. no condition has an undefined gold (a 2:2/scattered tie); a 2:1:1 "weak"
     gold is allowed through unless GoldConfig.require_strong_consensus
  3. every condition's mean naturalness rating meets GoldConfig.naturalness_min

Exclusion is family-wise: any one condition failing takes the whole family
out, because the core bare/ba/ma contrast needs all three conditions intact.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from .config import GoldConfig
from .majority_vote import GoldResult, consensus_tier, majority_vote

EXPECTED_CONDITIONS = {"bare", "ba", "ma"}


@dataclass
class FamilyDecision:
    family_id: str
    retained: bool
    reasons: list[str] = field(default_factory=list)  # exclusion reasons; empty iff retained
    gold_by_condition: dict[str, GoldResult] = field(default_factory=dict)
    mean_naturalness_by_condition: dict[str, float] = field(default_factory=dict)


def mean_naturalness(item: dict) -> float | None:
    values = [a["naturalness"] for a in item["annotations"] if a.get("naturalness") is not None]
    return sum(values) / len(values) if values else None


def evaluate_families(
    items: list[dict], config: GoldConfig = GoldConfig()
) -> tuple[list[GoldResult], list[FamilyDecision]]:
    """Returns (per-item gold results, per-family retain/exclude decisions)."""
    gold_results = [majority_vote(item) for item in items]
    gold_by_item_id = {g.item_id: g for g in gold_results}

    by_family: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_family[item["family_id"]].append(item)

    decisions = [
        _evaluate_one_family(family_id, family_items, gold_by_item_id, config)
        for family_id, family_items in by_family.items()
    ]
    return gold_results, decisions


def _evaluate_one_family(
    family_id: str, family_items: list[dict], gold_by_item_id: dict[str, GoldResult], config: GoldConfig
) -> FamilyDecision:
    reasons = []
    gold_by_condition: dict[str, GoldResult] = {}
    naturalness_by_condition: dict[str, float | None] = {}

    for item in family_items:
        condition = item["particle_condition"]
        gold_by_condition[condition] = gold_by_item_id[item["item_id"]]
        naturalness_by_condition[condition] = mean_naturalness(item)

    missing = EXPECTED_CONDITIONS - set(gold_by_condition)
    if missing:
        reasons.append(f"incomplete_family: missing condition(s) {sorted(missing)}")

    for condition, gold in gold_by_condition.items():
        if gold.gold_semantic is None:
            reasons.append(f"undefined_gold: {condition} has no majority ({gold.consensus_strength})")
        elif config.require_strong_consensus and consensus_tier(gold.consensus_strength) != "strong":
            reasons.append(f"weak_consensus: {condition} is {gold.consensus_strength}")

    defined_golds = [g.gold_semantic for g in gold_by_condition.values() if g.gold_semantic is not None]
    if len(defined_golds) != len(set(defined_golds)):
        reasons.append("gold_collision: two or more conditions share the same gold_semantic")

    for condition, mean_nat in naturalness_by_condition.items():
        if mean_nat is not None and mean_nat < config.naturalness_min:
            reasons.append(f"low_naturalness: {condition} mean={mean_nat:.2f} < {config.naturalness_min}")

    return FamilyDecision(
        family_id=family_id,
        retained=(len(reasons) == 0),
        reasons=reasons,
        gold_by_condition=gold_by_condition,
        mean_naturalness_by_condition=naturalness_by_condition,
    )


def exclusion_report(decisions: list[FamilyDecision]) -> dict:
    """Buckets excluded families by (first) reason category, for the
    plan's required "剔除原因分类统计" -- family-wise, not item-wise.
    """
    counts: dict[str, int] = defaultdict(int)
    for decision in decisions:
        if decision.retained:
            continue
        for reason in decision.reasons:
            category = reason.split(":", 1)[0]
            counts[category] += 1
    return {
        "n_families_total": len(decisions),
        "n_retained": sum(1 for d in decisions if d.retained),
        "n_excluded": sum(1 for d in decisions if not d.retained),
        "excluded_by_reason_category": dict(counts),
    }
