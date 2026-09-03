"""Module 5: logprob-derived semantic probability profile (plan section 5,
Module 5, "若有logprob"). Best-effort and informational only -- as covered in
the module 4 smoke test, not every model/provider on OpenRouter returns
logprobs, so this silently produces fewer (or zero) data points for models
that never do, rather than failing the rest of the scorecard.

Converts each item's four letter-logprobs to probabilities via softmax, then
sums the probability mass onto each semantic role via that item's
option_semantics, and averages per condition. The plan's question is whether
the mean profile shifts as expected across bare -> +ba -> +ma; this produces
the numbers to check that against, without asserting an interpretation here.
"""

import math
from collections import defaultdict

_LETTERS = ("A", "B", "C", "D")
_SEMANTICS = ("statement", "confirmation", "neutral", "distractor")


def _softmax_letters(record: dict) -> dict[str, float] | None:
    logprobs = {letter: record.get(f"logprob_{letter}") for letter in _LETTERS}
    if any(v is None for v in logprobs.values()):
        return None
    m = max(logprobs.values())
    exp_vals = {letter: math.exp(v - m) for letter, v in logprobs.items()}
    total = sum(exp_vals.values())
    return {letter: v / total for letter, v in exp_vals.items()}


def semantic_probability_profile(scored_records: list[dict]) -> dict:
    by_condition: dict[str, list[dict[str, float]]] = defaultdict(list)

    for r in scored_records:
        letter_probs = _softmax_letters(r)
        option_semantics = r.get("option_semantics")
        if letter_probs is None or not option_semantics:
            continue
        semantic_probs = dict.fromkeys(_SEMANTICS, 0.0)
        for letter, p in letter_probs.items():
            sem = option_semantics.get(letter)
            if sem in semantic_probs:
                semantic_probs[sem] += p
        by_condition[r["particle_condition"]].append(semantic_probs)

    result = {}
    for condition in ("bare", "ba", "ma"):
        profiles = by_condition.get(condition, [])
        n = len(profiles)
        mean_profile = (
            {sem: sum(p[sem] for p in profiles) / n for sem in _SEMANTICS} if n else None
        )
        result[condition] = {"n_with_logprobs": n, "mean_semantic_probability": mean_profile}
    return result
