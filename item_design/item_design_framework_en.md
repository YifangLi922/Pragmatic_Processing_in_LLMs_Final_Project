# Item Design Framework for Mandarin Sentence-Final **吧**

**Project:** Pragmatic Processing in LLMs — Mandarin sentence-final particles  
**Purpose:** Short English-facing summary for dataset construction and repository documentation  
**Status:** Condensed from the full Chinese framework (`item_design_framework_zh.md`)

## 1. Core design principle

The experimental manipulation is the **sentence-final form**, not the sampling category. Each base proposition `P` is expanded into a three-condition family:

- **bare:** `P`
- **+吧:** `P + 吧`
- **+吗:** `P + 吗`

Within a family, the **context, propositional content, question, answer-option semantics, and option order are held constant** as far as possible. The intended contrast is therefore local: the sentence-final form changes, while the rest of the item remains fixed.

Before constructing a context, candidate propositions are screened for strong **epistemic-access / authority asymmetries**. A proposition is avoided if the speaker or recipient would naturally have such privileged knowledge of `P` that one of the three conditions becomes pragmatically anomalous. Contexts should license the topic without supplying decisive evidence for `P`, making either participant obviously epistemically dominant, or presupposing that the recipient already knows the answer.

The interaction grid and proposition classes below are **researcher-defined sampling and construction heuristics**. They are not linguistic categories or confirmatory experimental factors.

## 2. Interaction setting: 2 × 2 sampling grid

Items are sampled along two descriptive dimensions: **channel** and **interaction relation**.

| | Personal / peer-oriented | Role-based / institutional |
|---|---|---|
| **Offline** | friends talking face-to-face, family conversation, classmates discussing in person | classroom or office interaction, institutional exchange, in-person service encounter |
| **Online** | group chats, private messages, social-media interaction | course/work groups, institutional platforms, online support |

**Channel** is normally established by the context rather than by the target sentence itself. Online items do not need internet slang, emoji, or exaggerated punctuation. Likewise, **role-based does not mean service-counter by default**: institutional settings with shared or publicly accessible information are preferred when a service encounter would introduce a strong knowledge asymmetry.

## 3. Four proposition construction classes

The four classes are used to diversify semantic content and surface form across families.

| Class | Description | Typical examples |
|---|---|---|
| **1. Identity / classification** | identity, role, category, ownership/affiliation, naming | `王老师是这个项目的负责人` “Professor Wang is in charge of this project”; `这个账号是小林的` “This account belongs to Xiaolin” |
| **2. External state / result** | observable or checkable states, quantities, locations, availability, processes, outcomes | `文件在共享盘里` “The file is on the shared drive”; `系统现在在维护` “The system is under maintenance” |
| **3. Person-related state / experience** | past experience, residence/location, familiarity, possession, preference, ability, current activity or schedule | `小林住这附近` “Xiaolin lives nearby”; `小张最近在准备考试` “Xiaozhang has been preparing for an exam recently” |
| **4. Future / expected event** | scheduled, planned, expected, or otherwise grounded future events | `会议三点开始` “The meeting starts at three”; `电影周五上映` “The movie opens on Friday” |

These classes should not become templates that are mechanically tied to person, setting, or syntax. In particular, avoid systematic correlations such as personal contexts always using second-person subjects, external-state items always using `已经……了`, or future items repeatedly using explicit epistemic markers such as `应该`, `可能`, `大概`, `也许`, or `好像`.

## 4. Construction priorities

When design goals conflict, use the following ordering:

> **contrast quality > naturalness > coverage/diversity > numerical balance**

A clean `P / P吧 / P吗` contrast is more important than filling every cell of the sampling grid. Naturalness is more important than maximizing formal coverage. Coverage should prevent obvious dataset artifacts, but no family should be retained merely to make counts perfectly balanced.

In practice, select a candidate `P` first, check that all three forms are natural and yield the intended stance contrast, and only then assign it to an interaction cell and proposition class. Do not start from an empty grid cell and force a weak proposition into it.

## 5. Worked family example

**Sampling metadata**

- Channel: **online**
- Relation: **personal / peer-oriented**
- Proposition class: **future / expected event**
- Base proposition `P`: `电影周五上映` (“The movie opens on Friday”)

**Neutral context**

> A few friends are discussing in a group chat which movie to see over the weekend. Xiaolin then sends one message.

The context introduces the topic and marks the interaction as online, but it does not state whether Xiaolin has checked the release date, whether another participant has privileged knowledge, or whether the answer is already known.

**Three conditions**

```text
bare: 电影周五上映
+吧: 电影周五上映吧
+吗: 电影周五上映吗
```

**Shared question**

> Which option best describes the speaker's stance toward the proposition that the movie opens on Friday?

**Shared answer-option semantics**

- **A. Statement:** the speaker presents `P` relatively confidently as information.
- **B. Confirmation-seeking / tentative assertion:** the speaker leans toward `P` but is not fully committed and seeks confirmation.
- **C. Neutral question:** the speaker asks whether `P` is true without a clear prior commitment.
- **D. Distractor:** another social action not represented by the three target readings.

**Gold mapping:** bare → A; +吧 → B; +吗 → C. The question, options, and option order remain identical across the three items.

## 6. Full framework

This document intentionally omits the detailed risk table, surface-pattern metadata, global de-correlation checklist, pilot coverage scheme, item-by-item construction workflow, and literature discussion. For those details—and for the rationale behind epistemic-authority screening and context neutrality—refer to the full Chinese framework:

> **`item_design_framework_zh.md`**

The short version should therefore be read as a repository-facing summary of the construction logic, not as a replacement for the full internal design guide.
