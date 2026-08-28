"""Cost guard for paid models (Module 4).

Tracks a running total across a run and refuses further paid calls once the
configured max_cost_usd would be exceeded, so a bug or retry storm can't
silently rack up a bill against the user's OpenRouter credits. Free models
(is_free: true in config/models.yaml) never touch this at all.
"""

from dataclasses import dataclass, field

from .providers.base import LLMResponse

_ASSUMED_OUTPUT_TOKENS = 20  # the task only asks for one letter, but pad for verbose responses


@dataclass
class CostGuard:
    max_cost_usd: float
    spent_usd: float = field(default=0.0, init=False)

    def estimate(self, model_cfg: dict, prompt: str) -> float:
        price_in = model_cfg.get("price_input_per_million_usd") or 0.0
        price_out = model_cfg.get("price_output_per_million_usd") or 0.0
        # Conservative: 1 token per character as an upper bound for mixed
        # Chinese/English prompts (real tokenizers are usually more efficient,
        # so this overestimates rather than risking an under-budget surprise).
        assumed_input_tokens = len(prompt)
        return (assumed_input_tokens / 1e6) * price_in + (_ASSUMED_OUTPUT_TOKENS / 1e6) * price_out

    def can_spend(self, estimated_usd: float) -> bool:
        return (self.spent_usd + estimated_usd) <= self.max_cost_usd

    def record_actual(self, model_cfg: dict, response: LLMResponse) -> None:
        price_in = model_cfg.get("price_input_per_million_usd") or 0.0
        price_out = model_cfg.get("price_output_per_million_usd") or 0.0
        input_tokens = response.prompt_tokens or 0
        output_tokens = response.completion_tokens or 0
        self.spent_usd += (input_tokens / 1e6) * price_in + (output_tokens / 1e6) * price_out
