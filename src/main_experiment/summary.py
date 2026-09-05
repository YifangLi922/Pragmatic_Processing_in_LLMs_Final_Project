"""Operational run report (calls made, parse-failure rate per model, models
needing attention) -- not the aggregate/delta analysis the user is
deferring until after reviewing raw results. Prints only; writes nothing.
"""

import json
from collections import Counter

# A model whose parse-failure rate clears this is called out explicitly --
# not auto-excluded, just flagged for a human look (mirrors this project's
# consistent "flag, don't decide" convention elsewhere).
HIGH_FAILURE_RATE_THRESHOLD = 0.30


def load_records(jsonl_path: str) -> list[dict]:
    with open(jsonl_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_run_report(records: list[dict], n_items: int, n_models: int) -> dict:
    total_expected = n_items * n_models
    n_done = len(records)

    by_model_total = Counter(r["model"] for r in records)
    by_model_parse_failed = Counter(r["model"] for r in records if r["parse_failed"])
    by_model_error = Counter(r["model"] for r in records if r["raw_response"].startswith("[ERROR]"))

    per_model = {}
    for model in sorted(by_model_total):
        total = by_model_total[model]
        parse_failed = by_model_parse_failed.get(model, 0)
        errors = by_model_error.get(model, 0)
        per_model[model] = {
            "n_done": total,
            "n_parse_failed": parse_failed,
            "parse_failure_rate": parse_failed / total if total else None,
            "n_api_errors": errors,
            "api_error_rate": errors / total if total else None,
        }

    flagged = [
        model
        for model, stats in per_model.items()
        if (stats["parse_failure_rate"] or 0) >= HIGH_FAILURE_RATE_THRESHOLD
        or (stats["api_error_rate"] or 0) >= HIGH_FAILURE_RATE_THRESHOLD
    ]

    return {
        "total_expected": total_expected,
        "n_done": n_done,
        "n_missing": total_expected - n_done,
        "per_model": per_model,
        "flagged_models": flagged,
    }


def print_run_report(report: dict) -> None:
    print(f"\nTotal expected calls: {report['total_expected']}")
    print(f"Completed (written to disk): {report['n_done']}")
    print(f"Missing (not yet attempted or skipped by circuit breaker): {report['n_missing']}")
    print("\nPer-model parse-failure / API-error rate:")
    for model, stats in report["per_model"].items():
        print(
            f"  {model}: {stats['n_done']} done, "
            f"parse_failed {stats['n_parse_failed']} ({stats['parse_failure_rate']:.1%}), "
            f"api_errors {stats['n_api_errors']} ({stats['api_error_rate']:.1%})"
        )
    if report["flagged_models"]:
        print(f"\nWARNING -- models needing a look (>= {HIGH_FAILURE_RATE_THRESHOLD:.0%} parse-failure or API-error rate): "
              + ", ".join(report["flagged_models"]))
    else:
        print("\nNo model crossed the parse-failure/API-error attention threshold.")
