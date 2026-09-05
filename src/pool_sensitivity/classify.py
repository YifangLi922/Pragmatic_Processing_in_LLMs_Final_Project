"""Family-level three-way classification, per pool (spec sections 5-6)."""

from .pools import CONDITIONS


def classify_family(condition_results: dict[str, dict]) -> dict:
    """`condition_results` = {"bare": condition_majority() dict, "ba": ..., "ma": ...}
    for one family under one pool.

    - EXCLUDE_BROKEN (checked first, ahead of everything else, including
      NO_CONSENSUS): any condition's majority_label is DISTRACTOR -- the
      item failed to activate its target semantics on at least one
      condition. This used to be a COLLAPSE subtype (collapse_distractor);
      it's now its own top-level class and short-circuits before the
      has-majority check, so a family with a distractor majority on one
      condition and no majority at all on another is EXCLUDE_BROKEN, not
      NO_CONSENSUS.
    - NO_CONSENSUS: (no distractor majority anywhere, and) any condition
      lacks a majority.
    - KEEP: all three conditions have a majority, none DISTRACTOR, AND the
      three majority labels are pairwise distinct -- a genuine three-way
      contrast, matching the family's design intent (bare vs +ba vs +ma
      each meant to read differently). Design-gold agreement is irrelevant
      here (spec section 7 handles that separately and must not feed back
      into this decision).
    - COLLAPSE (structural only now -- see EXCLUDE_BROKEN above): all three
      have a majority, none DISTRACTOR, but two or more conditions
      collapsed onto the same label, so the contrast is broken.
    """
    labels = {c: condition_results[c]["majority_label"] for c in CONDITIONS}

    if "distractor" in labels.values():
        return {"class": "EXCLUDE_BROKEN", "collapse_type": None, "collapse_pair": None, "collapse_label": None}

    if not all(condition_results[c]["has_majority"] for c in CONDITIONS):
        return {"class": "NO_CONSENSUS", "collapse_type": None, "collapse_pair": None, "collapse_label": None}

    if len(set(labels.values())) == len(CONDITIONS):
        return {"class": "KEEP", "collapse_type": None, "collapse_pair": None, "collapse_label": None}

    return {"class": "COLLAPSE", **_structural_collapse_detail(labels)}


def _structural_collapse_detail(labels: dict[str, str]) -> dict:
    """No distractor majority but <3 distinct labels among 3 conditions:
    either exactly one pair shares a label (the third differs) or all three
    share the same label. Either way there's exactly one "collapsed group"
    to report -- the largest group of conditions tied on the same label.
    """
    groups: dict[str, list[str]] = {}
    for condition, label in labels.items():
        groups.setdefault(label, []).append(condition)
    collapsed_label, collapsed_conditions = max(groups.items(), key=lambda kv: len(kv[1]))
    collapse_pair = "=".join(sorted(collapsed_conditions, key=CONDITIONS.index))
    return {"collapse_type": "structural", "collapse_pair": collapse_pair, "collapse_label": collapsed_label}
