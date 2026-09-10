# 项目规划 v3：LLM 能否追踪普通话句末“吧”的语用贡献？

**课程：** Pragmatic Processing in Large Language Models（Saarland University, LST）  
**类型：** 话题二 —— 把语用 probing 方法扩展到新语言 + 新现象（普通话句末语气词）  
**定位：** 课程项目（小 scope），同时为将来 workshop 投稿预留接口  
**指导：** 助教 Sasha 看好该选题，欢迎 publication 方向  
**版本日期：** 2026-08-23

> **本版说明（v3 相比 v2 的核心变化）：**
>
> 1. **主实验从“吧 + 呢”收紧为只测“吧”**。原计划中的“呢”在 pilot 的 context-only ablation 中暴露出明显 shortcut：模型在看不到目标句时仍能仅凭 context 恢复正确答案，因此当前 text-only + forced-choice MCQ 设计无法干净隔离“呢”本身的贡献。“呢”不再进入 confirmatory experiment，而保留为 methodological case / limitation。
> 2. Research Questions 重新编号为 **RQ1–RQ3**，全部围绕 bare / +吧 / +吗 的 controlled contrast 展开；不再保留旧编号 RQ5。
> 3. “吧”类材料构造全面采用 **`ba_item_design_framework_v0.3`**：把 interaction setting 和 proposition class 明确降级为 sampling scaffold；真正实验变量只有 particle condition。
> 4. 新增 **epistemic-authority / knowledge-distribution screening**：形式上只有句末变化并不自动保证三档可比，必须先排除会让 bare、+吧 或 +吗 某一档天然不自然的知识权威失衡。
> 5. 新增更严格的 **context neutrality**：context 只负责许可话题，不直接提供 P 的证据、不赋予任一方压倒性知识权威、也不暗示听话人已经知道答案。
> 6. 数据规模改为以 **family 数量** 为核心：正式目标约 30 个高质量 base families × 3 conditions ≈ 90 items；初稿约 36 families × 3 = 108 items，用于标注后整组过滤。
> 7. context-only ablation 从一次性诊断升级为正式的 **dataset validation** 步骤；“呢”的失败 pilot 作为为什么需要这种 validation 的方法学例子。
> 8. 分析计划加入 **pair success + family success + condition accuracy + confusion matrix + logprob shift**；sampling metadata 只做 exploratory breakdown，不作为主实验因素。

---

## 0. 一句话概括

构建一个小而受控的普通话评测集，通过同一 base proposition 的 **bare / +吧 / +吗** 三条件对比，测试大语言模型是否对句末形式所贡献的说话人立场表现出**系统性的对比敏感度（contrastive sensitivity）**，并比较这种敏感度在不同模型家族之间是否存在差异。

> **核心主张：**  
> **This project evaluates whether LLMs show systematic contrastive sensitivity to the pragmatic contribution of Mandarin sentence-final 吧 under tightly controlled bare / 吧 / 吗 contrasts.**

---

## 1. 研究主题与动机（Motivation）

### 1.1 为什么研究普通话句末语气词

普通话句末语气词（sentence-final particles, SFPs）不主要改变命题内容本身，而会改变说话人的立场、互动行动以及听话人应如何理解这句话（Chao, 1968; Li & Thompson, 1981）。

例如：

- `他是老师`：较确定地陈述 P
- `他是老师吧`：说话人对 P 有倾向，但降低自己的 epistemic commitment，并寻求听话人确认
- `他是老师吗`：较中性的询问，不预设 P 为真

这类现象很适合 controlled pragmatic probing，因为命题内容可以保持不变，而句末形式变化会系统性改变解释。

Fang & Hengeveld (2020) 反对把“吧”简单处理成一个表示“不确定”的 modal marker，而将其分析为作用于整个 utterance 的 **mitigator**。Kendrick (2018) 的会话分析进一步指出，“吧”可以调整会话中的 **epistemic gradient**，降低说话人的 epistemic position；在 assessment 等序列中，它也可以向具有相关知识的听话人征求响应。

因此，本项目不会声称覆盖“吧”的全部功能，而是明确锁定一个可受控测试的用法：

> **We focus on the confirmation-seeking / tentative-assertion use of 吧, rather than the full functional range of the particle.**

### 1.2 研究空白

现有研究已经开始系统评估 LLM 的语用能力。例如：

- **PUB** 覆盖 implicature、presupposition、reference 和 deixis 等语用现象；
- **MultiPragEval** 评估英语、德语、韩语和中文中的多语言 pragmatic inference；
- Yue et al. (2024) 用中文情景喜剧对话测试 conversational implicature；
- 2026 年的 **MalayPrag** 预印本开始直接研究口语马来语中的 discourse particles；
- Ma et al. (2025) 的 ACL survey 也指出，现有 pragmatics benchmark 在 phenomenon coverage、task design 与 evaluation validity 上仍有明显空缺。

但就本项目检索范围而言，尚未发现已有工作专门把：

> **普通话句末“吧” + family-internal bare / 吧 / 吗 controlled contrast + 母语者验证 + input ablation**

组合起来进行行为探测。

因此正式写作时可采用谨慎措辞：

> *To our knowledge, prior multilingual pragmatic benchmarks have not specifically targeted the Mandarin sentence-final particle 吧 through tightly controlled within-family contrasts with native-speaker validation and input-ablation checks.*

不要写 “the first pragmatics probing study” 或 “the first discourse-particle benchmark”。正式投稿前仍应再做一次完整 literature review。

### 1.3 Pilot 后的设计修订：为什么“呢”退出主实验

原计划希望同时测试“吧”和“呢”。“呢”的目标用法是 `X呢` 一类 fragment / follow-up question，原本采用“目标句不变、context 改变”的设计。

但 pilot 的 **context-only ablation** 发现：删除目标句 `X呢` 后，模型仍能根据 context 直接选中 gold answer。也就是说，题目可能实际允许：

> `context → answer option`

而不需要：

> `context + utterance containing 呢 → pragmatic interpretation`

这种 partial-input success 与 NLP benchmark 中常见的 shortcut / annotation-artifact 诊断逻辑一致：如果去掉理论上必需的输入后模型仍能完成任务，就不能把完整任务中的高分干净解释为目标能力（Gururangan et al., 2018; Poliak et al., 2018）。

因此：

- **“呢”不是因为语言学上不重要而被放弃；**
- **是当前 operationalization 无法保证 construct validity。**

“呢”不再进入 confirmatory experiment，只保留在：

- pilot / design validation；
- methodological decision；
- limitations / future work。

若以后扩展成 workshop paper，可以重新设计不同任务范式，再研究高度 context-dependent 的 fragment question。

---

## 2. 研究问题与假设（Research Questions & Hypotheses）

### 2.1 Research Questions

### RQ1 — Interpretation accuracy

> **Can LLMs recover the target speaker-stance interpretations associated with bare, +吧, and +吗 forms in controlled Mandarin contexts?**

中文：

> **在受控语境中，LLM 能否正确区分裸句、+吧、+吗所对应的目标说话人态度？**

主要指标：

- Accuracy(bare)
- Accuracy(+吧)
- Accuracy(+吗)
- 与 human baseline / annotator agreement 对照

---

### RQ2 — Contrastive sensitivity（核心 RQ）

> **Holding propositional content and discourse context constant, does changing only the sentence-final form (bare / 吧 / 吗) systematically shift model interpretations in the linguistically predicted direction?**

中文：

> **在命题内容和 discourse context 保持不变时，仅改变句末形式（裸句 / 吧 / 吗），是否会使模型的解释沿语言学预测的方向系统性变化？**

主要指标：

- bare ↔ +吧 pair success
- +吧 ↔ +吗 pair success
- bare ↔ +吗 pair success
- **family success**：同一 base family 的三个条件全部判断正确
- 若 API 支持：对应 answer choice 的 logprob / normalized probability shift

RQ2 是本项目最重要的研究问题，因为它直接对应实验真正操纵的变量：**particle condition**。

---

### RQ3 — Model variation

> **How does contrastive sensitivity to the pragmatic contribution of 吧 vary across model families, and, if a matched English control is included, how does performance compare with functionally similar English constructions?**

中文：

> **不同模型家族对“吧”语用贡献的 contrastive sensitivity 有何差异？如果加入功能匹配的英语对照，这种表现与相近的英语语用结构相比如何？**

注意：

- 跨模型差异是描述性的；
- 模型之间同时存在 size、architecture、tokenizer、pretraining data、instruction tuning、RL/post-training 等混淆变量；
- 不能把 “Qwen > Llama” 直接写成 “because Qwen is Chinese-dominant”；
- 最多讨论 observed pattern 是否**consistent with / suggestive of** language-related asymmetry。

英语对照仍然是 optional extension，而不是完成主项目的必要条件。

---

### 2.2 方向性假设

如果 H1–H4 尚未正式 preregister / timestamp，建议更新为：

- **H1：** +吧 条件的准确率低于 bare 条件，因为模型需要恢复额外的 speaker-stance contribution。
- **H2：** within-family contrast success 高于随机水平，但低于母语者水平。
- **H3（若做英语对照）：** 功能匹配的英语 confirmation-seeking construction 的 contrast success 高于中文 +吧。
- **H4：** +吧 的错误不是随机的；最主要的系统性错误是将 +吧 同化为 +吗 式的中性提问。

如果原 H1–H4 已经在仓库中正式 timestamp，则**不要覆盖历史记录**。应新增一条 dated design amendment：

> *The pilot context-only ablation invalidated the planned 呢 contrast, so hypotheses and confirmatory analyses concerning 呢 were dropped before the full model evaluation.*

---

## 3. 现象范围（Scope）

### 3.1 主实验只测“吧”

**Confirmatory experiment：**

- 只测试句末“吧”的 **confirmation-seeking / tentative-assertion** use；
- 每个 base proposition 形成：
  - bare：`P`
  - +吧：`P + 吧`
  - +吗：`P + 吗`

### 3.2 “呢”的位置

“呢”保留为：

- pilot 中发现的 methodological negative result；
- 当前 text-only forced-choice paradigm 的一个边界案例；
- future work 的重新设计对象。

不再把“呢”的结果和“吧”的结果放在同一主统计分析里。

### 3.3 其他语气词暂不进入主实验

- **了**：aspect / change-of-state 与 sentence-final function 容易纠缠，暂不纳入。
- **嘛**：功能边界较宽、与多种 interactional reading 纠缠，课程项目阶段暂不纳入。

> 未来扩展时可以重新加入其他 SFP，但前提是先找到与“吧”一样可验证、可 ablate、可形成干净 contrast 的 operationalization。

---

## 4. 实验设计（Research Design）

## 4.1 基本单位：family，而不是孤立 item

一个 **base family** 包含同一个 proposition `P` 的三个条件：

| Condition | Target form | Target interpretation |
|---|---|---|
| bare | `P` | 较确定地陈述 P |
| +吧 | `P吧` | 对 P 有倾向但不完全确定，并寻求确认 |
| +吗 | `P吗` | 较中性地询问 P，不预设答案 |

同一个 family 内必须尽量共享：

- 同一个 context
- 同一个 proposition content `P`
- 同一个 question
- 同一套 semantic options
- 同一个 option order

因此真正实验操纵只有：

> **particle condition = bare / +吧 / +吗**

这与 contrast-set 的基本思想一致：对同一个测试实例做小而有意义、并改变 gold interpretation 的局部扰动，从而观察模型的局部决策边界（Gardner et al., 2020）。

---

## 4.2 五条硬约束

1. **family 内只允许句末形式变化。**  
   不改变词汇、主语、时态/体、标点或问题措辞。

2. **目标句统一不带句末标点。**  
   避免 `。` / `？` 本身泄露 speech-act 类型。

3. **context 不得直接决定 gold。**  
   遮住目标句后，context 不应唯一推出“确定陈述 / 求确认 / 中性提问”中的某一个。

4. **family 内 option semantics 与 option order 完全一致。**  
   family 之间再进行 option-order counterbalancing，避免 position bias。MCQ option order 对 LLM 结果可能产生显著影响，因此必须显式控制。

5. **三档的语用自然度必须可比。**  
   形式上只差 particle 并不自动保证实验干净；必须额外检查 epistemic access / authority 和 context neutrality。

---

## 4.3 三层设计：sampling scaffold 与 experimental manipulation 分开

| 层级 | 内容 | 作用 | 是否主实验变量 |
|---|---|---|---|
| Interaction setting | online/offline × personal/peer-oriented / role-based-institutional | 保证互动场景覆盖 | 否 |
| Proposition class | 4 类 researcher-defined construction classes | 指导造题、保证语义/句式多样性 | 否 |
| Particle condition | bare / +吧 / +吗 | 测试模型是否对句末形式敏感 | **是** |

> **优先级：**  
> `contrast quality > naturalness > diversity > perfect numerical balance`

不能为了填满 sampling cell 而牺牲三档的可比性。

---

## 4.4 Interaction setting：2×2 取样框架

### Channel

- **Offline**：面对面 / 同一物理场所中的口头互动
- **Online**：群聊、私聊、评论区、课程平台、工作群、在线客服等文字互动

### Interaction relation

- **Personal / peer-oriented**：朋友、家人、同学、较平等同辈关系
- **Role-based / institutional**：职业、学校、服务、组织等角色关系

| | Personal / peer-oriented | Role-based / institutional |
|---|---|---|
| **Offline** | 朋友聚会、家庭聊天、宿舍/同学讨论 | 课堂、办公室、线下服务、机构交流 |
| **Online** | 朋友群、私聊、社交媒体 | 课程群、工作群、机构平台、在线客服 |

### 两个重要限制

**1. Online 不等于“网络黑话”。**

尽量不用：

- emoji
- `hhh`
- 大量重复问号/感叹号
- 网络缩写
- 强烈流行语

这些会引入额外 pragmatic cues。

**2. Role-based 不等于 service counter。**

顾客—店员、用户—客服很容易天然产生知识不对称。例如“还剩几张票”通常由店员掌握；如果顾客用 bare 陈述告诉店员，bare 会因为 epistemic authority 失衡而先天不自然。

因此 role-based item 优先使用：

- 工作群 / 课程群
- 项目组 / 办公室
- 同事 / 同学 / 学生—助教
- 共享文件、公开日程、课程通知、机构公告等双方都可获取的信息

---

## 4.5 Proposition construction classes

以下四类是**研究者定义的造题 scaffold**，不是普通话语言学中的固定分类，也不是主统计因素。

### Class 1：identity / classification

包括：

- 身份、角色、类别
- 所属 / 归属
- 名称
- 机构 / 群体归属

例：

- `他是新来的老师`
- `王老师是这个项目的负责人`
- `这个账号是小林的`
- `这是学生票`
- `那个人叫小周`
- `他在市场部`

**高风险：** 第二人称当前身份，如 `你是这里的负责人`。听话人通常对自己的当前身份拥有更直接知识权威，bare 很容易失衡。

---

### Class 2：external state / result

关于外部世界中可观察或可确认的：

- 数量
- 位置
- 可用性
- 营业/开放状态
- 当前过程
- 结果状态

例：

- `今晚的场次只剩两张票`
- `这个链接还能用`
- `这家店今天不营业`
- `门现在锁着`
- `文件在共享盘里`
- `系统现在在维护`

`已经……了` 不禁止，但不要大量重复，否则容易形成 surface template artifact。

---

### Class 3：person-related state / experience

关于人物的：

- 既往经历
- 居住 / 位置关系
- 熟悉度
- 拥有
- 偏好
- 能力
- 当前活动
- 安排 / 义务

例：

- `他去过成都`
- `小林住这附近`
- `她认识王老师`
- `她有校园卡`
- `他喜欢科幻片`
- `小张最近在准备考试`

**中高风险：**

- `你去过巴黎`
- `你认识王老师`
- `你会开车`
- 听话人的内部身体/心理状态
- 听话人的个人意图

第二人称不是禁用，但必须单独做 epistemic-authority screen。

---

### Class 4：future / expected event

关于尚未发生、但有安排、预定、规律或现实依据的事件：

- `他明天也来`
- `会议三点开始`
- `快递明天到`
- `成绩明天公布`
- `报名周五截止`
- `新版本下周上线`
- `电影周五上映`
- `下一班车十分钟后到`

尽量避免把不确定性提前编码进 P：

- 应该
- 可能
- 大概
- 也许
- 好像

否则会削弱 bare → +吧 的解释力。

---

## 4.6 Epistemic-authority screening：先筛 P，再写 context

`P / P吧 / P吗` 形式上只差句末，并不意味着三档自动可比。

在写 context 前，先问：

> **谁对命题 P 拥有更自然、更直接的知识访问、权利或地位？**

这里的 **epistemic authority** 是研究者内部的便利简称，受 conversation-analytic work on epistemic status / gradients 启发（Heritage & Raymond, 2005; Heritage, 2012a, 2012b; Kendrick, 2018），但不是本项目新增的正式语言学分类。

### 快速风险筛选

| 风险 | 常见命题 | 示例 | 主要问题 |
|---|---|---|---|
| 高 | 听话人当前身份、内部状态、个人意图 | `您是这里的负责人`、`你现在很紧张` | bare 往往先天不自然 |
| 中 | 听话人过去经历、熟悉度、能力 | `你去过巴黎`、`你认识王老师` | bare 可能产生“为什么告诉我我自己的事” |
| 低 | 第三人称、非人物、共享/公开事实 | `这个账号是小林的`、`报名周五截止` | 三档更容易保持可比 |

如果 P 明显属于：

- **recipient-privileged knowledge** → 优先换 P；
- **speaker-privileged knowledge** → 同样警惕 +吧 退化成软化/保留式断言，而不是 confirmation-seeking。

真正的最终标准仍然是：

> **在同一个中立 context 中，bare / +吧 / +吗 是否都自然，并且解释差异主要来自 particle。**

---

## 4.7 Context neutrality

context 的任务是：

> **让这个话题有理由被说出来，但不替 particle 提前决定说话人的 epistemic stance。**

必须避免三种越界：

### 1. context 直接提供 P 的证据

例如写明：

- 说话人“刚刚看到通知写着 P”
- 说话人“亲眼看到 P”
- 说话人“刚查到 P”

这会使说话人已经拥有明显证据，压缩 bare / +吧 / +吗 的差异。

### 2. context 让说话人对 P 权威过高

例如 P 是：

- 说话人自己的身份
- 自己刚作出的决定
- 自己专属经历
- 自己刚完成的动作

+吧 可能因此被重新分析为软化、犹豫或非承诺式陈述。

### 3. context 明示听话人已经知道 P

例如听话人：

- 刚发过通知
- 亲自安排了该事项
- 刚刚把 P 告诉说话人

这会让 bare 变成多余重复，并诱发其他 social-action readings。

> **通则：**  
> context 只负责 **topic licensing**，不提供 decisive evidence，不把任何一方设置成压倒性的 K+，也不预设听话人已经知道答案。

---

## 4.8 从 candidate P 到完整 family 的构造流程

### Step 1：先找 candidate proposition P

不要先问：

> “我缺一个 online × role-based 的句子。”

先问：

> “这个 P 能否形成一个干净的 `P / P吧 / P吗` contrast？”

---

### Step 2：做“第 0 问”——epistemic-authority screen

检查：

- speaker 是否天然比 recipient 更知道 P？
- recipient 是否天然比 speaker 更知道 P？
- 这种不对称是否会使其中一档失效？

高风险就优先换 P。

---

### Step 3：做三问自查

1. `P` 能否自然作为较确定的陈述？
2. `P + 吧` 能否自然得到 tentative assertion / confirmation-seeking reading？
3. `P + 吗` 能否自然作为较中性的询问？

三个都“是”，再继续。

---

### Step 4：为 P 分配 sampling cell

补足：

- online / offline
- personal/peer / role-based

但**不为了 balance 接受一个差 P**。

---

### Step 5：写轻量、中立 context

只标记必要互动信息，例如：

> 几个朋友正在群里商量周末去看电影，小林随后发了一句。

而不是过度描写手机、软件、表情等无关细节。

---

### Step 6：生成三个条件

例如：

```text
bare: 电影周五上映
+吧: 电影周五上映吧
+吗: 电影周五上映吗
```

---

### Step 7：共享 question / options

同一 family：

- question 完全一致
- 四个 semantic options 完全一致
- option order 完全一致
- gold semantic 随 condition 变化

推荐语义骨架：

- **Statement**：说话人比较确定 P，是在告诉对方
- **Confirmation-seeking**：说话人对 P 有倾向但不完全确定，希望对方确认
- **Neutral question**：说话人只是在询问 P，没有明显倾向
- **Distractor**：惊讶 / 建议 / 重复 / 其他与三档均不匹配的社会行动

---

### Step 8：做最终污染检查

检查：

- context 是否出现“不确定、拿不准、想确认、不知道、好奇、犹豫”等显式泄露词；
- context 是否直接给了 P 的证据；
- speaker / recipient 权威是否严重失衡；
- context 是否暗示 recipient 已经知道 P；
- 三档是否被迫承担不同于目标解释的 social action；
- 除 particle 外是否有词汇 / 标点 / 结构变化；
- 四个选项是否对三档保持同一语义空间。

通过后才进入母语者标注。

---

## 4.9 题量结构

### Pilot

维持：

- **10 个 base families**
- 每 family × 3 conditions
- **30 个 pilot items**

建议：

- 8 个 core families：四个 interaction cells 各至少 2 个；
- 四种 proposition classes 各至少出现 2 次；
- 2 个 flexible families：优先材料质量，不强求填表。

### 正式材料

新的核心单位是 **family**，不再为了“总题数 100”硬凑多个语气词。

建议：

- **初稿：约 36 families × 3 = 108 items**
- **正式 gold target：约 30 families × 3 = 90 items**
- 可接受范围：约 28–32 个高质量 family，具体由 native annotation 决定

这样既有约 20% oversampling buffer，又能保证：

- 四个 interaction cells 有足够覆盖；
- 四类 proposition scaffold 有足够覆盖；
- subject type / surface pattern 不过度集中；
- family-wise exclusion 后仍有足够独立 base propositions。

---

## 4.10 全局 de-correlation 与多样性检查

sampling scaffold 的目的不是做 factorial experiment，而是防止 dataset artifact。

需要主动避免：

- personal/peer 几乎全部是第二人称；
- role-based 几乎全部是非人物主语；
- person-related 几乎全部是 `你 V过 X`；
- external state/result 大量重复 `已经……了`；
- future 大量重复 `会 / 应该 / 可能 / 大概`；
- identity 几乎全部 `他是职业名词`；
- online item 过度依赖 emoji / 网络黑话；
- role-based 过度集中顾客—店员 / 客服等强知识不对称；
- 某个 surface pattern 占比过高。

可记录：

```text
subject_type:
- human_2p
- human_3p
- proper_name
- nonhuman_np
- implicit/other

surface_pattern:
- X 是 Y
- X 是 Y 的
- X V 过 Y
- X 在 Y
- X 有 Y
- X V 着
- X 已经 V 了
- time + event
- other
```

这些字段主要用于 sanity check，不预设进入主统计模型。

---

## 4.11 材料来源与 provenance

语料库 / 真实对话材料的作用是：

> **找自然的 sentence skeleton、互动语感和 lexical diversity，而不是直接捞现成测试题。**

可用来源：

- BCC 语料库
- CCL 语料库
- OpenSubtitles / 影视字幕
- 开源中文对话语料
- 作者构造材料

改编流程：

1. 找真实句式骨架；
2. 去掉真实人物、地名、具体剧情等私有上下文；
3. 抽出 candidate proposition P；
4. 做 epistemic-authority screen；
5. 写新的 neutral context；
6. 扩展为 bare / +吧 / +吗 family；
7. 记录 provenance。

方法中可写：

> *Materials were constructed by the authors and, where appropriate, adapted from corpus or subtitle examples to improve lexical and conversational naturalness.*

---

## 4.12 造题中的 LLM 使用

流程：

> **LLM 辅助生成 / 改写 → 研究者筛选 → 母语者独立验证**

不能让自动生成代替人为设计检查。

### 重要控制

如果被测模型包括 Qwen / DeepSeek / GLM / Llama 等，最好不要让同一模型直接生成最终测试集。

LLM 可以用于：

- 提供 candidate P
- 改写 context
- 提供同义表达
- 检查 lexical repetition
- 辅助 brainstorm sampling cells

但最终 family 必须人工通过：

- authority screen
- three-question screen
- context-neutrality check
- leakage check
- native validation

---

## 4.13 母语者标注与过滤

### 正式阶段

- **3 位普通话母语者独立标注**
- item 顺序随机化
- 同一 family 三个条件不要连续出现
- 不让标注员知道 family 配对关系
- 保存所有原始标注

### 每题标两项

#### 1. Naturalness：1–5

> 这个 `context + utterance` 组合在真实普通话会话中有多自然？

#### 2. Interpretation：四选一

> 哪个选项最符合说话人的态度 / 行动？

### 建议 exclusion criteria

任一条件满足以下情况时，整组 family 剔除或重写：

1. family 内某条件 naturalness 平均分 < 4.0；
2. 任一标注员对某条件给 ≤ 2；
3. interpretation 未达到多数一致；
4. ≥ 2 人标 ambiguous；
5. ≥ 1 人认为“吧”并非目标 confirmation-seeking / tentative-assertion 用法；
6. ≥ 2 人认为解释明显依赖纯文本中没有编码的语调；
7. 某一条件因 epistemic authority / interactional role 出现系统性不自然。

> **Family-wise exclusion：**  
> 一个 family 的任一条件不合格，整个 family 不进入 confirmatory gold set，因为核心推断依赖完整三条件对比。

### 一致度

- 3 人：Fleiss’ κ
- 同时报告：
  - naturalness distribution
  - interpretation agreement
  - family exclusion rate

---

## 4.14 人类基线

如果无法额外招独立 human control group，可使用 leave-one-annotator-out（LOO）近似：

1. 留出 1 位 annotator；
2. 用其余 2 位的共同判断作为 provisional gold；
3. 算被留出者 accuracy；
4. 三人轮换；
5. 取平均。

必须在报告中说明：

- 这是课程项目的近似 human ceiling；
- 独立的新一组母语者会是更严格的 baseline。

---

## 4.15 Dataset validation：context-only ablation 正式化

“呢”的失败 pilot 表明，**遮住目标句后还能不能做题**是非常重要的 construct-validity check。

### 对“吧”family 的 context-only test

给模型：

- context
- question
- options

但删除：

- target sentence

理想结果：

- context 本身不应稳定指向某一个 gold semantic；
- 同一 family 的 context 不应预先编码 statement / confirmation-seeking / neutral question。

如果 context-only condition 能明显、高一致率地推出某个 answer：

> **该 family 的 context 需要重写或删除。**

这一步不是为了证明模型“一定真正理解了吧”，而是为了排除一个明显 shortcut。

这种做法与 partial-input baseline / annotation-artifact diagnostics 的方法逻辑一致（Gururangan et al., 2018; Poliak et al., 2018）。

---

## 4.16 Prompt 设计

所有模型使用同一主模板：

```text
阅读下面的对话情景，判断说话人的态度，只输出选项字母。

情景：{context}
句子：“{sentence}”
问题：{question}

选项：
A) {opt_a}
B) {opt_b}
C) {opt_c}
D) {opt_d}

答案：
```

### Prompt robustness

抽一个小 subset 再用 1–2 个轻微改写模板重跑，例如：

- “判断说话人说这句话时最可能是什么态度”
- “哪个选项最符合这句话在该情景中的意思”

目的不是把 prompt 本身变成实验变量，而是检查主结论是否完全依赖某一种 wording。

---

## 4.17 Option order

已有研究显示，LLM 在 MCQ 上可能对 option order 很敏感，因此：

- family 内三条件使用**完全相同的 option order**；
- family 之间做 counterbalancing；
- gold letter 在全数据中尽量均衡；
- 保存 `option_order` 和 `gold_semantic`，不要只保存 gold letter。

如果资源允许，可对小 subset 做 option-order robustness rerun。

---

## 4.18 打分

### 基础

- 模型只输出 A/B/C/D
- 解析字母
- 与 gold 对比
- correct = 0/1

### 连续分数（能拿 logprob 时）

保存：

- logprob_A
- logprob_B
- logprob_C
- logprob_D

或对四个 answer letters 归一化得到 conditional choice probabilities。

重点观察：

- bare → statement option 的概率
- +吧 → confirmation-seeking option 的概率
- +吗 → neutral-question option 的概率

即使 argmax 没变化，logprob shift 也可能揭示更细的 contrastive sensitivity。

拿不到 logprob 的模型仍然可以使用 categorical accuracy / pair success / family success。

---

## 4.19 模型选型

### 主原则

- 选多个不同模型家族；
- 尽量使用规模接近、instruction/chat 版本；
- 固定 decoding configuration；
- 记录 exact model identifier、provider、run date 和参数；
- 正式跑实验后不要随意换模型版本。

可考虑：

- 中文能力较强 / 中文数据明显较多的系列：Qwen、DeepSeek、GLM 等
- 全球通用 / 英语资源占比较高的系列：Llama、Mistral 等
- 如预算允许，可加 1–2 个 closed-source general-purpose model

### 不做强因果归因

模型家族不是严格控制的“语言训练条件”。

所以 RQ3 只能回答：

> observed sensitivity differs across model families

而不能直接回答：

> language-dominant pretraining caused the difference

---

## 4.20 可选英语对照

若时间充足，可从 15–20 个中文 family 中构造功能匹配的英语版本：

- `He is the teacher.`
- `He is the teacher, right?`
- 中性 yes/no question

目的：

- 如果某模型英语 control 明显更好、中文 +吧 明显更差，模式与 language-related asymmetry 相容；
- 如果英语也同样失败，可能是更一般的 pragmatic / contrastive difficulty。

英语对照是 bonus，不影响中文主实验成立。

---

## 4.21 数据表 schema

### Construction / item metadata

```text
family_id
item_id
particle_condition          # bare / ba / ma
context
sentence
question
channel                     # online / offline
interaction_relation        # personal_peer / role_based
proposition_class           # identity / external_state / person_state / future_event
subject_type
surface_pattern
epistemic_authority_profile # roughly_shared / recipient_advantaged / speaker_advantaged / unclear
knowledge_source            # public_shared / personal_experience / role_privileged / context_evidence / other
source_type                 # corpus / subtitle / constructed / adapted
source_note
option_order
gold_semantic
gold_letter
construction_notes
```

### Model result fields

```text
model_name
model_provider
model_group
run_date
temperature
prompt_variant
model_answer
correct
logprob_A
logprob_B
logprob_C
logprob_D
raw_response
```

---

## 5. 分析计划（Analysis Plan）

## 5.1 RQ1：按 condition 的解释准确率

每个模型报告：

- Accuracy(bare)
- Accuracy(+吧)
- Accuracy(+吗)
- overall accuracy
- 95% CI（如适用）
- human LOO baseline

重点不是只报告 overall accuracy，因为 overall 会掩盖模型是否只在某一个 condition 崩溃。

---

## 5.2 RQ2：within-family contrastive sensitivity

### Pair success

一个 pair 只有**两档都答对**才算成功。

分别报告：

- bare ↔ +吧
- +吧 ↔ +吗
- bare ↔ +吗

在四选一、独立均匀随机猜测的理想化条件下：

- 单题 chance = 0.25
- pair success chance = 0.25² = 0.0625

这个 chance 仅作为直觉参照；实际模型错误并不一定独立。

### Family success

一个 family 的三个条件全部答对才算成功：

> `family_success = correct_bare & correct_ba & correct_ma`

独立均匀猜测下：

> `0.25³ = 0.015625`

family success 是只测“吧”后非常重要的 summary metric，因为它直接回答：

> 模型是否能在同一个 P 上完整区分三种句末形式？

---

## 5.3 Inferential statistics

### 简单配对比较

对每个模型，可以针对同一批 families 使用 **McNemar test** 比较：

- bare vs. +吧 的 correct / incorrect
- +吧 vs. +吗
- bare vs. +吗

McNemar 检验的是**同一 family 下两个 condition 的 paired binary accuracy difference**，而不是直接检验“pair success”。

### 主/补充模型

可使用 mixed-effects logistic regression：

```text
correct ~ condition * model_or_model_group + (1 | family_id)
```

如数据量和收敛允许，可进一步考虑 condition 的 family-level random slope。

对于课程项目：

- 先完成 descriptive + paired tests；
- mixed-effects 作为更完整的 inferential analysis；
- 不要为了“高级统计”牺牲可解释性。

---

## 5.4 Logprob shift

对于提供 logprob 的模型，分析：

- target answer probability 是否在对应 condition 下上升；
- +吧 condition 是否把 mass 从 statement / neutral question 移向 confirmation-seeking；
- bare → +吧 → +吗 是否形成预期的 probability profile。

这能补充离散 accuracy 在小样本下的信息损失。

---

## 5.5 Error analysis：混淆矩阵

共享 semantic options 使错误方向具有可解释性。

重点看：

- +吧 → neutral question（+吗 reading）
- +吧 → statement（忽略 mitigation / confirmation-seeking）
- +吗 → +吧 reading
- bare → +吧 reading

海报最适合用：

- confusion-matrix heatmap
- condition-wise accuracy / family success 图
- model-family comparison 图

H4 直接对应：

> +吧 是否最常被同化为 +吗。

---

## 5.6 RQ3：跨模型比较

报告：

- condition × model
- pair success × model
- family success × model
- confusion pattern × model

如果使用 model group，只把它作为描述性 grouping。

不要把 sampling scaffold（online/offline、relation、proposition class）当作 confirmatory RQ。

---

## 5.7 Exploratory breakdown

如果最终 family 数量足够，可做 exploratory sanity check：

- online vs offline
- personal/peer vs role-based
- proposition class
- subject type
- epistemic_authority_profile

目的：

- 检查 dataset 是否出现系统性 blind spot；
- 检查某些材料类型是否特别难；
- 为 future work 产生 hypothesis。

这些 breakdown **不应被写成 v3 的核心 confirmatory claims**。

---

## 6. 贡献（Contribution）

### 6.1 实证贡献

提供一个针对普通话句末“吧”的：

> **受控 within-family contrast + 母语者验证 + 多模型比较**

行为探测。

与“同时测很多语气词”相比，本项目更强调：

> **一个小而干净的现象是否被模型稳定追踪。**

### 6.2 方法贡献

材料构造中显式区分：

- experimental manipulation
- sampling scaffold
- surface diversity metadata

并加入：

- epistemic-authority screening
- context-neutrality constraints
- context-only ablation
- family-wise exclusion

这些步骤共同提高 construct validity。

### 6.3 Pilot negative result 也是方法学结果

“呢”的 pilot 不进入主实验，但它说明：

> 对高度依赖 discourse context 的 fragment question，text-only forced-choice context-variation 设计可能允许 context shortcut。

因此，pilot 不是“失败数据”，而是帮助项目在 full evaluation 前发现了 measurement problem。

### 6.4 资源贡献

计划公开：

- gold dataset
- construction metadata
- prompt templates
- annotation guideline
- evaluation code
- ablation scripts
- model outputs（若 provider policy 允许）

---

## 7. 交付物与时间线

## 7.1 课程交付物

### 2 页摘要

建议结构：

1. Motivation + gap
2. RQ1–RQ3 + H1–H4
3. “呢” pilot amendment（1–2 句）
4. ba family construction
5. epistemic-authority + context-neutrality validation
6. native annotation
7. models / prompt / metrics
8. accuracy + pair/family success + confusion matrix
9. discussion / limitation

### Poster

视觉核心：

- `P / P吧 / P吗` family schematic
- construction pipeline
- condition-wise performance
- family success
- confusion matrix
- 1 个小框说明“呢为何从主实验删除”

### Repository

建议结构：

```text
README.md
project_plan_v3.md
data/
  pilot/
  gold/
annotations/
  guideline_v0.2.md
  raw/
  processed/
pilot_notes/
  ne_context_only_ablation.md
  ba_pilot_notes.md
scripts/
  build_prompts/
  run_models/
  score/
  analysis/
results/
```

---

## 7.2 截至 2026-08-23 的状态

已经完成 / 已形成明确结论：

- Project Plan v2
- annotation guideline v0.1
- “呢”的初始设计
- “呢”的 context-only ablation
- 决定“呢”不进入主实验
- “吧”类构造框架 v0.3
- 根据母语者 pilot 反馈新增 epistemic-authority 与 context-neutrality 原则

---

## 7.3 下一阶段时间线

### 8/23–8/30

- 把 annotation guideline 更新成 **v0.2：主实验只保留“吧”**
- 按 v0.3 框架定稿 10 个 ba pilot families
- 对 10 families 跑：
  - authority screen
  - context-only ablation
  - 母语者 naturalness / interpretation pilot
- 同时跑通 1 model × 5 items 的 API 最小闭环
- 冻结 RQ / hypotheses / design amendment

### 8/31–9/6

- 根据 pilot 修订材料
- 扩到约 **36 families / 108 items**
- 做全局 de-correlation / surface-pattern sanity check
- 补齐 provenance metadata

### 9/7–9/13

- 3 位母语者正式独立标注
- Fleiss’ κ
- family-wise filtering
- 目标保留约 **30 families / 90 items**
- LOO human baseline

### 9/14–9/20

- 全模型批量跑
- 收集 categorical answer
- 能拿则记录 logprob
- 小 subset 做 prompt robustness / option-order robustness

### 9/21–9/27

- descriptive analysis
- McNemar paired comparisons
- mixed-effects model
- pair success / family success
- confusion matrix
- model comparison

### 9/28–poster session 前

- 2 页摘要
- poster
- repository cleanup
- README + reproduction instructions

> **关键路径仍然是：材料质量 + 母语者验证。**  
> 模型批量运行和统计分析都不应抢在 dataset validation 前面。

---

## 8. “吧”family 逐题 checklist

### A. Proposition 层

- [ ] P 是否能自然形成 bare / +吧 / +吗？
- [ ] P 是否没有显式 `可能 / 大概 / 应该 / 也许 / 好像` 等提前编码 stance 的词？
- [ ] speaker / recipient 对 P 的 epistemic authority 是否没有严重失衡？
- [ ] 是否避免了高风险的听话人当前身份 / 内部状态 / 专属意图？
- [ ] 如使用第二人称，是否单独检查 bare 的自然度？

### B. Context 层

- [ ] context 是否只负责许可话题？
- [ ] 是否没有直接给出 P 的证据？
- [ ] 是否没有写“不确定 / 想确认 / 好奇 / 不知道”等答案泄露词？
- [ ] 是否没有把 speaker 设置成明显 K+？
- [ ] 是否没有把 recipient 设置成明显 K+？
- [ ] 是否没有暗示 recipient 已经知道 P？
- [ ] online context 是否没有不必要的 emoji / 网络黑话？
- [ ] role-based context 是否避免强 service-counter knowledge asymmetry？

### C. Family manipulation

- [ ] 三档是否只改变句末形式？
- [ ] target sentence 是否都不带句末标点？
- [ ] question 是否完全一致？
- [ ] semantic options 是否完全一致？
- [ ] option order 是否完全一致？
- [ ] gold semantic 是否按 bare / 吧 / 吗 正确变化？

### D. Dataset-level diversity

- [ ] interaction cells 是否没有严重偏斜？
- [ ] proposition classes 是否都有覆盖？
- [ ] personal/peer 是否没有几乎全用第二人称？
- [ ] role-based 是否没有几乎全用非人物主语？
- [ ] surface pattern 是否没有大量重复？
- [ ] aspect marker `了` 是否没有成为固定模板？
- [ ] future item 是否没有大量重复 `会`？
- [ ] identity item 是否没有全是 `他是职业`？

### E. Validation

- [ ] context-only ablation 是否无法稳定推出 gold？
- [ ] 3 位母语者 naturalness 是否达标？
- [ ] interpretation 是否达到多数一致？
- [ ] 是否无明显 ambiguous / non-target reading？
- [ ] family 三档是否都通过；否则整组剔除？

---

## 9. 面向 workshop 的扩展接口

当前项目先做小而干净，不堵死后续扩展。

未来可逐步增加：

1. **重新设计“呢”**
   - 不直接复用失败的 context-variation MCQ
   - 可考虑 production / completion、对比判断、acceptability、信息恢复等不同范式
   - 继续使用 partial-input ablation 验证

2. **加入其他 SFP**
   - 嘛、啊、啦等
   - 每个现象单独 operationalize，避免“一个模板套所有 particle”

3. **独立 human baseline**
   - 与 gold annotators 分离

4. **英语功能对照**
   - confirmation-seeking tag question / right?
   - 分离“中文能力”和更一般的 pragmatic contrast ability

5. **增加模型数量 / 多次运行**
   - 如 stochastic decoding，需要报告 run-level variance

6. **更完整 related work**
   - Mandarin SFP linguistics
   - computational pragmatics
   - multilingual pragmatics
   - discourse-particle benchmarks
   - benchmark artifacts / contrast sets / input ablations

### 可能的 workshop positioning

> *A small, phenomenon-driven evaluation of Mandarin sentence-final pragmatics, with emphasis on contrast validity rather than benchmark scale.*

投稿前再根据当期 CFP 查找：

- computational pragmatics
- multilingual evaluation
- linguistic evaluation of LLMs
- resources / benchmarking
- student research workshops

---

## 10. 参考文献

> 下列与 v3 关键设计直接相关的文献已于 2026-08-23 通过 publisher / ACL Anthology / institutional repository 核对；MalayPrag 目前为 arXiv preprint。

### Mandarin SFP / epistemics

- Chao, Y. R. (1968). *A Grammar of Spoken Chinese*. University of California Press.
- Li, C. N., & Thompson, S. A. (1981). *Mandarin Chinese: A Functional Reference Grammar*. University of California Press.
- Dong, H. (2019). A semantic analysis of –ne as a topic marker: A grammaticalization perspective. In *Proceedings of the 30th North American Conference on Chinese Linguistics (NACCL-30)*, Vol. 2, 472–489.
- Fang, H., & Hengeveld, K. (2020). A mitigator in Mandarin: The sentence-final particle ba (吧). *Open Linguistics, 6*(1), 284–306. https://doi.org/10.1515/opli-2020-0018
- Fang, H., & Hengeveld, K. (2022). Sentence-final particles in Mandarin. *Studia Linguistica, 76*(3), 873–913. https://doi.org/10.1111/stul.12198
- Kendrick, K. H. (2018). Adjusting epistemic gradients: The final particle ba in Mandarin Chinese conversation. *East Asian Pragmatics, 3*(1), 5–26. https://doi.org/10.1558/eap.36120
- Heritage, J., & Raymond, G. (2005). The terms of agreement: Indexing epistemic authority and subordination in talk-in-interaction. *Social Psychology Quarterly, 68*(1), 15–38. https://doi.org/10.1177/019027250506800103
- Heritage, J. (2012a). Epistemics in action: Action formation and territories of knowledge. *Research on Language and Social Interaction, 45*(1), 1–29. https://doi.org/10.1080/08351813.2012.646684
- Heritage, J. (2012b). The epistemic engine: Sequence organization and territories of knowledge. *Research on Language and Social Interaction, 45*(1), 30–52. https://doi.org/10.1080/08351813.2012.646685

### Pragmatics benchmarks / LLM evaluation

- Sravanthi, S., Doshi, M., Tankala, P., Murthy, R., Dabre, R., & Bhattacharyya, P. (2024). PUB: A Pragmatics Understanding Benchmark for Assessing LLMs’ Pragmatics Capabilities. *Findings of ACL 2024*, 12075–12097. https://aclanthology.org/2024.findings-acl.719/
- Park, D., Lee, J., Park, S., Jeong, H., Koo, Y., Hwang, S., Park, S., & Lee, S. (2024). MultiPragEval: Multilingual Pragmatic Evaluation of Large Language Models. *Proceedings of the 2nd GenBench Workshop*, 96–119. https://aclanthology.org/2024.genbench-1.7/
- Yue, S., Song, S., Cheng, X., & Hu, H. (2024). Do Large Language Models Understand Conversational Implicature – A Case Study with a Chinese Sitcom. In *Chinese Computational Linguistics*, 402–418. https://doi.org/10.1007/978-981-97-8367-0_24
- Ma, B., Li, Y., Zhou, W., Gong, Z., Liu, Y. J., Jasinskaja, K., Friedrich, A., Hirschberg, J., Kreuter, F., & Plank, B. (2025). Pragmatics in the Era of Large Language Models: A Survey on Datasets, Evaluation, Opportunities and Challenges. *ACL 2025*, 8679–8696. https://aclanthology.org/2025.acl-long.425/
- Yusoff, M. A. G. B., Tan, J., Chen, B., Liu, G., & Chen, X. (2026). Can Large Language Models Handle Discourse Particles? A Case Study of Colloquial Malay. *arXiv:2605.28782*. https://arxiv.org/abs/2605.28782

### Benchmark construction / validation

- Gardner, M., Artzi, Y., Basmov, V., et al. (2020). Evaluating Models’ Local Decision Boundaries via Contrast Sets. *Findings of EMNLP 2020*, 1307–1323. https://aclanthology.org/2020.findings-emnlp.117/
- Ribeiro, M. T., Wu, T., Guestrin, C., & Singh, S. (2020). Beyond Accuracy: Behavioral Testing of NLP Models with CheckList. *ACL 2020*. https://aclanthology.org/2020.acl-main.442/
- Gururangan, S., Swayamdipta, S., Levy, O., Schwartz, R., Bowman, S. R., & Smith, N. A. (2018). Annotation Artifacts in Natural Language Inference Data. *NAACL-HLT 2018*, 107–112. https://aclanthology.org/N18-2017/
- Poliak, A., Naradowsky, J., Haldar, A., Rudinger, R., & Van Durme, B. (2018). Hypothesis Only Baselines in Natural Language Inference. *SEM 2018*, 180–191. https://aclanthology.org/S18-2023/
- Pezeshkpour, P., & Hruschka, E. (2024). Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions. *Findings of NAACL 2024*, 2006–2017. https://aclanthology.org/2024.findings-naacl.130/

---

## 11. 立即行动清单

### 现在就做

1. **把 annotation guideline v0.1 更新为 v0.2**
   - 正式标注部分只保留“吧”
   - 删除“呢”正式实验说明
   - 加入 epistemic-authority / context-neutrality 的研究者检查说明
   - “呢”移到 `pilot_notes/ne_context_only_ablation.md`

2. **冻结 10 个 ba pilot families**
   - 先按 v0.3 做 authority screen
   - 再做三问
   - 再写 neutral context
   - 最后做 context-only ablation

3. **让 1–2 位母语者复核 pilot**
   - naturalness
   - interpretation
   - 重点收集“bare 为什么怪”的评论

4. **在仓库中写 dated design amendment**
   - 记录“呢”退出主实验的时间和原因
   - 不回写、覆盖旧 preregistration / hypothesis history

5. **并行跑 API 最小闭环**
   - 1 model × 5 items
   - 解析 A/B/C/D
   - 测 logprob 是否可用
   - 保存 raw response

### Pilot 通过后再做

6. 扩到约 36 families；
7. 全局检查 sampling / surface pattern / person / authority 去相关；
8. 3 人正式标注；
9. 过滤到约 30 gold families；
10. 批量模型评估；
11. 分析 + poster + 2 页摘要。

### 暂时不要做

- 不为了凑 100 题重新硬塞“呢”或其他 particle；
- 不为了填满 2×2×4 的所有格子牺牲自然度；
- 不把 epistemic-authority heuristic 误写成一个既有的三分类理论；
- 不把 model-family difference 直接解释成 English bias；
- 不在 dataset validation 完成前投入大量 API 成本。

---

## 12. 一句话版修改原则

> **主实验只保留能够形成干净 controlled contrast 的“吧”：先用 epistemic-authority screening 排除先天失衡的 P，再用 neutral context 构造 `P / P吧 / P吗` family；interaction setting 与 proposition class 只用于取样多样性，不是实验变量；所有 family 必须通过母语者验证与 context-only ablation。原计划中的“呢”因 context-only shortcut 暂不进入 confirmatory experiment，而作为当前 text-only forced-choice probing 的方法学边界案例保留。**

### 最终 project claim（英文）

> **This project evaluates whether LLMs show systematic contrastive sensitivity to the pragmatic contribution of Mandarin sentence-final 吧 under tightly controlled bare / 吧 / 吗 contrasts. Candidate propositions are screened for epistemic-access asymmetries, and contexts are designed to license the topic without predetermining the speaker’s epistemic stance. A pilot design for 呢 was excluded from the confirmatory experiment after a context-only ablation showed that its intended labels could often be recovered without the target utterance, revealing a limitation of the current text-only forced-choice design for highly context-dependent fragment questions.**

### 最终 project claim（中文）

> **本项目通过严格控制的裸句 / 吧 / 吗对比，测试 LLM 是否对普通话句末“吧”的语用贡献表现出系统性的 contrastive sensitivity。候选命题在进入三条件扩展前先接受 epistemic-access / authority screening，context 只负责许可话题而不预先决定说话人的知识立场。原计划中的“呢”在 context-only ablation 中暴露出明显语境捷径，因此不进入主实验，而被保留为当前 text-only forced-choice 设计在高度语境依赖 fragment question 上的一个方法学边界案例。**
