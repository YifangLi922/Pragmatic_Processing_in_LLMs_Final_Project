# Pool Sensitivity Grid + Empirical Gold — 实现规格（for Claude Code）

> **这是实现规格，不是教学文档。** 目标：在不同 annotator pool 下对每个 family 做三档分类，输出一张"family × pool"网格，用来判断哪些 family 的保留对"选了哪组标注者"不敏感；同时基于母语者多数票产出 empirical gold，并标记出 gold 相对 design gold 发生偏移的 family。
>
> **实现前先做一件事**：读完后先输出一份"输入契约 + 输出文件 + 三档规则的精确定义 + 边界情况"的确认清单，等我确认后再写代码。不要直接开始写。
>
> **复用**：数据读取、letter→semantic 映射、no-option 双字段逻辑，全部复用 Econ 诊断脚本里已有的实现，不要重写。两套映射一旦分叉会产生对不上的数字。
>
> **语言**：代码、变量名、注释用英文；本规格为中文。

---

## 0. 定位

- 这是 **dataset-level 分析**，目的是量化 family 分类对 annotator pool 选择的敏感度，并生成 empirical gold。
- 本步骤**不跑模型、不碰外部 API、不做显著性检验**。
- 输出是描述性的表格，供人工做最终 KEEP/EXCLUDE 决策。**脚本本身不自动删除 family**，只做分类和标记。

---

## 1. 输入数据契约

- 单位：全部 **36 families / 108 items**。
- 在 **semantic label 层面**操作（ASSERT / TENTATIVE / NEUTRAL / DISTRACTOR），不碰 A/B/C/D。
- 每题每人字段（复用诊断脚本已有字段）：
  ```
  item_id, family_id, condition (bare/ba/ma), annotator,
  semantic_choice (四类或 None), no_option_flag (bool)
  ```
- 需要一份 **design gold** 输入：每个 family 每个 condition 你设计时预期的语义标签。若已有文件直接读；若没有，需要我另外提供，先在确认清单里问我。

- annotator 全集固定为 5 人：`Media, Materials, EngLit, Econ, BWL`。

---

## 2. no-option 处理

复用诊断脚本已定规则，本步骤统一用 **mode A（choice-first）**：

- `semantic_choice = None`（真弃权，本项目 Materials 属此）→ 该题该人计为 abstention，不进该题多数票分母。
- `semantic_choice ≠ None` 且 `no_option_flag = True`（本项目 EngLit 属此）→ 用其实际 choice 计票。

（mode B 是诊断步骤的 robustness check，本网格不重复，除非确认清单里我另有要求。）

---

## 3. 四种 annotator pool

固定这四种，顺序不变：

```
pool_core3   = [Media, Materials, EngLit]
pool_econ    = [Media, Materials, EngLit, Econ]
pool_bwl     = [Media, Materials, EngLit, BWL]
pool_all5    = [Media, Materials, EngLit, Econ, BWL]
```

---

## 4. 单个 condition 的多数票规则

对给定 pool、给定 item：

1. 在该 pool 成员中取计票的 `semantic_choice`（按第 2 节决定谁计票）。
2. 求多数：
   - 存在严格多数（> 半数计票人）→ `majority_label` = 该标签，`has_majority = True`。
   - 无严格多数（含平票、1-1-1、计票人不足）→ `majority_label = None`，`has_majority = False`。
3. **偶数 pool（4 人或含弃权后为偶数）出现 2-2 平票**：记为 `has_majority = False`。不要用任何 tie-break 规则偏向某一方。

---

## 5. family 三档分类规则（对每个 pool 各跑一次）

一个 family 有三个 condition（bare / ba / ma）。先算每个 condition 的 `majority_label` 与 `has_majority`，再按下面分类：

- **KEEP（保留）**：三个 condition 全部 `has_majority = True`，**且** 三个 majority_label 不完全相同（即至少形成了区分）。
- **COLLAPSE（塌缩）**：三个 condition 全部 `has_majority = True`，**但** 存在 condition 之间 majority_label 重合到失去区分的情况（见第 6 节细分）。
- **NO_CONSENSUS（无共识）**：至少一个 condition `has_majority = False`。

> 注意：KEEP 只要求"形成了区分"，不要求区分方向和 design gold 一致。gold 与 design 不一致的情况在第 7 节单独标记，**不影响** KEEP/COLLAPSE/NO_CONSENSUS 判定。

---

## 6. COLLAPSE 细分（仅对被判 COLLAPSE 的 family）

区分两种，分别计数：

- **COLLAPSE_distractor**：任一 condition 的 majority_label = DISTRACTOR。含义：该题选项设计失效，目标语义未被激活。
- **COLLAPSE_structural**：无 DISTRACTOR 多数，但两个（或更多）condition 的 majority_label 相同，导致对比消失（如 +吧 的 majority = +吗 的 majority）。含义：题目合法，但该语境撑不起条件间区分。

对每个 COLLAPSE_structural family，额外记录**塌缩方向**，即哪两个 condition 重合、重合到哪个标签，例如：
```
collapse_pair = "ba=ma", collapse_label = "TENTATIVE"
```
（这批方向数据后续用于对照 H4 中"吧最常被同化为吗"的预测，务必逐个记录，不要只给总数。）

---

## 7. Empirical gold + design-shift 标记

对 **pool_core3**（主 pool）：

- 对每个 family 每个 condition，若 `has_majority = True`，则 `empirical_gold[condition] = majority_label`；否则为 None。
- 与 design gold 逐 condition 比较：
  - `gold_shifted = True` 当且仅当 该 condition `has_majority = True` 且 `empirical_gold ≠ design_gold`。
- family 级标记 `family_gold_shifted = True`：该 family 至少有一个 condition 出现 `gold_shifted = True`。

> **这批 shifted family 不是失效 family，是 empirical gold 覆盖了 design gold。** 它们默认应进入主集合，gold 用 empirical 值。脚本只负责标记和输出，是否纳入由人工决定。

对这批 shifted family，额外输出每个 shifted condition 的：
```
design_gold_label, empirical_gold_label, majority_count, pool_size, margin
```
`margin` = 最高票数 − 次高票数，用于判断这个偏移后的 empirical gold 本身稳不稳（margin 大 = 稳）。

---

## 8. 输出文件

```
# 主网格：36 family × 4 pool
pool_sensitivity_grid.csv
  列：family_id,
      core3_class, econ_class, bwl_class, all5_class,      # 每个 pool 的三档结果
      stable_keep_all_pools,                                # 四 pool 是否全为 KEEP (bool)
      core3_class_detail                                    # 可选：core3 下三 condition 的 majority 一览

# COLLAPSE 细分
collapse_breakdown.csv
  列：family_id, pool, collapse_type,                       # distractor / structural
      collapse_pair, collapse_label                         # 仅 structural 有值

# empirical gold（基于 core3）
empirical_gold_core3.csv
  列：family_id, condition, has_majority, majority_label,
      design_gold_label, gold_shifted, majority_count, pool_size, margin

# shifted family 汇总（从上表筛 gold_shifted=True）
gold_shifted_families.csv
  列：family_id, condition, design_gold_label, empirical_gold_label, margin
```

---

## 9. 要在运行日志/README 里注明的事

- 四种 pool 中，`pool_econ / pool_bwl / pool_all5` 含偶数或存疑标注者，其 KEEP 数与 core3 的差异**不可解释为 stimulus 质量变化**——它是 pool 构成的机械后果。网格的用途是找 `stable_keep_all_pools = True` 的交集，不是比较各 pool 的 KEEP 总数。
- BWL 出现在 `pool_bwl` 和 `pool_all5` 中仅用于 stress test（检验 core3 的分类是否被这个存疑标注者推翻），不代表 BWL 被接纳为有效标注者。

---

## 10. 明确不要做

- 不自动删除任何 family（只分类、只标记）。
- 不用 tie-break 规则消除平票（平票即 no-majority）。
- 不让 gold-shift 影响 KEEP/COLLAPSE/NO_CONSENSUS 判定。
- 不比较各 pool 的 KEEP 总数并解读为质量差异。
- 不重新实现语义映射 / no-option 逻辑（复用诊断脚本）。
- 不跑模型、不做显著性检验。
- 不直接比较 A/B/C/D 字母。

---

## 11. 交付前自检清单

- [ ] 数据读取与 letter→semantic 映射复用诊断脚本，未重写。
- [ ] 四种 pool 各跑一次三档分类。
- [ ] 平票一律记为 no-majority，无 tie-break。
- [ ] 网格输出 `stable_keep_all_pools` 交集列。
- [ ] COLLAPSE 拆成 distractor / structural 两类，structural 记录方向。
- [ ] empirical gold 基于 core3，逐 condition 与 design gold 比较。
- [ ] gold_shifted 标记正确，且不影响三档判定。
- [ ] shifted family 输出 margin 供稳定性判断。
- [ ] 日志注明"KEEP 总数差异 ≠ 质量差异"与 BWL 的 stress-test 角色。
