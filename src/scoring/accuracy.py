"""Module 5: condition accuracy + 95% CI (plan section 5, Module 5).

Uses the Wilson score interval rather than the naive normal-approximation CI
-- after family exclusion, per-condition sample sizes are likely to be small
(tens of items), where Wilson stays well-behaved and the naive interval can
go outside [0, 1] or misbehave near 0%/100% accuracy.
"""

import math

_Z_95 = 1.959963984540054  # scipy.stats.norm.ppf(0.975), hardcoded to avoid a scipy dependency


def wilson_ci(successes: int, n: int, z: float = _Z_95) -> tuple[float, float] | tuple[None, None]:
    if n == 0:
        return None, None
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half_width = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return max(0.0, center - half_width), min(1.0, center + half_width)


def accuracy_with_ci(records: list[dict]) -> dict:
    """`records` need a boolean "correct" field. Empty input returns n=0 and
    None for accuracy/CI rather than dividing by zero.
    """
    n = len(records)
    n_correct = sum(1 for r in records if r["correct"])
    accuracy = (n_correct / n) if n else None
    ci_low, ci_high = wilson_ci(n_correct, n)
    return {"n": n, "n_correct": n_correct, "accuracy": accuracy, "ci_low": ci_low, "ci_high": ci_high}


def condition_accuracy(scored_records: list[dict]) -> dict:
    """One model's scored records (from join.build_scoreboard) -> overall +
    per-condition accuracy/CI.
    """
    result = {"overall": accuracy_with_ci(scored_records)}
    for condition in ("bare", "ba", "ma"):
        subset = [r for r in scored_records if r["particle_condition"] == condition]
        result[condition] = accuracy_with_ci(subset)
    return result
