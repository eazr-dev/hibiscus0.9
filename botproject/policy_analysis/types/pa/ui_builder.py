"""
Personal Accident Insurance UI Builder (EAZR_04)
Build Flutter UI-specific structure for PA insurance policies.
"""
import logging
import re
from datetime import datetime, timedelta

from policy_analysis.utils import safe_num, get_score_label
from policy_analysis.types.pa.helpers import (
    _calculate_pa_income_replacement_score,
    _calculate_pa_disability_protection_score,
    _simulate_pa_scenarios,
    _analyze_pa_gaps,
    _generate_pa_recommendations,
)

logger = logging.getLogger(__name__)


def _build_pa_policy_details_ui(
    extracted_data: dict,
    category_data: dict,
    policy_type: str = "",
    policy_status: str = "active"
) -> dict:
    """
    Build Flutter UI-specific structure for Personal Accident Insurance Policy.
    Full implementation per EAZR_04_Personal_Accident.md specification.
    Includes: Emergency Info, Policy Overview, Coverage Details (5 cards),
    Additional Benefits, Exclusions, Premium, Scoring (2 scores), 4 Scenarios,
    Gap Analysis (6 rules), Recommendations, IPF Integration.
    """
    category_data = category_data or {}

    # Extract structured sections from category_data
    policy_basics = category_data.get("policyBasics", category_data.get("policyIdentification", {}))
    coverage_details = category_data.get("coverageDetails", {})
    additional_benefits_data = category_data.get("additionalBenefits", {})
    exclusions_data = category_data.get("exclusions", {})
    premium_details = category_data.get("premiumDetails", {})
    insured_members = category_data.get("insuredMembers", [])
    nomination = category_data.get("nomination", {})
    claims_info = category_data.get("claimsInfo", {})
    contact_info = category_data.get("contactInfo", {})

    sum_insured = safe_num(coverage_details.get("sumInsured"), 0)
    insurer_name = policy_basics.get("insurerName") or extracted_data.get("insuranceProvider") or "Unknown Insurer"
    product_name = policy_basics.get("productName") or "Personal Accident Insurance"
    policy_number = policy_basics.get("policyNumber") or extracted_data.get("policyNumber") or ""
    policy_sub_type = policy_basics.get("policySubType") or "IND_PA"

    # PA Insurer helpline lookup
    pa_helpline_map = {
        "icici lombard": "1800-266-9725",
        "bajaj allianz": "1800-209-5858",
        "hdfc ergo": "1800-266-0700",
        "tata aig": "1800-266-7780",
        "new india": "1800-209-1415",
        "united india": "1800-425-1552",
        "national insurance": "1800-345-0330",
        "oriental insurance": "1800-118-485",
        "sbi general": "1800-102-1111",
        "star health": "1800-425-2255",
        "care health": "1800-102-4488",
        "reliance general": "1800-102-4088",
        "future generali": "1800-220-233",
        "go digit": "1800-258-4242",
        "chola ms": "1800-200-5544"
    }
    insurer_lower = insurer_name.lower() if insurer_name else ""
    claims_helpline = claims_info.get("claimsHelpline") or ""
    if not claims_helpline:
        for key, val in pa_helpline_map.items():
            if key in insurer_lower:
                claims_helpline = val
                break

    # Sub-type configuration
    subtype_config = {
        "IND_PA": {"label": "Individual PA", "color": "#3B82F6", "icon": "person"},
        "FAM_PA": {"label": "Family PA", "color": "#8B5CF6", "icon": "family_restroom"},
        "GRP_PA": {"label": "Group PA", "color": "#10B981", "icon": "groups"},
        "PA_MED": {"label": "PA with Medical", "color": "#F59E0B", "icon": "medical_services"},
        "STU_PA": {"label": "Student PA", "color": "#6366F1", "icon": "school"}
    }
    st_config = subtype_config.get(policy_sub_type, subtype_config["IND_PA"])

    # ==================== 1. EMERGENCY INFO ====================
    emergency_info = {
        "policyNumber": policy_number,
        "policyNumberCopyable": True,
        "claimsHelpline": claims_helpline,
        "claimsHelplineCallable": True,
        "claimsEmail": claims_info.get("claimsEmail") or "",
        "policyStatus": policy_status or "active",
        "policyStatusColor": "#22C55E" if policy_status == "active" else "#EF4444"
    }

    # ==================== 2. POLICY OVERVIEW ====================
    start_date = policy_basics.get("policyStartDate") or extracted_data.get("startDate") or ""
    end_date = policy_basics.get("policyEndDate") or extracted_data.get("endDate") or ""
    members_count = len(insured_members) if insured_members else 1

    policy_overview = {
        "insurerName": insurer_name,
        "productName": product_name,
        "subType": {
            "code": policy_sub_type,
            "label": st_config["label"],
            "color": st_config["color"],
            "icon": st_config["icon"]
        },
        "principalSumInsured": sum_insured,
        "principalSumInsuredFormatted": f"₹{sum_insured:,.0f}",
        "policyValidity": {
            "startDate": start_date,
            "endDate": end_date
        },
        "membersCovered": members_count,
        "insuredMembers": insured_members,
        "groupDetails": {
            "groupPolicyholder": policy_basics.get("groupPolicyholderName"),
            "groupPolicyNumber": policy_basics.get("groupPolicyNumber")
        } if policy_sub_type == "GRP_PA" else None,
        "nomination": {
            "nomineeName": nomination.get("nomineeName"),
            "nomineeRelationship": nomination.get("nomineeRelationship"),
            "nomineeShare": nomination.get("nomineeShare")
        }
    }

    # ==================== 3. COVERAGE DETAILS (5 Cards) ====================
    ad = coverage_details.get("accidentalDeath", {})
    ptd = coverage_details.get("permanentTotalDisability", {})
    ppd = coverage_details.get("permanentPartialDisability", {})
    ttd = coverage_details.get("temporaryTotalDisability", {})
    medical = coverage_details.get("medicalExpenses", {})

    ad_benefit = safe_num(ad.get("benefitAmount"), sum_insured)
    ptd_benefit = safe_num(ptd.get("benefitAmount"), sum_insured)
    ttd_benefit = safe_num(ttd.get("benefitAmount"), 0)
    if ttd_benefit == 0 and ttd.get("covered") and sum_insured > 0:
        pct = safe_num(ttd.get("benefitPercentage"), 1)
        ttd_benefit = sum_insured * pct / 100

    # Build PPD schedule with calculated amounts
    ppd_schedule = ppd.get("schedule", [])
    ppd_schedule_with_amounts = []
    for item in ppd_schedule:
        pct = item.get("percentage", 0)
        amount = sum_insured * pct / 100
        ppd_schedule_with_amounts.append({
            "disability": item.get("disability", ""),
            "percentage": pct,
            "benefitAmount": amount,
            "benefitFormatted": f"₹{amount:,.0f}"
        })

    # Medical expense limit calculation
    medical_limit = safe_num(medical.get("limitAmount"), 0)
    if medical_limit == 0 and medical.get("covered") and medical.get("limitType") == "percentage_of_si":
        medical_limit = sum_insured * safe_num(medical.get("limitPercentage"), 10) / 100

    coverage_section = {
        "accidentalDeath": {
            "covered": True,
            "benefitPercentage": ad.get("benefitPercentage", 100),
            "benefitAmount": ad_benefit,
            "benefitFormatted": f"₹{ad_benefit:,.0f}",
            "description": f"{ad.get('benefitPercentage', 100)}% of Sum Insured",
            "doubleIndemnity": {
                "applicable": ad.get("doubleIndemnity", {}).get("applicable", False),
                "conditions": ad.get("doubleIndemnity", {}).get("conditions", ""),
                "doubleAmount": ad_benefit * 2 if ad.get("doubleIndemnity", {}).get("applicable") else 0,
                "doubleFormatted": f"₹{ad_benefit * 2:,.0f}" if ad.get("doubleIndemnity", {}).get("applicable") else ""
            }
        },
        "permanentTotalDisability": {
            "covered": ptd.get("covered", False),
            "benefitPercentage": ptd.get("benefitPercentage", 100),
            "benefitAmount": ptd_benefit,
            "benefitFormatted": f"₹{ptd_benefit:,.0f}",
            "description": f"{ptd.get('benefitPercentage', 100)}% of Sum Insured",
            "conditionsList": ptd.get("conditionsList", [])
        },
        "permanentPartialDisability": {
            "covered": ppd.get("covered", False),
            "benefitType": "As per IRDAI schedule",
            "scheduleCount": len(ppd_schedule),
            "schedule": ppd_schedule_with_amounts,
            "note": "Multiple disabilities can be claimed up to 100% total"
        },
        "temporaryTotalDisability": {
            "covered": ttd.get("covered", False),
            "benefitType": ttd.get("benefitType", "weekly"),
            "benefitAmount": ttd_benefit,
            "benefitFormatted": f"₹{ttd_benefit:,.0f}/{ttd.get('benefitType', 'week')}",
            "maximumWeeks": ttd.get("maximumWeeks", 52),
            "waitingPeriodDays": ttd.get("waitingPeriodDays", 7),
            "exampleCalculations": [
                {"duration": "2 weeks", "benefit": ttd_benefit * 1, "formatted": f"₹{ttd_benefit * 1:,.0f}", "note": "Week 2 only (Week 1 is waiting)"},
                {"duration": "4 weeks", "benefit": ttd_benefit * 3, "formatted": f"₹{ttd_benefit * 3:,.0f}", "note": "Weeks 2-4"},
                {"duration": "3 months", "benefit": ttd_benefit * 12, "formatted": f"₹{ttd_benefit * 12:,.0f}", "note": "Weeks 2-13"},
                {"duration": "6 months", "benefit": ttd_benefit * 25, "formatted": f"₹{ttd_benefit * 25:,.0f}", "note": "Weeks 2-26"},
                {"duration": "1 year", "benefit": ttd_benefit * min(51, ttd.get("maximumWeeks", 52) - 1), "formatted": f"₹{ttd_benefit * min(51, ttd.get('maximumWeeks', 52) - 1):,.0f}", "note": f"Weeks 2-{min(52, ttd.get('maximumWeeks', 52))}"}
            ] if ttd.get("covered") else []
        },
        "medicalExpenses": {
            "covered": medical.get("covered", False),
            "limitType": medical.get("limitType", "percentage_of_si"),
            "limitPercentage": medical.get("limitPercentage", 0),
            "limitAmount": medical_limit,
            "limitFormatted": f"₹{medical_limit:,.0f}" if medical_limit > 0 else f"{medical.get('limitPercentage', 0)}% of SI",
            "perAccidentOrAnnual": medical.get("perAccidentOrAnnual", "per_accident")
        }
    }

    # ==================== 4. ADDITIONAL BENEFITS ====================
    additional_benefits_section = {
        "benefits": []
    }
    benefit_labels = {
        "educationBenefit": {"label": "Education Benefit", "icon": "school", "description": "Education continuation for dependent children"},
        "loanEmiCover": {"label": "Loan EMI Cover", "icon": "account_balance", "description": "EMI payment during disability period"},
        "ambulanceCharges": {"label": "Ambulance Charges", "icon": "local_hospital", "description": "Emergency ambulance transportation"},
        "transportationOfMortalRemains": {"label": "Transport of Mortal Remains", "icon": "flight", "description": "Transportation of mortal remains"},
        "funeralExpenses": {"label": "Funeral Expenses", "icon": "church", "description": "Funeral and cremation expenses"},
        "homeModification": {"label": "Home Modification", "icon": "home", "description": "Home accessibility modifications for PTD"},
        "vehicleModification": {"label": "Vehicle Modification", "icon": "directions_car", "description": "Vehicle accessibility modifications for PTD"},
        "carriageOfAttendant": {"label": "Carriage of Attendant", "icon": "person", "description": "Travel expenses for an attendant"}
    }
    for key, meta in benefit_labels.items():
        benefit_data = additional_benefits_data.get(key, {})
        covered = benefit_data.get("covered", False) if isinstance(benefit_data, dict) else bool(benefit_data)
        limit = 0
        if isinstance(benefit_data, dict):
            limit = safe_num(benefit_data.get("limit") or benefit_data.get("benefitAmount") or benefit_data.get("maxAmountPerMonth", 0), 0)
        additional_benefits_section["benefits"].append({
            "key": key,
            "label": meta["label"],
            "icon": meta["icon"],
            "description": meta["description"],
            "covered": covered,
            "limit": limit,
            "limitFormatted": f"₹{limit:,.0f}" if limit > 0 else ("Included" if covered else "Not covered"),
            "statusColor": "#22C55E" if covered else "#9CA3AF"
        })

    # ==================== 5. EXCLUSIONS ====================
    exclusions_section = {
        "standardExclusions": exclusions_data.get("standardExclusions", []),
        "waitingPeriods": {
            "initialWaiting": {"days": exclusions_data.get("waitingPeriods", {}).get("initialWaiting", 0), "note": "PA covers accidents from Day 1"},
            "ttdWaiting": {"days": exclusions_data.get("waitingPeriods", {}).get("ttdWaiting", 7), "note": "TTD benefit starts after elimination period"}
        },
        "ageLimits": exclusions_data.get("ageLimits", {}),
        "occupationRestrictions": exclusions_data.get("occupationRestrictions", [])
    }

    # ==================== 6. PREMIUM DETAILS ====================
    base_premium = safe_num(premium_details.get("basePremium"), 0)
    gst_amount = safe_num(premium_details.get("gstAmount") or premium_details.get("gst"), 0)
    total_premium = safe_num(premium_details.get("totalPremium"), 0)
    if total_premium == 0 and base_premium > 0:
        gst_amount = base_premium * 0.18
        total_premium = base_premium + gst_amount

    premium_section = {
        "basePremium": base_premium,
        "basePremiumFormatted": f"₹{base_premium:,.0f}",
        "gstAmount": gst_amount,
        "gstFormatted": f"₹{gst_amount:,.0f}",
        "totalPremium": total_premium,
        "totalPremiumFormatted": f"₹{total_premium:,.0f}",
        "premiumFrequency": premium_details.get("premiumFrequency", "annual"),
        "premiumFactors": premium_details.get("premiumFactors", {}),
        "renewalDate": end_date
    }

    # ==================== 7. SCORING ENGINE (2 Scores) ====================
    annual_income = 1000000  # Default assumed income
    s1 = _calculate_pa_income_replacement_score(coverage_details, additional_benefits_data, annual_income)
    s2 = _calculate_pa_disability_protection_score(coverage_details, additional_benefits_data)
    overall_score = round(s1["score"] * 0.6 + s2["score"] * 0.4)
    overall_label = get_score_label(overall_score)

    scoring_engine = {
        "overallScore": overall_score,
        "overallLabel": overall_label["label"],
        "overallColor": overall_label["color"],
        "scores": [
            {
                "name": "Income Replacement Adequacy",
                "weight": "60%",
                "score": s1["score"],
                "label": get_score_label(s1["score"])["label"],
                "color": get_score_label(s1["score"])["color"],
                "factors": s1["factors"]
            },
            {
                "name": "Disability Protection Depth",
                "weight": "40%",
                "score": s2["score"],
                "label": get_score_label(s2["score"])["label"],
                "color": get_score_label(s2["score"])["color"],
                "factors": s2["factors"]
            }
        ]
    }

    # ==================== 8. SCENARIO SIMULATIONS (4 Scenarios) ====================
    # Inject insured members for age/dependents derivation in scenarios
    _sc_coverage = dict(coverage_details)
    _sc_coverage["_insuredMembers"] = category_data.get("insuredMembers", [])
    scenarios = _simulate_pa_scenarios(_sc_coverage, additional_benefits_data, sum_insured, annual_income)

    # ==================== 9. GAP ANALYSIS (6 Rules) ====================
    gaps = _analyze_pa_gaps(coverage_details, additional_benefits_data, annual_income)
    gap_analysis = {
        "totalGaps": len(gaps),
        "highSeverity": len([g for g in gaps if g["severity"] == "high"]),
        "mediumSeverity": len([g for g in gaps if g["severity"] == "medium"]),
        "lowSeverity": len([g for g in gaps if g["severity"] == "low"]),
        "gaps": gaps
    }

    # ==================== 10. RECOMMENDATIONS ====================
    recommendations = _generate_pa_recommendations(gaps, coverage_details, additional_benefits_data, policy_sub_type=policy_sub_type)
    recommendations_section = {
        "totalRecommendations": len(recommendations),
        "recommendations": recommendations
    }

    # ==================== 11. IPF INTEGRATION ====================
    ipf_section = None
    if total_premium >= 5000:
        emi_3 = round(total_premium / 3)
        emi_6 = round(total_premium / 6)
        ipf_section = {
            "eligible": True,
            "totalPremium": total_premium,
            "totalPremiumFormatted": f"₹{total_premium:,.0f}",
            "options": [
                {"tenure": 3, "emiAmount": emi_3, "emiFormatted": f"₹{emi_3:,.0f}/month"},
                {"tenure": 6, "emiAmount": emi_6, "emiFormatted": f"₹{emi_6:,.0f}/month"}
            ],
            "cta": "Pay in easy EMIs with EAZR"
        }

    # ==================== RETURN STRUCTURE ====================
    return {
        "emergencyInfo": emergency_info,
        "policyOverview": policy_overview,
        "coverageDetails": coverage_section,
        "additionalBenefits": additional_benefits_section,
        "exclusions": exclusions_section,
        "premiumDetails": premium_section,
        "scoringEngine": scoring_engine,
        "scenarioSimulations": scenarios,
        "gapAnalysis": gap_analysis,
        "recommendations": recommendations_section,
        "ipfIntegration": ipf_section
    }
