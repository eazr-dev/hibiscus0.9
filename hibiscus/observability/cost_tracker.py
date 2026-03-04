"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Cost tracker — per-conversation LLM spend in INR with tier-level breakdown.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Pricing (USD per 1M tokens, as of March 2026) ─────────────────────────
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "deepseek/deepseek-chat": {
        "input": 0.028,   # $0.028 per 1M input tokens
        "output": 0.110,  # $0.11 per 1M output tokens
    },
    "deepseek/deepseek-reasoner": {
        "input": 0.550,   # $0.55 per 1M input tokens
        "output": 2.190,  # $2.19 per 1M output tokens
    },
    "anthropic/claude-sonnet-4-5": {
        "input": 3.000,   # $3.00 per 1M input tokens
        "output": 15.000, # $15.00 per 1M output tokens
    },
    "text-embedding-3-small": {
        "input": 0.020,
        "output": 0.000,
    },
}

USD_TO_INR = 85.0


@dataclass
class LLMCall:
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    cost_inr: float
    agent: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConversationCost:
    conversation_id: str
    calls: List[LLMCall] = field(default_factory=list)

    @property
    def total_tokens_in(self) -> int:
        return sum(c.tokens_in for c in self.calls)

    @property
    def total_tokens_out(self) -> int:
        return sum(c.tokens_out for c in self.calls)

    @property
    def total_cost_usd(self) -> float:
        return sum(c.cost_usd for c in self.calls)

    @property
    def total_cost_inr(self) -> float:
        return sum(c.cost_inr for c in self.calls)

    @property
    def models_used(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for call in self.calls:
            counts[call.model] = counts.get(call.model, 0) + 1
        return counts


# In-memory store for current session (in production, persist to Redis/PostgreSQL)
_conversation_costs: Dict[str, ConversationCost] = {}


def compute_cost(model: str, tokens_in: int, tokens_out: int) -> tuple[float, float]:
    """Compute cost in USD and INR for an LLM call."""
    pricing = MODEL_COSTS.get(model, {"input": 0.028, "output": 0.11})
    cost_usd = (tokens_in * pricing["input"] + tokens_out * pricing["output"]) / 1_000_000
    cost_inr = cost_usd * USD_TO_INR
    return cost_usd, cost_inr


def track_llm_call(
    conversation_id: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    agent: str = "unknown",
) -> LLMCall:
    """Record an LLM API call and accumulate conversation cost."""
    cost_usd, cost_inr = compute_cost(model, tokens_in, tokens_out)

    call = LLMCall(
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        cost_inr=cost_inr,
        agent=agent,
    )

    if conversation_id not in _conversation_costs:
        _conversation_costs[conversation_id] = ConversationCost(conversation_id)

    _conversation_costs[conversation_id].calls.append(call)

    logger.info(
        "llm_cost_tracked",
        conversation_id=conversation_id,
        model=model,
        agent=agent,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=round(cost_usd, 6),
        cost_inr=round(cost_inr, 4),
    )

    return call


def get_conversation_cost(conversation_id: str) -> Optional[ConversationCost]:
    return _conversation_costs.get(conversation_id)


def finalize_conversation(conversation_id: str) -> Optional[ConversationCost]:
    """Log final conversation cost summary and return it."""
    cost = _conversation_costs.get(conversation_id)
    if not cost:
        return None

    logger.info(
        "conversation_cost_final",
        conversation_id=conversation_id,
        total_tokens_in=cost.total_tokens_in,
        total_tokens_out=cost.total_tokens_out,
        total_cost_usd=round(cost.total_cost_usd, 6),
        total_cost_inr=round(cost.total_cost_inr, 4),
        models_used=cost.models_used,
        llm_calls=len(cost.calls),
    )

    # Warn if conversation cost exceeds threshold (₹5)
    if cost.total_cost_inr > 5.0:
        logger.warning(
            "conversation_cost_high",
            conversation_id=conversation_id,
            cost_inr=round(cost.total_cost_inr, 4),
            threshold_inr=5.0,
        )

    return cost


async def print_summary() -> None:
    """Print cost summary for all tracked conversations."""
    if not _conversation_costs:
        print("No conversations tracked yet.")
        return

    total_usd = sum(c.total_cost_usd for c in _conversation_costs.values())
    total_inr = total_usd * USD_TO_INR
    avg_inr = total_inr / len(_conversation_costs)

    print(f"\n=== Hibiscus LLM Cost Summary ===")
    print(f"Conversations tracked: {len(_conversation_costs)}")
    print(f"Total cost: ${total_usd:.4f} USD / ₹{total_inr:.2f} INR")
    print(f"Avg per conversation: ₹{avg_inr:.2f} INR")
    print("================================\n")
