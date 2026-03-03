# Health Insurance - Flutter Integration Guide

**Category**: Health Insurance | **Version**: 1.0 | **Date**: February 2026

> This document is specific to **Health Insurance** policy responses. For generic Dart models (`PolicySection`, `Field`, `SectionItem`, etc.) and base widgets, refer to [FLUTTER_INTEGRATION_GUIDE.md](../FLUTTER_INTEGRATION_GUIDE.md).

---

## Table of Contents

1. [Response Overview](#1-response-overview)
2. [Top-Level Response Fields](#2-top-level-response-fields)
3. [Sections Reference (Dynamic Rendering)](#3-sections-reference)
4. [categorySpecificData (Typed Access)](#4-categoryspecificdata)
5. [Health-Specific Dart Models](#5-health-specific-dart-models)
6. [UI Rendering Guide - Section by Section](#6-ui-rendering-guide)
7. [Value Type Handling](#7-value-type-handling)
8. [Health-Specific Formatters](#8-health-specific-formatters)
9. [Complete Sample API Response](#9-complete-sample-api-response)

---

## 1. Response Overview

The health insurance API returns a **dynamic** response. Sections, fields, and their order can vary across different health policies (Acko, Star Health, HDFC ERGO, etc.). The Flutter app must render sections **dynamically** based on `sectionType` and fields based on `valueType`.

### Two Ways to Access Data

| Approach | Use For | Source |
|----------|---------|--------|
| **`sections[]`** | Dynamic UI rendering - iterate & render | `policyDetails.sections` |
| **`categorySpecificData`** | Typed access for business logic, scores, comparisons | `policyDetails.categorySpecificData` |

**Rule**: Use `sections[]` for rendering the Policy Details tab. Use `categorySpecificData` when you need to compute something (e.g., check if restoration is available, calculate effective SI).

---

## 2. Top-Level Response Fields

```
API Response
├── success: bool
├── userId: String
├── policyId: String              // Internal analysis ID (ANL_282_xxx)
├── policyNumber: String
├── message: String
└── policyDetails
    ├── policyNumber: String
    ├── uin: String
    ├── insuranceProvider: String
    ├── policyType: "health"
    ├── policyHolderName: String
    ├── insuredName: String
    ├── coverageAmount: number     // Sum Insured in paisa-free integer (e.g., 12000000 = ₹1.2Cr)
    ├── sumAssured: number
    ├── premium: number            // Total premium (e.g., 25459.42)
    ├── premiumFrequency: String   // "annual" | "half_yearly" | "quarterly" | "monthly"
    ├── startDate: String          // "YYYY-MM-DD"
    ├── endDate: String            // "YYYY-MM-DD"
    ├── status: String             // "active" | "expired" | "lapsed"
    ├── relationship: String
    ├── originalDocumentUrl: String // S3 URL to original policy PDF
    ├── sections: [...]            // Dynamic sections for UI
    ├── categorySpecificData: {...} // Typed health insurance data
    ├── dataValidation: {...}      // Validation warnings/errors
    └── redundantAddonAnalysis: {...} // Add-on overlap analysis
```

### Key Formatting Notes

| Field | Format | Flutter Display |
|-------|--------|----------------|
| `coverageAmount` | Raw number (12000000) | Format as `₹1.2 Cr` or `₹1,20,00,000` |
| `premium` | Decimal (25459.42) | Format as `₹25,459` |
| `startDate` / `endDate` | `YYYY-MM-DD` | Format as `01 Mar 2025` |
| `status` | lowercase string | Capitalize + color badge |

---

## 3. Sections Reference

### 3.1 Section Structure

Every section follows this structure:

```json
{
  "sectionId": "coverageDetails",
  "sectionTitle": "Coverage Details",
  "sectionType": "fields" | "list",
  "displayOrder": 3,
  "fields": [...],    // Present when sectionType = "fields"
  "items": [...]      // Present when sectionType = "list"
}
```

### 3.2 All Health Insurance Sections

Render sections **sorted by `displayOrder`**. Not all sections appear in every policy.

| displayOrder | sectionId | sectionTitle | sectionType | Always Present |
|-------------|-----------|-------------|-------------|----------------|
| 1 | `policyIdentification` | Policy Identification | fields | Yes |
| 2 | `insuredMembers` | Insured Members | **list** | Yes |
| 3 | `coverageDetails` | Coverage Details | fields | Yes |
| 4 | `waitingPeriods` | Waiting Periods | fields | Yes |
| 5 | `copayDetails` | Copay Details | fields | Yes |
| 6 | `subLimits` | Sub-Limits | fields | Most policies |
| 7 | `exclusions` | Exclusions | fields | Yes |
| 8 | `premiumBreakdown` | Premium Breakdown | fields | Yes |
| 9 | `noClaimBonus` | No Claim Bonus | fields | Most policies |
| 10 | `addOnPolicies` | Add-On Policies | fields | If add-ons exist |
| 11 | `declaredPed` | Declared Pre-existing Diseases | fields | Yes |
| 12 | `benefits` | Benefits & Features | fields | Yes |
| 13 | `accumulatedBenefits` | Accumulated Benefits | fields | Most policies |
| 14 | `membersCovered` | Members Covered | **list** | Yes |
| 15 | `policyHistory` | Policy History | fields | Yes |
| 16 | `networkInfo` | Network Hospital Information | fields | Yes |
| 17 | `claimInfo` | Claim Information | fields | Yes |

### 3.3 Field Structure

```json
{
  "fieldId": "coverageDetails_sumInsured",
  "label": "Sum Insured",
  "value": 12000000,
  "valueType": "number",
  "displayOrder": 0
}
```

### 3.4 List Item Structure (for `insuredMembers`, `membersCovered`)

```json
{
  "itemId": "insuredMembers_item_0",
  "fields": [
    { "fieldId": "...", "label": "Membername", "value": "KUNJAL RAJEEV VASANI", "valueType": "string", "displayOrder": 0 },
    { "fieldId": "...", "label": "Memberrelationship", "value": "Spouse", "valueType": "string", "displayOrder": 1 },
    { "fieldId": "...", "label": "Memberage", "value": 33, "valueType": "number", "displayOrder": 2 },
    { "fieldId": "...", "label": "Membergender", "value": "Female", "valueType": "string", "displayOrder": 3 }
  ]
}
```

---

## 4. categorySpecificData

This is the **typed** health insurance data. Use it for business logic, not for rendering.

```
categorySpecificData
├── policyIdentification
│   ├── policyNumber: String
│   ├── uin: String
│   ├── productName: String       // "ACKO Personal Health Policy - Platinum Plan"
│   ├── policyType: String        // "Family Floater" | "Individual" | "Super Top-up"
│   ├── insurerName: String
│   ├── insurerRegistrationNumber: String
│   ├── insurerAddress: String
│   ├── insurerTollFree: String
│   ├── tpaName: String?          // null if insurer has own network
│   ├── intermediaryName: String
│   ├── intermediaryCode: String
│   ├── intermediaryEmail: String
│   ├── policyIssueDate: String
│   ├── policyPeriod: String
│   ├── policyPeriodStart: String
│   └── policyPeriodEnd: String
│
├── insuredMembers: List
│   └── [{ memberName, memberRelationship, memberAge, memberGender }]
│
├── coverageDetails
│   ├── sumInsured: number
│   ├── coverType: String         // "Individual" | "Family Floater"
│   ├── roomRentLimit: String     // "No limit" | "₹X,XXX per day" | "1% of SI"
│   ├── roomRentCopay: String?
│   ├── icuLimit: String          // "No limit" | "₹X,XXX per day"
│   ├── icuDailyLimit: String?
│   ├── preHospitalization: String  // "60 days"
│   ├── postHospitalization: String // "120 days"
│   ├── dayCareProcedures: bool
│   ├── domiciliaryHospitalization: bool
│   ├── ambulanceCover: String    // "No limit" | "₹X,XXX"
│   ├── healthCheckup: String     // "Once per policy year"
│   ├── ayushTreatment: bool
│   ├── organDonor: bool
│   ├── restoration
│   │   ├── available: bool
│   │   └── type: String          // "Unlimited restore" | "100% restore" | "200% restore"
│   ├── restorationAmount: String
│   ├── modernTreatment: bool
│   ├── dailyCashAllowance: String?
│   ├── convalescenceBenefit: String?
│   ├── consumablesCoverage: bool
│   └── consumablesCoverageDetails: String?
│
├── waitingPeriods
│   ├── initialWaitingPeriod: String    // "No waiting period" | "30 days"
│   ├── preExistingDiseaseWaiting: String // "No waiting period" | "36 months" | "48 months"
│   ├── specificDiseaseWaiting: String    // "No waiting period" | "24 months"
│   ├── maternityWaiting: String?
│   ├── accidentCoveredFromDay1: bool
│   └── specificDiseasesList: List<String>
│
├── copayDetails
│   ├── generalCopay: String      // "0%" | "10%" | "20%"
│   ├── ageBasedCopay: List       // [{ age_bracket, copay_percentage }]
│   └── diseaseSpecificCopay: List
│
├── subLimits
│   ├── cataractLimit: String?
│   ├── jointReplacementLimit: String?
│   ├── internalProsthesisLimit: String?
│   ├── kidneyStoneLimit: String?
│   ├── gallStoneLimit: String?
│   ├── modernTreatmentLimit: String?
│   └── otherSubLimits: List
│
├── exclusions
│   ├── permanentExclusions: List<String>
│   ├── conditionalExclusions: List
│   └── pedSpecificExclusions: List
│
├── premiumBreakdown
│   ├── basePremium: number
│   ├── totalPremium: number
│   ├── premiumFrequency: String
│   ├── gracePeriod: String
│   └── addOns: List<{ name, premium }>  // via otherAddOns_* fields
│
├── noClaimBonus
│   ├── available: bool
│   └── maxNcbPercentage: String
│
├── addOnPolicies
│   ├── hasAddOn: bool
│   ├── addOnPoliciesList: List<AddOn>
│   ├── claimShield: bool
│   ├── ncbShield: bool
│   └── inflationShield: bool
│
├── declaredPed
│   ├── pedWaitingPeriodCompleted: bool
│   └── pedStatus: String
│
├── benefits
│   ├── ayushCovered: bool
│   ├── ayushLimit: String
│   ├── mentalHealthCovered: bool
│   ├── dayCareCovered: bool
│   └── dayCareCoverageType: String
│
├── accumulatedBenefits
│   └── totalEffectiveCoverage: number
│
├── policyHistory
│   ├── firstEnrollmentDate: String
│   ├── insuredSinceDate: String
│   └── portability: { available: bool }
│
├── networkInfo
│   ├── networkHospitalsCount: String  // "14,000+ Hospitals"
│   ├── ambulanceCover: String
│   ├── cashlessFacility: bool
│   └── networkType: String            // "Pan India"
│
└── claimInfo
    ├── claimSettlementRatio: String   // "92%"
    ├── claimProcess: String           // "Cashless & Reimbursement"
    ├── claimIntimation: String        // "Within 24 hours of admission"
    └── claimDocuments: List<String>
```

---

## 5. Health-Specific Dart Models

These models parse `categorySpecificData` for typed access. Use **alongside** the generic models from [FLUTTER_INTEGRATION_GUIDE.md](../FLUTTER_INTEGRATION_GUIDE.md).

### 5.1 HealthCategoryData (Root)

```dart
class HealthCategoryData {
  final HealthPolicyIdentification policyIdentification;
  final List<InsuredMember> insuredMembers;
  final HealthCoverageDetails coverageDetails;
  final HealthWaitingPeriods waitingPeriods;
  final HealthCopayDetails copayDetails;
  final HealthSubLimits subLimits;
  final HealthExclusions exclusions;
  final HealthPremiumBreakdown premiumBreakdown;
  final HealthNoClaimBonus noClaimBonus;
  final HealthAddOnPolicies addOnPolicies;
  final HealthDeclaredPed declaredPed;
  final HealthBenefits benefits;
  final HealthAccumulatedBenefits accumulatedBenefits;
  final HealthPolicyHistory policyHistory;
  final HealthNetworkInfo networkInfo;
  final HealthClaimInfo claimInfo;

  HealthCategoryData({
    required this.policyIdentification,
    required this.insuredMembers,
    required this.coverageDetails,
    required this.waitingPeriods,
    required this.copayDetails,
    required this.subLimits,
    required this.exclusions,
    required this.premiumBreakdown,
    required this.noClaimBonus,
    required this.addOnPolicies,
    required this.declaredPed,
    required this.benefits,
    required this.accumulatedBenefits,
    required this.policyHistory,
    required this.networkInfo,
    required this.claimInfo,
  });

  factory HealthCategoryData.fromJson(Map<String, dynamic> json) {
    final membersList = json['insuredMembers'] as List? ?? [];

    return HealthCategoryData(
      policyIdentification: HealthPolicyIdentification.fromJson(
        json['policyIdentification'] ?? {},
      ),
      insuredMembers: membersList
          .map((m) => InsuredMember.fromJson(m as Map<String, dynamic>))
          .toList(),
      coverageDetails: HealthCoverageDetails.fromJson(
        json['coverageDetails'] ?? {},
      ),
      waitingPeriods: HealthWaitingPeriods.fromJson(
        json['waitingPeriods'] ?? {},
      ),
      copayDetails: HealthCopayDetails.fromJson(
        json['copayDetails'] ?? {},
      ),
      subLimits: HealthSubLimits.fromJson(
        json['subLimits'] ?? {},
      ),
      exclusions: HealthExclusions.fromJson(
        json['exclusions'] ?? {},
      ),
      premiumBreakdown: HealthPremiumBreakdown.fromJson(
        json['premiumBreakdown'] ?? {},
      ),
      noClaimBonus: HealthNoClaimBonus.fromJson(
        json['noClaimBonus'] ?? {},
      ),
      addOnPolicies: HealthAddOnPolicies.fromJson(
        json['addOnPolicies'] ?? {},
      ),
      declaredPed: HealthDeclaredPed.fromJson(
        json['declaredPed'] ?? {},
      ),
      benefits: HealthBenefits.fromJson(
        json['benefits'] ?? {},
      ),
      accumulatedBenefits: HealthAccumulatedBenefits.fromJson(
        json['accumulatedBenefits'] ?? {},
      ),
      policyHistory: HealthPolicyHistory.fromJson(
        json['policyHistory'] ?? {},
      ),
      networkInfo: HealthNetworkInfo.fromJson(
        json['networkInfo'] ?? {},
      ),
      claimInfo: HealthClaimInfo.fromJson(
        json['claimInfo'] ?? {},
      ),
    );
  }
}
```

### 5.2 Policy Identification

```dart
class HealthPolicyIdentification {
  final String policyNumber;
  final String uin;
  final String productName;
  final String policyType;
  final String insurerName;
  final String? insurerRegistrationNumber;
  final String? insurerAddress;
  final String? insurerTollFree;
  final String? tpaName;
  final String? intermediaryName;
  final String? intermediaryCode;
  final String? intermediaryEmail;
  final String? policyIssueDate;
  final String? policyPeriod;
  final String policyPeriodStart;
  final String policyPeriodEnd;

  HealthPolicyIdentification({
    required this.policyNumber,
    required this.uin,
    required this.productName,
    required this.policyType,
    required this.insurerName,
    this.insurerRegistrationNumber,
    this.insurerAddress,
    this.insurerTollFree,
    this.tpaName,
    this.intermediaryName,
    this.intermediaryCode,
    this.intermediaryEmail,
    this.policyIssueDate,
    this.policyPeriod,
    required this.policyPeriodStart,
    required this.policyPeriodEnd,
  });

  factory HealthPolicyIdentification.fromJson(Map<String, dynamic> json) {
    return HealthPolicyIdentification(
      policyNumber: json['policyNumber']?.toString() ?? '',
      uin: json['uin']?.toString() ?? '',
      productName: json['productName']?.toString() ?? '',
      policyType: json['policyType']?.toString() ?? '',
      insurerName: json['insurerName']?.toString() ?? '',
      insurerRegistrationNumber: json['insurerRegistrationNumber']?.toString(),
      insurerAddress: json['insurerAddress']?.toString(),
      insurerTollFree: json['insurerTollFree']?.toString(),
      tpaName: json['tpaName']?.toString(),
      intermediaryName: json['intermediaryName']?.toString(),
      intermediaryCode: json['intermediaryCode']?.toString(),
      intermediaryEmail: json['intermediaryEmail']?.toString(),
      policyIssueDate: json['policyIssueDate']?.toString(),
      policyPeriod: json['policyPeriod']?.toString(),
      policyPeriodStart: json['policyPeriodStart']?.toString() ?? '',
      policyPeriodEnd: json['policyPeriodEnd']?.toString() ?? '',
    );
  }
}
```

### 5.3 Insured Member

```dart
class InsuredMember {
  final String memberName;
  final String memberRelationship;
  final int memberAge;
  final String memberGender;

  InsuredMember({
    required this.memberName,
    required this.memberRelationship,
    required this.memberAge,
    required this.memberGender,
  });

  factory InsuredMember.fromJson(Map<String, dynamic> json) {
    return InsuredMember(
      memberName: json['memberName']?.toString() ?? '',
      memberRelationship: json['memberRelationship']?.toString() ?? '',
      memberAge: (json['memberAge'] as num?)?.toInt() ?? 0,
      memberGender: json['memberGender']?.toString() ?? '',
    );
  }

  /// Helper: Get icon based on relationship
  String get relationshipIcon {
    switch (memberRelationship.toLowerCase()) {
      case 'self':
        return 'person';
      case 'spouse':
        return 'favorite';
      case 'son':
      case 'daughter':
        return 'child_care';
      case 'father':
      case 'mother':
        return 'elderly';
      default:
        return 'person';
    }
  }
}
```

### 5.4 Coverage Details

```dart
class HealthCoverageDetails {
  final double sumInsured;
  final String coverType;
  final String roomRentLimit;
  final String? roomRentCopay;
  final String icuLimit;
  final String? icuDailyLimit;
  final String preHospitalization;
  final String postHospitalization;
  final bool dayCareProcedures;
  final bool domiciliaryHospitalization;
  final String ambulanceCover;
  final String? healthCheckup;
  final bool ayushTreatment;
  final bool organDonor;
  final HealthRestoration restoration;
  final String? restorationAmount;
  final bool modernTreatment;
  final String? dailyCashAllowance;
  final String? convalescenceBenefit;
  final bool consumablesCoverage;
  final String? consumablesCoverageDetails;

  HealthCoverageDetails({
    required this.sumInsured,
    required this.coverType,
    required this.roomRentLimit,
    this.roomRentCopay,
    required this.icuLimit,
    this.icuDailyLimit,
    required this.preHospitalization,
    required this.postHospitalization,
    required this.dayCareProcedures,
    required this.domiciliaryHospitalization,
    required this.ambulanceCover,
    this.healthCheckup,
    required this.ayushTreatment,
    required this.organDonor,
    required this.restoration,
    this.restorationAmount,
    required this.modernTreatment,
    this.dailyCashAllowance,
    this.convalescenceBenefit,
    required this.consumablesCoverage,
    this.consumablesCoverageDetails,
  });

  factory HealthCoverageDetails.fromJson(Map<String, dynamic> json) {
    return HealthCoverageDetails(
      sumInsured: (json['sumInsured'] as num?)?.toDouble() ?? 0.0,
      coverType: json['coverType']?.toString() ?? '',
      roomRentLimit: json['roomRentLimit']?.toString() ?? '',
      roomRentCopay: json['roomRentCopay']?.toString(),
      icuLimit: json['icuLimit']?.toString() ?? '',
      icuDailyLimit: json['icuDailyLimit']?.toString(),
      preHospitalization: json['preHospitalization']?.toString() ?? '',
      postHospitalization: json['postHospitalization']?.toString() ?? '',
      dayCareProcedures: json['dayCareProcedures'] == true,
      domiciliaryHospitalization: json['domiciliaryHospitalization'] == true,
      ambulanceCover: json['ambulanceCover']?.toString() ?? '',
      healthCheckup: json['healthCheckup']?.toString(),
      ayushTreatment: json['ayushTreatment'] == true,
      organDonor: json['organDonor'] == true,
      restoration: HealthRestoration.fromJson(
        json['restoration'] as Map<String, dynamic>? ?? {},
      ),
      restorationAmount: json['restorationAmount']?.toString(),
      modernTreatment: json['modernTreatment'] == true,
      dailyCashAllowance: json['dailyCashAllowance']?.toString(),
      convalescenceBenefit: json['convalescenceBenefit']?.toString(),
      consumablesCoverage: json['consumablesCoverage'] == true,
      consumablesCoverageDetails: json['consumablesCoverageDetails']?.toString(),
    );
  }

  /// Helper: Check if room rent has no limit
  bool get hasNoRoomRentLimit =>
      roomRentLimit.toLowerCase().contains('no limit');

  /// Helper: Check if ICU has no limit
  bool get hasNoIcuLimit =>
      icuLimit.toLowerCase().contains('no limit');
}

class HealthRestoration {
  final bool available;
  final String type;

  HealthRestoration({required this.available, required this.type});

  factory HealthRestoration.fromJson(Map<String, dynamic> json) {
    return HealthRestoration(
      available: json['available'] == true,
      type: json['type']?.toString() ?? '',
    );
  }

  bool get isUnlimited => type.toLowerCase().contains('unlimited');
}
```

### 5.5 Waiting Periods

```dart
class HealthWaitingPeriods {
  final String initialWaitingPeriod;
  final String preExistingDiseaseWaiting;
  final String specificDiseaseWaiting;
  final String? maternityWaiting;
  final bool accidentCoveredFromDay1;
  final List<String> specificDiseasesList;

  HealthWaitingPeriods({
    required this.initialWaitingPeriod,
    required this.preExistingDiseaseWaiting,
    required this.specificDiseaseWaiting,
    this.maternityWaiting,
    required this.accidentCoveredFromDay1,
    required this.specificDiseasesList,
  });

  factory HealthWaitingPeriods.fromJson(Map<String, dynamic> json) {
    final diseasesList = json['specificDiseasesList'] as List? ?? [];

    return HealthWaitingPeriods(
      initialWaitingPeriod: json['initialWaitingPeriod']?.toString() ?? '',
      preExistingDiseaseWaiting: json['preExistingDiseaseWaiting']?.toString() ?? '',
      specificDiseaseWaiting: json['specificDiseaseWaiting']?.toString() ?? '',
      maternityWaiting: json['maternityWaiting']?.toString(),
      accidentCoveredFromDay1: json['accidentCoveredFromDay1'] == true,
      specificDiseasesList: diseasesList.map((d) => d.toString()).toList(),
    );
  }

  /// Helper: Check if all waiting periods are waived
  bool get allWaitingPeriodsWaived =>
      initialWaitingPeriod.toLowerCase().contains('no waiting') &&
      preExistingDiseaseWaiting.toLowerCase().contains('no waiting') &&
      specificDiseaseWaiting.toLowerCase().contains('no waiting');
}
```

### 5.6 Copay Details

```dart
class HealthCopayDetails {
  final String generalCopay;
  final List<Map<String, dynamic>> ageBasedCopay;
  final List<Map<String, dynamic>> diseaseSpecificCopay;

  HealthCopayDetails({
    required this.generalCopay,
    required this.ageBasedCopay,
    required this.diseaseSpecificCopay,
  });

  factory HealthCopayDetails.fromJson(Map<String, dynamic> json) {
    return HealthCopayDetails(
      generalCopay: json['generalCopay']?.toString() ?? '0%',
      ageBasedCopay: (json['ageBasedCopay'] as List? ?? [])
          .map((e) => Map<String, dynamic>.from(e))
          .toList(),
      diseaseSpecificCopay: (json['diseaseSpecificCopay'] as List? ?? [])
          .map((e) => Map<String, dynamic>.from(e))
          .toList(),
    );
  }

  /// Helper: Check if there is zero copay
  bool get isZeroCopay => generalCopay == '0%' || generalCopay == '0';
}
```

### 5.7 Sub-Limits

```dart
class HealthSubLimits {
  final String? cataractLimit;
  final String? jointReplacementLimit;
  final String? internalProsthesisLimit;
  final String? kidneyStoneLimit;
  final String? gallStoneLimit;
  final String? modernTreatmentLimit;
  final List<Map<String, dynamic>> otherSubLimits;

  HealthSubLimits({
    this.cataractLimit,
    this.jointReplacementLimit,
    this.internalProsthesisLimit,
    this.kidneyStoneLimit,
    this.gallStoneLimit,
    this.modernTreatmentLimit,
    required this.otherSubLimits,
  });

  factory HealthSubLimits.fromJson(Map<String, dynamic> json) {
    return HealthSubLimits(
      cataractLimit: json['cataractLimit']?.toString(),
      jointReplacementLimit: json['jointReplacementLimit']?.toString(),
      internalProsthesisLimit: json['internalProsthesisLimit']?.toString(),
      kidneyStoneLimit: json['kidneyStoneLimit']?.toString(),
      gallStoneLimit: json['gallStoneLimit']?.toString(),
      modernTreatmentLimit: json['modernTreatmentLimit']?.toString(),
      otherSubLimits: (json['otherSubLimits'] as List? ?? [])
          .map((e) => Map<String, dynamic>.from(e))
          .toList(),
    );
  }

  /// Helper: Check if sub-limits exist
  bool get hasSubLimits =>
      cataractLimit != null ||
      jointReplacementLimit != null ||
      internalProsthesisLimit != null ||
      kidneyStoneLimit != null ||
      gallStoneLimit != null;
}
```

### 5.8 Exclusions

```dart
class HealthExclusions {
  final List<String> permanentExclusions;
  final List<String> conditionalExclusions;
  final List<String> pedSpecificExclusions;

  HealthExclusions({
    required this.permanentExclusions,
    required this.conditionalExclusions,
    required this.pedSpecificExclusions,
  });

  factory HealthExclusions.fromJson(Map<String, dynamic> json) {
    return HealthExclusions(
      permanentExclusions: (json['permanentExclusions'] as List? ?? [])
          .map((e) => e.toString())
          .toList(),
      conditionalExclusions: (json['conditionalExclusions'] as List? ?? [])
          .map((e) => e.toString())
          .toList(),
      pedSpecificExclusions: (json['pedSpecificExclusions'] as List? ?? [])
          .map((e) => e.toString())
          .toList(),
    );
  }
}
```

### 5.9 Premium Breakdown

```dart
class HealthPremiumBreakdown {
  final double basePremium;
  final double totalPremium;
  final String premiumFrequency;
  final String? gracePeriod;

  HealthPremiumBreakdown({
    required this.basePremium,
    required this.totalPremium,
    required this.premiumFrequency,
    this.gracePeriod,
  });

  factory HealthPremiumBreakdown.fromJson(Map<String, dynamic> json) {
    return HealthPremiumBreakdown(
      basePremium: (json['basePremium'] as num?)?.toDouble() ?? 0.0,
      totalPremium: (json['totalPremium'] as num?)?.toDouble() ?? 0.0,
      premiumFrequency: json['premiumFrequency']?.toString() ?? 'Annual',
      gracePeriod: json['gracePeriod']?.toString(),
    );
  }

  /// Estimated GST (18%)
  double get estimatedGst => totalPremium - basePremium;
}
```

### 5.10 No Claim Bonus

```dart
class HealthNoClaimBonus {
  final bool available;
  final String? maxNcbPercentage;

  HealthNoClaimBonus({
    required this.available,
    this.maxNcbPercentage,
  });

  factory HealthNoClaimBonus.fromJson(Map<String, dynamic> json) {
    final availableValue = json['available'];
    return HealthNoClaimBonus(
      available: availableValue == true ||
          availableValue == 'Yes' ||
          availableValue == 'yes',
      maxNcbPercentage: json['maxNcbPercentage']?.toString(),
    );
  }
}
```

### 5.11 Add-On Policies

```dart
class HealthAddOnPolicies {
  final bool hasAddOn;
  final List<HealthAddOn> addOnPoliciesList;
  final bool claimShield;
  final bool ncbShield;
  final bool inflationShield;

  HealthAddOnPolicies({
    required this.hasAddOn,
    required this.addOnPoliciesList,
    required this.claimShield,
    required this.ncbShield,
    required this.inflationShield,
  });

  factory HealthAddOnPolicies.fromJson(Map<String, dynamic> json) {
    final addonList = json['addOnPoliciesList'] as List? ?? [];

    return HealthAddOnPolicies(
      hasAddOn: json['hasAddOn'] == true || json['hasAddOn'] == 'Yes',
      addOnPoliciesList: addonList
          .map((a) => HealthAddOn.fromJson(a as Map<String, dynamic>))
          .toList(),
      claimShield: json['claimShield'] == true || json['claimShield'] == 'Yes',
      ncbShield: json['ncbShield'] == true || json['ncbShield'] == 'Yes',
      inflationShield: json['inflationShield'] == true || json['inflationShield'] == 'Yes',
    );
  }
}

class HealthAddOn {
  final String addOnName;
  final String? uin;
  final double? sumInsured;
  final String? premium;
  final List<String>? benefits;
  final List<String>? coverageCountries;

  HealthAddOn({
    required this.addOnName,
    this.uin,
    this.sumInsured,
    this.premium,
    this.benefits,
    this.coverageCountries,
  });

  factory HealthAddOn.fromJson(Map<String, dynamic> json) {
    return HealthAddOn(
      addOnName: json['addOnName']?.toString() ?? '',
      uin: json['uin']?.toString(),
      sumInsured: (json['sumInsured'] as num?)?.toDouble(),
      premium: json['premium']?.toString(),
      benefits: (json['benefits'] as List?)?.map((b) => b.toString()).toList(),
      coverageCountries: (json['coverageCountries'] as List?)
          ?.map((c) => c.toString())
          .toList(),
    );
  }
}
```

### 5.12 Declared PED

```dart
class HealthDeclaredPed {
  final bool pedWaitingPeriodCompleted;
  final String pedStatus;

  HealthDeclaredPed({
    required this.pedWaitingPeriodCompleted,
    required this.pedStatus,
  });

  factory HealthDeclaredPed.fromJson(Map<String, dynamic> json) {
    final completed = json['pedWaitingPeriodCompleted'];
    return HealthDeclaredPed(
      pedWaitingPeriodCompleted:
          completed == true || completed == 'Yes' || completed == 'yes',
      pedStatus: json['pedStatus']?.toString() ?? '',
    );
  }
}
```

### 5.13 Benefits

```dart
class HealthBenefits {
  final bool ayushCovered;
  final String? ayushLimit;
  final bool mentalHealthCovered;
  final bool dayCareCovered;
  final String? dayCareCoverageType;

  HealthBenefits({
    required this.ayushCovered,
    this.ayushLimit,
    required this.mentalHealthCovered,
    required this.dayCareCovered,
    this.dayCareCoverageType,
  });

  factory HealthBenefits.fromJson(Map<String, dynamic> json) {
    return HealthBenefits(
      ayushCovered: json['ayushCovered'] == true || json['ayushCovered'] == 'Yes',
      ayushLimit: json['ayushLimit']?.toString(),
      mentalHealthCovered:
          json['mentalHealthCovered'] == true || json['mentalHealthCovered'] == 'Yes',
      dayCareCovered: json['dayCareCovered'] == true || json['dayCareCovered'] == 'Yes',
      dayCareCoverageType: json['dayCareCoverageType']?.toString(),
    );
  }
}
```

### 5.14 Accumulated Benefits, Policy History, Network Info, Claim Info

```dart
class HealthAccumulatedBenefits {
  final double totalEffectiveCoverage;

  HealthAccumulatedBenefits({required this.totalEffectiveCoverage});

  factory HealthAccumulatedBenefits.fromJson(Map<String, dynamic> json) {
    return HealthAccumulatedBenefits(
      totalEffectiveCoverage:
          (json['totalEffectiveCoverage'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class HealthPolicyHistory {
  final String? firstEnrollmentDate;
  final String? insuredSinceDate;
  final bool portabilityAvailable;

  HealthPolicyHistory({
    this.firstEnrollmentDate,
    this.insuredSinceDate,
    required this.portabilityAvailable,
  });

  factory HealthPolicyHistory.fromJson(Map<String, dynamic> json) {
    final portability = json['portability'] as Map<String, dynamic>? ?? {};
    return HealthPolicyHistory(
      firstEnrollmentDate: json['firstEnrollmentDate']?.toString(),
      insuredSinceDate: json['insuredSinceDate']?.toString(),
      portabilityAvailable:
          portability['available'] == true || portability['available'] == 'Yes',
    );
  }

  /// Helper: Years of continuous coverage
  int get yearsOfCoverage {
    if (firstEnrollmentDate == null) return 0;
    try {
      final start = DateTime.parse(firstEnrollmentDate!);
      return DateTime.now().difference(start).inDays ~/ 365;
    } catch (_) {
      return 0;
    }
  }
}

class HealthNetworkInfo {
  final String networkHospitalsCount;
  final String ambulanceCover;
  final bool cashlessFacility;
  final String networkType;

  HealthNetworkInfo({
    required this.networkHospitalsCount,
    required this.ambulanceCover,
    required this.cashlessFacility,
    required this.networkType,
  });

  factory HealthNetworkInfo.fromJson(Map<String, dynamic> json) {
    return HealthNetworkInfo(
      networkHospitalsCount: json['networkHospitalsCount']?.toString() ?? '',
      ambulanceCover: json['ambulanceCover']?.toString() ?? '',
      cashlessFacility:
          json['cashlessFacility'] == true || json['cashlessFacility'] == 'Yes',
      networkType: json['networkType']?.toString() ?? '',
    );
  }
}

class HealthClaimInfo {
  final String? claimSettlementRatio;
  final String? claimProcess;
  final String? claimIntimation;
  final List<String> claimDocuments;

  HealthClaimInfo({
    this.claimSettlementRatio,
    this.claimProcess,
    this.claimIntimation,
    required this.claimDocuments,
  });

  factory HealthClaimInfo.fromJson(Map<String, dynamic> json) {
    return HealthClaimInfo(
      claimSettlementRatio: json['claimSettlementRatio']?.toString(),
      claimProcess: json['claimProcess']?.toString(),
      claimIntimation: json['claimIntimation']?.toString(),
      claimDocuments: (json['claimDocuments'] as List? ?? [])
          .map((d) => d.toString())
          .toList(),
    );
  }
}
```

---

## 6. UI Rendering Guide

### 6.1 Dynamic Section Rendering (Primary Approach)

The `sections[]` array is designed for **direct UI rendering**. Iterate sections sorted by `displayOrder` and render based on `sectionType`.

```dart
Widget buildHealthPolicyDetails(List<PolicySection> sections) {
  // Sort by displayOrder
  final sorted = List<PolicySection>.from(sections)
    ..sort((a, b) => a.displayOrder.compareTo(b.displayOrder));

  return ListView.builder(
    itemCount: sorted.length,
    itemBuilder: (context, index) {
      final section = sorted[index];
      switch (section.sectionType) {
        case 'list':
          return _buildListSection(section);
        case 'fields':
        default:
          return _buildFieldsSection(section);
      }
    },
  );
}
```

### 6.2 Section-Specific UI Patterns

#### Policy Identification - Header Card

```dart
/// Render as a gradient header card with key info
/// Fields: policyNumber, productName, insurerName, policyPeriod
Widget buildPolicyIdentificationHeader(PolicySection section) {
  final fields = {for (var f in section.fields!) f.fieldId: f};

  return Container(
    padding: EdgeInsets.all(20),
    decoration: BoxDecoration(
      gradient: LinearGradient(
        colors: [Color(0xFF1E3A5F), Color(0xFF2D5F8B)],
      ),
      borderRadius: BorderRadius.circular(16),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Insurer name
        Text(
          fields['policyIdentification_insurerName']?.value?.toString() ?? '',
          style: TextStyle(color: Colors.white70, fontSize: 12),
        ),
        SizedBox(height: 4),
        // Product name
        Text(
          fields['policyIdentification_productName']?.value?.toString() ?? '',
          style: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 12),
        // Policy number with copy
        Row(
          children: [
            Text(
              'Policy: ${fields['policyIdentification_policyNumber']?.value ?? ''}',
              style: TextStyle(color: Colors.white60, fontSize: 13),
            ),
            SizedBox(width: 8),
            // Copy icon button
            GestureDetector(
              onTap: () => Clipboard.setData(ClipboardData(
                text: fields['policyIdentification_policyNumber']?.value?.toString() ?? '',
              )),
              child: Icon(Icons.copy, size: 14, color: Colors.white60),
            ),
          ],
        ),
        SizedBox(height: 8),
        // Policy period
        Text(
          fields['policyIdentification_policyPeriod']?.value?.toString() ?? '',
          style: TextStyle(color: Colors.white60, fontSize: 12),
        ),
      ],
    ),
  );
}
```

#### Insured Members - Horizontal Member Cards

```dart
/// sectionType = "list" — render as horizontal scrollable member cards
Widget buildInsuredMembersCards(PolicySection section) {
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Padding(
        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Text(
          section.sectionTitle,
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
      ),
      SizedBox(
        height: 120,
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          padding: EdgeInsets.symmetric(horizontal: 12),
          itemCount: section.items?.length ?? 0,
          itemBuilder: (context, index) {
            final item = section.items![index];
            final fields = {for (var f in item.fields!) f.label.toLowerCase(): f};

            final name = fields['membername']?.value?.toString() ?? '';
            final relation = fields['memberrelationship']?.value?.toString() ?? '';
            final age = fields['memberage']?.value?.toString() ?? '';
            final gender = fields['membergender']?.value?.toString() ?? '';

            return Container(
              width: 140,
              margin: EdgeInsets.symmetric(horizontal: 4),
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.shade100),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircleAvatar(
                    radius: 20,
                    backgroundColor: Colors.blue.shade100,
                    child: Text(
                      name.isNotEmpty ? name[0] : '?',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.blue.shade700,
                      ),
                    ),
                  ),
                  SizedBox(height: 8),
                  Text(
                    _formatName(name),
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                    textAlign: TextAlign.center,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    '$relation | $age yrs',
                    style: TextStyle(fontSize: 10, color: Colors.grey[600]),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    ],
  );
}

String _formatName(String name) {
  return name.split(' ').map((w) =>
    w.isNotEmpty ? '${w[0]}${w.substring(1).toLowerCase()}' : ''
  ).join(' ');
}
```

#### Coverage Details - Feature Grid

```dart
/// Render boolean fields as a grid of covered/not-covered chips
/// Render string/number fields as label-value rows
Widget buildCoverageDetailsSection(PolicySection section) {
  final booleanFields = section.fields!
      .where((f) => f.valueType == 'boolean')
      .toList();
  final otherFields = section.fields!
      .where((f) => f.valueType != 'boolean')
      .toList();

  return Card(
    margin: EdgeInsets.all(12),
    child: Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(section.sectionTitle,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          SizedBox(height: 12),
          // Key metrics as rows
          ...otherFields.map((f) => _buildFieldRow(f)),
          SizedBox(height: 12),
          // Boolean fields as chips grid
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: booleanFields.map((f) {
              final isYes = f.value == true ||
                  f.value == 'Yes' ||
                  f.value == 'yes';
              return Chip(
                avatar: Icon(
                  isYes ? Icons.check_circle : Icons.cancel,
                  size: 16,
                  color: isYes ? Colors.green : Colors.grey,
                ),
                label: Text(f.label, style: TextStyle(fontSize: 12)),
                backgroundColor: isYes ? Colors.green.shade50 : Colors.grey.shade100,
              );
            }).toList(),
          ),
        ],
      ),
    ),
  );
}
```

#### Waiting Periods - Status Cards

```dart
/// Highlight waiting period status with colored badges
Widget buildWaitingPeriodsSection(PolicySection section) {
  return Card(
    margin: EdgeInsets.all(12),
    child: Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(section.sectionTitle,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          SizedBox(height: 12),
          ...section.fields!.map((f) {
            if (f.valueType == 'array' && f.value is List) {
              // Render disease list
              return _buildDiseaseList(f);
            }
            // Render waiting period with status badge
            return _buildWaitingPeriodRow(f);
          }),
        ],
      ),
    ),
  );
}

Widget _buildWaitingPeriodRow(Field field) {
  final value = field.value?.toString() ?? '';
  final isNoWaiting = value.toLowerCase().contains('no waiting');
  final isCompleted = value.toLowerCase().contains('completed');

  Color badgeColor;
  String badgeText;
  if (isNoWaiting || isCompleted) {
    badgeColor = Colors.green;
    badgeText = isNoWaiting ? 'Waived' : 'Completed';
  } else {
    badgeColor = Colors.orange;
    badgeText = 'Active';
  }

  return Padding(
    padding: EdgeInsets.symmetric(vertical: 6),
    child: Row(
      children: [
        Expanded(
          flex: 3,
          child: Text(field.label, style: TextStyle(fontSize: 13)),
        ),
        Container(
          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(
            color: badgeColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            badgeText,
            style: TextStyle(
              color: badgeColor,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        SizedBox(width: 8),
        Expanded(
          flex: 2,
          child: Text(
            value,
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
            textAlign: TextAlign.right,
          ),
        ),
      ],
    ),
  );
}
```

#### Sub-Limits - Comparison Table

```dart
/// Render sub-limits as a table with currency values
Widget buildSubLimitsSection(PolicySection section) {
  return Card(
    margin: EdgeInsets.all(12),
    child: Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(section.sectionTitle,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          SizedBox(height: 12),
          Table(
            columnWidths: {
              0: FlexColumnWidth(2),
              1: FlexColumnWidth(3),
            },
            children: section.fields!.map((f) {
              return TableRow(
                children: [
                  Padding(
                    padding: EdgeInsets.symmetric(vertical: 8),
                    child: Text(f.label, style: TextStyle(fontSize: 13)),
                  ),
                  Padding(
                    padding: EdgeInsets.symmetric(vertical: 8),
                    child: Text(
                      f.value?.toString() ?? '-',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: Colors.deepOrange,
                      ),
                    ),
                  ),
                ],
              );
            }).toList(),
          ),
        ],
      ),
    ),
  );
}
```

#### Exclusions - Expandable List

```dart
/// Render exclusions as an expandable/collapsible list (collapsed by default)
Widget buildExclusionsSection(PolicySection section) {
  return Card(
    margin: EdgeInsets.all(12),
    child: ExpansionTile(
      title: Text(
        section.sectionTitle,
        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
      ),
      subtitle: Text(
        'Tap to view',
        style: TextStyle(fontSize: 12, color: Colors.grey),
      ),
      initiallyExpanded: false,
      children: section.fields!.map((f) {
        if (f.value is List) {
          return Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(f.label,
                    style: TextStyle(
                        fontSize: 13, fontWeight: FontWeight.w600)),
                SizedBox(height: 4),
                ...(f.value as List).map((item) => Padding(
                      padding: EdgeInsets.only(left: 8, bottom: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('• ', style: TextStyle(color: Colors.grey)),
                          Expanded(
                            child: Text(item.toString(),
                                style: TextStyle(fontSize: 12)),
                          ),
                        ],
                      ),
                    )),
                SizedBox(height: 8),
              ],
            ),
          );
        }
        return SizedBox.shrink();
      }).toList(),
    ),
  );
}
```

#### Premium Breakdown - Stacked Bar Card

```dart
/// Render premium as a visual breakdown
Widget buildPremiumBreakdownSection(PolicySection section) {
  final fields = {for (var f in section.fields!) f.fieldId: f};

  final basePremium = _toDouble(fields['premiumBreakdown_basePremium']?.value);
  final totalPremium = _toDouble(fields['premiumBreakdown_totalPremium']?.value);
  final gst = totalPremium - basePremium;

  // Extract add-on premiums (fields starting with "otherAddOns_")
  final addOns = section.fields!
      .where((f) => f.fieldId.startsWith('otherAddOns_'))
      .toList();

  return Card(
    margin: EdgeInsets.all(12),
    child: Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(section.sectionTitle,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          SizedBox(height: 16),
          // Total premium highlight
          Container(
            padding: EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.green.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Total Premium',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                Text(
                  '₹${totalPremium.toStringAsFixed(0)}',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.green.shade700,
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: 12),
          // Breakdown
          _premiumRow('Base Premium', basePremium),
          _premiumRow('GST (18%)', gst),
          if (addOns.isNotEmpty) ...[
            SizedBox(height: 8),
            Text('Add-On Premiums',
                style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
            ...addOns.map((f) => _premiumRow(f.label, _toDouble(f.value))),
          ],
          // Grace period
          if (fields['premiumBreakdown_gracePeriod'] != null) ...[
            Divider(),
            _fieldRow('Grace Period',
                fields['premiumBreakdown_gracePeriod']!.value.toString()),
          ],
        ],
      ),
    ),
  );
}

Widget _premiumRow(String label, double amount) {
  return Padding(
    padding: EdgeInsets.symmetric(vertical: 4),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: TextStyle(fontSize: 13, color: Colors.grey[700])),
        Text('₹${amount.toStringAsFixed(0)}',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
      ],
    ),
  );
}

double _toDouble(dynamic value) {
  if (value is num) return value.toDouble();
  if (value is String) return double.tryParse(value) ?? 0.0;
  return 0.0;
}
```

#### Add-On Policies - Swipeable Cards

```dart
/// Render add-ons from the addOnPolicies section
/// The addOnPoliciesList field contains a List of add-on objects
Widget buildAddOnPoliciesSection(PolicySection section) {
  final addOnListField = section.fields?.firstWhere(
    (f) => f.fieldId == 'addOnPolicies_addOnPoliciesList',
    orElse: () => Field(fieldId: '', label: '', value: null, valueType: 'string', displayOrder: 0),
  );

  if (addOnListField == null || addOnListField.value is! List) {
    return SizedBox.shrink();
  }

  final addOns = (addOnListField.value as List)
      .map((a) => a as Map<String, dynamic>)
      .toList();

  return Card(
    margin: EdgeInsets.all(12),
    child: Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(section.sectionTitle,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          SizedBox(height: 12),
          ...addOns.map((addon) => Container(
                margin: EdgeInsets.only(bottom: 8),
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.purple.shade100),
                  borderRadius: BorderRadius.circular(8),
                  color: Colors.purple.shade50,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          addon['addOnName'] ?? '',
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 14,
                          ),
                        ),
                        Text(
                          addon['premium']?.toString() ?? '',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Colors.purple.shade700,
                          ),
                        ),
                      ],
                    ),
                    if (addon['benefits'] is List) ...[
                      SizedBox(height: 4),
                      Wrap(
                        spacing: 4,
                        children: (addon['benefits'] as List)
                            .map((b) => Chip(
                                  label: Text(b.toString(),
                                      style: TextStyle(fontSize: 10)),
                                  materialTapTargetSize:
                                      MaterialTapTargetSize.shrinkWrap,
                                  visualDensity: VisualDensity.compact,
                                ))
                            .toList(),
                      ),
                    ],
                    if (addon['coverageCountries'] is List) ...[
                      SizedBox(height: 4),
                      Text(
                        'Countries: ${(addon['coverageCountries'] as List).join(', ')}',
                        style: TextStyle(fontSize: 11, color: Colors.grey[600]),
                      ),
                    ],
                  ],
                ),
              )),
        ],
      ),
    ),
  );
}
```

#### Claim Info - Action Card

```dart
/// Render claim info with actionable buttons (call helpline, etc.)
Widget buildClaimInfoSection(PolicySection section) {
  final fields = {for (var f in section.fields!) f.fieldId: f};

  return Card(
    margin: EdgeInsets.all(12),
    child: Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(section.sectionTitle,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          SizedBox(height: 12),
          // CSR Badge
          if (fields['claimInfo_claimSettlementRatio'] != null)
            Container(
              padding: EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.verified, color: Colors.blue),
                  SizedBox(width: 8),
                  Text('Claim Settlement Ratio: '),
                  Text(
                    fields['claimInfo_claimSettlementRatio']!.value.toString(),
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                ],
              ),
            ),
          SizedBox(height: 12),
          // Other fields
          ...section.fields!
              .where((f) => f.fieldId != 'claimInfo_claimSettlementRatio')
              .map((f) {
            if (f.value is List) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(f.label,
                      style: TextStyle(
                          fontSize: 13, fontWeight: FontWeight.w600)),
                  SizedBox(height: 4),
                  ...(f.value as List).map((doc) => Padding(
                        padding: EdgeInsets.only(bottom: 2),
                        child: Row(
                          children: [
                            Icon(Icons.description,
                                size: 14, color: Colors.grey),
                            SizedBox(width: 6),
                            Text(doc.toString(),
                                style: TextStyle(fontSize: 12)),
                          ],
                        ),
                      )),
                  SizedBox(height: 8),
                ],
              );
            }
            return _buildFieldRow(f);
          }),
        ],
      ),
    ),
  );
}
```

### 6.3 Section Routing (Full Switch)

```dart
Widget buildSection(PolicySection section) {
  switch (section.sectionId) {
    case 'policyIdentification':
      return buildPolicyIdentificationHeader(section);
    case 'insuredMembers':
    case 'membersCovered':
      return buildInsuredMembersCards(section);
    case 'coverageDetails':
      return buildCoverageDetailsSection(section);
    case 'waitingPeriods':
      return buildWaitingPeriodsSection(section);
    case 'subLimits':
      return buildSubLimitsSection(section);
    case 'exclusions':
      return buildExclusionsSection(section);
    case 'premiumBreakdown':
      return buildPremiumBreakdownSection(section);
    case 'addOnPolicies':
      return buildAddOnPoliciesSection(section);
    case 'claimInfo':
      return buildClaimInfoSection(section);
    default:
      // Generic rendering for all other sections
      if (section.sectionType == 'list') {
        return ListSectionWidget(section: section);
      }
      return FieldsSectionWidget(section: section);
  }
}
```

---

## 7. Value Type Handling

All fields have a `valueType` that determines rendering. Handle each type:

| valueType | Dart Type | Rendering | Example Value |
|-----------|-----------|-----------|---------------|
| `string` | `String` | Plain text | `"Family Floater"` |
| `number` | `num` | Formatted number, Indian comma format for large numbers | `12000000` → `₹1,20,00,000` |
| `currency` | `String` | Green text, already formatted with ₹ | `"₹40,000 per eye"` |
| `date` | `String` | Parse `YYYY-MM-DD` → `dd MMM yyyy` | `"2025-03-01"` → `01 Mar 2025` |
| `boolean` | `bool` or `String` | Green "Yes" / Grey "No" chip | `true`, `"Yes"`, `"No"` |
| `array` | `List` | Bulleted list or comma-separated | `["item1", "item2"]` |

### Boolean Value Gotcha

The API may return booleans as actual `bool`, as `"Yes"`/`"No"` strings, or as `"true"`/`"false"`. Always normalize:

```dart
bool parseBool(dynamic value) {
  if (value is bool) return value;
  if (value is String) {
    return value.toLowerCase() == 'yes' || value.toLowerCase() == 'true';
  }
  return false;
}
```

### Array Value Gotcha

Array values can contain:
- Simple strings: `["item1", "item2"]`
- Complex objects: `[{"addOnName": "Care Shield", "premium": "₹3,500", ...}]`

Check `item is Map` before rendering:

```dart
Widget buildArrayField(Field field) {
  final list = field.value as List? ?? [];
  if (list.isEmpty) return Text('-');

  if (list.first is Map) {
    // Complex object array - render as cards
    return Column(
      children: list.map((item) {
        final map = item as Map<String, dynamic>;
        return _buildObjectCard(map);
      }).toList(),
    );
  }

  // Simple string array - render as bullet list
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: list.map((item) => Padding(
      padding: EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('• ', style: TextStyle(color: Colors.grey)),
          Expanded(child: Text(item.toString(), style: TextStyle(fontSize: 13))),
        ],
      ),
    )).toList(),
  );
}
```

---

## 8. Health-Specific Formatters

```dart
class HealthFormatter {
  /// Format sum insured for display
  /// 12000000 → "₹1.2 Cr" or "₹1,20,00,000"
  static String formatSumInsured(double amount) {
    if (amount >= 10000000) {
      return '₹${(amount / 10000000).toStringAsFixed(1)} Cr';
    } else if (amount >= 100000) {
      return '₹${(amount / 100000).toStringAsFixed(0)} Lakh';
    } else {
      return '₹${amount.toStringAsFixed(0)}';
    }
  }

  /// Format with Indian comma system
  /// 1200000 → "12,00,000"
  static String formatIndianNumber(num amount) {
    final str = amount.toInt().toString();
    if (str.length <= 3) return str;

    String result = str.substring(str.length - 3);
    String remaining = str.substring(0, str.length - 3);
    while (remaining.isNotEmpty) {
      final chunk = remaining.length >= 2
          ? remaining.substring(remaining.length - 2)
          : remaining;
      result = '$chunk,$result';
      remaining = remaining.substring(
          0, remaining.length - chunk.length);
    }
    return result;
  }

  /// Format premium
  /// 25459.42 → "₹25,459/year"
  static String formatPremium(double amount, String frequency) {
    final suffix = frequency.toLowerCase() == 'annual'
        ? '/year'
        : frequency.toLowerCase() == 'monthly'
            ? '/month'
            : '/$frequency';
    return '₹${formatIndianNumber(amount.round())}$suffix';
  }

  /// Format policy status badge color
  static Color statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'active':
        return Color(0xFF22C55E);
      case 'expired':
        return Color(0xFFEF4444);
      case 'lapsed':
        return Color(0xFFF97316);
      default:
        return Color(0xFF6B7280);
    }
  }

  /// Calculate days remaining in policy
  static int daysRemaining(String endDate) {
    try {
      final end = DateTime.parse(endDate);
      final remaining = end.difference(DateTime.now()).inDays;
      return remaining > 0 ? remaining : 0;
    } catch (_) {
      return 0;
    }
  }

  /// Format "No limit" or actual value
  static String formatLimit(String value) {
    if (value.toLowerCase().contains('no limit')) {
      return 'No Limit';
    }
    return value;
  }
}
```

---

## 9. Complete Sample API Response

Below is a **real sample** response for an Acko Health Insurance policy. Use this for development and testing.

```json
{
    "success": true,
    "userId": "282",
    "policyId": "ANL_282_fb1cd159234d",
    "policyNumber": "APHP20223052R2",
    "message": "Policy uploaded and analyzed successfully",
    "policyDetails": {
        "policyNumber": "APHP20223052R2",
        "uin": "ACKHLIP25035V022425",
        "insuranceProvider": "Acko General Insurance Limited",
        "policyType": "health",
        "policyHolderName": "SARABJIT SINGH MUDDAR",
        "insuredName": "SARABJIT SINGH MUDDAR",
        "coverageAmount": 12000000,
        "sumAssured": 12000000,
        "premium": 25459.42,
        "premiumFrequency": "annual",
        "startDate": "2025-03-01",
        "endDate": "2026-02-28",
        "status": "active",
        "relationship": "other",
        "originalDocumentUrl": "https://raceabove-dev.s3.ap-south-1.amazonaws.com/reports/policy_original_UPL_282_cd39027f3cac_20260205_105610.pdf",
        "sections": [
            {
                "sectionId": "policyIdentification",
                "sectionTitle": "Policy Identification",
                "sectionType": "fields",
                "displayOrder": 1,
                "fields": [
                    {"fieldId": "policyIdentification_policyNumber", "label": "Policy Number", "value": "APHP20223052R2", "valueType": "string", "displayOrder": 0},
                    {"fieldId": "policyIdentification_uin", "label": "UIN", "value": "ACKHLIP25035V022425", "valueType": "string", "displayOrder": 1},
                    {"fieldId": "policyIdentification_productName", "label": "Product Name", "value": "ACKO Personal Health Policy - Platinum Plan", "valueType": "string", "displayOrder": 2},
                    {"fieldId": "policyIdentification_policyType", "label": "Policy Type", "value": "Family Floater", "valueType": "string", "displayOrder": 3},
                    {"fieldId": "policyIdentification_insurerName", "label": "Insurance Company", "value": "Acko General Insurance Limited", "valueType": "string", "displayOrder": 4},
                    {"fieldId": "policyIdentification_insurerRegistrationNumber", "label": "Insurer Registration Number", "value": "157", "valueType": "string", "displayOrder": 5},
                    {"fieldId": "policyIdentification_insurerAddress", "label": "Insurer Address", "value": "36/5, Somasandra palya, Haralukunte village, Adjacent 27th main road, sector 2, HSR layout, Bengaluru Urban, Bengaluru, Karnataka, 560102", "valueType": "string", "displayOrder": 6},
                    {"fieldId": "policyIdentification_insurerTollFree", "label": "Insurer Toll Free", "value": "18004250005", "valueType": "string", "displayOrder": 7},
                    {"fieldId": "policyIdentification_intermediaryName", "label": "Intermediary Name", "value": "Eazr Finserv Pvt Ltd", "valueType": "string", "displayOrder": 8},
                    {"fieldId": "policyIdentification_intermediaryCode", "label": "Intermediary Code", "value": "IRDAI/DB/885/2024", "valueType": "string", "displayOrder": 9},
                    {"fieldId": "policyIdentification_intermediaryEmail", "label": "Intermediary Email", "value": "support@eazr.com", "valueType": "string", "displayOrder": 10},
                    {"fieldId": "policyIdentification_policyIssueDate", "label": "Issue Date", "value": "2025-03-01", "valueType": "date", "displayOrder": 11},
                    {"fieldId": "policyIdentification_policyPeriod", "label": "Policy Period", "value": "01 March 2025 -> 28 February 2026", "valueType": "string", "displayOrder": 12},
                    {"fieldId": "policyIdentification_policyPeriodStart", "label": "Policy Period Start", "value": "2025-03-01", "valueType": "string", "displayOrder": 13},
                    {"fieldId": "policyIdentification_policyPeriodEnd", "label": "Policy Period End", "value": "2026-02-28", "valueType": "string", "displayOrder": 14}
                ]
            },
            {
                "sectionId": "insuredMembers",
                "sectionTitle": "Insured Members",
                "sectionType": "list",
                "displayOrder": 2,
                "items": [
                    {
                        "itemId": "insuredMembers_item_0",
                        "fields": [
                            {"fieldId": "insuredMembers_0_memberName", "label": "Membername", "value": "KUNJAL RAJEEV VASANI", "valueType": "string", "displayOrder": 0},
                            {"fieldId": "insuredMembers_0_memberRelationship", "label": "Memberrelationship", "value": "Spouse", "valueType": "string", "displayOrder": 1},
                            {"fieldId": "insuredMembers_0_memberAge", "label": "Memberage", "value": 33, "valueType": "number", "displayOrder": 2},
                            {"fieldId": "insuredMembers_0_memberGender", "label": "Membergender", "value": "Female", "valueType": "string", "displayOrder": 3}
                        ]
                    },
                    {
                        "itemId": "insuredMembers_item_1",
                        "fields": [
                            {"fieldId": "insuredMembers_1_memberName", "label": "Membername", "value": "SARABJIT SINGH MUDDAR", "valueType": "string", "displayOrder": 0},
                            {"fieldId": "insuredMembers_1_memberRelationship", "label": "Memberrelationship", "value": "Self", "valueType": "string", "displayOrder": 1},
                            {"fieldId": "insuredMembers_1_memberAge", "label": "Memberage", "value": 35, "valueType": "number", "displayOrder": 2},
                            {"fieldId": "insuredMembers_1_memberGender", "label": "Membergender", "value": "Male", "valueType": "string", "displayOrder": 3}
                        ]
                    },
                    {
                        "itemId": "insuredMembers_item_2",
                        "fields": [
                            {"fieldId": "insuredMembers_2_memberName", "label": "Membername", "value": "RABJAL KAUR MUDDAR", "valueType": "string", "displayOrder": 0},
                            {"fieldId": "insuredMembers_2_memberRelationship", "label": "Memberrelationship", "value": "Daughter", "valueType": "string", "displayOrder": 1},
                            {"fieldId": "insuredMembers_2_memberAge", "label": "Memberage", "value": 4, "valueType": "number", "displayOrder": 2},
                            {"fieldId": "insuredMembers_2_memberGender", "label": "Membergender", "value": "Female", "valueType": "string", "displayOrder": 3}
                        ]
                    }
                ]
            },
            {
                "sectionId": "coverageDetails",
                "sectionTitle": "Coverage Details",
                "sectionType": "fields",
                "displayOrder": 3,
                "fields": [
                    {"fieldId": "coverageDetails_sumInsured", "label": "Sum Insured", "value": 12000000, "valueType": "number", "displayOrder": 0},
                    {"fieldId": "coverageDetails_coverType", "label": "Cover Type", "value": "Individual", "valueType": "string", "displayOrder": 1},
                    {"fieldId": "coverageDetails_roomRentLimit", "label": "Room Rent Limit", "value": "No limit", "valueType": "string", "displayOrder": 2},
                    {"fieldId": "coverageDetails_icuLimit", "label": "ICU Limit", "value": "No limit", "valueType": "string", "displayOrder": 3},
                    {"fieldId": "coverageDetails_preHospitalization", "label": "Pre-Hospitalization", "value": "60 days", "valueType": "string", "displayOrder": 4},
                    {"fieldId": "coverageDetails_postHospitalization", "label": "Post-Hospitalization", "value": "120 days", "valueType": "string", "displayOrder": 5},
                    {"fieldId": "coverageDetails_dayCareProcedures", "label": "Day Care Procedures", "value": "Yes", "valueType": "boolean", "displayOrder": 6},
                    {"fieldId": "coverageDetails_domiciliaryHospitalization", "label": "Domiciliary Hospitalization", "value": "Yes", "valueType": "boolean", "displayOrder": 7},
                    {"fieldId": "coverageDetails_ambulanceCover", "label": "Ambulance Cover", "value": "No limit", "valueType": "string", "displayOrder": 8},
                    {"fieldId": "coverageDetails_healthCheckup", "label": "Health Checkup", "value": "Once per policy year", "valueType": "string", "displayOrder": 9},
                    {"fieldId": "coverageDetails_ayushTreatment", "label": "AYUSH Treatment", "value": "Yes", "valueType": "boolean", "displayOrder": 10},
                    {"fieldId": "coverageDetails_organDonor", "label": "Organ Donor Cover", "value": "Yes", "valueType": "boolean", "displayOrder": 11},
                    {"fieldId": "restoration_available", "label": "Available", "value": "Yes", "valueType": "boolean", "displayOrder": 0},
                    {"fieldId": "restoration_type", "label": "Type", "value": "Unlimited restore", "valueType": "string", "displayOrder": 1},
                    {"fieldId": "coverageDetails_restorationAmount", "label": "Restoration Amount", "value": "Unlimited restore", "valueType": "string", "displayOrder": 12},
                    {"fieldId": "coverageDetails_modernTreatment", "label": "Modern Treatment", "value": "Yes", "valueType": "boolean", "displayOrder": 13},
                    {"fieldId": "coverageDetails_consumablesCoverage", "label": "Consumablescoverage", "value": "Yes", "valueType": "boolean", "displayOrder": 14},
                    {"fieldId": "coverageDetails_consumablesCoverageDetails", "label": "Consumablescoveragedetails", "value": "No deductions on consumables like gloves, masks etc.", "valueType": "string", "displayOrder": 15}
                ]
            },
            {
                "sectionId": "waitingPeriods",
                "sectionTitle": "Waiting Periods",
                "sectionType": "fields",
                "displayOrder": 4,
                "fields": [
                    {"fieldId": "waitingPeriods_initialWaitingPeriod", "label": "Initial Waiting Period", "value": "No waiting period", "valueType": "string", "displayOrder": 0},
                    {"fieldId": "waitingPeriods_preExistingDiseaseWaiting", "label": "Pre-existing Disease Waiting", "value": "No waiting period", "valueType": "string", "displayOrder": 1},
                    {"fieldId": "waitingPeriods_specificDiseaseWaiting", "label": "Specific Disease Waiting", "value": "No waiting period", "valueType": "string", "displayOrder": 2},
                    {"fieldId": "waitingPeriods_accidentCoveredFromDay1", "label": "Accident Covered From Day 1", "value": "Yes", "valueType": "boolean", "displayOrder": 3},
                    {"fieldId": "waitingPeriods_specificDiseasesList", "label": "Specific Diseases List", "value": ["Osteoarthritis & Osteoporosis", "Hernia", "Hydrocele", "Fistula in Ano", "Piles", "Sinusitis", "Tonsillitis", "Gall Stone", "Kidney Stone", "Joint Replacement"], "valueType": "array", "displayOrder": 4}
                ]
            },
            {
                "sectionId": "copayDetails",
                "sectionTitle": "Copaydetails",
                "sectionType": "fields",
                "displayOrder": 5,
                "fields": [
                    {"fieldId": "copayDetails_generalCopay", "label": "Generalcopay", "value": "0%", "valueType": "string", "displayOrder": 0}
                ]
            },
            {
                "sectionId": "subLimits",
                "sectionTitle": "Sub-Limits",
                "sectionType": "fields",
                "displayOrder": 6,
                "fields": [
                    {"fieldId": "subLimits_cataractLimit", "label": "Cataract Limit", "value": "₹40,000 per eye (with lens implant)", "valueType": "currency", "displayOrder": 0},
                    {"fieldId": "subLimits_jointReplacementLimit", "label": "Joint Replacement Limit", "value": "₹2,00,000 per joint", "valueType": "currency", "displayOrder": 1},
                    {"fieldId": "subLimits_internalProsthesisLimit", "label": "Internal Prosthesis Limit", "value": "₹1,00,000 or actual cost, whichever is less", "valueType": "currency", "displayOrder": 2},
                    {"fieldId": "subLimits_kidneyStoneLimit", "label": "Kidney Stone Limit", "value": "₹50,000", "valueType": "currency", "displayOrder": 3},
                    {"fieldId": "subLimits_gallStoneLimit", "label": "Gall Stone Limit", "value": "₹50,000", "valueType": "currency", "displayOrder": 4},
                    {"fieldId": "subLimits_modernTreatmentLimit", "label": "Modern Treatment Limit", "value": "Up to Sum Insured", "valueType": "string", "displayOrder": 5}
                ]
            },
            {
                "sectionId": "exclusions",
                "sectionTitle": "Exclusions",
                "sectionType": "fields",
                "displayOrder": 7,
                "fields": [
                    {"fieldId": "exclusions_permanentExclusions", "label": "Permanent Exclusions", "value": ["Self-inflicted injury", "Participation in criminal activities", "War or nuclear risks", "Cosmetic procedures", "Dental treatment (unless due to accident)", "Hearing aids & spectacles"], "valueType": "array", "displayOrder": 0}
                ]
            },
            {
                "sectionId": "premiumBreakdown",
                "sectionTitle": "Premium Breakdown",
                "sectionType": "fields",
                "displayOrder": 8,
                "fields": [
                    {"fieldId": "premiumBreakdown_basePremium", "label": "Base Premium", "value": 16483.46, "valueType": "number", "displayOrder": 0},
                    {"fieldId": "premiumBreakdown_totalPremium", "label": "Total Premium", "value": 25459.42, "valueType": "number", "displayOrder": 1},
                    {"fieldId": "premiumBreakdown_premiumFrequency", "label": "Premium Frequency", "value": "Annual", "valueType": "string", "displayOrder": 2},
                    {"fieldId": "otherAddOns_Initial waiting period waiver", "label": "Initial Waiting Period Waiver", "value": 217.59, "valueType": "number", "displayOrder": 0},
                    {"fieldId": "otherAddOns_Medically necessary hospitalization", "label": "Medically Necessary Hospitalization", "value": 906.58, "valueType": "number", "displayOrder": 1},
                    {"fieldId": "otherAddOns_Inflation Protect SI", "label": "Inflation Protect Si", "value": 453.29, "valueType": "number", "displayOrder": 2},
                    {"fieldId": "otherAddOns_Restore SI", "label": "Restore Si", "value": 329.66, "valueType": "number", "displayOrder": 3},
                    {"fieldId": "otherAddOns_Reduction in Specific illness waiting period", "label": "Reduction In Specific Illness Waiting Period", "value": 2719.77, "valueType": "number", "displayOrder": 4},
                    {"fieldId": "otherAddOns_Doctor on call", "label": "Doctor On Call", "value": 114.39, "valueType": "number", "displayOrder": 5},
                    {"fieldId": "otherAddOns_Waiver of non-payable medical expenses", "label": "Waiver Of Non-Payable Medical Expenses", "value": 1648.34, "valueType": "number", "displayOrder": 6},
                    {"fieldId": "otherAddOns_Preventive Health Check-up", "label": "Preventive Health Check-Up", "value": 1100, "valueType": "number", "displayOrder": 7},
                    {"fieldId": "premiumBreakdown_gracePeriod", "label": "Grace Period", "value": "30 days", "valueType": "string", "displayOrder": 3}
                ]
            },
            {
                "sectionId": "noClaimBonus",
                "sectionTitle": "No Claim Bonus",
                "sectionType": "fields",
                "displayOrder": 9,
                "fields": [
                    {"fieldId": "noClaimBonus_available", "label": "Available", "value": "No", "valueType": "boolean", "displayOrder": 0},
                    {"fieldId": "noClaimBonus_maxNcbPercentage", "label": "Max NCB %", "value": "50%", "valueType": "string", "displayOrder": 1}
                ]
            },
            {
                "sectionId": "addOnPolicies",
                "sectionTitle": "Add-On Policies",
                "sectionType": "fields",
                "displayOrder": 10,
                "fields": [
                    {"fieldId": "addOnPolicies_hasAddOn", "label": "Has Add-On", "value": "No", "valueType": "boolean", "displayOrder": 0},
                    {
                        "fieldId": "addOnPolicies_addOnPoliciesList",
                        "label": "Add-On Policies List",
                        "value": [
                            {"addOnName": "Care Shield", "uin": "INSAH6483611V052324", "sumInsured": 12000000, "premium": "₹3,500", "benefits": ["Claim Shield", "Restore Benefit", "Daily Cash"]},
                            {"addOnName": "International Coverage", "uin": null, "sumInsured": 12000000, "premium": "₹850", "coverageCountries": ["USA", "Canada", "UK", "Europe", "Singapore", "Thailand", "Malaysia", "UAE"]},
                            {"addOnName": "Universal Shield", "uin": null, "sumInsured": 12000000, "premium": "₹2,000", "benefits": ["Restoration", "Inflation Shield", "NCB Protect"]},
                            {"addOnName": "Covid Care", "uin": null, "sumInsured": 12000000, "premium": "₹700", "benefits": ["Home Care Treatment", "Tele-consultation", "Medicine Delivery"]}
                        ],
                        "valueType": "array",
                        "displayOrder": 1
                    },
                    {"fieldId": "addOnPolicies_claimShield", "label": "Claim Shield", "value": "No", "valueType": "boolean", "displayOrder": 2},
                    {"fieldId": "addOnPolicies_ncbShield", "label": "NCB Shield", "value": "No", "valueType": "boolean", "displayOrder": 3},
                    {"fieldId": "addOnPolicies_inflationShield", "label": "Inflation Shield", "value": "Yes", "valueType": "boolean", "displayOrder": 4}
                ]
            },
            {
                "sectionId": "declaredPed",
                "sectionTitle": "Declared Pre-existing Diseases",
                "sectionType": "fields",
                "displayOrder": 11,
                "fields": [
                    {"fieldId": "declaredPed_pedWaitingPeriodCompleted", "label": "PED Waiting Period Completed", "value": "Yes", "valueType": "boolean", "displayOrder": 0},
                    {"fieldId": "declaredPed_pedStatus", "label": "PED Status", "value": "No waiting period", "valueType": "string", "displayOrder": 1}
                ]
            },
            {
                "sectionId": "benefits",
                "sectionTitle": "Benefits & Features",
                "sectionType": "fields",
                "displayOrder": 12,
                "fields": [
                    {"fieldId": "restoration_available", "label": "Available", "value": "Yes", "valueType": "boolean", "displayOrder": 0},
                    {"fieldId": "restoration_type", "label": "Type", "value": "Unlimited restore", "valueType": "string", "displayOrder": 1},
                    {"fieldId": "noClaimBonus_available", "label": "Available", "value": "No", "valueType": "boolean", "displayOrder": 0},
                    {"fieldId": "noClaimBonus_percentage", "label": "Percentage", "value": "10% per claim-free year", "valueType": "string", "displayOrder": 1},
                    {"fieldId": "noClaimBonus_maxPercentage", "label": "Maxpercentage", "value": "50%", "valueType": "string", "displayOrder": 2},
                    {"fieldId": "benefits_ayushCovered", "label": "Ayushcovered", "value": "Yes", "valueType": "boolean", "displayOrder": 0},
                    {"fieldId": "benefits_ayushLimit", "label": "Ayushlimit", "value": "Up to SI", "valueType": "string", "displayOrder": 1},
                    {"fieldId": "benefits_mentalHealthCovered", "label": "Mentalhealthcovered", "value": "No", "valueType": "boolean", "displayOrder": 2},
                    {"fieldId": "benefits_dayCareCovered", "label": "Daycarecovered", "value": "Yes", "valueType": "boolean", "displayOrder": 3},
                    {"fieldId": "benefits_dayCareCoverageType", "label": "Daycarecoveragetype", "value": "540+ Procedures", "valueType": "string", "displayOrder": 4}
                ]
            },
            {
                "sectionId": "accumulatedBenefits",
                "sectionTitle": "Accumulated Benefits",
                "sectionType": "fields",
                "displayOrder": 13,
                "fields": [
                    {"fieldId": "accumulatedBenefits_totalEffectiveCoverage", "label": "Totaleffectivecoverage", "value": 12000000, "valueType": "number", "displayOrder": 0}
                ]
            },
            {
                "sectionId": "membersCovered",
                "sectionTitle": "Members Covered",
                "sectionType": "list",
                "displayOrder": 14,
                "items": [
                    {
                        "itemId": "membersCovered_item_0",
                        "fields": [
                            {"fieldId": "membersCovered_0_memberName", "label": "Membername", "value": "KUNJAL RAJEEV VASANI", "valueType": "string", "displayOrder": 0},
                            {"fieldId": "membersCovered_0_memberRelationship", "label": "Memberrelationship", "value": "Spouse", "valueType": "string", "displayOrder": 1},
                            {"fieldId": "membersCovered_0_memberAge", "label": "Memberage", "value": 33, "valueType": "number", "displayOrder": 2},
                            {"fieldId": "membersCovered_0_memberGender", "label": "Membergender", "value": "Female", "valueType": "string", "displayOrder": 3}
                        ]
                    },
                    {
                        "itemId": "membersCovered_item_1",
                        "fields": [
                            {"fieldId": "membersCovered_1_memberName", "label": "Membername", "value": "SARABJIT SINGH MUDDAR", "valueType": "string", "displayOrder": 0},
                            {"fieldId": "membersCovered_1_memberRelationship", "label": "Memberrelationship", "value": "Self", "valueType": "string", "displayOrder": 1},
                            {"fieldId": "membersCovered_1_memberAge", "label": "Memberage", "value": 35, "valueType": "number", "displayOrder": 2},
                            {"fieldId": "membersCovered_1_memberGender", "label": "Membergender", "value": "Male", "valueType": "string", "displayOrder": 3}
                        ]
                    },
                    {
                        "itemId": "membersCovered_item_2",
                        "fields": [
                            {"fieldId": "membersCovered_2_memberName", "label": "Membername", "value": "RABJAL KAUR MUDDAR", "valueType": "string", "displayOrder": 0},
                            {"fieldId": "membersCovered_2_memberRelationship", "label": "Memberrelationship", "value": "Daughter", "valueType": "string", "displayOrder": 1},
                            {"fieldId": "membersCovered_2_memberAge", "label": "Memberage", "value": 4, "valueType": "number", "displayOrder": 2},
                            {"fieldId": "membersCovered_2_memberGender", "label": "Membergender", "value": "Female", "valueType": "string", "displayOrder": 3}
                        ]
                    }
                ]
            },
            {
                "sectionId": "policyHistory",
                "sectionTitle": "Policy History",
                "sectionType": "fields",
                "displayOrder": 15,
                "fields": [
                    {"fieldId": "policyHistory_firstEnrollmentDate", "label": "Firstenrollmentdate", "value": "2023-03-01", "valueType": "date", "displayOrder": 0},
                    {"fieldId": "policyHistory_insuredSinceDate", "label": "Insuredsincedate", "value": "2023-03-01", "valueType": "date", "displayOrder": 1},
                    {"fieldId": "portability_available", "label": "Available", "value": "No", "valueType": "boolean", "displayOrder": 0}
                ]
            },
            {
                "sectionId": "networkInfo",
                "sectionTitle": "Network Hospital Information",
                "sectionType": "fields",
                "displayOrder": 16,
                "fields": [
                    {"fieldId": "networkInfo_networkHospitalsCount", "label": "Network Hospitals Count", "value": "14,000+ Hospitals", "valueType": "string", "displayOrder": 0},
                    {"fieldId": "networkInfo_ambulanceCover", "label": "Ambulance Cover", "value": "No limit", "valueType": "string", "displayOrder": 1},
                    {"fieldId": "networkInfo_cashlessFacility", "label": "Cashless Facility", "value": "Yes", "valueType": "boolean", "displayOrder": 2},
                    {"fieldId": "networkInfo_networkType", "label": "Network Type", "value": "Pan India", "valueType": "string", "displayOrder": 3}
                ]
            },
            {
                "sectionId": "claimInfo",
                "sectionTitle": "Claim Information",
                "sectionType": "fields",
                "displayOrder": 17,
                "fields": [
                    {"fieldId": "claimInfo_claimSettlementRatio", "label": "Claim Settlement Ratio", "value": "92%", "valueType": "string", "displayOrder": 0},
                    {"fieldId": "claimInfo_claimProcess", "label": "Claim Process", "value": "Cashless & Reimbursement", "valueType": "string", "displayOrder": 1},
                    {"fieldId": "claimInfo_claimIntimation", "label": "Claim Intimation", "value": "Within 24 hours of admission", "valueType": "string", "displayOrder": 2},
                    {"fieldId": "claimInfo_claimDocuments", "label": "Claim Documents", "value": ["Claim Form", "Medical Reports", "Discharge Summary", "Bills & Receipts", "Investigation Reports", "KYC Documents"], "valueType": "array", "displayOrder": 3}
                ]
            }
        ],
        "categorySpecificData": {
            "policyIdentification": {
                "policyNumber": "APHP20223052R2",
                "uin": "ACKHLIP25035V022425",
                "productName": "ACKO Personal Health Policy - Platinum Plan",
                "policyType": "Family Floater",
                "insurerName": "Acko General Insurance Limited",
                "insurerRegistrationNumber": "157",
                "insurerAddress": "36/5, Somasandra palya, Haralukunte village, Adjacent 27th main road, sector 2, HSR layout, Bengaluru Urban, Bengaluru, Karnataka, 560102",
                "insurerTollFree": "18004250005",
                "tpaName": null,
                "intermediaryName": "Eazr Finserv Pvt Ltd",
                "intermediaryCode": "IRDAI/DB/885/2024",
                "intermediaryEmail": "support@eazr.com",
                "policyIssueDate": "2025-03-01",
                "policyPeriod": "01 March 2025 -> 28 February 2026",
                "policyPeriodStart": "2025-03-01",
                "policyPeriodEnd": "2026-02-28"
            },
            "insuredMembers": [
                {"memberName": "KUNJAL RAJEEV VASANI", "memberRelationship": "Spouse", "memberAge": 33, "memberGender": "Female"},
                {"memberName": "SARABJIT SINGH MUDDAR", "memberRelationship": "Self", "memberAge": 35, "memberGender": "Male"},
                {"memberName": "RABJAL KAUR MUDDAR", "memberRelationship": "Daughter", "memberAge": 4, "memberGender": "Female"}
            ],
            "coverageDetails": {
                "sumInsured": 12000000,
                "coverType": "Individual",
                "roomRentLimit": "No limit",
                "roomRentCopay": null,
                "icuLimit": "No limit",
                "icuDailyLimit": null,
                "preHospitalization": "60 days",
                "postHospitalization": "120 days",
                "dayCareProcedures": true,
                "domiciliaryHospitalization": true,
                "ambulanceCover": "No limit",
                "healthCheckup": "Once per policy year",
                "ayushTreatment": true,
                "organDonor": true,
                "restoration": {"available": true, "type": "Unlimited restore"},
                "restorationAmount": "Unlimited restore",
                "modernTreatment": true,
                "dailyCashAllowance": null,
                "convalescenceBenefit": null,
                "consumablesCoverage": true,
                "consumablesCoverageDetails": "No deductions on consumables like gloves, masks etc."
            },
            "waitingPeriods": {
                "initialWaitingPeriod": "No waiting period",
                "preExistingDiseaseWaiting": "No waiting period",
                "specificDiseaseWaiting": "No waiting period",
                "maternityWaiting": null,
                "accidentCoveredFromDay1": true,
                "specificDiseasesList": ["Osteoarthritis & Osteoporosis", "Hernia", "Hydrocele", "Fistula in Ano", "Piles", "Sinusitis", "Tonsillitis", "Gall Stone", "Kidney Stone", "Joint Replacement"]
            },
            "copayDetails": {
                "generalCopay": "0%",
                "ageBasedCopay": [],
                "diseaseSpecificCopay": []
            },
            "subLimits": {
                "cataractLimit": "₹40,000 per eye (with lens implant)",
                "jointReplacementLimit": "₹2,00,000 per joint",
                "internalProsthesisLimit": "₹1,00,000 or actual cost, whichever is less",
                "kidneyStoneLimit": "₹50,000",
                "gallStoneLimit": "₹50,000",
                "modernTreatmentLimit": "Up to Sum Insured",
                "otherSubLimits": []
            },
            "exclusions": {
                "permanentExclusions": ["Self-inflicted injury", "Participation in criminal activities", "War or nuclear risks", "Cosmetic procedures", "Dental treatment (unless due to accident)", "Hearing aids & spectacles"],
                "conditionalExclusions": [],
                "pedSpecificExclusions": []
            },
            "premiumBreakdown": {
                "basePremium": 16483.46,
                "totalPremium": 25459.42,
                "premiumFrequency": "Annual",
                "gracePeriod": "30 days"
            },
            "noClaimBonus": {
                "available": false,
                "maxNcbPercentage": "50%"
            },
            "addOnPolicies": {
                "hasAddOn": false,
                "addOnPoliciesList": [
                    {"addOnName": "Care Shield", "uin": "INSAH6483611V052324", "sumInsured": 12000000, "premium": "₹3,500", "benefits": ["Claim Shield", "Restore Benefit", "Daily Cash"]},
                    {"addOnName": "International Coverage", "uin": null, "sumInsured": 12000000, "premium": "₹850", "coverageCountries": ["USA", "Canada", "UK", "Europe", "Singapore", "Thailand", "Malaysia", "UAE"]},
                    {"addOnName": "Universal Shield", "uin": null, "sumInsured": 12000000, "premium": "₹2,000", "benefits": ["Restoration", "Inflation Shield", "NCB Protect"]},
                    {"addOnName": "Covid Care", "uin": null, "sumInsured": 12000000, "premium": "₹700", "benefits": ["Home Care Treatment", "Tele-consultation", "Medicine Delivery"]}
                ],
                "claimShield": false,
                "ncbShield": false,
                "inflationShield": true
            },
            "declaredPed": {
                "pedWaitingPeriodCompleted": true,
                "pedStatus": "No waiting period"
            },
            "benefits": {
                "ayushCovered": true,
                "ayushLimit": "Up to SI",
                "mentalHealthCovered": false,
                "dayCareCovered": true,
                "dayCareCoverageType": "540+ Procedures"
            },
            "accumulatedBenefits": {
                "totalEffectiveCoverage": 12000000
            },
            "policyHistory": {
                "firstEnrollmentDate": "2023-03-01",
                "insuredSinceDate": "2023-03-01",
                "portability": {"available": false}
            },
            "networkInfo": {
                "networkHospitalsCount": "14,000+ Hospitals",
                "ambulanceCover": "No limit",
                "cashlessFacility": true,
                "networkType": "Pan India"
            },
            "claimInfo": {
                "claimSettlementRatio": "92%",
                "claimProcess": "Cashless & Reimbursement",
                "claimIntimation": "Within 24 hours of admission",
                "claimDocuments": ["Claim Form", "Medical Reports", "Discharge Summary", "Bills & Receipts", "Investigation Reports", "KYC Documents"]
            }
        }
    }
}
```

---

## Important Notes for Flutter Team

### 1. Sections are Dynamic
- **Never hardcode section order** — always sort by `displayOrder`
- **New sections may appear** in future policies — the generic fallback renderer handles unknown sections
- **Some sections may be missing** — always null-check before rendering

### 2. `insuredMembers` and `membersCovered` Are Duplicates
- Both contain the same member data
- Render only `insuredMembers` (displayOrder 2) in the main view
- Skip `membersCovered` (displayOrder 14) or use it as a secondary reference

### 3. Premium Add-Ons Are Mixed into premiumBreakdown
- Add-on premium fields have `fieldId` starting with `otherAddOns_`
- Filter them separately for the breakdown UI

### 4. Boolean Values Are Inconsistent
- May come as `true`/`false`, `"Yes"`/`"No"`, or `"yes"`/`"no"`
- Always use the `parseBool()` helper from Section 7

### 5. Number Fields May Represent Currency
- `coverageAmount: 12000000` means ₹1.2 Crore (not ₹12 million display)
- Use `HealthFormatter.formatSumInsured()` for large amounts
- Use `HealthFormatter.formatIndianNumber()` for Indian comma formatting

### 6. The `originalDocumentUrl` is an S3 Pre-signed URL
- Use it for "View Original Policy" button
- Open in WebView or external browser
- URL may expire — handle 403 errors gracefully

---

*Last Updated: February 2026*
*Version: 1.0.0*
*EAZR Digipayments Private Limited - Confidential*
