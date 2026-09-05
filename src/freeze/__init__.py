"""Dataset freeze: assembles frozen_dataset.csv (confirmatory, core3 KEEP
families) and frozen_exploratory.csv (core3 COLLAPSE_structural families)
from the already-generated pool sensitivity outputs
(pool_sensitivity_output/pool_sensitivity_grid.csv,
empirical_gold_core3.csv, collapse_breakdown.csv) joined with item text from
data/reconstructed_5ann.json. Also writes freeze_report.md.

This is the last step before the dataset is frozen -- after this runs and
its two CSVs are committed and tagged, they are not edited again. Nothing
here re-derives majority votes or classifications; it only reads and joins
what pool sensitivity already computed, so the frozen files are guaranteed
consistent with pool_sensitivity_output/ at the moment of freezing.
"""
