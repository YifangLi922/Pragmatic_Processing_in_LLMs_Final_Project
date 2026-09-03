# SFP-吧：普通话语气词对比敏感度评测

项目背景、实验设计、数据格式规格、代码模块规格详见 [`SFP_coding plan.md`](./SFP_coding%20plan.md)。本 README 说明目前已实现部分（模块2/3/4）的安装和运行方式。

## 目录结构

```
config/models.yaml         # 模型清单（provider/model_id/分组/价格），改模型不用改代码
data/fake_items.json       # 5 道手写假题，用于模块4冒烟测试，不是正式数据
data/fake_annotations.json # 5 个假 family（15题）× 4 假标注员，用于模块2/3测试，不是正式数据
                            # 已经是"母题对照表还原后"的形状（模块1的输出形状），只含
                            # item_id/family_id/particle_condition + 语义层面的标注，
                            # 刻意覆盖了 4:0/3:1/2:1:1/2:2 四种共识、以及 gold 撞车/
                            # 无多数/自然度不达标三种剔除触发场景，方便测试
data/reconstructed.json    # 模块1对真实标注数据的还原结果（108题，4标注员），非最终数据集
data/quality_report.json   # 模块1的质量报告（按标注员：划水/漏答/自然度方差/与设计gold过度一致等）
SFP标注完整版.xlsx          # 母题对照表（答案键），模块1的 --master 输入
SFP母语者标注N ....xlsx     # 4 份标注员原始答题表，模块1的 --annotator 输入

src/reconstruct/            # 模块1：数据读取与还原
  semantics.py               # 从选项文本模式匹配出 statement/confirmation/neutral/distractor
  master_table.py             # 读母题对照表（答案键），家族/条件/设计gold/选项语义
  annotator_table.py           # 读单个标注员的原始答题表
  build.py                      # 按shuffled_index join，字母→语义翻译，产出4.3节的结构
  quality.py                     # 质量报告：划水/漏答/自然度方差/与设计gold过度一致
  __main__.py                     # 命令行入口

src/gold/                  # 模块2：gold 定义 + family 剔除
  config.py                 # 可配置阈值（自然度下限、是否要求强共识）
  majority_vote.py           # 语义层面多数票 + 共识强度分级
  exclusion.py                # family 级剔除规则 + 剔除原因统计

src/agreement/              # 模块3：一致度 + LOO human baseline
  kappa.py                    # Fleiss' kappa（支持每题有效评分数不等）
  rates.py                     # hesitation/no_valid_option 比率、自然度分布，按condition分
  loo_baseline.py               # leave-one-annotator-out human baseline，按condition分

src/llm_query/              # 模块4：prompt构造 → 调用 → 解析 → 落盘
  prompt.py                  # build_prompt(item) -> str
  parser.py                   # parse_answer(raw_text) -> "A"/"B"/"C"/"D"/None
  providers/
    base.py                    # Provider 接口 + LLMResponse 数据结构
    mock.py                     # 不联网的假 provider，用哈希生成确定性答案
    openrouter.py                # 真实 OpenRouter 客户端（重试/退避、可选 logprobs）
  cost_guard.py                 # 付费模型（目前只有 gemini-3-flash-preview）的花费护栏
  runner.py                      # 主循环：item × model，断点续跑
  __main__.py                    # 命令行入口

src/scoring/                 # 模块5：模型答案 vs gold 打分
  join.py                     # 把模块4结果和模块2的gold/保留family连接成打分表
  accuracy.py                  # condition accuracy + Wilson 95% CI
  pair_family_success.py        # pair success、family success
  confusion.py                   # 每condition下模型答案的语义分布
  logprob_shift.py                 # 有logprob时的语义概率轮廓（best-effort）
  report.py                         # 组装每个模型的成绩单
  __main__.py                        # 命令行入口

src/stats/                   # 模块6：McNemar + 描述性图表（mixed-effects部分见下方"现状"）
  mcnemar.py                  # McNemar精确检验（配对二元准确率比较）
  plot_data.py                 # 出图前的纯数据整形（不含matplotlib，可单测）
  plots.py                      # 四张图：confusion热图、condition accuracy、family success、model vs human baseline
  __main__.py                    # 命令行入口

tests/test_module1.py       # 单元测试，纯 Python fixture，不需要真实 .xlsx 文件
tests/test_module2.py       # 单元测试，用 data/fake_annotations.json
tests/test_module3.py       # 单元测试，用 data/fake_annotations.json（含手算校验的小样例）
tests/test_module4.py       # 单元测试，全部用 MockProvider，不需要网络/key
tests/test_module5.py       # 单元测试，手造已知期望结果的小样例
tests/test_module6.py       # 单元测试，McNemar/出图数据整形单测 + 出图函数冒烟测试
output/                     # 运行结果落盘目录（.jsonl，每行一条记录）
```

## 安装

```bash
pip install -r requirements.txt
cp .env.example .env   # 之后把 OPENROUTER_API_KEY 填进 .env
```

## 跑单元测试

```bash
python -m pytest tests/ -v
```

## 冒烟测试（不需要 API key）

用 mock provider 在 5 道假题上跑一遍，验证 prompt 构造、解析、落盘、断点续跑整条链路：

```bash
python -m src.llm_query --items data/fake_items.json \
    --output output/fake_mock_results.jsonl --mock
```

再跑一次同样的命令，输出行数不会增加——已成功的 (item, model) 组合会被跳过，这就是断点续跑机制。想重新跑就删掉 `output/fake_mock_results.jsonl`。

## 真实调用 OpenRouter

`.env` 填好 key 后：

```bash
# 指定模型（逗号分隔，名字对应 config/models.yaml 的 name 字段）
python -m src.llm_query --items data/fake_items.json \
    --output output/fake_openrouter_results.jsonl \
    --models deepseek-v3,gemini-3-flash-preview

# 不传 --models 则跑 config/models.yaml 里的全部 6 个模型
python -m src.llm_query --items data/fake_items.json \
    --output output/fake_openrouter_results.jsonl
```

请求节奏按 `config/models.yaml` 里的 `rate_limit.requests_per_minute`（默认 20/分钟）自动控速；`gemini-3-flash-preview` 这类付费模型每次调用前会先估算花费，累计预估超过 `cost_guard.max_cost_usd`（默认 $1）就会跳过并在结果里记录 `error`，不会真的调用。

## 输出格式

`output/*.jsonl` 每行一个 JSON 对象，对应 plan 里 4.4 节的模型结果表（外加 `family_id`/`particle_condition`/`prompt`/`error` 等便于调试的字段）。`error` 为 `null` 代表成功；非 `null` 代表这条记录失败（解析失败、API报错、或被 cost guard 拦下），断点续跑时会重试。

## 模块1 怎么用

真实母题对照表（答案键，"研究者答案键"工作表）+ N 份标注员原始答题表（"母语者填写"工作表）在手后：

```bash
python -m src.reconstruct \
    --master "SFP标注完整版.xlsx" \
    --annotator A1="SFP母语者标注1 经济学.xlsx" \
    --annotator A2="SFP母语者标注2 媒体信息.xlsx" \
    --annotator A3="SFP母语者标注3 材料科学.xlsx" \
    --annotator A4="SFP母语者标注4 BWL.xlsx" \
    --output data/reconstructed.json \
    --quality-output data/quality_report.json
```

`--annotator` 可以传任意多个（不写死 4 个），加第 5 个标注员只需要多加一个 `--annotator` 参数，不用改代码。选项字母到语义骨架（statement/confirmation/neutral/distractor）的映射不依赖额外的 option_order 列，而是直接从选项原文按固定模板模式匹配得出（见 `semantics.py`），这是从真实答案键的用词规律里验证出来的，比预想的方案更省一步。

质量报告目前会自动标出：划水（单一字母占比>70%）、漏答、**自然度评分标准差为0**、**零犹豫+零"无合适答案"+零自然度方差同时出现**（"flat responding"信号）、以及**与设计者预期gold的一致率相对同批标注员是统计离群值**（z>2，需要3人以上才会算）。这几条不是随口加的——是照着一次真实的"怀疑标注员用AI代答"场景写的，现在跑在真实4人数据上就是这个结果：

```
[A3] 13/108 items unanswered
[A4] naturalness rating is constant (5) across all 108 items;
     flat responding: zero hesitation marks, zero 'no valid option' marks,
     and zero naturalness variance -- worth a closer look
```

## 模块2/3 怎么用

真实标注数据到位、模块1把它还原成 4.3 节那种"每题一条记录 + annotations 列表"的形状之前，可以先用 `data/fake_annotations.json`（已经是还原后的形状）跑通逻辑：

```python
import json
from src.gold.exclusion import evaluate_families, exclusion_report
from src.agreement.kappa import fleiss_kappa
from src.agreement.rates import hesitation_rate_by_condition, naturalness_distribution_by_condition
from src.agreement.loo_baseline import loo_human_baseline

items = json.load(open("data/fake_annotations.json", encoding="utf-8"))

gold_results, family_decisions = evaluate_families(items)   # 模块2
print(exclusion_report(family_decisions))

print(fleiss_kappa(items))                                   # 模块3
print(hesitation_rate_by_condition(items))
print(naturalness_distribution_by_condition(items))
print(loo_human_baseline(items))
```

`evaluate_families` 用的阈值（自然度下限、是否要求强共识）在 `src/gold/config.py` 的 `GoldConfig` 里，真实数据到位后如果要调整阈值，改这里的默认值或者传参覆盖，不用碰逻辑代码。

## 模块5 怎么用

模块1的输出 + 模块4的结果文件（可以是真实调用也可以是mock）在手后：

```bash
python -m src.scoring \
    --items data/reconstructed.json \
    --results output/real_openrouter_results.jsonl \
    --output data/scorecards.json
```

`--results` 可以传多次（比如每个模型一个文件），也可以传一个合并好的文件。gold 和 family 保留名单是在这里直接调用模块2的 `evaluate_families()` 现算的（模块2自己还没有落盘 gold.csv/retained_families.csv），所以永远反映 `src/gold/config.py` 当前的阈值设置。

打分口径（`join.py` 里也有注释）：API报错（限流、超时、被cost guard拦下）不计入打分分母，单独统计到 `n_errored`；调用成功但解析不出字母，按plan字面定义算"答错"而不是排除，单独统计到 `n_unparseable`，两个数字都留在成绩单里，方便你按需要重新核算。

## 模块6 怎么用

模块5的 `scorecards.json` + 模块1的还原数据在手后：

```bash
python -m src.stats \
    --items data/reconstructed.json \
    --results output/real_openrouter_results.jsonl \
    --scorecards data/scorecards.json \
    --output-dir output/figures \
    --mcnemar-output data/mcnemar_results.json
```

产出：每个模型一张混淆矩阵热图、一张跨模型 condition accuracy 对比图（Wilson CI误差棒）、一张 family success 对比图、一张 family×model 成败热图、一张模型 vs LOO human baseline 对比图；`mcnemar_results.json` 是每个模型三组条件对（bare vs +吧、+吧 vs +吗、bare vs +吗）的精确McNemar检验结果。

**mixed-effects logistic regression 还没写**：这部分该用 `statsmodels` 的 `BinomialBayesMixedGLM` 还是退一步用 GEE，等真实数据的方差结构出来后再定（细节见下面"现状"）。

## 现状 / 下一步

- **已完成**：
  - 模块1（数据读取与还原）：真实母题对照表 + 4 份真实标注表验证通过，108/108 题成功还原，0 条数据质量警告（修复过一次真实数据里的杂散空格问题）。质量报告成功自动检出两个真实的数据质量信号（见上面"模块1 怎么用"）。
  - 模块2（gold定义 + family剔除）、模块3（一致度 + LOO human baseline）：先用假标注表验证了 4:0/3:1/2:1:1/2:2 四种共识、gold撞车/无多数/自然度不达标三种剔除场景；后来也在真实108题数据上跑通了全流程（仅作管线验证，不是最终结果——最终 gold/剔除/baseline 要等标注员数量和处理方式定下来、数据集冻结后才算数）。
  - 模块4（LLM调用）：prompt构造→调用→解析→落盘→断点续跑全流程先用假题+mock provider验证，后用真实 OpenRouter key 在 6 个真模型上实测通过（5假题×6模型，0 API错误、0 解析失败，实付约 $0.01）。`config/models.yaml` 里的模型自那之后有更新：原先以为免费的 4 个模型（deepseek-v3/deepseek-r1-0528/qwen3-next-80b/mistral-small-3-24b）在 OpenRouter 上的 `:free` 版本已下架，已切换成付费版本并配了真实单价；gemma-4-31b 也主动从免费版换成付费版，让六个模型都在同一档（付费）上跑，避免"某模型表现差是因为免费限流"这种解释。
  - 模块5（打分）：condition accuracy（Wilson 95% CI）、pair/family success、confusion matrix、best-effort logprob概率轮廓。打分口径（报错排除、解析失败算错）写清楚在代码注释里。用真实108题数据（mock provider跑一个family）做过全链路验证。
  - 模块6（McNemar + 描述性图表）：McNemar精确检验、四张图（confusion热图/condition accuracy/family success/model vs baseline）+ 额外加了一张family×model成败热图。用真实数据全链路验证时抓到一个真bug——Wilson CI在accuracy恰好等于0.0时会有浮点误差（比如`5.5e-17`而不是精确的`0.0`），导致画图时误差棒变成负数报错，已修复并补了回归测试。mixed-effects部分留到真数据到位后再定用GEE还是`BinomialBayesMixedGLM`。
  - 单元测试共 79 个，全过。
- **进行中**：第 5 位标注员（英语文学硕士朋友）标注中，尚未提交。`src/gold/majority_vote.py` 的 `consensus_tier()` 目前按 4 人场景写死了"强/弱共识"的判定字符串，等 5 人数据到位、且定好 5 人场景下的共识阈值该怎么划之后再更新——这是需要人来决定的研究设计问题，不只是代码改动。
