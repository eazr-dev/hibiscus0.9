"""
Base schemas for PRD v2 extraction.

Defines ConfidenceField format and FieldCriticality levels used across
all 5 insurance type schemas.
"""
from enum import Enum
from typing import Any, Optional, TypedDict


class FieldCriticality(str, Enum):
    """How critical a field is for scoring and validation.

    Weights: CRITICAL=3x, IMPORTANT=2x, STANDARD=1x
    """
    CRITICAL = "critical"
    IMPORTANT = "important"
    STANDARD = "standard"


class ConfidenceField(TypedDict, total=False):
    """PRD v2 per-field extraction result with evidence grounding.

    Every extracted field returns this shape instead of a bare value.
    """
    value: Any
    source_page: Optional[int]
    confidence: float  # 0.0 - 1.0


def cf(value: Any, source_page: Optional[int] = None, confidence: float = 0.0) -> ConfidenceField:
    """Shorthand to build a ConfidenceField dict."""
    return ConfidenceField(value=value, source_page=source_page, confidence=confidence)


# Field criticality maps per type — used by Phase 2 (4-check validation)
# and Phase 3 (weighted confidence scoring).

HEALTH_CRITICALITY: dict[str, FieldCriticality] = {
    # Critical (3x weight)
    "policyNumber": FieldCriticality.CRITICAL,
    "insurerName": FieldCriticality.CRITICAL,
    "sumInsured": FieldCriticality.CRITICAL,
    "premium": FieldCriticality.CRITICAL,
    "policyPeriodStart": FieldCriticality.CRITICAL,
    "policyPeriodEnd": FieldCriticality.CRITICAL,
    "roomRentLimit": FieldCriticality.CRITICAL,
    "copay": FieldCriticality.CRITICAL,
    "generalCopay": FieldCriticality.CRITICAL,
    "preExistingDiseaseWaiting": FieldCriticality.CRITICAL,
    "insuredMembers": FieldCriticality.CRITICAL,
    # Important (2x weight)
    "uin": FieldCriticality.IMPORTANT,
    "coverType": FieldCriticality.IMPORTANT,
    "preHospitalization": FieldCriticality.IMPORTANT,
    "postHospitalization": FieldCriticality.IMPORTANT,
    "dayCareProcedures": FieldCriticality.IMPORTANT,
    "restoration": FieldCriticality.IMPORTANT,
    "initialWaitingPeriod": FieldCriticality.IMPORTANT,
    "networkHospitalsCount": FieldCriticality.IMPORTANT,
    "ayushTreatment": FieldCriticality.IMPORTANT,
    "ncbPercentage": FieldCriticality.IMPORTANT,
    "ambulanceCover": FieldCriticality.IMPORTANT,
    "claimSettlementRatio": FieldCriticality.IMPORTANT,
}

MOTOR_CRITICALITY: dict[str, FieldCriticality] = {
    "policyNumber": FieldCriticality.CRITICAL,
    "insurerName": FieldCriticality.CRITICAL,
    "idv": FieldCriticality.CRITICAL,
    "odPremium": FieldCriticality.CRITICAL,
    "tpPremium": FieldCriticality.CRITICAL,
    "totalPremium": FieldCriticality.CRITICAL,
    "policyPeriodStart": FieldCriticality.CRITICAL,
    "policyPeriodEnd": FieldCriticality.CRITICAL,
    "registrationNumber": FieldCriticality.CRITICAL,
    "productType": FieldCriticality.CRITICAL,
    "uin": FieldCriticality.IMPORTANT,
    "vehicleMake": FieldCriticality.IMPORTANT,
    "vehicleModel": FieldCriticality.IMPORTANT,
    "ncbPercentage": FieldCriticality.IMPORTANT,
    "zeroDepreciation": FieldCriticality.IMPORTANT,
    "engineProtection": FieldCriticality.IMPORTANT,
    "compulsoryDeductible": FieldCriticality.IMPORTANT,
    "paOwnerCover": FieldCriticality.IMPORTANT,
}

LIFE_CRITICALITY: dict[str, FieldCriticality] = {
    "policyNumber": FieldCriticality.CRITICAL,
    "insurerName": FieldCriticality.CRITICAL,
    "sumAssured": FieldCriticality.CRITICAL,
    "premiumAmount": FieldCriticality.CRITICAL,
    "policyTerm": FieldCriticality.CRITICAL,
    "policyType": FieldCriticality.CRITICAL,
    "policyPeriodStart": FieldCriticality.CRITICAL,
    "maturityDate": FieldCriticality.CRITICAL,
    "uin": FieldCriticality.IMPORTANT,
    "premiumPayingTerm": FieldCriticality.IMPORTANT,
    "deathBenefit": FieldCriticality.IMPORTANT,
    "riders": FieldCriticality.IMPORTANT,
    "nominees": FieldCriticality.IMPORTANT,
    "surrenderValue": FieldCriticality.IMPORTANT,
    "bonusType": FieldCriticality.IMPORTANT,
}

PA_CRITICALITY: dict[str, FieldCriticality] = {
    "policyNumber": FieldCriticality.CRITICAL,
    "insurerName": FieldCriticality.CRITICAL,
    "paSumInsured": FieldCriticality.CRITICAL,
    "accidentalDeathBenefitPercentage": FieldCriticality.CRITICAL,
    "permanentTotalDisabilityPercentage": FieldCriticality.CRITICAL,
    "policyPeriodStart": FieldCriticality.CRITICAL,
    "policyPeriodEnd": FieldCriticality.CRITICAL,
    "uin": FieldCriticality.IMPORTANT,
    "permanentPartialDisabilityCovered": FieldCriticality.IMPORTANT,
    "temporaryTotalDisabilityCovered": FieldCriticality.IMPORTANT,
    "medicalExpensesCovered": FieldCriticality.IMPORTANT,
    "ppdSchedule": FieldCriticality.IMPORTANT,
}

TRAVEL_CRITICALITY: dict[str, FieldCriticality] = {
    "policyNumber": FieldCriticality.CRITICAL,
    "insurerName": FieldCriticality.CRITICAL,
    "medicalExpenses": FieldCriticality.CRITICAL,
    "tripStartDate": FieldCriticality.CRITICAL,
    "tripEndDate": FieldCriticality.CRITICAL,
    "totalPremium": FieldCriticality.CRITICAL,
    "destinationCountries": FieldCriticality.CRITICAL,
    "uin": FieldCriticality.IMPORTANT,
    "tripType": FieldCriticality.IMPORTANT,
    "emergencyMedicalEvacuation": FieldCriticality.IMPORTANT,
    "tripCancellation": FieldCriticality.IMPORTANT,
    "baggageLoss": FieldCriticality.IMPORTANT,
    "personalLiability": FieldCriticality.IMPORTANT,
    "preExistingCovered": FieldCriticality.IMPORTANT,
}

# Map type string to criticality map
CRITICALITY_MAPS: dict[str, dict[str, FieldCriticality]] = {
    "health": HEALTH_CRITICALITY,
    "motor": MOTOR_CRITICALITY,
    "life": LIFE_CRITICALITY,
    "pa": PA_CRITICALITY,
    "travel": TRAVEL_CRITICALITY,
}
