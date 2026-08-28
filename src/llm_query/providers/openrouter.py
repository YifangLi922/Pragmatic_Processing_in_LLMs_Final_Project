"""OpenRouter client -- one OpenAI-compatible API for every model in
config/models.yaml, free or paid.
"""

import os
import time

import requests

from .base import LLMResponse, Provider

_API_URL = "https://openrouter.ai/api/v1/chat/completions"
_MAX_RETRIES = 5
_BACKOFF_BASE_SECONDS = 2
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class OpenRouterProvider(Provider):
    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self._api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        self._session = session or requests.Session()

    def call(self, model_id: str, prompt: str, temperature: float = 0.0) -> LLMResponse:
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "logprobs": True,
            "top_logprobs": 4,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}

        last_error = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = self._session.post(_API_URL, json=payload, headers=headers, timeout=60)
            except requests.RequestException as exc:
                last_error = str(exc)
                time.sleep(_BACKOFF_BASE_SECONDS * (2**attempt))
                continue

            if resp.status_code == 200:
                return self._parse_success(resp.json())

            if resp.status_code in _RETRYABLE_STATUS:
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                time.sleep(_BACKOFF_BASE_SECONDS * (2**attempt))
                continue

            # Non-retryable (bad request, auth failure, unknown model id, ...)
            return LLMResponse(
                raw_response="",
                logprobs=None,
                prompt_tokens=None,
                completion_tokens=None,
                error=f"HTTP {resp.status_code}: {resp.text[:200]}",
            )

        return LLMResponse(
            raw_response="",
            logprobs=None,
            prompt_tokens=None,
            completion_tokens=None,
            error=f"exhausted retries: {last_error}",
        )

    @staticmethod
    def _parse_success(data: dict) -> LLMResponse:
        try:
            choice = data["choices"][0]
            raw_response = choice["message"]["content"]
        except (KeyError, IndexError):
            return LLMResponse(
                raw_response="",
                logprobs=None,
                prompt_tokens=None,
                completion_tokens=None,
                error=f"unexpected response shape: {data}",
            )

        usage = data.get("usage") or {}
        return LLMResponse(
            raw_response=raw_response,
            logprobs=_extract_option_logprobs(choice),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )


def _extract_option_logprobs(choice: dict) -> dict | None:
    """Pull a {"A":..,"B":..,"C":..,"D":..} logprob dict out of the OpenAI-
    style logprobs block, if the model/provider returned one. Looks at the
    first emitted token that is itself one of A/B/C/D, and reads the
    alternative-letter logprobs from its top_logprobs list. Returns None
    (never raises) if the response has no logprobs -- not every model on
    OpenRouter supports them.
    """
    logprobs_obj = choice.get("logprobs")
    if not logprobs_obj or not logprobs_obj.get("content"):
        return None

    for token_info in logprobs_obj["content"]:
        token = (token_info.get("token") or "").strip()
        if token not in ("A", "B", "C", "D"):
            continue
        result = {"A": None, "B": None, "C": None, "D": None}
        for cand in token_info.get("top_logprobs", []) or []:
            cand_token = (cand.get("token") or "").strip()
            if cand_token in result:
                result[cand_token] = cand.get("logprob")
        result[token] = token_info.get("logprob", result[token])
        return result

    return None
