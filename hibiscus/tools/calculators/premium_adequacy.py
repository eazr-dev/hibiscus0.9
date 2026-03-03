"""
Premium Adequacy Tool
=====================
Agent-callable tool wrapping knowledge/formulas/premium_adequacy.py.
"""
from typing import Any, Dict, Optional

from hibiscus.knowledge.formulas.premium_adequacy import (
    hlv_method,
    income_multiple_method,
    health_cover_needed,
)


async def calculate_life_cover_needed(
    annual_income: float,
    age: int,
    retirement_age: int = 60,
    *,
    existing_cover: float = 0.0,
    liabilities: float = 0.0,
    expenses_annual: Optional[float] = None,
    inflation_rate: float = 0.06,
    discount_rate: float = 0.08,
) -> Dict[str, Any]:
    """
    Calculate how much life insurance cover is needed using HLV and income multiple methods.

    Returns both calculations and the gap (needed - existing).
    """
    hlv = hlv_method(
        annual_income=annual_income,
        age=age,
        retirement_age=retirement_age,
        expenses_annual=expenses_annual,
        inflation_rate=inflation_rate,
        discount_rate=discount_rate,
    )
    income_mult = income_multiple_method(annual_income, age)

    recommended = max(hlv, income_mult) + liabilities
    gap = recommended - existing_cover

    return {
        "hlv_method": hlv,
        "income_multiple_method": income_mult,
        "liabilities": liabilities,
        "recommended_cover": recommended,
        "existing_cover": existing_cover,
        "gap": max(gap, 0),
        "adequate": gap <= 0,
    }


async def calculate_health_cover_needed(
    city_tier: int = 1,
    family_size: int = 2,
    *,
    has_senior: bool = False,
    existing_cover: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate recommended health insurance cover based on city and family.

    Returns recommendation with gap analysis.
    """
    needed = health_cover_needed(city_tier, family_size, has_senior)
    gap = needed - existing_cover

    return {
        "recommended_cover": needed,
        "existing_cover": existing_cover,
        "gap": max(gap, 0),
        "adequate": gap <= 0,
        "city_tier": city_tier,
        "family_size": family_size,
    }
