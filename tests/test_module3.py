import json
from pathlib import Path

import pytest

from src.agreement.kappa import fleiss_kappa
from src.agreement.loo_baseline import loo_human_baseline
from src.agreement.rates import (
    hesitation_rate_by_condition,
    naturalness_distribution_by_condition,
    no_valid_option_rate_by_condition,
)

FAKE_ANNOTATIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "fake_annotations.json"


def load_fake_annotations() -> list[dict]:
    with open(FAKE_ANNOTATIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---- kappa.py ----------------------------------------------------------------

def test_fleiss_kappa_perfect_agreement_across_spread_categories():
    items = [
        {"annotations": [{"answer_semantic": "statement"} for _ in range(4)]},
        {"annotations": [{"answer_semantic": "confirmation"} for _ in range(4)]},
        {"annotations": [{"answer_semantic": "neutral"} for _ in range(4)]},
        {"annotations": [{"answer_semantic": "distractor"} for _ in range(4)]},
    ]
    assert fleiss_kappa(items) == pytest.approx(1.0)


def test_fleiss_kappa_none_with_fewer_than_two_scorable_items():
    items = [{"annotations": [{"answer_semantic": "statement"} for _ in range(4)]}]
    assert fleiss_kappa(items) is None


def test_fleiss_kappa_on_fake_dataset_is_in_valid_range():
    kappa = fleiss_kappa(load_fake_annotations())
    assert kappa is not None
    assert -1.0 <= kappa <= 1.0


# ---- rates.py ------------------------------------------------------------------

def test_hesitation_rate_by_condition():
    rates = hesitation_rate_by_condition(load_fake_annotations())
    assert rates["bare"] == pytest.approx(3 / 20)
    assert rates["ba"] == pytest.approx(5 / 20)
    assert rates["ma"] == pytest.approx(0.0)
    assert rates["overall"] == pytest.approx(8 / 60)


def test_no_valid_option_rate_by_condition():
    rates = no_valid_option_rate_by_condition(load_fake_annotations())
    assert rates["bare"] == pytest.approx(0.0)
    assert rates["ba"] == pytest.approx(0.0)
    assert rates["ma"] == pytest.approx(1 / 20)
    assert rates["overall"] == pytest.approx(1 / 60)


def test_naturalness_distribution_by_condition():
    dist = naturalness_distribution_by_condition(load_fake_annotations())
    assert dist["bare"]["n"] == 20
    assert dist["bare"]["mean"] == pytest.approx(4.6)
    assert dist["ba"]["mean"] == pytest.approx(3.85)
    assert dist["ma"]["mean"] == pytest.approx(4.65)
    assert dist["overall"]["n"] == 60
    assert dist["overall"]["mean"] == pytest.approx(262 / 60)


# ---- loo_baseline.py -------------------------------------------------------------

def test_loo_baseline_hand_computed_small_example():
    items = [
        {
            "particle_condition": "bare",
            "annotations": [
                {"annotator_id": "A1", "answer_semantic": "statement"},
                {"annotator_id": "A2", "answer_semantic": "statement"},
                {"annotator_id": "A3", "answer_semantic": "confirmation"},
            ],
        },
        {
            "particle_condition": "bare",
            "annotations": [
                {"annotator_id": "A1", "answer_semantic": "confirmation"},
                {"annotator_id": "A2", "answer_semantic": "neutral"},
                {"annotator_id": "A3", "answer_semantic": "neutral"},
            ],
        },
    ]
    result = loo_human_baseline(items)
    # A1's fold: item1 skipped (A2/A3 tie stmt vs confirmation), item2 scored (A1 vs
    #   majority "neutral" -> wrong). A2's fold: both items tie among the other two
    #   -> no scored items -> fold excluded from the average. A3's fold: item1 scored
    #   (A3 vs majority "statement" -> wrong), item2 skipped (A1/A2 tie).
    assert result["overall"]["accuracy"] == pytest.approx(0.0)
    assert result["overall"]["n_folds_used"] == 2
    assert result["overall"]["n_folds_total"] == 3
    assert result["bare"] == result["overall"]  # only one condition present


def test_loo_baseline_on_fake_dataset_has_all_conditions():
    result = loo_human_baseline(load_fake_annotations())
    assert set(result.keys()) == {"overall", "bare", "ba", "ma"}
    for stats in result.values():
        assert stats["accuracy"] is None or 0.0 <= stats["accuracy"] <= 1.0
        assert stats["n_folds_total"] == 4
