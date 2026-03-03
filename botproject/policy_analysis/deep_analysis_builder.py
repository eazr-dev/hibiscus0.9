"""
Deep Analysis Builder for EAZR Policy Intelligence Report V4.0
Builds category-specific deep analysis sections based on policy type templates.

Extracted from routers/policy_upload.py to reduce monolith size.
"""
import logging
import re
from datetime import datetime

from policy_analysis.utils import get_score_label, safe_num, get_insurer_logo_url
from policy_analysis.types.pa.helpers import (
    _calculate_pa_income_replacement_score,
    _calculate_pa_disability_protection_score,
    _analyze_pa_gaps,
    _generate_pa_recommendations,
)
from policy_analysis.types.travel.helpers import _parse_travel_cover_amount

logger = logging.getLogger(__name__)


def build_deep_analysis(policy_type: str, extracted_data: dict, category_data: dict,
                         formatted_gaps: list, protection_score: int, protection_score_label: str,
                         key_benefits: list, exclusions_list: list, waiting_periods_list: list,
                         user_name: str, user_age: int, user_gender: str) -> dict:
    """
    Build comprehensive deep analysis based on EAZR Policy Intelligence Report V4.0 templates.
    Returns category-specific analysis sections.
    """
    analysis = {
        "reportVersion": "4.0",
        "analysisType": policy_type.upper() if policy_type else "GENERAL",
        "sections": []
    }

    # Common helper functions
    def create_section(section_id: str, title: str, subtitle: str, display_order: int, content: dict) -> dict:
        return {
            "sectionId": section_id,
            "sectionTitle": title,
            "sectionSubtitle": subtitle,
            "displayOrder": display_order,
            "content": content
        }

    def calculate_coverage_adequacy(coverage_amount: int, annual_income: int = 500000) -> dict:
        """Calculate coverage adequacy based on standard financial planning principles"""
        recommended_min = annual_income * 10
        recommended_max = annual_income * 15
        gap = max(0, recommended_min - coverage_amount)
        adequacy_score = min(10, int((coverage_amount / recommended_min) * 10)) if recommended_min > 0 else 5

        if coverage_amount >= recommended_max:
            level = "Excellent"
        elif coverage_amount >= recommended_min:
            level = "Adequate"
        elif coverage_amount >= recommended_min * 0.7:
            level = "Building"
        else:
            level = "Needs Attention"

        return {
            "coverageAmount": coverage_amount,
            "recommendedMinimum": recommended_min,
            "recommendedMaximum": recommended_max,
            "coverageGap": gap,
            "adequacyScore": adequacy_score,
            "adequacyLevel": level
        }

    # Get common data - safely convert to numeric
    coverage_amount_raw = extracted_data.get("coverageAmount", 0) or 0
    premium_raw = extracted_data.get("premium", 0) or 0

    try:
        coverage_amount = int(float(str(coverage_amount_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if coverage_amount_raw else 0
    except (ValueError, TypeError):
        coverage_amount = 0

    try:
        premium = int(float(str(premium_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if premium_raw else 0
    except (ValueError, TypeError):
        premium = 0

    start_date = extracted_data.get("startDate", "")
    end_date = extracted_data.get("endDate", "")

    # ==================== LIFE INSURANCE ANALYSIS ====================
    if "life" in policy_type or "term" in policy_type or "endowment" in policy_type or "ulip" in policy_type:
        # Section 1: Your Protection at a Glance
        sum_assured_raw = category_data.get("coverageDetails", {}).get("sumAssured") or coverage_amount
        bonus_accumulated_raw = category_data.get("bonusValue", {}).get("accruedBonus") or 0

        # Convert to numeric (handle string values)
        try:
            sum_assured = int(float(str(sum_assured_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if sum_assured_raw else 0
        except (ValueError, TypeError):
            sum_assured = 0

        try:
            bonus_accumulated = int(float(str(bonus_accumulated_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if bonus_accumulated_raw else 0
        except (ValueError, TypeError):
            bonus_accumulated = 0

        rider_benefits = 0
        riders = category_data.get("riders", [])
        if isinstance(riders, list):
            for rider in riders:
                if isinstance(rider, dict):
                    rider_raw = rider.get("sumAssured", 0) or 0
                    try:
                        rider_benefits += int(float(str(rider_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if rider_raw else 0
                    except (ValueError, TypeError):
                        pass

        net_death_benefit = sum_assured + bonus_accumulated + rider_benefits
        coverage_adequacy = calculate_coverage_adequacy(sum_assured)

        analysis["sections"].append(create_section(
            "protection_at_glance",
            "Your Protection at a Glance",
            "What your policy provides and how it compares to what your family would need",
            1,
            {
                "protectionSummary": {
                    "title": "Policy Protection Summary",
                    "items": [
                        {"label": "Sum Assured", "value": sum_assured, "description": "The guaranteed amount your nominee receives"},
                        {"label": "Bonus Accumulated", "value": bonus_accumulated, "description": "Additional amount built up over time"},
                        {"label": "Rider Benefits", "value": rider_benefits, "description": "Extra protection for accidents, illness, etc."},
                        {"label": "Net Death Benefit", "value": net_death_benefit, "description": "Total amount payable to your family", "highlight": True}
                    ]
                },
                "protectionAdequacy": {
                    "title": "Protection Adequacy",
                    "description": "Based on standard financial planning principles (10-15x annual income)",
                    "currentCover": sum_assured,
                    "recommendedCover": f"{coverage_adequacy['recommendedMinimum']} - {coverage_adequacy['recommendedMaximum']}",
                    "coverageGap": coverage_adequacy["coverageGap"],
                    "protectionLevel": coverage_adequacy["adequacyScore"],
                    "protectionStatus": coverage_adequacy["adequacyLevel"]
                }
            }
        ))

        # Section 2: Policy Reliability
        policy_age_years = 0
        if start_date:
            try:
                start = datetime.strptime(start_date.split("T")[0], "%Y-%m-%d")
                policy_age_years = (datetime.now() - start).days // 365
            except:
                pass

        contestability_complete = policy_age_years >= 2
        nomination_status = "Valid" if category_data.get("nomination", {}).get("nominees") else "Needs update"
        policy_assignment = category_data.get("policyIdentification", {}).get("hypothecation") or "None"

        analysis["sections"].append(create_section(
            "policy_reliability",
            "Policy Reliability",
            "Factors that determine how smoothly a claim would be processed",
            2,
            {
                "claimReadinessStatus": {
                    "title": "Claim Readiness Status",
                    "factors": [
                        {
                            "factor": "Contestability Period",
                            "status": "Complete" if contestability_complete else f"{24 - (policy_age_years * 12)} months remaining",
                            "impact": "Clear for claims" if contestability_complete else "Subject to verification"
                        },
                        {
                            "factor": "Premium Status",
                            "status": "Current",
                            "impact": "Policy active"
                        },
                        {
                            "factor": "Nomination",
                            "status": nomination_status,
                            "impact": "Smooth settlement" if nomination_status == "Valid" else "Potential delays"
                        },
                        {
                            "factor": "Policy Assignment",
                            "status": policy_assignment if policy_assignment != "None" else "None",
                            "impact": "Full benefit to nominee" if policy_assignment == "None" else "Bank paid first"
                        }
                    ]
                },
                "policyAgeYears": policy_age_years,
                "contestabilityComplete": contestability_complete
            }
        ))

        # Section 3: Value Assessment
        policy_term = category_data.get("coverageDetails", {}).get("policyTerm")
        premium_frequency = extracted_data.get("premiumFrequency", "annually")
        annual_premium = premium
        if premium_frequency == "monthly":
            annual_premium = premium * 12
        elif premium_frequency == "quarterly":
            annual_premium = premium * 4
        elif premium_frequency == "half-yearly":
            annual_premium = premium * 2

        premium_per_lakh = (annual_premium / (sum_assured / 100000)) if sum_assured > 0 else 0

        analysis["sections"].append(create_section(
            "value_assessment",
            "Value Assessment",
            "Is this policy giving you good value for what you're paying?",
            3,
            {
                "termInsuranceMetrics": {
                    "title": "For Term Insurance",
                    "metrics": [
                        {"metric": "Premium per Rs. 1 Lakh Cover", "yourPolicy": f"Rs. {int(premium_per_lakh)}/year", "marketBenchmark": "Rs. 500-800/year"},
                        {"metric": "Cost Efficiency", "yourPolicy": "Good" if premium_per_lakh < 800 else "Average" if premium_per_lakh < 1200 else "Review recommended"}
                    ]
                },
                "annualPremium": annual_premium,
                "premiumPerLakh": premium_per_lakh
            }
        ))

        # Section 4: What Needs Your Attention
        gaps_identified = []
        # Income Protection Gap
        if coverage_adequacy["coverageGap"] > 0:
            gaps_identified.append({
                "gap": "Income Protection",
                "currentStatus": f"{int(sum_assured / 500000)}x annual income covered" if sum_assured > 0 else "Not covered",
                "recommendation": f"Consider additional Rs. {coverage_adequacy['coverageGap']} term cover" if coverage_adequacy["coverageGap"] > 0 else "Adequate"
            })

        # Critical Illness
        has_ci = any("critical" in str(r).lower() or "ci" in str(r).lower() for r in riders) if riders else False
        gaps_identified.append({
            "gap": "Critical Illness",
            "currentStatus": "Covered" if has_ci else "Not covered",
            "recommendation": "Protected" if has_ci else "Consider CI rider"
        })

        # Add gaps from analysis
        for gap in formatted_gaps[:3]:
            if isinstance(gap, dict):
                gaps_identified.append({
                    "gap": gap.get("category", "Coverage Gap"),
                    "currentStatus": gap.get("severity", "medium").capitalize(),
                    "recommendation": gap.get("recommendation", "Review recommended")
                })

        analysis["sections"].append(create_section(
            "attention_needed",
            "What Needs Your Attention",
            "Areas that may benefit from review",
            4,
            {
                "coverageGapsIdentified": {
                    "title": "Coverage Gaps Identified",
                    "gaps": gaps_identified
                }
            }
        ))

        # Section 5: Recommended Actions
        actions = []
        action_priority = 1
        for gap in formatted_gaps[:3]:
            if isinstance(gap, dict):
                actions.append({
                    "priority": action_priority,
                    "action": gap.get("recommendation", "Review coverage"),
                    "timeline": "At renewal" if gap.get("severity") != "high" else "Immediate",
                    "urgency": "Critical" if gap.get("severity") == "high" else "High" if gap.get("severity") == "medium" else "Medium"
                })
                action_priority += 1

        analysis["sections"].append(create_section(
            "recommended_actions",
            "Recommended Actions",
            "Prioritized steps to strengthen your protection",
            5,
            {
                "actions": actions,
                "eazrServices": {
                    "title": "EAZR Can Help",
                    "services": [
                        {"service": "Premium Financing (IPF)", "eligibility": "Eligible" if annual_premium > 50000 else "Not eligible", "benefit": f"Convert Rs. {annual_premium} annual premium to EMI"},
                        {"service": "Surrender Value Loan (SVF)", "eligibility": "Eligible" if policy_age_years >= 3 else "Not eligible", "benefit": "Access funds without surrendering policy"}
                    ]
                }
            }
        ))

        # Section 6: Assessment
        if protection_score >= 80:
            assessment_status = "WELL PROTECTED"
        elif protection_score >= 60:
            assessment_status = "ADEQUATELY COVERED"
        else:
            assessment_status = "ACTION RECOMMENDED"

        analysis["sections"].append(create_section(
            "assessment",
            "Assessment",
            assessment_status,
            6,
            {
                "status": assessment_status,
                "keyFinding": f"Your coverage is {int(sum_assured / 500000)}x income. {'Contestability is clear and policy is well-maintained.' if contestability_complete else 'Policy is within contestability period.'}",
                "recommendedAction": gaps_identified[0]["recommendation"] if gaps_identified else "Continue current coverage and review annually."
            }
        ))

    # ==================== HEALTH INSURANCE ANALYSIS ====================
    elif "health" in policy_type or "mediclaim" in policy_type or "medical" in policy_type:
        # Safely convert to numeric values
        sum_insured_raw = category_data.get("coverageDetails", {}).get("sumInsured") or coverage_amount
        cumulative_bonus_raw = category_data.get("premiumNcb", {}).get("ncbPercentage") or 0

        # Convert to numeric (handle string values)
        try:
            sum_insured = int(float(str(sum_insured_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if sum_insured_raw else 0
        except (ValueError, TypeError):
            sum_insured = 0

        try:
            cumulative_bonus = float(str(cumulative_bonus_raw).replace('%', '').strip()) if cumulative_bonus_raw else 0
        except (ValueError, TypeError):
            cumulative_bonus = 0

        effective_coverage = sum_insured * (1 + cumulative_bonus / 100) if sum_insured > 0 else 0
        restoration = category_data.get("coverageDetails", {}).get("restoration")
        room_rent_limit = category_data.get("coverageDetails", {}).get("roomRentLimit") or "Not specified"

        # Section 1: Coverage Overview
        insured_members = category_data.get("insuredMembers", [])
        if not insured_members:
            insured_members = [{"name": user_name, "age": user_age, "waitingPeriodStatus": "Check policy document"}]

        analysis["sections"].append(create_section(
            "coverage_overview",
            "Coverage Overview",
            "What your policy actually covers when you need hospitalization",
            1,
            {
                "coverageSummary": {
                    "title": "Your Coverage Summary",
                    "items": [
                        {"component": "Base Sum Insured", "value": f"Rs. {sum_insured:,}"},
                        {"component": "Cumulative Bonus", "value": f"Rs. {int(sum_insured * cumulative_bonus / 100):,} ({cumulative_bonus}%)" if cumulative_bonus else "Not accumulated yet"},
                        {"component": "Effective Coverage", "value": f"Rs. {int(effective_coverage):,}"},
                        {"component": "Restoration Benefit", "value": "Available - 100%" if restoration else "Not available"},
                        {"component": "Room Category", "value": str(room_rent_limit)}
                    ]
                },
                "familyMembersCovered": {
                    "title": "Family Members Covered",
                    "members": insured_members
                }
            }
        ))

        # Section 2: What You Actually Pay in a Claim
        room_rent_daily = 5000  # Default assumption
        if isinstance(room_rent_limit, str):
            match = re.search(r'(\d+,?\d*)', room_rent_limit.replace(',', ''))
            if match:
                room_rent_daily = int(match.group(1))

        co_payment_raw = category_data.get("coverageDetails", {}).get("coPayment") or 0
        deductible_raw = category_data.get("coverageDetails", {}).get("deductible") or 0

        # Convert to numeric (handle string values)
        try:
            co_payment = float(str(co_payment_raw).replace('%', '').replace(',', '').strip()) if co_payment_raw else 0
        except (ValueError, TypeError):
            co_payment = 0

        try:
            deductible = float(str(deductible_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip()) if deductible_raw else 0
        except (ValueError, TypeError):
            deductible = 0

        # Example calculation for Rs. 5 lakh bill
        example_bill = 500000
        room_adjustment = min(50000, example_bill * 0.1)  # Estimate 10% room adjustment
        co_pay_amount = example_bill * co_payment / 100 if co_payment else 0
        non_payable = example_bill * 0.05  # Estimate 5% non-payable
        insurer_pays = example_bill - room_adjustment - co_pay_amount - deductible - non_payable
        you_pay = example_bill - insurer_pays

        analysis["sections"].append(create_section(
            "out_of_pocket",
            "What You Actually Pay in a Claim",
            "Health insurance rarely pays 100% of your hospital bill",
            2,
            {
                "outOfPocketBreakdown": {
                    "title": f"If hospitalized with Rs. {example_bill:,} bill",
                    "items": [
                        {"item": "Hospital Bill", "amount": example_bill},
                        {"item": "(-) Room Rent Adjustment", "amount": -room_adjustment, "note": "if room exceeds limit"},
                        {"item": f"(-) Co-payment ({co_payment}%)", "amount": -co_pay_amount},
                        {"item": "(-) Deductible", "amount": -deductible},
                        {"item": "(-) Non-payable Items", "amount": -non_payable, "note": "consumables, etc."},
                        {"item": "Insurer Pays", "amount": insurer_pays, "highlight": True},
                        {"item": "You Pay from Pocket", "amount": you_pay, "highlight": True, "warning": you_pay > 50000}
                    ]
                },
                "roomRentImpact": {
                    "title": "Room Rent Impact",
                    "description": f"Your policy has a Rs. {room_rent_daily}/day room limit. If you choose a higher room, proportionate deduction applies to ALL charges.",
                    "warning": room_rent_daily < 10000
                }
            }
        ))

        # Section 3: Waiting Periods & Exclusions
        waiting_period_status = []
        initial_waiting = category_data.get("waitingPeriods", {}).get("initialWaitingPeriod") or "30 days"
        ped_waiting = category_data.get("waitingPeriods", {}).get("preExistingDiseaseWaiting") or "48 months"
        specific_waiting = category_data.get("waitingPeriods", {}).get("specificDiseaseWaiting") or "24 months"
        maternity_waiting = category_data.get("waitingPeriods", {}).get("maternityWaiting")

        # Calculate if waiting periods are complete based on policy start date
        policy_months = 0
        if start_date:
            try:
                start = datetime.strptime(start_date.split("T")[0], "%Y-%m-%d")
                policy_months = (datetime.now() - start).days // 30
            except:
                pass

        waiting_period_status = [
            {"condition": "General Illnesses", "waitingPeriod": "30 days", "status": "Complete ✓" if policy_months > 1 else "Active"},
            {"condition": "Pre-existing Diseases", "waitingPeriod": ped_waiting, "status": "Complete ✓" if policy_months > 48 else f"{48 - policy_months} months left"},
            {"condition": "Specific Diseases", "waitingPeriod": specific_waiting, "status": "Complete ✓" if policy_months > 24 else f"{24 - policy_months} months left"}
        ]
        if maternity_waiting:
            waiting_period_status.append({"condition": "Maternity", "waitingPeriod": maternity_waiting, "status": "Check policy"})

        analysis["sections"].append(create_section(
            "waiting_periods_exclusions",
            "Waiting Periods & Exclusions",
            "Conditions that affect when and what you can claim",
            3,
            {
                "waitingPeriodStatus": {
                    "title": "Current Waiting Period Status",
                    "periods": waiting_period_status
                },
                "exclusions": {
                    "title": "Policy Exclusions",
                    "permanentExclusions": category_data.get("exclusions", {}).get("permanentExclusions") or exclusions_list[:5],
                    "conditionalExclusions": category_data.get("exclusions", {}).get("conditionalExclusions") or []
                }
            }
        ))

        # Section 4: Major Illness Preparedness
        critical_scenarios = [
            {"scenario": "Heart Surgery (CABG)", "typicalCost": "Rs. 4-8 Lakhs", "yourCoverage": f"Rs. {sum_insured:,}", "gap": "Covered" if sum_insured >= 800000 else f"Gap: Rs. {800000 - sum_insured:,}"},
            {"scenario": "Cancer Treatment (over 2 years)", "typicalCost": "Rs. 15-30 Lakhs", "yourCoverage": f"Rs. {sum_insured:,}", "gap": "Covered" if sum_insured >= 1500000 else f"Gap: Rs. {1500000 - sum_insured:,}"},
            {"scenario": "Kidney Transplant", "typicalCost": "Rs. 8-15 Lakhs", "yourCoverage": f"Rs. {sum_insured:,}", "gap": "Covered" if sum_insured >= 800000 else f"Gap: Rs. {800000 - sum_insured:,}"},
            {"scenario": "Major Accident (ICU + Surgery)", "typicalCost": "Rs. 10-20 Lakhs", "yourCoverage": f"Rs. {sum_insured:,}", "gap": "Covered" if sum_insured >= 1000000 else f"Gap: Rs. {1000000 - sum_insured:,}"}
        ]

        analysis["sections"].append(create_section(
            "major_illness_preparedness",
            "Major Illness Preparedness",
            "How well does your policy handle serious health events",
            4,
            {
                "coverageAdequacy": {
                    "title": "Coverage Adequacy for Critical Scenarios",
                    "scenarios": critical_scenarios,
                    "note": "Major illnesses often require multiple hospitalizations. With restoration benefit, your cover resets after each claim."
                },
                "hasRestoration": restoration is not None
            }
        ))

        # Section 5: Improvement Opportunities
        improvement_gaps = []
        if room_rent_daily < 10000:
            improvement_gaps.append({"gap": "Room rent limit", "impact": "Higher out-of-pocket in good hospitals", "solution": "Consider upgrade to no-limit plan at renewal"})
        if co_payment > 0:
            improvement_gaps.append({"gap": f"{co_payment}% Co-payment", "impact": f"Pay {co_payment}% of every claim yourself", "solution": "Port to zero co-pay plan"})
        if not restoration:
            improvement_gaps.append({"gap": "No restoration", "impact": "Second illness in same year = no cover", "solution": "Upgrade to plan with restoration"})
        if sum_insured < 1000000:
            improvement_gaps.append({"gap": "Sum insured < Rs. 10L", "impact": "Major illness exhausts cover", "solution": "Add Super Top-up of Rs. 50L-1Cr"})

        analysis["sections"].append(create_section(
            "improvement_opportunities",
            "Improvement Opportunities",
            "Areas where your coverage could be strengthened",
            5,
            {
                "gaps": improvement_gaps,
                "superTopUpOpportunity": {
                    "title": "Super Top-Up Opportunity",
                    "description": f"A Super Top-up of Rs. 1 Crore with Rs. {sum_insured} deductible costs only Rs. 5,000-12,000/year.",
                    "recommended": sum_insured < 2000000
                }
            }
        ))

        # Section 6: Recommended Actions
        actions = []
        if end_date:
            actions.append({"priority": 1, "action": f"Renew before {end_date} to maintain NCB and waiting period credits", "timeline": "Before expiry", "urgency": "Critical"})

        for idx, gap in enumerate(improvement_gaps[:2]):
            actions.append({"priority": idx + 2, "action": gap["solution"], "timeline": "At renewal", "urgency": "High"})

        analysis["sections"].append(create_section(
            "recommended_actions",
            "Recommended Actions",
            "Prioritized steps to strengthen your coverage",
            6,
            {
                "actions": actions,
                "importantInfo": {
                    "title": "Know Before You're Hospitalized",
                    "items": [
                        {"info": "Room rent limit", "detail": str(room_rent_limit)},
                        {"info": "TPA Helpline", "detail": "Check policy document"},
                        {"info": "Claim Intimation Deadline", "detail": "Within 24 hours of admission"}
                    ]
                }
            }
        ))

        # Section 7: Assessment
        if sum_insured >= 1000000 and restoration and co_payment == 0:
            assessment_status = "COMPREHENSIVE COVER"
        elif sum_insured >= 500000:
            assessment_status = "ADEQUATE WITH GAPS"
        else:
            assessment_status = "NEEDS ENHANCEMENT"

        analysis["sections"].append(create_section(
            "assessment",
            "Assessment",
            assessment_status,
            7,
            {
                "status": assessment_status,
                "keyFinding": f"Coverage of Rs. {sum_insured:,} is {'adequate for routine hospitalization' if sum_insured >= 500000 else 'limited'}. {'Has restoration benefit.' if restoration else 'No restoration benefit - consider adding.'}",
                "recommendedAction": improvement_gaps[0]["solution"] if improvement_gaps else "Maintain current coverage and review at renewal."
            }
        ))

    # ==================== MOTOR INSURANCE ANALYSIS ====================
    elif "motor" in policy_type or "car" in policy_type or "vehicle" in policy_type or "auto" in policy_type or "bike" in policy_type:
        idv_raw = category_data.get("coverageDetails", {}).get("idv") or coverage_amount
        ncb_percentage_raw = category_data.get("ncb", {}).get("ncbPercentage") or 0

        # Convert to numeric (handle string values)
        try:
            idv = int(float(str(idv_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if idv_raw else 0
        except (ValueError, TypeError):
            idv = 0

        try:
            ncb_percentage = float(str(ncb_percentage_raw).replace('%', '').strip()) if ncb_percentage_raw else 0
        except (ValueError, TypeError):
            ncb_percentage = 0

        policy_type_motor = category_data.get("policyIdentification", {}).get("productType") or "Comprehensive"
        vehicle_details = category_data.get("vehicleDetails", {})

        # Section 1: Your Coverage Snapshot
        analysis["sections"].append(create_section(
            "coverage_snapshot",
            "Your Coverage Snapshot",
            "Vehicle & Policy Details",
            1,
            {
                "vehiclePolicyDetails": {
                    "title": "Vehicle & Policy Details",
                    "items": [
                        {"detail": "Vehicle", "value": f"{vehicle_details.get('vehicleMake', '')} {vehicle_details.get('vehicleModel', '')} — {vehicle_details.get('registrationNumber', '')}"},
                        {"detail": "Policy Type", "value": policy_type_motor},
                        {"detail": "IDV (Insured Value)", "value": f"Rs. {idv:,}" if idv else "Not specified"},
                        {"detail": "No Claim Bonus", "value": f"{ncb_percentage}%" if ncb_percentage else "0%"},
                        {"detail": "Policy Valid Until", "value": end_date or "Check policy"}
                    ]
                },
                "coverageBreakdown": {
                    "title": "Coverage Breakdown",
                    "coverages": [
                        {"type": "Own Damage (OD)", "limit": f"Up to IDV (Rs. {idv:,})" if idv else "Up to IDV", "status": "Covered" if "comprehensive" in policy_type_motor.lower() else "Not covered"},
                        {"type": "Third Party - Death/Injury", "limit": "Unlimited", "status": "Covered — Mandatory"},
                        {"type": "Third Party - Property", "limit": "Rs. 7,50,000", "status": "Covered — Mandatory"},
                        {"type": "Personal Accident (Owner)", "limit": "Rs. 15,00,000", "status": "Covered" if "comprehensive" in policy_type_motor.lower() else "Check policy"}
                    ]
                }
            }
        ))

        # Section 2: What You Get in a Claim
        deductible = category_data.get("coverageDetails", {}).get("compulsoryDeductible") or 1000
        voluntary_deductible = category_data.get("coverageDetails", {}).get("voluntaryDeductible") or 0

        vehicle_age = 0
        mfg_year = vehicle_details.get("manufacturingYear")
        if mfg_year:
            try:
                vehicle_age = datetime.now().year - int(mfg_year)
            except:
                pass

        # Depreciation rates based on vehicle age
        metal_depreciation = min(50, vehicle_age * 5) if vehicle_age > 0 else 0

        analysis["sections"].append(create_section(
            "claim_payout",
            "What You Get in a Claim",
            "Depreciation and deductibles affect your claim amount",
            2,
            {
                "totalLossCalculation": {
                    "title": "If Your Vehicle is Totaled or Stolen",
                    "items": [
                        {"item": "Insured Declared Value (IDV)", "amount": idv},
                        {"item": "(-) Compulsory Deductible", "amount": -deductible},
                        {"item": "(-) Voluntary Deductible", "amount": -voluntary_deductible, "note": "if opted"},
                        {"item": "Amount You Receive", "amount": idv - deductible - voluntary_deductible, "highlight": True}
                    ]
                },
                "depreciationRates": {
                    "title": "For Repair Claims — Depreciation Applies",
                    "rates": [
                        {"partCategory": "Rubber, Plastic, Nylon", "rate": "50%", "whatYouPay": "Half the part cost"},
                        {"partCategory": "Glass", "rate": "Nil", "whatYouPay": "Nothing (fully covered)"},
                        {"partCategory": f"Metal Parts (your car: {vehicle_age} years)", "rate": f"{metal_depreciation}%", "whatYouPay": f"{metal_depreciation}% of part cost"},
                        {"partCategory": "Battery", "rate": "50%", "whatYouPay": "Half the cost"},
                        {"partCategory": "Tyres", "rate": "50%", "whatYouPay": "Half the cost"}
                    ],
                    "example": f"On Rs. 80,000 repair with {25}% average depreciation, you pay approximately Rs. 20,000 + deductibles without Zero Depreciation."
                }
            }
        ))

        # Section 3: Your Liability Exposure
        analysis["sections"].append(create_section(
            "liability_exposure",
            "Your Liability Exposure",
            "The most important part of motor insurance",
            3,
            {
                "thirdPartyLiability": {
                    "title": "Third-Party Liability: Understanding the Stakes",
                    "description": "If you cause an accident injuring or killing someone, courts can award Rs. 20 Lakhs to Rs. 2+ Crores. Your TP insurance covers this — but ONLY if your policy is valid and you were driving legally.",
                    "warning": True
                },
                "whenNotCovered": {
                    "title": "When Third-Party Coverage Does NOT Protect You",
                    "situations": [
                        {"situation": "Driving under influence", "consequence": "Policy void — You pay full compensation personally"},
                        {"situation": "Driving without valid license", "consequence": "Policy void — Full personal liability"},
                        {"situation": "Commercial use (if private policy)", "consequence": "Coverage denied for that use"},
                        {"situation": "Policy expired (even by one day)", "consequence": "No coverage — Full personal liability"}
                    ]
                }
            }
        ))

        # Section 4: Add-On Coverage Analysis
        add_ons = category_data.get("addOnCovers", {})
        add_on_analysis = [
            {"addOn": "Zero Depreciation", "status": "Yes" if add_ons.get("zeroDepreciation") else "No", "benefit": "Eliminates depreciation deduction", "value": "Essential for cars < 5 years"},
            {"addOn": "Engine Protection", "status": "Yes" if add_ons.get("engineProtection") else "No", "benefit": "Covers water damage to engine", "value": "Important in flood-prone areas"},
            {"addOn": "Roadside Assistance", "status": "Yes" if add_ons.get("roadsideAssistance") else "No", "benefit": "24x7 help for breakdown", "value": "Convenience at low cost"},
            {"addOn": "NCB Protection", "status": "Yes" if add_ons.get("ncbProtect") else "No", "benefit": "Protects bonus after claim", "value": "Good for high NCB holders"},
            {"addOn": "Return to Invoice", "status": "Yes" if add_ons.get("returnToInvoice") else "No", "benefit": "Get invoice price on total loss", "value": "Valuable for new cars"}
        ]

        analysis["sections"].append(create_section(
            "addon_analysis",
            "Add-On Coverage Analysis",
            "Optional covers that reduce out-of-pocket costs",
            4,
            {
                "addOns": add_on_analysis
            }
        ))

        # Section 5: Your NCB Value
        ncb_saving = int(premium * ncb_percentage / 100) if ncb_percentage else 0
        analysis["sections"].append(create_section(
            "ncb_value",
            "Your NCB Value",
            "No Claim Bonus is a valuable asset",
            5,
            {
                "ncbStatus": {
                    "title": "NCB Status",
                    "items": [
                        {"status": "Current NCB Level", "value": f"{ncb_percentage}%"},
                        {"status": "Premium Saved This Year", "value": f"Rs. {ncb_saving:,}"},
                        {"status": "If You Make a Claim", "value": f"NCB resets to 0% — Next year premium increases by Rs. {ncb_saving:,}"},
                        {"status": "5-Year NCB Value", "value": f"Rs. {ncb_saving * 5:,} (potential savings if maintained)"}
                    ]
                },
                "smartClaimAdvice": "For repairs under Rs. 10,000-15,000, paying yourself may be better than losing years of NCB."
            }
        ))

        # Section 6: Recommended Actions & Assessment
        actions = []
        if end_date:
            actions.append({"priority": 1, "action": f"Renew before {end_date} — Any gap voids NCB", "timeline": "Before expiry", "urgency": "Critical"})
        if not add_ons.get("zeroDepreciation") and vehicle_age < 5:
            actions.append({"priority": 2, "action": "Add Zero Depreciation at renewal", "timeline": "At renewal", "urgency": "High"})

        assessment_status = "WELL COVERED" if add_ons.get("zeroDepreciation") and ncb_percentage >= 20 else "STANDARD PROTECTION" if "comprehensive" in policy_type_motor.lower() else "ENHANCEMENT RECOMMENDED"

        analysis["sections"].append(create_section(
            "recommended_actions",
            "Recommended Actions",
            "Prioritized steps",
            6,
            {"actions": actions}
        ))

        analysis["sections"].append(create_section(
            "assessment",
            "Assessment",
            assessment_status,
            7,
            {
                "status": assessment_status,
                "keyFinding": f"{'Comprehensive' if 'comprehensive' in policy_type_motor.lower() else 'Third-party'} cover with {ncb_percentage}% NCB. {'Has Zero Depreciation.' if add_ons.get('zeroDepreciation') else 'No Zero Depreciation - significant out-of-pocket on repairs.'}",
                "recommendedAction": actions[0]["action"] if actions else "Maintain current coverage."
            }
        ))

    # ==================== TRAVEL INSURANCE ANALYSIS ====================
    elif "travel" in policy_type:
        trip_details = category_data.get("tripDetails", {})
        coverage_summary = category_data.get("coverageSummary", {})
        emergency_contacts = category_data.get("emergencyContacts", {})

        medical_expenses_raw = coverage_summary.get("medicalExpenses") or coverage_amount
        # Parse to numeric for comparisons; keep raw for display
        try:
            medical_expenses = _parse_travel_cover_amount(medical_expenses_raw) if isinstance(medical_expenses_raw, str) else (float(medical_expenses_raw) if medical_expenses_raw else 0)
        except (ValueError, TypeError):
            medical_expenses = 0
        destinations = trip_details.get("destinationCountries") or []
        trip_duration = trip_details.get("tripDuration") or "Check policy"

        # Section 1: Trip & Coverage Summary
        analysis["sections"].append(create_section(
            "trip_coverage_summary",
            "Trip & Coverage Summary",
            "Your travel protection details",
            1,
            {
                "tripDetails": {
                    "title": "Trip Details",
                    "items": [
                        {"detail": "Trip Type", "value": trip_details.get("tripType", "Single Trip")},
                        {"detail": "Destination(s)", "value": ", ".join(destinations) if destinations else "Check policy"},
                        {"detail": "Coverage Period", "value": f"{start_date} to {end_date}" if start_date and end_date else "Check policy"},
                        {"detail": "Trip Duration", "value": str(trip_duration)}
                    ]
                },
                "coverageLimits": {
                    "title": "Coverage Limits",
                    "coverages": [
                        {"coverage": "Medical Expenses", "limit": f"USD {medical_expenses:,}" if isinstance(medical_expenses, (int, float)) else str(medical_expenses)},
                        {"coverage": "Emergency Evacuation", "limit": str(coverage_summary.get("emergencyMedicalEvacuation", "Check policy"))},
                        {"coverage": "Trip Cancellation", "limit": str(coverage_summary.get("tripCancellation", "Check policy"))},
                        {"coverage": "Baggage Loss", "limit": str(coverage_summary.get("baggageLoss", "Check policy"))},
                        {"coverage": "Personal Accident", "limit": str(coverage_summary.get("accidentalDeath", "Check policy"))}
                    ]
                }
            }
        ))

        # Section 2: Medical Coverage Adequacy
        destination_costs = {
            "usa": {"hospitalDay": "$3,000 - $5,000", "surgery": "$30,000 - $150,000", "recommended": "$100,000 - $250,000"},
            "europe": {"hospitalDay": "$1,000 - $2,500", "surgery": "$15,000 - $50,000", "recommended": "$50,000 - $100,000"},
            "asia": {"hospitalDay": "$300 - $1,200", "surgery": "$5,000 - $30,000", "recommended": "$50,000"}
        }

        analysis["sections"].append(create_section(
            "medical_adequacy",
            "Medical Coverage Adequacy",
            "Medical costs vary by destination",
            2,
            {
                "destinationCosts": destination_costs,
                "yourAssessment": {
                    "title": "Your Coverage Assessment",
                    "description": f"Your medical limit provides coverage for typical hospitalization. Verify adequacy based on destination."
                }
            }
        ))

        # Section 3: What's Not Covered
        exclusions_travel = category_data.get("exclusions", {})
        analysis["sections"].append(create_section(
            "not_covered",
            "What's Not Covered",
            "Common claim rejection reasons",
            3,
            {
                "exclusions": [
                    {"exclusion": "Pre-existing conditions (undeclared)", "impact": "Any related illness — claim rejected"},
                    {"exclusion": "Adventure sports (without add-on)", "impact": "Skiing/Diving/Trekking injuries — not covered"},
                    {"exclusion": "Treatment without authorization", "impact": "Cashless denied; reimbursement reduced"},
                    {"exclusion": "Alcohol/drug related", "impact": "Most policies exclude completely"},
                    {"exclusion": "Travel against medical advice", "impact": "No coverage if doctor advised not to travel"}
                ]
            }
        ))

        # Section 4: Emergency Preparedness
        analysis["sections"].append(create_section(
            "emergency_preparedness",
            "Emergency Preparedness",
            "Critical information for emergencies abroad",
            4,
            {
                "emergencyInfo": {
                    "title": "Your Emergency Information",
                    "contacts": [
                        {"contact": "24x7 Assistance Helpline", "detail": emergency_contacts.get("emergencyHelpline24x7", "Check policy document")},
                        {"contact": "Claims Email", "detail": emergency_contacts.get("claimsEmail", "Check policy document")},
                        {"contact": "Policy Number", "detail": extracted_data.get("policyNumber", "")}
                    ]
                },
                "tip": "Save the assistance number in your phone. In an emergency, call FIRST — before going to hospital if possible."
            }
        ))

        # Section 5 & 6: Actions and Assessment
        assessment_status = "ADEQUATELY PROTECTED" if medical_expenses and medical_expenses >= 50000 else "REVIEW MEDICAL LIMIT"
        analysis["sections"].append(create_section(
            "assessment",
            "Assessment",
            assessment_status,
            5,
            {
                "status": assessment_status,
                "keyFinding": "Coverage appears adequate for standard travel. Verify medical limits for high-cost destinations like USA.",
                "recommendedAction": "Save emergency contacts and policy document offline on phone before travel."
            }
        ))

    # ==================== BUSINESS INSURANCE ANALYSIS ====================
    elif "business" in policy_type or "commercial" in policy_type or "fire" in policy_type:
        property_coverage = category_data.get("propertyCoverage", {})
        liability_coverage = category_data.get("liabilityCoverage", {})
        bi_coverage = category_data.get("businessInterruption", {})

        total_property_value = property_coverage.get("totalPropertyValue") or coverage_amount

        # Section 1: Coverage Overview
        analysis["sections"].append(create_section(
            "coverage_overview",
            "Coverage Overview",
            "Your commercial protection details",
            1,
            {
                "businessDetails": {
                    "title": "Business & Policy Details",
                    "items": [
                        {"detail": "Business Name", "value": category_data.get("insuredEntity", {}).get("businessName", user_name)},
                        {"detail": "Business Type", "value": category_data.get("insuredEntity", {}).get("businessType", "Check policy")},
                        {"detail": "Policy Type", "value": category_data.get("policyIdentification", {}).get("policyType", policy_type)},
                        {"detail": "Policy Period", "value": f"{start_date} to {end_date}" if start_date else "Check policy"}
                    ]
                },
                "propertyCoverage": {
                    "title": "Property Coverage",
                    "assets": [
                        {"category": "Building", "insuredValue": property_coverage.get("buildingValue", 0)},
                        {"category": "Plant & Machinery", "insuredValue": property_coverage.get("plantMachineryValue", 0)},
                        {"category": "Stock / Inventory", "insuredValue": property_coverage.get("stocksValue", 0)},
                        {"category": "TOTAL", "insuredValue": total_property_value, "highlight": True}
                    ]
                }
            }
        ))

        # Section 2: Underinsurance Problem
        analysis["sections"].append(create_section(
            "underinsurance",
            "The Underinsurance Problem",
            "Average clause affects every claim",
            2,
            {
                "averageClause": {
                    "title": "Average Clause Impact",
                    "description": "If your insured values are less than actual replacement values, all claims are reduced proportionately.",
                    "example": "If 20% underinsured, a Rs. 50 Lakh claim only pays Rs. 40 Lakhs.",
                    "recommendation": "Update Sum Insured to current replacement values at renewal."
                }
            }
        ))

        # Section 3: Business Interruption
        has_bi = bi_coverage.get("businessInterruptionCover") is not None
        analysis["sections"].append(create_section(
            "business_interruption",
            "Business Interruption Analysis",
            "Income protection if operations stop",
            3,
            {
                "biCoverage": {
                    "title": "Business Interruption Cover",
                    "covered": has_bi,
                    "indemnityPeriod": bi_coverage.get("indemnityPeriod", "N/A") if has_bi else "NOT COVERED",
                    "grossProfitInsured": bi_coverage.get("grossProfitInsured", "N/A") if has_bi else "N/A"
                },
                "warning": None if has_bi else "Without BI Cover, a fire or flood means zero revenue but continued expenses. This comes entirely from reserves or debt."
            }
        ))

        # Section 4: Liability Coverage
        liabilities = [
            {"type": "Public Liability", "coverage": liability_coverage.get("publicLiability", "Not covered")},
            {"type": "Product Liability", "coverage": liability_coverage.get("productLiability", "Not covered")},
            {"type": "Professional Indemnity", "coverage": liability_coverage.get("professionalIndemnity", "Not covered")},
            {"type": "Cyber Liability", "coverage": liability_coverage.get("cyberLiability", "Not covered")}
        ]

        analysis["sections"].append(create_section(
            "liability_coverage",
            "Liability Coverage",
            "Protection against third-party claims",
            4,
            {"liabilities": liabilities}
        ))

        # Section 5 & 6: Assessment
        assessment_status = "ADEQUATELY PROTECTED" if has_bi else "GAPS IN KEY AREAS"
        analysis["sections"].append(create_section(
            "assessment",
            "Assessment",
            assessment_status,
            5,
            {
                "status": assessment_status,
                "keyFinding": f"Property coverage of Rs. {total_property_value:,}. {'Has BI cover.' if has_bi else 'NO Business Interruption cover - critical gap.'}",
                "recommendedAction": "Update Sum Insured to current replacement values." if has_bi else "Add Business Interruption cover urgently."
            }
        ))

    # ==================== PERSONAL ACCIDENT / ACCIDENTAL INSURANCE ANALYSIS (EAZR_04) ====================
    elif "accidental" in policy_type or "accident" in policy_type or "pa" in policy_type or "personal accident" in policy_type:
        # Extract PA-specific data (supports both old flat format and new EAZR_04 nested format)
        coverage_details = category_data.get("coverageDetails", {})
        additional_benefits = category_data.get("additionalBenefits", {})
        exclusions_data = category_data.get("exclusions", {})
        claims_info_pa = category_data.get("claimsInfo", {})

        # Safe numeric parser for deep analysis
        def _da_safe_num(val, default=0):
            if val is None:
                return default
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                cleaned = val.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
                try:
                    return float(cleaned)
                except (ValueError, TypeError):
                    return default
            return default

        sum_insured = _da_safe_num(coverage_details.get("sumInsured"), 0) or _da_safe_num(coverage_amount, 0)
        annual_income = 1000000  # Default assumed income

        # Handle both old flat format and new nested format for coverage data
        ad = coverage_details.get("accidentalDeath", {}) if isinstance(coverage_details.get("accidentalDeath"), dict) else {}
        ptd_data = coverage_details.get("permanentTotalDisability", {}) if isinstance(coverage_details.get("permanentTotalDisability"), dict) else {}
        ppd_data = coverage_details.get("permanentPartialDisability", {}) if isinstance(coverage_details.get("permanentPartialDisability"), dict) else {}
        ttd_data = coverage_details.get("temporaryTotalDisability", {}) if isinstance(coverage_details.get("temporaryTotalDisability"), dict) else {}
        medical_data = coverage_details.get("medicalExpenses", {}) if isinstance(coverage_details.get("medicalExpenses"), dict) else {}

        ad_benefit = _da_safe_num(ad.get("benefitAmount"), sum_insured)
        ptd_benefit = _da_safe_num(ptd_data.get("benefitAmount"), sum_insured)

        # Detect if this is an EAZR company complimentary PA or a standalone paid PA
        is_company_pa = category_data.get("policyBasics", {}).get("isCompanyPA", False)

        # Section 1: PA Coverage Snapshot with 5 Coverage Cards
        analysis["sections"].append(create_section(
            "coverage_snapshot",
            "Your Complimentary PA Coverage" if is_company_pa else "Your PA Coverage",
            (f"Complimentary PA Cover — Sum Insured: \u20b9{sum_insured:,}" if is_company_pa
             else f"Personal Accident Cover — Sum Insured: Rs. {sum_insured:,}"),
            1,
            {
                "sumInsured": sum_insured,
                "sumInsuredFormatted": f"Rs. {sum_insured:,}",
                "coverageCards": [
                    {
                        "type": "AD", "label": "Accidental Death", "covered": True,
                        "benefitAmount": ad_benefit,
                        "benefitFormatted": f"Rs. {ad_benefit:,}",
                        "detail": f"{ad.get('benefitPercentage', 100)}% of SI" + (" + Double Indemnity" if ad.get("doubleIndemnity", {}).get("applicable") else "")
                    },
                    {
                        "type": "PTD", "label": "Permanent Total Disability",
                        "covered": ptd_data.get("covered", True) if ptd_data else bool(coverage_details.get("permanentTotalDisability")),
                        "benefitAmount": ptd_benefit,
                        "benefitFormatted": f"Rs. {ptd_benefit:,}",
                        "detail": f"{ptd_data.get('benefitPercentage', 100)}% of SI"
                    },
                    {
                        "type": "PPD", "label": "Permanent Partial Disability",
                        "covered": ppd_data.get("covered", True) if ppd_data else bool(coverage_details.get("permanentPartialDisability")),
                        "detail": f"{len(ppd_data.get('schedule', []))} conditions in schedule" if ppd_data.get("schedule") else "As per IRDAI schedule"
                    },
                    {
                        "type": "TTD", "label": "Temporary Total Disability",
                        "covered": ttd_data.get("covered", False) if ttd_data else bool(coverage_details.get("temporaryTotalDisability")),
                        "detail": f"Rs. {_da_safe_num(ttd_data.get('benefitAmount'), 0):,.0f}/{ttd_data.get('benefitType', 'week')} for up to {ttd_data.get('maximumWeeks', 52)} weeks" if ttd_data.get("covered") else "Not covered"
                    },
                    {
                        "type": "Medical", "label": "Medical Expenses",
                        "covered": medical_data.get("covered", False) if medical_data else bool(coverage_details.get("medicalExpenses")),
                        "detail": f"{medical_data.get('limitPercentage', 0)}% of SI" if medical_data.get("covered") else "Not covered"
                    }
                ],
                "policyPeriod": f"{start_date} to {end_date}" if start_date else "Check policy"
            }
        ))

        # Section 2: Scoring Engine
        s1 = _calculate_pa_income_replacement_score(coverage_details, additional_benefits, annual_income)
        s2 = _calculate_pa_disability_protection_score(coverage_details, additional_benefits)
        overall_score = round(s1["score"] * 0.6 + s2["score"] * 0.4)
        overall_label = get_score_label(overall_score)

        analysis["sections"].append(create_section(
            "scoring_engine",
            "Coverage Overview",
            (f"Complimentary PA Cover — Score: {overall_score}/100" if is_company_pa
             else f"Protection Score: {overall_score}/100 — {overall_label['label']}"),
            2,
            {
                "overallScore": overall_score,
                "overallLabel": overall_label["label"],
                "overallColor": overall_label["color"],
                "contextNote": ("This PA cover is provided as a complimentary benefit without any additional premium. Scores are relative to standalone paid PA policies."
                                if is_company_pa else None),
                "scores": [
                    {
                        "name": "Income Replacement Adequacy", "weight": "60%",
                        "score": s1["score"],
                        "label": get_score_label(s1["score"])["label"],
                        "color": get_score_label(s1["score"])["color"],
                        "factors": s1["factors"]
                    },
                    {
                        "name": "Disability Protection Depth", "weight": "40%",
                        "score": s2["score"],
                        "label": get_score_label(s2["score"])["label"],
                        "color": get_score_label(s2["score"])["color"],
                        "factors": s2["factors"]
                    }
                ]
            }
        ))

        # Section 3: Gap Analysis / Coverage Notes
        pa_gaps_raw = _analyze_pa_gaps(coverage_details, additional_benefits, annual_income)

        if is_company_pa:
            # Soften gaps for free cover
            pa_gaps_display = []
            for g in pa_gaps_raw:
                soft_gap = dict(g)
                soft_gap["severity"] = "info"
                soft_gap["severityColor"] = "#6B7280"
                if soft_gap.get("gapId") == "G001":
                    soft_gap["title"] = "PA Sum Insured (Complimentary Cover)"
                    soft_gap["description"] = f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{sum_insured:,} is provided as a complimentary benefit under this policy, without any additional premium."
                    soft_gap["impact"] = "This coverage is subject to the applicable terms, conditions, and exclusions of the policy."
                    soft_gap["solution"] = "For higher accident coverage, standalone PA plans may be explored separately."
                elif soft_gap.get("gapId") == "G002":
                    soft_gap["title"] = "TTD Not Included"
                    soft_gap["description"] = "Temporary Total Disability benefit is not included under this complimentary PA cover."
                    soft_gap["impact"] = "Hospitalization expenses, if any, are covered under your separate health insurance policy."
                    soft_gap["solution"] = "Standalone PA plans with TTD benefit are available if required."
                elif soft_gap.get("gapId") == "G004":
                    soft_gap["title"] = "Medical Expenses (Covered under Health Insurance)"
                    soft_gap["description"] = "Accident-related medical expenses are covered under your separate health insurance policy."
                    soft_gap["impact"] = "Your health insurance policy is the primary cover for medical treatment costs."
                    soft_gap["solution"] = "Ensure your health insurance policy is active for medical expense coverage."
                pa_gaps_display.append(soft_gap)
            analysis["sections"].append(create_section(
                "gap_analysis",
                "Coverage Notes",
                "Coverage notes for this complimentary PA cover" if pa_gaps_display else "Complimentary PA cover details noted",
                3,
                {
                    "totalGaps": len(pa_gaps_display),
                    "highSeverity": 0, "mediumSeverity": 0, "lowSeverity": 0,
                    "infoNotes": len(pa_gaps_display),
                    "contextNote": "These are informational notes about your complimentary PA cover provided without any additional premium.",
                    "gaps": pa_gaps_display
                }
            ))
        else:
            # Standalone PA: show real gaps
            high_count = sum(1 for g in pa_gaps_raw if g.get("severity") == "high")
            medium_count = sum(1 for g in pa_gaps_raw if g.get("severity") == "medium")
            low_count = sum(1 for g in pa_gaps_raw if g.get("severity") == "low")
            gap_subtitle = f"{high_count} critical, {medium_count} moderate, {low_count} minor" if pa_gaps_raw else "No significant gaps found"
            analysis["sections"].append(create_section(
                "gap_analysis",
                "Gap Analysis",
                gap_subtitle,
                3,
                {
                    "totalGaps": len(pa_gaps_raw),
                    "highSeverity": high_count, "mediumSeverity": medium_count, "lowSeverity": low_count,
                    "gaps": pa_gaps_raw
                }
            ))

        # Section 4: Key Exclusions
        standard_exclusions = exclusions_data.get("standardExclusions", [])
        if not standard_exclusions:
            # Fallback for old format
            standard_exclusions = []
            for key in ["suicideExclusion", "warExclusion", "intoxicationExclusion", "criminalActExclusion", "hazardousActivitiesExclusion"]:
                val = exclusions_data.get(key)
                if val:
                    standard_exclusions.append(str(val))
            other_exc = exclusions_data.get("otherExclusions", [])
            if isinstance(other_exc, list):
                standard_exclusions.extend([str(e) for e in other_exc[:5]])

        exclusion_items = [{"exclusion": exc, "details": exc} for exc in standard_exclusions] if standard_exclusions else [
            {"exclusion": "Self-inflicted Injuries", "details": "Suicide and self-harm not covered"},
            {"exclusion": "War & Nuclear Perils", "details": "War, terrorism, nuclear events excluded"},
            {"exclusion": "Intoxication", "details": "Injuries under influence of alcohol/drugs"},
            {"exclusion": "Criminal Acts", "details": "Injuries during illegal activities"},
            {"exclusion": "Hazardous Activities", "details": "Adventure sports may be excluded unless declared"}
        ]

        analysis["sections"].append(create_section(
            "exclusions",
            "Key Exclusions",
            "What is NOT covered",
            4,
            {
                "exclusions": exclusion_items,
                "ageLimits": exclusions_data.get("ageLimits", {}),
                "occupationRestrictions": exclusions_data.get("occupationRestrictions", []),
                "importantNote": "PA insurance covers ACCIDENTS only, not illness. Refer to policy document for complete exclusions."
            }
        ))

        # Section 5: Recommendations
        _pa_claims_process = {
            "steps": [
                {"step": 1, "title": "Intimate Claim", "description": "Report accident to insurer immediately (within 24-48 hours)"},
                {"step": 2, "title": "File FIR", "description": "Lodge police FIR for accidents (mandatory for death/serious injury)"},
                {"step": 3, "title": "Collect Documents", "description": "Medical reports, hospital bills, FIR copy, ID proof, policy copy"},
                {"step": 4, "title": "Submit Claim Form", "description": "Fill claim form and submit with all documents"},
                {"step": 5, "title": "Claim Settlement", "description": "Insurer verifies and settles claim (typically 30 days)"}
            ],
            "contact": {
                "email": claims_info_pa.get("claimsEmail") or "Check policy",
                "helpline": claims_info_pa.get("claimsHelpline") or "Check policy"
            }
        }

        if is_company_pa:
            pa_deep_recommendations = [
                {"id": "keep_active", "category": "maintenance", "priority": 1, "title": "Keep Your PA Cover Active",
                 "description": "This PA cover is provided as a complimentary benefit without any additional premium. Keep the policy active to continue availing this benefit.",
                 "estimatedCost": "No additional premium", "ipfEligible": False, "icon": "verified"},
                {"id": "know_your_cover", "category": "awareness", "priority": 2, "title": "Know Your Coverage",
                 "description": f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{sum_insured:,} is provided under this policy. Share the policy details with your nominee/family for their awareness.",
                 "estimatedCost": "No additional cost", "ipfEligible": False, "icon": "info"},
                {"id": "review_at_renewal", "category": "maintenance", "priority": 3, "title": "Review at Renewal",
                 "description": "Review the PA cover details at renewal to stay updated on any changes to benefits, terms, or conditions.",
                 "estimatedCost": "No additional cost", "ipfEligible": False, "icon": "rate_review"}
            ]
            analysis["sections"].append(create_section(
                "recommendations", "Good to Know", "Key information about your complimentary PA cover", 5,
                {"recommendations": pa_deep_recommendations, "claimsProcess": _pa_claims_process}
            ))
        else:
            pa_policy_sub_type = category_data.get("policyBasics", {}).get("policySubType", "")
            pa_deep_recommendations = _generate_pa_recommendations(pa_gaps_raw, coverage_details, additional_benefits, pa_policy_sub_type)
            analysis["sections"].append(create_section(
                "recommendations", "Recommendations",
                f"{len(pa_deep_recommendations)} recommendations to strengthen your PA cover", 5,
                {"recommendations": pa_deep_recommendations, "claimsProcess": _pa_claims_process}
            ))

        # Section 6: Assessment
        if is_company_pa:
            assessment_status = "COMPLIMENTARY PROTECTION"
            key_finding = f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{sum_insured:,} is provided as a complimentary benefit under this policy, without any additional premium, and is subject to the applicable terms, conditions, and exclusions."
            rec_action = "Keep the policy active to continue availing this complimentary PA benefit."
            analysis["sections"].append(create_section(
                "assessment", "Assessment", assessment_status, 6,
                {"status": assessment_status, "protectionScore": overall_score,
                 "scoreLabel": "Complimentary", "scoreColor": "#3B82F6",
                 "keyFinding": key_finding, "recommendedAction": rec_action,
                 "importantReminder": "This PA cover provides benefits for accidental death and disability. For illness and medical expenses, your health insurance policy is the primary cover."}
            ))
        else:
            if overall_score >= 70:
                assessment_status = "WELL PROTECTED"
                key_finding = f"Your PA cover of Rs. {sum_insured:,} provides strong accident protection with a score of {overall_score}/100."
                rec_action = "Review your coverage annually to keep pace with income growth."
            elif overall_score >= 40:
                assessment_status = "GAPS IN KEY AREAS"
                key_finding = f"Your PA cover of Rs. {sum_insured:,} has some gaps. Score: {overall_score}/100."
                rec_action = "Consider addressing the high-severity gaps identified above."
            else:
                assessment_status = "NEEDS ATTENTION"
                key_finding = f"Your PA cover of Rs. {sum_insured:,} has significant coverage gaps. Score: {overall_score}/100."
                rec_action = "Upgrade to a comprehensive PA plan with higher sum insured, TTD benefit, and medical expenses cover."
            analysis["sections"].append(create_section(
                "assessment", "Assessment", assessment_status, 6,
                {"status": assessment_status, "protectionScore": overall_score,
                 "scoreLabel": overall_label["label"], "scoreColor": overall_label["color"],
                 "keyFinding": key_finding, "recommendedAction": rec_action,
                 "importantReminder": "PA insurance covers accidents only. Ensure you have Health Insurance for illness and Life Insurance for comprehensive family protection."}
            ))

    # ==================== AGRICULTURE INSURANCE ANALYSIS ====================
    elif "agriculture" in policy_type or "crop" in policy_type or "farm" in policy_type or "pmfby" in policy_type:
        farmer_details = category_data.get("farmerDetails", {})
        land_crop = category_data.get("landCropDetails", {})
        risks_covered = category_data.get("risksCovered", {})
        premium_details = category_data.get("premium", {})

        total_sum_insured = category_data.get("coverageDetails", {}).get("totalSumInsured") or coverage_amount
        farmer_premium = premium_details.get("farmerSharePremium") or premium

        # Section 1: Enrollment Summary
        analysis["sections"].append(create_section(
            "enrollment_summary",
            "Enrollment Summary",
            "Your crop protection under PMFBY/RWBCIS",
            1,
            {
                "policyDetails": {
                    "title": "Policy Details",
                    "items": [
                        {"detail": "Scheme", "value": category_data.get("policyIdentification", {}).get("schemeName", "PMFBY")},
                        {"detail": "Season", "value": category_data.get("policyIdentification", {}).get("seasonYear", "Check policy")},
                        {"detail": "Farmer Category", "value": farmer_details.get("farmerCategory", "Check policy")},
                        {"detail": "Crop", "value": land_crop.get("cropName", "Check policy")},
                        {"detail": "Total Area Insured", "value": land_crop.get("totalAreaInsured", "Check policy")},
                        {"detail": "Total Sum Insured", "value": f"Rs. {total_sum_insured:,}" if total_sum_insured else "Check policy"}
                    ]
                }
            }
        ))

        # Section 2: Claim Calculation
        analysis["sections"].append(create_section(
            "claim_calculation",
            "How Your Claim is Calculated",
            "PMFBY claims are based on VILLAGE-LEVEL yield",
            2,
            {
                "claimFormula": {
                    "title": "Claim Calculation",
                    "description": "Your individual crop loss does not directly determine your claim. The Crop Cutting Experiment (CCE) in your village determines yield for all farmers.",
                    "formula": "Claim = Sum Insured × Shortfall × Indemnity Level",
                    "important": "Village-Level Assessment means all farmers with same crop in your area get same claim percentage."
                }
            }
        ))

        # Section 3: What's Covered
        covered_risks = [
            {"risk": "Prevented Sowing", "status": "Covered", "notes": "If sowing prevented due to deficit rainfall"},
            {"risk": "Standing Crop Loss", "status": "Covered", "notes": "Yield loss due to drought, flood, pests"},
            {"risk": "Post-Harvest Loss", "status": "Covered (14 days)", "notes": "Cyclone, unseasonal rain after harvest"},
            {"risk": "Localized Calamity", "status": "Covered", "notes": "Hailstorm, landslide — individual assessment"},
            {"risk": "Wild Animal Attack", "status": str(risks_covered.get("wildAnimalAttack", "Check policy")), "notes": "If add-on opted"}
        ]

        analysis["sections"].append(create_section(
            "coverage",
            "What's Covered",
            "Risks protected under the scheme",
            3,
            {"risks": covered_risks}
        ))

        # Section 4: Premium Contribution
        gov_subsidy = premium_details.get("stateSharePremium", 0) + premium_details.get("centralSharePremium", 0) if premium_details else 0
        leverage = int(total_sum_insured / farmer_premium) if farmer_premium and farmer_premium > 0 else 0

        analysis["sections"].append(create_section(
            "premium_contribution",
            "Your Premium Contribution",
            "PMFBY is heavily subsidized",
            4,
            {
                "premiumBreakdown": {
                    "title": "Premium Breakdown",
                    "items": [
                        {"component": "Your Contribution", "amount": farmer_premium, "note": "2% for Kharif / 1.5% for Rabi"},
                        {"component": "Government Subsidy", "amount": gov_subsidy},
                        {"component": "Leverage (SI ÷ Premium)", "amount": f"{leverage}x", "highlight": True}
                    ]
                },
                "valueAssessment": f"For every Rs. {farmer_premium:,} you pay, you receive Rs. {total_sum_insured:,} coverage. One of the most subsidized insurance products in India."
            }
        ))

        # Section 5 & 6: Assessment
        analysis["sections"].append(create_section(
            "assessment",
            "Assessment",
            "PROPERLY ENROLLED" if total_sum_insured else "VERIFICATION NEEDED",
            5,
            {
                "status": "PROPERLY ENROLLED" if total_sum_insured else "VERIFICATION NEEDED",
                "keyFinding": f"Enrolled for {land_crop.get('cropName', 'crop')} with Rs. {total_sum_insured:,} coverage.",
                "recommendedAction": "Verify crop and area details match actual sowing. Report any loss within 72 hours."
            }
        ))

    # ==================== GENERIC ANALYSIS (fallback) ====================
    else:
        analysis["sections"].append(create_section(
            "coverage_overview",
            "Coverage Overview",
            "Your policy protection summary",
            1,
            {
                "summary": {
                    "policyType": policy_type,
                    "coverageAmount": coverage_amount,
                    "premium": premium,
                    "status": "Active" if protection_score >= 50 else "Review Needed"
                }
            }
        ))

        analysis["sections"].append(create_section(
            "assessment",
            "Assessment",
            protection_score_label,
            2,
            {
                "status": protection_score_label,
                "protectionScore": protection_score,
                "keyFinding": f"Policy provides Rs. {coverage_amount:,} coverage.",
                "recommendedAction": "Review policy details for specific coverage information."
            }
        ))

    return analysis
