"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Inflation adjustment tool — projects future costs using Indian CPI inflation rates.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict

from hibiscus.knowledge.formulas.inflation import (
    inflate,
    real_coverage_needed,
    deflate,
    inflation_gap,
)


async def calculate_future_value(
    present_value: float,
    years: int,
    inflation_rate: float = 0.06,
) -> Dict[str, Any]:
    """
    Calculate inflation-adjusted future value.

    Example: ₹10L today → ₹17.9L in 10 years at 6% inflation.
    """
    future = inflate(present_value, years, inflation_rate)
    return {
        "present_value": present_value,
        "future_value": future,
        "years": years,
        "inflation_rate": inflation_rate,
        "multiplier": round(future / present_value, 2) if present_value else 0,
    }


async def calculate_coverage_needed(
    current_expenses: float,
    years_to_cover: int,
    inflation_rate: float = 0.06,
) -> Dict[str, Any]:
    """
    Calculate how much insurance cover is needed accounting for inflation.
    """
    needed = real_coverage_needed(current_expenses, years_to_cover, inflation_rate)
    return {
        "current_annual_expenses": current_expenses,
        "years_to_cover": years_to_cover,
        "coverage_needed": needed,
        "inflation_rate": inflation_rate,
    }


async def calculate_inflation_gap(
    sum_insured: float,
    years_since_purchase: int,
    inflation_rate: float = 0.06,
) -> Dict[str, Any]:
    """
    Calculate how much coverage has eroded due to inflation.
    """
    gap = inflation_gap(sum_insured, years_since_purchase, inflation_rate)
    real_value = deflate(sum_insured, years_since_purchase, inflation_rate)
    return {
        "nominal_cover": sum_insured,
        "real_value_today": real_value,
        "inflation_gap": gap,
        "erosion_pct": round((gap / sum_insured) * 100, 1) if sum_insured else 0,
        "years_since_purchase": years_since_purchase,
    }
