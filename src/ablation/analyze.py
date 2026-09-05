"""CLI: turn the ablation query checkpoint (from `python -m src.ablation.query`)
into all four required outputs. Pure/cheap -- safe to re-run any time
without touching the query step or spending API budget again.

Usage:
    python -m src.ablation.analyze \\
        --frozen-dataset frozen_dataset/frozen_dataset.csv \\
        --frozen-exploratory frozen_dataset/frozen_exploratory.csv \\
        --reconstructed data/reconstructed_5ann.json \\
        --raw data/ablation_raw.jsonl \\
        --output-dir ablation_output
"""

import argparse
import os

from .analysis import build_collapse_pair_check, build_item_summary_rows, build_result_rows, load_query_records
from .report import render_set_summary, write_collapse_pair_check, write_item_summary, write_result_rows
from .sources import load_ablation_items


def run_all(items: list[dict], records: list[dict], output_dir: str) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    items_by_id = {item["item_id"]: item for item in items}

    result_rows = build_result_rows(records, items_by_id)
    write_result_rows(result_rows, os.path.join(output_dir, "ablation_results.csv"))

    item_summary_rows = build_item_summary_rows(result_rows)
    write_item_summary(item_summary_rows, os.path.join(output_dir, "ablation_item_summary.csv"))

    collapse_lookup = {
        item["family_id"]: {"collapse_pair": item["collapse_pair"], "collapse_label": item["collapse_label"]}
        for item in items
        if item["set"] == "exploratory"
    }
    collapse_pair_rows = build_collapse_pair_check(item_summary_rows, collapse_lookup)
    write_collapse_pair_check(collapse_pair_rows, os.path.join(output_dir, "ablation_collapse_pair_check.csv"))

    confirmatory_report = render_set_summary("confirmatory", item_summary_rows, result_rows)
    with open(os.path.join(output_dir, "ablation_summary_confirmatory.md"), "w", encoding="utf-8") as f:
        f.write(confirmatory_report)

    exploratory_report = render_set_summary("exploratory", item_summary_rows, result_rows, collapse_pair_rows)
    with open(os.path.join(output_dir, "ablation_summary_exploratory.md"), "w", encoding="utf-8") as f:
        f.write(exploratory_report)

    return {
        "n_result_rows": len(result_rows),
        "n_items": len(item_summary_rows),
        "n_confirmatory": sum(1 for r in item_summary_rows if r["set"] == "confirmatory"),
        "n_exploratory": sum(1 for r in item_summary_rows if r["set"] == "exploratory"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze the context-only ablation query results.")
    parser.add_argument("--frozen-dataset", required=True)
    parser.add_argument("--frozen-exploratory", required=True)
    parser.add_argument("--reconstructed", required=True)
    parser.add_argument("--raw", required=True, help="JSONL checkpoint written by `python -m src.ablation.query`.")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    items = load_ablation_items(args.frozen_dataset, args.frozen_exploratory, args.reconstructed)
    records = load_query_records(args.raw)

    summary = run_all(items, records, args.output_dir)
    print(
        f"{summary['n_result_rows']} query results over {summary['n_items']} items "
        f"({summary['n_confirmatory']} confirmatory, {summary['n_exploratory']} exploratory) "
        f"written to {args.output_dir}"
    )


if __name__ == "__main__":
    main()
