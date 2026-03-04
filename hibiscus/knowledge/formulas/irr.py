"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
IRR formula — internal rate of return for ULIP and endowment policy evaluation.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


def compute_irr(cash_flows: list[float], initial_guess: float = 0.1, max_iter: int = 1000) -> Optional[float]:
    """
    Compute IRR using Newton-Raphson iteration.

    Args:
        cash_flows: List of cash flows. First element is typically negative (investment).
                    Example: [-100000, 0, 0, 0, 0, 150000] for ₹1L invested, ₹1.5L returned in 5 years
        initial_guess: Starting IRR estimate (0.1 = 10%)
        max_iter: Maximum iterations

    Returns:
        IRR as decimal (0.05 = 5%) or None if doesn't converge
    """
    rate = initial_guess

    for iteration in range(max_iter):
        npv = sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))
        npv_derivative = sum(
            -t * cf / (1 + rate) ** (t + 1)
            for t, cf in enumerate(cash_flows)
            if t > 0
        )

        if abs(npv_derivative) < 1e-10:
            logger.warning(
                "irr_convergence_failed",
                reason="zero_derivative",
                iteration=iteration,
                last_rate=round(rate, 6),
                last_npv=round(npv, 4),
                num_cash_flows=len(cash_flows),
            )
            return None

        new_rate = rate - npv / npv_derivative

        if abs(new_rate - rate) < 1e-8:
            return round(new_rate, 6)

        rate = new_rate

    logger.warning(
        "irr_convergence_failed",
        reason="max_iterations_exceeded",
        max_iter=max_iter,
        last_rate=round(rate, 6),
        last_npv=round(npv, 4),
        num_cash_flows=len(cash_flows),
        initial_guess=initial_guess,
    )
    return None


def compute_policy_irr(
    annual_premium: float,
    premium_term: int,
    maturity_amount: float,
    policy_term: int,
    annual_bonus: float = 0.0,
) -> Optional[float]:
    """
    Compute IRR of an insurance policy.

    Cash flows:
    - Negative: premium paid each year (years 0 to premium_term - 1)
    - Positive: maturity amount at year policy_term, + accumulated bonuses

    Returns IRR as decimal, or None if no convergence.
    """
    cash_flows = []

    for year in range(policy_term + 1):
        cf = 0.0
        if year < premium_term:
            cf -= annual_premium  # Premium outflow
        if year == policy_term:
            cf += maturity_amount + (annual_bonus * policy_term)
        cash_flows.append(cf)

    return compute_irr(cash_flows)


def interpret_irr(irr: Optional[float]) -> dict:
    """
    Interpret IRR in Indian insurance context.

    Returns assessment dict for display.
    """
    if irr is None:
        return {"irr_pct": None, "verdict": "Could not calculate IRR", "comparison": {}}

    irr_pct = round(irr * 100, 2)
    comparisons = {
        "vs_fd": irr_pct - 7.5,   # FD rate ~7.5%
        "vs_ppf": irr_pct - 7.1,  # PPF ~7.1%
        "vs_nifty": irr_pct - 12.5, # Nifty 50 historical ~12.5%
    }

    if irr_pct >= 10:
        verdict = "Good returns for an insurance product"
    elif 7 <= irr_pct < 10:
        verdict = "Moderate returns — comparable to FD, below equity"
    elif 5 <= irr_pct < 7:
        verdict = "Low returns — below FD rates. Check if insurance component justifies it."
    else:
        verdict = "Very low returns — primarily for insurance cover, not investment"

    return {
        "irr_pct": irr_pct,
        "verdict": verdict,
        "comparisons": comparisons,
        "context": (
            f"IRR of {irr_pct}% means this policy grows at {irr_pct}% per year "
            f"(vs FD ~7.5%, PPF ~7.1%, Nifty 50 historical ~12.5%)"
        )
    }
