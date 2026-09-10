"""Unit tests for Module 5 (src/scoring). Pure Python fixtures throughout --
constructs a tiny fake dataset with a known expected scoring outcome and
checks the numbers exactly, the same style as tests/test_module2.py and
tests/test_module3.py.
"""

from src.gold.exclusion import evaluate_families
from src.scoring.accuracy import accuracy_with_ci, condition_accuracy, wilson_ci
from src.scoring.confusion import confusion_matrix
from src.scoring.join import build_scoreboard
from src.scoring.logprob_shift import semantic_probability_profile
from src.scoring.pair_family_success import family_success, pair_success
from src.scoring.report import build_all_scorecards

OPTS = {"A": "neutral", "B": "confirmation", "C": "distractor", "D": "statement"}


def _item(item_id, family_id, condition, gold_semantic):
    # 4 annotators unanimous on gold_semantic so evaluate_families() gives a clean 4:0 gold
    return {
        "item_id": item_id,
        "family_id": family_id,
        "particle_condition": condition,
        "option_semantics": OPTS,
        "annotations": [
            {"annotator_id": f"A{i}", "answer_semantic": gold_semantic, "naturalness": 5,
             "hesitation": 0, "no_valid_option": 0}
            for i in range(1, 5)
        ],
    }


def _two_clean_families():
    # F01: gold bare=statement, ba=confirmation, ma=neutral (matches designed pattern)
    # F02: same pattern, different family
    items = [
        _item("F01_bare", "F01", "bare", "statement"),
        _item("F01_ba", "F01", "ba", "confirmation"),
        _item("F01_ma", "F01", "ma", "neutral"),
        _item("F02_bare", "F02", "bare", "statement"),
        _item("F02_ba", "F02", "ba", "confirmation"),
        _item("F02_ma", "F02", "ma", "neutral"),
    ]
    return items


def _result(item_id, family_id, condition, model_name, answer_semantic, answer_letter="D", error=None, **extra):
    letter_for = {v: k for k, v in OPTS.items()}
    return {
        "model_name": model_name,
        "model_group": "test_group",
        "item_id": item_id,
        "family_id": family_id,
        "particle_condition": condition,
        "model_answer_letter": letter_for.get(answer_semantic, answer_letter) if answer_semantic else None,
        "model_answer_semantic": answer_semantic,
        "error": error,
        **{f"logprob_{L}": None for L in "ABCD"},
        **extra,
    }


# ---- accuracy.py -------------------------------------------------------------


def test_wilson_ci_empty_n_returns_none():
    assert wilson_ci(0, 0) == (None, None)


def test_wilson_ci_bounds_within_unit_interval():
    lo, hi = wilson_ci(9, 10)
    assert 0.0 <= lo < 0.9 < hi <= 1.0


def test_accuracy_with_ci_basic():
    records = [{"correct": True}, {"correct": True}, {"correct": False}, {"correct": True}]
    result = accuracy_with_ci(records)
    assert result["n"] == 4
    assert result["n_correct"] == 3
    assert result["accuracy"] == 0.75


def test_condition_accuracy_splits_by_condition():
    scored = [
        {"particle_condition": "bare", "correct": True},
        {"particle_condition": "bare", "correct": True},
        {"particle_condition": "ba", "correct": False},
    ]
    result = condition_accuracy(scored)
    assert result["bare"]["accuracy"] == 1.0
    assert result["ba"]["accuracy"] == 0.0
    assert result["ma"]["n"] == 0
    assert result["overall"]["n"] == 3


# ---- join.py -------------------------------------------------------------


def test_build_scoreboard_all_correct():
    items = _two_clean_families()
    gold_results, family_decisions = evaluate_families(items)

    model_results = [
        _result("F01_bare", "F01", "bare", "modelX", "statement"),
        _result("F01_ba", "F01", "ba", "modelX", "confirmation"),
        _result("F01_ma", "F01", "ma", "modelX", "neutral"),
        _result("F02_bare", "F02", "bare", "modelX", "statement"),
        _result("F02_ba", "F02", "ba", "modelX", "confirmation"),
        _result("F02_ma", "F02", "ma", "modelX", "neutral"),
    ]

    scored_by_model, skipped = build_scoreboard(items, model_results, gold_results, family_decisions)
    assert skipped == []
    assert len(scored_by_model["modelX"]) == 6
    assert all(r["correct"] for r in scored_by_model["modelX"])


def test_build_scoreboard_excludes_errored_and_scores_unparseable_as_incorrect():
    items = _two_clean_families()
    gold_results, family_decisions = evaluate_families(items)

    model_results = [
        _result("F01_bare", "F01", "bare", "modelX", "statement"),
        _result("F01_ba", "F01", "ba", "modelX", None, error="HTTP 429"),  # excluded: infra error
        _result("F01_ma", "F01", "ma", "modelX", None),  # scored: unparseable -> incorrect
        _result("F02_bare", "F02", "bare", "modelX", "confirmation"),  # scored: wrong answer
        _result("F02_ba", "F02", "ba", "modelX", "confirmation"),
        _result("F02_ma", "F02", "ma", "modelX", "neutral"),
    ]

    scored_by_model, skipped = build_scoreboard(items, model_results, gold_results, family_decisions)
    assert len(skipped) == 1
    assert skipped[0]["reason"] == "call_error"

    scored = scored_by_model["modelX"]
    assert len(scored) == 5  # everything except the errored call
    unparseable = next(r for r in scored if r["item_id"] == "F01_ma")
    assert unparseable["unparseable"] is True
    assert unparseable["correct"] is False
    wrong = next(r for r in scored if r["item_id"] == "F02_bare")
    assert wrong["correct"] is False


def test_build_scoreboard_excludes_non_retained_family():
    # F03 has a gold collision (bare and ba both "statement") -> excluded family
    items = _two_clean_families() + [
        {**_item("F03_bare", "F03", "bare", "statement")},
        {**_item("F03_ba", "F03", "ba", "statement")},
        {**_item("F03_ma", "F03", "ma", "neutral")},
    ]
    gold_results, family_decisions = evaluate_families(items)
    model_results = [_result("F03_bare", "F03", "bare", "modelX", "statement")]

    scored_by_model, skipped = build_scoreboard(items, model_results, gold_results, family_decisions)
    assert scored_by_model == {}
    assert skipped[0]["reason"] == "family_not_retained"


# ---- pair_family_success.py -------------------------------------------------


def test_pair_and_family_success():
    scored = [
        {"family_id": "F01", "particle_condition": "bare", "correct": True},
        {"family_id": "F01", "particle_condition": "ba", "correct": True},
        {"family_id": "F01", "particle_condition": "ma", "correct": True},
        {"family_id": "F02", "particle_condition": "bare", "correct": True},
        {"family_id": "F02", "particle_condition": "ba", "correct": False},
        {"family_id": "F02", "particle_condition": "ma", "correct": True},
    ]
    pairs = pair_success(scored)
    assert pairs["bare_ba"] == {"n_families": 2, "n_success": 1, "rate": 0.5}
    assert pairs["bare_ma"] == {"n_families": 2, "n_success": 2, "rate": 1.0}

    fam = family_success(scored)
    assert fam == {"n_families": 2, "n_success": 1, "rate": 0.5}


# ---- confusion.py -------------------------------------------------------------


def test_confusion_matrix_counts_by_condition():
    scored = [
        {"particle_condition": "ba", "model_answer_semantic": "confirmation"},
        {"particle_condition": "ba", "model_answer_semantic": "neutral"},
        {"particle_condition": "ba", "model_answer_semantic": None},
    ]
    matrix = confusion_matrix(scored)
    assert matrix["ba"]["counts"]["confirmation"] == 1
    assert matrix["ba"]["counts"]["neutral"] == 1
    assert matrix["ba"]["counts"]["unparseable"] == 1
    assert matrix["bare"]["n"] == 0


# ---- logprob_shift.py -------------------------------------------------------------


def test_semantic_probability_profile_skips_records_without_full_logprobs():
    scored = [
        {"particle_condition": "bare", "option_semantics": OPTS,
         "logprob_A": -3.0, "logprob_B": -2.0, "logprob_C": -4.0, "logprob_D": -0.1},
        {"particle_condition": "bare", "option_semantics": OPTS,
         "logprob_A": None, "logprob_B": -2.0, "logprob_C": -4.0, "logprob_D": -0.1},  # missing A -> skipped
    ]
    profile = semantic_probability_profile(scored)
    assert profile["bare"]["n_with_logprobs"] == 1
    assert profile["ma"]["n_with_logprobs"] == 0
    assert profile["ma"]["mean_semantic_probability"] is None
    total = sum(profile["bare"]["mean_semantic_probability"].values())
    assert abs(total - 1.0) < 1e-9


# ---- report.py -------------------------------------------------------------


def test_build_all_scorecards_end_to_end():
    items = _two_clean_families()
    gold_results, family_decisions = evaluate_families(items)
    model_results = [
        _result("F01_bare", "F01", "bare", "modelX", "statement"),
        _result("F01_ba", "F01", "ba", "modelX", "confirmation"),
        _result("F01_ma", "F01", "ma", "modelX", "confirmation"),  # wrong
        _result("F02_bare", "F02", "bare", "modelX", "statement"),
        _result("F02_ba", "F02", "ba", "modelX", "confirmation"),
        _result("F02_ma", "F02", "ma", "modelX", "neutral"),
    ]
    report = build_all_scorecards(items, model_results, gold_results, family_decisions)
    card = report["scorecards"]["modelX"]
    assert card["n_scored"] == 6
    assert card["condition_accuracy"]["overall"]["n_correct"] == 5
    assert card["family_success"]["n_success"] == 1  # only F02 went 3/3
