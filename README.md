# SFP-吧：普通话语气词对比敏感度评测

项目背景、实验设计、数据格式规格、代码模块规格详见 [`SFP_coding plan.md`](./SFP_coding%20plan.md)。本 README 只说明目前已实现部分（模块4）的安装和运行方式。

## 目录结构

```
config/models.yaml       # 模型清单（provider/model_id/分组/价格），改模型不用改代码
data/fake_items.json     # 5 道手写假题，用于冒烟测试，不是正式数据
src/llm_query/           # 模块4：prompt构造 → 调用 → 解析 → 落盘
  prompt.py              # build_prompt(item) -> str
  parser.py              # parse_answer(raw_text) -> "A"/"B"/"C"/"D"/None
  providers/
    base.py              # Provider 接口 + LLMResponse 数据结构
    mock.py               # 不联网的假 provider，用哈希生成确定性答案
    openrouter.py          # 真实 OpenRouter 客户端（重试/退避、可选 logprobs）
  cost_guard.py            # 付费模型（目前只有 gemini-3-flash-preview）的花费护栏
  runner.py                 # 主循环：item × model，断点续跑
  __main__.py               # 命令行入口
tests/test_module4.py       # 单元测试，全部用 MockProvider，不需要网络/key
output/                      # 运行结果落盘目录（.jsonl，每行一条记录）
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

## 现状 / 下一步

- **已完成**：模块4（本 README 覆盖的部分），用假题+mock provider 全流程验证通过，尚未接入真实 OpenRouter key 做实测。
- **待接入**：拿到 `OPENROUTER_API_KEY` 后跑一次真实调用，确认返回格式、logprobs 有无、实际限流表现符合预期。
- **等标注数据到位后**：模块1（数据读取还原）、模块2（gold + family 剔除）、模块3（一致度 + human baseline），规则见 plan 第6节。
- **模块5/6**（打分、统计、出图）依赖模块2/3/4 的输出，尚未开始。
