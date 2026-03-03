# EAZR 04 — Personal Accident Insurance | Flutter Mobile Integration Guide

**Version:** 1.0
**API Base:** `/api/policy/upload`
**Insurance Category:** Personal Accident (PA)
**Spec Reference:** `EAZR_04_Personal_Accident.md`

---

## Table of Contents

1. [API Endpoints](#1-api-endpoints)
2. [Policy Detection Keywords](#2-policy-detection-keywords)
3. [Policy Details Tab — Response Schema](#3-policy-details-tab--response-schema)
4. [Deep Analysis — Response Schema](#4-deep-analysis--response-schema)
5. [PDF Report — Download Integration](#5-pdf-report--download-integration)
6. [Data Models (Dart)](#6-data-models-dart)
7. [UI Component Mapping](#7-ui-component-mapping)
8. [Scoring Engine](#8-scoring-engine)
9. [Scenario Simulations](#9-scenario-simulations)
10. [Gap Analysis](#10-gap-analysis)
11. [Recommendations](#11-recommendations)
12. [IPF Integration](#12-ipf-integration)
13. [Color Tokens & Icons](#13-color-tokens--icons)
14. [PPD Schedule Table](#14-ppd-schedule-table)
15. [Backward Compatibility Notes](#15-backward-compatibility-notes)

---

## 1. API Endpoints

### Upload & Extract Policy

```
POST /api/policy/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | Yes | PDF/image of PA policy document |
| `userId` | String | Yes | User identifier |

**Response:** Contains `policyDetails` (Section 3) and `policyAnalyzer` (Section 4).

### Download PDF Report

```
POST /api/policy/download-report
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "policyId": "<policy_id>",
  "userId": "<user_id>"
}
```

**Response:** Returns S3 URL for the generated PA PDF report.

---

## 2. Policy Detection Keywords

The backend routes to the PA-specific builder when `policyType` (case-insensitive) contains any of:

| Keyword | Note |
|---------|------|
| `personal accident` | Primary match |
| `accidental` | Covers "accidental death" etc. |
| `accident` | Generic accident match |
| `pa ` | Trailing space prevents false match on "payment", "parent" |

---

## 3. Policy Details Tab — Response Schema

The `policyDetails` object contains **11 top-level sections**:

```json
{
  "emergencyInfo": { ... },
  "policyOverview": { ... },
  "coverageDetails": { ... },
  "additionalBenefits": { ... },
  "exclusions": { ... },
  "premiumDetails": { ... },
  "scoringEngine": { ... },
  "scenarioSimulations": [ ... ],
  "gapAnalysis": { ... },
  "recommendations": { ... },
  "ipfIntegration": { ... }
}
```

### 3.1 Emergency Info

Quick-access emergency information. Display at the top of the policy screen.

```json
{
  "emergencyInfo": {
    "policyNumber": "PA/1234/5678/2024",
    "policyNumberCopyable": true,
    "claimsHelpline": "1800-266-9725",
    "claimsHelplineCallable": true,
    "claimsEmail": "claims@insurer.com",
    "policyStatus": "active",
    "policyStatusColor": "#22C55E"
  }
}
```

| Field | Type | Flutter Widget | Notes |
|-------|------|---------------|-------|
| `policyNumber` | String | `SelectableText` + Copy button | `policyNumberCopyable: true` |
| `claimsHelpline` | String | Tappable with `url_launcher` | `claimsHelplineCallable: true` |
| `policyStatus` | String | Badge/Chip | Color from `policyStatusColor` |

**Helpline Lookup:** Backend resolves helpline from 15 PA insurers (ICICI Lombard, Bajaj Allianz, HDFC ERGO, Tata AIG, New India, United India, National, Oriental, SBI General, Star Health, Care Health, Reliance General, Future Generali, Go Digit, Chola MS).

### 3.2 Policy Overview

```json
{
  "policyOverview": {
    "insurerName": "ICICI Lombard",
    "productName": "Personal Accident Insurance",
    "subType": {
      "code": "IND_PA",
      "label": "Individual PA",
      "color": "#3B82F6",
      "icon": "person"
    },
    "principalSumInsured": 2500000,
    "principalSumInsuredFormatted": "₹25,00,000",
    "policyValidity": {
      "startDate": "01-Apr-2024",
      "endDate": "31-Mar-2025"
    },
    "membersCovered": 1,
    "insuredMembers": [
      {
        "name": "John Doe",
        "relationship": "self",
        "dateOfBirth": "15-Jan-1990",
        "gender": "Male",
        "occupation": "IT Professional"
      }
    ],
    "groupDetails": null,
    "nomination": {
      "nomineeName": "Jane Doe",
      "nomineeRelationship": "Spouse",
      "nomineeShare": "100%"
    }
  }
}
```

**Sub-Type Codes:**

| Code | Label | Color | Icon |
|------|-------|-------|------|
| `IND_PA` | Individual PA | `#3B82F6` | `person` |
| `FAM_PA` | Family PA | `#8B5CF6` | `family_restroom` |
| `GRP_PA` | Group PA | `#10B981` | `groups` |
| `PA_MED` | PA with Medical | `#F59E0B` | `medical_services` |
| `STU_PA` | Student PA | `#6366F1` | `school` |

**Note:** `groupDetails` is only non-null when `subType.code == "GRP_PA"`.

### 3.3 Coverage Details (5 Cards)

This is the core section. Render as **5 expandable cards**, one per benefit type.

```json
{
  "coverageDetails": {
    "accidentalDeath": {
      "covered": true,
      "benefitPercentage": 100,
      "benefitAmount": 2500000,
      "benefitFormatted": "₹25,00,000",
      "description": "100% of Sum Insured",
      "doubleIndemnity": {
        "applicable": true,
        "conditions": "Public transport accident",
        "doubleAmount": 5000000,
        "doubleFormatted": "₹50,00,000"
      }
    },
    "permanentTotalDisability": {
      "covered": true,
      "benefitPercentage": 100,
      "benefitAmount": 2500000,
      "benefitFormatted": "₹25,00,000",
      "description": "100% of Sum Insured",
      "conditionsList": [
        "Loss of both eyes",
        "Loss of both hands or feet",
        "Loss of one hand and one foot",
        "Total and permanent paralysis",
        "Complete and incurable insanity"
      ]
    },
    "permanentPartialDisability": {
      "covered": true,
      "benefitType": "As per IRDAI schedule",
      "scheduleCount": 19,
      "schedule": [
        {
          "disability": "Loss of both hands",
          "percentage": 100,
          "benefitAmount": 2500000,
          "benefitFormatted": "₹25,00,000"
        }
      ],
      "note": "Multiple disabilities can be claimed up to 100% total"
    },
    "temporaryTotalDisability": {
      "covered": true,
      "benefitType": "weekly",
      "benefitAmount": 25000,
      "benefitFormatted": "₹25,000/week",
      "maximumWeeks": 52,
      "waitingPeriodDays": 7,
      "exampleCalculations": [
        { "duration": "2 weeks", "benefit": 25000, "formatted": "₹25,000", "note": "Week 2 only (Week 1 is waiting)" },
        { "duration": "4 weeks", "benefit": 75000, "formatted": "₹75,000", "note": "Weeks 2-4" },
        { "duration": "3 months", "benefit": 300000, "formatted": "₹3,00,000", "note": "Weeks 2-13" },
        { "duration": "6 months", "benefit": 625000, "formatted": "₹6,25,000", "note": "Weeks 2-26" },
        { "duration": "1 year", "benefit": 1275000, "formatted": "₹12,75,000", "note": "Weeks 2-52" }
      ]
    },
    "medicalExpenses": {
      "covered": true,
      "limitType": "percentage_of_si",
      "limitPercentage": 10,
      "limitAmount": 250000,
      "limitFormatted": "₹2,50,000",
      "perAccidentOrAnnual": "per_accident"
    }
  }
}
```

**Card Rendering Guide:**

| Card | Header | Key Value | Expandable Content |
|------|--------|-----------|-------------------|
| AD | Accidental Death | `benefitFormatted` | Double indemnity badge if `applicable` |
| PTD | Permanent Total Disability | `benefitFormatted` | `conditionsList` as bullet list |
| PPD | Permanent Partial Disability | `scheduleCount` conditions | Full `schedule` table (see Section 14) |
| TTD | Temporary Total Disability | `benefitFormatted` | `exampleCalculations` table + waiting period note |
| Medical | Medical Expenses | `limitFormatted` | `perAccidentOrAnnual` badge |

**Note:** `exampleCalculations` is an empty array `[]` when TTD is not covered.

### 3.4 Additional Benefits

8 supplementary benefits. Render as a status list with covered/not-covered indicators.

```json
{
  "additionalBenefits": {
    "benefits": [
      {
        "key": "educationBenefit",
        "label": "Education Benefit",
        "icon": "school",
        "description": "Education continuation for dependent children",
        "covered": true,
        "limit": 500000,
        "limitFormatted": "₹5,00,000",
        "statusColor": "#22C55E"
      },
      {
        "key": "loanEmiCover",
        "label": "Loan EMI Cover",
        "icon": "account_balance",
        "description": "EMI payment during disability period",
        "covered": false,
        "limit": 0,
        "limitFormatted": "Not covered",
        "statusColor": "#9CA3AF"
      }
    ]
  }
}
```

**All 8 Benefit Keys:**

| Key | Label | Icon | Description |
|-----|-------|------|-------------|
| `educationBenefit` | Education Benefit | `school` | Education continuation for dependent children |
| `loanEmiCover` | Loan EMI Cover | `account_balance` | EMI payment during disability period |
| `ambulanceCharges` | Ambulance Charges | `local_hospital` | Emergency ambulance transportation |
| `transportationOfMortalRemains` | Transport of Mortal Remains | `flight` | Transportation of mortal remains |
| `funeralExpenses` | Funeral Expenses | `church` | Funeral and cremation expenses |
| `homeModification` | Home Modification | `home` | Home accessibility modifications for PTD |
| `vehicleModification` | Vehicle Modification | `directions_car` | Vehicle accessibility modifications for PTD |
| `carriageOfAttendant` | Carriage of Attendant | `person` | Travel expenses for an attendant |

**Rendering:** Use `statusColor` (`#22C55E` green = covered, `#9CA3AF` gray = not covered). Show `limitFormatted` as subtitle.

### 3.5 Exclusions

```json
{
  "exclusions": {
    "standardExclusions": [
      "Suicide or self-inflicted injury",
      "War, invasion, act of foreign enemy",
      "Nuclear reaction, radiation",
      "Participation in criminal activity",
      "While under influence of alcohol/drugs",
      "Mental disorder or insanity",
      "Childbirth or pregnancy",
      "Pre-existing physical defect or infirmity",
      "Aviation other than as fare-paying passenger",
      "Hazardous sports (unless covered)",
      "Venereal diseases or HIV/AIDS"
    ],
    "waitingPeriods": {
      "initialWaiting": { "days": 0, "note": "PA covers accidents from Day 1" },
      "ttdWaiting": { "days": 7, "note": "TTD benefit starts after elimination period" }
    },
    "ageLimits": {
      "minimumEntryAge": 18,
      "maximumEntryAge": 65,
      "maximumRenewalAge": 70
    },
    "occupationRestrictions": []
  }
}
```

**Rendering:** Show `standardExclusions` as a collapsed/expandable list. Show `waitingPeriods` and `ageLimits` as info chips.

### 3.6 Premium Details

```json
{
  "premiumDetails": {
    "basePremium": 5000,
    "basePremiumFormatted": "₹5,000",
    "gstAmount": 900,
    "gstFormatted": "₹900",
    "totalPremium": 5900,
    "totalPremiumFormatted": "₹5,900",
    "premiumFrequency": "annual",
    "premiumFactors": {
      "ageBand": "30-35",
      "occupationClass": "Class I",
      "sumInsuredBand": ""
    },
    "renewalDate": "31-Mar-2025"
  }
}
```

### 3.7 Scoring Engine

See [Section 8](#8-scoring-engine) for full details.

### 3.8 Scenario Simulations

See [Section 9](#9-scenario-simulations) for full details.

### 3.9 Gap Analysis

See [Section 10](#10-gap-analysis) for full details.

### 3.10 Recommendations

See [Section 11](#11-recommendations) for full details.

### 3.11 IPF Integration

See [Section 12](#12-ipf-integration) for full details.

---

## 4. Deep Analysis — Response Schema

The `policyAnalyzer` object contains PA-specific analysis in the `sections` array. Each section follows a standard structure:

```json
{
  "protectionScore": 72,
  "sections": [
    {
      "id": "coverage_snapshot",
      "title": "Your PA Coverage Snapshot",
      "subtitle": "Principal Sum Insured: Rs. 25,00,000",
      "priority": 1,
      "data": { ... }
    }
  ]
}
```

### Section Structure

```json
{
  "id": "<section_id>",
  "title": "Section Title",
  "subtitle": "Brief description",
  "priority": 1,
  "data": { }
}
```

### 4.1 Coverage Snapshot (`coverage_snapshot`, priority: 1)

```json
{
  "sumInsured": 2500000,
  "sumInsuredFormatted": "Rs. 25,00,000",
  "coverageCards": [
    {
      "type": "AD",
      "label": "Accidental Death",
      "covered": true,
      "benefitAmount": 2500000,
      "benefitFormatted": "Rs. 25,00,000",
      "detail": "100% of SI + Double Indemnity"
    },
    {
      "type": "PTD",
      "label": "Permanent Total Disability",
      "covered": true,
      "benefitAmount": 2500000,
      "benefitFormatted": "Rs. 25,00,000",
      "detail": "100% of SI"
    },
    {
      "type": "PPD",
      "label": "Permanent Partial Disability",
      "covered": true,
      "detail": "19 conditions in schedule"
    },
    {
      "type": "TTD",
      "label": "Temporary Total Disability",
      "covered": true,
      "detail": "Rs. 25,000/week for up to 52 weeks"
    },
    {
      "type": "Medical",
      "label": "Medical Expenses",
      "covered": true,
      "detail": "10% of SI"
    }
  ],
  "policyPeriod": "01-Apr-2024 to 31-Mar-2025"
}
```

### 4.2 Scoring Engine (`scoring_engine`, priority: 2)

```json
{
  "overallScore": 72,
  "overallLabel": "Good",
  "overallColor": "#22C55E",
  "scores": [
    {
      "name": "Income Replacement Adequacy",
      "weight": "60%",
      "score": 78,
      "label": "Good",
      "color": "#22C55E",
      "factors": [
        { "name": "Death Benefit vs Income", "score": 22, "maxScore": 35, "detail": "2.5x annual income (₹25,00,000)" },
        { "name": "PTD Benefit vs Income", "score": 8, "maxScore": 25, "detail": "2.5x annual income (₹25,00,000)" },
        { "name": "TTD vs Weekly Income", "score": 20, "maxScore": 20, "detail": "TTD benefit active" },
        { "name": "EMI Protection", "score": 0, "maxScore": 10, "detail": "No EMI protection" },
        { "name": "Double Indemnity", "score": 10, "maxScore": 10, "detail": "Double benefit for public transport" }
      ]
    },
    {
      "name": "Disability Protection Depth",
      "weight": "40%",
      "score": 65,
      "label": "Good",
      "color": "#22C55E",
      "factors": [
        { "name": "PPD Schedule Comprehensiveness", "score": 30, "maxScore": 30, "detail": "19 conditions in schedule" },
        { "name": "TTD Duration", "score": 15, "maxScore": 25, "detail": "52 weeks max" },
        { "name": "TTD Waiting Period", "score": 15, "maxScore": 15, "detail": "7 days" },
        { "name": "Modification Benefits", "score": 0, "maxScore": 15, "detail": "No modification benefits" },
        { "name": "Medical Expenses Coverage", "score": 8, "maxScore": 15, "detail": "10% of SI" }
      ]
    }
  ]
}
```

### 4.3 Gap Analysis (`gap_analysis`, priority: 3)

```json
{
  "totalGaps": 3,
  "highSeverity": 1,
  "mediumSeverity": 1,
  "lowSeverity": 1,
  "gaps": [ ]
}
```

See [Section 10](#10-gap-analysis) for gap object schema.

### 4.4 Key Exclusions (`exclusions`, priority: 4)

```json
{
  "exclusions": [
    { "exclusion": "Suicide or self-inflicted injury", "details": "Suicide or self-inflicted injury" }
  ],
  "ageLimits": {
    "minimumEntryAge": 18,
    "maximumEntryAge": 65,
    "maximumRenewalAge": 70
  },
  "occupationRestrictions": [],
  "importantNote": "PA insurance covers ACCIDENTS only, not illness. Refer to policy document for complete exclusions."
}
```

### 4.5 Recommendations (`recommendations`, priority: 5)

```json
{
  "recommendations": [ ],
  "claimsProcess": {
    "steps": [
      { "step": 1, "title": "Intimate Claim", "description": "Report accident to insurer immediately (within 24-48 hours)" },
      { "step": 2, "title": "File FIR", "description": "Lodge police FIR for accidents (mandatory for death/serious injury)" },
      { "step": 3, "title": "Collect Documents", "description": "Medical reports, hospital bills, FIR copy, ID proof, policy copy" },
      { "step": 4, "title": "Submit Claim Form", "description": "Fill claim form and submit with all documents" },
      { "step": 5, "title": "Claim Settlement", "description": "Insurer verifies and settles claim (typically 30 days)" }
    ],
    "contact": {
      "email": "claims@insurer.com",
      "helpline": "1800-266-9725"
    }
  }
}
```

### 4.6 Assessment (`assessment`, priority: 6)

```json
{
  "status": "ADEQUATE PROTECTION",
  "protectionScore": 72,
  "scoreLabel": "Good",
  "scoreColor": "#22C55E",
  "keyFinding": "PA coverage of Rs. 25,00,000 provides adequate accident protection with some gaps.",
  "recommendedAction": "Increase PA Sum Insured",
  "importantReminder": "PA insurance covers ACCIDENTS only. Ensure you also have Health Insurance for illness coverage and Life Insurance for comprehensive family protection."
}
```

**Assessment Status Thresholds:**

| Score Range | Status | Meaning |
|-------------|--------|---------|
| 80-100 | `WELL PROTECTED` | Comprehensive PA coverage |
| 60-79 | `ADEQUATE PROTECTION` | Adequate with some gaps |
| 40-59 | `BASIC PROTECTION` | Significant gaps to address |
| 0-39 | `LIMITED COVERAGE` | Insufficient protection |

---

## 5. PDF Report — Download Integration

### Trigger

PA reports are generated when the user requests a downloadable PDF report. The backend detects PA policies via keyword matching on `policyType`.

### PDF Sections (in order)

| # | Section | Content |
|---|---------|---------|
| 1 | Header/Cover | EAZR branding, greeting, introduction |
| 2 | Policy Overview | 10-row key details table |
| 3 | Coverage Details | 5 benefit types with status and amounts |
| 4 | PPD Schedule | Full IRDAI table with calculated amounts |
| 5 | Protection Scores | Overall score badge + 2-component breakdown |
| 6 | Gap Analysis | Severity-colored gap rows |
| 7 | Recommendations | Priority-based actions with cost estimates |
| 8 | Additional Benefits | 8 supplementary benefits table |
| 9 | Exclusions | Standard exclusions + disclaimer |
| 10 | Premium Details | Base/GST/total breakdown |

### PDF Styling

| Property | Value |
|----------|-------|
| Page Size | A4 |
| Primary Color | `#00847E` (EAZR Teal) |
| Secondary Color | `#00A99D` |
| Font | DejaVuSans (with Helvetica fallback) |
| Margins | 36pt all sides |

---

## 6. Data Models (Dart)

### Main Response Model

```dart
class PAPolicyDetails {
  final PAEmergencyInfo emergencyInfo;
  final PAPolicyOverview policyOverview;
  final PACoverageDetails coverageDetails;
  final PAAdditionalBenefits additionalBenefits;
  final PAExclusions exclusions;
  final PAPremiumDetails premiumDetails;
  final PAScoringEngine scoringEngine;
  final List<PAScenario> scenarioSimulations;
  final PAGapAnalysis gapAnalysis;
  final PARecommendations recommendations;
  final PAIPFIntegration? ipfIntegration;  // nullable — only when premium >= 5000
}
```

### Emergency Info

```dart
class PAEmergencyInfo {
  final String policyNumber;
  final bool policyNumberCopyable;
  final String claimsHelpline;
  final bool claimsHelplineCallable;
  final String claimsEmail;
  final String policyStatus;       // "active" | "expired" | "cancelled"
  final String policyStatusColor;  // Hex color
}
```

### Policy Overview

```dart
class PAPolicyOverview {
  final String insurerName;
  final String productName;
  final PASubType subType;
  final double principalSumInsured;
  final String principalSumInsuredFormatted;
  final PAValidity policyValidity;
  final int membersCovered;
  final List<PAInsuredMember> insuredMembers;
  final PAGroupDetails? groupDetails;  // nullable — only for GRP_PA
  final PANomination nomination;
}

class PASubType {
  final String code;   // IND_PA, FAM_PA, GRP_PA, PA_MED, STU_PA
  final String label;
  final String color;  // Hex color for badge
  final String icon;   // Material icon name
}

class PAInsuredMember {
  final String name;
  final String relationship;
  final String dateOfBirth;
  final String gender;
  final String occupation;
}
```

### Coverage Details

```dart
class PACoverageDetails {
  final PAAccidentalDeath accidentalDeath;
  final PAPermanentTotalDisability permanentTotalDisability;
  final PAPermanentPartialDisability permanentPartialDisability;
  final PATemporaryTotalDisability temporaryTotalDisability;
  final PAMedicalExpenses medicalExpenses;
}

class PAAccidentalDeath {
  final bool covered;              // Always true for PA
  final int benefitPercentage;     // Usually 100
  final double benefitAmount;
  final String benefitFormatted;
  final String description;
  final PADoubleIndemnity doubleIndemnity;
}

class PADoubleIndemnity {
  final bool applicable;
  final String conditions;         // e.g. "Public transport accident"
  final double doubleAmount;       // 2x benefit
  final String doubleFormatted;
}

class PAPermanentTotalDisability {
  final bool covered;
  final int benefitPercentage;
  final double benefitAmount;
  final String benefitFormatted;
  final String description;
  final List<String> conditionsList;  // PTD qualifying conditions
}

class PAPermanentPartialDisability {
  final bool covered;
  final String benefitType;        // "As per IRDAI schedule"
  final int scheduleCount;
  final List<PPDScheduleItem> schedule;
  final String note;
}

class PPDScheduleItem {
  final String disability;
  final double percentage;
  final double benefitAmount;      // SI * percentage / 100
  final String benefitFormatted;
}

class PATemporaryTotalDisability {
  final bool covered;
  final String benefitType;        // "weekly" | "monthly"
  final double benefitAmount;      // Per week/month
  final String benefitFormatted;
  final int maximumWeeks;          // Max payout duration
  final int waitingPeriodDays;     // Elimination period
  final List<TTDExample> exampleCalculations;  // Empty if not covered
}

class TTDExample {
  final String duration;           // "2 weeks", "4 weeks", etc.
  final double benefit;
  final String formatted;
  final String note;               // "Week 2 only (Week 1 is waiting)"
}

class PAMedicalExpenses {
  final bool covered;
  final String limitType;          // "percentage_of_si" | "fixed_amount"
  final double limitPercentage;
  final double limitAmount;
  final String limitFormatted;
  final String perAccidentOrAnnual;  // "per_accident" | "annual"
}
```

### Additional Benefits

```dart
class PAAdditionalBenefits {
  final List<PABenefitItem> benefits;  // Always 8 items
}

class PABenefitItem {
  final String key;           // e.g. "educationBenefit"
  final String label;         // e.g. "Education Benefit"
  final String icon;          // Material icon name
  final String description;
  final bool covered;
  final double limit;
  final String limitFormatted;  // "₹5,00,000" or "Not covered"
  final String statusColor;     // "#22C55E" (green) or "#9CA3AF" (gray)
}
```

### Scoring Engine

```dart
class PAScoringEngine {
  final int overallScore;       // 0-100
  final String overallLabel;    // "Excellent" | "Good" | "Fair" | "Poor"
  final String overallColor;    // Hex color
  final List<PAScoreComponent> scores;  // Always 2 items
}

class PAScoreComponent {
  final String name;            // "Income Replacement Adequacy" | "Disability Protection Depth"
  final String weight;          // "60%" | "40%"
  final int score;              // 0-100
  final String label;
  final String color;
  final List<PAScoreFactor> factors;  // 5 factors each
}

class PAScoreFactor {
  final String name;
  final int score;
  final int maxScore;
  final String detail;
}
```

### Scenarios

```dart
class PAScenario {
  final String scenarioId;      // PA001, PA002, PA003, PA004
  final String name;
  final String description;
  final String icon;            // Material icon name
  final String severity;        // "high" | "medium" | "low"
  final Map<String, dynamic> inputs;
  final Map<String, dynamic> analysis;
  final Map<String, dynamic> output;
  final String recommendation;
}
```

### Gap Analysis

```dart
class PAGapAnalysis {
  final int totalGaps;
  final int highSeverity;
  final int mediumSeverity;
  final int lowSeverity;
  final List<PAGap> gaps;
}

class PAGap {
  final String gapId;           // G001-G006
  final String severity;        // "high" | "medium" | "low"
  final String severityColor;   // Hex color
  final String title;
  final String description;
  final String impact;
  final String solution;
  final String estimatedCost;
  final bool ipfEligible;
}
```

### Recommendations

```dart
class PARecommendations {
  final int totalRecommendations;
  final List<PARecommendation> recommendations;
}

class PARecommendation {
  final String id;              // "increase_si", "add_ttd", etc.
  final String category;        // "enhancement" | "addon" | "upgrade"
  final int priority;           // 1-5 (1 = highest)
  final String title;
  final String description;
  final String estimatedCost;
  final bool ipfEligible;
  final String icon;            // Material icon name
}
```

### IPF Integration

```dart
class PAIPFIntegration {
  final bool eligible;          // true when premium >= ₹5,000
  final double totalPremium;
  final String totalPremiumFormatted;
  final List<PAIPFOption> options;
  final String cta;             // "Pay in easy EMIs with EAZR"
}

class PAIPFOption {
  final int tenure;             // 3 or 6 months
  final double emiAmount;
  final String emiFormatted;    // "₹1,967/month"
}
```

---

## 7. UI Component Mapping

### Screen Layout (Top to Bottom)

```
┌──────────────────────────────────┐
│  Emergency Info Bar              │  ← Sticky top bar
│  [Policy #] [Helpline] [Status] │
├──────────────────────────────────┤
│  Policy Overview Card            │  ← Insurer + SI + Sub-type badge
│  ┌─ Sub-type Badge ─┐           │
│  │ Individual PA     │           │
│  └───────────────────┘           │
├──────────────────────────────────┤
│  Coverage Details (5 Cards)      │  ← Expandable cards
│  ┌─ AD ──────────── ₹25L ─────┐ │
│  │  Double Indemnity: Yes      │ │
│  ├─ PTD ─────────── ₹25L ─────┤ │
│  │  5 qualifying conditions    │ │
│  ├─ PPD ─────────── Schedule ──┤ │
│  │  19 conditions (expandable) │ │
│  ├─ TTD ─────── ₹25K/week ────┤ │
│  │  Example calculations table │ │
│  ├─ Medical ─────── ₹2.5L ────┤ │
│  │  10% of SI per accident     │ │
│  └─────────────────────────────┘ │
├──────────────────────────────────┤
│  Additional Benefits             │  ← 8-item status list
│  ✓ Education Benefit    ₹5L     │
│  ✗ Loan EMI Cover       —       │
│  ✓ Ambulance Charges    ₹5K     │
│  ...                             │
├──────────────────────────────────┤
│  Exclusions (Collapsed)          │  ← Expandable section
│  11 standard exclusions          │
│  Waiting: 0 days / TTD: 7 days  │
├──────────────────────────────────┤
│  Premium Details                 │  ← Breakdown card
│  Base: ₹5,000 | GST: ₹900      │
│  Total: ₹5,900 (Annual)         │
├──────────────────────────────────┤
│  Protection Score                │  ← Circular gauge + factors
│  ┌─ Overall: 72/100 [Good] ────┐ │
│  │  S1: Income Replacement 60% │ │
│  │  S2: Disability Protect 40% │ │
│  │  Factor breakdown bars      │ │
│  └─────────────────────────────┘ │
├──────────────────────────────────┤
│  Scenario Simulations            │  ← 4 swipeable cards
│  [PA001] [PA002] [PA003] [PA004]│
├──────────────────────────────────┤
│  Gap Analysis                    │  ← Severity-grouped list
│  🔴 2 High | 🟡 1 Medium | ⚪ 1 Low│
│  [Gap cards with actions]        │
├──────────────────────────────────┤
│  Recommendations                 │  ← Priority-ordered actions
│  1. Increase PA Sum Insured      │
│  2. Add TTD Benefit              │
│  ...                             │
├──────────────────────────────────┤
│  IPF Integration                 │  ← CTA card (if eligible)
│  Pay ₹5,900 in 3 EMIs of ₹1,967│
│  [Pay with EAZR]                 │
└──────────────────────────────────┘
```

### Widget Suggestions

| Section | Recommended Widget |
|---------|-------------------|
| Emergency Info | `AppBar` bottom or sticky `Container` |
| Sub-type Badge | `Chip` with `color` and `icon` from sub-type config |
| Coverage Cards | `ExpansionTile` or custom `Card` with expand/collapse |
| PPD Schedule | `DataTable` or `Table` inside expansion |
| TTD Examples | `DataTable` with 5 rows |
| Additional Benefits | `ListView` with `ListTile` + leading icon + trailing status |
| Exclusions | `ExpansionTile` (collapsed by default) |
| Premium | `Card` with 3-row breakdown |
| Protection Score | `CircularProgressIndicator` custom + `LinearProgressIndicator` for factors |
| Scenarios | `PageView` or horizontal `ListView.builder` |
| Gaps | `ListView` grouped by severity, use `severityColor` for left border |
| Recommendations | `ListView` with priority numbers and action buttons |
| IPF | `ElevatedButton` with CTA text |

---

## 8. Scoring Engine

### Algorithm

```
Overall Score = (S1 × 0.60) + (S2 × 0.40)
```

### S1: Income Replacement Adequacy (100 pts)

| # | Factor | Max | Scoring Tiers |
|---|--------|-----|--------------|
| 1 | Death Benefit vs Income | 35 | >=10x: 35, >=7x: 28, >=5x: 22, >=3x: 15, <3x: 8 |
| 2 | PTD Benefit vs Income | 25 | >=10x: 25, >=7x: 20, >=5x: 15, <5x: 8 |
| 3 | TTD vs Weekly Income | 20 | >=0.5x: 20, >=0.3x: 15, >=0.2x: 10, <0.2x: 5, none: 0 |
| 4 | EMI Protection | 10 | Covered: 10, Not: 0 |
| 5 | Double Indemnity | 10 | Applicable: 10, Not: 0 |

**Assumed annual income:** Rs. 10,00,000 (default).

### S2: Disability Protection Depth (100 pts)

| # | Factor | Max | Scoring Tiers |
|---|--------|-----|--------------|
| 1 | PPD Schedule Comprehensiveness | 30 | >=18: 30, >=15: 25, >=10: 18, >0: 10, 0: 5 |
| 2 | TTD Duration | 25 | >=104w: 25, >=78w: 20, >=52w: 15, <52w: 10, none: 0 |
| 3 | TTD Waiting Period | 15 | <=7d: 15, <=14d: 10, >14d: 5, none: 0 |
| 4 | Home/Vehicle Modification | 15 | Home: 8 + Vehicle: 7 = max 15 |
| 5 | Medical Expenses Coverage | 15 | >=40%: 15, >=20%: 12, >=10%: 8, <10%: 5, none: 0 |

### Score Labels

| Score Range | Label | Color |
|-------------|-------|-------|
| 80-100 | Excellent | `#22C55E` (Green) |
| 60-79 | Good | `#22C55E` (Green) |
| 40-59 | Fair | `#F59E0B` (Amber) |
| 0-39 | Poor | `#EF4444` (Red) |

### Flutter Rendering

```dart
// Circular score gauge
Widget buildScoreGauge(int score, String label, String color) {
  return Stack(
    alignment: Alignment.center,
    children: [
      SizedBox(
        width: 120, height: 120,
        child: CircularProgressIndicator(
          value: score / 100,
          strokeWidth: 10,
          color: Color(int.parse(color.replaceFirst('#', '0xFF'))),
          backgroundColor: Colors.grey.shade200,
        ),
      ),
      Column(children: [
        Text('$score', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
        Text(label, style: TextStyle(fontSize: 14)),
      ]),
    ],
  );
}

// Factor progress bars
Widget buildFactorBar(PAScoreFactor factor) {
  return Row(children: [
    Expanded(flex: 3, child: Text(factor.name)),
    Expanded(flex: 5, child: LinearProgressIndicator(
      value: factor.score / factor.maxScore,
    )),
    SizedBox(width: 40, child: Text('${factor.score}/${factor.maxScore}')),
  ]);
}
```

---

## 9. Scenario Simulations

### 4 Scenarios

| ID | Name | Icon | Severity | Description |
|----|------|------|----------|-------------|
| `PA001` | Accidental Death — Family Financial Impact | `family_restroom` | high | Road accident resulting in death |
| `PA002` | Permanent Total Disability — Living with Disability | `accessible` | high | Severe accident causing PTD |
| `PA003` | Temporary Total Disability — 6 Month Recovery | `healing` | medium | Major leg fracture, 6 months off work |
| `PA004` | Permanent Partial Disability — Understanding PPD | `back_hand` | low | Loss of index finger |

### PA001: Accidental Death Response Structure

```json
{
  "scenarioId": "PA001",
  "analysis": {
    "immediateNeeds": {
      "items": [
        { "label": "Funeral Expenses", "amount": 100000 },
        { "label": "Emergency Fund (6 months)", "amount": 2412000 },
        { "label": "Loan Settlement", "amount": 3000000 }
      ],
      "total": 5512000,
      "totalFormatted": "₹55,12,000"
    },
    "ongoingNeeds": {
      "items": [
        { "label": "Income Replacement (15 years)", "amount": 12000000 },
        { "label": "Child Education (2 children)", "amount": 5000000 }
      ],
      "total": 17000000,
      "totalFormatted": "₹1,70,00,000"
    },
    "totalNeed": 22512000,
    "paBenefit": 2500000,
    "otherLifeCover": 10000000,
    "totalCoverage": 12500000,
    "gap": 10012000
  },
  "output": {
    "paProvides": "₹25L to family",
    "combinedProtection": "₹1.3Cr (PA + Life)",
    "gapToTotalNeed": "₹100L gap",
    "hasGap": true
  }
}
```

**Assumed Defaults:**
- Annual income: Rs. 10L
- Outstanding loans: Rs. 30L
- Monthly expenses: 67% of monthly income
- Children: 2
- Life cover: 10x annual income (separate from PA)

### PA003: TTD Timeline (unique to this scenario)

```json
{
  "timeline": [
    { "week": "1", "status": "Waiting period", "benefit": 0, "benefitFormatted": "₹0" },
    { "week": "2-26", "status": "TTD benefit active", "benefit": 25000, "benefitFormatted": "₹25,000/week" },
    { "week": "27+", "status": "Back to work", "benefit": 0, "benefitFormatted": "₹0" }
  ]
}
```

### Flutter Card Layout for Scenarios

```
┌─────────────────────────────────┐
│ 🏥 PA003: TTD - 6 Month Recovery │
│ Severity: ●● Medium              │
├─────────────────────────────────┤
│ Description:                     │
│ Major leg fracture, unable to    │
│ work for 6 months.               │
├─────────────────────────────────┤
│ Income Lost:     ₹5,00,000      │
│ Expenses (6mo):  ₹5,10,000      │
│ TTD Benefit:     ₹6,25,000      │
│ Shortfall:       ₹0 (Covered)   │
├─────────────────────────────────┤
│ Timeline:                        │
│ Week 1    → Waiting period       │
│ Week 2-26 → ₹25,000/week        │
│ Week 27+  → Back to work        │
├─────────────────────────────────┤
│ ✅ TTD coverage is adequate      │
└─────────────────────────────────┘
```

---

## 10. Gap Analysis

### 6 Gap Rules

| Gap ID | Title | Severity | Trigger Condition | IPF Eligible |
|--------|-------|----------|-------------------|-------------|
| `G001` | PA Sum Insured Below Recommended | High | SI < 5x annual income | Yes |
| `G002` | No Temporary Disability Benefit | High | TTD not covered | Yes |
| `G003` | Limited TTD Duration | Medium | TTD max < 52 weeks | No |
| `G004` | No Accident Medical Expenses Cover | Medium | Medical not covered | Yes |
| `G005` | No EMI Protection During Disability | Low | EMI cover not covered | Yes |
| `G006` | No Home/Vehicle Modification Benefits | Low | Both mods not covered | No |

### Gap Object Schema

```json
{
  "gapId": "G001",
  "severity": "high",
  "severityColor": "#EF4444",
  "title": "PA Sum Insured Below Recommended",
  "description": "Current ₹25L = 2.5x income. Recommended: 10x (₹100L)",
  "impact": "Family may face severe financial hardship in case of accidental death or permanent disability",
  "solution": "Increase PA Sum Insured to ₹100L (10x annual income)",
  "estimatedCost": "₹3,000-8,000/year for ₹1Cr PA cover",
  "ipfEligible": true
}
```

### Severity Colors

| Severity | Color | Hex |
|----------|-------|-----|
| High | Red | `#EF4444` |
| Medium | Amber | `#F59E0B` |
| Low | Gray | `#6B7280` |

### Flutter Gap Card

```dart
Widget buildGapCard(PAGap gap) {
  return Card(
    child: Container(
      decoration: BoxDecoration(
        border: Border(left: BorderSide(
          color: Color(int.parse(gap.severityColor.replaceFirst('#', '0xFF'))),
          width: 4,
        )),
      ),
      padding: EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Chip(label: Text(gap.severity.toUpperCase()),
               backgroundColor: Color(int.parse(gap.severityColor.replaceFirst('#', '0xFF'))).withOpacity(0.1)),
          if (gap.ipfEligible) Chip(label: Text('IPF'), backgroundColor: Colors.blue.shade50),
        ]),
        SizedBox(height: 8),
        Text(gap.title, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
        SizedBox(height: 4),
        Text(gap.description),
        Divider(),
        Text('Impact: ${gap.impact}', style: TextStyle(color: Colors.red.shade700)),
        SizedBox(height: 8),
        Text('Solution: ${gap.solution}', style: TextStyle(color: Colors.green.shade700)),
        Text('Est. Cost: ${gap.estimatedCost}', style: TextStyle(color: Colors.grey)),
      ]),
    ),
  );
}
```

---

## 11. Recommendations

### 5 Recommendation Types

| ID | Category | Priority | Icon | Triggered By |
|----|----------|----------|------|-------------|
| `increase_si` | enhancement | 1 | `trending_up` | G001 |
| `add_ttd` | enhancement | 2 | `healing` | G002 |
| `add_medical` | enhancement | 3 | `medical_services` | G004 |
| `add_emi_cover` | addon | 4 | `account_balance` | G005 |
| `family_upgrade` | upgrade | 5 | `family_restroom` | Always (for individual policies) |

### Recommendation Object

```json
{
  "id": "increase_si",
  "category": "enhancement",
  "priority": 1,
  "title": "Increase PA Sum Insured",
  "description": "Increase your PA cover to 10x annual income for adequate protection for your family",
  "estimatedCost": "₹3,000-8,000/year for ₹1Cr",
  "ipfEligible": true,
  "icon": "trending_up"
}
```

**Note:** Recommendations are gap-driven. Only triggered gaps produce recommendations (except `family_upgrade` which always appears for individual policies).

---

## 12. IPF Integration

**Trigger:** `ipfIntegration` is non-null only when `totalPremium >= 5000`.

```json
{
  "ipfIntegration": {
    "eligible": true,
    "totalPremium": 5900,
    "totalPremiumFormatted": "₹5,900",
    "options": [
      { "tenure": 3, "emiAmount": 1967, "emiFormatted": "₹1,967/month" },
      { "tenure": 6, "emiAmount": 983, "emiFormatted": "₹983/month" }
    ],
    "cta": "Pay in easy EMIs with EAZR"
  }
}
```

**Flutter CTA:**

```dart
if (ipfIntegration != null && ipfIntegration!.eligible) {
  ElevatedButton(
    onPressed: () => navigateToIPF(ipfIntegration!.totalPremium),
    style: ElevatedButton.styleFrom(backgroundColor: Color(0xFF00847E)),
    child: Text(ipfIntegration!.cta),
  );
}
```

---

## 13. Color Tokens & Icons

### Brand Colors

| Token | Hex | Usage |
|-------|-----|-------|
| Primary | `#00847E` | Headers, CTAs, primary actions |
| Secondary | `#00A99D` | Accents, secondary elements |
| Dark | `#004D47` | Dark backgrounds |
| Light | `#E6F7F6` | Light backgrounds |

### Status Colors

| Token | Hex | Usage |
|-------|-----|-------|
| Green | `#22C55E` | Active, covered, good scores |
| Amber | `#F59E0B` | Warning, medium severity, fair scores |
| Red | `#EF4444` | Error, high severity, poor scores |
| Blue | `#3B82F6` | Info, Individual PA badge |
| Gray | `#9CA3AF` | Not covered, disabled |

### Material Icons Used

| Icon | Context |
|------|---------|
| `person` | Individual PA |
| `family_restroom` | Family PA, Death scenario |
| `groups` | Group PA |
| `medical_services` | PA with Medical, Medical recommendation |
| `school` | Student PA, Education benefit |
| `account_balance` | EMI cover |
| `local_hospital` | Ambulance charges |
| `flight` | Mortal remains transport |
| `church` | Funeral expenses |
| `home` | Home modification |
| `directions_car` | Vehicle modification |
| `accessible` | PTD scenario |
| `healing` | TTD scenario, TTD recommendation |
| `back_hand` | PPD scenario |
| `trending_up` | Increase SI recommendation |

---

## 14. PPD Schedule Table

The PPD schedule contains up to 19 IRDAI-standard conditions. Render as an expandable data table.

### Default IRDAI PPD Schedule

| # | Disability | % of SI | Example (SI = ₹25L) |
|---|-----------|---------|---------------------|
| 1 | Loss of both hands | 100% | ₹25,00,000 |
| 2 | Loss of both feet | 100% | ₹25,00,000 |
| 3 | Loss of sight of both eyes | 100% | ₹25,00,000 |
| 4 | Loss of one hand and one foot | 100% | ₹25,00,000 |
| 5 | Loss of one hand and sight of one eye | 100% | ₹25,00,000 |
| 6 | Loss of one foot and sight of one eye | 100% | ₹25,00,000 |
| 7 | Loss of one hand | 50% | ₹12,50,000 |
| 8 | Loss of one foot | 50% | ₹12,50,000 |
| 9 | Loss of sight of one eye | 50% | ₹12,50,000 |
| 10 | Loss of thumb | 25% | ₹6,25,000 |
| 11 | Loss of index finger | 10% | ₹2,50,000 |
| 12 | Loss of middle finger | 6% | ₹1,50,000 |
| 13 | Loss of ring finger | 5% | ₹1,25,000 |
| 14 | Loss of little finger | 4% | ₹1,00,000 |
| 15 | Loss of hearing both ears | 50% | ₹12,50,000 |
| 16 | Loss of hearing one ear | 15% | ₹3,75,000 |
| 17 | Loss of big toe | 5% | ₹1,25,000 |
| 18 | Loss of any other toe | 2% | ₹50,000 |
| 19 | Shortening of leg by 5cm+ | 7% | ₹1,75,000 |

### Flutter Table

```dart
DataTable(
  columns: [
    DataColumn(label: Text('Disability')),
    DataColumn(label: Text('% of SI'), numeric: true),
    DataColumn(label: Text('Benefit'), numeric: true),
  ],
  rows: schedule.map((item) => DataRow(cells: [
    DataCell(Text(item.disability)),
    DataCell(Text('${item.percentage}%')),
    DataCell(Text(item.benefitFormatted)),
  ])).toList(),
)
```

---

## 15. Backward Compatibility Notes

### Old vs New Data Format

The backend supports both old (flat) and new (nested) category_data formats:

**Old format (pre-EAZR_04):**
```json
{
  "accidentalDeathCover": "100% of SI",
  "permanentDisabilityCover": "100% of SI",
  "temporaryDisabilityCover": "1% of SI per week",
  "medicalExpensesCover": "10% of SI"
}
```

**New format (EAZR_04):**
```json
{
  "coverageDetails": {
    "accidentalDeath": {
      "covered": true,
      "benefitPercentage": 100,
      "benefitAmount": 2500000,
      "doubleIndemnity": { "applicable": true, "conditions": "..." }
    }
  }
}
```

**Flutter handling:** Always check for the new nested format first. The backend UI builder normalizes both formats into the same output structure, so the Flutter app should always receive the consistent 11-section response regardless of the extraction format.

### Null Safety

Fields that can be null:
- `policyOverview.groupDetails` — only for `GRP_PA`
- `ipfIntegration` — only when premium >= ₹5,000
- `coverageDetails.temporaryTotalDisability.exampleCalculations` — empty array when TTD not covered
- `emergencyInfo.claimsEmail` — may be empty string
- Individual `insuredMembers` fields (DOB, gender, occupation)

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│                  EAZR PA Insurance                    │
│                  Flutter Quick Ref                    │
├─────────────────────────────────────────────────────┤
│ API: POST /api/policy/upload                         │
│ Detection: "personal accident" | "accidental" | "pa "│
│                                                      │
│ Response: 11 sections                                │
│  1. emergencyInfo     → Sticky bar                   │
│  2. policyOverview    → Hero card + sub-type badge   │
│  3. coverageDetails   → 5 expandable cards           │
│  4. additionalBenefits→ 8-item status list           │
│  5. exclusions        → Collapsed list               │
│  6. premiumDetails    → Breakdown card               │
│  7. scoringEngine     → Circular gauge + bars        │
│  8. scenarioSimulations → 4 swipeable cards          │
│  9. gapAnalysis       → Severity-grouped list        │
│ 10. recommendations   → Priority-ordered actions     │
│ 11. ipfIntegration    → CTA (if premium >= ₹5K)     │
│                                                      │
│ Scores: S1 (60%) + S2 (40%) = Overall               │
│ Gaps: G001-G006 (high → medium → low)               │
│ Scenarios: PA001-PA004                               │
│ Recommendations: 1-5 (priority ordered)              │
│                                                      │
│ PDF Report: POST /api/policy/download-report         │
│ Brand Color: #00847E (Teal)                          │
└─────────────────────────────────────────────────────┘
```
