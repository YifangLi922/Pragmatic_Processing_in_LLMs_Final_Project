"""CLI: run the main experiment (target_sentence included) against the
same 78 frozen items and same model roster as the context-only ablation.
Query only -- no aggregate analysis, no ablation-vs-main delta (deliberate
follow-up steps once these raw results are reviewed).

Resumable: main_results.jsonl is appended to one line per (item, model) as
soon as each call returns; a rerun reads what's already there and only
queries the missing pairs. main_results.csv is regenerated (a plain reshape
of the jsonl, not a re-query) every time this finishes or is interrupted.

Usage:
    python -m src.main_experiment.query \\
        --frozen-dataset frozen_dataset/frozen_dataset.csv \\
        --frozen-exploratory frozen_dataset/frozen_exploratory.csv \\
        --reconstructed data/reconstructed_5ann.json \\
        --output-dir main_experiment_output
"""

import argparse
import os

from src.ablation.sources import load_ablation_items
from src.llm_query.config import load_config
from src.llm_query.prompt import build_prompt
from src.llm_query.runner import run_items

from .csv_export import jsonl_to_csv
from .record import build_main_record
from .summary import build_run_report, load_records, print_run_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the main experiment against the frozen dataset + exploratory set.")
    parser.add_argument("--frozen-dataset", required=True, help="Path to frozen_dataset.csv (confirmatory). Read-only.")
    parser.add_argument("--frozen-exploratory", required=True, help="Path to frozen_exploratory.csv. Read-only.")
    parser.add_argument("--reconstructed", required=True, help="Path to module 1's reconstructed items JSON (for `question`).")
    parser.add_argument("--output-dir", required=True, help="Directory for main_results.jsonl / main_results.csv.")
    parser.add_argument("--config", default=None, help="Path to config/models.yaml (default: the project's own).")
    parser.add_argument("--models", nargs="*", default=None, help="Subset of model names to run (default: full roster).")
    parser.add_argument("--max-consecutive-failures", type=int, default=10)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    jsonl_path = os.path.join(args.output_dir, "main_results.jsonl")
    csv_path = os.path.join(args.output_dir, "main_results.csv")

    items = load_ablation_items(args.frozen_dataset, args.frozen_exploratory, args.reconstructed)
    n_confirmatory = sum(1 for it in items if it["set"] == "confirmatory")
    n_exploratory = sum(1 for it in items if it["set"] == "exploratory")
    print(f"Loaded {len(items)} items ({n_confirmatory} confirmatory, {n_exploratory} exploratory).")

    try:
        run_items(
            items=items,
            output_path=jsonl_path,
            model_names=args.models,
            config_path=args.config,
            prompt_builder=build_prompt,
            record_builder=build_main_record,
            max_consecutive_failures=args.max_consecutive_failures,
            verbose=True,
        )
    finally:
        # Regenerate the CSV from whatever is on disk even on interruption,
        # so a ctrl-c or crash never leaves main_results.csv silently stale.
        if os.path.exists(jsonl_path):
            n_rows = jsonl_to_csv(jsonl_path, csv_path)
            print(f"main_results.csv regenerated: {n_rows} rows")

    print(f"main_results.jsonl: {jsonl_path}")

    config = load_config(args.config) if args.config else load_config()
    models = config["models"]
    if args.models is not None:
        models = [m for m in models if m["name"] in args.models]
    records = load_records(jsonl_path)
    report = build_run_report(records, n_items=len(items), n_models=len(models))
    print_run_report(report)


if __name__ == "__main__":
    main()
