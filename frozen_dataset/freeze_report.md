# Dataset Freeze Report

Generated from `pool_sensitivity_output/` (pool_core3). Total families: 36.
After this report and the two frozen CSVs are committed and tagged, they are not edited again.

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

## Exclusion reasons (families in neither frozen file)

- **NO_CONSENSUS** (8): at least one of bare/+ba/+ma has no reference-pool majority at all under pool_core3 (tie, 1-1-1 split, or too few cast votes).
- **EXCLUDE_BROKEN** (2): at least one condition's core3 majority landed on the DISTRACTOR role -- the item failed to activate any of its three target semantics on that condition, so the whole family is excluded even where another condition's numbers would otherwise look like an ordinary gold shift.

COLLAPSE_structural under a *different* pool (e.g. pool_econ) that is NO_CONSENSUS or KEEP under core3 is not counted as an exclusion here -- pool_core3 is the pool this freeze decision is based on. See `pool_sensitivity_output/pool_sensitivity_grid.csv` for the full per-pool picture.

## stable_keep_all_pools

11 of the 20 core3-KEEP families are also KEEP under pool_econ, pool_bwl, and pool_all5 (`stable_keep_all_pools=True`). All are still included in `frozen_dataset.csv` -- core3 alone decides membership and gold here -- but the column flags which ones don't survive a different pool. See `pool_sensitivity_output/core3_keep_dropouts.csv` for which pool(s) disagree on each of the remaining 9.

## Gold-shifted items (empirical gold != design gold)

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
