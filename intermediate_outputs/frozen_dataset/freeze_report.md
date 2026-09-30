# Dataset Freeze Report

Created from `intermediate_outputs/pool_sensitivity/` (pool_core3). Total families: 36.
Once the two frozen CSVs were committed and tagged, they were treated as read-only and were not edited again.

## Provenance

The two frozen CSV files are identified by Git tag `dataset-frozen-v1`, which points to commit `4f3e11d49ad7ed82e2e84c255be346ad05b5ba92`. The current copies of `frozen_dataset.csv` and `frozen_exploratory.csv` are byte-identical to the versions in that tagged commit. This report was finalized in a later commit; the tag intentionally remains on the commit that froze the dataset.

## Family counts by core3 class

| class | count |
|---|---|
| KEEP | 20 |
| COLLAPSE_structural | 6 |
| NO_CONSENSUS | 8 |
| EXCLUDE_BROKEN | 2 |
| **total** | **36** |

- `frozen_dataset.csv` (confirmatory): 20 families x 3 conditions = 60 rows.
- `frozen_exploratory.csv`: 6 families x 3 conditions = 18 rows.
- Neither file: 10 families (excluded from this freeze; see below).

## Family membership by class

- **KEEP** (20): F01, F02, F04, F07, F14, F15, F16, F17, F20, F21, F23, F24, F25, F27, F28, F30, F32, F34, F35, F36
- **COLLAPSE_structural** (6): F06, F11, F12, F13, F18, F33
- **NO_CONSENSUS** (8): F03, F05, F08, F10, F19, F22, F26, F29
- **EXCLUDE_BROKEN** (2): F09, F31

## Exclusion reasons (families in neither frozen file)

- **NO_CONSENSUS (8):** At least one of the three conditions (bare, +ba, or +ma) did not receive a clear majority label from the core3 annotators. This can happen when the valid votes are split (for example, 1-1-1), tied after an abstention, or too few valid votes remain to form a majority. Because a stable empirical gold label cannot be assigned to every condition, the whole family is excluded.
- **EXCLUDE_BROKEN (2):** At least one condition received a core3 majority for the DISTRACTOR option rather than for one of the three target semantic roles. This indicates that the item did not work as intended for that condition. Since dataset selection is done at the family level, the whole family is excluded, even if the other conditions in that family are otherwise interpretable.

Only the **core3 classification** is used to decide membership in this dataset freeze. A family may receive a different classification under another annotator pool (for example, `COLLAPSE_structural` under `pool_econ`), but that does not change how it is treated here. Cross-pool differences are reported separately in `intermediate_outputs/pool_sensitivity/pool_sensitivity_grid.csv`.

## stable_keep_all_pools

Of the 20 families classified as KEEP under core3, 11 are also classified as KEEP under all three alternative annotator pools: `pool_econ`, `pool_bwl`, and `pool_all5`. These families have `stable_keep_all_pools=True`. This variable is a sensitivity indicator, not an inclusion criterion. All 20 core3-KEEP families are included in `frozen_dataset.csv`, for core3 alone determines dataset membership and empirical gold labels for the primary analysis. The `stable_keep_all_pools` column simply shows whether a family would still be classified as KEEP if a different annotator pool were used.

For the remaining 9 families, see `intermediate_outputs/pool_sensitivity/core3_keep_dropouts.csv` for which alternative pool(s) produce a different classification.

## Confirmatory set (frozen_dataset.csv) consensus-strength distribution

| split | count | share |
|---|---|---|
| 3:0 (unanimous, all 3 cast) | 38 | 63% |
| 2:0 (unanimous, 1 abstention) | 5 | 8% |
| 2:1 (majority, all 3 cast) | 17 | 28% |

This distribution is calculated across all 60 confirmatory items using the `margin` column in `frozen_dataset.csv`. It records how strongly the core3 annotators agreed on each empirical gold label. The margin can later be used to check whether model performance differs between items with weaker human agreement (2:1) and items with unanimous agreement (3:0).

## Gold-shifted items (empirical gold != design gold)

All 7 items whose empirical gold differs from the original design gold are in the exploratory set. None of the 60 confirmatory items changed label: for every confirmatory item, the core3 empirical gold matches the original design gold.

**Why every collapsed family contains at least one gold shift:** The original design assigns a different semantic role to each of the three conditions: bare, +ba, and +ma. In a `COLLAPSE_structural` family, however, two conditions receive the same empirical gold label from the core3 annotators.Those two conditions were originally designed to have different labels, so they cannot both still match their own design gold once they collapse onto the same empirical label. At least one of them must count as a gold shift. This explains 6 of the 7 shifted items: each of the 6 collapsed families contributes one shift associated with its collapsed pair. F33 contains one additional shift. Its structural collapse is between bare and +ba, but its +ma condition also changes from the design gold `neutral` to the empirical gold `confirmation`. This +ma shift is separate from the bare/+ba collapse, which is why F33 contributes two shifted items instead of one.

| family_id | condition | set | design_gold | empirical_gold | margin |
|---|---|---|---|---|---|
| F06 | ba | exploratory | confirmation | statement | 1 |
| F11 | ma | exploratory | neutral | confirmation | 1 |
| F12 | ma | exploratory | neutral | confirmation | 3 |
| F13 | ma | exploratory | neutral | confirmation | 1 |
| F18 | ba | exploratory | confirmation | neutral | 1 |
| F33 | ba | exploratory | confirmation | statement | 1 |
| F33 | ma | exploratory | neutral | confirmation | 1 |

**Margin distribution (7 shifted items total)**: margin=1: 6, margin=3: 1. 

Among the 7 shifted items, 6 have `margin=1` and 1 has `margin=3`. A margin of 1 means that the empirical gold is based on a 2:1 split among the three core3 annotators, so one annotator preferred a different interpretation. These six shifts have weaker human agreement than the single `margin=3` shift, where all three annotators agreed. The `margin=1` cases are consequently the most useful ones to inspect individually when interpreting the exploratory results.

Note: The table above lists all 7 items for which the empirical gold differs from the original design gold. Later `design_gold_following` analyses focus on a narrower subset of 4 +ma items whose gold shifts specifically from NEUTRAL to TENTATIVE.

## Context-only ablation validation

After the dataset was frozen, a context-only ablation was used as an additional check that the surrounding context did not by itself determine the intended answer. In this ablation, the target sentence was removed while the context, question, and answer options were left unchanged. Once the target sentence is removed, the bare, +ba, and +ma versions of the same family become identical prompts. Each model produces only one context-based default answer for that family. If this default happens to match the gold label of one condition, it can appear as a "shortcut" for that condition even though no condition-specific information remains in the prompt.

For the 20 confirmatory families, no context-only default was ASSERT, so **the bare-condition shortcut rate was 0%**. Some defaults instead matched the +ba gold (TENTATIVE) in 8 of 20 families or the +ma gold (NEUTRAL) in 3 of 20 families. The three ablated prompts within a family are identical. These matches are better interpreted as model-specific default-label preferences instead of evidence that the context itself reveals the correct +ba or +ma answer. No families were excluded on this basis. See `intermediate_outputs/ablation/ablation_summary_confirmatory.md` for the detailed ablation results.

The main experiment provided a second check on whether the target sentence affected model behavior. Comparing each model's context-only answer with its full-prompt answer shows that models changed their response on approximately 48–67% of comparable confirmatory items. This calculation includes only items for which both an ablation response and a main-experiment response were available. The result shows that adding the target sentence often changes the model's interpretation, although a changed answer is not necessarily a correct one. See `results/main_scoring/target_sentence_delta/used_target_by_model.csv` for the full comparison.

