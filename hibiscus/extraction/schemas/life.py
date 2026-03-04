"""
Life Insurance Extraction Schema — 60 fields.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CF(BaseModel):
    value: Any = None
    source_page: Optional[int] = None
    confidence: float = 0.0


class Rider(BaseModel):
    riderName: Optional[str] = None
    riderSumAssured: Optional[Any] = None
    riderPremium: Optional[Any] = None
    riderTerm: Optional[Any] = None


class Nominee(BaseModel):
    nomineeName: Optional[str] = None
    nomineeRelationship: Optional[str] = None
    nomineeShare: Optional[float] = None
    nomineeAge: Optional[int] = None


class FundOption(BaseModel):
    fundName: Optional[str] = None
    allocation: Optional[float] = None


class ModalPremiumBreakdown(BaseModel):
    base: Optional[float] = None
    gst: Optional[float] = None
    rider: Optional[float] = None


class LifeExtraction(BaseModel):
    """Complete life insurance extraction — 60 fields."""

    # Policy Basics
    policyNumber: CF = Field(default_factory=CF)
    uin: CF = Field(default_factory=CF)
    insurerName: CF = Field(default_factory=CF)
    productName: CF = Field(default_factory=CF)
    policyType: CF = Field(default_factory=CF)  # Term/Endowment/ULIP/Whole Life/Money Back/Pension
    policyIssueDate: CF = Field(default_factory=CF)
    policyStatus: CF = Field(default_factory=CF)  # Active/Lapsed/Paid-Up/Surrendered
    policyPeriodStart: CF = Field(default_factory=CF)
    policyPeriodEnd: CF = Field(default_factory=CF)

    # Policyholder & Life Assured
    policyholderName: CF = Field(default_factory=CF)
    policyholderDob: CF = Field(default_factory=CF)
    policyholderAge: CF = Field(default_factory=CF)
    policyholderGender: CF = Field(default_factory=CF)
    lifeAssuredName: CF = Field(default_factory=CF)
    lifeAssuredDob: CF = Field(default_factory=CF)
    lifeAssuredAge: CF = Field(default_factory=CF)
    relationshipWithPolicyholder: CF = Field(default_factory=CF)

    # Coverage & Terms
    sumAssured: CF = Field(default_factory=CF)
    coverType: CF = Field(default_factory=CF)  # Level/Increasing/Decreasing
    policyTerm: CF = Field(default_factory=CF)
    premiumPayingTerm: CF = Field(default_factory=CF)
    maturityDate: CF = Field(default_factory=CF)
    deathBenefit: CF = Field(default_factory=CF)

    # Premiums
    premiumAmount: CF = Field(default_factory=CF)
    premiumFrequency: CF = Field(default_factory=CF)
    premiumDueDate: CF = Field(default_factory=CF)
    gracePeriod: CF = Field(default_factory=CF)
    modalPremiumBreakdown: CF = Field(default_factory=CF)
    basePremium: CF = Field(default_factory=CF)
    gst: CF = Field(default_factory=CF)
    totalPremium: CF = Field(default_factory=CF)

    # Riders
    riders: CF = Field(default_factory=CF)  # value = list[Rider]

    # Bonus & Valuation
    bonusType: CF = Field(default_factory=CF)
    declaredBonusRate: CF = Field(default_factory=CF)
    accruedBonus: CF = Field(default_factory=CF)
    surrenderValue: CF = Field(default_factory=CF)
    paidUpValue: CF = Field(default_factory=CF)
    loanValue: CF = Field(default_factory=CF)

    # ULIP-Specific
    fundOptions: CF = Field(default_factory=CF)  # value = list[FundOption]
    currentNav: CF = Field(default_factory=CF)
    unitsHeld: CF = Field(default_factory=CF)
    fundValue: CF = Field(default_factory=CF)
    switchOptions: CF = Field(default_factory=CF)
    partialWithdrawal: CF = Field(default_factory=CF)

    # Nominees & Appointees
    nominees: CF = Field(default_factory=CF)  # value = list[Nominee]
    appointeeName: CF = Field(default_factory=CF)
    appointeeRelationship: CF = Field(default_factory=CF)

    # Policy Features
    revivalPeriod: CF = Field(default_factory=CF)
    freelookPeriod: CF = Field(default_factory=CF)
    policyLoanInterestRate: CF = Field(default_factory=CF)
    autoPayMode: CF = Field(default_factory=CF)

    # Exclusions
    suicideClause: CF = Field(default_factory=CF)
    otherExclusions: CF = Field(default_factory=CF)

    # Claims
    claimSettlementRatio: CF = Field(default_factory=CF)
    claimProcess: CF = Field(default_factory=CF)
    insurerTollFree: CF = Field(default_factory=CF)
    claimEmail: CF = Field(default_factory=CF)
