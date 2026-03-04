"""
Common extraction types shared across all policy categories.
Mirrors botproject's ConfidenceField pattern with Pydantic v2.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    """Every extracted value carries provenance metadata."""

    value: Any = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_page: Optional[int] = None
    source_clause: Optional[str] = None
    extraction_note: Optional[str] = None


def cf(
    value: Any = None,
    source_page: Optional[int] = None,
    confidence: float = 0.0,
) -> dict:
    """Shorthand to build a ConfidenceField dict (for LLM output parsing)."""
    return {"value": value, "source_page": source_page, "confidence": confidence}


# ── Criticality levels (weight multipliers for validation) ──────────────

CRITICALITY_CRITICAL = 3  # Must be present and accurate
CRITICALITY_IMPORTANT = 2  # Should be present
CRITICALITY_STANDARD = 1  # Nice to have

HEALTH_CRITICALITY = {
    "policyNumber": CRITICALITY_CRITICAL,
    "insurerName": CRITICALITY_CRITICAL,
    "sumInsured": CRITICALITY_CRITICAL,
    "totalPremium": CRITICALITY_CRITICAL,
    "policyPeriodStart": CRITICALITY_CRITICAL,
    "policyPeriodEnd": CRITICALITY_CRITICAL,
    "roomRentLimit": CRITICALITY_CRITICAL,
    "generalCopay": CRITICALITY_CRITICAL,
    "preExistingDiseaseWaiting": CRITICALITY_CRITICAL,
    "insuredMembers": CRITICALITY_CRITICAL,
    "basePremium": CRITICALITY_CRITICAL,
    # Important
    "uin": CRITICALITY_IMPORTANT,
    "coverType": CRITICALITY_IMPORTANT,
    "preHospitalization": CRITICALITY_IMPORTANT,
    "postHospitalization": CRITICALITY_IMPORTANT,
    "dayCareProcedures": CRITICALITY_IMPORTANT,
    "restoration": CRITICALITY_IMPORTANT,
    "initialWaitingPeriod": CRITICALITY_IMPORTANT,
    "networkHospitalsCount": CRITICALITY_IMPORTANT,
    "ayushTreatment": CRITICALITY_IMPORTANT,
    "ncbPercentage": CRITICALITY_IMPORTANT,
    "ambulanceCover": CRITICALITY_IMPORTANT,
    "claimSettlementRatio": CRITICALITY_IMPORTANT,
}

MOTOR_CRITICALITY = {
    "policyNumber": CRITICALITY_CRITICAL,
    "insurerName": CRITICALITY_CRITICAL,
    "idv": CRITICALITY_CRITICAL,
    "odPremium": CRITICALITY_CRITICAL,
    "tpPremium": CRITICALITY_CRITICAL,
    "totalPremium": CRITICALITY_CRITICAL,
    "policyPeriodStart": CRITICALITY_CRITICAL,
    "policyPeriodEnd": CRITICALITY_CRITICAL,
    "registrationNumber": CRITICALITY_CRITICAL,
    "productType": CRITICALITY_CRITICAL,
    # Important
    "uin": CRITICALITY_IMPORTANT,
    "vehicleMake": CRITICALITY_IMPORTANT,
    "vehicleModel": CRITICALITY_IMPORTANT,
    "ncbPercentage": CRITICALITY_IMPORTANT,
    "zeroDepreciation": CRITICALITY_IMPORTANT,
    "engineProtection": CRITICALITY_IMPORTANT,
    "compulsoryDeductible": CRITICALITY_IMPORTANT,
    "paOwnerCover": CRITICALITY_IMPORTANT,
}

LIFE_CRITICALITY = {
    "policyNumber": CRITICALITY_CRITICAL,
    "insurerName": CRITICALITY_CRITICAL,
    "sumAssured": CRITICALITY_CRITICAL,
    "premiumAmount": CRITICALITY_CRITICAL,
    "policyTerm": CRITICALITY_CRITICAL,
    "policyType": CRITICALITY_CRITICAL,
    "policyPeriodStart": CRITICALITY_CRITICAL,
    "maturityDate": CRITICALITY_CRITICAL,
    # Important
    "uin": CRITICALITY_IMPORTANT,
    "premiumPayingTerm": CRITICALITY_IMPORTANT,
    "deathBenefit": CRITICALITY_IMPORTANT,
    "riders": CRITICALITY_IMPORTANT,
    "nominees": CRITICALITY_IMPORTANT,
    "surrenderValue": CRITICALITY_IMPORTANT,
    "bonusType": CRITICALITY_IMPORTANT,
}

PA_CRITICALITY = {
    "policyNumber": CRITICALITY_CRITICAL,
    "insurerName": CRITICALITY_CRITICAL,
    "paSumInsured": CRITICALITY_CRITICAL,
    "accidentalDeathBenefitPercentage": CRITICALITY_CRITICAL,
    "permanentTotalDisabilityPercentage": CRITICALITY_CRITICAL,
    "policyPeriodStart": CRITICALITY_CRITICAL,
    "policyPeriodEnd": CRITICALITY_CRITICAL,
    # Important
    "uin": CRITICALITY_IMPORTANT,
    "ppdSchedule": CRITICALITY_IMPORTANT,
    "temporaryTotalDisabilityCovered": CRITICALITY_IMPORTANT,
    "medicalExpensesCovered": CRITICALITY_IMPORTANT,
}

TRAVEL_CRITICALITY = {
    "policyNumber": CRITICALITY_CRITICAL,
    "insurerName": CRITICALITY_CRITICAL,
    "medicalExpenses": CRITICALITY_CRITICAL,
    "tripStartDate": CRITICALITY_CRITICAL,
    "tripEndDate": CRITICALITY_CRITICAL,
    "totalPremium": CRITICALITY_CRITICAL,
    "destinationCountries": CRITICALITY_CRITICAL,
    # Important
    "uin": CRITICALITY_IMPORTANT,
    "tripType": CRITICALITY_IMPORTANT,
    "emergencyMedicalEvacuation": CRITICALITY_IMPORTANT,
    "tripCancellation": CRITICALITY_IMPORTANT,
    "baggageLoss": CRITICALITY_IMPORTANT,
    "personalLiability": CRITICALITY_IMPORTANT,
    "preExistingCovered": CRITICALITY_IMPORTANT,
}

CRITICALITY_BY_TYPE = {
    "health": HEALTH_CRITICALITY,
    "life": LIFE_CRITICALITY,
    "motor": MOTOR_CRITICALITY,
    "travel": TRAVEL_CRITICALITY,
    "pa": PA_CRITICALITY,
}


def get_criticality(category: str, field_name: str) -> int:
    """Return weight multiplier for a field."""
    return CRITICALITY_BY_TYPE.get(category, {}).get(
        field_name, CRITICALITY_STANDARD
    )


# ── Insurer CSR data (from botproject helpers.py) ──────────────────────

CSR_DATA = {
    "ACKO": 98.50,
    "Niva Bupa": 96.30,
    "Max Bupa": 96.30,
    "ICICI Lombard": 96.49,
    "HDFC ERGO": 99.33,
    "Bajaj Allianz": 93.06,
    "Tata AIG": 87.08,
    "SBI General": 92.78,
    "Reliance General": 95.51,
    "New India Assurance": 92.31,
    "Oriental Insurance": 90.45,
    "United India": 89.72,
    "Digit Insurance": 97.18,
    "Go Digit": 97.18,
    "Care Health": 94.17,
    "Star Health": 90.37,
    "National Insurance": 91.28,
    "Future Generali": 88.96,
    "IFFCO Tokio": 94.00,
    "Cholamandalam MS": 91.00,
    "Royal Sundaram": 89.00,
    "Liberty General": 86.00,
    "LIC": 98.62,
    "HDFC Life": 99.00,
    "ICICI Prudential Life": 97.80,
    "SBI Life": 97.01,
    "Max Life": 99.34,
    "Kotak Mahindra Life": 98.00,
    "Aditya Birla Sun Life": 97.50,
    "Tata AIA Life": 98.50,
    "PNB MetLife": 97.00,
    "Canara HSBC": 96.00,
    "Exide Life": 97.50,
    "Edelweiss Tokio": 96.00,
    "Aegon Life": 95.00,
    "Aviva Life": 96.00,
    "Bharti AXA Life": 97.00,
    "IndiaFirst Life": 96.00,
    "Pramerica Life": 97.00,
    "Sahara Life": 90.00,
    "Shriram Life": 95.00,
    "Aditya Birla Health": 95.00,
    "ManipalCigna": 93.50,
    "Manipal Cigna": 93.50,
}


def lookup_csr(insurer_name: str) -> float | None:
    """Look up Claim Settlement Ratio by insurer name (fuzzy)."""
    if not insurer_name:
        return None
    name = insurer_name.strip()
    # Exact match
    if name in CSR_DATA:
        return CSR_DATA[name]
    # Case-insensitive match
    lower = name.lower()
    for k, v in CSR_DATA.items():
        if k.lower() == lower:
            return v
    # Partial match
    for k, v in CSR_DATA.items():
        if k.lower() in lower or lower in k.lower():
            return v
    return None


# ── Network hospital data ──────────────────────────────────────────────

NETWORK_HOSPITALS = {
    "ACKO": 14300,
    "Niva Bupa": 10000,
    "ICICI Lombard": 7200,
    "HDFC ERGO": 14300,
    "Bajaj Allianz": 10000,
    "Tata AIG": 7200,
    "SBI General": 9500,
    "Reliance General": 9100,
    "New India Assurance": 10000,
    "Oriental Insurance": 9000,
    "United India": 8000,
    "Digit Insurance": 16000,
    "Go Digit": 16000,
    "Care Health": 18500,
    "Star Health": 14000,
    "National Insurance": 9500,
    "Future Generali": 9700,
    "IFFCO Tokio": 8500,
    "Cholamandalam MS": 8000,
    "Royal Sundaram": 7200,
    "Liberty General": 5500,
    "Aditya Birla Health": 10000,
    "ManipalCigna": 8000,
    "Manipal Cigna": 8000,
}


def lookup_network_hospitals(insurer_name: str) -> int | None:
    """Look up network hospital count by insurer name (fuzzy)."""
    if not insurer_name:
        return None
    name = insurer_name.strip()
    if name in NETWORK_HOSPITALS:
        return NETWORK_HOSPITALS[name]
    lower = name.lower()
    for k, v in NETWORK_HOSPITALS.items():
        if k.lower() in lower or lower in k.lower():
            return v
    return None
