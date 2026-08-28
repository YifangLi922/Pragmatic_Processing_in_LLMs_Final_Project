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

tests/test_module2.py       # 单元测试，用 data/fake_annotations.json
tests/test_module3.py       # 单元测试，用 data/fake_annotations.json（含手算校验的小样例）
tests/test_module4.py       # 单元测试，全部用 MockProvider，不需要网络/key
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

## 现状 / 下一步

- **已完成**：
  - 模块2（gold定义 + family剔除）、模块3（一致度 + LOO human baseline）：用假标注表验证了 4:0/3:1/2:1:1/2:2 四种共识、gold撞车/无多数/自然度不达标三种剔除场景，43个单元测试全过。
  - 模块4（LLM调用）：prompt构造→调用→解析→落盘→断点续跑全流程用假题+mock provider验证通过。真实 OpenRouter 调用因为这个云端沙盒环境的网络出口策略挡住了 `openrouter.ai`，还没能在这里实测，需要你在自己电脑本地跑一次验证（见上面"真实调用 OpenRouter"一节），或者放开这个环境的网络策略。
- **待接入**：模块1（数据读取与还原）——框架等真实标注表的列名确定后再写，逻辑本身不复杂（按 `shuffled_index` 还原 + 按 `option_order` 把字母翻译成语义）。
- **模块5/6**（打分、统计、出图）依赖模块1/2/3/4 的输出，尚未开始。
