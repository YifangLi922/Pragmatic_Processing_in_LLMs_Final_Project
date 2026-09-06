"""CLI: core3 LOO human baseline on the frozen 20 confirmatory families.

Usage:
    python -m src.human_baseline_core3 \\
        --reconstructed data/reconstructed_5ann.json \\
        --frozen-dataset frozen_dataset/frozen_dataset.csv \\
        --output-dir human_baseline_core3_output
"""

import argparse
import csv
import json
import os

from src.agreement.loo_baseline import loo_human_baseline

from .filter import load_keep_family_ids, restrict_to_core3_keep_families

_CONDITIONS = ("bare", "ba", "ma")


def main() -> None:
    parser = argparse.ArgumentParser(description="core3 LOO human baseline on the frozen 20 KEEP families.")
    parser.add_argument("--reconstructed", required=True)
    parser.add_argument("--frozen-dataset", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    with open(args.reconstructed, encoding="utf-8") as f:
        reconstructed_items = json.load(f)
    with open(args.frozen_dataset, newline="", encoding="utf-8") as f:
        frozen_rows = list(csv.DictReader(f))

    keep_family_ids = load_keep_family_ids(frozen_rows)
    restricted_items = restrict_to_core3_keep_families(reconstructed_items, keep_family_ids)

    result = loo_human_baseline(restricted_items)

    rows = []
    for condition in ("overall", *_CONDITIONS):
        stats = result[condition]
        rows.append(
            {
                "condition": condition,
                "accuracy": stats["accuracy"],
                "n_folds_used": stats["n_folds_used"],
                "n_folds_total": stats["n_folds_total"],
            }
        )

    output_path = os.path.join(args.output_dir, "human_baseline_core3.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["condition", "accuracy", "n_folds_used", "n_folds_total"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"core3 LOO human baseline on {len(keep_family_ids)} frozen KEEP families ({len(restricted_items)} items):")
    for row in rows:
        acc = f"{row['accuracy']:.1%}" if row["accuracy"] is not None else "n/a"
        print(f"  {row['condition']}: {acc} ({row['n_folds_used']}/{row['n_folds_total']} folds)")
    print(f"\nWritten to {output_path}")


if __name__ == "__main__":
    main()
