"""
Health Insurance Extraction Schema — 84 fields.
Mirrors botproject's v2 ConfidenceField format.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Nested models ───────────────────────────────────────────────────────


class InsuredMember(BaseModel):
    memberName: Optional[Any] = None
    memberRelationship: Optional[Any] = None
    memberAge: Optional[Any] = None
    memberGender: Optional[Any] = None
    memberDOB: Optional[str] = None
    memberSumInsured: Optional[Any] = None
    memberCopay: Optional[Any] = None
    memberOPLimit: Optional[Any] = None
    memberPED: Optional[Any] = None


class AgeBasedCopay(BaseModel):
    ageBracket: Optional[str] = None
    copayPercentage: Optional[float] = None


class DiseaseSpecificCopay(BaseModel):
    disease: Optional[str] = None
    copayPercentage: Optional[float] = None


class AddOnPolicy(BaseModel):
    addOnName: Optional[str] = None
    uin: Optional[str] = None
    sumInsured: Optional[Any] = None
    premium: Optional[Any] = None


class Portability(BaseModel):
    available: Optional[bool] = None
    waitingPeriodCredit: Optional[str] = None


# ── Confidence-wrapped field ─────────────────────────────────────────


class CF(BaseModel):
    """ConfidenceField wrapper — every extracted value carries provenance."""

    value: Any = None
    source_page: Optional[int] = None
    confidence: float = 0.0


# ── Main schema ──────────────────────────────────────────────────────


class HealthExtraction(BaseModel):
    """Complete health insurance extraction — 84 fields."""

    # Policy Basics
    policyNumber: CF = Field(default_factory=CF)
    uin: CF = Field(default_factory=CF)
    insurerName: CF = Field(default_factory=CF)
    insurerRegistrationNumber: CF = Field(default_factory=CF)
    insurerTollFree: CF = Field(default_factory=CF)
    insurerAddress: CF = Field(default_factory=CF)
    productName: CF = Field(default_factory=CF)
    policyType: CF = Field(default_factory=CF)  # Individual/Family Floater/Group
    coverType: CF = Field(default_factory=CF)  # Individual/Floater
    policyPeriod: CF = Field(default_factory=CF)
    policyPeriodStart: CF = Field(default_factory=CF)
    policyPeriodEnd: CF = Field(default_factory=CF)
    policyHolderName: CF = Field(default_factory=CF)

    # Intermediaries
    tpaName: CF = Field(default_factory=CF)
    intermediaryName: CF = Field(default_factory=CF)
    intermediaryCode: CF = Field(default_factory=CF)
    intermediaryEmail: CF = Field(default_factory=CF)

    # Members & Coverage
    insuredMembers: CF = Field(default_factory=CF)  # value = list[InsuredMember]
    totalMembersCovered: CF = Field(default_factory=CF)
    sumInsured: CF = Field(default_factory=CF)
    roomRentLimit: CF = Field(default_factory=CF)
    roomRentCopay: CF = Field(default_factory=CF)
    icuLimit: CF = Field(default_factory=CF)
    icuDailyLimit: CF = Field(default_factory=CF)

    # Core Benefits
    preHospitalization: CF = Field(default_factory=CF)
    postHospitalization: CF = Field(default_factory=CF)
    dayCareProcedures: CF = Field(default_factory=CF)
    domiciliaryHospitalization: CF = Field(default_factory=CF)
    ambulanceCover: CF = Field(default_factory=CF)
    healthCheckup: CF = Field(default_factory=CF)
    ayushTreatment: CF = Field(default_factory=CF)
    organDonor: CF = Field(default_factory=CF)
    restoration: CF = Field(default_factory=CF)
    restorationAmount: CF = Field(default_factory=CF)
    modernTreatment: CF = Field(default_factory=CF)
    modernTreatmentLimit: CF = Field(default_factory=CF)
    mentalHealthCovered: CF = Field(default_factory=CF)
    mentalHealthLimit: CF = Field(default_factory=CF)
    dailyCashAllowance: CF = Field(default_factory=CF)
    convalescenceBenefit: CF = Field(default_factory=CF)
    consumablesCoverage: CF = Field(default_factory=CF)
    consumablesCoverageDetails: CF = Field(default_factory=CF)

    # Waiting Periods
    initialWaitingPeriod: CF = Field(default_factory=CF)
    preExistingDiseaseWaiting: CF = Field(default_factory=CF)
    specificDiseaseWaiting: CF = Field(default_factory=CF)
    maternityWaiting: CF = Field(default_factory=CF)
    accidentCoveredFromDay1: CF = Field(default_factory=CF)
    specificDiseasesList: CF = Field(default_factory=CF)

    # Copay
    generalCopay: CF = Field(default_factory=CF)  # Percentage: 0, 10, 20
    ageBasedCopay: CF = Field(default_factory=CF)  # value = list[AgeBasedCopay]
    diseaseSpecificCopay: CF = Field(default_factory=CF)

    # Sub-Limits
    cataractLimit: CF = Field(default_factory=CF)
    jointReplacementLimit: CF = Field(default_factory=CF)
    internalProsthesisLimit: CF = Field(default_factory=CF)
    kidneyStoneLimit: CF = Field(default_factory=CF)
    gallStoneLimit: CF = Field(default_factory=CF)
    otherSubLimits: CF = Field(default_factory=CF)

    # Exclusions
    permanentExclusions: CF = Field(default_factory=CF)
    conditionalExclusions: CF = Field(default_factory=CF)
    preExistingConditions: CF = Field(default_factory=CF)
    pedSpecificExclusions: CF = Field(default_factory=CF)

    # Premium & Bonuses
    basePremium: CF = Field(default_factory=CF)
    gst: CF = Field(default_factory=CF)
    totalPremium: CF = Field(default_factory=CF)
    premiumFrequency: CF = Field(default_factory=CF)
    otherAddOnPremiums: CF = Field(default_factory=CF)
    existingCustomerDiscount: CF = Field(default_factory=CF)
    healthGracePeriod: CF = Field(default_factory=CF)
    ncbPercentage: CF = Field(default_factory=CF)
    currentNcb: CF = Field(default_factory=CF)
    maxNcbPercentage: CF = Field(default_factory=CF)
    ncbAmount: CF = Field(default_factory=CF)
    ncbProtect: CF = Field(default_factory=CF)
    ncbBoost: CF = Field(default_factory=CF)
    accumulatedNcbAmount: CF = Field(default_factory=CF)
    cumulativeBonusAmount: CF = Field(default_factory=CF)
    inflationShieldAmount: CF = Field(default_factory=CF)
    totalEffectiveCoverage: CF = Field(default_factory=CF)

    # Add-ons & Riders
    hasAddOn: CF = Field(default_factory=CF)
    addOnPoliciesList: CF = Field(default_factory=CF)
    claimShield: CF = Field(default_factory=CF)
    ncbShield: CF = Field(default_factory=CF)
    inflationShield: CF = Field(default_factory=CF)
    inflationShieldPercentage: CF = Field(default_factory=CF)

    # PED & Continuity
    declaredConditions: CF = Field(default_factory=CF)
    pedWaitingPeriodCompleted: CF = Field(default_factory=CF)
    pedStatus: CF = Field(default_factory=CF)
    firstEnrollmentDate: CF = Field(default_factory=CF)
    insuredSinceDate: CF = Field(default_factory=CF)
    previousPolicyNumber: CF = Field(default_factory=CF)
    continuousCoverageYears: CF = Field(default_factory=CF)
    claimHistory: CF = Field(default_factory=CF)
    portability: CF = Field(default_factory=CF)

    # Network & Claims
    networkHospitalsCount: CF = Field(default_factory=CF)
    cashlessFacility: CF = Field(default_factory=CF)
    networkType: CF = Field(default_factory=CF)
    claimSettlementRatio: CF = Field(default_factory=CF)
    claimProcess: CF = Field(default_factory=CF)
    claimIntimation: CF = Field(default_factory=CF)
    claimDocuments: CF = Field(default_factory=CF)
    preAuthTurnaround: CF = Field(default_factory=CF)
