"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
PA extraction schema — structured output for personal accident policy data.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CF(BaseModel):
    value: Any = None
    source_page: Optional[int] = None
    confidence: float = 0.0


class PPDEntry(BaseModel):
    disability: Optional[str] = None
    percentage: Optional[float] = None


class PAInsuredMember(BaseModel):
    memberName: Optional[str] = None
    memberRelationship: Optional[str] = None
    memberAge: Optional[int] = None
    memberGender: Optional[str] = None
    memberSumInsured: Optional[Any] = None


class PAExtraction(BaseModel):
    """Complete personal accident insurance extraction — 54 fields."""

    # Policy Basics
    policyNumber: CF = Field(default_factory=CF)
    uin: CF = Field(default_factory=CF)
    insurerName: CF = Field(default_factory=CF)
    productName: CF = Field(default_factory=CF)
    policyPeriodStart: CF = Field(default_factory=CF)
    policyPeriodEnd: CF = Field(default_factory=CF)
    policyHolderName: CF = Field(default_factory=CF)

    # Policy Type
    paInsuranceType: CF = Field(default_factory=CF)  # Individual/Family/Group
    paPolicySubType: CF = Field(default_factory=CF)
    paCertificateNumber: CF = Field(default_factory=CF)
    groupPolicyholderName: CF = Field(default_factory=CF)
    groupPolicyNumber: CF = Field(default_factory=CF)
    paOccupationClass: CF = Field(default_factory=CF)

    # Sum Insured & Death
    paSumInsured: CF = Field(default_factory=CF)
    accidentalDeathBenefitPercentage: CF = Field(default_factory=CF)
    accidentalDeathBenefitAmount: CF = Field(default_factory=CF)
    doubleIndemnityApplicable: CF = Field(default_factory=CF)
    doubleIndemnityConditions: CF = Field(default_factory=CF)

    # PTD
    permanentTotalDisabilityCovered: CF = Field(default_factory=CF)
    permanentTotalDisabilityPercentage: CF = Field(default_factory=CF)
    permanentTotalDisabilityAmount: CF = Field(default_factory=CF)
    ptdConditions: CF = Field(default_factory=CF)

    # PPD
    ppdSchedule: CF = Field(default_factory=CF)  # value = list[PPDEntry]

    # TTD
    temporaryTotalDisabilityCovered: CF = Field(default_factory=CF)
    ttdBenefitType: CF = Field(default_factory=CF)
    ttdBenefitPercentage: CF = Field(default_factory=CF)
    ttdBenefitAmount: CF = Field(default_factory=CF)
    ttdMaximumWeeks: CF = Field(default_factory=CF)
    ttdWaitingPeriodDays: CF = Field(default_factory=CF)

    # Medical Expenses
    medicalExpensesCovered: CF = Field(default_factory=CF)
    medicalExpensesLimitType: CF = Field(default_factory=CF)
    medicalExpensesLimitPercentage: CF = Field(default_factory=CF)
    medicalExpensesLimitAmount: CF = Field(default_factory=CF)
    medicalExpensesPerAccidentOrAnnual: CF = Field(default_factory=CF)

    # Additional Benefits
    educationBenefitCovered: CF = Field(default_factory=CF)
    educationBenefitAmount: CF = Field(default_factory=CF)
    educationBenefitType: CF = Field(default_factory=CF)
    loanEmiCoverCovered: CF = Field(default_factory=CF)
    loanEmiCoverMaxMonths: CF = Field(default_factory=CF)
    loanEmiCoverMaxAmountPerMonth: CF = Field(default_factory=CF)
    ambulanceChargesCovered: CF = Field(default_factory=CF)
    ambulanceChargesLimit: CF = Field(default_factory=CF)
    transportMortalRemainsCovered: CF = Field(default_factory=CF)
    transportMortalRemainsLimit: CF = Field(default_factory=CF)
    funeralExpensesCovered: CF = Field(default_factory=CF)
    funeralExpensesLimit: CF = Field(default_factory=CF)
    homeModificationCovered: CF = Field(default_factory=CF)
    homeModificationLimit: CF = Field(default_factory=CF)
    vehicleModificationCovered: CF = Field(default_factory=CF)
    vehicleModificationLimit: CF = Field(default_factory=CF)
    carriageOfAttendantCovered: CF = Field(default_factory=CF)
    carriageOfAttendantLimit: CF = Field(default_factory=CF)

    # Exclusions & Restrictions
    paStandardExclusions: CF = Field(default_factory=CF)
    paOccupationRestrictions: CF = Field(default_factory=CF)
    paAgeMinimum: CF = Field(default_factory=CF)
    paAgeMaximum: CF = Field(default_factory=CF)
    paMaxRenewalAge: CF = Field(default_factory=CF)
    ttdEliminationPeriod: CF = Field(default_factory=CF)

    # Premium
    paPremiumFrequency: CF = Field(default_factory=CF)
    paAgeBand: CF = Field(default_factory=CF)
    basePremium: CF = Field(default_factory=CF)
    gst: CF = Field(default_factory=CF)
    totalPremium: CF = Field(default_factory=CF)

    # Insured Members
    paInsuredMembers: CF = Field(default_factory=CF)  # value = list[PAInsuredMember]
