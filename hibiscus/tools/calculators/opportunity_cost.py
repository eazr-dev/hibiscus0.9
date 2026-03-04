"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Opportunity cost tool — compares insurance vs alternative investment returns.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict

from hibiscus.knowledge.formulas.opportunity_cost import (
    endowment_vs_term_mf,
)


async def calculate_opportunity_cost(
    endowment_premium: float,
    sum_assured: float,
    policy_term: int,
    maturity_value: float,
    *,
    age: int = 30,
    term_premium_estimate: float = 0.0,
    mf_return_rate: float = 0.12,
) -> Dict[str, Any]:
    """
    Compare endowment/ULIP vs term + mutual fund strategy.

    Shows what the user would have if they bought term insurance and
    invested the premium difference in a mutual fund.
    """
    result = endowment_vs_term_mf(
        endowment_premium=endowment_premium,
        sum_assured=sum_assured,
        policy_term=policy_term,
        maturity_value=maturity_value,
        age=age,
        term_premium_estimate=term_premium_estimate,
        mf_return_rate=mf_return_rate,
    )
    return {
        "endowment_maturity": result.endowment_maturity,
        "term_plus_mf_corpus": result.term_plus_mf_corpus,
        "difference": result.difference,
        "mf_return_rate": mf_return_rate,
        "recommendation": result.recommendation,
        "annual_savings": result.annual_savings,
    }
