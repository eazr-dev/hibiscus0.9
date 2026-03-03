# EAZR Policy Intelligence Platform
# Category 4: Personal Accident Insurance
# Complete Implementation Specification

**Version**: 1.0 | **Date**: January 2026 | **Category Owner**: PA Insurance Product Team

---

# Table of Contents
1. Category Overview
2. Product Sub-Types
3. Data Extraction Schema (6 Sections)
4. Policy Details Tab Architecture
5. Scoring Engine (2 Scores)
6. Scenario Simulations (4 Scenarios)
7. Gap Analysis Engine (6 Gap Types)
8. Recommendation Engine
9. IPF Integration Points
10. UI/UX Specifications

---

# 1. Category Overview

## 1.1 Business Context

Personal Accident (PA) Insurance is EAZR's **portfolio completion product** - it fills critical gaps that health and life insurance don't cover, particularly for income loss due to accidents.

## 1.2 Strategic Importance

| Metric | Value | EAZR Opportunity |
|--------|-------|------------------|
| Market Size | ₹15,000+ Cr (FY24) | Growing awareness |
| Penetration | <5% of insurable population | Massive untapped |
| Premium Range | ₹1,000 - ₹25,000/year | IPF on ₹5K+ |
| Policy Term | Annual | Regular touchpoint |
| Cross-sell | From Health/Motor | Portfolio completion |

## 1.3 Why PA is Different from Health & Life

```
PA INSURANCE - UNIQUE VALUE PROPOSITION
═══════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  HEALTH INSURANCE                                                   │
│  ✅ Covers: Medical treatment costs                                │
│  ❌ Doesn't cover: Income loss during recovery                     │
│                                                                     │
│  LIFE INSURANCE                                                     │
│  ✅ Covers: Death benefit                                          │
│  ❌ Doesn't cover: Disability (you're alive but can't work)        │
│                                                                     │
│  PERSONAL ACCIDENT fills these gaps:                               │
│  ✅ Accidental Death: Lump sum to family                           │
│  ✅ Permanent Total Disability: 100% Sum Insured                   │
│  ✅ Permanent Partial Disability: % based on schedule              │
│  ✅ Temporary Total Disability: Weekly/monthly benefit             │
│  ✅ Medical Expenses: Accident-related treatment                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 1.4 User Pain Points Addressed

1. **"I have health insurance, why PA?"** → Clear value differentiation
2. **"What if I'm disabled?"** → Disability benefit explanation
3. **"How much will I get for partial disability?"** → PPD schedule clarity
4. **"I'm self-employed, income stops if injured"** → TTD benefit value

---

# 2. Product Sub-Types Supported

| Sub-Type | Code | Description | Key Features | IPF Relevance |
|----------|------|-------------|--------------|---------------|
| Individual PA | IND_PA | Single person comprehensive | All 5 benefits | High (₹5-25K) |
| Family PA | FAM_PA | Family floater | Shared benefits | High (₹10-40K) |
| Group PA | GRP_PA | Employer-provided | Limited customization | Low |
| PA with Medical | PA_MED | PA + Accident medical | Enhanced medical | High |
| Student PA | STU_PA | Education-linked | Low SI, basic cover | Low |

## 2.1 Coverage Types Explained

| Coverage Type | Definition | Benefit Type | Typical % of SI |
|---------------|------------|--------------|-----------------|
| Accidental Death (AD) | Death due to accident | Lump sum | 100% |
| Permanent Total Disability (PTD) | Total loss of function | Lump sum | 100% |
| Permanent Partial Disability (PPD) | Partial loss of function | Lump sum | As per schedule |
| Temporary Total Disability (TTD) | Temporary inability to work | Weekly/Monthly | 1% per week |
| Medical Expenses | Treatment costs | Reimbursement | 10-40% of SI |

---

# 3. Data Extraction Schema

## 3.1 Section 1: Policy Basics

```json
{
  "section": "policy_basics",
  "fields": {
    "policy_number": {
      "type": "string",
      "required": true,
      "confidence_threshold": 0.95
    },
    "insurer_name": {
      "type": "string",
      "required": true,
      "lookup_table": "pa_insurers_master"
    },
    "product_name": {"type": "string", "required": true},
    "policy_type": {
      "type": "enum",
      "values": ["individual", "family", "group"],
      "required": true
    },
    "policy_start_date": {"type": "date", "required": true},
    "policy_end_date": {"type": "date", "required": true},
    "policy_term": {"type": "integer", "unit": "years"},
    "policy_status": {
      "type": "enum",
      "values": ["active", "lapsed", "expired", "claimed"]
    }
  }
}
```

## 3.2 Section 2: Coverage Details

```json
{
  "section": "coverage_details",
  "fields": {
    "sum_insured": {
      "type": "currency",
      "required": true,
      "display_name": "Principal Sum Insured",
      "analysis_benchmarks": {
        "minimum": "annual_income × 5",
        "recommended": "annual_income × 10",
        "optimal": "annual_income × 15"
      }
    },
    "accidental_death": {
      "type": "object",
      "schema": {
        "covered": {"type": "boolean", "required": true},
        "benefit_percentage": {"type": "decimal", "default": 100},
        "benefit_amount": {
          "type": "currency",
          "derived": true,
          "formula": "sum_insured × benefit_percentage / 100"
        },
        "double_indemnity": {
          "type": "object",
          "description": "Double benefit for accidents in public transport",
          "schema": {
            "applicable": "boolean",
            "conditions": "string"
          }
        }
      }
    },
    "permanent_total_disability": {
      "type": "object",
      "schema": {
        "covered": {"type": "boolean", "required": true},
        "benefit_percentage": {"type": "decimal", "default": 100},
        "benefit_amount": {"type": "currency", "derived": true},
        "definition": {
          "type": "string",
          "typical": "Total and irrecoverable loss of both eyes, both hands, both feet, or one hand and one foot"
        },
        "conditions_list": {
          "type": "array",
          "typical_conditions": [
            "Loss of both eyes",
            "Loss of both hands or feet",
            "Loss of one hand and one foot",
            "Total and permanent paralysis",
            "Complete and incurable insanity"
          ]
        }
      }
    },
    "permanent_partial_disability": {
      "type": "object",
      "schema": {
        "covered": {"type": "boolean", "required": true},
        "benefit_type": {"type": "string", "value": "As per schedule"},
        "schedule": {
          "type": "array",
          "irdai_standard_schedule": [
            {"disability": "Loss of both hands or both feet", "percentage": 100},
            {"disability": "Loss of one hand and one foot", "percentage": 100},
            {"disability": "Total loss of sight of both eyes", "percentage": 100},
            {"disability": "Loss of arm at shoulder", "percentage": 70},
            {"disability": "Loss of arm between elbow and shoulder", "percentage": 65},
            {"disability": "Loss of arm at or below elbow", "percentage": 60},
            {"disability": "Loss of hand", "percentage": 55},
            {"disability": "Loss of leg at or above knee", "percentage": 60},
            {"disability": "Loss of leg below knee", "percentage": 50},
            {"disability": "Loss of foot", "percentage": 45},
            {"disability": "Total loss of sight of one eye", "percentage": 50},
            {"disability": "Loss of thumb", "percentage": 25},
            {"disability": "Loss of index finger", "percentage": 10},
            {"disability": "Loss of any other finger", "percentage": 5},
            {"disability": "Loss of big toe", "percentage": 5},
            {"disability": "Loss of any other toe", "percentage": 2},
            {"disability": "Total deafness of both ears", "percentage": 50},
            {"disability": "Total deafness of one ear", "percentage": 15},
            {"disability": "Loss of speech", "percentage": 50}
          ]
        }
      }
    },
    "temporary_total_disability": {
      "type": "object",
      "schema": {
        "covered": {"type": "boolean", "required": true},
        "benefit_type": {
          "type": "enum",
          "values": ["weekly", "monthly"]
        },
        "benefit_percentage": {
          "type": "decimal",
          "common_values": [1, 2],
          "description": "Percentage of SI per week/month"
        },
        "benefit_amount": {
          "type": "currency",
          "derived": true
        },
        "maximum_weeks": {
          "type": "integer",
          "common_values": [52, 100, 104]
        },
        "waiting_period_days": {
          "type": "integer",
          "common_values": [7, 14]
        },
        "definition": {
          "type": "string",
          "typical": "Total inability to engage in gainful employment"
        }
      }
    },
    "medical_expenses": {
      "type": "object",
      "schema": {
        "covered": {"type": "boolean"},
        "limit_type": {
          "type": "enum",
          "values": ["percentage_of_si", "fixed_amount", "actual"]
        },
        "limit_percentage": {"type": "decimal", "common_values": [10, 20, 40]},
        "limit_amount": {"type": "currency"},
        "per_accident_or_annual": {
          "type": "enum",
          "values": ["per_accident", "annual_aggregate"]
        },
        "covers": {
          "type": "array",
          "items": "string",
          "typical": ["Hospitalization", "Surgery", "Doctor fees", "Medicines", "Diagnostics"]
        }
      }
    }
  }
}
```

## 3.3 Section 3: Additional Benefits

```json
{
  "section": "additional_benefits",
  "fields": {
    "education_benefit": {
      "type": "object",
      "schema": {
        "covered": "boolean",
        "benefit_type": {
          "type": "enum",
          "values": ["lump_sum", "annual", "per_child"]
        },
        "benefit_amount": "currency",
        "children_covered": "integer",
        "max_age_of_child": "integer"
      },
      "description": "Education continuation for dependent children if insured dies/disabled"
    },
    "loan_emi_cover": {
      "type": "object",
      "schema": {
        "covered": "boolean",
        "max_months": "integer",
        "max_amount_per_month": "currency",
        "loans_covered": {
          "type": "array",
          "items": "string",
          "typical": ["Home loan", "Car loan", "Personal loan"]
        }
      },
      "description": "EMI payment during TTD period"
    },
    "ambulance_charges": {
      "type": "object",
      "schema": {
        "covered": "boolean",
        "limit": "currency"
      }
    },
    "transportation_of_mortal_remains": {
      "type": "object",
      "schema": {
        "covered": "boolean",
        "limit": "currency"
      }
    },
    "funeral_expenses": {
      "type": "object",
      "schema": {
        "covered": "boolean",
        "limit": "currency"
      }
    },
    "home_modification": {
      "type": "object",
      "schema": {
        "covered": "boolean",
        "limit": "currency",
        "for": "PTD cases requiring home accessibility modifications"
      }
    },
    "vehicle_modification": {
      "type": "object",
      "schema": {
        "covered": "boolean",
        "limit": "currency",
        "for": "PTD cases requiring vehicle modifications"
      }
    },
    "carriage_of_attendant": {
      "type": "object",
      "schema": {
        "covered": "boolean",
        "limit": "currency"
      }
    }
  }
}
```

## 3.4 Section 4: Exclusions

```json
{
  "section": "exclusions",
  "fields": {
    "standard_exclusions": {
      "type": "array",
      "irdai_standard": [
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
      ]
    },
    "waiting_periods": {
      "type": "object",
      "schema": {
        "initial_waiting": {
          "type": "integer",
          "days": 0,
          "note": "PA typically has no initial waiting"
        },
        "ttd_waiting": {
          "type": "integer",
          "days": 7,
          "note": "TTD benefit starts after elimination period"
        }
      }
    },
    "age_limits": {
      "type": "object",
      "schema": {
        "minimum_entry_age": {"type": "integer", "typical": 18},
        "maximum_entry_age": {"type": "integer", "typical": 65},
        "maximum_renewal_age": {"type": "integer", "typical": 70}
      }
    },
    "occupation_restrictions": {
      "type": "object",
      "schema": {
        "excluded_occupations": {
          "type": "array",
          "typical": ["Military personnel", "Miners", "Circus performers", "Explosives handlers"]
        },
        "loading_occupations": {
          "type": "array",
          "typical": ["Factory workers", "Drivers", "Construction workers"]
        }
      }
    }
  }
}
```

## 3.5 Section 5: Premium Details

```json
{
  "section": "premium_details",
  "fields": {
    "base_premium": {"type": "currency", "required": true},
    "gst_amount": {"type": "currency", "rate": 0.18},
    "total_premium": {"type": "currency", "required": true},
    "premium_frequency": {
      "type": "enum",
      "values": ["annual", "single"],
      "note": "PA is typically annual"
    },
    "premium_factors": {
      "type": "object",
      "schema": {
        "age_band": "string",
        "occupation_class": "string",
        "sum_insured_band": "string"
      }
    }
  }
}
```

## 3.6 Section 6: Insured Members (for Family PA)

```json
{
  "section": "insured_members",
  "applicable_for": ["family"],
  "fields": {
    "members": {
      "type": "array",
      "items": {
        "name": {"type": "string", "required": true},
        "relationship": {
          "type": "enum",
          "values": ["self", "spouse", "child", "parent"]
        },
        "date_of_birth": {"type": "date", "required": true},
        "gender": {"type": "enum", "values": ["male", "female", "other"]},
        "occupation": {"type": "string"},
        "individual_si": {"type": "currency"}
      }
    }
  }
}
```

---

# 4. Policy Details Tab Architecture

```
PERSONAL ACCIDENT POLICY DETAILS TAB
════════════════════════════════════

EMERGENCY INFO CARD (Sticky)
├── Policy Number [COPY]
├── Claim Helpline [CALL]
└── Policy Status Badge

POLICY OVERVIEW
├── Insurer Logo + Name
├── Product Name + Type
├── Principal Sum Insured
├── Policy Validity
└── Members Covered (if Family)

COVERAGE DETAILS
├── Accidental Death Card
│   ├── Benefit: 100% of SI = ₹X
│   ├── Double Indemnity: Yes/No
│   └── Conditions
│
├── Permanent Total Disability Card
│   ├── Benefit: 100% of SI = ₹X
│   └── Qualifying conditions list
│
├── Permanent Partial Disability Card
│   ├── As per Schedule
│   └── [VIEW FULL SCHEDULE] (expandable table)
│
├── Temporary Total Disability Card
│   ├── Weekly Benefit: ₹X/week
│   ├── Maximum: Y weeks
│   ├── Waiting Period: 7 days
│   └── Example calculation
│
└── Medical Expenses Card
    ├── Limit: ₹X or Y% of SI
    └── Per accident / Annual

ADDITIONAL BENEFITS
├── Education Benefit
├── Loan EMI Cover
├── Ambulance Charges
├── Home/Vehicle Modification
└── Other benefits

EXCLUSIONS
├── Standard Exclusions (collapsed)
├── Occupation Restrictions
└── Age Limits

PREMIUM DETAILS
├── Premium Breakdown
├── Payment Status
└── Renewal Date
```

---

# 5. Scoring Engine (2 Scores)

## 5.1 Score Overview

| Score | Name | Purpose | Weight |
|-------|------|---------|--------|
| S1 | Income Replacement Adequacy | Death/PTD benefit vs income | 60% |
| S2 | Disability Protection Depth | TTD + PPD comprehensiveness | 40% |

## 5.2 Score 1: Income Replacement Adequacy (0-100)

**Scoring Factors:**

| Factor | Weight | Measurement | Optimal Value |
|--------|--------|-------------|---------------|
| Death Benefit vs Income | 35 pts | SI ÷ Annual Income | 10x income |
| PTD Benefit vs Income | 25 pts | PTD benefit vs income | 10x income |
| TTD vs Weekly Income | 20 pts | Weekly TTD vs weekly income | ≥50% of weekly |
| EMI Coverage | 10 pts | Loan EMI cover present | Yes |
| Double Indemnity | 10 pts | Double for public transport | Yes |

**Algorithm:**
```python
def calculate_income_replacement_score(policy, user_profile):
    score = 0
    annual_income = user_profile.get('annual_income', 1000000)
    weekly_income = annual_income / 52
    
    # Factor 1: Death Benefit vs Income (35 pts)
    death_benefit = policy['accidental_death']['benefit_amount']
    income_multiple = death_benefit / annual_income
    
    if income_multiple >= 10: score += 35
    elif income_multiple >= 7: score += 28
    elif income_multiple >= 5: score += 22
    elif income_multiple >= 3: score += 15
    else: score += 8
    
    # Factor 2: PTD Benefit (25 pts)
    ptd_benefit = policy['permanent_total_disability']['benefit_amount']
    ptd_multiple = ptd_benefit / annual_income
    
    if ptd_multiple >= 10: score += 25
    elif ptd_multiple >= 7: score += 20
    elif ptd_multiple >= 5: score += 15
    else: score += 8
    
    # Factor 3: TTD vs Weekly Income (20 pts)
    if policy['temporary_total_disability']['covered']:
        ttd_weekly = policy['temporary_total_disability']['benefit_amount']
        ttd_ratio = ttd_weekly / weekly_income
        
        if ttd_ratio >= 0.5: score += 20
        elif ttd_ratio >= 0.3: score += 15
        elif ttd_ratio >= 0.2: score += 10
        else: score += 5
    
    # Factor 4: EMI Coverage (10 pts)
    if policy.get('additional_benefits', {}).get('loan_emi_cover', {}).get('covered'):
        score += 10
    
    # Factor 5: Double Indemnity (10 pts)
    if policy['accidental_death'].get('double_indemnity', {}).get('applicable'):
        score += 10
    
    return round(score, 1)
```

## 5.3 Score 2: Disability Protection Depth (0-100)

**Scoring Factors:**

| Factor | Weight | Measurement | Optimal Value |
|--------|--------|-------------|---------------|
| PPD Schedule Comprehensiveness | 30 pts | Number of conditions | IRDAI full schedule |
| TTD Duration | 25 pts | Maximum weeks covered | 104 weeks |
| TTD Waiting Period | 15 pts | Elimination period | 7 days |
| Home/Vehicle Modification | 15 pts | Coverage for PTD needs | Yes |
| Medical Expenses Coverage | 15 pts | % of SI for treatment | ≥20% |

**Algorithm:**
```python
def calculate_disability_protection_score(policy):
    score = 0
    
    # Factor 1: PPD Schedule (30 pts)
    ppd_conditions = len(policy['permanent_partial_disability'].get('schedule', []))
    if ppd_conditions >= 18: score += 30  # Full IRDAI schedule
    elif ppd_conditions >= 15: score += 25
    elif ppd_conditions >= 10: score += 18
    else: score += 10
    
    # Factor 2: TTD Duration (25 pts)
    if policy['temporary_total_disability']['covered']:
        max_weeks = policy['temporary_total_disability'].get('maximum_weeks', 52)
        if max_weeks >= 104: score += 25
        elif max_weeks >= 78: score += 20
        elif max_weeks >= 52: score += 15
        else: score += 10
    
    # Factor 3: TTD Waiting Period (15 pts)
    waiting = policy['temporary_total_disability'].get('waiting_period_days', 14)
    if waiting <= 7: score += 15
    elif waiting <= 14: score += 10
    else: score += 5
    
    # Factor 4: Home/Vehicle Modification (15 pts)
    additional = policy.get('additional_benefits', {})
    if additional.get('home_modification', {}).get('covered'): score += 8
    if additional.get('vehicle_modification', {}).get('covered'): score += 7
    
    # Factor 5: Medical Expenses (15 pts)
    medical = policy.get('medical_expenses', {})
    if medical.get('covered'):
        pct = medical.get('limit_percentage', 0)
        if pct >= 40: score += 15
        elif pct >= 20: score += 12
        elif pct >= 10: score += 8
        else: score += 5
    
    return round(score, 1)
```

---

# 6. Scenario Simulations

## 6.1 Scenario Library (4 Scenarios)

| ID | Scenario | Key Insight | Gap Identified |
|----|----------|-------------|----------------|
| PA001 | Accidental Death | Family financial impact | SI adequacy |
| PA002 | Permanent Total Disability | Living with disability | PTD + modification benefits |
| PA003 | Temporary Disability - 6 Months | Income loss recovery | TTD adequacy |
| PA004 | Partial Disability - Finger Loss | PPD calculation | Schedule understanding |

## 6.2 Scenario PA001: Accidental Death

```json
{
  "scenario_id": "PA001",
  "name": "Accidental Death - Family Financial Impact",
  "description": "Road accident resulting in death. How is family protected?",
  
  "inputs": {
    "annual_income": 1200000,
    "outstanding_loans": 3000000,
    "monthly_expenses": 80000,
    "children": 2,
    "pa_sum_insured": 5000000
  },
  
  "analysis": {
    "immediate_needs": {
      "funeral_expenses": 100000,
      "emergency_fund_6_months": 480000,
      "loan_settlement": 3000000,
      "total_immediate": 3580000
    },
    "ongoing_needs": {
      "income_replacement_15_years": {
        "annual_need": 960000,
        "inflation_adjusted_pv": 10000000
      },
      "child_education_2_children": 5000000,
      "total_ongoing": 15000000
    },
    "total_need": 18580000,
    "pa_benefit": 5000000,
    "other_life_cover": 10000000,
    "total_coverage": 15000000,
    "gap": 3580000
  },
  
  "output": {
    "pa_provides": "₹50L to family",
    "combined_protection": "₹1.5Cr (PA + Life)",
    "gap_to_total_need": "₹35.8L gap",
    "recommendation": "Consider increasing PA to ₹1Cr"
  }
}
```

## 6.3 Scenario PA003: Temporary Disability - 6 Months

```json
{
  "scenario_id": "PA003",
  "name": "Temporary Total Disability - 6 Month Recovery",
  "description": "Major leg fracture, unable to work for 6 months",
  
  "inputs": {
    "monthly_income": 100000,
    "monthly_emi": 35000,
    "monthly_expenses": 60000,
    "pa_ttd_benefit": 10000,
    "ttd_waiting_days": 7,
    "ttd_max_weeks": 52
  },
  
  "analysis": {
    "income_loss": {
      "duration_months": 6,
      "total_income_lost": 600000
    },
    "fixed_expenses_continue": {
      "emi_6_months": 210000,
      "other_expenses_6_months": 360000,
      "total_needed": 570000
    },
    "pa_ttd_benefit": {
      "after_waiting_period": "Week 2 onwards",
      "weeks_covered": 23,
      "benefit_per_week": 10000,
      "total_benefit": 230000
    },
    "gap": {
      "need_minus_benefit": 340000,
      "message": "₹3.4L shortfall during recovery"
    }
  },
  
  "output_display": {
    "timeline": [
      {"week": "1", "status": "Waiting period", "benefit": 0},
      {"week": "2-24", "status": "TTD benefit active", "benefit": 10000},
      {"week": "25+", "status": "Back to work", "benefit": 0}
    ],
    "total_benefit": 230000,
    "gap": 340000,
    "recommendation": "Consider higher TTD benefit or EMI protection add-on"
  }
}
```

## 6.4 Scenario PA004: Partial Disability Calculation

```json
{
  "scenario_id": "PA004",
  "name": "Permanent Partial Disability - Understanding PPD",
  "description": "Industrial accident causing loss of index finger",
  
  "inputs": {
    "pa_sum_insured": 2500000,
    "disability": "Loss of index finger"
  },
  
  "ppd_schedule_lookup": {
    "disability": "Loss of index finger",
    "percentage": 10,
    "benefit_calculation": "SI × 10% = ₹2,50,000"
  },
  
  "educational_content": {
    "how_ppd_works": [
      "PPD pays a percentage of Sum Insured based on disability type",
      "Percentages are set by IRDAI schedule",
      "Multiple disabilities can be claimed (up to 100%)",
      "Benefit is lump sum, not recurring"
    ],
    "common_ppd_amounts": {
      "loss_of_thumb": "25% = ₹6.25L",
      "loss_of_one_eye_sight": "50% = ₹12.5L",
      "loss_of_hearing_both_ears": "50% = ₹12.5L",
      "loss_of_hand": "55% = ₹13.75L"
    }
  }
}
```

---

# 7. Gap Analysis Engine

## 7.1 Gap Categories (6 Types)

| Gap ID | Gap Type | Severity | Trigger |
|--------|----------|----------|---------|
| G001 | SI Below Income Multiple | High | SI < 5x annual income |
| G002 | No TTD Benefit | High | TTD not covered |
| G003 | Low TTD Duration | Medium | Max weeks < 52 |
| G004 | No Medical Expenses | Medium | Medical not covered |
| G005 | No EMI Protection | Low | EMI cover absent |
| G006 | No Modification Benefits | Low | Home/vehicle mod absent |

## 7.2 Gap Detection Rules

```python
class PAGapAnalyzer:
    
    def analyze_gaps(self, policy, user_profile):
        gaps = []
        annual_income = user_profile.get('annual_income', 1000000)
        
        # G001: SI Below Income Multiple
        si = policy['sum_insured']
        income_multiple = si / annual_income
        
        if income_multiple < 5:
            gaps.append({
                'gap_id': 'G001',
                'severity': 'high',
                'title': 'PA Sum Insured Below Recommended',
                'description': f'Current ₹{si/100000:.0f}L = {income_multiple:.1f}x income. Recommended: 10x',
                'impact': 'Family may face financial hardship in case of accident',
                'solution': f'Increase to ₹{annual_income*10/100000:.0f}L (10x income)',
                'estimated_premium': '₹3,000-8,000/year for ₹1Cr',
                'ipf_eligible': True
            })
        
        # G002: No TTD Benefit
        if not policy['temporary_total_disability'].get('covered'):
            gaps.append({
                'gap_id': 'G002',
                'severity': 'high',
                'title': 'No Temporary Disability Benefit',
                'description': 'No income replacement during recovery period',
                'impact': f'If disabled for 6 months, lose ₹{annual_income/2:,.0f} income',
                'solution': 'Add TTD benefit',
                'ipf_eligible': True
            })
        
        # G003: Low TTD Duration
        elif policy['temporary_total_disability'].get('maximum_weeks', 52) < 52:
            max_weeks = policy['temporary_total_disability']['maximum_weeks']
            gaps.append({
                'gap_id': 'G003',
                'severity': 'medium',
                'title': 'Limited TTD Duration',
                'description': f'TTD limited to {max_weeks} weeks',
                'impact': 'Major injuries may need longer recovery',
                'solution': 'Look for plan with 52+ weeks TTD'
            })
        
        # G004: No Medical Expenses
        if not policy.get('medical_expenses', {}).get('covered'):
            gaps.append({
                'gap_id': 'G004',
                'severity': 'medium',
                'title': 'No Accident Medical Expenses Cover',
                'description': 'Treatment costs not covered under PA',
                'impact': 'Out-of-pocket medical expenses for accident treatment',
                'solution': 'Add medical expenses benefit'
            })
        
        # G005: No EMI Protection
        has_loans = user_profile.get('total_liabilities', 0) > 0
        if has_loans and not policy.get('additional_benefits', {}).get('loan_emi_cover', {}).get('covered'):
            gaps.append({
                'gap_id': 'G005',
                'severity': 'low',
                'title': 'No EMI Protection During Disability',
                'description': 'Loan EMIs continue during disability period',
                'impact': 'EMI burden when income stops',
                'solution': 'Add EMI protection benefit'
            })
        
        return sorted(gaps, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}.get(x['severity'], 3))
```

---

# 8. Recommendation Engine

## 8.1 PA Recommendations

```python
PA_RECOMMENDATIONS = {
    'increase_si': {
        'category': 'enhancement',
        'title': 'Increase PA Sum Insured',
        'template': 'Increase from ₹{current}L to ₹{recommended}L (10x income)',
        'ipf_eligible': True,
        'priority': 1
    },
    'add_ttd': {
        'category': 'enhancement',
        'title': 'Add Temporary Disability Benefit',
        'template': 'Get ₹{weekly}/week during recovery',
        'ipf_eligible': True,
        'priority': 2
    },
    'add_medical': {
        'category': 'enhancement',
        'title': 'Add Medical Expenses Cover',
        'template': 'Cover accident treatment costs up to ₹{limit}',
        'ipf_eligible': True,
        'priority': 3
    },
    'add_emi_cover': {
        'category': 'addon',
        'title': 'Add EMI Protection',
        'template': 'Protect loan EMIs during disability',
        'ipf_eligible': True,
        'priority': 4
    },
    'family_upgrade': {
        'category': 'upgrade',
        'title': 'Upgrade to Family PA',
        'template': 'Cover spouse and children under family floater',
        'ipf_eligible': True,
        'priority': 5
    }
}
```

---

# 9. IPF Integration Points

## 9.1 IPF Touchpoints

| Touchpoint | Trigger | CTA |
|------------|---------|-----|
| Gap Analysis | SI increase needed | "Finance upgraded PA" |
| Cross-sell | Health/Life customer without PA | "Add PA, finance together" |
| Renewal | PA due > ₹5K | "Pay in EMIs" |
| Recommendations | Enhancement suggested | "Add with EAZR EMI" |

---

# 10. UI/UX Specifications

## 10.1 PPD Schedule Display

```
┌─────────────────────────────────────────────────────────────────────┐
│ 📋 PERMANENT PARTIAL DISABILITY SCHEDULE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Your Sum Insured: ₹25,00,000                                       │
│                                                                     │
│ Disability                              % of SI    Benefit Amount  │
│ ─────────────────────────────────────────────────────────────────  │
│ Both hands or both feet                   100%       ₹25,00,000    │
│ One hand and one foot                     100%       ₹25,00,000    │
│ Total sight loss both eyes                100%       ₹25,00,000    │
│ Arm at shoulder                            70%       ₹17,50,000    │
│ Arm between elbow and shoulder             65%       ₹16,25,000    │
│ Arm at or below elbow                      60%       ₹15,00,000    │
│ Hand                                       55%       ₹13,75,000    │
│ Leg at or above knee                       60%       ₹15,00,000    │
│ Leg below knee                             50%       ₹12,50,000    │
│ Foot                                       45%       ₹11,25,000    │
│ Sight of one eye                           50%       ₹12,50,000    │
│ Thumb                                      25%        ₹6,25,000    │
│ Index finger                               10%        ₹2,50,000    │
│ Other finger (each)                         5%        ₹1,25,000    │
│ Hearing both ears                          50%       ₹12,50,000    │
│ Hearing one ear                            15%        ₹3,75,000    │
│ Speech                                     50%       ₹12,50,000    │
│                                                                     │
│ Note: Multiple disabilities can be claimed up to 100% total        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 10.2 TTD Benefit Calculator

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🧮 TTD BENEFIT CALCULATOR                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Your TTD Benefit: ₹10,000/week                                     │
│ Maximum Duration: 52 weeks                                         │
│ Waiting Period: 7 days                                             │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐    │
│ │ If disabled for:                                            │    │
│ │                                                             │    │
│ │ 2 weeks  →  ₹10,000  (Week 2 only, Week 1 is waiting)      │    │
│ │ 4 weeks  →  ₹30,000  (Weeks 2-4)                           │    │
│ │ 3 months →  ₹1,10,000 (Weeks 2-12)                         │    │
│ │ 6 months →  ₹2,40,000 (Weeks 2-25)                         │    │
│ │ 1 year   →  ₹5,10,000 (Weeks 2-52, max)                    │    │
│ └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│ Compare with your weekly income: ₹23,000                           │
│ TTD covers: 43% of weekly income                                   │
│                                                                     │
│ 💡 Consider increasing SI for higher weekly benefit                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

# Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | EAZR Product | Initial spec |

---

**END OF PERSONAL ACCIDENT INSURANCE SPECIFICATION**

*EAZR Digipayments Private Limited - Confidential*
