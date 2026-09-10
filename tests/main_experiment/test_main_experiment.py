"""Unit tests for the main experiment (src/main_experiment). Pure Python /
tmp_path fixtures throughout -- no real model calls.
"""

import json

from src.llm_query.prompt import build_prompt
from src.llm_query.providers.base import LLMResponse
from src.llm_query.providers.mock import MockProvider
from src.llm_query.runner import run_items
from src.main_experiment.csv_export import jsonl_to_csv
from src.main_experiment.record import build_main_record
from src.main_experiment.summary import build_run_report


def _item(item_id="F01_bare", gold_letter="C", set_name="confirmatory"):
    return {
        "item_id": item_id,
        "family_id": "F01",
        "particle_condition": "bare",
        "context": "context",
        "sentence": "target sentence",
        "question": "question",
        "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
        "option_semantics": {"A": "distractor", "B": "neutral", "C": "statement", "D": "confirmation"},
        "set": set_name,
        "gold_letter": gold_letter,
        "gold_semantic": "statement",
        "collapse_pair": None,
        "collapse_label": None,
    }


def _response(raw="答案：C", error=None):
    return LLMResponse(raw_response=raw, logprobs=None, prompt_tokens=10, completion_tokens=2, error=error)


def _model_cfg(name="deepseek-v3"):
    return {"name": name, "provider": "openrouter", "model_group": "chinese_strong"}


# ---- record.py ---------------------------------------------------------


def test_build_main_record_hit_gold_true():
    item = _item(gold_letter="C")
    record = build_main_record(item, _model_cfg(), "prompt text", "2026-01-01", 0.0, _response(), "C")
    assert record["hit_gold"] is True
    assert record["parse_failed"] is False
    assert record["parsed_choice_semantic"] == "statement"
    assert record["set"] == "confirmatory"
    assert record["condition"] == "bare"
    assert record["model"] == "deepseek-v3"
    assert "T" in record["timestamp"]  # ISO 8601


def test_build_main_record_hit_gold_false():
    item = _item(gold_letter="C")
    record = build_main_record(item, _model_cfg(), "prompt", "2026-01-01", 0.0, _response(raw="答案：B"), "B")
    assert record["hit_gold"] is False


def test_build_main_record_parse_failure():
    item = _item()
    record = build_main_record(item, _model_cfg(), "prompt", "2026-01-01", 0.0, _response(raw="我不确定"), None)
    assert record["parse_failed"] is True
    assert record["hit_gold"] is False
    assert record["parsed_choice_semantic"] is None


def test_build_main_record_api_error_prefixed_into_raw_response():
    item = _item()
    record = build_main_record(
        item, _model_cfg(), "prompt", "2026-01-01", 0.0,
        _response(raw="", error="HTTP 429: rate limited"), None,
    )
    assert record["raw_response"].startswith("[ERROR]")
    assert "429" in record["raw_response"]
    assert record["parse_failed"] is True


# ---- integration: run_items + build_main_record + build_prompt ------------


def test_run_items_with_main_record_builder_end_to_end(tmp_path):
    output_path = tmp_path / "main_results.jsonl"
    items = [_item("F01_bare", gold_letter="C"), _item("F01_ba", gold_letter="D", set_name="exploratory")]

    run_items(
        items=items, output_path=output_path, model_names=["deepseek-v3"],
        provider_factory=lambda cfg: MockProvider(), sleep_fn=lambda s: None,
        prompt_builder=build_prompt, record_builder=build_main_record,
    )

    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().splitlines()]
    assert len(records) == 2
    assert {r["item_id"] for r in records} == {"F01_bare", "F01_ba"}
    assert {r["set"] for r in records} == {"confirmatory", "exploratory"}
    assert all("hit_gold" in r and "timestamp" in r for r in records)


# ---- csv_export.py ----------------------------------------------------------


def test_jsonl_to_csv_roundtrip(tmp_path):
    jsonl_path = tmp_path / "main_results.jsonl"
    rows = [
        {"set": "confirmatory", "family_id": "F01", "item_id": "F01_bare", "condition": "bare",
         "model": "deepseek-v3", "raw_response": "C", "parsed_choice_letter": "C",
         "parsed_choice_semantic": "statement", "gold_letter": "C", "gold_semantic": "statement",
         "hit_gold": True, "parse_failed": False, "timestamp": "2026-01-01T00:00:00+00:00"},
    ]
    jsonl_path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    csv_path = tmp_path / "main_results.csv"
    n = jsonl_to_csv(str(jsonl_path), str(csv_path))
    assert n == 1

    import csv

    with open(csv_path, encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    assert csv_rows[0]["item_id"] == "F01_bare"
    assert csv_rows[0]["hit_gold"] == "True"


# ---- summary.py ---------------------------------------------------------


def _record(model, parse_failed=False, error=False):
    return {
        "model": model,
        "parse_failed": parse_failed,
        "raw_response": "[ERROR] boom" if error else "C",
    }


def test_build_run_report_counts_and_flags_high_failure_model():
    records = (
        [_record("good-model") for _ in range(10)]
        + [_record("bad-model", parse_failed=True) for _ in range(4)]
        + [_record("bad-model", error=True) for _ in range(6)]
    )
    report = build_run_report(records, n_items=10, n_models=2)
    assert report["total_expected"] == 20
    assert report["n_done"] == 20
    assert report["n_missing"] == 0
    assert report["per_model"]["good-model"]["parse_failure_rate"] == 0.0
    assert report["per_model"]["bad-model"]["parse_failure_rate"] == 0.4
    assert report["per_model"]["bad-model"]["api_error_rate"] == 0.6
    assert "bad-model" in report["flagged_models"]
    assert "good-model" not in report["flagged_models"]


def test_build_run_report_tracks_missing_calls():
    records = [_record("model-a") for _ in range(3)]
    report = build_run_report(records, n_items=5, n_models=2)  # 10 expected, only 3 done
    assert report["total_expected"] == 10
    assert report["n_done"] == 3
    assert report["n_missing"] == 7
