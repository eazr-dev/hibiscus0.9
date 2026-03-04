"""
Surrender Value Calculator Tool
================================
Agent-callable tool wrapping knowledge/formulas/surrender_value.py.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List, Optional

from hibiscus.knowledge.formulas.surrender_value import (
    calculate_gsv,
    calculate_surrender_projection,
)


async def compute_surrender_value(
    total_premiums_paid: float,
    gsv_factor: float,
    bonus_rate: float = 0.0,
    sum_assured: float = 0.0,
    years_paid: int = 0,
) -> Dict[str, Any]:
    """
    Compute Guaranteed Surrender Value (GSV).

    Returns:
        {"gsv": float, "inputs": dict}
    """
    gsv = calculate_gsv(total_premiums_paid, gsv_factor, bonus_rate, sum_assured, years_paid)
    return {
        "gsv": gsv,
        "inputs": {
            "total_premiums_paid": total_premiums_paid,
            "gsv_factor": gsv_factor,
            "bonus_rate": bonus_rate,
        },
    }


async def project_surrender_value(
    annual_premium: float,
    policy_term: int,
    current_year: int,
    sum_assured: float,
    gsv_factors: Optional[List[float]] = None,
    bonus_rate: float = 40.0,
) -> Dict[str, Any]:
    """
    Year-by-year surrender value projection.

    Returns list of {year, premiums_paid, gsv, total_bonus, estimated_sv}.
    """
    projection = calculate_surrender_projection(
        annual_premium=annual_premium,
        policy_term=policy_term,
        current_year=current_year,
        sum_assured=sum_assured,
        gsv_factors=gsv_factors,
        bonus_rate=bonus_rate,
    )
    return {"projection": projection, "current_year": current_year}
