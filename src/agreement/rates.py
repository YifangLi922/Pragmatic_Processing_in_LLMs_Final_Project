"""Module 3: descriptive quality metrics -- hesitation rate, no-valid-option
rate, naturalness distribution (plan section 6). Always split by
particle_condition (plan requirement), plus a pooled "overall" bucket.
"""

from collections import defaultdict
from statistics import mean, stdev


def _bucket_by_condition(items: list[dict]) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        for a in item["annotations"]:
            buckets[item["particle_condition"]].append(a)
            buckets["overall"].append(a)
    return buckets


def _rate(annotations: list[dict], field_name: str) -> float | None:
    flags = [1 if a.get(field_name) else 0 for a in annotations if field_name in a]
    return sum(flags) / len(flags) if flags else None


def hesitation_rate_by_condition(items: list[dict]) -> dict[str, float | None]:
    return {cond: _rate(rows, "hesitation") for cond, rows in _bucket_by_condition(items).items()}


def no_valid_option_rate_by_condition(items: list[dict]) -> dict[str, float | None]:
    return {cond: _rate(rows, "no_valid_option") for cond, rows in _bucket_by_condition(items).items()}


def naturalness_distribution_by_condition(items: list[dict]) -> dict[str, dict]:
    buckets = _bucket_by_condition(items)
    result = {}
    for cond, rows in buckets.items():
        values = [a["naturalness"] for a in rows if a.get("naturalness") is not None]
        result[cond] = {
            "n": len(values),
            "mean": mean(values) if values else None,
            "stdev": stdev(values) if len(values) > 1 else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        }
    return result
