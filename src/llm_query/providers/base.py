"""Provider interface for Module 4 (LLM querying).

Every concrete provider (mock, OpenRouter, ...) implements the same
`call(model_id, prompt, temperature) -> LLMResponse` signature so the runner
never needs to know which backend it's talking to.
"""

from dataclasses import dataclass


@dataclass
class LLMResponse:
    raw_response: str
    logprobs: dict | None  # {"A": float|None, "B": ..., "C": ..., "D": ...} when available
    prompt_tokens: int | None
    completion_tokens: int | None
    error: str | None = None  # set (raw_response left empty) when the call failed


class Provider:
    def call(self, model_id: str, prompt: str, temperature: float = 0.0) -> LLMResponse:
        raise NotImplementedError
