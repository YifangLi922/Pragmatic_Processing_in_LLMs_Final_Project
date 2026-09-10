# “吧”类题目构造框架

**项目：** Pragmatic Processing in LLMs — Mandarin sentence-final particles  
**用途：** 研究者内部的 pilot / 正式题目构造指南（不直接发给母语者标注员）  
**日期：** 2026-08-23  
**状态：** 在 v0.2 基础上结合母语者 pilot 反馈，新增 epistemic authority / knowledge-distribution 筛选与 context neutrality 原则

---

## 1. 核心原则：把“取样框架”和“实验操纵”分开

本项目中，“吧”类题目的真正实验操纵只有：

- **bare**：`P`
- **+吧**：`P + 吧`
- **+吗**：`P + 吗`

同一个 family 内，三种条件应尽量共享：

- 同一个 context
- 同一个 proposition content（P）
- 同一个问题
- 同一套选项
- 同一个选项顺序

因此，**online/offline、personal/peer/role-based、proposition class 都不是主实验变量**。它们只是用来保证材料来源、互动场景和句式内容不要过于单一。

可以把整个设计理解成三层：

| 层级 | 内容 | 作用 | 是否为主实验变量 |
|---|---|---|---|
| Interaction setting | online/offline × personal/peer/role-based | 保证互动场景覆盖 | 否（sampling metadata） |
| Proposition class | 4 类命题内容 | 指导造题并保证语义/句式多样性 | 否（construction scaffold） |
| Particle condition | bare / +吧 / +吗 | 检验模型是否对句末语气词敏感 | **是** |

> **一句话原则：** 2×2 interaction setting 是“取样地图”，4 类 proposition class 是“造题脚手架”，真正需要严格控制的是 family 内的 `P / P吧 / P吗` 对比。

### 1.1 新增贯穿性约束：三档可比性还取决于知识分布

`P / P吧 / P吗` 形式上只差句末语气词，并不自动保证三档在语用上可比。**谁对命题 P 拥有更自然、更直接的知识访问（epistemic access / rights / status）**，会影响 bare、+吧、+吗分别是否自然。

因此，v0.3 增加一个贯穿所有 proposition class 和 interaction setting 的前置筛选：

> **在写 context 之前，先检查说话人与听话人对 P 的知识权威是否严重不对称。若这种不对称会让某一档天然失效，就优先换 P，而不是靠 context 硬救。**

这里的 **epistemic authority** 是研究者内部的便利简称，泛指会话中相对的知识访问、权利和地位；它**不是**本项目新增的实验变量，也不应被写成一个已有文献规定的固定三分类。

---

## 2. Interaction setting：2×2 取样框架

### 2.1 两个维度

#### Channel

- **Offline**：面对面/同一物理场所中的口头互动。
- **Online**：群聊、私聊、评论区、课程平台、在线客服等文字互动。

#### Interaction relation

- **Personal / peer-oriented**：当前互动主要建立在朋友、家人、同学、同辈等私人或较平等关系上。
- **Role-based / institutional**：当前互动主要由服务、职业、学校、机构等角色关系组织，例如顾客—店员、学生—助教、用户—客服。

> 不建议简单称为“熟人 vs. 陌生人”。角色型互动双方可能彼此认识；关键是**当前互动由哪种关系组织**。

### 2.2 2×2 表

| | Personal / peer-oriented | Role-based / institutional |
|---|---|---|
| **Offline** | 朋友聚会、家庭聊天、宿舍/同学面对面讨论 | 柜台咨询、课堂/办公室交流、线下服务场景 |
| **Online** | 朋友群、私聊、社交媒体评论 | 课程群、工作群、在线客服、学校/机构平台 |

### 2.3 Channel 主要由 context 标记，不要求 target sentence 自己体现

例如 `电影周五上映` 本身既可在线说，也可线下说。

- **Online × personal/peer context**：几个朋友正在群里商量周末看电影，小林随后发了一句。
- **Offline × personal/peer context**：几个朋友吃饭时正在商量周末看电影，小林随后说了一句。

这不是缺陷。语用实验的 item 本来就是 **context + utterance** 的组合。对“吧”而言，context 在 family 内保持不变，因此 online/offline 不会解释 bare / +吧 / +吗之间的差异。

### 2.4 不把 online 等同于“网络黑话”

Online item 可以完全使用标准普通话：

- 你也报名了吧
- 文件在共享盘里吧
- 电影周五上映吧

尽量避免为了“显得像网络”而大量加入：

- emoji
- `hhh`、`哈哈哈`
- 大量问号/感叹号
- 网络缩写或强烈流行语

否则会引入额外 pragmatic cues，污染 particle contrast。

### 2.5 Role-based / institutional 不等于“服务柜台”

母语者 pilot 暴露出一个系统性问题：**服务柜台场景很容易天然带入知识不对称**。例如店员通常知道“还剩几张票”，顾客通常不知道；如果让顾客对店员说一个 bare 陈述，句子可能先因为知识权威不匹配而变怪，而不是因为 particle condition 本身。

因此，role-based / institutional item 优先使用：

- 工作群、课程群、办公室、项目组等机构内部互动；
- 同事、同学、学生—助教等双方都可能通过公共渠道获取信息的关系；
- 共享文件、课程通知、公开日程、机构公告等**非排他性信息源**。

服务场景并非一律禁止，但应额外检查：

- P 是否天然属于店员/客服/工作人员的专属信息域；
- bare 是否因此变成“一个明显不知道的人在告诉明显知道的人”；
- 是否可以把 P 改成双方均可观察、均可从公共来源得知的事实。

> **实操原则：** `role-based ≠ service-counter`。宁可优先选“机构内部平级或弱不对称”的互动，也不要为了填 role-based 格子强行使用顾客—店员式的强知识不对称场景。

---

## 3. Proposition classes：研究者定义的四类造题模板

### 3.1 重要说明

以下四类是本项目为了**系统化材料构造、减少 lexical/syntactic repetition**而定义的 heuristic taxonomy。

它们：

- **不是**普通话语言学中公认的四大命题类别；
- **不是**需要进入主统计模型的四个实验条件；
- 主要作用是帮助研究者避免 20 多个 family 都长成同一种句式。

建议在论文中称为：

> **researcher-defined proposition construction classes / sampling heuristics**

---

# 4. Class 1：身份 / 分类

**英文建议：** `identity / classification`

### 4.1 定义

关于某个人或事物的：

- 身份
- 角色
- 类别
- 所属/归属
- 名称
- 机构或群体归属

重点不是必须出现“是”，而是 proposition 在回答“X 是谁 / 属于什么 / 是哪一类”。

### 4.2 可覆盖的 surface structures

| Surface structure | Candidate P | 备注 |
|---|---|---|
| 系词身份 `X 是 Y` | 他是新来的老师 | 最典型，但不要全部用这一型 |
| 角色/职位 | 王老师是这个项目的负责人 | 角色判断 |
| 所有/归属 `X 是 Y 的` | 这个账号是小林的 | 可同时用于 online context |
| 类别判断 | 这是学生票 | 非人物主语 |
| 姓名/身份识别 | 那个人叫小周 | 避免全部使用“是” |
| 群体/机构归属 | 他在市场部 | 人物归属 |
| 属性分类 | 这个版本是免费的 | 物品/版本分类 |

### 4.3 造题注意事项

- 避免所有题都是 `他/她是……`。
- 避免只改变职业名词形成伪多样性（老师/医生/经理/助教）。
- 可以混合：
  - 第三人称：`他是助教`
  - 专名：`小林是负责人`
  - 非人物 NP：`这是学生票`
  - 所属关系：`这个账号是小林的`
- **第二人称当前身份/角色属于高风险类型**。例如 `你是这里的负责人` 中，听话人通常比说话人更有资格知道自己的当前身份；+吧、+吗可以自然，但 bare 往往很难解释成普通的信息陈述。除非有非常特殊且中立的情境，否则优先换成第三人称或非人物命题。
- 同样避免明显属于说话人必然知道的信息，例如第一人称的 `我是负责人吧`：这会把知识权威推到说话人一侧，使 +吧 容易变成软化/犹豫式断言，而不是本项目要锁定的 confirmation-seeking reading。

---

# 5. Class 2：外部状态 / 结果

**英文建议：** `external state / result`

### 5.1 定义

关于外部世界中可观察、可确认的状态、数量、位置、可用性、过程或结果。

这类**不等于“完成事件”**，也不应等同于 `已经……了`。

### 5.2 可覆盖的 surface structures

| Surface structure | Candidate P | 备注 |
|---|---|---|
| 数量/余量 | 今晚的场次只剩两张票 | 避免完成体模板 |
| 可用性 | 这个链接还能用 | 状态型 |
| 营业/开放状态 | 这家店今天不营业 | 无需“了” |
| 持续状态 | 门现在锁着 | `着` 状态 |
| 存在/位置 | 文件在共享盘里 | 很适合 role-based/online |
| 当前过程 | 系统现在在维护 | 过程型 |
| 结果状态 | 门票已经卖完了 | 可以保留少量 |

### 5.3 关于“了”的控制

`已经……了` 并不会自动使一个 family 无效，因为三种 particle condition 中该结构保持恒定；但如果大量 family 都使用同一个模板，会产生：

- surface-form repetition
- `了吧 / 了吗` 等局部形式的高频绑定
- 不必要的 aspect / sentence-final marking 复杂性

因此建议：

- **不禁止“了”**；
- pilot 10 个“吧”family 中可以保留约 1–2 个自然的 `已经……了` 例子；
- 其余外部状态题尽量使用数量、位置、可用性、持续状态、当前过程等不同结构。

---

# 6. Class 3：人物相关状态 / 经历

**英文建议：** `person-related state / experience`

> 相比旧名称“听话人状态/经历”，这里改成 **人物相关**，以避免错误地把这一类与第二人称 `你` 绑定。

### 6.1 定义

关于某个人的：

- 既往经历
- 居住/位置关系
- 熟悉度/认识关系
- 拥有
- 偏好
- 能力
- 当前活动
- 较稳定的个人属性或安排

主语**可以是第二人称，也可以是第三人称、专名等**。

### 6.2 可覆盖的 surface structures

| Surface structure | Candidate P | 备注 |
|---|---|---|
| 过去经历 `V过` | 他去过成都 / 小林去过成都 | 第二人称版本属于中风险，需额外检查 bare |
| 居住/位置关系 | 小林住这附近 | 无 aspect marker |
| 认识/熟悉 | 她认识王老师 | relation / knowledge；第二人称版本需做 authority screen |
| 拥有/具备 | 她有校园卡 | 当前属性 |
| 偏好 | 他喜欢科幻片 | 稳定倾向 |
| 技能/能力 | 小张会开车 | ability；听话人自己的能力通常有更强第一人称知识权威 |
| 当前活动 | 小张最近在准备考试 | ongoing activity |
| 安排/义务 | 她今天有课 | person-related external fact |

### 6.3 造题注意事项

- **不要让这一类自动等于“你……”**。第二人称并非禁用，但要把“听话人是否天然 K+”当作前置筛选。
- 可以有意识混合：
  - `他去过成都`
  - `小林住这附近`
  - `她认识王老师`
  - `小张最近在准备考试`
- **听话人的过去经历属于中风险**：如 `你去过巴黎`，说话人理论上可能记得对方曾说过，因此 bare 不是绝对不成立，但通常比第三人称命题更容易产生“为什么你在告诉我我自己的经历？”的语用压力。
- **听话人的当前身份、内部心理/身体状态、个人意图或能力通常风险更高**，因为听话人往往拥有更直接的第一人称知识访问。即便 +吧 很自然，bare 也可能因此失衡。
- pilot 阶段优先选**第三人称、非人物、或双方通过共同资源可访问**的事实；如确实保留第二人称题，应单独记录并检查三档自然度。

---

# 7. Class 4：未来事件 / 预期结果

**英文建议：** `future / expected event`

### 7.1 定义

关于尚未发生、但有时间安排、计划、预定、规律或现实依据的事件/结果。

建议避免把这一类叫“预测/推断”，因为本项目本身就在研究 `吧` 所贡献的 tentative / confirmation-seeking stance。

### 7.2 可覆盖的 surface structures

| Surface structure | Candidate P | 备注 |
|---|---|---|
| 人的未来参与 | 他明天也来 | 不需要“会” |
| 预定时间 | 会议三点开始 | schedule-based |
| 到达事件 | 快递明天到 | 口语自然 |
| 公布/发布事件 | 成绩明天公布 | 无人称主语也可 |
| 截止事件 | 报名周五截止 | 无 modal |
| 营业/开放安排 | 这家店周末营业 | future time + state |
| 上线/推出 | 新版本下周上线 | 适合 online / role-based |
| 娱乐/活动安排 | 电影周五上映 | 也可用于 online × personal |
| 自然事件 | 明天有雨 | 内容多样化 |
| 交通事件 | 下一班车十分钟后到 | role-based/service 很自然 |

### 7.3 避免显式 epistemic markers 过度重复

普通话中这些词可以和“吧”自然共现，但对本实验而言会提前编码不确定性：

- 应该
- 可能
- 大概
- 也许
- 好像

例如：

- `他应该明天会来吧`
- `可能周五上映吧`

作为真实中文并不一定有问题，但作为 controlled family 会削弱 `bare → +吧` 的解释力。

因此优先：

- `他明天来`
- `电影周五上映`
- `成绩明天公布`

而不是显式加入 epistemic modal。

---

## 8. 不要让 proposition class、interaction setting、人称彼此绑定

这是后续设计中需要主动避免的 dataset artifact。

### 8.1 风险模式

如果材料逐渐变成：

- personal/peer → 总是 `你/他/她`
- role-based → 总是 `文件/成绩/申请/门票`
- person-related experience → 总是 `你 V过 X`
- external state → 总是 `已经 V 了`

那么这些表面特征会与 sampling cell 高度相关。

这不会直接破坏 family 内 `P / P吧 / P吗` 的核心 contrast，但会：

- 降低数据集的结构多样性；
- 让 exploratory 的场景比较难以解释；
- 增加模型依赖 superficial cues 的可能性；
- 让数据集看起来更像模板生成，而不是对目标语用现象的广泛采样。

### 8.2 推荐做法

有意识进行 **de-correlation**：

- personal/peer 中也安排非人物主语：
  - `电影周五上映`
  - `门现在锁着`
  - `这个账号是小林的`
- role-based 中也可以安排人物主语，但优先使用**非听话人专属知识**：
  - `王老师今天也来`
  - `小林是这个项目的负责人`
  - `助教下午在办公室`
- person-related class 中混合 2nd / 3rd / proper name；其中 2nd-person item 另做 epistemic-authority screen，不把“人称去相关”凌驾于三档自然度之上。
- future class 中混合 human / non-human subjects。

---

## 9. （可选，不强求一定要做）建议增加的 metadata：subject type 与 surface pattern

这些变量**不需要进入主实验条件**，只作为研究者的 sanity check。

### 9.1 Subject type

建议记录：

```text
subject_type:
- human_2p
- human_3p
- proper_name
- nonhuman_np
- implicit/other
```

pilot 阶段无需严格均分，但应避免明显集中，例如：

- 8/10 个 personal item 都是 `你……`
- 所有 role-based item 都是非人物主语

### 9.2 Surface pattern

建议额外记录：

```text
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

**研究者 heuristic：** pilot 中尽量不要让同一种 surface pattern 占据过高比例。可以把“同一模式最好不超过约 2 次”当作内部提醒，但不要把这个数字写成有理论依据的正式 exclusion criterion。

### 9.3 （可选）Epistemic-authority sanity-check metadata

如果后续 family 较多，建议再记录两个**研究者内部检查字段**：

```text
epistemic_authority_profile:
- roughly_shared
- recipient_advantaged
- speaker_advantaged
- unclear/mixed

knowledge_source:
- public/shared
- personal_experience
- role_privileged
- context_evidence
- other
```

这些字段的目的只是帮助发现“某一批题天然把知识权威推向一方”的材料偏差，**不预设进入主统计模型，也不把它们当作语言学中的离散类别**。

---

## 10. Pilot：“吧”需要多少 family？

### 10.1 目标规模

维持原计划：

- **10 个 base families**
- 每个 family 产生 3 个 item：bare / +吧 / +吗
- 合计 **30 个 pilot items**

### 10.2 不需要填满 2×2×4 的全部 16 格

`2 × 2 interaction cells × 4 proposition classes = 16` 只是**候选空间**，不是 factorial experiment。

推荐：

- **8 个 core families**：保证四个 interaction cells 各至少 2 个，同时四种 proposition class 各至少出现 2 次；
- **2 个 flexible families**：根据语料自然度、候选质量和需要补足的结构自由选择。

### 10.3 一个可用的 8-family core coverage

| ID | Channel | Relation | Proposition class |
|---|---|---|---|
| BA01 | offline | personal/peer | identity/classification |
| BA02 | offline | personal/peer | person-related state/experience |
| BA03 | offline | role-based | external state/result |
| BA04 | offline | role-based | future/expected event |
| BA05 | online | personal/peer | identity/classification |
| BA06 | online | personal/peer | future/expected event |
| BA07 | online | role-based | external state/result |
| BA08 | online | role-based | person-related state/experience |
| BA09 | flexible | flexible | flexible |
| BA10 | flexible | flexible | flexible |

> **重点：** 不要为了填满格子牺牲自然度。最终优先级是 `contrast quality > naturalness > diversity > perfect numerical balance`。

---

## 11. 从 candidate P 到完整 family 的构造流程

### Step 1：先找到 candidate proposition P

不要先问“我缺一个 online × personal 的句子是什么”。

先问：

> 这个 P 能不能形成一个干净的三条件 contrast？

例如：

```text
P = 电影周五上映
```

### Step 2：先做“第 0 问”——epistemic-authority screen

在三问自查之前，先问：

> **说话人和听话人，谁对这个命题 P 拥有更自然、更直接的知识权威？**

如果答案明显是“听话人”，尤其是涉及听话人的当前身份、角色、内部状态、个人意图等，**优先换一个 P**。原因是：+吧 和 +吗 可能都自然，但 bare 很容易变成“说话人在告诉对方一个对方显然比自己更知道的事实”。

如果答案明显是“说话人”，也要继续警惕：+吧 可能不再被理解成“我有倾向、请你确认”，而更像说话人对自己已知信息做软化、保留或非承诺式陈述。

#### 风险分层（研究者 heuristic，不是理论分类）

| 风险 | 常见命题类型 | 例子 | 对 bare / +吧 的主要风险 |
|---|---|---|---|
| **高** | 听话人当前身份/角色；听话人内部状态/个人意图 | `您是这里的负责人`、`你现在很紧张` | bare 往往很难成立；听话人天然拥有更直接知识 |
| **中** | 听话人过去经历、熟悉度、能力等 | `你去过巴黎`、`你认识王老师` | bare 可勉强成立（说话人可能记得），但容易产生“为何告诉我我自己的事”的压力 |
| **低** | 第三人称、非人物、双方共同可及的公开事实 | `这个账号是小林的`、`报名周五截止` | 三档通常更容易保持对称 |

这张表只用于**快速筛题**。真正标准仍是：三档在同一中立 context 中是否都自然、且 gold interpretation 能随 particle 稳定变化。

### Step 3：再做三问自查

1. `P` 能否自然地作为较确定的陈述？
2. `P + 吧` 能否自然地得到 tentative assertion / confirmation-seeking reading？
3. `P + 吗` 能否自然地作为较中性的询问？

三个都“是”才进入下一步。

> **重要：** 第 0 问不是三问的替代品，而是更早的一道筛子。很多 pilot 中的问题 family 在形式上看似能凑出三档，但一放进实际说话人—听话人关系里，bare 就因 epistemic authority 失衡而先天变弱。

### Step 4：给 P 安排一个 sampling cell

例如当前需要补：

```text
channel = online
relation = personal/peer
```

不要反过来为了填格子接受一个 authority 风险很高的 P。

### Step 5：写一个轻量、中立、且不预分配知识权威的 context

例如：

> 几个朋友正在群里商量周末去看电影，小林随后发了一句。

Channel marker `在群里` 已经足够，不要过度描述“拿出手机—打开微信—输入文字”等无关细节。

#### 5.1 Context neutrality：让话题浮出来，但让 epistemic stance 保持“未指定”

context 的任务是让这句话在场景中**有理由被说出来**，而不是替 particle 提前决定说话人的知识状态。尤其避免以下三种越界：

1. **情景直接提供了命题证据**
   - 例如 context 已明确写出说话人刚刚看见/读到 P。
   - 后果：说话人已经获得明显依据，+吗 可能被读成带倾向的确认，bare 也可能变成“根据刚看到的东西做推断”，三档边界被压缩。

2. **说话人对 P 的权威过高**
   - 例如 P 属于说话人自己的专属经历、身份、决定或刚亲自完成的行为。
   - 后果：+吧 容易变成软化、犹豫或非承诺式断言，而不是本项目锁定的 confirmation-seeking reading。

3. **情景暗示听话人已经明确知道 P**
   - 例如 context 写明听话人刚发过通知、亲自安排了该事项、或刚把事实告诉过说话人。
   - 后果：bare 容易变成多余重复，母语者会重新解释说话人在做别的社会行动，干扰项因此变得有吸引力。

> **一条通则：** 情景要让“为什么谈这个话题”变得自然，但不要给命题的直接证据、不要赋予说话人压倒性的知识权威、也不要预设听话人已经知道答案。

### Step 6：生成 family

```text
bare: 电影周五上映
+吧: 电影周五上映吧
+吗: 电影周五上映吗
```

### Step 7：共享 question/options

同一 family：

- 问题完全一致；
- 四个 semantic options 完全一致；
- option order 完全一致；
- gold 随 particle condition 改变。

### Step 8：检查 leakage、authority 与自然度

先检查显式 leakage，尤其是 context 是否直接写出：

- 不确定
- 猜测
- 想确认
- 好奇
- 不知道
- 犹豫

再检查不那么显眼、但同样会污染对比的**知识分布线索**：

- context 是否已经给了 P 的直接证据？
- 说话人是否明显比听话人更有权威？
- 听话人是否明显比说话人更有权威？
- context 是否暗示听话人已经知道 P？
- bare / +吧 / +吗 是否因此被迫承担不同于目标选项的社会行动？

只有显式 leakage 与 epistemic-authority leakage 都通过，family 才进入母语者标注。

---

## 12. 重点避免的重复与偏向

在 pilot/正式扩展时做一次全局 sanity check：

- [ ] personal/peer 是否几乎全部使用第二人称？
- [ ] role-based 是否几乎全部使用非人物主语？
- [ ] person-related 是否几乎全部是 `你 V过 X`？
- [ ] external state/result 是否大量重复 `已经……了`？
- [ ] future/expected event 是否大量重复 `会` 或 `应该/可能/大概`？
- [ ] identity/classification 是否几乎全部为 `他是职业名词`？
- [ ] online item 是否过度依赖网络流行语、emoji 或特殊标点？
- [ ] role-based item 是否过度集中在顾客—店员/客服等强知识不对称场景？
- [ ] 是否存在“听话人天然更知道 P”的高风险第二人称命题，导致 bare 失衡？
- [ ] 是否存在“说话人天然更知道 P”的命题，导致 +吧 退化为软化断言？
- [ ] context 是否直接提供了 P 的证据？
- [ ] context 是否暗示听话人已经明确知道 P，从而让 bare 变成多余重复？
- [ ] 同一个 surface pattern 是否占据过高比例？
- [ ] 同一 family 内除了 particle 之外是否有额外词汇/标点变化？
- [ ] bare / +吧 / +吗 是否在同一个 context 中都自然，并且三档的差异主要来自 particle？

---

## 13. （可选，不一定要做）推荐的数据表字段（与原 schema 兼容）

可在原有 item/result schema 之外，为材料构造增加以下列：

```text
family_id
item_id
particle_condition
context
sentence
channel                  # online / offline
interaction_relation     # personal_peer / role_based
proposition_class        # identity / external_state / person_state / future_event
subject_type             # human_2p / human_3p / proper_name / nonhuman_np / other
surface_pattern
epistemic_authority_profile # roughly_shared / recipient_advantaged / speaker_advantaged / unclear
knowledge_source           # public/shared / personal_experience / role_privileged / context_evidence / other
source_type               # corpus / subtitle / constructed / adapted
source_note
option_order
gold_semantic
gold_letter
construction_notes
```

这些新增字段主要用于：

- 检查数据集是否被某些模板主导；
- 检查是否系统性地把某些 proposition class / interaction setting 与知识权威方向绑定；
- 记录材料 provenance；
- 在正式写 method 时解释材料如何系统产生；
- 必要时做 exploratory breakdown，但不预设为主分析。

---

## 14. 方法部分可以怎样解释这套框架

### 中文概括

> 为保证材料在互动场景、命题内容和表层形式上的多样性，我们使用两个研究者定义的 sampling scaffold。互动场景按交流媒介（online/offline）与互动关系（personal/peer-oriented vs. role-based/institutional）编码；候选命题则按 identity/classification、external state/result、person-related state/experience 和 future/expected event 四类 construction templates 组织。这些维度只用于材料构造和覆盖度控制，并非主实验因素。在进入三条件扩展前，我们额外对候选命题进行 epistemic-authority screening，排除会让说话人或听话人天然拥有压倒性知识权威、从而使某一 particle condition 先天不自然的候选。context 只负责许可话题，不直接提供命题证据，也不预设任一方已经知道答案。每个保留的 base proposition 随后生成 bare、+吧、+吗三个受控条件；family 内其余材料保持一致。

### 英文方法表述（可后续改写进 paper）

> To ensure lexical, structural, and interactional diversity, we organized candidate items using two researcher-defined sampling scaffolds. Interaction settings were coded along two dimensions—channel (online vs. offline) and interaction relation (personal/peer-oriented vs. role-based/institutional). Candidate propositions were additionally grouped into four construction classes: identity/classification, external state/result, person-related state/experience, and future/expected event. These categories served as material-construction heuristics rather than linguistic categories or experimental factors. Before expanding a proposition into contrastive conditions, we screened for strong asymmetries in epistemic access/rights that would make one condition pragmatically anomalous. Contexts were designed to license the topic while leaving the speaker's epistemic stance underdetermined: they did not supply direct evidence for the proposition or presuppose that either participant already possessed decisive knowledge. Each retained proposition was then expanded into three conditions (bare, +吧, +吗), with context, question, answer options, and option order held constant within a family.

---

## 15. 文献依据与“研究者自定义”部分的边界

### 15.1 文献直接支持的原则

1. **吧的功能范围比“简单不确定性 modal”更宽。**  
   Fang & Hengeveld (2020) 将句末“吧”分析为作用于整个 utterance 的 mitigator，而不是简单的 modal marker。这支持本项目把范围收紧到其中一种 confirmation-seeking / tentative-assertion use，而不是声称覆盖“吧”的全部功能。

2. **吧的解释与相对 epistemic position / access 有系统关系。**  
   Kendrick (2018) 的会话分析指出，“吧”可作为调整 epistemic gradient 的资源，降低说话人的 epistemic position；在 assessment sequences 中，带“吧”的评估出现在听话人具有主要或至少相等 epistemic access 的环境中，并可向听话人征求确认。这直接支持本项目新增的提醒：不能只检查句法形式，还要检查说话人和听话人对 P 的知识分布。

3. **epistemic status / rights 可以影响一句话被理解成什么社会行动，因此不能把形态形式当成唯一线索。**  
   Heritage & Raymond (2005) 讨论 assessment sequence 中不同参与者对被评估事项的 epistemic authority / rights；Heritage (2012a, 2012b) 进一步强调 epistemic status、stance 与 information imbalance 对 action formation 和 sequence organization 的作用。对本项目而言，这意味着：即使 `P / P吧 / P吗` 的字面差异受控，如果 context 先把某一方设置成明显 K+，三档仍可能不再承担预期的 assertion / confirmation-seeking / neutral question 对比。

4. **用系统化矩阵帮助生成多样测试是合理的 benchmark-construction 方法。**  
   Ribeiro et al. (2020) 的 CheckList 使用 linguistic capabilities × test types 的矩阵系统化测试构思；这为本项目把 interaction setting 与 proposition template 当作 coverage scaffold 提供方法学类比。

5. **family 内做局部、意义明确的变化符合 contrast-set 思路。**  
   Gardner et al. (2020) 建议对测试实例做 small but meaningful perturbations，并观察 gold label 是否相应改变。本项目 `P / P吧 / P吗` 的设计与这一思想相符。

6. **普通话 aspect / surface structure 本身具有复杂性。**  
   Li & Thompson (1981) 提供普通话功能语法的系统描述；Xiao & McEnery (2004) 对普通话 aspect 做了语料库研究。这些文献可用于支持我们有意识避免把材料过度绑定在某一个 aspectual template（如 `已经……了`）上。

### 15.2 研究者自定义、不可错误归因给文献的部分

以下内容是**本项目自己的设计决策或由 pilot 反馈抽象出的 heuristic**：

- online/offline × personal/peer/role-based 的 2×2；
- 四种 proposition construction classes；
- pilot 的 8 core + 2 flexible sampling 方案；
- subject_type / surface_pattern metadata；
- epistemic-authority 的“高/中/低风险”快速筛选表；
- “第 0 问：谁对 P 更有知识权威？”这一 construction filter；
- 优先采用机构内部共享信息，而不是把 role-based 等同于服务柜台；
- context 的“三类越界”检查（直接证据 / 说话人权威过高 / 暗示听话人已知）；
- “同一 surface pattern 尽量不要出现过多”等 heuristic；
- 对人称、场景与 proposition class 进行 de-correlation 的策略。

因此论文中可以说这些设计**受 conversation-analytic work on epistemics 启发**，但不要写成：

> “Prior work classifies Mandarin ba items into high-, medium-, and low-epistemic-authority risk.”

也不要写：

> “Previous work divides Mandarin propositions into these four classes.”

更准确的写法是：

> “Building on prior work on epistemic gradients and territories of knowledge, we introduced a researcher-defined screening heuristic to avoid candidate propositions whose knowledge distribution made one contrast condition pragmatically anomalous.”

---

## 16. References

- Fang, H., & Hengeveld, K. (2020). *A mitigator in Mandarin: The sentence-final particle ba (吧).* **Open Linguistics, 6**, 284–306. https://doi.org/10.1515/opli-2020-0018
- Gardner, M., Artzi, Y., Basmova, V., Berant, J., Bogin, B., Chen, S., et al. (2020). *Evaluating models’ local decision boundaries via contrast sets.* Findings of EMNLP 2020, 1307–1323. https://aclanthology.org/2020.findings-emnlp.117/
- Heritage, J. (2012a). *Epistemics in action: Action formation and territories of knowledge.* **Research on Language and Social Interaction, 45**(1), 1–29. https://doi.org/10.1080/08351813.2012.646684
- Heritage, J. (2012b). *The epistemic engine: Sequence organization and territories of knowledge.* **Research on Language and Social Interaction, 45**(1), 30–52. https://doi.org/10.1080/08351813.2012.646685
- Heritage, J., & Raymond, G. (2005). *The terms of agreement: Indexing epistemic authority and subordination in talk-in-interaction.* **Social Psychology Quarterly, 68**(1), 15–38. https://doi.org/10.1177/019027250506800103
- Kendrick, K. H. (2018). *Adjusting epistemic gradients: The final particle ba in Mandarin Chinese conversation.* **East Asian Pragmatics, 3**(1), 5–26. https://doi.org/10.1558/eap.36120
- Li, C. N., & Thompson, S. A. (1981). *Mandarin Chinese: A Functional Reference Grammar.* University of California Press.
- Ribeiro, M. T., Wu, T., Guestrin, C., & Singh, S. (2020). *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList.* Proceedings of ACL 2020. https://aclanthology.org/2020.acl-main.442/
- Xiao, R., & McEnery, T. (2004). *Aspect in Mandarin Chinese: A Corpus-based Study.* John Benjamins.

---

## 17. 当前执行版的一句话总结

> **先用 epistemic-authority “第 0 问”筛掉会让任一条件先天失衡的 P，再检查它能否自然形成 `P / P吧 / P吗`；随后用 2×2 interaction setting 和 4 类 proposition construction classes 检查覆盖度，并主动打散人称、主语类型和 surface pattern 的对应关系。context 只负责许可话题，不提供命题证据、不赋予任一方压倒性知识权威、也不暗示听话人已知答案；最终由母语者 naturalness 与 interpretation agreement 决定材料是否进入 gold set。**

---

## 18. 版本记录

| 版本 | 日期 | 主要变更 |
|---|---|---|
| v0.2 | 2026-08-19 | 建立 2×2 interaction sampling、四类 proposition construction scaffold、surface-pattern / subject-type 多样性控制 |
| **v0.3** | **2026-08-23** | 根据母语者 pilot 反馈新增 epistemic-authority “第 0 问”、三档知识权威风险筛选、context 三类越界检查；修正第二人称身份/经历与 role-based 服务柜台示例；补充 Heritage / Kendrick 的 epistemics 文献依据与可选 metadata |

