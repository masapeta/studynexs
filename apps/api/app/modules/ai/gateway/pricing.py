"""Approximate per-model token pricing (USD per 1K tokens) for cost metering.

⚠️ APPROXIMATE — update with current published vendor rates before relying on the
cost numbers for pricing decisions. Unknown models fall back to 0 cost.
"""
from __future__ import annotations

# model -> (input_usd_per_1k, output_usd_per_1k)
PRICING: dict[str, tuple[float, float]] = {
    "gemini-1.5-flash": (0.000075, 0.00030),
    "gemini-1.5-pro": (0.00125, 0.00500),
    "claude-haiku-4-5": (0.00100, 0.00500),
    "claude-sonnet-4-6": (0.00300, 0.01500),
    "gpt-4o-mini": (0.00015, 0.00060),
    "gpt-4o": (0.00250, 0.01000),
}


def estimate_cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    rate = PRICING.get(model)
    if rate is None:
        return 0.0
    return round((tokens_in / 1000) * rate[0] + (tokens_out / 1000) * rate[1], 6)
