# SFP-ba: Results and Metrics Guide

This guide documents the result structure for the SFP-ba project. It explains the confirmatory and exploratory datasets, model and human metrics, context-only ablation, confusion matrices, denominators, CSV fields, figures, and common interpretation errors.

## 1. Where to start

The best entry point is:

[`../results/main_scoring/main_scoring_summary.md`](../results/main_scoring/main_scoring_summary.md)

It provides the narrated summary of the final tables. Use this guide when you need to understand a metric, denominator, subfolder, or column in more detail.

A practical reading order is:

1. `condition_accuracy/` for the headline model scores;
2. `human_baseline_core3/` for the human reference;
3. `confusion_matrices/` for error direction;
4. `target_sentence_delta/` for prior-versus-update behavior;
5. `design_gold_following/` for the qualitative context/canonical comparison;
6. `margin_stratified_accuracy/` for the robustness check by human vote strength.

## 2. Analysis sets

### 2.1 Confirmatory set

The primary analysis uses **20 families × 3 conditions = 60 items**. Every family has a distinct empirical gold label for bare, +吧, and +吗.

Under the core3 gold pool, the confirmatory condition labels are:

| Condition | Gold semantic role | Items |
|---|---|---:|
| bare | `ASSERT` | 20 |
| +吧 | `TENTATIVE` | 20 |
| +吗 | `NEUTRAL` | 20 |

Use this set for model accuracy, human/model comparisons, confusion matrices, and the main confirmatory conclusions.

### 2.2 Exploratory set

The exploratory analysis uses **6 families × 3 conditions = 18 items**. In every family, two conditions share an empirical gold label. These families remain interpretable, but the intended three-way contrast has collapsed under native-speaker majority judgment.

Do not compare exploratory accuracy directly with confirmatory accuracy. A single answer can be correct for two conditions in a collapsed family, so the exploratory structure may favor a default-label strategy.

Use the exploratory set for questions such as:

- Which conditions collapse together in native-speaker judgments?
- In what direction does the collapse occur?
- When empirical gold differs from design intent, do models follow the contextual human reading or the original canonical label?

### 2.3 Excluded families

Ten candidate families do not enter either frozen set:

- 8 `NO_CONSENSUS` families, where at least one condition lacks a core3 majority;
- 2 `EXCLUDE_BROKEN` families, where at least one majority selects the distractor.

These exclusions belong to dataset validation, not model scoring. See [`dataset_and_annotation.md`](dataset_and_annotation.md).

## 3. Semantic labels

The project uses four semantic roles:

| Label | Meaning |
|---|---|
| `ASSERT` | confident statement of proposition `P` |
| `TENTATIVE` | the speaker leans toward `P` but seeks confirmation |
| `NEUTRAL` | neutral yes/no question with no stated leaning |
| `DISTRACTOR` | an intentionally irrelevant interpretation |

In the stored item files, the equivalent lower-case descriptions may appear as `statement`, `confirmation`, `neutral`, and `distractor`. `option_semantic_map` connects the displayed answer letter to the underlying role.

The displayed A/B/C/D position is not itself meaningful. Option order is shuffled once per family and held constant across its three conditions.

## 4. Headline model accuracy

The primary table contains 60 confirmatory items per model:

| Model | Overall | bare | +吧 | +吗 |
|---|---:|---:|---:|---:|
| deepseek-r1-0528 | 90.0% | 95% | 100% | 75% |
| deepseek-v3 | 80.0% | 100% | **40%** | 100% |
| gemini-3-flash-preview | 81.7% | 90% | 100% | 55% |
| gemma-4-31b | 78.3% | 100% | 100% | **35%** |
| mistral-small-3-24b | 91.7% | 85% | 90% | 100% |
| qwen3-next-80b | 70.0% | 100% | 65% | 45% |

Overall accuracy spans 70.0–91.7%; condition accuracy spans 35–100%. The important pattern is not only rank order. Several models are perfect on one particle condition and weak on another, which motivates the default-label and target-sentence analyses.

## 5. Human baseline

Human results are under:

[`../results/human_baseline_core3/`](../results/human_baseline_core3/)

| Condition | Leave-one-out | Concordance |
|---|---:|---:|
| bare | 98.3% | 98.3% |
| +吧 | 66.6% | 78.3% |
| +吗 | 83.9% | 86.7% |

### 5.1 Leave-one-out baseline

For each fold, one core3 annotator is held out. The other two annotators define a temporary reference, and the held-out annotator is scored against it.

On an item with a 2:1 split, the minority annotator is necessarily counted as incorrect in their fold. LOO therefore acts as a systematic lower bound on human performance.

### 5.2 Concordance

For each item, concordance is the fraction of all three core3 annotators whose answer matches the final empirical gold. These values are then averaged within condition.

Concordance is the preferred descriptive comparison with model accuracy because both ask what share of answers match the same final gold label.

### 5.3 Main human/model contrast

Humans agree least on +吧, while model performance is generally weakest on +吗. This mismatch means that model difficulty cannot be reduced to whichever condition is also hardest for native speakers.

## 6. `condition_accuracy/`

This folder reports accuracy by model and condition for confirmatory and exploratory items separately.

Use confirmatory files for headline percentages. Keep the following distinctions explicit when reporting:

- overall accuracy uses all 60 confirmatory items;
- each condition accuracy uses 20 confirmatory items;
- exploratory denominators are smaller and structurally different;
- an apparently high exploratory result does not imply stronger contrastive sensitivity.

If a report combines +吧 and +吗 or averages across sets, state the exact denominator and rationale. The repository's standard outputs intentionally preserve the separation.

## 7. `margin_stratified_accuracy/`

The empirical gold has three possible core3 support patterns:

| `margin` | Annotation pattern | Interpretation |
|---:|---|---|
| `3` | 3:0 | unanimous |
| `2` | 2:0 plus one abstention | unanimous among valid answers |
| `1` | 2:1 | majority |

The margin-stratified outputs test whether models perform worse on items with weaker human consensus. In this dataset, confirmatory accuracy is approximately flat across margins, at roughly 80–82%.

This is a robustness check rather than a central finding. Do not infer that agreement strength never matters in general; the result describes this dataset and its small item counts.

## 8. Context-only ablation

The ablation removes the target sentence while preserving context, question, and answer options.

Within a family, all three ablation prompts are byte-for-byte identical because the target sentence is the only condition-varying field. A model therefore produces one context-conditioned default per family. The repeated condition rows record how that single default compares with each condition's gold; they do not represent three independent context-only trials.

This distinction prevents a common misreading. If a family default equals TENTATIVE, it will look “correct” against the +吧 row and incorrect against bare and +吗. That does not mean the +吧 context leaked a condition-specific answer—the context is identical for all three rows.

No context-only default is ASSERT, which yields a 0% bare shortcut rate. Observed TENTATIVE and NEUTRAL defaults are best examined as model-specific priors.

## 9. `target_sentence_delta/`

This folder compares each model's context-only answer with its main-experiment answer after the target sentence is restored.

### 9.1 `used_target_by_model[_condition].csv`

`used_target` indicates whether the parsed answer changed between the ablation and main experiment.

Its denominator contains **both-answered pairs only**. If a model refuses or produces an unparseable response in the ablation, that row provides no before/after comparison. It is excluded rather than counted as “did not use the target.”

Changing an answer is not automatically good. A model may change from correct to incorrect or from one incorrect label to another. Read this metric together with update precision and final accuracy.

### 9.2 Update-precision files

The relevant files are `update_precision_comparison.csv` and `update_precision_by_model_condition.csv`.

Update precision asks:

> Among cases where the model changed its answer, what proportion of the new answers match gold?

It measures the quality of changes, not their frequency. A model can have low `used_target` and high update precision, or change frequently but imprecisely.

Do not compare update precision directly with ordinary accuracy without identifying their different denominators:

- accuracy: all scored main-experiment items in the relevant cell;
- update precision: changed, both-answered pairs only.

### 9.3 `prior_correction_by_model_condition.csv`

This table divides each model/condition cell into:

- `prior_correct`: the ablation answer already equals gold;
- `prior_incorrect`: the ablation answer does not equal gold.

For each group, it reports `n_items` and main-experiment `accuracy`.

The `prior_incorrect` group provides the clearest evidence of correction after seeing the target sentence. In the `prior_correct` group, a correct final answer is compatible with both genuine reading and retention of a fortunate default; the design cannot distinguish them.

Two representative positive cases are:

- DeepSeek R1 / +吧: all 9 initially incorrect priors are corrected;
- Mistral / +吗: all 10 initially incorrect priors are corrected.

By contrast, several perfect cells contain only two comparable items requiring correction because most priors already match gold.

## 10. `confusion_matrices/`

The folder contains raw-count matrices (`_counts.csv`) and row-normalized matrices (`_rownorm.csv`) for each model. Rows and columns follow a fixed order:

```text
ASSERT, TENTATIVE, NEUTRAL, DISTRACTOR
```

Rows are empirical gold labels; columns are model responses. In a row-normalized matrix, each row shows how items with one gold role are distributed across predicted roles.

### Reading the +吗 pattern

The NEUTRAL row corresponds to confirmatory +吗 items. For every model that makes a +吗 error, all error mass falls in the TENTATIVE column:

| Model | NEUTRAL | TENTATIVE | ASSERT | DISTRACTOR |
|---|---:|---:|---:|---:|
| Gemma | 35% | 65% | 0% | 0% |
| Qwen | 45% | 55% | 0% | 0% |
| Gemini | 55% | 45% | 0% | 0% |
| DeepSeek R1 | 75% | 25% | 0% | 0% |
| DeepSeek V3 | 100% | 0% | 0% | 0% |
| Mistral | 100% | 0% | 0% | 0% |

For the four affected models, 100% of +吗 **errors** are TENTATIVE. The TENTATIVE percentages in the table are shares of all 20 +吗 items, so they equal the error rates only because ASSERT and DISTRACTOR are zero.

## 11. `design_gold_following/`

This analysis uses four exploratory items where the empirical gold moves away from the design-intended NEUTRAL label toward TENTATIVE.

It asks whether each model follows:

- the empirical, context-driven human label; or
- the original design label associated with the canonical +吗 function.

| Model group | Design label selected |
|---|---:|
| DeepSeek R1 / DeepSeek V3 | 4 of 4 |
| Gemini / Mistral | 3 of 4 |
| Gemma / Qwen | 2 of 4 |

This is the most direct context-versus-canonical comparison, but `n=4` is too small for a stable rate estimate. Report counts alongside percentages and describe the result as qualitative.

## 12. Distractor and the reference level

No model selects DISTRACTOR in the main experiment. The active response competition is therefore among ASSERT, TENTATIVE, and NEUTRAL.

A three-label 33% reference is descriptively more informative than the nominal 25% implied by four displayed options. It is not a formal chance model and should not be presented as proof that any score above 33% is statistically significant.

Gemma's 35% +吗 result illustrates why error structure matters. Its answers are 35% NEUTRAL, 65% TENTATIVE, and 0% ASSERT. The accuracy is close to the three-label reference, but the pattern is highly directional rather than random.

## 13. Parse failures and refusals

Raw result rows include `parsed_choice_letter`, `parsed_choice_semantic`, and `parse_failed`.

- A valid A–D response is mapped through the family-specific semantic map.
- A refusal or response with no parsable letter has empty parsed fields and `parse_failed = True`.
- An ablation parse failure removes that item from metrics requiring a paired before/after answer.

When reporting a metric, use the denominator written in the generated table. Do not silently convert missing paired observations into “unchanged” answers.

Gemma's context-only refusals are especially relevant: only 7 of 20 +吧 items have comparable ablation responses. Claims about its prior should therefore rely more heavily on its main-experiment confusion pattern than on the reduced paired sample.

## 14. Figure guide

All figures are under [`../results/figures/`](../results/figures/) and are supplied as 300-dpi PNG plus vector PDF. They omit in-image titles so that reports and posters can provide their own captions.

| Figure | What it shows | Main use |
|---|---|---|
| `fig1_condition_accuracy` | model accuracy by condition with human-reference bands | headline performance comparison |
| `fig2_confusion_grid` | six row-normalized confusion matrices | error direction and defaults |
| `fig3_ba_vs_ma_scatter` | +吧 versus +吗 accuracy with human references | condition trade-offs across models |
| `fig4_used_target_by_condition` | answer-change frequency after restoring the target | ablation/main comparison |
| `fig5_design_gold_following` | the four exploratory design-gold items | qualitative context/canonical pattern |

Always caption Figure 5 with `n=4`. For Figure 4, retain or report the displayed denominators because paired sample sizes vary by model.

## 15. Primary CSV schemas

### 15.1 Frozen item files

Files:

- `../intermediate_outputs/frozen_dataset/frozen_dataset.csv`;
- `../intermediate_outputs/frozen_dataset/frozen_exploratory.csv`.

| Column | Meaning |
|---|---|
| `family_id` | family identifier such as `F01` |
| `item_id` | unique family/condition identifier such as `F01_ba` |
| `condition` | `bare`, `ba`, or `ma` |
| `context_text` | shared discourse context |
| `target_sentence` | condition-specific target utterance |
| `option_A` … `option_D` | answer text in displayed order |
| `option_semantic_map` | maps each letter to a semantic role |
| `gold_semantic` | core3 empirical majority role |
| `gold_letter` | letter carrying the empirical gold role |
| `design_gold_semantic` | originally intended semantic role |
| `gold_shifted` | whether empirical and design gold differ |
| `margin` | core3 vote support: 3, 2, or 1 |
| `stable_keep_all_pools` | whether the family remains KEEP under all four pools |
| `collapse_pair` | exploratory only: conditions sharing one label |
| `collapse_label` | exploratory only: their shared label |

### 15.2 Main experiment results

File: `../intermediate_outputs/main_experiment/main_results.csv`.

| Column | Meaning |
|---|---|
| `set` | confirmatory or exploratory |
| `family_id`, `item_id`, `condition` | item identifiers |
| `model` | configured model name |
| `raw_response` | complete model reply |
| `parsed_choice_letter` | parsed A–D response |
| `parsed_choice_semantic` | semantic role after applying the option map |
| `gold_letter`, `gold_semantic` | frozen empirical gold |
| `hit_gold` | whether the parsed role equals gold |
| `parse_failed` | whether no valid letter was parsed |
| `timestamp` | time the main-experiment call returned |

The analyzed ablation CSV uses the same core fields but does not include the main-experiment timestamp.

### 15.3 Prior-correction output

File: `../results/main_scoring/target_sentence_delta/prior_correction_by_model_condition.csv`.

| Column | Meaning |
|---|---|
| `set` | confirmatory or exploratory |
| `model` | model name |
| `condition` | bare, ba, or ma |
| `group` | `prior_correct` or `prior_incorrect` |
| `n_items` | rows with both an ablation and main answer |
| `accuracy` | main-experiment accuracy within that group |

`accuracy` is blank when `n_items = 0`.


