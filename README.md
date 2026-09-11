# SFP-ba: Sentence-Final Particle Sensitivity in Large Language Models

This project tests whether large language models interpret the pragmatic meaning of Mandarin sentence-final particles in context in ways that align with native-speaker judgments. It focuses on the confirmation-seeking use of **吧 (ba)**; particle-less declaratives and **吗 (ma)** questions provide two controlled contrasts.

A sentence-final particle does not substantially change the proposition `P`, but it can change the speaker's stance toward that proposition:

| Form | Approximate English gloss | Expected speaker stance |
|---|---|---|
| `P` (bare) | “P.” | a relatively confident **assertion** |
| `P` + **吧 (ba)** | “P, right?” | a **tentative, confirmation-seeking** statement |
| `P` + **吗 (ma)** | “Is P the case?” | a **neutral yes/no question** with no stated leaning |

The experiment uses minimal triplets: within each item family, the context, proposition, question, and answer choices remain constant, while only the sentence-final form changes. This makes it possible to ask whether a model responds to the particle contrast rather than to unrelated differences between items.

The repository contains the item-design materials, native-speaker annotations, model-querying code, frozen datasets, scoring pipeline, and final tables and figures. It is written for readers who do not need prior knowledge of Mandarin linguistics.

## TL;DR

> ****The results suggest that models generally follow a particle's canonical interpretation, while native speakers are more likely to adjust their interpretation to the local context. When the two agree, models perform well; when they conflict, models often fail to make the same contextual shift as native speakers.**

The clearest confirmatory pattern is directional: whenever a model misinterprets a +吗 item, it selects the **TENTATIVE** interpretation associated with +吧, never **ASSERT** or the distractor. Native speakers show the same direction of collapse in the exploratory data. At the same time, humans and models find different conditions difficult: human agreement is lowest on +吧, while model performance is generally weakest on +吗.

These conclusions should be read with two qualifications. The most direct context-versus-canonical comparison contains only four exploratory items, so it is qualitative. In addition, each condition has one fixed intended label, which allows a model-specific default answer to produce a high score without necessarily demonstrating particle-sensitive interpretation.

## Research questions

The project addresses three questions:

1. **Interpretation accuracy:** Can LLMs recover the human-validated speaker stance associated with bare, +吧, and +吗 forms in controlled Mandarin contexts?
2. **Contrastive sensitivity:** Holding the proposition and context constant, does changing only the sentence-final form systematically shift model interpretations in the direction supported by native-speaker judgments?
3. **Model variation:** How do these interpretation patterns differ across model families?

The second question is the central one because the experimental manipulation occurs within families: the context and propositional content remain constant while only the sentence-final form changes. In the final analysis, contrastive sensitivity is assessed through the pattern of accuracy across the three conditions, the direction of model confusions, and the context-only ablation, which tests whether seeing the target sentence changes a model's answer relative to its context-conditioned prior.

The original hypotheses predicted that +吧 would be the hardest condition for models and that +吧 errors would collapse toward the neutral +吗 interpretation. Neither prediction was supported: +吗 was generally more difficult, and its errors moved toward the +吧-like TENTATIVE reading instead.

## Experimental design

Each family contains one shared discourse context, one target proposition `P`, and one four-option interpretation question. The target sentence appears in three forms:

- bare `P`;
- `P` + 吧;
- `P` + 吗.

The four answer options represent the same semantic roles throughout the project:

- **ASSERT:** the speaker presents `P` as a statement;
- **TENTATIVE:** the speaker leans toward `P` but seeks confirmation;
- **NEUTRAL:** the speaker asks whether `P` is true without expressing a leaning;
- **DISTRACTOR:** an intentionally irrelevant interpretation.

### Example family

**Context:** Zhou and Lin are attending a workplace training session. A staff member has just reminded everyone to sign in. After that person leaves, Zhou speaks to Lin.

- **bare:** 刚才那位是这里的负责人 — “That person just now is the one in charge here.”
- **+吧:** 刚才那位是这里的负责人**吧** — “That person just now is the one in charge here, right?”
- **+吗:** 刚才那位是这里的负责人**吗** — “Is that person the one in charge here?”

**Question:** Which attitude is Zhou most likely expressing?

A. Zhou is asking Lin to find that person. *(DISTRACTOR)*  
B. Zhou is asking whether the person is in charge, with no clear leaning. *(NEUTRAL)*  
C. Zhou is fairly confident that the person is in charge and is telling Lin. *(ASSERT)*  
D. Zhou thinks the person is probably in charge but wants Lin to confirm. *(TENTATIVE)*

By design, the expected answers are C for bare, D for +吧, and B for +吗. The option order is shuffled by family but held constant across its three conditions.

## Dataset and human validation

Items were drafted manually or developed from LLM-generated starting points, then reviewed and substantially revised by the author. The construction framework varied interaction setting and proposition type to avoid a narrow or repetitive sample, but these dimensions were writing heuristics rather than fully crossed experimental factors. The guiding priority was:

> **contrast quality > naturalness > diversity > exact numerical balance**

A pilot with 10 families and one native Mandarin speaker was used only to revise the materials. The final candidate set contained **36 families (108 items)**. Five native Mandarin speakers then completed the main annotation task.

Quality control was conducted before the model-facing analysis. Two annotators were excluded: one showed a strong global preference for the confirmation label, and another produced a response pattern consistent with non-independent evaluation, including identical naturalness ratings across all items. The remaining three annotators, referred to as **core3**, did not know one another and reached approximately 72% pairwise agreement across four answer options. Their majority judgments define the primary empirical gold labels.

Under the core3 pool, the 36 families were classified as follows:

| Classification | Families | Use in this project |
|---|---:|---|
| **KEEP** | 20 | confirmatory set: 60 items with distinct gold labels across all three conditions |
| **COLLAPSE_structural** | 6 | exploratory set: 18 items where two conditions share an empirical gold label |
| **NO_CONSENSUS** | 8 | excluded because at least one condition lacks a majority |
| **EXCLUDE_BROKEN** | 2 | excluded because at least one condition's majority selects the distractor |

The **confirmatory set** is the primary basis for accuracy comparisons. The **exploratory set** is reported separately because its collapsed labels make its accuracy structurally different and unsuitable for direct comparison with confirmatory accuracy. The sensitivity analysis also evaluates four candidate annotator pools; 11 families remain KEEP under every pool, while the main analysis uses the 20 core3 KEEP families.

## Models and evaluation

Six models were queried through OpenRouter's OpenAI-compatible API at `temperature=0`:

- DeepSeek R1 0528;
- DeepSeek V3;
- Gemini 3 Flash Preview;
- Gemma 4 31B;
- Mistral Small 3 24B;
- Qwen3 Next 80B.

The exact provider identifiers and configuration are stored in [`config/models.yaml`](config/models.yaml). Cross-model differences are descriptive rather than causal because the models differ in architecture, scale, training data, tokenization, instruction tuning, and post-training.

The main experiment presents all 78 frozen items with the target sentence included. A context-only ablation removes the target sentence while preserving the context, question, and options. Because the three conditions in a family then become identical, the ablation measures one context-conditioned **default answer**, or prior, per family. Comparing that prior with the full-prompt answer helps distinguish an already-correct default from a correction made after the model sees the target sentence.

## Main results

### Model accuracy

The primary accuracy table covers the 60 confirmatory items: 20 families × 3 conditions.

| Model | Overall | bare | +吧 | +吗 |
|---|---:|---:|---:|---:|
| deepseek-r1-0528 | 90.0% | 95% | 100% | 75% |
| deepseek-v3 | 80.0% | 100% | **40%** | 100% |
| gemini-3-flash-preview | 81.7% | 90% | 100% | 55% |
| gemma-4-31b | 78.3% | 100% | 100% | **35%** |
| mistral-small-3-24b | 91.7% | 85% | 90% | 100% |
| qwen3-next-80b | 70.0% | 100% | 65% | 45% |

Overall accuracy ranges from 70.0% to 91.7%, while condition-level accuracy ranges from 35% to 100%. The task therefore differentiates models and conditions without producing a uniform ceiling or floor.

### Human baseline

| Condition | Leave-one-out baseline | Concordance with gold |
|---|---:|---:|
| bare | 98.3% | 98.3% |
| +吧 | 66.6% | 78.3% |
| +吗 | 83.9% | 86.7% |

**Concordance** is the most direct comparison with model accuracy: it is the proportion of core3 judgments matching the final gold label. The leave-one-out measure is a lower bound because, on a 2:1 split, the minority annotator is necessarily scored as incorrect against the other two.

The most important contrast is not simply that one condition is harder than another. **Native speakers agree least on +吧, whereas models tend to perform worst on +吗.** This mismatch suggests that the main source of model difficulty is not identical to the ambiguity experienced by human readers.

## Key findings

### 1. Models favor the canonical label when context supports a different human reading

Four exploratory +吗 items have an empirical human gold label that shifts from the design-intended NEUTRAL reading to TENTATIVE in context. On these items, DeepSeek R1 and DeepSeek V3 select the original design label on all four items; Gemini and Mistral do so on three; Gemma and Qwen do so on two.

This is the most direct evidence that the models favor the canonical particle function over a context-driven human interpretation. Because the comparison contains only four items, it should be treated as a qualitative pattern rather than a stable quantitative estimate.

### 2. +吗 errors move systematically toward the +吧 interpretation

In the confirmatory set, every +吗 error made by every model is a TENTATIVE response—the interpretation associated with +吧. No +吗 error is an ASSERT or DISTRACTOR response. Among the models that make +吗 errors, the NEUTRAL/TENTATIVE split is:

- Gemma: 35% / 65%;
- Qwen: 45% / 55%;
- Gemini: 55% / 45%;
- DeepSeek R1: 75% / 25%.

DeepSeek V3 and Mistral make no +吗 errors. This direction reverses the original hypothesis: rather than +吧 collapsing toward +吗, +吗 is assimilated toward the +吧-like reading. The human exploratory data show the same direction—all six structurally collapsed families and all four gold-shifted items move from neutral toward confirmation-seeking, never in the reverse direction.

### 3. Model-specific default labels shape both strong and weak scores

The confusion matrices and context-only ablation indicate that some models gravitate toward a preferred label:

- **Gemma favors TENTATIVE**, scoring 100% on +吧 but 35% on +吗. It returns TENTATIVE on all 20 +吧 items and on 13 of 20 +吗 items.
- **DeepSeek V3 favors NEUTRAL**, producing the mirror pattern: 100% on +吗 but 40% on +吧.
- **Mistral shows no comparably strong default**, with more balanced scores of 85%, 90%, and 100% across bare, +吧, and +吗.

These defaults do not by themselves establish whether a model understands a particle. They explain why a fixed label preference can help on one condition and hurt on another.

### 4. Identical 100% scores can reflect different behavior

The ablation separates cases where the model's context-only prior was already correct from cases where the target sentence corrected an initially wrong answer. For example, Gemini's 100% +吧 score includes only two comparable items requiring correction, whereas DeepSeek R1 correctly updates all nine +吧 items with an initially wrong prior. Similarly, DeepSeek V3's 100% +吗 score includes two genuine correction cases, while Mistral correctly updates all ten +吗 items with an initially wrong prior.

High accuracy therefore does not always imply the same degree of particle-sensitive updating. At the same time, the DeepSeek R1 and Mistral results show that successful correction after seeing the target sentence does occur.

### 5. The distractor is never selected

No model selects the DISTRACTOR on any main-experiment item. The substantive competition is therefore among ASSERT, TENTATIVE, and NEUTRAL. A three-way **33% reference level** is more informative than a nominal four-option 25% baseline for interpreting these results.

This also clarifies Gemma's 35% +吗 accuracy. Although the score is close to 33%, its response pattern is not random: 65% of its answers are TENTATIVE and none are ASSERT. The near-reference accuracy results from a directional label preference rather than an even distribution across the three live alternatives.

For the complete narrated analysis and all supporting tables, start with [`results/main_scoring/main_scoring_summary.md`](results/main_scoring/main_scoring_summary.md).

## Limitations and future work

- **Fixed condition-to-label mapping.** In the confirmatory set, bare always maps to ASSERT, +吧 to TENTATIVE, and +吗 to NEUTRAL. A model can therefore score well on a condition by favoring its associated label. Future work should vary the correct interpretation within each surface condition so that a default-label strategy cannot mimic competence.
- **Small annotator pool.** Five annotators were recruited, and the primary gold uses three after quality-control exclusions. A larger independent pool would reduce the influence of individual response styles and permit more stable estimates of disagreement.
- **Text-only presentation.** Without intonation or an interactive exchange, +吧 is particularly difficult for native speakers to judge consistently. Its 78.3% concordance is substantially below the 98.3% bare result.
- **Exploratory evidence is limited.** The direct context-versus-canonical comparison rests on four gold-shifted items. It supports the main interpretation but does not justify broad statistical generalization on its own.
- **Residual API non-determinism.** Temperature 0 does not guarantee identical outputs across calls; one item produced two different responses to the same prompt in separate runs.

## Repository structure

```text
item_design/              item-construction framework and pilot materials
raw_xlsx_data/            original answer key and annotation spreadsheets
data/                     reconstructed annotations and raw model responses
intermediate_outputs/     QC, dataset-freeze, ablation, and query artifacts
results/                  final scoring tables, human baselines, and figures
src/                      reconstruction, querying, scoring, and visualization code
tests/                    unit tests using synthetic fixtures
docs/                     project plan, analysis narrative, and earlier documentation
config/                   model roster and runtime configuration
```

Useful entry points:

- [`results/main_scoring/main_scoring_summary.md`](results/main_scoring/main_scoring_summary.md) — complete narrated results;
- [`results/human_baseline_core3/`](results/human_baseline_core3/) — human leave-one-out and concordance baselines;
- [`results/figures/`](results/figures/) — five poster-ready figures in PNG and PDF;
- [`intermediate_outputs/frozen_dataset/freeze_report.md`](intermediate_outputs/frozen_dataset/freeze_report.md) — dataset provenance and family selection;
- [`item_design/item_design_framework_en.md`](item_design/item_design_framework_en.md) — condensed English item-design framework;
- [`docs/dataset and annotation.md`](docs/dataset_and_annotation.md) — item construction, annotator recruitment, quality control, gold-label formation, and dataset freezing;
- [`docs/pipeline.md`](docs/pipeline.md) — full commands, inputs, outputs, testing procedures, cost controls, and reproducibility notes;
- [`docs/results_guide.md`](docs/results_guide.md) — result-directory map, metric definitions, denominators, CSV schemas, and reporting guidance.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env  # add OPENROUTER_API_KEY before running model queries
python -m pytest tests/ -v
```

The analysis pipeline proceeds in this order:

```text
raw annotations
→ reconstruction and annotator QC
→ annotator-pool sensitivity analysis
→ confirmatory/exploratory dataset freeze
→ context-only ablation
→ main model experiment
→ scoring, human baseline, and figures
```

All 183 tests use synthetic fixtures; they require no API key or network access. The two model-querying stages are resumable and append successful responses to checkpoints. A configurable cost guard in `config/models.yaml` stops further paid calls when the estimated running total reaches its limit.

This root README intentionally presents only the quickest entry points. Each pipeline package exposes its own command-line interface, while the generated reports under `intermediate_outputs/` and `results/` preserve the detailed provenance and metric outputs.
