"""Travel Insurance Helper Functions (EAZR_05 Spec)
Scoring, scenarios, gaps, recommendations for travel insurance policies.
"""

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== TRAVEL INSURANCE HELPER FUNCTIONS (EAZR_05) ====================

def _parse_travel_cover_amount(value) -> float:
    """Parse a coverage amount string to USD float. Handles $50,000 / ₹25,00,000 / 50000 / EUR 30,000."""
    if not value:
        return 0.0
    val_str = str(value).strip().upper()
    # Remove commas and spaces
    cleaned = val_str.replace(",", "").replace(" ", "")
    try:
        if "$" in cleaned or "USD" in cleaned:
            num_str = cleaned.replace("$", "").replace("USD", "")
            return float(num_str)
        elif "EUR" in cleaned or "€" in cleaned:
            num_str = cleaned.replace("EUR", "").replace("€", "")
            return float(num_str) * 1.1  # EUR to USD approx
        elif "₹" in cleaned or "INR" in cleaned or "RS" in cleaned:
            num_str = cleaned.replace("₹", "").replace("INR", "").replace("RS", "").replace(".", "")
            inr_val = float(num_str)
            return inr_val / 83.0  # INR to USD approx
        else:
            num_val = float(cleaned)
            # If > 100000, likely INR
            if num_val > 100000:
                return num_val / 83.0
            return num_val
    except (ValueError, TypeError):
        return 0.0


def _calculate_travel_medical_readiness(
    coverage_data: dict,
    destination: str,
    travelers: list = None
) -> dict:
    """
    Score S1: Medical Emergency Readiness (0-100) per EAZR_05 Section 5.2.
    6 factors, 60% weight in overall score.
    """
    from services.travel_insurance_report_generator import get_destination_healthcare_costs

    factors = []
    total_score = 0

    # Get destination benchmarks
    dest_costs = get_destination_healthcare_costs(destination)
    recommended_cover = dest_costs.get("recommended_cover", 50000)  # USD

    # Factor 1: Medical SI vs Destination Benchmark (35 pts)
    medical_si = _parse_travel_cover_amount(coverage_data.get("medicalExpenses"))
    if recommended_cover > 0:
        ratio = medical_si / recommended_cover
    else:
        ratio = 1.0

    if ratio >= 1.5:
        f1_score = 35
        f1_detail = f"${medical_si:,.0f} is 150%+ of recommended ${recommended_cover:,.0f}"
    elif ratio >= 1.0:
        f1_score = 28
        f1_detail = f"${medical_si:,.0f} meets recommended ${recommended_cover:,.0f}"
    elif ratio >= 0.75:
        f1_score = 20
        f1_detail = f"${medical_si:,.0f} is 75% of recommended ${recommended_cover:,.0f}"
    else:
        f1_score = 10
        f1_detail = f"${medical_si:,.0f} is below recommended ${recommended_cover:,.0f}"
    factors.append({"name": "Medical SI vs Destination", "score": f1_score, "maxScore": 35, "detail": f1_detail})
    total_score += f1_score

    # Factor 2: Evacuation Coverage (20 pts)
    evac_amount = _parse_travel_cover_amount(coverage_data.get("emergencyMedicalEvacuation"))
    if evac_amount >= 100000:
        f2_score = 20
        f2_detail = f"${evac_amount:,.0f} evacuation - excellent"
    elif evac_amount >= 50000:
        f2_score = 15
        f2_detail = f"${evac_amount:,.0f} evacuation - adequate"
    elif evac_amount > 0:
        f2_score = 10
        f2_detail = f"${evac_amount:,.0f} evacuation - low for air ambulance"
    else:
        f2_score = 0
        f2_detail = "No evacuation coverage"
    factors.append({"name": "Evacuation Coverage", "score": f2_score, "maxScore": 20, "detail": f2_detail})
    total_score += f2_score

    # Factor 3: Pre-existing Coverage (15 pts)
    medical_coverage = coverage_data.get("_medicalCoverage", {})
    ped_info = medical_coverage.get("preExistingConditions", {})
    ped_covered = ped_info.get("covered")
    ped_conditions = str(ped_info.get("conditions", "")).lower()

    if ped_covered is True:
        f3_score = 15
        f3_detail = "Pre-existing conditions covered"
    elif "emergency" in ped_conditions or "exacerbation" in ped_conditions:
        f3_score = 10
        f3_detail = "Emergency exacerbation of PED covered"
    else:
        f3_score = 0
        f3_detail = "Pre-existing conditions not covered"
    factors.append({"name": "Pre-existing Coverage", "score": f3_score, "maxScore": 15, "detail": f3_detail})
    total_score += f3_score

    # Factor 4: COVID Coverage (10 pts)
    covid_info = medical_coverage.get("covidCoverage", {})
    covid_treatment = covid_info.get("treatmentCovered")
    covid_quarantine = covid_info.get("quarantineCovered")

    if covid_treatment and covid_quarantine:
        f4_score = 10
        f4_detail = "COVID treatment + quarantine covered"
    elif covid_treatment:
        f4_score = 6
        f4_detail = "COVID treatment covered, quarantine not covered"
    else:
        f4_score = 0
        f4_detail = "COVID coverage not included"
    factors.append({"name": "COVID Coverage", "score": f4_score, "maxScore": 10, "detail": f4_detail})
    total_score += f4_score

    # Factor 5: Cashless Network (10 pts)
    cashless_info = medical_coverage.get("cashlessNetwork", {})
    cashless_available = cashless_info.get("available")

    if cashless_available:
        f5_score = 10
        network_name = cashless_info.get("networkName", "Available")
        f5_detail = f"Cashless network: {network_name}"
    else:
        f5_score = 0
        f5_detail = "No cashless network"
    factors.append({"name": "Cashless Network", "score": f5_score, "maxScore": 10, "detail": f5_detail})
    total_score += f5_score

    # Factor 6: Repatriation (10 pts)
    repatriation = _parse_travel_cover_amount(coverage_data.get("repatriationOfRemains"))
    if repatriation > 0:
        f6_score = 10
        f6_detail = f"${repatriation:,.0f} repatriation coverage"
    else:
        f6_score = 0
        f6_detail = "No repatriation coverage"
    factors.append({"name": "Repatriation", "score": f6_score, "maxScore": 10, "detail": f6_detail})
    total_score += f6_score

    return {"score": min(total_score, 100), "factors": factors}


def _calculate_travel_trip_protection(
    coverage_data: dict,
    trip_protection: dict = None,
    baggage_coverage: dict = None,
    trip_cost: int = 200000
) -> dict:
    """
    Score S2: Trip Protection Score (0-100) per EAZR_05 Section 5.3.
    6 factors, 40% weight in overall score.
    """
    factors = []
    total_score = 0
    trip_protection = trip_protection or {}
    baggage_coverage = baggage_coverage or {}

    # Factor 1: Cancellation Cover vs Trip Cost (30 pts)
    cancel_info = trip_protection.get("tripCancellation", {})
    cancel_covered = cancel_info.get("covered", False)
    cancel_limit_raw = cancel_info.get("limit")

    if cancel_covered and cancel_limit_raw:
        # Parse cancel limit - may be INR or USD
        cancel_str = str(cancel_limit_raw).replace(",", "").replace(" ", "")
        try:
            if "₹" in cancel_str or "INR" in cancel_str:
                cancel_val = float(cancel_str.replace("₹", "").replace("INR", "").replace(".", ""))
            elif "$" in cancel_str or "USD" in cancel_str:
                cancel_val = float(cancel_str.replace("$", "").replace("USD", "")) * 83.0  # Convert to INR
            else:
                cancel_val = float(cancel_str)
                if cancel_val < 10000:
                    cancel_val = cancel_val * 83.0  # Likely USD
        except (ValueError, TypeError):
            cancel_val = 0

        if trip_cost > 0:
            ratio = cancel_val / trip_cost
        else:
            ratio = 1.0

        if ratio >= 1.0:
            f1_score = 30
            f1_detail = f"Cancellation covers 100%+ of trip cost"
        elif ratio >= 0.75:
            f1_score = 25
            f1_detail = f"Cancellation covers ~75% of trip cost"
        elif ratio >= 0.5:
            f1_score = 18
            f1_detail = f"Cancellation covers ~50% of trip cost"
        else:
            f1_score = 10
            f1_detail = f"Cancellation cover is low relative to trip cost"
    else:
        f1_score = 0
        f1_detail = "No trip cancellation coverage"
    factors.append({"name": "Cancellation Cover", "score": f1_score, "maxScore": 30, "detail": f1_detail})
    total_score += f1_score

    # Factor 2: Cancellation Reasons Comprehensiveness (20 pts)
    covered_reasons = cancel_info.get("coveredReasons", [])
    num_reasons = len(covered_reasons) if isinstance(covered_reasons, list) else 0

    if not cancel_covered:
        f2_score = 0
        f2_detail = "No cancellation coverage"
    elif num_reasons >= 8:
        f2_score = 20
        f2_detail = f"{num_reasons} covered cancellation reasons - comprehensive"
    elif num_reasons >= 5:
        f2_score = 15
        f2_detail = f"{num_reasons} covered cancellation reasons - adequate"
    else:
        f2_score = 8
        f2_detail = f"{num_reasons} covered cancellation reasons - limited"
    factors.append({"name": "Cancellation Reasons", "score": f2_score, "maxScore": 20, "detail": f2_detail})
    total_score += f2_score

    # Factor 3: Delay Compensation (15 pts)
    delay_info = trip_protection.get("tripDelay", {})
    delay_covered = delay_info.get("covered", False)
    trigger_hours = delay_info.get("triggerHours")

    if delay_covered:
        try:
            trigger_h = int(trigger_hours) if trigger_hours else 12
        except (ValueError, TypeError):
            trigger_h = 12

        if trigger_h <= 6:
            f3_score = 15
            f3_detail = f"Delay compensation after {trigger_h} hours - excellent"
        elif trigger_h <= 8:
            f3_score = 12
            f3_detail = f"Delay compensation after {trigger_h} hours - good"
        else:
            f3_score = 8
            f3_detail = f"Delay compensation after {trigger_h} hours - high threshold"
    else:
        f3_score = 0
        f3_detail = "No flight delay compensation"
    factors.append({"name": "Delay Compensation", "score": f3_score, "maxScore": 15, "detail": f3_detail})
    total_score += f3_score

    # Factor 4: Baggage Protection (15 pts)
    f4_score = 0
    f4_parts = []
    baggage_loss = baggage_coverage.get("loss", {})
    baggage_delay = baggage_coverage.get("delay", {})

    if baggage_loss.get("totalLimit"):
        f4_score += 10
        f4_parts.append("loss covered")
    if baggage_delay.get("covered"):
        f4_score += 5
        f4_parts.append("delay covered")

    f4_detail = ", ".join(f4_parts) if f4_parts else "No baggage protection"
    f4_detail = f"Baggage: {f4_detail}" if f4_parts else f4_detail
    factors.append({"name": "Baggage Protection", "score": f4_score, "maxScore": 15, "detail": f4_detail})
    total_score += f4_score

    # Factor 5: Documentation Ease (10 pts)
    f5_score = 7  # Default - hard to assess from extraction
    f5_detail = "Standard documentation requirements"
    factors.append({"name": "Documentation Ease", "score": f5_score, "maxScore": 10, "detail": f5_detail})
    total_score += f5_score

    # Factor 6: Passport Loss (10 pts)
    passport_info = baggage_coverage.get("passportLoss", {})
    if passport_info.get("covered"):
        f6_score = 10
        f6_detail = f"Passport loss covered: {passport_info.get('limit', 'Yes')}"
    else:
        passport_from_summary = _parse_travel_cover_amount(coverage_data.get("passportLoss"))
        if passport_from_summary > 0:
            f6_score = 10
            f6_detail = f"Passport loss covered: ${passport_from_summary:,.0f}"
        else:
            f6_score = 0
            f6_detail = "No passport loss coverage"
    factors.append({"name": "Passport Loss", "score": f6_score, "maxScore": 10, "detail": f6_detail})
    total_score += f6_score

    return {"score": min(total_score, 100), "factors": factors}


def _simulate_travel_scenarios(
    coverage_data: dict,
    destination: str,
    trip_protection: dict = None,
    baggage_coverage: dict = None,
    medical_coverage: dict = None,
    exclusions: dict = None,
    trip_cost: int = 200000
) -> list:
    """
    5 Travel Scenario Simulations per EAZR_05 Section 6.
    Returns list of scenario dicts following motor pattern.
    """
    scenarios = []
    trip_protection = trip_protection or {}
    baggage_coverage = baggage_coverage or {}
    medical_coverage = medical_coverage or {}
    exclusions = exclusions or {}

    medical_si = _parse_travel_cover_amount(coverage_data.get("medicalExpenses"))
    deductible = _parse_travel_cover_amount(coverage_data.get("deductiblePerClaim") or medical_coverage.get("medicalDeductible"))

    # ==================== T001: Medical Emergency USA ====================
    total_cost_usd = 68000
    total_cost_inr = int(total_cost_usd * 83)

    if medical_si >= total_cost_usd:
        t001_status = "protected"
        t001_your_gap = 0
        t001_rec = "Your medical coverage is adequate for US emergencies"
    elif medical_si >= 50000:
        t001_status = "at_risk"
        t001_your_gap = max(0, total_cost_usd - medical_si + deductible)
        t001_rec = f"Consider upgrading to $100K+ for USA travel. Current gap: ${t001_your_gap:,.0f}"
    else:
        t001_status = "at_risk"
        t001_your_gap = max(0, total_cost_usd - medical_si + deductible)
        t001_rec = f"Critically underinsured for USA. Upgrade immediately. Gap: ${t001_your_gap:,.0f}"

    scenarios.append({
        "scenarioId": "T001",
        "name": "Medical Emergency in USA - Appendicitis",
        "description": "Sudden appendicitis requiring emergency surgery in USA",
        "icon": "local_hospital",
        "severity": "high",
        "medicalCosts": {
            "emergencyRoom": 3000,
            "surgery": 35000,
            "hospitalization3Days": 15000,
            "anesthesia": 5000,
            "doctorFees": 8000,
            "medicines": 2000,
            "totalUsd": total_cost_usd,
            "totalInrEquivalent": total_cost_inr,
            "currencyNote": "At ₹83/USD"
        },
        "withoutAddon": {
            "label": "With $50K Coverage",
            "claimAmount": 50000,
            "claimAmountFormatted": "$50,000",
            "gap": 18000,
            "gapFormatted": "$18,000 (₹15.0L)",
            "description": "₹15.0L out-of-pocket after coverage exhausted"
        },
        "withAddon": {
            "label": "With $100K Coverage",
            "claimAmount": 68000,
            "claimAmountFormatted": "$68,000",
            "gap": 0,
            "gapFormatted": "$0",
            "description": "Fully covered - zero out-of-pocket"
        },
        "yourStatus": t001_status,
        "yourCoverage": f"${medical_si:,.0f}",
        "recommendation": t001_rec
    })

    # ==================== T002: Flight Cancellation ====================
    trip_costs = {
        "flights": 85000,
        "hotels": 45000,
        "toursActivities": 20000,
        "visaFees": 8000,
        "totalNonRefundable": 158000
    }

    cancel_info = trip_protection.get("tripCancellation", {})
    cancel_covered = cancel_info.get("covered", False)
    cancel_limit_str = cancel_info.get("limit")
    # Parse cancel limit to INR
    try:
        cancel_val = _parse_travel_cover_amount(cancel_limit_str) * 83.0 if cancel_limit_str else 0
    except Exception:
        cancel_val = 0

    if cancel_covered and cancel_val >= 150000:
        t002_status = "protected"
        t002_oop = max(0, 158000 - cancel_val)
        t002_rec = "Trip cancellation coverage protects your investment"
    elif cancel_covered:
        t002_status = "at_risk"
        t002_oop = max(0, 158000 - cancel_val)
        t002_rec = f"Cancellation limit may not cover full trip cost. Gap: ₹{t002_oop:,.0f}"
    else:
        t002_status = "at_risk"
        t002_oop = 158000
        t002_rec = "No trip cancellation coverage. ₹1.58L at risk if trip cancelled"

    scenarios.append({
        "scenarioId": "T002",
        "name": "Flight Cancellation - Family Emergency",
        "description": "Cancel Europe trip due to parent's sudden hospitalization",
        "icon": "flight_takeoff",
        "severity": "medium",
        "tripCosts": trip_costs,
        "withoutAddon": {
            "label": "Without Cancellation Cover",
            "claimAmount": 0,
            "claimAmountFormatted": "₹0",
            "gap": 158000,
            "gapFormatted": "₹1,58,000",
            "description": "Entire non-refundable amount lost"
        },
        "withAddon": {
            "label": "With Cancellation Cover",
            "claimAmount": 150000,
            "claimAmountFormatted": "₹1,50,000",
            "gap": 8000,
            "gapFormatted": "₹8,000",
            "description": "Only visa fees not recoverable"
        },
        "yourStatus": t002_status,
        "recommendation": t002_rec
    })

    # ==================== T003: Lost Baggage ====================
    baggage_loss_info = baggage_coverage.get("loss", {})
    baggage_total = _parse_travel_cover_amount(baggage_loss_info.get("totalLimit") or coverage_data.get("baggageLoss"))
    per_item = _parse_travel_cover_amount(baggage_loss_info.get("perItemLimit"))

    lost_items_value = 2500  # USD typical lost bag
    laptop_value = 1200  # Single expensive item

    if baggage_total >= lost_items_value:
        t003_status = "protected"
        t003_rec = "Baggage loss coverage is adequate"
    elif baggage_total > 0:
        t003_status = "at_risk"
        t003_rec = f"Baggage limit ${baggage_total:,.0f} may not cover full loss. Per-item limits may apply"
    else:
        t003_status = "at_risk"
        t003_rec = "No baggage loss coverage. Consider adding this protection"

    scenarios.append({
        "scenarioId": "T003",
        "name": "Lost Baggage - International Flight",
        "description": "Airline loses checked baggage on international flight with laptop and valuables",
        "icon": "luggage",
        "severity": "medium",
        "lostItemsCost": {
            "clothing": 500,
            "electronics": 1200,
            "toiletries": 100,
            "documents": 200,
            "miscellaneous": 500,
            "totalUsd": lost_items_value
        },
        "withoutAddon": {
            "label": "Without Baggage Cover",
            "claimAmount": 0,
            "claimAmountFormatted": "$0",
            "gap": lost_items_value,
            "gapFormatted": f"${lost_items_value:,} (₹{int(lost_items_value * 83):,})",
            "description": "Only airline compensation (often minimal)"
        },
        "withAddon": {
            "label": "With Baggage Cover",
            "claimAmount": min(lost_items_value, 2000),
            "claimAmountFormatted": "$2,000",
            "gap": max(0, lost_items_value - 2000),
            "gapFormatted": f"${max(0, lost_items_value - 2000):,}",
            "description": "Covered up to policy limit (per-item limits may apply)"
        },
        "yourStatus": t003_status,
        "recommendation": t003_rec
    })

    # ==================== T004: COVID Quarantine ====================
    covid_info = medical_coverage.get("covidCoverage", {})
    covid_treatment = covid_info.get("treatmentCovered")
    covid_quarantine = covid_info.get("quarantineCovered")

    covid_hospital_cost = 15000  # USD typical COVID hospitalization abroad
    quarantine_cost = 2000  # USD hotel quarantine 14 days

    if covid_treatment and covid_quarantine:
        t004_status = "protected"
        t004_rec = "COVID treatment and quarantine both covered"
    elif covid_treatment:
        t004_status = "at_risk"
        t004_rec = f"COVID treatment covered but quarantine expenses (${quarantine_cost:,}) not covered"
    else:
        t004_status = "at_risk"
        t004_rec = f"No COVID coverage. Hospitalization abroad can cost ${covid_hospital_cost:,}+"

    scenarios.append({
        "scenarioId": "T004",
        "name": "COVID Quarantine Abroad",
        "description": "Test positive for COVID during international trip, need hospitalization and quarantine",
        "icon": "coronavirus",
        "severity": "medium",
        "covidCosts": {
            "hospitalTreatment": covid_hospital_cost,
            "hotelQuarantine14Days": quarantine_cost,
            "medications": 500,
            "totalUsd": covid_hospital_cost + quarantine_cost + 500,
            "totalInrEquivalent": int((covid_hospital_cost + quarantine_cost + 500) * 83)
        },
        "withoutAddon": {
            "label": "Without COVID Cover",
            "claimAmount": 0,
            "claimAmountFormatted": "$0",
            "gap": covid_hospital_cost + quarantine_cost + 500,
            "gapFormatted": f"${covid_hospital_cost + quarantine_cost + 500:,}",
            "description": "All COVID expenses out-of-pocket"
        },
        "withAddon": {
            "label": "With COVID Cover",
            "claimAmount": covid_hospital_cost + quarantine_cost + 500,
            "claimAmountFormatted": f"${covid_hospital_cost + quarantine_cost + 500:,}",
            "gap": 0,
            "gapFormatted": "$0",
            "description": "Treatment and quarantine fully covered"
        },
        "yourStatus": t004_status,
        "recommendation": t004_rec
    })

    # ==================== T005: Adventure Sport Injury ====================
    adventure_excluded = str(exclusions.get("adventureSportsExclusion", "")).lower()
    adventure_covered = "covered" in adventure_excluded and "excluded" not in adventure_excluded

    scuba_cost_usd = 4000
    scuba_cost_inr = int(scuba_cost_usd * 83)

    if adventure_covered:
        t005_status = "protected"
        t005_rec = "Adventure sports covered - verify specific activity is included"
    else:
        t005_status = "at_risk"
        t005_rec = f"Adventure sports excluded. Scuba injury = ${scuba_cost_usd:,} out-of-pocket. Add adventure add-on"

    scenarios.append({
        "scenarioId": "T005",
        "name": "Adventure Sport Injury - Scuba Diving",
        "description": "Decompression sickness during scuba diving in Thailand",
        "icon": "scuba_diving",
        "severity": "medium",
        "treatmentCosts": {
            "hyperbaricChamber": 2000,
            "hospitalization": 1200,
            "doctorFees": 500,
            "medication": 300,
            "totalUsd": scuba_cost_usd,
            "totalInrEquivalent": scuba_cost_inr
        },
        "withoutAddon": {
            "label": "Standard Policy (No Adventure)",
            "claimAmount": 0,
            "claimAmountFormatted": "$0",
            "gap": scuba_cost_usd,
            "gapFormatted": f"${scuba_cost_usd:,} (₹{scuba_cost_inr:,})",
            "description": "CLAIM REJECTED - Scuba diving excluded"
        },
        "withAddon": {
            "label": "With Adventure Sports Add-on",
            "claimAmount": scuba_cost_usd,
            "claimAmountFormatted": f"${scuba_cost_usd:,}",
            "gap": 0,
            "gapFormatted": "$0",
            "description": "Fully covered under adventure sports rider"
        },
        "yourStatus": t005_status,
        "recommendation": t005_rec
    })

    return scenarios


def _analyze_travel_gaps(
    coverage_data: dict,
    destination: str,
    medical_coverage: dict = None,
    trip_protection: dict = None,
    baggage_coverage: dict = None,
    exclusions: dict = None,
    travelers: list = None
) -> list:
    """
    6 structured gap types per EAZR_05 Section 7.
    Returns sorted list of gap dicts following motor pattern.
    """
    from services.travel_insurance_report_generator import get_destination_healthcare_costs

    gaps = []
    medical_coverage = medical_coverage or {}
    trip_protection = trip_protection or {}
    baggage_coverage = baggage_coverage or {}
    exclusions = exclusions or {}
    travelers = travelers or []

    dest_costs = get_destination_healthcare_costs(destination)
    recommended_cover = dest_costs.get("recommended_cover", 50000)
    medical_si = _parse_travel_cover_amount(coverage_data.get("medicalExpenses"))

    # G001: Medical SI Inadequate (HIGH)
    if medical_si < recommended_cover:
        gap_amount = recommended_cover - medical_si
        gaps.append({
            "gapId": "G001",
            "severity": "high",
            "severityColor": "#EF4444",
            "title": f"Medical Coverage Below {dest_costs.get('region', 'Destination')} Requirement",
            "description": f"Your coverage ${medical_si:,.0f} is below recommended ${recommended_cover:,.0f} for {dest_costs.get('region', 'this destination')}",
            "impact": f"Emergency surgery abroad can cost ${recommended_cover * 1.5:,.0f}+. You'd pay ${gap_amount:,.0f} out-of-pocket",
            "solution": f"Upgrade medical coverage to at least ${recommended_cover:,.0f}",
            "estimatedCost": "₹2,000-8,000 additional premium",
            "ipfEligible": True
        })

    # G002: No Pre-existing Cover (MEDIUM)
    ped_info = medical_coverage.get("preExistingConditions", {})
    has_ped = any(
        t.get("preExistingConditionsDeclared") and len(t.get("preExistingConditionsDeclared", [])) > 0
        for t in travelers
    )
    ped_covered = ped_info.get("covered")

    if has_ped and not ped_covered:
        gaps.append({
            "gapId": "G002",
            "severity": "medium",
            "severityColor": "#F97316",
            "title": "Pre-existing Conditions Not Covered",
            "description": "Declared pre-existing conditions are excluded from coverage",
            "impact": "Any treatment related to PED abroad will be 100% out-of-pocket",
            "solution": "Look for a policy that covers pre-existing conditions or emergency exacerbation",
            "estimatedCost": "₹3,000-10,000 additional premium",
            "ipfEligible": True
        })

    # G003: No COVID Coverage (MEDIUM)
    covid_info = medical_coverage.get("covidCoverage", {})
    if not covid_info.get("treatmentCovered"):
        gaps.append({
            "gapId": "G003",
            "severity": "medium",
            "severityColor": "#F97316",
            "title": "COVID Treatment Not Covered",
            "description": "COVID-19 treatment is excluded from your policy",
            "impact": "COVID hospitalization abroad can cost $15,000-50,000+",
            "solution": "Upgrade to a COVID-inclusive travel insurance policy",
            "estimatedCost": "₹500-2,000 additional premium",
            "ipfEligible": True
        })

    # G004: No Trip Cancellation (MEDIUM)
    cancel_info = trip_protection.get("tripCancellation", {})
    if not cancel_info.get("covered"):
        gaps.append({
            "gapId": "G004",
            "severity": "medium",
            "severityColor": "#F97316",
            "title": "No Trip Cancellation Coverage",
            "description": "Trip cancellation expenses are not covered",
            "impact": "Could lose ₹1-3 lakhs in non-refundable costs if trip cancelled",
            "solution": "Add trip cancellation coverage to protect your travel investment",
            "estimatedCost": "₹500-2,000 additional premium",
            "ipfEligible": True
        })

    # G005: Adventure Not Covered (MEDIUM)
    adventure_text = str(exclusions.get("adventureSportsExclusion", "")).lower()
    if "excluded" in adventure_text or (adventure_text and "covered" not in adventure_text):
        gaps.append({
            "gapId": "G005",
            "severity": "medium",
            "severityColor": "#F97316",
            "title": "Adventure Sports Not Covered",
            "description": "Injuries during adventure activities are excluded from coverage",
            "impact": "Scuba diving, skiing, trekking injuries = 100% out-of-pocket (can be $4,000+)",
            "solution": "Add adventure sports add-on (₹500-2,000)",
            "estimatedCost": "₹500-2,000 additional premium",
            "ipfEligible": True
        })

    # G006: Low Baggage Limits (LOW)
    baggage_loss = baggage_coverage.get("loss", {})
    per_item_limit = _parse_travel_cover_amount(baggage_loss.get("perItemLimit"))
    total_baggage = _parse_travel_cover_amount(baggage_loss.get("totalLimit") or coverage_data.get("baggageLoss"))

    if total_baggage > 0 and (per_item_limit > 0 and per_item_limit < 120):  # $120 ≈ ₹10,000
        gaps.append({
            "gapId": "G006",
            "severity": "low",
            "severityColor": "#EAB308",
            "title": "Low Per-Item Baggage Limit",
            "description": f"Per-item limit ${per_item_limit:,.0f} may not cover expensive items like laptops",
            "impact": "Single laptop worth $1,000+ would only be reimbursed up to per-item limit",
            "solution": "Check if valuable items can be declared separately for higher coverage",
            "estimatedCost": "₹200-500 additional premium",
            "ipfEligible": False
        })
    elif total_baggage == 0:
        gaps.append({
            "gapId": "G006",
            "severity": "low",
            "severityColor": "#EAB308",
            "title": "No Baggage Loss Coverage",
            "description": "Baggage loss is not covered under your policy",
            "impact": "Lost luggage = 100% financial loss (typical bag value $1,500-3,000)",
            "solution": "Add baggage protection coverage",
            "estimatedCost": "₹300-800 additional premium",
            "ipfEligible": False
        })

    # Sort by severity: high → medium → low
    severity_order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))

    return gaps


def _generate_travel_recommendations(
    gaps: list,
    coverage_data: dict,
    trip_protection: dict = None,
    destination: str = "",
    trip_type: str = ""
) -> list:
    """
    5 recommendation types per EAZR_05 Section 8.
    Maps gaps to actionable recommendations following motor pattern.
    """
    recommendations = []
    gap_ids = {g.get("gapId") for g in gaps}
    trip_protection = trip_protection or {}

    # Gap → Recommendation mappings
    rec_map = {
        "G001": {
            "id": "upgrade_medical",
            "category": "enhancement",
            "priority": 1,
            "title": "Increase Medical Coverage",
            "description": f"Upgrade medical coverage for {destination or 'your destination'}. "
                           f"US needs $100K+, Europe needs EUR 30K+, Asia needs $50K+",
            "estimatedCost": "₹2,000-8,000 additional",
            "ipfEligible": True,
            "icon": "trending_up"
        },
        "G003": {
            "id": "add_covid",
            "category": "addon",
            "priority": 2,
            "title": "Add COVID Coverage",
            "description": "Include COVID-19 treatment and quarantine coverage. "
                           "COVID hospitalization abroad costs $15,000-50,000",
            "estimatedCost": "₹500-2,000 additional",
            "ipfEligible": True,
            "icon": "coronavirus"
        },
        "G004": {
            "id": "add_cancellation",
            "category": "addon",
            "priority": 3,
            "title": "Add Trip Cancellation",
            "description": "Protect your travel investment. Non-refundable costs "
                           "(flights, hotels, tours) can be ₹1-3 lakhs",
            "estimatedCost": "₹500-2,000 additional",
            "ipfEligible": True,
            "icon": "event_busy"
        },
        "G005": {
            "id": "add_adventure",
            "category": "addon",
            "priority": 4,
            "title": "Add Adventure Sports Cover",
            "description": "Cover injuries during adventure activities like scuba diving, "
                           "skiing, trekking, paragliding",
            "estimatedCost": "₹500-2,000 additional",
            "ipfEligible": True,
            "icon": "sports_martial_arts"
        }
    }

    for gap_id, rec in rec_map.items():
        if gap_id in gap_ids:
            recommendations.append(rec)

    # Always suggest multi-trip if single trip
    trip_type_lower = str(trip_type).lower() if trip_type else ""
    if "multi" not in trip_type_lower and "annual" not in trip_type_lower:
        recommendations.append({
            "id": "multi_trip",
            "category": "optimization",
            "priority": 5,
            "title": "Consider Annual Multi-Trip Policy",
            "description": "If you travel 2+ times a year, an annual multi-trip policy "
                           "can save 30-50% vs buying per-trip",
            "estimatedCost": "₹8,000-25,000 per year",
            "ipfEligible": True,
            "icon": "repeat"
        })

    # Sort by priority
    recommendations.sort(key=lambda x: x.get("priority", 99))

    return recommendations


def _calculate_travel_ipf(premium: float) -> dict:
    """
    Travel Insurance IPF (Instant Premium Financing) per EAZR_05 Section 9.
    Eligible if premium > ₹5,000.
    """
    if not premium or premium <= 5000:
        return {
            "eligible": False,
            "totalPremium": premium or 0,
            "totalPremiumFormatted": f"₹{int(premium or 0):,}",
            "reason": "Premium below ₹5,000 threshold"
        }

    premium_val = float(premium)
    options = []

    for tenure in [3, 6]:
        emi = round(premium_val / tenure)
        options.append({
            "tenure": tenure,
            "tenureLabel": f"{tenure} months",
            "emi": emi,
            "emiFormatted": f"₹{emi:,}/month",
            "total": int(premium_val),
            "totalFormatted": f"₹{int(premium_val):,}"
        })

    recommended = options[0]  # 3 months for travel (shorter duration)

    return {
        "eligible": True,
        "totalPremium": int(premium_val),
        "totalPremiumFormatted": f"₹{int(premium_val):,}",
        "options": options,
        "recommended": recommended,
        "display": f"₹{recommended['emi']:,}/month × {recommended['tenure']} months",
        "touchpoints": [
            {
                "touchpoint": "purchase",
                "trigger": "Premium > ₹5,000",
                "cta": "Pay in EMIs",
                "icon": "credit_card"
            },
            {
                "touchpoint": "upgrade",
                "trigger": "Medical upgrade needed",
                "cta": "Upgrade with EMI",
                "icon": "trending_up"
            },
            {
                "touchpoint": "multi_trip",
                "trigger": "Annual policy > ₹10,000",
                "cta": "Finance annual policy",
                "icon": "repeat"
            },
            {
                "touchpoint": "family",
                "trigger": "Multiple travelers > ₹8,000",
                "cta": "Finance family coverage",
                "icon": "family_restroom"
            }
        ]
    }


# ==================== TRAVEL INSURANCE V10 HELPER FUNCTIONS (EAZR_05 Spec) ====================


def _get_trip_state(
    trip_start_date: str,
    trip_end_date: str,
    policy_status: str = "active"
) -> dict:
    """
    Determine trip temporal state per EAZR_05 Section 2.1.
    Returns PRE_TRIP / DURING_TRIP / POST_TRIP / EXPIRED with countdown and urgency.
    """
    from datetime import date, datetime

    def _parse_date(val):
        if not val:
            return None
        val_str = str(val).strip()[:10]
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(val_str, fmt).date()
            except (ValueError, TypeError):
                continue
        return None

    start = _parse_date(trip_start_date)
    end = _parse_date(trip_end_date)
    today = date.today()

    if not start or not end:
        return {
            "state": "EXPIRED" if policy_status == "expired" else "POST_TRIP",
            "daysToDepart": None, "daysRemaining": None, "tripDay": None,
            "totalDays": None, "urgency": None,
            "actionFraming": "For your next trip",
            "showCountdown": False, "showEmergencyProminent": False
        }

    total_days = max(1, (end - start).days + 1)

    if policy_status == "expired" and today > end:
        return {
            "state": "EXPIRED",
            "daysToDepart": None, "daysRemaining": None, "tripDay": None,
            "totalDays": total_days, "urgency": None,
            "actionFraming": "For your next trip",
            "showCountdown": False, "showEmergencyProminent": False
        }

    if today < start:
        days_to_go = (start - today).days
        return {
            "state": "PRE_TRIP",
            "daysToDepart": days_to_go,
            "daysRemaining": None, "tripDay": None,
            "totalDays": total_days,
            "urgency": "high" if days_to_go <= 7 else "normal",
            "actionFraming": "Fix before you fly",
            "showCountdown": True, "showEmergencyProminent": False
        }
    elif start <= today <= end:
        days_remaining = (end - today).days
        trip_day = (today - start).days + 1
        return {
            "state": "DURING_TRIP",
            "daysToDepart": None,
            "daysRemaining": days_remaining,
            "tripDay": trip_day,
            "totalDays": total_days,
            "urgency": None,
            "actionFraming": "For your next trip",
            "showCountdown": False, "showEmergencyProminent": True
        }
    else:
        return {
            "state": "POST_TRIP",
            "daysToDepart": None, "daysRemaining": None, "tripDay": None,
            "totalDays": total_days, "urgency": None,
            "actionFraming": "For your next trip",
            "showCountdown": False, "showEmergencyProminent": False
        }


def _build_destination_coverage_check(
    coverage_summary: dict,
    destination: str,
    destination_costs: dict,
    is_schengen: bool,
    travelers: list,
    premium: float,
    trip_duration: int
) -> dict:
    """
    Build Section B: Destination Coverage Check per EAZR_05 Section 3.3.
    Medical SI vs benchmark, Schengen compliance, per-day cost breakdown.
    """
    from services.travel_insurance_report_generator import is_schengen_country

    medical_si = _parse_travel_cover_amount(coverage_summary.get("medicalExpenses"))
    benchmark_usd = destination_costs.get("recommended_cover", 50000)
    region = destination_costs.get("region", "International")
    currency = destination_costs.get("currency", "USD")

    # Medical benchmark
    if benchmark_usd > 0:
        pct = int((medical_si / benchmark_usd) * 100) if medical_si > 0 else 0
    else:
        pct = 100

    if pct >= 100:
        bm_status = "above"
        bm_color = "#22C55E"
    elif pct >= 75:
        bm_status = "meets"
        bm_color = "#EAB308"
    else:
        bm_status = "below"
        bm_color = "#EF4444"

    inr_rate = 83
    benchmark_inr = int(benchmark_usd * inr_rate)
    medical_inr = int(medical_si * inr_rate)

    benchmark_formatted = f"${benchmark_usd:,.0f} (Rs.{benchmark_inr / 100000:.1f}L)" if benchmark_usd else "N/A"
    your_formatted = f"${medical_si:,.0f} (Rs.{medical_inr / 100000:.1f}L)" if medical_si else "N/A"

    bm_note = ""
    if region == "USA":
        bm_note = "US healthcare is 10-20x more expensive than India."
    elif "Schengen" in region or "Europe" in region:
        bm_note = "Schengen visa requires minimum EUR 30,000 medical coverage."
    elif region == "UK":
        bm_note = "UK healthcare costs are high for non-residents."

    # Schengen compliance
    schengen_check = None
    if is_schengen:
        schengen_min_usd = 33000  # ~EUR 30K
        compliant = medical_si >= schengen_min_usd
        schengen_check = {
            "applicable": True,
            "compliant": compliant,
            "badgeLabel": "Schengen Visa Compliant" if compliant else "Below Schengen Minimum - Visa Risk",
            "badgeColor": "#22C55E" if compliant else "#EF4444",
            "details": f"Medical cover ${medical_si:,.0f} {'meets' if compliant else 'is below'} Schengen minimum of EUR 30,000 (~${schengen_min_usd:,})."
        }

    # Destination countries
    dest_countries = []
    if isinstance(destination, str) and destination:
        dest_countries = [c.strip() for c in destination.split(",") if c.strip()]

    geographic_scope = coverage_summary.get("geographicCoverage") or coverage_summary.get("coverageScope") or ""

    # Per-day cost
    trip_days = max(1, int(trip_duration) if trip_duration else 1)
    travelers_count = max(1, len(travelers) if travelers else 1)
    premium_val = float(premium) if premium else 0

    per_day = round(premium_val / trip_days, 2) if trip_days > 0 else 0
    per_person_per_day = round(per_day / travelers_count, 2) if travelers_count > 0 else 0

    # Verdict one-liner
    if pct >= 150:
        verdict_line = f"Your medical cover exceeds {region} benchmark by {pct - 100}%. Well positioned."
    elif pct >= 100:
        verdict_line = f"Your medical cover meets the {region} benchmark."
    elif pct >= 75:
        verdict_line = f"Your medical cover is {pct}% of the {region} benchmark. Marginal."
    else:
        verdict_line = f"Your medical cover is only {pct}% of recommended for {region}. Upgrade before departure."

    return {
        "destinations": {
            "countries": dest_countries,
            "coverageScope": str(geographic_scope),
            "scopeMatch": True,
            "scopeMatchNote": "All destinations covered under your scope" if dest_countries else ""
        },
        "medicalBenchmark": {
            "required": benchmark_usd,
            "requiredFormatted": benchmark_formatted,
            "yourCoverage": medical_si,
            "yourCoverageFormatted": your_formatted,
            "percentOfRequired": pct,
            "status": bm_status,
            "statusColor": bm_color,
            "note": bm_note
        },
        "schengenCompliance": schengen_check,
        "perDayCost": {
            "totalPremium": premium_val,
            "totalPremiumFormatted": f"Rs.{int(premium_val):,}" if premium_val else "N/A",
            "tripDays": trip_days,
            "travelersCount": travelers_count,
            "perDay": per_day,
            "perDayFormatted": f"Rs.{int(per_day):,}/day" if per_day else "N/A",
            "perPersonPerDay": per_person_per_day,
            "perPersonPerDayFormatted": f"Rs.{int(per_person_per_day):,}/day/person" if per_person_per_day else "N/A"
        },
        "verdictOneLiner": verdict_line
    }


def _build_emergency_reference(
    category_data: dict,
    insurer_name: str,
    destination: str,
    policy_details: dict
) -> dict:
    """Build emergency reference card data for PDF Page 6 per EAZR_05 Section 4.3."""
    from services.travel_insurance_report_generator import get_travel_claims_helpline

    emergency_contacts = category_data.get("emergencyContacts", {})
    traveller_details = category_data.get("travellerDetails", [])
    coverage_summary = category_data.get("coverageSummary", {})
    policy_id = category_data.get("policyIdentification", {})
    trip_details = category_data.get("tripDetails", {})
    cashless_info = category_data.get("medicalCoverage", {}).get("cashlessNetwork", {})

    helpline = get_travel_claims_helpline(insurer_name)
    abroad_helpline = emergency_contacts.get("emergencyHelpline24x7") or helpline
    from_india = helpline if helpline != abroad_helpline else f"1800-{helpline.replace('1800-', '')}" if helpline.startswith("1800") else helpline

    medical_si = _parse_travel_cover_amount(coverage_summary.get("medicalExpenses"))
    inr_equiv = int(medical_si * 83) if medical_si else 0
    medical_cover_str = f"${medical_si:,.0f} (Rs.{inr_equiv / 100000:.1f}L)" if medical_si else "See policy"

    travelers = []
    for t in (traveller_details or []):
        travelers.append({
            "name": t.get("name", ""),
            "passport": t.get("passportNumber", "")
        })

    return {
        "policyNumber": policy_id.get("policyNumber") or policy_details.get("policyNumber", ""),
        "validFrom": trip_details.get("tripStartDate") or policy_details.get("startDate", ""),
        "validTo": trip_details.get("tripEndDate") or policy_details.get("endDate", ""),
        "destinations": destination,
        "medicalCover": medical_cover_str,
        "helplines": {
            "fromIndia": from_india,
            "fromAbroad": abroad_helpline,
            "whatsapp": emergency_contacts.get("whatsapp", ""),
            "email": emergency_contacts.get("claimsEmail", "")
        },
        "cashlessNetwork": {
            "networkName": cashless_info.get("networkName", ""),
            "available": bool(cashless_info.get("available"))
        },
        "claimSteps": [
            "Call 24x7 assistance FIRST (numbers above)",
            "Go to nearest network hospital for cashless treatment",
            "Keep all receipts, medical reports, and prescriptions",
            "File claim within the time period specified in your policy",
            "Submit: Medical reports, bills, prescriptions, PIR (if baggage)"
        ],
        "travelers": travelers
    }


def _get_travel_strengths(scores_detailed: dict, category_data: dict) -> list:
    """
    Extract top coverage strengths from Travel S1/S2 scoring factors
    that scored >=80% of max points. Returns up to 5 strengths.
    """
    strengths = []
    strength_map = {
        "Medical SI vs Destination": ("Strong Medical Coverage", "Medical cover {detail}"),
        "Evacuation Coverage": ("Excellent Evacuation", "{detail}"),
        "Pre-existing Coverage": ("Pre-existing Covered", "{detail}"),
        "COVID Coverage": ("COVID Protected", "{detail}"),
        "Cashless Network": ("Cashless Available", "{detail}"),
        "Repatriation": ("Repatriation Included", "{detail}"),
        "Cancellation Cover": ("Trip Investment Protected", "{detail}"),
        "Cancellation Reasons": ("Comprehensive Cancellation", "{detail}"),
        "Delay Compensation": ("Delay Protection", "{detail}"),
        "Baggage Protection": ("Baggage Protected", "{detail}"),
        "Documentation Ease": ("Easy Claims Process", "{detail}"),
        "Passport Loss": ("Passport Loss Covered", "{detail}"),
    }

    scores = scores_detailed.get("scores", {})
    priority = 0
    for score_key in ["s1", "s2"]:
        score_data = scores.get(score_key, {})
        for factor in score_data.get("factors", []):
            pts_earned = factor.get("pointsEarned", factor.get("score", 0))
            pts_max = factor.get("pointsMax", factor.get("maxScore", 1))
            if pts_max > 0 and (pts_earned / pts_max) >= 0.80:
                name = factor.get("name", "")
                detail = factor.get("detail", "")
                if name in strength_map:
                    title, reason_tmpl = strength_map[name]
                    reason = reason_tmpl.replace("{detail}", detail)
                    priority += 1
                    strengths.append({"title": title, "reason": reason, "priority": priority})

    return strengths[:5]


def _analyze_travel_gaps_v10(
    coverage_data: dict,
    destination: str,
    medical_coverage: dict = None,
    trip_protection: dict = None,
    baggage_coverage: dict = None,
    exclusions: dict = None,
    travelers: list = None
) -> dict:
    """
    Wraps _analyze_travel_gaps() into V10 format with summary counts.
    """
    gaps_raw = _analyze_travel_gaps(
        coverage_data=coverage_data,
        destination=destination,
        medical_coverage=medical_coverage,
        trip_protection=trip_protection,
        baggage_coverage=baggage_coverage,
        exclusions=exclusions,
        travelers=travelers
    )

    severity_counts = {"high": 0, "medium": 0, "low": 0}
    enriched_gaps = []

    for g in gaps_raw:
        sev = g.get("severity", "low")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Parse estimated cost to int
        cost_str = g.get("estimatedCost", "")
        cost_val = 0
        if cost_str:
            nums = re.findall(r'[\d,]+', str(cost_str).replace(",", ""))
            if nums:
                try:
                    cost_val = int(nums[-1])
                except (ValueError, TypeError):
                    pass

        emi = int(cost_val / 6) if cost_val > 0 else 0

        enriched = dict(g)
        enriched["estimatedCost"] = cost_val
        enriched["estimatedCostFormatted"] = cost_str
        enriched["eazrEmi"] = emi
        enriched["eazrEmiFormatted"] = f"Rs.{emi:,}/mo" if emi > 0 else ""
        enriched_gaps.append(enriched)

    total = sum(severity_counts.values())
    return {
        "summary": {
            "high": severity_counts["high"],
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
            "total": total
        },
        "gaps": enriched_gaps
    }


def _select_travel_primary_scenario(
    destination: str,
    gaps_v10: dict,
    trip_details: dict = None,
    is_domestic: bool = False
) -> str:
    """
    Auto-select primary scenario per EAZR_05 Section 3.5 logic.
    Returns one of T001-T005.
    """
    gap_ids = set()
    if isinstance(gaps_v10, dict):
        for g in gaps_v10.get("gaps", []):
            gap_ids.add(g.get("gapId", ""))

    dest_lower = (destination or "").lower()
    trip_details = trip_details or {}

    # USA/Canada + G001 (medical inadequate) → T001
    if ("usa" in dest_lower or "canada" in dest_lower or "america" in dest_lower) and "G001" in gap_ids:
        return "T001"

    # Adventure activities + G005 → T005
    activities = trip_details.get("plannedActivities", []) or []
    if activities and "G005" in gap_ids:
        return "T005"

    # No cancellation (G004) + high trip cost → T002
    if "G004" in gap_ids:
        return "T002"

    # International default → T001
    if not is_domestic:
        return "T001"

    # Domestic default → T002
    return "T002"


def _build_travel_recommendations_v10(
    gaps_v10: dict,
    coverage_data: dict = None,
    trip_protection: dict = None,
    destination: str = "",
    trip_type: str = "",
    scores_detailed: dict = None
) -> dict:
    """
    Build V10-structured recommendations: quickWins + priorityUpgrades + totalUpgradeCost.
    """
    gaps_list = gaps_v10.get("gaps", []) if isinstance(gaps_v10, dict) else []
    gap_ids = {g.get("gapId") for g in gaps_list}

    # Quick Wins — always applicable
    quick_wins = [
        {
            "id": "download_emergency",
            "title": "Download Emergency Card PDF",
            "description": "Save the emergency reference page with helplines and claim steps for offline access abroad.",
            "effort": "1 minute",
            "icon": "download"
        },
        {
            "id": "save_helpline",
            "title": "Save Emergency Helpline in Contacts",
            "description": "Add insurer's 24x7 helpline to your phone contacts before departure.",
            "effort": "2 minutes",
            "icon": "contact_phone"
        }
    ]

    if "G005" in gap_ids:
        quick_wins.append({
            "id": "verify_adventure",
            "title": "Verify Adventure Activity Coverage",
            "description": "Call insurer to confirm specific activities (scuba, skiing, trekking) are covered.",
            "effort": "5 minutes",
            "icon": "sports"
        })

    # Priority Upgrades — mapped from gaps
    upgrade_map = {
        "G001": {
            "id": "upgrade_medical",
            "category": "enhancement",
            "priority": 1,
            "priorityLabel": "HIGH",
            "title": "Increase Medical Coverage",
            "description": f"Upgrade medical coverage for {destination or 'your destination'}. US needs $100K+, Europe needs EUR 30K+, Asia needs $50K+.",
            "estimatedCost": 5000,
            "estimatedCostFormatted": "Rs.2,000-8,000",
            "ipfEligible": True,
            "icon": "trending_up",
            "when": "Before departure",
            "gapMapping": ["G001"]
        },
        "G003": {
            "id": "add_covid",
            "category": "addon",
            "priority": 2,
            "priorityLabel": "MEDIUM",
            "title": "Add COVID Coverage",
            "description": "Include COVID-19 treatment and quarantine coverage. Hospitalization abroad costs $15,000-50,000.",
            "estimatedCost": 1000,
            "estimatedCostFormatted": "Rs.500-2,000",
            "ipfEligible": True,
            "icon": "coronavirus",
            "when": "Before departure",
            "gapMapping": ["G003"]
        },
        "G004": {
            "id": "add_cancellation",
            "category": "addon",
            "priority": 3,
            "priorityLabel": "MEDIUM",
            "title": "Add Trip Cancellation",
            "description": "Protect your travel investment. Non-refundable costs (flights, hotels, tours) can be Rs.1-3 lakhs.",
            "estimatedCost": 1500,
            "estimatedCostFormatted": "Rs.500-2,000",
            "ipfEligible": True,
            "icon": "event_busy",
            "when": "Before departure",
            "gapMapping": ["G004"]
        },
        "G005": {
            "id": "add_adventure",
            "category": "addon",
            "priority": 4,
            "priorityLabel": "LOW",
            "title": "Add Adventure Sports Cover",
            "description": "Cover injuries during adventure activities like scuba diving, skiing, trekking, paragliding.",
            "estimatedCost": 1000,
            "estimatedCostFormatted": "Rs.500-2,000",
            "ipfEligible": True,
            "icon": "sports_martial_arts",
            "when": "Before departure",
            "gapMapping": ["G005"]
        },
    }

    priority_upgrades = []
    total_annual = 0
    for gap_id in ["G001", "G003", "G004", "G005"]:
        if gap_id in gap_ids and gap_id in upgrade_map:
            rec = dict(upgrade_map[gap_id])
            cost = rec.get("estimatedCost", 0)
            rec["eazrEmi"] = int(cost / 6) if cost > 0 else 0
            rec["eazrEmiFormatted"] = f"Rs.{rec['eazrEmi']:,}/mo" if rec["eazrEmi"] > 0 else ""
            priority_upgrades.append(rec)
            total_annual += cost

    monthly_emi = int(total_annual / 12) if total_annual > 0 else 0

    # Multi-trip consideration
    trip_type_lower = str(trip_type).lower() if trip_type else ""
    multi_trip = None
    if "multi" not in trip_type_lower and "annual" not in trip_type_lower:
        multi_trip = {
            "applicable": True,
            "savingsPercent": "30-50%",
            "annualCost": "Rs.8,000-25,000 per year",
            "note": "If you travel 2+ times a year, an annual multi-trip policy can save 30-50% vs buying per-trip."
        }

    return {
        "quickWins": quick_wins,
        "priorityUpgrades": priority_upgrades,
        "totalUpgradeCost": {
            "annual": total_annual,
            "annualFormatted": f"Rs.{total_annual:,}" if total_annual else "Rs.0",
            "monthlyEmi": monthly_emi,
            "monthlyEmiFormatted": f"Rs.{monthly_emi:,}/mo" if monthly_emi else "Rs.0/mo"
        },
        "multiTripConsideration": multi_trip
    }
