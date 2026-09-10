"""Unit tests for the dataset freeze step (src/freeze). Pure Python
fixtures throughout -- no real pool_sensitivity_output/ needed.
"""

from src.freeze.build import build_exploratory_rows, build_frozen_rows, build_row
from src.freeze.report import render_freeze_report


def _item(family_id, condition, option_semantics, gold_semantic_designed):
    letters = ("A", "B", "C", "D")
    return {
        "item_id": f"{family_id}_{condition}",
        "family_id": family_id,
        "particle_condition": condition,
        "context": f"context for {family_id}_{condition}",
        "sentence": f"sentence for {family_id}_{condition}",
        "options": {letter: f"option {letter} text" for letter in letters},
        "option_semantics": option_semantics,
        "gold_semantic_designed": gold_semantic_designed,
    }


_OPTION_SEMANTICS = {"A": "distractor", "B": "neutral", "C": "statement", "D": "confirmation"}


def _gold(gold_semantic, gold_shifted=False, margin=1):
    return {"gold_semantic": gold_semantic, "gold_shifted": gold_shifted, "margin": margin}


# ---- build_row ---------------------------------------------------------


def test_build_row_maps_gold_letter_and_option_semantic_map():
    item = _item("F01", "bare", _OPTION_SEMANTICS, gold_semantic_designed="statement")
    row = build_row(item, _gold("statement"), stable_keep_all_pools=True)
    assert row["gold_letter"] == "C"
    assert row["option_semantic_map"] == "A:distractor|B:neutral|C:statement|D:confirmation"
    assert row["design_gold_semantic"] == "statement"
    assert row["gold_semantic"] == "statement"
    assert row["stable_keep_all_pools"] is True


# ---- build_frozen_rows / build_exploratory_rows -------------------------


def _fixture_items():
    items = []
    for family_id in ("F01", "F02", "F03"):
        for condition in ("bare", "ba", "ma"):
            items.append(_item(family_id, condition, _OPTION_SEMANTICS, gold_semantic_designed="statement"))
    return items


def _fixture_grid():
    return {
        "F01": {"core3_class": "KEEP", "stable_keep_all_pools": True},
        "F02": {"core3_class": "COLLAPSE", "stable_keep_all_pools": False},
        "F03": {"core3_class": "NO_CONSENSUS", "stable_keep_all_pools": False},
    }


def _fixture_gold_lookup():
    lookup = {}
    for family_id in ("F01", "F02"):
        for condition in ("bare", "ba", "ma"):
            lookup[(family_id, condition)] = _gold("statement")
    return lookup


def test_build_frozen_rows_only_includes_keep_families():
    rows = build_frozen_rows(_fixture_items(), _fixture_grid(), _fixture_gold_lookup(), target_class="KEEP")
    assert {r["family_id"] for r in rows} == {"F01"}
    assert len(rows) == 3
    assert [r["condition"] for r in rows] == ["bare", "ba", "ma"]  # canonical order


def test_build_frozen_rows_excludes_no_consensus_family_not_in_gold_lookup():
    # F03 is NO_CONSENSUS and deliberately absent from the gold lookup
    # (mirrors empirical_gold_core3.csv excluding non-KEEP/COLLAPSE families);
    # filtering must happen before any lookup into it.
    rows = build_frozen_rows(_fixture_items(), _fixture_grid(), _fixture_gold_lookup(), target_class="KEEP")
    assert "F03" not in {r["family_id"] for r in rows}


def test_build_exploratory_rows_adds_collapse_columns():
    collapse_lookup = {"F02": {"collapse_pair": "ba=ma", "collapse_label": "confirmation"}}
    rows = build_exploratory_rows(_fixture_items(), _fixture_grid(), _fixture_gold_lookup(), collapse_lookup)
    assert {r["family_id"] for r in rows} == {"F02"}
    assert all(r["collapse_pair"] == "ba=ma" and r["collapse_label"] == "confirmation" for r in rows)


# ---- render_freeze_report -------------------------------------------------


def test_render_freeze_report_counts_and_margin_distribution():
    class_counts = {"KEEP": 20, "COLLAPSE": 6, "NO_CONSENSUS": 8, "EXCLUDE_BROKEN": 2}
    grid = {
        "F06": {"core3_class": "COLLAPSE"},
        "F12": {"core3_class": "COLLAPSE"},
        "F20": {"core3_class": "KEEP"},
        "F21": {"core3_class": "KEEP"},
    }
    shifted_rows = [
        {"family_id": "F06", "condition": "ba", "design_gold_label": "confirmation", "empirical_gold_label": "statement", "margin": "1"},
        {"family_id": "F12", "condition": "ma", "design_gold_label": "neutral", "empirical_gold_label": "confirmation", "margin": "3"},
    ]
    frozen_rows = [
        {"family_id": "F20", "margin": 3},
        {"family_id": "F20", "margin": 1},
        {"family_id": "F21", "margin": 3},
    ]
    report = render_freeze_report(
        class_counts, shifted_rows, grid, stable_keep_count=11, n_total_families=36,
        frozen_rows=frozen_rows, tag_name="dataset-frozen-v1", tag_commit="abc1234",
    )

    assert "| KEEP | 20 |" in report
    assert "| COLLAPSE_structural | 6 |" in report
    assert "| NO_CONSENSUS | 8 |" in report
    assert "| EXCLUDE_BROKEN | 2 |" in report
    assert "F20" in report and "F21" in report  # family membership listing
    assert "F06" in report and "F12" in report
    assert "exploratory" in report  # F06/F12 (COLLAPSE) labeled correctly
    assert "margin=1: 1" in report
    assert "margin=3: 1" in report
    assert "11 of the 20" in report
    assert "dataset-frozen-v1" in report and "abc1234" in report
    assert "All 2 shifted items fall in the exploratory set" in report
    assert "3:0 (unanimous, all 3 cast)" in report
    assert "2:1 (majority, all 3 cast)" in report


def test_render_freeze_report_no_shifts():
    class_counts = {"KEEP": 5, "COLLAPSE": 0, "NO_CONSENSUS": 0, "EXCLUDE_BROKEN": 0}
    grid = {f"F0{i}": {"core3_class": "KEEP"} for i in range(1, 6)}
    frozen_rows = [{"family_id": fid, "margin": 3} for fid in grid]
    report = render_freeze_report(
        class_counts, [], grid, stable_keep_count=5, n_total_families=5,
        frozen_rows=frozen_rows, tag_name="dataset-frozen-v1", tag_commit=None,
    )
    assert "(none)" in report
    assert "not found in this checkout" in report
