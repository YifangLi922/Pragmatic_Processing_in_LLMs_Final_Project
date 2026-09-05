"""Family-level three-way classification, per pool (spec sections 5-6)."""

from .pools import CONDITIONS


def classify_family(condition_results: dict[str, dict]) -> dict:
    """`condition_results` = {"bare": condition_majority() dict, "ba": ..., "ma": ...}
    for one family under one pool.

    - NO_CONSENSUS: any condition lacks a majority.
    - KEEP: all three conditions have a majority, none of them DISTRACTOR,
      AND the three majority labels are pairwise distinct -- a genuine
      three-way contrast, matching the family's design intent (bare vs +ba
      vs +ma each meant to read differently). Design-gold agreement is
      irrelevant here (spec section 7 handles that separately and must not
      feed back into this decision).
    - COLLAPSE: all three have a majority but the contrast is broken. Split
      into distractor (ANY condition's majority is the DISTRACTOR role --
      the item itself failed to activate its target semantics, checked
      first and independent of what the other two conditions read as) vs.
      structural (no distractor majority, but two or more conditions
      collapsed onto the same label) per section 6.
    """
    if not all(condition_results[c]["has_majority"] for c in CONDITIONS):
        return {"class": "NO_CONSENSUS", "collapse_type": None, "collapse_pair": None, "collapse_label": None}

    labels = {c: condition_results[c]["majority_label"] for c in CONDITIONS}

    # Checked before the pairwise-distinctness test: a distractor majority
    # on any single condition is a design failure regardless of whether the
    # other two conditions happen to differ from each other.
    if "distractor" in labels.values():
        return {"class": "COLLAPSE", "collapse_type": "distractor", "collapse_pair": None, "collapse_label": None}

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
