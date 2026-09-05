"""CLI driver for the dataset freeze step.

Reads data/reconstructed_5ann.json (item text) and pool_sensitivity_output/
(core3 classification + empirical gold), joins them into frozen_dataset.csv
(core3 KEEP families) and frozen_exploratory.csv (core3 COLLAPSE_structural
families), and writes freeze_report.md.

Usage:
    python -m src.freeze \\
        --reconstructed data/reconstructed_5ann.json \\
        --pool-sensitivity-dir pool_sensitivity_output \\
        --output-dir frozen_dataset
"""

import argparse
import json
import os
from collections import Counter

from .build import build_exploratory_rows, build_frozen_rows
from .report import EXPLORATORY_FIELDS, FROZEN_FIELDS, render_freeze_report, write_frozen_csv
from .sources import read_core3_collapse_pairs, read_empirical_gold, read_gold_shifted, read_grid


def run_all(items: list[dict], grid: dict, gold_lookup: dict, collapse_lookup: dict, shifted_rows: list[dict], output_dir: str) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    frozen_rows = build_frozen_rows(items, grid, gold_lookup, target_class="KEEP")
    write_frozen_csv(frozen_rows, FROZEN_FIELDS, os.path.join(output_dir, "frozen_dataset.csv"))

    exploratory_rows = build_exploratory_rows(items, grid, gold_lookup, collapse_lookup)
    write_frozen_csv(exploratory_rows, EXPLORATORY_FIELDS, os.path.join(output_dir, "frozen_exploratory.csv"))

    class_counts = Counter(v["core3_class"] for v in grid.values())
    stable_keep_count = sum(1 for v in grid.values() if v["core3_class"] == "KEEP" and v["stable_keep_all_pools"])

    report = render_freeze_report(class_counts, shifted_rows, grid, stable_keep_count, len(grid))
    with open(os.path.join(output_dir, "freeze_report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    return {
        "frozen_rows": len(frozen_rows),
        "exploratory_rows": len(exploratory_rows),
        "class_counts": class_counts,
        "stable_keep_count": stable_keep_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze the confirmatory + exploratory datasets.")
    parser.add_argument("--reconstructed", required=True, help="Path to module 1's reconstructed items JSON.")
    parser.add_argument("--pool-sensitivity-dir", required=True, help="Directory with pool_sensitivity_output's CSVs.")
    parser.add_argument("--output-dir", required=True, help="Directory to write the frozen files into.")
    args = parser.parse_args()

    with open(args.reconstructed, encoding="utf-8") as f:
        items = json.load(f)

    grid = read_grid(os.path.join(args.pool_sensitivity_dir, "pool_sensitivity_grid.csv"))
    gold_lookup = read_empirical_gold(os.path.join(args.pool_sensitivity_dir, "empirical_gold_core3.csv"))
    collapse_lookup = read_core3_collapse_pairs(os.path.join(args.pool_sensitivity_dir, "collapse_breakdown.csv"))
    shifted_rows = read_gold_shifted(os.path.join(args.pool_sensitivity_dir, "gold_shifted_families.csv"))

    summary = run_all(items, grid, gold_lookup, collapse_lookup, shifted_rows, args.output_dir)

    print(f"frozen_dataset.csv: {summary['frozen_rows']} rows ({summary['frozen_rows'] // 3} families)")
    print(f"frozen_exploratory.csv: {summary['exploratory_rows']} rows ({summary['exploratory_rows'] // 3} families)")
    for cls in ("KEEP", "COLLAPSE", "NO_CONSENSUS", "EXCLUDE_BROKEN"):
        print(f"  {cls}: {summary['class_counts'].get(cls, 0)}")
    print(f"stable_keep_all_pools: {summary['stable_keep_count']}")


if __name__ == "__main__":
    main()
