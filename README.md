# SFP-ba: Sentence-Final Particle Sensitivity in Large Language Models

This project tests whether large language models interpret the speaker stance conveyed by Mandarin sentence-final particles in context in line with native-speaker judgments. It focuses on the confirmation-seeking use of **吧 (ba)**, using bare declaratives and **吗 (ma)** questions as two controlled comparison conditions.

A sentence-final particle does not substantially change the proposition `P`, but it can change the speaker's stance toward that proposition:

| Form | Approximate English gloss | Expected speaker stance |
|---|---|---|
| `P` (bare) | “P.” | a relatively confident **assertion** |
| `P` + **吧 (ba)** | “P, right?” | a **tentative, confirmation-seeking** statement |
| `P` + **吗 (ma)** | “Is P the case?” | a **neutral yes/no question** with no stated leaning |

The experiment uses minimal triplets: within each item family, the context, proposition, question, and answer choices remain constant, while only the sentence-final form changes. This makes it possible to ask whether a model responds to the particle contrast rather than to unrelated differences between items.

The repository contains the item-design materials, native-speaker annotations, model-querying code, frozen datasets, scoring pipeline, and final tables and figures. It is written for readers who do not need prior knowledge of Mandarin linguistics.

## TL;DR

> **The results suggest that models are sensitive to sentence-final form, but do not always adjust their interpretations to context in the same way native speakers do. When native-speaker judgments match a particle's usual interpretation, models often perform well; when context supports a different reading, models are more likely to stay with the particle's usual interpretation.**

The clearest pattern in the confirmatory set is the direction of +吗 errors: every incorrect +吗 response is **TENTATIVE**, which is the confirmation-seeking interpretation associated with +吧, but not **ASSERT** or DISTRACTOR. The exploratory human data show the same direction of shift. Humans and models also differ in which condition is hardest: native-speaker agreement is lowest on +吧, whereas model accuracy is generally lowest on +吗.

Two qualifications are important. First, the most direct comparison between context and the usual particle interpretation contains only four exploratory items, so it should be treated as qualitative evidence. Second, each condition has one fixed gold label in the confirmatory set, so a model can score well partly by favoring that label rather than by consistently using the sentence-final form.

## Research questions

The project addresses three questions:

1. **Interpretation accuracy:** Can LLMs identify the speaker stance that native speakers associate with bare, +吧, and +吗 forms?
2. **Sensitivity to sentence-final form:** When only the sentence-final form changes, do LLMs change their interpretation in line with native-speaker judgments?
3. **Model variation:** How do these interpretation patterns differ across model families?

The second question is the central one because the study changes only the sentence-final form within each family, while the context and proposition remain the same. This is evaluated by comparing performance across bare, +吧, and +吗, examining the kinds of errors models make, and using the context-only ablation to see whether the target sentence changes the answer a model would give from context alone.

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

Items were drafted manually or developed from LLM-generated starting points, then reviewed and substantially revised by the author. The construction framework varied interaction setting and proposition type to avoid a narrow or repetitive sample, but these dimensions were writing heuristics instead of fully crossed experimental factors. The guiding priority was:

> **contrast quality > naturalness > diversity > exact numerical balance**

A pilot with 10 families and one native Mandarin speaker was used only to revise the materials. The final candidate set contained **36 families (108 items)**. Five native Mandarin speakers then completed the main annotation task.

Quality control was conducted before the main experiment. Two annotators were excluded: one showed a strong overall preference for the confirmation label, while the other showed a highly uniform response pattern that raised concerns about independent item-by-item evaluation. For example, this annotator gave the same naturalness rating to every item. The remaining three annotators, referred to as **core3**, did not know one another and reached approximately 72% pairwise agreement across four answer options. Their majority judgments define the primary empirical gold labels.

Under the core3 pool, the 36 families were classified as follows:

| Classification | Families | Use in this project |
|---|---:|---|
| **KEEP** | 20 | confirmatory set: 60 items with distinct gold labels across all three conditions |
| **COLLAPSE_structural** | 6 | exploratory set: 18 items where two conditions share an empirical gold label |
| **NO_CONSENSUS** | 8 | excluded because at least one condition lacks a majority |
| **EXCLUDE_BROKEN** | 2 | excluded because at least one condition's majority selects the distractor |

The **confirmatory set** is the primary basis for accuracy comparisons. The **exploratory set** is reported separately because two conditions share the same gold label in these families. As a result, its accuracy is not directly comparable with accuracy on the confirmatory set. The sensitivity analysis also evaluates four candidate annotator pools. 11 families remain KEEP under every pool, while the main analysis uses the 20 core3 KEEP families.

## Models and evaluation

Six models were queried through OpenRouter's OpenAI-compatible API at `temperature=0`:

- DeepSeek R1 0528;
- DeepSeek V3;
- Gemini 3 Flash Preview;
- Gemma 4 31B;
- Mistral Small 3 24B;
- Qwen3 Next 80B.

The exact provider identifiers and configuration are stored in [`config/models.yaml`](config/models.yaml). Cross-model differences are descriptive because the models differ in architecture, scale, training data, tokenization, instruction tuning, and post-training.

The main experiment presents all 78 frozen items with the target sentence included. A context-only ablation removes the target sentence while preserving the context, question, and options. Because removing the target sentence makes the three conditions in a family identical, the ablation shows what answer each model gives based on the context alone. Comparing this context-only answer with the full-prompt answer shows whether the model was already correct before seeing the target sentence or changed to the correct answer after seeing it. 

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

Overall accuracy ranges from 70.0% to 91.7%, while condition-level accuracy ranges from 35% to 100%. The task differentiates models and conditions without producing a uniform ceiling or floor.

### Human baseline

| Condition | Leave-one-out baseline | Concordance with gold |
|---|---:|---:|
| bare | 98.3% | 98.3% |
| +吧 | 66.6% | 78.3% |
| +吗 | 83.9% | 86.7% |

**Concordance** is the most direct comparison with model accuracy: it is the proportion of core3 judgments matching the final gold label. The leave-one-out measure is a lower bound because, on a 2:1 split, the minority annotator is necessarily scored as incorrect against the other two.

The most important contrast is not simply that one condition is harder than another. **Native speakers agree least on +吧, whereas models tend to perform worst on +吗.** This mismatch suggests that models and native speakers are not struggling with the same aspects of the task.

## Key findings

### 1. Models may favor a particle's usual interpretation when context supports a different reading

Four exploratory +吗 items were originally designed with a NEUTRAL interpretation, but native-speaker judgments favored TENTATIVE in these specific contexts. On these four items, DeepSeek R1 and DeepSeek V3 chose the original NEUTRAL interpretation on all four; Gemini and Mistral did so on three; and Gemma and Qwen did so on two.

This pattern suggests that models may favor a particle's usual interpretation even when native speakers arrive at a different reading in context. These four items provide the most direct evidence for this tendency: native speakers shifted away from the usual +吗 interpretation, while models often did not make the same shift. Because the comparison contains only four items, this should be treated only as a qualitative evidence.

### 2. +吗 errors move systematically toward the +吧 interpretation

In the confirmatory set, every +吗 error made by every model is a TENTATIVE response, which is the interpretation associated with +吧. No +吗 error is an ASSERT or DISTRACTOR response. Among the models that make +吗 errors, the NEUTRAL/TENTATIVE split is:

- Gemma: 35% / 65%;
- Qwen: 45% / 55%;
- Gemini: 55% / 45%;
- DeepSeek R1: 75% / 25%.

DeepSeek V3 and Mistral make no +吗 errors. This direction reverses the original hypothesis: instead of +吧 collapsing toward +吗, +吗 is assimilated toward the +吧-like reading. The human exploratory data show the same direction. All six structurally collapsed families and all four gold-shifted items move from neutral toward confirmation-seeking, never in the reverse direction.

### 3. Model-specific default labels shape both strong and weak scores

The confusion matrices and context-only ablation indicate that some models gravitate toward a preferred label:

- **Gemma favors TENTATIVE**, scoring 100% on +吧 but 35% on +吗. It returns TENTATIVE on all 20 +吧 items and on 13 of 20 +吗 items.
- **DeepSeek V3 favors NEUTRAL**, producing the mirror pattern: 100% on +吗 but 40% on +吧.
- **Mistral shows no comparably strong default**, with more balanced scores of 85%, 90%, and 100% across bare, +吧, and +吗.

These defaults do not establish whether a model understands a particle. They explain why a fixed label preference can help on one condition and hurt on another.

### 4. Identical 100% scores can reflect different behavior

The ablation shows that the same 100% accuracy can come about in different ways. In some cases, the model already gave the correct answer based on the context alone. In others, the model initially gave a wrong answer and changed to the correct one after seeing the target sentence.

For example, Gemini and DeepSeek R1 both scored 100% on +吧, but their ablation results differ. Gemini had only two cases where its context-only answer was wrong and needed to be corrected, while DeepSeek R1 corrected all nine such cases after seeing the target sentence. The same contrast appears for +吗: DeepSeek V3 had only two cases to correct, while Mistral corrected all ten of its initially wrong answers. Thus, a 100% score does not always mean that models are using the target sentence in the same way. The DeepSeek R1 and Mistral results also show that models can use the sentence-final form to revise their initial interpretation.

### 5. The distractor is never selected

No model selects the DISTRACTOR on any main-experiment item. Although each question has four answer options, model responses are effectively limited to the three meaningful interpretations: ASSERT, TENTATIVE, and NEUTRAL. For describing these results, **33%** is a more useful reference point than the nominal four-option level of 25%.

This helps put Gemma's 35% accuracy on +吗 into perspective. Its answers are not spread evenly across the three interpretations: Gemma chooses TENTATIVE on 65% of the +吗 items and NEUTRAL on 35%, while never choosing ASSERT or the distractor. Its 35% accuracy is close to 33% because Gemma strongly favors TENTATIVE on these items, not because it is choosing randomly among the three interpretations.

For the complete narrated analysis and all supporting tables, start with [`results/main_scoring/main_scoring_summary.md`](results/main_scoring/main_scoring_summary.md).

## Limitations and future work

- **Fixed condition-to-label mapping.** In the confirmatory set, bare always maps to ASSERT, +吧 to TENTATIVE, and +吗 to NEUTRAL. A model can score well on a condition by favoring its associated label. Future work should vary the correct interpretation within each surface condition so that a model can truly use the context.
- **Small annotator pool.** Five annotators were recruited, and the primary gold uses three after quality-control exclusions. A larger independent pool would make the results less dependent on any one annotator's response pattern and give a more reliable picture of how much native speakers disagree. 
- **Text-only presentation.** Without intonation or an interactive exchange, +吧 is particularly difficult for native speakers to judge consistently. Its 78.3% concordance is greatly below the 98.3% bare result.
- **Exploratory evidence is limited.** Only four items directly test what happens when native speakers shift away from a particle's usual interpretation in context. These items suggest that models may favor the usual reading, but four cases are too few to show how general or stable this pattern is.
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
docs/                     project documentation and analysis
config/                   model roster and runtime configuration
```

Useful entry points:

- [`results/main_scoring/main_scoring_summary.md`](results/main_scoring/main_scoring_summary.md) — complete narrated results;
- [`results/human_baseline_core3/`](results/human_baseline_core3/) — human leave-one-out and concordance baselines;
- [`results/figures/`](results/figures/) — five result figures in PNG and PDF;
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

This root README intentionally presents only the quickest entry points. Each stage of the pipeline can be run separately from the command line. Detailed intermediate records are saved under `intermediate_outputs/`, while final tables, summaries, and figures are stored under `results/`.
