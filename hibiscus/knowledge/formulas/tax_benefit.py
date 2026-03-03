"""
Insurance Tax Benefit Calculator
==================================
Computes tax benefits under Indian Income Tax Act for insurance premiums.

Sections:
- 80C: Life insurance premium (max ₹1.5L, combined with other 80C investments)
- 80D: Health insurance premium (max ₹25K/₹50K/₹1L depending on age)
- 10(10D): Maturity proceeds exemption (conditions apply)
- 80CCC: Pension fund (within 80C limit)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TaxBenefitResult:
    section: str
    eligible_deduction: float    # Amount that can be deducted
    actual_premium: float        # Premium paid
    tax_saving: float            # Tax saved based on tax bracket
    notes: str
    conditions_met: bool
    conditions_failed: list[str]


def compute_80c_benefit(
    life_premium: float,
    sum_assured: float,
    annual_premium: float,
    policy_issue_date_after_2012: bool = True,
    tax_bracket: float = 0.30,    # 30% = highest bracket
    existing_80c_investments: float = 0.0,
) -> TaxBenefitResult:
    """
    Compute Section 80C benefit for life insurance premium.

    Conditions (policies after Apr 1, 2012):
    - Sum assured must be >= 10x annual premium
    - Max deduction: ₹1.5L (shared with other 80C investments)
    - If sum assured < 10x premium: proportionate deduction (premium × SA/10SA)
    """
    MAX_80C = 150_000  # ₹1.5 lakh

    conditions_failed = []
    eligible = life_premium

    if policy_issue_after_2012 := policy_issue_date_after_2012:
        min_sa_required = annual_premium * 10
        if sum_assured < min_sa_required:
            # Proportionate deduction
            ratio = sum_assured / (annual_premium * 10)
            eligible = life_premium * ratio
            conditions_failed.append(
                f"Sum assured (₹{sum_assured:,.0f}) < 10× annual premium (₹{min_sa_required:,.0f}). "
                f"Deduction restricted to {ratio:.0%} of premium."
            )

    # Apply 80C ceiling (net of other investments)
    remaining_80c = max(0, MAX_80C - existing_80c_investments)
    deductible = min(eligible, remaining_80c)

    tax_saving = deductible * tax_bracket

    return TaxBenefitResult(
        section="80C",
        eligible_deduction=round(deductible, 2),
        actual_premium=round(life_premium, 2),
        tax_saving=round(tax_saving, 2),
        notes=(
            f"Life insurance premium deductible up to ₹1.5L under Section 80C "
            f"(combined with PPF, ELSS, NSC, etc.)"
        ),
        conditions_met=len(conditions_failed) == 0,
        conditions_failed=conditions_failed,
    )


def compute_80d_benefit(
    self_family_premium: float,
    parent_premium: float = 0.0,
    self_age: int = 35,
    parent_age: int = 0,      # 0 = no parents covered
    tax_bracket: float = 0.30,
    includes_preventive_health_checkup: bool = False,
) -> TaxBenefitResult:
    """
    Compute Section 80D benefit for health insurance premium.

    Slabs:
    - Self + family (age < 60): max ₹25,000
    - Self + family (age >= 60 OR senior): max ₹50,000
    - Parents (age < 60): max ₹25,000 additional
    - Parents (age >= 60): max ₹50,000 additional
    - Max if both policyholder and parents are 60+: ₹1,00,000

    Preventive health checkup: ₹5,000 within the above limits.
    """
    # Self + family limit
    self_limit = 50_000 if self_age >= 60 else 25_000
    self_deductible = min(self_family_premium, self_limit)

    # Preventive health checkup: ₹5000 included in self_limit
    if includes_preventive_health_checkup:
        # If checkup included in premium, it's within the 25K/50K limit
        pass

    # Parents' limit
    parent_deductible = 0.0
    if parent_premium > 0 and parent_age > 0:
        parent_limit = 50_000 if parent_age >= 60 else 25_000
        parent_deductible = min(parent_premium, parent_limit)

    total_deductible = self_deductible + parent_deductible
    tax_saving = total_deductible * tax_bracket

    notes_parts = [f"Self + family: ₹{self_deductible:,.0f} (limit ₹{self_limit:,.0f})"]
    if parent_deductible:
        parent_limit = 50_000 if parent_age >= 60 else 25_000
        notes_parts.append(f"Parents: ₹{parent_deductible:,.0f} (limit ₹{parent_limit:,.0f})")

    return TaxBenefitResult(
        section="80D",
        eligible_deduction=round(total_deductible, 2),
        actual_premium=round(self_family_premium + parent_premium, 2),
        tax_saving=round(tax_saving, 2),
        notes="; ".join(notes_parts),
        conditions_met=True,
        conditions_failed=[],
    )


def check_10_10d_exemption(
    sum_assured: float,
    annual_premium: float,
    policy_year_of_issue: int,
    is_ulip: bool = False,
    ulip_annual_premium: float = 0.0,
) -> dict:
    """
    Check if maturity proceeds qualify for Section 10(10D) exemption.

    Key conditions:
    1. Sum assured >= 10x annual premium (for policies after Apr 2012)
    2. For ULIPs after Feb 1, 2021: annual premium <= ₹2.5L for exemption
       (If > ₹2.5L, gains taxable at 10% LTCG)
    3. Keyman insurance and high-premium ULIP excluded from exemption
    """
    result = {
        "exempt": True,
        "conditions": [],
        "warnings": [],
        "tax_treatment": "Maturity proceeds fully exempt under Section 10(10D)",
    }

    # Condition 1: SA/Premium ratio
    if policy_year_of_issue >= 2012:
        min_sa = annual_premium * 10
        if sum_assured < min_sa:
            result["exempt"] = False
            result["conditions"].append(
                f"Sum assured (₹{sum_assured:,.0f}) < 10× premium (₹{min_sa:,.0f}). "
                "Proportionate exemption applies."
            )

    # Condition 2: ULIP premium cap
    if is_ulip:
        if policy_year_of_issue >= 2021 and ulip_annual_premium > 250_000:
            result["exempt"] = False
            result["tax_treatment"] = (
                f"ULIP annual premium ₹{ulip_annual_premium:,.0f} > ₹2.5L. "
                "Gains taxable at 10% LTCG (equity funds) or applicable rate."
            )
            result["warnings"].append(
                "ULIP premiums > ₹2.5L/year lose tax exemption on maturity (Budget 2021)"
            )

    return result


def compute_total_tax_benefit(
    life_premium: float = 0.0,
    health_premium: float = 0.0,
    parent_health_premium: float = 0.0,
    sum_assured: float = 0.0,
    annual_life_premium: float = 0.0,
    self_age: int = 35,
    parent_age: int = 0,
    tax_bracket: float = 0.30,
    existing_80c_investments: float = 0.0,
) -> dict:
    """Compute complete tax benefit picture for a user's insurance portfolio."""
    results = {}
    total_tax_saving = 0.0

    if life_premium > 0:
        r80c = compute_80c_benefit(
            life_premium=life_premium,
            sum_assured=sum_assured,
            annual_premium=annual_life_premium,
            tax_bracket=tax_bracket,
            existing_80c_investments=existing_80c_investments,
        )
        results["80C"] = r80c
        total_tax_saving += r80c.tax_saving

    if health_premium > 0 or parent_health_premium > 0:
        r80d = compute_80d_benefit(
            self_family_premium=health_premium,
            parent_premium=parent_health_premium,
            self_age=self_age,
            parent_age=parent_age,
            tax_bracket=tax_bracket,
        )
        results["80D"] = r80d
        total_tax_saving += r80d.tax_saving

    return {
        "sections": results,
        "total_tax_saving": round(total_tax_saving, 2),
        "effective_cost_reduction": (
            f"You save ₹{total_tax_saving:,.0f} in taxes, reducing the effective cost of your insurance."
        ),
        "disclaimer": (
            "Tax computations are indicative. Actual tax benefit depends on total income, "
            "other deductions, and applicable tax regime. Consult a CA for precise computation."
        ),
    }
