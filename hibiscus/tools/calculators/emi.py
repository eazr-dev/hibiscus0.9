"""
EMI Calculator Tool (IPF/SVF)
==============================
Agent-callable tool wrapping knowledge/formulas/emi.py.
"""
from typing import Any, Dict

from hibiscus.knowledge.formulas.emi import ipf_emi, svf_emi


async def calculate_ipf_emi(
    premium_amount: float,
    tenure_months: int = 12,
    interest_rate: float = 0.14,
) -> Dict[str, Any]:
    """
    Calculate Insurance Premium Financing (IPF) EMI.

    IPF lets users pay annual premiums in monthly installments.
    This is a key EAZR product.
    """
    result = ipf_emi(premium_amount, tenure_months, interest_rate)
    return {
        "monthly_emi": result.monthly_emi,
        "total_payable": result.total_payable,
        "total_interest": result.total_interest,
        "effective_rate": result.effective_rate,
        "premium_amount": premium_amount,
        "tenure_months": tenure_months,
    }


async def calculate_svf_emi(
    surrender_value: float,
    loan_amount: float,
    tenure_months: int = 36,
    interest_rate: float = 0.12,
) -> Dict[str, Any]:
    """
    Calculate Surrender Value Financing (SVF) EMI.

    SVF lets users get a loan against their policy's surrender value
    instead of actually surrendering. This preserves the policy.
    """
    result = svf_emi(surrender_value, loan_amount, tenure_months, interest_rate)
    return {
        "monthly_emi": result.monthly_emi,
        "total_payable": result.total_payable,
        "total_interest": result.total_interest,
        "effective_rate": result.effective_rate,
        "surrender_value": surrender_value,
        "loan_amount": loan_amount,
        "tenure_months": tenure_months,
    }
