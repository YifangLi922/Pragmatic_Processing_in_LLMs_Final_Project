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

Per-model breakdown in margin_stratified_accuracy_by_model.csv. Note there are three margin values in the real data (3:0, 2:1, and 2:0-with-one-abstention), not just the two named in the request -- all three are reported rather than folding the third into either named bucket.

## 3. Target-sentence delta (used_target)

**Note:** the ablation's confirmatory shortcut_risk set has **11 families**, not the 8 mentioned in the request -- verified directly against ablation_item_summary.csv (F01/F04/F14/F15/F16/F20/F23/F24/F30/F34/F36). Using the verified 11 for the sensitivity column below rather than silently matching an assumed 8.

### confirmatory

| model | n_valid_pairs | used_target_rate | (of which: ablation parse-failed / real alternative) |
|---|---|---|---|
| deepseek-r1-0528 | 60 | 60.0% | 0 / 36 |
| deepseek-v3 | 60 | 56.7% | 1 / 33 |
| gemini-3-flash-preview | 60 | 50.0% | 0 / 30 |
| gemma-4-31b | 60 | 78.3% | 35 / 12 |
| mistral-small-3-24b | 60 | 66.7% | 9 / 31 |
| qwen3-next-80b | 60 | 56.7% | 0 / 34 |

| model | accuracy_raw (n) | accuracy_purified (n) | accuracy_sensitivity (n) |
|---|---|---|---|
| deepseek-r1-0528 | 90.0% (60) | 88.9% (36) | 88.2% (17) |
| deepseek-v3 | 80.0% (60) | 82.4% (34) | 92.9% (14) |
| gemini-3-flash-preview | 81.7% (60) | 100.0% (30) | 100.0% (15) |
| gemma-4-31b | 78.3% (60) | 83.0% (47) | 79.2% (24) |
| mistral-small-3-24b | 91.7% (60) | 95.0% (40) | 100.0% (20) |
| qwen3-next-80b | 70.0% (60) | 76.5% (34) | 80.0% (15) |

### exploratory (own used_target rate; no sensitivity column -- see note above)

| model | n_valid_pairs | used_target_rate | (of which: ablation parse-failed / real alternative) |
|---|---|---|---|
| deepseek-r1-0528 | 18 | 66.7% | 0 / 12 |
| deepseek-v3 | 18 | 55.6% | 1 / 9 |
| gemini-3-flash-preview | 18 | 55.6% | 0 / 10 |
| gemma-4-31b | 18 | 88.9% | 11 / 5 |
| mistral-small-3-24b | 18 | 61.1% | 3 / 8 |
| qwen3-next-80b | 18 | 55.6% | 0 / 10 |

| model | accuracy_raw (n) | accuracy_purified (n) |
|---|---|---|
| deepseek-r1-0528 | 50.0% (18) | 66.7% (12) |
| deepseek-v3 | 55.6% (18) | 80.0% (10) |
| gemini-3-flash-preview | 61.1% (18) | 70.0% (10) |
| gemma-4-31b | 61.1% (18) | 68.8% (16) |
| mistral-small-3-24b | 61.1% (18) | 81.8% (11) |
| qwen3-next-80b | 55.6% (18) | 60.0% (10) |

## 4. Confusion matrices -- confirmatory, per model

Full 4x4 raw-count and row-normalized matrices are in confusion_matrix_confirmatory_counts.csv and confusion_matrix_confirmatory_rownorm.csv (rows=gold_semantic, cols=model choice). n_scored (parse_failed=False) per model:

- deepseek-r1-0528: 60
- deepseek-v3: 60
- gemini-3-flash-preview: 60
- gemma-4-31b: 60
- mistral-small-3-24b: 60
- qwen3-next-80b: 60
