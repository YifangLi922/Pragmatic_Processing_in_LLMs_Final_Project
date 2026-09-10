"""CLI: core3 LOO human baseline on the frozen 20 confirmatory families.

Usage:
    python -m src.human_baseline_core3 \\
        --reconstructed data/reconstructed_5ann.json \\
        --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \\
        --output-dir results/human_baseline_core3
"""

import argparse
import csv
import json
import os

from src.agreement.loo_baseline import loo_human_baseline

from .concordance import core3_concordance
from .filter import load_keep_family_ids, restrict_to_core3_keep_families

_CONDITIONS = ("bare", "ba", "ma")


def _fmt_pct(value: float | None) -> str:
    return f"{value:.1%}" if value is not None else "n/a"


def _render_comparison_notes(comparison_rows: list[dict]) -> str:
    lines = [
        "# Human baseline: LOO vs. concordance",
        "",
        "Two human baselines on the same frozen 20 confirmatory families, "
        "answering different questions -- read side by side, not as "
        "duplicates:",
        "",
        "- **human_LOO** (leave-one-annotator-out): for each held-out "
        "core3 annotator, the majority of the *other two* becomes that "
        "fold's temporary gold, and the held-out person is scored against "
        "it; folds are averaged. On a 2:1 split, whichever annotator is in "
        "the minority is *always* scored as a miss for that fold -- LOO "
        "structurally cannot credit a minority vote, even when it happens "
        "to match the real gold.",
        "- **human_concordance**: for each item, the fraction of all three "
        "core3 annotators whose answer matches the actual gold, averaged "
        "within condition. This asks the same question model accuracy "
        "does (\"what fraction of answerers picked gold?\") on every item, "
        "including 2:1 splits -- it is the metric directly comparable to "
        "model accuracy, and the primary human reference point.",
        "",
        "| condition | human_LOO | human_concordance |",
        "|---|---|---|",
    ]
    for row in comparison_rows:
        lines.append(
            f"| {row['condition']} | {_fmt_pct(row['human_LOO'])} "
            f"({row['human_LOO_n_folds_used']}/{row['human_LOO_n_folds_total']} folds) "
            f"| {_fmt_pct(row['human_concordance'])} ({row['human_concordance_n_items']} items) |"
        )
    lines.append("")
    return "\n".join(lines)


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
    gold_by_item = {row["item_id"]: row["gold_semantic"] for row in frozen_rows}

    result = loo_human_baseline(restricted_items)
    concordance = core3_concordance(restricted_items, gold_by_item)

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

    # ---- LOO vs. concordance comparison (two different questions -- see concordance.py) ----
    comparison_rows = []
    for condition in ("overall", *_CONDITIONS):
        loo_stats = result[condition]
        conc_stats = concordance[condition]
        comparison_rows.append(
            {
                "condition": condition,
                "human_LOO": loo_stats["accuracy"],
                "human_LOO_n_folds_used": loo_stats["n_folds_used"],
                "human_LOO_n_folds_total": loo_stats["n_folds_total"],
                "human_concordance": conc_stats["accuracy"],
                "human_concordance_n_items": conc_stats["n_items"],
            }
        )

    comparison_path = os.path.join(args.output_dir, "human_baseline_comparison.csv")
    with open(comparison_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "condition",
                "human_LOO",
                "human_LOO_n_folds_used",
                "human_LOO_n_folds_total",
                "human_concordance",
                "human_concordance_n_items",
            ],
        )
        writer.writeheader()
        writer.writerows(comparison_rows)

    notes_path = os.path.join(args.output_dir, "human_baseline_comparison.md")
    with open(notes_path, "w", encoding="utf-8") as f:
        f.write(_render_comparison_notes(comparison_rows))

    print(f"\nLOO vs. concordance comparison written to {comparison_path} and {notes_path}")


if __name__ == "__main__":
    main()
