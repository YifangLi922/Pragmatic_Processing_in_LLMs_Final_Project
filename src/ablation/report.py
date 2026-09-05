"""CSV writers + the two per-set markdown summaries for the context-only
ablation.
"""

import csv

RESULT_FIELDS = [
    "set",
    "family_id",
    "item_id",
    "condition",
    "model",
    "raw_response",
    "parsed_choice_letter",
    "parsed_choice_semantic",
    "gold_letter",
    "gold_semantic",
    "hit_gold",
    "parse_failed",
]

ITEM_SUMMARY_FIELDS = [
    "set",
    "family_id",
    "item_id",
    "condition",
    "n_models",
    "n_hit_gold",
    "hit_rate",
    "modal_choice",
    "modal_choice_count",
    "converged",
    "shortcut_risk",
]

COLLAPSE_PAIR_FIELDS = ["family_id", "collapse_pair", "collapse_label", "cond1_modal", "cond2_modal", "same_modal"]

_CONDITIONS = ("bare", "ba", "ma")


def _write_rows(path: str, fields: list[str], rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_result_rows(rows: list[dict], path: str) -> None:
    _write_rows(path, RESULT_FIELDS, rows)


def write_item_summary(rows: list[dict], path: str) -> None:
    _write_rows(path, ITEM_SUMMARY_FIELDS, rows)


def write_collapse_pair_check(rows: list[dict], path: str) -> None:
    _write_rows(path, COLLAPSE_PAIR_FIELDS, rows)


def render_set_summary(
    set_name: str,
    item_summary_rows: list[dict],
    result_rows: list[dict],
    collapse_pair_rows: list[dict] | None = None,
) -> str:
    """`set_name` is "confirmatory" or "exploratory". `collapse_pair_rows`
    is only passed (non-None) for the exploratory report.
    """
    set_items = [r for r in item_summary_rows if r["set"] == set_name]
    set_results = [r for r in result_rows if r["set"] == set_name]
    n_items = len(set_items)
    n_shortcut = sum(1 for r in set_items if r["shortcut_risk"])

    lines = [
        f"# Context-only ablation summary -- {set_name}",
        "",
        f"{n_items} items, {len(set_results)} (item, model) query results. shortcut_risk threshold: "
        "≥2/3 of models land on gold from context alone (no target sentence shown).",
        "",
        "**Structural note (applies to every family, both sets):** by dataset design, context/question/"
        "options are identical across a family's bare/+ba/+ma conditions -- only the target sentence "
        "differs, and this ablation removes exactly that. So the ablation prompt for all three conditions "
        "of one family is byte-for-byte identical, and at temperature 0 a given model gives the *same* "
        "answer to all three. That answer can therefore match at most one of a KEEP family's three "
        "(necessarily distinct) gold labels -- shortcut_risk on more than one condition in the same "
        "confirmatory family is not possible by construction, not because the model resisted the shortcut "
        "on the others.",
        "",
    ]

    if set_name == "exploratory":
        lines += [
            "**Not comparable to the confirmatory numbers below at face value.** Every exploratory "
            "family has two conditions whose human reference-pool majority already collapsed onto the "
            "same label (that's why it's here and not in frozen_dataset.csv). Because those two conditions "
            "share a prompt (see the structural note above) and therefore get the same model answer, that "
            "one answer can trigger shortcut_risk on *both* of them simultaneously if it happens to equal "
            "the shared gold -- something structurally impossible in a confirmatory family. A higher "
            "shortcut rate here is expected baseline behavior, not evidence of a worse ablation result.",
            "",
        ]

    lines += [
        f"## shortcut_risk items: {n_shortcut} / {n_items} ({(n_shortcut / n_items):.1%})" if n_items else "## shortcut_risk items: 0 / 0",
        "",
        "### By condition",
        "",
        "| condition | n_items | n_shortcut_risk | shortcut_rate |",
        "|---|---|---|---|",
    ]
    for condition in _CONDITIONS:
        cond_items = [r for r in set_items if r["condition"] == condition]
        cond_shortcut = sum(1 for r in cond_items if r["shortcut_risk"])
        rate = f"{(cond_shortcut / len(cond_items)):.1%}" if cond_items else "n/a"
        lines.append(f"| {condition} | {len(cond_items)} | {cond_shortcut} | {rate} |")
    lines.append("")

    lines.append("### shortcut_risk item list")
    lines.append("")
    shortcut_list = sorted(
        (r["family_id"], r["condition"]) for r in set_items if r["shortcut_risk"]
    )
    if shortcut_list:
        for family_id, condition in shortcut_list:
            lines.append(f"- {family_id} ({condition})")
    else:
        lines.append("(none)")
    lines.append("")

    n_parse_failed = sum(1 for r in set_results if r["parse_failed"])
    parse_failure_rate = (n_parse_failed / len(set_results)) if set_results else 0.0
    lines.append(
        f"### Parse failure rate: {n_parse_failed} / {len(set_results)} query results "
        f"({parse_failure_rate:.1%})"
    )
    lines.append("")

    if collapse_pair_rows is not None:
        lines.append("## Collapse-pair modal-choice check")
        lines.append("")
        lines.append(
            "For each collapsed family, whether the ablation's modal (most common) choice agrees "
            "between the two conditions whose human reference-pool majority collapsed onto the same "
            "label. **Read this as a consistency check, not independent confirmation the model "
            "'reproduces' the human collapse:** per the structural note above, the two collapsing "
            "conditions share an identical context-only prompt, so any single model is expected to answer "
            "them identically regardless of collapse -- `same_modal=True` across the board is the "
            "mechanically expected outcome, not a discovery. A `False` here is the informative direction: "
            "it would mean a model's answer actually varied on two prompts that were byte-for-byte "
            "identical, which (temperature 0 aside) would point to API-level nondeterminism worth checking."
        )
        lines.append("")
        lines.append("| family_id | collapse_pair | collapse_label | cond1_modal | cond2_modal | same_modal |")
        lines.append("|---|---|---|---|---|---|")
        for row in collapse_pair_rows:
            lines.append(
                f"| {row['family_id']} | {row['collapse_pair']} | {row['collapse_label']} | "
                f"{row['cond1_modal'] or '-'} | {row['cond2_modal'] or '-'} | {row['same_modal']} |"
            )
        lines.append("")
        n_same = sum(1 for r in collapse_pair_rows if r["same_modal"])
        lines.append(f"{n_same} / {len(collapse_pair_rows)} collapsed families show the same modal choice on both conditions.")
        lines.append("")

    return "\n".join(lines)
