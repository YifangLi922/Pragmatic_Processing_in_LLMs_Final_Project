# SFP-吧 项目开发说明书（Handoff for Claude Code）

> **文档用途**：这是一份交给 Claude Code 的项目说明书。它总结了本项目已完成的工作、数据格式、接下来要写的代码模块及其规格、以及分析流程的判断规则。Claude Code 读完本文件后，应能理解项目全貌并按需分模块编写代码。
>
> **阅读顺序建议**：先读第 1–2 节了解项目和现状，再读第 4 节（数据格式）和第 5 节（代码模块规格），这两节是写代码的直接依据。第 3、6 节是分析流程的判断规则，实现模块 2/3/5 时需要严格遵守。
>
> **语言说明**：题目材料、标注结果为中文；代码、变量名、注释用英文即可。

---

## 1. 项目一句话概述

构建一个小而受控的普通话评测集，通过同一命题 P 的 **裸句 / +吧 / +吗** 三条件对比，测试大语言模型（LLM）是否对句末语气词"吧"所贡献的说话人立场表现出**系统性的对比敏感度（contrastive sensitivity）**，并比较不同模型家族之间的差异。

- **实验真正操纵的变量**：particle condition（bare / +吧 / +吗），在每个 family 内部严格受控。
- **核心指标**：condition accuracy、pair success、family success、confusion matrix，以及（若模型支持）logprob shift。
- **人类基线**：用 leave-one-annotator-out（LOO）在标注员上近似 human ceiling。

> 术语约定：一个 **family** = 同一个命题 P 的三个条件（bare/吧/吗）三道题。36 个 family = 108 道题。

---

## 2. 目前已完成的工作

### 2.1 设计与材料

- 已完成 project plan（v3）与"吧"类题目构造框架（v0.3），确立了三条核心设计原则：
  1. **family 内只改句末形式**（不改词汇、结构、标点；目标句一律不带句末标点）。
  2. **epistemic-authority 筛选**：造题前先排除说话人或听话人对 P 天然拥有压倒性知识权威的命题。
  3. **context neutrality + 当场不可核实性**：语境只负责"让话题自然出现"，不提供 P 的直接证据、不预设任一方已知答案；且命题应是"当场看一眼/点一下无法直接核实"的（关于第三方、别处、之前/之后的事），使"问对方"成为解决不确定性的自然方式。

- 已构造 **36 个 family（108 道题）**，覆盖一个 2×2×4 的取样框架（sampling scaffold，**非实验变量**）：
  - Channel：online / offline
  - Interaction relation：personal-peer / role-based
  - Proposition class：identity / external-state / person-state / future-event

- 每道题包含：情景（context）、句子（sentence，含 particle）、问题（question）、4 个选项（A–D）。
- 四个选项对应的语义骨架固定为：
  - **statement**：说话人比较确定 P，是在告诉对方
  - **confirmation-seeking**：说话人倾向 P，但不完全确定，希望对方确认
  - **neutral-question**：说话人只是在询问 P，没有明显倾向
  - **distractor**：一个与三档正交的社会行动（建议/提议/惊讶/请求等）

### 2.2 已完成的 pilot（1 名母语者）

- 对最初 10 个 family（30 题）做了单人母语者标注，产出了标注结果与分析。
- 关键发现：
  - +吧 的自然度系统性偏低（纯文本范式对"吧"存在固有劣势，需在正式阶段按 condition 分别报告自然度）。
  - family 级"干净率"低于题目级一致率（因为主指标吃的是 family，不是单题）。
  - 六个问题 family 的共同病因是"语境越界"（提供了证据 / 说话人权威过高 / 暗示听话人已知 / 命题当场可核实），据此修订了材料。
  - "吗"未必是绝对中性问句：文献支持"吗"允许弱 epistemic bias，真正强制中性的是正反问（A-not-A）。因此选项措辞"没有明显倾向"属于**偏严**而非错误；正式阶段 **gold 改由母语者多数票决定**，而非设计者预设。

### 2.3 关于"呢"（重要背景，影响不到代码）

- 原计划测"吧"和"呢"两个语气词。"呢"经 context-only ablation 发现语境会直接泄露答案（partial-input shortcut），因此**"呢"退出主实验**，只作为方法学 limitation 保留。
- 当前主实验**只测"吧"**（bare/吧/吗 三条件对比）。

### 2.4 当前进行中

- 已在大学群聊中**付费招募 4 名不同专业的普通话母语者**进行独立标注，标注**尚未完成**。
- 标注表包含 4 个维度：**选答案（A–D）**、**自然度评分（1–5）**、**是否在选项间犹豫（有则填理由）**、**是否认为没有正确选项（有则标注）**。
- 题目和选项顺序在发放前会打乱（family 内三题不相邻、family 间做 option-order counterbalancing）。设计者自己保留一张"乱序题号 ↔ family/condition/预期 gold"的**母题对照表**（不给标注员看）。

---

## 3. 接下来要做的事（分析流程总览）

拿到 4 名标注员的结果后，按以下顺序处理。**数据集在第 4 步结束后冻结，之后才能喂给模型。**

| 步骤 | 做什么 | 关键产物 |
|---|---|---|
| 0 | 读取 + 还原 + 质量清洗 | 结构化标注数据 |
| 1 | 多数票定 gold | 每题 gold + 共识强度 |
| 2 | family 级剔除 | 保留 family 列表 + 剔除原因统计 |
| 3 | 一致度（Fleiss' κ 等） | 数据集质量指标 |
| 4 | LOO human baseline（分 condition） | 人类基线（总 + 三档） |
| — | **数据集冻结** | 正式测试集 |
| 5 | 跑 LLM → 打分 → 指标 | 各模型成绩单 |
| 6 | 统计检验 + 出图 | 报告用图表 |

判断规则（gold 定义、family 剔除、LOO）见第 6 节，实现时必须严格遵守。

---

## 4. 数据格式规格（写代码的直接依据）

> 以下 schema 供 Claude Code 设计数据读取和内部数据结构。真实列名可能在拿到标注表后微调，但结构不变。字段命名用英文。

### 4.1 母题对照表（设计者持有，item metadata）

每道题一行，108 行。这是把乱序标注还原成 family 结构的关键。

```
family_id            # 如 F01 ... F36
item_id              # 如 F01_bare / F01_ba / F01_ma
particle_condition   # bare / ba / ma
shuffled_index       # 发给标注员时的乱序题号（用于还原）
context
sentence
question
option_A             # 选项 A 的文本
option_B
option_C
option_D
option_order         # 记录本题四个选项的排列（用于还原语义↔字母映射）
gold_semantic_designed   # 设计者预期语义：statement / confirmation / neutral / distractor
gold_letter_designed     # 设计者预期字母（仅供参考，非最终 gold）
# sampling metadata（非实验变量，仅供 de-correlation 检查）
channel              # online / offline
interaction_relation # personal_peer / role_based
proposition_class    # identity / external_state / person_state / future_event
subject_type         # human_2p / human_3p / proper_name / nonhuman_np / other
surface_pattern
```

> **关键**：每道题的四个选项文本里，"哪个字母对应哪个语义骨架"是随 option_order 变化的。分析时要能从字母还原到语义（statement/confirmation/neutral/distractor），因为跨 family 比较的是**语义**不是字母。

### 4.2 标注员原始答题表（4 份，或合并成 1 份）

每个标注员对每道题一行：

```
annotator_id         # A1 / A2 / A3 / A4
shuffled_index       # 对应母题对照表
answer_letter        # 该标注员选的 A/B/C/D
naturalness          # 1–5
hesitation           # 是否犹豫：0/1 或 空/有
hesitation_reason    # 文本，可空
no_valid_option      # 是否认为无正确选项：0/1 或 空/有
```

### 4.3 还原后的内部结构（模块 1 的输出）

建议还原成"每题一条记录，聚合 4 名标注员"的结构，例如每道题：

```
item_id, family_id, particle_condition,
context, sentence, question, options{A,B,C,D},
option_semantics{A:..., B:..., C:..., D:...},   # 字母→语义映射
annotations: [
   {annotator_id, answer_letter, answer_semantic, naturalness, hesitation, no_valid_option},
   ... x4
]
```

`answer_semantic` = 把 answer_letter 通过 option_semantics 翻译成语义骨架，**后续所有一致度/gold/baseline 都建议在语义层面算**，避免被 option_order 干扰。

### 4.4 模型结果表（模块 4 的输出）

```
model_name
model_provider
model_group          # 描述性分组，如 chinese_strong / general
run_date
temperature
prompt_variant       # main / robustness_1 / ...
item_id
model_answer_letter
model_answer_semantic
correct              # 0/1，与 gold_semantic 比
logprob_A            # 若可得
logprob_B
logprob_C
logprob_D
raw_response
```

---

## 5. 代码模块规格

> 建议切成 6 个职责单一的模块，模块之间通过**落盘的中间文件**传递数据（不要一个大脚本跑到底）。每个模块跑完存一份结果文件，任何一步出错只重跑那一步。特别是模块 4 调 API 花钱又花时间，结果必须落盘、支持断点续跑。

### 依赖关系

```
模块1 (数据地基)
 ├─> 模块2 (gold + 剔除) ──┐
 ├─> 模块3 (一致度 + LOO) ─┤
 └─> 模块4 (LLM 调用) ─────┤
                           ├─> 模块5 (打分 + 指标) ─> 模块6 (统计 + 出图)
        模块2 ─────────────┘                          模块3 ─┘
```

### 现在就能写（等数据期间）

- **模块 4（LLM 调用）**：最优先。用 5 道手写假题跑通"读题→拼 prompt→调 API→解析字母→落盘"，把限流/返回格式/logprob 有无等坑先踩平。
- **模块 2、模块 3**：用一张**假标注表**（4 标注员 × 108 题随便填 ABCD）把逻辑写通并测试。
- **模块 1**：框架可搭（格式已知），等真表来微调列名。

### 必须等数据

- 只有"基于真实标注做出的决策结果"（哪些 family 被剔、gold 具体值、baseline 数值）要等。做这些决策的**代码**现在就能写好。

---

### 模块 1：数据读取与还原

**职责**：读 4 份标注表 + 母题对照表，还原成 4.3 的结构；做质量清洗。

**要实现**：
- 读入母题对照表和标注表（CSV/Excel 皆可）。
- 用 `shuffled_index` 把标注还原到 item/family/condition。
- 建立 `answer_letter → answer_semantic` 的映射（依据 option_order / option_semantics）。
- **质量检查**（输出一份 quality report）：
  - 每个标注员是否整体几乎只选某一个字母（划水信号，如某字母占比 > 某阈值如 70%）。
  - 是否有漏答、无效值。
  - 若设置了练手题，检查练手题正确率。
  - 标注耗时（如有记录）。
- 输出：统一的结构化数据文件 + quality report。

---

### 模块 2：gold 定义 + family 剔除

**职责**：定 gold，做 family 级剔除，决定"哪些题进入正式测试集"。

**要实现**：
- **多数票定 gold**（在**语义**层面，见第 6.1 节规则）：对每题聚合 4 名标注员的 `answer_semantic`，取多数，同时记录共识强度（4:0 / 3:1 / 2:2 / 2:1:1）。
- **family 级剔除**（见第 6.2 节规则）：逐 family 检查三档 gold 是否互不相同、共识是否够强、自然度是否达标；不合格整组剔除。
- 按剔除原因分类统计（撞 gold / 高分歧 / 自然度低 / 其他）。
- 输出：`gold.csv`（每题最终 gold_semantic + 共识强度）、`retained_families.csv`（保留列表）、`exclusion_report`（剔除原因统计）。

---

### 模块 3：一致度 + LOO human baseline

**职责**：计算数据集质量指标和人类基线。

**要实现**：
- **Fleiss' κ**（4 标注员、四类别，在语义层面）。可在"全部题"和"保留题"上各算一份。
- **hesitation rate**、**no-valid-option rate**、自然度分布（**必须按 condition 分别报告**：bare / 吧 / 吗 各一套）。
- **LOO human baseline**（见第 6.3 节规则，4 人版本）：
  - 轮流留出 1 名标注员，用其余 3 人的多数票当该轮 gold，算被留出者的正确率；4 轮取平均。
  - **必须分 condition 算**：总 baseline + bare / 吧 / 吗 各一个。
  - 某轮里"其余 3 人无多数"的题，该轮跳过（不计入该轮分母）。
- 输出：`agreement_metrics`（κ、各 rate、自然度分布）、`human_baseline`（总 + 三档）。

---

### 模块 4：LLM 调用（现在就写）

**职责**：给一批题，逐题调模型，解析答案，落盘。

**要实现**：
- **prompt 构造函数**：输入一道题字段，输出 prompt 字符串。主模板（已定）：
  ```
  阅读下面的对话情景，判断说话人的态度，只输出选项字母。

  情景：{context}
  句子："{sentence}"
  问题：{question}

  选项：
  A) {opt_a}
  B) {opt_b}
  C) {opt_c}
  D) {opt_d}

  答案：
  ```
- **API 调用**：支持多个模型 / provider；固定 decoding 配置（如 temperature=0）；记录 exact model identifier、provider、run date、参数。
- **答案解析函数**：从模型原始回复中稳健解析出 A/B/C/D（处理"我选 A"、"A)"、含解释的啰嗦回复等情况）；解析失败要记录而非崩溃。
- **logprob**：若该模型 API 支持，记录四个选项字母的 logprob / 归一化概率；不支持则留空，不影响主流程。
- **鲁棒性**：重试、限流处理（退避）、**逐题落盘 + 断点续跑**（跑一半中断能续，不重复消耗额度）。
- **prompt robustness**（可选）：支持用 1–2 个改写模板对小 subset 重跑（prompt_variant 字段）。
- **现阶段只用免费模型**。
- 建议先用 5 道手写假题跑通最小闭环，再批量。
- 输出：4.4 的模型结果表（每模型一份或合并）。

---

### 模块 5：打分 + 指标

**职责**：对比模型答案与 gold，算所有核心指标。

**要实现**（在语义层面对比，见第 6 节）：
- **correct**：model_answer_semantic 是否等于该题 gold_semantic。
- **condition accuracy**：每模型 × 每 condition（bare/吧/吗）的准确率 + overall + 95% CI。
- **pair success**：同一 family 内两档都答对才算成功；分别算 bare↔吧、吧↔吗、bare↔吗。
- **family success**：一个 family 三档全对才算成功。
- **confusion matrix**：每 condition 下，模型把它读成了哪个语义（重点看 +吧→neutral(吗读法)、+吧→statement、+吗→confirmation 等）。
- （若有 logprob）**logprob shift**：bare→吧→吗 是否形成预期的概率轮廓。
- 输出：各模型成绩单（各项指标）。

> chance 参照（四选一独立均匀猜测的理想化值，仅作直觉参照）：单题 0.25、pair success 0.0625、family success 0.015625。

---

### 模块 6：统计检验 + 出图

**职责**：inferential statistics 和报告用图。

**要实现**：
- **McNemar test**：对每个模型，在同一批 family 上比较 bare vs 吧、吧 vs 吗、bare vs 吗 的 paired binary accuracy。
- **mixed-effects logistic regression**（主/补充）：
  ```
  correct ~ condition * model_or_model_group + (1 | family_id)
  ```
  数据量/收敛允许时可考虑 condition 的 family-level random slope。
- **图**：confusion-matrix 热图、condition-wise accuracy / family success 图、model-family 比较图；模型 vs human baseline 对照。
- 输出：图表文件 + 统计结果。

> 对课程项目：先完成 descriptive + paired tests，mixed-effects 作为更完整的 inferential analysis；不要为了"高级统计"牺牲可解释性。

---

## 6. 关键判断规则（模块 2/3/5 必须遵守）

### 6.1 gold 定义

- **gold = 4 名母语者的多数票**（在语义骨架层面：statement / confirmation / neutral / distractor），**不是**设计者预期。
- 共识强度分级并记录：
  - 4:0 或 3:1 → 多数即 gold（共识强）。
  - 2:1:1 → 2 票者暂定 gold，但标记为**弱共识**。
  - 2:2 → **无多数，gold 悬空**，标记为**高分歧题**。

### 6.2 family 级剔除规则

一个 family 要进入正式测试集，必须同时满足：

1. **三档 gold 互不相同**（bare/吧/吗 分别落在三个不同语义上）。若任意两档 gold 撞成同一个 → 该语境撑不起三分对比 → **整组剔除**。
2. **各档共识足够强**（不含 2:2 悬空档；弱共识档视整体保留率决定是否放宽）。
3. **自然度达标**（如某档自然度均分低于阈值，例如 < 4.0 → 触发剔除；阈值可配置）。

> 剔除是 **family-wise**：一个 family 的任一条件不合格，整个 family 不进入 confirmatory gold set，因为核心推断依赖完整三条件对比。剔除原因要分类统计，本身是报告数据。

### 6.3 LOO human baseline（4 人版）

目的：得到一个不含"自己给自己打分"虚高的人类基线，作为评判模型的标尺。

步骤：
1. 留出 1 名标注员。
2. 用其余 3 人的**多数票**作为该轮临时 gold（某题若其余 3 人无多数，该题该轮跳过）。
3. 计算被留出者相对该临时 gold 的正确率。
4. 4 名标注员轮流各留出一次，共 4 轮。
5. 取 4 轮平均 = human baseline。
6. **分 condition 各算一遍**（总 + bare + 吧 + 吗）。

报告时注明：这是课程项目条件下的近似 human ceiling；更严格的做法是另招一组独立母语者当考生。

---

## 7. 冻结数据集之后才做的事 + 收尾

- **数据集冻结点**：模块 2、3 跑完、保留 family 列表和 human baseline 确定后，数据集不再改动，然后才跑模型（模块 4→5→6）。
- **de-correlation sanity check**（可在冻结后做）：检查保留下来的 family 是否在 sampling metadata 上过度集中（例如 role-based 是否几乎全是职场场景、某 surface_pattern 是否占比过高）。仅用于 sanity check 和 discussion，不进主统计。
- **交付要求**（来自课程）：代码要有注释、有 README 说明各文件用途、如何运行、如何解读输出。计划公开 gold dataset、construction metadata、prompt templates、annotation guideline、evaluation code、model outputs（若 provider policy 允许）。

---

## 8. 给 Claude Code 的落地建议

1. **先做模块 4 的 API 最小闭环**（5 道假题），这是唯一有外部不确定性的部分。
2. 用**假标注表**把模块 2、3 的逻辑写通并单元测试。
3. 所有中间结果**落盘成文件**；模块 4 必须支持断点续跑。
4. 所有一致度 / gold / 打分**在语义层面**进行（先把字母映射成 statement/confirmation/neutral/distractor），避免 option_order 干扰。
5. 阈值（自然度下限、划水判定比例等）写成**可配置参数**，别硬编码。
6. 每个模块产出一份清晰的结果文件 + 简短日志，方便写 README 和复现。
