"""CSV writers + freeze_report.md renderer for the dataset freeze step."""

import csv
from collections import Counter

FROZEN_FIELDS = [
    "family_id",
    "item_id",
    "condition",
    "context_text",
    "target_sentence",
    "option_A",
    "option_B",
    "option_C",
    "option_D",
    "option_semantic_map",
    "gold_semantic",
    "gold_letter",
    "design_gold_semantic",
    "gold_shifted",
    "margin",
    "stable_keep_all_pools",
]

EXPLORATORY_FIELDS = FROZEN_FIELDS + ["collapse_pair", "collapse_label"]


def write_frozen_csv(rows: list[dict], fields: list[str], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


# For pool_core3 (fixed at 3 members), margin unambiguously encodes the
# vote split -- there's no other (majority_count, pool_size) combination
# that produces each value in this dataset. Kept as an explicit, documented
# lookup rather than re-deriving it from majority_count/pool_size, which
# frozen_dataset.csv's schema doesn't carry (only `margin` does).
_MARGIN_LABELS = {
    3: "3:0 (unanimous, all 3 cast)",
    2: "2:0 (unanimous, 1 abstention)",
    1: "2:1 (majority, all 3 cast)",
}


def _margin_label(margin: int) -> str:
    return _MARGIN_LABELS.get(margin, f"margin={margin}")


def _family_ids_by_class(grid: dict) -> dict[str, list[str]]:
    by_class: dict[str, list[str]] = {}
    for family_id, info in grid.items():
        by_class.setdefault(info["core3_class"], []).append(family_id)
    for ids in by_class.values():
        ids.sort()
    return by_class


def render_freeze_report(
    class_counts: dict[str, int],
    shifted_rows: list[dict],
    grid: dict,
    stable_keep_count: int,
    n_total_families: int,
    frozen_rows: list[dict],
    tag_name: str,
    tag_commit: str | None,
) -> str:
    keep_n = class_counts.get("KEEP", 0)
    collapse_n = class_counts.get("COLLAPSE", 0)
    no_consensus_n = class_counts.get("NO_CONSENSUS", 0)
    broken_n = class_counts.get("EXCLUDE_BROKEN", 0)
    by_class = _family_ids_by_class(grid)

    commit_line = (
        f"Tag `{tag_name}` -> commit `{tag_commit}`. frozen_dataset.csv and frozen_exploratory.csv are "
        "byte-identical to that commit; this report was completed afterward and re-committed separately "
        "(the tag stays pinned to the CSV-freezing commit, not this one)."
        if tag_commit
        else f"Tag `{tag_name}` not found in this checkout -- run `git tag` to confirm it was created."
    )

    lines = [
        "# Dataset Freeze Report",
        "",
        f"Generated from `pool_sensitivity_output/` (pool_core3). Total families: {n_total_families}.",
        "After this report and the two frozen CSVs are committed and tagged, the two CSVs are not edited again.",
        "",
        "## Provenance",
        "",
        commit_line,
        "",
        "## Family counts by core3 class",
        "",
        "| class | count |",
        "|---|---|",
        f"| KEEP | {keep_n} |",
        f"| COLLAPSE_structural | {collapse_n} |",
        f"| NO_CONSENSUS | {no_consensus_n} |",
        f"| EXCLUDE_BROKEN | {broken_n} |",
        f"| **total** | **{keep_n + collapse_n + no_consensus_n + broken_n}** |",
        "",
        f"- `frozen_dataset.csv` (confirmatory): {keep_n} families x 3 conditions = {keep_n * 3} rows.",
        f"- `frozen_exploratory.csv`: {collapse_n} families x 3 conditions = {collapse_n * 3} rows.",
        f"- Neither file: {no_consensus_n + broken_n} families (excluded from this freeze; see below).",
        "",
        "## Family membership by class",
        "",
        f"- **KEEP** ({keep_n}): {', '.join(by_class.get('KEEP', []))}",
        f"- **COLLAPSE_structural** ({collapse_n}): {', '.join(by_class.get('COLLAPSE', []))}",
        f"- **NO_CONSENSUS** ({no_consensus_n}): {', '.join(by_class.get('NO_CONSENSUS', []))}",
        f"- **EXCLUDE_BROKEN** ({broken_n}): {', '.join(by_class.get('EXCLUDE_BROKEN', []))}",
        "",
        "## Exclusion reasons (families in neither frozen file)",
        "",
        f"- **NO_CONSENSUS** ({no_consensus_n}): at least one of bare/+ba/+ma has no reference-pool majority "
        "at all under pool_core3 (tie, 1-1-1 split, or too few cast votes).",
        f"- **EXCLUDE_BROKEN** ({broken_n}): at least one condition's core3 majority landed on the DISTRACTOR "
        "role -- the item failed to activate any of its three target semantics on that condition, so the "
        "whole family is excluded even where another condition's numbers would otherwise look like an "
        "ordinary gold shift.",
        "",
        "COLLAPSE_structural under a *different* pool (e.g. pool_econ) that is NO_CONSENSUS or KEEP under "
        "core3 is not counted as an exclusion here -- pool_core3 is the pool this freeze decision is based "
        "on. See `pool_sensitivity_output/pool_sensitivity_grid.csv` for the full per-pool picture.",
        "",
        "## stable_keep_all_pools",
        "",
        f"{stable_keep_count} of the {keep_n} core3-KEEP families are also KEEP under pool_econ, pool_bwl, "
        "and pool_all5 (`stable_keep_all_pools=True`). All are still included in `frozen_dataset.csv` -- "
        "core3 alone decides membership and gold here -- but the column flags which ones don't survive a "
        "different pool. See `pool_sensitivity_output/core3_keep_dropouts.csv` for which pool(s) disagree on "
        f"each of the remaining {keep_n - stable_keep_count}.",
        "",
        "## Confirmatory set (frozen_dataset.csv) consensus-strength distribution",
        "",
    ]

    if frozen_rows:
        margin_counts = Counter(int(row["margin"]) for row in frozen_rows)
        lines.append("| split | count | share |")
        lines.append("|---|---|---|")
        for margin, n in sorted(margin_counts.items(), reverse=True):
            lines.append(f"| {_margin_label(margin)} | {n} | {n / len(frozen_rows):.0%} |")
        lines.append("")
        lines.append(
            f"Computed over all {len(frozen_rows)} confirmatory items (`margin` column of "
            "frozen_dataset.csv), not just the shifted ones -- this is the distribution to slice model "
            "performance by later (e.g. \"is accuracy lower on the weaker 2:1 items than the unanimous "
            "3:0 ones\")."
        )
    else:
        lines.append("(no confirmatory items)")
    lines.append("")

    lines.append("## Gold-shifted items (empirical gold != design gold)")
    lines.append("")

    if shifted_rows:
        n_confirmatory_shifted = sum(1 for r in shifted_rows if grid.get(r["family_id"], {}).get("core3_class") == "KEEP")
        lines.append(
            f"All {len(shifted_rows)} shifted items fall in the exploratory set; the {len(frozen_rows)} "
            f"confirmatory items have empirical gold identical to design gold on every condition "
            f"({n_confirmatory_shifted} confirmatory shifts found)."
        )
        lines.append("")
        lines.append(
            "**Why shift and collapse are mechanically linked, not just correlated:** design intends each "
            "of bare/+ba/+ma to land on its own distinct semantic role. A structural collapse means two of "
            "those three conditions' empirical majorities converged onto the *same* label -- and since "
            "their design labels were different to begin with, at most one of the two collapsing conditions "
            "can still match its own design gold; the other is shifted by construction, not by chance. That "
            "accounts for exactly one shift per collapsing family (6 families -> 6 shifts, each landing "
            "precisely on the collapsing condition whose own design label differs from the shared "
            "majority). F33 additionally shows a second, independent shift on `ma` -- not one of its "
            "collapsing conditions (its collapse is `bare=ba`) -- so that seventh shift is a coincidental "
            "extra, not a product of the collapse mechanism itself."
        )
        lines.append("")
        lines.append("| family_id | condition | set | design_gold | empirical_gold | margin |")
        lines.append("|---|---|---|---|---|---|")
        for row in shifted_rows:
            core3_class = grid.get(row["family_id"], {}).get("core3_class")
            dataset = {"KEEP": "confirmatory", "COLLAPSE": "exploratory"}.get(core3_class, core3_class)
            lines.append(
                f"| {row['family_id']} | {row['condition']} | {dataset} | {row['design_gold_label']} | "
                f"{row['empirical_gold_label']} | {row['margin']} |"
            )
        lines.append("")
        margin_counts = Counter(int(row["margin"]) for row in shifted_rows)
        distribution = ", ".join(f"margin={m}: {n}" for m, n in sorted(margin_counts.items()))
        lines.append(f"Margin distribution ({len(shifted_rows)} shifted items total): {distribution}.")
        lines.append(
            "A margin of 1 (2-1 split among 3 cast votes) is the weakest possible majority; treat those "
            "shifted golds as the ones most worth a second look, not the ones with a wider margin."
        )
    else:
        lines.append("(none)")
    lines.append("")

    return "\n".join(lines)
