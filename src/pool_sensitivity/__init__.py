"""Pool sensitivity grid + empirical gold (pool_sensitivity_spec_for_claude_code.md).

Dataset-level analysis: classifies each of the 36 families as KEEP / COLLAPSE
/ NO_CONSENSUS under four different annotator pools, to see which families'
three-way (bare/ba/ma) contrast survives regardless of which annotators are
in the reference pool. Also derives empirical gold from pool_core3's
majority vote and flags where it shifts away from the design gold.

Purely descriptive: no family is auto-excluded, no model is run, no
significance testing. Reuses src.diagnostic.core.resolve_vote for the
no-option handling rather than reimplementing it.
"""
