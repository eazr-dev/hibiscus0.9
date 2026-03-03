"""
Surrender Value Formulas
=========================
Guaranteed Surrender Value (GSV) and Special Surrender Value (SSV) calculations.

These are the core financial formulas used by the SurrenderCalculatorAgent.

NEVER pass these results to LLM and ask it to make up numbers.
Every output is based on deterministic formulas with stated assumptions.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SurrenderValueResult:
    year: int
    gsv: float           # Guaranteed Surrender Value
    ssv: Optional[float] # Special Surrender Value (if higher)
    paid_premiums: float # Total premiums paid to date
    sv_percentage: float # SV as % of premiums paid
    notes: str


def gsv_percentage(policy_year: int) -> float:
    """
    IRDAI minimum GSV percentages by policy year.
    (IRDAI guidelines — standard for traditional plans)
    """
    if policy_year < 3:
        return 0.0   # No surrender value in first 3 years
    elif policy_year == 3:
        return 0.30  # 30% of paid premiums
    elif policy_year == 4:
        return 0.50
    elif policy_year == 5:
        return 0.50
    elif 6 <= policy_year <= 7:
        return 0.50
    elif 8 <= policy_year <= 9:
        return 0.50
    elif 10 <= policy_year <= 11:
        return 0.60
    elif 12 <= policy_year <= 14:
        return 0.65
    elif 15 <= policy_year <= 19:
        return 0.70
    elif policy_year >= 20:
        return 0.90
    return 0.0


def calculate_gsv(
    annual_premium: float,
    policy_year: int,
    bonus_accumulated: float = 0.0,
    premium_term: int = 20,
) -> float:
    """
    Calculate Guaranteed Surrender Value.

    GSV = GSV% × Premiums Paid + Bonus Value
    Bonus value on surrender = 30% of accumulated bonuses (standard)

    Args:
        annual_premium: Annual premium paid
        policy_year: Year of surrender (must be ≥ 3 for any value)
        bonus_accumulated: Total bonuses accumulated (for with-profit plans)
        premium_term: Total premium payment term
    """
    premiums_paid = annual_premium * min(policy_year, premium_term)
    gsv_pct = gsv_percentage(policy_year)
    gsv = premiums_paid * gsv_pct
    # Bonus surrender value: typically 30% of accumulated bonus
    bonus_sv = bonus_accumulated * 0.30
    return gsv + bonus_sv


def calculate_surrender_projection(
    annual_premium: float,
    policy_term: int,
    premium_term: int,
    sum_assured: float,
    bonus_rate_per_1000: float = 35.0,  # ₹35 per ₹1000 SA per year (LIC typical)
    start_year: int = 1,
) -> list[SurrenderValueResult]:
    """
    Year-by-year surrender value projection.

    Args:
        annual_premium: Annual premium
        policy_term: Total policy duration
        premium_term: Premium payment term
        sum_assured: Policy sum assured
        bonus_rate_per_1000: Bonus accrual per ₹1000 SA (0 for non-participating plans)
        start_year: Start projection from this year

    Returns:
        List of SurrenderValueResult for each year
    """
    results = []
    cumulative_bonus = 0.0

    for year in range(start_year, policy_term + 1):
        premiums_paid = annual_premium * min(year, premium_term)
        cumulative_bonus += (sum_assured / 1000) * bonus_rate_per_1000

        gsv = calculate_gsv(annual_premium, year, cumulative_bonus, premium_term)

        sv_pct = (gsv / premiums_paid * 100) if premiums_paid > 0 else 0

        notes = []
        if year < 3:
            notes.append("No surrender value in first 3 years")
        if year == 3:
            notes.append("First year of surrender value availability")
        if sv_pct < 50:
            notes.append("Significant loss vs premiums paid — consider holding")

        results.append(SurrenderValueResult(
            year=year,
            gsv=round(gsv, 2),
            ssv=None,  # SSV requires insurer-specific calculation
            paid_premiums=round(premiums_paid, 2),
            sv_percentage=round(sv_pct, 1),
            notes="; ".join(notes) if notes else "Standard surrender",
        ))

    return results
