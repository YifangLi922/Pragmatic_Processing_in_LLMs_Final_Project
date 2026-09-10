"""Human LOO baseline restricted to the frozen 20 confirmatory (core3 KEEP)
families and the core3 pool (Media/Materials/EngLit) only.

Answers a specific question the earlier diagnostic couldn't: the
intermediate_outputs/diagnostic/diagnostic_summary_all_annotators.csv numbers (bare 0.95,
ba/ma ~0.58) average each of Media/Materials/EngLit's leave-one-out
agreement against a reference pool that includes Econ, computed over all 36
families -- 16 of which were later excluded (COLLAPSE/NO_CONSENSUS/
EXCLUDE_BROKEN) precisely because they *don't* have a clean human majority.
Folding those in understates how well core3 agrees with itself on the
families that actually made it into the frozen confirmatory set, and having
Econ in the pool is a different question (Econ's own divergence) from "how
much do the three trusted annotators agree with each other".

This module answers the narrower, fairer question: among the 20 KEEP
families only, with a pool of exactly Media/Materials/EngLit (no Econ, no
BWL), what is the LOO agreement rate per condition? That is the number
model accuracy should actually be compared against.

Reuses src.agreement.loo_baseline.loo_human_baseline unmodified -- it
already implements exactly this (auto-detects annotators present in the
input, per-condition + overall, fold-then-average) generically for however
many annotators are in the data; this module's only job is to build that
restricted input (20 families, core3-only annotations).
"""
