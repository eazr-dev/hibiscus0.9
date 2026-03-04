"""
Compound Growth Formulas
=========================
Time-value-of-money calculations for insurance and investment analysis.

Used by: PortfolioOptimizer, TaxAdvisor, OpportunityCostCalculator.
All values in INR. All rates as decimals (0.12 = 12%).
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import math
from dataclasses import dataclass, field
from typing import Optional


def fv_lumpsum(pv: float, rate: float, years: int) -> float:
    """
    Future Value of a lump sum investment.

    FV = PV × (1 + r)^n

    Args:
        pv: Present value (initial investment)
        rate: Annual rate of return (e.g. 0.12 for 12%)
        years: Investment horizon in years

    Returns:
        Future value
    """
    if years < 0:
        raise ValueError("years must be >= 0")
    return pv * ((1 + rate) ** years)


def fv_annuity(pmt: float, rate: float, years: int) -> float:
    """
    Future Value of a regular annual payment (end-of-year).

    FV = PMT × [((1+r)^n - 1) / r]

    Args:
        pmt: Annual payment (e.g. annual premium)
        rate: Annual rate of return
        years: Number of years

    Returns:
        Future value of the annuity stream
    """
    if years < 0:
        raise ValueError("years must be >= 0")
    if rate == 0:
        return pmt * years
    return pmt * (((1 + rate) ** years - 1) / rate)


def pv(fv: float, rate: float, years: int) -> float:
    """
    Present Value of a future amount.

    PV = FV / (1 + r)^n

    Args:
        fv: Future value
        rate: Annual discount rate
        years: Number of years

    Returns:
        Present value
    """
    if years < 0:
        raise ValueError("years must be >= 0")
    if rate == -1:
        raise ValueError("rate cannot be -1")
    return fv / ((1 + rate) ** years)


def emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Equated Monthly Instalment (standard reducing-balance formula).

    EMI = P × r × (1+r)^n / ((1+r)^n - 1)
    where r = monthly rate, n = tenure months

    Args:
        principal: Loan / financing amount
        annual_rate: Annual interest rate (e.g. 0.12 for 12%)
        tenure_months: Loan tenure in months

    Returns:
        Monthly EMI amount
    """
    if tenure_months <= 0:
        raise ValueError("tenure_months must be > 0")
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return principal / tenure_months
    n = tenure_months
    r = monthly_rate
    return principal * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)


def cagr(initial: float, final: float, years: int) -> float:
    """
    Compound Annual Growth Rate.

    CAGR = (FV/PV)^(1/n) - 1

    Args:
        initial: Initial value
        final: Final value
        years: Number of years

    Returns:
        CAGR as decimal (e.g. 0.12 for 12%)
    """
    if years <= 0:
        raise ValueError("years must be > 0")
    if initial <= 0:
        raise ValueError("initial must be > 0")
    return (final / initial) ** (1 / years) - 1


def doubling_years(rate: float) -> float:
    """
    Rule of 72: approximate years to double at given rate.

    Args:
        rate: Annual rate (decimal)

    Returns:
        Approximate years to double
    """
    if rate <= 0:
        raise ValueError("rate must be > 0")
    return 72 / (rate * 100)
