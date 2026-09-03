"""Module 5: pair success + family success (plan section 5, Module 5).

Both are computed only over families where the relevant condition(s) are
actually present in a given model's scored records -- a family missing a
condition (e.g. that one call errored and got excluded upstream in join.py)
is skipped for that comparison rather than silently counted as a failure.
"""

from collections import defaultdict

_PAIRS = (("bare", "ba"), ("ba", "ma"), ("bare", "ma"))


def _correct_by_family(scored_records: list[dict]) -> dict[str, dict[str, bool]]:
    by_family: dict[str, dict[str, bool]] = defaultdict(dict)
    for r in scored_records:
        by_family[r["family_id"]][r["particle_condition"]] = r["correct"]
    return by_family


def pair_success(scored_records: list[dict]) -> dict:
    by_family = _correct_by_family(scored_records)
    result = {}
    for c1, c2 in _PAIRS:
        n = 0
        n_success = 0
        for conds in by_family.values():
            if c1 in conds and c2 in conds:
                n += 1
                if conds[c1] and conds[c2]:
                    n_success += 1
        result[f"{c1}_{c2}"] = {"n_families": n, "n_success": n_success, "rate": (n_success / n) if n else None}
    return result


def family_success(scored_records: list[dict]) -> dict:
    by_family = _correct_by_family(scored_records)
    n = 0
    n_success = 0
    for conds in by_family.values():
        if {"bare", "ba", "ma"} <= conds.keys():
            n += 1
            if all(conds.values()):
                n_success += 1
    return {"n_families": n, "n_success": n_success, "rate": (n_success / n) if n else None}
