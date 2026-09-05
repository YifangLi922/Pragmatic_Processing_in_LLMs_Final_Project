# Dataset Freeze Report

Generated from `pool_sensitivity_output/` (pool_core3). Total families: 36.
After this report and the two frozen CSVs are committed and tagged, the two CSVs are not edited again.

## Provenance

Tag `dataset-frozen-v1` -> commit `4f3e11d49ad7ed82e2e84c255be346ad05b5ba92`. frozen_dataset.csv and frozen_exploratory.csv are byte-identical to that commit; this report was completed afterward and re-committed separately (the tag stays pinned to the CSV-freezing commit, not this one).

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

- **NO_CONSENSUS** (8): at least one of bare/+ba/+ma has no reference-pool majority at all under pool_core3 (tie, 1-1-1 split, or too few cast votes).
- **EXCLUDE_BROKEN** (2): at least one condition's core3 majority landed on the DISTRACTOR role -- the item failed to activate any of its three target semantics on that condition, so the whole family is excluded even where another condition's numbers would otherwise look like an ordinary gold shift.

COLLAPSE_structural under a *different* pool (e.g. pool_econ) that is NO_CONSENSUS or KEEP under core3 is not counted as an exclusion here -- pool_core3 is the pool this freeze decision is based on. See `pool_sensitivity_output/pool_sensitivity_grid.csv` for the full per-pool picture.

## stable_keep_all_pools

11 of the 20 core3-KEEP families are also KEEP under pool_econ, pool_bwl, and pool_all5 (`stable_keep_all_pools=True`). All are still included in `frozen_dataset.csv` -- core3 alone decides membership and gold here -- but the column flags which ones don't survive a different pool. See `pool_sensitivity_output/core3_keep_dropouts.csv` for which pool(s) disagree on each of the remaining 9.

## Confirmatory set (frozen_dataset.csv) consensus-strength distribution

| split | count | share |
|---|---|---|
| 3:0 (unanimous, all 3 cast) | 38 | 63% |
| 2:0 (unanimous, 1 abstention) | 5 | 8% |
| 2:1 (majority, all 3 cast) | 17 | 28% |

Computed over all 60 confirmatory items (`margin` column of frozen_dataset.csv), not just the shifted ones -- this is the distribution to slice model performance by later (e.g. "is accuracy lower on the weaker 2:1 items than the unanimous 3:0 ones").

## Gold-shifted items (empirical gold != design gold)

All 7 shifted items fall in the exploratory set; the 60 confirmatory items have empirical gold identical to design gold on every condition (0 confirmatory shifts found).

**Why shift and collapse are mechanically linked, not just correlated:** design intends each of bare/+ba/+ma to land on its own distinct semantic role. A structural collapse means two of those three conditions' empirical majorities converged onto the *same* label -- and since their design labels were different to begin with, at most one of the two collapsing conditions can still match its own design gold; the other is shifted by construction, not by chance. That accounts for exactly one shift per collapsing family (6 families -> 6 shifts, each landing precisely on the collapsing condition whose own design label differs from the shared majority). F33 additionally shows a second, independent shift on `ma` -- not one of its collapsing conditions (its collapse is `bare=ba`) -- so that seventh shift is a coincidental extra, not a product of the collapse mechanism itself.

| family_id | condition | set | design_gold | empirical_gold | margin |
|---|---|---|---|---|---|
| F06 | ba | exploratory | confirmation | statement | 1 |
| F11 | ma | exploratory | neutral | confirmation | 1 |
| F12 | ma | exploratory | neutral | confirmation | 3 |
| F13 | ma | exploratory | neutral | confirmation | 1 |
| F18 | ba | exploratory | confirmation | neutral | 1 |
| F33 | ba | exploratory | confirmation | statement | 1 |
| F33 | ma | exploratory | neutral | confirmation | 1 |

Margin distribution (7 shifted items total): margin=1: 6, margin=3: 1.
A margin of 1 (2-1 split among 3 cast votes) is the weakest possible majority; treat those shifted golds as the ones most worth a second look, not the ones with a wider margin.
