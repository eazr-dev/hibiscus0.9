"""Personal Accident V10 Enhanced Helpers (EAZR_04 Spec)"""
import logging
import re
from policy_analysis.utils import safe_num, get_score_label

logger = logging.getLogger(__name__)


def _build_pa_coverage_gaps_rich(pa_light_gaps: list, coverage_gaps_table: list) -> list:
    """
    Build properly structured coverageGaps for PA insurance from rich pa_light_gaps (from _analyze_pa_gaps).
    Each gap includes: area, title, status, statusType, severity, details, description, impact, solution, estimatedCost, gapId.
    Falls back to coverage_gaps_table for items not covered by pa_light_gaps.
    """
    coverage_gaps = []
    covered_gap_ids = set()

    severity_to_status_type = {
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "info"
    }

    # PRIORITY 1: Use rich pa_light_gaps (G001-G006 from _analyze_pa_gaps)
    for gap in pa_light_gaps:
        if not isinstance(gap, dict):
            continue
        gap_title = gap.get("title", "Coverage Gap")
        gap_severity = str(gap.get("severity", "medium")).lower()
        gap_description = gap.get("description", "")
        gap_impact = gap.get("impact", "")
        gap_solution = gap.get("solution", "")
        gap_estimated_cost = gap.get("estimatedCost", "")
        gap_id = gap.get("gapId", "")

        covered_gap_ids.add(gap_id)

        coverage_gaps.append({
            "area": gap_title,
            "title": gap_title,
            "status": "Not Covered",
            "statusType": severity_to_status_type.get(gap_severity, "medium"),
            "severity": gap_severity,
            "details": gap_description,
            "description": gap_description,
            "impact": gap_impact,
            "solution": gap_solution,
            "estimatedCost": gap_estimated_cost,
            "gapId": gap_id
        })

    # PRIORITY 2: Add coverage_gaps_table items NOT already covered by rich gaps
    # Map area names to gap IDs to avoid duplicates
    rich_areas_lower = {g.get("area", "").lower() for g in coverage_gaps}
    for item in coverage_gaps_table:
        if not isinstance(item, dict):
            continue
        item_status = item.get("statusType", "")
        # Only include gaps (not strengths)
        if item_status not in ["warning", "danger", "info"]:
            continue
        item_area = item.get("area", "")
        # Skip if already covered by rich gaps
        if item_area.lower() in rich_areas_lower:
            continue
        # Check for partial match (e.g. "PA Sum Insured" vs "PA Sum Insured Below Recommended")
        already_covered = False
        for ra in rich_areas_lower:
            if item_area.lower() in ra or ra in item_area.lower():
                already_covered = True
                break
        if already_covered:
            continue

        # Enrich the basic item with severity based on statusType
        severity_map = {"danger": "high", "warning": "medium", "info": "low"}
        item_severity = severity_map.get(item_status, "medium")

        coverage_gaps.append({
            "area": item_area,
            "title": item_area,
            "status": item.get("status", "Not Covered"),
            "statusType": item_status,
            "severity": item_severity,
            "details": item.get("details", ""),
            "description": item.get("details", ""),
            "impact": "",
            "solution": "",
            "estimatedCost": "",
            "gapId": ""
        })

    return coverage_gaps


# ==================== PERSONAL ACCIDENT V10 HELPERS (EAZR_04 Spec) ====================
# Used by _build_light_analysis() for PA-specific policyAnalyzer structure

def _get_pa_strengths(scores_detailed: dict, category_data: dict) -> list:
    """
    Extract top coverage strengths from PA S1/S2 scoring factors that scored >=80% of max points.
    Returns up to 5 strengths sorted by priority.
    """
    strengths = []
    scores = scores_detailed.get("scores", {})

    # Map factor names to user-friendly strength descriptions
    strength_map = {
        "Death Benefit vs Income": ("Strong Death Benefit", "Death benefit covers {policy} — exceeds recommended minimum"),
        "PTD Benefit vs Income": ("Adequate PTD Cover", "Permanent disability benefit covers {policy}"),
        "TTD vs Weekly Income": ("Income Replacement Active", "TTD replaces {policy} during recovery period"),
        "EMI Coverage": ("EMI Protection Included", "Loan EMI payments protected during disability"),
        "Double Indemnity": ("Double Indemnity Active", "Double payout for public transport accidents"),
        "PPD Schedule Comprehensiveness": ("Comprehensive PPD Schedule", "{policy} — covers wide range of disabilities"),
        "TTD Duration": ("Extended TTD Duration", "TTD coverage for up to {policy}"),
        "TTD Waiting Period": ("Short Waiting Period", "Only {policy} waiting before TTD payments begin"),
        "Home/Vehicle Modification": ("Modification Benefits", "{policy} modification support for PTD"),
        "Medical Expenses Coverage": ("Medical Expenses Covered", "Accident medical expenses covered at {policy}"),
    }

    for score_key in ["s1", "s2"]:
        score_data = scores.get(score_key)
        if not score_data or not isinstance(score_data, dict):
            continue
        for factor in score_data.get("factors", []):
            earned = factor.get("pointsEarned", 0)
            max_pts = factor.get("pointsMax", 1)
            if max_pts > 0 and (earned / max_pts) >= 0.80:
                fname = factor.get("name", "")
                mapping = strength_map.get(fname)
                if mapping:
                    title, reason_tpl = mapping
                    policy_val = factor.get("yourPolicy", "")
                    reason = reason_tpl.replace("{policy}", policy_val)
                    strengths.append({
                        "title": title,
                        "reason": reason,
                        "priority": len(strengths) + 1
                    })

    return strengths[:5]


def _analyze_pa_gaps_v10(category_data: dict, sum_assured: float, formatted_gaps: list | None = None, scores_detailed: dict | None = None) -> dict:
    """
    Wraps existing _analyze_pa_gaps() into V10 format with summary counts.
    Returns: {"summary": {"high": N, "medium": N, "low": N, "total": N}, "gaps": [...]}
    """
    from policy_analysis.types.pa.helpers import _analyze_pa_gaps

    formatted_gaps = formatted_gaps or []
    scores_detailed = scores_detailed or {}
    coverage = category_data.get("coverageDetails", {}) or {}
    additional = category_data.get("additionalBenefits", {}) or {}

    # Derive annual income from scores_detailed or fallback to SI/10
    _pa_annual_income = 0
    if scores_detailed:
        try:
            _pa_annual_income = int(scores_detailed.get("_annualIncome", 0))
        except (ValueError, TypeError):
            pass
    if _pa_annual_income <= 0:
        _pa_annual_income = int(sum_assured / 10) if sum_assured > 0 else 1000000

    raw_gaps = _analyze_pa_gaps(coverage, additional, _pa_annual_income)

    # Enrich gaps with V10 fields
    v10_gaps = []
    for g in raw_gaps:
        cost_str = g.get("estimatedCost", "")
        # Parse estimated cost to numeric
        est_annual = 0
        if cost_str:
            nums = re.findall(r'[\d,]+', cost_str.replace(',', ''))
            if nums:
                try:
                    est_annual = int(nums[-1])
                except (ValueError, IndexError):
                    pass

        monthly_emi = round(est_annual / 12) if est_annual > 0 else 0

        v10_gaps.append({
            "gapId": g.get("gapId", ""),
            "severity": g.get("severity", "low"),
            "severityColor": g.get("severityColor", "#6B7280"),
            "title": g.get("title", ""),
            "description": g.get("description", ""),
            "impact": g.get("impact", ""),
            "solution": g.get("solution", ""),
            "estimatedCost": est_annual,
            "estimatedCostFormatted": g.get("estimatedCost", ""),
            "eazrEmi": monthly_emi,
            "eazrEmiFormatted": f"Rs.{monthly_emi:,}/mo" if monthly_emi > 0 else "",
            "ipfEligible": g.get("ipfEligible", False)
        })

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    v10_gaps.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))

    high = sum(1 for g in v10_gaps if g.get("severity") == "high")
    medium = sum(1 for g in v10_gaps if g.get("severity") == "medium")
    low = sum(1 for g in v10_gaps if g.get("severity") == "low")

    return {
        "summary": {"high": high, "medium": medium, "low": low, "total": len(v10_gaps)},
        "gaps": v10_gaps
    }


def _select_pa_primary_scenario(scores_detailed: dict, gaps_result: dict, pa_scenarios: list) -> str:
    """
    Auto-select primary PA scenario per EAZR_04 spec Section 2.5.
    Returns scenario ID string.
    """
    gap_ids = set()
    if isinstance(gaps_result, dict):
        for g in gaps_result.get("gaps", []):
            gap_ids.add(g.get("gapId", ""))

    # Check TTD coverage from S1 factors
    s1 = scores_detailed.get("scores", {}).get("s1", {})
    ttd_factor = None
    for f in s1.get("factors", []):
        if "ttd" in f.get("name", "").lower() and "duration" not in f.get("name", "").lower():
            ttd_factor = f
            break
    ttd_score = ttd_factor.get("pointsEarned", 0) if ttd_factor else 0

    # If TTD not covered (0 points) -> PA003
    if ttd_score == 0:
        return "PA003"

    # If G001 exists (SI below recommended) -> PA001
    if "G001" in gap_ids:
        return "PA001"

    # If TTD covered but low (< 15 out of 20 pts) -> PA003
    if ttd_score < 15:
        return "PA003"

    # Default: PA002
    return "PA002"


def _build_pa_recommendations_v10(gaps_result: dict | None = None, category_data: dict | None = None, sum_assured: float = 0, scores_detailed: dict | None = None) -> dict:
    """
    Build V10-structured recommendations: quickWins + priorityUpgrades + totalUpgradeCost.
    """
    gaps_result = gaps_result or {}
    category_data = category_data or {}
    scores_detailed = scores_detailed or {}
    coverage = category_data.get("coverageDetails", {}) or {}
    additional = category_data.get("additionalBenefits", {}) or {}

    quick_wins = [
        {
            "id": "review_nominee",
            "title": "Review Nominee Details",
            "description": "Ensure your nominee details are up to date for quick claim settlement.",
            "effort": "5 minutes",
            "icon": "person"
        },
        {
            "id": "keep_active",
            "title": "Keep Policy Active",
            "description": "Ensure premium is paid on time to maintain continuous accident protection.",
            "effort": "At renewal",
            "icon": "verified"
        }
    ]

    # Build priority upgrades from gaps
    priority_upgrades = []
    total_annual = 0
    gaps = gaps_result.get("gaps", []) if isinstance(gaps_result, dict) else []

    _si = float(sum_assured) if sum_assured else 0
    _g001_v10_cost = max(3000, int(_si * 0.0008))  # ~₹0.80 per ₹1000 SI
    _g002_v10_cost = max(2000, int(_si * 0.0003))  # TTD add-on
    _g003_v10_cost = max(1000, int(_si * 0.00015))  # TTD extension
    _g004_v10_cost = max(500, int(_si * 0.0002))  # Medical add-on
    _g005_v10_cost = max(500, int(_si * 0.00015))  # EMI protection
    _g006_v10_cost = max(800, int(_si * 0.0001))  # Modification benefit

    gap_to_rec = {
        "G001": {
            "id": "increase_si",
            "category": "enhancement",
            "title": "Increase PA Sum Insured",
            "description": "Increase your PA cover to 10x annual income for adequate protection for your family.",
            "estimatedCost": _g001_v10_cost,
            "estimatedCostFormatted": f"~Rs.{_g001_v10_cost:,}/year",
            "ipfEligible": True,
            "icon": "trending_up",
            "when": "At renewal or now"
        },
        "G002": {
            "id": "add_ttd",
            "category": "enhancement",
            "title": "Add Temporary Disability Benefit",
            "description": "Get weekly/monthly income replacement during recovery period after an accident.",
            "estimatedCost": _g002_v10_cost,
            "estimatedCostFormatted": f"~Rs.{_g002_v10_cost:,}/year",
            "ipfEligible": True,
            "icon": "healing",
            "when": "At renewal"
        },
        "G003": {
            "id": "extend_ttd",
            "category": "enhancement",
            "title": "Extend TTD Duration",
            "description": "Increase TTD coverage to 52+ weeks for extended recovery protection.",
            "estimatedCost": _g003_v10_cost,
            "estimatedCostFormatted": f"~Rs.{_g003_v10_cost:,}/year",
            "ipfEligible": True,
            "icon": "schedule",
            "when": "At renewal"
        },
        "G004": {
            "id": "add_medical",
            "category": "enhancement",
            "title": "Add Medical Expenses Cover",
            "description": "Cover accident-related treatment costs including hospitalization, surgery, and medicines.",
            "estimatedCost": _g004_v10_cost,
            "estimatedCostFormatted": f"~Rs.{_g004_v10_cost:,}/year",
            "ipfEligible": True,
            "icon": "medical_services",
            "when": "At renewal"
        },
        "G005": {
            "id": "add_emi_cover",
            "category": "addon",
            "title": "Add EMI Protection",
            "description": "Protect your loan EMI payments during disability period.",
            "estimatedCost": _g005_v10_cost,
            "estimatedCostFormatted": f"~Rs.{_g005_v10_cost:,}/year",
            "ipfEligible": True,
            "icon": "account_balance",
            "when": "At renewal"
        },
        "G006": {
            "id": "add_modification",
            "category": "addon",
            "title": "Add Modification Benefits",
            "description": "Get coverage for home and vehicle accessibility modifications after permanent disability.",
            "estimatedCost": _g006_v10_cost,
            "estimatedCostFormatted": f"~Rs.{_g006_v10_cost:,}/year",
            "ipfEligible": False,
            "icon": "home",
            "when": "At renewal"
        }
    }

    priority = 1
    for gap in gaps:
        gap_id = gap.get("gapId", "")
        rec = gap_to_rec.get(gap_id)
        if rec:
            rec_copy = dict(rec)
            rec_copy["priority"] = priority
            rec_copy["priorityLabel"] = "HIGH" if gap.get("severity") == "high" else ("MEDIUM" if gap.get("severity") == "medium" else "LOW")
            rec_copy["gapMapping"] = [gap_id]
            rec_copy["impact"] = gap.get("impact", "")
            rec_copy["eazrEmi"] = round(rec["estimatedCost"] / 12) if rec["estimatedCost"] > 0 else 0
            rec_copy["eazrEmiFormatted"] = f"Rs.{rec_copy['eazrEmi']:,}/mo" if rec_copy["eazrEmi"] > 0 else ""
            priority_upgrades.append(rec_copy)
            total_annual += rec.get("estimatedCost", 0)
            priority += 1

    monthly_emi = round(total_annual / 12) if total_annual > 0 else 0

    return {
        "quickWins": quick_wins,
        "priorityUpgrades": priority_upgrades,
        "totalUpgradeCost": {
            "annual": total_annual,
            "annualFormatted": f"Rs.{total_annual:,}/year" if total_annual > 0 else "Rs.0",
            "monthlyEmi": monthly_emi,
            "monthlyEmiFormatted": f"Rs.{monthly_emi:,}/mo" if monthly_emi > 0 else "Rs.0/mo"
        }
    }


def _build_pa_income_gap_check(category_data: dict, sum_assured: float, scores_detailed: dict) -> dict:
    """
    PA-unique Section B: Income Gap Check.
    Shows SI vs annual income and TTD vs weekly income.
    """
    coverage = category_data.get("coverageDetails", {}) or {}
    ttd = coverage.get("temporaryTotalDisability", {}) if isinstance(coverage.get("temporaryTotalDisability"), dict) else {}

    # Derive income: extracted from members -> SI/10 -> premium*10
    annual_income = 0
    members = category_data.get("insuredMembers", [])
    if isinstance(members, list) and members:
        first = members[0] if isinstance(members[0], dict) else {}
        ai = first.get("annualIncome", 0)
        if ai and isinstance(ai, (int, float)) and ai > 0:
            annual_income = int(ai)
    if annual_income <= 0:
        # Derive from SI (typical PA cover is 5-10x income)
        _si_derived = float(sum_assured) / 10 if sum_assured and float(sum_assured) > 0 else 0
        # Derive from premium (PA premium is ~0.1-0.3% of SI, income ~ SI/10)
        _prem_raw = category_data.get("premiumDetails", {}).get("basePremium", 0) or category_data.get("premiumDetails", {}).get("totalPremium", 0)
        _prem_derived = float(_prem_raw) * 500 if _prem_raw and float(_prem_raw) > 0 else 0  # PA premium ~0.2% of SI, income ~ SI/10
        annual_income = int(max(_si_derived, _prem_derived))
    if annual_income <= 0:
        annual_income = int(float(sum_assured) / 10) if sum_assured and float(sum_assured) > 0 else 0

    weekly_income = annual_income / 52
    si = float(sum_assured) if sum_assured else 0

    # Death benefit analysis
    income_multiple = round(si / annual_income, 1) if annual_income > 0 else 0
    recommended = annual_income * 10

    if income_multiple >= 10:
        death_indicator = "green"
    elif income_multiple >= 5:
        death_indicator = "yellow"
    elif income_multiple >= 3:
        death_indicator = "orange"
    else:
        death_indicator = "gray"

    # TTD benefit analysis
    ttd_covered = ttd.get("covered", False)
    ttd_weekly = 0
    if ttd_covered:
        ttd_weekly = float(ttd.get("benefitAmount", 0) or 0)
        if isinstance(ttd_weekly, str):
            try:
                ttd_weekly = float(re.sub(r'[^\d.]', '', ttd_weekly))
            except (ValueError, TypeError):
                ttd_weekly = 0
        if ttd_weekly == 0 and si > 0:
            pct = float(ttd.get("benefitPercentage", 1) or 1)
            ttd_weekly = si * pct / 100

    coverage_pct = round(ttd_weekly / weekly_income * 100) if weekly_income > 0 and ttd_weekly > 0 else 0
    shortfall_per_week = max(0, weekly_income - ttd_weekly)
    six_month_gap = max(0, (weekly_income * 26) - (ttd_weekly * 25))  # 26 weeks, 1 week waiting

    if not ttd_covered:
        ttd_indicator = "gray"
    elif coverage_pct >= 50:
        ttd_indicator = "green"
    elif coverage_pct >= 30:
        ttd_indicator = "yellow"
    elif coverage_pct >= 20:
        ttd_indicator = "orange"
    else:
        ttd_indicator = "gray"

    summary_line = f"Your PA replaces {coverage_pct}% of lost income during disability." if ttd_covered else "Your PA has no income replacement benefit during disability."

    return {
        "deathBenefit": {
            "paPays": si,
            "paPaysFormatted": f"Rs.{si:,.0f}",
            "recommended": recommended,
            "recommendedFormatted": f"Rs.{recommended:,.0f}",
            "incomeMultiple": income_multiple,
            "recommendedMultiple": 10,
            "indicator": death_indicator
        },
        "ttdBenefit": {
            "covered": ttd_covered,
            "weeklyIncome": round(weekly_income),
            "weeklyIncomeFormatted": f"Rs.{weekly_income:,.0f}",
            "ttdWeekly": round(ttd_weekly),
            "ttdWeeklyFormatted": f"Rs.{ttd_weekly:,.0f}/week" if ttd_covered else "Not covered",
            "coveragePct": coverage_pct,
            "shortfallPerWeek": round(shortfall_per_week),
            "shortfallPerWeekFormatted": f"Rs.{shortfall_per_week:,.0f}/week",
            "sixMonthGap": round(six_month_gap),
            "sixMonthGapFormatted": f"Rs.{six_month_gap:,.0f}",
            "indicator": ttd_indicator
        },
        "summaryLine": summary_line
    }


def _build_pa_portfolio_view() -> dict:
    """
    PA-unique Section F: Portfolio View — How PA Fits.
    Static comparison matrix of Health / Life / PA coverage.
    """
    return {
        "matrix": [
            {"risk": "Medical bills", "health": "covered", "life": "not_covered", "pa": "partial"},
            {"risk": "Death benefit", "health": "not_covered", "life": "covered", "pa": "covered"},
            {"risk": "Disability payout", "health": "not_covered", "life": "not_covered", "pa": "covered"},
            {"risk": "Income loss", "health": "not_covered", "life": "not_covered", "pa": "covered"},
            {"risk": "EMI protection", "health": "not_covered", "life": "not_covered", "pa": "conditional"}
        ],
        "footerNote": "PA fills the gaps Health and Life don't cover: disability payouts and income replacement during recovery."
    }
