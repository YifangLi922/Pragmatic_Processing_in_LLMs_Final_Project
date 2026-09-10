# Main experiment scoring summary

## Precondition check (main_results vs. ablation_results)

PASS

Model rosters match (6 models), item sets match (78 items), and gold_letter agrees on every item -- main and ablation are comparable item-for-item.

## 1. Condition accuracy -- confirmatory (60 items)

| model | n_valid | accuracy | bare (n) | ba (n) | ma (n) |
|---|---|---|---|---|---|
| deepseek-r1-0528 | 60 | 90.0% | 95.0% (20) | 100.0% (20) | 75.0% (20) |
| deepseek-v3 | 60 | 80.0% | 100.0% (20) | 40.0% (20) | 100.0% (20) |
| gemini-3-flash-preview | 60 | 81.7% | 90.0% (20) | 100.0% (20) | 55.0% (20) |
| gemma-4-31b | 60 | 78.3% | 100.0% (20) | 100.0% (20) | 35.0% (20) |
| mistral-small-3-24b | 60 | 91.7% | 85.0% (20) | 90.0% (20) | 100.0% (20) |
| qwen3-next-80b | 60 | 70.0% | 100.0% (20) | 65.0% (20) | 45.0% (20) |

## 1. Condition accuracy -- exploratory (18 items, NOT comparable to confirmatory)

Exploratory families have two conditions sharing the same human-majority gold by construction (that's why they're COLLAPSE, not KEEP) -- a higher accuracy here reflects that structural baseline, not stronger model performance.

| model | n_valid | accuracy | bare (n) | ba (n) | ma (n) |
|---|---|---|---|---|---|
| deepseek-r1-0528 | 18 | 50.0% | 100.0% (6) | 50.0% (6) | 0.0% (6) |
| deepseek-v3 | 18 | 55.6% | 100.0% (6) | 33.3% (6) | 33.3% (6) |
| gemini-3-flash-preview | 18 | 61.1% | 100.0% (6) | 50.0% (6) | 33.3% (6) |
| gemma-4-31b | 18 | 61.1% | 100.0% (6) | 50.0% (6) | 33.3% (6) |
| mistral-small-3-24b | 18 | 61.1% | 100.0% (6) | 50.0% (6) | 33.3% (6) |
| qwen3-next-80b | 18 | 55.6% | 100.0% (6) | 33.3% (6) | 33.3% (6) |

## 2. Margin-stratified accuracy -- confirmatory, pooled across models

| margin | n_items | n_valid | accuracy |
|---|---|---|---|
| 3:0 (unanimous, all 3 cast) | 38 | 228 | 82.0% |
| 2:0 (unanimous, 1 abstention) | 5 | 30 | 80.0% |
| 2:1 (majority, all 3 cast) | 17 | 102 | 82.4% |

Per-model breakdown in margin_stratified_accuracy/margin_stratified_accuracy_by_model.csv. Note there are three margin values in the real data (3:0, 2:1, and 2:0-with-one-abstention), not just the two named in the request -- all three are reported rather than folding the third into either named bucket.

## 3. Target-sentence delta (used_target) and update_precision

**Note:** the ablation's confirmatory shortcut_risk set has **11 families**, not the 8 mentioned in the request -- verified directly against ablation_item_summary.csv (F01/F04/F14/F15/F16/F20/F23/F24/F30/F34/F36). Using the verified 11 for the sensitivity column below rather than silently matching an assumed 8.

**used_target denominator is both-answered pairs only.** A model that refused to answer the ablation (no target sentence) gives no baseline judgment to compare against -- that's excluded from the denominator entirely (`n_excluded_no_ablation_answer`), not counted as used_target=True. An earlier version of this table counted it as True, which inflated gemma-4-31b's and mistral-small-3-24b's rates since they refuse most often in the ablation.

**update_precision is not a corrected accuracy.** It's the accuracy *only on the items where the model changed its answer* once shown the target sentence -- a distinct question ("when the model updates on the sentence, is the update usually right?") reported side by side with raw accuracy, never as a replacement for it.

### confirmatory

| model | n_valid_pairs | used_target_rate | n_excluded_no_ablation_answer |
|---|---|---|---|
| deepseek-r1-0528 | 60 | 60.0% | 0 |
| deepseek-v3 | 59 | 55.9% | 1 |
| gemini-3-flash-preview | 60 | 50.0% | 0 |
| gemma-4-31b | 25 | 48.0% | 35 |
| mistral-small-3-24b | 51 | 60.8% | 9 |
| qwen3-next-80b | 60 | 56.7% | 0 |

| model | accuracy_raw (n) | update_precision (n) | update_precision_sensitivity (n) |
|---|---|---|---|
| deepseek-r1-0528 | 90.0% (60) | 88.9% (36) | 88.2% (17) |
| deepseek-v3 | 80.0% (60) | 81.8% (33) | 92.9% (14) |
| gemini-3-flash-preview | 81.7% (60) | 100.0% (30) | 100.0% (15) |
| gemma-4-31b | 78.3% (60) | 83.3% (12) | 75.0% (8) |
| mistral-small-3-24b | 91.7% (60) | 93.5% (31) | 100.0% (12) |
| qwen3-next-80b | 70.0% (60) | 76.5% (34) | 80.0% (15) |

### exploratory (own used_target rate; no sensitivity column -- see note above)

| model | n_valid_pairs | used_target_rate | n_excluded_no_ablation_answer |
|---|---|---|---|
| deepseek-r1-0528 | 18 | 66.7% | 0 |
| deepseek-v3 | 17 | 52.9% | 1 |
| gemini-3-flash-preview | 18 | 55.6% | 0 |
| gemma-4-31b | 7 | 71.4% | 11 |
| mistral-small-3-24b | 15 | 53.3% | 3 |
| qwen3-next-80b | 18 | 55.6% | 0 |

| model | accuracy_raw (n) | update_precision (n) |
|---|---|---|
| deepseek-r1-0528 | 50.0% (18) | 66.7% (12) |
| deepseek-v3 | 55.6% (18) | 88.9% (9) |
| gemini-3-flash-preview | 61.1% (18) | 70.0% (10) |
| gemma-4-31b | 61.1% (18) | 60.0% (5) |
| mistral-small-3-24b | 61.1% (18) | 87.5% (8) |
| qwen3-next-80b | 55.6% (18) | 60.0% (10) |

used_target_rate and update_precision broken out by condition (bare/ba/ma), one row per (model, condition), both-answered-pairs denominator per cell: see `target_sentence_delta/used_target_by_model_condition.csv` and `target_sentence_delta/update_precision_by_model_condition.csv`.

**Raw condition accuracy conflates two different things.** Splitting each (model, condition)'s both-answered items by whether the *ablation* answer already equaled gold (prior_correct) or not (prior_incorrect), and reporting each group's own main-experiment accuracy separately, is what actually measures "used the target sentence to fix a wrong judgment" -- only the prior_incorrect group's accuracy answers that question. See `target_sentence_delta/prior_correction_by_model_condition.csv`.

## 4. Confusion matrices -- confirmatory, per model

Full 4x4 raw-count and row-normalized matrices are in confusion_matrices/confusion_matrix_confirmatory_counts.csv and confusion_matrices/confusion_matrix_confirmatory_rownorm.csv (rows=gold_semantic, cols=model choice). n_scored (parse_failed=False) per model:

- deepseek-r1-0528: 60
- deepseek-v3: 60
- gemini-3-flash-preview: 60
- gemma-4-31b: 60
- mistral-small-3-24b: 60
- qwen3-next-80b: 60

## 5. Design-gold following on shifted exploratory items (qualitative, n=4 families)

For the 4 exploratory families whose "ma" condition gold shifted from design (neutral) to empirical (confirmation) -- F11/F12/F13/F33 -- what fraction of each model's choice on that condition equals the *design* gold (neutral) rather than the *empirical* gold the model is actually scored against. F06/F18 are excluded: their "ma" gold never shifted, so they can't speak to this question. Only 4 items -- report as a qualitative pattern, not a statistic.

| model | n_shifted_items | n_matches_design_gold | design_gold_following_rate |
|---|---|---|---|
| deepseek-r1-0528 | 4 | 4 | 100.0% |
| deepseek-v3 | 4 | 4 | 100.0% |
| gemini-3-flash-preview | 4 | 3 | 75.0% |
| gemma-4-31b | 4 | 2 | 50.0% |
| mistral-small-3-24b | 4 | 3 | 75.0% |
| qwen3-next-80b | 4 | 2 | 50.0% |
