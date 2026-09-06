"""Unit tests for main-experiment scoring (src/main_scoring). Pure Python
fixtures throughout -- CSV rows modeled as the plain string dicts
csv.DictReader would actually produce (booleans as "True"/"False" strings).
"""

from src.main_scoring.accuracy import condition_accuracy_table, margin_stratified_accuracy
from src.main_scoring.confusion import confusion_matrices_by_model
from src.main_scoring.delta import (
    build_delta_rows,
    count_missing_ablation_answer,
    update_precision_comparison,
    used_target_summary,
)
from src.main_scoring.sources import PreconditionError, check_preconditions


def _main_row(item_id, family_id, condition, set_name, model, letter, semantic, gold_letter, gold_semantic, parse_failed=False):
    return {
        "set": set_name, "family_id": family_id, "item_id": item_id, "condition": condition, "model": model,
        "raw_response": letter or "", "parsed_choice_letter": letter, "parsed_choice_semantic": semantic,
        "gold_letter": gold_letter, "gold_semantic": gold_semantic,
        "hit_gold": "True" if letter == gold_letter else "False",
        "parse_failed": "True" if parse_failed else "False",
    }


def _ablation_row(item_id, set_name, model, letter, gold_letter):
    return {
        "set": set_name, "item_id": item_id, "model": model,
        "parsed_choice_letter": letter, "gold_letter": gold_letter,
    }


# ---- sources.py: precondition check -----------------------------------------


def test_check_preconditions_passes_on_matching_data():
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement")]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelA", "B", "C")]
    check_preconditions(main_rows, ablation_rows)  # should not raise


def test_check_preconditions_fails_on_model_mismatch():
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement")]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelB", "B", "C")]
    try:
        check_preconditions(main_rows, ablation_rows)
        assert False, "expected PreconditionError"
    except PreconditionError as exc:
        assert "model sets differ" in str(exc)


def test_check_preconditions_fails_on_gold_letter_mismatch():
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement")]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelA", "B", "D")]  # gold_letter differs
    try:
        check_preconditions(main_rows, ablation_rows)
        assert False, "expected PreconditionError"
    except PreconditionError as exc:
        assert "gold_letter" in str(exc)


# ---- accuracy.py -------------------------------------------------------


def test_condition_accuracy_table_excludes_parse_failures():
    rows = [
        _main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement"),
        _main_row("F01_ba", "F01", "ba", "confirmatory", "modelA", "D", "confirmation", "D", "confirmation"),
        _main_row("F01_ma", "F01", "ma", "confirmatory", "modelA", None, None, "B", "neutral", parse_failed=True),
    ]
    table = condition_accuracy_table(rows, "confirmatory")
    assert len(table) == 1
    row = table[0]
    assert row["n_valid_overall"] == 2  # parse-failed ma row excluded
    assert row["accuracy_overall"] == 1.0
    assert row["n_valid_ma"] == 0
    assert row["accuracy_ma"] is None


def test_condition_accuracy_table_separates_sets():
    rows = [
        _main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement"),
        _main_row("F06_bare", "F06", "bare", "exploratory", "modelA", "D", "confirmation", "C", "statement"),
    ]
    confirmatory = condition_accuracy_table(rows, "confirmatory")
    exploratory = condition_accuracy_table(rows, "exploratory")
    assert confirmatory[0]["n_valid_overall"] == 1
    assert exploratory[0]["n_valid_overall"] == 1
    assert confirmatory[0]["accuracy_overall"] == 1.0
    assert exploratory[0]["accuracy_overall"] == 0.0


def test_margin_stratified_accuracy_reports_n_items_and_pooled_accuracy():
    rows = [
        _main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement"),
        _main_row("F01_bare", "F01", "bare", "confirmatory", "modelB", "D", "confirmation", "C", "statement"),
        _main_row("F02_bare", "F02", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement"),
    ]
    margin_lookup = {"F01_bare": 3, "F02_bare": 1}
    table = margin_stratified_accuracy(rows, margin_lookup)
    by_margin = {row["margin"]: row for row in table}
    assert by_margin[3]["n_items"] == 1
    assert by_margin[3]["n_valid"] == 2  # modelA + modelB both answered F01_bare
    assert by_margin[3]["accuracy"] == 0.5
    assert by_margin[1]["n_items"] == 1
    assert by_margin[1]["n_valid"] == 1
    assert by_margin[1]["accuracy"] == 1.0


# ---- delta.py -----------------------------------------------------------


def test_build_delta_rows_used_target_true_on_real_alternative():
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement")]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelA", "D", "C")]
    delta = build_delta_rows(main_rows, ablation_rows, "confirmatory")
    assert len(delta) == 1
    assert delta[0]["used_target"] is True


def test_build_delta_rows_used_target_false_on_same_answer():
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement")]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelA", "C", "C")]
    delta = build_delta_rows(main_rows, ablation_rows, "confirmatory")
    assert delta[0]["used_target"] is False


def test_build_delta_rows_excludes_pair_when_ablation_parse_failed():
    # A missing ablation answer is not "kept the same answer" -- it's no
    # comparison at all, so the pair must not appear in delta_rows.
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement")]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelA", None, "C")]
    delta = build_delta_rows(main_rows, ablation_rows, "confirmatory")
    assert delta == []


def test_build_delta_rows_excludes_main_parse_failures():
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", None, None, "C", "statement", parse_failed=True)]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelA", "D", "C")]
    delta = build_delta_rows(main_rows, ablation_rows, "confirmatory")
    assert delta == []


def test_count_missing_ablation_answer():
    main_rows = [
        _main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement"),
        _main_row("F02_bare", "F02", "bare", "confirmatory", "modelA", "D", "confirmation", "D", "confirmation"),
    ]
    ablation_rows = [
        _ablation_row("F01_bare", "confirmatory", "modelA", None, "C"),  # ablation parse-failed -- excluded
        _ablation_row("F02_bare", "confirmatory", "modelA", "D", "D"),
    ]
    counts = count_missing_ablation_answer(main_rows, ablation_rows, "confirmatory")
    assert counts == {"modelA": 1}


def test_used_target_summary_reports_rate_and_exclusions():
    delta_rows = [
        {"model": "modelA", "family_id": "F02", "used_target": True, "hit_gold": True},
        {"model": "modelA", "family_id": "F03", "used_target": False, "hit_gold": True},
    ]
    missing_counts = {"modelA": 1}
    summary = used_target_summary(delta_rows, missing_counts)
    assert summary[0]["n_valid_pairs"] == 2
    assert summary[0]["n_used_target"] == 1
    assert summary[0]["used_target_rate"] == 0.5
    assert summary[0]["n_excluded_no_ablation_answer"] == 1


def test_used_target_summary_includes_model_with_zero_valid_pairs():
    # A model whose every ablation call failed to parse has no delta rows at
    # all, but should still surface (with n_valid_pairs=0) rather than
    # silently vanishing from the table.
    summary = used_target_summary([], {"all-refused-model": 5})
    assert summary[0]["model"] == "all-refused-model"
    assert summary[0]["n_valid_pairs"] == 0
    assert summary[0]["used_target_rate"] is None
    assert summary[0]["n_excluded_no_ablation_answer"] == 5


def test_update_precision_comparison_with_and_without_sensitivity():
    delta_rows = [
        {"model": "modelA", "family_id": "F01", "used_target": True, "hit_gold": True},
        {"model": "modelA", "family_id": "F02", "used_target": True, "hit_gold": False},
        {"model": "modelA", "family_id": "F03", "used_target": False, "hit_gold": True},
    ]
    raw_by_model = {"modelA": (3, 2 / 3)}

    no_sensitivity = update_precision_comparison(delta_rows, raw_by_model, None)
    assert no_sensitivity[0]["update_precision"] == 0.5  # 1 hit / 2 used_target rows
    assert no_sensitivity[0]["n_updates"] == 2
    assert no_sensitivity[0]["update_precision_sensitivity"] is None

    with_sensitivity = update_precision_comparison(delta_rows, raw_by_model, shortcut_families={"F01"})
    assert with_sensitivity[0]["n_updates_sensitivity"] == 1  # F01 excluded, F02 remains
    assert with_sensitivity[0]["update_precision_sensitivity"] == 0.0


# ---- confusion.py -------------------------------------------------------


def test_confusion_matrices_by_model_counts_and_rownorm():
    rows = [
        _main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement"),
        _main_row("F01_ba", "F01", "ba", "confirmatory", "modelA", "D", "confirmation", "D", "confirmation"),
        _main_row("F02_bare", "F02", "bare", "confirmatory", "modelA", "B", "neutral", "C", "statement"),
        _main_row("F02_ba", "F02", "ba", "confirmatory", "modelA", None, None, "C", "statement", parse_failed=True),
    ]
    matrices = confusion_matrices_by_model(rows)
    modelA = matrices["modelA"]
    assert modelA["n_scored"] == 3  # parse-failed row excluded
    assert modelA["raw"]["statement"]["statement"] == 1
    assert modelA["raw"]["statement"]["neutral"] == 1
    assert modelA["raw"]["confirmation"]["confirmation"] == 1
    assert modelA["rownorm"]["statement"]["statement"] == 0.5
    assert modelA["rownorm"]["statement"]["neutral"] == 0.5


# ---- design_gold_following.py -------------------------------------------


def test_design_gold_following_table():
    from src.main_scoring.design_gold_following import design_gold_following_table

    shifted_ma_items = {"F11_ma": "neutral", "F12_ma": "neutral"}
    rows = [
        _main_row("F11_ma", "F11", "ma", "exploratory", "modelA", "B", "neutral", "D", "confirmation"),
        _main_row("F12_ma", "F12", "ma", "exploratory", "modelA", "D", "confirmation", "D", "confirmation"),
        # not a shifted item -- must be excluded from the computation
        _main_row("F06_ma", "F06", "ma", "exploratory", "modelA", "B", "neutral", "B", "neutral"),
        # parse-failed shifted item -- excluded from both numerator and denominator
        _main_row("F11_ma", "F11", "ma", "exploratory", "modelB", None, None, "D", "confirmation", parse_failed=True),
    ]
    table = design_gold_following_table(rows, shifted_ma_items)
    by_model = {r["model"]: r for r in table}

    assert by_model["modelA"]["n_shifted_items"] == 2
    assert by_model["modelA"]["n_matches_design_gold"] == 1  # F11_ma matched design (neutral), F12_ma did not
    assert by_model["modelA"]["design_gold_following_rate"] == 0.5
    assert "modelB" not in by_model  # its only shifted-item row was parse-failed


def test_load_shifted_ma_items(tmp_path):
    import csv

    from src.main_scoring.sources import load_shifted_ma_items

    path = tmp_path / "frozen_exploratory.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "condition", "gold_shifted", "design_gold_semantic"])
        writer.writeheader()
        writer.writerow({"item_id": "F11_ma", "condition": "ma", "gold_shifted": "True", "design_gold_semantic": "neutral"})
        writer.writerow({"item_id": "F06_ma", "condition": "ma", "gold_shifted": "False", "design_gold_semantic": "neutral"})
        writer.writerow({"item_id": "F11_ba", "condition": "ba", "gold_shifted": "True", "design_gold_semantic": "confirmation"})

    result = load_shifted_ma_items(str(path))
    assert result == {"F11_ma": "neutral"}  # only ma + gold_shifted=True
