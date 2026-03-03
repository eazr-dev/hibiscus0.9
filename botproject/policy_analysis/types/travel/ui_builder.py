"""Travel Insurance UI Builder (EAZR_05 Spec)
Build Flutter UI-specific structure for travel insurance policies.
"""
import logging
import re
from datetime import datetime

from policy_analysis.utils import safe_num, get_score_label
from policy_analysis.types.travel.helpers import (
    _calculate_travel_medical_readiness,
    _calculate_travel_trip_protection,
    _simulate_travel_scenarios,
    _analyze_travel_gaps,
    _generate_travel_recommendations,
    _calculate_travel_ipf,
)

logger = logging.getLogger(__name__)


# ==================== TRAVEL INSURANCE UI BUILDER (EAZR_05) ====================

def _build_travel_policy_details_ui(
    extracted_data: dict,
    category_data: dict,
    policy_type: str = "",
    policy_status: str = "active"
) -> dict:
    """
    Build Flutter UI-specific structure for Travel Insurance Policy Details Tab.
    Full implementation per EAZR_05_Travel_Insurance.md specification.
    """
    category_data = category_data or {}
    extracted_data = extracted_data or {}

    # Extract all sections from category_data
    policy_id = category_data.get("policyIdentification", {})
    trip_details = category_data.get("tripDetails", {})
    traveller_details = category_data.get("travellerDetails", [])
    coverage_summary = category_data.get("coverageSummary", {})
    medical_cov = category_data.get("medicalCoverage", {})
    trip_prot = category_data.get("tripProtection", {})
    baggage_cov = category_data.get("baggageCoverage", {})
    exclusions = category_data.get("exclusions", {})
    premium_data = category_data.get("premium", {})
    emergency_contacts = category_data.get("emergencyContacts", {})

    insurer_name = policy_id.get("insurerName") or extracted_data.get("insuranceProvider", "")
    policy_number = policy_id.get("policyNumber") or extracted_data.get("policyNumber", "")

    # Destination string
    dest_countries = trip_details.get("destinationCountries", [])
    destination = ", ".join(dest_countries) if isinstance(dest_countries, list) and dest_countries else str(dest_countries or "")

    # Trip dates and duration
    trip_start = trip_details.get("tripStartDate", "")
    trip_end = trip_details.get("tripEndDate", "")
    trip_duration = trip_details.get("tripDuration", "")

    # Compute days remaining/to trip
    days_remaining = None
    days_to_trip = None
    try:
        if trip_end:
            end_date = datetime.strptime(str(trip_end)[:10], "%Y-%m-%d")
            today = datetime.now()
            days_remaining = max(0, (end_date - today).days)
        if trip_start:
            start_date = datetime.strptime(str(trip_start)[:10], "%Y-%m-%d")
            today = datetime.now()
            days_to_trip = max(0, (start_date - today).days) if start_date > today else 0
    except (ValueError, TypeError):
        pass

    # Determine policy status
    if not policy_status or policy_status == "active":
        try:
            if trip_start and trip_end:
                today = datetime.now()
                start_d = datetime.strptime(str(trip_start)[:10], "%Y-%m-%d")
                end_d = datetime.strptime(str(trip_end)[:10], "%Y-%m-%d")
                if today < start_d:
                    policy_status = "upcoming"
                elif today > end_d:
                    policy_status = "expired"
                else:
                    policy_status = "active"
        except (ValueError, TypeError):
            pass

    status_colors = {"active": "#22C55E", "upcoming": "#3B82F6", "expired": "#EF4444", "claimed": "#F97316"}

    # Parse premium
    total_premium = 0
    try:
        prem_val = premium_data.get("totalPremium") or extracted_data.get("premium", 0)
        total_premium = float(str(prem_val).replace(",", "").replace("₹", "").replace("INR", "").strip() or 0)
    except (ValueError, TypeError):
        pass

    # ===== Section 1: Emergency Info =====
    emergency_info = {
        "policyNumber": policy_number,
        "policyNumberCopyable": True,
        "assistanceHelpline24x7": emergency_contacts.get("emergencyHelpline24x7", ""),
        "assistanceHelplineCallable": True,
        "claimsEmail": emergency_contacts.get("claimsEmail", ""),
        "cashlessHospitals": emergency_contacts.get("cashlessHospitals", ""),
        "policyStatus": policy_status,
        "policyStatusColor": status_colors.get(policy_status, "#6B7280")
    }

    # ===== Section 2: Trip Overview =====
    trip_overview = {
        "destinationCountries": dest_countries if isinstance(dest_countries, list) else [],
        "destinationString": destination,
        "tripType": policy_id.get("tripType", ""),
        "travelType": policy_id.get("travelType", ""),
        "tripDates": {"start": trip_start, "end": trip_end},
        "durationDays": trip_duration,
        "travelersCount": len(traveller_details),
        "purposeOfTravel": trip_details.get("purposeOfTravel", ""),
        "geographicCoverage": trip_details.get("geographicCoverage", ""),
        "policyStatus": policy_status,
        "daysRemaining": days_remaining,
        "daysToTrip": days_to_trip
    }

    # ===== Section 3: Medical Coverage =====
    medical_coverage_section = {
        "medicalExpenses": {
            "sumInsured": coverage_summary.get("medicalExpenses", ""),
            "deductible": medical_cov.get("medicalDeductible", "0"),
            "coverageIncludes": coverage_summary.get("coverageIncludes", []),
            "currency": coverage_summary.get("coverageCurrency", "USD")
        },
        "covidCoverage": medical_cov.get("covidCoverage", {}),
        "preExistingConditions": medical_cov.get("preExistingConditions", {}),
        "cashlessNetwork": medical_cov.get("cashlessNetwork", {}),
        "maternityCoverage": medical_cov.get("maternityCoverage", {}),
        "emergencyEvacuation": {
            "limit": coverage_summary.get("emergencyMedicalEvacuation", ""),
            "covered": bool(coverage_summary.get("emergencyMedicalEvacuation"))
        },
        "repatriationOfRemains": {
            "limit": coverage_summary.get("repatriationOfRemains", ""),
            "covered": bool(coverage_summary.get("repatriationOfRemains"))
        }
    }

    # ===== Section 4: Trip Protection =====
    trip_protection_section = {
        "tripCancellation": trip_prot.get("tripCancellation", {}),
        "tripDelay": trip_prot.get("tripDelay", {}),
        "tripCurtailment": trip_prot.get("tripCurtailment", {}),
        "missedConnection": trip_prot.get("missedConnection", {}),
        "hijackDistress": trip_prot.get("hijackDistress", {}),
        "tripInterruption": {
            "covered": bool(coverage_summary.get("tripInterruption")),
            "limit": coverage_summary.get("tripInterruption", "")
        }
    }

    # ===== Section 5: Baggage Protection =====
    baggage_section = {
        "loss": baggage_cov.get("loss", {}),
        "delay": baggage_cov.get("delay", {}),
        "passportLoss": baggage_cov.get("passportLoss", {})
    }

    # ===== Section 6: Other Coverage =====
    other_coverage = {
        "personalLiability": {
            "limit": coverage_summary.get("personalLiability", ""),
            "covered": bool(coverage_summary.get("personalLiability"))
        },
        "personalAccident": {
            "accidentalDeath": {
                "benefit": coverage_summary.get("accidentalDeath", ""),
                "covered": bool(coverage_summary.get("accidentalDeath"))
            },
            "permanentDisability": {
                "benefit": coverage_summary.get("permanentDisability", ""),
                "covered": bool(coverage_summary.get("permanentDisability"))
            }
        },
        "adventureSports": {
            "exclusion": exclusions.get("adventureSportsExclusion", ""),
            "sportsIncluded": exclusions.get("adventureSportsIncluded", []),
            "sportsExcluded": exclusions.get("adventureSportsExcluded", []),
            "additionalPremium": exclusions.get("adventureAdditionalPremium")
        },
        "homeburglary": {
            "limit": coverage_summary.get("homeburglary", ""),
            "covered": bool(coverage_summary.get("homeburglary"))
        }
    }

    # ===== Section 7: Premium Details =====
    premium_per_day = premium_data.get("premiumPerDay")
    if not premium_per_day and total_premium and trip_duration:
        try:
            dur = int(str(trip_duration).strip())
            if dur > 0:
                premium_per_day = round(total_premium / dur, 2)
        except (ValueError, TypeError):
            pass

    premium_section = {
        "basePremium": premium_data.get("basePremium", ""),
        "gst": premium_data.get("gst", ""),
        "totalPremium": premium_data.get("totalPremium", ""),
        "totalPremiumFormatted": f"₹{int(total_premium):,}" if total_premium else "",
        "premiumPerDay": premium_per_day,
        "premiumPerDayFormatted": f"₹{round(float(premium_per_day)):,}/day" if premium_per_day else "",
        "premiumFactors": premium_data.get("premiumFactors", {})
    }

    # ===== Section 8: Travelers =====
    travelers_section = []
    for t in traveller_details:
        travelers_section.append({
            "name": t.get("name", ""),
            "age": t.get("age", ""),
            "dateOfBirth": t.get("dateOfBirth", ""),
            "relationship": t.get("relationship", ""),
            "passportNumber": t.get("passportNumber", ""),
            "preExistingConditionsDeclared": t.get("preExistingConditionsDeclared", [])
        })

    # ===== Section 9: Scoring Engine (2 sub-scores) =====
    # Pass medical coverage info into coverage_data for scoring
    coverage_with_medical = dict(coverage_summary)
    coverage_with_medical["_medicalCoverage"] = medical_cov

    s1 = _calculate_travel_medical_readiness(coverage_with_medical, destination, traveller_details)
    s2 = _calculate_travel_trip_protection(coverage_summary, trip_prot, baggage_cov)
    overall_score = round(s1["score"] * 0.6 + s2["score"] * 0.4)
    overall_label = get_score_label(overall_score)

    scoring_engine = {
        "overallScore": overall_score,
        "overallLabel": overall_label["label"],
        "overallColor": overall_label["color"],
        "scores": [
            {
                "scoreId": "S1",
                "name": "Medical Emergency Readiness",
                "purpose": "Healthcare protection adequacy for destination",
                "weight": "60%",
                "score": s1["score"],
                "label": get_score_label(s1["score"])["label"],
                "color": get_score_label(s1["score"])["color"],
                "factors": s1["factors"]
            },
            {
                "scoreId": "S2",
                "name": "Trip Protection Score",
                "purpose": "Financial protection for trip investment",
                "weight": "40%",
                "score": s2["score"],
                "label": get_score_label(s2["score"])["label"],
                "color": get_score_label(s2["score"])["color"],
                "factors": s2["factors"]
            }
        ]
    }

    # ===== Section 10: Scenario Simulations =====
    scenarios = _simulate_travel_scenarios(
        coverage_data=coverage_summary,
        destination=destination,
        trip_protection=trip_prot,
        baggage_coverage=baggage_cov,
        medical_coverage=medical_cov,
        exclusions=exclusions
    )

    # ===== Section 11: Gap Analysis =====
    structured_gaps = _analyze_travel_gaps(
        coverage_data=coverage_summary,
        destination=destination,
        medical_coverage=medical_cov,
        trip_protection=trip_prot,
        baggage_coverage=baggage_cov,
        exclusions=exclusions,
        travelers=traveller_details
    )

    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for g in structured_gaps:
        sev = g.get("severity", "low")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    gap_analysis = {
        "totalGaps": len(structured_gaps),
        "severityBreakdown": severity_counts,
        "gaps": structured_gaps
    }

    # ===== Section 12: Recommendations =====
    recs = _generate_travel_recommendations(
        gaps=structured_gaps,
        coverage_data=coverage_summary,
        trip_protection=trip_prot,
        destination=destination,
        trip_type=policy_id.get("tripType", "")
    )

    recommendations_section = {
        "totalRecommendations": len(recs),
        "recommendations": recs,
        "summary": f"{len(recs)} recommendation(s) to improve your travel coverage"
    }

    # ===== Section 13: IPF Integration =====
    ipf_section = _calculate_travel_ipf(total_premium)

    # ===== Return Complete Structure =====
    return {
        "emergencyInfo": emergency_info,
        "tripOverview": trip_overview,
        "medicalCoverage": medical_coverage_section,
        "tripProtection": trip_protection_section,
        "baggageProtection": baggage_section,
        "otherCoverage": other_coverage,
        "premiumDetails": premium_section,
        "travelers": travelers_section,
        "scoringEngine": scoring_engine,
        "scenarioSimulations": scenarios,
        "gapAnalysis": gap_analysis,
        "recommendations": recommendations_section,
        "ipfIntegration": ipf_section
    }


# ==================== END TRAVEL INSURANCE UI BUILDER ====================
