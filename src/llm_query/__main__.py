"""CLI entry point for Module 4.

Examples:
    # smoke test, no API key needed:
    python -m src.llm_query --items data/fake_items.json \\
        --output output/fake_mock_results.jsonl --mock

    # real run against a subset of models:
    python -m src.llm_query --items data/fake_items.json \\
        --output output/fake_openrouter_results.jsonl \\
        --models deepseek-v3,gemini-3-flash-preview
"""

import argparse
from pathlib import Path

from dotenv import load_dotenv

from .runner import run


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Module 4: query LLMs over the item set.")
    parser.add_argument("--items", required=True, help="Path to a JSON file of items.")
    parser.add_argument("--output", required=True, help="JSONL checkpoint/results file.")
    parser.add_argument(
        "--models", default=None,
        help="Comma-separated model names from config/models.yaml (default: all).",
    )
    parser.add_argument("--config", default=None, help="Path to models.yaml (default: config/models.yaml).")
    parser.add_argument(
        "--mock", action="store_true",
        help="Use the MockProvider instead of calling OpenRouter (no API key needed).",
    )
    args = parser.parse_args()

    model_names = args.models.split(",") if args.models else None

    provider_factory = None
    if args.mock:
        from .providers.mock import MockProvider

        provider_factory = lambda model_cfg: MockProvider()

    output_path = run(
        items_path=Path(args.items),
        output_path=Path(args.output),
        model_names=model_names,
        config_path=Path(args.config) if args.config else None,
        provider_factory=provider_factory,
    )
    print(f"Results written to {output_path}")


if __name__ == "__main__":
    main()
