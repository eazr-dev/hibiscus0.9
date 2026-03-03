"""Health Insurance UI Builder (EAZR_01 Spec)
Build Flutter UI-specific structure for health insurance policies.
Includes the main dispatcher that routes to type-specific builders.
"""
import logging
import re
from datetime import datetime, timedelta

from policy_analysis.utils import safe_num, get_score_label, lookup_csr

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy imports for other type-specific builders (may not exist yet)
# ---------------------------------------------------------------------------
def _import_motor_builder():
    from policy_analysis.types.motor.ui_builder import _build_motor_policy_details_ui
    return _build_motor_policy_details_ui


def _import_life_builder():
    from policy_analysis.types.life.ui_builder import build_life_policy_details_ui
    return build_life_policy_details_ui


def _import_pa_builder():
    from policy_analysis.types.pa.ui_builder import _build_pa_policy_details_ui
    return _build_pa_policy_details_ui


def _import_travel_builder():
    from policy_analysis.types.travel.ui_builder import _build_travel_policy_details_ui
    return _build_travel_policy_details_ui


# ============================================================================
# Main Dispatcher + Health-specific builder
# ============================================================================

def _build_policy_details_ui(
    extracted_data: dict,
    category_data: dict,
    policy_type: str = "",
    policy_status: str = "active",
    original_document_url: str = ""
) -> dict:
    """
    Build Flutter UI-specific structure for Policy Details Tab.
    Simplified, clean JSON format easy to integrate in frontend.
    """
    category_data = category_data or {}
    policy_type_lower = policy_type.lower() if policy_type else ""

    # Check if it's motor insurance - use separate builder
    if any(kw in policy_type_lower for kw in ["motor", "car", "vehicle", "auto", "two wheeler", "bike", "scooter", "truck"]):
        _build_motor_policy_details_ui = _import_motor_builder()
        return _build_motor_policy_details_ui(
            extracted_data=extracted_data,
            category_data=category_data,
            policy_type=policy_type,
            policy_status=policy_status
        )

    # Check if it's life insurance - use separate builder
    if any(kw in policy_type_lower for kw in ["life", "term", "endowment", "ulip", "whole life", "money back", "pension", "annuity", "jeevan", "child plan"]):
        _build_life_policy_details_ui = _import_life_builder()
        return _build_life_policy_details_ui(
            extracted_data=extracted_data,
            category_data=category_data,
            policy_type=policy_type,
            policy_status=policy_status
        )

    # Check if it's personal accident insurance - use separate builder (EAZR_04)
    if any(kw in policy_type_lower for kw in ["personal accident", "accidental", "accident", "pa "]) or policy_type_lower.strip() in ["pa", "p.a.", "p.a"]:
        _build_pa_policy_details_ui = _import_pa_builder()
        return _build_pa_policy_details_ui(
            extracted_data=extracted_data,
            category_data=category_data,
            policy_type=policy_type,
            policy_status=policy_status
        )

    # Check if it's travel insurance - use separate builder (EAZR_05)
    if any(kw in policy_type_lower for kw in ["travel", "overseas", "international travel"]):
        _build_travel_policy_details_ui = _import_travel_builder()
        return _build_travel_policy_details_ui(
            extracted_data=extracted_data,
            category_data=category_data,
            policy_type=policy_type,
            policy_status=policy_status
        )

    policy_identification = category_data.get("policyIdentification", {})
    coverage_details = category_data.get("coverageDetails", {})
    waiting_periods = category_data.get("waitingPeriods", {})
    policy_history = category_data.get("policyHistory", {})
    premium_breakdown = category_data.get("premiumBreakdown", {})
    no_claim_bonus = category_data.get("noClaimBonus", {})
    accumulated_benefits = category_data.get("accumulatedBenefits", {})
    sub_limits = category_data.get("subLimits", {})
    exclusions = category_data.get("exclusions", {})
    network_info = category_data.get("networkInfo", {})
    copay_details = category_data.get("copayDetails", {})
    declared_ped = category_data.get("declaredPed", {})
    benefits_data = category_data.get("benefits", {})

    insurer_name = extracted_data.get("insuranceProvider", "")
    policy_number = extracted_data.get("policyNumber", "")
    sum_insured = coverage_details.get("sumInsured") or extracted_data.get("coverageAmount", 0)

    # ==================== 1. EMERGENCY INFO ====================
    helpline_number = policy_identification.get("insurerTollFree") or "18004250005"
    emergency_info = {
        "policyNumber": policy_number,
        "helpline": helpline_number,
        "whatsappSupport": "+919876543210",
        "nearestHospitalAction": "find_hospital",
        "actions": [
            {"type": "copy", "label": "Policy Number", "value": policy_number, "icon": "content_copy"},
            {"type": "call", "label": "24/7 Helpline", "value": helpline_number, "icon": "phone"},
            {"type": "chat", "label": "WhatsApp Claims", "value": "+919876543210", "icon": "chat"},
            {"type": "navigate", "label": "Nearest Hospital", "value": "find_hospital", "icon": "location_on"}
        ]
    }

    # ==================== 2. POLICY OVERVIEW ====================
    # CSR lookup — centralized in policy_analysis/utils.py (single source of truth)
    csr_value = lookup_csr(insurer_name)
    if csr_value > 0:
        csr_data = {"csr": f"{csr_value}%", "year": "2024-25"}
    else:
        # Fallback: check if DeepSeek extracted it
        extracted_csr = category_data.get("claimInfo", {}).get("claimSettlementRatio")
        if extracted_csr:
            csr_data = {"csr": str(extracted_csr), "year": "2023-24"}
        else:
            csr_data = {"csr": "N/A", "year": ""}

    # Get insured members
    insured_members = category_data.get("insuredMembers", []) or []
    members_list = []
    for idx, member in enumerate(insured_members):
        name = member.get("memberName") or member.get("name", "")
        members_list.append({
            "id": f"member_{idx + 1}",
            "name": name,
            "relationship": member.get("memberRelationship") or member.get("relationship", "Self"),
            "age": member.get("memberAge") or member.get("age", 0),
            "gender": member.get("memberGender") or member.get("gender", ""),
            "avatar": f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=random"
        })

    # Calculate validity
    start_date = policy_identification.get("policyPeriodStart") or extracted_data.get("startDate", "")
    end_date = policy_identification.get("policyPeriodEnd") or extracted_data.get("endDate", "")
    days_remaining = 0
    progress_percent = 0

    if end_date:
        try:
            if "-" in str(end_date):
                parts = str(end_date).split("-")
                if len(parts[0]) == 4:
                    end_dt = datetime.strptime(str(end_date), "%Y-%m-%d")
                else:
                    end_dt = datetime.strptime(str(end_date), "%d-%m-%Y")
            else:
                end_dt = datetime.strptime(str(end_date), "%Y-%m-%d")

            days_remaining = max(0, (end_dt.date() - datetime.now().date()).days)

            if start_date:
                if "-" in str(start_date):
                    parts = str(start_date).split("-")
                    if len(parts[0]) == 4:
                        start_dt = datetime.strptime(str(start_date), "%Y-%m-%d")
                    else:
                        start_dt = datetime.strptime(str(start_date), "%d-%m-%Y")
                else:
                    start_dt = datetime.strptime(str(start_date), "%Y-%m-%d")

                total_days = (end_dt - start_dt).days
                days_elapsed = (datetime.now() - start_dt).days
                if total_days > 0:
                    progress_percent = max(0, min(100, int((days_elapsed / total_days) * 100)))
        except:
            pass

    # Accumulated benefits
    accumulated_ncb = accumulated_benefits.get("accumulatedNcbAmount") or 0
    accumulated_ncb = accumulated_benefits.get("accumulatedNcbAmount") or 0
    accumulated_inflation = accumulated_benefits.get("accumulatedInflationShield") or 0
    total_effective = accumulated_benefits.get("totalEffectiveCoverage") or sum_insured

    # Ensure numeric values
    try:
        sum_insured = float(sum_insured) if not isinstance(sum_insured, (int, float)) else sum_insured
    except:
        sum_insured = 0

    try:
        accumulated_ncb = float(accumulated_ncb) if not isinstance(accumulated_ncb, (int, float)) else accumulated_ncb
    except:
        accumulated_ncb = 0

    try:
        accumulated_inflation = float(accumulated_inflation) if not isinstance(accumulated_inflation, (int, float)) else accumulated_inflation
    except:
        accumulated_inflation = 0

    try:
        total_effective = float(total_effective) if not isinstance(total_effective, (int, float)) else total_effective
    except:
        total_effective = sum_insured

    policy_overview = {
        "insurer": {
            "name": insurer_name,
            "logo": f"https://logo.clearbit.com/{insurer_name.lower().replace(' ', '').replace(',', '')}.com",
            "claimSettlementRatio": csr_data["csr"],
            "claimSettlementYear": csr_data["year"]
        },
        "plan": {
            "name": policy_identification.get("productName") or extracted_data.get("productName") or "Health Insurance",
            "variant": policy_identification.get("policyType") or "Individual",
            "uin": policy_identification.get("uin") or extracted_data.get("uin", ""),
            "type": policy_identification.get("policyType") or "Individual"
        },
        "coverage": {
            "sumInsured": sum_insured,
            "sumInsuredFormatted": f"\u20b9{sum_insured:,.0f}",
            "accumulatedBonus": accumulated_ncb + accumulated_inflation,
            "accumulatedBonusFormatted": f"\u20b9{(accumulated_ncb + accumulated_inflation):,.0f}",
            "effectiveCoverage": total_effective,
            "effectiveCoverageFormatted": f"\u20b9{total_effective:,.0f}"
        },
        "validity": {
            "startDate": start_date,
            "endDate": end_date,
            "status": policy_status,
            "daysRemaining": days_remaining,
            "progressPercent": progress_percent
        },
        "members": members_list
    }

    # ==================== 3. COVERAGE DETAILS ====================
    # Hospitalization coverage list
    hospitalization = []

    # Sum Insured
    hospitalization.append({
        "id": "coverage_1",
        "label": "Sum Insured",
        "value": f"\u20b9{sum_insured:,.0f}",
        "benchmark": "Excellent" if sum_insured >= 1000000 else "Adequate",
        "status": "excellent" if sum_insured >= 1000000 else "adequate"
    })

    # Room Rent
    room_rent = coverage_details.get("roomRentLimit", "No limit")
    if "no limit" in str(room_rent).lower():
        hospitalization.append({
            "id": "coverage_2",
            "label": "Room Rent",
            "value": "No Limit",
            "benchmark": "Best in class",
            "status": "excellent"
        })
    else:
        hospitalization.append({
            "id": "coverage_2",
            "label": "Room Rent",
            "value": str(room_rent),
            "benchmark": "Industry: \u20b95,000-10,000/day",
            "status": "basic"
        })

    # ICU
    icu = coverage_details.get("icuLimit", "No limit")
    hospitalization.append({
        "id": "coverage_3",
        "label": "ICU Charges",
        "value": str(icu),
        "benchmark": "Best in class" if "no limit" in str(icu).lower() else "Industry standard",
        "status": "excellent" if "no limit" in str(icu).lower() else "adequate"
    })

    # Pre-Hospitalization
    pre_hosp = coverage_details.get("preHospitalization", "30 days")
    hospitalization.append({
        "id": "coverage_4",
        "label": "Pre-Hospitalization",
        "value": str(pre_hosp),
        "benchmark": "Industry: 30 days",
        "status": "better" if "60" in str(pre_hosp) else "adequate"
    })

    # Post-Hospitalization
    post_hosp = coverage_details.get("postHospitalization", "90 days")
    hospitalization.append({
        "id": "coverage_5",
        "label": "Post-Hospitalization",
        "value": str(post_hosp),
        "benchmark": "Industry: 60-90 days",
        "status": "better" if any(x in str(post_hosp) for x in ["120", "180", "15%"]) else "adequate"
    })

    # Ambulance
    ambulance = coverage_details.get("ambulanceCover", "\u20b93,000")
    hospitalization.append({
        "id": "coverage_6",
        "label": "Ambulance",
        "value": str(ambulance),
        "benchmark": "Industry: \u20b92,000-5,000",
        "status": "excellent" if "no limit" in str(ambulance).lower() else "adequate"
    })

    # Benefits list
    benefits = []

    if coverage_details.get("dayCareProcedures"):
        benefits.append({
            "id": "benefit_1",
            "name": "Day Care Procedures",
            "value": "540+ Covered",
            "icon": "medical_services",
            "covered": True
        })

    if coverage_details.get("domiciliaryHospitalization"):
        benefits.append({
            "id": "benefit_2",
            "name": "Domiciliary Hospitalization",
            "value": "Up to Sum Insured",
            "icon": "home",
            "covered": True
        })

    if coverage_details.get("healthCheckup"):
        benefits.append({
            "id": "benefit_3",
            "name": "Health Checkup",
            "value": str(coverage_details.get("healthCheckup", "Once per year")),
            "icon": "health_and_safety",
            "covered": True
        })

    if coverage_details.get("ayushTreatment"):
        benefits.append({
            "id": "benefit_4",
            "name": "AYUSH Treatment",
            "value": "Up to Sum Insured",
            "icon": "spa",
            "covered": True
        })

    if coverage_details.get("organDonor"):
        benefits.append({
            "id": "benefit_5",
            "name": "Organ Donor Cover",
            "value": "Up to Sum Insured",
            "icon": "favorite",
            "covered": True
        })

    if coverage_details.get("modernTreatment"):
        benefits.append({
            "id": "benefit_6",
            "name": "Modern Treatment",
            "value": "Covered",
            "icon": "biotech",
            "covered": True
        })

    # Mental Health Coverage (mandatory per Mental Healthcare Act 2017)
    mental_health_covered = benefits_data.get("mentalHealthCovered", False)
    benefits.append({
        "id": "benefit_7",
        "name": "Mental Illness Coverage",
        "value": "Covered" if mental_health_covered else "Not Specified",
        "icon": "psychology",
        "covered": bool(mental_health_covered),
        "regulatory": "Mandatory per Mental Healthcare Act 2017"
    })

    # Consumables Coverage
    consumables_covered = coverage_details.get("consumablesCoverage", False)
    consumables_details_str = coverage_details.get("consumablesCoverageDetails", "")
    # Also check add-on premiums for "waiver of non-payable" or "consumable"
    if not consumables_covered:
        add_ons_check = premium_breakdown.get("addOnPremiums", {})
        other_add_ons_check = add_ons_check.get("otherAddOns", {}) if isinstance(add_ons_check, dict) else {}
        for addon_name in (other_add_ons_check if isinstance(other_add_ons_check, dict) else {}):
            if any(kw in addon_name.lower() for kw in ["consumable", "non-payable", "non payable", "waiver of non"]):
                consumables_covered = True
                consumables_details_str = addon_name
                break

    benefits.append({
        "id": "benefit_8",
        "name": "Consumables Coverage",
        "value": consumables_details_str if consumables_details_str else ("Covered" if consumables_covered else "Not Covered"),
        "icon": "build",
        "covered": bool(consumables_covered),
        "impact": "Consumables = 10-15% of hospital bill. Critical gap if not covered."
    })

    # Restoration
    restoration_info = coverage_details.get("restoration")
    if isinstance(restoration_info, dict):
        restoration_available = restoration_info.get("available", False)
        restoration_type = restoration_info.get("type") or ""
    else:
        restoration_available = bool(restoration_info)
        restoration_type = coverage_details.get("restorationAmount") or ""

    restoration_desc = f"Sum Insured restores {restoration_type.lower()} after exhaustion during policy year"
    if "unlimited" in str(restoration_type).lower():
        restoration_desc = "Sum Insured restores unlimited times after exhaustion during policy year"
        restoration_highlight = "Best in class feature"
    elif "100%" in str(restoration_type):
        restoration_desc = "100% of Sum Insured restores once after exhaustion during policy year"
        restoration_highlight = "Good feature"
    else:
        restoration_highlight = ""

    # NCB
    ncb_available = no_claim_bonus.get("available") if isinstance(no_claim_bonus, dict) else no_claim_bonus
    ncb_desc = "Not available in this policy"
    if accumulated_ncb > 0:
        ncb_desc = f"\u20b9{(accumulated_ncb + accumulated_inflation):,.0f} (Inflation Shield)"
    elif ncb_available:
        ncb_desc = f"{no_claim_bonus.get('percentage', '10%')} per claim-free year"

    # Determine sum insured type
    policy_type_val = policy_identification.get("policyType", "")
    sum_insured_type = "floater" if "floater" in str(policy_type_val).lower() else "individual"

    coverage_details_section = {
        "sumInsuredType": sum_insured_type,
        "hospitalization": hospitalization,
        "benefits": benefits,
        "restoration": {
            "available": restoration_available,
            "type": str(restoration_type),
            "description": restoration_desc,
            "highlight": restoration_highlight if restoration_highlight else None
        },
        "noClaimBonus": {
            "available": bool(ncb_available),
            "description": ncb_desc
        }
    }

    # ==================== 4. WAITING PERIODS ====================
    initial_waiting = waiting_periods.get("initialWaitingPeriod", "30 days")
    ped_waiting = waiting_periods.get("preExistingDiseaseWaiting", "36 months")
    specific_waiting = waiting_periods.get("specificDiseaseWaiting", "24 months")
    specific_diseases = waiting_periods.get("specificDiseasesList", [])
    maternity_waiting = waiting_periods.get("maternityWaiting")

    # Helper: parse date safely
    def parse_date_safe(date_str):
        if not date_str:
            return None
        try:
            date_str = str(date_str).strip()[:10]
            if "-" in date_str:
                parts = date_str.split("-")
                if len(parts[0]) == 4:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    return datetime.strptime(date_str, "%d-%m-%Y")
        except:
            pass
        return None

    def extract_period_months(period_str):
        match = re.search(r'(\d+)\s*month', str(period_str), re.IGNORECASE)
        return int(match.group(1)) if match else 0

    def extract_period_days(period_str):
        match = re.search(r'(\d+)\s*day', str(period_str), re.IGNORECASE)
        return int(match.group(1)) if match else 0

    enrollment_date = parse_date_safe(
        policy_history.get("firstEnrollmentDate") or
        policy_history.get("insuredSinceDate") or
        start_date
    )
    now = datetime.now()
    years_covered = 0
    if enrollment_date:
        years_covered = (now - enrollment_date).days // 365

    def get_waiting_status_detailed(period_str, enrollment_dt, period_type="days"):
        period_str_lower = str(period_str).lower()
        if any(kw in period_str_lower for kw in ["no waiting", "nil", "day 1", "covered from day 1", "not applicable"]):
            return {"status": "completed", "color": "green", "completion_date": None, "days_remaining": 0, "months_remaining": 0}

        if not enrollment_dt:
            return {"status": "active", "color": "orange", "completion_date": None, "days_remaining": None, "months_remaining": None}

        if period_type == "months":
            months = extract_period_months(period_str)
            if months > 0:
                completion = enrollment_dt + timedelta(days=months * 30)
                if now >= completion:
                    return {"status": "completed", "color": "green", "completion_date": completion.strftime("%Y-%m-%d"), "days_remaining": 0, "months_remaining": 0}
                else:
                    remaining_days = (completion - now).days
                    return {"status": "in_progress", "color": "orange", "completion_date": completion.strftime("%Y-%m-%d"), "days_remaining": remaining_days, "months_remaining": remaining_days // 30}
        else:
            days = extract_period_days(period_str)
            if days > 0:
                completion = enrollment_dt + timedelta(days=days)
                if now >= completion:
                    return {"status": "completed", "color": "green", "completion_date": completion.strftime("%Y-%m-%d"), "days_remaining": 0, "months_remaining": 0}
                else:
                    remaining = (completion - now).days
                    return {"status": "in_progress", "color": "orange", "completion_date": completion.strftime("%Y-%m-%d"), "days_remaining": remaining, "months_remaining": remaining // 30}

        return {"status": "active", "color": "orange", "completion_date": None, "days_remaining": None, "months_remaining": None}

    periods_list = []

    # 1. Initial waiting period
    initial_detail = get_waiting_status_detailed(initial_waiting, enrollment_date, "days")
    periods_list.append({
        "id": "waiting_1",
        "type": "Initial Waiting Period",
        "period": str(initial_waiting),
        "status": initial_detail["status"],
        "completion_date": initial_detail["completion_date"],
        "days_remaining": initial_detail["days_remaining"],
        "description": "All illnesses covered from Day 1. No 30-day waiting." if initial_detail["status"] == "completed" else f"Standard {initial_waiting} waiting before illness coverage begins.",
        "icon": "schedule",
        "color": initial_detail["color"]
    })

    # 2. PED waiting period
    ped_detail = get_waiting_status_detailed(ped_waiting, enrollment_date, "months")

    # Build per-disease PED list
    declared_conditions = declared_ped.get("declaredConditions", [])
    ped_list = []
    for ped_item in declared_conditions:
        if isinstance(ped_item, str):
            ped_name = ped_item
        elif isinstance(ped_item, dict):
            ped_name = ped_item.get("diseaseName") or ped_item.get("condition") or str(ped_item)
        else:
            ped_name = str(ped_item)
        ped_list.append({
            "disease_name": ped_name,
            "waiting_months": extract_period_months(ped_waiting),
            "status": ped_detail["status"],
            "completion_date": ped_detail["completion_date"],
            "months_remaining": ped_detail["months_remaining"]
        })

    ped_desc = "Pre-existing conditions covered from Day 1" if ped_detail["status"] == "completed" else f"Pre-existing conditions covered after {ped_waiting}"
    if enrollment_date and years_covered > 0:
        ped_desc += f". Enrolled since {enrollment_date.strftime('%d-%b-%Y')} ({years_covered} years)"

    periods_list.append({
        "id": "waiting_2",
        "type": "Pre-Existing Disease (PED)",
        "period": str(ped_waiting),
        "status": ped_detail["status"],
        "completion_date": ped_detail["completion_date"],
        "days_remaining": ped_detail["days_remaining"],
        "months_remaining": ped_detail["months_remaining"],
        "description": ped_desc,
        "icon": "medical_information",
        "color": ped_detail["color"],
        "enrollmentDate": enrollment_date.strftime("%Y-%m-%d") if enrollment_date else None,
        "yearsCovered": years_covered,
        "pedList": ped_list
    })

    # 3. Specific diseases waiting
    specific_detail = get_waiting_status_detailed(specific_waiting, enrollment_date, "months")
    specific_desc = "Hernia, kidney stones, joint replacement covered from Day 1" if specific_detail["status"] == "completed" else f"Specific diseases covered after {specific_waiting}"

    periods_list.append({
        "id": "waiting_3",
        "type": "Specific Diseases",
        "period": str(specific_waiting),
        "status": specific_detail["status"],
        "completion_date": specific_detail["completion_date"],
        "days_remaining": specific_detail["days_remaining"],
        "months_remaining": specific_detail["months_remaining"],
        "description": specific_desc,
        "icon": "healing",
        "color": specific_detail["color"],
        "diseases": specific_diseases
    })

    # 4. Maternity waiting (spec requires it)
    if maternity_waiting:
        maternity_detail = get_waiting_status_detailed(maternity_waiting, enrollment_date, "months")
        periods_list.append({
            "id": "waiting_4",
            "type": "Maternity Waiting Period",
            "period": str(maternity_waiting),
            "status": maternity_detail["status"],
            "completion_date": maternity_detail["completion_date"],
            "days_remaining": maternity_detail["days_remaining"],
            "months_remaining": maternity_detail["months_remaining"],
            "description": f"Maternity covered after {maternity_waiting}" if maternity_detail["status"] != "completed" else "Maternity waiting period completed",
            "icon": "pregnant_woman",
            "color": maternity_detail["color"]
        })

    # Build visual timeline
    timeline_events = []
    if enrollment_date:
        timeline_events.append({
            "type": "start",
            "date": enrollment_date.strftime("%Y-%m-%d"),
            "label": "Policy Start / Enrollment"
        })
    for period in periods_list:
        if period.get("completion_date"):
            timeline_events.append({
                "type": "completion",
                "date": period["completion_date"],
                "label": f"{period['type']} Completes",
                "status": period["status"]
            })
    timeline_events.sort(key=lambda x: x.get("date", ""))

    waiting_periods_section = {
        "summary": {
            "overallStatus": "Excellent" if all(p["status"] == "completed" for p in periods_list) else ("Good" if any(p["status"] == "completed" for p in periods_list) else "Active"),
            "totalWaitingPeriods": len(periods_list),
            "completed": sum(1 for p in periods_list if p["status"] == "completed"),
            "inProgress": sum(1 for p in periods_list if p["status"] == "in_progress"),
            "color": "green" if all(p["status"] == "completed" for p in periods_list) else "orange"
        },
        "timeline": timeline_events,
        "periods": periods_list
    }

    # ==================== 5. CO-PAYMENTS & LIMITS ====================
    sub_limits_list = []

    def extract_amount(limit_str):
        """Extract numeric amount from limit string"""
        match = re.search(r'[\d,]+', str(limit_str))
        if match:
            return int(match.group().replace(',', ''))
        return 0

    if sub_limits.get("cataractLimit"):
        cataract_amount = extract_amount(sub_limits.get("cataractLimit", ""))
        sub_limits_list.append({
            "id": "limit_1",
            "procedure": "Cataract",
            "limit": str(sub_limits.get("cataractLimit")),
            "benchmark": "Industry: \u20b925,000-50,000",
            "status": "adequate",
            "color": "green"
        })

    if sub_limits.get("jointReplacementLimit"):
        joint_amount = extract_amount(sub_limits.get("jointReplacementLimit", ""))
        sub_limits_list.append({
            "id": "limit_2",
            "procedure": "Joint Replacement",
            "limit": str(sub_limits.get("jointReplacementLimit")),
            "benchmark": "Industry: \u20b91,50,000-3,00,000",
            "status": "adequate" if joint_amount >= 200000 else "basic",
            "color": "green" if joint_amount >= 200000 else "orange",
            "note": "May not cover premium implants" if joint_amount < 300000 else None
        })

    if sub_limits.get("internalProsthesisLimit"):
        prosthesis_amount = extract_amount(sub_limits.get("internalProsthesisLimit", ""))
        sub_limits_list.append({
            "id": "limit_3",
            "procedure": "Internal Prosthesis",
            "limit": str(sub_limits.get("internalProsthesisLimit")),
            "benchmark": "Industry: \u20b91,00,000-3,00,000",
            "status": "adequate" if prosthesis_amount >= 100000 else "basic",
            "color": "green" if prosthesis_amount >= 100000 else "orange",
            "note": "Pacemaker/stent may have partial coverage"
        })

    if sub_limits.get("kidneyStoneLimit"):
        sub_limits_list.append({
            "id": "limit_4",
            "procedure": "Kidney Stone",
            "limit": str(sub_limits.get("kidneyStoneLimit")),
            "benchmark": "Industry: \u20b940,000-80,000",
            "status": "adequate",
            "color": "green"
        })

    if sub_limits.get("gallStoneLimit"):
        sub_limits_list.append({
            "id": "limit_5",
            "procedure": "Gall Stone",
            "limit": str(sub_limits.get("gallStoneLimit")),
            "benchmark": "Industry: \u20b940,000-80,000",
            "status": "adequate",
            "color": "green"
        })

    # Age-based copay
    age_copay_data = copay_details.get("ageBasedCopay", [])
    has_age_copay = len(age_copay_data) > 0
    age_copay_list = []
    for item in age_copay_data:
        if isinstance(item, dict):
            copay_pct = item.get("copayPercentage") or item.get("copay_percentage") or 0
            try:
                copay_pct = float(copay_pct)
            except:
                copay_pct = 0
            age_copay_list.append({
                "ageBracket": item.get("ageBracket") or item.get("age_bracket", ""),
                "copayPercentage": copay_pct,
                "status": "concern" if copay_pct > 20 else ("acceptable" if copay_pct > 0 else "optimal")
            })

    # Disease-specific copay
    disease_copay_data = copay_details.get("diseaseSpecificCopay", [])
    disease_copay_list = []
    for item in disease_copay_data:
        if isinstance(item, dict):
            disease_copay_list.append({
                "disease": item.get("disease", ""),
                "copayPercentage": item.get("copayPercentage") or item.get("copay_percentage", 0)
            })

    # Proportionate deduction example calculation
    room_rent_raw = coverage_details.get("roomRentLimit", "No limit")
    proportionate_deduction = None
    if "no limit" not in str(room_rent_raw).lower() and "no capping" not in str(room_rent_raw).lower():
        room_limit_amount = extract_amount(str(room_rent_raw))
        if room_limit_amount > 0:
            actual_room = 15000  # typical metro rate
            if room_limit_amount < actual_room:
                deduction_ratio = round(room_limit_amount / actual_room, 2)
                sample_claim = 500000
                payable = int(sample_claim * deduction_ratio)
                proportionate_deduction = {
                    "description": "If room rent exceeds limit, ENTIRE claim is reduced proportionately",
                    "example": {
                        "roomLimit": room_limit_amount,
                        "actualRoom": actual_room,
                        "totalClaim": sample_claim,
                        "deductionRatio": deduction_ratio,
                        "payable": payable,
                        "outOfPocket": sample_claim - payable
                    },
                    "warning": f"For a \u20b9{sample_claim:,} claim, you could pay \u20b9{sample_claim - payable:,} out-of-pocket due to room rent proportionate deduction"
                }

    copay_limits_section = {
        "hasAgeBasedCopay": has_age_copay,
        "ageBasedCopay": age_copay_list,
        "hasDiseaseSpecificCopay": len(disease_copay_list) > 0,
        "diseaseSpecificCopay": disease_copay_list,
        "generalCopay": copay_details.get("generalCopay", "0%"),
        "hasSubLimits": len(sub_limits_list) > 0,
        "subLimits": sub_limits_list,
        "proportionateDeduction": proportionate_deduction
    }

    # ==================== 6. HOSPITAL NETWORK ====================
    tpa_name = policy_identification.get("tpaName") or ""
    network_type = network_info.get("networkType") or "Pan India"
    pre_auth_raw = network_info.get("preAuthTurnaround")
    if isinstance(pre_auth_raw, str) and pre_auth_raw:
        pre_auth_turnaround = {"planned": pre_auth_raw, "emergency": "1 hour"}
    elif isinstance(pre_auth_raw, dict):
        pre_auth_turnaround = pre_auth_raw
    else:
        pre_auth_turnaround = {"planned": "4-6 hours", "emergency": "30 minutes - 1 hour"}

    hospital_network = {
        "summary": {
            "totalHospitals": network_info.get("networkHospitalsCount") or "14,000+",
            "cashlessAvailable": network_info.get("cashlessFacility", True),
            "networkType": network_type,
            "panIndia": network_type == "Pan India",
            "tpaName": tpa_name,
            "preAuthTurnaround": pre_auth_turnaround
        },
        "topCities": [
            {
                "city": "Mumbai",
                "count": "2,500+",
                "hospitals": ["Fortis", "Apollo", "Lilavati", "Nanavati"]
            },
            {
                "city": "Delhi NCR",
                "count": "3,000+",
                "hospitals": ["Apollo", "Max", "Fortis", "Medanta"]
            },
            {
                "city": "Bangalore",
                "count": "1,800+",
                "hospitals": ["Apollo", "Fortis", "Manipal", "Narayana"]
            },
            {
                "city": "Chennai",
                "count": "1,500+",
                "hospitals": ["Apollo", "Fortis Malar", "MIOT", "SIMS"]
            },
            {
                "city": "Kolkata",
                "count": "1,200+",
                "hospitals": ["Apollo", "Medica", "Fortis", "BM Birla"]
            }
        ],
        "findAction": {
            "label": "Find Network Hospitals",
            "action": "open_map",
            "icon": "map"
        }
    }

    # ==================== 7. EXCLUSIONS ====================
    permanent_exclusions = exclusions.get("permanentExclusions", [])
    conditional_exclusions = exclusions.get("conditionalExclusions", [])
    ped_specific_exclusions = exclusions.get("pedSpecificExclusions", [])

    if not permanent_exclusions:
        permanent_exclusions = [
            "Self-inflicted injury or suicide attempt",
            "Participation in criminal activities",
            "War, nuclear risks or bioterrorism",
            "Cosmetic procedures for beautification",
            "Dental treatment unless due to accident",
            "Hearing aids and spectacles",
            "Expenses incurred outside India",
            "HIV/AIDS related conditions",
            "Drug or alcohol abuse related treatments",
            "Congenital external diseases"
        ]

    # Derive PED-specific exclusions from declared PED if not explicitly extracted
    if not ped_specific_exclusions:
        declared_conditions = declared_ped.get("declaredConditions", [])
        if declared_conditions:
            ped_waiting_str = waiting_periods.get("preExistingDiseaseWaiting", "36 months")
            for condition in declared_conditions:
                cond_name = condition if isinstance(condition, str) else (condition.get("diseaseName") or condition.get("condition") or str(condition))
                ped_specific_exclusions.append(
                    f"{cond_name} - claims excluded during {ped_waiting_str} waiting period"
                )

    exclusions_section = {
        "permanent": permanent_exclusions,
        "conditional": conditional_exclusions,
        "pedSpecific": ped_specific_exclusions,
        "collapsed": True
    }

    # ==================== 8. PREMIUM & TAX ====================
    base_premium = premium_breakdown.get("basePremium", 0)
    gst_amount = premium_breakdown.get("gst", 0)
    total_premium = premium_breakdown.get("totalPremium", 0)
    premium_frequency = premium_breakdown.get("premiumFrequency", "Annual")

    # Safe conversion for premium amounts
    if base_premium is None or base_premium == "":
        base_premium = 0
    try:
        base_premium = float(base_premium) if not isinstance(base_premium, (int, float)) else base_premium
    except:
        base_premium = 0

    if gst_amount is None or gst_amount == "":
        gst_amount = 0
    try:
        gst_amount = float(gst_amount) if not isinstance(gst_amount, (int, float)) else gst_amount
    except:
        gst_amount = 0

    if total_premium is None or total_premium == "":
        total_premium = 0
    try:
        total_premium = float(total_premium) if not isinstance(total_premium, (int, float)) else total_premium
    except:
        total_premium = 0

    # Build add-ons list
    add_on_premiums = []
    add_ons = premium_breakdown.get("addOnPremiums", {})
    other_add_ons = add_ons.get("otherAddOns", {}) if isinstance(add_ons, dict) else {}

    # Check for redundant add-ons
    initial_waiver_premium = other_add_ons.get("Initial waiting period waiver", 0)
    specific_illness_premium = other_add_ons.get("Reduction in Specific illness waiting period", 0)

    for add_on_name, premium in other_add_ons.items():
        note = ""
        # Safe conversion for premium
        if premium is None or premium == "":
            premium = 0
        try:
            premium = float(premium) if not isinstance(premium, (int, float)) else premium
        except:
            premium = 0

        if "waiting period waiver" in add_on_name.lower() and "no waiting" in str(initial_waiting).lower():
            note = "Redundant - policy has no waiting period"
        elif "specific illness" in add_on_name.lower() and "no waiting" in str(specific_waiting).lower():
            note = "Redundant - policy has no waiting period"
        elif "inflation protect" in add_on_name.lower() and accumulated_inflation > 0:
            note = f"Excellent - accumulated \u20b9{accumulated_inflation:,.0f} already"
        elif "restore si" in add_on_name.lower() and "unlimited" in str(restoration_type).lower():
            note = "Good - works with unlimited restoration"
        elif "medically necessary" in add_on_name.lower():
            note = "Recommended - keep"
        elif "waiver of non-payable" in add_on_name.lower():
            note = "Excellent - covers non-medical costs"
        elif "health check-up" in add_on_name.lower():
            note = "Good - free checkup for family"
        elif "doctor on call" in add_on_name.lower():
            note = "Optional - rarely used"

        add_on_premiums.append({
            "name": add_on_name.replace("_", " ").title(),
            "premium": premium,
            "premiumFormatted": f"\u20b9{premium:,.0f}",
            "note": note
        })

    # Calculate per month
    per_month = total_premium / 12 if total_premium > 0 else 0

    # Tax benefit calculation
    can_claim_80d = min(total_premium, 25000) if total_premium > 0 else 0

    # Check if any member is 60+
    has_senior = any(m.get("age", 0) >= 60 for m in members_list)
    parents_max_limit = 50000 if has_senior else 25000

    premium_tax_section = {
        "premium": {
            "basePremium": base_premium,
            "basePremiumFormatted": f"\u20b9{base_premium:,.0f}",
            "gst": gst_amount,
            "gstFormatted": f"\u20b9{gst_amount:,.0f}",
            "totalPremium": total_premium,
            "totalPremiumFormatted": f"\u20b9{total_premium:,.0f}",
            "frequency": premium_frequency,
            "perMonth": per_month,
            "perMonthFormatted": f"\u20b9{per_month:,.0f}/month",
            "addOns": add_on_premiums,
            "gracePeriod": {
                "days": int(re.search(r'(\d+)', str(premium_breakdown.get("gracePeriod", "30"))).group(1)) if re.search(r'(\d+)', str(premium_breakdown.get("gracePeriod", "30"))) else 30,
                "description": f"Premium can be paid within {premium_breakdown.get('gracePeriod', '30 days')} after due date without policy lapsing"
            }
        },
        "paymentHistory": {
            "records": [],
            "schema": {
                "date": "string (YYYY-MM-DD)",
                "amount": "number",
                "mode": "string (online/cheque/cash/auto-debit)",
                "transactionId": "string",
                "status": "string (success/pending/failed)"
            },
            "note": "Payment history will be populated when transaction data is available"
        },
        "taxBenefit": {
            "section80D": {
                "selfAndFamily": {
                    "maxLimit": 25000,
                    "premiumPaid": total_premium,
                    "canClaim": can_claim_80d,
                    "description": "For self, spouse & dependent children (< 60 years)",
                    "status": "eligible"
                },
                "parents": {
                    "maxLimit": parents_max_limit,
                    "premiumPaid": 0,
                    "canClaim": 0,
                    "description": f"For parents (< 60 years: \u20b925K, \u2265 60 years: \u20b950K)",
                    "status": "not_claimed",
                    "note": "Add parents to policy or buy separate policy" if parents_max_limit == 25000 else "Parents eligible for higher deduction"
                },
                "totalDeduction": {
                    "maxLimit": 50000 if not has_senior else 75000,
                    "youCanClaim": can_claim_80d,
                    "description": "Total tax deduction under Section 80D",
                    "note": f"Save \u20b9{int(can_claim_80d * 0.3):,} in taxes (if in 30% slab)" if can_claim_80d > 0 else "No tax benefit available"
                }
            }
        },
        "renewalAlerts": {
            "nextRenewalDate": end_date,
            "daysUntilRenewal": days_remaining,
            "recommendedActions": []
        }
    }

    # Add renewal recommendations
    redundant_add_ons = []
    redundant_savings = 0

    # Safe conversion for waiver premiums
    if initial_waiver_premium is None or initial_waiver_premium == "":
        initial_waiver_premium = 0
    try:
        initial_waiver_premium = float(initial_waiver_premium) if not isinstance(initial_waiver_premium, (int, float)) else initial_waiver_premium
    except:
        initial_waiver_premium = 0

    if specific_illness_premium is None or specific_illness_premium == "":
        specific_illness_premium = 0
    try:
        specific_illness_premium = float(specific_illness_premium) if not isinstance(specific_illness_premium, (int, float)) else specific_illness_premium
    except:
        specific_illness_premium = 0

    if initial_waiver_premium > 0:
        redundant_add_ons.append(f"Initial Waiting Period Waiver (\u20b9{initial_waiver_premium:,.0f})")
        redundant_savings += initial_waiver_premium
    if specific_illness_premium > 0:
        redundant_add_ons.append(f"Reduction in Specific Illness Waiting Period (\u20b9{specific_illness_premium:,.0f})")
        redundant_savings += specific_illness_premium

    if redundant_add_ons:
        premium_tax_section["renewalAlerts"]["recommendedActions"].append({
            "priority": "high",
            "action": "Drop redundant add-ons",
            "savings": f"\u20b9{redundant_savings:,.0f}/year",
            "addons": redundant_add_ons
        })

    # Coverage upgrade recommendation
    if sum_insured < 15000000:  # Less than 15L
        premium_tax_section["renewalAlerts"]["recommendedActions"].append({
            "priority": "medium",
            "action": "Consider upgrading Sum Insured",
            "current": f"\u20b9{sum_insured:,.0f}",
            "recommended": "\u20b915,00,000",
            "extraPremium": "~\u20b93,000/year"
        })

    # ==================== BUILD FINAL STRUCTURE ====================
    return {
        "emergencyInfo": emergency_info,
        "policyOverview": policy_overview,
        "coverageDetails": coverage_details_section,
        "waitingPeriods": waiting_periods_section,
        "copayLimits": copay_limits_section,
        "hospitalNetwork": hospital_network,
        "exclusions": exclusions_section,
        "premiumTax": premium_tax_section
    }


# ============================================================================
# Description Helper Functions
# ============================================================================

def get_restoration_description(restoration_type: str) -> str:
    """Get user-friendly description of restoration benefit"""
    restoration_str = str(restoration_type).lower()
    if "unlimited" in restoration_str:
        return "Unlimited restoration of Sum Insured during policy year"
    elif "100%" in restoration_str:
        return "100% of Sum Insured restored once after exhaustion"
    else:
        return f"Restoration benefit: {restoration_type}"


def get_initial_waiting_description(initial_waiting: str) -> str:
    """Get user-friendly description of initial waiting period"""
    initial_str = str(initial_waiting).lower()
    if "no waiting" in initial_str or "nil" in initial_str:
        return "Excellent! Coverage starts from Day 1 for all illnesses"
    elif "30 day" in initial_str:
        return "Standard 30-day waiting period. Only accidents covered initially."
    else:
        return f"{initial_waiting} waiting period before illness coverage begins."


def get_ped_description(ped_waiting: str, first_enrollment: str = None) -> str:
    """Get user-friendly description of PED waiting period"""
    ped_str = str(ped_waiting).lower()
    if "no waiting" in ped_str or "nil" in ped_str:
        return "Excellent! Pre-existing conditions covered from Day 1"
    elif first_enrollment:
        return f"Pre-existing conditions covered after {ped_waiting}. Check completion date based on enrollment: {first_enrollment}"
    else:
        return f"Pre-existing conditions covered after {ped_waiting} of continuous coverage."


def calculate_ped_status(first_enrollment: str, ped_waiting: str) -> str:
    """Calculate PED waiting period status"""
    if not first_enrollment:
        return "Active"

    try:
        enroll_date = datetime.strptime(str(first_enrollment)[:10], "%Y-%m-%d")
        months_required = int(''.join(filter(str.isdigit, str(ped_waiting)[:3])))
        months_elapsed = (datetime.now() - enroll_date).days // 30

        if months_elapsed >= months_required:
            return "Completed"
        else:
            return f"{months_required - months_elapsed} months remaining"
    except:
        return "Active"


def get_specific_disease_description(specific_waiting: str, diseases: list) -> str:
    """Get user-friendly description of specific disease waiting"""
    if "no waiting" in str(specific_waiting).lower():
        return "Excellent! No waiting period for specific diseases"
    elif diseases:
        return f"{len(diseases)} conditions require {specific_waiting} waiting period"
    else:
        return f"Specific diseases covered after {specific_waiting}"
