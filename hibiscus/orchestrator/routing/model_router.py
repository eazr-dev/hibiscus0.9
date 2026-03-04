"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Model router — selects LLM tier (DeepSeek V3/R1/Claude) based on query complexity.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Optional

from hibiscus.llm.model_selector import Tier, select_tier, tier_label


def select_model_for_task(
    task: str,
    *,
    complexity: Optional[str] = None,
    confidence: Optional[float] = None,
    emotional_state: Optional[str] = None,
) -> str:
    """
    Select the LLM tier (model identifier) for a given task.

    Returns the tier string used by llm/router.py:
    - "deepseek_v3" (Tier 1 — 80% of calls)
    - "deepseek_r1" (Tier 2 — 15% of calls)
    - "claude_sonnet" (Tier 3 — 5% of calls)
    """
    tier = select_tier(
        task=task,
        confidence=confidence,
        emotional_state=emotional_state,
        complexity=complexity,
    )
    return tier.value


def get_model_label(tier_str: str) -> str:
    """Get human-readable model label for logging."""
    tier_map = {t.value: t for t in Tier}
    tier = tier_map.get(tier_str, Tier.T1)
    return tier_label(tier)


def should_escalate_to_claude(
    confidence: float,
    emotional_state: str = "neutral",
    task: str = "",
) -> bool:
    """
    Check if a response should be escalated to Claude (Tier 3).

    Conditions:
    - User is distressed/urgent
    - Confidence < 0.70 on critical financial decisions
    - Explicit safety net needed
    """
    if emotional_state in ("distressed", "urgent"):
        return True

    critical_tasks = {"surrender_calculation", "portfolio_optimization", "recommendation"}
    if confidence < 0.70 and task in critical_tasks:
        return True

    return False
