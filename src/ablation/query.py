"""CLI: run the context-only ablation queries (the expensive, network-
dependent, resumable step -- separate from analysis so re-running the
analysis never re-spends API budget).

Usage:
    python -m src.ablation.query \\
        --frozen-dataset frozen_dataset/frozen_dataset.csv \\
        --frozen-exploratory frozen_dataset/frozen_exploratory.csv \\
        --reconstructed data/reconstructed_5ann.json \\
        --output data/ablation_raw.jsonl
"""

import argparse

from src.llm_query.prompt import build_context_only_prompt
from src.llm_query.runner import run_items

from .sources import load_ablation_items


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the context-only ablation against the main experiment's model roster.")
    parser.add_argument("--frozen-dataset", required=True, help="Path to frozen_dataset.csv (confirmatory).")
    parser.add_argument("--frozen-exploratory", required=True, help="Path to frozen_exploratory.csv.")
    parser.add_argument("--reconstructed", required=True, help="Path to module 1's reconstructed items JSON (for `question`).")
    parser.add_argument("--output", required=True, help="JSONL checkpoint file (appended to; safe to resume).")
    parser.add_argument("--config", default=None, help="Path to config/models.yaml (default: the project's own).")
    parser.add_argument("--models", nargs="*", default=None, help="Subset of model names to run (default: full roster).")
    args = parser.parse_args()

    items = load_ablation_items(args.frozen_dataset, args.frozen_exploratory, args.reconstructed)
    n_confirmatory = sum(1 for it in items if it["set"] == "confirmatory")
    n_exploratory = sum(1 for it in items if it["set"] == "exploratory")
    print(f"Loaded {len(items)} ablation items ({n_confirmatory} confirmatory, {n_exploratory} exploratory).")

    run_items(
        items=items,
        output_path=args.output,
        model_names=args.models,
        config_path=args.config,
        prompt_builder=build_context_only_prompt,
    )
    print(f"Ablation queries written to {args.output}")


if __name__ == "__main__":
    main()
