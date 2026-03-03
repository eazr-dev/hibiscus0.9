"""Health Insurance V10 Enhanced Helpers"""
import logging
import re
from policy_analysis.utils import safe_num, get_score_label

logger = logging.getLogger(__name__)


# ==================== HEALTH INSURANCE V10 HELPERS ====================
# Used by _build_light_analysis() for health-specific policyAnalyzer structure

def _get_health_strengths(scores_detailed: dict, category_data: dict) -> list:
    """
    Extract top coverage strengths from scoring factors that scored >=80% of their max points.
    Returns up to 5 strengths sorted by priority per spec Section 2.3.
    """
    strengths = []
    scores = scores_detailed.get("scores", {})

    for score_key in ["s1", "s2", "s3", "s4"]:
        score_data = scores.get(score_key)
        if not score_data or not isinstance(score_data, dict):
            continue
        for factor in score_data.get("factors", []):
            pts = factor.get("pointsEarned", 0)
            max_pts = factor.get("pointsMax", 1)
            if max_pts <= 0 or (pts / max_pts) < 0.80:
                continue

            name = factor.get("name", "")
            your_policy = factor.get("yourPolicy", "")
            name_lower = name.lower()

            # Build human-friendly titles per factor type
            if "sum insured" in name_lower:
                title = f"Strong Sum Insured: {your_policy}"
                reason = "Adequate for most metro hospitalizations"
            elif "room rent" in name_lower:
                title = "No Room Rent Cap" if "no limit" in str(your_policy).lower() else f"Good Room Rent: {your_policy}"
                reason = "Full room charges covered regardless of hospital choice"
            elif "restoration" in name_lower:
                title = "Restoration Benefit Available"
                reason = "Sum insured resets after each claim — no coverage gap"
            elif "consumable" in name_lower:
                title = "Consumables Covered"
                reason = "Surgical disposables (10–15% of bills) included"
            elif "claim settlement" in name_lower:
                title = f"{your_policy} Claim Settlement Ratio"
                reason = "Insurer has strong track record of paying claims"
            elif "lifetime renew" in name_lower or "renewab" in name_lower:
                title = "Lifetime Renewability Guaranteed"
                reason = "Insurer cannot refuse renewal regardless of claims"
            elif "ncb" in name_lower or "no claim bonus" in name_lower:
                title = "Strong No-Claim Bonus"
                reason = "Effective coverage boosted by NCB"
            elif "modern treatment" in name_lower:
                title = "Modern Treatments Covered"
                reason = "Robotic surgery, immunotherapy, stem cell therapy included"
            elif "network" in name_lower:
                title = f"Strong Hospital Network: {your_policy}"
                reason = "Wide cashless hospital network for easy access"
            elif "co-payment" in name_lower or "copay" in name_lower:
                title = "Zero Co-payment"
                reason = "No percentage deduction on claim payouts"
            elif "sub-limit" in name_lower:
                title = "No Sub-limits on Procedures"
                reason = "Full coverage for surgeries without internal caps"
            elif "icu" in name_lower:
                title = "No ICU Limit"
                reason = "Full ICU charges covered without daily caps"
            elif "cashless" in name_lower:
                title = "Fast Cashless Processing"
                reason = f"Pre-authorization: {your_policy}"
            else:
                title = name
                reason = f"{your_policy}" if your_policy and your_policy != "Not specified" else f"Scored {pts}/{max_pts}"

            strengths.append({"title": title, "reason": reason, "priority": len(strengths) + 1})

    return strengths[:5]


def _analyze_health_gaps(category_data: dict, sum_assured: int, insurer_name: str, formatted_gaps: list) -> dict:
    """
    Analyze 12 gap types (G001-G012) for health insurance per spec Section 2.4.
    Returns: {"summary": {"high": N, "medium": N, "info": N, "total": N}, "gaps": [...]}
    """
    import re as _re
    from services.protection_score_calculator import calculate_ipf_emi, _lookup_csr

    coverage_details = category_data.get("coverageDetails", {}) or {}
    waiting_periods = category_data.get("waitingPeriods", {}) or {}
    copay_details = category_data.get("copayDetails", {}) or {}
    sub_limits = category_data.get("subLimits", {}) or {}
    ncb_data = category_data.get("noClaimBonus", {}) or {}
    policy_id = category_data.get("policyIdentification", {}) or {}
    claim_info = category_data.get("claimInfo", {}) or {}
    members = category_data.get("insuredMembers", []) or category_data.get("membersCovered", []) or []
    category_str = str(category_data).lower()

    gaps = []

    # G001: SI Inadequacy
    member_count = max(len(members), 1)
    if member_count >= 3:
        recommended_si = 5000000
    elif member_count == 2:
        recommended_si = 2500000
    else:
        recommended_si = 1000000

    if sum_assured < recommended_si:
        gap_amt = recommended_si - sum_assured
        fix_cost = max(4000, int(gap_amt * 0.004))
        gaps.append({
            "gapId": "G001", "severity": "high",
            "title": "Sum Insured Below Recommended",
            "impact": f"\u20b9{sum_assured:,} current vs \u20b9{recommended_si:,} recommended for metro family of {member_count}",
            "fix": f"Increase SI at renewal by \u20b9{gap_amt:,}",
            "estimatedCost": fix_cost, "estimatedCostFormatted": f"+\u20b9{fix_cost:,}/yr",
            "eazrEmi": calculate_ipf_emi(fix_cost)
        })

    # G002: Room Rent Cap
    room_rent = coverage_details.get("roomRentLimit", "")
    room_str = str(room_rent).lower() if room_rent else ""
    if room_rent and not any(kw in room_str for kw in ["no limit", "no sub", "no cap", "unlimited"]):
        fix_cost = max(1500, min(8000, int(sum_assured * 0.0007)))
        gaps.append({
            "gapId": "G002", "severity": "high",
            "title": "Room Rent Cap Below City Rates",
            "impact": f"{room_rent} limit \u2014 entire claim reduced proportionately if you choose a higher room",
            "fix": "Upgrade to no-cap plan at renewal",
            "estimatedCost": fix_cost, "estimatedCostFormatted": f"+\u20b9{fix_cost:,}/yr",
            "eazrEmi": calculate_ipf_emi(fix_cost)
        })

    # G003: ICU Limit
    icu_limit = coverage_details.get("icuLimit", "")
    icu_str = str(icu_limit).lower() if icu_limit else ""
    if icu_limit and icu_str not in ["", "none", "null"] and not any(kw in icu_str for kw in ["no limit", "unlimited", "no cap", "no sub"]):
        g003_cost = max(1000, min(5000, int(sum_assured * 0.0004)))
        gaps.append({
            "gapId": "G003", "severity": "high",
            "title": "ICU Coverage Limited",
            "impact": f"ICU limit: {icu_limit}. ICU costs \u20b925,000\u201350,000/day in metro hospitals",
            "fix": "Upgrade to plan with no ICU sub-limit",
            "estimatedCost": g003_cost, "estimatedCostFormatted": f"+\u20b9{g003_cost:,}/yr",
            "eazrEmi": calculate_ipf_emi(g003_cost)
        })

    # G004: Consumables Not Covered
    consumables = coverage_details.get("consumablesCoverage") or coverage_details.get("consumablesCover")
    cons_str = str(consumables).lower() if consumables else ""
    # Check add-on policies (Care Shield, Claim Shield, Claim Shield Plus cover consumables)
    _addon_policies_g = category_data.get("addOnPolicies", {}) or {}
    _addon_list_g = _addon_policies_g.get("addOnPoliciesList", []) or []
    _has_cons_addon_g = (
        bool(_addon_policies_g.get("claimShield"))
        or any(
            any(kw in str(a.get("addOnName", "")).lower() for kw in ["care shield", "claim shield", "consumable"])
            for a in _addon_list_g if isinstance(a, dict)
        )
    )
    # Also check premiumBreakdown.addOnPremiums.otherAddOns for paid consumable add-ons
    _pb_g4 = category_data.get("premiumBreakdown", {}) or {}
    _ap_g4 = _pb_g4.get("addOnPremiums", {}) or {}
    _oa_g4 = _ap_g4.get("otherAddOns", {}) if isinstance(_ap_g4, dict) else {}
    for _aon_g4, _apv_g4 in _oa_g4.items():
        if any(kw in str(_aon_g4).lower() for kw in ["claim shield", "care shield", "consumable"]):
            try:
                if float(_apv_g4) > 0:
                    _has_cons_addon_g = True
            except (ValueError, TypeError):
                pass
    has_consumables = (
        _has_cons_addon_g
        or cons_str in ["true", "yes", "covered", "available", "included"]
        or consumables is True
    )
    if not has_consumables:
        g004_cost = max(500, min(3000, int(sum_assured * 0.00016)))
        gaps.append({
            "gapId": "G004", "severity": "medium",
            "title": "Consumables Not Covered",
            "impact": f"Surgical disposables = 10\u201315% of every hospital bill (\u20b9{int(sum_assured * 0.10):,}\u2013\u20b9{int(sum_assured * 0.15):,} on \u20b9{sum_assured:,} SI)",
            "fix": "Add consumables coverage at renewal",
            "estimatedCost": g004_cost, "estimatedCostFormatted": f"+\u20b9{g004_cost:,}/yr",
            "eazrEmi": calculate_ipf_emi(g004_cost)
        })

    # G005: Co-payment
    general_copay = copay_details.get("generalCopay", "")
    copay_str = str(general_copay).lower() if general_copay else ""
    copay_match = _re.search(r'(\d+)', copay_str)
    copay_pct = int(copay_match.group(1)) if copay_match else 0
    if copay_pct > 0 and not any(kw in copay_str for kw in ["no co", "nil", "none"]):
        g005_cost = max(1500, min(8000, int(sum_assured * copay_pct / 100 * 0.005)))
        gaps.append({
            "gapId": "G005", "severity": "medium",
            "title": f"Co-payment of {copay_pct}% Applicable",
            "impact": f"You pay {copay_pct}% of every claim \u2014 \u20b9{int(500000 * copay_pct / 100):,} on a \u20b95L bill",
            "fix": "Switch to zero co-pay plan at renewal",
            "estimatedCost": g005_cost, "estimatedCostFormatted": f"+\u20b9{g005_cost:,}/yr",
            "eazrEmi": calculate_ipf_emi(g005_cost)
        })

    # G006: Sub-limits on Procedures
    sub_limit_items = []
    for key in ["cataractLimit", "jointReplacementLimit", "internalProsthesisLimit", "kidneyStoneLimit", "gallStoneLimit"]:
        val = sub_limits.get(key)
        if val and str(val).lower() not in ["", "none", "null", "no limit", "up to sum insured", "up to si"]:
            sub_limit_items.append(f"{key.replace('Limit', '')}: {val}")
    if sub_limit_items:
        g006_cost = max(1000, min(6000, int(len(sub_limit_items) * 1200)))
        gaps.append({
            "gapId": "G006", "severity": "medium",
            "title": f"{len(sub_limit_items)} Sub-limit(s) on Procedures",
            "impact": f"Internal caps on {', '.join(sub_limit_items[:2])} reduce effective coverage",
            "fix": "Upgrade to plan with no sub-limits",
            "estimatedCost": g006_cost, "estimatedCostFormatted": f"+\u20b9{g006_cost:,}/yr",
            "eazrEmi": calculate_ipf_emi(g006_cost)
        })

    # G007: Waiting Period Exposure
    ped_waiting = waiting_periods.get("preExistingDiseaseWaiting", "")
    ped_str = str(ped_waiting).lower() if ped_waiting else ""
    if ped_waiting and not any(kw in ped_str for kw in ["no waiting", "waived", "nil", "0", "day 1", "covered"]):
        # Check if waiting periods are waived via add-ons or portability continuity
        from services.protection_score_calculator import _parse_indian_date, _detect_waiting_waivers
        _g007_waivers = _detect_waiting_waivers(category_data)
        ped_completed_g = _g007_waivers["ped"]

        # Also check declaredPed field
        if not ped_completed_g:
            declared_ped = category_data.get("declaredPed", {}) or {}
            ped_completed_g = bool(declared_ped.get("pedWaitingPeriodCompleted"))

        if not ped_completed_g:
            policy_history_g = category_data.get("policyHistory", {}) or {}
            first_enrollment_g = (policy_history_g.get("firstEnrollmentDate") or
                                  policy_history_g.get("insuredSinceDate"))
            if first_enrollment_g:
                enrollment_dt_g = _parse_indian_date(str(first_enrollment_g))
                if enrollment_dt_g:
                    from datetime import datetime as _dt_g
                    years_insured_g = (_dt_g.now() - enrollment_dt_g).days / 365.25
                    wait_match_g = _re.search(r'(\d+)\s*(?:month|year)', ped_str)
                    if wait_match_g:
                        wait_months_g = int(wait_match_g.group(1))
                        if "year" in ped_str[wait_match_g.start():wait_match_g.end() + 5]:
                            wait_months_g *= 12
                        if years_insured_g * 12 >= wait_months_g:
                            ped_completed_g = True
            # Fallback: continuousCoverageYears
            cont_yrs_g = policy_history_g.get("continuousCoverageYears")
            if not ped_completed_g and cont_yrs_g:
                try:
                    cy_g = float(str(cont_yrs_g).replace("+", "").strip())
                    if cy_g >= 4:
                        ped_completed_g = True
                except (ValueError, TypeError):
                    pass

        if not ped_completed_g:
            gaps.append({
                "gapId": "G007", "severity": "info",
                "title": "Waiting Period Active for Pre-existing Diseases",
                "impact": f"PED waiting: {ped_waiting}. Claims for existing conditions rejected during this period",
                "fix": "Maintain continuous coverage \u2014 do not let policy lapse",
                "estimatedCost": 0, "estimatedCostFormatted": "No cost",
                "eazrEmi": 0
            })

    # G008: No Restoration
    restoration = coverage_details.get("restoration")
    has_restoration = bool(restoration) if not isinstance(restoration, dict) else restoration.get("available", False)
    if not has_restoration and "restoration" not in category_str and "recharge" not in category_str:
        g008_cost = max(1000, min(5000, int(sum_assured * 0.0003)))
        gaps.append({
            "gapId": "G008", "severity": "medium",
            "title": "No Restoration Benefit",
            "impact": f"Once \u20b9{sum_assured:,} SI exhausted in a year, no further claims possible until renewal",
            "fix": "Upgrade to plan with restoration benefit",
            "estimatedCost": g008_cost, "estimatedCostFormatted": f"+\u20b9{g008_cost:,}/yr",
            "eazrEmi": calculate_ipf_emi(g008_cost)
        })

    # G009: Low CSR
    csr = _lookup_csr(insurer_name)
    csr_from_data = claim_info.get("claimSettlementRatio", "")
    if csr_from_data:
        try:
            csr = float(str(csr_from_data).replace("%", "").strip())
        except (ValueError, TypeError):
            pass
    if 0 < csr < 85:
        gaps.append({
            "gapId": "G009", "severity": "info",
            "title": f"Insurer CSR Below Average ({csr:.0f}%)",
            "impact": f"Claim Settlement Ratio of {csr:.0f}% means ~{100 - csr:.0f}% claims may face challenges",
            "fix": "Consider portability to a higher-CSR insurer at renewal",
            "estimatedCost": 0, "estimatedCostFormatted": "No additional cost",
            "eazrEmi": 0
        })

    # G010: No NCB
    ncb_available = ncb_data.get("available", False)
    if isinstance(ncb_available, str):
        ncb_available = ncb_available.lower() in ["yes", "true"]
    if not ncb_available and "no claim bonus" not in category_str and "ncb" not in category_str:
        g010_cost = max(800, min(3000, int(sum_assured * 0.0002)))
        gaps.append({
            "gapId": "G010", "severity": "info",
            "title": "No Claim Bonus Not Available",
            "impact": "Your effective coverage stays flat \u2014 no annual increase for claim-free years",
            "fix": "Consider plan with NCB to grow coverage over time",
            "estimatedCost": g010_cost, "estimatedCostFormatted": f"+\u20b9{g010_cost:,}/yr approx",
            "eazrEmi": calculate_ipf_emi(g010_cost)
        })

    # G011: No Super Top-up
    if sum_assured < 1500000:
        topup_gap = max(0, 2500000 - sum_assured)
        g011_cost = max(2500, min(8000, int(topup_gap * 0.0018)))
        gaps.append({
            "gapId": "G011", "severity": "high",
            "title": "No Super Top-up Coverage",
            "impact": f"\u20b9{sum_assured:,} SI may exhaust in cancer/cardiac cases costing \u20b910\u201325L",
            "fix": f"Add Super Top-up of \u20b925L with \u20b9{sum_assured:,} deductible",
            "estimatedCost": g011_cost, "estimatedCostFormatted": f"+\u20b9{g011_cost:,}/yr",
            "eazrEmi": calculate_ipf_emi(g011_cost)
        })

    # G012: No Maternity (floater with young female only)
    policy_type_str = str(policy_id.get("policyType", "")).lower()
    is_floater = any(kw in policy_type_str for kw in ["floater", "family"]) or len(members) > 1
    has_young_female = any(
        str(m.get("memberGender", "")).lower() == "female" and 18 <= (m.get("memberAge", 0) or 0) <= 45
        for m in members
    )
    maternity = waiting_periods.get("maternityWaiting") or waiting_periods.get("maternityCoverage", "")
    mat_str = str(maternity).lower() if maternity else ""
    has_maternity = any(kw in mat_str for kw in ["covered", "available", "yes"]) or "maternity" in category_str
    if is_floater and has_young_female and not has_maternity:
        g012_cost = max(3000, min(10000, int(sum_assured * 0.001)))
        gaps.append({
            "gapId": "G012", "severity": "medium",
            "title": "No Maternity Coverage",
            "impact": "Normal delivery \u20b91.25L, C-section \u20b92L \u2014 entirely out of pocket",
            "fix": "Add maternity benefit (usually 9-month waiting period)",
            "estimatedCost": g012_cost, "estimatedCostFormatted": f"+\u20b9{g012_cost:,}/yr",
            "eazrEmi": calculate_ipf_emi(g012_cost)
        })

    # Sort gaps by severity: high -> medium -> info (critical for top-3 display per spec Section C)
    _severity_order = {"high": 0, "medium": 1, "info": 2}
    gaps.sort(key=lambda g: _severity_order.get(g.get("severity", "info"), 2))

    # Summary counts
    high_count = sum(1 for g in gaps if g["severity"] == "high")
    medium_count = sum(1 for g in gaps if g["severity"] == "medium")
    info_count = sum(1 for g in gaps if g["severity"] == "info")

    return {
        "summary": {"high": high_count, "medium": medium_count, "info": info_count, "total": len(gaps)},
        "gaps": gaps
    }


def _select_primary_scenario(members: list, gaps_result: dict, health_scenarios: list) -> str:
    """
    Auto-select the most relevant scenario based on member ages and gaps per spec Section 2.5.
    Returns scenarioId string (e.g. 'H001').
    """
    ages = []
    for m in members:
        age = m.get("memberAge", 0) or 0
        if isinstance(age, (int, float)) and age > 0:
            ages.append(age)
    max_age = max(ages) if ages else 35

    has_young_female = any(
        str(m.get("memberGender", "")).lower() == "female" and 25 <= (m.get("memberAge", 0) or 0) <= 40
        for m in members
    )

    gap_ids = {g.get("gapId", "") for g in gaps_result.get("gaps", [])}

    # Priority rules per spec (first match wins)
    if max_age >= 55:
        return "H003"  # Knee Replacement — highest relevance for 55+
    if max_age >= 50:
        return "H001"  # Cardiac Emergency — high relevance for 50+
    if "G001" in gap_ids and max_age >= 40:
        return "H002"  # Cancer — to show SI inadequacy impact
    if has_young_female and "G012" in gap_ids:
        return "H004"  # Maternity — relevant gap

    # Default: scenario with highest out-of-pocket
    if health_scenarios:
        worst = max(health_scenarios, key=lambda s: s.get("costBreakdown", {}).get("outOfPocket", 0))
        return worst.get("scenarioId", "H001")

    return "H001"  # Cardiac — universally relevant


def _build_health_recommendations(gaps_result: dict, category_data: dict, sum_assured: int) -> dict:
    """
    Build recommendations from gap analysis per spec Section 2.6.
    Returns: {"quickWins": [...], "priorityUpgrades": [...], "totalUpgradeCost": {...}}
    """
    import re as _re
    from services.protection_score_calculator import calculate_ipf_emi

    quick_wins = []
    priority_upgrades = []

    # Quick Win 1: NCB awareness
    ncb_data = category_data.get("noClaimBonus", {}) or {}
    ncb_available = ncb_data.get("available", False)
    if isinstance(ncb_available, str):
        ncb_available = ncb_available.lower() in ["yes", "true"]
    ncb_pct = ncb_data.get("currentNcbPercentage") or ncb_data.get("accumulatedNcbPercentage") or ""
    ncb_amt = ncb_data.get("ncbAmount") or 0
    try:
        ncb_amt = float(str(ncb_amt).replace(",", "").replace("\u20b9", "")) if ncb_amt else 0
    except (ValueError, TypeError):
        ncb_amt = 0

    if ncb_available and (ncb_pct or ncb_amt > 0):
        effective_si = sum_assured + ncb_amt
        quick_wins.append({
            "title": "Your Effective Coverage is Higher!",
            "description": f"With {ncb_pct or 'accumulated'} NCB, effective SI is \u20b9{effective_si:,.0f} (not just \u20b9{sum_assured:,.0f})",
            "action": "No action needed \u2014 just be aware during claims"
        })

    # Quick Win 2: PED waiting progress — skip if waived via add-ons or portability continuity
    waiting_periods = category_data.get("waitingPeriods", {}) or {}
    policy_history = category_data.get("policyHistory", {}) or {}
    ped_waiting = waiting_periods.get("preExistingDiseaseWaiting", "")
    first_enrollment = policy_history.get("firstEnrollmentDate") or policy_history.get("insuredSinceDate")

    # Check if PED waiting is waived (add-on or portability continuity)
    from services.protection_score_calculator import _detect_waiting_waivers
    _qw_waivers = _detect_waiting_waivers(category_data)
    _ped_waived_qw = _qw_waivers["ped"]

    # Also check explicit "no waiting"/"waived" in the PED field itself
    _ped_str_qw = str(ped_waiting).lower() if ped_waiting else ""
    if any(kw in _ped_str_qw for kw in ["no waiting", "waived", "nil", "0 year", "0 month", "day 1", "reduced to 0"]):
        _ped_waived_qw = True

    if not _ped_waived_qw and first_enrollment and ped_waiting:
        from datetime import datetime as _dt
        from services.protection_score_calculator import _parse_indian_date
        try:
            enrollment_date = _parse_indian_date(str(first_enrollment))
            if enrollment_date:
                months_since = (_dt.now() - enrollment_date).days // 30
                ped_months = 48
                m = _re.search(r'(\d+)', str(ped_waiting))
                if m:
                    ped_months = int(m.group(1))
                pct_complete = min(100, round(months_since / max(ped_months, 1) * 100))
                if pct_complete >= 100:
                    quick_wins.append({
                        "title": "Pre-existing Disease Waiting Completed!",
                        "description": f"All {ped_months} months served. Your PED conditions are now fully covered.",
                        "action": "No action needed \u2014 maintain continuous coverage"
                    })
                elif 0 < pct_complete < 100:
                    quick_wins.append({
                        "title": f"Pre-existing Disease Waiting {pct_complete}% Complete",
                        "description": f"{months_since} of {ped_months} months completed. Maintain continuous coverage.",
                        "action": "Do not let policy lapse \u2014 waiting period resets on break"
                    })
        except Exception:
            pass
    elif _ped_waived_qw:
        quick_wins.append({
            "title": "No PED Waiting Period!",
            "description": _qw_waivers["reason"] if _qw_waivers["reason"] else "All waiting periods waived \u2014 PED conditions covered from day one.",
            "action": "No action needed \u2014 your pre-existing conditions are fully covered"
        })

    # Priority Upgrades from actionable gaps (sorted by severity)
    gap_list = gaps_result.get("gaps", [])
    severity_order = {"high": 0, "medium": 1, "info": 2}
    actionable_gaps = [g for g in gap_list if g.get("estimatedCost", 0) > 0]
    actionable_gaps.sort(key=lambda g: severity_order.get(g.get("severity", "info"), 2))

    priority = 1
    for gap in actionable_gaps:
        severity = gap.get("severity", "medium")
        priority_label = "HIGH" if severity == "high" else ("MEDIUM" if severity == "medium" else "LOW")
        gap_id = gap.get("gapId", "")

        # Category per gap type
        if gap_id in ["G002", "G003", "G004", "G008"]:
            category = "Enhancement"
        elif gap_id in ["G001", "G011"]:
            category = "Gap Fill"
        elif gap_id in ["G012"]:
            category = "Enhancement"
        else:
            category = "Optimization"

        # When to action
        if gap_id == "G011":
            when = "Can purchase immediately (separate policy)"
        elif gap_id == "G012":
            when = "Add at renewal (9-month waiting applies)"
        else:
            when = "Request at next renewal"

        annual_cost = gap.get("estimatedCost", 0)
        emi = gap.get("eazrEmi", 0)
        priority_upgrades.append({
            "id": f"REC_{gap_id}",
            "priority": priority,
            "priorityLabel": priority_label,
            "title": gap.get("fix", gap.get("title", "")),
            "gapMapping": [gap_id],
            "estimatedCost": annual_cost,
            "estimatedCostFormatted": gap.get("estimatedCostFormatted", ""),
            "eazrEmi": emi,
            "eazrEmiFormatted": f"\u20b9{emi:,}/mo" if emi > 0 else "",
            "impact": gap.get("impact", ""),
            "when": when,
            "category": category
        })
        priority += 1

    # Total upgrade cost
    total_annual = sum(u.get("estimatedCost", 0) for u in priority_upgrades)
    total_monthly_emi = calculate_ipf_emi(total_annual) if total_annual > 0 else 0

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
