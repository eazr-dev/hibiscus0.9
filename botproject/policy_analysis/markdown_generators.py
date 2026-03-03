"""Markdown Report Generators
Generate markdown reports for different insurance types.
"""
import logging
from datetime import datetime

from policy_analysis.utils import safe_num, get_score_label

logger = logging.getLogger(__name__)


def _generate_travel_insurance_md(
    light_analysis: dict,
    policy_details: dict,
    category_data: dict
) -> str:
    """
    Generate Markdown content for travel insurance light analysis.
    Travel-specific template with destination costs, Schengen check, adventure assessment.
    """
    insurer_name = light_analysis.get("insurerName", "Insurance Provider")
    trip_info = light_analysis.get("tripInfo", {})
    destination = trip_info.get("destination", "International")
    destination_region = trip_info.get("destinationRegion", "International")
    trip_type = trip_info.get("tripType", "Single Trip")
    trip_duration = trip_info.get("tripDuration", "N/A")

    verdict = light_analysis.get("protectionVerdict", {})
    verdict_label = verdict.get("label", "Adequate Coverage")
    verdict_one_liner = verdict.get("oneLiner", "")
    protection_score = light_analysis.get("protectionScore", 0)
    protection_score_label = light_analysis.get("protectionScoreLabel", "")

    numbers = light_analysis.get("numbersThatMatter", {})
    claim_check = light_analysis.get("claimRealityCheck", {})
    dest_costs = light_analysis.get("destinationCosts", {})
    key_concerns = light_analysis.get("keyConcerns", [])
    actions = light_analysis.get("whatYouShouldDo", {})
    policy_strengths = light_analysis.get("policyStrengths", [])
    schengen = light_analysis.get("schengenCompliance")
    adventure = light_analysis.get("adventureAssessment", {})
    quick_ref = light_analysis.get("quickReference", {})

    report_date = light_analysis.get("reportDate", datetime.utcnow().strftime("%Y-%m-%d"))
    analysis_version = light_analysis.get("analysisVersion", "9.0")

    md_content = f"""# {insurer_name} - Travel Insurance Analysis

**Destination:** {destination} ({destination_region})
**Trip Type:** {trip_type} | **Duration:** {trip_duration} days

---

## Coverage Verdict: {verdict_label}

**Protection Score: {protection_score}/100** ({protection_score_label})

{verdict_one_liner}

---

## The Numbers That Matter

| | |
|---|---|
| Your Medical Cover | ${numbers.get('yourCover', 0):,} |
| Recommended for {destination_region} | ${numbers.get('yourNeed', 0):,} |
| Coverage Gap | ${numbers.get('gap', 0):,} |

{numbers.get('gapOneLiner', '')}

---

## Claim Reality Check

**Scenario:** {claim_check.get('scenario', 'Emergency surgery abroad')}

| | |
|---|---|
| Typical Cost | ${claim_check.get('claimAmount', 0):,} |
| Insurance Pays | ${claim_check.get('insurancePays', 0):,} |
| You Pay | ${claim_check.get('youPay', 0):,} |

{claim_check.get('oneLiner', '')}

---

## Destination Healthcare Costs ({destination_region})

| Treatment | Cost Range |
|---|---|
| ER Visit | {dest_costs.get('erVisit', 'N/A')} |
| Hospital/Day | {dest_costs.get('hospitalDay', 'N/A')} |
| ICU/Day | {dest_costs.get('icuDay', 'N/A')} |
| Air Ambulance | {dest_costs.get('airAmbulance', 'N/A')} |

**Cost Tier:** {dest_costs.get('costTier', 'Moderate')}

"""

    # Schengen compliance section
    if schengen:
        status = "COMPLIANT" if schengen.get("compliant") else "NON-COMPLIANT"
        md_content += f"""---

## Schengen Compliance: {status}

{schengen.get('details', '')}

"""

    # Adventure sports section
    md_content += f"""---

## Adventure Sports: {adventure.get('statusLabel', 'Check Policy')}

{adventure.get('details', 'Check your policy document for adventure sports terms.')}

"""

    # Key Concerns
    if key_concerns:
        md_content += """---

## Key Concerns

"""
        for concern in key_concerns:
            severity = concern.get("severity", "medium").upper()
            md_content += f"**[{severity}]** {concern.get('title', '')}: {concern.get('brief', '')}\n\n"

    # Coverage Strengths
    strengths = light_analysis.get("coverageStrengths", [])
    if strengths:
        md_content += """---

## Coverage Strengths

"""
        for s in strengths:
            if isinstance(s, dict):
                # V10 format: {"title": ..., "reason": ..., "icon": ...}
                if "title" in s and "reason" in s:
                    md_content += f"- **{s.get('title', '')}**: {s.get('reason', '')}\n"
                else:
                    # V9 format: {"area": ..., "status": ..., "details": ...}
                    md_content += f"- **{s.get('area', '')}**: {s.get('status', '')} - {s.get('details', '')}\n"
            elif isinstance(s, str):
                md_content += f"- {s}\n"

    # Coverage Gaps
    gaps_raw = light_analysis.get("coverageGaps", [])
    # V10 format: {"summary": {...}, "gaps": [...]} or V9 format: [list of dicts]
    if isinstance(gaps_raw, dict):
        gaps = gaps_raw.get("gaps", [])
    else:
        gaps = gaps_raw if isinstance(gaps_raw, list) else []
    if gaps:
        md_content += """
---

## Coverage Gaps

"""
        for g in gaps:
            if isinstance(g, dict):
                sev = g.get("severity", "medium").upper()
                title = g.get("title", g.get("area", "Gap"))
                desc = g.get("description", g.get("details", ""))
                md_content += f"- **[{sev}]** {title}: {desc}\n"
            elif isinstance(g, str):
                md_content += f"- {g}\n"

    # Policy Strengths
    if policy_strengths:
        md_content += """
---

## Policy Strengths

"""
        for strength in policy_strengths[:3]:
            md_content += f"- {strength}\n"

    # Scenario Check (EAZR_05 enhancement)
    scenario_highlights = light_analysis.get("scenarioHighlights", [])
    if scenario_highlights:
        md_content += """
---

## Scenario Check

"""
        for sc in scenario_highlights:
            status = sc.get("yourStatus", "unknown")
            status_icon = "PROTECTED" if status == "protected" else "AT RISK"
            md_content += f"- **{sc.get('name', 'Scenario')}**: {status_icon}\n"

    # Scoring Breakdown (EAZR_05 enhancement)
    scoring = light_analysis.get("scoringBreakdown", {})
    if scoring.get("medicalReadiness") or scoring.get("tripProtection"):
        medical_r = scoring.get("medicalReadiness", {})
        trip_p = scoring.get("tripProtection", {})
        md_content += f"""
---

## Scoring Breakdown

| Score | Value | Rating |
|-------|-------|--------|
| Medical Emergency Readiness (60%) | {medical_r.get('score', 'N/A')}/100 | {medical_r.get('label', 'N/A')} |
| Trip Protection (40%) | {trip_p.get('score', 'N/A')}/100 | {trip_p.get('label', 'N/A')} |

"""

    # Quick Reference
    md_content += f"""
---

## Quick Reference

| | |
|---|---|
| Emergency Helpline | {quick_ref.get('emergencyHelpline', 'See policy')} |
| Claims Helpline | {quick_ref.get('claimsHelpline', 'See policy')} |
| Claims Email | {quick_ref.get('claimsEmail', 'See policy')} |
| Policy Expiry | {quick_ref.get('policyExpiry', 'N/A')} |
| Destination | {quick_ref.get('destination', 'N/A')} |

---

*Analysis generated {report_date} | Version {analysis_version}*
"""

    return md_content


def _generate_motor_insurance_md(
    light_analysis: dict,
    policy_details: dict,
    category_data: dict
) -> str:
    """
    Generate Markdown content for MOTOR insurance based on EAZR_Motor_Insurance_Light_Analysis_V9 template.
    """
    # Helper function to format currency
    def format_currency(amount):
        if not amount:
            return "N/A"
        try:
            amount = float(str(amount).replace(",", "").replace("\u20b9", "").replace("Rs.", "").strip())
            if amount >= 10000000:
                return f"\u20b9{amount/10000000:.2f} Cr"
            elif amount >= 100000:
                return f"\u20b9{amount/100000:.2f} L"
            else:
                return f"\u20b9{amount:,.0f}"
        except:
            return str(amount)

    # Map emoji names to actual emojis
    emoji_map = {
        "shield": "\U0001f6e1\ufe0f",
        "warning": "\u26a0\ufe0f",
        "alert": "\U0001f6a8",
        "check": "\u2705",
        "cross": "\u274c"
    }

    # Extract all data from light_analysis
    insurer_name = light_analysis.get("insurerName", "Insurance Provider")
    vehicle_info = light_analysis.get("vehicleInfo", {})
    vehicle_make = vehicle_info.get("make", "N/A")
    vehicle_model = vehicle_info.get("model", "N/A")
    manufacturing_year = vehicle_info.get("year", "N/A")

    verdict = light_analysis.get("protectionVerdict", {})
    verdict_emoji = emoji_map.get(verdict.get("emoji", "warning"), "\u26a0\ufe0f")
    verdict_label = verdict.get("label", "Adequate Coverage")
    verdict_one_liner = verdict.get("oneLiner", "")

    replacement_gap = light_analysis.get("replacementGap", {})
    idv = replacement_gap.get("idv", 0)
    current_on_road_price = replacement_gap.get("currentOnRoadPrice", 0)
    gap = replacement_gap.get("gap", 0)
    has_loan = replacement_gap.get("hasLoan", False)
    outstanding_loan = replacement_gap.get("outstandingLoan", 0)
    loan_warning = replacement_gap.get("loanWarning", "")

    claim_reality = light_analysis.get("claimRealityCheck", {})
    insurance_pays_1l = claim_reality.get("insurancePays", 0)
    you_pay_1l = claim_reality.get("youPay", 0)
    has_zero_dep = claim_reality.get("hasZeroDep", False)
    depreciation_percentage = claim_reality.get("depreciationPercentage", 0)

    key_concerns = light_analysis.get("keyConcerns", [])
    addon_status = light_analysis.get("addOnsStatus", {})

    ncb = light_analysis.get("ncb", {})
    ncb_percentage = ncb.get("percentage", 0)
    ncb_savings = ncb.get("savings", 0)
    ncb_claim_consequence = ncb.get("claimConsequence", "")
    ncb_recommendation = ncb.get("recommendation", "")

    actions = light_analysis.get("whatYouShouldDo", {})
    policy_strengths = light_analysis.get("policyStrengths", [])

    quick_ref = light_analysis.get("quickReference", {})
    claims_helpline = quick_ref.get("claimsHelpline", "See policy document")
    policy_expiry = quick_ref.get("policyExpiry", "N/A")

    report_date = light_analysis.get("reportDate", datetime.utcnow().strftime("%Y-%m-%d"))
    analysis_version = light_analysis.get("analysisVersion", "9.0")

    # Build markdown content
    md_content = f"""# Policy Analysis Summary

**{vehicle_make} {vehicle_model} ({manufacturing_year})**
**Policy: {insurer_name}** | **Valid till: {policy_expiry}**

---

## Coverage Verdict

{verdict_emoji} **{verdict_label}**

{verdict_one_liner}

---

## If Your Car is Gone Tomorrow

| | |
|---|---|
| Insurance pays (IDV) | {format_currency(idv)} |
| Replacement cost (on-road) | {format_currency(current_on_road_price)} |
| **You pay from pocket** | **{format_currency(gap)}** |

"""

    # Add loan warning if applicable
    if has_loan and outstanding_loan > 0:
        md_content += f"""\u26a0\ufe0f Loan outstanding: {format_currency(outstanding_loan)} \u2013 {loan_warning}

"""

    md_content += f"""---

## Claim Reality Check

**On a \u20b91 Lakh repair bill:**

| | |
|---|---|
| Insurance pays | \u20b9{insurance_pays_1l:,} |
| **You pay (depreciation + deductibles)** | **\u20b9{you_pay_1l:,}** |

"""

    # Zero Dep status
    if has_zero_dep:
        md_content += """\u2705 Zero Dep active \u2013 depreciation waived

"""
    else:
        md_content += f"""\u274c No Zero Dep \u2013 {depreciation_percentage}% lost to depreciation

"""

    md_content += """---

## Key Concerns

"""

    # Add key concerns
    if key_concerns and len(key_concerns) > 0:
        for i, concern in enumerate(key_concerns[:3], 1):
            title = concern.get("title", "Coverage Gap")
            brief = concern.get("brief", "")
            md_content += f"""**{i}. {title}**
{brief}

"""
    else:
        md_content += """No critical concerns identified.

"""

    md_content += """---

## Add-Ons Status

| Add-On | Status | Impact |
|--------|--------|--------|
"""

    # Add-ons table
    default_cross = "\u274c"
    zero_dep = addon_status.get("zeroDepreciation", {})
    md_content += f"""| Zero Depreciation | {zero_dep.get('emoji', default_cross)} | {zero_dep.get('impact', 'N/A')} |
"""

    engine = addon_status.get("engineProtection", {})
    md_content += f"""| Engine Protection | {engine.get('emoji', default_cross)} | {engine.get('impact', 'N/A')} |
"""

    ncb_prot = addon_status.get("ncbProtection", {})
    md_content += f"""| NCB Protection | {ncb_prot.get('emoji', default_cross)} | {ncb_prot.get('impact', 'N/A')} |
"""

    rti = addon_status.get("returnToInvoice", {})
    md_content += f"""| Return to Invoice | {rti.get('emoji', default_cross)} | {rti.get('impact', 'N/A')} |
"""

    rsa = addon_status.get("roadsideAssistance", {})
    md_content += f"""| Roadside Assistance | {rsa.get('emoji', default_cross)} | {rsa.get('impact', 'N/A')} |

"""

    md_content += f"""---

## Your NCB

| | |
|---|---|
| Current NCB | **{ncb_percentage}%** |
| Annual savings | \u20b9{ncb_savings:,} |
| If you claim | {ncb_claim_consequence} |

{ncb_recommendation}

---

## What You Should Do

"""

    # Add actions
    immediate = actions.get("immediate")
    renewal = actions.get("renewal")
    ongoing = actions.get("ongoing")

    if immediate:
        md_content += f"""\U0001f534 **{immediate.get('action', 'Take Action')}**
{immediate.get('brief', '')}

"""

    if renewal:
        md_content += f"""\U0001f7e1 **{renewal.get('action', 'Review Soon')}**
{renewal.get('brief', '')}

"""

    if ongoing:
        md_content += f"""\U0001f7e2 **{ongoing.get('action', 'Monitor')}**
{ongoing.get('brief', '')}

"""

    md_content += """---

## Policy Strengths

"""

    # Add strengths
    for strength in policy_strengths[:3]:
        md_content += f"""\u2705 {strength}

"""

    md_content += f"""---

## Quick Reference

| | |
|---|---|
| Claims helpline | {claims_helpline} |
| Policy expires | {policy_expiry} |
| NCB | {ncb_percentage}% |

**In case of accident:**
1. Photos first, move later
2. FIR if third-party involved
3. Call {claims_helpline} within 24 hours

---

*Analysis generated {report_date} | Version {analysis_version}*
"""

    return md_content


def _generate_light_analysis_md(
    light_analysis: dict,
    policy_details: dict,
    category_data: dict
) -> str:
    """
    Generate Markdown content for light policy analysis based on EAZR template.
    This provides a readable summary for display in the app.
    Routes to motor-specific template if it's a motor policy.
    """
    # Extract data from light_analysis
    insurer_name = light_analysis.get("insurerName", "Insurance Provider")
    plan_name = light_analysis.get("planName", "Insurance Plan")

    # Check if this is a motor insurance policy - route to motor-specific template
    if plan_name == "motor" or "motor" in str(plan_name).lower():
        return _generate_motor_insurance_md(light_analysis, policy_details, category_data)
    if plan_name == "travel" or "travel" in str(plan_name).lower():
        return _generate_travel_insurance_md(light_analysis, policy_details, category_data)
    verdict = light_analysis.get("protectionVerdict", {})
    verdict_emoji = verdict.get("emoji", "warning")
    verdict_label = verdict.get("label", "Adequate Coverage")
    verdict_one_liner = verdict.get("oneLiner", "")
    protection_score = light_analysis.get("protectionScore", 0)
    protection_score_label = light_analysis.get("protectionScoreLabel", "")
    numbers = light_analysis.get("numbersThatMatter", {})
    key_concerns = light_analysis.get("keyConcerns", [])
    actions = light_analysis.get("whatYouShouldDo", {})
    policy_strengths = light_analysis.get("policyStrengths", [])
    report_date = light_analysis.get("reportDate", datetime.utcnow().strftime("%Y-%m-%d"))
    analysis_version = light_analysis.get("analysisVersion", "9.0")

    # Extract from policy_details
    sum_insured = policy_details.get("coverageAmount", 0) or policy_details.get("sumAssured", 0)

    # Extract member count
    members = category_data.get("insuredMembers", []) or category_data.get("membersCovered", [])
    member_count = len(members) if members else 1

    # Format sum insured
    def format_currency(amount):
        if not amount:
            return "N/A"
        try:
            amount = float(str(amount).replace(",", "").replace("\u20b9", "").replace("Rs.", "").strip())
            if amount >= 10000000:
                return f"\u20b9{amount/10000000:.2f} Cr"
            elif amount >= 100000:
                return f"\u20b9{amount/100000:.2f} L"
            else:
                return f"\u20b9{amount:,.0f}"
        except:
            return str(amount)

    # Map emoji names to actual emojis
    emoji_map = {
        "shield": "\U0001f6e1\ufe0f",
        "warning": "\u26a0\ufe0f",
        "alert": "\U0001f6a8",
        "check": "\u2705",
        "cross": "\u274c"
    }
    verdict_emoji_char = emoji_map.get(verdict_emoji, "\u26a0\ufe0f")

    # Get city for healthcare context
    city = policy_details.get("city", "Mumbai")

    # Calculate claim scenario (on ₹5L hospital bill)
    # This is a simplified estimation
    room_rent_limit = category_data.get("coverageDetails", {}).get("roomRentLimit", "No Sub-limits")
    has_room_rent_limit = room_rent_limit and "no" not in str(room_rent_limit).lower() and "sub" not in str(room_rent_limit).lower()

    # Estimate out of pocket based on coverage quality
    if protection_score >= 80 and not has_room_rent_limit:
        insurance_pays = 475000  # ₹4.75L
        you_pay = 25000  # ₹25K (copay/deductibles)
        claim_reality_liner = "Excellent coverage with minimal out-of-pocket expenses expected."
    elif protection_score >= 60:
        insurance_pays = 400000  # ₹4L
        you_pay = 100000  # ₹1L
        claim_reality_liner = "Good coverage but some expenses may not be fully covered."
    else:
        insurance_pays = 300000  # ₹3L
        you_pay = 200000  # ₹2L
        claim_reality_liner = "Significant gaps may result in higher out-of-pocket costs."

    # Build coverage gaps section
    coverage_details = category_data.get("coverageDetails", {})
    waiting_periods = category_data.get("waitingPeriods", {})

    # Room rent status
    if has_room_rent_limit:
        room_rent_status = f"Limited to {room_rent_limit}"
        room_rent_emoji = "\u26a0\ufe0f"
    else:
        room_rent_status = "No Limits"
        room_rent_emoji = "\u2705"

    # Sum insured adequacy
    your_need = numbers.get("yourNeed", 5000000)
    if sum_insured >= your_need:
        si_status = "Adequate"
        si_emoji = "\u2705"
    elif sum_insured >= your_need * 0.6:
        si_status = "Moderate"
        si_emoji = "\u26a0\ufe0f"
    else:
        si_status = "Insufficient"
        si_emoji = "\u274c"

    # PED status
    ped_waiting = waiting_periods.get("preExistingDiseaseWaiting", "48 months")
    policy_history = category_data.get("policyHistory", {})
    first_enrollment = policy_history.get("firstEnrollmentDate") or policy_history.get("insuredSinceDate")

    if first_enrollment:
        try:
            from datetime import timedelta
            # Parse enrollment date
            date_formats = ['%d-%b-%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']
            enrollment_date = None
            for fmt in date_formats:
                try:
                    enrollment_date = datetime.strptime(str(first_enrollment).strip()[:11], fmt)
                    break
                except:
                    continue

            if enrollment_date:
                months_since = (datetime.now() - enrollment_date).days // 30
                ped_months = 48  # default
                try:
                    ped_months = int(''.join(filter(str.isdigit, str(ped_waiting)[:3])))
                except:
                    pass

                if months_since >= ped_months:
                    ped_status = "Completed"
                    ped_emoji = "\u2705"
                else:
                    remaining = ped_months - months_since
                    ped_status = f"{remaining} months remaining"
                    ped_emoji = "\u26a0\ufe0f"
            else:
                ped_status = ped_waiting
                ped_emoji = "\u26a0\ufe0f"
        except:
            ped_status = ped_waiting
            ped_emoji = "\u26a0\ufe0f"
    else:
        ped_status = ped_waiting
        ped_emoji = "\u26a0\ufe0f"

    # Waiting period status
    initial_waiting = waiting_periods.get("initialWaitingPeriod", "30 days")
    waiting_status = initial_waiting
    waiting_emoji = "\u2705" if "complete" in str(initial_waiting).lower() else "\u26a0\ufe0f"

    # Get network info
    network_info = category_data.get("networkInfo", {})
    network_count = network_info.get("networkHospitalsCount", "Check with insurer")

    # Get TPA/helpline info
    tpa_name = category_data.get("policyIdentification", {}).get("tpaName")

    # Build MD content
    md_content = f"""# Policy Analysis Summary

**{insurer_name} \u2013 {plan_name}**
**Members: {member_count}** | **Sum Insured: {format_currency(sum_insured)}**

---

## Coverage Verdict

{verdict_emoji_char} **{verdict_label}**

{verdict_one_liner}

**Protection Score: {protection_score}/100** - {protection_score_label}

---

## Claim Reality Check

**On a \u20b95 Lakh hospital bill in {city}:**

| | |
|---|---|
| Insurance pays | {format_currency(insurance_pays)} |
| **You pay from pocket** | **{format_currency(you_pay)}** |

{claim_reality_liner}

---

## Key Concerns

"""

    # Add key concerns
    if key_concerns:
        for i, concern in enumerate(key_concerns[:3], 1):
            severity_emoji = "\U0001f534" if concern.get("severity") == "high" else "\U0001f7e1" if concern.get("severity") == "medium" else "\U0001f7e2"
            md_content += f"""**{i}. {concern.get('title', 'Concern')}** {severity_emoji}
{concern.get('brief', '')}

"""
    else:
        md_content += "No critical concerns identified.\n\n"

    md_content += """---

## Coverage Gaps

| Area | Status |
|------|--------|
"""
    md_content += f"| Room rent limit | {room_rent_emoji} {room_rent_status} |\n"
    md_content += f"| Sum insured adequacy | {si_emoji} {si_status} |\n"
    md_content += f"| Pre-existing coverage | {ped_emoji} {ped_status} |\n"
    md_content += f"| Waiting periods | {waiting_emoji} {waiting_status} |\n"

    md_content += """
---

## What You Should Do

"""

    # Add actions
    if actions.get("immediate"):
        md_content += f"""\U0001f534 **{actions['immediate'].get('action', 'Take Immediate Action')}**
{actions['immediate'].get('brief', '')}

"""

    if actions.get("shortTerm"):
        md_content += f"""\U0001f7e1 **{actions['shortTerm'].get('action', 'Review Soon')}**
{actions['shortTerm'].get('brief', '')}

"""

    if actions.get("ongoing"):
        md_content += f"""\U0001f7e2 **{actions['ongoing'].get('action', 'Monitor')}**
{actions['ongoing'].get('brief', '')}

"""

    md_content += """---

## Policy Strengths

"""

    # Add strengths
    for strength in policy_strengths[:3]:
        md_content += f"\u2705 {strength}\n\n"

    md_content += """---

## Quick Reference

| | |
|---|---|
"""
    md_content += f"| Cashless hospitals | {network_count} |\n"
    if tpa_name:
        md_content += f"| TPA | {tpa_name} |\n"

    md_content += f"""
---

*Analysis generated {report_date} | Version {analysis_version}*
"""

    return md_content
