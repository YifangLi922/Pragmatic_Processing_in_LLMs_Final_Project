"""Unit tests for src/human_baseline_core3 (the fair core3-only, 20-family
human LOO baseline). Pure Python fixtures.
"""

from src.agreement.loo_baseline import loo_human_baseline
from src.human_baseline_core3.concordance import core3_concordance, item_concordance
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


# ---- concordance.py -----------------------------------------------------


def test_item_concordance_counts_matches_over_all_annotations():
    item = _item(
        "F01_ba", "F01", "ba",
        [_annotation("Media", "confirmation"), _annotation("Materials", "confirmation"), _annotation("EngLit", "statement")],
    )
    assert item_concordance(item, "confirmation") == 2 / 3


def test_item_concordance_treats_missing_answer_semantic_as_no_match():
    item = _item(
        "F01_ba", "F01", "ba",
        [_annotation("Media", "confirmation"), _annotation("Materials", None), _annotation("EngLit", "confirmation")],
    )
    assert item_concordance(item, "confirmation") == 2 / 3


def test_core3_concordance_averages_within_condition_including_2_1_splits():
    # A 2:1 split (Media+Materials say "statement", EngLit says "neutral") on
    # a bare item -- concordance should credit 2/3, unlike LOO which always
    # scores the minority vote as a miss.
    items = [
        _item("F01_bare", "F01", "bare", [_annotation("Media", "statement"), _annotation("Materials", "statement"),
                                            _annotation("EngLit", "neutral")]),
        _item("F02_bare", "F02", "bare", [_annotation("Media", "statement"), _annotation("Materials", "statement"),
                                            _annotation("EngLit", "statement")]),
    ]
    gold_by_item = {"F01_bare": "statement", "F02_bare": "statement"}
    result = core3_concordance(items, gold_by_item)
    assert result["bare"]["accuracy"] == (2 / 3 + 1.0) / 2
    assert result["bare"]["n_items"] == 2
    assert result["overall"]["n_items"] == 2


def test_core3_concordance_skips_items_with_no_gold():
    items = [_item("F99_bare", "F99", "bare", [_annotation("Media", "statement")])]
    result = core3_concordance(items, gold_by_item={})
    assert result == {}  # no item had a gold entry, so no condition ever got a value
