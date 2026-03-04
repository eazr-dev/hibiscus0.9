"""
Inflation Formulas
==================
Adjust monetary amounts for inflation over time.
Used for projecting future coverage needs and real cost of insurance.

NEVER invent inflation rates — always use stated assumptions.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from dataclasses import dataclass


def inflate(amount: float, years: int, rate: float = 0.06) -> float:
    """
    Future value of an amount after inflation.

    Args:
        amount: Current value (e.g. current sum insured ₹10L)
        years: Number of years into the future
        rate: Annual inflation rate (default 6% — India CPI average)

    Returns:
        Inflated future value
    """
    if years < 0:
        raise ValueError("years must be >= 0")
    return amount * ((1 + rate) ** years)


def real_coverage_needed(
    current_coverage: float,
    years: int,
    rate: float = 0.06,
) -> float:
    """
    How much coverage is needed in the future to match today's purchasing power.

    Example: ₹10L today → ₹17.9L in 10 years at 6% medical inflation.

    Args:
        current_coverage: Today's sum insured / coverage amount
        years: Years until renewal / review
        rate: Medical inflation rate (default 6%; use 0.10-0.15 for medical costs)

    Returns:
        Recommended future coverage to maintain real value
    """
    return inflate(current_coverage, years, rate)


def deflate(future_amount: float, years: int, rate: float = 0.06) -> float:
    """
    Present value of a future amount (reverse inflation).

    Args:
        future_amount: Future value
        years: Number of years
        rate: Annual inflation rate

    Returns:
        Present value equivalent
    """
    if years < 0:
        raise ValueError("years must be >= 0")
    return future_amount / ((1 + rate) ** years)


def inflation_gap(
    current_coverage: float,
    years: int,
    medical_inflation: float = 0.12,
) -> dict:
    """
    Calculate the coverage gap created by medical inflation.

    Returns a dict with current, needed, gap, gap_pct.
    Medical inflation in India: ~12-15% for hospitalisation costs.
    """
    needed = real_coverage_needed(current_coverage, years, medical_inflation)
    gap = max(0.0, needed - current_coverage)
    gap_pct = (gap / current_coverage * 100) if current_coverage > 0 else 0.0
    return {
        "current_coverage": round(current_coverage, 2),
        "needed_in_future": round(needed, 2),
        "years": years,
        "inflation_rate": medical_inflation,
        "gap": round(gap, 2),
        "gap_pct": round(gap_pct, 1),
        "note": (
            f"At {medical_inflation*100:.0f}% medical inflation, "
            f"₹{current_coverage/1e5:.1f}L coverage today will feel like "
            f"₹{needed/1e5:.1f}L in {years} years."
        ),
    }
