# SFP-ba: Sentence-Final Particle Sensitivity in Large Language Models

This project tests whether large language models can read the pragmatic
meaning that Mandarin sentence-final particles add to an utterance, the
same way native speakers do. The study **centers on the particle 吧 (ba)**;
**吗 (ma)** and the particle-less "bare" form serve as its two contrast
conditions. A sentence-final particle attaches to the end of a sentence and,
without changing its literal content, sets the speaker's stance toward it:

| Form | Literal gloss | Pragmatic effect |
|---|---|---|
| `P` (no particle, "bare") | plain statement | read as a confident **assertion** |
| `P` + **吧 (ba)** | "P, right?" / "P, I take it" | read as a **tentative, confirmation-seeking** statement — the speaker leans toward believing P but wants it confirmed |
| `P` + **吗 (ma)** | "Is it the case that P?" | read as a **neutral yes/no question** — the speaker has no stated leaning |

A model that has genuinely learned this should give a different answer to
"what is the speaker doing here?" depending on which of the three forms it
sees, even though the surrounding context and the propositional content
`P` are identical. A model that has only memorized the dictionary
definitions of 吧/吗 without being sensitive to how they interact with
context might not.

This repository contains the full pipeline: the hand-built + LLM-assisted
item set, the native-speaker annotation and quality-control process used to
establish ground truth, the code that queries six LLMs, and the analysis
that scores them against that ground truth and against a human baseline.

**This is the authoritative, up-to-date documentation of the finished
project**, written for readers who do not read Mandarin. The repository
also contains `README_zh.md`, which is an earlier-stage Chinese-language
development log (covering roughly the first third of the project, before
the dataset was frozen); it is kept for historical continuity but is no
longer current. `analysis_note_zh.md` (Chinese) is the original analysis
narrative this README's "Key Findings" section is adapted from.

---

## TL;DR — the main finding

> **Models track the "textbook" function of a particle; native speakers
> track the specific context. When the two agree, models look excellent.
> When they disagree, models fall back to the textbook.**

This claim rests **directly** on two pieces of evidence, supported by
**three further results** that establish the task is valid and identify the
mechanism behind the raw numbers (see [Key Findings](#8-key-findings)
below). The result runs opposite to the project's original hypotheses
(see [§1](#1-research-question-and-design)).

---

## Table of contents

1. [Research question and design](#1-research-question-and-design)
2. [Repository structure](#2-repository-structure)
3. [Setup](#3-setup)
4. [Item construction](#4-item-construction-how-the-stimuli-were-built)
5. [The data pipeline, step by step](#5-the-data-pipeline-step-by-step)
6. [Running the tests](#6-running-the-tests)
7. [How to interpret the output](#7-how-to-interpret-the-output)
8. [Key findings](#8-key-findings)
9. [Limitations and future work](#9-limitations-and-future-work)
10. [Evidence summary](#10-evidence-summary)
11. [Models, cost, and reproducibility notes](#11-models-cost-and-reproducibility-notes)

---

## 1. Research question and design

**Core question.** The focal particle is **吧 (ba)** — specifically its
*confirmation-seeking / tentative-assertion* use (the reading where the
speaker leans toward `P` but lowers their commitment and invites the hearer
to confirm), not the particle's full functional range. The central question
is whether a model shows **systematic contrastive sensitivity** to the
stance this 吧 contributes: holding the proposition `P` and the context
fixed and changing *only* the sentence-final form (bare / 吧 / 吗), does the
model's reading of the speaker's attitude *shift in the linguistically
predicted direction* — the way a native speaker's does — or does it only
recognize the particles' dictionary meaning without tracking how they
interact with context? Two further questions sit alongside it: whether
models recover each condition's intended reading at all (per-condition
accuracy), and whether this sensitivity differs across model **families**.

The contrast is what makes 吧's contribution measurable: **bare** `P` is the
no-particle baseline (a plain assertion), and **+吗** is a neutral-question
comparison. The bar is deliberately higher than getting any single condition
right — genuine sensitivity requires the answer to *change appropriately*
when the ending changes and everything else is held fixed.

**Design — the minimal triplet.** Every test item belongs to a *family*: one
shared context, one shared target proposition `P`, and one shared
four-option question, realized in three conditions that differ **only** in
how the target sentence ends (bare / +ba / +ma). Because everything else is
held fixed within a family, any difference in a model's answer across the
three conditions can only be attributed to the particle itself.

**Example family** (F01, one of the 20 families used in the main
analysis; English glosses added):

> **Context:** Zhou and Lin are attending a training session organized by
> their workplace. A staff member just came by to remind everyone to sign
> in. After that person leaves, Zhou says to Lin:
>
> - **bare:** 刚才那位是这里的负责人 — *"That person just now is the one in
>   charge here."*
> - **+ba:** 刚才那位是这里的负责人**吧** — *"That person just now is the one
>   in charge here, right?"*
> - **+ma:** 刚才那位是这里的负责人**吗** — *"Is that person the one in
>   charge here?"*
>
> **Question:** which attitude is Zhou most likely expressing?
>
> A. Zhou is asking Lin to go find that person *(distractor — off-topic)*
> B. Zhou is just asking whether that person is in charge, with no clear
>    leaning either way *(neutral)*
> C. Zhou is fairly confident that person is in charge, and is telling Lin
>    *(assert / statement)*
> D. Zhou leans toward thinking that person is in charge, but isn't fully
>    sure, and wants Lin to confirm *(tentative / confirmation-seeking)*

By design, bare items are expected to select C, +ba items D, and +ma items
B. Throughout the code and the output tables these four semantic roles are
labelled **ASSERT** (statement), **TENTATIVE** (confirmation-seeking),
**NEUTRAL**, and **DISTRACTOR** — this is the fixed vocabulary used
everywhere (confusion matrices, figures, CSV columns).

**Original hypotheses (H1 and H4):** +ba would be the hardest condition for
models (H1), and +ba's errors would systematically collapse into +ma — a
confirmation-seeking statement misread as a neutral question (H4). **Both
came out the other way around:** models found +ma the hardest condition, and
it was +ma that collapsed into +ba — see [Finding 2](#8-key-findings).

---

## 2. Repository structure

```
item_design/                    # How the test items were designed (see §4)
  item_design_framework_zh.md   # The original construction framework/heuristics in Chinese
  item_design_framework_en.md   # The translated English construction framework/heuristics
  SFP pilot families.docx                # First-draft write-up: the 10 pilot families
  SFP expanded families.docx             # Draft after expanding to all 36 families
  pilot/
    SFP_pilot_annotation_form.xlsx         # Annotation form given to the 1 pilot annotator
    SFP_pilot_annotation_result.xlsx       # That pilot annotator's completed responses

raw_xlsx_data/                  # Raw spreadsheets, as collected
  original_data_with_answers/
    SFP_master_answer_key.xlsx   # Master item bank + intended ("design") answer key
  native_speaker_annotations/
    SFP_annotator1_Econ.xlsx           # Annotator "Econ" (economics background) -- excluded, see §8 §0
    SFP_annotator2_Media.xlsx          # Annotator "Media" (media studies) -- core3
    SFP_annotator3_Materials.xlsx      # Annotator "Materials" (materials science) -- core3
    SFP_annotator4_BWL.xlsx            # Annotator "BWL" (business administration) -- excluded, see §8 §0
    SFP_annotator5_EngLit.xlsx         # Annotator "EngLit" (English literature) -- core3

data/                           # Derived data (JSON), used as input further down the pipeline
  reconstructed_5ann.json        # Final reconstruction: 108 items x 5 annotators -- everything
                                  # downstream (diagnostic, pool sensitivity, freeze, human
                                  # baseline) reads this file
  reconstructed.json             # Earlier 4-annotator reconstruction, used only to validate
                                  # the reconstruction code before the 5th annotator's data
                                  # arrived; not used by any of the reported results
  quality_report_5ann.json / quality_report.json   # Per-annotator QC reports for the two files above
  ablation_raw.jsonl              # Raw LLM responses from the context-only ablation query
  fake_items.json / fake_annotations.json           # Synthetic fixtures used only by unit tests

intermediate_outputs/           # Process artifacts -- each stage's own output, consumed by
                                 # a later stage, not itself a headline result
  diagnostic/                    # Per-annotator, per-condition QC (used to decide the
                                  # Econ/BWL exclusions, see §4 and §8 §0)
  pool_sensitivity/               # Family classification (KEEP / COLLAPSE / NO_CONSENSUS /
                                  #  EXCLUDE_BROKEN) under 4 candidate annotator pools
  frozen_dataset/                  # The final, frozen item set (see §5.4) -- frozen_dataset.csv
                                  # (60 confirmatory items) + frozen_exploratory.csv (18
                                  # exploratory items) + freeze_report.md
  ablation/                         # Context-only ablation: what each model answers when the
                                  # target sentence is removed
  main_experiment/                  # Raw main-experiment query results (6 models x 78 items,
                                  # target sentence included)

results/                        # Final tables and figures -- the headline output
  main_scoring/
    main_scoring_summary.md         # Start here -- narrated summary of every table below
    condition_accuracy/              # Accuracy by model x condition (confirmatory + exploratory)
    margin_stratified_accuracy/       # Accuracy broken down by how unanimous the human gold was
    target_sentence_delta/             # Did the model change its answer once shown the target
                                      # sentence, and was the change correct? (used_target,
                                      # update_precision, prior_correction)
    confusion_matrices/                 # Model choice vs. gold, per model
    design_gold_following/               # On exploratory items where the empirical gold shifted
                                      # away from the design intent, which one did the model follow?
  human_baseline_core3/             # Native-speaker baseline (LOO + concordance), for
                                  # comparison against model accuracy
  figures/                          # The 5 poster figures, PNG (300dpi) + PDF, one subfolder each
    fig1_condition_accuracy/
    fig2_confusion_grid/
    fig3_ba_vs_ma_scatter/
    fig4_used_target_by_condition/
    fig5_design_gold_following/

config/models.yaml               # The 6-model roster (provider/model id/price/notes) -- change
                                  # models here, not in code
.env.example                     # Copy to .env and fill in OPENROUTER_API_KEY

src/                              # All pipeline code (one subpackage per stage, see §5)
tests/                            # Unit tests, one subfolder per src/ subpackage


SFP_project_plan_v3.md                      # Original research plan (v3): research questions, hypotheses, scope (Chinese), summarized in §1 of this README
analysis_note_zh.md                              # Full analysis narrative this README's §8-10 are based on (Chinese)
README_zh.md                                # Earlier-stage Chinese development log (see note above)
```

---

## 3. Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in OPENROUTER_API_KEY
```

Everything below is pure Python (stdlib + `PyYAML`, `python-dotenv`,
`requests`, `openpyxl`, `matplotlib`, `numpy`, `pytest`); no GPU or external
service is required except for the two steps that call LLMs
(`src.ablation.query` and `src.main_experiment.query`), and those are
resumable and budget-capped (see [§11](#11-models-cost-and-reproducibility-notes)).

---

## 4. Item construction: how the stimuli were built

The complete design framework is in [`item_design/item_design_framework_zh.md`](item_design/item_design_framework_zh.md)
(Chinese) and the condensed English version is in [`item_design/item_design_framework_en.md`](item_design/item_design_framework_en.md). This section gives a summary.

Every family's target proposition `P` had to support a clean three-way
contrast (bare reads as assertion, +ba as confirmation-seeking, +ma as a
neutral question), so items were not sampled from a fixed experimental
design in the usual factorial sense. Instead, the framework document lays
out a **construction scaffold**, not a set of experimental factors:

- A **2x2 "interaction setting" grid** (channel: offline / online, x
  relation: personal-peer / role-based-institutional) used to keep the
  *sampling* of contexts varied, so that all 20+ families didn't end up
  reading like the same conversation.
- **4 researcher-defined "proposition classes"** (identity/classification;
  external state or result; person-related state/experience;
  future/expected event) used as a *writing heuristic* to keep the content
  of `P` varied, again not as an experimental factor to be analyzed.

Crossing these gives a 4x4 space of 16 candidate cells, used only as
coverage guidance ("try to touch most of these cells, don't obsess over
filling every one") — the framework is explicit that **contrast quality
comes before naturalness, which comes before coverage, which comes before
exact numerical balance.**

Concretely, item authoring worked like this:

1. For a candidate proposition `P`, either the author (a native Mandarin
   speaker) wrote the context and target sentence directly, **or** asked an
   LLM (ChatGPT 5.6, reasoning effort set to "high") for candidate sentences
   that fit a specific cell of the framework above.
2. LLM-generated candidates were essentially never used verbatim — they
   tended to read as stiff or artificial. In practice, only the underlying
   *idea* (the proposition and the intended contrast) was kept, and the
   context and phrasing were rewritten by hand, often changing the setting
   completely.
3. **Pilot phase:** 10 families (30 items) were built first and given to a
   single native speaker — an acquaintance of the author (an architecture
   student) — to annotate. This surfaced concrete problems (for
   instance, +ba items in particular tended to read as less natural than
   the other two conditions in a pure-text, no-intonation format — see
   [Limitations](#9-limitations-and-future-work)). The pilot materials
   (write-up, annotation form, and that annotator's responses) are kept in
   [`item_design/pilot/`](item_design/pilot/).
4. After revising based on pilot feedback, the set was expanded from 10 to
   36 families (26 new families added). Only after the full 36-family set
   was finalized, option order shuffled (once per family, so a family's three
   conditions share the same A/B/C/D layout), and compiled into the
   master answer-key spreadsheet
   ([`raw_xlsx_data/original_data_with_answers/`](raw_xlsx_data/original_data_with_answers/))
   were the native-speaker annotators recruited to annotate it (§5.1); how
   that recruitment worked is described next.

**How the annotators were recruited (and why it matters for the ground
truth).** The single pilot annotator was an acquaintance of the author (the
architecture student above); because the pilot only informed item revision
and contributes no ground-truth label, it has no bearing on the reported
results. For the main annotation, **four native speakers were recruited
openly and at random through a university group chat** — they did not know
one another or the author. This arm's-length recruitment is what gives the
core-3 agreement figure (§8 §0) its weight: independent strangers converging
on the same reading is evidence about the *items*, not about who was picked.

After the four responses came back, one annotator (**BWL**) showed signs of
non-independent responding (§8 §0), which left the batch short of usable
independent annotators. **A fifth native speaker — an English-literature
student known to the author — was then recruited to restore that lost
capacity.** This was a *reactive* addition, made after the first responses
had been seen, so to be explicit about it: the fifth annotator went through
exactly the *same* blind diagnostic and the *same* pre-specified exclusion
criteria as everyone else (and passed both), was given no special weight, and
does not know the other two core-3 annotators — so core-3's cross-annotator
agreement still reflects independent convergence rather than coordination.
The exclusion criteria themselves were fixed before the gold labels were
computed.

---

## 5. The data pipeline, step by step

Every step below is a `python -m src.<package>` command with its own
`__main__.py`; run them in this order to reproduce every file under
`intermediate_outputs/` and `results/` from scratch. All arguments are
explicit paths — nothing is hardcoded to a particular machine.

### 5.1 Reconstruction (`src.reconstruct`)

Joins the master answer-key spreadsheet with each native speaker's raw
answer sheet into one machine-readable record per item, with each
annotator's answer translated from a letter (A/B/C/D, whose order was
shuffled per family) into its semantic role (statement / confirmation /
neutral / distractor).

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

The quality report automatically flags: straight-lining (>70% of answers on
one letter), unanswered items, zero variance in naturalness ratings, "flat
responding" (zero hesitation + zero "no valid option" + zero naturalness
variance at once), and an annotator whose agreement with the *design*
answer key is a statistical outlier relative to the rest of the batch
(z > 2). These checks fed directly into the annotator-exclusion decision
below.

### 5.2 Annotator diagnostic (`src.diagnostic`)

Descriptive, condition-wise QC per annotator (bare/ba/ma agreement and
coverage against a leave-one-out reference pool of the others). This is
what identified the two annotators later excluded from the "core3" pool:

```bash
python -m src.diagnostic \
    --reconstructed data/reconstructed_5ann.json \
    --output-dir intermediate_outputs/diagnostic
```

See [`intermediate_outputs/diagnostic/Diagnostic_Output_README.md`](intermediate_outputs/diagnostic/Diagnostic_Output_README.md)
for the full output layout, and [Key Findings §0](#8-key-findings) below for
what it found.

### 5.3 Pool sensitivity (`src.pool_sensitivity`)

For each of the 36 item families, computes the empirical (annotator-vote)
gold answer for each condition and classifies the family as KEEP /
COLLAPSE_structural / NO_CONSENSUS / EXCLUDE_BROKEN, under 4 different
candidate annotator pools (core3, core3+Econ, core3+BWL, all 5) — this is
what makes the final family selection auditable rather than a one-off
manual call.

```bash
python -m src.pool_sensitivity \
    --reconstructed data/reconstructed_5ann.json \
    --output-dir intermediate_outputs/pool_sensitivity
```

Under the core3 pool, the 36 families classify as follows:

| Class | Count | Meaning | Fate |
|---|---|---|---|
| **KEEP** | 20 | every condition has a clear majority gold, and the three golds are distinct | **confirmatory set** |
| **COLLAPSE_structural** | 6 | two conditions' majority golds land on the same label — the contrast disappears, but the item is otherwise valid | **exploratory set** |
| **NO_CONSENSUS** | 8 | at least one condition has no majority | dropped |
| **EXCLUDE_BROKEN** | 2 | a condition's majority landed on the distractor, so the item is broken | dropped |

The **exclusion rate is itself a result**: 8 no-consensus families plus 2
broken ones (10 of 36) mean that, in a pure-text format, a sizeable share of
particle-annotation items simply cannot reach native-speaker consensus. This
is a property of the paradigm, not a flaw in these particular items.

The grid also shows how much the family selection depends on *which*
annotators are in the pool. Of the 20 core3 KEEP families, 9 change class
under at least one other pool — but **8 of those 9 are destabilized by Econ
alone**, not scattered across annotators, which re-confirms the Econ
diagnostic (§5.2) at the family level. Taking the intersection of all four
pools (families that survive under *every* annotator choice) leaves **11
families**. That number is reported as the most conservative lower bound,
but the main analysis uses the 20 core3 KEEP families: requiring survival
under the +Econ pool would effectively give the one diagnosed outlier a veto
over the item set.

### 5.4 Freeze (`src.freeze`)

Joins the pool-sensitivity classification (under the core3 pool
specifically) with the item text into the two CSVs that every later step
treats as read-only ground truth, and writes a full provenance report.

```bash
python -m src.freeze \
    --reconstructed data/reconstructed_5ann.json \
    --pool-sensitivity-dir intermediate_outputs/pool_sensitivity \
    --output-dir intermediate_outputs/frozen_dataset
```

This produced `frozen_dataset.csv` (20 KEEP families x 3 conditions = 60
"confirmatory" items — the primary analysis set) and
`frozen_exploratory.csv` (6 COLLAPSE_structural families x 3 = 18
"exploratory" items — reported separately, not comparable to confirmatory
accuracy, see [§7](#7-how-to-interpret-the-output)). The commit that
produced these two files is tagged `dataset-frozen-v1`; see
[`intermediate_outputs/frozen_dataset/freeze_report.md`](intermediate_outputs/frozen_dataset/freeze_report.md)
for the complete provenance record, including the pool-sensitivity grid
and the exact list of gold-shifted items.

### 5.5 Context-only ablation (`src.ablation`)

Queries all 6 models on the frozen items with the **target sentence
removed** (context + question + options only, everything else identical).

One consequence of the minimal-triplet design matters for reading this step
correctly. Within a family, the three conditions share the *same* context
and differ *only* in the target sentence. Once that sentence is removed, the
three prompts become byte-for-byte identical, so a model necessarily returns
the *same* answer for all three conditions of a family. The ablation
therefore does **not** measure a separate context leak per condition; what
it measures is each model's single **default answer** for that context when
no particle has been seen yet — its "prior". This prior is used two ways:
as a leakage check (if the context alone already forced the gold answer, the
item would be answerable without the particle) and, more importantly, as the
baseline that `target_sentence_delta` compares the real,
sentence-included run against (Findings 3 and 4).

```bash
# Step 1: query (resumable; only missing (item, model) pairs are re-queried)
python -m src.ablation.query \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --frozen-exploratory intermediate_outputs/frozen_dataset/frozen_exploratory.csv \
    --reconstructed data/reconstructed_5ann.json \
    --output data/ablation_raw.jsonl

# Step 2: turn the checkpoint into analysis tables (cheap, safe to re-run any time)
python -m src.ablation.analyze \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --frozen-exploratory intermediate_outputs/frozen_dataset/frozen_exploratory.csv \
    --reconstructed data/reconstructed_5ann.json \
    --raw data/ablation_raw.jsonl \
    --output-dir intermediate_outputs/ablation
```

**Result: 0% shortcut rate on bare items** — context alone never leaks the
answer. Because a family's three context-only prompts are byte-identical (see
above), "shortcut" cannot be a per-condition property of the stimulus: there
is only *one* default answer per family, and it gets *recorded* as a shortcut
against whichever condition's gold it happens to coincide with. The bare gold
is always ASSERT, so bare's 0% shortcut rate says precisely that **no
family's default answer is ASSERT**. The flags that do appear — on 8 +ba
items and 3 +ma items in the 60-item confirmatory set (the default coinciding
with the +ba gold, TENTATIVE, or the +ma gold, NEUTRAL) — are that same single
default landing on the +ba or +ma gold, i.e. a reflection of each model's
default-label preference (see [Finding 3](#8-key-findings)), not a leak in
the stimulus. So no families were dropped for this reason. (This also doubles
as an extra piece of evidence for Finding 3: the leak check recovers the same
default-label story from a completely separate table.)

### 5.6 Main experiment (`src.main_experiment`)

The real trial: queries all 6 models on the same 78 frozen items **with**
the target sentence included.

```bash
python -m src.main_experiment.query \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --frozen-exploratory intermediate_outputs/frozen_dataset/frozen_exploratory.csv \
    --reconstructed data/reconstructed_5ann.json \
    --output-dir intermediate_outputs/main_experiment
```

### 5.7 Main scoring (`src.main_scoring`)

Combines the main-experiment results, the ablation results, and the frozen
gold to produce every table under `results/main_scoring/`: condition
accuracy, margin-stratified accuracy, the target-sentence delta analysis,
confusion matrices, and design-gold following.

```bash
python -m src.main_scoring \
    --main-results intermediate_outputs/main_experiment/main_results.csv \
    --ablation-results intermediate_outputs/ablation/ablation_results.csv \
    --ablation-item-summary intermediate_outputs/ablation/ablation_item_summary.csv \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --frozen-exploratory intermediate_outputs/frozen_dataset/frozen_exploratory.csv \
    --output-dir results/main_scoring
```

### 5.8 Human baseline (`src.human_baseline_core3`)

Computes what native speakers themselves achieve on the same 60
confirmatory items, restricted to the three core3 annotators, under two
different metrics (explained in [§7](#7-how-to-interpret-the-output)).

```bash
python -m src.human_baseline_core3 \
    --reconstructed data/reconstructed_5ann.json \
    --frozen-dataset intermediate_outputs/frozen_dataset/frozen_dataset.csv \
    --output-dir results/human_baseline_core3
```

### 5.9 Figures (`src.results_viz`)

Renders the 5 poster figures from the two results folders above.

```bash
python -m src.results_viz \
    --main-scoring-dir results/main_scoring \
    --human-baseline-dir results/human_baseline_core3 \
    --output-dir results/figures
```

### A note on `src/gold`, `src/scoring`, and `src/stats`

These three packages are an **earlier prototype** of the scoring pipeline,
written before the dataset was frozen at 36 families (back when the plan
was still a single fixed annotator pool with no pool-sensitivity check).
They are not part of the pipeline that produced any table or figure under
`results/` — `src.main_scoring` and `src.results_viz` are the modules that
actually generated the reported results, and they do not import from
`src.gold` or `src.scoring`. `src/gold`, `src/scoring`, and `src/stats` (and
the `kappa`/`rates` helpers in `src/agreement`, as opposed to
`loo_baseline`, which *is* still used by `src.human_baseline_core3`) are
kept only because their unit tests still document the logic they contain;
they are not required to reproduce anything under `results/`.

### The generic LLM-querying engine (`src.llm_query`)

Both `src.ablation.query` and `src.main_experiment.query` are built on top
of a shared, provider-agnostic engine in `src/llm_query/`: prompt
construction, response parsing, a mock provider for offline testing, a real
OpenRouter client with retry/backoff, and a resumable runner (a rerun skips
any (item, model) pair that already has a result on disk). It can also be
run directly, which is useful as a no-API-key smoke test:

```bash
# smoke test: 5 synthetic items, deterministic mock answers, no network/API key
python -m src.llm_query --items data/fake_items.json \
    --output /tmp/fake_mock_results.jsonl --mock
```

---

## 6. Running the tests

```bash
python -m pytest tests/ -v
```

All 183 tests use synthetic fixtures only — no real `.xlsx` files, no
network access, and no API key are needed to run them. `tests/`
mirrors `src/` one subpackage at a time (e.g. `tests/main_scoring/` tests
`src/main_scoring/`). `tests/reconstruct/` does import `openpyxl`
transitively (through the module it tests), so make sure
`pip install -r requirements.txt` has been run first.

---

## 7. How to interpret the output

Start with **[`results/main_scoring/main_scoring_summary.md`](results/main_scoring/main_scoring_summary.md)** —
it narrates every table below in one place, including several
clarifications about denominators and edge cases that matter for reading
the numbers correctly. The subfolders it links to:

- **`condition_accuracy/`** — accuracy per model, per condition (bare/ba/ma),
  for the confirmatory (60-item) and exploratory (18-item) sets
  *separately*. **These two sets are never comparable to each other**: every
  exploratory family was, by construction, one where two of its three
  conditions' empirical gold collapsed onto the same label, which
  structurally inflates its accuracy relative to confirmatory. Treat
  exploratory as a secondary, qualitative set only.
- **`margin_stratified_accuracy/`** — confirmatory accuracy broken down by
  how unanimous the 3 core3 annotators were on an item's gold label (3:0
  unanimous, 2:0 unanimous-with-one-abstention, 2:1 majority). In this
  dataset, accuracy is essentially flat across all three margins (~80–82%),
  so this is not a major axis of the story — it's reported for completeness.
- **`target_sentence_delta/`** — the "did the model actually use the
  particle, or already know the answer?" family of tables:
  - `used_target_by_model[_condition].csv`: how often a model changed its
    answer once the target sentence (with the particle) was shown, versus
    the context-only ablation answer. The denominator is *both-answered
    pairs only* — a model that refused to guess in the ablation contributes
    no comparison and is excluded, not counted as "used the target".
  - `update_precision_comparison.csv` / `update_precision_by_model_condition.csv`:
    among the times a model *did* change its answer, how often was the new
    answer correct? This is a different question from raw accuracy and
    should be read alongside it, not as a replacement.
  - `prior_correction_by_model_condition.csv`: the most important table for
    interpreting any accuracy figure that looks unexpectedly high. It
    splits every (model, condition) cell into items where the ablation
    answer (no particle seen) already happened to equal gold
    ("`prior_correct`") versus items where it didn't ("`prior_incorrect`"),
    and reports each group's own main-experiment accuracy. Only the
    `prior_incorrect` group's accuracy actually measures "the model used
    the sentence to correct a wrong guess" — see
    [Finding 4](#8-key-findings) for why this matters.
- **`confusion_matrices/`** — row-normalized (`_rownorm.csv`) and raw-count
  (`_counts.csv`) confusion between gold and each model's answer, rows and
  columns fixed in ASSERT / TENTATIVE / NEUTRAL / DISTRACTOR order.
- **`design_gold_following/`** — on the 4 exploratory items where the
  empirical (annotator-majority) gold shifted away from the item's original
  design intent, how often did the model's answer match the *original
  design* label instead of the (correct, but shifted) empirical one? n=4,
  reported as a qualitative pattern only.

**`results/human_baseline_core3/`** reports two different human-baseline
metrics side by side (see `human_baseline_comparison.md` for the full
explanation of why they differ and give different numbers):
- **LOO** (leave-one-annotator-out): for each held-out core3 annotator, the
  other two's majority becomes that fold's temporary gold, and the held-out
  person is scored against it. On a 2:1 split, the minority annotator is
  *always* scored as a miss for that fold — this makes LOO a systematic
  **lower bound** on human performance.
- **concordance**: for each item, the fraction of all three core3
  annotators whose answer matches the real gold, averaged within condition.
  This asks exactly the same question model accuracy does ("what fraction
  of answerers picked gold?") and is the metric that should be compared
  directly to model accuracy in the figures.

**`results/figures/`** — five figures, PNG (300dpi, for print) and PDF
(vector) in every subfolder. No figure has an in-image title (all should
be captioned externally); model order and bare/ba/ma color coding are
consistent across all of them.

| Figure | What it shows |
|---|---|
| `fig1_condition_accuracy` | Grouped bars: accuracy per model x condition, with a shaded human-reference band (LOO–concordance range) per condition |
| `fig2_confusion_grid` | 2x3 grid of per-model confusion matrices, one shared colorbar |
| `fig3_ba_vs_ma_scatter` | Each model's +ba accuracy vs. +ma accuracy, with a y=x reference line and dashed lines marking human concordance on each axis |
| `fig4_used_target_by_condition` | How often each model changed its answer after seeing the target sentence, by condition, with n labeled on every bar |
| `fig5_design_gold_following` | The n=4 design-gold-following rates from above, deliberately drawn small since the sample is qualitative |

### 7.1 Column reference

The three files most readers will open directly. Every other CSV under
`results/` and `intermediate_outputs/` reuses the column names defined here.

**`frozen_dataset/frozen_dataset.csv`** (confirmatory, 60 rows) and
**`frozen_dataset/frozen_exploratory.csv`** (exploratory, 18 rows) — the
frozen item set each later step treats as read-only ground truth:

| Column | Meaning |
|---|---|
| `family_id` | The family (e.g. `F01`); a family's three conditions share it |
| `item_id` | Unique item id, `<family>_<condition>` (e.g. `F01_ba`) |
| `condition` | `bare` / `ba` / `ma` |
| `context_text` | The shared situational context shown before the target sentence |
| `target_sentence` | The target utterance — the *only* field that differs across a family's three conditions |
| `option_A` … `option_D` | The four answer-option texts, in the shuffled display order actually shown to annotators and models (the same order across a family's three conditions — which is what makes the ablation prompts byte-identical, §5.5) |
| `option_semantic_map` | Maps each letter to its semantic role, e.g. `A:distractor\|B:neutral\|C:statement\|D:confirmation` |
| `gold_semantic` | The empirical (core3 annotator-majority) correct role: `statement` / `confirmation` / `neutral` / `distractor` |
| `gold_letter` | The option letter carrying `gold_semantic` for this item |
| `design_gold_semantic` | The role the item was *designed* to have (bare→statement, ba→confirmation, ma→neutral) |
| `gold_shifted` | `True` if `gold_semantic` ≠ `design_gold_semantic` — always `False` in the confirmatory set; the 4 shifts live in exploratory |
| `margin` | The core3 vote lead for the gold label: `3` = 3:0 unanimous, `2` = 2:0 (one abstention), `1` = 2:1 majority |
| `stable_keep_all_pools` | `True` if the family stays KEEP under all four annotator pools (the conservative 11-family intersection, §5.3) |
| `collapse_pair`, `collapse_label` | *(exploratory only)* which two conditions' golds collapsed onto one label, and that shared label |

**`main_experiment/main_results.csv`** — one row per (item, model); the raw
trial. (`ablation/ablation_results.csv` has the identical schema minus
`timestamp`.)

| Column | Meaning |
|---|---|
| `set` | `confirmatory` / `exploratory` |
| `family_id`, `item_id`, `condition` | As above |
| `model` | Model name from `config/models.yaml` |
| `raw_response` | The model's raw text reply |
| `parsed_choice_letter` | The option letter parsed from it (`A`–`D`); empty on a refusal / parse failure |
| `parsed_choice_semantic` | That letter's semantic role, via `option_semantic_map` |
| `gold_letter`, `gold_semantic` | The item's gold, joined from the frozen data |
| `hit_gold` | `True` if `parsed_choice_semantic` == `gold_semantic` |
| `parse_failed` | `True` if no valid letter could be parsed (e.g. the model refused) |
| `timestamp` | *(main_results only)* when the call returned |

**`main_scoring/target_sentence_delta/prior_correction_by_model_condition.csv`**
— the table Finding 4 is read off (see §7 above for why it matters):

| Column | Meaning |
|---|---|
| `set` | `confirmatory` / `exploratory` |
| `model` | Model name |
| `condition` | `bare` / `ba` / `ma` |
| `group` | `prior_correct` (the ablation answer already equalled gold) or `prior_incorrect` (it did not) |
| `n_items` | Items in that group having *both* an ablation answer and a main answer — ablation refusals are excluded, which is why some `n_items` are below 20 |
| `accuracy` | That group's main-experiment accuracy (fraction hitting gold); blank when `n_items` = 0 |

---

## 8. Key findings

*(Condensed from `SFP_分析总结.md`, sections 1–6; its final "remaining
tasks" and appendix sections are about paper/poster writing and are
omitted here as no longer relevant.)*

**§0 — Why only 3 of the 5 annotators ("core3") are used as ground truth.**
Two of the five recruited native speakers were excluded before any
model-facing analysis:
- **"Econ" — excluded for response style.** The diagnostic found a
  *global* over-use of the "confirmation" label: only 66.7% self-consistency
  on bare items (the other three annotators: 94–97%) and only 25% on +ma
  items, while +ba looked completely normal (because +ba's gold answer is
  usually "confirmation" anyway, so this annotator's bias happened to line
  up with it there). One single bias explains all three conditions' numbers
  — this is a response-style issue, not "a different but valid reading."
- **"BWL" — excluded for suspected non-independent responding.** All 108
  naturalness ratings were a flat 5/5, zero hesitation marks, zero
  "no valid option" marks, and 94% agreement with the *original design*
  answer key (far higher than any other annotator) — consistent with the
  annotator not evaluating each item independently.

Importantly, dropping Econ increases the number of families with a clean
majority — but that alone is **not** evidence the item set "got better";
it's simply what happens when you remove one strong disagreeing vote. The
actual justification for treating the remaining 3 annotators
("core3": media studies, materials science, English literature
backgrounds) as ground truth is that they do not know one another and still
converge on ~72% pairwise agreement (chance level, picking among 4 options,
is 25%) — a property of the *data*, independent of which three people they
happen to be. Two of the three (Media, Materials) were recruited blind
through a public group chat; the third (EngLit) was recruited later and is
known to the author (see [§4](#4-item-construction-how-the-stimuli-were-built)
on recruitment), but does not know the other two, so the cross-annotator
convergence is still between people who could not have coordinated.

**Main result table** (6 models x 3 conditions, 60 confirmatory items):

| Model | Overall | bare | +ba | +ma |
|---|---|---|---|---|
| deepseek-r1-0528 | 90.0% | 95% | 100% | 75% |
| deepseek-v3 | 80.0% | 100% | **40%** | 100% |
| gemini-3-flash-preview | 81.7% | 90% | 100% | 55% |
| gemma-4-31b | 78.3% | 100% | 100% | **35%** |
| mistral-small-3-24b | 91.7% | 85% | 90% | 100% |
| qwen3-next-80b | 70.0% | 100% | 65% | 45% |

Accuracy ranges from 70–92% overall and 35–100% at the condition level —
neither a ceiling nor a floor, meaning the item set is discriminative
rather than trivially easy or impossibly hard.

**Human baseline** (core3, frozen confirmatory set):

| Condition | LOO (lower bound) | Concordance (primary comparison) |
|---|---|---|
| bare | 98.3% | 98.3% |
| +ba | 66.6% | 78.3% |
| +ma | 83.9% | 86.7% |

One striking mismatch: **native speakers disagree with each other most on
+ba** (lowest concordance), while **models struggle most with +ma**
(lowest accuracy). Humans and models find different conditions hard — that
mismatch is itself part of the story.

**How the five findings fit together.** The central claim — models track the
textbook function, native speakers track context — rests **directly** on two
findings: Finding 1 (what models do when the two readings disagree) and
Finding 2 (the direction in which +ma errors go). **A note on focus, since
both direct findings are stated in terms of +ma items even though the study
centers on 吧:** the whole force of Finding 2 is *where* the +ma errors go —
they land, without exception, on TENTATIVE (the 吧 reading) and never on
ASSERT. That is itself a result *about* 吧: it shows the model's 吧 is a
default reading strong enough to pull a neutral question (+ma) toward it. The
+ma condition is, in effect, the probe; the gravitational pull of 吧 is what
it measures. Findings 3–5 do not test the central claim directly; they
establish that the task is valid and identify the single mechanism (a
per-model default) behind the raw accuracy numbers. Note the difference in
weight between the two direct findings: Finding 2 is a confirmatory result
(20 items x 6 models), while Finding 1 is the most direct test but rests on
only 4 items from the exploratory set. Finding 1 is therefore read *together
with* Finding 2, not on its own.

**Finding 1 — models track the textbook function, not the context (the
main claim).** On the 4 exploratory items where native speakers' actual
reading of +ma drifted from "neutral" to "confirmation-seeking" in
context, models systematically fell back to the original *design* answer
(neutral) instead of following the context-driven human reading:

| Model | % choosing the original design label (of 4 items) |
|---|---|
| deepseek-r1 / deepseek-v3 | 100% |
| gemini / mistral | 75% |
| gemma / qwen | 50% |

In other words: **when a native speaker's contextual reading diverges from
a particle's textbook function, models follow the textbook, not the
speaker.** (n=4 — reported as a clean qualitative pattern, not a
statistic.)

**Finding 2 — +ma gets assimilated toward +ba, reversing the original
hypothesis (H4).** The confusion matrices are unambiguous about *where* +ma
errors go (the correct label for +ma is NEUTRAL): **for every model that
misreads any +ma item, 100% of those misreadings land on TENTATIVE — the
+ba reading — and none land on ASSERT or on the distractor.** Reading the
NEUTRAL row of the row-normalized confusion matrix, the split across
NEUTRAL / TENTATIVE / ASSERT is: gemma 35% / 65% / 0%, qwen 45% / 55% / 0%,
gemini 55% / 45% / 0%, deepseek-r1 75% / 25% / 0%. The two remaining models,
deepseek-v3 and mistral, make no +ma errors at all. So across all six models,
without exception, whenever +ma is misread it is misread as +ba, never as a
plain assertion.

> **Note on the denominator.** The percentages above are the share of *all*
> 20 +ma items read as TENTATIVE. Because the ASSERT and DISTRACTOR columns
> are exactly zero, that share coincides numerically with each model's +ma
> *error* rate (e.g. gemma's 35% +ma accuracy leaves 65% errors, all of them
> TENTATIVE). Stated as a fraction of errors, the figure is 100% for every
> model — the stronger and correct way to phrase it.

H4 predicted the opposite direction (+ba collapsing into +ma); the data show
the reverse. This
direction is **also what happens in the human data**: every one of the 6
naturally-collapsing families and all 4 gold-shifted items drift from
neutral toward confirmation-seeking, never the other way — a directional
finding that holds for both humans and models.

**Finding 3 — a single default-answer bias explains both a model's best
and worst condition.** Each model appears to have one preferred "default"
semantic label — the label its answers gravitate toward, read directly off
the rows of its main-experiment confusion matrix (§7,
`confusion_matrices/`), and corroborated by the answer it gives from context
alone in the ablation (its "prior", §5.5). Whichever condition's gold happens
to match that default, the model looks perfect on it; whichever doesn't, it
collapses:
- **gemma** defaults to TENTATIVE → 100% on +ba, 35% on +ma. The strong
  evidence is in the main experiment itself: gemma returns TENTATIVE on all
  20 +ba items *and* on 13 of the 20 +ma items whose gold is NEUTRAL — 33 of
  60 confirmatory answers are TENTATIVE regardless of the particle shown. (Its
  ablation prior points the same way but is observable on only 7 of 20 +ba
  items — the other 13 were refusals — so for gemma the confusion-matrix row
  bias, not the thin prior, is what carries the claim.)
- **deepseek-v3** defaults to NEUTRAL → 100% on +ma, 40% on +ba (the mirror
  image): its NEUTRAL row is perfect and its +ba errors leak toward NEUTRAL,
  and here the prior is robust too (observable on 19 items, already equal to
  gold on 17 of the 19 +ma items).
- **mistral** shows no strong default → balanced across all three
  conditions (85/90/100%), with almost no off-diagonal mass in its confusion
  matrix.

This is one underlying mechanism producing what look like two separate
patterns (a model's best score and its worst score). It also ties Finding 3
directly to Finding 2: gemma's 65% of +ma items answered TENTATIVE *are* the
+ma→+ba assimilation — the default and the error direction are one and the
same fact seen from two tables.

**Why this does not contradict Finding 1.** A natural objection: if models
were tracking a shared "textbook" function, why do their defaults differ
(gemma leans TENTATIVE, deepseek-v3 leans NEUTRAL)? Isn't that just an
arbitrary per-model label preference? The answer is that the two findings
describe two different situations, which must be kept apart:
- The **default** (Finding 3) is what a model falls back to on its own: seen
  most cleanly in the ablation, where the target sentence is *absent* and
  there is no particle to interpret, so the model can only return a house
  preference — and there is no reason those preferences should agree across
  models.
- The **textbook claim** (Finding 1) is about what a model does when a
  particle's *textbook* reading and a native speaker's *context-driven*
  reading point to different answers: there, models side with the textbook
  reading rather than the speaker's. That tendency is shared across models
  even when their defaults are not.

In short, differing defaults are a fact about each model's fallback, not a
counter-argument to the textbook claim.

**Finding 4 — most (but not all) of the perfect 100% scores are "already
knew," not "read the sentence."** Splitting each 100%-accuracy cell by
whether the ablation (no-sentence) answer already equalled gold reveals
very different stories:

| Cell | What's actually going on |
|---|---|
| gemini / +ba, 100% | 18 of 20 items were already correct without seeing the sentence; only 2 items are genuine correction cases |
| gemma / +ba, 100% | the ablation didn't answer at all on 13/20 items (refused); of the 7 comparable items, only 2 needed correcting |
| deepseek-v3 / +ma, 100% | 17 of 19 comparable items were already correct beforehand (the 20th had no ablation answer to compare against); 2 genuine correction cases |
| **deepseek-r1 / +ba, 100%** | **9 genuine correction cases, and all 9 were corrected successfully** |
| **mistral / +ma, 100%** | **10 genuine correction cases, and all 10 were corrected successfully** |

The main result table has **eight** 100% cells; the three not listed here are
the bare-condition 100%s (deepseek-v3, gemma, and qwen on bare), omitted
deliberately. Bare is at ceiling for nearly every model, and because no
*family's* context-only default is ASSERT (the 0% bare shortcut rate, §5.5),
a bare 100% is almost all "correction" cases — but trivial ones: showing a
plain declarative sentence makes ASSERT the obvious read, which is not the
subtle, particle-driven correction this table is about. They carry no
diagnostic weight for the "already knew vs. read the sentence" question here.

To be precise: on items where the prior guess already happens to equal
gold, this design **cannot tell** whether the model is truly reading the
sentence or simply got lucky on its default guess — that is a limitation of
the measurement, not evidence the model "doesn't understand" (it still
answered correctly). But deepseek-r1 and mistral's two cells above have
enough genuinely-uninformed items (n=9 and n=10) to say, with reasonable
confidence, that **the ability to use the target sentence to correct a
wrong prior does exist** — and that the task is measuring something real.

**Finding 5 — a validity check that also resets the chance baseline.** No
model ever chose the distractor option, on any item, in the main
experiment (the DISTRACTOR column of every confusion matrix is all zeros).
This means (a) the four answer options are functioning as intended — the
real competition is between the three semantic roles, not against an
obviously-wrong option — and (b) **the effective chance baseline is 33%,
not 25%**.

This reframes gemma's 35% on +ma — but carefully. Its *accuracy* sits at
chance, yet its *error structure* is the opposite of random. A model
guessing among the three live options would spread its answers roughly
33% / 33% / 33% over NEUTRAL / TENTATIVE / ASSERT; gemma instead answers
35% / 65% / 0%. So gemma is not guessing — it is applying a fixed TENTATIVE
prior that merely happens to yield a chance-level accuracy number.
"Accuracy at chance, error structure far from chance" is precisely the
signature of a standing prior (Finding 3), and is the opposite of what
genuine guessing would produce.

---

## 9. Limitations and future work

**The main limitation: each condition maps to a single fixed gold label.**
By design, +ba's gold is always TENTATIVE, +ma's is always NEUTRAL, and
bare's is always ASSERT. This means "prior correct" cases (Finding 4)
cannot be ruled out in principle: a model with a standing preference for
TENTATIVE would score perfectly on every +ba item without reading a single
target sentence. The concrete, data-driven fix for a follow-up study: vary
the gold label *within* a condition (e.g., include some +ba items whose
correct reading is not TENTATIVE), so a default-answer strategy can no
longer pass as competence.

**Other limitations:**
- **Small annotator pool (n=5).** Five annotators were already enough to
  surface one response-style outlier and one suspected-non-independent
  respondent, which shows the QC process works — but it also means any
  single outlier has an outsized effect on the result. A larger pool would
  dilute this, though the underlying tension (majority-vote-based
  exclusion is somewhat self-reinforcing) doesn't fully go away just by
  adding more annotators. One related degree of freedom is disclosed openly
  (see [§4](#4-item-construction-how-the-stimuli-were-built)): the fifth
  annotator was recruited reactively, after the first four responses had been
  seen, to replace the capacity lost to the exclusions — under the same
  pre-specified diagnostic and criteria, but a reactive addition nonetheless.
- **Text-only presentation is a harder format for +ba specifically.**
  Native-speaker concordance on +ba (78.3%) is markedly lower than on bare
  (98.3%), suggesting that without intonation or a real interactive
  exchange, the stance +ba conveys is intrinsically harder for humans to
  converge on in pure text. This is consistent with +ba's lower naturalness
  ratings seen already in the pilot phase, and with a separate particle,
  呢 (ne), being dropped from the study altogether after piloting for a
  related reason.
- **Residual API non-determinism.** Even at temperature 0, and on the paid
  serving tier (see [§11](#11-models-cost-and-reproducibility-notes)), one
  item (F12) was observed to receive two different answers to an identical
  prompt on separate calls — a minor but non-zero source of noise.

---

## 10. Evidence summary

| Conclusion | Supporting evidence |
|---|---|
| Models track the textbook function; native speakers track context | Finding 1 (design-gold following) + Finding 2 (the ma-to-ba assimilation direction matches humans) + near-ceiling bare accuracy everywhere (models can do the task; they specifically fail at context-driven reinterpretation) |
| A single per-model prior explains both high and low scores | Finding 3 (mirrored confusion patterns) + Finding 4 (correction-sample sizes) |
| The task is valid and measures a real capability | Finding 4 (deepseek-r1/mistral: n=9/10 genuine corrections, all correct) + Finding 5 (no model ever picks the distractor) + 0% shortcut rate in the bare-condition ablation |
| The dataset construction is principled, not fitted to the conclusion | All 60 confirmatory items have empirical gold identical to design gold (every shift is confined to the excluded/exploratory families) + the 4-pool sensitivity grid + all exclusion criteria were fixed before results were inspected |
| The annotator exclusions are justified, not arbitrary | Econ's condition-wise diagnostic + 8 of the 9 pool-unstable families are attributable to Econ specifically at the family level |

---

## 11. Models, cost, and reproducibility notes

The 6-model roster, exact OpenRouter model IDs, and per-model notes on why
each was chosen live in [`config/models.yaml`](config/models.yaml) — to
add, remove, or swap a model, edit that file; no code changes are needed.
In brief: three "Chinese-strong" models (deepseek-v3, deepseek-r1-0528,
qwen3-next-80b) and three general-purpose models (gemma-4-31b,
mistral-small-3-24b, gemini-3-flash-preview), all called through
OpenRouter's OpenAI-compatible API at `temperature=0`, all on OpenRouter's
paid tier (the free tiers for these models were retired mid-project; all
six were deliberately kept on the same — paid — serving tier so that a
weak result can't be explained away as "that model was rate-limited on the
free tier").

Both `src.ablation.query` and `src.main_experiment.query` are
**resumable**: they append one line per (item, model) to a `.jsonl`
checkpoint as soon as it succeeds, and a rerun only retries what's still
missing. A **cost guard** (`cost_guard.max_cost_usd` in `models.yaml`,
currently $3) estimates spend before every paid call and refuses to
continue once the running total would exceed it, so a bug or retry loop
cannot silently run up a large bill. A full 108-item x 6-model pass is
estimated at well under $1.

The commit that produced the two frozen CSVs is tagged `dataset-frozen-v1`;
see [`intermediate_outputs/frozen_dataset/freeze_report.md`](intermediate_outputs/frozen_dataset/freeze_report.md)
for the complete provenance chain from that tag forward.
