import json
from pathlib import Path

import pytest

from src.llm_query.cost_guard import CostGuard
from src.llm_query.parser import parse_answer
from src.llm_query.prompt import build_context_only_prompt, build_prompt
from src.llm_query.providers.base import LLMResponse
from src.llm_query.providers.mock import MockProvider
from src.llm_query.runner import load_done_keys, run, run_items

FAKE_ITEMS_PATH = Path(__file__).resolve().parents[1] / "data" / "fake_items.json"


def _sample_item():
    return {
        "item_id": "F00_bare",
        "family_id": "F00",
        "particle_condition": "bare",
        "context": "情景内容",
        "sentence": "他明天要出差",
        "question": "问题内容",
        "options": {"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
        "option_semantics": {"A": "statement", "B": "confirmation", "C": "neutral", "D": "distractor"},
    }


# ---- prompt.py ----------------------------------------------------------

def test_build_prompt_fills_all_fields():
    prompt = build_prompt(_sample_item())
    assert "情景：情景内容" in prompt
    assert '句子："他明天要出差"' in prompt
    assert "问题：问题内容" in prompt
    assert "A) 选项A" in prompt
    assert "D) 选项D" in prompt
    assert prompt.rstrip().endswith("答案：")


def test_build_context_only_prompt_omits_sentence_but_keeps_rest():
    prompt = build_context_only_prompt(_sample_item())
    assert "情景：情景内容" in prompt
    assert "他明天要出差" not in prompt  # the sentence itself never appears
    assert "句子" not in prompt  # the label line is dropped, not left blank
    assert "问题：问题内容" in prompt
    assert "A) 选项A" in prompt
    assert "D) 选项D" in prompt
    assert prompt.rstrip().endswith("答案：")
    assert prompt.startswith("阅读下面的对话情景，判断说话人的态度，只输出选项字母。")


# ---- parser.py ------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("A", "A"),
        ("B)", "B"),
        ("C) 这是理由", "C"),
        ("答案：D", "D"),
        ("答案是B。", "B"),
        ("答案为 C", "C"),
        ("我选A", "A"),
        ("我觉得选项C比较合适", "C"),
        ("The answer is A.", "A"),
        ("经过分析，说话人更像是在确认，所以答案应该是 B", "B"),
        ("**A**", "A"),
        ("根据语境，最合适的是 (D)", "D"),
        ("我不确定选哪个", None),
        ("", None),
        ("   ", None),
    ],
)
def test_parse_answer_variants(raw, expected):
    assert parse_answer(raw) == expected


def test_parse_answer_does_not_match_word_starting_with_letter():
    assert parse_answer("According to the context, the speaker is asking.") is None


# ---- providers/mock.py -----------------------------------------------------

def test_mock_provider_is_deterministic():
    provider = MockProvider()
    r1 = provider.call("model-x", "some prompt")
    r2 = provider.call("model-x", "some prompt")
    assert r1.raw_response == r2.raw_response
    assert parse_answer(r1.raw_response) in {"A", "B", "C", "D"}


def test_mock_provider_can_simulate_failure():
    provider = MockProvider(fail_on_substrings=("F00_bare",))
    r = provider.call("model-x", "prompt containing F00_bare marker")
    assert r.error is not None
    assert r.raw_response == ""


# ---- cost_guard.py ----------------------------------------------------------

def test_cost_guard_blocks_once_budget_exhausted():
    guard = CostGuard(max_cost_usd=0.0000001)
    model_cfg = {"price_input_per_million_usd": 0.50, "price_output_per_million_usd": 3.00}
    estimated = guard.estimate(model_cfg, prompt="x" * 1000)
    assert estimated > 0
    assert guard.can_spend(estimated) is False


def test_cost_guard_allows_free_style_zero_price():
    guard = CostGuard(max_cost_usd=1.0)
    model_cfg = {"price_input_per_million_usd": None, "price_output_per_million_usd": None}
    estimated = guard.estimate(model_cfg, prompt="x" * 1000)
    assert estimated == 0.0
    assert guard.can_spend(estimated) is True


# ---- runner.py (end-to-end smoke test with MockProvider) --------------------

def _mock_factory(model_cfg):
    return MockProvider()


def test_runner_smoke_creates_one_record_per_item(tmp_path):
    output_path = tmp_path / "results.jsonl"
    run(
        items_path=FAKE_ITEMS_PATH,
        output_path=output_path,
        model_names=["deepseek-v3"],
        provider_factory=_mock_factory,
        sleep_fn=lambda seconds: None,
    )

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    records = [json.loads(line) for line in lines]
    assert len(records) == 5  # 5 fake items x 1 model
    assert all(r["model_name"] == "deepseek-v3" for r in records)
    assert all(r["model_answer_letter"] in {"A", "B", "C", "D"} for r in records)
    assert all(r["model_answer_semantic"] is not None for r in records)
    assert all(r["error"] is None for r in records)


def test_run_items_accepts_in_memory_list_and_custom_prompt_builder(tmp_path):
    output_path = tmp_path / "results.jsonl"
    seen_prompts = []

    class RecordingMockProvider(MockProvider):
        def call(self, model_id, prompt, temperature=0.0):
            seen_prompts.append(prompt)
            return super().call(model_id, prompt, temperature)

    run_items(
        items=[_sample_item()],
        output_path=output_path,
        model_names=["deepseek-v3"],
        provider_factory=lambda model_cfg: RecordingMockProvider(),
        sleep_fn=lambda seconds: None,
        prompt_builder=build_context_only_prompt,
    )

    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().splitlines()]
    assert len(records) == 1
    assert records[0]["error"] is None
    assert "他明天要出差" not in seen_prompts[0]  # confirms the ablation prompt builder was actually used


def test_run_items_circuit_breaker_skips_rest_of_model_after_consecutive_failures(tmp_path):
    output_path = tmp_path / "results.jsonl"

    class AlwaysFailProvider(MockProvider):
        def call(self, model_id, prompt, temperature=0.0):
            return LLMResponse(raw_response="", logprobs=None, prompt_tokens=None,
                                completion_tokens=None, error="simulated persistent failure")

    run(
        items_path=FAKE_ITEMS_PATH, output_path=output_path, model_names=["deepseek-v3"],
        provider_factory=lambda model_cfg: AlwaysFailProvider(),
        sleep_fn=lambda s: None, max_consecutive_failures=2,
    )

    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().splitlines()]
    assert len(records) == 2  # breaker trips after 2 consecutive failures, 3 remaining items untouched
    assert all(r["error"] is not None for r in records)

    # Nothing was written for the skipped items, so a later run retries them
    # rather than treating them as permanently failed.
    written_ids = {r["item_id"] for r in records}
    assert written_ids != {"F00_bare", "F00_ba", "F00_ma", "F01_bare", "F01_ba"}


def test_run_items_consecutive_failure_count_resets_on_success(tmp_path):
    output_path = tmp_path / "results.jsonl"

    class FailOnceThenSucceed(MockProvider):
        def __init__(self):
            super().__init__()
            self._calls = 0

        def call(self, model_id, prompt, temperature=0.0):
            self._calls += 1
            if self._calls % 3 == 1:  # fail every third call, never twice in a row
                return LLMResponse(raw_response="", logprobs=None, prompt_tokens=None,
                                    completion_tokens=None, error="transient")
            return super().call(model_id, prompt, temperature)

    run(
        items_path=FAKE_ITEMS_PATH, output_path=output_path, model_names=["deepseek-v3"],
        provider_factory=lambda model_cfg: FailOnceThenSucceed(),
        sleep_fn=lambda s: None, max_consecutive_failures=2,
    )

    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().splitlines()]
    assert len(records) == 5  # breaker never trips: failures are isolated, never 2 in a row


def test_run_items_uses_custom_record_builder(tmp_path):
    output_path = tmp_path / "results.jsonl"

    def tiny_record_builder(item, model_cfg, prompt, run_date, temperature, response, answer_letter):
        return {"item_id": item["item_id"], "model": model_cfg["name"], "letter": answer_letter,
                "error": response.error}

    run(
        items_path=FAKE_ITEMS_PATH, output_path=output_path, model_names=["deepseek-v3"],
        provider_factory=lambda model_cfg: MockProvider(),
        sleep_fn=lambda s: None, record_builder=tiny_record_builder,
    )

    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().splitlines()]
    assert len(records) == 5
    assert set(records[0].keys()) == {"item_id", "model", "letter", "error"}


def test_runner_resume_skips_already_successful_pairs(tmp_path):
    output_path = tmp_path / "results.jsonl"
    call_log = []

    class CountingMockProvider(MockProvider):
        def call(self, model_id, prompt, temperature=0.0):
            call_log.append((model_id, prompt))
            return super().call(model_id, prompt, temperature)

    factory = lambda model_cfg: CountingMockProvider()

    run(items_path=FAKE_ITEMS_PATH, output_path=output_path, model_names=["deepseek-v3"],
        provider_factory=factory, sleep_fn=lambda s: None)
    assert len(call_log) == 5

    # Second run over the same output file should be a no-op: every pair
    # already has a successful record, so nothing new gets called.
    run(items_path=FAKE_ITEMS_PATH, output_path=output_path, model_names=["deepseek-v3"],
        provider_factory=factory, sleep_fn=lambda s: None)
    assert len(call_log) == 5

    done = load_done_keys(output_path)
    assert len(done) == 5


def test_runner_retries_failed_pair_on_resume(tmp_path):
    output_path = tmp_path / "results.jsonl"

    # F00_bare is the only item whose prompt contains this exact quoted
    # sentence (F00_ba/F00_ma have the same sentence plus a trailing particle,
    # so the closing quote never immediately follows "出差" for them).
    failing_factory = lambda model_cfg: MockProvider(fail_on_substrings=('"他明天要出差"',))
    run(items_path=FAKE_ITEMS_PATH, output_path=output_path, model_names=["deepseek-v3"],
        provider_factory=failing_factory, sleep_fn=lambda s: None)

    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().splitlines()]
    assert len(records) == 5
    failed = [r for r in records if r["item_id"] == "F00_bare"]
    assert len(failed) == 1
    assert failed[0]["error"] is not None
    assert len(load_done_keys(output_path)) == 4  # 4 succeeded, 1 failed

    succeeding_factory = lambda model_cfg: MockProvider()
    run(items_path=FAKE_ITEMS_PATH, output_path=output_path, model_names=["deepseek-v3"],
        provider_factory=succeeding_factory, sleep_fn=lambda s: None)

    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").strip().splitlines()]
    assert len(records) == 6  # the retry appends a new line rather than rewriting
    assert len(load_done_keys(output_path)) == 5  # all 5 items now have a successful record
