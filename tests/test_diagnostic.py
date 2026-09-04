"""Unit tests for the annotator condition-wise diagnostic (src/diagnostic).
Pure Python fixtures -- no .xlsx or reconstructed.json needed.
"""

from src.diagnostic.core import diagnose_item, reference_majority, resolve_vote, run_diagnostic
from src.diagnostic.metrics import condition_summary, confusion_matrices, disagreement_directions, reference_marginals


def _annotation(annotator_id, semantic, no_valid_option=0, naturalness=5, hesitation=0):
    return {
        "annotator_id": annotator_id,
        "answer_semantic": semantic,
        "naturalness": naturalness,
        "hesitation": hesitation,
        "no_valid_option": no_valid_option,
    }


def _item(item_id, family_id, condition, annotations):
    return {"item_id": item_id, "family_id": family_id, "particle_condition": condition, "annotations": annotations}


# ---- resolve_vote -----------------------------------------------------------


def test_resolve_vote_true_abstention_ignores_mode():
    ann = _annotation("R1", None, no_valid_option=1)
    assert resolve_vote(ann, "A") is None
    assert resolve_vote(ann, "B") is None


def test_resolve_vote_checked_but_answered_mode_a_counts_it():
    ann = _annotation("R1", "neutral", no_valid_option=1)
    assert resolve_vote(ann, "A") == "neutral"


def test_resolve_vote_checked_but_answered_mode_b_discards_it():
    ann = _annotation("R1", "neutral", no_valid_option=1)
    assert resolve_vote(ann, "B") is None


def test_resolve_vote_normal_answer_counts_either_mode():
    ann = _annotation("R1", "statement")
    assert resolve_vote(ann, "A") == "statement"
    assert resolve_vote(ann, "B") == "statement"


def test_resolve_vote_missing_annotation():
    assert resolve_vote(None, "A") is None


# ---- reference_majority -----------------------------------------------------


def test_majority_unanimous_three():
    assert reference_majority(["neutral", "neutral", "neutral"]) == ("neutral", True)


def test_majority_two_of_three():
    assert reference_majority(["neutral", "neutral", "statement"]) == ("neutral", True)


def test_majority_one_one_one_invalid():
    assert reference_majority(["neutral", "statement", "confirmation"]) == (None, False)


def test_majority_single_vote_two_abstentions_invalid():
    # explicit example from the spec: one voter left, other two abstained
    assert reference_majority(["neutral", None, None]) == (None, False)


def test_majority_two_way_tie_among_two_cast_votes_invalid():
    assert reference_majority(["neutral", "statement", None]) == (None, False)


def test_majority_two_cast_votes_agree_is_valid():
    assert reference_majority(["neutral", "neutral", None]) == ("neutral", True)


# ---- diagnose_item -----------------------------------------------------------


def test_diagnose_item_agreement():
    item = _item(
        "F01_bare", "F01", "bare",
        [
            _annotation("Media", "statement"),
            _annotation("Materials", "statement"),
            _annotation("EngLit", "confirmation"),
            _annotation("Econ", "statement"),
        ],
    )
    record = diagnose_item(item, "Econ", ["Media", "Materials", "EngLit"], "A")
    assert record["reference_valid"] is True
    assert record["reference_label"] == "statement"
    assert record["agree"] is True
    assert record["disagreement_direction"] is None
    assert record["Media_semantic"] == "statement"


def test_diagnose_item_disagreement_direction():
    item = _item(
        "F02_ma", "F02", "ma",
        [
            _annotation("Media", "neutral"),
            _annotation("Materials", "neutral"),
            _annotation("EngLit", "statement"),
            _annotation("Econ", "confirmation"),
        ],
    )
    record = diagnose_item(item, "Econ", ["Media", "Materials", "EngLit"], "A")
    assert record["reference_label"] == "neutral"
    assert record["agree"] is False
    assert record["disagreement_direction"] == "neutral->confirmation"


def test_diagnose_item_reference_invalid_excludes_from_agreement():
    item = _item(
        "F03_ba", "F03", "ba",
        [
            _annotation("Media", "neutral"),
            _annotation("Materials", "statement"),
            _annotation("EngLit", "confirmation"),
            _annotation("Econ", "statement"),
        ],
    )
    record = diagnose_item(item, "Econ", ["Media", "Materials", "EngLit"], "A")
    assert record["reference_valid"] is False
    assert record["agree"] is None
    assert record["disagreement_direction"] is None


def test_diagnose_item_target_abstention_counts_as_non_agreement_but_no_direction():
    item = _item(
        "F04_bare", "F04", "bare",
        [
            _annotation("Media", "statement"),
            _annotation("Materials", "statement"),
            _annotation("EngLit", "statement"),
            _annotation("Econ", None, no_valid_option=1),
        ],
    )
    record = diagnose_item(item, "Econ", ["Media", "Materials", "EngLit"], "A")
    assert record["reference_valid"] is True
    assert record["target_semantic"] is None
    assert record["agree"] is False
    assert record["disagreement_direction"] is None


def test_diagnose_item_mode_b_changes_reference_validity():
    # EngLit checked no-option but answered "statement"; with only Media+EngLit
    # agreeing under mode A that's a 2/2 majority, but mode B discards EngLit's
    # vote, leaving Media alone -> invalid (single voter).
    item = _item(
        "F05_bare", "F05", "bare",
        [
            _annotation("Media", "statement"),
            _annotation("Materials", "neutral"),
            _annotation("EngLit", "statement", no_valid_option=1),
            _annotation("Econ", "statement"),
        ],
    )
    record_a = diagnose_item(item, "Econ", ["Media", "Materials", "EngLit"], "A")
    record_b = diagnose_item(item, "Econ", ["Media", "Materials", "EngLit"], "B")
    assert record_a["reference_valid"] is True
    assert record_a["reference_label"] == "statement"
    assert record_b["reference_valid"] is False


# ---- run_diagnostic + metrics (integration over a tiny fixture) ------------


def _fixture_items():
    # Two families x 3 conditions = 6 items. Econ is target; Media/Materials/
    # EngLit form the reference pool and always agree with each other, so
    # reference_valid is True everywhere and coverage should read 1.0.
    items = []
    for fam, agree_condition in [("F01", True), ("F02", False)]:
        for condition, ref_label, econ_choice in [
            ("bare", "statement", "statement"),
            ("ba", "confirmation", "confirmation" if agree_condition else "neutral"),
            ("ma", "neutral", "neutral"),
        ]:
            other_label = {"statement": "confirmation", "confirmation": "neutral", "neutral": "distractor"}[ref_label]
            items.append(
                _item(
                    f"{fam}_{condition}", fam, condition,
                    [
                        _annotation("Media", ref_label),
                        _annotation("Materials", ref_label),
                        _annotation("EngLit", other_label if fam == "F02" and condition == "ba" else ref_label),
                        _annotation("Econ", econ_choice),
                    ],
                )
            )
    return items


def test_run_diagnostic_and_metrics_end_to_end():
    items = _fixture_items()
    records = run_diagnostic(items, "Econ", ["Media", "Materials", "EngLit"], "A")
    assert len(records) == 6

    summary = condition_summary(records)
    ba_row = next(r for r in summary if r["condition"] == "ba")
    assert ba_row["total_n"] == 2
    assert ba_row["reference_n"] == 2  # both ba items still get a 2/3+ majority
    assert ba_row["agreement_n"] == 1  # only F01's ba item agrees

    marginals = reference_marginals(records)
    overall_row = next(r for r in marginals if r["condition"] == "overall")
    assert overall_row["reference_valid_n"] == 6

    matrices = confusion_matrices(records)
    assert matrices["ba"]["raw"]["confirmation"]["confirmation"] == 1
    assert matrices["ba"]["raw"]["confirmation"]["neutral"] == 1

    directions = disagreement_directions(records)
    ba_direction = next(
        d for d in directions if d["condition"] == "ba" and d["reference_label"] == "confirmation" and d["target_label"] == "neutral"
    )
    assert ba_direction["count"] == 1
    assert ba_direction["low_n"] is True  # below the threshold of 8
