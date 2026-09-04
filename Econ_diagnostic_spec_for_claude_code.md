# Annotator Condition-wise Diagnostic — 实现规格（for Claude Code）

> **这是一份实现规格，不是教学文档。** 目标：写一个可复用的诊断脚本，比较任一 target annotator 与一个 reference annotator pool 在 bare / +吧 / +吗 三个条件上的一致结构。首要用例是诊断 Econ，但代码必须对四个人都能跑。
>
> **实现前先做一件事**：读完本文档后，先输出一份"输入契约 + 输出文件 + 每个指标的精确定义 + 边界情况"的压缩确认清单，等我确认后再写代码。不要直接开始写。
>
> **语言**：代码、变量名、注释用英文；本规格为中文。

---

## 0. 这一步在整个项目中的定位

- 这是 **annotator-level QC / interpretation 诊断**，不是最终 dataset analysis。
- 本步骤**不自动删除任何 annotator**，**不决定 family inclusion**，**不做显著性检验**，**不看 LLM 结果**。
- 输出是描述性的：一组表 + 混淆矩阵，用来判断某个 annotator 与 reference pool 的分歧是 **condition-specific 且 directional**、还是 **diffuse low agreement**。

---

## 1. 核心设计：必须参数化，不要硬编码任何人

函数签名的核心是两个参数：

```
run_diagnostic(target_annotator, reference_pool, no_option_mode)
```

- `target_annotator`：被诊断的人（如 "Econ"）。
- `reference_pool`：用来构造多数票参照的人的列表（如 ["Media", "Materials", "EngLit"]）。
- `no_option_mode`：`"A"` 或 `"B"`（见第 5 节）。

**不要把 Econ 写死进逻辑。** 同一份代码必须能跑下面全部组合（见第 8 节的 driver）。

---

## 2. 必须对四个人都跑一遍（这是本次最重要的修改）

不能只算 Econ。要对 **Econ / Media / Materials / EngLit** 每个人各跑一次 leave-one-out：

- 留出的人 = `target_annotator`
- 其余三人 = `reference_pool`

**理由（写进代码注释即可）**：Econ 在某条件上的 agreement 数字，只有和其他三人在同一条件上的 agreement 放在一起才有意义。若"吗"条件对所有人都低，则低是条件属性而非 Econ 属性；若只有 Econ 低，才是 Econ 的 condition-specific divergence。这一步同时产出分 condition 的 LOO baseline，与后续分析共用，不要重复实现。

**已知的不对称，写进输出说明**：Econ 被留出时 reference 是互相高度一致的 core-3；Media/Materials/EngLit 被留出时 reference 含 Econ，噪声更大，其分数会被压低。此不对称对 Econ 有利（抬高对照、压低自己），因此若 Econ 在此条件下仍明显更低，结论更稳健。**不要去"修正"这个不对称，只需在输出的 README/日志里注明。**

**BWL 不进入本步骤的任何 reference_pool，也不作为 target 跑。** 理由：对 BWL 的 concern 是 response-process quality（是否独立逐题判断），这类问题无法用与他人的 agreement 来诊断，且其存疑来源会污染用于诊断 Econ 的参照。BWL 在后续 pool-sensitivity 分析中作为 stress test 处理，不在本脚本范围内。

---

## 3. 输入数据契约

- 分析单位：**全部 36 families / 108 items**，不要预先只取 20 个 three-way candidate（否则诊断被 family selection 条件化）。
- **必须在 semantic label 层面比较，不能比较 A/B/C/D**（不同 family 的 option order 不同）。
- 语义标签固定四类：`ASSERT` / `TENTATIVE` / `NEUTRAL` / `DISTRACTOR`。
- **语义映射必须复用模块 1 已有的 letter→semantic 映射逻辑，不要在本脚本重新实现。** 两套映射一旦分叉会产生对不上的数字且极难排查。

每道题每个 annotator 需要以下字段（若模块 1 输出里没有，需先补齐）：

```
item_id
family_id
condition            # bare / ba / ma
annotator
semantic_choice      # ASSERT/TENTATIVE/NEUTRAL/DISTRACTOR，或 None（真的没选）
no_option_flag       # True / False
naturalness          # 1–5，或 None
hesitation_flag      # True / False
```

---

## 4. no-option 的双字段规则（已确认的真实数据情况）

真实数据里 no-option 有两种人，靠 `semantic_choice` 是否为空区分，**不是靠 flag**：

- **真弃权**：`no_option_flag=True` 且 `semantic_choice=None`（本项目中 Materials 属此类）。→ 该题该人一律计为 abstention，**不进任何多数票分母**，A/B 两种模式下都一样。
- **勾了但仍给了选择**：`no_option_flag=True` 且 `semantic_choice≠None`（本项目中 EngLit 属此类）。→ 是否计票取决于 `no_option_mode`（见第 5 节）。

普通作答：`no_option_flag=False` 且 `semantic_choice≠None`，正常计票。

---

## 5. 两个 no-option variant

只作用于"勾了 flag 但仍给了选择"的题（本项目实际只影响 EngLit 的一小批题）：

- **Variant A（primary，默认）**：用其实际 `semantic_choice` 计票。理由：尊重其明确选择、保留更多数据。
- **Variant B（robustness）**：将其也计为 abstention，不计票。

**两个 variant 都要跑并各自输出一套结果。** 若两者的 condition-wise pattern 与 dominant direction 基本不变，则结论对 no-option 处理稳健。**A 是主结果，B 是稳健性检查——这个主/辅关系现在就固定，不得看完结果再改。**

---

## 6. 每个 item 的处理流程

对给定的 `(target_annotator, reference_pool, no_option_mode)`：

1. 取 reference_pool 三人在该 item 的 `semantic_choice`，按第 4/5 节规则决定每人是否计票。
2. 在计票的 reference 成员中求多数：
   - 有 2/3 或 3/3 多数 → `reference_label` = 该多数标签，`reference_valid = True`。
   - 1–1–1，或计票人数不足以形成多数（如两人弃权）→ `reference_label = None`，`reference_valid = False`。
3. 若 `reference_valid = True` 且 target 在该题有 `semantic_choice`：
   - `agree = (target_choice == reference_label)`
   - 该 item 进入 agreement 分母与 confusion matrix。
4. 若 `reference_valid = False`：该 item **不进** agreement 分母、**不进** confusion matrix，但**必须计入 coverage 统计**。

---

## 7. 要计算和输出的指标

### 7.1 Condition-wise agreement + coverage（每人每条件）

对 bare / ba / ma 分别：

```
total_n            # 该条件总 item 数（36）
reference_n        # 该条件中 reference_valid=True 的 item 数
coverage           # reference_n / total_n
agreement_n        # target 与 reference_label 相同的数
agreement_rate     # agreement_n / reference_n   （分母是 reference_n，不是 total_n）
```

**coverage 必须和 agreement 一起报。** 分母永远是 reference_n。

### 7.2 Reference-label 边际分布（每人每条件，默认必报，不是可选）

对每个条件，输出 reference_pool 多数票落在各标签的计数：

```
condition | ASSERT | TENTATIVE | NEUTRAL | DISTRACTOR | (reference_valid 总数)
```

**为什么必报**：某条件（尤其 ma）的 reference 可能压倒性集中在单一标签（如 NEUTRAL）。此时"dominant disagreement 高度定向"在结构上是被迫的（除该标签外几乎没有其他行可产生方向）。不看边际分布会高估方向集中度。凡解读 dominant direction，必须同时呈现这张表。

### 7.3 Confusion matrix（每人每条件 + overall）

- **rows = reference_pool majority label；columns = target response。**
- 标签顺序固定：`ASSERT, TENTATIVE, NEUTRAL, DISTRACTOR`。
- 对角线 = agreement；非对角线 = 分歧方向。
- 每条件一张（bare / ba / ma），另加一张 overall。
- 每张矩阵**同时输出 raw counts 和 row-normalized 两个版本**（row-normalized = 每格 / 该行总数；小样本下 raw 更重要，不要只给百分比）。

### 7.4 Disagreement direction 统计

对每个非对角线方向 `REF_LABEL → TARGET_LABEL`，计算两个比例，**两者含义不同，不要混用**：

```
share_among_disagreements = 该方向计数 / 该条件全部 disagreement 数
within_reference_rate      = 该方向计数 / 该条件中该 REF_LABEL 的 item 总数
```

- 前者答"分歧是否集中在一个方向"；后者答"当 reference 给某标签时，target 多常改判成另一标签"。

### 7.5 最小解读门槛（现在就固定，防止事后放宽）

**任何单个 off-diagonal cell 的计数 < 8 的，只输出数字，不做定性解读。** 在输出里对低于门槛的 cell 加标记（如 `low_n=True`）。此门槛写死为常量，不依赖看到的数据。

---

## 8. Driver：一次跑完所有组合

主 driver 循环：

```
targets = ["Econ", "Media", "Materials", "EngLit"]
for target in targets:
    reference_pool = [x for x in targets if x != target]   # 留一，其余三人；BWL 永不入列
    for mode in ["A", "B"]:
        run_diagnostic(target, reference_pool, mode)
```

= 4 人 × 2 variant = 8 次运行。

**核心汇总表（最重要的产物）**：把四个人的 condition-wise agreement 拼成一张对照表，这样才能一眼看出"是否只有 Econ 在某条件上异常低"：

| annotator | mode | bare_cov | bare_agr | ba_cov | ba_agr | ma_cov | ma_agr |
|---|---|---|---|---|---|---|---|

---

## 9. 输出文件

```
# 汇总（跨 4 人对照，最重要）
diagnostic_summary_all_annotators.csv      # 第 8 节汇总表，含 A/B 两 mode

# 每人一套（{ann} ∈ econ/media/materials/englit，{mode} ∈ A/B）
{ann}_condition_summary_{mode}.csv         # 7.1
{ann}_reference_marginals_{mode}.csv       # 7.2
{ann}_item_level_{mode}.csv                # 第 10 节
{ann}_disagreement_directions_{mode}.csv   # 7.4，含 low_n 标记

{ann}_confusion_bare_counts_{mode}.csv
{ann}_confusion_ba_counts_{mode}.csv
{ann}_confusion_ma_counts_{mode}.csv
{ann}_confusion_overall_counts_{mode}.csv
{ann}_confusion_bare_rownorm_{mode}.csv
{ann}_confusion_ba_rownorm_{mode}.csv
{ann}_confusion_ma_rownorm_{mode}.csv
{ann}_confusion_overall_rownorm_{mode}.csv

# 图（每条件一张 heatmap，raw counts；四人可选，Econ 必出）
{ann}_confusion_{bare,ba,ma,overall}_{mode}.png
```

---

## 10. Item-level 表字段（每行一题一人的诊断记录）

**必须包含 naturalness 和 hesitation 两列**（这是本次新增，用来区分"题本身模糊"还是"target 有稳定的独特判断"）：

```
family_id
item_id
condition

# reference pool 三人
ref1_semantic, ref2_semantic, ref3_semantic   # 用实际 pool 成员名
reference_label
reference_valid

# target
target_semantic
agree
disagreement_direction        # "REF→TARGET"，agree 时留空

# 供 qualitative 追查
target_naturalness            # target 在该题打的自然度
target_hesitation             # target 在该题是否标犹豫
target_no_option_flag
ref1_no_option_flag, ref2_no_option_flag, ref3_no_option_flag
```

**用途**：当某个 dominant confusion 出现时，可回到具体 items 检查——若这些分歧题 target 多为低自然度 / 标了犹豫 → 题本身模糊；若多为自然度 5 分 / 无犹豫 → target 有稳定的不同解读。两种情况正文写法相反。

---

## 11. 结果 → 正文表述的预设映射（在看数据前已固定）

看结果按此顺序，且按落入的 pattern 选写法（这是本诊断的 pre-specified 判读规则）：

**判读顺序**：① 看四人 condition-wise agreement 对照表，是否只有 target 在某条件明显低于其他三人 → ② 若是，看该条件最大 off-diagonal cell（须过第 7.5 节门槛）→ ③ 结合边际分布看方向是否真集中 → ④ 回 item-level 看这些题是否 target 高自然度无犹豫。

- **Pattern A（某条件特异，如 ma 低 + NEUTRAL→TENTATIVE 集中，且过门槛、边际分布不完全塌缩、target 高自然度无犹豫）**
  → "condition-specific interpretive divergence"，强调是 dissenting interpretation 而非 error；可谨慎引 Mandarin polar-question bias 文献（仅在此 pattern 成立时）。
- **Pattern B（三条件都低、方向分散、无突出 cell）**
  → "consistently low agreement across conditions, no single condition/direction accounts for it"；不强行找语言学解释。
- **Pattern C（+吧 特异——碰到 target construct）**
  → "substantive disagreement on the target +吧 interpretation"；target 必须作为重要 sensitivity annotator 保留。**并追加一个分析**：后续跑 LLM 时，检查模型在 core-3 gold 上的"错误"是否系统命中 target 的 minority reading——若是，则"模型答错"要重述为"模型对齐了人类少数派解读"。（BWL 的标签亦可同法使用。此分析写入后续 plan，不在本脚本。）
- **Pattern D（某语义标签被 target 全局过度使用，与 condition 无关）**
  → 可能是 response-category preference 而非语言效应；对照第 7.2 节 target 自身的 label 边际分布确认。

---

## 12. 明确不要做

- 不基于本步骤自动删除任何 annotator。
- 不先只分析 20 个 three-way family。
- 不用 design gold 代替 reference_pool majority。
- 不直接比较 A/B/C/D 字母。
- 不只报 overall agreement（必须分 condition）。
- 不只看对角线（非对角线才是重点）。
- 不对 < 8 的 cell 做定性解读。
- 不在本步做显著性检验。
- 不先看 LLM 结果再决定如何解释 target。
- 不把 BWL 放进任何 reference_pool。
- 不看完结果再改 no-option primary variant（A 恒为 primary）。

---

## 13. 交付前自检清单

- [ ] `target_annotator` / `reference_pool` / `no_option_mode` 三参数化，无人被硬编码。
- [ ] driver 跑满 4 人 × 2 mode = 8 次。
- [ ] 语义映射复用模块 1，未重复实现。
- [ ] 所有 agreement_rate 分母为 reference_n，coverage 同表呈现。
- [ ] no-option 双字段逻辑：choice=None 恒弃权；choice≠None+flag 按 mode 处理。
- [ ] 每条件输出 reference-label 边际分布。
- [ ] confusion matrix 有 raw + rownorm 两版，rows=reference / cols=target。
- [ ] 两个 direction 比例都算，含义标注清楚。
- [ ] item-level 表含 naturalness 与 hesitation 列。
- [ ] < 8 的 cell 标 low_n。
- [ ] 输出四人对照汇总表。
- [ ] 不对称说明写入输出 README/日志。
