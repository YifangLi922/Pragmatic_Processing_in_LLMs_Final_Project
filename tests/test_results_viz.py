"""Unit tests for src/results_viz/data.py (pure CSV-row shaping for the five
poster figures). No matplotlib import needed here.
"""

from src.results_viz.data import (
    load_by_condition_metric,
    load_condition_accuracy,
    load_confusion_rownorm,
    load_design_gold_following,
    load_human_baseline_comparison,
)


def test_load_condition_accuracy():
    rows = [
        {
            "model": "modelA",
            "accuracy_bare": "0.95", "n_valid_bare": "20",
            "accuracy_ba": "1.0", "n_valid_ba": "20",
            "accuracy_ma": "0.75", "n_valid_ma": "20",
        }
    ]
    result = load_condition_accuracy(rows)
    assert result["modelA"]["bare"] == {"accuracy": 0.95, "n": 20}
    assert result["modelA"]["ma"] == {"accuracy": 0.75, "n": 20}


def test_load_human_baseline_comparison():
    rows = [{"condition": "ba", "human_LOO": "0.6662596662596663", "human_concordance": "0.7833333333333332"}]
    result = load_human_baseline_comparison(rows)
    assert result["ba"]["loo"] == 0.6662596662596663
    assert result["ba"]["concordance"] == 0.7833333333333332


def test_load_confusion_rownorm_handles_blank_as_none():
    rows = [
        {"model": "modelA", "gold_semantic": "statement", "statement": "0.95", "confirmation": "0.05", "neutral": "0.0", "distractor": "0.0"},
        {"model": "modelA", "gold_semantic": "distractor", "statement": "", "confirmation": "", "neutral": "", "distractor": ""},
    ]
    result = load_confusion_rownorm(rows)
    assert result["modelA"]["statement"]["statement"] == 0.95
    assert result["modelA"]["distractor"]["statement"] is None


def test_load_by_condition_metric_filters_set_and_parses():
    rows = [
        {"set": "confirmatory", "model": "modelA", "condition": "bare", "used_target_rate": "0.6", "n_valid_pairs": "60"},
        {"set": "exploratory", "model": "modelA", "condition": "bare", "used_target_rate": "0.5", "n_valid_pairs": "18"},
    ]
    result = load_by_condition_metric(rows, "confirmatory", "used_target_rate", "n_valid_pairs")
    assert result == {("modelA", "bare"): {"rate": 0.6, "n": 60}}


def test_load_design_gold_following():
    rows = [{"model": "modelA", "n_shifted_items": "4", "design_gold_following_rate": "1.0"}]
    result = load_design_gold_following(rows)
    assert result["modelA"] == {"rate": 1.0, "n_shifted_items": 4}
