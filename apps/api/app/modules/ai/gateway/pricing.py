"""Approximate per-model token pricing (USD per 1K tokens) for cost metering.

⚠️ APPROXIMATE — update with current published vendor rates before relying on the
cost numbers for pricing decisions. Unknown models fall back to 0 cost.
"""
from __future__ import annotations

from decimal import Decimal

# model -> (input_usd_per_1k, output_usd_per_1k)
PRICING: dict[str, tuple[Decimal, Decimal]] = {
    "gemini-1.5-flash": (Decimal("0.000075"), Decimal("0.00030")),
    "gemini-1.5-pro": (Decimal("0.00125"), Decimal("0.00500")),
    "claude-haiku-4-5": (Decimal("0.00100"), Decimal("0.00500")),
    "claude-sonnet-4-6": (Decimal("0.00300"), Decimal("0.01500")),
    "gpt-4o-mini": (Decimal("0.00015"), Decimal("0.00060")),
    "gpt-4o": (Decimal("0.00250"), Decimal("0.01000")),
    # Ollama cloud — meter tokens; cost tracked separately.
    "gemma4:cloud": (Decimal("0"), Decimal("0")),
    "gemma4:31b-cloud": (Decimal("0"), Decimal("0")),
}

_TOKENS_PER_THOUSAND = Decimal("1000")
_COST_QUANTUM = Decimal("0.000001")


def estimate_cost_usd(model: str, tokens_in: int, tokens_out: int) -> Decimal:
    rate = PRICING.get(model)
    if rate is None:
        return Decimal("0.000000")
    cost = (
        (Decimal(tokens_in) / _TOKENS_PER_THOUSAND) * rate[0]
        + (Decimal(tokens_out) / _TOKENS_PER_THOUSAND) * rate[1]
    )
    return cost.quantize(_COST_QUANTUM)
