import json
from pathlib import Path

from src.gold.config import GoldConfig
from src.gold.exclusion import evaluate_families, exclusion_report
from src.gold.majority_vote import consensus_tier, majority_vote

FAKE_ANNOTATIONS_PATH = Path(__file__).resolve().parents[1] / "data" / "fake_annotations.json"


def load_fake_annotations() -> list[dict]:
    with open(FAKE_ANNOTATIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _item(items: list[dict], item_id: str) -> dict:
    return next(i for i in items if i["item_id"] == item_id)


# ---- majority_vote.py -------------------------------------------------------

def test_unanimous_vote_is_4_0():
    items = load_fake_annotations()
    result = majority_vote(_item(items, "FA_bare"))
    assert result.gold_semantic == "statement"
    assert result.consensus_strength == "4:0"
    assert consensus_tier(result.consensus_strength) == "strong"


def test_three_one_vote_is_strong_consensus():
    items = load_fake_annotations()
    result = majority_vote(_item(items, "FA_ba"))
    assert result.gold_semantic == "confirmation"
    assert result.consensus_strength == "3:1"
    assert consensus_tier(result.consensus_strength) == "strong"


def test_two_one_one_vote_is_weak_consensus():
    items = load_fake_annotations()
    result = majority_vote(_item(items, "FE_bare"))
    assert result.gold_semantic == "statement"
    assert result.consensus_strength == "2:1:1"
    assert consensus_tier(result.consensus_strength) == "weak"


def test_two_two_tie_has_no_gold():
    items = load_fake_annotations()
    result = majority_vote(_item(items, "FC_bare"))
    assert result.gold_semantic is None
    assert result.consensus_strength == "2:2"
    assert consensus_tier(result.consensus_strength) == "undefined"


# ---- exclusion.py ------------------------------------------------------------

def _decision_for(decisions, family_id):
    return next(d for d in decisions if d.family_id == family_id)


def test_clean_family_is_retained():
    items = load_fake_annotations()
    _, decisions = evaluate_families(items)
    decision = _decision_for(decisions, "FA")
    assert decision.retained is True
    assert decision.reasons == []


def test_gold_collision_excludes_family():
    items = load_fake_annotations()
    _, decisions = evaluate_families(items)
    decision = _decision_for(decisions, "FB")
    assert decision.retained is False
    assert any(r.startswith("gold_collision") for r in decision.reasons)


def test_undefined_gold_excludes_family():
    items = load_fake_annotations()
    _, decisions = evaluate_families(items)
    decision = _decision_for(decisions, "FC")
    assert decision.retained is False
    assert any(r.startswith("undefined_gold") for r in decision.reasons)


def test_low_naturalness_excludes_family():
    items = load_fake_annotations()
    _, decisions = evaluate_families(items)
    decision = _decision_for(decisions, "FD")
    assert decision.retained is False
    assert any(r.startswith("low_naturalness") for r in decision.reasons)
    assert decision.mean_naturalness_by_condition["ba"] == 2.75


def test_weak_consensus_family_retained_by_default():
    items = load_fake_annotations()
    _, decisions = evaluate_families(items, GoldConfig(require_strong_consensus=False))
    decision = _decision_for(decisions, "FE")
    assert decision.retained is True


def test_weak_consensus_family_excluded_when_strict():
    items = load_fake_annotations()
    _, decisions = evaluate_families(items, GoldConfig(require_strong_consensus=True))
    decision = _decision_for(decisions, "FE")
    assert decision.retained is False
    assert any(r.startswith("weak_consensus") for r in decision.reasons)


def test_exclusion_report_counts_by_default_config():
    items = load_fake_annotations()
    _, decisions = evaluate_families(items)
    report = exclusion_report(decisions)
    assert report["n_families_total"] == 5
    assert report["n_retained"] == 2  # FA, FE
    assert report["n_excluded"] == 3  # FB, FC, FD
    assert report["excluded_by_reason_category"] == {
        "gold_collision": 1,
        "undefined_gold": 1,
        "low_naturalness": 1,
    }
