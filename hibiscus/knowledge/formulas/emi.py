"""
EMI Formulas — Insurance Premium Financing
==========================================
Calculate EMIs for Insurance Premium Financing (IPF) and
Surrender Value Financing (SVF) loans.

Deterministic reducing-balance calculations only.
NEVER let LLM generate loan repayment numbers.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class AmortizationRow:
    month: int
    emi: float
    principal_paid: float
    interest_paid: float
    balance: float


@dataclass
class EMIResult:
    principal: float
    monthly_emi: float
    total_payment: float
    total_interest: float
    annual_rate: float
    tenure_months: int
    amortization_schedule: List[AmortizationRow] = field(default_factory=list)

    @property
    def effective_annual_cost(self) -> float:
        """Effective Annual Rate (EAR) accounting for monthly compounding."""
        monthly = self.annual_rate / 12
        return (1 + monthly) ** 12 - 1


def _build_amortization(
    principal: float,
    monthly_rate: float,
    tenure_months: int,
    monthly_emi: float,
) -> List[AmortizationRow]:
    """Build full amortization schedule."""
    schedule = []
    balance = principal
    for month in range(1, tenure_months + 1):
        interest = balance * monthly_rate
        principal_paid = monthly_emi - interest
        balance -= principal_paid
        balance = max(0.0, balance)
        schedule.append(AmortizationRow(
            month=month,
            emi=round(monthly_emi, 2),
            principal_paid=round(principal_paid, 2),
            interest_paid=round(interest, 2),
            balance=round(balance, 2),
        ))
    return schedule


def _calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> EMIResult:
    """Core EMI calculation — used by IPF and SVF variants."""
    if principal <= 0:
        raise ValueError("principal must be > 0")
    if tenure_months <= 0:
        raise ValueError("tenure_months must be > 0")
    if annual_rate < 0:
        raise ValueError("annual_rate must be >= 0")

    monthly_rate = annual_rate / 12

    if monthly_rate == 0:
        monthly_emi = principal / tenure_months
    else:
        n = tenure_months
        r = monthly_rate
        monthly_emi = principal * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)

    total_payment = monthly_emi * tenure_months
    total_interest = total_payment - principal
    schedule = _build_amortization(principal, monthly_rate, tenure_months, monthly_emi)

    return EMIResult(
        principal=round(principal, 2),
        monthly_emi=round(monthly_emi, 2),
        total_payment=round(total_payment, 2),
        total_interest=round(total_interest, 2),
        annual_rate=annual_rate,
        tenure_months=tenure_months,
        amortization_schedule=schedule,
    )


def ipf_emi(
    loan_amount: float,
    annual_rate: float = 0.12,
    tenure_months: int = 12,
) -> EMIResult:
    """
    Insurance Premium Financing EMI.

    User borrows money to pay an upfront insurance premium, repays over tenure.
    Typical IPF: 12-24 months at 12-15% p.a.

    Args:
        loan_amount: Total premium to be financed
        annual_rate: Annual interest rate (default 12% p.a.)
        tenure_months: Repayment tenure in months (typically 6-24)

    Returns:
        EMIResult with full amortization schedule
    """
    return _calculate_emi(loan_amount, annual_rate, tenure_months)


def svf_emi(
    surrender_value: float,
    annual_rate: float = 0.10,
    tenure_months: int = 24,
) -> EMIResult:
    """
    Surrender Value Financing EMI.

    User borrows against policy surrender value to avoid surrendering.
    Typically lower rate than IPF since SV is collateral.
    Typical SVF: 24-48 months at 10-13% p.a.

    Args:
        surrender_value: Loan amount (typically 80-90% of SV)
        annual_rate: Annual interest rate (default 10% p.a.)
        tenure_months: Repayment tenure in months

    Returns:
        EMIResult with full amortization schedule
    """
    return _calculate_emi(surrender_value, annual_rate, tenure_months)
