"""Main-experiment scoring: condition accuracy, margin-stratified accuracy,
target-sentence delta analysis (vs. the context-only ablation), and
per-model confusion matrices -- all against main_experiment_output/
main_results.csv, gold taken verbatim from the frozen CSVs (already joined
into main_results.csv's gold_letter/gold_semantic columns at query time, not
re-derived here).

Every denominator is parse_failed=False responses only, reported alongside
each table (never silently implied). confirmatory and exploratory are never
pooled into one number. Tables (CSV) + one markdown summary only -- no
plots at this step.

Does not reuse src/scoring/ (the original module-5 design from before the
frozen-dataset/ablation pipeline existed): that module is built around
reconstructed.json + src.gold.exclusion's family_decisions/gold_results
objects, a data shape this step doesn't have or need -- main_results.csv
already carries gold per row. Forcing an adapter onto that shape would add
more complexity than it removes, so this is a small, purpose-built sibling
instead.
"""
