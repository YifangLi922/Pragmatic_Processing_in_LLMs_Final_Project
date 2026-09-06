"""Unit tests for src/human_baseline_core3 (the fair core3-only, 20-family
human LOO baseline). Pure Python fixtures.
"""

from src.agreement.loo_baseline import loo_human_baseline
from src.human_baseline_core3.filter import load_keep_family_ids, restrict_to_core3_keep_families


def _annotation(annotator_id, semantic):
    return {"annotator_id": annotator_id, "answer_semantic": semantic}


def _item(item_id, family_id, condition, annotations):
    return {"item_id": item_id, "family_id": family_id, "particle_condition": condition, "annotations": annotations}


def test_load_keep_family_ids():
    rows = [{"family_id": "F01", "other": "x"}, {"family_id": "F01"}, {"family_id": "F04"}]
    assert load_keep_family_ids(rows) == {"F01", "F04"}


def test_restrict_to_core3_keep_families_drops_non_keep_family_and_non_core3_annotators():
    items = [
        _item(
            "F01_bare", "F01", "bare",
            [
                _annotation("Media", "statement"),
                _annotation("Materials", "statement"),
                _annotation("EngLit", "statement"),
                _annotation("Econ", "confirmation"),
                _annotation("BWL", "statement"),
            ],
        ),
        _item("F99_bare", "F99", "bare", [_annotation("Media", "neutral")]),  # not a keep family
    ]
    restricted = restrict_to_core3_keep_families(items, keep_family_ids={"F01"})

    assert len(restricted) == 1
    assert restricted[0]["item_id"] == "F01_bare"
    annotator_ids = {a["annotator_id"] for a in restricted[0]["annotations"]}
    assert annotator_ids == {"Media", "Materials", "EngLit"}


def test_end_to_end_matches_loo_human_baseline_on_restricted_items():
    # Three items, core3 unanimous on two of them, split on the third --
    # confirms the restricted item list feeds loo_human_baseline correctly
    # and produces a sane, boundedly-correct accuracy.
    items = [
        _item("F01_bare", "F01", "bare", [_annotation("Media", "statement"), _annotation("Materials", "statement"),
                                            _annotation("EngLit", "statement"), _annotation("Econ", "neutral")]),
        _item("F01_ba", "F01", "ba", [_annotation("Media", "confirmation"), _annotation("Materials", "confirmation"),
                                        _annotation("EngLit", "statement"), _annotation("Econ", "statement")]),
    ]
    restricted = restrict_to_core3_keep_families(items, keep_family_ids={"F01"})
    result = loo_human_baseline(restricted)

    assert result["bare"]["accuracy"] == 1.0  # all three core3 members agree -> every fold's other-2 majority hits
    assert result["overall"]["n_folds_total"] == 3  # Media, Materials, EngLit
