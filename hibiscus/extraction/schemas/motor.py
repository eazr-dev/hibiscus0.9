"""
Motor Insurance Extraction Schema — 97 fields.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CF(BaseModel):
    value: Any = None
    source_page: Optional[int] = None
    confidence: float = 0.0


class Hypothecation(BaseModel):
    isHypothecated: Optional[bool] = None
    financierName: Optional[str] = None
    loanAccountNumber: Optional[str] = None


class MotorExtraction(BaseModel):
    """Complete motor insurance extraction — 97 fields."""

    # Section 1: Policy Basics
    policyNumber: CF = Field(default_factory=CF)
    uin: CF = Field(default_factory=CF)
    certificateNumber: CF = Field(default_factory=CF)
    coverNoteNumber: CF = Field(default_factory=CF)
    productType: CF = Field(default_factory=CF)  # Comprehensive/Third Party Only/Standalone OD
    insurerName: CF = Field(default_factory=CF)
    policyPeriodStart: CF = Field(default_factory=CF)
    policyPeriodEnd: CF = Field(default_factory=CF)
    policyTerm: CF = Field(default_factory=CF)
    previousPolicyNumber: CF = Field(default_factory=CF)
    previousInsurer: CF = Field(default_factory=CF)
    insurerTollFree: CF = Field(default_factory=CF)
    claimEmail: CF = Field(default_factory=CF)
    claimApp: CF = Field(default_factory=CF)

    # Section 2: Vehicle Details
    registrationNumber: CF = Field(default_factory=CF)
    vehicleClass: CF = Field(default_factory=CF)
    vehicleCategory: CF = Field(default_factory=CF)
    vehicleMake: CF = Field(default_factory=CF)
    vehicleModel: CF = Field(default_factory=CF)
    vehicleVariant: CF = Field(default_factory=CF)
    manufacturingYear: CF = Field(default_factory=CF)
    registrationDate: CF = Field(default_factory=CF)
    engineNumber: CF = Field(default_factory=CF)
    chassisNumber: CF = Field(default_factory=CF)
    fuelType: CF = Field(default_factory=CF)
    cubicCapacity: CF = Field(default_factory=CF)
    seatingCapacity: CF = Field(default_factory=CF)
    vehicleColor: CF = Field(default_factory=CF)
    rtoLocation: CF = Field(default_factory=CF)
    hypothecation: CF = Field(default_factory=CF)

    # Section 3: Owner/Policyholder
    ownerName: CF = Field(default_factory=CF)
    ownerType: CF = Field(default_factory=CF)
    ownerAddress: CF = Field(default_factory=CF)
    ownerAddressCity: CF = Field(default_factory=CF)
    ownerAddressState: CF = Field(default_factory=CF)
    ownerAddressPincode: CF = Field(default_factory=CF)
    ownerContact: CF = Field(default_factory=CF)
    ownerEmail: CF = Field(default_factory=CF)
    ownerPan: CF = Field(default_factory=CF)

    # Section 4: Coverage Details
    idv: CF = Field(default_factory=CF)
    idvMinimum: CF = Field(default_factory=CF)
    idvMaximum: CF = Field(default_factory=CF)
    odPremium: CF = Field(default_factory=CF)
    tpPremium: CF = Field(default_factory=CF)
    compulsoryDeductible: CF = Field(default_factory=CF)
    voluntaryDeductible: CF = Field(default_factory=CF)
    geographicScope: CF = Field(default_factory=CF)
    paOwnerCover: CF = Field(default_factory=CF)
    paUnnamedPassengers: CF = Field(default_factory=CF)
    paUnnamedPassengersPerPerson: CF = Field(default_factory=CF)
    paPaidDriver: CF = Field(default_factory=CF)
    llPaidDriver: CF = Field(default_factory=CF)
    llEmployees: CF = Field(default_factory=CF)
    tppdCover: CF = Field(default_factory=CF)

    # Section 5: NCB
    ncbPercentage: CF = Field(default_factory=CF)
    ncbProtection: CF = Field(default_factory=CF)
    ncbDeclaration: CF = Field(default_factory=CF)
    claimFreeYears: CF = Field(default_factory=CF)

    # Section 6: Add-on Covers
    zeroDepreciation: CF = Field(default_factory=CF)
    engineProtection: CF = Field(default_factory=CF)
    returnToInvoice: CF = Field(default_factory=CF)
    roadsideAssistance: CF = Field(default_factory=CF)
    consumables: CF = Field(default_factory=CF)
    tyreCover: CF = Field(default_factory=CF)
    keyCover: CF = Field(default_factory=CF)
    ncbProtect: CF = Field(default_factory=CF)
    emiBreakerCover: CF = Field(default_factory=CF)
    passengerCover: CF = Field(default_factory=CF)
    passengerCoverAmount: CF = Field(default_factory=CF)
    personalBaggage: CF = Field(default_factory=CF)
    outstationEmergency: CF = Field(default_factory=CF)
    dailyAllowance: CF = Field(default_factory=CF)
    windshieldCover: CF = Field(default_factory=CF)
    electricVehicleCover: CF = Field(default_factory=CF)
    batteryProtect: CF = Field(default_factory=CF)
    legalLiabilityPaidDriver: CF = Field(default_factory=CF)
    legalLiabilityEmployees: CF = Field(default_factory=CF)
    paNamedPersons: CF = Field(default_factory=CF)

    # Section 7: Premium Breakdown
    basicOdPremium: CF = Field(default_factory=CF)
    ncbDiscount: CF = Field(default_factory=CF)
    voluntaryDeductibleDiscount: CF = Field(default_factory=CF)
    antiTheftDiscount: CF = Field(default_factory=CF)
    aaiMembershipDiscount: CF = Field(default_factory=CF)
    electricalAccessoriesPremium: CF = Field(default_factory=CF)
    nonElectricalAccessoriesPremium: CF = Field(default_factory=CF)
    cngLpgKitPremium: CF = Field(default_factory=CF)
    addOnPremium: CF = Field(default_factory=CF)
    loading: CF = Field(default_factory=CF)
    netOdPremium: CF = Field(default_factory=CF)
    basicTpPremium: CF = Field(default_factory=CF)
    paOwnerDriverPremium: CF = Field(default_factory=CF)
    paPassengersPremium: CF = Field(default_factory=CF)
    paPaidDriverPremium: CF = Field(default_factory=CF)
    llPaidDriverPremium: CF = Field(default_factory=CF)
    netTpPremium: CF = Field(default_factory=CF)
    grossPremium: CF = Field(default_factory=CF)
    gst: CF = Field(default_factory=CF)
    totalPremium: CF = Field(default_factory=CF)

    # Section 8: Exclusions
    electricalAccessoriesExclusion: CF = Field(default_factory=CF)
    nonElectricalAccessoriesExclusion: CF = Field(default_factory=CF)
    biofuelKitExclusion: CF = Field(default_factory=CF)
    otherExclusions: CF = Field(default_factory=CF)
