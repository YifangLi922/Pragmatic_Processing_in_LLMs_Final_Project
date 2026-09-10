"""Unit tests for the context-only ablation (src/ablation). Pure Python /
tmp_path fixtures throughout -- no real model calls, no real frozen CSVs.
"""

import csv

from src.ablation.analysis import (
    build_collapse_pair_check,
    build_item_summary_rows,
    build_result_rows,
)
from src.ablation.report import render_set_summary
from src.ablation.sources import load_ablation_items, parse_option_semantic_map


# ---- sources.py -------------------------------------------------------------


def test_parse_option_semantic_map_roundtrip():
    assert parse_option_semantic_map("A:distractor|B:neutral|C:statement|D:confirmation") == {
        "A": "distractor",
        "B": "neutral",
        "C": "statement",
        "D": "confirmation",
    }


def _write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


_FROZEN_FIELDS = [
    "family_id", "item_id", "condition", "context_text", "target_sentence",
    "option_A", "option_B", "option_C", "option_D", "option_semantic_map",
    "gold_semantic", "gold_letter", "design_gold_semantic", "gold_shifted",
    "margin", "stable_keep_all_pools",
]


def test_load_ablation_items_joins_question_and_tags_set(tmp_path):
    import json

    reconstructed = [
        {"item_id": "F01_bare", "question": "小周说这句话时，最接近下面哪种态度？"},
        {"item_id": "F06_ba", "question": "佳佳说这句话时，最接近下面哪种态度？"},
    ]
    reconstructed_path = tmp_path / "reconstructed.json"
    reconstructed_path.write_text(json.dumps(reconstructed), encoding="utf-8")

    frozen_path = tmp_path / "frozen_dataset.csv"
    _write_csv(
        frozen_path, _FROZEN_FIELDS,
        [{
            "family_id": "F01", "item_id": "F01_bare", "condition": "bare",
            "context_text": "context", "target_sentence": "sentence",
            "option_A": "a", "option_B": "b", "option_C": "c", "option_D": "d",
            "option_semantic_map": "A:distractor|B:neutral|C:statement|D:confirmation",
            "gold_semantic": "statement", "gold_letter": "C", "design_gold_semantic": "statement",
            "gold_shifted": "False", "margin": "3", "stable_keep_all_pools": "True",
        }],
    )
    exploratory_path = tmp_path / "frozen_exploratory.csv"
    _write_csv(
        exploratory_path, _FROZEN_FIELDS + ["collapse_pair", "collapse_label"],
        [{
            "family_id": "F06", "item_id": "F06_ba", "condition": "ba",
            "context_text": "context2", "target_sentence": "sentence2",
            "option_A": "a", "option_B": "b", "option_C": "c", "option_D": "d",
            "option_semantic_map": "A:distractor|B:statement|C:confirmation|D:neutral",
            "gold_semantic": "statement", "gold_letter": "B", "design_gold_semantic": "confirmation",
            "gold_shifted": "True", "margin": "1", "stable_keep_all_pools": "False",
            "collapse_pair": "bare=ba", "collapse_label": "statement",
        }],
    )

    items = load_ablation_items(str(frozen_path), str(exploratory_path), str(reconstructed_path))
    by_id = {it["item_id"]: it for it in items}

    assert by_id["F01_bare"]["set"] == "confirmatory"
    assert by_id["F01_bare"]["question"] == "小周说这句话时，最接近下面哪种态度？"
    assert by_id["F01_bare"]["option_semantics"]["C"] == "statement"
    assert by_id["F01_bare"]["collapse_pair"] is None

    assert by_id["F06_ba"]["set"] == "exploratory"
    assert by_id["F06_ba"]["collapse_pair"] == "bare=ba"
    assert by_id["F06_ba"]["gold_letter"] == "B"


# ---- analysis.py: build_result_rows -----------------------------------------


def _item(item_id, family_id, condition, set_name, gold_letter, gold_semantic, collapse_pair=None, collapse_label=None):
    return {
        "item_id": item_id, "family_id": family_id, "particle_condition": condition,
        "set": set_name, "gold_letter": gold_letter, "gold_semantic": gold_semantic,
        "collapse_pair": collapse_pair, "collapse_label": collapse_label,
    }


def _record(item_id, model_name, answer_letter, answer_semantic="statement", raw="答案：C", error=None):
    return {
        "item_id": item_id, "model_name": model_name,
        "model_answer_letter": answer_letter, "model_answer_semantic": answer_semantic if answer_letter else None,
        "raw_response": raw, "error": error,
    }


def test_build_result_rows_hit_gold_and_parse_failed():
    items_by_id = {"F01_bare": _item("F01_bare", "F01", "bare", "confirmatory", "C", "statement")}
    records = [
        _record("F01_bare", "modelA", "C"),
        _record("F01_bare", "modelB", "D", answer_semantic="confirmation"),
        _record("F01_bare", "modelC", None, raw="我不确定"),
    ]
    rows = build_result_rows(records, items_by_id)
    by_model = {r["model"]: r for r in rows}

    assert by_model["modelA"]["hit_gold"] is True
    assert by_model["modelA"]["parse_failed"] is False
    assert by_model["modelB"]["hit_gold"] is False
    assert by_model["modelC"]["hit_gold"] is False
    assert by_model["modelC"]["parse_failed"] is True
    assert all(r["set"] == "confirmatory" and r["gold_semantic"] == "statement" for r in rows)


def test_build_result_rows_carries_api_error_into_raw_response():
    items_by_id = {"F01_bare": _item("F01_bare", "F01", "bare", "confirmatory", "C", "statement")}
    records = [_record("F01_bare", "modelA", None, raw="", error="HTTP 429: rate limited")]
    rows = build_result_rows(records, items_by_id)
    assert "HTTP 429" in rows[0]["raw_response"]
    assert rows[0]["parse_failed"] is True


# ---- analysis.py: build_item_summary_rows -----------------------------------


def _result_row(item_id, family_id, condition, set_name, letter, gold_letter="C"):
    return {
        "set": set_name, "family_id": family_id, "item_id": item_id, "condition": condition,
        "model": f"model-{letter}-{id(letter)}",  # uniqueness not required by the function
        "parsed_choice_letter": letter, "hit_gold": letter == gold_letter,
    }


def test_item_summary_shortcut_risk_and_converged_thresholds():
    # 6 models: 4/6 hit gold (== 2/3 exactly) -> shortcut_risk True.
    rows = (
        [dict(_result_row("F01_bare", "F01", "bare", "confirmatory", "C"), model=f"m{i}") for i in range(4)]
        + [dict(_result_row("F01_bare", "F01", "bare", "confirmatory", "D"), model=f"m{i}") for i in range(4, 6)]
    )
    summary = build_item_summary_rows(rows)
    assert len(summary) == 1
    row = summary[0]
    assert row["n_models"] == 6
    assert row["n_hit_gold"] == 4
    assert row["hit_rate"] == 4 / 6
    assert row["shortcut_risk"] is True  # exactly at the >=2/3 boundary
    assert row["modal_choice"] == "C"
    assert row["modal_choice_count"] == 4
    assert row["converged"] is True


def test_item_summary_below_threshold_is_not_shortcut_risk():
    # 3/6 hit gold -> below 2/3, shortcut_risk False.
    rows = (
        [dict(_result_row("F02_ba", "F02", "ba", "confirmatory", "C"), model=f"m{i}") for i in range(3)]
        + [dict(_result_row("F02_ba", "F02", "ba", "confirmatory", "D"), model=f"m{i}") for i in range(3, 6)]
    )
    summary = build_item_summary_rows(rows)
    assert summary[0]["shortcut_risk"] is False


def test_item_summary_modal_choice_tie_break_alphabetical():
    rows = [
        dict(_result_row("F03_ma", "F03", "ma", "confirmatory", "D"), model="m1"),
        dict(_result_row("F03_ma", "F03", "ma", "confirmatory", "B"), model="m2"),
    ]
    summary = build_item_summary_rows(rows)
    assert summary[0]["modal_choice"] == "B"  # tie between B and D -> alphabetically first
    assert summary[0]["modal_choice_count"] == 1


def test_item_summary_all_parse_failures_has_no_modal_choice():
    rows = [dict(_result_row("F04_bare", "F04", "bare", "confirmatory", None), model="m1")]
    summary = build_item_summary_rows(rows)
    assert summary[0]["modal_choice"] is None
    assert summary[0]["modal_choice_count"] == 0
    assert summary[0]["shortcut_risk"] is False


# ---- analysis.py: build_collapse_pair_check ---------------------------------


def test_build_collapse_pair_check_matches_and_mismatches():
    item_summary_rows = [
        {"set": "exploratory", "family_id": "F12", "condition": "ba", "modal_choice": "C"},
        {"set": "exploratory", "family_id": "F12", "condition": "ma", "modal_choice": "C"},
        {"set": "exploratory", "family_id": "F06", "condition": "bare", "modal_choice": "B"},
        {"set": "exploratory", "family_id": "F06", "condition": "ba", "modal_choice": "D"},
    ]
    collapse_lookup = {
        "F12": {"collapse_pair": "ba=ma", "collapse_label": "confirmation"},
        "F06": {"collapse_pair": "bare=ba", "collapse_label": "statement"},
    }
    rows = build_collapse_pair_check(item_summary_rows, collapse_lookup)
    by_family = {r["family_id"]: r for r in rows}

    assert by_family["F12"]["same_modal"] is True
    assert by_family["F12"]["cond1_modal"] == "C" and by_family["F12"]["cond2_modal"] == "C"
    assert by_family["F06"]["same_modal"] is False
    assert by_family["F06"]["cond1_modal"] == "B" and by_family["F06"]["cond2_modal"] == "D"


# ---- report.py: render_set_summary ------------------------------------------


def test_render_set_summary_confirmatory_basic_content():
    item_summary_rows = [
        {"set": "confirmatory", "family_id": "F01", "condition": "bare", "shortcut_risk": True},
        {"set": "confirmatory", "family_id": "F02", "condition": "ba", "shortcut_risk": False},
    ]
    result_rows = [
        {"set": "confirmatory", "parse_failed": False},
        {"set": "confirmatory", "parse_failed": True},
    ]
    report = render_set_summary("confirmatory", item_summary_rows, result_rows)
    assert "shortcut_risk items: 1 / 2 (50.0%)" in report
    assert "F01 (bare)" in report
    assert "F02" not in report.split("shortcut_risk item list")[1].split("###")[0]
    assert "Parse failure rate: 1 / 2 query results (50.0%)" in report
    assert "Not comparable" not in report  # confirmatory report has no exploratory caveat


def test_render_set_summary_exploratory_includes_caveat_and_collapse_table():
    item_summary_rows = [{"set": "exploratory", "family_id": "F06", "condition": "ba", "shortcut_risk": True}]
    result_rows = [{"set": "exploratory", "parse_failed": False}]
    collapse_rows = [
        {"family_id": "F06", "collapse_pair": "bare=ba", "collapse_label": "statement",
         "cond1_modal": "B", "cond2_modal": "B", "same_modal": True}
    ]
    report = render_set_summary("exploratory", item_summary_rows, result_rows, collapse_rows)
    assert "Not comparable" in report
    assert "Collapse-pair modal-choice check" in report
    assert "1 / 1 collapsed families show the same modal choice" in report
