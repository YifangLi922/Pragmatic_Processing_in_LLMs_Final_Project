"""Unit tests for main-experiment scoring (src/main_scoring). Pure Python
fixtures throughout -- CSV rows modeled as the plain string dicts
csv.DictReader would actually produce (booleans as "True"/"False" strings).
"""

from src.main_scoring.accuracy import condition_accuracy_table, margin_stratified_accuracy
from src.main_scoring.confusion import confusion_matrices_by_model
from src.main_scoring.delta import build_delta_rows, purified_accuracy_comparison, used_target_summary
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
    assert delta[0]["ablation_parse_failed"] is False


def test_build_delta_rows_used_target_false_on_same_answer():
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement")]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelA", "C", "C")]
    delta = build_delta_rows(main_rows, ablation_rows, "confirmatory")
    assert delta[0]["used_target"] is False


def test_build_delta_rows_used_target_true_when_ablation_parse_failed():
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", "C", "statement", "C", "statement")]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelA", None, "C")]
    delta = build_delta_rows(main_rows, ablation_rows, "confirmatory")
    assert delta[0]["used_target"] is True
    assert delta[0]["ablation_parse_failed"] is True


def test_build_delta_rows_excludes_main_parse_failures():
    main_rows = [_main_row("F01_bare", "F01", "bare", "confirmatory", "modelA", None, None, "C", "statement", parse_failed=True)]
    ablation_rows = [_ablation_row("F01_bare", "confirmatory", "modelA", "D", "C")]
    delta = build_delta_rows(main_rows, ablation_rows, "confirmatory")
    assert delta == []


def test_used_target_summary_splits_subflavors():
    delta_rows = [
        {"model": "modelA", "family_id": "F01", "used_target": True, "ablation_parse_failed": True, "hit_gold": False},
        {"model": "modelA", "family_id": "F02", "used_target": True, "ablation_parse_failed": False, "hit_gold": True},
        {"model": "modelA", "family_id": "F03", "used_target": False, "ablation_parse_failed": False, "hit_gold": True},
    ]
    summary = used_target_summary(delta_rows)
    assert summary[0]["n_valid_pairs"] == 3
    assert summary[0]["n_used_target"] == 2
    assert summary[0]["n_used_target_ablation_parse_failed"] == 1
    assert summary[0]["n_used_target_real_alternative"] == 1


def test_purified_accuracy_comparison_with_and_without_sensitivity():
    delta_rows = [
        {"model": "modelA", "family_id": "F01", "used_target": True, "ablation_parse_failed": False, "hit_gold": True},
        {"model": "modelA", "family_id": "F02", "used_target": True, "ablation_parse_failed": False, "hit_gold": False},
        {"model": "modelA", "family_id": "F03", "used_target": False, "ablation_parse_failed": False, "hit_gold": True},
    ]
    raw_by_model = {"modelA": (3, 2 / 3)}

    no_sensitivity = purified_accuracy_comparison(delta_rows, raw_by_model, None)
    assert no_sensitivity[0]["accuracy_purified"] == 0.5  # 1 hit / 2 used_target rows
    assert no_sensitivity[0]["accuracy_sensitivity"] is None

    with_sensitivity = purified_accuracy_comparison(delta_rows, raw_by_model, shortcut_families={"F01"})
    assert with_sensitivity[0]["n_valid_sensitivity"] == 1  # F01 excluded, F02 remains
    assert with_sensitivity[0]["accuracy_sensitivity"] == 0.0


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
