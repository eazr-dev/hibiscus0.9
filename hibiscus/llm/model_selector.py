"""
Hibiscus Model Selector
=======================
Determines which LLM tier to use for each task type.

Task → Tier mapping:
  Tier 1 (DeepSeek V3.2): intent classification, L1/L2 responses,
                           policy analysis (tool-grounded), education,
                           claims guidance, regulation lookup, education
  Tier 2 (DeepSeek R1):   surrender calculations, portfolio optimization,
                           tax computation, complex multi-step math
  Tier 3 (Claude Sonnet): low confidence escalation, distressed users,
                           API fallback
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from enum import Enum
from typing import Optional


class Tier(str, Enum):
    T1 = "deepseek_v3"    # Tier 1 — 80% — cheap + fast + smart
    T2 = "deepseek_r1"    # Tier 2 — 15% — deep reasoning
    T3 = "claude_sonnet"  # Tier 3 — 5% — safety net


# Task to tier mapping
_TASK_TIER_MAP: dict[str, Tier] = {
    # Tier 1 — fast, cheap, grounded by tools
    "intent_classification": Tier.T1,
    "l1_response": Tier.T1,
    "l2_response": Tier.T1,
    "policy_analysis": Tier.T1,
    "recommendation": Tier.T1,
    "claims_guide": Tier.T1,
    "regulation_lookup": Tier.T1,
    "education": Tier.T1,
    "risk_detection": Tier.T1,
    "grievance_navigation": Tier.T1,
    "response_aggregation": Tier.T1,
    "memory_extraction": Tier.T1,
    "context_assembly": Tier.T1,

    # Tier 2 — complex math and reasoning
    "surrender_calculation": Tier.T2,
    "portfolio_optimization": Tier.T2,
    "tax_computation": Tier.T2,
    "irr_calculation": Tier.T2,
    "premium_adequacy": Tier.T2,
    "l4_response": Tier.T2,

    # Tier 3 — safety net (also triggered by conditions, not task type alone)
    "low_confidence_escalation": Tier.T3,
    "distressed_user_response": Tier.T3,
    "compliance_verification": Tier.T3,
    "api_fallback": Tier.T3,
}


def select_tier(
    task: str,
    confidence: Optional[float] = None,
    emotional_state: Optional[str] = None,
    complexity: Optional[str] = None,
) -> Tier:
    """
    Select the appropriate LLM tier.

    Priority:
    1. Emotional distress → Tier 3 (empathy requires Claude)
    2. Low confidence on financial decision → Tier 3
    3. Task-based mapping
    4. Default → Tier 1
    """
    # Emotional override
    if emotional_state in ("distressed", "urgent"):
        return Tier.T3

    # Low confidence override (for critical financial decisions)
    if confidence is not None and confidence < 0.70:
        if task in ("surrender_calculation", "portfolio_optimization", "recommendation"):
            return Tier.T3

    # Complexity override
    if complexity == "L4":
        return Tier.T2

    # Task-based mapping
    return _TASK_TIER_MAP.get(task, Tier.T1)


def tier_label(tier: Tier) -> str:
    labels = {
        Tier.T1: "DeepSeek V3.2 (Tier 1)",
        Tier.T2: "DeepSeek R1 (Tier 2)",
        Tier.T3: "Claude Sonnet (Tier 3)",
    }
    return labels.get(tier, "Unknown")
