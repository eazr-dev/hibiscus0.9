"""
Light Analysis Builder
Builds simplified/light policy analysis for all insurance types.
Handles Health, Motor, Life, Travel, and Personal Accident insurance.
"""
import logging

from policy_analysis.types.health.v10_helpers import (
    _get_health_strengths,
    _analyze_health_gaps,
    _select_primary_scenario,
    _build_health_recommendations,
)
from policy_analysis.types.life.v10_helpers import (
    _get_life_strengths,
    _analyze_life_gaps,
    _select_life_primary_scenario,
    _build_life_recommendations_v10,
    _build_life_svf_opportunity,
)
from policy_analysis.types.pa.v10_helpers import (
    _get_pa_strengths,
    _analyze_pa_gaps_v10,
    _build_pa_recommendations_v10,
    _build_pa_income_gap_check,
    _build_pa_portfolio_view,
    _build_pa_coverage_gaps_rich,
    _select_pa_primary_scenario,
)
from policy_analysis.types.pa.helpers import _simulate_pa_scenarios

logger = logging.getLogger(__name__)


def _build_light_analysis(
    protection_score: int,
    protection_score_label: str,
    insurer_name: str,
    plan_name: str,
    sum_assured: int,
    formatted_gaps: list,
    key_benefits: list,
    recommendations: list,
    deep_analysis: dict,
    category_data: dict = None,
    policy_type: str = "",
    city: str = "Mumbai",
    enhanced_insights: dict = None
) -> dict:
    """
    Build a simplified/light policy analysis based on EAZR Light Analysis V9 template.
    This replaces the detailed policyAnalyzer with a concise summary for quick understanding.

    Includes: Coverage Verdict, Claim Reality Check, Key Concerns, Coverage Gaps,
    What You Should Do, Policy Strengths, Quick Reference
    """
    import re
    from datetime import datetime as dt

    category_data = category_data or {}
    policy_type_lower = policy_type.lower() if policy_type else ""

    # Protection Verdict
    if protection_score >= 80:
        verdict_emoji = "shield"  # Will be rendered as emoji by frontend
        verdict_label = "Well Protected"
        verdict_one_liner = "Your policy provides solid coverage with strong fundamentals."
    elif protection_score >= 60:
        verdict_emoji = "warning"
        verdict_label = "Adequate Coverage"
        verdict_one_liner = "Your policy covers the basics but has some gaps to address."
    else:
        verdict_emoji = "alert"
        verdict_label = "Needs Attention"
        verdict_one_liner = "Your policy has significant gaps that should be addressed soon."

    # Personal Accident: Check if company PA (complimentary) or standalone
    _is_pa = "accidental" in policy_type_lower or "accident" in policy_type_lower or "pa" in policy_type_lower or "personal accident" in policy_type_lower
    _is_company_pa = _is_pa and category_data.get("policyBasics", {}).get("isCompanyPA", False)

    if _is_pa and _is_company_pa:
        verdict_emoji = "shield"
        verdict_label = "Complimentary PA Cover"
        verdict_one_liner = "You have a free Personal Accident cover — a valuable complimentary benefit that protects you against accidents at no extra cost."

    # The Numbers That Matter - Policy type specific
    if _is_pa and _is_company_pa:
        # Company PA: This is a FREE/complimentary cover — show what's covered positively
        total_protection_needed = sum_assured
        protection_gap = 0
        if sum_assured > 0:
            gap_one_liner = f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{sum_assured:,} is provided as a complimentary benefit under this policy, without any additional premium, and is subject to the applicable terms, conditions, and exclusions."
        else:
            gap_one_liner = "A Personal Accident (PA) insurance cover is provided as a complimentary benefit under this policy, without any additional premium."
    elif _is_pa and not _is_company_pa:
        # Standalone PA: show actual gap vs recommended (10x income)
        recommended_pa = 1000000  # Default Rs 10L if income unknown
        total_protection_needed = recommended_pa
        protection_gap = max(0, recommended_pa - sum_assured)
        if protection_gap == 0:
            gap_one_liner = f"Your PA cover of Rs. {sum_assured:,} meets the recommended accident protection level."
        elif sum_assured > 0:
            gap_one_liner = f"Your PA cover of Rs. {sum_assured:,} is below the recommended Rs. {recommended_pa:,}. Consider increasing for better protection."
        else:
            gap_one_liner = "No Personal Accident sum insured found. Ensure your PA cover amount is adequate."
    elif "health" in policy_type_lower or "medical" in policy_type_lower:
        # Health insurance: Compare with recommended health cover
        # For metro cities, recommended is Rs. 25L-50L for family
        # For individual, Rs. 10L-25L
        insured_members = category_data.get("insuredMembers", []) or category_data.get("membersCovered", [])
        member_count = len(insured_members) if insured_members else 1

        if member_count >= 3:
            total_protection_needed = 5000000  # Rs. 50L for family of 3+
        elif member_count == 2:
            total_protection_needed = 2500000  # Rs. 25L for couple
        else:
            total_protection_needed = 1000000  # Rs. 10L for individual

        protection_gap = max(0, total_protection_needed - sum_assured)
        if protection_gap > 0:
            gap_one_liner = f"Consider increasing cover by Rs. {protection_gap:,} for adequate protection."
        elif sum_assured >= 10000000:  # Rs. 1 Crore+
            gap_one_liner = "Excellent! Your health cover of Rs. 1Cr+ provides comprehensive protection."
        elif sum_assured >= 5000000:  # Rs. 50L+
            gap_one_liner = "Good coverage. Your health cover meets recommended levels for a family."
        else:
            gap_one_liner = "Your health cover meets minimum recommended levels."
    elif "life" in policy_type_lower or "term" in policy_type_lower:
        # Life insurance: 10-15x annual income — derive income from data
        _life_prem_det = category_data.get("premiumDetails", {}) or {}
        _life_prem_raw = _life_prem_det.get("premiumAmount", 0)
        try:
            _life_prem_val = float(str(_life_prem_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('₹', '').strip()) if _life_prem_raw else 0
        except (ValueError, TypeError):
            _life_prem_val = 0
        # Estimate income: SA/10 or premium*10, whichever is larger
        estimated_annual_income = max(int(sum_assured / 10) if sum_assured > 0 else 0, int(_life_prem_val * 10) if _life_prem_val > 0 else 0)
        if estimated_annual_income <= 0:
            estimated_annual_income = 500000  # Fallback only if both methods fail
        total_protection_needed = estimated_annual_income * 10
        protection_gap = max(0, total_protection_needed - sum_assured)
        if protection_gap > 0:
            gap_one_liner = f"You may need additional cover of Rs. {protection_gap:,} to fully protect your family."
        else:
            gap_one_liner = "Your coverage meets the recommended protection level."
    elif "motor" in policy_type_lower or "car" in policy_type_lower or "vehicle" in policy_type_lower:
        # Motor: IDV vs recommended
        total_protection_needed = sum_assured  # IDV is what matters
        protection_gap = 0
        gap_one_liner = "Your vehicle is insured at its declared value."
    else:
        # Generic
        estimated_annual_income = 500000
        total_protection_needed = estimated_annual_income * 10
        protection_gap = max(0, total_protection_needed - sum_assured)
        if protection_gap > 0:
            gap_one_liner = f"You may need additional cover of Rs. {protection_gap:,}."
        else:
            gap_one_liner = "Your coverage meets the recommended protection level."

    # ==================== CLAIM REALITY CHECK ====================
    # Calculate what happens on a typical claim
    claim_reality = {
        "claimAmount": 500000,  # Rs.5L sample claim
        "insurancePays": 0,
        "youPay": 0,
        "oneLiner": "",
        "currency": "INR"
    }

    if _is_pa:
        # Personal Accident insurance claim reality
        coverage_details = category_data.get("coverageDetails", {})
        accidental_death_cover = coverage_details.get("accidentalDeathCover") or "100% of SI"

        claim_reality["claimAmount"] = sum_assured
        claim_reality["insurancePays"] = sum_assured
        claim_reality["youPay"] = 0
        if _is_company_pa:
            claim_reality["oneLiner"] = f"This complimentary PA cover pays full Rs. {sum_assured:,} on accidental death. Disability benefits as per policy schedule — all at zero premium."
        else:
            claim_reality["oneLiner"] = f"Your PA cover pays Rs. {sum_assured:,} on accidental death. Disability benefits as per policy schedule."

    elif "health" in policy_type_lower or "medical" in policy_type_lower:
        # Health insurance claim reality - based on actual policy features
        import re as _cr_re
        coverage_details = category_data.get("coverageDetails", {})
        copay_details_cr = category_data.get("copayDetails", {}) or {}
        room_rent_limit = coverage_details.get("roomRentLimit", "")
        rrl_str = str(room_rent_limit).lower() if room_rent_limit else ""
        has_no_room_rent_limit = any(kw in rrl_str for kw in ["no limit", "no sub", "no cap", "unlimited", "single private", "single room"])

        # Extract actual copay percentage from copayDetails
        general_copay_cr = copay_details_cr.get("generalCopay") or coverage_details.get("coPay") or coverage_details.get("copay") or ""
        copay_str_cr = str(general_copay_cr).lower() if general_copay_cr else ""
        has_no_copay = not general_copay_cr or any(kw in copay_str_cr for kw in ["no co", "nil", "none", "0%"])
        copay_pct_cr = 0
        if not has_no_copay:
            cp_match = _cr_re.search(r'(\d+)', copay_str_cr)
            copay_pct_cr = int(cp_match.group(1)) if cp_match else 0
            if copay_pct_cr == 0:
                has_no_copay = True

        # Check for consumables coverage
        consumables_val = coverage_details.get("consumablesCoverage") or coverage_details.get("consumablesCover")
        cons_str_cr = str(consumables_val).lower() if consumables_val else ""
        has_consumables = cons_str_cr in ["true", "yes", "covered"] or consumables_val is True or "consumable" in str(category_data).lower() and "cover" in str(category_data).lower()

        # Reference claim: Rs.5L hospitalization (industry standard benchmark)
        claim_amount = 500000
        deductions = 0

        # Room rent deduction - calculated from ACTUAL room rent limit
        if not has_no_room_rent_limit and room_rent_limit:
            daily_limit = 0
            # Try extracting numeric daily limit (e.g., "₹5,000 per day")
            amt_match = _cr_re.search(r'[\₹Rs.]*\s*([\d,]+)', str(room_rent_limit))
            if amt_match:
                daily_limit = int(amt_match.group(1).replace(',', ''))
            elif "1%" in rrl_str:
                daily_limit = int(sum_assured * 0.01) if sum_assured > 0 else 0
            elif "2%" in rrl_str:
                daily_limit = int(sum_assured * 0.02) if sum_assured > 0 else 0
            # Calculate proportionate deduction with actual limit
            if daily_limit > 0:
                metro_room_rate = 12000  # Typical metro private hospital room rate
                if daily_limit < metro_room_rate:
                    room_days = 5
                    room_gap = (metro_room_rate - daily_limit) * room_days
                    proportionate = int(claim_amount * (1 - daily_limit / metro_room_rate) * 0.3)
                    deductions += room_gap + proportionate
            elif rrl_str:
                # Room rent is limited but can't parse exact amount
                deductions += int(claim_amount * 0.08)

        # Co-pay deduction - using ACTUAL copay percentage
        if not has_no_copay and copay_pct_cr > 0:
            deductions += int(claim_amount * copay_pct_cr / 100)

        # Consumables - 5% of claim amount (industry standard 10-15% of bills)
        if not has_consumables:
            deductions += int(claim_amount * 0.05)

        insurance_pays = max(0, claim_amount - deductions)
        you_pay = claim_amount - insurance_pays

        claim_reality["claimAmount"] = claim_amount
        claim_reality["insurancePays"] = insurance_pays
        claim_reality["youPay"] = you_pay

        if you_pay == 0:
            claim_reality["oneLiner"] = "Excellent! Full claim amount covered with no out-of-pocket expenses."
        elif you_pay <= 30000:
            claim_reality["oneLiner"] = "Very good coverage with minimal out-of-pocket expenses."
        elif you_pay <= 75000:
            claim_reality["oneLiner"] = f"Good coverage but ~₹{you_pay:,} out-of-pocket on a ₹5L claim due to policy limits."
        elif you_pay <= 150000:
            claim_reality["oneLiner"] = f"₹{you_pay:,} out-of-pocket on a ₹5L claim. Room rent caps and co-pay are the main contributors."
        else:
            claim_reality["oneLiner"] = f"₹{you_pay:,} out-of-pocket on a ₹5L claim. Consider upgrading room rent and co-pay terms at renewal."
    elif "motor" in policy_type_lower or "car" in policy_type_lower:
        # Motor insurance claim reality - uses actual policy values
        from datetime import datetime as _dt_motor
        coverage_details = category_data.get("coverageDetails", {})
        vehicle_details_cr = category_data.get("vehicleDetails", {}) or {}
        add_on_cr = category_data.get("addOnCovers", {}) or {}
        compulsory_deductible = int(coverage_details.get("compulsoryDeductible", 0) or 0)
        voluntary_deductible = int(coverage_details.get("voluntaryDeductible", 0) or 0)
        has_zero_dep = bool(add_on_cr.get("zeroDepreciation")) or bool(coverage_details.get("zeroDepreciation")) or "zero" in str(category_data).lower() and "depreciation" in str(category_data).lower()

        claim_amount_motor = 100000  # Rs.1L repair bill (reference scenario)
        claim_reality["claimAmount"] = claim_amount_motor

        if has_zero_dep:
            total_ded = compulsory_deductible + voluntary_deductible
            claim_reality["insurancePays"] = max(0, claim_amount_motor - total_ded)
            claim_reality["youPay"] = total_ded
            claim_reality["oneLiner"] = f"Zero depreciation covers full parts cost. You pay only ₹{total_ded:,} deductible."
        else:
            # Calculate depreciation based on actual vehicle age
            mfg_year = vehicle_details_cr.get("manufacturingYear") or vehicle_details_cr.get("yearOfManufacture")
            v_age = 3  # default
            try:
                v_age = _dt_motor.now().year - int(str(mfg_year))
            except (ValueError, TypeError):
                pass
            if v_age <= 1:
                dep_pct = 5
            elif v_age <= 2:
                dep_pct = 10
            elif v_age <= 3:
                dep_pct = 15
            elif v_age <= 4:
                dep_pct = 20
            else:
                dep_pct = 25
            depreciation_loss = int(claim_amount_motor * dep_pct / 100)
            total_ded = compulsory_deductible + voluntary_deductible + depreciation_loss
            claim_reality["insurancePays"] = max(0, claim_amount_motor - total_ded)
            claim_reality["youPay"] = total_ded
            claim_reality["oneLiner"] = f"~{dep_pct}% depreciation (₹{depreciation_loss:,}) + ₹{compulsory_deductible + voluntary_deductible:,} deductible = ₹{total_ded:,} out-of-pocket on a ₹1L claim."
    elif "life" in policy_type_lower or "term" in policy_type_lower:
        claim_reality["claimAmount"] = sum_assured
        claim_reality["insurancePays"] = sum_assured
        claim_reality["youPay"] = 0
        claim_reality["oneLiner"] = "Full sum assured paid to nominee on valid claim."
    else:
        # Generic
        claim_reality["insurancePays"] = int(sum_assured * 0.9)
        claim_reality["youPay"] = int(sum_assured * 0.1)
        claim_reality["oneLiner"] = "Refer to policy terms for claim settlement details."

    # ==================== COVERAGE GAPS TABLE ====================
    coverage_gaps_table = []

    if _is_pa:
        # Personal Accident specific gaps table
        coverage_details = category_data.get("coverageDetails", {})
        _pa_tone = "complimentary" if _is_company_pa else "standalone"

        # 1. Sum Insured
        if _is_company_pa:
            si_status, si_type = "Included", "success"
            si_details = f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{sum_assured:,} is provided as a complimentary benefit under this policy, without any additional premium."
        else:
            # Standalone PA: evaluate against recommended 10x income
            if sum_assured >= 2500000:
                si_status, si_type = "Excellent", "success"
                si_details = f"PA Sum Insured of Rs.{sum_assured:,} provides strong accident protection."
            elif sum_assured >= 1000000:
                si_status, si_type = "Good", "success"
                si_details = f"PA Sum Insured of Rs.{sum_assured:,}. Consider increasing to 10x annual income for optimal protection."
            elif sum_assured >= 500000:
                si_status, si_type = "Moderate", "warning"
                si_details = f"PA Sum Insured of Rs.{sum_assured:,} may be insufficient. Recommended: at least Rs.10,00,000 (10x income)."
            else:
                si_status, si_type = "Low", "danger"
                si_details = f"PA Sum Insured of Rs.{sum_assured:,} is below recommended levels. Consider upgrading to at least Rs.10,00,000."

        coverage_gaps_table.append({"area": "PA Sum Insured", "status": si_status, "statusType": si_type, "details": si_details})

        # 2. Accidental Death Benefit
        ad_data = coverage_details.get("accidentalDeath", {})
        if isinstance(ad_data, dict):
            ad_pct = ad_data.get("benefitPercentage", 100)
            has_di = ad_data.get("doubleIndemnity", {}).get("applicable", False)
            if _is_company_pa:
                ad_details = f"Accidental Death benefit of \u20b9{sum_assured:,} ({ad_pct}% of SI) is payable to the nominee under this complimentary PA cover." + (" Double indemnity applicable for public transport accidents." if has_di else "")
            else:
                ad_details = f"Rs.{sum_assured:,} ({ad_pct}% of SI) paid to nominee on accidental death." + (" Double indemnity for public transport accidents." if has_di else "")
        else:
            ad_benefit_str = str(coverage_details.get("accidentalDeathCover") or ad_data or "100% of SI")
            ad_details = f"Accidental death benefit: {ad_benefit_str}. Paid to nominee."

        coverage_gaps_table.append({"area": "Accidental Death", "status": "Covered", "statusType": "success", "details": ad_details})

        # 3. Permanent Disability
        ptd_data = coverage_details.get("permanentTotalDisability", {})
        ppd_data = coverage_details.get("permanentPartialDisability", {})
        ptd_covered = ptd_data.get("covered", True) if isinstance(ptd_data, dict) else bool(ptd_data)
        ppd_covered = ppd_data.get("covered", True) if isinstance(ppd_data, dict) else bool(ppd_data)

        if ptd_covered and ppd_covered:
            disability_status, disability_type = "Fully Covered", "success"
            ppd_count = len(ppd_data.get("schedule", [])) if isinstance(ppd_data, dict) else 0
            disability_details = f"PTD: 100% of SI (Rs.{sum_assured:,}). PPD: As per IRDAI schedule ({ppd_count} conditions)."
        elif ptd_covered:
            disability_status, disability_type = "PTD Covered", "success"
            disability_details = f"PTD: 100% of SI (Rs.{sum_assured:,}) for permanent total disability."
        elif ppd_covered:
            disability_status, disability_type = "PPD Covered", "success"
            disability_details = "Partial disability covered as per IRDAI schedule."
        else:
            disability_status, disability_type = "Check Policy", "info"
            disability_details = "Disability benefits are typically included in PA covers. Check your policy document."

        coverage_gaps_table.append({"area": "Permanent Disability", "status": disability_status, "statusType": disability_type, "details": disability_details})

        # 4. TTD Benefit
        ttd_data = coverage_details.get("temporaryTotalDisability", {})
        ttd_covered = ttd_data.get("covered", False) if isinstance(ttd_data, dict) else bool(ttd_data)
        if ttd_covered:
            ttd_details = f"TTD benefit of Rs.{ttd_data.get('benefitAmount', 0):,.0f}/{ttd_data.get('benefitType', 'week')} for up to {ttd_data.get('maximumWeeks', 52)} weeks — income support during recovery."
        elif _is_company_pa:
            ttd_details = "Temporary Total Disability benefit is not included under this complimentary PA cover."
        else:
            ttd_details = "TTD (income replacement during recovery) is not covered. Consider adding TTD benefit for income protection during disability."

        coverage_gaps_table.append({
            "area": "Temporary Disability (TTD)",
            "status": "Covered" if ttd_covered else ("Not Included" if _is_company_pa else "Not Covered"),
            "statusType": "success" if ttd_covered else ("info" if _is_company_pa else "danger"),
            "details": ttd_details
        })

        # 5. Medical Expenses
        medical_data = coverage_details.get("medicalExpenses", {})
        medical_covered = medical_data.get("covered", False) if isinstance(medical_data, dict) else bool(medical_data)
        if medical_covered:
            pct = medical_data.get("limitPercentage", 0) if isinstance(medical_data, dict) else 0
            medical_details = f"Medical expenses covered ({pct}% of SI)."
        elif _is_company_pa:
            medical_details = "Accident-related medical expenses are covered under your separate health insurance policy."
        else:
            medical_details = "Accident medical expenses are not covered. Consider adding medical expenses cover or ensure your Health Insurance covers accident treatment."

        coverage_gaps_table.append({
            "area": "Medical Expenses",
            "status": "Covered" if medical_covered else ("Via Health Insurance" if _is_company_pa else "Not Covered"),
            "statusType": "success" if medical_covered else ("info" if _is_company_pa else "warning"),
            "details": medical_details
        })

    elif "health" in policy_type_lower or "medical" in policy_type_lower:
        coverage_details = category_data.get("coverageDetails", {})
        waiting_periods = category_data.get("waitingPeriods", {})
        policy_history = category_data.get("policyHistory", {})

        # 1. Room Rent Limit
        room_rent_limit = coverage_details.get("roomRentLimit", "No Sub-limits")
        has_room_rent_limit = room_rent_limit and "no" not in str(room_rent_limit).lower()
        if has_room_rent_limit:
            room_rent_details = f"Your policy has a Room Rent limit of {room_rent_limit}. This means if you choose a room with higher rent than this limit, you will have to pay the excess amount from your pocket. Additionally, other expenses like doctor fees, medicines, and surgery charges may also be proportionally reduced based on the room rent ratio. For example, if room rent limit is Rs.5,000 but you choose a Rs.10,000 room, your entire claim payout could be reduced by 50%. Always choose a room within your policy's limit to avoid out-of-pocket expenses."
        else:
            room_rent_details = "Your policy has NO Room Rent sub-limits, which is excellent! This means you can choose any room category (Single AC, Deluxe, Suite) during hospitalization without worrying about proportional deductions. The insurer will pay the full room rent regardless of which room you choose. This is a significant advantage as many policies with room rent limits end up paying only 50-60% of the total bill."

        coverage_gaps_table.append({
            "area": "Room Rent Limit",
            "status": "Limited" if has_room_rent_limit else "No Limits",
            "statusType": "warning" if has_room_rent_limit else "success",
            "details": room_rent_details
        })

        # 2. Sum Insured Adequacy
        if sum_assured >= total_protection_needed:
            si_status = "Adequate"
            si_type = "success"
            si_details = f"Your Sum Insured of Rs.{sum_assured:,} meets or exceeds the recommended coverage of Rs.{total_protection_needed:,} based on your profile. This should be sufficient to cover most medical emergencies including major surgeries, ICU stays, and treatments at premium hospitals. Your coverage provides good financial protection against healthcare inflation and rising treatment costs."
        elif sum_assured >= total_protection_needed * 0.6:
            si_status = "Moderate"
            si_type = "warning"
            si_details = f"Your Sum Insured of Rs.{sum_assured:,} is moderately adequate but falls short of the recommended Rs.{total_protection_needed:,}. While it may cover routine hospitalizations, major procedures like heart surgery (Rs.3-5L), cancer treatment (Rs.10-20L), or organ transplants (Rs.15-30L) could exhaust your coverage quickly. Consider increasing your Sum Insured or adding a Super Top-up policy to bridge the gap."
        else:
            si_status = "Insufficient"
            si_type = "danger"
            si_details = f"Your Sum Insured of Rs.{sum_assured:,} is significantly below the recommended Rs.{total_protection_needed:,}. With medical inflation at 14% annually, this coverage may be exhausted quickly during a major hospitalization. Critical treatments, extended ICU stays, or treatments at top hospitals could leave you with substantial out-of-pocket expenses. Strongly recommend increasing coverage or adding a Super Top-up policy immediately."

        coverage_gaps_table.append({
            "area": "Sum Insured Adequacy",
            "status": si_status,
            "statusType": si_type,
            "details": si_details
        })

        # 3. Pre-Existing Disease Coverage
        ped_waiting = waiting_periods.get("preExistingDiseaseWaiting", "48 months")
        first_enrollment = policy_history.get("firstEnrollmentDate") or policy_history.get("insuredSinceDate")
        ped_status = "Waiting"
        ped_type = "warning"
        ped_details = str(ped_waiting)

        # Check if PED waiting is waived via add-ons or portability continuity
        from services.protection_score_calculator import _detect_waiting_waivers as _dww_cgt
        _cgt_waivers = _dww_cgt(category_data)

        # Check if policy explicitly states "No waiting period" or similar
        ped_waiting_str = str(ped_waiting).lower() if ped_waiting else ""
        if (_cgt_waivers["ped"]
            or "no waiting" in ped_waiting_str or "not applicable" in ped_waiting_str
            or "waived" in ped_waiting_str or "nil" in ped_waiting_str or ped_waiting_str == "0"):
            ped_status = "No Waiting Period"
            ped_type = "success"
            if _cgt_waivers["ped"] and _cgt_waivers["reason"]:
                ped_details = f"Excellent! Your policy has NO waiting period for Pre-Existing Diseases (PED). {_cgt_waivers['reason']}. This means conditions like diabetes, hypertension, thyroid disorders, or any other health issues you had before buying this policy are covered from day one. You can claim for any hospitalization related to your existing health conditions immediately."
            else:
                ped_details = "Excellent! Your policy has NO waiting period for Pre-Existing Diseases (PED). This means conditions like diabetes, hypertension, thyroid disorders, or any other health issues you had before buying this policy are covered from day one. This is a significant advantage as most policies have a 2-4 year waiting period during which pre-existing conditions are not covered. You can claim for any hospitalization related to your existing health conditions immediately."
        elif first_enrollment:
            try:
                date_formats = ['%d-%b-%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']
                enrollment_date = None
                for fmt in date_formats:
                    try:
                        enrollment_date = dt.strptime(str(first_enrollment).strip()[:11], fmt)
                        break
                    except:
                        continue
                if enrollment_date:
                    months_since = (dt.now() - enrollment_date).days // 30
                    ped_months = 48
                    try:
                        ped_months = int(''.join(filter(str.isdigit, str(ped_waiting)[:3])))
                    except:
                        pass
                    if months_since >= ped_months:
                        ped_status = "Completed"
                        ped_type = "success"
                        ped_details = f"Great news! Your Pre-Existing Disease waiting period of {ped_months} months has been completed. Since you enrolled on {first_enrollment}, you have now crossed the mandatory waiting period. Any hospitalization related to your pre-existing conditions like diabetes, hypertension, heart disease, or other declared conditions will now be covered under your policy. Make sure to keep your policy continuous without any breaks to maintain this benefit."
                    else:
                        remaining_months = ped_months - months_since
                        ped_status = f"{remaining_months} months remaining"
                        ped_type = "warning"
                        ped_details = f"Your Pre-Existing Disease waiting period is still ongoing. You enrolled on {first_enrollment} and have completed {months_since} months out of the required {ped_months} months. You have {remaining_months} months remaining before your pre-existing conditions (diabetes, BP, thyroid, etc.) will be covered. Until then, any hospitalization related to these conditions will NOT be payable. IMPORTANT: Do not switch insurers during this period as the waiting period will restart with a new insurer."
            except:
                ped_details = f"Your policy has a Pre-Existing Disease waiting period of {ped_waiting}. During this time, any hospitalization related to conditions you had before buying this policy (like diabetes, hypertension, heart disease) will NOT be covered. After the waiting period completes, these conditions become eligible for coverage. Ensure you maintain continuous coverage without breaks to complete this waiting period."
        else:
            ped_details = f"Your policy has a Pre-Existing Disease waiting period of {ped_waiting}. During this time, any hospitalization related to conditions you had before buying this policy (like diabetes, hypertension, heart disease) will NOT be covered. After the waiting period completes, these conditions become eligible for coverage. Ensure you maintain continuous coverage without breaks to complete this waiting period."

        coverage_gaps_table.append({
            "area": "Pre-Existing Disease",
            "status": ped_status,
            "statusType": ped_type,
            "details": ped_details
        })

        # 4. Initial Waiting Period
        initial_waiting = waiting_periods.get("initialWaitingPeriod", "30 days")
        initial_waiting_str = str(initial_waiting).lower() if initial_waiting else ""

        # Determine status type and details based on waiting period (also check add-on waivers)
        if (_cgt_waivers["initial"]
            or "no waiting" in initial_waiting_str or "waived" in initial_waiting_str
            or "nil" in initial_waiting_str or initial_waiting_str == "0"):
            initial_status_type = "success"
            initial_details = "Your policy has NO initial waiting period which means coverage starts from day one of policy issuance. This is excellent as you can claim for any hospitalization immediately after the policy is active. Most policies have a 30-day initial waiting period during which only accidents are covered, but your policy provides full coverage from the start. This is especially beneficial if you need immediate medical attention after buying the policy."
        elif "30 day" in initial_waiting_str:
            initial_status_type = "info"
            initial_details = "Your policy has a standard 30-day initial waiting period. During these first 30 days, only hospitalizations due to accidents are covered. Non-emergency illnesses and planned treatments are NOT covered during this period. This is a standard clause in most health insurance policies to prevent adverse selection. After 30 days, you can claim for any illness-related hospitalization as per policy terms."
        else:
            initial_status_type = "warning"
            initial_details = f"Your policy has an initial waiting period of {initial_waiting}. During this time, only accident-related hospitalizations are covered. Any illness, planned surgery, or non-emergency treatment will NOT be covered until this waiting period is over. This is longer than the standard 30-day waiting period. Avoid any planned treatments during this period as claims will be rejected."

        coverage_gaps_table.append({
            "area": "Initial Waiting Period",
            "status": str(initial_waiting),
            "statusType": initial_status_type,
            "details": initial_details
        })

        # 5. No Claim Bonus (NCB) - Eazr Health Specific
        ncb_info = category_data.get("noClaimBonus", {})
        ncb_available = ncb_info.get("available") if isinstance(ncb_info, dict) else ncb_info
        if ncb_available:
            ncb_percentage = ncb_info.get("currentNcbPercentage") or ncb_info.get("percentage") or "10%"
            ncb_status = "Available"
            ncb_type = "success"
            ncb_details = f"Excellent! Your policy includes No Claim Bonus (NCB) benefit. For every claim-free year, your Sum Insured increases by {ncb_percentage} without any extra premium. This is a cumulative bonus that keeps growing up to the maximum limit (usually 50%). NCB is a valuable reward for maintaining good health and not making claims. The accumulated NCB increases your effective coverage over time, providing better protection against rising medical costs. IMPORTANT: If you make a claim, the accumulated NCB may be reduced or lost unless you have NCB Protect add-on."
        else:
            ncb_status = "Not Available"
            ncb_type = "info"
            ncb_details = "Your policy does not include No Claim Bonus (NCB) benefit. NCB is a reward feature where your Sum Insured increases by a percentage (usually 10%) for every claim-free year. Without NCB, your coverage remains constant throughout the policy tenure regardless of your claims history. Many health insurance policies offer NCB as a standard feature to incentivize policyholders to stay healthy and claim-free. Consider upgrading to a policy with NCB feature for long-term coverage growth."

        coverage_gaps_table.append({
            "area": "No Claim Bonus",
            "status": ncb_status,
            "statusType": ncb_type,
            "details": ncb_details
        })

        # 6. Add-on Policies - Eazr Health Specific
        add_on_policies = category_data.get("addOnPolicies", {})
        has_add_ons = add_on_policies.get("hasAddOn", False)
        add_on_list = add_on_policies.get("addOnPoliciesList", []) if isinstance(add_on_policies, dict) else []

        if has_add_ons and add_on_list:
            add_on_names = [ao.get("addOnName", "") for ao in add_on_list if isinstance(ao, dict)]
            add_on_count = len(add_on_names)
            add_on_status = f"{add_on_count} Add-ons"
            add_on_type = "success"
            add_on_details = f"Your policy includes {add_on_count} valuable add-on covers: {', '.join(add_on_names)}. These add-ons enhance your base health insurance coverage with additional benefits like Claim Shield (protects your NCB), International Coverage (covers medical emergencies abroad), Inflation Shield (increases coverage to counter medical inflation), and Covid Care (covers COVID-19 treatment at home). Add-ons provide comprehensive protection beyond the base policy and are designed to address specific healthcare needs. Review each add-on's benefits to understand the enhanced coverage you have."
        else:
            add_on_status = "None"
            add_on_type = "info"
            add_on_details = "Your policy does not include any add-on covers. Add-ons are optional enhancements that provide additional benefits beyond the base policy. Popular add-ons include: Care Shield (claim protection & restoration benefits), International Coverage (medical emergencies abroad), Universal Shield (NCB protect + inflation shield), and Covid Care (home treatment & tele-consultation). Consider adding relevant add-ons based on your healthcare needs, travel frequency, and family requirements for comprehensive protection."

        coverage_gaps_table.append({
            "area": "Add-on Policies",
            "status": add_on_status,
            "statusType": add_on_type,
            "details": add_on_details
        })

        # 7. Restoration Benefit - Eazr Health Specific
        restoration_benefit = coverage_details.get("restoration")
        restoration_amount = coverage_details.get("restorationAmount", "")

        if restoration_benefit:
            restoration_status = "Available"
            restoration_type = "success"
            restoration_details = f"Excellent! Your policy includes Restoration Benefit ({restoration_amount or '100% of Sum Insured'}). This means if you exhaust your Sum Insured during a policy year, the insurer will restore the coverage amount (usually once per policy year) for subsequent claims. For example, if you have Rs.1 Crore SI and exhaust it in March, your coverage gets restored and you can claim again during the same policy year. This is extremely valuable for critical illnesses or multiple hospitalizations in a year. Restoration benefit effectively doubles your protection for the policy year."
        else:
            restoration_status = "Not Available"
            restoration_type = "warning"
            restoration_details = "Your policy does NOT include Restoration Benefit. This means once you exhaust your Sum Insured during a policy year, no further claims can be made until the policy renews. If you have a major illness that exhausts your coverage early in the year and then require hospitalization again later, you will have to pay from your pocket. Restoration benefit replenishes your Sum Insured (usually 100% once per year) allowing multiple claims during the same policy year. Consider upgrading to a policy with Restoration benefit for comprehensive annual coverage."

        coverage_gaps_table.append({
            "area": "Restoration Benefit",
            "status": restoration_status,
            "statusType": restoration_type,
            "details": restoration_details
        })

        # 8. Sub-Limits Check - Eazr Health Specific
        sub_limits = category_data.get("subLimits", {})
        cataract_limit = sub_limits.get("cataractLimit", "No Limit")
        joint_limit = sub_limits.get("jointReplacementLimit", "No Limit")

        if cataract_limit == "No Limit" and joint_limit == "No Limit":
            sub_limits_status = "No Sub-limits"
            sub_limits_type = "success"
            sub_limits_details = "Excellent! Your policy has NO sub-limits on any treatments or procedures. This means the insurer will pay up to your Sum Insured for any covered medical expense without imposing internal caps. For example, cataract surgery, joint replacement, heart surgery, cancer treatment - all are covered up to your SI without any percentage-based restrictions. Sub-limits are restrictive clauses in many policies that cap payouts for specific procedures regardless of your overall SI. No sub-limits gives you complete flexibility and coverage for any medical condition."
        else:
            limits_list = []
            if cataract_limit != "No Limit":
                limits_list.append(f"Cataract: {cataract_limit}")
            if joint_limit != "No Limit":
                limits_list.append(f"Joint Replacement: {joint_limit}")
            other_limits = sub_limits.get("otherSubLimits", [])
            if other_limits and isinstance(other_limits, list):
                limits_list.extend(other_limits)

            sub_limits_status = f"{len(limits_list)} Sub-limits"
            sub_limits_type = "warning"
            sub_limits_details = f"Your policy has {len(limits_list)} sub-limits: {', '.join(limits_list)}. Sub-limits are internal caps on specific procedures regardless of your overall Sum Insured. For example, if cataract limit is Rs.40,000 but actual cost is Rs.60,000, you pay Rs.20,000 from your pocket even if your SI is Rs.1 Crore. These restrictions reduce the effective coverage for expensive treatments. When renewing, consider policies with NO sub-limits for unrestricted coverage."

        coverage_gaps_table.append({
            "area": "Sub-Limits",
            "status": sub_limits_status,
            "statusType": sub_limits_type,
            "details": sub_limits_details
        })

        # 9. Network Hospitals - Eazr Health Specific
        network_info = category_data.get("networkInfo", {})
        network_count = network_info.get("networkHospitalsCount", "")
        cashless = network_info.get("cashlessFacility", True)

        if cashless and network_count:
            network_status = "Cashless Available"
            network_type = "success"
            network_details = f"Your policy provides cashless hospitalization at {network_count} network hospitals. Cashless facility means you don't have to pay bills upfront - the insurer settles directly with the hospital. This is crucial during medical emergencies when arranging large amounts can be difficult. Always choose network hospitals for planned procedures to avail cashless benefits. For emergency admissions at non-network hospitals, you can request cashless approval if the condition is life-threatening. Carry your health card and keep insurer's helpline handy."
        elif cashless:
            network_status = "Cashless Available"
            network_type = "success"
            network_details = "Your policy provides cashless hospitalization at network hospitals. Cashless facility means you don't have to pay bills upfront - the insurer settles directly with the hospital. This is crucial during medical emergencies when arranging large amounts can be difficult. Always choose network hospitals for planned procedures to avail cashless benefits. For emergency admissions at non-network hospitals, you can request cashless approval if the condition is life-threatening. Carry your health card and keep insurer's helpline handy."
        else:
            network_status = "Reimbursement Only"
            network_type = "warning"
            network_details = "Your policy may have limited cashless hospitalization network. This means you may need to pay hospital bills upfront and then claim reimbursement. Reimbursement claims involve paperwork, bill collection, and processing time (typically 15-30 days). For planned procedures, verify if your preferred hospital is in the insurer's network. In emergencies, check if cashless can be arranged at nearby network hospitals to avoid upfront payment stress."

        coverage_gaps_table.append({
            "area": "Network Hospitals",
            "status": network_status,
            "statusType": network_type,
            "details": network_details
        })

    elif "motor" in policy_type_lower or "car" in policy_type_lower:
        coverage_details = category_data.get("coverageDetails", {})

        # 1. Zero Depreciation
        has_zero_dep = coverage_details.get("zeroDepreciation", False)
        if has_zero_dep:
            zero_dep_details = "Your policy includes Zero Depreciation cover which means during a claim, the insurer will pay the full cost of replaced parts without deducting depreciation. This is especially valuable for new vehicles as it ensures you don't pay out-of-pocket for age-related value reduction on parts like rubber, plastic, glass, and metal components."
        else:
            zero_dep_details = "Your policy does NOT include Zero Depreciation cover. This means during any claim, depreciation will be deducted from the cost of replaced parts based on their age. For example, if your car is 3 years old, you may have to pay 30-40% of parts cost from your pocket. Strongly recommended to add this add-on, especially for vehicles less than 5 years old."

        coverage_gaps_table.append({
            "area": "Zero Depreciation",
            "status": "Covered" if has_zero_dep else "Not Covered",
            "statusType": "success" if has_zero_dep else "danger",
            "details": zero_dep_details
        })

        # 2. NCB Protection
        has_ncb_protect = coverage_details.get("ncbProtection", False)
        if has_ncb_protect:
            ncb_details = "Your No Claim Bonus (NCB) is protected with this add-on. Even if you make a claim during the policy year, your accumulated NCB discount (up to 50% on premium) will be preserved for the next renewal. This protects years of claim-free driving benefits from being lost due to a single claim."
        else:
            ncb_details = "Your policy does NOT have NCB Protection. If you make any claim during this policy year, you will lose your entire accumulated No Claim Bonus discount. For example, if you have 50% NCB (built over 5 claim-free years), one claim will reset it to 0%, significantly increasing your next year's premium. Consider adding NCB Protect add-on to safeguard your discount."

        coverage_gaps_table.append({
            "area": "NCB Protection",
            "status": "Protected" if has_ncb_protect else "Not Protected",
            "statusType": "success" if has_ncb_protect else "warning",
            "details": ncb_details
        })

        # 3. Roadside Assistance
        has_rsa = coverage_details.get("roadsideAssistance", False)
        if has_rsa:
            rsa_details = "Your policy includes 24x7 Roadside Assistance (RSA). In case of breakdown, flat tyre, battery jump-start, fuel assistance, or minor repairs, you can call the insurer's helpline and get assistance at your location. This also typically includes towing service to the nearest garage if the vehicle cannot be repaired on-spot."
        else:
            rsa_details = "Your policy does NOT include Roadside Assistance (RSA). In case of vehicle breakdown, flat tyre, or battery failure on the road, you will have to arrange for help yourself and bear the towing costs. RSA add-on provides 24x7 emergency support including towing, on-spot repairs, fuel delivery, and flat tyre assistance. Highly recommended for frequent travelers."

        coverage_gaps_table.append({
            "area": "Roadside Assistance",
            "status": "Included" if has_rsa else "Not Included",
            "statusType": "success" if has_rsa else "info",
            "details": rsa_details
        })

        # 4. Engine Protection
        has_engine_protect = coverage_details.get("engineProtection", False)
        if has_engine_protect:
            engine_details = "Your policy includes Engine Protection cover. This covers damage to your engine due to water ingression (hydrostatic lock), oil leakage, or other consequential damages that are typically excluded in standard policies. Essential coverage for areas prone to waterlogging or floods."
        else:
            engine_details = "Your policy does NOT include Engine Protection cover. Standard motor insurance excludes engine damage due to water ingression (hydrostatic lock) which commonly occurs during monsoons when vehicles are driven through waterlogged roads. Engine repairs can cost Rs.50,000 to Rs.2,00,000+. Consider adding this cover if you drive in flood-prone areas."

        coverage_gaps_table.append({
            "area": "Engine Protection",
            "status": "Covered" if has_engine_protect else "Not Covered",
            "statusType": "success" if has_engine_protect else "warning",
            "details": engine_details
        })

        # 5. Personal Accident Cover
        pa_cover = coverage_details.get("personalAccidentCover", 0)
        if pa_cover:
            pa_details = f"Your policy includes Owner-Driver Personal Accident cover of Rs.{pa_cover:,}. This provides compensation to you or your nominee in case of accidental death or permanent disability while driving or traveling in the insured vehicle. This is mandatory as per Motor Vehicles Act."
        else:
            pa_details = "Personal Accident cover for Owner-Driver is mandatory as per Motor Vehicles Act. Please verify that your policy includes at least Rs.15,00,000 PA cover. This provides compensation in case of accidental death or permanent disability while driving the insured vehicle."

        coverage_gaps_table.append({
            "area": "Personal Accident",
            "status": f"Rs.{pa_cover:,}" if pa_cover else "Check Policy",
            "statusType": "success" if pa_cover else "warning",
            "details": pa_details
        })

    elif "life" in policy_type_lower or "term" in policy_type_lower:
        coverage_details = category_data.get("coverageDetails", {})
        riders = category_data.get("riders", [])

        # 1. Death Benefit
        death_benefit_details = f"Your Life Insurance policy provides a Death Benefit (Sum Assured) of Rs.{sum_assured:,} which will be paid as a lump sum to your nominated beneficiary in case of your unfortunate demise during the policy term. This amount should ideally be 10-15 times your annual income to adequately replace your income and cover your family's future financial needs including living expenses, children's education, loan repayments, and retirement planning for your spouse. The claim amount is tax-free under Section 10(10D) of the Income Tax Act."
        coverage_gaps_table.append({
            "area": "Death Benefit",
            "status": f"Rs.{sum_assured:,}",
            "statusType": "success",
            "details": death_benefit_details,
            "category": "Death Benefit",
            "description": death_benefit_details,
            "severity": "low"
        })

        # 2. Critical Illness
        has_ci = any("critical" in str(r).lower() for r in riders) if riders else False
        if has_ci:
            ci_details = "Your policy includes Critical Illness Rider which provides an early payout upon diagnosis of specified critical illnesses like Cancer, Heart Attack, Stroke, Kidney Failure, Major Organ Transplant, and others (typically 30-40 conditions covered). This payout is made while you are still alive and can be used for expensive treatments, lifestyle modifications, or clearing debts. The benefit is usually paid as a lump sum immediately upon diagnosis, helping you focus on recovery without financial stress. This is separate from and in addition to the death benefit."
        else:
            ci_details = "Your policy does NOT include Critical Illness Rider. This means if you are diagnosed with a life-threatening illness like Cancer, Heart Attack, Stroke, or Kidney Failure, you will NOT receive any early payout from this policy. You would have to rely on your health insurance (which may have limits) or personal savings for treatment costs that can run into Rs.20-50 lakhs or more. STRONGLY RECOMMENDED: Add a Critical Illness Rider to get a lump sum payout on diagnosis, which can be used for treatment, income replacement during recovery, or lifestyle changes."

        coverage_gaps_table.append({
            "area": "Critical Illness Rider",
            "status": "Covered" if has_ci else "Not Covered",
            "statusType": "success" if has_ci else "warning",
            "details": ci_details,
            "category": "Critical Illness Rider",
            "description": ci_details,
            "severity": "low" if has_ci else "medium",
            "recommendation": "" if has_ci else "Add Critical Illness Rider for Rs.25-50L cover"
        })

        # 3. Accidental Death
        has_adb = any("accidental" in str(r).lower() or "adb" in str(r).lower() for r in riders) if riders else False
        if has_adb:
            adb_details = f"Your policy includes Accidental Death Benefit (ADB) Rider which provides an ADDITIONAL payout over and above the base Sum Assured if death occurs due to an accident. For example, if your Sum Assured is Rs.{sum_assured:,} and you have ADB for the same amount, your family would receive Rs.{sum_assured*2:,} (double the coverage) in case of accidental death. This extra coverage is crucial as accidents can happen to anyone regardless of age or health, and accidental deaths often occur during peak earning years leaving families financially vulnerable."
        else:
            adb_details = f"Your policy does NOT include Accidental Death Benefit (ADB) Rider. In case of death due to accident, your family will only receive the base Sum Assured of Rs.{sum_assured:,}. Adding ADB Rider would provide ADDITIONAL coverage (typically equal to Sum Assured) specifically for accidental deaths. Since accidents are unpredictable and often happen during peak earning years, having extra coverage for accidental death provides important additional protection for your family. The ADB rider is usually very affordable with premiums of just Rs.500-1000 per lakh of cover."

        coverage_gaps_table.append({
            "area": "Accidental Death Benefit",
            "status": "Covered" if has_adb else "Not Covered",
            "statusType": "success" if has_adb else "info",
            "details": adb_details,
            "category": "Accidental Death Benefit",
            "description": adb_details,
            "severity": "low" if has_adb else "medium",
            "recommendation": "" if has_adb else "Add Accidental Death Benefit Rider"
        })

        # 4. Premium Waiver
        has_waiver = any("waiver" in str(r).lower() for r in riders) if riders else False
        if has_waiver:
            waiver_details = "Your policy includes Premium Waiver Rider which ensures that if you become permanently disabled due to accident or illness and are unable to work, all future premiums will be waived by the insurance company. Your policy will continue to remain active and provide full coverage without you having to pay any more premiums. This is an important safety net as disability can severely impact your earning capacity, and without this rider, you might have to let the policy lapse due to inability to pay premiums, leaving your family unprotected."
        else:
            waiver_details = "Your policy does NOT include Premium Waiver Rider. This means if you become permanently disabled due to accident or illness and cannot earn, you will still have to continue paying premiums to keep the policy active. If you fail to pay premiums, the policy will lapse and your family will lose the life cover protection. Consider adding Premium Waiver Rider which costs very little (typically Rs.200-500 per year) but provides crucial protection - ensuring your policy continues even if you cannot pay premiums due to disability."

        coverage_gaps_table.append({
            "area": "Premium Waiver",
            "status": "Included" if has_waiver else "Not Included",
            "statusType": "success" if has_waiver else "info",
            "details": waiver_details,
            "category": "Premium Waiver on Disability",
            "description": waiver_details,
            "severity": "low" if has_waiver else "low",
            "recommendation": "" if has_waiver else "Consider Premium Waiver Rider for financial security"
        })

    # Key Concerns (prefer enhanced insights, fall back to gaps)
    key_concerns = []
    enhanced_insights = enhanced_insights or {}

    # First, use AI-generated key concerns if available
    ai_concerns = enhanced_insights.get("keyConcerns", [])
    if ai_concerns:
        for idx, concern in enumerate(ai_concerns[:4]):
            if isinstance(concern, str):
                # Extract meaningful title from concern text (first phrase before colon, or first 6 words)
                concern_title = concern.split(":")[0].strip() if ":" in concern else " ".join(concern.split()[:6])
                concern_title = concern_title[:60] if len(concern_title) > 60 else concern_title
                key_concerns.append({
                    "title": concern_title,
                    "brief": concern[:150] + "..." if len(concern) > 150 else concern,
                    "severity": "medium"
                })
            elif isinstance(concern, dict):
                key_concerns.append({
                    "title": concern.get("title", f"Concern {idx + 1}"),
                    "brief": concern.get("description", concern.get("brief", ""))[:150],
                    "severity": concern.get("severity", "medium")
                })

    # If no AI concerns, fall back to gaps
    if not key_concerns:
        for gap in formatted_gaps[:3]:
            if isinstance(gap, dict):
                key_concerns.append({
                    "title": gap.get("title", gap.get("category", "Coverage Gap")),
                    "brief": gap.get("description", "")[:150] + "..." if len(gap.get("description", "")) > 150 else gap.get("description", ""),
                    "severity": gap.get("severity", "medium")
                })

    # PA: Override key_concerns based on company PA vs standalone
    if _is_pa and _is_company_pa:
        key_concerns = [
            {
                "title": "Complimentary PA Cover",
                "brief": f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{sum_assured:,} is provided as a complimentary benefit under this policy, without any additional premium.",
                "severity": "low"
            },
            {
                "title": "Covers Accidents Only",
                "brief": "This PA cover provides benefits for accidental death and disability only. For illness and medical expenses, your health insurance policy is the primary cover.",
                "severity": "low"
            }
        ]
    elif _is_pa and not _is_company_pa:
        # Standalone PA: show real concerns
        _pa_concerns = []
        if sum_assured < 1000000:
            _pa_concerns.append({"title": "Low Sum Insured", "brief": f"PA Sum Insured of Rs. {sum_assured:,} may be insufficient for adequate accident protection. Recommended: 10x annual income.", "severity": "high"})
        _pa_ttd = coverage_details.get("temporaryTotalDisability", {}) if isinstance(coverage_details.get("temporaryTotalDisability"), dict) else {}
        if not _pa_ttd.get("covered"):
            _pa_concerns.append({"title": "No TTD Benefit", "brief": "No income replacement during recovery from an accident. If unable to work, EMIs and expenses continue with no support.", "severity": "high"})
        _pa_concerns.append({"title": "Covers Accidents Only", "brief": "PA insurance covers accidental death and disability only. Ensure you have Health Insurance for illness and Life Insurance for comprehensive protection.", "severity": "low"})
        key_concerns = _pa_concerns if _pa_concerns else key_concerns

    # What You Should Do (from recommendations, categorized by urgency)
    actions = {
        "immediate": None,
        "shortTerm": None,
        "ongoing": None
    }

    for rec in recommendations[:3]:
        if isinstance(rec, dict):
            priority = rec.get("priority", "medium").lower() if isinstance(rec.get("priority"), str) else "medium"
            suggestion = rec.get("suggestion", "")
            brief = suggestion[:100] + "..." if len(suggestion) > 100 else suggestion

            if priority == "high" and not actions["immediate"]:
                actions["immediate"] = {
                    "action": rec.get("category", "Take Action"),
                    "brief": brief
                }
            elif priority == "medium" and not actions["shortTerm"]:
                actions["shortTerm"] = {
                    "action": rec.get("category", "Review Soon"),
                    "brief": brief
                }
            elif not actions["ongoing"]:
                actions["ongoing"] = {
                    "action": rec.get("category", "Monitor"),
                    "brief": brief
                }

    # Policy Strengths (prefer AI-generated strengths, then key benefits)
    policy_strengths = []

    # First, use AI-generated policy strengths if available
    ai_strengths = enhanced_insights.get("policyStrengths", [])
    if ai_strengths:
        for strength in ai_strengths[:4]:
            if isinstance(strength, str):
                policy_strengths.append(strength[:100] + "..." if len(strength) > 100 else strength)
            elif isinstance(strength, dict):
                policy_strengths.append(strength.get("description", strength.get("name", ""))[:100])

    # If no AI strengths, use key benefits
    if not policy_strengths:
        for benefit in key_benefits[:4]:
            if isinstance(benefit, str):
                policy_strengths.append(benefit[:100] + "..." if len(benefit) > 100 else benefit)
            elif isinstance(benefit, dict):
                policy_strengths.append(benefit.get("description", benefit.get("name", ""))[:100])

    # ==================== QUICK REFERENCE ====================
    quick_reference = {}

    if "health" in policy_type_lower or "medical" in policy_type_lower:
        network_info = category_data.get("networkInfo", {})
        quick_reference = {
            "cashlessHospitals": network_info.get("networkHospitalsCount", "Check with insurer"),
            "tpaName": category_data.get("policyIdentification", {}).get("tpaName", ""),
            "claimsHelpline": "See policy document",
            "renewalDate": category_data.get("policyIdentification", {}).get("renewalDate", "")
        }
    elif "motor" in policy_type_lower or "car" in policy_type_lower:
        quick_reference = {
            "garageNetwork": "Pan India network garages",
            "claimsHelpline": "See policy document",
            "renewalDate": category_data.get("policyIdentification", {}).get("renewalDate", ""),
            "idv": sum_assured
        }
    elif "life" in policy_type_lower or "term" in policy_type_lower:
        quick_reference = {
            "policyTerm": category_data.get("coverageDetails", {}).get("policyTerm", ""),
            "premiumPayingTerm": category_data.get("coverageDetails", {}).get("premiumPayingTerm", ""),
            "claimsHelpline": "See policy document",
            "maturityDate": category_data.get("coverageDetails", {}).get("maturityDate", "")
        }

    # ==================== HEALTH INSURANCE SCENARIO SIMULATIONS (H001-H010) ====================
    health_scenarios = []
    health_recommendations = []
    if "health" in policy_type_lower or "medical" in policy_type_lower:
        import re as _re

        coverage_det_h = category_data.get("coverageDetails", {}) or {}
        sub_limits_h = category_data.get("subLimits", {}) or {}
        waiting_h = category_data.get("waitingPeriods", {}) or {}
        copay_h = category_data.get("copayDetails", {}) or {}
        benefits_h = category_data.get("benefits", {}) or {}
        premium_h = category_data.get("premiumBreakdown", {}) or {}
        ncb_h = category_data.get("noClaimBonus", {}) or {}

        h_si = sum_assured or 0
        h_room_rent = str(coverage_det_h.get("roomRentLimit") or "")
        h_has_no_room_limit = not h_room_rent or any(kw in h_room_rent.lower() for kw in ["no limit", "no capping", "unlimited", "no sub", "single private", "single room"])
        # Check consumables coverage: add-on benefits take priority, then explicit field
        add_on_policies_h = category_data.get("addOnPolicies", {}) or {}
        add_on_list_h = add_on_policies_h.get("addOnPoliciesList", []) or []
        _has_cons_addon_h = (
            bool(add_on_policies_h.get("claimShield"))
            or any(
                any(kw in str(a.get("addOnName", "")).lower() for kw in ["care shield", "claim shield", "consumable"])
                for a in add_on_list_h if isinstance(a, dict)
            )
        )
        # Also check premiumBreakdown.addOnPremiums.otherAddOns for paid consumable add-ons
        _pb_h = category_data.get("premiumBreakdown", {}) or {}
        _ap_h = _pb_h.get("addOnPremiums", {}) or {}
        _oa_h = _ap_h.get("otherAddOns", {}) if isinstance(_ap_h, dict) else {}
        for _aon_h, _apv_h in _oa_h.items():
            _aon_h_lower = str(_aon_h).lower()
            if any(kw in _aon_h_lower for kw in ["claim shield", "care shield", "consumable"]):
                try:
                    if float(_apv_h) > 0:
                        _has_cons_addon_h = True
                except (ValueError, TypeError):
                    pass
        # Explicit field from AI extraction
        _cons_field_h = str(coverage_det_h.get("consumablesCoverage") or coverage_det_h.get("consumablesCover") or "").lower()
        _cons_explicit_h = _cons_field_h in ["covered", "yes", "true", "available", "included"]
        h_consumables = bool(_has_cons_addon_h or _cons_explicit_h)

        # Detect maternity coverage for H004/H005 simulations
        _maternity_field = (coverage_det_h.get("maternityCoverage") or coverage_det_h.get("maternityBenefit")
                           or coverage_det_h.get("maternity") or "")
        _maternity_str = str(_maternity_field).lower() if _maternity_field else ""
        _maternity_waiting = str(waiting_h.get("maternityWaiting", "")).lower()
        _has_maternity = (
            any(kw in _maternity_str for kw in ["covered", "yes", "true", "available", "included"])
            or (_maternity_waiting and _maternity_waiting not in ["", "0", "none", "null", "not applicable", "not covered", "no", "excluded"])
        )
        # Check for explicit exclusion
        if any(kw in _maternity_str for kw in ["not covered", "not available", "excluded", "no", "false"]):
            _has_maternity = False
        h_restoration = coverage_det_h.get("restoration")
        h_has_restoration = bool(h_restoration) if not isinstance(h_restoration, dict) else h_restoration.get("available", False)

        # Extract room rent limit amount
        def _extract_amt(s, default=0):
            m = _re.search(r'[\d,]+', str(s))
            return int(m.group().replace(',', '')) if m else default

        h_room_limit_amt = 0 if h_has_no_room_limit else _extract_amt(h_room_rent)
        h_copay_pct = 0
        general_copay = copay_h.get("generalCopay") or ""
        copay_match = _re.search(r'(\d+)', str(general_copay))
        if copay_match:
            h_copay_pct = int(copay_match.group(1))

        def _calc_scenario(scenario_id, name, description, hospital_stay, total_cost, cost_breakdown, common_gaps, waiting_period=False, waiting_days=0, excluded=False, exclusion_reason=""):
            """Calculate a health scenario against user's policy."""
            total_deductions = 0
            gap_items = []

            # If the scenario is excluded from coverage (e.g., maternity not covered), entire bill is OOP
            if excluded:
                return {
                    "scenarioId": scenario_id,
                    "scenarioName": name,
                    "name": name,
                    "situation": description,
                    "description": description,
                    "hospitalStay": hospital_stay,
                    "waitingPeriodApplicable": False,
                    "waitingDays": 0,
                    "totalBill": total_cost,
                    "totalBillFormatted": f"₹{total_cost:,}",
                    "coveredAmount": 0,
                    "coveredAmountFormatted": "₹0",
                    "outOfPocket": total_cost,
                    "outOfPocketFormatted": f"₹{total_cost:,}",
                    "coveragePercentage": 0,
                    "oopPercentage": 100,
                    "costBreakdown": {
                        "totalCost": total_cost,
                        "totalCostFormatted": f"₹{total_cost:,}",
                        "covered": 0,
                        "coveredFormatted": "₹0",
                        "outOfPocket": total_cost,
                        "outOfPocketFormatted": f"₹{total_cost:,}",
                        "outOfPocketPercent": 100
                    },
                    "gaps": [{"type": "exclusion", "description": exclusion_reason or "Not covered under this policy", "gap": total_cost, "impact": "Entire bill is out-of-pocket"}],
                    "gapsTriggered": [exclusion_reason or "Not covered under this policy"],
                    "verdict": "Not Covered",
                    "verdictColor": "gray"
                }

            # Room rent gap
            if not h_has_no_room_limit and h_room_limit_amt > 0:
                room_days = cost_breakdown.get("room_days", 4)
                actual_rate = cost_breakdown.get("room_rate", 12000)
                if h_room_limit_amt < actual_rate:
                    room_gap = (actual_rate - h_room_limit_amt) * room_days
                    # Proportionate deduction on entire claim
                    deduction_ratio = h_room_limit_amt / actual_rate
                    proportionate_gap = int(total_cost * (1 - deduction_ratio) * 0.5)
                    total_deductions += room_gap + proportionate_gap
                    gap_items.append({
                        "type": "room_rent_limit",
                        "description": f"Room ₹{actual_rate:,}/day vs ₹{h_room_limit_amt:,} limit",
                        "gap": room_gap + proportionate_gap,
                        "impact": "Proportionate deduction on entire claim"
                    })

            # Consumables gap
            consumables_cost = cost_breakdown.get("consumables", 0)
            if consumables_cost > 0 and not h_consumables:
                total_deductions += consumables_cost
                gap_items.append({
                    "type": "consumables",
                    "description": f"₹{consumables_cost:,} consumables not covered",
                    "gap": consumables_cost,
                    "impact": "100% out-of-pocket"
                })

            # Copay
            if h_copay_pct > 0:
                copay_deduction = int(total_cost * h_copay_pct / 100)
                total_deductions += copay_deduction
                gap_items.append({
                    "type": "copay",
                    "description": f"{h_copay_pct}% co-payment applicable",
                    "gap": copay_deduction,
                    "impact": f"₹{copay_deduction:,} co-pay on total bill"
                })

            # Sub-limit gaps
            for sg in common_gaps:
                if sg.get("type") == "sublimit":
                    sublimit_gap = sg.get("typical_gap", 0)
                    total_deductions += sublimit_gap
                    gap_items.append({
                        "type": "sublimit",
                        "description": sg.get("description", ""),
                        "gap": sublimit_gap,
                        "impact": "Direct gap in implant/device cost"
                    })

            # SI adequacy
            if total_cost > h_si:
                si_gap = total_cost - h_si
                total_deductions += si_gap
                gap_items.append({
                    "type": "si_inadequacy",
                    "description": f"Total cost ₹{total_cost:,} exceeds SI ₹{h_si:,}",
                    "gap": si_gap,
                    "impact": "Excess amount entirely out-of-pocket"
                })

            covered = max(0, total_cost - total_deductions)
            out_of_pocket = total_cost - covered
            oop_percent = round((out_of_pocket / total_cost) * 100) if total_cost > 0 else 0

            coverage_percent = 100 - oop_percent

            return {
                "scenarioId": scenario_id,
                "scenarioName": name,
                "name": name,
                "situation": description,
                "description": description,
                "hospitalStay": hospital_stay,
                "waitingPeriodApplicable": waiting_period,
                "waitingDays": waiting_days,
                # Flattened top-level fields for Flutter (spec Section D donut chart)
                "totalBill": total_cost,
                "totalBillFormatted": f"₹{total_cost:,}",
                "coveredAmount": covered,
                "coveredAmountFormatted": f"₹{covered:,}",
                "outOfPocket": out_of_pocket,
                "outOfPocketFormatted": f"₹{out_of_pocket:,}",
                "coveragePercentage": coverage_percent,
                "oopPercentage": oop_percent,
                # Nested breakdown (backward compat)
                "costBreakdown": {
                    "totalCost": total_cost,
                    "totalCostFormatted": f"₹{total_cost:,}",
                    "covered": covered,
                    "coveredFormatted": f"₹{covered:,}",
                    "outOfPocket": out_of_pocket,
                    "outOfPocketFormatted": f"₹{out_of_pocket:,}",
                    "outOfPocketPercent": oop_percent
                },
                "gaps": gap_items,
                # Key gaps as simple string list for Section D card display
                "gapsTriggered": [g["description"] for g in gap_items if "description" in g][:3],
                "verdict": "Fully Covered" if out_of_pocket == 0 else ("Minor Gap" if oop_percent <= 15 else ("Moderate Gap" if oop_percent <= 30 else "Significant Gap")),
                "verdictColor": "green" if out_of_pocket == 0 else ("light_green" if oop_percent <= 15 else ("orange" if oop_percent <= 30 else "gray"))
            }

        # H001: Cardiac Emergency - Angioplasty
        stent_sublimit = _extract_amt(sub_limits_h.get("internalProsthesisLimit", ""), 0)
        h001_sublimit_gaps = []
        if stent_sublimit > 0 and stent_sublimit < 45000 * 2:
            h001_sublimit_gaps.append({"type": "sublimit", "description": f"Stent sublimit ₹{stent_sublimit:,} vs ₹90,000 actual", "typical_gap": max(0, 90000 - stent_sublimit)})
        health_scenarios.append(_calc_scenario(
            "H001", "Cardiac Emergency - Angioplasty with 2 Stents",
            "Heart attack requiring emergency angioplasty with 2 drug-eluting stents",
            "7 days (4 room + 3 ICU)",
            680500,
            {"room_days": 4, "room_rate": 12000, "consumables": 35000},
            h001_sublimit_gaps, waiting_period=False
        ))

        # H002: Cancer - Stage 2/3 Breast
        health_scenarios.append(_calc_scenario(
            "H002", "Cancer Treatment - Stage 2 Breast Cancer",
            "Surgery + Chemotherapy (8 cycles) + Radiation (25 sessions)",
            "6-8 months treatment",
            1451000,
            {"room_days": 10, "room_rate": 12000, "consumables": 50000},
            [], waiting_period=True, waiting_days=90
        ))

        # H003: Knee Replacement Surgery
        joint_sublimit = _extract_amt(sub_limits_h.get("jointReplacementLimit", ""), 0)
        h003_sublimit_gaps = []
        if joint_sublimit > 0 and joint_sublimit < 350000:
            h003_sublimit_gaps.append({"type": "sublimit", "description": f"Joint replacement sublimit ₹{joint_sublimit:,} vs ₹3,50,000 actual", "typical_gap": max(0, 350000 - joint_sublimit)})
        health_scenarios.append(_calc_scenario(
            "H003", "Knee Replacement Surgery",
            "Single knee replacement with imported implant in metro hospital",
            "5-7 days",
            480000,
            {"room_days": 5, "room_rate": 10000, "consumables": 25000},
            h003_sublimit_gaps, waiting_period=True, waiting_days=730
        ))

        # H004: Normal Delivery (Maternity) — check if maternity is covered
        health_scenarios.append(_calc_scenario(
            "H004", "Normal Delivery (Maternity)",
            "Normal delivery in private hospital with standard room",
            "3 days",
            125000,
            {"room_days": 3, "room_rate": 8000, "consumables": 8000},
            [], waiting_period=True, waiting_days=270,
            excluded=not _has_maternity,
            exclusion_reason="Maternity is not covered under this policy"
        ))

        # H005: C-Section Delivery — check if maternity is covered
        health_scenarios.append(_calc_scenario(
            "H005", "C-Section Delivery",
            "Caesarean section in private hospital",
            "5 days",
            200000,
            {"room_days": 5, "room_rate": 10000, "consumables": 15000},
            [], waiting_period=True, waiting_days=270,
            excluded=not _has_maternity,
            exclusion_reason="Maternity is not covered under this policy"
        ))

        # H006: Appendectomy (Emergency)
        health_scenarios.append(_calc_scenario(
            "H006", "Appendectomy (Emergency)",
            "Emergency appendix removal surgery",
            "3 days",
            175000,
            {"room_days": 3, "room_rate": 10000, "consumables": 12000},
            [], waiting_period=False
        ))

        # H007: Dengue Hospitalization
        health_scenarios.append(_calc_scenario(
            "H007", "Dengue Hospitalization",
            "Dengue fever requiring platelet transfusion and monitoring",
            "5 days",
            120000,
            {"room_days": 5, "room_rate": 8000, "consumables": 10000},
            [], waiting_period=False
        ))

        # H008: COVID Hospitalization
        health_scenarios.append(_calc_scenario(
            "H008", "COVID Hospitalization",
            "COVID-19 with oxygen support, moderate severity",
            "10 days (7 room + 3 ICU)",
            550000,
            {"room_days": 7, "room_rate": 10000, "consumables": 40000},
            [], waiting_period=False
        ))

        # H009: Cataract Surgery (Both Eyes)
        cataract_sublimit = _extract_amt(sub_limits_h.get("cataractLimit", ""), 0)
        h009_sublimit_gaps = []
        actual_cataract = 50000 * 2  # Both eyes
        if cataract_sublimit > 0 and cataract_sublimit * 2 < actual_cataract:
            h009_sublimit_gaps.append({"type": "sublimit", "description": f"Cataract sublimit ₹{cataract_sublimit:,}/eye vs ₹50,000 actual", "typical_gap": max(0, actual_cataract - cataract_sublimit * 2)})
        health_scenarios.append(_calc_scenario(
            "H009", "Cataract Surgery (Both Eyes)",
            "Phacoemulsification with premium IOL for both eyes",
            "Day care (2 visits)",
            90000,
            {"room_days": 0, "room_rate": 0, "consumables": 5000},
            h009_sublimit_gaps, waiting_period=True, waiting_days=730
        ))

        # H010: Kidney Stone Treatment
        kidney_sublimit = _extract_amt(sub_limits_h.get("kidneyStoneLimit", ""), 0)
        h010_sublimit_gaps = []
        if kidney_sublimit > 0 and kidney_sublimit < 120000:
            h010_sublimit_gaps.append({"type": "sublimit", "description": f"Kidney stone sublimit ₹{kidney_sublimit:,} vs ₹1,20,000 actual", "typical_gap": max(0, 120000 - kidney_sublimit)})
        health_scenarios.append(_calc_scenario(
            "H010", "Kidney Stone Treatment",
            "ESWL or ureteroscopy for kidney stone removal",
            "2-3 days",
            120000,
            {"room_days": 2, "room_rate": 8000, "consumables": 8000},
            h010_sublimit_gaps, waiting_period=True, waiting_days=365
        ))

        # ==================== HEALTH INSURANCE RECOMMENDATIONS ====================
        h_total_premium = 0
        try:
            h_total_premium = float(premium_h.get("totalPremium") or 0)
        except:
            h_total_premium = 0

        ncb_pct = ncb_h.get("currentNcbPercentage") or ncb_h.get("accumulatedNcbPercentage")
        ncb_amt = ncb_h.get("ncbAmount") or 0
        try:
            ncb_amt = float(str(ncb_amt).replace(',', '').replace('₹', '')) if ncb_amt else 0
        except:
            ncb_amt = 0

        rec_priority = 1

        # R1: NCB Awareness (Quick Win)
        if ncb_pct or ncb_amt > 0:
            effective_si = h_si + ncb_amt
            health_recommendations.append({
                "id": "HR1",
                "priority": rec_priority,
                "category": "quick_win",
                "title": "Your Effective Coverage is Higher!",
                "description": f"With {ncb_pct or 'accumulated'} NCB, effective SI is ₹{effective_si:,.0f} (not just ₹{h_si:,.0f})",
                "action": "No action needed - just be aware",
                "impact": "awareness",
                "ipfEligible": False
            })
            rec_priority += 1

        # R2: Increase Sum Insured (Enhancement)
        if h_si < 1500000:
            health_recommendations.append({
                "id": "HR2",
                "priority": rec_priority,
                "category": "enhancement",
                "title": "Increase Sum Insured",
                "description": f"Current ₹{h_si:,.0f} is below ₹15L recommended for metro family. Major hospitalizations often exceed ₹10L.",
                "estimatedCost": "₹4,000-6,000/year additional",
                "action": "Request at renewal",
                "impact": "high",
                "ipfEligible": True,
                "ipf": {
                    "emiAmount": "₹500/month",
                    "tenure": "6 months"
                }
            })
            rec_priority += 1

        # R3: Add Consumables Coverage (Enhancement)
        if not h_consumables:
            health_recommendations.append({
                "id": "HR3",
                "priority": rec_priority,
                "category": "enhancement",
                "title": "Add Consumables Coverage",
                "description": "Surgical disposables (gloves, syringes, PPE) = 10-15% of hospital bill. Not covered currently.",
                "estimatedCost": "₹800-1,500/year",
                "action": "Add at renewal",
                "impact": "medium",
                "ipfEligible": True
            })
            rec_priority += 1

        # R4: Super Top-up (Gap Fill)
        if h_si < 1500000:
            health_recommendations.append({
                "id": "HR4",
                "priority": rec_priority,
                "category": "gap_fill",
                "title": "Add Super Top-up Policy",
                "description": f"₹25L coverage with ₹{h_si:,.0f} deductible (your current SI). Kicks in when base policy exhausts.",
                "estimatedCost": "₹3,500-8,000/year",
                "action": "Buy separately",
                "impact": "high",
                "ipfEligible": True,
                "ipf": {
                    "emiAmount": "₹375/month",
                    "tenure": "6 months"
                }
            })
            rec_priority += 1

        # R5: Multi-year Premium (Optimization)
        if h_total_premium > 15000:
            health_recommendations.append({
                "id": "HR5",
                "priority": rec_priority,
                "category": "optimization",
                "title": "Switch to Multi-Year Policy",
                "description": f"Lock premium of ₹{h_total_premium:,.0f} for 2-3 years. Save 5-10% on total premium.",
                "estimatedSavings": f"₹{int(h_total_premium * 0.08):,}/year",
                "action": "Check at renewal",
                "impact": "medium",
                "ipfEligible": True
            })
            rec_priority += 1

    # ==================== LIFE INSURANCE RECOMMENDATIONS ====================
    life_recommendations = []
    if "life" in policy_type_lower or "term" in policy_type_lower:
        riders = category_data.get("riders", [])
        bonus_val = category_data.get("bonusValue", {}) or {}
        coverage_det = category_data.get("coverageDetails", {}) or {}
        surrender_val_raw = bonus_val.get("surrenderValue") or 0
        try:
            surrender_val = float(str(surrender_val_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip()) if surrender_val_raw else 0
        except (ValueError, TypeError):
            surrender_val = 0

        policy_term_raw = coverage_det.get("policyTerm", "")
        ppt_raw = coverage_det.get("premiumPayingTerm", "")

        # Detect product sub-type for SVF eligibility
        product_name_lower = (plan_name or "").lower() + " " + policy_type_lower
        is_term_only = any(t in product_name_lower for t in ['term', 'jeevan amar', 'iprotect', 'click2protect', 'saral jeevan bima']) and not any(t in product_name_lower for t in ['endowment', 'ulip', 'money back', 'whole life'])
        is_savings_plan = not is_term_only

        rec_priority = 1

        # Compute annual premium estimate early (used by R1, R3, R6)
        premium_val = 0
        try:
            premium_raw_val = category_data.get("premiumDetails", {}).get("premiumAmount") or 0
            premium_val = float(str(premium_raw_val).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('₹', '').strip()) if premium_raw_val else 0
        except (ValueError, TypeError):
            premium_val = 0
        freq = (category_data.get("premiumDetails", {}).get("premiumFrequency") or "").lower()
        annual_premium_est = premium_val
        if freq == "monthly":
            annual_premium_est = premium_val * 12
        elif freq == "quarterly":
            annual_premium_est = premium_val * 4
        elif freq in ("half-yearly", "semi-annual", "semi_annual"):
            annual_premium_est = premium_val * 2

        # R1: Add Term Cover (if SA < 10x estimated income)
        # Derive income from policy data
        _r1_policyholder = category_data.get("policyholderLifeAssured", {}) or {}
        _r1_extracted_income = 0
        try:
            _r1_inc_raw = _r1_policyholder.get("annualIncome") or _r1_policyholder.get("income") or 0
            _r1_extracted_income = float(str(_r1_inc_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('₹', '').strip()) if _r1_inc_raw else 0
        except (ValueError, TypeError):
            _r1_extracted_income = 0
        _r1_sa_income = sum_assured / 10 if sum_assured > 0 else 0
        _r1_prem_income = annual_premium_est * 10 if annual_premium_est > 0 else 0
        _r1_income = _r1_extracted_income if _r1_extracted_income > 0 else max(_r1_sa_income, _r1_prem_income)
        _r1_recommended = _r1_income * 10 if _r1_income > 0 else sum_assured * 2
        if sum_assured < _r1_recommended and _r1_recommended > 0:
            gap_amount = int(_r1_recommended - sum_assured)
            life_recommendations.append({
                "id": "add_term_cover",
                "priority": rec_priority,
                "category": "Gap Fill",
                "title": "Add Pure Term Insurance",
                "description": f"Your current life cover of Rs.{sum_assured:,} is below the recommended 10x income (~Rs.{_r1_recommended:,.0f}). Consider adding Rs.{gap_amount:,} term cover to adequately protect your family.",
                "impact": "high",
                "ipfEligible": True,
                "action": {
                    "label": "Explore Term Plans",
                    "type": "explore_plans",
                    "planType": "term"
                }
            })
            rec_priority += 1

        # R2: Add Critical Illness Rider
        has_ci = any("critical" in str(r).lower() for r in riders) if riders else False
        if not has_ci:
            _r2_ci_cover = max(500000, int(sum_assured * 0.25))  # CI cover ~25% of SA
            life_recommendations.append({
                "id": "add_ci_rider",
                "priority": rec_priority,
                "category": "Enhancement",
                "title": "Add Critical Illness Coverage",
                "description": f"Your policy does not include Critical Illness coverage. A CI rider (~₹{_r2_ci_cover/100000:.0f}L) provides a lump sum payout on diagnosis of major illnesses like Cancer, Heart Attack, or Stroke — helping cover treatment costs.",
                "impact": "high",
                "ipfEligible": True,
                "action": {
                    "label": "Add CI Rider",
                    "type": "add_rider",
                    "riderType": "critical_illness"
                }
            })
            rec_priority += 1

        # R3: Add Premium Waiver
        has_waiver = any("waiver" in str(r).lower() for r in riders) if riders else False
        if not has_waiver and premium_val > 0:
            _r3_wop_cost = max(300, int(annual_premium_est * 0.03)) if annual_premium_est > 0 else max(300, int(premium_val * 0.03))  # ~3% of premium
            life_recommendations.append({
                "id": "add_wop_rider",
                "priority": rec_priority,
                "category": "Enhancement",
                "title": "Add Waiver of Premium Rider",
                "description": f"If you become disabled and can't earn, your policy will lapse without a Premium Waiver rider. For ~Rs.{_r3_wop_cost:,}/year, your premiums of Rs.{annual_premium_est:,.0f} will be waived automatically." if annual_premium_est > 0 else f"If you become disabled and can't earn, your policy will lapse without a Premium Waiver rider. For ~Rs.{_r3_wop_cost:,}/year, your premiums will be waived automatically.",
                "impact": "medium",
                "ipfEligible": False,
                "action": {
                    "label": "Add WoP Rider",
                    "type": "add_rider",
                    "riderType": "waiver_of_premium"
                }
            })
            rec_priority += 1

        # R4: SVF Opportunity (for savings plans with surrender value)
        if is_savings_plan and surrender_val >= 50000:
            svf_amount = surrender_val * 0.9
            life_recommendations.append({
                "id": "svf_opportunity",
                "priority": rec_priority,
                "category": "Financing",
                "title": "Surrender Value Financing Available",
                "description": f"Your policy has a surrender value of Rs.{surrender_val:,.0f}. Access up to Rs.{svf_amount:,.0f} (90% of SV) through EAZR SVF without surrendering your policy — keep earning bonuses and maintain your life cover.",
                "impact": "opportunity",
                "svfEligible": True,
                "action": {
                    "label": "Check SVF Eligibility",
                    "type": "svf_check"
                }
            })
            rec_priority += 1

        # R5: Nominee Review
        nominees = category_data.get("nomination", {}).get("nominees") or []
        start_date_str = category_data.get("policyIdentification", {}).get("policyIssueDate") or ""
        policy_age = 0
        if start_date_str:
            try:
                start_dt = dt.strptime(start_date_str.split("T")[0], "%Y-%m-%d")
                policy_age = (dt.now() - start_dt).days // 365
            except:
                pass

        if policy_age >= 3 or not nominees:
            life_recommendations.append({
                "id": "nominee_update",
                "priority": rec_priority,
                "category": "Hygiene",
                "title": "Review Nominee Details",
                "description": f"Your policy is {policy_age} years old. Verify that nominee details are correct and up to date for hassle-free claim settlement." if policy_age >= 3 else "No nominee details found. Add nominee immediately to ensure smooth claim processing.",
                "impact": "low",
                "action": {
                    "label": "Update Nominee",
                    "type": "update_nominee"
                }
            })
            rec_priority += 1

        # R6: IPF for premium payment (if annual premium > threshold)
        if annual_premium_est >= 25000:
            life_recommendations.append({
                "id": "ipf_premium",
                "priority": rec_priority,
                "category": "Financing",
                "title": "Pay Premium in Easy EMIs",
                "description": f"Your annual premium of Rs.{annual_premium_est:,.0f} can be converted to easy monthly EMIs with EAZR Insurance Premium Financing. Never miss a premium payment and prevent policy lapse.",
                "impact": "opportunity",
                "ipfEligible": True,
                "action": {
                    "label": "Finance with EAZR IPF",
                    "type": "ipf_apply"
                }
            })

    # ==================== PERSONAL ACCIDENT RECOMMENDATIONS ====================
    pa_recommendations = []
    pa_light_gaps = []
    if _is_pa:
        if _is_company_pa:
            # Company PA: soft recommendations for free cover
            pa_recommendations = [{
                "id": "keep_active",
                "category": "maintenance",
                "priority": 1,
                "title": "Keep Your PA Cover Active",
                "description": "This PA cover is provided as a complimentary benefit without any additional premium. Keep the policy active to continue availing this benefit.",
                "estimatedCost": "No additional premium",
                "ipfEligible": False,
                "icon": "verified"
            }, {
                "id": "review_coverage",
                "category": "maintenance",
                "priority": 2,
                "title": "Review at Renewal",
                "description": "Review the PA cover details at renewal to stay updated on any changes to benefits, terms, or conditions.",
                "estimatedCost": "No additional cost",
                "ipfEligible": False,
                "icon": "rate_review"
            }]
        else:
            # Standalone PA: real recommendations from v10 helper
            pa_light_gaps = _analyze_pa_gaps_v10(category_data, sum_assured)
            pa_recommendations = _build_pa_recommendations_v10(pa_light_gaps, category_data, sum_assured)

    # ==================== LIFE INSURANCE SCENARIO SIMULATIONS ====================
    life_scenarios = []
    if "life" in policy_type_lower or "term" in policy_type_lower:
        riders = category_data.get("riders", [])
        bonus_val = category_data.get("bonusValue", {}) or {}
        coverage_det = category_data.get("coverageDetails", {}) or {}
        premium_det = category_data.get("premiumDetails", {}) or {}
        nomination_data = category_data.get("nomination", {}) or {}

        # Safe numeric helpers (reuse same approach)
        def _sn(val, default=0):
            if val is None or val == "" or val == "N/A":
                return default
            if isinstance(val, (int, float)):
                return val
            try:
                cleaned = re.sub(r'[^\d.]', '', str(val))
                return float(cleaned) if cleaned else default
            except:
                return default

        sc_sum_assured = _sn(coverage_det.get("sumAssured") or sum_assured)
        sc_accrued_bonus = _sn(bonus_val.get("accruedBonus"))
        sc_surrender_val = _sn(bonus_val.get("surrenderValue"))
        sc_paid_up_val = _sn(bonus_val.get("paidUpValue"))
        sc_loan_val = _sn(bonus_val.get("loanValue"))
        sc_premium = _sn(premium_det.get("premiumAmount") or 0)
        sc_freq = (premium_det.get("premiumFrequency") or "").lower()
        sc_annual_premium = sc_premium
        if sc_freq == "monthly":
            sc_annual_premium = sc_premium * 12
        elif sc_freq == "quarterly":
            sc_annual_premium = sc_premium * 4
        elif sc_freq in ("half-yearly", "semi-annual", "semi_annual"):
            sc_annual_premium = sc_premium * 2

        sc_policy_term_str = coverage_det.get("policyTerm", "")
        sc_ppt_str = coverage_det.get("premiumPayingTerm", "")
        sc_policy_term = 0
        sc_ppt = 0
        try:
            m = re.search(r'(\d+)', str(sc_policy_term_str))
            sc_policy_term = int(m.group(1)) if m else 0
        except:
            pass
        try:
            m = re.search(r'(\d+)', str(sc_ppt_str))
            sc_ppt = int(m.group(1)) if m else 0
        except:
            pass

        sc_start = category_data.get("policyIdentification", {}).get("policyIssueDate") or extracted_data.get("startDate", "")
        sc_years_completed = 0
        sc_years_remaining = 0
        if sc_start:
            try:
                s_dt = dt.strptime(str(sc_start).split("T")[0], "%Y-%m-%d")
                sc_years_completed = max(0, (dt.now() - s_dt).days / 365.25)
                sc_years_remaining = max(0, sc_policy_term - sc_years_completed) if sc_policy_term > 0 else 0
            except:
                pass

        sc_premiums_paid_count = min(sc_ppt, int(sc_years_completed)) if sc_ppt > 0 else int(sc_years_completed)
        sc_premiums_remaining = max(0, sc_ppt - sc_premiums_paid_count) if sc_ppt > 0 else 0
        sc_total_premiums_paid = sc_annual_premium * sc_premiums_paid_count

        # Rider benefits total
        sc_rider_total = 0
        if isinstance(riders, list):
            for r in riders:
                if isinstance(r, dict):
                    sc_rider_total += _sn(r.get("riderSumAssured", 0))

        # Detect savings plan
        pn_lower = (plan_name or "").lower() + " " + policy_type_lower
        sc_is_term = any(t in pn_lower for t in ['term', 'jeevan amar', 'iprotect', 'click2protect', 'saral jeevan bima']) and not any(t in pn_lower for t in ['endowment', 'ulip', 'money back', 'whole life'])
        sc_is_savings = not sc_is_term

        # ===== SCENARIO L001: Premature Death Impact =====
        immediate_needs = 100000  # Funeral/emergency (reference constant)

        # Derive income from policy data: extracted → SA/10 → premium×10
        _sc_policyholder = category_data.get("policyholderLifeAssured", {}) or {}
        _sc_extracted_income = 0
        try:
            _sc_inc_raw = _sc_policyholder.get("annualIncome") or _sc_policyholder.get("income") or 0
            _sc_extracted_income = float(str(_sc_inc_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').replace('₹', '').strip()) if _sc_inc_raw else 0
        except (ValueError, TypeError):
            _sc_extracted_income = 0
        _sc_sa_income = sc_sum_assured / 10 if sc_sum_assured > 0 else 0
        _sc_prem_income = sc_annual_premium * 10 if sc_annual_premium > 0 else 0
        sc_estimated_income = _sc_extracted_income if _sc_extracted_income > 0 else max(_sc_sa_income, _sc_prem_income)
        if sc_estimated_income <= 0:
            sc_estimated_income = sc_sum_assured / 10 if sc_sum_assured > 0 else 0

        emergency_fund = sc_annual_premium * 6 if sc_annual_premium > 0 else int(sc_estimated_income * 0.5)  # 6 months expenses

        # Derive age and replacement years from policy data
        _sc_age = 0
        try:
            _sc_age_raw = _sc_policyholder.get("policyholderAge") or _sc_policyholder.get("lifeAssuredAge") or _sc_policyholder.get("age") or 0
            _sc_age = int(float(str(_sc_age_raw).replace(',', '').strip())) if _sc_age_raw else 0
        except (ValueError, TypeError):
            _sc_age = 0
        income_replacement_years = max(5, 60 - _sc_age) if _sc_age > 0 else max(5, min(25, int(sc_sum_assured / max(1, sc_estimated_income))))
        inflation_factor = 1 + 0.03 * income_replacement_years  # ~3% effective annual inflation
        income_replacement_corpus = int(sc_estimated_income * income_replacement_years * inflation_factor) if sc_estimated_income > 0 else 0
        child_education_corpus = max(500000, int(sc_estimated_income * 5)) if sc_estimated_income > 0 else 0  # 5x income
        spouse_retirement_corpus = max(1000000, int(sc_estimated_income * 10)) if sc_estimated_income > 0 else 0  # 10x income

        total_family_need = immediate_needs + emergency_fund + income_replacement_corpus + child_education_corpus + spouse_retirement_corpus
        existing_coverage = sc_sum_assured + sc_accrued_bonus + sc_rider_total
        family_gap = max(0, total_family_need - existing_coverage)

        l001 = {
            "scenarioId": "L001",
            "name": "Premature Death - Family Financial Impact",
            "description": "What happens to your family's finances if you pass away today",
            "icon": "family_restroom",
            "policyInfo": {
                "policyName": plan_name or insurer_name,
                "policyNumber": category_data.get("policyIdentification", {}).get("policyNumber", ""),
                "sumAssured": sc_sum_assured,
                "sumAssuredFormatted": f"Rs.{sc_sum_assured:,.0f}"
            },
            "familyReceives": {
                "title": "What Your Family Receives",
                "items": [
                    {"label": "Sum Assured", "amount": sc_sum_assured, "formatted": f"Rs.{sc_sum_assured:,.0f}"},
                    {"label": "Accrued Bonuses", "amount": sc_accrued_bonus, "formatted": f"Rs.{sc_accrued_bonus:,.0f}"},
                    {"label": "Rider Benefits (ADB etc.)", "amount": sc_rider_total, "formatted": f"Rs.{sc_rider_total:,.0f}"},
                ],
                "totalPayout": existing_coverage,
                "totalFormatted": f"Rs.{existing_coverage:,.0f}"
            },
            "familyNeeds": {
                "title": "What Your Family Actually Needs",
                "items": [
                    {"label": "Immediate Expenses (funeral, emergency)", "amount": immediate_needs, "formatted": f"Rs.{immediate_needs:,.0f}"},
                    {"label": "Emergency Fund (6 months)", "amount": emergency_fund, "formatted": f"Rs.{emergency_fund:,.0f}"},
                    {"label": f"Income Replacement ({income_replacement_years} years)", "amount": income_replacement_corpus, "formatted": f"Rs.{income_replacement_corpus:,.0f}"},
                    {"label": "Children's Education Corpus", "amount": child_education_corpus, "formatted": f"Rs.{child_education_corpus:,.0f}"},
                    {"label": "Spouse Retirement Corpus", "amount": spouse_retirement_corpus, "formatted": f"Rs.{spouse_retirement_corpus:,.0f}"},
                ],
                "totalNeed": total_family_need,
                "totalFormatted": f"Rs.{total_family_need:,.0f}"
            },
            "gap": {
                "amount": family_gap,
                "formatted": f"Rs.{family_gap:,.0f}",
                "hasGap": family_gap > 0,
                "description": f"Your family would face a shortfall of Rs.{family_gap:,.0f}" if family_gap > 0 else "Your coverage meets estimated family needs"
            },
            "recommendation": {
                "action": f"Consider additional term cover of Rs.{family_gap:,.0f} to close the gap" if family_gap > 0 else "Continue maintaining your current coverage",
                "ipfEligible": True
            }
        }
        life_scenarios.append(l001)

        # ===== SCENARIO L002: Surrender Now Analysis (for savings plans) =====
        if sc_is_savings:
            # What you get
            tds_applicable = sc_surrender_val > sc_total_premiums_paid and sc_surrender_val > 0
            tds_amount = (sc_surrender_val - sc_total_premiums_paid) * 0.05 if tds_applicable and (sc_surrender_val - sc_total_premiums_paid) > 0 else 0  # 5% TDS if taxable
            net_surrender = sc_surrender_val - tds_amount

            # What you lose
            future_bonus_years = sc_years_remaining if sc_years_remaining > 0 else 0
            bonus_rate_raw = bonus_val.get("declaredBonusRate", "")
            annual_bonus_est = 0
            if bonus_rate_raw:
                try:
                    rate_match = re.search(r'(\d+)', str(bonus_rate_raw))
                    if rate_match:
                        per_thousand = float(rate_match.group(1))
                        annual_bonus_est = (sc_sum_assured / 1000) * per_thousand
                except:
                    pass
            if annual_bonus_est == 0 and sc_accrued_bonus > 0 and sc_years_completed > 0:
                annual_bonus_est = sc_accrued_bonus / sc_years_completed

            future_bonuses = annual_bonus_est * future_bonus_years
            projected_maturity = sc_sum_assured + sc_accrued_bonus + future_bonuses  # Simplified
            tax_benefit_per_year = min(sc_annual_premium, 150000) * 0.312  # 30% slab + cess
            tax_benefits_lost = tax_benefit_per_year * min(sc_premiums_remaining, future_bonus_years)

            total_value_foregone = sc_sum_assured + sc_accrued_bonus + future_bonuses + tax_benefits_lost

            # Loss on surrender
            loss_on_surrender = sc_total_premiums_paid - sc_surrender_val
            loss_pct = (loss_on_surrender / sc_total_premiums_paid * 100) if sc_total_premiums_paid > 0 else 0

            # SVF alternative
            svf_amount = sc_surrender_val * 0.9

            l002 = {
                "scenarioId": "L002",
                "name": "Surrender Now - Complete Impact Analysis",
                "description": "What you gain and lose by surrendering your policy today",
                "icon": "account_balance_wallet",
                "policyInfo": {
                    "policyName": plan_name or insurer_name,
                    "policyNumber": category_data.get("policyIdentification", {}).get("policyNumber", ""),
                    "premiumsPaid": f"Rs.{sc_total_premiums_paid:,.0f} ({sc_premiums_paid_count} years x Rs.{sc_annual_premium:,.0f})" if sc_annual_premium > 0 else f"Rs.{sc_total_premiums_paid:,.0f}"
                },
                "whatYouGet": {
                    "title": "What You Get",
                    "items": [
                        {"label": "Surrender Value", "amount": sc_surrender_val, "formatted": f"Rs.{sc_surrender_val:,.0f}"},
                        {"label": "TDS (if applicable)", "amount": -tds_amount, "formatted": f"-Rs.{tds_amount:,.0f}"},
                    ],
                    "netAmount": net_surrender,
                    "netFormatted": f"Rs.{net_surrender:,.0f}"
                },
                "whatYouLose": {
                    "title": "What You Lose",
                    "items": [
                        {"label": "Life Protection Lost", "amount": sc_sum_assured, "formatted": f"Rs.{sc_sum_assured:,.0f}"},
                        {"label": "Accrued Bonuses Lost", "amount": sc_accrued_bonus, "formatted": f"Rs.{sc_accrued_bonus:,.0f}"},
                        {"label": f"Future Bonuses (est. {int(future_bonus_years)} years)", "amount": future_bonuses, "formatted": f"Rs.{future_bonuses:,.0f}"},
                        {"label": "Projected Maturity Benefit", "amount": projected_maturity, "formatted": f"Rs.{projected_maturity:,.0f}"},
                        {"label": f"Tax Benefits Lost ({int(min(sc_premiums_remaining, future_bonus_years))} years)", "amount": tax_benefits_lost, "formatted": f"Rs.{tax_benefits_lost:,.0f}"},
                    ],
                    "totalValueForegone": total_value_foregone,
                    "totalFormatted": f"Rs.{total_value_foregone:,.0f}"
                },
                "comparison": {
                    "title": "Comparison",
                    "premiumsPaid": sc_total_premiums_paid,
                    "premiumsFormatted": f"Rs.{sc_total_premiums_paid:,.0f}",
                    "surrenderValue": sc_surrender_val,
                    "surrenderFormatted": f"Rs.{sc_surrender_val:,.0f}",
                    "lossOnSurrender": loss_on_surrender,
                    "lossFormatted": f"Rs.{loss_on_surrender:,.0f}",
                    "lossPercent": round(loss_pct, 1),
                    "lossDescription": f"Rs.{loss_on_surrender:,.0f} ({round(loss_pct, 1)}% of premiums)" if loss_on_surrender > 0 else "No loss - SV exceeds premiums paid"
                },
                "betterAlternative": {
                    "title": "Better Alternative: EAZR Surrender Value Financing",
                    "svfAmount": svf_amount,
                    "svfFormatted": f"Rs.{svf_amount:,.0f}",
                    "svfDescription": f"Access up to Rs.{svf_amount:,.0f} (90% of SV)",
                    "benefits": [
                        f"Keep your Rs.{sc_sum_assured:,.0f} life protection active",
                        f"Continue earning Rs.{annual_bonus_est:,.0f}/year in bonuses" if annual_bonus_est > 0 else "Continue earning bonuses",
                        f"Maturity benefit of Rs.{projected_maturity:,.0f} intact" if projected_maturity > 0 else "Maturity benefit intact",
                        "Tax benefits continue"
                    ],
                    "terms": {
                        "interestRate": "~12% p.a.",
                        "repayment": "Flexible, up to policy maturity"
                    },
                    "cta": [
                        {"label": "Check SVF Eligibility", "action": "svf_check"},
                        {"label": "Apply Now", "action": "svf_apply"}
                    ]
                }
            }
            life_scenarios.append(l002)

        # ===== SCENARIO L003: Loan Comparison =====
        if sc_is_savings and (sc_surrender_val > 0 or sc_loan_val > 0):
            max_policy_loan = sc_surrender_val * 0.9 if sc_surrender_val > 0 else sc_loan_val
            loan_interest = bonus_val.get("loanValue") or category_data.get("keyTerms", {}).get("policyLoanInterestRate", "")
            policy_loan_rate = str(loan_interest) if loan_interest else ""

            l003 = {
                "scenarioId": "L003",
                "name": "Loan Options Comparison",
                "description": "Policy Loan vs Personal Loan vs EAZR SVF — find the best option",
                "icon": "compare_arrows",
                "comparisonTable": [
                    {
                        "option": "Policy Loan",
                        "interestRate": f"{policy_loan_rate} p.a." if policy_loan_rate else "Refer policy terms",
                        "maxAmount": max_policy_loan,
                        "maxFormatted": f"Rs.{max_policy_loan:,.0f}",
                        "impactOnPolicy": "Reduces death benefit if unpaid",
                        "documentation": "Minimal - just policy documents",
                        "processingTime": "3-7 days",
                        "repaymentFlexibility": "Very flexible, can pay at maturity",
                        "pros": ["Low interest rate", "No credit check", "Flexible repayment"],
                        "cons": ["Reduces death benefit", "Interest compounds", "Slow processing"]
                    },
                    {
                        "option": "Personal Loan",
                        "interestRate": "12-18% p.a.",
                        "maxAmount": 0,
                        "maxFormatted": "Based on income",
                        "impactOnPolicy": "None",
                        "documentation": "Income proof, bank statements, CIBIL check",
                        "processingTime": "1-7 days",
                        "repaymentFlexibility": "Fixed EMI mandatory",
                        "pros": ["No impact on policy", "Quick processing"],
                        "cons": ["High interest", "Affects CIBIL", "Fixed EMI burden"]
                    },
                    {
                        "option": "EAZR SVF",
                        "interestRate": "10-14% p.a.",
                        "maxAmount": sc_surrender_val * 0.9 if sc_surrender_val > 0 else 0,
                        "maxFormatted": f"Rs.{sc_surrender_val * 0.9:,.0f}" if sc_surrender_val > 0 else "Based on SV",
                        "impactOnPolicy": "Policy assigned but remains active",
                        "documentation": "Policy documents only",
                        "processingTime": "24-72 hours",
                        "repaymentFlexibility": "Flexible, policy-backed",
                        "pros": [
                            "Policy continues earning bonuses",
                            "Death benefit intact",
                            "No impact on credit score",
                            "Fast processing"
                        ],
                        "cons": ["Policy assigned to EAZR during loan tenure"],
                        "recommended": True
                    }
                ],
                "verdict": {
                    "recommended": "EAZR SVF",
                    "reason": "Best combination of competitive interest rate, fast processing, and no impact on death benefit or credit score"
                }
            }
            life_scenarios.append(l003)

        # ===== SCENARIO L004: Continue vs Paid-Up =====
        if sc_is_savings and sc_annual_premium > 0:
            # Continue scenario
            remaining_premiums_total = sc_annual_premium * sc_premiums_remaining
            projected_maturity_continue = sc_sum_assured + sc_accrued_bonus + (annual_bonus_est * sc_years_remaining) if annual_bonus_est > 0 else sc_sum_assured + sc_accrued_bonus
            total_investment_continue = sc_total_premiums_paid + remaining_premiums_total

            # Paid-up scenario
            paid_up_sa = (sc_premiums_paid_count / sc_ppt * sc_sum_assured) if sc_ppt > 0 else sc_paid_up_val if sc_paid_up_val > 0 else sc_sum_assured * 0.5
            paid_up_maturity = paid_up_sa + sc_accrued_bonus  # No future bonuses on paid-up typically
            premium_saved = remaining_premiums_total

            # Investment of saved premium (at 8% return)
            if sc_years_remaining > 0 and remaining_premiums_total > 0:
                investment_returns = remaining_premiums_total * ((1 + 0.08) ** (sc_years_remaining / 2)) - remaining_premiums_total  # Rough SIP-like return
            else:
                investment_returns = 0

            total_paid_up_value = paid_up_maturity + remaining_premiums_total + investment_returns

            l004 = {
                "scenarioId": "L004",
                "name": "Continue Premiums vs Convert to Paid-Up",
                "description": "Should you keep paying premiums or make the policy paid-up?",
                "icon": "swap_horiz",
                "continueScenario": {
                    "title": "Continue Paying Premiums",
                    "remainingPremiums": sc_premiums_remaining,
                    "remainingAmount": remaining_premiums_total,
                    "remainingFormatted": f"Rs.{remaining_premiums_total:,.0f}",
                    "totalInvestment": total_investment_continue,
                    "totalFormatted": f"Rs.{total_investment_continue:,.0f}",
                    "projectedMaturity": projected_maturity_continue,
                    "maturityFormatted": f"Rs.{projected_maturity_continue:,.0f}",
                    "deathBenefit": sc_sum_assured + sc_accrued_bonus,
                    "deathBenefitFormatted": f"Rs.{sc_sum_assured + sc_accrued_bonus:,.0f}",
                    "pros": [
                        "Full maturity benefit with bonuses",
                        "Full death benefit maintained",
                        "Tax benefits on premiums continue",
                        "Loan eligibility increases"
                    ]
                },
                "paidUpScenario": {
                    "title": "Convert to Paid-Up",
                    "paidUpSA": paid_up_sa,
                    "paidUpFormatted": f"Rs.{paid_up_sa:,.0f}",
                    "paidUpMaturity": paid_up_maturity,
                    "paidUpMaturityFormatted": f"Rs.{paid_up_maturity:,.0f}",
                    "premiumSaved": premium_saved,
                    "savedFormatted": f"Rs.{premium_saved:,.0f}",
                    "investmentReturns": investment_returns,
                    "returnsFormatted": f"Rs.{investment_returns:,.0f}",
                    "totalValue": total_paid_up_value,
                    "totalFormatted": f"Rs.{total_paid_up_value:,.0f}",
                    "reducedDeathBenefit": paid_up_sa,
                    "reducedFormatted": f"Rs.{paid_up_sa:,.0f}",
                    "pros": [
                        "No more premium outflow",
                        "Saved premiums can be invested elsewhere",
                        "Policy continues with reduced cover"
                    ],
                    "cons": [
                        f"Death benefit drops from Rs.{sc_sum_assured:,.0f} to Rs.{paid_up_sa:,.0f}",
                        "No future bonuses added",
                        "Tax benefits on premiums lost",
                        "Reduced loan eligibility"
                    ]
                },
                "verdict": {
                    "recommendation": "Continue" if projected_maturity_continue > total_paid_up_value else "Paid-Up may be better",
                    "reason": f"Continuing premiums projects Rs.{projected_maturity_continue:,.0f} at maturity vs Rs.{total_paid_up_value:,.0f} with paid-up + invest strategy" if projected_maturity_continue > 0 else "Evaluate based on your premium paying capacity",
                    "ipfSuggestion": {
                        "applicable": sc_annual_premium >= 25000,
                        "description": f"If premium of Rs.{sc_annual_premium:,.0f}/year is a burden, consider EAZR IPF to convert to EMIs instead of going paid-up",
                        "cta": {"label": "Explore EAZR IPF", "action": "ipf_apply"}
                    }
                }
            }
            life_scenarios.append(l004)

    # ==================== V10: HEALTH-SPECIFIC NEW STRUCTURES ====================
    health_protection_readiness = None
    health_strengths_v10 = None
    health_gaps_v10 = None
    health_recs_v10 = None
    health_primary_scenario_id = None

    if "health" in policy_type_lower or "medical" in policy_type_lower:
        try:
            from services.protection_score_calculator import calculate_health_scores_detailed, calculate_ipf_emi

            scores_detailed = calculate_health_scores_detailed(
                gaps=formatted_gaps,
                extracted_data={"coverageAmount": sum_assured},
                category_data=category_data,
                insurer_name=insurer_name
            )

            health_protection_readiness = {
                "compositeScore": scores_detailed.get("compositeScore", protection_score),
                "verdict": scores_detailed.get("verdict", {}),
                "scores": scores_detailed.get("scores", {}),
                "analyzedAt": dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            }

            health_strengths_v10 = _get_health_strengths(scores_detailed, category_data)

            health_gaps_v10 = _analyze_health_gaps(
                category_data=category_data,
                sum_assured=sum_assured,
                insurer_name=insurer_name,
                formatted_gaps=formatted_gaps
            )

            # Trust deterministic gap analysis result — if no real structural gaps found,
            # return empty gaps. Do NOT fall back to AI keyConcerns which produce generic,
            # inaccurate placeholders (e.g. "Policy wording not in document", "Network hospitals
            # not listed") that do not represent actual coverage deficiencies.

            _h_members = category_data.get("insuredMembers", []) or category_data.get("membersCovered", []) or []
            health_primary_scenario_id = _select_primary_scenario(_h_members, health_gaps_v10, health_scenarios)

            health_recs_v10 = _build_health_recommendations(health_gaps_v10, category_data, sum_assured)

        except Exception as _v10_err:
            import logging as _logging
            _logging.getLogger(__name__).warning(f"V10 health analysis failed, falling back to V9: {_v10_err}")

    # ==================== V10: LIFE-SPECIFIC NEW STRUCTURES (EAZR_02 Spec) ====================
    life_protection_readiness = None
    life_strengths_v10 = None
    life_gaps_v10 = None
    life_recs_v10 = None
    life_primary_scenario_id = None
    life_svf_opportunity = None

    if ("life" in policy_type_lower or "term" in policy_type_lower) and not ("health" in policy_type_lower):
        try:
            from services.protection_score_calculator import calculate_life_scores_detailed

            life_scores_detailed = calculate_life_scores_detailed(
                extracted_data={"coverageAmount": sum_assured},
                category_data=category_data,
                insurer_name=insurer_name
            )

            life_protection_readiness = {
                "compositeScore": life_scores_detailed.get("compositeScore", protection_score),
                "verdict": life_scores_detailed.get("verdict", {}),
                "productType": life_scores_detailed.get("productType", ""),
                "renderMode": life_scores_detailed.get("renderMode", {}),
                "scores": life_scores_detailed.get("scores", {}),
                "analyzedAt": dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            }

            life_strengths_v10 = _get_life_strengths(life_scores_detailed, category_data)

            life_gaps_v10 = _analyze_life_gaps(
                category_data=category_data,
                sum_assured=sum_assured,
                formatted_gaps=formatted_gaps,
                scores_detailed=life_scores_detailed
            )

            life_primary_scenario_id = _select_life_primary_scenario(life_scores_detailed, life_gaps_v10, life_scenarios)

            life_recs_v10 = _build_life_recommendations_v10(life_gaps_v10, category_data, sum_assured, life_scores_detailed)

            life_svf_opportunity = _build_life_svf_opportunity(category_data, life_scores_detailed)

        except Exception as _v10_life_err:
            import logging as _logging
            _logging.getLogger(__name__).warning(f"V10 life analysis failed, falling back to V9: {_v10_life_err}")

    # ==================== V10: PA-SPECIFIC NEW STRUCTURES (EAZR_04 Spec) ====================
    pa_protection_readiness = None
    pa_strengths_v10 = None
    pa_gaps_v10 = None
    pa_recs_v10 = None
    pa_primary_scenario_id = None
    pa_scenarios = []
    pa_income_gap_check = None
    pa_portfolio_view = None

    if ("accidental" in policy_type_lower or "accident" in policy_type_lower
            or "personal accident" in policy_type_lower
            or policy_type_lower.strip() in ["pa", "p.a.", "p.a"]):
        try:
            from services.protection_score_calculator import calculate_pa_scores_detailed

            pa_scores_detailed = calculate_pa_scores_detailed(
                extracted_data={"coverageAmount": sum_assured},
                category_data=category_data,
                insurer_name=insurer_name
            )

            pa_protection_readiness = {
                "compositeScore": pa_scores_detailed.get("compositeScore", protection_score),
                "verdict": pa_scores_detailed.get("verdict", {}),
                "scores": pa_scores_detailed.get("scores", {}),
                "analyzedAt": dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            }

            pa_strengths_v10 = _get_pa_strengths(pa_scores_detailed, category_data)

            pa_gaps_v10 = _analyze_pa_gaps_v10(
                category_data=category_data,
                sum_assured=sum_assured,
                formatted_gaps=formatted_gaps,
                scores_detailed=pa_scores_detailed
            )

            pa_recs_v10 = _build_pa_recommendations_v10(
                pa_gaps_v10, category_data, sum_assured, pa_scores_detailed
            )

            pa_income_gap_check = _build_pa_income_gap_check(
                category_data, sum_assured, pa_scores_detailed
            )

            pa_portfolio_view = _build_pa_portfolio_view()

            # Generate PA scenario simulations
            _pa_cov = category_data.get("coverageDetails", {}) or {}
            _pa_add_ben = category_data.get("additionalBenefits", {}) or {}
            _pa_income = 0
            if pa_scores_detailed:
                _s1_data = pa_scores_detailed.get("scores", {}).get("s1", {})
                for _f in (_s1_data.get("factors") or []):
                    if "income" in (_f.get("name", "") or "").lower():
                        _pa_income = int(float(_f.get("_derivedIncome", 0) or 0))
                        break
            if _pa_income <= 0:
                _pa_income = sum_assured // 10 if sum_assured > 0 else 500000
            pa_scenarios = _simulate_pa_scenarios(_pa_cov, _pa_add_ben, sum_assured, _pa_income)

            pa_primary_scenario_id = _select_pa_primary_scenario(
                pa_scores_detailed, pa_gaps_v10, pa_scenarios
            )

        except Exception as _v10_pa_err:
            import logging as _logging
            _logging.getLogger(__name__).warning(f"V10 PA analysis failed, falling back to V9: {_v10_pa_err}")

    # Build the light analysis response
    light_analysis = {
        # Policy identification
        "insurerName": insurer_name,
        "planName": plan_name,
        "policyType": policy_type,
        "city": city,

        # Coverage Verdict (backward compat — updated from V10 for health/life/pa)
        "coverageVerdict": {
            "emoji": (health_protection_readiness or life_protection_readiness or pa_protection_readiness or {}).get("verdict", {}).get("emoji", verdict_emoji) if (health_protection_readiness or life_protection_readiness or pa_protection_readiness) else verdict_emoji,
            "label": (health_protection_readiness or life_protection_readiness or pa_protection_readiness or {}).get("verdict", {}).get("label", verdict_label) if (health_protection_readiness or life_protection_readiness or pa_protection_readiness) else verdict_label,
            "oneLiner": (health_protection_readiness or life_protection_readiness or pa_protection_readiness or {}).get("verdict", {}).get("summary", verdict_one_liner) if (health_protection_readiness or life_protection_readiness or pa_protection_readiness) else verdict_one_liner
        },

        # Protection Score (backward compat — now composite from V10 system for health/life/pa)
        "protectionScore": (health_protection_readiness or life_protection_readiness or pa_protection_readiness or {}).get("compositeScore", protection_score) if (health_protection_readiness or life_protection_readiness or pa_protection_readiness) else protection_score,
        "protectionScoreLabel": (health_protection_readiness or life_protection_readiness or pa_protection_readiness or {}).get("verdict", {}).get("label", protection_score_label) if (health_protection_readiness or life_protection_readiness or pa_protection_readiness) else protection_score_label,

        # Claim Reality Check
        "claimRealityCheck": claim_reality,

        # The Numbers That Matter
        "numbersThatMatter": {
            "yourCover": sum_assured,
            "yourNeed": total_protection_needed,
            "gap": protection_gap,
            "gapOneLiner": gap_one_liner
        },

        # Key Concerns (backward compat)
        "keyConcerns": key_concerns,

        # Coverage Strengths — new V10 format for health/life/pa, existing for others
        "coverageStrengths": health_strengths_v10 if health_strengths_v10 is not None else (
            life_strengths_v10 if life_strengths_v10 is not None else (
                pa_strengths_v10 if pa_strengths_v10 is not None
                else [item for item in coverage_gaps_table if item.get("statusType") == "success"])
        ),

        # Coverage Gaps — new V10 format for health/life/pa (with summary+gaps), existing for others
        "coverageGaps": health_gaps_v10 if health_gaps_v10 is not None else (
            life_gaps_v10 if life_gaps_v10 is not None else (
                pa_gaps_v10 if pa_gaps_v10 is not None
                else (_build_pa_coverage_gaps_rich(pa_light_gaps, coverage_gaps_table) if pa_light_gaps
                      else [item for item in coverage_gaps_table if item.get("statusType") in ["warning", "danger", "info"]]))
        ),

        # What You Should Do (backward compat)
        "whatYouShouldDo": actions,

        # Recommendations — new V10 format for health/life/pa, existing for others
        "recommendations": health_recs_v10 if health_recs_v10 is not None else (
            life_recs_v10 if life_recs_v10 is not None else (
                pa_recs_v10 if pa_recs_v10 is not None
                else (health_recommendations if health_recommendations
                      else (life_recommendations if life_recommendations
                            else (pa_recommendations if pa_recommendations else []))))
        ),

        # Scenarios — restructured with primaryScenarioId for health/life/pa, existing for others
        "scenarios": (
            {"primaryScenarioId": health_primary_scenario_id, "simulations": health_scenarios}
            if health_primary_scenario_id is not None
            else ({"primaryScenarioId": life_primary_scenario_id, "simulations": life_scenarios}
                  if life_primary_scenario_id is not None
                  else ({"primaryScenarioId": pa_primary_scenario_id, "simulations": pa_scenarios}
                        if pa_primary_scenario_id is not None
                        else (health_scenarios if health_scenarios
                              else (life_scenarios if life_scenarios else []))))
        ),

        # Policy Strengths (backward compat)
        "policyStrengths": policy_strengths,

        # Quick Reference
        "quickReference": quick_reference,

        # Report URL (will be populated after PDF generation)
        "reportUrl": None,
        "reportError": None,

        # Report metadata (Section F: Download Full Report)
        "reportDate": dt.utcnow().strftime("%Y-%m-%d"),
        "reportFileName": f"EAZR_Analysis_{category_data.get('policyIdentification', {}).get('policyNumber', 'NA')}_{dt.utcnow().strftime('%Y%m%d')}.pdf",
        "reportSubtext": "Detailed scores, all gaps, 10 scenarios, recommendations",
        "analysisVersion": "10.0" if (health_protection_readiness or life_protection_readiness or pa_protection_readiness) else "9.0"
    }

    # Add V10 health-specific field: protectionReadiness (4-score breakdown)
    if health_protection_readiness:
        light_analysis["protectionReadiness"] = health_protection_readiness

    # Add V10 life-specific fields: protectionReadiness (3-score) + svfOpportunity
    if life_protection_readiness:
        light_analysis["protectionReadiness"] = life_protection_readiness
    if life_svf_opportunity:
        light_analysis["svfOpportunity"] = life_svf_opportunity

    # Add V10 PA-specific fields: protectionReadiness (2-score) + incomeGapCheck + portfolioView
    if pa_protection_readiness:
        light_analysis["protectionReadiness"] = pa_protection_readiness
    if pa_income_gap_check:
        light_analysis["incomeGapCheck"] = pa_income_gap_check
    if pa_portfolio_view:
        light_analysis["portfolioView"] = pa_portfolio_view

    return light_analysis


