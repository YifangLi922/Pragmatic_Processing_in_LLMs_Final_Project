# SFP-ba: Reproduction Pipeline and Output Reference

This document contains the detailed environment setup, repository layout, pipeline order, full commands, inputs and outputs, metric definitions, result-folder guidance, CSV schemas, testing, and reproducibility notes.

## 1. Requirements and setup

Run all commands from the repository root.

```bash
pip install -r requirements.txt
cp .env.example .env
```

Add an OpenRouter API key to `.env` before running either model-query stage:

```text
OPENROUTER_API_KEY=...
```

The project uses Python plus `PyYAML`, `python-dotenv`, `requests`, `openpyxl`, `matplotlib`, `numpy`, and `pytest`. No GPU is required. External model access is needed only for:

- `src.ablation.query`;
- `src.main_experiment.query`.

All other stages operate on local files. Both query stages are resumable and budget-capped.

## 2. Repository layout

```text
item_design/
  item_design_framework_zh.md
  item_design_framework_en.md
  SFP pilot families.docx
  SFP expanded families.docx
  pilot/
    SFP_pilot_annotation_form.xlsx
    SFP_pilot_annotation_result.xlsx

raw_xlsx_data/
  original_data_with_answers/
    SFP_master_answer_key.xlsx
  native_speaker_annotations/
    SFP_annotator1_Econ.xlsx
    SFP_annotator2_Media.xlsx
    SFP_annotator3_Materials.xlsx
    SFP_annotator4_BWL.xlsx
    SFP_annotator5_EngLit.xlsx

data/
  reconstructed_5ann.json
  reconstructed.json
  quality_report_5ann.json
  quality_report.json
  ablation_raw.jsonl
  fake_items.json
  fake_annotations.json

intermediate_outputs/
  diagnostic/
  pool_sensitivity/
  frozen_dataset/
    frozen_dataset.csv
    frozen_exploratory.csv
    freeze_report.md
  ablation/
  main_experiment/
    main_results.csv

results/
  main_scoring/
    main_scoring_summary.md
    condition_accuracy/
    margin_stratified_accuracy/
    target_sentence_delta/
    confusion_matrices/
    design_gold_following/
  human_baseline_core3/
  figures/
    fig1_condition_accuracy/
    fig2_confusion_grid/
    fig3_ba_vs_ma_scatter/
    fig4_used_target_by_condition/
    fig5_design_gold_following/

config/
  models.yaml
.env.example
src/
tests/
docs/
```

### Source and derived data

- `raw_xlsx_data/` contains the collected spreadsheets and master answer key. Treat these as source records.
- `data/reconstructed_5ann.json` is the canonical machine-readable reconstruction used downstream.
- `intermediate_outputs/` contains stage-to-stage artifacts rather than headline results.
- `results/` contains final tables, summaries, human baselines, and figures.
- `data/reconstructed.json` and `data/quality_report.json` belong to an earlier four-annotator validation pass and do not produce the reported results.
- `data/fake_items.json` and `data/fake_annotations.json` are synthetic fixtures used only by tests.

## 3. Pipeline overview

Run the stages in this order:

```text
raw answer key + annotation spreadsheets
                ↓
       reconstruction and QC
                ↓
       annotator diagnostics
                ↓
    annotator-pool sensitivity
                ↓
  confirmatory/exploratory freeze
          ↙             ↘
 context-only          main experiment
   ablation          with target sentence
          ↘             ↙
             main scoring
                 ↓
        human baseline + figures
```

Every stage has a `python -m src.<package>` entry point. Paths are supplied explicitly rather than hardcoded to a particular machine.

## 4. Stage 1 — Reconstruction

Package: `src.reconstruct`

This stage joins the master answer-key spreadsheet with each annotator's raw answer sheet. It produces one machine-readable record per item and converts the displayed A/B/C/D answer into its semantic role: statement, confirmation, neutral, or distractor.

```bash
python -m src.reconstruct \
    --master "raw_xlsx_data/original_data_with_answers/SFP_master_answer_key.xlsx" \
    --annotator Econ="raw_xlsx_data/native_speaker_annotations/SFP_annotator1_Econ.xlsx" \
    --annotator Media="raw_xlsx_data/native_speaker_annotations/SFP_annotator2_Media.xlsx" \
    --annotator Materials="raw_xlsx_data/native_speaker_annotations/SFP_annotator3_Materials.xlsx" \
    --annotator BWL="raw_xlsx_data/native_speaker_annotations/SFP_annotator4_BWL.xlsx" \
    --annotator EngLit="raw_xlsx_data/native_speaker_annotations/SFP_annotator5_EngLit.xlsx" \
    --output data/reconstructed_5ann.json \
    --quality-output data/quality_report_5ann.json
```

### Inputs

- master item bank and design answer key;
- five completed annotation spreadsheets.

### Outputs

- `data/reconstructed_5ann.json` — 108 items × 5 annotators;
- `data/quality_report_5ann.json` — automated response-quality flags.

The quality report checks for:

- straight-lining: more than 70% of responses on one answer letter;
- unanswered items;
- zero variance in naturalness ratings;
- flat responding: zero hesitation, zero “no valid option,” and zero naturalness variance together;
- agreement with the design key that is a statistical outlier relative to the batch (`z > 2`).

These checks inform annotator assessment but do not by themselves create empirical gold labels.

## 5. Stage 2 — Annotator diagnostics

Package: `src.diagnostic`

This stage computes descriptive, condition-wise quality-control measures for each annotator, including agreement and coverage against a leave-one-out reference pool of the other annotators.

```bash
python -m src.diagnostic \
    --reconstructed data/reconstructed_5ann.json \
    --output-dir intermediate_outputs/diagnostic
```

### Output

The output directory contains per-annotator and per-condition diagnostic files. Start with:

[`../intermediate_outputs/diagnostic/Diagnostic_Output_README.md`](../intermediate_outputs/diagnostic/Diagnostic_Output_README.md)

The diagnostic supports the exclusion of Econ for a global confirmation-label response style and BWL for a pattern consistent with non-independent evaluation. The retained Media, Materials, and EngLit annotators form the `core3` pool.

## 6. Stage 3 — Annotator-pool sensitivity

Package: `src.pool_sensitivity`

For every family, this stage calculates empirical gold labels and classifies the family under four candidate annotator pools:

- core3;
- core3 + Econ;
- core3 + BWL;
- all five annotators.

```bash
python -m src.pool_sensitivity \
    --reconstructed data/reconstructed_5ann.json \
    --output-dir intermediate_outputs/pool_sensitivity
```

### Family classes

| Class | Definition | Core3 count | Downstream use |
|---|---|---:|---|
| `KEEP` | each condition has a clear majority and the three gold labels remain distinct | 20 | confirmatory |
| `COLLAPSE_structural` | two conditions share an empirical gold label, but the item is otherwise valid | 6 | exploratory |
| `NO_CONSENSUS` | at least one condition has no majority | 8 | excluded |
| `EXCLUDE_BROKEN` | at least one condition's majority is the distractor | 2 | excluded |

The pool grid makes family selection auditable. Eleven families remain KEEP under every candidate pool; the primary analysis uses the 20 core3 KEEP families.

## 7. Stage 4 — Dataset freeze

Package: `src.freeze`

This stage joins the core3 pool-sensitivity classification with item text and writes the two datasets that all later stages treat as read-only ground truth.

```bash
python -m src.freeze \
    --reconstructed data/reconstructed_5ann.json \
    --pool-sensitivity-dir intermediate_outputs/pool_sensitivity \
    --output-dir intermediate_outputs/frozen_dataset
```

### Outputs

- `frozen_dataset.csv` — 20 KEEP families × 3 conditions = 60 confirmatory items;
- `frozen_exploratory.csv` — 6 `COLLAPSE_structural` families × 3 = 18 exploratory items;
- `freeze_report.md` — complete provenance, pool grid, and gold-shift records.

The two item sets must be analyzed separately. Exploratory families contain a structural label collapse, so their raw accuracy is not comparable with confirmatory accuracy.

The commit that produced the frozen files is tagged `dataset-frozen-v1`.

## 8. Stage 5 — Context-only ablation

Packages:

- `src.ablation.query`;
- `src.ablation.analyze`.

The query removes the target sentence while leaving the context, question, and answer options unchanged. Within a family, the resulting three prompts are byte-for-byte identical. The ablation therefore measures a single context-conditioned default response per model and family, not three independent condition-specific leaks.

### 8.1 Query models

```bash
python -m src.ablation.query \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --frozen-exploratory intermediate_outputs/frozen_dataset/frozen_exploratory.csv \
    --reconstructed data/reconstructed_5ann.json \
    --output data/ablation_raw.jsonl
```

The query is resumable. Successful `(item, model)` responses are appended immediately, and rerunning the command requests only missing pairs.

### 8.2 Analyze the checkpoint

```bash
python -m src.ablation.analyze \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --frozen-exploratory intermediate_outputs/frozen_dataset/frozen_exploratory.csv \
    --reconstructed data/reconstructed_5ann.json \
    --raw data/ablation_raw.jsonl \
    --output-dir intermediate_outputs/ablation
```

### Interpretation

The ablation has two uses:

1. **Context shortcut check:** does the context alone force an answer?
2. **Prior baseline:** after the target sentence is shown, does the model retain, change, or correct its initial response?

No context-only response defaults to ASSERT, yielding a 0% bare shortcut rate. A default that coincides with the TENTATIVE or NEUTRAL gold should not automatically be called a stimulus leak; it may instead reveal the model's preferred semantic label.

## 9. Stage 6 — Main experiment

Package: `src.main_experiment.query`

This is the main model-facing trial. It presents the 60 confirmatory and 18 exploratory items with their target sentences included.

```bash
python -m src.main_experiment.query \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --frozen-exploratory intermediate_outputs/frozen_dataset/frozen_exploratory.csv \
    --reconstructed data/reconstructed_5ann.json \
    --output-dir intermediate_outputs/main_experiment
```

The resulting `main_results.csv` contains one row per `(item, model)` trial, including the raw response, parsed answer, semantic label, gold match, parse status, and timestamp.

Like the ablation query, this stage is resumable and writes successful responses incrementally.

## 10. Stage 7 — Main scoring

Package: `src.main_scoring`

This stage combines the main results, context-only ablation, and frozen gold files.

```bash
python -m src.main_scoring \
    --main-results intermediate_outputs/main_experiment/main_results.csv \
    --ablation-results intermediate_outputs/ablation/ablation_results.csv \
    --ablation-item-summary intermediate_outputs/ablation/ablation_item_summary.csv \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --frozen-exploratory intermediate_outputs/frozen_dataset/frozen_exploratory.csv \
    --output-dir results/main_scoring
```

### Output groups

- `condition_accuracy/` — accuracy by model and condition, with confirmatory and exploratory sets reported separately;
- `margin_stratified_accuracy/` — confirmatory accuracy by core3 vote margin;
- `target_sentence_delta/` — changes between ablation and full-prompt responses;
- `confusion_matrices/` — raw and row-normalized gold/response matrices;
- `design_gold_following/` — behavior on exploratory items where empirical gold differs from the design label;
- `main_scoring_summary.md` — narrated guide to the final tables.

Start with [`../results/main_scoring/main_scoring_summary.md`](../results/main_scoring/main_scoring_summary.md).

## 11. Stage 8 — Human baseline

Package: `src.human_baseline_core3`

This stage computes human performance on the same 60 confirmatory items using the core3 annotators.

```bash
python -m src.human_baseline_core3 \
    --reconstructed data/reconstructed_5ann.json \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --output-dir results/human_baseline_core3
```

### Human metrics

- **Leave-one-out (LOO):** hold out one annotator, build temporary gold from the other two, and score the held-out response. On a 2:1 split, the minority response is necessarily counted as wrong, so LOO is a lower bound.
- **Concordance:** calculate the proportion of all core3 responses matching the final empirical gold, then average within condition. This answers the same form of question as model accuracy and is the primary human/model comparison.

See [`../results/human_baseline_core3/human_baseline_comparison.md`](../results/human_baseline_core3/human_baseline_comparison.md) for the detailed comparison.

## 12. Stage 9 — Figures

Package: `src.results_viz`

```bash
python -m src.results_viz \
    --main-scoring-dir results/main_scoring \
    --human-baseline-dir results/human_baseline_core3 \
    --output-dir results/figures
```

Every figure is written as a 300-dpi PNG and a vector PDF. Figures contain no in-image title so that captions can be supplied externally. Model order and condition colors are consistent.

| Figure directory | Content |
|---|---|
| `fig1_condition_accuracy/` | grouped accuracy by model and condition with human-reference bands |
| `fig2_confusion_grid/` | 2 × 3 model confusion-matrix grid with a shared color scale |
| `fig3_ba_vs_ma_scatter/` | +吧 versus +吗 accuracy, equality line, and human concordance references |
| `fig4_used_target_by_condition/` | rate of answer change after the target sentence, with denominators |
| `fig5_design_gold_following/` | qualitative `n=4` design-gold-following comparison |

## 13. Tests

```bash
python -m pytest tests/ -v
```

All 183 tests use synthetic fixtures. They require no real annotation spreadsheets, network connection, or API key. The `tests/` hierarchy mirrors `src/` by package. `tests/reconstruct/` imports `openpyxl` through the module under test, so dependencies must be installed first.

### Offline query-engine smoke test

```bash
python -m src.llm_query \
    --items data/fake_items.json \
    --output /tmp/fake_mock_results.jsonl \
    --mock
```

This runs five synthetic items through deterministic mock responses and does not use an API key.

## 14. How to interpret the scoring outputs

### 14.1 Confirmatory versus exploratory

Never combine or directly compare their raw accuracy:

- **confirmatory:** three distinct empirical gold labels per family;
- **exploratory:** two conditions share an empirical gold label by construction.

Exploratory accuracy can be structurally inflated because one response can be correct for two conditions. Use this set for qualitative analysis only.

### 14.2 Margin-stratified accuracy

The margin records core3 support for an item's gold:

- `3`: unanimous 3:0;
- `2`: 2:0 with one abstention;
- `1`: 2:1 majority.

In this dataset, model accuracy remains approximately 80–82% across these margins. The result is retained for completeness but is not a central explanatory axis.

### 14.3 Target-sentence delta metrics

`used_target_by_model[_condition].csv` measures whether the model changed its answer between the context-only and full-prompt run. Its denominator includes only pairs with both answers. An ablation refusal is excluded rather than counted as “did not use the target.”

`update_precision_comparison.csv` and `update_precision_by_model_condition.csv` ask: among cases where the model changed its answer, how often was the new answer correct? Update precision complements raw accuracy; it does not replace it.

`prior_correction_by_model_condition.csv` divides each model/condition cell into:

- `prior_correct`: the context-only answer already equals gold;
- `prior_incorrect`: the context-only answer differs from gold.

Accuracy in the `prior_incorrect` group is the clearest measure of whether the target sentence corrected a wrong prior. For `prior_correct`, the design cannot determine whether the model actively read the target or retained a fortunate default.

### 14.4 Confusion matrices

Raw-count files end in `_counts.csv`; row-normalized files end in `_rownorm.csv`. Rows and columns use a fixed order:

```text
ASSERT, TENTATIVE, NEUTRAL, DISTRACTOR
```

The NEUTRAL row is central to the +吗 analysis. Every observed +吗 error moves to TENTATIVE rather than ASSERT or DISTRACTOR.

### 14.5 Design-gold following

The exploratory set contains four items whose empirical gold differs from their original design label. `design_gold_following/` records whether models follow the original design label rather than the human empirical gold. Because there are only four items, treat percentages as a qualitative pattern.

## 15. CSV column reference

### 15.1 Frozen datasets

Files:

- `intermediate_outputs/frozen_dataset/frozen_dataset.csv`;
- `intermediate_outputs/frozen_dataset/frozen_exploratory.csv`.

| Column | Meaning |
|---|---|
| `family_id` | family identifier, such as `F01` |
| `item_id` | unique `<family>_<condition>` identifier, such as `F01_ba` |
| `condition` | `bare`, `ba`, or `ma` |
| `context_text` | shared situational context |
| `target_sentence` | target utterance; the only text field that differs within a family |
| `option_A` … `option_D` | displayed answer options, with one shared order per family |
| `option_semantic_map` | maps letters to semantic roles |
| `gold_semantic` | core3 empirical majority role |
| `gold_letter` | answer letter carrying the empirical gold role |
| `design_gold_semantic` | intended role: bare→statement, ba→confirmation, ma→neutral |
| `gold_shifted` | whether empirical and design gold differ |
| `margin` | core3 vote margin: `3`, `2`, or `1` |
| `stable_keep_all_pools` | whether the family remains KEEP under all four pools |
| `collapse_pair` | exploratory only: the conditions sharing a gold label |
| `collapse_label` | exploratory only: the shared label |

`gold_shifted` is always false in the confirmatory set. The four shifts appear in the exploratory set.

### 15.2 Main and ablation results

Primary file: `intermediate_outputs/main_experiment/main_results.csv`. The ablation result uses the same core schema, without the main-run timestamp.

| Column | Meaning |
|---|---|
| `set` | `confirmatory` or `exploratory` |
| `family_id`, `item_id`, `condition` | item identifiers |
| `model` | configured model name |
| `raw_response` | complete model reply |
| `parsed_choice_letter` | parsed A–D choice; empty on refusal or parse failure |
| `parsed_choice_semantic` | semantic role obtained from the option map |
| `gold_letter`, `gold_semantic` | frozen empirical gold |
| `hit_gold` | whether the parsed semantic response equals gold |
| `parse_failed` | whether no valid answer letter could be parsed |
| `timestamp` | main run only: time the call returned |

### 15.3 Prior-correction table

File: `results/main_scoring/target_sentence_delta/prior_correction_by_model_condition.csv`.

| Column | Meaning |
|---|---|
| `set` | confirmatory or exploratory |
| `model` | model name |
| `condition` | bare, ba, or ma |
| `group` | `prior_correct` or `prior_incorrect` |
| `n_items` | number of items having both an ablation and main answer |
| `accuracy` | full-prompt accuracy within the group; blank when `n_items = 0` |

Ablation refusals reduce `n_items`; they are not treated as ordinary wrong priors.

## 16. Model configuration, cost, and reproducibility

The model roster, exact OpenRouter identifiers, per-model notes, and prices used by the project are stored in [`../config/models.yaml`](../config/models.yaml). Change the model roster there rather than editing code.

The recorded roster contains three models selected for strong Chinese-language capability—DeepSeek V3, DeepSeek R1 0528, and Qwen3 Next 80B—and three general-purpose models—Gemma 4 31B, Mistral Small 3 24B, and Gemini 3 Flash Preview.

Both query stages append each successful result immediately and skip completed `(item, model)` pairs on rerun. This limits data loss and prevents completed calls from being paid for twice after interruption.

The configuration includes a cost guard at `cost_guard.max_cost_usd`, set to `$3` in the recorded project configuration. Before each paid request, the runner estimates whether the next call would exceed the limit and stops if necessary. The original full-pass estimate was below `$1`, but provider pricing can change; inspect the current configuration before rerunning.

All models were run at `temperature=0` on the same paid serving tier. This reduces one source of variation but does not guarantee deterministic responses. Item F12 returned different answers to an identical prompt on separate calls.

## 17. Shared LLM-query infrastructure

`src.llm_query` provides the common infrastructure used by both live query stages:

- prompt construction;
- answer parsing;
- deterministic mock provider;
- OpenRouter client;
- retry and backoff;
- resumable execution;
- per-call cost checks.

The standalone mock command in the testing section is the safest way to verify this layer before using the API.
