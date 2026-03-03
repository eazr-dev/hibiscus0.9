"""
Travel Insurance Light Analysis
Builds travel-specific light analysis with destination costs, Schengen compliance,
and V10 protection readiness scoring.
"""
import logging

from policy_analysis.utils import get_score_label as _get_score_label
from policy_analysis.types.travel.helpers import (
    _calculate_travel_medical_readiness,
    _calculate_travel_trip_protection,
    _simulate_travel_scenarios,
    _get_trip_state,
    _build_destination_coverage_check,
    _build_emergency_reference,
    _get_travel_strengths,
    _analyze_travel_gaps_v10,
    _select_travel_primary_scenario,
    _build_travel_recommendations_v10,
)

logger = logging.getLogger(__name__)


def _build_travel_scoring_breakdown(category_data: dict, destination: str, overall_protection_score: int) -> dict:
    """Build 2-sub-score breakdown for travel light analysis per EAZR_05."""
    try:
        coverage_summary = category_data.get("coverageSummary", {})
        medical_cov = category_data.get("medicalCoverage", {})
        trip_prot = category_data.get("tripProtection", {})
        baggage_cov = category_data.get("baggageCoverage", {})
        travellers = category_data.get("travellerDetails", [])

        coverage_with_medical = dict(coverage_summary)
        coverage_with_medical["_medicalCoverage"] = medical_cov

        s1 = _calculate_travel_medical_readiness(coverage_with_medical, destination, travellers)
        s2 = _calculate_travel_trip_protection(coverage_summary, trip_prot, baggage_cov)

        return {
            "medicalReadiness": {
                "score": s1["score"],
                "label": _get_score_label(s1["score"])["label"],
                "weight": "60%"
            },
            "tripProtection": {
                "score": s2["score"],
                "label": _get_score_label(s2["score"])["label"],
                "weight": "40%"
            },
            "overallScore": overall_protection_score
        }
    except Exception:
        return {"medicalReadiness": {"score": 0, "label": "N/A"}, "tripProtection": {"score": 0, "label": "N/A"}}


def _build_travel_scenario_highlights(category_data: dict, destination: str) -> list:
    """Build top 3 scenario status summaries for travel light analysis."""
    try:
        coverage_summary = category_data.get("coverageSummary", {})
        medical_cov = category_data.get("medicalCoverage", {})
        trip_prot = category_data.get("tripProtection", {})
        baggage_cov = category_data.get("baggageCoverage", {})
        exclusions = category_data.get("exclusions", {})

        scenarios = _simulate_travel_scenarios(
            coverage_data=coverage_summary,
            destination=destination,
            trip_protection=trip_prot,
            baggage_coverage=baggage_cov,
            medical_coverage=medical_cov,
            exclusions=exclusions
        )

        highlights = []
        for s in scenarios[:3]:
            highlights.append({
                "name": s.get("name", ""),
                "scenarioId": s.get("scenarioId", ""),
                "yourStatus": s.get("yourStatus", "unknown"),
                "severity": s.get("severity", "medium")
            })
        return highlights
    except Exception:
        return []


def _build_travel_light_analysis(
    protection_score: int,
    protection_score_label: str,
    insurer_name: str,
    sum_assured: int,
    formatted_gaps: list,
    key_benefits: list,
    recommendations: list,
    category_data: dict,
    policy_details: dict,
    enhanced_insights: dict = None,
    scores_detailed: dict = None,
) -> dict:
    """
    Build travel insurance light analysis based on EAZR Travel Insurance template.
    Returns structured data with travel-specific analysis (destination costs, Schengen, adventure).
    V10: protectionReadiness (2-score), tripState, destinationCoverageCheck, emergencyReference.
    """
    enhanced_insights = enhanced_insights or {}
    from datetime import datetime as dt

    # Import travel-specific helpers
    from services.travel_insurance_report_generator import (
        get_destination_healthcare_costs,
        is_schengen_country,
        get_travel_claims_helpline,
        safe_int,
        safe_str
    )

    # Extract travel-specific data from category_data
    trip_details = category_data.get("tripDetails", {})
    coverage_summary = category_data.get("coverageSummary", {})
    exclusions = category_data.get("exclusions", {})
    emergency_contacts = category_data.get("emergencyContacts", {})
    premium_data = category_data.get("premium", {})
    policy_identification = category_data.get("policyIdentification", {})

    # Trip information
    destination_countries = trip_details.get("destinationCountries", [])
    if isinstance(destination_countries, list) and destination_countries:
        destination = ", ".join(str(c) for c in destination_countries)
    else:
        destination = str(destination_countries) if destination_countries else "International"

    trip_type = trip_details.get("tripType", "Single Trip")
    trip_duration = trip_details.get("tripDuration", "N/A")
    policy_end_date = policy_details.get("endDate", "N/A")

    # Get destination-specific healthcare costs and Schengen status
    destination_costs = get_destination_healthcare_costs(destination)
    is_schengen = is_schengen_country(destination)
    recommended_cover = destination_costs.get("recommended_cover", 50000)  # USD

    # Parse medical cover amount (handle various formats: "$50,000", "50000", "₹25,00,000")
    def _parse_cover_amount(val):
        """Parse coverage amount to numeric USD value"""
        if val is None:
            return 0
        if isinstance(val, (int, float)):
            return int(val)
        val_str = str(val).replace(",", "").replace(" ", "")
        # Remove currency symbols
        for symbol in ["$", "USD", "€", "EUR", "₹", "Rs.", "Rs", "INR"]:
            val_str = val_str.replace(symbol, "")
        try:
            num = float(val_str)
            # If value looks like INR (> 100000), convert to approximate USD
            if num > 100000:
                return int(num / 83)  # Approximate INR to USD
            return int(num)
        except (ValueError, TypeError):
            return 0

    medical_cover = _parse_cover_amount(coverage_summary.get("medicalExpenses") or sum_assured)
    evacuation_cover = _parse_cover_amount(coverage_summary.get("emergencyMedicalEvacuation"))
    trip_cancel_cover = _parse_cover_amount(coverage_summary.get("tripCancellation"))
    baggage_cover = _parse_cover_amount(coverage_summary.get("baggageLoss"))
    flight_delay_cover = _parse_cover_amount(coverage_summary.get("flightDelay"))
    passport_cover = _parse_cover_amount(coverage_summary.get("passportLoss"))
    personal_liability = _parse_cover_amount(coverage_summary.get("personalLiability"))
    deductible = _parse_cover_amount(coverage_summary.get("deductiblePerClaim", 0))

    # Coverage gap calculation
    coverage_gap_usd = max(0, recommended_cover - medical_cover) if medical_cover else recommended_cover

    # ===== V10: Compute travel-specific V10 structures =====
    travel_protection_readiness = None
    travel_trip_state = None
    travel_dest_coverage_check = None
    travel_emergency_ref = None
    travel_strengths_v10 = None
    travel_gaps_v10 = None
    travel_primary_scenario_id = None
    travel_recs_v10 = None
    is_v10 = False

    if scores_detailed and isinstance(scores_detailed, dict) and scores_detailed.get("compositeScore") is not None:
        try:
            is_v10 = True
            travel_protection_readiness = scores_detailed

            # Override protection_score with V10 composite
            protection_score = scores_detailed.get("compositeScore", protection_score)
            protection_score_label = scores_detailed.get("verdict", {}).get("label", protection_score_label)

            # Trip state
            trip_start = trip_details.get("tripStartDate", "")
            trip_end = trip_details.get("tripEndDate", "") or policy_details.get("endDate", "")
            p_status = trip_details.get("policyStatus", "active")
            travel_trip_state = _get_trip_state(trip_start, trip_end, p_status)

            # Determine domestic vs international
            dest_countries = destination_countries if isinstance(destination_countries, list) else []
            is_domestic = False
            if dest_countries:
                is_domestic = all(
                    str(c).strip().lower() in ("india", "domestic", "")
                    for c in dest_countries if c
                )
            elif "domestic" in str(trip_details.get("travelType", "")).lower():
                is_domestic = True

            # Traveller details
            travellers = category_data.get("travellerDetails", [])
            premium_val = 0
            try:
                prem_data = category_data.get("premium", {})
                if isinstance(prem_data, dict):
                    premium_val = safe_int(prem_data.get("totalPremium", 0))
                else:
                    premium_val = safe_int(prem_data)
            except Exception:
                pass

            trip_dur_val = 0
            try:
                trip_dur_val = int(str(trip_duration).replace(" days", "").replace("days", "").strip()) if trip_duration and trip_duration != "N/A" else 0
            except Exception:
                pass

            # Destination coverage check
            travel_dest_coverage_check = _build_destination_coverage_check(
                coverage_summary=coverage_summary,
                destination=destination,
                destination_costs=destination_costs,
                is_schengen=is_schengen,
                travelers=travellers,
                premium=premium_val,
                trip_duration=trip_dur_val
            )

            # Emergency reference
            travel_emergency_ref = _build_emergency_reference(
                category_data=category_data,
                insurer_name=insurer_name,
                destination=destination,
                policy_details=policy_details
            )

            # Strengths
            travel_strengths_v10 = _get_travel_strengths(scores_detailed, category_data)

            # Gaps V10
            medical_cov = category_data.get("medicalCoverage", {})
            trip_prot = category_data.get("tripProtection", {})
            baggage_cov_data = category_data.get("baggageCoverage", {})
            travel_gaps_v10 = _analyze_travel_gaps_v10(
                coverage_data=coverage_summary,
                destination=destination,
                medical_coverage=medical_cov,
                trip_protection=trip_prot,
                baggage_coverage=baggage_cov_data,
                exclusions=exclusions,
                travelers=travellers
            )

            # Primary scenario
            travel_primary_scenario_id = _select_travel_primary_scenario(
                destination=destination,
                gaps_v10=travel_gaps_v10,
                trip_details=trip_details,
                is_domestic=is_domestic
            )

            # Recommendations V10
            travel_recs_v10 = _build_travel_recommendations_v10(
                gaps_v10=travel_gaps_v10,
                coverage_data=coverage_summary,
                trip_protection=trip_prot,
                destination=destination,
                trip_type=trip_type,
                scores_detailed=scores_detailed
            )

        except Exception as _v10_err:
            import traceback
            logger.warning(f"Travel V10 computation failed, falling back to V9: {_v10_err}\n{traceback.format_exc()}")
            is_v10 = False
            travel_protection_readiness = None
            travel_trip_state = None
            travel_dest_coverage_check = None
            travel_emergency_ref = None
            travel_strengths_v10 = None
            travel_gaps_v10 = None
            travel_primary_scenario_id = None
            travel_recs_v10 = None

    # Protection Verdict (V10 uses scores_detailed verdict, V9 uses threshold)
    if is_v10 and scores_detailed:
        v10_verdict = scores_detailed.get("verdict", {})
        verdict_emoji = v10_verdict.get("emoji", "shield")
        verdict_label = v10_verdict.get("label", protection_score_label)
        verdict_one_liner = v10_verdict.get("summary", "")
        if not verdict_one_liner:
            if protection_score >= 80:
                verdict_one_liner = f"Your travel policy provides strong coverage for {destination_costs['region']}."
            elif protection_score >= 60:
                verdict_one_liner = f"Your travel policy covers basics but has gaps for {destination_costs['region']}."
            else:
                verdict_one_liner = f"Your travel policy has significant gaps for {destination_costs['region']}. Review before travel."
    elif protection_score >= 80:
        verdict_emoji = "shield"
        verdict_label = "Well Protected"
        verdict_one_liner = f"Your travel policy provides strong coverage for {destination_costs['region']}."
    elif protection_score >= 60:
        verdict_emoji = "warning"
        verdict_label = "Adequately Covered"
        verdict_one_liner = f"Your travel policy covers basics but has gaps for {destination_costs['region']}."
    elif protection_score >= 40:
        verdict_emoji = "alert"
        verdict_label = "Needs Improvement"
        verdict_one_liner = f"Your travel policy has significant gaps for {destination_costs['region']}. Review before travel."
    else:
        verdict_emoji = "alert"
        verdict_label = "Under-Protected"
        verdict_one_liner = f"Your travel policy is insufficient for {destination_costs['region']}. Upgrade strongly recommended."

    # Key Concerns (up to 3 from formatted gaps)
    key_concerns = []
    for gap in formatted_gaps[:3]:
        if isinstance(gap, dict):
            concern_title = gap.get("title", gap.get("category", "Coverage Gap"))
            concern_desc = gap.get("description", gap.get("suggestion", ""))
            key_concerns.append({
                "title": concern_title,
                "brief": concern_desc[:150] + "..." if len(concern_desc) > 150 else concern_desc,
                "severity": gap.get("severity", "medium")
            })

    # Claim Reality Check - Emergency surgery abroad scenario
    # Use destination-specific typical emergency cost
    typical_emergency_cost = {
        "USA": 40000,
        "UK": 15000,
        "Europe/Schengen": 12000,
        "Australia/NZ": 20000,
        "Southeast Asia": 5000,
        "Middle East": 15000,
        "International": 10000
    }.get(destination_costs.get("region", "International"), 10000)

    if medical_cover >= typical_emergency_cost:
        insurance_pays = typical_emergency_cost - deductible
        you_pay = deductible
        claim_one_liner = f"Emergency surgery in {destination_costs['region']}: Fully covered with ${deductible:,} deductible." if deductible else f"Emergency surgery in {destination_costs['region']}: Fully covered."
    else:
        insurance_pays = max(0, medical_cover - deductible)
        you_pay = typical_emergency_cost - insurance_pays
        claim_one_liner = f"Emergency surgery in {destination_costs['region']}: You'd pay ${you_pay:,} out of pocket."

    # Numbers That Matter - travel-specific (USD-based)
    if coverage_gap_usd > 0:
        gap_one_liner = f"Your medical cover of ${medical_cover:,} is ${coverage_gap_usd:,} below the recommended ${recommended_cover:,} for {destination_costs['region']}."
    else:
        gap_one_liner = f"Your medical cover of ${medical_cover:,} meets the recommended ${recommended_cover:,} for {destination_costs['region']}."

    # Coverage Assessment - travel-specific areas
    coverage_areas = [
        {
            "area": "Medical Cover",
            "status": f"${medical_cover:,}" if medical_cover else "Not Found",
            "statusType": "success" if medical_cover >= recommended_cover else ("warning" if medical_cover >= recommended_cover * 0.5 else "danger"),
            "details": f"Recommended: ${recommended_cover:,} for {destination_costs['region']}"
        },
        {
            "area": "Emergency Evacuation",
            "status": f"${evacuation_cover:,}" if evacuation_cover else "Not Covered",
            "statusType": "success" if evacuation_cover > 0 else "danger",
            "details": "Air ambulance and emergency transport" if evacuation_cover else "Air ambulance can cost $50K-$100K"
        },
        {
            "area": "Trip Cancellation",
            "status": f"${trip_cancel_cover:,}" if trip_cancel_cover else "Not Covered",
            "statusType": "success" if trip_cancel_cover > 0 else "warning",
            "details": "Non-refundable costs covered" if trip_cancel_cover else "No refund if trip cancelled"
        },
        {
            "area": "Baggage Protection",
            "status": f"${baggage_cover:,}" if baggage_cover else "Not Covered",
            "statusType": "success" if baggage_cover > 0 else "warning",
            "details": "Lost/delayed baggage compensated" if baggage_cover else "No compensation for lost bags"
        },
        {
            "area": "Flight Delay",
            "status": f"${flight_delay_cover:,}" if flight_delay_cover else "Not Covered",
            "statusType": "success" if flight_delay_cover > 0 else "info",
            "details": "Delay compensation available" if flight_delay_cover else "No airport delay support"
        },
        {
            "area": "Personal Liability",
            "status": f"${personal_liability:,}" if personal_liability else "Not Covered",
            "statusType": "success" if personal_liability >= 50000 else ("warning" if personal_liability > 0 else "danger"),
            "details": "Third-party liability covered" if personal_liability else "No liability protection abroad"
        }
    ]

    # Adventure sports assessment
    adventure_exclusion = str(exclusions.get("adventureSportsExclusion", "") or "")
    adventure_excluded = "excluded" in adventure_exclusion.lower() or not adventure_exclusion
    coverage_areas.append({
        "area": "Adventure Sports",
        "status": "Covered" if not adventure_excluded else "Excluded",
        "statusType": "success" if not adventure_excluded else "danger",
        "details": adventure_exclusion if adventure_exclusion else "Check policy for adventure sports terms"
    })

    # Pre-existing condition assessment
    ped_exclusion = str(exclusions.get("preExistingConditionExclusion", "") or "")
    ped_excluded = "excluded" in ped_exclusion.lower() or not ped_exclusion
    coverage_areas.append({
        "area": "Pre-existing Conditions",
        "status": "Covered" if not ped_excluded else "Excluded",
        "statusType": "success" if not ped_excluded else "warning",
        "details": ped_exclusion if ped_exclusion else "Most travel policies exclude pre-existing conditions"
    })

    # Schengen compliance check
    schengen_compliance = None
    if is_schengen:
        schengen_min_usd = 33000  # EUR 30,000 approx
        if medical_cover >= schengen_min_usd:
            schengen_compliance = {
                "compliant": True,
                "details": f"Medical cover ${medical_cover:,} meets Schengen minimum of EUR 30,000."
            }
            coverage_areas.append({
                "area": "Schengen Compliance",
                "status": "Compliant",
                "statusType": "success",
                "details": f"Medical cover meets EUR 30,000 minimum"
            })
        else:
            schengen_compliance = {
                "compliant": False,
                "details": f"Medical cover ${medical_cover:,} is below Schengen minimum EUR 30,000 (~${schengen_min_usd:,}). Visa may be rejected."
            }
            coverage_areas.append({
                "area": "Schengen Compliance",
                "status": "Non-Compliant",
                "statusType": "danger",
                "details": f"Below EUR 30,000 minimum - visa risk"
            })

    # Split into strengths and gaps
    coverage_strengths = [item for item in coverage_areas if item["statusType"] == "success"]
    coverage_gaps_list = [item for item in coverage_areas if item["statusType"] in ["warning", "danger", "info"]]

    # What You Should Do (from recommendations)
    actions = {
        "immediate": None,
        "renewal": None,
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
            elif priority == "medium" and not actions["renewal"]:
                actions["renewal"] = {
                    "action": rec.get("category", "Review"),
                    "brief": brief
                }
            elif not actions["ongoing"]:
                actions["ongoing"] = {
                    "action": rec.get("category", "Monitor"),
                    "brief": brief
                }

    # Policy Strengths (prefer AI-generated)
    policy_strengths = []
    ai_strengths = enhanced_insights.get("policyStrengths", [])
    if ai_strengths:
        for strength in ai_strengths[:4]:
            if isinstance(strength, str):
                policy_strengths.append(strength[:100] + "..." if len(strength) > 100 else strength)
            elif isinstance(strength, dict):
                policy_strengths.append(strength.get("description", strength.get("name", ""))[:100])
    else:
        for benefit in key_benefits[:3]:
            if isinstance(benefit, str):
                policy_strengths.append(benefit[:80] + "..." if len(benefit) > 80 else benefit)
            elif isinstance(benefit, dict):
                policy_strengths.append(benefit.get("description", benefit.get("name", ""))[:80])

    # Claims helpline
    claims_helpline = get_travel_claims_helpline(insurer_name)

    # Build travel light analysis response - UNIFIED FORMAT
    travel_light_analysis = {
        # Policy identification - UNIFIED
        "insurerName": insurer_name,
        "planName": "travel",
        "policyType": "travel",

        # Travel-specific metadata
        "tripInfo": {
            "destination": destination,
            "destinationRegion": destination_costs.get("region", "International"),
            "tripType": trip_type,
            "tripDuration": trip_duration,
            "isSchengen": is_schengen,
            "costTier": destination_costs.get("tier", "Moderate Cost")
        },

        # Coverage Verdict - UNIFIED
        "coverageVerdict": {
            "emoji": verdict_emoji,
            "label": verdict_label,
            "oneLiner": verdict_one_liner
        },

        # Keep protectionVerdict for backward compatibility
        "protectionVerdict": {
            "emoji": verdict_emoji,
            "label": verdict_label,
            "oneLiner": verdict_one_liner
        },

        # Protection Score - UNIFIED
        "protectionScore": protection_score,
        "protectionScoreLabel": protection_score_label,

        # Claim Reality Check - UNIFIED (travel-specific scenario)
        "claimRealityCheck": {
            "scenario": f"Emergency surgery in {destination_costs['region']}",
            "claimAmount": typical_emergency_cost,
            "insurancePays": insurance_pays,
            "youPay": you_pay,
            "deductible": deductible,
            "oneLiner": claim_one_liner,
            "currency": "USD"
        },

        # The Numbers That Matter - UNIFIED (USD-based for travel)
        "numbersThatMatter": {
            "yourCover": medical_cover,
            "yourNeed": recommended_cover,
            "gap": coverage_gap_usd,
            "gapOneLiner": gap_one_liner,
            "currency": "USD"
        },

        # Travel-specific: Destination Healthcare Costs
        "destinationCosts": {
            "region": destination_costs.get("region", "International"),
            "erVisit": destination_costs.get("er_visit", "N/A"),
            "hospitalDay": destination_costs.get("hospital_day", "N/A"),
            "icuDay": destination_costs.get("icu_day", "N/A"),
            "airAmbulance": destination_costs.get("air_ambulance", "N/A"),
            "recommendedCover": recommended_cover,
            "costTier": destination_costs.get("tier", "Moderate Cost")
        },

        # Key Concerns - UNIFIED
        "keyConcerns": key_concerns,

        # V10: Override coverageStrengths with structured format
        "coverageStrengths": travel_strengths_v10 if travel_strengths_v10 else coverage_strengths,

        # V10: Override coverageGaps with summary + gaps format
        "coverageGaps": travel_gaps_v10 if travel_gaps_v10 else coverage_gaps_list,

        # Travel-specific: Schengen Compliance (backward compat)
        "schengenCompliance": schengen_compliance,

        # Travel-specific: Adventure Sports Assessment (backward compat)
        "adventureAssessment": {
            "status": "danger" if adventure_excluded else "success",
            "statusLabel": "Excluded" if adventure_excluded else "Covered",
            "details": adventure_exclusion if adventure_exclusion else "Check policy for adventure sports coverage"
        },

        # What You Should Do - UNIFIED (backward compat)
        "whatYouShouldDo": actions,

        # Policy Strengths - UNIFIED (backward compat)
        "policyStrengths": policy_strengths,

        # V10: Override recommendations with structured format
        "recommendations": travel_recs_v10 if travel_recs_v10 else None,

        # V10: Scenarios with primaryScenarioId
        "scenarios": {
            "primaryScenarioId": travel_primary_scenario_id or "T001",
            "simulations": [],  # populated in move step
        } if is_v10 else None,

        # Quick Reference - UNIFIED (travel-specific)
        "quickReference": {
            "claimsHelpline": claims_helpline,
            "emergencyHelpline": emergency_contacts.get("emergencyHelpline24x7", "See policy document"),
            "claimsEmail": emergency_contacts.get("claimsEmail", "See policy document"),
            "policyExpiry": policy_end_date,
            "destination": destination,
            "destinationRegion": destination_costs.get("region", "International")
        },

        # Scoring Breakdown - 2 sub-scores (backward compat)
        "scoringBreakdown": _build_travel_scoring_breakdown(category_data, destination, protection_score),

        # Scenario Highlights - top 3 scenario statuses (backward compat)
        "scenarioHighlights": _build_travel_scenario_highlights(category_data, destination),

        # Report URL - UNIFIED
        "reportUrl": None,
        "reportError": None,

        # Report metadata - UNIFIED
        "reportDate": dt.utcnow().strftime("%Y-%m-%d"),
        "analysisVersion": "10.0" if is_v10 else "9.0",
    }

    # ===== V10: Add travel-specific top-level sections =====
    if is_v10:
        if travel_protection_readiness:
            travel_light_analysis["protectionReadiness"] = travel_protection_readiness
        if travel_trip_state:
            travel_light_analysis["tripState"] = travel_trip_state
        if travel_dest_coverage_check:
            travel_light_analysis["destinationCoverageCheck"] = travel_dest_coverage_check
        if travel_emergency_ref:
            travel_light_analysis["emergencyReference"] = travel_emergency_ref

    # Remove None values to keep response clean
    travel_light_analysis = {k: v for k, v in travel_light_analysis.items() if v is not None}

    return travel_light_analysis


