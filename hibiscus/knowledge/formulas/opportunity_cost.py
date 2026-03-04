"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Opportunity cost formula — compares insurance vs mutual fund/FD/PPF alternatives.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from dataclasses import dataclass


@dataclass
class OpportunityCostResult:
    endowment_premium_total: float   # Total premiums paid into endowment
    term_premium_total: float        # Total term insurance premiums (much lower)
    savings_invested: float          # Annual savings redirected to MF (premium diff × years)
    investment_value: float          # Future value of savings in MF at mf_return
    endowment_maturity_value: float  # What the endowment actually pays at maturity
    opportunity_cost: float          # MF value minus endowment maturity value
    verdict: str                     # "MF strategy better by ₹X.XL" or "Endowment better"
    verdict_simple: str              # One sentence for response
    annual_savings: float            # Annual premium difference (endowment - term)
    years: int
    mf_return: float


def endowment_vs_term_mf(
    endowment_premium: float,
    term_premium: float,
    endowment_sum_assured: float,
    years: int,
    mf_return: float = 0.12,
) -> OpportunityCostResult:
    """
    Compare endowment insurance vs. term + mutual fund strategy.

    Strategy:
      Option A (Endowment): Pay endowment premium every year → get maturity value at end.
      Option B (Term + MF): Pay term premium (much lower) + invest difference in MF.

    Endowment maturity value is approximated as sum_assured (most endowments
    pay SA + accrued bonus; we use SA as conservative floor).
    For more accuracy, caller should pass actual maturity value if known.

    Args:
        endowment_premium: Annual endowment policy premium (₹)
        term_premium: Annual term insurance premium for equivalent cover (₹)
        endowment_sum_assured: Endowment maturity / sum assured value (₹)
        years: Policy term in years
        mf_return: Expected annual MF return (default 12%)

    Returns:
        OpportunityCostResult with full comparison
    """
    if years <= 0:
        raise ValueError("years must be > 0")
    if endowment_premium < term_premium:
        # Unusual: endowment cheaper than term — still compute correctly
        pass

    # Total premiums
    endowment_total = endowment_premium * years
    term_total = term_premium * years
    annual_savings = endowment_premium - term_premium

    # Future value of annual savings invested in MF (end-of-year payments)
    if mf_return == 0:
        investment_value = annual_savings * years
    else:
        investment_value = annual_savings * (((1 + mf_return) ** years - 1) / mf_return)

    # Endowment maturity (using SA as floor)
    endowment_maturity = endowment_sum_assured

    opportunity_cost = investment_value - endowment_maturity

    if opportunity_cost > 0:
        diff_lakh = opportunity_cost / 1e5
        verdict = f"Term + MF strategy better by ₹{diff_lakh:.1f}L over {years} years"
        verdict_simple = (
            f"By paying term insurance (₹{term_premium/1e3:.0f}K/yr) and investing "
            f"the ₹{annual_savings/1e3:.0f}K annual savings in mutual funds at {mf_return*100:.0f}%, "
            f"you could accumulate ₹{investment_value/1e5:.1f}L vs the endowment's "
            f"₹{endowment_maturity/1e5:.1f}L — a difference of ₹{diff_lakh:.1f}L."
        )
    else:
        diff_lakh = abs(opportunity_cost) / 1e5
        verdict = f"Endowment better by ₹{diff_lakh:.1f}L over {years} years"
        verdict_simple = (
            f"In this case, the endowment policy at ₹{endowment_maturity/1e5:.1f}L maturity "
            f"outperforms the term + MF strategy by ₹{diff_lakh:.1f}L."
        )

    return OpportunityCostResult(
        endowment_premium_total=round(endowment_total, 2),
        term_premium_total=round(term_total, 2),
        savings_invested=round(annual_savings * years, 2),
        investment_value=round(investment_value, 2),
        endowment_maturity_value=round(endowment_maturity, 2),
        opportunity_cost=round(opportunity_cost, 2),
        verdict=verdict,
        verdict_simple=verdict_simple,
        annual_savings=round(annual_savings, 2),
        years=years,
        mf_return=mf_return,
    )
