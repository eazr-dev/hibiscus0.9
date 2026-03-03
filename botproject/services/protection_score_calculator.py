"""
Protection Score Calculator
Calculates accurate protection scores for different insurance policy types
Based on EAZR Production Templates V1.0
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from policy_analysis.utils import lookup_csr as _lookup_csr

logger = logging.getLogger(__name__)


def calculate_protection_score(
    policy_type: str,
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_specific_data: Dict[str, Any]
) -> Tuple[int, str]:
    """
    Calculate protection score based on policy type and analysis

    Args:
        policy_type: Type of insurance (health, life, motor, travel, etc.)
        gaps: List of coverage gaps identified
        extracted_data: General policy data
        category_specific_data: Policy-type-specific data

    Returns:
        Tuple of (protection_score: int, protection_label: str)
    """
    policy_type_lower = policy_type.lower()

    # Route to specific calculator based on policy type
    if policy_type_lower in ["health", "medical", "mediclaim"]:
        return calculate_health_protection_score(gaps, extracted_data, category_specific_data)
    elif policy_type_lower in ["life", "term", "endowment", "ulip", "whole life"]:
        return calculate_life_protection_score(gaps, extracted_data, category_specific_data)
    elif policy_type_lower in ["motor", "car", "vehicle", "bike", "two-wheeler", "four-wheeler", "auto"]:
        return calculate_motor_protection_score(gaps, extracted_data, category_specific_data)
    elif policy_type_lower in ["travel", "overseas", "international"]:
        return calculate_travel_protection_score(gaps, extracted_data, category_specific_data)
    else:
        # Generic fallback for other policy types
        return calculate_generic_protection_score(gaps, extracted_data)


# ==================== HEALTH INSURANCE 4-SCORE SYSTEM (V10.0) ====================
# Based on EAZR_01_Health_Insurance_PolicyAnalysisTab.md specification
# S1: Emergency Hospitalization Readiness (30%/35%)
# S2: Critical Illness Preparedness (25%/30%)
# S3: Family Protection (25%, floater only)
# S4: Coverage Stability (20%/35%)

# Verdict map per spec
HEALTH_VERDICT_MAP = {
    (90, 100): {"label": "Excellent Protection", "summary": "Your policy is comprehensive. Minor optimizations possible.", "color": "#22C55E", "emoji": "shield"},
    (75, 89): {"label": "Strong Protection", "summary": "Solid coverage. A few targeted upgrades can make it even better.", "color": "#84CC16", "emoji": "shield"},
    (60, 74): {"label": "Adequate Protection", "summary": "Your policy covers most basics but has notable gaps in high-cost scenarios.", "color": "#EAB308", "emoji": "warning"},
    (40, 59): {"label": "Moderate Protection", "summary": "Significant gaps exist. Action recommended before your next hospitalization.", "color": "#F97316", "emoji": "warning"},
    (0, 39): {"label": "Needs Attention", "summary": "Critical coverage gaps found. Review recommended actions urgently.", "color": "#6B7280", "emoji": "alert"},
}

# CSR Lookup — centralized in policy_analysis/utils.py (single source of truth)
# Imported as _lookup_csr at top of file


def _find_value(data: dict, keys: list, default=None):
    """Search for value using multiple possible keys in nested dict"""
    if not data:
        return default
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
        for v in data.values():
            if isinstance(v, dict) and key in v and v[key] is not None:
                return v[key]
    return default


def _get_score_label(score: int) -> str:
    """Get score label based on value"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Strong"
    elif score >= 60:
        return "Adequate"
    elif score >= 40:
        return "Moderate"
    else:
        return "Weak"


def _parse_number_from_string(text: str) -> int:
    """Extract first number from a string like '14,000+ Hospitals' -> 14000"""
    import re
    if not text:
        return 0
    text = str(text).replace(",", "")
    match = re.search(r'(\d+)', text)
    return int(match.group(1)) if match else 0


def _get_copay_percentage(copay_str: str) -> float:
    """Extract copay percentage from string like '10%' -> 10.0"""
    import re
    if not copay_str:
        return 0.0
    copay_str = str(copay_str).lower()
    if any(kw in copay_str for kw in ["no co", "0%", "nil", "none", "no copay"]):
        return 0.0
    match = re.search(r'(\d+(?:\.\d+)?)\s*%', copay_str)
    return float(match.group(1)) if match else 0.0


# _lookup_csr imported from policy_analysis.utils (centralized CSR data)


def _parse_indian_date(date_str: str):
    """Parse dates in common Indian insurance formats. Returns datetime or None."""
    from datetime import datetime
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%d",   # 2014-06-20
        "%d-%m-%Y",   # 20-06-2014
        "%d/%m/%Y",   # 20/06/2014
        "%d-%b-%Y",   # 20-Jun-2014
        "%d %b %Y",   # 20 Jun 2014
        "%d %B %Y",   # 20 June 2014
        "%B %d, %Y",  # June 20, 2014
        "%b %d, %Y",  # Jun 20, 2014
        "%d-%b-%y",   # 20-Jun-14
        "%Y/%m/%d",   # 2014/06/20
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str[:20].strip(), fmt)
        except (ValueError, TypeError):
            continue
    # Last resort: extract any 4-digit year
    import re
    year_match = re.search(r'(19|20)\d{2}', date_str)
    if year_match:
        try:
            return datetime(int(year_match.group()), 1, 1)
        except Exception:
            pass
    return None


def _detect_waiting_waivers(category_data: dict) -> dict:
    """
    Detect if waiting periods are waived via paid add-on policies OR portability continuity benefit.
    Returns dict: {"initial": bool, "ped": bool, "specific": bool, "reason": str}
    Checks: addOnPolicies list, premiumBreakdown.addOnPremiums.otherAddOns,
            portability continuity benefit, and explicit "reduced to 0" in policy text.
    """
    import re as _re_ww
    result = {"initial": False, "ped": False, "specific": False, "reason": ""}

    # Source 1: addOnPolicies.addOnPoliciesList
    add_on_policies = category_data.get("addOnPolicies", {}) or {}
    add_on_list = add_on_policies.get("addOnPoliciesList", []) or []
    for addon in add_on_list:
        if not isinstance(addon, dict):
            continue
        name = str(addon.get("addOnName", "")).lower()
        if "initial" in name and "waiting" in name and ("waiver" in name or "reduction" in name or "waive" in name):
            result["initial"] = True
        if ("ped" in name or "pre-existing" in name or "pre existing" in name) and ("waiver" in name or "reduction" in name or "waive" in name):
            result["ped"] = True
        if "specific" in name and ("illness" in name or "disease" in name) and ("waiver" in name or "reduction" in name or "waive" in name):
            result["specific"] = True
        # Generic "waiting period waiver" covers all
        if "waiting period waiver" in name and "initial" not in name and "specific" not in name:
            result["initial"] = True
            result["ped"] = True
            result["specific"] = True

    # Source 2: premiumBreakdown.addOnPremiums.otherAddOns (keyed by add-on name with premium values)
    premium_breakdown = category_data.get("premiumBreakdown", {}) or {}
    add_on_premiums = premium_breakdown.get("addOnPremiums", {}) or {}
    other_add_ons = add_on_premiums.get("otherAddOns", {}) if isinstance(add_on_premiums, dict) else {}
    for addon_name, premium_val in other_add_ons.items():
        name_lower = str(addon_name).lower()
        try:
            prem = float(premium_val) if premium_val else 0
        except (ValueError, TypeError):
            prem = 0
        if prem <= 0:
            continue  # Only count if premium was actually paid
        if "initial" in name_lower and "waiting" in name_lower:
            result["initial"] = True
        if ("ped" in name_lower or "pre-existing" in name_lower or "pre existing" in name_lower) and "waiting" in name_lower:
            result["ped"] = True
        if "specific" in name_lower and ("illness" in name_lower or "disease" in name_lower):
            result["specific"] = True
        if "waiting period waiver" in name_lower and "initial" not in name_lower and "specific" not in name_lower:
            result["initial"] = True
            result["ped"] = True
            result["specific"] = True

    # Source 3: Portability continuity benefit — ported policies often have waiting periods reduced to 0
    policy_history = category_data.get("policyHistory", {}) or {}
    portability = policy_history.get("portability", {}) or {}
    ported_from = ""
    is_ported = False
    if isinstance(portability, dict):
        is_ported = bool(portability.get("portedFrom") or portability.get("previousInsurer") or portability.get("ported"))
        ported_from = str(portability.get("portedFrom") or portability.get("previousInsurer") or "")
    elif isinstance(portability, str):
        port_lower = portability.lower()
        is_ported = port_lower not in ["no", "false", "not applicable", "na", "n/a", ""]
        if is_ported:
            ported_from = portability

    # Check continuousCoverageYears — if ported with long coverage, waiting periods are likely served/waived
    cont_years = policy_history.get("continuousCoverageYears")
    years_covered = 0
    if cont_years:
        try:
            years_covered = float(str(cont_years).replace("+", "").replace("years", "").strip())
        except (ValueError, TypeError):
            pass
    # Also calculate from firstEnrollmentDate
    if years_covered <= 0:
        first_enrollment = (policy_history.get("firstEnrollmentDate") or
                           policy_history.get("insuredSinceDate") or
                           policy_history.get("firstPolicyDate") or "")
        if first_enrollment:
            enrollment_dt = _parse_indian_date(str(first_enrollment))
            if enrollment_dt:
                from datetime import datetime
                years_covered = (datetime.now() - enrollment_dt).days / 365.25

    # If ported with sufficient continuous coverage, PED and specific waiting are served
    if is_ported and years_covered >= 4:
        if not result["ped"]:
            result["ped"] = True
        if not result["specific"]:
            result["specific"] = True

    # Source 4: Check explicit "reduced to 0" / "waived" / "no waiting" in waiting period fields
    waiting_periods = category_data.get("waitingPeriods", {}) or {}
    for field_key, flag_key in [
        ("preExistingDiseaseWaiting", "ped"),
        ("pedWaiting", "ped"),
        ("specificDiseaseWaiting", "specific"),
        ("specificIllnessWaiting", "specific"),
        ("initialWaitingPeriod", "initial"),
    ]:
        val = str(waiting_periods.get(field_key, "")).lower()
        if any(kw in val for kw in ["no waiting", "waived", "nil", "0 year", "0 month", "0 day", "day 1", "reduced to 0"]):
            result[flag_key] = True

    # Source 5: Check category text for explicit continuity/portability benefit reducing waiting
    category_str = str(category_data).lower()
    if _re_ww.search(r'(?:ped|pre.?existing).*?(?:reduced|waived).*?0', category_str):
        result["ped"] = True
    if _re_ww.search(r'(?:specific|named)\s*(?:illness|ailment|disease).*?(?:reduced|waived).*?0', category_str):
        result["specific"] = True
    if "continuity benefit" in category_str and ("0 year" in category_str or "reduced to 0" in category_str):
        result["ped"] = True
        result["specific"] = True

    reasons = []
    if result["initial"]:
        reasons.append("Initial waiting waived")
    if result["ped"]:
        if is_ported and years_covered >= 4:
            reasons.append(f"PED waiting served/waived (ported, {years_covered:.0f}yr continuous coverage)")
        else:
            reasons.append("PED waiting waived (paid add-on)")
    if result["specific"]:
        if is_ported and years_covered >= 4:
            reasons.append(f"Specific illness waiting served/waived (ported, {years_covered:.0f}yr continuous coverage)")
        else:
            reasons.append("Specific illness waiting waived (paid add-on)")
    result["reason"] = "; ".join(reasons)

    return result


def _lookup_network_hospital_count(insurer_name: str) -> int:
    """
    Look up network hospital count from insurer database as fallback
    when policy document doesn't specify the count.
    Returns hospital count or 0 if not found.
    """
    import re
    try:
        from services.insurance_provider_info import get_insurance_provider_info
        provider = get_insurance_provider_info(insurer_name)
        if provider:
            network_size = provider.get("networkSize", "")
            if network_size and network_size != "N/A":
                # Extract hospital count from strings like "14,300+ Network Hospitals, 6,500+ Garages"
                hospital_match = re.search(r'([\d,]+)\+?\s*(?:Network\s*)?Hospital', str(network_size), re.IGNORECASE)
                if hospital_match:
                    return int(hospital_match.group(1).replace(",", ""))
    except Exception:
        pass
    return 0


def calculate_ipf_emi(principal: float, annual_rate: float = 12.0, tenure_months: int = 12) -> int:
    """
    Full IPF (Insurance Premium Financing) EMI calculation.
    Uses standard reducing balance EMI formula: P * r * (1+r)^n / ((1+r)^n - 1)

    Args:
        principal: Total annual cost to finance
        annual_rate: Annual interest rate (default 12%)
        tenure_months: Loan tenure in months (default 12)

    Returns:
        Monthly EMI amount (rounded to nearest integer)
    """
    if principal <= 0:
        return 0
    if annual_rate <= 0 or tenure_months <= 0:
        return round(principal / max(tenure_months, 1))
    r = annual_rate / (12 * 100)  # Monthly interest rate
    n = tenure_months
    emi = principal * r * (1 + r) ** n / ((1 + r) ** n - 1)
    return round(emi)


def calculate_s1_emergency_readiness(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    S1: Emergency Hospitalization Readiness (100 points)

    Factors:
    - Sum Insured Adequacy: 25 pts
    - Room Rent Adequacy: 20 pts
    - ICU Coverage: 15 pts
    - Network Strength: 15 pts
    - Cashless TAT: 10 pts
    - Restoration Benefit: 10 pts
    - Co-payment Level: 5 pts
    """
    factors = []
    total_score = 0
    category_str = str(category_data).lower()
    coverage_details = category_data.get("coverageDetails", {}) or {}
    network_info = category_data.get("networkInfo", {}) or {}
    copay_details = category_data.get("copayDetails", {}) or {}

    # --- Factor 1: Sum Insured Adequacy (25 pts) ---
    si = extracted_data.get("coverageAmount", 0) or coverage_details.get("sumInsured", 0) or 0
    if si >= 25000000:
        pts = 25
    elif si >= 15000000:
        pts = 23
    elif si >= 10000000:
        pts = 21
    elif si >= 5000000:
        pts = 17
    elif si >= 2500000:
        pts = 12
    elif si >= 1000000:
        pts = 8
    elif si >= 500000:
        pts = 5
    else:
        pts = 2

    si_formatted = f"₹{si / 100000:.0f}L" if si >= 100000 else f"₹{si:,.0f}"
    factors.append({"name": "Sum Insured Adequacy", "yourPolicy": si_formatted, "benchmark": "₹15L+ metro family", "pointsEarned": pts, "pointsMax": 25})
    total_score += pts

    # --- Factor 2: Room Rent Adequacy (20 pts) ---
    room_rent = _find_value(coverage_details, ["roomRentLimit", "roomRent", "roomRentCapping"], "")
    room_rent_str = str(room_rent).lower() if room_rent else ""
    if any(kw in room_rent_str for kw in ["no limit", "no sub", "no cap", "unlimited"]) or "no limit" in category_str:
        pts = 20
        room_display = "No Limit"
    elif "single private" in room_rent_str or "single room" in room_rent_str:
        pts = 16
        room_display = "Single Private Room"
    elif "2%" in room_rent_str:
        pts = 12
        room_display = "2% of SI"
    elif "1%" in room_rent_str:
        pts = 8
        room_display = "1% of SI"
    elif room_rent_str and room_rent_str not in ["", "none", "null"]:
        pts = 6
        room_display = str(room_rent)
    else:
        pts = 10  # Unknown, assume moderate
        room_display = "Not specified"
    factors.append({"name": "Room Rent Adequacy", "yourPolicy": room_display, "benchmark": "No Limit", "pointsEarned": pts, "pointsMax": 20})
    total_score += pts

    # --- Factor 3: ICU Coverage (15 pts) ---
    icu_limit = _find_value(coverage_details, ["icuLimit", "icuDailyLimit", "icuCharges"], "")
    icu_str = str(icu_limit).lower() if icu_limit else ""
    if any(kw in icu_str for kw in ["no limit", "unlimited", "no cap", "no sub"]) or ("icu" in category_str and "no limit" in category_str):
        pts = 15
        icu_display = "No Limit"
    elif icu_str and icu_str not in ["", "none", "null"]:
        pts = 8
        icu_display = str(icu_limit)
    else:
        pts = 10  # Not specified, assume moderate
        icu_display = "Not specified"
    factors.append({"name": "ICU Coverage", "yourPolicy": icu_display, "benchmark": "No Limit", "pointsEarned": pts, "pointsMax": 15})
    total_score += pts

    # --- Factor 4: Network Strength (15 pts) ---
    hospital_count_str = _find_value(network_info, ["networkHospitalsCount", "totalHospitals", "networkHospitals"], "")
    hospital_count = _parse_number_from_string(str(hospital_count_str))
    cashless = network_info.get("cashlessFacility", False)
    # Fallback: look up from insurer database when policy document doesn't specify
    _s1_insurer = (category_data.get("policyIdentification", {}) or {}).get("insuranceProvider", "") or ""
    if hospital_count == 0 and _s1_insurer:
        hospital_count = _lookup_network_hospital_count(_s1_insurer)
        if hospital_count > 0:
            hospital_count_str = f"{hospital_count:,}+ (insurer network)"
    if hospital_count >= 10000:
        pts = 15
    elif hospital_count >= 5000:
        pts = 13
    elif hospital_count >= 2000:
        pts = 11
    elif hospital_count >= 500:
        pts = 8
    elif hospital_count > 0:
        pts = 5
    else:
        pts = 7 if cashless or "cashless" in category_str else 4
    hospital_display = str(hospital_count_str) if hospital_count_str else "Not specified"
    factors.append({"name": "Network Strength", "yourPolicy": hospital_display, "benchmark": "10,000+ hospitals", "pointsEarned": pts, "pointsMax": 15})
    total_score += pts

    # --- Factor 5: Cashless TAT (10 pts) ---
    pre_auth = _find_value(network_info, ["preAuthTurnaround", "cashlessTAT"], "")
    pre_auth_str = str(pre_auth).lower() if pre_auth else ""
    if "30 min" in pre_auth_str or "instant" in pre_auth_str:
        pts = 10
    elif "1 hour" in pre_auth_str or "60 min" in pre_auth_str:
        pts = 9
    elif "2 hour" in pre_auth_str:
        pts = 7
    elif "4 hour" in pre_auth_str or "4-6 hour" in pre_auth_str:
        pts = 5
    elif pre_auth_str:
        pts = 6
    else:
        pts = 6  # Default moderate if not specified
    factors.append({"name": "Cashless Processing", "yourPolicy": str(pre_auth) if pre_auth else "Standard", "benchmark": "≤1 hour", "pointsEarned": pts, "pointsMax": 10})
    total_score += pts

    # --- Factor 6: Restoration Benefit (10 pts) ---
    restoration = _find_value(coverage_details, ["restoration", "restorationAmount"], {})
    restoration_str = str(restoration).lower() if restoration else ""
    if "unlimited" in restoration_str:
        pts = 10
    elif isinstance(restoration, dict) and restoration.get("available"):
        restoration_type = str(restoration.get("type", "")).lower()
        if "unlimited" in restoration_type:
            pts = 10
        elif "100%" in restoration_type or "full" in restoration_type:
            pts = 8
        else:
            pts = 7
    elif "restoration" in category_str or "recharge" in category_str:
        pts = 7
    else:
        pts = 0
    restoration_display = "Unlimited" if pts == 10 else ("Available" if pts >= 7 else "Not Available")
    if isinstance(restoration, dict) and restoration.get("type"):
        restoration_display = str(restoration["type"])
    factors.append({"name": "Restoration Benefit", "yourPolicy": restoration_display, "benchmark": "Unlimited", "pointsEarned": pts, "pointsMax": 10})
    total_score += pts

    # --- Factor 7: Co-payment Level (5 pts) ---
    general_copay = _find_value(copay_details, ["generalCopay", "copay", "coPayment"], "")
    copay_pct = _get_copay_percentage(str(general_copay))
    if copay_pct <= 0:
        pts = 5
    elif copay_pct <= 10:
        pts = 3
    elif copay_pct <= 20:
        pts = 1
    else:
        pts = 0
    copay_display = f"{copay_pct:.0f}%" if copay_pct > 0 else "0%"
    factors.append({"name": "Co-payment Level", "yourPolicy": copay_display, "benchmark": "0%", "pointsEarned": pts, "pointsMax": 5})
    total_score += pts

    total_score = max(0, min(100, total_score))
    label = _get_score_label(total_score)

    return {
        "score": total_score,
        "label": label,
        "name": "Emergency Readiness",
        "icon": "hospital",
        "factors": factors
    }


def calculate_s2_critical_illness(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    S2: Critical Illness Preparedness (100 points)

    Factors:
    - Modern Treatment Coverage: 25 pts
    - CI Rider / Critical Illness Coverage: 20 pts
    - Waiting Periods (critical conditions): 20 pts
    - Sub-limits on Major Procedures: 20 pts
    - Consumables Coverage: 15 pts
    """
    factors = []
    total_score = 0
    category_str = str(category_data).lower()
    coverage_details = category_data.get("coverageDetails", {}) or {}
    waiting_periods = category_data.get("waitingPeriods", {}) or {}
    sub_limits = category_data.get("subLimits", {}) or {}

    # --- Factor 1: Modern Treatment Coverage (25 pts) ---
    modern = _find_value(coverage_details, ["modernTreatment", "modernTreatmentCoverage", "modernTreatmentMethods"], "")
    modern_str = str(modern).lower() if modern else ""
    # Also check add-on policies for modern treatment coverage
    add_on_policies = category_data.get("addOnPolicies", {}) or {}
    add_on_list = add_on_policies.get("addOnPoliciesList", []) or []
    has_modern_addon = any(
        any(kw in str(a.get("addOnName", "")).lower() for kw in ["modern", "advanced"])
        for a in add_on_list if isinstance(a, dict)
    )
    if (any(kw in modern_str for kw in ["up to si", "up to sum", "covered", "yes", "full", "available", "included", "as per si"])
            or "modern treatment" in category_str
            or "advanced technology" in category_str
            or "advanced treatment" in category_str
            or "robotic" in category_str
            or has_modern_addon):
        pts = 25
        modern_display = str(modern) if modern else "Covered"
    elif modern_str and modern_str not in ["", "no", "not covered", "none", "null", "not available"]:
        pts = 15
        modern_display = str(modern)
    else:
        pts = 0
        modern_display = "Not Covered"
    factors.append({"name": "Modern Treatment Coverage", "yourPolicy": modern_display, "benchmark": "Up to SI", "pointsEarned": pts, "pointsMax": 25})
    total_score += pts

    # --- Factor 2: CI Rider / Critical Illness (20 pts) ---
    has_ci = any(kw in category_str for kw in ["critical illness", "ci rider", "ci cover", "cancer cover"])
    if has_ci:
        pts = 20
        ci_display = "Available"
    else:
        # Even without explicit CI rider, high SI covers critical illness costs
        si = extracted_data.get("coverageAmount", 0) or coverage_details.get("sumInsured", 0) or 0
        if si >= 10000000:
            pts = 15  # High SI compensates somewhat
            ci_display = f"No dedicated rider (SI: ₹{si / 100000:.0f}L covers most)"
        elif si >= 5000000:
            pts = 10
            ci_display = f"No dedicated rider (SI: ₹{si / 100000:.0f}L partial)"
        else:
            pts = 3
            ci_display = "Not Available"
    factors.append({"name": "Critical Illness Coverage", "yourPolicy": ci_display, "benchmark": "Dedicated CI Rider", "pointsEarned": pts, "pointsMax": 20})
    total_score += pts

    # --- Factor 3: Waiting Periods for Critical Conditions (20 pts) ---
    ped_waiting = _find_value(waiting_periods, ["preExistingDiseaseWaiting", "pedWaiting", "preExistingWaiting"], "")
    specific_waiting = _find_value(waiting_periods, ["specificDiseaseWaiting", "specificIllnessWaiting"], "")
    ped_str = str(ped_waiting).lower() if ped_waiting else ""
    specific_str = str(specific_waiting).lower() if specific_waiting else ""

    # Check if waiting periods are waived via add-ons or portability continuity benefit
    waiting_waivers = _detect_waiting_waivers(category_data)
    ped_waived = waiting_waivers["ped"]
    specific_waived = waiting_waivers["specific"]

    # Also check if PED waiting period is already completed by time served
    declared_ped = category_data.get("declaredPed", {}) or {}
    policy_history_s2 = category_data.get("policyHistory", {}) or {}
    ped_completed = bool(declared_ped.get("pedWaitingPeriodCompleted"))

    if not ped_completed and not ped_waived:
        first_enrollment_s2 = _find_value(policy_history_s2, ["firstEnrollmentDate", "insuredSinceDate", "firstPolicyDate"], "")
        if first_enrollment_s2:
            enrollment_dt = _parse_indian_date(str(first_enrollment_s2))
            if enrollment_dt:
                from datetime import datetime
                years_insured_s2 = (datetime.now() - enrollment_dt).days / 365.25
                import re as _re_s2
                wait_match = _re_s2.search(r'(\d+)\s*(?:month|year)', ped_str)
                if wait_match:
                    wait_months = int(wait_match.group(1))
                    if "year" in ped_str[wait_match.start():wait_match.end() + 5]:
                        wait_months *= 12
                    if years_insured_s2 * 12 >= wait_months:
                        ped_completed = True
        cont_yrs_s2 = policy_history_s2.get("continuousCoverageYears")
        if not ped_completed and cont_yrs_s2:
            try:
                cy = float(str(cont_yrs_s2).replace("+", "").strip())
                if cy >= 4:
                    ped_completed = True
            except (ValueError, TypeError):
                pass

    # PED waiting (12 pts)
    if ped_waived or ped_completed or any(kw in ped_str for kw in ["no waiting", "waived", "nil", "0", "covered", "day 1"]):
        ped_pts = 12
    elif "12 month" in ped_str or "1 year" in ped_str:
        ped_pts = 10
    elif "24 month" in ped_str or "2 year" in ped_str:
        ped_pts = 7
    elif "36 month" in ped_str or "3 year" in ped_str:
        ped_pts = 4
    elif "48 month" in ped_str or "4 year" in ped_str:
        ped_pts = 2
    else:
        ped_pts = 5  # Default moderate

    # Specific disease waiting (8 pts)
    if specific_waived or any(kw in specific_str for kw in ["no waiting", "waived", "nil", "0", "covered", "day 1"]):
        specific_pts = 8
    elif "12 month" in specific_str or "1 year" in specific_str:
        specific_pts = 6
    elif "24 month" in specific_str or "2 year" in specific_str:
        specific_pts = 4
    else:
        specific_pts = 4  # Default moderate

    pts = ped_pts + specific_pts
    if ped_waived:
        ped_display = f"No Waiting Period (Waived)" if not waiting_waivers["reason"] else f"Waived — {waiting_waivers['reason'].split(';')[0]}"
    elif ped_completed:
        ped_display = f"{ped_waiting} (Completed)" if ped_waiting else "Completed"
    else:
        ped_display = str(ped_waiting) if ped_waiting else "Standard (48 months)"
    factors.append({"name": "Waiting Periods (Critical)", "yourPolicy": ped_display, "benchmark": "No waiting / Waived", "pointsEarned": pts, "pointsMax": 20})
    total_score += pts

    # --- Factor 4: Sub-limits on Major Procedures (20 pts) ---
    sub_limit_items = []
    for key in ["cataractLimit", "jointReplacementLimit", "internalProsthesisLimit", "kidneyStoneLimit", "gallStoneLimit"]:
        val = sub_limits.get(key)
        if val and str(val).lower() not in ["", "none", "null", "no limit", "up to sum insured", "up to si"]:
            sub_limit_items.append(key)

    # Also check otherSubLimits
    other_subs = sub_limits.get("otherSubLimits", [])
    if isinstance(other_subs, list):
        sub_limit_items.extend(other_subs)

    modern_limit = sub_limits.get("modernTreatmentLimit", "")
    modern_limit_str = str(modern_limit).lower() if modern_limit else ""
    has_modern_sub = modern_limit_str and modern_limit_str not in ["up to sum insured", "up to si", "no limit", "unlimited", ""]

    num_sub_limits = len(sub_limit_items) + (1 if has_modern_sub else 0)
    if num_sub_limits == 0:
        pts = 20
        sub_display = "No Sub-limits"
    elif num_sub_limits <= 2:
        pts = 14
        sub_display = f"{num_sub_limits} sub-limit(s)"
    elif num_sub_limits <= 4:
        pts = 8
        sub_display = f"{num_sub_limits} sub-limits"
    else:
        pts = 4
        sub_display = f"{num_sub_limits} sub-limits"
    factors.append({"name": "Sub-limits on Procedures", "yourPolicy": sub_display, "benchmark": "No Sub-limits", "pointsEarned": pts, "pointsMax": 20})
    total_score += pts

    # --- Factor 5: Consumables Coverage (15 pts) ---
    consumables = _find_value(coverage_details, ["consumablesCoverage", "consumables", "consumablesCovered"], "")
    consumables_str = str(consumables).lower() if consumables else ""
    # Check add-on policies (Care Shield, Claim Shield, Claim Shield Plus cover consumables)
    _addon_s2 = category_data.get("addOnPolicies", {}) or {}
    _addon_list_s2 = _addon_s2.get("addOnPoliciesList", []) or []
    _has_cons_addon = (
        bool(_addon_s2.get("claimShield"))
        or any(
            any(kw in str(a.get("addOnName", "")).lower() for kw in ["care shield", "claim shield", "consumable"])
            for a in _addon_list_s2 if isinstance(a, dict)
        )
    )
    # Also check premiumBreakdown.addOnPremiums.otherAddOns for paid consumable add-ons
    _pb_s2 = category_data.get("premiumBreakdown", {}) or {}
    _ap_s2 = _pb_s2.get("addOnPremiums", {}) or {}
    _oa_s2 = _ap_s2.get("otherAddOns", {}) if isinstance(_ap_s2, dict) else {}
    for _aon_s2, _apv_s2 in _oa_s2.items():
        _aon_lower = str(_aon_s2).lower()
        if any(kw in _aon_lower for kw in ["claim shield", "care shield", "consumable"]):
            try:
                if float(_apv_s2) > 0:
                    _has_cons_addon = True
            except (ValueError, TypeError):
                pass

    if _has_cons_addon:
        pts = 15
        cons_display = "Covered (Add-on)"
    elif consumables_str in ["true", "yes", "covered", "available", "included"] or consumables is True:
        # Explicit field from AI extraction — trust it but cross-validate
        # If add-on list exists but no consumable add-on, be cautious
        if _addon_list_s2 and not _has_cons_addon:
            # Add-ons exist but no consumable add-on: might be base plan coverage or AI error
            # Only trust if the explicit field is strongly positive
            if consumables_str in ["covered", "yes", "true"]:
                pts = 15
                cons_display = "Covered (Base Plan)"
            else:
                pts = 0
                cons_display = "Not Covered"
        else:
            pts = 15
            cons_display = "Covered"
    elif consumables_str and consumables_str not in ["", "no", "not covered", "none", "null", "not available", "false", "excluded"]:
        pts = 8
        cons_display = str(consumables)
    else:
        pts = 0
        cons_display = "Not Covered"
    factors.append({"name": "Consumables Coverage", "yourPolicy": cons_display, "benchmark": "Covered", "pointsEarned": pts, "pointsMax": 15})
    total_score += pts

    total_score = max(0, min(100, total_score))
    label = _get_score_label(total_score)

    return {
        "score": total_score,
        "label": label,
        "name": "Critical Illness",
        "icon": "ribbon",
        "factors": factors
    }


def calculate_s3_family_protection(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any]
) -> Any:
    """
    S3: Family Protection Score (100 points, FLOATER ONLY)
    Returns None for individual policies.

    Factors:
    - Member Count vs SI Ratio: 25 pts
    - Per-member Adequacy: 25 pts
    - Maternity Coverage: 20 pts
    - Child-specific Benefits: 15 pts
    - Coverage Continuity: 15 pts
    """
    # Detect if floater/family
    policy_id_data = category_data.get("policyIdentification", {}) or {}
    policy_type_str = str(policy_id_data.get("policyType", "")).lower()
    cover_type = str((category_data.get("coverageDetails", {}) or {}).get("coverType", "")).lower()

    is_floater = any(kw in policy_type_str for kw in ["floater", "family"]) or any(kw in cover_type for kw in ["floater", "family"])

    # Also check member count
    members = category_data.get("insuredMembers", []) or category_data.get("membersCovered", []) or []
    if not is_floater and len(members) <= 1:
        return None  # Individual policy

    # If multiple members exist but not explicitly labeled as floater, treat as floater
    if len(members) > 1:
        is_floater = True

    if not is_floater:
        return None

    factors = []
    total_score = 0
    category_str = str(category_data).lower()
    coverage_details = category_data.get("coverageDetails", {}) or {}
    waiting_periods = category_data.get("waitingPeriods", {}) or {}
    policy_history = category_data.get("policyHistory", {}) or {}
    benefits = category_data.get("benefits", {}) or {}

    si = extracted_data.get("coverageAmount", 0) or coverage_details.get("sumInsured", 0) or 0
    member_count = max(len(members), 1)

    # --- Factor 1: Member Count vs SI Ratio (25 pts) ---
    # Floater: each member can access full SI (shared limit, not divided)
    if is_floater:
        si_per_member = si
    else:
        si_per_member = si / member_count if member_count > 0 else si
    if si_per_member >= 5000000:
        pts = 25
    elif si_per_member >= 3000000:
        pts = 21
    elif si_per_member >= 2000000:
        pts = 17
    elif si_per_member >= 1000000:
        pts = 12
    elif si_per_member >= 500000:
        pts = 7
    else:
        pts = 3
    if is_floater:
        si_per_display = f"₹{si / 100000:.0f}L (floater - full SI per member)"
    else:
        si_per_display = f"₹{si_per_member / 100000:.0f}L per member ({member_count} members)"
    factors.append({"name": "SI per Member Ratio", "yourPolicy": si_per_display, "benchmark": "₹50L+ per member", "pointsEarned": pts, "pointsMax": 25})
    total_score += pts

    # --- Factor 2: Per-member Adequacy (25 pts) ---
    # Check ages and coverage adequacy
    ages = []
    for m in members:
        age = m.get("memberAge", 0)
        if isinstance(age, (int, float)) and age > 0:
            ages.append(age)
    max_age = max(ages) if ages else 30
    has_senior = max_age >= 60
    has_child = any(a < 18 for a in ages)

    # Recommended SI based on family composition
    if has_senior:
        recommended = 15000000 if member_count >= 3 else 10000000
    else:
        recommended = 10000000 if member_count >= 3 else 5000000

    ratio = si / recommended if recommended > 0 else 1
    if ratio >= 1.5:
        pts = 25
    elif ratio >= 1.0:
        pts = 21
    elif ratio >= 0.75:
        pts = 16
    elif ratio >= 0.5:
        pts = 10
    else:
        pts = 5
    factors.append({"name": "Per-member Adequacy", "yourPolicy": f"₹{si / 100000:.0f}L for {member_count}", "benchmark": f"₹{recommended / 100000:.0f}L recommended", "pointsEarned": pts, "pointsMax": 25})
    total_score += pts

    # --- Factor 3: Maternity Coverage (20 pts) ---
    maternity = _find_value(waiting_periods, ["maternityWaiting", "maternityCoverage", "maternity"], "")
    maternity_str = str(maternity).lower() if maternity else ""
    has_young_female = any(
        (m.get("memberGender") or "").lower() == "female" and 18 <= (m.get("memberAge") or 0) <= 45
        for m in members
    )
    if not has_young_female:
        pts = 15  # Not applicable, give moderate score
        mat_display = "N/A (no eligible members)"
    elif any(kw in maternity_str for kw in ["covered", "available", "yes"]) or "maternity" in category_str:
        if "no waiting" in maternity_str or "waived" in maternity_str:
            pts = 20
        elif "9 month" in maternity_str or "12 month" in maternity_str:
            pts = 16
        elif "24 month" in maternity_str or "2 year" in maternity_str:
            pts = 12
        else:
            pts = 14
        mat_display = str(maternity) if maternity else "Covered"
    else:
        pts = 0
        mat_display = "Not Covered"
    factors.append({"name": "Maternity Coverage", "yourPolicy": mat_display, "benchmark": "Covered with minimal waiting", "pointsEarned": pts, "pointsMax": 20})
    total_score += pts

    # --- Factor 4: Child-specific Benefits (15 pts) ---
    if has_child:
        child_pts = 0
        if "day care" in category_str or "daycare" in category_str:
            child_pts += 5
        if "vaccination" in category_str or "immunization" in category_str:
            child_pts += 5
        if "newborn" in category_str or "new born" in category_str:
            child_pts += 5
        pts = min(15, child_pts) if child_pts > 0 else 5  # Baseline for having child covered
        child_display = f"{child_pts} benefit(s) detected" if child_pts > 0 else "Basic child coverage"
    else:
        pts = 10  # No children, moderate score
        child_display = "N/A (no children)"
    factors.append({"name": "Child-specific Benefits", "yourPolicy": child_display, "benchmark": "Day care + Vaccination + Newborn", "pointsEarned": pts, "pointsMax": 15})
    total_score += pts

    # --- Factor 5: Coverage Continuity (15 pts) ---
    first_enrollment = _find_value(policy_history, ["firstEnrollmentDate", "insuredSinceDate", "firstPolicyDate"], "")
    continuous_years_raw = policy_history.get("continuousCoverageYears")
    years_covered = 0

    if first_enrollment:
        enrollment_date = _parse_indian_date(str(first_enrollment))
        if enrollment_date:
            from datetime import datetime
            years_covered = (datetime.now() - enrollment_date).days / 365.25

    # Fallback: use continuousCoverageYears if date parsing didn't work
    if years_covered <= 0 and continuous_years_raw:
        try:
            years_covered = float(str(continuous_years_raw).replace("+", "").strip())
        except (ValueError, TypeError):
            pass

    if years_covered >= 5:
        pts = 15
        cont_display = f"{years_covered:.0f} years continuous"
    elif years_covered >= 3:
        pts = 12
        cont_display = f"{years_covered:.0f} years continuous"
    elif years_covered >= 2:
        pts = 9
        cont_display = f"{years_covered:.0f} years continuous"
    elif years_covered >= 1:
        pts = 6
        cont_display = f"{years_covered:.0f} year continuous"
    elif first_enrollment:
        pts = 7
        cont_display = "Enrollment date available"
    else:
        pts = 5
        cont_display = "Not specified"
    factors.append({"name": "Coverage Continuity", "yourPolicy": cont_display, "benchmark": "5+ years continuous", "pointsEarned": pts, "pointsMax": 15})
    total_score += pts

    total_score = max(0, min(100, total_score))
    label = _get_score_label(total_score)

    return {
        "score": total_score,
        "label": label,
        "name": "Family Protection",
        "icon": "family",
        "factors": factors
    }


def calculate_s4_coverage_stability(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any],
    insurer_name: str = ""
) -> Dict[str, Any]:
    """
    S4: Coverage Stability (100 points)

    Factors:
    - Lifetime Renewability: 25 pts
    - Claim Settlement Ratio: 25 pts
    - NCB/Cumulative Bonus: 20 pts
    - Premium vs Coverage Value: 15 pts
    - Grace Period & Portability: 15 pts
    """
    factors = []
    total_score = 0
    category_str = str(category_data).lower()
    ncb_data = category_data.get("noClaimBonus", {}) or {}
    premium_data = category_data.get("premiumDetails", category_data.get("premiumBreakdown", {})) or {}
    policy_history = category_data.get("policyHistory", {}) or {}
    claim_info = category_data.get("claimInfo", {}) or {}
    coverage_details = category_data.get("coverageDetails", {}) or {}

    # --- Factor 1: Lifetime Renewability (25 pts) ---
    if "lifetime renew" in category_str or "lifelong renew" in category_str:
        pts = 25
        renew_display = "Lifetime Guaranteed"
    elif "renew" in category_str:
        pts = 18
        renew_display = "Renewable (check terms)"
    else:
        pts = 12  # Most IRDAI policies are renewable
        renew_display = "Standard IRDAI terms"
    factors.append({"name": "Lifetime Renewability", "yourPolicy": renew_display, "benchmark": "Lifetime Guaranteed", "pointsEarned": pts, "pointsMax": 25})
    total_score += pts

    # --- Factor 2: Claim Settlement Ratio (25 pts) ---
    csr = 0.0
    csr_from_data = _find_value(claim_info, ["claimSettlementRatio", "csr"], "")
    if csr_from_data:
        csr_str = str(csr_from_data).replace("%", "").strip()
        try:
            csr = float(csr_str)
        except (ValueError, TypeError):
            csr = 0.0
    if csr <= 0:
        csr = _lookup_csr(insurer_name)

    if csr >= 97:
        pts = 25
    elif csr >= 95:
        pts = 22
    elif csr >= 90:
        pts = 18
    elif csr >= 85:
        pts = 14
    elif csr >= 80:
        pts = 10
    elif csr > 0:
        pts = 6
    else:
        pts = 8  # Unknown CSR, moderate default
    csr_display = f"{csr:.1f}%" if csr > 0 else "Not available"
    factors.append({"name": "Claim Settlement Ratio", "yourPolicy": csr_display, "benchmark": "≥95%", "pointsEarned": pts, "pointsMax": 25})
    total_score += pts

    # --- Factor 3: NCB/Cumulative Bonus (20 pts) ---
    ncb_available = ncb_data.get("available", False)
    if isinstance(ncb_available, str):
        ncb_available = ncb_available.lower() in ["yes", "true"]
    # Prioritize max NCB for scoring (not current annual rate)
    ncb_max_pct = _find_value(ncb_data, ["maxNcbPercentage", "accumulatedNcbPercentage"], "")
    ncb_current = ncb_data.get("currentNcbPercentage", "")
    ncb_pct_str = str(ncb_max_pct).lower() if ncb_max_pct else str(ncb_current).lower() if ncb_current else ""

    import re
    # Extract ALL numbers and use the MAXIMUM (e.g., "10% per year, max 50%" → 50)
    ncb_numbers = re.findall(r'(\d+)', ncb_pct_str)
    ncb_value = max(int(n) for n in ncb_numbers) if ncb_numbers else 0

    if not ncb_available and ("no claim bonus" in category_str or "ncb" in category_str):
        ncb_available = True

    if ncb_available and ncb_value >= 50:
        pts = 20
    elif ncb_available and ncb_value >= 25:
        pts = 16
    elif ncb_available:
        pts = 12
    else:
        pts = 0
    if ncb_available and ncb_value > 0:
        ncb_display = f"Available (max {ncb_value}%)"
    elif ncb_available:
        ncb_display = "Available"
    else:
        ncb_display = "Not Available"
    factors.append({"name": "No Claim Bonus (NCB)", "yourPolicy": ncb_display, "benchmark": "50%+ NCB", "pointsEarned": pts, "pointsMax": 20})
    total_score += pts

    # --- Factor 4: Premium vs Coverage Value (15 pts) ---
    si = extracted_data.get("coverageAmount", 0) or coverage_details.get("sumInsured", 0) or 0
    total_premium = premium_data.get("totalPremium", 0) or extracted_data.get("premium", 0) or 0
    if si > 0 and total_premium > 0:
        # Premium ratio: lower is better value
        ratio = (total_premium / si) * 1000  # Premium per 1000 of SI
        if ratio <= 2:
            pts = 15
        elif ratio <= 4:
            pts = 13
        elif ratio <= 6:
            pts = 10
        elif ratio <= 10:
            pts = 7
        else:
            pts = 4
        ratio_display = f"₹{total_premium:,.0f} for ₹{si / 100000:.0f}L cover"
    else:
        pts = 8  # Unknown, moderate
        ratio_display = "Not available"
    factors.append({"name": "Premium Value", "yourPolicy": ratio_display, "benchmark": "≤₹4 per ₹1000 SI", "pointsEarned": pts, "pointsMax": 15})
    total_score += pts

    # --- Factor 5: Grace Period & Portability (15 pts) ---
    grace_period = _find_value(premium_data, ["gracePeriod", "grace"], "")
    grace_str = str(grace_period).lower() if grace_period else ""
    portability = _find_value(policy_history, ["portability"], {})

    # IRDAI mandates portability for ALL health insurance policies in India.
    # "Portability: No" means the policy was NOT ported FROM another insurer — NOT that
    # portability is unavailable. Always give full portability points for health insurance.
    port_available = True  # IRDAI-guaranteed right for all health policies
    port_display = "Available (IRDAI Mandated)"

    # Check if policy was actually ported (for display purposes)
    if isinstance(portability, dict):
        ported_from = portability.get("portedFrom") or portability.get("previousInsurer") or ""
        if ported_from:
            port_display = f"Ported from {ported_from}"
        elif portability.get("available") or portability.get("ported"):
            port_display = "Available"
    elif isinstance(portability, str):
        port_lower = portability.lower()
        # "No" means not ported, not that portability is unavailable
        if port_lower not in ["no", "false", "not applicable", "na", "n/a", ""]:
            port_display = f"Ported ({portability})"

    grace_pts = 0
    if "30 day" in grace_str or "30day" in grace_str:
        grace_pts = 8
    elif "15 day" in grace_str:
        grace_pts = 6
    elif grace_str:
        grace_pts = 5
    else:
        grace_pts = 5  # Standard IRDAI grace

    port_pts = 7  # Always full — IRDAI mandates portability
    pts = min(15, grace_pts + port_pts)

    grace_display = str(grace_period) if grace_period else "Standard"
    factors.append({"name": "Grace Period & Portability", "yourPolicy": f"Grace: {grace_display}, Port: {port_display}", "benchmark": "30 days grace + Portability", "pointsEarned": pts, "pointsMax": 15})
    total_score += pts

    total_score = max(0, min(100, total_score))
    label = _get_score_label(total_score)

    return {
        "score": total_score,
        "label": label,
        "name": "Stability",
        "icon": "shield",
        "factors": factors
    }


def calculate_health_composite_score(
    s1: Dict[str, Any],
    s2: Dict[str, Any],
    s3: Any,
    s4: Dict[str, Any]
) -> Tuple[int, str, Dict[str, Any]]:
    """
    Calculate composite score with proper weighting per spec.

    Floater: S1(30%) + S2(25%) + S3(25%) + S4(20%)
    Individual (S3=None): S1(35%) + S2(30%) + S4(35%)

    Returns:
        (composite_score, verdict_label, full_result_dict)
    """
    s1_score = s1.get("score", 0) if s1 else 0
    s2_score = s2.get("score", 0) if s2 else 0
    s4_score = s4.get("score", 0) if s4 else 0

    if s3 is not None:
        # Floater weights
        s3_score = s3.get("score", 0)
        composite = round(s1_score * 0.30 + s2_score * 0.25 + s3_score * 0.25 + s4_score * 0.20)
    else:
        # Individual weights (no S3)
        composite = round(s1_score * 0.35 + s2_score * 0.30 + s4_score * 0.35)

    composite = max(0, min(100, composite))

    # Find verdict from map
    verdict = {"label": "Needs Attention", "summary": "Critical coverage gaps found. Review recommended actions urgently.", "color": "#6B7280", "emoji": "alert"}
    for (low, high), v in HEALTH_VERDICT_MAP.items():
        if low <= composite <= high:
            verdict = v.copy()
            break

    result = {
        "compositeScore": composite,
        "verdict": verdict,
        "scores": {
            "s1": s1,
            "s2": s2,
            "s3": s3,
            "s4": s4
        }
    }

    return composite, verdict["label"], result


def calculate_health_scores_detailed(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any],
    insurer_name: str = ""
) -> Dict[str, Any]:
    """
    Public entry point: returns the full 4-score breakdown with factor details.
    Used by policyAnalyzer in policy_upload.py for the protectionReadiness section.

    Returns:
        {
            "compositeScore": 72,
            "verdict": {"label": "Adequate Protection", "summary": "...", "color": "#EAB308", "emoji": "warning"},
            "scores": {
                "s1": {"score": 78, "label": "Strong", "name": "Emergency Readiness", "icon": "hospital", "factors": [...]},
                "s2": {"score": 65, "label": "Adequate", ...},
                "s3": {"score": 68, ...} or None,
                "s4": {"score": 80, ...}
            }
        }
    """
    s1 = calculate_s1_emergency_readiness(gaps, extracted_data, category_data)
    s2 = calculate_s2_critical_illness(gaps, extracted_data, category_data)
    s3 = calculate_s3_family_protection(gaps, extracted_data, category_data)
    s4 = calculate_s4_coverage_stability(gaps, extracted_data, category_data, insurer_name)

    composite, label, result = calculate_health_composite_score(s1, s2, s3, s4)

    logger.info(
        f"🏥 Health 4-Score System: Composite={composite} ({label}) | "
        f"S1={s1['score']} S2={s2['score']} S3={s3['score'] if s3 else 'N/A'} S4={s4['score']}"
    )

    return result


def calculate_health_protection_score(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any]
) -> Tuple[int, str]:
    """
    Backward-compatible wrapper: calls 4 sub-scores, returns composite as Tuple[int, str].
    The router call site at policy_upload.py expects this signature.
    For full score details, use calculate_health_scores_detailed() instead.
    """
    result = calculate_health_scores_detailed(gaps, extracted_data, category_data)
    composite = result["compositeScore"]
    label = result["verdict"]["label"]
    return composite, label


def calculate_life_protection_score(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any]
) -> Tuple[int, str]:
    """
    Calculate protection score for life insurance

    Scoring methodology (100 points total):
    1. Sum assured adequacy (35 points)
    2. Policy type and term (20 points)
    3. Essential riders (25 points)
    4. Premium and payment status (10 points)
    5. Gap severity deductions (10 points max)
    """
    score = 0

    # Convert entire category_data to string for keyword search
    category_str = str(category_data).lower()

    # Helper to find value in nested dict
    def find_value(data: dict, keys: list, default=None):
        if not data:
            return default
        for key in keys:
            if key in data and data[key]:
                return data[key]
            for v in data.values():
                if isinstance(v, dict) and key in v and v[key]:
                    return v[key]
        return default

    # Extract nested data
    coverage_details = category_data.get("coverageDetails", {})
    riders = category_data.get("riders", []) or []
    policy_info = category_data.get("policyIdentification", {})

    # 1. Sum Assured Adequacy (35 points)
    sum_assured = extracted_data.get("coverageAmount", 0) or find_value(coverage_details, ["sumAssured", "deathBenefit", "coverageAmount"], 0)

    if sum_assured >= 20000000:  # Rs. 2 Crore+
        score += 35
    elif sum_assured >= 10000000:  # Rs. 1 Crore+
        score += 32
    elif sum_assured >= 7500000:  # Rs. 75 Lakhs+
        score += 28
    elif sum_assured >= 5000000:  # Rs. 50 Lakhs+
        score += 24
    elif sum_assured >= 2500000:  # Rs. 25 Lakhs+
        score += 18
    elif sum_assured >= 1000000:  # Rs. 10 Lakhs+
        score += 12
    elif sum_assured >= 500000:  # Rs. 5 Lakhs+
        score += 7
    else:
        score += 3  # Any coverage is better than none

    # 2. Policy Type and Term (20 points)
    policy_type = find_value(policy_info, ["policyType", "planType", "productType"], "")
    policy_type_str = str(policy_type).lower() if policy_type else ""

    # Pure term insurance is most efficient for protection
    if "term" in category_str and "ulip" not in category_str:
        score += 12
    elif "endowment" in category_str or "money back" in category_str:
        score += 8
    elif "ulip" in category_str:
        score += 6
    elif "whole life" in category_str:
        score += 10
    else:
        score += 7  # Unknown type

    # Policy term consideration
    policy_term = find_value(coverage_details, ["policyTerm", "term", "coverageTerm"], "")
    policy_term_str = str(policy_term).lower() if policy_term else ""

    import re
    term_match = re.search(r'(\d+)', policy_term_str)
    if term_match:
        term_years = int(term_match.group(1))
        if term_years >= 30:
            score += 8
        elif term_years >= 20:
            score += 6
        elif term_years >= 15:
            score += 4
        elif term_years >= 10:
            score += 2
    else:
        score += 3  # Term exists but unknown

    # 3. Essential Riders (25 points total)
    rider_score = 0
    riders_str = str(riders).lower()

    # Critical Illness Rider (7 points)
    if "critical illness" in category_str or "critical illness" in riders_str:
        rider_score += 7
    elif find_value(category_data, ["criticalIllnessRider", "ciRider"]):
        rider_score += 7

    # Accidental Death Benefit (5 points)
    if "accidental death" in category_str or "adb" in category_str or "accidental death" in riders_str:
        rider_score += 5
    elif find_value(category_data, ["accidentalDeathBenefit", "adb"]):
        rider_score += 5

    # Premium Waiver (5 points)
    if "premium waiver" in category_str or "waiver of premium" in category_str:
        rider_score += 5
    elif find_value(category_data, ["premiumWaiver", "premiumWaiverRider", "premiumWaiverOnCriticalIllness"]):
        rider_score += 5

    # Terminal Illness Benefit (4 points)
    if "terminal illness" in category_str:
        rider_score += 4
    elif find_value(category_data, ["terminalIllnessBenefit", "tibRider"]):
        rider_score += 4

    # Permanent Disability Rider (4 points)
    if "permanent disability" in category_str or "disability" in riders_str:
        rider_score += 4
    elif find_value(category_data, ["permanentDisabilityRider", "disabilityRider"]):
        rider_score += 4

    score += min(25, rider_score)

    # 4. Premium and Payment Status (10 points)
    premium = extracted_data.get("premium", 0) or find_value(category_data, ["premiumAmount", "annualPremium", "premium"], 0)
    policy_status = find_value(policy_info, ["policyStatus", "status"], "")
    policy_status_str = str(policy_status).lower() if policy_status else ""

    if "active" in policy_status_str or "in force" in policy_status_str:
        score += 6
    elif "lapsed" in policy_status_str:
        score += 0  # Lapsed policy - critical issue
    else:
        score += 4  # Unknown status

    # Premium affordability (lower premium for same cover = better value)
    if premium and sum_assured:
        premium_ratio = premium / sum_assured * 1000  # Premium per 1000 SI
        if premium_ratio <= 5:  # Very affordable
            score += 4
        elif premium_ratio <= 10:
            score += 3
        elif premium_ratio <= 20:
            score += 2
        else:
            score += 1
    else:
        score += 2

    # 5. Gap severity deductions (max -10 points)
    high_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "high")
    medium_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "medium")

    gap_deduction = min(10, (high_severity_gaps * 4) + (medium_severity_gaps * 2))
    score -= gap_deduction

    # Ensure score is between 0 and 100
    score = max(0, min(100, score))

    # Determine label
    if score >= 90:
        label = "Excellent Coverage"
    elif score >= 75:
        label = "Good Coverage"
    elif score >= 60:
        label = "Fair Coverage"
    elif score >= 40:
        label = "Needs Improvement"
    else:
        label = "Critical Gaps"

    logger.info(f"💼 Life Insurance Protection Score: {score}% ({label}) - Gaps: H:{high_severity_gaps} M:{medium_severity_gaps}")

    return score, label


# ==================== LIFE INSURANCE V10 — 3-SCORE SYSTEM (EAZR_02 Spec) ====================

# Product type detection constants
LIFE_TERM_KEYWORDS = ['term', 'jeevan amar', 'iprotect', 'click2protect', 'saral jeevan bima', 'term plan', 'term life']
LIFE_SAVINGS_KEYWORDS = ['endowment', 'ulip', 'money back', 'moneyback', 'whole life', 'child', 'pension', 'jeevan anand', 'jeevan lakshya', 'jeevan umang', 'jeevan tarun']

LIFE_PRODUCT_BADGE_COLORS = {
    'term': '#3B82F6',
    'endowment': '#22C55E',
    'ulip': '#8B5CF6',
    'whole_life': '#F59E0B',
    'money_back': '#EC4899',
    'pension': '#6B7280',
    'child_plan': '#14B8A6'
}

LIFE_PRODUCT_LABELS = {
    'term': 'Term Life',
    'endowment': 'Endowment',
    'ulip': 'ULIP',
    'whole_life': 'Whole Life',
    'money_back': 'Money-back',
    'pension': 'Pension',
    'child_plan': 'Child Plan'
}

LIFE_VERDICT_MAP = [
    (90, 100, "Excellent Protection", "Excellent — Protection + Value",
     "Your family is well-protected. Coverage exceeds recommended levels.",
     "Strong protection and healthy policy value. Well-positioned.",
     "#22C55E"),
    (75, 89, "Strong Protection", "Strong — Protection + Value",
     "Solid coverage. Minor enhancements possible via riders.",
     "Good protection base. Policy value on track. Minor optimizations possible.",
     "#84CC16"),
    (60, 74, "Adequate Protection", "Adequate — Protection + Value",
     "Your term cover handles basics but falls short of recommended income replacement.",
     "Good protection base. Policy value growing steadily. SVF opportunity available.",
     "#EAB308"),
    (40, 59, "Moderate Protection", "Moderate — Protection + Value",
     "Significant coverage gap. Family may face financial stress. Action recommended.",
     "Protection gaps exist and policy value underperforming. Review needed.",
     "#F97316"),
    (0, 39, "Needs Attention", "Needs Attention",
     "Critical coverage shortfall. Immediate review recommended.",
     "Major gaps in protection and value. Urgent action needed.",
     "#6B7280"),
]

# Tier-1 insurers for SVF eligibility scoring
LIFE_TIER1_INSURERS = ['lic', 'life insurance corporation', 'hdfc life', 'hdfc standard', 'icici prudential',
                        'sbi life', 'max life', 'max new york']
LIFE_TIER2_INSURERS = ['bajaj allianz life', 'tata aia', 'kotak life', 'aditya birla', 'pnb metlife',
                        'canara hsbc', 'edelweiss tokio', 'star union']


def _get_life_score_label(score: int) -> Dict[str, str]:
    """Return label and color for a life score tier."""
    if score >= 90:
        return {"label": "Excellent", "color": "#22C55E"}
    elif score >= 75:
        return {"label": "Strong", "color": "#84CC16"}
    elif score >= 60:
        return {"label": "Adequate", "color": "#EAB308"}
    elif score >= 40:
        return {"label": "Moderate", "color": "#F97316"}
    else:
        return {"label": "Needs Attention", "color": "#6B7280"}


def _detect_life_product_type(category_data: Dict[str, Any]) -> str:
    """Detect life insurance product sub-type from category data."""
    category_str = str(category_data).lower()

    is_term = any(t in category_str for t in LIFE_TERM_KEYWORDS) and not any(t in category_str for t in LIFE_SAVINGS_KEYWORDS)

    if is_term:
        return 'term'

    # Detect specific savings types
    if 'ulip' in category_str:
        return 'ulip'
    if 'whole life' in category_str or 'jeevan umang' in category_str:
        return 'whole_life'
    if 'money back' in category_str or 'moneyback' in category_str:
        return 'money_back'
    if 'pension' in category_str:
        return 'pension'
    if 'child' in category_str or 'jeevan tarun' in category_str:
        return 'child_plan'
    # Default savings type
    return 'endowment'


def _life_safe_numeric(val, default=0):
    """Safely extract numeric value from various formats."""
    if val is None or val == "" or val == "N/A":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    try:
        import re as _re
        cleaned = _re.sub(r'[^\d.]', '', str(val))
        return float(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


def calculate_life_s1_family_security(
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    S1: Family Financial Security (100 points).
    Evaluates how well the policy protects the family financially.
    Always computed for both term and savings plans.
    """
    coverage_details = category_data.get("coverageDetails", {}) or {}
    policy_info = category_data.get("policyIdentification", {}) or {}
    policyholder = category_data.get("policyholderLifeAssured", {}) or {}
    riders = category_data.get("riders", []) or []
    premium_details = category_data.get("premiumDetails", {}) or {}
    category_str = str(category_data).lower()
    riders_str = str(riders).lower()

    factors = []
    total_score = 0

    # Extract values
    sum_assured = _life_safe_numeric(extracted_data.get("coverageAmount") or coverage_details.get("sumAssured") or coverage_details.get("deathBenefit"), 0)
    age = _life_safe_numeric(policyholder.get("policyholderAge") or policyholder.get("lifeAssuredAge"), 35)

    # Derive annual income: try extracted → SA/10 → premium×10
    _s1_extracted_income = 0
    try:
        _s1_inc_raw = policyholder.get("annualIncome") or policyholder.get("income") or 0
        _s1_extracted_income = float(str(_s1_inc_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('₹', '').strip()) if _s1_inc_raw else 0
    except (ValueError, TypeError):
        _s1_extracted_income = 0
    _s1_prem = 0
    try:
        _s1_prem_raw = premium_details.get("premiumAmount") or 0
        _s1_prem = float(str(_s1_prem_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('₹', '').strip()) if _s1_prem_raw else 0
    except (ValueError, TypeError):
        _s1_prem = 0
    _s1_freq = (premium_details.get("premiumFrequency") or "").lower()
    _s1_annual_prem = _s1_prem
    if _s1_freq == "monthly": _s1_annual_prem = _s1_prem * 12
    elif _s1_freq == "quarterly": _s1_annual_prem = _s1_prem * 4
    elif _s1_freq in ("half-yearly", "semi-annual", "semi_annual"): _s1_annual_prem = _s1_prem * 2
    _s1_sa_income = sum_assured / 10 if sum_assured > 0 else 0
    _s1_prem_income = _s1_annual_prem * 10 if _s1_annual_prem > 0 else 0
    estimated_annual_income = _s1_extracted_income if _s1_extracted_income > 0 else max(_s1_sa_income, _s1_prem_income)
    if estimated_annual_income <= 0:
        estimated_annual_income = sum_assured / 10 if sum_assured > 0 else 0

    # --- Factor 1: SA vs Annual Income (35 pts) ---
    income_multiple = sum_assured / estimated_annual_income if estimated_annual_income > 0 else 0
    if sum_assured >= 20000000:
        sa_pts = 35
    elif sum_assured >= 10000000:
        sa_pts = 32
    elif sum_assured >= 7500000:
        sa_pts = 28
    elif sum_assured >= 5000000:
        sa_pts = 24
    elif sum_assured >= 2500000:
        sa_pts = 18
    elif sum_assured >= 1000000:
        sa_pts = 12
    elif sum_assured >= 500000:
        sa_pts = 7
    else:
        sa_pts = 3

    factors.append({
        "name": "SA vs Annual Income",
        "yourPolicy": f"{income_multiple:.0f}x (₹{sum_assured/100000:.1f}L)" if sum_assured >= 100000 else f"₹{sum_assured:,.0f}",
        "benchmark": "15x annual income",
        "pointsEarned": sa_pts,
        "pointsMax": 35
    })
    total_score += sa_pts

    # --- Factor 2: Liability Coverage (20 pts) ---
    # We don't have actual loan data, estimate based on SA adequacy
    # If SA >= 50L, likely covers most loans; if SA < 10L, likely doesn't
    if sum_assured >= 5000000:
        liability_pts = 20
        liability_desc = "SA likely covers outstanding liabilities"
    elif sum_assured >= 2500000:
        liability_pts = 15
        liability_desc = "SA covers moderate liabilities"
    elif sum_assured >= 1000000:
        liability_pts = 10
        liability_desc = "SA may not cover all liabilities"
    elif sum_assured >= 500000:
        liability_pts = 5
        liability_desc = "SA insufficient for major liabilities"
    else:
        liability_pts = 2
        liability_desc = "SA too low for liability coverage"

    factors.append({
        "name": "Liability Coverage",
        "yourPolicy": liability_desc,
        "benchmark": "SA > 2x outstanding loans",
        "pointsEarned": liability_pts,
        "pointsMax": 20
    })
    total_score += liability_pts

    # --- Factor 3: Policy Term Adequacy (15 pts) ---
    import re as _re
    policy_term_str = str(coverage_details.get("policyTerm", ""))
    term_match = _re.search(r'(\d+)', policy_term_str)
    policy_term = int(term_match.group(1)) if term_match else 0

    # Calculate years remaining
    start_date_str = policy_info.get("policyIssueDate", "")
    years_completed = 0
    years_remaining = 0
    if start_date_str:
        try:
            from datetime import datetime as _dt
            s_dt = _dt.strptime(str(start_date_str).split("T")[0], "%Y-%m-%d")
            years_completed = max(0, (_dt.now() - s_dt).days / 365.25)
            years_remaining = max(0, policy_term - years_completed) if policy_term > 0 else 0
        except (ValueError, TypeError):
            pass

    coverage_end_age = age + years_remaining if years_remaining > 0 else age + policy_term
    if coverage_end_age >= 65:
        term_pts = 15
    elif coverage_end_age >= 60:
        term_pts = 12
    elif coverage_end_age >= 55:
        term_pts = 10
    elif coverage_end_age >= 50:
        term_pts = 7
    else:
        term_pts = 4

    factors.append({
        "name": "Policy Term Adequacy",
        "yourPolicy": f"Till age {int(coverage_end_age)}" if coverage_end_age > age else f"{policy_term} years",
        "benchmark": "Till age 60+",
        "pointsEarned": term_pts,
        "pointsMax": 15
    })
    total_score += term_pts

    # --- Factor 4: Essential Riders (20 pts) ---
    rider_pts = 0

    has_ci = "critical illness" in category_str or "critical illness" in riders_str
    has_adb = "accidental death" in category_str or "adb" in category_str or "addb" in riders_str or "accidental death" in riders_str
    has_wop = "premium waiver" in category_str or "waiver of premium" in category_str or "waiver" in riders_str
    has_terminal = "terminal illness" in category_str or "terminal" in riders_str

    if has_ci:
        rider_pts += 7
    if has_adb:
        rider_pts += 5
    if has_wop:
        rider_pts += 5
    if has_terminal:
        rider_pts += 3

    rider_pts = min(20, rider_pts)
    active_riders = []
    if has_ci:
        active_riders.append("CI")
    if has_adb:
        active_riders.append("ADB")
    if has_wop:
        active_riders.append("WoP")
    if has_terminal:
        active_riders.append("TIB")

    factors.append({
        "name": "Essential Riders",
        "yourPolicy": ", ".join(active_riders) if active_riders else "None",
        "benchmark": "CI + ADB + WoP",
        "pointsEarned": rider_pts,
        "pointsMax": 20
    })
    total_score += rider_pts

    # --- Factor 5: Policy Status & Premium (10 pts) ---
    policy_status = str(policy_info.get("policyStatus", "")).lower()
    status_pts = 0
    if "active" in policy_status or "in force" in policy_status:
        status_pts = 6
    elif "lapsed" in policy_status:
        status_pts = 0
    else:
        status_pts = 4

    _prem_for_ratio = _s1_annual_prem if _s1_annual_prem > 0 else _life_safe_numeric(premium_details.get("premiumAmount") or extracted_data.get("premium"), 0)
    if _prem_for_ratio > 0 and sum_assured > 0:
        premium_ratio = _prem_for_ratio / sum_assured * 1000
        if premium_ratio <= 5:
            status_pts += 4
        elif premium_ratio <= 10:
            status_pts += 3
        elif premium_ratio <= 20:
            status_pts += 2
        else:
            status_pts += 1
    else:
        status_pts += 2

    factors.append({
        "name": "Policy Status & Premium",
        "yourPolicy": policy_status.title() if policy_status else "Unknown",
        "benchmark": "Active with affordable premium",
        "pointsEarned": min(10, status_pts),
        "pointsMax": 10
    })
    total_score += min(10, status_pts)

    total_score = max(0, min(100, total_score))
    label_info = _get_life_score_label(total_score)

    return {
        "score": total_score,
        "label": label_info["label"],
        "color": label_info["color"],
        "name": "Family Financial Security",
        "icon": "family_restroom",
        "factors": factors
    }


def calculate_life_s2_policy_value(
    category_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    S2: Policy Value Score (100 points).
    Savings plans only — returns None for term insurance.
    Evaluates how well the policy is performing as a financial instrument.
    """
    product_type = _detect_life_product_type(category_data)
    if product_type == 'term':
        return None

    coverage_details = category_data.get("coverageDetails", {}) or {}
    bonus_val = category_data.get("bonusValue", {}) or {}
    premium_details = category_data.get("premiumDetails", {}) or {}
    policy_info = category_data.get("policyIdentification", {}) or {}
    key_terms = category_data.get("keyTerms", {}) or {}
    ulip_details = category_data.get("ulipDetails", {}) or {}

    factors = []
    total_score = 0

    # Extract values
    sum_assured = _life_safe_numeric(coverage_details.get("sumAssured"), 0)
    surrender_val = _life_safe_numeric(bonus_val.get("surrenderValue"), 0)
    accrued_bonus = _life_safe_numeric(bonus_val.get("accruedBonus"), 0)
    paid_up_val = _life_safe_numeric(bonus_val.get("paidUpValue"), 0)
    loan_val = _life_safe_numeric(bonus_val.get("loanValue"), 0)
    premium = _life_safe_numeric(premium_details.get("premiumAmount"), 0)
    freq = (premium_details.get("premiumFrequency") or "").lower()
    annual_premium = premium
    if freq == "monthly":
        annual_premium = premium * 12
    elif freq == "quarterly":
        annual_premium = premium * 4
    elif freq in ("half-yearly", "semi-annual", "semi_annual"):
        annual_premium = premium * 2

    import re as _re
    ppt_str = str(coverage_details.get("premiumPayingTerm", ""))
    ppt_match = _re.search(r'(\d+)', ppt_str)
    ppt = int(ppt_match.group(1)) if ppt_match else 0

    policy_term_str = str(coverage_details.get("policyTerm", ""))
    term_match = _re.search(r'(\d+)', policy_term_str)
    policy_term = int(term_match.group(1)) if term_match else 0

    start_date_str = policy_info.get("policyIssueDate", "")
    years_completed = 0
    if start_date_str:
        try:
            from datetime import datetime as _dt
            s_dt = _dt.strptime(str(start_date_str).split("T")[0], "%Y-%m-%d")
            years_completed = max(0, (_dt.now() - s_dt).days / 365.25)
        except (ValueError, TypeError):
            pass

    premiums_paid_count = min(ppt, int(years_completed)) if ppt > 0 else int(years_completed)
    total_premiums_paid = annual_premium * premiums_paid_count

    # --- Factor 1: SV vs Premiums Paid (30 pts) ---
    if total_premiums_paid > 0:
        sv_ratio = surrender_val / total_premiums_paid
        if sv_ratio >= 1.0:
            sv_pts = 30
            sv_desc = f"{sv_ratio:.0%} recovery"
        elif sv_ratio >= 0.9:
            sv_pts = 25
            sv_desc = f"{sv_ratio:.0%} recovery"
        elif sv_ratio >= 0.75:
            sv_pts = 20
            sv_desc = f"{sv_ratio:.0%} recovery"
        elif sv_ratio >= 0.5:
            sv_pts = 15
            sv_desc = f"{sv_ratio:.0%} recovery"
        else:
            sv_pts = 8
            sv_desc = f"{sv_ratio:.0%} recovery" if sv_ratio > 0 else "No SV yet"
    else:
        sv_pts = 10  # New policy, no premiums paid yet
        sv_desc = "New policy"
        sv_ratio = 0

    factors.append({
        "name": "SV vs Premiums Paid",
        "yourPolicy": sv_desc,
        "benchmark": "100%+",
        "pointsEarned": sv_pts,
        "pointsMax": 30
    })
    total_score += sv_pts

    # --- Factor 2: Bonus Rate / CAGR (25 pts) ---
    bonus_rate_raw = bonus_val.get("declaredBonusRate", "")
    annual_bonus_est = 0
    if bonus_rate_raw:
        try:
            rate_match = _re.search(r'(\d+)', str(bonus_rate_raw))
            if rate_match:
                per_thousand = float(rate_match.group(1))
                annual_bonus_est = (sum_assured / 1000) * per_thousand
        except (ValueError, TypeError):
            pass
    if annual_bonus_est == 0 and accrued_bonus > 0 and years_completed > 0:
        annual_bonus_est = accrued_bonus / years_completed

    # For ULIP, check fund value growth
    fund_value = _life_safe_numeric(ulip_details.get("fundValue") or ulip_details.get("totalFundValue"), 0)

    if product_type == 'ulip':
        if fund_value > 0 and total_premiums_paid > 0:
            growth = fund_value / total_premiums_paid
            if growth >= 1.2:
                bonus_pts = 25
            elif growth >= 1.1:
                bonus_pts = 20
            elif growth >= 1.0:
                bonus_pts = 15
            else:
                bonus_pts = 10
            bonus_desc = f"Fund Value ₹{fund_value/100000:.1f}L" if fund_value >= 100000 else f"₹{fund_value:,.0f}"
        else:
            bonus_pts = 12
            bonus_desc = "Fund value not available"
    else:
        if annual_bonus_est > 0:
            per_thousand = (annual_bonus_est / sum_assured * 1000) if sum_assured > 0 else 0
            if per_thousand >= 50:
                bonus_pts = 25
            elif per_thousand >= 40:
                bonus_pts = 20
            elif per_thousand >= 30:
                bonus_pts = 15
            else:
                bonus_pts = 10
            bonus_desc = f"₹{per_thousand:.0f}/₹1000 SA" if per_thousand > 0 else f"₹{annual_bonus_est:,.0f}/yr"
        elif accrued_bonus > 0:
            bonus_pts = 18
            bonus_desc = f"₹{accrued_bonus/100000:.1f}L accrued"
        else:
            bonus_pts = 10
            bonus_desc = "No bonus data available"

    factors.append({
        "name": "Bonus Rate / CAGR",
        "yourPolicy": bonus_desc,
        "benchmark": "₹50+/₹1000 SA",
        "pointsEarned": bonus_pts,
        "pointsMax": 25
    })
    total_score += bonus_pts

    # --- Factor 3: Maturity Projection (20 pts) ---
    years_remaining = max(0, policy_term - years_completed) if policy_term > 0 else 0
    future_bonus = annual_bonus_est * years_remaining if annual_bonus_est > 0 else 0
    projected_maturity = sum_assured + accrued_bonus + future_bonus
    total_future_premiums = annual_premium * max(0, ppt - premiums_paid_count) if ppt > 0 else 0
    total_investment = total_premiums_paid + total_future_premiums

    if total_investment > 0:
        maturity_ratio = projected_maturity / total_investment
        if maturity_ratio >= 2.0:
            mat_pts = 20
        elif maturity_ratio >= 1.5:
            mat_pts = 17
        elif maturity_ratio >= 1.2:
            mat_pts = 15
        elif maturity_ratio >= 1.0:
            mat_pts = 12
        else:
            mat_pts = 8
    else:
        mat_pts = 10
        maturity_ratio = 0

    factors.append({
        "name": "Maturity Projection",
        "yourPolicy": f"₹{projected_maturity/100000:.1f}L projected" if projected_maturity >= 100000 else f"₹{projected_maturity:,.0f}",
        "benchmark": "High guaranteed + bonuses",
        "pointsEarned": mat_pts,
        "pointsMax": 20
    })
    total_score += mat_pts

    # --- Factor 4: Lock-in Progress (15 pts) ---
    if ppt > 0:
        progress = premiums_paid_count / ppt
        if progress >= 0.5:
            lock_pts = 15
        elif progress >= 0.33:
            lock_pts = 12
        else:
            lock_pts = 8
        lock_desc = f"{premiums_paid_count}/{ppt} years paid ({progress:.0%})"
    elif years_completed > 0 and policy_term > 0:
        progress = years_completed / policy_term
        if progress >= 0.5:
            lock_pts = 15
        elif progress >= 0.33:
            lock_pts = 12
        else:
            lock_pts = 8
        lock_desc = f"{years_completed:.0f}/{policy_term} years completed"
    else:
        lock_pts = 8
        lock_desc = "New policy"
        progress = 0

    factors.append({
        "name": "Lock-in Progress",
        "yourPolicy": lock_desc,
        "benchmark": "50%+ premiums paid",
        "pointsEarned": lock_pts,
        "pointsMax": 15
    })
    total_score += lock_pts

    # --- Factor 5: Loan Availability (10 pts) ---
    has_loan_eligibility = loan_val > 0 or surrender_val > 0
    loan_max = loan_val if loan_val > 0 else (surrender_val * 0.9 if surrender_val > 0 else 0)

    if has_loan_eligibility and loan_max >= 50000:
        loan_pts = 10
        loan_desc = f"₹{loan_max/100000:.1f}L max" if loan_max >= 100000 else f"₹{loan_max:,.0f} max"
    elif has_loan_eligibility:
        loan_pts = 7
        loan_desc = f"₹{loan_max:,.0f} available"
    else:
        loan_pts = 3
        loan_desc = "Not yet eligible"

    factors.append({
        "name": "Loan Availability",
        "yourPolicy": loan_desc,
        "benchmark": "≥70% of premiums paid",
        "pointsEarned": loan_pts,
        "pointsMax": 10
    })
    total_score += loan_pts

    total_score = max(0, min(100, total_score))
    label_info = _get_life_score_label(total_score)

    return {
        "score": total_score,
        "label": label_info["label"],
        "color": label_info["color"],
        "name": "Policy Value Score",
        "icon": "savings",
        "factors": factors
    }


def calculate_life_s3_svf_eligibility(
    category_data: Dict[str, Any],
    insurer_name: str = ""
) -> Optional[Dict[str, Any]]:
    """
    S3: SVF Eligibility Score (100 points).
    Savings plans only — returns None for term insurance.
    Evaluates how suitable the policy is for EAZR Surrender Value Financing.
    """
    product_type = _detect_life_product_type(category_data)
    if product_type == 'term':
        return None

    bonus_val = category_data.get("bonusValue", {}) or {}
    coverage_details = category_data.get("coverageDetails", {}) or {}
    policy_info = category_data.get("policyIdentification", {}) or {}
    key_terms = category_data.get("keyTerms", {}) or {}

    factors = []
    total_score = 0

    surrender_val = _life_safe_numeric(bonus_val.get("surrenderValue"), 0)
    loan_outstanding = _life_safe_numeric(key_terms.get("loanOutstanding") or bonus_val.get("loanOutstanding"), 0)
    insurer_lower = (insurer_name or str(policy_info.get("insurerName", ""))).lower()

    import re as _re
    policy_term_str = str(coverage_details.get("policyTerm", ""))
    term_match = _re.search(r'(\d+)', policy_term_str)
    policy_term = int(term_match.group(1)) if term_match else 0

    ppt_str = str(coverage_details.get("premiumPayingTerm", ""))
    ppt_match = _re.search(r'(\d+)', ppt_str)
    ppt = int(ppt_match.group(1)) if ppt_match else 0

    start_date_str = policy_info.get("policyIssueDate", "")
    years_completed = 0
    years_remaining = 0
    if start_date_str:
        try:
            from datetime import datetime as _dt
            s_dt = _dt.strptime(str(start_date_str).split("T")[0], "%Y-%m-%d")
            years_completed = max(0, (_dt.now() - s_dt).days / 365.25)
            years_remaining = max(0, policy_term - years_completed) if policy_term > 0 else 0
        except (ValueError, TypeError):
            pass

    premiums_paid_count = min(ppt, int(years_completed)) if ppt > 0 else int(years_completed)

    # --- Factor 1: Surrender Value Amount (35 pts) ---
    if surrender_val >= 500000:
        sv_pts = 35
    elif surrender_val >= 300000:
        sv_pts = 30
    elif surrender_val >= 100000:
        sv_pts = 25
    elif surrender_val >= 50000:
        sv_pts = 18
    else:
        sv_pts = 8

    factors.append({
        "name": "Surrender Value Amount",
        "yourPolicy": f"₹{surrender_val/100000:.1f}L" if surrender_val >= 100000 else f"₹{surrender_val:,.0f}",
        "benchmark": "₹5L+",
        "pointsEarned": sv_pts,
        "pointsMax": 35
    })
    total_score += sv_pts

    # --- Factor 2: Insurer Tier (20 pts) ---
    is_tier1 = any(t in insurer_lower for t in LIFE_TIER1_INSURERS)
    is_tier2 = any(t in insurer_lower for t in LIFE_TIER2_INSURERS)

    if is_tier1:
        tier_pts = 20
        tier_desc = "Tier 1"
    elif is_tier2:
        tier_pts = 15
        tier_desc = "Tier 2"
    else:
        tier_pts = 10
        tier_desc = "Other"

    factors.append({
        "name": "Insurer Tier",
        "yourPolicy": f"{tier_desc}",
        "benchmark": "Tier 1",
        "pointsEarned": tier_pts,
        "pointsMax": 20
    })
    total_score += tier_pts

    # --- Factor 3: Years to Maturity (20 pts) ---
    if years_remaining >= 10:
        maturity_pts = 20
    elif years_remaining >= 5:
        maturity_pts = 18
    elif years_remaining >= 3:
        maturity_pts = 12
    else:
        maturity_pts = 5

    factors.append({
        "name": "Years to Maturity",
        "yourPolicy": f"{years_remaining:.0f} years" if years_remaining > 0 else "N/A",
        "benchmark": "10+ years",
        "pointsEarned": maturity_pts,
        "pointsMax": 20
    })
    total_score += maturity_pts

    # --- Factor 4: Premium Payment Progress (15 pts) ---
    if ppt > 0 and premiums_paid_count > 0:
        pay_progress = premiums_paid_count / ppt
        if pay_progress >= 0.5:
            pay_pts = 15
        elif pay_progress >= 0.33:
            pay_pts = 12
        else:
            pay_pts = 8
        pay_desc = f"{pay_progress:.0%} paid ({premiums_paid_count}/{ppt})"
    elif premiums_paid_count > 0:
        pay_pts = 12
        pay_desc = f"{premiums_paid_count} years paid"
    else:
        pay_pts = 5
        pay_desc = "No premiums paid yet"

    factors.append({
        "name": "Premium Payment Progress",
        "yourPolicy": pay_desc,
        "benchmark": "50%+ paid",
        "pointsEarned": pay_pts,
        "pointsMax": 15
    })
    total_score += pay_pts

    # --- Factor 5: No Existing Loan (10 pts) ---
    if loan_outstanding <= 0:
        loan_pts = 10
        loan_desc = "No outstanding loan"
    else:
        loan_pts = 0
        loan_desc = f"₹{loan_outstanding:,.0f} outstanding"

    factors.append({
        "name": "No Existing Loan",
        "yourPolicy": loan_desc,
        "benchmark": "₹0 loan",
        "pointsEarned": loan_pts,
        "pointsMax": 10
    })
    total_score += loan_pts

    total_score = max(0, min(100, total_score))
    label_info = _get_life_score_label(total_score)

    return {
        "score": total_score,
        "label": label_info["label"],
        "color": label_info["color"],
        "name": "SVF Eligibility",
        "icon": "account_balance",
        "factors": factors
    }


def calculate_life_composite_score(
    s1: Dict[str, Any],
    s2: Optional[Dict[str, Any]],
    s3: Optional[Dict[str, Any]],
    is_term: bool
) -> Tuple[int, str, Dict[str, Any]]:
    """
    Calculate composite life score and verdict.
    Term: Composite = S1.
    Savings: Composite = S1(45%) + S2(30%) + S3(25%).
    """
    s1_score = s1.get("score", 0)

    if is_term:
        composite = s1_score
    else:
        s2_score = s2.get("score", 0) if s2 else 0
        s3_score = s3.get("score", 0) if s3 else 0
        composite = int(round(s1_score * 0.45 + s2_score * 0.30 + s3_score * 0.25))

    composite = max(0, min(100, composite))

    # Look up verdict
    for low, high, label_term, label_savings, summary_term, summary_savings, color in LIFE_VERDICT_MAP:
        if low <= composite <= high:
            label = label_term if is_term else label_savings
            summary = summary_term if is_term else summary_savings
            verdict = {
                "label": label,
                "summary": summary,
                "color": color,
                "emoji": "shield" if composite >= 75 else ("alert" if composite < 40 else "info")
            }
            return composite, label, verdict

    # Fallback
    verdict = {"label": "Needs Attention", "summary": "Review recommended.", "color": "#6B7280", "emoji": "alert"}
    return composite, "Needs Attention", verdict


def calculate_life_scores_detailed(
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any],
    insurer_name: str = ""
) -> Dict[str, Any]:
    """
    Public entry point for life insurance V10 3-score system.
    Returns complete protectionReadiness structure for policyAnalyzer.
    """
    from datetime import datetime as _dt

    product_type = _detect_life_product_type(category_data)
    is_term = (product_type == 'term')

    # Calculate individual scores
    s1 = calculate_life_s1_family_security(extracted_data, category_data)
    s2 = calculate_life_s2_policy_value(category_data) if not is_term else None
    s3 = calculate_life_s3_svf_eligibility(category_data, insurer_name) if not is_term else None

    # Composite
    composite, verdict_label, verdict = calculate_life_composite_score(s1, s2, s3, is_term)

    # Render mode
    if is_term:
        render_mode = {
            "mode": "PROTECTION_ONLY",
            "scoresShown": ["S1"],
            "compositeFormula": "S1",
            "scenariosApplicable": ["L001"],
            "showSvf": False,
            "showPolicyValue": False,
            "badgeColor": LIFE_PRODUCT_BADGE_COLORS.get(product_type, "#3B82F6"),
            "badgeLabel": LIFE_PRODUCT_LABELS.get(product_type, "Term Life")
        }
        s1["weight"] = "100%"
    else:
        render_mode = {
            "mode": "PROTECTION_AND_VALUE",
            "scoresShown": ["S1", "S2", "S3"],
            "compositeFormula": "S1*0.45 + S2*0.30 + S3*0.25",
            "scenariosApplicable": ["L001", "L002", "L003", "L004"],
            "showSvf": True,
            "showPolicyValue": True,
            "badgeColor": LIFE_PRODUCT_BADGE_COLORS.get(product_type, "#22C55E"),
            "badgeLabel": LIFE_PRODUCT_LABELS.get(product_type, "Endowment")
        }
        s1["weight"] = "45%"
        if s2:
            s2["weight"] = "30%"
        if s3:
            s3["weight"] = "25%"

    scores = {"s1": s1, "s2": s2, "s3": s3}

    logger.info(f"💼 Life V10 Scores: S1={s1['score']}, S2={s2['score'] if s2 else 'N/A'}, S3={s3['score'] if s3 else 'N/A'}, Composite={composite} ({verdict_label}), Type={product_type}")

    return {
        "compositeScore": composite,
        "verdict": verdict,
        "productType": product_type,
        "renderMode": render_mode,
        "scores": scores,
        "analyzedAt": _dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }


# ==================== MOTOR INSURANCE V10 — 3-SCORE SYSTEM (EAZR_03 Spec) ====================

def _get_motor_score_label(score: int) -> Dict[str, str]:
    """Return label and color for motor score per EAZR_03 Section 3.2"""
    if score >= 90:
        return {"label": "Excellent", "color": "#22C55E"}
    elif score >= 75:
        return {"label": "Strong", "color": "#84CC16"}
    elif score >= 60:
        return {"label": "Adequate", "color": "#EAB308"}
    elif score >= 40:
        return {"label": "Basic", "color": "#F97316"}
    else:
        return {"label": "Minimal", "color": "#6B7280"}


MOTOR_VERDICT_MAP = [
    (90, 100, "Excellent Coverage", "Your vehicle is comprehensively protected with all recommended add-ons.", "#22C55E"),
    (75, 89, "Strong Coverage", "Well-covered vehicle. Minor add-on gaps you may want to fill at renewal.", "#84CC16"),
    (60, 74, "Adequate Coverage", "Good base coverage, but key add-ons missing for your vehicle age and city.", "#EAB308"),
    (40, 59, "Basic Coverage", "Significant add-on gaps. Major repair or total loss scenarios will hurt financially.", "#F97316"),
    (0, 39, "Minimal Coverage", "Critical gaps. Your vehicle has very limited protection.", "#6B7280"),
]

MOTOR_TP_VERDICT = "Only third-party liability is covered. Your vehicle itself has zero protection."


def _get_motor_render_mode(product_type: str) -> Dict[str, Any]:
    """Get rendering mode for motor product type per EAZR_03 Section 2.2"""
    pt = product_type.upper()
    if pt.startswith("COMP"):
        return {
            "mode": "FULL_COVERAGE",
            "scoresShown": ["S1", "S2", "S3"],
            "compositeFormula": "S1*0.40 + S2*0.35 + S3*0.25",
            "showIdv": True,
            "showNcb": True,
            "showAddonsAnalysis": True,
            "scenariosApplicable": ["M001", "M002", "M003", "M004", "M005"],
            "showUpgradeBanner": False,
            "badgeColor": "#22C55E",
            "badgeLabel": "Comprehensive",
        }
    elif pt.startswith("TP"):
        return {
            "mode": "TP_ONLY",
            "scoresShown": ["S1"],
            "compositeFormula": "S1",
            "showIdv": False,
            "showNcb": False,
            "showAddonsAnalysis": False,
            "scenariosApplicable": ["M004"],
            "showUpgradeBanner": True,
            "badgeColor": "#F97316",
            "badgeLabel": "Third Party Only",
        }
    else:  # SAOD
        return {
            "mode": "OD_ONLY",
            "scoresShown": ["S1", "S3"],
            "compositeFormula": "S1*0.50 + S3*0.50",
            "showIdv": True,
            "showNcb": True,
            "showAddonsAnalysis": True,
            "scenariosApplicable": ["M001", "M002", "M003", "M005"],
            "showUpgradeBanner": False,
            "badgeColor": "#3B82F6",
            "badgeLabel": "Standalone OD",
        }


def calculate_motor_s1_coverage_adequacy(
    policy_data: Dict[str, Any],
    vehicle_age: int,
    idv: float,
    market_value: float,
) -> Dict[str, Any]:
    """
    Score 1: Coverage Adequacy (0-100) per EAZR_03 Section 5.2
    Factors: IDV vs Market (25), Add-ons for Age (25), PA Cover (15),
             TP Limit (10), Deductible (10), Accessories (10), Geographic Scope (5)
    """
    score = 0
    factors = []
    addons = policy_data.get("addons_map", {})

    # Factor 1: IDV vs Market Value (25 pts)
    idv_ratio = idv / market_value if market_value > 0 else 1.0
    if idv_ratio >= 0.95:
        f1 = 25
    elif idv_ratio >= 0.90:
        f1 = 22
    elif idv_ratio >= 0.85:
        f1 = 18
    elif idv_ratio >= 0.80:
        f1 = 14
    else:
        f1 = 8
    score += f1
    factors.append({
        "name": "IDV vs Market Value",
        "yourPolicy": f"{idv_ratio*100:.0f}%",
        "benchmark": ">=95% of market value",
        "pointsEarned": f1,
        "pointsMax": 25,
    })

    # Factor 2: Add-ons for Vehicle Age (25 pts)
    if vehicle_age <= 3:
        required = ["zero_depreciation", "return_to_invoice", "engine_protect"]
    elif vehicle_age <= 5:
        required = ["zero_depreciation", "engine_protect", "roadside_assistance"]
    else:
        required = ["roadside_assistance", "consumables_cover"]
    have = sum(1 for r in required if addons.get(r))
    f2 = int((have / len(required)) * 25) if required else 25
    score += f2
    factors.append({
        "name": "Add-ons for Vehicle Age",
        "yourPolicy": f"{have}/{len(required)} relevant add-ons",
        "benchmark": f"All {len(required)} recommended",
        "pointsEarned": f2,
        "pointsMax": 25,
    })

    # Factor 3: PA Cover (15 pts)
    pa_owner = policy_data.get("pa_owner_covered", False)
    pa_passengers = policy_data.get("pa_passengers_covered", False)
    if pa_owner and pa_passengers:
        f3 = 15
        pa_detail = "Owner + Passengers"
    elif pa_owner:
        f3 = 10
        pa_detail = "Owner-driver only"
    else:
        f3 = 0
        pa_detail = "No PA cover"
    score += f3
    factors.append({
        "name": "PA Cover",
        "yourPolicy": pa_detail,
        "benchmark": "Owner + Passenger PA",
        "pointsEarned": f3,
        "pointsMax": 15,
    })

    # Factor 4: TP Limit (10 pts) — statutory always covered
    score += 10
    factors.append({
        "name": "TP Limit",
        "yourPolicy": "Statutory TP active",
        "benchmark": "Unlimited (death/injury)",
        "pointsEarned": 10,
        "pointsMax": 10,
    })

    # Factor 5: Deductible Level (10 pts)
    deductible = policy_data.get("voluntary_deductible", 0)
    if deductible <= 1000:
        f5 = 10
    elif deductible <= 2500:
        f5 = 8
    elif deductible <= 5000:
        f5 = 5
    else:
        f5 = 3
    score += f5
    factors.append({
        "name": "Deductible Level",
        "yourPolicy": f"Rs.{deductible:,.0f} voluntary",
        "benchmark": "<=Rs.1,000",
        "pointsEarned": f5,
        "pointsMax": 10,
    })

    # Factor 6: Accessories Coverage (10 pts)
    elec_acc = policy_data.get("electrical_accessories_premium", 0) or 0
    non_elec_acc = policy_data.get("non_electrical_accessories_premium", 0) or 0
    if elec_acc > 0 or non_elec_acc > 0:
        f6 = 10
        acc_detail = "Accessories covered"
    else:
        f6 = 5
        acc_detail = "No accessories premium"
    score += f6
    factors.append({
        "name": "Accessories Coverage",
        "yourPolicy": acc_detail,
        "benchmark": "Electrical + Non-electrical",
        "pointsEarned": f6,
        "pointsMax": 10,
    })

    # Factor 7: Geographic Scope (5 pts)
    f7 = 3
    score += f7
    factors.append({
        "name": "Geographic Scope",
        "yourPolicy": "India",
        "benchmark": "India + Nepal/Bhutan/etc",
        "pointsEarned": f7,
        "pointsMax": 5,
    })

    final_score = min(score, 100)
    label_info = _get_motor_score_label(final_score)
    return {
        "score": final_score,
        "label": label_info["label"],
        "color": label_info["color"],
        "name": "Coverage Adequacy",
        "icon": "shield",
        "factors": factors,
    }


def calculate_motor_s2_claim_readiness(
    policy_data: Dict[str, Any],
    insurer_name: str,
) -> Dict[str, Any]:
    """
    Score 2: Claim Readiness (0-100) per EAZR_03 Section 5.3
    Factors: Network Garages (25), Cashless (20), Claim-friendly Add-ons (20),
             RSA (15), Insurer Reputation (15), Documentation (5)
    """
    score = 0
    factors = []
    addons = policy_data.get("addons_map", {})

    # Factor 1: Network Garages (25 pts)
    f1 = 15  # Default moderate
    score += f1
    factors.append({
        "name": "Network Garages",
        "yourPolicy": "Network garage availability",
        "benchmark": "5,000+ garages",
        "pointsEarned": f1,
        "pointsMax": 25,
    })

    # Factor 2: Cashless Facility (20 pts)
    f2 = 20
    score += f2
    factors.append({
        "name": "Cashless Facility",
        "yourPolicy": "Cashless repair available",
        "benchmark": "Cashless at network garages",
        "pointsEarned": f2,
        "pointsMax": 20,
    })

    # Factor 3: Claim-friendly Add-ons (20 pts)
    claim_addons = ["zero_depreciation", "consumables_cover"]
    have = sum(1 for a in claim_addons if addons.get(a))
    f3 = int((have / len(claim_addons)) * 20) if claim_addons else 20
    score += f3
    factors.append({
        "name": "Claim-friendly Add-ons",
        "yourPolicy": f"{have}/{len(claim_addons)} claim add-ons",
        "benchmark": "Zero Dep + Consumables",
        "pointsEarned": f3,
        "pointsMax": 20,
    })

    # Factor 4: RSA Available (15 pts)
    f4 = 15 if addons.get("roadside_assistance") else 0
    score += f4
    factors.append({
        "name": "RSA Available",
        "yourPolicy": "RSA active" if f4 > 0 else "No RSA",
        "benchmark": "24x7 roadside assistance",
        "pointsEarned": f4,
        "pointsMax": 15,
    })

    # Factor 5: Insurer Claim Reputation (15 pts)
    top_insurers = [
        "icici lombard", "hdfc ergo", "bajaj allianz", "tata aig",
        "new india", "oriental insurance", "united india", "national insurance",
    ]
    insurer_lower = insurer_name.lower() if insurer_name else ""
    f5 = 12 if any(ins in insurer_lower for ins in top_insurers) else 8
    score += f5
    factors.append({
        "name": "Insurer Reputation",
        "yourPolicy": insurer_name or "Unknown",
        "benchmark": "Top-tier insurer",
        "pointsEarned": f5,
        "pointsMax": 15,
    })

    # Factor 6: Documentation (5 pts)
    f6 = 5
    score += f6
    factors.append({
        "name": "Documentation Ready",
        "yourPolicy": "Policy uploaded to EAZR",
        "benchmark": "Digital policy accessible",
        "pointsEarned": f6,
        "pointsMax": 5,
    })

    final_score = min(score, 100)
    label_info = _get_motor_score_label(final_score)
    return {
        "score": final_score,
        "label": label_info["label"],
        "color": label_info["color"],
        "name": "Claim Readiness",
        "icon": "build",
        "factors": factors,
    }


def calculate_motor_s3_value_for_money(
    policy_data: Dict[str, Any],
    ncb_percentage: int,
    idv: float,
    total_premium: float,
) -> Dict[str, Any]:
    """
    Score 3: Value for Money (0-100) per EAZR_03 Section 5.4
    Factors: NCB Utilization (30), Premium vs Market (25), Discounts (20),
             Coverage per Rupee (15), No Wasteful Add-ons (10)
    """
    score = 0
    factors = []

    # Factor 1: NCB Utilization (30 pts)
    if ncb_percentage >= 50:
        f1 = 30
    elif ncb_percentage >= 45:
        f1 = 25
    elif ncb_percentage >= 35:
        f1 = 20
    elif ncb_percentage >= 20:
        f1 = 15
    else:
        f1 = 5
    score += f1
    factors.append({
        "name": "NCB Utilization",
        "yourPolicy": f"{ncb_percentage}% NCB applied",
        "benchmark": "50% (Maximum)",
        "pointsEarned": f1,
        "pointsMax": 30,
    })

    # Factor 2: Premium vs Market (25 pts)
    f2 = 18  # Default adequate
    score += f2
    factors.append({
        "name": "Premium vs Market",
        "yourPolicy": "Market rate comparison",
        "benchmark": "At or below market average",
        "pointsEarned": f2,
        "pointsMax": 25,
    })

    # Factor 3: Discounts Applied (20 pts)
    discounts_found = 0
    if ncb_percentage > 0:
        discounts_found += 1
    if policy_data.get("voluntary_deductible", 0) > 0:
        discounts_found += 1
    f3 = min(discounts_found * 10, 20)
    score += f3
    factors.append({
        "name": "Discounts Applied",
        "yourPolicy": f"{discounts_found} discount(s)",
        "benchmark": "NCB + Voluntary deductible",
        "pointsEarned": f3,
        "pointsMax": 20,
    })

    # Factor 4: Coverage per Rupee (15 pts)
    if total_premium > 0:
        coverage_ratio = idv / total_premium
        if coverage_ratio >= 100:
            f4 = 15
        elif coverage_ratio >= 80:
            f4 = 12
        elif coverage_ratio >= 50:
            f4 = 8
        else:
            f4 = 5
    else:
        f4 = 8
    score += f4
    factors.append({
        "name": "Coverage per Rupee",
        "yourPolicy": f"Rs.{idv:,.0f} IDV for Rs.{total_premium:,.0f}",
        "benchmark": ">=100x IDV:Premium ratio",
        "pointsEarned": f4,
        "pointsMax": 15,
    })

    # Factor 5: No Wasteful Add-ons (10 pts)
    f5 = 8
    score += f5
    factors.append({
        "name": "No Wasteful Add-ons",
        "yourPolicy": "Add-on efficiency check",
        "benchmark": "No unnecessary add-ons",
        "pointsEarned": f5,
        "pointsMax": 10,
    })

    final_score = min(score, 100)
    label_info = _get_motor_score_label(final_score)
    return {
        "score": final_score,
        "label": label_info["label"],
        "color": label_info["color"],
        "name": "Value for Money",
        "icon": "payments",
        "factors": factors,
    }


def calculate_motor_composite_score(
    s1: Dict[str, Any],
    s2: Optional[Dict[str, Any]],
    s3: Optional[Dict[str, Any]],
    product_type: str,
) -> Tuple[int, str, Dict[str, Any]]:
    """
    Calculate composite motor score based on product type per EAZR_03 Section 2.1
    - Comprehensive: S1(40%) + S2(35%) + S3(25%)
    - TP-Only: S1 only (caps at ~40)
    - SAOD: S1(50%) + S3(50%)
    """
    pt = product_type.upper()

    if pt.startswith("COMP"):
        composite = int(
            s1["score"] * 0.40
            + (s2["score"] if s2 else 0) * 0.35
            + (s3["score"] if s3 else 0) * 0.25
        )
    elif pt.startswith("TP"):
        # TP-Only: S1 only, naturally caps low since many factors score 0
        composite = min(s1["score"], 40)
    elif pt == "SAOD":
        composite = int(
            s1["score"] * 0.50
            + (s3["score"] if s3 else 0) * 0.50
        )
    else:
        composite = s1["score"]

    composite = max(0, min(100, composite))

    # Determine verdict
    verdict = {"label": "Minimal Coverage", "summary": "", "color": "#6B7280"}
    for low, high, label, summary, color in MOTOR_VERDICT_MAP:
        if low <= composite <= high:
            # TP-Only gets special summary
            if pt.startswith("TP") and composite < 40:
                summary = MOTOR_TP_VERDICT
            verdict = {"label": label, "summary": summary, "color": color}
            break

    return composite, verdict["label"], verdict


def calculate_motor_scores_detailed(
    policy_data: Dict[str, Any],
    vehicle_age: int,
    idv: float,
    market_value: float,
    ncb_percentage: int,
    total_premium: float,
    insurer_name: str,
    product_type: str,
) -> Dict[str, Any]:
    """
    Public entry point: Calculate all motor scores and return full structure.
    Returns dict with compositeScore, verdict, productType, renderMode, scores, analyzedAt.
    """
    from datetime import datetime, timezone

    pt = product_type.upper()

    # Always calculate S1
    s1 = calculate_motor_s1_coverage_adequacy(policy_data, vehicle_age, idv, market_value)

    # S2 only for Comprehensive
    s2 = None
    if pt.startswith("COMP"):
        s2 = calculate_motor_s2_claim_readiness(policy_data, insurer_name)

    # S3 for Comprehensive and SAOD
    s3 = None
    if pt.startswith("COMP") or pt == "SAOD":
        s3 = calculate_motor_s3_value_for_money(policy_data, ncb_percentage, idv, total_premium)

    composite, verdict_label, verdict = calculate_motor_composite_score(s1, s2, s3, product_type)
    render_mode = _get_motor_render_mode(product_type)

    # Add weights to scores
    if pt.startswith("COMP"):
        s1["weight"] = "40%"
        if s2:
            s2["weight"] = "35%"
        if s3:
            s3["weight"] = "25%"
    elif pt == "SAOD":
        s1["weight"] = "50%"
        if s3:
            s3["weight"] = "50%"
    else:
        s1["weight"] = "100%"

    return {
        "compositeScore": composite,
        "verdict": verdict,
        "productType": product_type,
        "renderMode": render_mode,
        "scores": {
            "s1": s1,
            "s2": s2,
            "s3": s3,
        },
        "analyzedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def calculate_motor_protection_score(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any],
) -> Tuple[int, str]:
    """
    Calculate protection score for motor/vehicle insurance.
    V10: Uses 3-score system (S1/S2/S3) internally, returns composite for backward compat.
    """
    import re

    category_str = str(category_data).lower()
    coverage_details = category_data.get("coverageDetails", {})
    add_on_covers = category_data.get("addOnCovers", {})
    ncb_data = category_data.get("ncb", {})
    premium_breakdown = category_data.get("premiumBreakdown", {})
    vehicle_details = category_data.get("vehicleDetails", {})

    # Detect product type
    policy_type_str = str(category_data.get("policyIdentification", {}).get("productType", "")).lower()
    if "standalone" in policy_type_str or "saod" in policy_type_str:
        product_type = "SAOD"
    elif "third party" in policy_type_str or "tp only" in policy_type_str or "tp" == policy_type_str:
        product_type = "TP_CAR"
    elif "comprehensive" in category_str or "package" in category_str:
        product_type = "COMP_CAR"
    else:
        # Fallback: check if OD and TP premiums exist
        od_p = _parse_number_from_string(str(premium_breakdown.get("basicOdPremium", 0)))
        tp_p = _parse_number_from_string(str(premium_breakdown.get("basicTpPremium", 0)))
        if od_p > 0 and tp_p > 0:
            product_type = "COMP_CAR"
        elif tp_p > 0 and od_p == 0:
            product_type = "TP_CAR"
        elif od_p > 0 and tp_p == 0:
            product_type = "SAOD"
        else:
            product_type = "COMP_CAR"

    # Build addons_map from category_data
    addons_map = {}
    addon_key_mapping = {
        "zeroDepreciation": "zero_depreciation",
        "engineProtection": "engine_protect",
        "returnToInvoice": "return_to_invoice",
        "roadsideAssistance": "roadside_assistance",
        "consumablesCover": "consumables_cover",
        "consumables": "consumables_cover",
        "ncbProtect": "ncb_protect",
        "keyReplacement": "key_replacement",
        "tyreProtect": "tyre_protect",
        "personalBaggage": "personal_baggage",
        "emiProtect": "emi_protect",
        "dailyAllowance": "daily_allowance",
        "windshieldCover": "windshield_cover",
        "evCover": "electric_vehicle_cover",
        "batteryProtect": "battery_protect",
    }
    for cat_key, map_key in addon_key_mapping.items():
        val = add_on_covers.get(cat_key, False)
        addons_map[map_key] = bool(val) if not isinstance(val, bool) else val

    # Also check category_str for addons not in structured data
    if not addons_map.get("zero_depreciation") and ("zero dep" in category_str or "nil dep" in category_str or "bumper to bumper" in category_str):
        addons_map["zero_depreciation"] = True
    if not addons_map.get("engine_protect") and ("engine protect" in category_str or "engine guard" in category_str):
        addons_map["engine_protect"] = True
    if not addons_map.get("roadside_assistance") and ("roadside" in category_str or "rsa" in category_str):
        addons_map["roadside_assistance"] = True

    # Extract IDV
    idv = _parse_number_from_string(str(coverage_details.get("idv", 0)))
    if not idv:
        idv = _parse_number_from_string(str(extracted_data.get("coverageAmount", 0)))
    market_value = idv * 1.15 if idv > 0 else 0

    # Extract vehicle age
    mfg_year = vehicle_details.get("manufacturingYear", "")
    try:
        vehicle_age = max(0, datetime.now().year - int(mfg_year)) if mfg_year else 3
    except (ValueError, TypeError):
        vehicle_age = 3

    # Extract NCB
    ncb_pct_raw = ncb_data.get("ncbPercentage", "0")
    try:
        ncb_pct = int(float(str(ncb_pct_raw).replace("%", "").strip()))
    except (ValueError, TypeError):
        ncb_pct = 0

    # Extract premiums
    od_premium = _parse_number_from_string(str(premium_breakdown.get("basicOdPremium", 0)))
    tp_premium = _parse_number_from_string(str(premium_breakdown.get("basicTpPremium", 0)))
    total_premium = _parse_number_from_string(str(premium_breakdown.get("totalPremium", 0)))
    if not total_premium:
        total_premium = od_premium + tp_premium

    # Build policy_data
    pa_owner = bool(coverage_details.get("personalAccidentCover") or "personal accident" in category_str or "pa cover" in category_str)
    policy_data = {
        "addons_map": addons_map,
        "product_type": product_type,
        "pa_owner_covered": pa_owner,
        "pa_passengers_covered": False,
        "voluntary_deductible": _parse_number_from_string(str(coverage_details.get("voluntaryDeductible", 0))),
        "electrical_accessories_premium": _parse_number_from_string(str(premium_breakdown.get("electricalAccessoriesPremium", 0))),
        "non_electrical_accessories_premium": _parse_number_from_string(str(premium_breakdown.get("nonElectricalAccessoriesPremium", 0))),
        "od_premium": od_premium,
    }

    insurer_name = extracted_data.get("insuranceProvider", "")

    # Calculate detailed scores
    scores = calculate_motor_scores_detailed(
        policy_data, vehicle_age, idv, market_value,
        ncb_pct, total_premium, insurer_name, product_type,
    )

    composite = scores["compositeScore"]
    label = scores["verdict"]["label"]

    logger.info(f"🚗 Motor V10 Score: {composite}% ({label}) | Type: {product_type} | S1:{scores['scores']['s1']['score']} S2:{scores['scores']['s2']['score'] if scores['scores']['s2'] else 'N/A'} S3:{scores['scores']['s3']['score'] if scores['scores']['s3'] else 'N/A'}")

    return composite, label


def calculate_travel_protection_score(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any]
) -> Tuple[int, str]:
    """
    Calculate protection score for travel insurance

    Factors considered:
    1. Coverage amount adequacy (30 points)
    2. Critical gaps severity (40 points)
    3. Essential features (30 points)
    """
    score = 100

    # Count gaps by severity
    high_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "high")
    medium_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "medium")
    low_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "low")

    # Deduct points based on gap severity (40 points max)
    score -= high_severity_gaps * 10  # High severity: -10 points each
    score -= medium_severity_gaps * 5  # Medium severity: -5 points each
    score -= low_severity_gaps * 2     # Low severity: -2 points each

    # Check coverage adequacy (30 points)
    coverage_amount = extracted_data.get("coverageAmount") or 0

    # For international travel, minimum coverage should be based on destination
    destination = (category_data.get("destination") or "").lower()

    if "schengen" in destination or "europe" in destination:
        # Schengen requires minimum €30,000 (≈ ₹27 lakhs)
        if coverage_amount < 2700000:
            score -= 30
        elif coverage_amount < 5000000:
            score -= 15
    elif "usa" in destination or "canada" in destination or "america" in destination:
        # USA/Canada recommended minimum $50,000 (≈ ₹40 lakhs)
        if coverage_amount < 4000000:
            score -= 30
        elif coverage_amount < 7500000:
            score -= 15
    else:
        # Other destinations - minimum ₹10 lakhs recommended
        if coverage_amount < 1000000:
            score -= 30
        elif coverage_amount < 2000000:
            score -= 20
        elif coverage_amount < 3000000:
            score -= 10

    # Check essential features (30 points total)
    essential_features_missing = 0

    # Check for medical expenses coverage
    medical_expenses = category_data.get("medicalExpensesCoverage", "")
    if not medical_expenses or medical_expenses == "Not covered":
        essential_features_missing += 1

    # Check for emergency evacuation
    emergency_evacuation = category_data.get("emergencyEvacuation", "")
    if not emergency_evacuation or emergency_evacuation == "Not covered":
        essential_features_missing += 1

    # Check for trip cancellation
    trip_cancellation = category_data.get("tripCancellation", "")
    if not trip_cancellation or trip_cancellation == "Not covered":
        essential_features_missing += 1

    # Check for baggage loss
    baggage_loss = category_data.get("baggageLoss", "")
    if not baggage_loss or baggage_loss == "Not covered":
        essential_features_missing += 1

    # Check for passport loss
    passport_loss = category_data.get("passportLoss", "")
    if not passport_loss or passport_loss == "Not covered":
        essential_features_missing += 1

    # Check for personal liability
    personal_liability = category_data.get("personalLiability", "")
    if not personal_liability or personal_liability == "Not covered":
        essential_features_missing += 1

    # Deduct for missing essential features
    score -= essential_features_missing * 5  # -5 points per missing feature

    # Ensure score is between 0 and 100
    score = max(0, min(100, score))

    # Determine label
    if score >= 90:
        label = "Excellent Coverage"
    elif score >= 75:
        label = "Good Coverage"
    elif score >= 60:
        label = "Fair Coverage"
    elif score >= 40:
        label = "Needs Improvement"
    else:
        label = "Critical Gaps"

    logger.info(f"✈️ Travel Insurance Protection Score: {score}% ({label}) - Gaps: H:{high_severity_gaps} M:{medium_severity_gaps} L:{low_severity_gaps}")

    return score, label


# ==================== TRAVEL INSURANCE V10 — 2-SCORE SYSTEM (EAZR_05 Spec) ====================
# S1: Medical Emergency Readiness (60% weight)
# S2: Trip Protection Score (40% weight)

TRAVEL_VERDICT_MAP = [
    (90, 100, "Excellent Travel Cover",
     "Comprehensive coverage for your destination. Medical and trip protection both strong.",
     "Well-covered for your domestic trip. Trip cancellation and medical adequately protected.",
     "#22C55E", "shield"),
    (75, 89, "Strong Travel Cover",
     "Good medical coverage for {destination}. Trip protection has minor gaps to fix before departure.",
     "Good coverage. Minor trip protection gaps to review.",
     "#84CC16", "shield"),
    (60, 74, "Adequate Travel Cover",
     "Medical coverage meets minimum for {destination} but leaves little margin. Key trip protections missing.",
     "Basic coverage in place. Trip cancellation or baggage gaps to address.",
     "#EAB308", "warning"),
    (40, 59, "Basic Travel Cover",
     "Medical coverage below recommended for {destination}. Significant trip protection gaps.",
     "Limited coverage. Key protections missing.",
     "#F97316", "warning"),
    (0, 39, "Needs Upgrade",
     "Critical gaps for {destination}. Medical coverage inadequate and trip poorly protected.",
     "Minimal coverage. Review before traveling.",
     "#6B7280", "alert"),
]


def _get_travel_score_label(score: int) -> Dict[str, str]:
    """Return label and color for a travel sub-score."""
    if score >= 90:
        return {"label": "Excellent", "color": "#22C55E"}
    elif score >= 75:
        return {"label": "Strong", "color": "#84CC16"}
    elif score >= 60:
        return {"label": "Adequate", "color": "#EAB308"}
    elif score >= 40:
        return {"label": "Basic", "color": "#F97316"}
    else:
        return {"label": "Minimal", "color": "#6B7280"}


def calculate_travel_scores_detailed(
    s1_result: Dict[str, Any],
    s2_result: Dict[str, Any],
    destination: str = "International",
    is_domestic: bool = False
) -> Dict[str, Any]:
    """
    Public entry point for Travel insurance V10 2-score system.
    Wraps pre-computed S1/S2 results (from _calculate_travel_medical_readiness
    and _calculate_travel_trip_protection in policy_upload.py) into V10
    protectionReadiness-compatible structure.

    Args:
        s1_result: {"score": int, "factors": [{"name": str, "score": int, "maxScore": int, "detail": str}, ...]}
        s2_result: {"score": int, "factors": [...]}
        destination: Destination string for verdict templating
        is_domestic: Whether trip is domestic (affects verdict summary text)

    Returns:
        Dict with compositeScore, verdict, scores (s1+s2 with factors), analyzedAt
    """
    from datetime import datetime as _dt

    s1_score = min(100, max(0, s1_result.get("score", 0)))
    s2_score = min(100, max(0, s2_result.get("score", 0)))

    # Composite = S1 * 0.6 + S2 * 0.4
    composite = round(s1_score * 0.6 + s2_score * 0.4)
    composite = min(100, max(0, composite))

    # Verdict from TRAVEL_VERDICT_MAP
    verdict = {"label": "Needs Upgrade", "summary": "Critical coverage gaps.", "color": "#6B7280", "emoji": "alert"}
    for low, high, label, summary_intl, summary_dom, color, emoji in TRAVEL_VERDICT_MAP:
        if low <= composite <= high:
            summary = summary_dom if is_domestic else summary_intl.replace("{destination}", destination)
            verdict = {"label": label, "summary": summary, "color": color, "emoji": emoji}
            break

    # Enrich S1 factors with V10 aliases
    s1_factors = []
    for f in s1_result.get("factors", []):
        enriched = dict(f)
        enriched["pointsEarned"] = f.get("score", 0)
        enriched["pointsMax"] = f.get("maxScore", 0)
        s1_factors.append(enriched)

    s2_factors = []
    for f in s2_result.get("factors", []):
        enriched = dict(f)
        enriched["pointsEarned"] = f.get("score", 0)
        enriched["pointsMax"] = f.get("maxScore", 0)
        s2_factors.append(enriched)

    s1_label_info = _get_travel_score_label(s1_score)
    s2_label_info = _get_travel_score_label(s2_score)

    scores = {
        "s1": {
            "scoreId": "S1",
            "name": "Medical Emergency Readiness",
            "purpose": "Medical preparedness for destination healthcare costs",
            "icon": "local_hospital",
            "weight": "60%",
            "score": s1_score,
            "label": s1_label_info["label"],
            "color": s1_label_info["color"],
            "factors": s1_factors
        },
        "s2": {
            "scoreId": "S2",
            "name": "Trip Protection Score",
            "purpose": "Financial protection for trip investment",
            "icon": "luggage",
            "weight": "40%",
            "score": s2_score,
            "label": s2_label_info["label"],
            "color": s2_label_info["color"],
            "factors": s2_factors
        }
    }

    logger.info(
        f"✈️ Travel V10 Scores: S1={s1_score}, S2={s2_score}, "
        f"Composite={composite} ({verdict['label']})"
    )

    return {
        "compositeScore": composite,
        "verdict": verdict,
        "scores": scores,
        "analyzedAt": _dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }


def calculate_accidental_protection_score(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any]
) -> Tuple[int, str]:
    """
    Calculate protection score for Personal Accident insurance

    Scoring methodology (100 points total):
    1. Sum insured adequacy (35 points)
    2. Accidental death benefit (20 points)
    3. Permanent disability coverage (20 points)
    4. Additional benefits (15 points)
    5. Gap severity deductions (10 points max)
    """
    score = 0

    # Extract nested data properly
    coverage_details = category_data.get("coverageDetails", {})
    additional_benefits = category_data.get("additionalBenefits", {})

    # 1. Sum Insured Adequacy (35 points)
    # Recommended PA cover: Minimum Rs. 5 lakhs, ideal Rs. 25 lakhs+
    sum_insured = extracted_data.get("coverageAmount", 0) or coverage_details.get("sumInsured", 0)

    if sum_insured >= 2500000:  # Rs. 25 lakhs+
        score += 35
    elif sum_insured >= 1500000:  # Rs. 15 lakhs+
        score += 30
    elif sum_insured >= 1000000:  # Rs. 10 lakhs+
        score += 25
    elif sum_insured >= 500000:  # Rs. 5 lakhs+
        score += 20
    elif sum_insured >= 250000:  # Rs. 2.5 lakhs+
        score += 12
    elif sum_insured >= 100000:  # Rs. 1 lakh+
        score += 5
    # Below 1 lakh: 0 points

    # 2. Accidental Death Benefit (20 points)
    # Check if 100% of SI is payable on accidental death
    ad_cover = coverage_details.get("accidentalDeath", coverage_details.get("accidentalDeathCover", ""))
    if isinstance(ad_cover, dict):
        ad_cover = ad_cover.get("benefitPercentage", ad_cover.get("covered", ""))
    ad_cover_str = str(ad_cover).lower()

    if ad_cover and ("100%" in ad_cover_str or "full" in ad_cover_str or "sum insured" in ad_cover_str):
        score += 20
    elif ad_cover and ("75%" in ad_cover_str or "80%" in ad_cover_str or "90%" in ad_cover_str):
        score += 15
    elif ad_cover and ("50%" in ad_cover_str or "60%" in ad_cover_str):
        score += 10
    elif ad_cover:
        score += 8  # Some coverage is better than none
    # No AD cover: 0 points

    # 3. Permanent Disability Coverage (20 points)
    # Check for PTD (Permanent Total Disability) and PPD (Permanent Partial Disability)
    ptd = coverage_details.get("permanentTotalDisability") or coverage_details.get("ptd")
    ppd = coverage_details.get("permanentPartialDisability") or coverage_details.get("ppd")
    ttd = coverage_details.get("temporaryTotalDisability") or coverage_details.get("ttd")

    disability_score = 0

    # PTD (10 points)
    if ptd:
        ptd_str = str(ptd).lower()
        if "100%" in ptd_str or "full" in ptd_str or "sum insured" in ptd_str:
            disability_score += 10
        else:
            disability_score += 7

    # PPD (7 points)
    if ppd:
        disability_score += 7

    # TTD bonus (3 points)
    if ttd:
        disability_score += 3

    score += min(20, disability_score)  # Cap at 20 points

    # 4. Additional Benefits (15 points total)
    additional_score = 0

    # Medical Expenses Reimbursement (5 points)
    if coverage_details.get("medicalExpenses") or additional_benefits.get("medicalExpenses"):
        additional_score += 5

    # Hospital Cash Benefit (3 points)
    if coverage_details.get("hospitalCashBenefit") or additional_benefits.get("hospitalCashBenefit"):
        additional_score += 3

    # Ambulance Cover (2 points)
    if coverage_details.get("ambulanceCover") or additional_benefits.get("ambulanceCharges"):
        additional_score += 2

    # Education Benefit (2 points)
    if coverage_details.get("educationBenefit") or additional_benefits.get("educationBenefit"):
        additional_score += 2

    # Transportation of Mortal Remains (1 point)
    if coverage_details.get("transportationOfMortalRemains") or additional_benefits.get("transportationOfMortalRemains"):
        additional_score += 1

    # Funeral Expenses (1 point)
    if coverage_details.get("funeralExpenses") or additional_benefits.get("funeralExpenses"):
        additional_score += 1

    # Loan Protector (1 point)
    if coverage_details.get("loanProtectorCover") or additional_benefits.get("loanProtectorCover"):
        additional_score += 1

    score += min(15, additional_score)  # Cap at 15 points

    # 5. Gap severity deductions (max -10 points)
    high_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "high")
    medium_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "medium")

    gap_deduction = min(10, (high_severity_gaps * 4) + (medium_severity_gaps * 2))
    score -= gap_deduction

    # Bonus points for comprehensive coverage
    # Health services included (teleconsultation, second opinion, etc.)
    if additional_benefits.get("healthServicesIncluded"):
        score += 3

    # Ensure score is between 0 and 100
    score = max(0, min(100, score))

    # Log if score is 0 — indicates data extraction found no expected fields
    if score == 0:
        logger.warning(f"🛡️ Personal Accident: Score is 0 — data extraction may have failed for SI: {sum_insured}")

    # Determine label
    if score >= 85:
        label = "Excellent Coverage"
    elif score >= 70:
        label = "Good Coverage"
    elif score >= 55:
        label = "Fair Coverage"
    elif score >= 40:
        label = "Needs Improvement"
    else:
        label = "Critical Gaps"

    logger.info(f"🛡️ Personal Accident Protection Score: {score}% ({label}) - SI: {sum_insured:,}, AD: {ad_cover or 'N/A'}, PTD: {ptd or 'N/A'}, PPD: {ppd or 'N/A'}, Gaps: H:{high_severity_gaps} M:{medium_severity_gaps}")

    return score, label


# ==================== PERSONAL ACCIDENT V10 — 2-SCORE SYSTEM (EAZR_04 Spec) ====================

PA_VERDICT_MAP = [
    (90, 100, "Excellent Protection", "Comprehensive accident coverage. Strong income replacement and disability benefits.", "#22C55E", "shield"),
    (75, 89, "Strong Protection", "Good accident cover with solid income replacement. Minor enhancement possible.", "#84CC16", "shield"),
    (60, 74, "Adequate Protection", "Basic accident cover in place. Income replacement during disability needs strengthening.", "#EAB308", "warning"),
    (40, 59, "Moderate Protection", "Your PA covers accidental death but income replacement during disability is significantly under-covered.", "#F97316", "warning"),
    (0, 39, "Needs Attention", "Critical gaps in accident protection. Disability and income loss largely uncovered.", "#6B7280", "alert"),
]


def _get_pa_score_label(score: int) -> Dict[str, str]:
    """Return label and color for PA score per EAZR_04 Section 2.2"""
    if score >= 90:
        return {"label": "Excellent", "color": "#22C55E"}
    elif score >= 75:
        return {"label": "Strong", "color": "#84CC16"}
    elif score >= 60:
        return {"label": "Adequate", "color": "#EAB308"}
    elif score >= 40:
        return {"label": "Moderate", "color": "#F97316"}
    else:
        return {"label": "Minimal", "color": "#6B7280"}


def _pa_safe_numeric(val, default=0):
    """Safely convert a value to float for PA scoring."""
    if val is None or val == "" or val == "N/A":
        return default
    if isinstance(val, (int, float)):
        return float(val)
    try:
        import re as _re
        cleaned = _re.sub(r'[^\d.]', '', str(val))
        return float(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


def calculate_pa_s1_income_replacement(category_data: Dict[str, Any], annual_income: int = 1000000) -> Dict[str, Any]:
    """
    S1: Income Replacement Adequacy (100 points, 60% weight)
    Per EAZR_04 Spec — same logic as _calculate_pa_income_replacement_score in policy_upload.py
    """
    coverage = category_data.get("coverageDetails", {}) or {}
    additional = category_data.get("additionalBenefits", {}) or {}

    sum_insured = _pa_safe_numeric(coverage.get("sumInsured", 0))
    if sum_insured <= 0:
        sum_insured = _pa_safe_numeric(category_data.get("sumInsured", 0))

    ad = coverage.get("accidentalDeath", {}) if isinstance(coverage.get("accidentalDeath"), dict) else {}
    ptd = coverage.get("permanentTotalDisability", {}) if isinstance(coverage.get("permanentTotalDisability"), dict) else {}
    ttd = coverage.get("temporaryTotalDisability", {}) if isinstance(coverage.get("temporaryTotalDisability"), dict) else {}

    ad_benefit = _pa_safe_numeric(ad.get("benefitAmount", sum_insured), sum_insured)
    ptd_benefit = _pa_safe_numeric(ptd.get("benefitAmount", sum_insured), sum_insured)
    ttd_covered = ttd.get("covered", False)
    ttd_weekly = _pa_safe_numeric(ttd.get("benefitAmount", 0))
    if ttd_weekly == 0 and ttd_covered and sum_insured > 0:
        pct = _pa_safe_numeric(ttd.get("benefitPercentage", 1), 1)
        ttd_weekly = sum_insured * pct / 100

    weekly_income = annual_income / 52

    factors = []
    score = 0

    # Factor 1: Death Benefit vs Income (35 pts)
    income_multiple = ad_benefit / annual_income if annual_income > 0 else 0
    if income_multiple >= 10:
        f1_pts = 35
    elif income_multiple >= 7:
        f1_pts = 28
    elif income_multiple >= 5:
        f1_pts = 22
    elif income_multiple >= 3:
        f1_pts = 15
    else:
        f1_pts = 8
    score += f1_pts
    factors.append({
        "name": "Death Benefit vs Income",
        "pointsEarned": f1_pts,
        "pointsMax": 35,
        "yourPolicy": f"{income_multiple:.1f}x annual income",
        "benchmark": "10x annual income"
    })

    # Factor 2: PTD Benefit vs Income (25 pts)
    ptd_multiple = ptd_benefit / annual_income if annual_income > 0 else 0
    if ptd_multiple >= 10:
        f2_pts = 25
    elif ptd_multiple >= 7:
        f2_pts = 20
    elif ptd_multiple >= 5:
        f2_pts = 15
    else:
        f2_pts = 8
    score += f2_pts
    factors.append({
        "name": "PTD Benefit vs Income",
        "pointsEarned": f2_pts,
        "pointsMax": 25,
        "yourPolicy": f"{ptd_multiple:.1f}x annual income",
        "benchmark": "10x annual income"
    })

    # Factor 3: TTD vs Weekly Income (20 pts)
    if not ttd_covered or ttd_weekly <= 0:
        f3_pts = 0
        ttd_pct_str = "Not covered"
    else:
        ttd_pct = (ttd_weekly / weekly_income * 100) if weekly_income > 0 else 0
        if ttd_pct >= 50:
            f3_pts = 20
        elif ttd_pct >= 30:
            f3_pts = 15
        elif ttd_pct >= 20:
            f3_pts = 10
        else:
            f3_pts = 5
        ttd_pct_str = f"{ttd_pct:.0f}% of weekly income"
    score += f3_pts
    factors.append({
        "name": "TTD vs Weekly Income",
        "pointsEarned": f3_pts,
        "pointsMax": 20,
        "yourPolicy": ttd_pct_str,
        "benchmark": "≥50% of weekly income"
    })

    # Factor 4: EMI Coverage (10 pts)
    emi_cover = additional.get("loanEmiCover", {})
    emi_covered = emi_cover.get("covered", False) if isinstance(emi_cover, dict) else False
    f4_pts = 10 if emi_covered else 0
    score += f4_pts
    factors.append({
        "name": "EMI Coverage",
        "pointsEarned": f4_pts,
        "pointsMax": 10,
        "yourPolicy": "Covered" if emi_covered else "Not covered",
        "benchmark": "EMI protection included"
    })

    # Factor 5: Double Indemnity (10 pts)
    double_ind = ad.get("doubleIndemnity", {})
    double_applicable = double_ind.get("applicable", False) if isinstance(double_ind, dict) else False
    f5_pts = 10 if double_applicable else 0
    score += f5_pts
    factors.append({
        "name": "Double Indemnity",
        "pointsEarned": f5_pts,
        "pointsMax": 10,
        "yourPolicy": "Applicable" if double_applicable else "Not applicable",
        "benchmark": "Double payout for public transport"
    })

    score = min(100, max(0, score))
    label_info = _get_pa_score_label(score)

    return {
        "score": score,
        "label": label_info["label"],
        "color": label_info["color"],
        "name": "Income Replacement Adequacy",
        "icon": "payments",
        "weight": "60%",
        "factors": factors
    }


def calculate_pa_s2_disability_protection(category_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    S2: Disability Protection Depth (100 points, 40% weight)
    Per EAZR_04 Spec — same logic as _calculate_pa_disability_protection_score in policy_upload.py
    """
    coverage = category_data.get("coverageDetails", {}) or {}
    additional = category_data.get("additionalBenefits", {}) or {}

    ppd = coverage.get("permanentPartialDisability", {}) if isinstance(coverage.get("permanentPartialDisability"), dict) else {}
    ttd = coverage.get("temporaryTotalDisability", {}) if isinstance(coverage.get("temporaryTotalDisability"), dict) else {}
    medical = coverage.get("medicalExpenses", {}) if isinstance(coverage.get("medicalExpenses"), dict) else {}

    ppd_schedule = ppd.get("schedule", []) if isinstance(ppd.get("schedule"), list) else []
    ttd_covered = ttd.get("covered", False)
    ttd_max_weeks = int(_pa_safe_numeric(ttd.get("maximumWeeks", 0)))
    ttd_waiting = int(_pa_safe_numeric(ttd.get("waitingPeriodDays", 0)))
    medical_covered = medical.get("covered", False)
    medical_pct = _pa_safe_numeric(medical.get("limitPercentage", 0))

    sum_insured = _pa_safe_numeric(coverage.get("sumInsured", 0))
    if medical_covered and medical_pct == 0:
        med_amount = _pa_safe_numeric(medical.get("limitAmount", 0))
        if med_amount > 0 and sum_insured > 0:
            medical_pct = (med_amount / sum_insured) * 100

    factors = []
    score = 0

    # Factor 1: PPD Schedule Comprehensiveness (30 pts)
    ppd_count = len(ppd_schedule)
    if ppd_count >= 18:
        f1_pts = 30
    elif ppd_count >= 15:
        f1_pts = 25
    elif ppd_count >= 10:
        f1_pts = 18
    elif ppd_count >= 1:
        f1_pts = 10
    else:
        f1_pts = 5
    score += f1_pts
    factors.append({
        "name": "PPD Schedule Comprehensiveness",
        "pointsEarned": f1_pts,
        "pointsMax": 30,
        "yourPolicy": f"{ppd_count} conditions defined" if ppd_count > 0 else "No schedule",
        "benchmark": "≥18 IRDAI conditions"
    })

    # Factor 2: TTD Duration (25 pts)
    if not ttd_covered:
        f2_pts = 0
        ttd_dur_str = "Not covered"
    elif ttd_max_weeks >= 104:
        f2_pts = 25
        ttd_dur_str = f"{ttd_max_weeks} weeks"
    elif ttd_max_weeks >= 78:
        f2_pts = 20
        ttd_dur_str = f"{ttd_max_weeks} weeks"
    elif ttd_max_weeks >= 52:
        f2_pts = 15
        ttd_dur_str = f"{ttd_max_weeks} weeks"
    else:
        f2_pts = 10
        ttd_dur_str = f"{ttd_max_weeks} weeks"
    score += f2_pts
    factors.append({
        "name": "TTD Duration",
        "pointsEarned": f2_pts,
        "pointsMax": 25,
        "yourPolicy": ttd_dur_str,
        "benchmark": "≥104 weeks (2 years)"
    })

    # Factor 3: TTD Waiting Period (15 pts)
    if not ttd_covered:
        f3_pts = 0
        wait_str = "Not covered"
    elif ttd_waiting <= 7:
        f3_pts = 15
        wait_str = f"{ttd_waiting} days"
    elif ttd_waiting <= 14:
        f3_pts = 10
        wait_str = f"{ttd_waiting} days"
    else:
        f3_pts = 5
        wait_str = f"{ttd_waiting} days"
    score += f3_pts
    factors.append({
        "name": "TTD Waiting Period",
        "pointsEarned": f3_pts,
        "pointsMax": 15,
        "yourPolicy": wait_str,
        "benchmark": "≤7 days"
    })

    # Factor 4: Home/Vehicle Modification (15 pts)
    home_mod = additional.get("homeModification", {})
    vehicle_mod = additional.get("vehicleModification", {})
    home_covered = home_mod.get("covered", False) if isinstance(home_mod, dict) else False
    vehicle_covered = vehicle_mod.get("covered", False) if isinstance(vehicle_mod, dict) else False
    f4_pts = 0
    if home_covered:
        f4_pts += 8
    if vehicle_covered:
        f4_pts += 7
    mod_parts = []
    if home_covered:
        mod_parts.append("Home")
    if vehicle_covered:
        mod_parts.append("Vehicle")
    score += f4_pts
    factors.append({
        "name": "Home/Vehicle Modification",
        "pointsEarned": f4_pts,
        "pointsMax": 15,
        "yourPolicy": " + ".join(mod_parts) if mod_parts else "Not covered",
        "benchmark": "Both home & vehicle"
    })

    # Factor 5: Medical Expenses (15 pts)
    if not medical_covered:
        f5_pts = 0
        med_str = "Not covered"
    elif medical_pct >= 40:
        f5_pts = 15
        med_str = f"{medical_pct:.0f}% of SI"
    elif medical_pct >= 20:
        f5_pts = 12
        med_str = f"{medical_pct:.0f}% of SI"
    elif medical_pct >= 10:
        f5_pts = 8
        med_str = f"{medical_pct:.0f}% of SI"
    else:
        f5_pts = 5
        med_str = f"{medical_pct:.0f}% of SI" if medical_pct > 0 else "Covered (limit unknown)"
    score += f5_pts
    factors.append({
        "name": "Medical Expenses Coverage",
        "pointsEarned": f5_pts,
        "pointsMax": 15,
        "yourPolicy": med_str,
        "benchmark": "≥40% of SI"
    })

    score = min(100, max(0, score))
    label_info = _get_pa_score_label(score)

    return {
        "score": score,
        "label": label_info["label"],
        "color": label_info["color"],
        "name": "Disability Protection Depth",
        "icon": "accessible",
        "weight": "40%",
        "factors": factors
    }


def calculate_pa_scores_detailed(
    extracted_data: Dict[str, Any],
    category_data: Dict[str, Any],
    insurer_name: str = ""
) -> Dict[str, Any]:
    """
    Public entry point for PA insurance V10 2-score system.
    Returns complete protectionReadiness structure for policyAnalyzer.
    Composite = S1 (60%) + S2 (40%). No product split — all PA policies scored uniformly.
    """
    from datetime import datetime as _dt

    # Derive annual income: extracted from members → SI/10 → premium×500
    members = category_data.get("insuredMembers", [])
    annual_income = 0
    if isinstance(members, list) and members:
        first_member = members[0] if isinstance(members[0], dict) else {}
        ai = _pa_safe_numeric(first_member.get("annualIncome", 0))
        if ai > 0:
            annual_income = int(ai)
    if annual_income <= 0:
        _pa_si = _pa_safe_numeric(category_data.get("coverageDetails", {}).get("sumInsured", 0))
        _pa_prem = _pa_safe_numeric(category_data.get("premiumDetails", {}).get("basePremium", 0) or category_data.get("premiumDetails", {}).get("totalPremium", 0))
        _si_income = _pa_si / 10 if _pa_si > 0 else 0
        _prem_income = _pa_prem * 500 if _pa_prem > 0 else 0
        annual_income = int(max(_si_income, _prem_income))
    if annual_income <= 0:
        _pa_si_fallback = _pa_safe_numeric(category_data.get("coverageDetails", {}).get("sumInsured", 0))
        annual_income = int(_pa_si_fallback / 10) if _pa_si_fallback > 0 else 0

    s1 = calculate_pa_s1_income_replacement(category_data, annual_income)
    s2 = calculate_pa_s2_disability_protection(category_data)

    # Composite = S1 * 0.6 + S2 * 0.4
    composite = round(s1["score"] * 0.6 + s2["score"] * 0.4)
    composite = min(100, max(0, composite))

    # Verdict from PA_VERDICT_MAP
    verdict = {"label": "Needs Attention", "summary": "Critical gaps in accident protection.", "color": "#6B7280", "emoji": "alert"}
    for low, high, label, summary, color, emoji in PA_VERDICT_MAP:
        if low <= composite <= high:
            verdict = {"label": label, "summary": summary, "color": color, "emoji": emoji}
            break

    scores = {"s1": s1, "s2": s2}

    logger.info(f"🛡️ PA V10 Scores: S1={s1['score']}, S2={s2['score']}, Composite={composite} ({verdict['label']})")

    return {
        "compositeScore": composite,
        "verdict": verdict,
        "scores": scores,
        "analyzedAt": _dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }


def calculate_generic_protection_score(
    gaps: List[Dict[str, Any]],
    extracted_data: Dict[str, Any]
) -> Tuple[int, str]:
    """
    Generic protection score calculation for other policy types
    Based on gap count and severity
    """
    score = 100

    # Count gaps by severity
    high_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "high")
    medium_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "medium")
    low_severity_gaps = sum(1 for gap in gaps if gap.get("severity", "").lower() == "low")

    # Deduct points based on gap severity
    score -= high_severity_gaps * 12  # High severity: -12 points each
    score -= medium_severity_gaps * 6  # Medium severity: -6 points each
    score -= low_severity_gaps * 3     # Low severity: -3 points each

    # Ensure score is between 0 and 100
    score = max(0, min(100, score))

    # Determine label
    if score >= 90:
        label = "Excellent Coverage"
    elif score >= 75:
        label = "Good Coverage"
    elif score >= 60:
        label = "Fair Coverage"
    elif score >= 40:
        label = "Needs Improvement"
    else:
        label = "Critical Gaps"

    logger.info(f"📋 Generic Protection Score: {score}% ({label}) - Gaps: H:{high_severity_gaps} M:{medium_severity_gaps} L:{low_severity_gaps}")

    return score, label