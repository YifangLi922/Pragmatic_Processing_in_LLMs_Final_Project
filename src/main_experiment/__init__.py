"""The main experiment: same frozen items, same model roster, same call
params, same prompt template family, and the same option_semantic_map-based
parsing as the context-only ablation (src.ablation) -- the one and only
difference is that build_prompt() keeps target_sentence in the prompt,
where the ablation's build_context_only_prompt() drops it. This is what
makes the two runs comparable item-for-item.

Reuses src.ablation.sources.load_ablation_items for item loading (so both
runs see the identical item set/order/text), src.llm_query.prompt.build_prompt,
src.llm_query.parser.parse_answer, src.llm_query.providers, and
src.llm_query.runner.run_items's call/retry/cost-guard/checkpoint/circuit-
breaker loop -- only the record shape written to disk differs (see
record.py), matching the field list the user specified for this step.

This step only queries and writes main_results.jsonl/.csv. Aggregate
analysis and the ablation-vs-main delta comparison are separate, deliberate
follow-up steps, not run here.
"""
