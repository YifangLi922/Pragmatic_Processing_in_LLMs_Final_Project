"""Convert main_results.jsonl into main_results.csv -- a plain reshape, no
analysis. Kept separate from query.py's run loop (and re-run automatically
at the end of it) so a partial/interrupted run's CSV can always be
regenerated from whatever the jsonl currently holds without re-querying.
"""

import csv
import json

FIELDS = [
    "set",
    "family_id",
    "item_id",
    "condition",
    "model",
    "raw_response",
    "parsed_choice_letter",
    "parsed_choice_semantic",
    "gold_letter",
    "gold_semantic",
    "hit_gold",
    "parse_failed",
    "timestamp",
]


def jsonl_to_csv(jsonl_path: str, csv_path: str) -> int:
    with open(jsonl_path, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)
    return len(records)
