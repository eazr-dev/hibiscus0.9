"""
Travel Insurance Extraction Schema — 71 fields.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CF(BaseModel):
    value: Any = None
    source_page: Optional[int] = None
    confidence: float = 0.0


class Traveller(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    dateOfBirth: Optional[str] = None
    relationship: Optional[str] = None
    passportNumber: Optional[str] = None
    preExistingConditionsDeclared: Optional[Any] = None


class TravelExtraction(BaseModel):
    """Complete travel insurance extraction — 71 fields."""

    # Policy Basics
    policyNumber: CF = Field(default_factory=CF)
    uin: CF = Field(default_factory=CF)
    insurerName: CF = Field(default_factory=CF)
    productName: CF = Field(default_factory=CF)
    policyIssueDate: CF = Field(default_factory=CF)
    policyStatus: CF = Field(default_factory=CF)
    tripType: CF = Field(default_factory=CF)
    travelType: CF = Field(default_factory=CF)
    geographicCoverage: CF = Field(default_factory=CF)
    policyPeriodStart: CF = Field(default_factory=CF)
    policyPeriodEnd: CF = Field(default_factory=CF)
    policyHolderName: CF = Field(default_factory=CF)

    # Trip Details
    tripStartDate: CF = Field(default_factory=CF)
    tripEndDate: CF = Field(default_factory=CF)
    tripDuration: CF = Field(default_factory=CF)
    destinationCountries: CF = Field(default_factory=CF)
    originCountry: CF = Field(default_factory=CF)
    purposeOfTravel: CF = Field(default_factory=CF)

    # Travellers
    travellers: CF = Field(default_factory=CF)  # value = list[Traveller]

    # Medical Coverage
    medicalExpenses: CF = Field(default_factory=CF)
    medicalDeductible: CF = Field(default_factory=CF)
    coverageIncludes: CF = Field(default_factory=CF)
    emergencyMedicalEvacuation: CF = Field(default_factory=CF)
    repatriationOfRemains: CF = Field(default_factory=CF)
    covidTreatmentCovered: CF = Field(default_factory=CF)
    covidQuarantineCovered: CF = Field(default_factory=CF)
    covidQuarantineLimit: CF = Field(default_factory=CF)
    preExistingCovered: CF = Field(default_factory=CF)
    preExistingConditions: CF = Field(default_factory=CF)
    preExistingLimit: CF = Field(default_factory=CF)
    preExistingAgeRestriction: CF = Field(default_factory=CF)
    maternityCovered: CF = Field(default_factory=CF)

    # Network & Cashless
    cashlessNetworkAvailable: CF = Field(default_factory=CF)
    cashlessNetworkName: CF = Field(default_factory=CF)
    cashlessHospitalsCount: CF = Field(default_factory=CF)
    assistanceHelplineForCashless: CF = Field(default_factory=CF)

    # Trip-Related Coverage
    tripCancellation: CF = Field(default_factory=CF)
    tripCancellationCoveredReasons: CF = Field(default_factory=CF)
    tripCancellationNotCoveredReasons: CF = Field(default_factory=CF)
    tripInterruption: CF = Field(default_factory=CF)
    tripCurtailmentCovered: CF = Field(default_factory=CF)
    tripCurtailmentLimit: CF = Field(default_factory=CF)
    tripCurtailmentBenefitType: CF = Field(default_factory=CF)
    flightDelay: CF = Field(default_factory=CF)
    tripDelayTriggerHours: CF = Field(default_factory=CF)
    tripDelayCoveredExpenses: CF = Field(default_factory=CF)
    missedConnectionCovered: CF = Field(default_factory=CF)
    missedConnectionTriggerHours: CF = Field(default_factory=CF)
    missedConnectionBenefitAmount: CF = Field(default_factory=CF)
    hijackDistress: CF = Field(default_factory=CF)

    # Baggage & Misc
    baggageLoss: CF = Field(default_factory=CF)
    baggagePerItemLimit: CF = Field(default_factory=CF)
    baggageValuablesLimit: CF = Field(default_factory=CF)
    baggageDocumentationRequired: CF = Field(default_factory=CF)
    baggageDelay: CF = Field(default_factory=CF)
    passportLoss: CF = Field(default_factory=CF)

    # Liability & Accident
    personalLiability: CF = Field(default_factory=CF)
    accidentalDeath: CF = Field(default_factory=CF)
    permanentDisability: CF = Field(default_factory=CF)
    homeburglary: CF = Field(default_factory=CF)

    # Sports & Adventure
    adventureSportsExclusion: CF = Field(default_factory=CF)
    sportsCoveredList: CF = Field(default_factory=CF)
    sportsExcludedList: CF = Field(default_factory=CF)
    adventureAdditionalPremium: CF = Field(default_factory=CF)

    # Premium
    travelBasePremium: CF = Field(default_factory=CF)
    travelGst: CF = Field(default_factory=CF)
    travelTotalPremium: CF = Field(default_factory=CF)
    premiumPerDay: CF = Field(default_factory=CF)
    premiumAgeBand: CF = Field(default_factory=CF)
    premiumDestinationZone: CF = Field(default_factory=CF)
    premiumCoverageLevel: CF = Field(default_factory=CF)
    coverageCurrency: CF = Field(default_factory=CF)
    deductiblePerClaim: CF = Field(default_factory=CF)
    schengenCompliant: CF = Field(default_factory=CF)

    # Contact & Support
    emergencyHelpline24x7: CF = Field(default_factory=CF)
    claimsEmail: CF = Field(default_factory=CF)
    insurerAddress: CF = Field(default_factory=CF)
    primaryContactName: CF = Field(default_factory=CF)
    primaryContactPhone: CF = Field(default_factory=CF)
    primaryContactEmail: CF = Field(default_factory=CF)
    emergencyContactIndiaName: CF = Field(default_factory=CF)
    emergencyContactIndiaRelationship: CF = Field(default_factory=CF)
    emergencyContactIndiaPhone: CF = Field(default_factory=CF)
