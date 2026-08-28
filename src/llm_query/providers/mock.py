"""Mock provider -- no network calls, no API key required.

Used to smoke-test the prompt -> call -> parse -> checkpoint loop (and in
unit tests) before spending real API quota/money on the real provider.
"""

import hashlib

from .base import LLMResponse, Provider

_LETTERS = "ABCD"


class MockProvider(Provider):
    """Derives a deterministic answer letter from a hash of (model_id, prompt),
    so repeated calls on the same item/model pair are stable across runs.

    `fail_on_substrings` lets tests simulate a failing call (e.g. to check
    that a partial run can resume) without any real network involved.
    """

    def __init__(self, fail_on_substrings: tuple[str, ...] = ()):
        self._fail_on_substrings = fail_on_substrings

    def call(self, model_id: str, prompt: str, temperature: float = 0.0) -> LLMResponse:
        for needle in self._fail_on_substrings:
            if needle in prompt:
                return LLMResponse(
                    raw_response="",
                    logprobs=None,
                    prompt_tokens=None,
                    completion_tokens=None,
                    error="mock induced failure",
                )

        digest = hashlib.sha256(f"{model_id}:{prompt}".encode("utf-8")).hexdigest()
        letter = _LETTERS[int(digest, 16) % 4]
        return LLMResponse(
            raw_response=f"答案：{letter}",
            logprobs=None,
            prompt_tokens=len(prompt) // 2,
            completion_tokens=2,
        )
