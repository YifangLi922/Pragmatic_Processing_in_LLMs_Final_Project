# SFP-Project: Dataset and Annotation Methodology

This document describes the human-data side of the SFP-ba project. It covers item design, piloting, annotator recruitment, automated and descriptive quality control, and frozen-dataset provenance.

## 1. Dataset purpose

The dataset tests whether changing only a Mandarin sentence-final form changes the interpreted stance of a speaker in a controlled context.

Each family holds constant:

- discourse context;
- proposition `P`;
- speaker and addressee;
- interpretation question;
- four answer options and their displayed order.

Only the target sentence's final form changes:

| Condition | Form | Design-intended role |
|---|---|---|
| bare | `P` | `ASSERT` |
| +吧 | `P` + 吧 | `TENTATIVE` |
| +吗 | `P` + 吗 | `NEUTRAL` |

The empirical gold is not assigned from this table automatically. It is calculated from native-speaker judgments. The distinction between **design intent** and **empirical gold** is essential because some contexts cause native speakers to reinterpret a particle away from its default description.

## 2. Unit of analysis: the minimal triplet

The basic unit is a **family**, not an isolated item. A family contains three conditions that differ only in sentence-final form.

The minimal-triplet design supports two levels of evaluation:

- **item-level accuracy:** whether one condition receives its empirical gold interpretation;
- **contrastive family success:** whether all three forms in the same context receive the appropriate, distinct interpretations.

The family structure also determines the ablation design. When the target sentence is removed, all three prompts in a family become identical. Any condition labels attached to the resulting context-only rows are bookkeeping comparisons with three gold labels, not three different contexts.

## 3. Semantic response roles

Every item presents four answer options corresponding to the following roles:

| Canonical label | Stored description | Definition |
|---|---|---|
| `ASSERT` | `statement` | the speaker presents `P` as a relatively confident assertion |
| `TENTATIVE` | `confirmation` | the speaker leans toward `P` but seeks confirmation |
| `NEUTRAL` | `neutral` | the speaker asks whether `P` is true without expressing a leaning |
| `DISTRACTOR` | `distractor` | an intentionally irrelevant interpretation |

The displayed option letters A–D do not have stable meanings across families. `option_semantic_map` records the mapping for each family.

To avoid confounding condition with option position, the options were shuffled once per family after the full item set was written. The same order was then used for bare, +吧, and +吗 within that family.

## 4. Construction framework

The detailed source framework is available in:

- [`../item_design/item_design_framework_zh.md`](../item_design/item_design_framework_zh.md) — original Chinese framework;
- [`../item_design/item_design_framework_en.md`](../item_design/item_design_framework_en.md) — condensed English version.

Two sets of dimensions guided sampling.

### 4.1 Interaction setting

A 2 × 2 grid combined:

- channel: offline or online;
- relationship: personal/peer or role-based/institutional.

The grid was used to prevent all items from resembling the same type of conversation. It was not analyzed as a fully crossed experimental factor.

### 4.2 Proposition grouping

Target propositions were varied across four broad categories:

1. identity or classification;
2. external state or result;
3. person-related state or experience;
4. future or expected event.

Combining the interaction grid and proposition groupings yields 16 possible sampling combinations. These combinations served as a coverage map, not a quota. The project did not require every combination to contain the same number of families.

The authoring priority was:

> **contrast quality > naturalness > diversity > exact numerical balance**

## 5. LLM assistance and human authorship

Some contexts and propositions were drafted directly. For others, an LLM (ChatGPT 5.6, thinking level set to high) was used to generate candidate starting points for a selected area of the sampling framework.

The LLM-generated text was not accepted as final stimulus material. Every candidate was reviewed manually. In many cases:

- only the underlying proposition was retained;
- the discourse context was rewritten;
- the target wording was changed;
- the relationship or setting was reassigned;
- distractors and answer phrasing were revised for semantic clarity.

The resulting dataset is therefore hand-curated and LLM-assisted rather than automatically generated. The construction framework records the intended coverage and revision principles.

## 6. Pilot phase

The pilot contained **10 families (30 items)** and was completed by one native Mandarin speaker known to the author.

Its purpose was formative:

- identify unnatural wording;
- detect contexts that did not support a clean three-way contrast;
- test whether answer options represented distinct pragmatic readings;
- identify particle conditions that were difficult to interpret without prosody.

The pilot annotator's responses were used to revise items only. They do not contribute to the main annotation pool or empirical gold labels.

The pilot highlighted a recurring limitation: +吧 was often harder to judge in plain text than bare or +吗. Confirmation-seeking force can depend on intonation, interpersonal expectations, and the immediate conversational exchange. A separate particle, 呢 (ne), was removed from the study after piloting for a related text-only interpretability problem.

Pilot materials are stored under [`../item_design/pilot/`](../item_design/pilot/).

## 7. Expansion and final item-bank preparation

After pilot-driven revision, the dataset was expanded by 26 families to **36 candidate families (108 items)**.

Before main annotation:

1. all contexts and target sentences were finalized;
2. each family received one shared four-option question;
3. the option order was shuffled once per family;
4. the same order was copied to all three conditions;
5. design-intended answers were stored in the master key;
6. annotation sheets were generated from the finalized item bank.

The master answer key is located at:

[`../raw_xlsx_data/original_data_with_answers/SFP_master_answer_key.xlsx`](../raw_xlsx_data/original_data_with_answers/SFP_master_answer_key.xlsx)

The design key is retained for provenance and later comparison. It is not substituted for native-speaker gold in the main analysis.

## 8. Main annotation task

Annotators evaluated all 108 items. The collected fields supported both semantic labeling and response-quality diagnostics.

The records include:

- selected answer option;
- item naturalness rating;
- hesitation indicator;
- “no valid option” indicator;
- unanswered or malformed responses where present.

The semantic answer letter was translated through the family-specific option map during reconstruction. This prevents analysis from treating one displayed letter as if it had a fixed semantic meaning.

The original spreadsheets are stored under:

[`../raw_xlsx_data/native_speaker_annotations/`](../raw_xlsx_data/native_speaker_annotations/)

## 9. Recruitment timeline

### 9.1 Initial recruitment

Four native Mandarin speakers were recruited through an open call in a university group chat. They completed the finalized annotation materials independently.

### 9.2 Fifth annotator

After the first batch was received, one annotator's pattern raised a concern about independent item-by-item evaluation. A fifth native speaker known to the author was recruited to restore the intended annotation capacity.

This addition was reactive and is treated as a disclosed researcher degree of freedom. The fifth annotator nevertheless:

- received the same finalized materials;
- completed the task independently;
- underwent the same blind diagnostic;
- was assessed under the same exclusion criteria.

The diagnostic rules were fixed before empirical gold labels were computed.

## 10. Reconstruction and automated quality checks

The reconstruction stage joins each answer sheet to the master item bank and writes:

- `data/reconstructed_5ann.json` — the canonical 108-item × 5-annotator record;
- `data/quality_report_5ann.json` — automated quality indicators.

The quality report checks for:

| Check | Operational signal |
|---|---|
| answer-letter straight-lining | more than 70% of answers use one displayed letter |
| missingness | unanswered items |
| naturalness invariance | zero variance in ratings |
| flat responding | zero hesitation, zero “no valid option,” and zero naturalness variance together |
| design-key outlier | agreement with the design key more than two standard deviations from the batch (`z > 2`) |

These checks are diagnostic signals. A high or low agreement score alone does not define the empirical gold and should not be used to exclude an annotator solely because they disagree with the intended answer.

The full reconstruction command is documented in [`pipeline.md`](pipeline.md).

## 11. Descriptive annotator diagnostics

`src.diagnostic` calculates condition-wise agreement and coverage for each annotator against a leave-one-out reference pool of the others.

The outputs are described in:

[`../intermediate_outputs/diagnostic/Diagnostic_Output_README.md`](../intermediate_outputs/diagnostic/Diagnostic_Output_README.md)

This condition-wise view is important because a global label preference can appear normal in the condition whose intended answer matches that preference. A single aggregate agreement score would conceal that structure.

## 12. Annotator decisions

Two of the five annotators were excluded before model-facing analysis.

### 12.1 Econ — response-style exclusion

Econ showed a strong global preference for the confirmation label.

- bare consistency was 66.7%, compared with approximately 94–97% for the retained annotators;
- +吗 consistency was 25%;
- +吧 appeared normal because the confirmation label usually coincides with the intended +吧 answer.

The same response tendency explains the pattern across conditions. The decision was therefore based on a cross-condition response style rather than on disagreement with isolated items.

### 12.2 BWL — suspected non-independent responding

BWL's combined response pattern included:

- a 5/5 naturalness rating on all 108 items;
- zero hesitation marks;
- zero “no valid option” marks;
- approximately 94% agreement with the original design answer key, substantially above the other annotators.

No single indicator is decisive in isolation. Taken together, the pattern was treated as inconsistent with independent evaluation of every item.

### 12.3 Timing and rationale

Both exclusions were made before inspecting model results. Removing a dissenting response mechanically increases majority formation, so the number of newly classifiable families is not itself evidence that the exclusions were correct.

The rationale rests on the diagnostic patterns, their condition-wise coherence, and the independent convergence of the retained annotators.

## 13. The core3 gold pool

The primary gold pool contains:

- **Media** — media studies background;
- **Materials** — materials science background;
- **EngLit** — English literature background.

Media and Materials came from the public group-chat recruitment. EngLit was recruited later and was known to the author. The three annotators did not know one another and could not coordinate responses.

They achieve approximately **72% pairwise agreement** across four answer options. With four displayed choices, a uniform nominal reference would be 25%, though the distractor is not equally plausible on well-formed items.

For each item, the core3 majority defines `gold_semantic`. The corresponding displayed option is stored as `gold_letter`.

## 14. Abstentions, margins, and majority strength

The frozen files record the core3 support margin:

| Margin | Pattern | Meaning |
|---:|---|---|
| `3` | 3:0 | all three annotators select the gold role |
| `2` | 2:0 plus one abstention | all valid responses agree |
| `1` | 2:1 | majority with one dissenting response |

An item without a majority cannot enter a KEEP family. Margin is preserved so model results can be stratified by human agreement strength.

In the final confirmatory set, model accuracy is broadly similar across margins. This does not change the gold rule; it is a downstream robustness observation.

## 15. Family classification

Gold labels are evaluated at the family level after item-level majorities are computed.

### `KEEP`

Every condition has a clear majority and the three labels are distinct. Under core3 there are **20 KEEP families**, forming the confirmatory dataset.

### `COLLAPSE_structural`

Every relevant item remains interpretable, but two conditions share an empirical gold label. Under core3 there are **6 collapsed families**, forming the exploratory dataset.

The collapse is analytically meaningful: all six families move in the neutral-to-confirmation-seeking direction rather than the reverse.

### `NO_CONSENSUS`

At least one condition has no majority. There are **8 such families**. They are excluded because the family does not support a stable empirical contrast.

### `EXCLUDE_BROKEN`

At least one condition's majority selects the distractor. There are **2 such families**. A distractor-majority item indicates that the intended interpretation question or options have failed.

## 16. Confirmatory and exploratory datasets

| Set | Families | Items | Purpose |
|---|---:|---:|---|
| confirmatory | 20 | 60 | primary accuracy and contrastive evaluation |
| exploratory | 6 | 18 | collapsed and design-shift analyses |
| excluded | 10 | 30 | no model-facing analysis |

The confirmatory set preserves the intended three-way distinction under empirical human gold. All 60 confirmatory items have empirical gold equal to design gold.

The exploratory set contains structural collapses and four individual items where empirical gold shifts away from the design label. It should not be pooled with confirmatory data or used for directly comparable accuracy estimates.

## 17. Annotator-pool sensitivity

Family classification is recalculated under four pools:

1. core3;
2. core3 + Econ;
3. core3 + BWL;
4. all five annotators.

This analysis exposes how much the frozen selection depends on the chosen annotator pool.

Of the 20 core3 KEEP families:

- 11 remain KEEP under all four pools;
- 9 change class under at least one alternative;
- 8 of those 9 are destabilized specifically by including Econ.

The 11-family intersection is a conservative stability subset. The main analysis uses all 20 core3 KEEP families because the core3 pool was selected through independent diagnostics. Requiring a family to survive the +Econ pool would effectively allow the diagnosed response-style outlier to veto it.

Pool-sensitivity outputs are stored under:

[`../intermediate_outputs/pool_sensitivity/`](../intermediate_outputs/pool_sensitivity/)

## 18. Dataset freeze and provenance

`src.freeze` joins:

- reconstructed item and annotation records;
- core3 item-level gold labels;
- core3 family classifications;
- four-pool stability information.

It writes:

- [`../intermediate_outputs/frozen_dataset/frozen_dataset.csv`](../intermediate_outputs/frozen_dataset/frozen_dataset.csv) — 60 confirmatory items;
- [`../intermediate_outputs/frozen_dataset/frozen_exploratory.csv`](../intermediate_outputs/frozen_dataset/frozen_exploratory.csv) — 18 exploratory items;
- [`../intermediate_outputs/frozen_dataset/freeze_report.md`](../intermediate_outputs/frozen_dataset/freeze_report.md) — provenance, family grid, and gold shifts.

All downstream querying and scoring stages treat the two CSV files as read-only ground truth. The producing commit is tagged `dataset-frozen-v1`.

Any later change to source annotations, exclusion rules, pool membership, or family classification should create a new frozen version rather than silently replacing the reported dataset.

## 19. Frozen-file fields

| Field | Purpose |
|---|---|
| `family_id` | links the three minimal-triplet conditions |
| `item_id` | uniquely identifies one family/condition row |
| `condition` | bare, ba, or ma |
| `context_text` | shared family context |
| `target_sentence` | the manipulated utterance |
| `option_A` … `option_D` | displayed answer texts |
| `option_semantic_map` | letter-to-role mapping |
| `gold_semantic` | core3 empirical majority role |
| `gold_letter` | displayed letter corresponding to gold |
| `design_gold_semantic` | role intended during construction |
| `gold_shifted` | whether empirical and design gold differ |
| `margin` | strength of core3 support |
| `stable_keep_all_pools` | whether family remains KEEP under all four pools |
| `collapse_pair` | exploratory conditions sharing a role |
| `collapse_label` | role shared by the collapsed conditions |

For the full model-result schema, see [`results_guide.md`](results_guide.md).


