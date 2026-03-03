"""Personal Accident Insurance Helper Functions (EAZR_04 Spec)
Scoring, scenarios, gaps, recommendations for PA insurance policies.
"""

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def _calculate_pa_income_replacement_score(
    coverage_data: dict,
    additional_benefits: dict,
    annual_income: int = 1000000
) -> dict:
    """Score S1: Income Replacement Adequacy (0-100) per EAZR_04 Section 5.2"""
    score = 0
    factors = []
    weekly_income = annual_income / 52

    # Factor 1: Death Benefit vs Income (35 pts)
    ad = coverage_data.get("accidentalDeath", {})
    death_benefit = ad.get("benefitAmount", 0) or coverage_data.get("sumInsured", 0)
    if isinstance(death_benefit, str):
        try:
            death_benefit = float(str(death_benefit).replace(",", "").replace("₹", "").replace("Rs.", "").strip())
        except (ValueError, TypeError):
            death_benefit = 0
    income_multiple = death_benefit / annual_income if annual_income > 0 else 0

    if income_multiple >= 10:
        f1 = 35
    elif income_multiple >= 7:
        f1 = 28
    elif income_multiple >= 5:
        f1 = 22
    elif income_multiple >= 3:
        f1 = 15
    else:
        f1 = 8
    score += f1
    factors.append({
        "name": "Death Benefit vs Income",
        "score": f1, "maxScore": 35,
        "detail": f"{income_multiple:.1f}x annual income (₹{death_benefit:,.0f})"
    })

    # Factor 2: PTD Benefit vs Income (25 pts)
    ptd = coverage_data.get("permanentTotalDisability", {})
    ptd_benefit = ptd.get("benefitAmount", 0) or coverage_data.get("sumInsured", 0)
    if isinstance(ptd_benefit, str):
        try:
            ptd_benefit = float(str(ptd_benefit).replace(",", "").replace("₹", "").replace("Rs.", "").strip())
        except (ValueError, TypeError):
            ptd_benefit = 0
    ptd_multiple = ptd_benefit / annual_income if annual_income > 0 else 0

    if ptd_multiple >= 10:
        f2 = 25
    elif ptd_multiple >= 7:
        f2 = 20
    elif ptd_multiple >= 5:
        f2 = 15
    else:
        f2 = 8
    score += f2
    factors.append({
        "name": "PTD Benefit vs Income",
        "score": f2, "maxScore": 25,
        "detail": f"{ptd_multiple:.1f}x annual income (₹{ptd_benefit:,.0f})"
    })

    # Factor 3: TTD vs Weekly Income (20 pts)
    ttd = coverage_data.get("temporaryTotalDisability", {})
    f3 = 0
    if ttd.get("covered"):
        ttd_weekly = ttd.get("benefitAmount", 0)
        if isinstance(ttd_weekly, str):
            try:
                ttd_weekly = float(str(ttd_weekly).replace(",", "").replace("₹", "").replace("Rs.", "").strip())
            except (ValueError, TypeError):
                ttd_weekly = 0
        if ttd_weekly == 0 and coverage_data.get("sumInsured", 0) > 0:
            pct = ttd.get("benefitPercentage", 1) or 1
            ttd_weekly = float(coverage_data["sumInsured"]) * float(pct) / 100
        ttd_ratio = ttd_weekly / weekly_income if weekly_income > 0 else 0

        if ttd_ratio >= 0.5:
            f3 = 20
        elif ttd_ratio >= 0.3:
            f3 = 15
        elif ttd_ratio >= 0.2:
            f3 = 10
        else:
            f3 = 5
    score += f3
    factors.append({
        "name": "TTD vs Weekly Income",
        "score": f3, "maxScore": 20,
        "detail": "TTD benefit active" if ttd.get("covered") else "No TTD coverage"
    })

    # Factor 4: EMI Coverage (10 pts)
    f4 = 10 if additional_benefits.get("loanEmiCover", {}).get("covered") else 0
    score += f4
    factors.append({
        "name": "EMI Protection",
        "score": f4, "maxScore": 10,
        "detail": "EMI cover active" if f4 > 0 else "No EMI protection"
    })

    # Factor 5: Double Indemnity (10 pts)
    di = ad.get("doubleIndemnity", {})
    f5 = 10 if di.get("applicable") else 0
    score += f5
    factors.append({
        "name": "Double Indemnity",
        "score": f5, "maxScore": 10,
        "detail": "Double benefit for public transport" if f5 > 0 else "No double indemnity"
    })

    return {"score": min(score, 100), "factors": factors}


def _calculate_pa_disability_protection_score(
    coverage_data: dict,
    additional_benefits: dict
) -> dict:
    """Score S2: Disability Protection Depth (0-100) per EAZR_04 Section 5.3"""
    score = 0
    factors = []

    # Factor 1: PPD Schedule Comprehensiveness (30 pts)
    ppd = coverage_data.get("permanentPartialDisability", {})
    ppd_conditions = len(ppd.get("schedule", []))
    if ppd_conditions >= 18:
        f1 = 30
    elif ppd_conditions >= 15:
        f1 = 25
    elif ppd_conditions >= 10:
        f1 = 18
    elif ppd_conditions > 0:
        f1 = 10
    else:
        f1 = 5
    score += f1
    factors.append({
        "name": "PPD Schedule Comprehensiveness",
        "score": f1, "maxScore": 30,
        "detail": f"{ppd_conditions} conditions in schedule"
    })

    # Factor 2: TTD Duration (25 pts)
    ttd = coverage_data.get("temporaryTotalDisability", {})
    f2 = 0
    if ttd.get("covered"):
        max_weeks = ttd.get("maximumWeeks", 52) or 52
        if max_weeks >= 104:
            f2 = 25
        elif max_weeks >= 78:
            f2 = 20
        elif max_weeks >= 52:
            f2 = 15
        else:
            f2 = 10
    score += f2
    factors.append({
        "name": "TTD Duration",
        "score": f2, "maxScore": 25,
        "detail": f"{ttd.get('maximumWeeks', 0)} weeks max" if ttd.get("covered") else "No TTD coverage"
    })

    # Factor 3: TTD Waiting Period (15 pts)
    f3 = 0
    if ttd.get("covered"):
        waiting = ttd.get("waitingPeriodDays", 14) or 14
        if waiting <= 7:
            f3 = 15
        elif waiting <= 14:
            f3 = 10
        else:
            f3 = 5
    score += f3
    factors.append({
        "name": "TTD Waiting Period",
        "score": f3, "maxScore": 15,
        "detail": f"{ttd.get('waitingPeriodDays', 'N/A')} days" if ttd.get("covered") else "N/A"
    })

    # Factor 4: Home/Vehicle Modification (15 pts)
    f4 = 0
    if additional_benefits.get("homeModification", {}).get("covered"):
        f4 += 8
    if additional_benefits.get("vehicleModification", {}).get("covered"):
        f4 += 7
    score += f4
    factors.append({
        "name": "Modification Benefits",
        "score": f4, "maxScore": 15,
        "detail": "Home/vehicle modification covered" if f4 > 0 else "No modification benefits"
    })

    # Factor 5: Medical Expenses Coverage (15 pts)
    medical = coverage_data.get("medicalExpenses", {})
    f5 = 0
    if medical.get("covered"):
        pct = medical.get("limitPercentage", 0) or 0
        if pct >= 40:
            f5 = 15
        elif pct >= 20:
            f5 = 12
        elif pct >= 10:
            f5 = 8
        else:
            f5 = 5
    score += f5
    factors.append({
        "name": "Medical Expenses Coverage",
        "score": f5, "maxScore": 15,
        "detail": f"{medical.get('limitPercentage', 0)}% of SI" if medical.get("covered") else "Not covered"
    })

    return {"score": min(score, 100), "factors": factors}


def _simulate_pa_scenarios(
    coverage_data: dict,
    additional_benefits: dict,
    sum_insured: float,
    annual_income: int = 1000000
) -> list:
    """Generate 4 scenario simulations per EAZR_04 Section 6"""
    scenarios = []
    monthly_income = annual_income / 12
    weekly_income = annual_income / 52

    ad = coverage_data.get("accidentalDeath", {})
    ptd = coverage_data.get("permanentTotalDisability", {})
    ttd = coverage_data.get("temporaryTotalDisability", {})
    ppd = coverage_data.get("permanentPartialDisability", {})

    # PA001: Accidental Death - Family Financial Impact
    # Derive assumptions from income rather than flat hardcoded amounts
    outstanding_loans = int(annual_income * 3)  # Estimated 3x income for loans
    monthly_expenses = int(monthly_income * 0.67)

    # Try to count dependents from insured members
    _pa_members = coverage_data.get("_insuredMembers", []) or []
    children_count = sum(1 for m in _pa_members if isinstance(m, dict) and str(m.get("relationship", "")).lower() in ("son", "daughter", "child")) if _pa_members else 1

    # Derive replacement years from age if available
    _pa_age = 0
    for m in _pa_members:
        if isinstance(m, dict) and str(m.get("relationship", "")).lower() == "self":
            try: _pa_age = int(float(str(m.get("age") or m.get("dateOfBirth") or 0)))
            except: pass
            break
    _pa_replace_years = max(5, 60 - _pa_age) if _pa_age > 20 else 15

    immediate_needs = {
        "funeralExpenses": 100000,  # Reference constant
        "emergencyFund6Months": monthly_expenses * 6,
        "loanSettlement": outstanding_loans
    }
    immediate_total = sum(immediate_needs.values())
    ongoing_needs = {
        f"incomeReplacement{_pa_replace_years}Years": int(annual_income * 0.8 * _pa_replace_years),
        "childEducation": children_count * max(500000, int(annual_income * 5))  # 5x income per child
    }
    ongoing_total = sum(ongoing_needs.values())
    total_need = immediate_total + ongoing_total
    assumed_life_cover = annual_income * 10
    total_coverage = sum_insured + assumed_life_cover
    gap = max(0, total_need - total_coverage)

    scenarios.append({
        "scenarioId": "PA001",
        "name": "Accidental Death - Family Financial Impact",
        "description": "Road accident resulting in death. How is your family protected?",
        "icon": "family_restroom",
        "severity": "high",
        "inputs": {
            "annualIncome": annual_income,
            "outstandingLoans": outstanding_loans,
            "monthlyExpenses": monthly_expenses,
            "children": children_count,
            "paSumInsured": sum_insured
        },
        "analysis": {
            "immediateNeeds": {
                "items": [
                    {"label": "Funeral Expenses", "amount": immediate_needs["funeralExpenses"]},
                    {"label": "Emergency Fund (6 months)", "amount": immediate_needs["emergencyFund6Months"]},
                    {"label": "Loan Settlement", "amount": immediate_needs["loanSettlement"]}
                ],
                "total": immediate_total,
                "totalFormatted": f"₹{immediate_total:,.0f}"
            },
            "ongoingNeeds": {
                "items": [
                    {"label": f"Income Replacement ({_pa_replace_years} years)", "amount": ongoing_needs[f"incomeReplacement{_pa_replace_years}Years"]},
                    {"label": f"Child Education ({children_count} children)", "amount": ongoing_needs["childEducation"]}
                ],
                "total": ongoing_total,
                "totalFormatted": f"₹{ongoing_total:,.0f}"
            },
            "totalNeed": total_need,
            "totalNeedFormatted": f"₹{total_need:,.0f}",
            "paBenefit": sum_insured,
            "paBenefitFormatted": f"₹{sum_insured:,.0f}",
            "otherLifeCover": assumed_life_cover,
            "totalCoverage": total_coverage,
            "totalCoverageFormatted": f"₹{total_coverage:,.0f}",
            "gap": gap,
            "gapFormatted": f"₹{gap:,.0f}"
        },
        "output": {
            "paProvides": f"₹{sum_insured/100000:.0f}L to family",
            "combinedProtection": f"₹{total_coverage/10000000:.1f}Cr (PA + Life)",
            "gapToTotalNeed": f"₹{gap/100000:.0f}L gap" if gap > 0 else "Fully covered",
            "hasGap": gap > 0
        },
        "recommendation": f"Consider increasing PA to ₹{min(annual_income * 10, 10000000)/100000:.0f}L" if gap > 0 else "Your coverage is adequate"
    })

    # PA002: Permanent Total Disability - Living with Disability
    ptd_benefit = ptd.get("benefitAmount", sum_insured) or sum_insured
    if isinstance(ptd_benefit, str):
        try:
            ptd_benefit = float(str(ptd_benefit).replace(",", "").replace("₹", "").replace("Rs.", "").strip())
        except (ValueError, TypeError):
            ptd_benefit = sum_insured
    home_mod_covered = additional_benefits.get("homeModification", {}).get("covered", False)
    home_mod_limit = additional_benefits.get("homeModification", {}).get("limit", 0)
    vehicle_mod_covered = additional_benefits.get("vehicleModification", {}).get("covered", False)
    vehicle_mod_limit = additional_benefits.get("vehicleModification", {}).get("limit", 0)
    ongoing_care_annual = max(200000, int(annual_income * 0.3))  # ~30% of income for ongoing care
    modification_cost = max(300000, int(annual_income * 0.5))  # ~50% of income for modifications
    _ptd_years = max(10, 60 - _pa_age) if _pa_age > 20 else 20  # Years until retirement
    income_loss_lifetime = int(annual_income * _ptd_years)  # Income loss for remaining working years

    ptd_total_need = income_loss_lifetime + modification_cost + (ongoing_care_annual * _ptd_years)
    ptd_total_coverage = ptd_benefit + (home_mod_limit if home_mod_covered else 0) + (vehicle_mod_limit if vehicle_mod_covered else 0)
    ptd_gap = max(0, ptd_total_need - ptd_total_coverage)

    scenarios.append({
        "scenarioId": "PA002",
        "name": "Permanent Total Disability - Living with Disability",
        "description": "Severe accident causing permanent total disability. What support do you get?",
        "icon": "accessible",
        "severity": "high",
        "inputs": {
            "paSumInsured": sum_insured,
            "ptdBenefit": ptd_benefit,
            "annualIncome": annual_income
        },
        "analysis": {
            "totalNeeds": {
                "items": [
                    {"label": f"Lifetime Income Loss ({_ptd_years} years)", "amount": income_loss_lifetime},
                    {"label": "Home/Vehicle Modifications", "amount": modification_cost},
                    {"label": f"Ongoing Care ({_ptd_years} years)", "amount": int(ongoing_care_annual * _ptd_years)}
                ],
                "total": ptd_total_need,
                "totalFormatted": f"₹{ptd_total_need:,.0f}"
            },
            "ptdBenefit": ptd_benefit,
            "ptdBenefitFormatted": f"₹{ptd_benefit:,.0f}",
            "homeModification": {"covered": home_mod_covered, "limit": home_mod_limit},
            "vehicleModification": {"covered": vehicle_mod_covered, "limit": vehicle_mod_limit},
            "totalCoverage": ptd_total_coverage,
            "totalCoverageFormatted": f"₹{ptd_total_coverage:,.0f}",
            "gap": ptd_gap,
            "gapFormatted": f"₹{ptd_gap:,.0f}"
        },
        "output": {
            "ptdProvides": f"₹{ptd_benefit/100000:.0f}L lump sum",
            "modificationSupport": "Covered" if (home_mod_covered or vehicle_mod_covered) else "Not covered",
            "hasGap": ptd_gap > 0
        },
        "recommendation": "Consider higher SI and modification benefits" if ptd_gap > 0 else "PTD coverage is adequate"
    })

    # PA003: Temporary Disability - 6 Month Recovery
    ttd_covered = ttd.get("covered", False)
    ttd_weekly_benefit = ttd.get("benefitAmount", 0) or 0
    if isinstance(ttd_weekly_benefit, str):
        try:
            ttd_weekly_benefit = float(str(ttd_weekly_benefit).replace(",", "").replace("₹", "").replace("Rs.", "").strip())
        except (ValueError, TypeError):
            ttd_weekly_benefit = 0
    if ttd_weekly_benefit == 0 and ttd_covered and sum_insured > 0:
        pct = ttd.get("benefitPercentage", 1) or 1
        ttd_weekly_benefit = sum_insured * float(pct) / 100
    ttd_waiting = ttd.get("waitingPeriodDays", 7) or 7
    ttd_max_weeks = ttd.get("maximumWeeks", 52) or 52

    disability_months = 6
    disability_weeks = disability_months * 4.33
    income_lost = monthly_income * disability_months
    emi_monthly = int(monthly_income * 0.35)
    expenses_6_months = monthly_expenses * disability_months
    emi_6_months = emi_monthly * disability_months
    total_needed = expenses_6_months + emi_6_months

    weeks_covered = max(0, min(int(disability_weeks) - 1, ttd_max_weeks))  # -1 for waiting period
    total_ttd_benefit = ttd_weekly_benefit * weeks_covered if ttd_covered else 0
    ttd_gap = max(0, total_needed - total_ttd_benefit)

    timeline = []
    if ttd_covered:
        timeline.append({"week": "1", "status": "Waiting period", "benefit": 0, "benefitFormatted": "₹0"})
        timeline.append({
            "week": f"2-{min(int(disability_weeks), ttd_max_weeks + 1)}",
            "status": "TTD benefit active",
            "benefit": ttd_weekly_benefit,
            "benefitFormatted": f"₹{ttd_weekly_benefit:,.0f}/week"
        })
        timeline.append({"week": f"{int(disability_weeks) + 1}+", "status": "Back to work", "benefit": 0, "benefitFormatted": "₹0"})

    scenarios.append({
        "scenarioId": "PA003",
        "name": "Temporary Total Disability - 6 Month Recovery",
        "description": "Major leg fracture, unable to work for 6 months. How does your income survive?",
        "icon": "healing",
        "severity": "medium",
        "inputs": {
            "monthlyIncome": monthly_income,
            "monthlyEmi": emi_monthly,
            "monthlyExpenses": monthly_expenses,
            "ttdBenefitPerWeek": ttd_weekly_benefit,
            "ttdWaitingDays": ttd_waiting,
            "ttdMaxWeeks": ttd_max_weeks
        },
        "analysis": {
            "incomeLoss": {
                "durationMonths": disability_months,
                "totalIncomeLost": income_lost,
                "totalIncomeLostFormatted": f"₹{income_lost:,.0f}"
            },
            "fixedExpensesContinue": {
                "items": [
                    {"label": f"EMI ({disability_months} months)", "amount": emi_6_months},
                    {"label": f"Living Expenses ({disability_months} months)", "amount": expenses_6_months}
                ],
                "totalNeeded": total_needed,
                "totalNeededFormatted": f"₹{total_needed:,.0f}"
            },
            "ttdBenefit": {
                "covered": ttd_covered,
                "afterWaitingPeriod": f"Week {int(ttd_waiting / 7) + 1} onwards" if ttd_covered else "N/A",
                "weeksCovered": weeks_covered,
                "benefitPerWeek": ttd_weekly_benefit,
                "benefitPerWeekFormatted": f"₹{ttd_weekly_benefit:,.0f}",
                "totalBenefit": total_ttd_benefit,
                "totalBenefitFormatted": f"₹{total_ttd_benefit:,.0f}"
            },
            "gap": ttd_gap,
            "gapFormatted": f"₹{ttd_gap:,.0f}",
            "timeline": timeline
        },
        "output": {
            "totalBenefit": f"₹{total_ttd_benefit:,.0f}" if ttd_covered else "₹0 (No TTD)",
            "shortfall": f"₹{ttd_gap:,.0f} shortfall during recovery" if ttd_gap > 0 else "Covered",
            "hasGap": ttd_gap > 0 or not ttd_covered
        },
        "recommendation": "Consider higher TTD benefit or EMI protection add-on" if ttd_gap > 0 else ("Add TTD benefit to cover income loss" if not ttd_covered else "TTD coverage is adequate")
    })

    # PA004: Partial Disability - Understanding PPD Schedule
    ppd_schedule = ppd.get("schedule", [])
    index_finger_pct = 10  # IRDAI standard
    for item in ppd_schedule:
        if "index" in str(item.get("disability", "")).lower():
            index_finger_pct = item.get("percentage", 10)
            break
    ppd_benefit_finger = sum_insured * index_finger_pct / 100

    common_ppd_examples = []
    for item in ppd_schedule[:8]:  # Show top 8 conditions
        pct = item.get("percentage", 0)
        amount = sum_insured * pct / 100
        common_ppd_examples.append({
            "disability": item.get("disability", ""),
            "percentage": pct,
            "benefitAmount": amount,
            "benefitFormatted": f"₹{amount:,.0f}"
        })

    scenarios.append({
        "scenarioId": "PA004",
        "name": "Permanent Partial Disability - Understanding PPD",
        "description": "Industrial accident causing loss of index finger. What benefit do you receive?",
        "icon": "back_hand",
        "severity": "low",
        "inputs": {
            "paSumInsured": sum_insured,
            "disability": "Loss of index finger"
        },
        "analysis": {
            "ppdLookup": {
                "disability": "Loss of index finger",
                "percentage": index_finger_pct,
                "calculation": f"SI × {index_finger_pct}% = ₹{ppd_benefit_finger:,.0f}",
                "benefitAmount": ppd_benefit_finger,
                "benefitFormatted": f"₹{ppd_benefit_finger:,.0f}"
            },
            "howPpdWorks": [
                "PPD pays a percentage of Sum Insured based on disability type",
                "Percentages are set by IRDAI standard schedule",
                "Multiple disabilities can be claimed (up to 100% total)",
                "Benefit is lump sum, not recurring"
            ],
            "commonExamples": common_ppd_examples,
            "scheduleSize": len(ppd_schedule)
        },
        "output": {
            "benefit": f"₹{ppd_benefit_finger:,.0f} ({index_finger_pct}% of SI)",
            "scheduleAvailable": len(ppd_schedule) > 0,
            "hasGap": len(ppd_schedule) < 10
        },
        "recommendation": "Review your PPD schedule to understand all covered disabilities"
    })

    return scenarios


def _analyze_pa_gaps(
    coverage_data: dict,
    additional_benefits: dict,
    annual_income: int = 1000000
) -> list:
    """Detect coverage gaps per EAZR_04 Section 7"""
    gaps = []
    sum_insured = coverage_data.get("sumInsured", 0) or 0
    if isinstance(sum_insured, str):
        try:
            sum_insured = float(str(sum_insured).replace(",", "").replace("₹", "").replace("Rs.", "").strip())
        except (ValueError, TypeError):
            sum_insured = 0

    income_multiple = sum_insured / annual_income if annual_income > 0 else 0

    # G001: SI Below Income Multiple
    if income_multiple < 5:
        recommended = annual_income * 10
        _g001_gap = max(0, recommended - sum_insured)
        _g001_cost = max(3000, int(_g001_gap * 0.0008))  # ~₹0.80 per ₹1000 SI for PA
        gaps.append({
            "gapId": "G001",
            "severity": "high",
            "severityColor": "#EF4444",
            "title": "PA Sum Insured Below Recommended",
            "description": f"Current ₹{sum_insured/100000:.0f}L = {income_multiple:.1f}x income. Recommended: 10x (₹{recommended/100000:.0f}L)",
            "impact": "Family may face severe financial hardship in case of accidental death or permanent disability",
            "solution": f"Increase PA Sum Insured to ₹{recommended/100000:.0f}L (10x annual income)",
            "estimatedCost": f"~₹{_g001_cost:,}/year",
            "ipfEligible": True
        })

    # G002: No TTD Benefit
    ttd = coverage_data.get("temporaryTotalDisability", {})
    if not ttd.get("covered"):
        monthly_income = annual_income / 12
        gaps.append({
            "gapId": "G002",
            "severity": "high",
            "severityColor": "#EF4444",
            "title": "No Temporary Disability Benefit",
            "description": "No income replacement during recovery period after an accident",
            "impact": f"If disabled for 6 months, you lose ₹{annual_income / 2:,.0f} income with no replacement",
            "solution": "Add TTD benefit — get weekly/monthly income during recovery",
            "estimatedCost": "Included in comprehensive PA plans",
            "ipfEligible": True
        })
    # G003: Low TTD Duration
    elif ttd.get("maximumWeeks", 52) and ttd.get("maximumWeeks", 52) < 52:
        max_weeks = ttd.get("maximumWeeks", 0)
        gaps.append({
            "gapId": "G003",
            "severity": "medium",
            "severityColor": "#F59E0B",
            "title": "Limited TTD Duration",
            "description": f"TTD benefit limited to {max_weeks} weeks — major injuries may need longer recovery",
            "impact": "Complex fractures or surgeries can require 6-12 months recovery",
            "solution": "Look for a plan with 52+ weeks TTD coverage",
            "estimatedCost": "Marginal premium difference",
            "ipfEligible": False
        })

    # G004: No Medical Expenses
    medical = coverage_data.get("medicalExpenses", {})
    if not medical.get("covered"):
        gaps.append({
            "gapId": "G004",
            "severity": "medium",
            "severityColor": "#F59E0B",
            "title": "No Accident Medical Expenses Cover",
            "description": "Treatment costs for accident injuries are not covered under this PA policy",
            "impact": "Out-of-pocket medical expenses for accident treatment (ambulance, surgery, medicines)",
            "solution": "Add medical expenses benefit or ensure health insurance covers accident treatment",
            "estimatedCost": f"~₹{max(500, int(sum_insured * 0.0002)):,}/year",
            "ipfEligible": True
        })

    # G005: No EMI Protection
    if not additional_benefits.get("loanEmiCover", {}).get("covered"):
        _g005_cost = max(500, int(sum_insured * 0.00015))
        gaps.append({
            "gapId": "G005",
            "severity": "low",
            "severityColor": "#6B7280",
            "title": "No EMI Protection During Disability",
            "description": "Loan EMIs continue during disability period — no coverage for EMI payments",
            "impact": "EMI burden continues when income stops after an accident",
            "solution": "Add EMI protection benefit to cover loan payments during disability",
            "estimatedCost": f"~₹{_g005_cost:,}/year",
            "ipfEligible": True
        })

    # G006: No Modification Benefits
    has_home_mod = additional_benefits.get("homeModification", {}).get("covered", False)
    has_vehicle_mod = additional_benefits.get("vehicleModification", {}).get("covered", False)
    if not has_home_mod and not has_vehicle_mod:
        gaps.append({
            "gapId": "G006",
            "severity": "low",
            "severityColor": "#6B7280",
            "title": "No Home/Vehicle Modification Benefits",
            "description": "No coverage for home or vehicle accessibility modifications after permanent disability",
            "impact": "If permanently disabled, home ramps, grab bars, vehicle controls etc. need to be self-funded",
            "solution": "Look for PA plans with home/vehicle modification benefits for PTD cases",
            "estimatedCost": "Available in premium PA plans",
            "ipfEligible": False
        })

    return sorted(gaps, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("severity", "low"), 3))


def _generate_pa_recommendations(
    gaps: list,
    coverage_data: dict,
    additional_benefits: dict,
    policy_sub_type: str = ""
) -> list:
    """Generate recommendations based on gaps per EAZR_04 Section 8.1"""
    recommendations = []

    # Map gap IDs to recommendation definitions (costs from gap's own estimatedCost)
    rec_meta = {
        "G001": {"id": "increase_si", "category": "enhancement", "priority": 1, "title": "Increase PA Sum Insured", "description": "Increase your PA cover to 10x annual income for adequate protection for your family", "ipfEligible": True, "icon": "trending_up"},
        "G002": {"id": "add_ttd", "category": "enhancement", "priority": 2, "title": "Add Temporary Disability Benefit", "description": "Get weekly/monthly income replacement during recovery period after an accident", "ipfEligible": True, "icon": "healing"},
        "G004": {"id": "add_medical", "category": "enhancement", "priority": 3, "title": "Add Medical Expenses Cover", "description": "Cover accident-related treatment costs including hospitalization, surgery, and medicines", "ipfEligible": True, "icon": "medical_services"},
        "G005": {"id": "add_emi_cover", "category": "addon", "priority": 4, "title": "Add EMI Protection", "description": "Protect your loan EMI payments during disability period", "ipfEligible": True, "icon": "account_balance"},
    }

    for gap in gaps:
        gap_id = gap.get("gapId", "")
        if gap_id in rec_meta:
            rec = dict(rec_meta[gap_id])
            rec["estimatedCost"] = gap.get("estimatedCost", "")
            recommendations.append(rec)

    # Check for family upgrade recommendation (only for individual PA)
    # policy_sub_type comes from policyBasics.policySubType (IND_PA, FAM_PA, GRP_PA, etc.)
    sub_type_lower = str(policy_sub_type).lower().strip() if policy_sub_type else ""
    is_individual = sub_type_lower in ["", "ind_pa"] or "individual" in sub_type_lower
    if is_individual:
        _si_val = coverage_data.get("sumInsured", 0) or 0
        if isinstance(_si_val, str):
            try: _si_val = float(str(_si_val).replace(",", "").replace("₹", "").replace("Rs.", "").strip())
            except: _si_val = 0
        _fam_cost = max(2000, int(float(_si_val) * 0.003)) if _si_val > 0 else 3000  # ~0.3% of SI for family upgrade
        recommendations.append({
            "id": "family_upgrade",
            "category": "upgrade",
            "priority": 5,
            "title": "Upgrade to Family PA",
            "description": "Cover your spouse and children under a family floater PA plan",
            "estimatedCost": f"~₹{_fam_cost:,}/year additional",
            "ipfEligible": True,
            "icon": "family_restroom"
        })

    # Ensure at least one recommendation exists
    if not recommendations:
        recommendations.append({
            "id": "review_coverage",
            "category": "maintenance",
            "priority": 5,
            "title": "Review Coverage at Renewal",
            "description": "Review your PA coverage annually to ensure it keeps pace with your income growth and changing needs",
            "estimatedCost": "No additional cost",
            "ipfEligible": False,
            "icon": "rate_review"
        })

    return sorted(recommendations, key=lambda x: x.get("priority", 99))
