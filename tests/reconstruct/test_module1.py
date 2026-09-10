"""Unit tests for Module 1 (src/reconstruct). Pure Python fixtures throughout
-- no .xlsx files needed, so these don't depend on the real annotation data
being present.
"""

from src.reconstruct.annotator_table import parse_annotator_rows
from src.reconstruct.build import build_dataset
from src.reconstruct.master_table import parse_master_rows
from src.reconstruct.quality import build_quality_report
from src.reconstruct.semantics import classify_option_text, derive_option_semantics

STATEMENT_TEXT = "小明比较确定这件事，是在告诉小红"
CONFIRMATION_TEXT = "小明倾向于认为这件事成立，但不完全确定，希望小红确认"
NEUTRAL_TEXT = "小明只是在询问这件事是否成立，没有明显倾向"
DISTRACTOR_TEXT = "小明建议小红去问问看"


# ---- semantics.py ----------------------------------------------------------


def test_classify_option_text_core_roles():
    assert classify_option_text(STATEMENT_TEXT) == "statement"
    assert classify_option_text(CONFIRMATION_TEXT) == "confirmation"
    assert classify_option_text(NEUTRAL_TEXT) == "neutral"
    assert classify_option_text(DISTRACTOR_TEXT) == "distractor"


def test_derive_option_semantics_clean_item():
    roles, warnings = derive_option_semantics(
        {"A": NEUTRAL_TEXT, "B": CONFIRMATION_TEXT, "C": DISTRACTOR_TEXT, "D": STATEMENT_TEXT}
    )
    assert roles == {"A": "neutral", "B": "confirmation", "C": "distractor", "D": "statement"}
    assert warnings == []


def test_derive_option_semantics_flags_duplicate_role():
    # two statements, no neutral -- malformed item, should warn not crash
    roles, warnings = derive_option_semantics(
        {"A": STATEMENT_TEXT, "B": STATEMENT_TEXT, "C": CONFIRMATION_TEXT, "D": DISTRACTOR_TEXT}
    )
    assert any("neutral" in w for w in warnings)
    assert any("statement" in w for w in warnings)


# ---- master_table.py / annotator_table.py ----------------------------------


def _master_row(shuffled_index, family_raw, condition_raw, gold_letter):
    # options fixed in A/B/C/D = neutral/confirmation/distractor/statement order
    return (
        shuffled_index,
        family_raw,
        "原20题",
        1,
        condition_raw,
        "示例句子",
        gold_letter,
        "(设计预期含义，未使用)",
        NEUTRAL_TEXT,
        CONFIRMATION_TEXT,
        DISTRACTOR_TEXT,
        STATEMENT_TEXT,
        None,
        None,
        None,
    )


def test_parse_master_rows_normalizes_family_and_condition():
    rows = [_master_row("Q001", "Family 7", "+吧", "B")]
    items = parse_master_rows(rows)
    item = items["Q001"]
    assert item["family_id"] == "F07"
    assert item["particle_condition"] == "ba"
    assert item["gold_letter_designed"] == "B"
    assert item["option_semantics"] == {"A": "neutral", "B": "confirmation", "C": "distractor", "D": "statement"}


def test_parse_master_rows_skips_blank_shuffled_index():
    rows = [_master_row("Q001", "Family 1", "裸句", "D"), _master_row(None, "总题数", "", "")]
    items = parse_master_rows(rows)
    assert list(items.keys()) == ["Q001"]


def _annotator_row(shuffled_index, answer_letter, naturalness, hesitation="", no_valid="", detail=""):
    return (
        shuffled_index,
        "示例情景",
        "示例句子",
        "示例问题",
        NEUTRAL_TEXT,
        CONFIRMATION_TEXT,
        DISTRACTOR_TEXT,
        STATEMENT_TEXT,
        answer_letter,
        naturalness,
        hesitation,
        "",
        no_valid,
        detail,
    )


def test_parse_annotator_rows_flags_are_boolean():
    rows = [_annotator_row("Q001", "B", 5, hesitation="有")]
    recs = parse_annotator_rows(rows)
    assert recs["Q001"]["hesitation"] == 1
    assert recs["Q001"]["no_valid_option"] == 0
    assert recs["Q001"]["naturalness"] == 5


def test_parse_annotator_rows_blank_answer_is_none():
    rows = [_annotator_row("Q001", "", "")]
    recs = parse_annotator_rows(rows)
    assert recs["Q001"]["answer_letter"] is None
    assert recs["Q001"]["naturalness"] is None


def test_parse_annotator_rows_strips_stray_whitespace_and_case_from_answer_letter():
    # real data had a "D " (trailing space) cell that should still count as "D"
    rows = [_annotator_row("Q001", "D ", 5), _annotator_row("Q002", "b", 4)]
    recs = parse_annotator_rows(rows)
    assert recs["Q001"]["answer_letter"] == "D"
    assert recs["Q002"]["answer_letter"] == "B"


# ---- build.py ---------------------------------------------------------------


def _small_dataset():
    master_rows = [
        _master_row("Q001", "Family 1", "裸句", "D"),  # statement is gold
        _master_row("Q002", "Family 1", "+吧", "B"),  # confirmation is gold
        _master_row("Q003", "Family 1", "+吗", "A"),  # neutral is gold
    ]
    master_items = parse_master_rows(master_rows)

    annotator_data = {
        "A1": parse_annotator_rows(
            [
                _annotator_row("Q001", "D", 5),
                _annotator_row("Q002", "B", 4),
                _annotator_row("Q003", "A", 5),
            ]
        ),
        "A2": parse_annotator_rows(
            [
                _annotator_row("Q001", "D", 4),
                _annotator_row("Q002", "C", 4),  # disagrees: picked the distractor
                _annotator_row("Q003", "A", 4),
            ]
        ),
    }
    return master_items, annotator_data


def test_build_dataset_translates_letters_to_semantics_and_sorts_by_family_condition():
    master_items, annotator_data = _small_dataset()
    items, warnings = build_dataset(master_items, annotator_data)

    assert [it["item_id"] for it in items] == ["F01_bare", "F01_ba", "F01_ma"]
    assert warnings == []

    bare_item = items[0]
    assert bare_item["gold_semantic_designed"] == "statement"
    a1_answer = next(a for a in bare_item["annotations"] if a["annotator_id"] == "A1")
    assert a1_answer["answer_semantic"] == "statement"

    ba_item = items[1]
    a2_answer = next(a for a in ba_item["annotations"] if a["annotator_id"] == "A2")
    assert a2_answer["answer_semantic"] == "distractor"


def test_build_dataset_warns_on_content_mismatch_between_annotators():
    master_items, annotator_data = _small_dataset()
    # corrupt A2's context for Q001 to simulate a copy/paste slip
    annotator_data["A2"]["Q001"]["context"] = "不一样的情景"

    _, warnings = build_dataset(master_items, annotator_data)
    assert any("context" in w and "Q001" in w for w in warnings)


def test_build_dataset_warns_on_missing_annotator_row():
    master_items, annotator_data = _small_dataset()
    del annotator_data["A2"]["Q003"]

    items, warnings = build_dataset(master_items, annotator_data)
    assert any("Q003" in w and "A2" in w for w in warnings)
    ma_item = next(it for it in items if it["item_id"] == "F01_ma")
    assert len(ma_item["annotations"]) == 1  # only A1


# ---- quality.py ---------------------------------------------------------------


def test_build_quality_report_flags_flat_responding_and_outlier_agreement():
    # 5 items, gold letter designed = "A" every time so agreement rate is trivial to control
    master_rows = [_master_row(f"Q{i:03d}", f"Family {i}", "裸句", "D") for i in range(1, 6)]
    master_items = parse_master_rows(master_rows)

    genuine = parse_annotator_rows(
        [
            _annotator_row("Q001", "D", 5),
            _annotator_row("Q002", "C", 3, hesitation="有"),
            _annotator_row("Q003", "D", 4),
            _annotator_row("Q004", "A", 4, no_valid="有", detail="都不太对"),
            _annotator_row("Q005", "D", 5),
        ]
    )
    # matches designed gold on every item, naturalness constant, never hesitates
    suspect = parse_annotator_rows([_annotator_row(f"Q{i:03d}", "D", 5) for i in range(1, 6)])

    annotator_data = {"A1": genuine, "A2": suspect}
    items, _ = build_dataset(master_items, annotator_data)
    report = build_quality_report(items, ["A1", "A2"])

    suspect_report = report["per_annotator"]["A2"]
    assert suspect_report["naturalness_sd"] == 0.0
    assert suspect_report["designed_gold_agreement_rate"] == 1.0
    assert any("flat responding" in f for f in suspect_report["flags"])

    genuine_report = report["per_annotator"]["A1"]
    assert genuine_report["naturalness_sd"] > 0
    assert not any("flat responding" in f for f in genuine_report["flags"])
