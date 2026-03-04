"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Tax benefit tool — computes Section 80C/80D deductions and 10(10D) exemptions.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, Optional

from hibiscus.knowledge.formulas.tax_benefit import (
    compute_80c_benefit,
    compute_80d_benefit,
    check_10_10d_exemption,
    compute_total_tax_benefit,
)


async def calculate_tax_benefit(
    annual_premium: float,
    tax_bracket: float,
    *,
    policy_type: str = "life",
    age: int = 30,
    is_senior: bool = False,
    sum_assured: float = 0.0,
    health_premium_self: float = 0.0,
    health_premium_parents: float = 0.0,
    parents_senior: bool = False,
    preventive_checkup: float = 0.0,
    existing_80c: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate complete tax benefits for insurance premiums.

    Covers Section 80C (life), 80D (health), and 10(10D) (maturity exemption).
    """
    result_80c = compute_80c_benefit(
        annual_premium=annual_premium,
        tax_bracket=tax_bracket,
        existing_80c=existing_80c,
    )

    result_80d = compute_80d_benefit(
        premium_self=health_premium_self,
        premium_parents=health_premium_parents,
        tax_bracket=tax_bracket,
        is_senior=is_senior,
        parents_senior=parents_senior,
        preventive_checkup=preventive_checkup,
    )

    is_exempt = check_10_10d_exemption(
        annual_premium=annual_premium,
        sum_assured=sum_assured,
        policy_start_year=2020,
    )

    total = compute_total_tax_benefit(
        life_premium=annual_premium,
        health_premium_self=health_premium_self,
        health_premium_parents=health_premium_parents,
        tax_bracket=tax_bracket,
        is_senior=is_senior,
        parents_senior=parents_senior,
        existing_80c=existing_80c,
    )

    return {
        "section_80c": result_80c,
        "section_80d": result_80d,
        "section_10_10d_exempt": is_exempt,
        "total_tax_saving": total,
        "tax_bracket": tax_bracket,
    }
