"""Unit tests for Module 6 (src/stats). mcnemar.py and plot_data.py are pure
data logic and fully tested here; plots.py (the matplotlib rendering layer)
is exercised only by a smoke test that checks it runs and produces a
non-empty file, since pixel-level correctness isn't something worth
asserting on.
"""

from src.stats.mcnemar import mcnemar_by_pair, mcnemar_exact_p
from src.stats.plot_data import (
    condition_accuracy_series,
    confusion_heatmap_data,
    family_by_model_matrix,
    family_success_rate_series,
    model_vs_baseline_series,
)


# ---- mcnemar.py -------------------------------------------------------------


def test_mcnemar_exact_p_no_discordant_pairs_is_none():
    assert mcnemar_exact_p(0, 0) is None


def test_mcnemar_exact_p_symmetric_in_b_and_c():
    assert mcnemar_exact_p(3, 7) == mcnemar_exact_p(7, 3)


def test_mcnemar_exact_p_matches_hand_computed_value():
    # b=1, c=9: exact two-sided p = 2 * P(Binomial(10, 0.5) <= 1)
    # P(X<=1) = (C(10,0)+C(10,1)) / 1024 = 11/1024
    expected = 2 * 11 / 1024
    assert abs(mcnemar_exact_p(1, 9) - expected) < 1e-12


def test_mcnemar_exact_p_all_discordant_one_side_is_significant():
    # 0 vs 10: every family flipped from correct to incorrect -> tiny p-value
    p = mcnemar_exact_p(0, 10)
    assert p < 0.01


def _scored(family_id, condition, correct):
    return {"family_id": family_id, "particle_condition": condition, "correct": correct}


def test_mcnemar_by_pair_counts_discordant_and_concordant_correctly():
    scored = [
        _scored("F1", "bare", True), _scored("F1", "ba", True),  # both correct
        _scored("F2", "bare", True), _scored("F2", "ba", False),  # bare only
        _scored("F3", "bare", False), _scored("F3", "ba", True),  # ba only
        _scored("F4", "bare", False), _scored("F4", "ba", False),  # both wrong
    ]
    result = mcnemar_by_pair(scored)
    pair = result["bare_vs_ba"]
    assert pair["n_families"] == 4
    assert pair["both_correct"] == 1
    assert pair["both_wrong"] == 1
    assert pair["bare_only_correct"] == 1
    assert pair["ba_only_correct"] == 1
    assert pair["p_value"] == mcnemar_exact_p(1, 1)


def test_mcnemar_by_pair_skips_families_missing_a_condition():
    scored = [_scored("F1", "bare", True)]  # no "ba" for F1 at all
    result = mcnemar_by_pair(scored)
    assert result["bare_vs_ba"]["n_families"] == 0
    assert result["bare_vs_ba"]["p_value"] is None


# ---- plot_data.py -------------------------------------------------------------


def _scorecard(overall_acc, bare_acc, ba_acc, ma_acc, family_rate, family_detail):
    def acc_block(a):
        return {"accuracy": a, "ci_low": max(0, a - 0.1) if a is not None else None,
                "ci_high": min(1, a + 0.1) if a is not None else None}

    return {
        "condition_accuracy": {"overall": acc_block(overall_acc), "bare": acc_block(bare_acc),
                                "ba": acc_block(ba_acc), "ma": acc_block(ma_acc)},
        "family_success": {"rate": family_rate},
        "family_success_detail": family_detail,
        "confusion_matrix": {
            cond: {"n": 1, "counts": {"statement": 0, "confirmation": 0, "neutral": 0, "distractor": 0, "unparseable": 0}}
            for cond in ("bare", "ba", "ma")
        },
    }


def test_confusion_heatmap_data_shape():
    confusion = {
        "bare": {"n": 2, "counts": {"statement": 2, "confirmation": 0, "neutral": 0, "distractor": 0, "unparseable": 0}},
        "ba": {"n": 1, "counts": {"statement": 0, "confirmation": 1, "neutral": 0, "distractor": 0, "unparseable": 0}},
        "ma": {"n": 0, "counts": {"statement": 0, "confirmation": 0, "neutral": 0, "distractor": 0, "unparseable": 0}},
    }
    rows, cols, matrix = confusion_heatmap_data(confusion)
    assert rows == ["bare", "ba", "ma"]
    assert "statement" in cols and "unparseable" in cols
    assert matrix[0][cols.index("statement")] == 2
    assert matrix[1][cols.index("confirmation")] == 1


def test_condition_accuracy_series_extracts_ci_tuples():
    scorecards = {"modelA": _scorecard(0.5, 0.6, 0.4, 0.5, 0.2, {})}
    series = condition_accuracy_series(scorecards)
    assert series["modelA"]["overall"] == (0.5, 0.4, 0.6)


def test_family_success_rate_series():
    scorecards = {"modelA": _scorecard(0.5, 0.5, 0.5, 0.5, 0.75, {})}
    assert family_success_rate_series(scorecards) == {"modelA": 0.75}


def test_family_by_model_matrix_marks_missing_data_distinctly():
    scorecards = {
        "modelA": _scorecard(0.5, 0.5, 0.5, 0.5, 0.5, {"F01": True, "F02": False}),
        "modelB": _scorecard(0.5, 0.5, 0.5, 0.5, 0.5, {"F01": False}),  # no data for F02
    }
    family_ids, model_names, matrix = family_by_model_matrix(scorecards)
    assert family_ids == ["F01", "F02"]
    assert model_names == ["modelA", "modelB"]
    assert matrix[0] == [1, 0]  # F01: modelA success, modelB failed
    assert matrix[1] == [0, -1]  # F02: modelA failed, modelB has no data


def test_model_vs_baseline_series_includes_baseline_key():
    scorecards = {"modelA": _scorecard(0.6, 0.7, 0.5, 0.6, 0.3, {})}
    human_baseline = {
        "overall": {"accuracy": 0.9}, "bare": {"accuracy": 0.95},
        "ba": {"accuracy": 0.85}, "ma": {"accuracy": 0.88},
    }
    series = model_vs_baseline_series(scorecards, human_baseline)
    assert series["human_baseline"]["overall"] == 0.9
    assert series["modelA"]["overall"] == 0.6


# ---- plots.py (smoke test only) ------------------------------------------------


def test_plot_condition_accuracy_survives_wilson_ci_float_noise_at_zero(tmp_path):
    # Real bug hit in a smoke test: wilson_ci(0, n) can return a rounding-error
    # ci_low like 5.5e-17 instead of exactly 0.0 when accuracy is exactly 0.0,
    # which used to make matplotlib's bar(yerr=...) raise on a negative value.
    # Uses the real accuracy_with_ci() (not the synthetic _scorecard fixture)
    # so this actually exercises the float-noise case instead of a stand-in
    # that can't reproduce it.
    from src.scoring.accuracy import accuracy_with_ci
    from src.stats.plots import plot_condition_accuracy

    zero_acc = accuracy_with_ci([{"correct": False}, {"correct": False}, {"correct": False}])
    scorecards = {
        "modelA": {
            "condition_accuracy": {c: zero_acc for c in ("overall", "bare", "ba", "ma")},
            "family_success": {"rate": 0.0},
            "family_success_detail": {},
            "confusion_matrix": {
                c: {"n": 0, "counts": {"statement": 0, "confirmation": 0, "neutral": 0, "distractor": 0, "unparseable": 0}}
                for c in ("bare", "ba", "ma")
            },
        }
    }
    out = tmp_path / "accuracy.png"
    plot_condition_accuracy(scorecards, out)  # must not raise
    assert out.exists() and out.stat().st_size > 0


def test_plot_functions_run_and_produce_nonempty_files(tmp_path):
    from src.stats.plots import (
        plot_condition_accuracy,
        plot_confusion_heatmap,
        plot_family_by_model_heatmap,
        plot_family_success,
        plot_model_vs_baseline,
    )

    scorecards = {
        "modelA": _scorecard(0.6, 0.7, 0.5, 0.6, 0.3, {"F01": True, "F02": False}),
        "modelB": _scorecard(0.4, 0.3, 0.5, 0.4, 0.1, {"F01": False, "F02": False}),
    }
    human_baseline = {
        "overall": {"accuracy": 0.9}, "bare": {"accuracy": 0.95},
        "ba": {"accuracy": 0.85}, "ma": {"accuracy": 0.88},
    }

    confusion_out = tmp_path / "confusion.png"
    plot_confusion_heatmap(scorecards["modelA"]["confusion_matrix"], "modelA", confusion_out)
    accuracy_out = tmp_path / "accuracy.png"
    plot_condition_accuracy(scorecards, accuracy_out)
    family_out = tmp_path / "family.png"
    plot_family_success(scorecards, family_out)
    heatmap_out = tmp_path / "heatmap.png"
    plot_family_by_model_heatmap(scorecards, heatmap_out)
    baseline_out = tmp_path / "baseline.png"
    plot_model_vs_baseline(scorecards, human_baseline, baseline_out)

    for path in (confusion_out, accuracy_out, family_out, heatmap_out, baseline_out):
        assert path.exists() and path.stat().st_size > 0
