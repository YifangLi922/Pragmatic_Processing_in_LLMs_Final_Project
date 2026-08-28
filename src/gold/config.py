"""Configurable thresholds for Module 2 (gold definition + family exclusion).

Kept separate from the logic so the naturalness cutoff and the
weak-consensus policy can be tuned without touching gold.py/exclusion.py
(plan section 8, point 5: thresholds should be config, not hardcoded).
"""

from dataclasses import dataclass


@dataclass
class GoldConfig:
    naturalness_min: float = 4.0
    # Plan 6.2 rule 2 always excludes an *undefined* gold (a 2:2/scattered
    # tie). A 2:1:1 "weak consensus" gold is allowed through by default and
    # only flagged; set this True to also require strong (4:0/3:1) consensus
    # once you've seen the real retention rate and decide to tighten it.
    require_strong_consensus: bool = False
