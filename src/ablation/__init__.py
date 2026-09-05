"""Context-only ablation: strip target_sentence from the prompt, keep
context/question/options/instructions/output-format identical to the main
experiment, and see how often models still land on gold from context alone.

Reuses the main experiment's pipeline throughout -- src.llm_query.prompt's
build_context_only_prompt (added alongside build_prompt, not a fork),
src.llm_query.runner.run_items (the same call/retry/cost-guard/checkpoint
loop as the main experiment, just fed a different prompt builder),
src.llm_query.parser.parse_answer, and src.llm_query.providers. Nothing here
re-derives letter->semantic mappings: option_semantic_map, already computed
and frozen in frozen_dataset.csv / frozen_exploratory.csv, is parsed back
into a dict and used as-is.

Two frozen files (confirmatory, exploratory), one run, one item list -- but
every output downstream is split by `set` so the two are never pooled into
one number, per spec.
"""
