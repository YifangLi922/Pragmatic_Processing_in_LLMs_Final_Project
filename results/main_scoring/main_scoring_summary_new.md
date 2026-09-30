# Main experiment scoring summary

This page is the reader-facing summary of the final model-scoring outputs. It is intended to be understandable without first reading the pipeline documentation.

The **confirmatory set** contains 20 human-validated families, or 60 items. Within each family, the bare, +吧, and +吗 conditions have three distinct empirical gold interpretations. The **exploratory set** contains 6 families, or 18 items, in which two conditions share the same empirical gold label. Its accuracy is reported separately and should not be compared directly with confirmatory accuracy.

The **context-only ablation** removes the target sentence while keeping the context, question, and answer options unchanged. Comparing the ablation response with the full-prompt response shows whether the model's answer changes once the target sentence is restored.

Unless stated otherwise, **gold** refers to the frozen empirical gold label defined by the core3 native-speaker majority.

---

## 0. Sanity check: can the main and ablation runs be paired item by item?

**PASS.**

The main experiment and the context-only ablation contain the same 6 models and the same 78 frozen items, and the empirical gold answer agrees for every item across the two result files. The two runs can therefore be compared item by item in the before/after analyses below.

---

## 1. Condition accuracy

### 1.1 Confirmatory set: 60 items

Each model is scored on 20 bare, 20 +吧, and 20 +吗 items. `n_scored` is the number of main-experiment responses that could be parsed as a valid A-D choice.

| model | n_scored | overall accuracy | bare (n=20) | +吧 (n=20) | +吗 (n=20) |
|---|---:|---:|---:|---:|---:|
| deepseek-r1-0528 | 60 | 90.0% | 95.0% | 100.0% | 75.0% |
| deepseek-v3 | 60 | 80.0% | 100.0% | 40.0% | 100.0% |
| gemini-3-flash-preview | 60 | 81.7% | 90.0% | 100.0% | 55.0% |
| gemma-4-31b | 60 | 78.3% | 100.0% | 100.0% | 35.0% |
| mistral-small-3-24b | 60 | 91.7% | 85.0% | 90.0% | 100.0% |
| qwen3-next-80b | 60 | 70.0% | 100.0% | 65.0% | 45.0% |

Overall confirmatory accuracy ranges from 70.0% to 91.7%, while condition-level accuracy ranges from 35.0% to 100.0%. The main pattern is not a uniform model ranking: several models are very strong on one condition and much weaker on another.

Detailed tables are in `condition_accuracy/`.

### 1.2 Exploratory set: 18 items

The exploratory set has a different structure. In every exploratory family, two of the three conditions share the same human-majority gold label. A model that repeatedly gives that shared label can be correct on two conditions without distinguishing the three sentence-final forms.

For this reason, exploratory accuracy is **not directly comparable** with confirmatory accuracy and should not be interpreted as evidence of stronger or weaker overall model performance.

| model | n_scored | overall accuracy | bare (n=6) | +吧 (n=6) | +吗 (n=6) |
|---|---:|---:|---:|---:|---:|
| deepseek-r1-0528 | 18 | 50.0% | 100.0% | 50.0% | 0.0% |
| deepseek-v3 | 18 | 55.6% | 100.0% | 33.3% | 33.3% |
| gemini-3-flash-preview | 18 | 61.1% | 100.0% | 50.0% | 33.3% |
| gemma-4-31b | 18 | 61.1% | 100.0% | 50.0% | 33.3% |
| mistral-small-3-24b | 18 | 61.1% | 100.0% | 50.0% | 33.3% |
| qwen3-next-80b | 18 | 55.6% | 100.0% | 33.3% | 33.3% |

Use these results for exploratory, context-sensitive patterns rather than for direct ranking against the confirmatory scores.

---

## 2. Does model accuracy depend on how strongly the human annotators agreed?

The frozen dataset records the strength of core3 support for each empirical gold label:

- **3:0**: all three annotators selected the same gold label;
- **2:0**: two valid annotators agreed and one annotator abstained;
- **2:1**: two annotators formed the majority and one selected another label.

Pooling the six models over the confirmatory set gives:

| core3 support | n_items | n_scored model responses | accuracy |
|---|---:|---:|---:|
| 3:0 | 38 | 228 | 82.0% |
| 2:0 with one abstention | 5 | 30 | 80.0% |
| 2:1 | 17 | 102 | 82.4% |

Accuracy is nearly unchanged across the three support levels (80.0-82.4%). This is a robustness check on this dataset, not evidence that annotation agreement is irrelevant in general.

The per-model breakdown is in:

`margin_stratified_accuracy/margin_stratified_accuracy_by_model.csv`

---

## 3. What changes when the target sentence is restored?

This section compares each model's context-only answer with its answer to the full prompt.

Two measures are reported:

- **Answer-change rate** (stored as `used_target`): the proportion of comparable item-model pairs for which the parsed answer changes after the target sentence is restored.
- **Update precision**: among the comparable pairs where the answer changes, the proportion of the new answers that match the empirical gold.

These measures answer different questions. The answer-change rate describes **how often** the model changes its response. Update precision describes **how often those changes are correct**.

(Note: An unchanged answer does not prove that the model ignored the target sentence, and a changed answer does not by itself prove successful pragmatic interpretation.)

### 3.1 Denominator for the before/after comparison

The comparison includes only pairs with a valid answer in both runs. If the model refused or produced an unparseable answer in the context-only ablation, there is no baseline judgment to compare with the main response, so that pair is excluded.

### 3.2 Confirmatory set: answer-change rate

| model | comparable pairs | answer-change rate | missing ablation baseline |
|---|---:|---:|---:|
| deepseek-r1-0528 | 60 | 60.0% | 0 |
| deepseek-v3 | 59 | 55.9% | 1 |
| gemini-3-flash-preview | 60 | 50.0% | 0 |
| gemma-4-31b | 25 | 48.0% | 35 |
| mistral-small-3-24b | 51 | 60.8% | 9 |
| qwen3-next-80b | 60 | 56.7% | 0 |

The paired denominator varies because some models, especially Gemma, produced context-only responses that could not be used as a baseline.

### 3.3 Confirmatory set: were the changed answers correct?

Ordinary main-experiment accuracy uses all scored confirmatory items. Update precision uses only the subset of comparable pairs where the model changed its answer.

| model | main accuracy (n) | update precision (n changed) | update precision, 11-family sensitivity subset (n changed) |
|---|---:|---:|---:|
| deepseek-r1-0528 | 90.0% (60) | 88.9% (36) | 88.2% (17) |
| deepseek-v3 | 80.0% (60) | 81.8% (33) | 92.9% (14) |
| gemini-3-flash-preview | 81.7% (60) | 100.0% (30) | 100.0% (15) |
| gemma-4-31b | 78.3% (60) | 83.3% (12) | 75.0% (8) |
| mistral-small-3-24b | 91.7% (60) | 93.5% (31) | 100.0% (12) |
| qwen3-next-80b | 70.0% (60) | 76.5% (34) | 80.0% (15) |

The final column repeats the same update-precision calculation on the 11-family confirmatory subset flagged by the ablation analysis:

`F01 / F04 / F14 / F15 / F16 / F20 / F23 / F24 / F30 / F34 / F36`

The upstream scoring output labels this subset `shortcut_risk`. Because the present summary does not contain the rule by which that upstream label was assigned, the column is presented here simply as a restricted **sensitivity analysis**, not as a separate primary metric.

### 3.4 Exploratory set: answer changes and update precision

The exploratory items use their own before/after comparison. The confirmatory-only 11-family sensitivity column is not applied here.

| model | comparable pairs | answer-change rate | missing ablation baseline |
|---|---:|---:|---:|
| deepseek-r1-0528 | 18 | 66.7% | 0 |
| deepseek-v3 | 17 | 52.9% | 1 |
| gemini-3-flash-preview | 18 | 55.6% | 0 |
| gemma-4-31b | 7 | 71.4% | 11 |
| mistral-small-3-24b | 15 | 53.3% | 3 |
| qwen3-next-80b | 18 | 55.6% | 0 |

| model | exploratory accuracy (n) | update precision (n changed) |
|---|---:|---:|
| deepseek-r1-0528 | 50.0% (18) | 66.7% (12) |
| deepseek-v3 | 55.6% (18) | 88.9% (9) |
| gemini-3-flash-preview | 61.1% (18) | 70.0% (10) |
| gemma-4-31b | 61.1% (18) | 60.0% (5) |
| mistral-small-3-24b | 61.1% (18) | 87.5% (8) |
| qwen3-next-80b | 55.6% (18) | 60.0% (10) |

For condition-specific results, including whether a model changes its answer more often on bare, +吧, or +吗, see:

- `target_sentence_delta/used_target_by_model_condition.csv`
- `target_sentence_delta/update_precision_by_model_condition.csv`

### 3.5 Did the target sentence correct an initially wrong answer?

A correct full-prompt answer can arise in two different ways:

1. the context-only answer already matched the gold label; or
2. the context-only answer was wrong, and the full-prompt answer became correct after the target sentence was restored.

The file

`target_sentence_delta/prior_correction_by_model_condition.csv`

separates these two cases for every model and condition:

- `prior_correct`: the context-only answer already equaled gold;
- `prior_incorrect`: the context-only answer differed from gold.

The `prior_incorrect` group is the more informative one for measuring correction. In these cases, the model first gave a wrong answer from the context alone, but gave the correct answer after the target sentence was restored. This provides clearer evidence that the target sentence helped the model revise its judgment. In the `prior_correct` group, the model was already correct before seeing the target sentence. If it is still correct in the full prompt, we cannot tell whether the target sentence affected its interpretation or whether it simply kept the same already-correct answer.

---

## 4. What kinds of errors do the models make?

The confirmatory confusion matrices compare empirical gold roles with model responses. Rows are gold labels and columns are model choices, using the fixed order:

`ASSERT, TENTATIVE, NEUTRAL, DISTRACTOR`

All six models have 60 scored confirmatory responses, so there are no main-experiment parse failures in this set.

The clearest directional error concerns **+吗 / NEUTRAL** items: whenever a model makes an error on a confirmatory +吗 item, the response is **TENTATIVE**, the interpretation associated with +吧. No +吗 error goes to ASSERT or DISTRACTOR.

The full raw-count and row-normalized matrices are in:

- `confusion_matrices/confusion_matrix_confirmatory_counts.csv`
- `confusion_matrices/confusion_matrix_confirmatory_rownorm.csv`

Use the row-normalized file to compare error direction across models; use the raw-count file when exact item counts matter.

---

## 5. When human empirical gold differs from the original design, which interpretation do models follow?

This analysis uses four exploratory +吗 items: **F11, F12, F13, and F33**.

For these items, the original design expected +吗 to receive its usual **NEUTRAL** reading, while in the specific context, the core3 native-speaker majority instead interpreted it as **TENTATIVE**. The model is scored against the empirical human label, but this additional analysis asks whether it instead selects the original design label.

F06 and F18 are not included because their +吗 gold label did not shift away from the original design label.

| model | shifted +吗 items | original design label selected |
|---|---:|---:|
| deepseek-r1-0528 | 4 | 4/4 (100.0%) |
| deepseek-v3 | 4 | 4/4 (100.0%) |
| gemini-3-flash-preview | 4 | 3/4 (75.0%) |
| gemma-4-31b | 4 | 2/4 (50.0%) |
| mistral-small-3-24b | 4 | 3/4 (75.0%) |
| qwen3-next-80b | 4 | 2/4 (50.0%) |

This is the most direct comparison between the original canonical design label and the context-sensitive human label. However, it contains only four items. Report the counts and percentages descriptively and treat the pattern as **qualitative**, not as a stable population estimate.

The underlying files are in `design_gold_following/`.
