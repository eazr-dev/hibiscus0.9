"""
Premium Adequacy Formulas
==========================
Determine whether life/health coverage is adequate for a user's profile.

Methods:
  - HLV (Human Life Value) — income replacement approach
  - Income Multiple — quick rule-of-thumb
  - Health cover needed — age/city/family-size heuristic

All amounts in INR. Inflation/discount rates as decimals.
NEVER pass results to LLM without confidence attribution.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import math
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AdequacyResult:
    current_coverage: float
    recommended_coverage: float
    gap: float
    gap_percentage: float
    method: str
    reasoning: str
    is_adequate: bool = False

    def __post_init__(self):
        self.is_adequate = self.gap <= 0
        self.gap = max(0.0, self.gap)


def hlv_method(
    annual_income: float,
    years_to_retirement: int,
    inflation: float = 0.06,
    discount: float = 0.08,
    existing_coverage: float = 0.0,
) -> AdequacyResult:
    """
    Human Life Value method — PV of future income streams.

    HLV = Annual Income × [(1 - (1+inflation)^n / (1+discount)^n) / (discount - inflation)]

    Args:
        annual_income: Current annual income
        years_to_retirement: Working years remaining
        inflation: Expected income growth / inflation rate (default 6%)
        discount: Discount rate (default 8% — risk-free + premium)
        existing_coverage: Existing life cover (deducted from recommendation)

    Returns:
        AdequacyResult with HLV-based recommendation
    """
    if years_to_retirement <= 0:
        return AdequacyResult(
            current_coverage=existing_coverage,
            recommended_coverage=0.0,
            gap=0.0,
            gap_percentage=0.0,
            method="hlv",
            reasoning="No working years remaining — coverage may not be needed.",
        )

    n = years_to_retirement
    if abs(discount - inflation) < 1e-9:
        # Edge case: equal rates
        hlv = annual_income * n
    else:
        # Growing annuity PV
        hlv = annual_income * (1 - ((1 + inflation) / (1 + discount)) ** n) / (discount - inflation)

    hlv = max(0.0, hlv)
    recommended = hlv
    gap = recommended - existing_coverage

    return AdequacyResult(
        current_coverage=round(existing_coverage, 2),
        recommended_coverage=round(recommended, 2),
        gap=round(gap, 2),
        gap_percentage=round((gap / recommended * 100) if recommended > 0 else 0, 1),
        method="hlv",
        reasoning=(
            f"HLV method: ₹{annual_income/1e5:.1f}L annual income × "
            f"{n} years remaining at {inflation*100:.0f}% growth / {discount*100:.0f}% discount "
            f"= ₹{recommended/1e5:.1f}L cover needed."
        ),
    )


def income_multiple_method(
    annual_income: float,
    dependents: int,
    existing_coverage: float = 0.0,
    age: int = 35,
) -> AdequacyResult:
    """
    Income multiple quick rule — thumb for life cover.

    Multiple varies by age:
      <30: 20×  |  30-40: 15×  |  40-50: 10×  |  50+: 7×
    Add 2× per dependent beyond 2.

    Args:
        annual_income: Current annual income
        dependents: Number of financial dependents
        existing_coverage: Existing life cover
        age: User's age (affects recommended multiple)

    Returns:
        AdequacyResult with income-multiple recommendation
    """
    if age < 30:
        base_multiple = 20
    elif age < 40:
        base_multiple = 15
    elif age < 50:
        base_multiple = 10
    else:
        base_multiple = 7

    extra = max(0, dependents - 2) * 2
    multiple = base_multiple + extra
    recommended = annual_income * multiple
    gap = recommended - existing_coverage

    return AdequacyResult(
        current_coverage=round(existing_coverage, 2),
        recommended_coverage=round(recommended, 2),
        gap=round(gap, 2),
        gap_percentage=round((gap / recommended * 100) if recommended > 0 else 0, 1),
        method="income_multiple",
        reasoning=(
            f"Income multiple: {multiple}× annual income "
            f"({base_multiple}× base for age {age}, +{extra}× for {dependents} dependents) "
            f"= ₹{recommended/1e5:.1f}L recommended."
        ),
    )


def health_cover_needed(
    city_tier: str,
    family_size: int,
    age: int,
    existing_coverage: float = 0.0,
) -> AdequacyResult:
    """
    Health sum insured recommendation based on city tier, family size, age.

    Benchmarks (2025 IRDAI / industry data):
      Metro (Mumbai/Delhi/Bengaluru/Chennai):
        Individual <40: ₹10L | Family 2-4: ₹25L | Family 5+: ₹50L
      Tier 1 (Pune/Hyderabad/Kolkata/Ahmedabad):
        Individual <40: ₹7L | Family 2-4: ₹15L | Family 5+: ₹25L
      Tier 2 (other cities):
        Individual <40: ₹5L | Family 2-4: ₹10L | Family 5+: ₹15L
    Age >60: add 50% to base (higher hospitalisation costs)

    Args:
        city_tier: "metro" | "tier1" | "tier2"
        family_size: Number of insured members
        age: Primary insured's age
        existing_coverage: Current sum insured

    Returns:
        AdequacyResult with health cover recommendation
    """
    benchmarks = {
        "metro": {
            "individual": 10_00_000,
            "family_small": 25_00_000,
            "family_large": 50_00_000,
        },
        "tier1": {
            "individual": 7_00_000,
            "family_small": 15_00_000,
            "family_large": 25_00_000,
        },
        "tier2": {
            "individual": 5_00_000,
            "family_small": 10_00_000,
            "family_large": 15_00_000,
        },
    }

    tier_key = city_tier.lower() if city_tier.lower() in benchmarks else "tier2"
    tiers = benchmarks[tier_key]

    if family_size <= 1:
        base = tiers["individual"]
    elif family_size <= 4:
        base = tiers["family_small"]
    else:
        base = tiers["family_large"]

    # Age adjustment
    if age >= 60:
        recommended = base * 1.5
        age_note = " (+50% for age ≥60)"
    else:
        recommended = base
        age_note = ""

    gap = recommended - existing_coverage

    return AdequacyResult(
        current_coverage=round(existing_coverage, 2),
        recommended_coverage=round(recommended, 2),
        gap=round(gap, 2),
        gap_percentage=round((gap / recommended * 100) if recommended > 0 else 0, 1),
        method="health_benchmark",
        reasoning=(
            f"Health benchmark ({city_tier}, family of {family_size}, age {age}{age_note}): "
            f"₹{recommended/1e5:.1f}L recommended sum insured."
        ),
    )
