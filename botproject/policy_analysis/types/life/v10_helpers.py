"""Life Insurance V10 Enhanced Helpers (EAZR_02 Spec)"""
import logging
import re
from policy_analysis.utils import safe_num, get_score_label

logger = logging.getLogger(__name__)


# ==================== LIFE INSURANCE V10 HELPERS (EAZR_02 Spec) ====================

def _get_life_strengths(scores_detailed: dict, category_data: dict) -> list:
    """
    Extract top 5 coverage/value strengths from life scoring factors.
    Factors scoring >=80% of max points are treated as strengths.
    Returns list of {"title": str, "reason": str, "priority": int}.
    """
    strengths = []
    scores = scores_detailed.get("scores", {})
    product_type = scores_detailed.get("productType", "endowment")
    is_term = product_type == "term"

    # Extract from S1 factors
    s1 = scores.get("s1")
    if s1 and isinstance(s1, dict):
        for factor in s1.get("factors", []):
            pts = factor.get("pointsEarned", 0)
            max_pts = factor.get("pointsMax", 1)
            if max_pts <= 0 or (pts / max_pts) < 0.80:
                continue
            name = factor.get("name", "")
            your_policy = factor.get("yourPolicy", "")
            name_lower = name.lower()

            if "sa vs" in name_lower or "income" in name_lower:
                strengths.append({"title": f"Strong Income Coverage: {your_policy}", "reason": "Sum Assured provides solid income replacement", "priority": 1})
            elif "liability" in name_lower:
                strengths.append({"title": "Liability Coverage Adequate", "reason": your_policy, "priority": 2})
            elif "term" in name_lower:
                strengths.append({"title": f"Coverage {your_policy}", "reason": "Policy covers through your earning years", "priority": 3})
            elif "rider" in name_lower:
                strengths.append({"title": f"Riders Active: {your_policy}", "reason": "Essential protection riders in place", "priority": 4})
            elif "status" in name_lower:
                strengths.append({"title": "Policy Active & Affordable", "reason": "Premium is well within affordable range", "priority": 5})

    # Extract from S2 factors (savings only)
    s2 = scores.get("s2")
    if s2 and isinstance(s2, dict) and not is_term:
        for factor in s2.get("factors", []):
            pts = factor.get("pointsEarned", 0)
            max_pts = factor.get("pointsMax", 1)
            if max_pts <= 0 or (pts / max_pts) < 0.80:
                continue
            name = factor.get("name", "")
            your_policy = factor.get("yourPolicy", "")
            name_lower = name.lower()

            if "sv vs" in name_lower or "premiums paid" in name_lower:
                strengths.append({"title": "Surrender Value Exceeds Premiums Paid", "reason": f"{your_policy} \u2014 money is growing", "priority": 6})
            elif "bonus" in name_lower or "cagr" in name_lower:
                strengths.append({"title": f"Strong Returns: {your_policy}", "reason": "Competitive bonus rate or fund growth", "priority": 7})
            elif "maturity" in name_lower:
                strengths.append({"title": f"Maturity Value: {your_policy}", "reason": "Projected maturity exceeds investment", "priority": 8})
            elif "lock-in" in name_lower:
                strengths.append({"title": f"Lock-in Progress: {your_policy}", "reason": "Policy is past early-year penalty zone", "priority": 9})
            elif "loan" in name_lower:
                strengths.append({"title": f"Loan Available: {your_policy}", "reason": "Can access funds via policy loan without surrendering", "priority": 10})

    # Also check riders directly from category_data for additional strengths
    riders = category_data.get("riders", []) or []
    category_str = str(category_data).lower()
    riders_str = str(riders).lower()

    if not any("rider" in s.get("title", "").lower() for s in strengths):
        # Check individual riders
        if "critical illness" in category_str or "critical illness" in riders_str:
            ci_sa = 0
            for r in riders:
                if isinstance(r, dict) and "critical" in str(r.get("riderName", "")).lower():
                    ci_sa = r.get("riderSumAssured", 0) or 0
            if ci_sa > 0:
                strengths.append({"title": f"Critical Illness Cover: \u20b9{ci_sa/100000:.0f}L", "reason": "Lump-sum payout on diagnosis of major illness", "priority": 4})

        if "waiver" in category_str or "waiver" in riders_str:
            strengths.append({"title": "Waiver of Premium Active", "reason": "Premiums auto-paid if you become disabled or critically ill", "priority": 4})

    return sorted(strengths, key=lambda x: x.get("priority", 99))[:5]


def _analyze_life_gaps(category_data: dict, sum_assured: int, formatted_gaps: list, scores_detailed: dict) -> dict:
    """
    Analyze 7 gap types (G001-G007) for life insurance per EAZR_02 spec.
    Returns: {"summary": {"high": N, "medium": N, "low": N, "opportunity": N, "total": N}, "gaps": [...]}
    """
    gaps = []
    riders = category_data.get("riders", []) or []
    bonus_val = category_data.get("bonusValue", {}) or {}
    policy_info = category_data.get("policyIdentification", {}) or {}
    coverage_details = category_data.get("coverageDetails", {}) or {}
    premium_details = category_data.get("premiumDetails", {}) or {}
    policyholder = category_data.get("policyholderLifeAssured", {}) or {}
    category_str = str(category_data).lower()
    riders_str = str(riders).lower()
    product_type = scores_detailed.get("productType", "endowment")
    is_savings = product_type != "term"

    # Extract annual premium for cost calculations
    _gap_premium = 0
    try:
        _gap_prem_raw = premium_details.get("premiumAmount") or 0
        _gap_premium = float(str(_gap_prem_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('\u20b9', '').strip()) if _gap_prem_raw else 0
    except (ValueError, TypeError):
        _gap_premium = 0
    _gap_freq = (premium_details.get("premiumFrequency") or "").lower()
    _gap_annual_premium = _gap_premium
    if _gap_freq == "monthly":
        _gap_annual_premium = _gap_premium * 12
    elif _gap_freq == "quarterly":
        _gap_annual_premium = _gap_premium * 4
    elif _gap_freq in ("half-yearly", "semi-annual", "semi_annual"):
        _gap_annual_premium = _gap_premium * 2

    # Derive income: try extracted -> SA/10 -> premium*10 (whichever is higher and non-zero)
    _extracted_income = 0
    try:
        _inc_raw = policyholder.get("annualIncome") or policyholder.get("income") or 0
        _extracted_income = float(str(_inc_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('\u20b9', '').strip()) if _inc_raw else 0
    except (ValueError, TypeError):
        _extracted_income = 0
    _sa_derived_income = sum_assured / 10 if sum_assured > 0 else 0
    _prem_derived_income = _gap_annual_premium * 10 if _gap_annual_premium > 0 else 0
    estimated_annual_income = _extracted_income if _extracted_income > 0 else max(_sa_derived_income, _prem_derived_income)
    if estimated_annual_income <= 0:
        estimated_annual_income = sum_assured / 10 if sum_assured > 0 else 0
    recommended_cover = estimated_annual_income * 10 if estimated_annual_income > 0 else sum_assured * 2

    # G001: Life Cover Below Recommended
    if sum_assured < recommended_cover:
        gap_amount = recommended_cover - sum_assured
        fix_cost = max(8000, int(gap_amount * 0.001))  # ~₹1 per ₹1000 SA for term
        gaps.append({
            "gapId": "G001", "severity": "high",
            "title": "Life Cover Below Recommended",
            "impact": f"Total life cover \u20b9{sum_assured/100000:.0f}L vs \u20b9{recommended_cover/100000:.0f}L recommended (10x income)",
            "solution": f"Add \u20b9{gap_amount/100000:.0f}L term plan",
            "estimatedCost": fix_cost,
            "estimatedCostFormatted": f"~\u20b9{fix_cost:,}/yr",
            "eazrEmi": int(fix_cost / 12) if fix_cost > 0 else 0
        })

    # G002: Loan Exposure Not Covered (estimated)
    # If SA is very low, likely doesn't cover typical loans
    if sum_assured < 1000000:
        _g002_gap = max(0, 1000000 - sum_assured)
        _g002_cost = max(3000, int(_g002_gap * 0.001))  # ~₹1 per ₹1000 SA for term
        gaps.append({
            "gapId": "G002", "severity": "high",
            "title": "Loan Exposure Not Covered",
            "impact": f"Sum Assured \u20b9{sum_assured/100000:.1f}L may not cover home/auto/personal loans",
            "solution": f"Add \u20b9{_g002_gap/100000:.0f}L term cover to match loan exposure",
            "estimatedCost": _g002_cost,
            "estimatedCostFormatted": f"~\u20b9{_g002_cost:,}/yr",
            "eazrEmi": int(_g002_cost / 12) if _g002_cost > 0 else 0
        })

    # G003: No Critical Illness Coverage
    has_ci = "critical illness" in category_str or "critical illness" in riders_str
    if not has_ci:
        _ci_cover = max(500000, int(sum_assured * 0.25))  # CI cover ~25% of SA
        _g003_cost = max(3000, min(12000, int(_ci_cover * 0.0006)))  # ~₹0.60 per ₹1000 CI cover
        gaps.append({
            "gapId": "G003", "severity": "medium",
            "title": "No Critical Illness Coverage",
            "impact": f"Major illness causes income loss; life cover pays only on death. No lump-sum on diagnosis of critical illness.",
            "solution": f"Add CI rider ~\u20b9{_ci_cover/100000:.0f}L",
            "estimatedCost": _g003_cost,
            "estimatedCostFormatted": f"~\u20b9{_g003_cost:,}/yr",
            "eazrEmi": int(_g003_cost / 12) if _g003_cost > 0 else 0
        })

    # G004: No Waiver of Premium
    has_wop = "premium waiver" in category_str or "waiver of premium" in category_str or "waiver" in riders_str
    if not has_wop:
        _g004_cost = max(300, int(_gap_annual_premium * 0.03)) if _gap_annual_premium > 0 else max(300, int(sum_assured * 0.00003))  # ~3% of premium
        gaps.append({
            "gapId": "G004", "severity": "medium",
            "title": "No Waiver of Premium",
            "impact": f"If disabled and unable to earn, you must still pay premiums of \u20b9{_gap_annual_premium:,.0f}/yr or policy will lapse." if _gap_annual_premium > 0 else "If disabled and unable to earn, you must still pay premiums or policy will lapse.",
            "solution": "Add Waiver of Premium rider",
            "estimatedCost": _g004_cost,
            "estimatedCostFormatted": f"~\u20b9{_g004_cost:,}/yr",
            "eazrEmi": 0
        })

    # G005: No Accidental Death Benefit
    has_adb = "accidental death" in category_str or "adb" in category_str or "addb" in riders_str or "accidental death" in riders_str
    if not has_adb:
        _g005_cost = max(500, int(sum_assured * 0.0005))  # ~₹0.50 per ₹1000 SA
        gaps.append({
            "gapId": "G005", "severity": "low",
            "title": "No Accidental Death Benefit",
            "impact": f"In accidental death, family receives only base SA \u20b9{sum_assured/100000:.1f}L. No additional payout.",
            "solution": f"Add ADB rider for extra \u20b9{sum_assured/100000:.0f}L accidental cover",
            "estimatedCost": _g005_cost,
            "estimatedCostFormatted": f"~\u20b9{_g005_cost:,}/yr",
            "eazrEmi": 0
        })

    # G006: Nominee Review Needed
    start_date_str = policy_info.get("policyIssueDate", "")
    policy_age = 0
    if start_date_str:
        try:
            from datetime import datetime as _dt
            s_dt = _dt.strptime(str(start_date_str).split("T")[0], "%Y-%m-%d")
            policy_age = (_dt.now() - s_dt).days // 365
        except (ValueError, TypeError):
            pass

    nominees = category_data.get("nomination", {}).get("nominees") or []
    if policy_age >= 3 or not nominees:
        gaps.append({
            "gapId": "G006", "severity": "low",
            "title": "Nominee Review Needed",
            "impact": f"Policy is {policy_age} years old. Nominee details may be outdated." if policy_age >= 3 else "No nominee details found.",
            "solution": "Review and update nominee details with insurer",
            "estimatedCost": 0,
            "estimatedCostFormatted": "No cost",
            "eazrEmi": 0
        })

    # G007: SVF Opportunity (savings plans with SV >= 50K)
    surrender_val = 0
    try:
        sv_raw = bonus_val.get("surrenderValue") or 0
        surrender_val = float(str(sv_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('\u20b9', '').strip()) if sv_raw else 0
    except (ValueError, TypeError):
        surrender_val = 0

    if is_savings and surrender_val >= 50000:
        svf_amount = surrender_val * 0.9
        gaps.append({
            "gapId": "G007", "severity": "opportunity",
            "title": f"SVF Available \u2014 \u20b9{svf_amount/100000:.1f}L Accessible",
            "impact": f"Your policy's SV is \u20b9{surrender_val/100000:.1f}L. Access up to 90% via EAZR SVF without surrendering.",
            "solution": "Check SVF eligibility at EAZR",
            "estimatedCost": 0,
            "estimatedCostFormatted": "No cost",
            "eazrEmi": 0
        })

    # Sort: high > medium > low > opportunity
    severity_order = {"high": 0, "medium": 1, "low": 2, "opportunity": 3}
    gaps.sort(key=lambda g: severity_order.get(g.get("severity", ""), 4))

    # Special rule: G007 always in top-3 if present
    # If more than 3 gaps and G007 exists, ensure it's in the first 3
    g007_gap = next((g for g in gaps if g.get("gapId") == "G007"), None)
    if g007_gap and len(gaps) > 3:
        gaps_without_g007 = [g for g in gaps if g.get("gapId") != "G007"]
        # Take top 2 by severity + G007
        top_2 = gaps_without_g007[:2]
        top_2.append(g007_gap)
        # Rebuild: top 3 (with G007) + remaining
        remaining = [g for g in gaps_without_g007[2:]]
        gaps = top_2 + remaining

    # Summary
    high_count = sum(1 for g in gaps if g["severity"] == "high")
    medium_count = sum(1 for g in gaps if g["severity"] == "medium")
    low_count = sum(1 for g in gaps if g["severity"] == "low")
    opportunity_count = sum(1 for g in gaps if g["severity"] == "opportunity")

    return {
        "summary": {"high": high_count, "medium": medium_count, "low": low_count, "opportunity": opportunity_count, "total": len(gaps)},
        "gaps": gaps
    }


def _select_life_primary_scenario(scores_detailed: dict, gaps_result: dict, life_scenarios: list) -> str:
    """
    Auto-select the most relevant life scenario per EAZR_02 spec Section 3.5.
    Term -> L001, Savings with SV >= 1L -> L002, else L001.
    """
    product_type = scores_detailed.get("productType", "endowment")
    render_mode = scores_detailed.get("renderMode", {})

    if render_mode.get("mode") == "PROTECTION_ONLY" or product_type == "term":
        return "L001"

    # Savings: check SV
    s3 = scores_detailed.get("scores", {}).get("s3")
    if s3 and isinstance(s3, dict):
        sv_factor = next((f for f in s3.get("factors", []) if "surrender value" in f.get("name", "").lower()), None)
        if sv_factor and sv_factor.get("pointsEarned", 0) >= 25:  # SV >= 1L
            return "L002"

    # Check if G001 exists
    gap_ids = {g.get("gapId", "") for g in gaps_result.get("gaps", [])}
    if "G001" in gap_ids:
        return "L001"

    return "L002"


def _build_life_recommendations_v10(gaps_result: dict, category_data: dict, sum_assured: int, scores_detailed: dict) -> dict:
    """
    Build V10 recommendations from life gap analysis.
    Returns: {"quickWins": [...], "priorityUpgrades": [...], "totalUpgradeCost": {"annual": N, "monthlyEmi": N}}
    """
    quick_wins = []
    priority_upgrades = []
    product_type = scores_detailed.get("productType", "endowment")
    is_savings = product_type != "term"

    # Quick Win 1: Nominee review
    gaps = gaps_result.get("gaps", [])
    g006 = next((g for g in gaps if g.get("gapId") == "G006"), None)
    if g006:
        quick_wins.append({
            "title": "Review Nominee Details",
            "description": g006.get("impact", "Verify nominee details are correct and up to date"),
            "action": "Contact insurer or update via their app/portal"
        })

    # Quick Win 2: Policy active check
    policy_info = category_data.get("policyIdentification", {}) or {}
    policy_status = str(policy_info.get("policyStatus", "")).lower()
    if "active" in policy_status:
        quick_wins.append({
            "title": "Policy is Active \u2014 Keep It Running",
            "description": "Your policy is in-force. Ensure premiums are paid on time to maintain coverage.",
            "action": "Set up auto-pay or calendar reminders for premium dates"
        })

    # Priority upgrades from gaps (excluding G006 and G007)
    priority = 1
    for gap in gaps:
        gap_id = gap.get("gapId", "")
        if gap_id in ("G006", "G007"):
            continue
        severity = gap.get("severity", "medium")
        est_cost = gap.get("estimatedCost", 0)
        emi = gap.get("eazrEmi", 0)

        priority_label = "HIGH" if severity == "high" else ("MEDIUM" if severity == "medium" else "LOW")
        when = "Immediately" if severity == "high" else ("At renewal" if severity == "medium" else "When convenient")
        category = "gap_fill" if gap_id in ("G001", "G002") else "enhancement"

        priority_upgrades.append({
            "id": f"REC_{gap_id}",
            "priority": priority,
            "priorityLabel": priority_label,
            "title": gap.get("solution", gap.get("title", "")),
            "description": gap.get("impact", ""),
            "gapMapping": [gap_id],
            "estimatedCost": est_cost,
            "estimatedCostFormatted": gap.get("estimatedCostFormatted", ""),
            "eazrEmi": emi,
            "eazrEmiFormatted": f"\u20b9{emi:,}/mo" if emi > 0 else "",
            "impact": severity,
            "when": when,
            "category": category,
            "ipfEligible": est_cost >= 5000
        })
        priority += 1

    # SVF opportunity as recommendation (for savings)
    g007 = next((g for g in gaps if g.get("gapId") == "G007"), None)
    if g007 and is_savings:
        priority_upgrades.append({
            "id": "REC_G007",
            "priority": priority,
            "priorityLabel": "OPPORTUNITY",
            "title": "Explore EAZR SVF",
            "description": g007.get("impact", "Access funds without surrendering your policy"),
            "gapMapping": ["G007"],
            "estimatedCost": 0,
            "estimatedCostFormatted": "No cost",
            "eazrEmi": 0,
            "eazrEmiFormatted": "",
            "impact": "opportunity",
            "when": "Anytime",
            "category": "financing",
            "ipfEligible": False,
            "svfEligible": True
        })

    # IPF recommendation (if annual premium >= 25K)
    premium_details = category_data.get("premiumDetails", {}) or {}
    premium = 0
    try:
        premium_raw = premium_details.get("premiumAmount") or 0
        premium = float(str(premium_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip()) if premium_raw else 0
    except (ValueError, TypeError):
        premium = 0
    freq = (premium_details.get("premiumFrequency") or "").lower()
    annual_premium = premium
    if freq == "monthly":
        annual_premium = premium * 12
    elif freq == "quarterly":
        annual_premium = premium * 4
    elif freq in ("half-yearly", "semi-annual", "semi_annual"):
        annual_premium = premium * 2

    if annual_premium >= 25000:
        emi_amt = int(annual_premium / 12)
        priority_upgrades.append({
            "id": "REC_IPF",
            "priority": priority + 1,
            "priorityLabel": "OPPORTUNITY",
            "title": "Pay Premium in Easy EMIs",
            "description": f"Convert annual premium of \u20b9{annual_premium:,.0f} to monthly EMIs with EAZR IPF",
            "gapMapping": [],
            "estimatedCost": 0,
            "estimatedCostFormatted": "No additional cost",
            "eazrEmi": emi_amt,
            "eazrEmiFormatted": f"\u20b9{emi_amt:,}/mo",
            "impact": "opportunity",
            "when": "Next premium cycle",
            "category": "financing",
            "ipfEligible": True
        })

    # Total upgrade cost (exclude financing/opportunity items)
    total_annual = sum(u.get("estimatedCost", 0) for u in priority_upgrades if u.get("category") not in ("financing",))
    total_monthly_emi = int(total_annual / 12) if total_annual > 0 else 0

    return {
        "quickWins": quick_wins,
        "priorityUpgrades": priority_upgrades,
        "totalUpgradeCost": {
            "annual": total_annual,
            "annualFormatted": f"\u20b9{total_annual:,}/yr",
            "monthlyEmi": total_monthly_emi,
            "monthlyEmiFormatted": f"\u20b9{total_monthly_emi:,}/mo"
        }
    }


def _build_life_svf_opportunity(category_data: dict, scores_detailed: dict) -> dict:
    """
    Build SVF opportunity card data for savings plans with SV >= 50K.
    Returns None for term policies or if SV < 50K.
    """
    product_type = scores_detailed.get("productType", "endowment")
    if product_type == "term":
        return None

    bonus_val = category_data.get("bonusValue", {}) or {}
    surrender_val = 0
    try:
        sv_raw = bonus_val.get("surrenderValue") or 0
        surrender_val = float(str(sv_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('\u20b9', '').strip()) if sv_raw else 0
    except (ValueError, TypeError):
        surrender_val = 0

    if surrender_val < 50000:
        return None

    svf_amount = surrender_val * 0.9

    return {
        "eligible": True,
        "surrenderValue": int(surrender_val),
        "surrenderValueFormatted": f"\u20b9{surrender_val/100000:.2f}L" if surrender_val >= 100000 else f"\u20b9{surrender_val:,.0f}",
        "maxSvfAmount": int(svf_amount),
        "maxSvfFormatted": f"\u20b9{svf_amount/100000:.2f}L" if svf_amount >= 100000 else f"\u20b9{svf_amount:,.0f}",
        "comparison": [
            {"feature": "Get Cash", "surrender": True, "svf": True},
            {"feature": "Keep Life Cover", "surrender": False, "svf": True},
            {"feature": "Maturity Intact", "surrender": False, "svf": True}
        ],
        "cta": {"label": "Check SVF Eligibility", "action": "svf_check"}
    }
