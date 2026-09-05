"""Unit tests for the pool sensitivity grid + empirical gold (src/pool_sensitivity).
Pure Python fixtures -- no .xlsx or reconstructed.json needed.
"""

import csv

from src.pool_sensitivity.__main__ import run_all
from src.pool_sensitivity.classify import classify_family
from src.pool_sensitivity.gold import empirical_gold_row, shifted_row
from src.pool_sensitivity.majority import condition_majority, pool_majority


def _annotation(annotator_id, semantic, no_valid_option=0):
    return {"annotator_id": annotator_id, "answer_semantic": semantic, "no_valid_option": no_valid_option}


def _item(family_id, condition, annotations, gold_semantic_designed=None):
    return {
        "item_id": f"{family_id}_{condition}",
        "family_id": family_id,
        "particle_condition": condition,
        "gold_semantic_designed": gold_semantic_designed,
        "annotations": annotations,
    }


# ---- pool_majority: strict majority, not "unique plurality" ----------------


def test_pool_majority_unanimous_three():
    assert pool_majority(["neutral", "neutral", "neutral"]) == ("neutral", True)


def test_pool_majority_two_of_three():
    assert pool_majority(["neutral", "neutral", "statement"]) == ("neutral", True)


def test_pool_majority_one_one_one_invalid():
    assert pool_majority(["neutral", "statement", "confirmation"]) == (None, False)


def test_pool_majority_single_vote_insufficient():
    assert pool_majority(["neutral"]) == (None, False)


def test_pool_majority_even_pool_two_two_tie_invalid():
    assert pool_majority(["neutral", "neutral", "statement", "statement"]) == (None, False)


def test_pool_majority_three_of_four_is_majority():
    assert pool_majority(["neutral", "neutral", "neutral", "statement"]) == ("neutral", True)


def test_pool_majority_two_of_four_plurality_is_not_majority():
    # unique top label (2), but 2 is not > half of 4 -- must be rejected,
    # unlike diagnostic.core.reference_majority's "unique top" shortcut
    assert pool_majority(["neutral", "neutral", "statement", "confirmation"]) == (None, False)


def test_pool_majority_two_of_five_plurality_is_not_majority():
    assert pool_majority(["neutral", "neutral", "statement", "confirmation", "distractor"]) == (None, False)


def test_pool_majority_three_of_five_is_majority():
    assert pool_majority(["neutral", "neutral", "neutral", "statement", "confirmation"]) == ("neutral", True)


# ---- condition_majority: no-option mode A + stats --------------------------


def test_condition_majority_basic_counts_and_margin():
    item = _item(
        "F01", "bare",
        [_annotation("Media", "statement"), _annotation("Materials", "statement"), _annotation("EngLit", "neutral")],
    )
    result = condition_majority(item, ["Media", "Materials", "EngLit"])
    assert result == {"majority_label": "statement", "has_majority": True, "majority_count": 2, "pool_size": 3, "margin": 1}


def test_condition_majority_true_abstention_excluded_from_pool_size():
    item = _item(
        "F02", "ma",
        [_annotation("Media", "neutral"), _annotation("Materials", None, no_valid_option=1), _annotation("EngLit", "neutral")],
    )
    result = condition_majority(item, ["Media", "Materials", "EngLit"])
    assert result["pool_size"] == 2
    assert result["has_majority"] is True
    assert result["majority_label"] == "neutral"


def test_condition_majority_checked_but_answered_counts_under_mode_a():
    item = _item(
        "F03", "ba",
        [
            _annotation("Media", "confirmation"),
            _annotation("Materials", "statement"),
            _annotation("EngLit", "confirmation", no_valid_option=1),
        ],
    )
    result = condition_majority(item, ["Media", "Materials", "EngLit"], mode="A")
    assert result == {"majority_label": "confirmation", "has_majority": True, "majority_count": 2, "pool_size": 3, "margin": 1}


# ---- classify_family --------------------------------------------------------


def _cond_result(label, has_majority=True):
    return {"majority_label": label, "has_majority": has_majority, "majority_count": 2, "pool_size": 3, "margin": 1}


def test_classify_family_keep_three_distinct_labels():
    result = classify_family({"bare": _cond_result("statement"), "ba": _cond_result("confirmation"), "ma": _cond_result("neutral")})
    assert result["class"] == "KEEP"


def test_classify_family_no_consensus_missing_majority():
    result = classify_family(
        {"bare": _cond_result("statement"), "ba": _cond_result(None, has_majority=False), "ma": _cond_result("neutral")}
    )
    assert result["class"] == "NO_CONSENSUS"


def test_classify_family_exclude_broken_distractor_takes_precedence():
    result = classify_family({"bare": _cond_result("distractor"), "ba": _cond_result("confirmation"), "ma": _cond_result("neutral")})
    assert result["class"] == "EXCLUDE_BROKEN"
    assert result["collapse_type"] is None


def test_classify_family_exclude_broken_beats_no_consensus():
    # distractor majority on one condition, no majority at all on another --
    # EXCLUDE_BROKEN short-circuits before the has-majority check runs.
    result = classify_family(
        {"bare": _cond_result("distractor"), "ba": _cond_result(None, has_majority=False), "ma": _cond_result("neutral")}
    )
    assert result["class"] == "EXCLUDE_BROKEN"


def test_classify_family_collapse_structural_pair():
    result = classify_family({"bare": _cond_result("statement"), "ba": _cond_result("neutral"), "ma": _cond_result("neutral")})
    assert result["class"] == "COLLAPSE"
    assert result["collapse_type"] == "structural"
    assert result["collapse_pair"] == "ba=ma"
    assert result["collapse_label"] == "neutral"


def test_classify_family_collapse_structural_all_three_same():
    result = classify_family({"bare": _cond_result("neutral"), "ba": _cond_result("neutral"), "ma": _cond_result("neutral")})
    assert result["class"] == "COLLAPSE"
    assert result["collapse_type"] == "structural"
    assert result["collapse_pair"] == "bare=ba=ma"


# ---- empirical gold + shift detection --------------------------------------


def test_empirical_gold_row_no_shift():
    item = _item(
        "F04", "bare",
        [_annotation("Media", "statement"), _annotation("Materials", "statement"), _annotation("EngLit", "neutral")],
        gold_semantic_designed="statement",
    )
    row = empirical_gold_row(item)
    assert row["gold_shifted"] is False
    assert row["majority_label"] == "statement"


def test_empirical_gold_row_shift_detected():
    item = _item(
        "F05", "ma",
        [_annotation("Media", "confirmation"), _annotation("Materials", "confirmation"), _annotation("EngLit", "neutral")],
        gold_semantic_designed="neutral",
    )
    row = empirical_gold_row(item)
    assert row["gold_shifted"] is True
    assert row["majority_label"] == "confirmation"
    assert row["margin"] == 1

    projected = shifted_row(row)
    assert projected == {
        "family_id": "F05",
        "condition": "ma",
        "design_gold_label": "neutral",
        "empirical_gold_label": "confirmation",
        "margin": 1,
    }


def test_empirical_gold_row_no_majority_is_never_shifted():
    item = _item(
        "F06", "ba",
        [_annotation("Media", "confirmation"), _annotation("Materials", "statement"), _annotation("EngLit", "neutral")],
        gold_semantic_designed="confirmation",
    )
    row = empirical_gold_row(item)
    assert row["has_majority"] is False
    assert row["gold_shifted"] is False


# ---- run_all: EXCLUDE_BROKEN must not leak into gold outputs ---------------


def _core3_annotations(bare, ba, ma):
    return {
        "bare": [_annotation("Media", bare), _annotation("Materials", bare), _annotation("EngLit", bare)],
        "ba": [_annotation("Media", ba), _annotation("Materials", ba), _annotation("EngLit", ba)],
        "ma": [_annotation("Media", ma), _annotation("Materials", ma), _annotation("EngLit", ma)],
    }


def test_run_all_excludes_broken_family_from_gold_outputs(tmp_path):
    # F01: bare and ba both collapse to distractor under core3 -- EXCLUDE_BROKEN
    # -- but ma's neutral -> confirmation would look like an ordinary shift
    # read in isolation (this mirrors the real F31 case). F02 is a normal
    # KEEP family with one genuine shift on "ma".
    broken_anns = _core3_annotations("distractor", "distractor", "confirmation")
    keep_anns = _core3_annotations("statement", "confirmation", "confirmation")
    items = [
        _item("F01", "bare", broken_anns["bare"], gold_semantic_designed="statement"),
        _item("F01", "ba", broken_anns["ba"], gold_semantic_designed="confirmation"),
        _item("F01", "ma", broken_anns["ma"], gold_semantic_designed="neutral"),
        _item("F02", "bare", keep_anns["bare"], gold_semantic_designed="statement"),
        _item("F02", "ba", keep_anns["ba"], gold_semantic_designed="confirmation"),
        _item("F02", "ma", keep_anns["ma"], gold_semantic_designed="neutral"),
    ]

    output_dir = tmp_path / "pool_sensitivity_output"
    run_all(items, str(output_dir))

    with open(output_dir / "pool_sensitivity_grid.csv") as f:
        grid = {r["family_id"]: r for r in csv.DictReader(f)}
    assert grid["F01"]["core3_class"] == "EXCLUDE_BROKEN"
    assert grid["F01"]["family_gold_shifted"] == "False"
    assert grid["F02"]["family_gold_shifted"] == "True"

    with open(output_dir / "empirical_gold_core3.csv") as f:
        gold_families = {r["family_id"] for r in csv.DictReader(f)}
    assert "F01" not in gold_families
    assert "F02" in gold_families

    with open(output_dir / "gold_shifted_families.csv") as f:
        shifted_families = {r["family_id"] for r in csv.DictReader(f)}
    assert "F01" not in shifted_families
    assert "F02" in shifted_families
