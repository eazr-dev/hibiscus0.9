"""
IRR Calculator Tool
====================
Agent-callable tool wrapping knowledge/formulas/irr.py.
"""
from typing import Any, Dict, List, Optional

from hibiscus.knowledge.formulas.irr import (
    compute_irr,
    compute_policy_irr,
    interpret_irr,
)


async def calculate_irr(
    cashflows: List[float],
    guess: float = 0.05,
) -> Dict[str, Any]:
    """
    Compute Internal Rate of Return for a series of cashflows.

    Args:
        cashflows: List of cashflows (negative = outflow, positive = inflow)
        guess: Initial IRR guess

    Returns:
        {"irr": float, "irr_pct": str, "interpretation": str}
    """
    irr = compute_irr(cashflows, guess)
    interpretation = interpret_irr(irr)
    return {
        "irr": irr,
        "irr_pct": f"{irr * 100:.2f}%",
        "interpretation": interpretation,
        "cashflows": cashflows,
    }


async def calculate_policy_irr(
    annual_premium: float,
    policy_term: int,
    maturity_value: float,
    death_benefit: Optional[float] = None,
    bonuses: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Compute IRR for an insurance policy.

    Returns IRR with interpretation and comparison to alternatives.
    """
    irr = compute_policy_irr(
        annual_premium=annual_premium,
        policy_term=policy_term,
        maturity_value=maturity_value,
        death_benefit=death_benefit,
        bonuses=bonuses,
    )
    interpretation = interpret_irr(irr)
    return {
        "irr": irr,
        "irr_pct": f"{irr * 100:.2f}%",
        "interpretation": interpretation,
        "annual_premium": annual_premium,
        "policy_term": policy_term,
        "maturity_value": maturity_value,
    }
