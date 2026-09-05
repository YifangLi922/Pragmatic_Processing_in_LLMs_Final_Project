"""Runner for Module 4 (LLM querying).

Iterates every (item, model) pair, calls the configured provider, parses the
answer, and appends each result as one line to a JSONL checkpoint file. A
run that gets interrupted (crash, rate limit, ctrl-c) can simply be started
again: pairs that already have a successful recorded result are skipped, so
no API quota or money is spent twice.
"""

import datetime as _dt
import json
import time
from pathlib import Path

from .config import load_config
from .cost_guard import CostGuard
from .parser import parse_answer
from .prompt import build_prompt
from .providers.base import LLMResponse, Provider


def load_items(path: Path | str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_done_keys(output_path: Path | str) -> set[tuple[str, str]]:
    """(item_id, model_name) pairs that already have a *successful* result."""
    done: set[tuple[str, str]] = set()
    path = Path(output_path)
    if not path.exists():
        return done
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("error") is None:
                done.add((record["item_id"], record["model_name"]))
    return done


def _build_record(
    item: dict,
    model_cfg: dict,
    prompt: str,
    run_date: str,
    temperature: float,
    response: LLMResponse,
    answer_letter: str | None,
) -> dict:
    option_semantics = item.get("option_semantics", {})
    logprobs = response.logprobs or {}
    return {
        "model_name": model_cfg["name"],
        "model_provider": model_cfg["provider"],
        "model_group": model_cfg["model_group"],
        "run_date": run_date,
        "temperature": temperature,
        "item_id": item["item_id"],
        "family_id": item.get("family_id"),
        "particle_condition": item.get("particle_condition"),
        "model_answer_letter": answer_letter,
        "model_answer_semantic": option_semantics.get(answer_letter) if answer_letter else None,
        "logprob_A": logprobs.get("A"),
        "logprob_B": logprobs.get("B"),
        "logprob_C": logprobs.get("C"),
        "logprob_D": logprobs.get("D"),
        "raw_response": response.raw_response,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "prompt": prompt,
        "error": response.error,
    }


def run(
    items_path: Path | str,
    output_path: Path | str,
    model_names: list[str] | None = None,
    config_path: Path | str | None = None,
    provider_factory=None,
    run_date: str | None = None,
    sleep_fn=time.sleep,
    prompt_builder=build_prompt,
    record_builder=_build_record,
    max_consecutive_failures: int = 10,
    verbose: bool = False,
) -> Path:
    """Run every (item, model) pair not already successfully recorded.

    `provider_factory(model_cfg) -> Provider` builds one provider instance
    per model (so tests can pass a MockProvider); defaults to a real
    OpenRouterProvider, built lazily so a mock-only smoke test never needs
    OPENROUTER_API_KEY to be set. `prompt_builder(item) -> str` defaults to
    the main experiment's build_prompt; callers that need a different
    prompt (e.g. the context-only ablation's build_context_only_prompt)
    pass their own rather than this module growing a second run loop.
    `record_builder(item, model_cfg, prompt, run_date, temperature, response,
    answer_letter) -> dict` likewise defaults to this module's own record
    shape; a caller needing a different one (e.g. the main experiment's
    schema with hit_gold/gold_letter/timestamp already joined in) passes its
    own rather than post-processing this module's output into another shape.
    """
    items = load_items(items_path)
    return run_items(
        items, output_path, model_names, config_path, provider_factory, run_date, sleep_fn,
        prompt_builder, record_builder, max_consecutive_failures, verbose,
    )


def run_items(
    items: list[dict],
    output_path: Path | str,
    model_names: list[str] | None = None,
    config_path: Path | str | None = None,
    provider_factory=None,
    run_date: str | None = None,
    sleep_fn=time.sleep,
    prompt_builder=build_prompt,
    record_builder=_build_record,
    max_consecutive_failures: int = 10,
    verbose: bool = False,
) -> Path:
    """Same loop as run(), taking an already-loaded item list instead of a
    JSON file path -- so callers that build items in memory (e.g. joining
    frozen CSVs with reconstructed item text for the ablation/main
    experiment) don't need to round-trip through a temp file just to reuse
    this function.

    Per-call retry/backoff (429/5xx/timeout) happens inside the provider
    (see providers/openrouter.py) and is unconditionally reused here. On top
    of that, this loop tracks *consecutive* failures per model: once a
    single model hits `max_consecutive_failures` in a row (a broken
    model_id, an account issue, etc. -- not a one-off flaky call, which the
    provider's own retries already absorb), the rest of that model's items
    are skipped for *this run* rather than each burning through the
    provider's full retry budget for a foregone conclusion. Nothing is
    written for the skipped items, so a later run (once the model_id/account
    issue is fixed) will retry them normally via the done-set skip logic.
    """
    config = load_config(config_path) if config_path else load_config()
    models = config["models"]
    if model_names is not None:
        models = [m for m in models if m["name"] in model_names]

    requests_per_minute = config.get("rate_limit", {}).get("requests_per_minute", 20)
    min_interval_seconds = 60.0 / requests_per_minute
    temperature = config.get("decoding", {}).get("temperature", 0.0)
    cost_guard = CostGuard(max_cost_usd=config.get("cost_guard", {}).get("max_cost_usd", 1.0))
    run_date = run_date or _dt.date.today().isoformat()

    if provider_factory is None:
        def provider_factory(model_cfg: dict) -> Provider:
            from .providers.openrouter import OpenRouterProvider

            return OpenRouterProvider()

    done = load_done_keys(output_path)
    total_pairs = len(models) * len(items)
    n_done = len(done)
    providers_by_model: dict[str, Provider] = {}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "a", encoding="utf-8") as out_f:
        for model_cfg in models:
            model_name = model_cfg["name"]
            if model_name not in providers_by_model:
                providers_by_model[model_name] = provider_factory(model_cfg)
            provider = providers_by_model[model_name]
            is_free = model_cfg.get("is_free", True)
            consecutive_failures = 0

            for item in items:
                key = (item["item_id"], model_name)
                if key in done:
                    continue

                if consecutive_failures >= max_consecutive_failures:
                    if verbose:
                        print(
                            f"[{model_name}] {consecutive_failures} consecutive failures -- "
                            f"skipping remaining items for this run (will retry next run)."
                        )
                    break

                prompt = prompt_builder(item)

                if not is_free:
                    estimated = cost_guard.estimate(model_cfg, prompt)
                    if not cost_guard.can_spend(estimated):
                        response = LLMResponse(
                            raw_response="",
                            logprobs=None,
                            prompt_tokens=None,
                            completion_tokens=None,
                            error=(
                                f"cost guard: would exceed max_cost_usd={cost_guard.max_cost_usd} "
                                f"(spent so far ${cost_guard.spent_usd:.4f})"
                            ),
                        )
                        answer_letter = None
                        record = record_builder(item, model_cfg, prompt, run_date, temperature,
                                                 response, answer_letter)
                        out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                        out_f.flush()
                        consecutive_failures += 1
                        n_done += 1
                        if verbose:
                            print(f"[{n_done}/{total_pairs}] {model_name} {item['item_id']}: cost guard blocked")
                        continue

                start = time.monotonic()
                response = provider.call(model_id=model_cfg["model_id"], prompt=prompt,
                                          temperature=temperature)

                if response.error is None and not is_free:
                    cost_guard.record_actual(model_cfg, response)

                answer_letter = parse_answer(response.raw_response) if response.error is None else None
                record = record_builder(item, model_cfg, prompt, run_date, temperature,
                                         response, answer_letter)
                out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                out_f.flush()

                n_done += 1
                consecutive_failures = 0 if response.error is None else consecutive_failures + 1
                if verbose:
                    status = "OK" if response.error is None else f"ERROR: {response.error[:80]}"
                    print(f"[{n_done}/{total_pairs}] {model_name} {item['item_id']}: {status}")

                elapsed = time.monotonic() - start
                remaining = min_interval_seconds - elapsed
                if remaining > 0:
                    sleep_fn(remaining)

    return output_path
