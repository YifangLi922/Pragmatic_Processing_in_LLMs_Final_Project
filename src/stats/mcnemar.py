"""Module 6: McNemar's exact test for paired condition comparisons (plan
section 5, Module 6).

For one model, on the same set of families, compares bare vs +ba, +ba vs
+ma, bare vs +ma as paired binary accuracy (paired because it's the same
family answering both conditions, so a plain two-sample test would be
wrong -- McNemar only looks at the *discordant* pairs, where the model got
one condition right and the other wrong).

Implemented as the exact binomial form (no scipy/statsmodels dependency):
p = 2 * P(Binomial(n=b+c, p=0.5) <= min(b,c)), capped at 1.0, where b and c
are the two discordant-pair counts. This matches R's mcnemar.exact / a
two-sided exact binomial test on the discordant pairs, and is preferred
over the chi-square approximation when b+c is small (plausible here after
family exclusion).
"""

import math
from collections import defaultdict

_PAIRS = (("bare", "ba"), ("ba", "ma"), ("bare", "ma"))


def mcnemar_exact_p(b: int, c: int) -> float | None:
    """Two-sided exact McNemar p-value from the two discordant-pair counts.
    None (undefined) when there are no discordant pairs at all -- the model
    agreed with itself on every family, so there's nothing to test.
    """
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    tail_mass = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2 * tail_mass)


def _correct_by_family(scored_records: list[dict]) -> dict[str, dict[str, bool]]:
    by_family: dict[str, dict[str, bool]] = defaultdict(dict)
    for r in scored_records:
        by_family[r["family_id"]][r["particle_condition"]] = r["correct"]
    return by_family


def mcnemar_by_pair(scored_records: list[dict]) -> dict:
    """One model's scored records (from src.scoring.join.build_scoreboard)
    -> a McNemar result for each of the three condition pairs, computed only
    over families where both conditions of that pair were actually scored.
    """
    by_family = _correct_by_family(scored_records)
    result = {}
    for c1, c2 in _PAIRS:
        both_correct = both_wrong = only_c1 = only_c2 = 0
        for conds in by_family.values():
            if c1 not in conds or c2 not in conds:
                continue
            v1, v2 = conds[c1], conds[c2]
            if v1 and v2:
                both_correct += 1
            elif not v1 and not v2:
                both_wrong += 1
            elif v1 and not v2:
                only_c1 += 1
            else:
                only_c2 += 1

        n_families = both_correct + both_wrong + only_c1 + only_c2
        result[f"{c1}_vs_{c2}"] = {
            "n_families": n_families,
            "both_correct": both_correct,
            "both_wrong": both_wrong,
            f"{c1}_only_correct": only_c1,
            f"{c2}_only_correct": only_c2,
            "p_value": mcnemar_exact_p(only_c1, only_c2),
        }
    return result
