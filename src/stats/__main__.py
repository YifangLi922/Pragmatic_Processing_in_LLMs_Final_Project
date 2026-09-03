"""CLI entry point for Module 6: McNemar tests + the four required figures.

Usage:
    python -m src.stats \\
        --items data/reconstructed.json \\
        --results output/real_openrouter_results.jsonl \\
        --scorecards data/scorecards.json \\
        --output-dir output/figures \\
        --mcnemar-output data/mcnemar_results.json

--scorecards should be module 5's output (src.scoring.__main__); --items and
--results are needed here too because McNemar and the family x model
heatmap need each model's raw scored records, which module 5 only
aggregates into rates in scorecards.json.
"""

import argparse
import json
from pathlib import Path

from src.agreement.loo_baseline import loo_human_baseline
from src.gold.exclusion import evaluate_families
from src.scoring.join import build_scoreboard

from .mcnemar import mcnemar_by_pair
from .plots import (
    plot_condition_accuracy,
    plot_confusion_heatmap,
    plot_family_by_model_heatmap,
    plot_family_success,
    plot_model_vs_baseline,
)


def _load_jsonl(paths: list[str]) -> list[dict]:
    records = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Module 6: McNemar tests + descriptive figures.")
    parser.add_argument("--items", required=True, help="Module 1 output (reconstructed items).")
    parser.add_argument("--results", action="append", required=True, help="Module 4 output .jsonl (repeatable).")
    parser.add_argument("--scorecards", required=True, help="Module 5 output (scorecards.json).")
    parser.add_argument("--output-dir", required=True, help="Directory to write figure PNGs into.")
    parser.add_argument("--mcnemar-output", required=True, help="Where to write McNemar results (JSON).")
    args = parser.parse_args()

    with open(args.items, encoding="utf-8") as f:
        items = json.load(f)
    with open(args.scorecards, encoding="utf-8") as f:
        scoring_report = json.load(f)
    scorecards = scoring_report["scorecards"]
    model_results = _load_jsonl(args.results)

    gold_results, family_decisions = evaluate_families(items)
    scored_by_model, _ = build_scoreboard(items, model_results, gold_results, family_decisions)

    mcnemar_results = {model_name: mcnemar_by_pair(records) for model_name, records in scored_by_model.items()}
    with open(args.mcnemar_output, "w", encoding="utf-8") as f:
        json.dump(mcnemar_results, f, ensure_ascii=False, indent=2)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for model_name, card in scorecards.items():
        plot_confusion_heatmap(card["confusion_matrix"], model_name, output_dir / f"confusion_{model_name}.png")
    plot_condition_accuracy(scorecards, output_dir / "condition_accuracy.png")
    plot_family_success(scorecards, output_dir / "family_success.png")
    plot_family_by_model_heatmap(scorecards, output_dir / "family_by_model.png")

    human_baseline = loo_human_baseline(items)
    plot_model_vs_baseline(scorecards, human_baseline, output_dir / "model_vs_baseline.png")

    print(f"McNemar results for {len(mcnemar_results)} model(s) written to {args.mcnemar_output}")
    print(f"Figures written to {output_dir}/")


if __name__ == "__main__":
    main()
