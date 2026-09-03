"""CLI entry point for Module 1: reconstruct + quality report.

Usage:
    python -m src.reconstruct \\
        --master "SFP标注完整版.xlsx" \\
        --annotator A1="SFP母语者标注1 经济学.xlsx" \\
        --annotator A2="SFP母语者标注2 媒体信息.xlsx" \\
        --annotator A3="SFP母语者标注3 材料科学.xlsx" \\
        --annotator A4="SFP母语者标注4 BWL.xlsx" \\
        --output data/reconstructed.json \\
        --quality-output data/quality_report.json
"""

import argparse
import json

from .annotator_table import load_annotator_table
from .build import build_dataset
from .master_table import load_master_table
from .quality import build_quality_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Module 1: reconstruct annotation data + quality report.")
    parser.add_argument("--master", required=True, help="Path to the master answer-key .xlsx file.")
    parser.add_argument(
        "--annotator",
        action="append",
        required=True,
        metavar="ID=PATH",
        help="One annotator's file, e.g. A1=path/to/file.xlsx. Repeat for each annotator.",
    )
    parser.add_argument("--output", required=True, help="Where to write the reconstructed item list (JSON).")
    parser.add_argument("--quality-output", required=True, help="Where to write the quality report (JSON).")
    args = parser.parse_args()

    annotator_paths = {}
    for entry in args.annotator:
        annotator_id, _, path = entry.partition("=")
        if not path:
            raise SystemExit(f"--annotator expects ID=PATH, got: {entry!r}")
        annotator_paths[annotator_id] = path

    master_items = load_master_table(args.master)
    annotator_data = {aid: load_annotator_table(path) for aid, path in annotator_paths.items()}

    items, warnings = build_dataset(master_items, annotator_data)
    quality_report = build_quality_report(items, list(annotator_paths.keys()))

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    with open(args.quality_output, "w", encoding="utf-8") as f:
        json.dump({"warnings": warnings, **quality_report}, f, ensure_ascii=False, indent=2)

    print(f"{len(items)} items written to {args.output}")
    print(f"{len(warnings)} data-quality warnings written to {args.quality_output}")
    for report in quality_report["per_annotator"].values():
        if report["flags"]:
            print(f"  [{report['annotator_id']}] " + "; ".join(report["flags"]))


if __name__ == "__main__":
    main()
