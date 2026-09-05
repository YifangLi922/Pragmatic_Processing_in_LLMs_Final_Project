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


def render_freeze_report(
    class_counts: dict[str, int],
    shifted_rows: list[dict],
    grid: dict,
    stable_keep_count: int,
    n_total_families: int,
) -> str:
    keep_n = class_counts.get("KEEP", 0)
    collapse_n = class_counts.get("COLLAPSE", 0)
    no_consensus_n = class_counts.get("NO_CONSENSUS", 0)
    broken_n = class_counts.get("EXCLUDE_BROKEN", 0)

    lines = [
        "# Dataset Freeze Report",
        "",
        f"Generated from `pool_sensitivity_output/` (pool_core3). Total families: {n_total_families}.",
        "After this report and the two frozen CSVs are committed and tagged, they are not edited again.",
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
        "## Gold-shifted items (empirical gold != design gold)",
        "",
    ]

    if shifted_rows:
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
