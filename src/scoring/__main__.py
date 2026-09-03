"""CLI entry point for Module 5: score model results against gold.

Usage:
    python -m src.scoring \\
        --items data/reconstructed.json \\
        --results output/real_openrouter_results.jsonl \\
        --output data/scorecards.json

`--results` can be repeated (e.g. one file per model run) or point at a
single combined file; every line is a module 4 output record.

Gold and family retention are derived here by calling module 2's
evaluate_families() directly on --items (module 2 doesn't have its own
persisted gold.csv/retained_families.csv yet), so this always reflects
the current GoldConfig thresholds in src/gold/config.py.
"""

import argparse
import json

from src.gold.exclusion import evaluate_families, exclusion_report

from .report import build_all_scorecards


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
    parser = argparse.ArgumentParser(description="Module 5: score model results against gold.")
    parser.add_argument("--items", required=True, help="Module 1 output (reconstructed items).")
    parser.add_argument("--results", action="append", required=True, help="Module 4 output .jsonl (repeatable).")
    parser.add_argument("--output", required=True, help="Where to write scorecards (JSON).")
    args = parser.parse_args()

    with open(args.items, encoding="utf-8") as f:
        items = json.load(f)
    model_results = _load_jsonl(args.results)

    gold_results, family_decisions = evaluate_families(items)
    report = build_all_scorecards(items, model_results, gold_results, family_decisions)
    report["exclusion_report"] = exclusion_report(family_decisions)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Scorecards for {len(report['scorecards'])} model(s) written to {args.output}")
    for model_name, card in report["scorecards"].items():
        acc = card["condition_accuracy"]["overall"]["accuracy"]
        acc_str = f"{acc:.1%}" if acc is not None else "n/a"
        print(f"  {model_name}: overall accuracy {acc_str} (n={card['n_scored']}, unparseable={card['n_unparseable']}, errored={card['n_errored']})")


if __name__ == "__main__":
    main()
