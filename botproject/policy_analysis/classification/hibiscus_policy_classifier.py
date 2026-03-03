"""
────────────────────────────────────────────────────────────────────────────────
│                    HIBISCUS POLICY CLASSIFIER v2.0                         │
│                    EAZR AI — Production Classification Engine              │
│                                                                            │
│  Architecture: 3-Tier Cascading Hybrid Pipeline                            │
│  Tier 1: Rule-based (UIN + Product Name + Deterministic Fields) → ~40%     │
│  Tier 2: Multi-Signal Scoring (Weighted Feature Matching) → ~40%           │
│  Tier 3: LLM Chain-of-Thought (Ambiguous/Edge Cases) → ~20%               │
│                                                                            │
│  Handles: All 12 IRDAI insurance categories (Life, Health, Motor,         │
│           Fire, Marine, Travel, Home, Liability, Engineering, Crop,       │
│           Personal Accident, Miscellaneous) — 69+ sub-categories          │
│  Edge Cases: Super Top-Up, Combo Products, Group Policies, CI Standalone   │
│  DB Output: Maps to insurance_india PostgreSQL schema (category/subcat)    │
│                                                                            │
│  © 2026 EAZR Digipayments Pvt Ltd. All rights reserved.                   │
────────────────────────────────────────────────────────────────────────────────
"""

import re
import json
import logging
from enum import Enum
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field

# ───────────────────────────────────────────────────────────────────────────────
# SECTION 1: ENUMS & DATA STRUCTURES
# ───────────────────────────────────────────────────────────────────────────────

class PolicyCategory(Enum):
    """Level 1: Life vs General/Non-Life vs Health (matches DB company_type_enum)"""
    LIFE = "life"
    GENERAL = "general"
    HEALTH = "health"
    UNKNOWN = "unknown"


class PolicyType(Enum):
    """Level 2: Specific product type — maps to DB subcategories via POLICY_TYPE_TO_DB_MAPPING"""

    # ── Health Insurance (11 subcategories) ──
    HEALTH = "health"
    HEALTH_FAMILY_FLOATER = "health_family_floater"
    HEALTH_SUPER_TOPUP = "health_super_topup"
    HEALTH_GROUP = "health_group"
    HEALTH_CRITICAL_ILLNESS = "health_critical_illness"
    HEALTH_SENIOR_CITIZEN = "health_senior_citizen"
    HEALTH_AROGYA_SANJEEVANI = "health_arogya_sanjeevani"
    HEALTH_HOSPITAL_CASH = "health_hospital_cash"
    HEALTH_DISEASE_SPECIFIC = "health_disease_specific"
    HEALTH_MATERNITY = "health_maternity"
    HEALTH_PA = "health_pa"

    # ── Motor Insurance (7 subcategories + generic) ──
    MOTOR = "motor"
    MOTOR_COMPREHENSIVE = "motor_comprehensive"
    MOTOR_THIRD_PARTY = "motor_third_party"
    MOTOR_TWO_WHEELER = "motor_two_wheeler"
    MOTOR_TWO_WHEELER_TP = "motor_two_wheeler_tp"
    MOTOR_COMMERCIAL = "motor_commercial"
    MOTOR_STANDALONE_OD = "motor_standalone_od"
    MOTOR_ADDON = "motor_addon"

    # ── Fire Insurance (4 subcategories + generic) ──
    FIRE = "fire"
    FIRE_IAR = "fire_iar"
    FIRE_BUSINESS_INTERRUPTION = "fire_business_interruption"
    FIRE_BURGLARY = "fire_burglary"

    # ── Marine Insurance (4 subcategories + generic) ──
    MARINE = "marine"
    MARINE_CARGO = "marine_cargo"
    MARINE_HULL = "marine_hull"
    MARINE_INLAND = "marine_inland"
    MARINE_LIABILITY = "marine_liability"

    # ── Travel Insurance (4 subcategories + generic) ──
    TRAVEL = "travel"
    TRAVEL_DOMESTIC = "travel_domestic"
    TRAVEL_INTERNATIONAL = "travel_international"
    TRAVEL_STUDENT = "travel_student"
    TRAVEL_CORPORATE = "travel_corporate"

    # ── Home Insurance (4 subcategories + generic) ──
    HOME = "home"
    HOME_BHARAT_GRIHA_RAKSHA = "home_bharat_griha_raksha"
    HOME_STRUCTURE = "home_structure"
    HOME_CONTENTS = "home_contents"
    HOME_PACKAGE = "home_package"

    # ── Liability Insurance (7 subcategories + generic) ──
    LIABILITY = "liability"
    LIABILITY_PUBLIC = "liability_public"
    LIABILITY_PRODUCT = "liability_product"
    LIABILITY_PROFESSIONAL = "liability_professional"
    LIABILITY_DNO = "liability_dno"
    LIABILITY_CYBER = "liability_cyber"
    LIABILITY_WORKMEN = "liability_workmen"
    LIABILITY_CGL = "liability_cgl"

    # ── Engineering Insurance (5 subcategories + generic) ──
    ENGINEERING = "engineering"
    ENGINEERING_CAR = "engineering_car"
    ENGINEERING_EAR = "engineering_ear"
    ENGINEERING_MACHINERY = "engineering_machinery"
    ENGINEERING_ELECTRONIC = "engineering_electronic"
    ENGINEERING_BOILER = "engineering_boiler"

    # ── Crop Insurance (3 subcategories + generic) ──
    CROP = "crop"
    CROP_PMFBY = "crop_pmfby"
    CROP_WEATHER = "crop_weather"
    CROP_LIVESTOCK = "crop_livestock"

    # ── Personal Accident (3 subcategories) ──
    PERSONAL_ACCIDENT = "personal_accident"
    PA_GROUP = "pa_group"
    PA_PMSBY = "pa_pmsby"

    # ── Miscellaneous (6 subcategories + generic) ──
    MISC = "misc"
    MISC_SURETY = "misc_surety"
    MISC_CREDIT = "misc_credit"
    MISC_CYBER_RETAIL = "misc_cyber_retail"
    MISC_FIDELITY = "misc_fidelity"
    MISC_SME = "misc_sme"
    MISC_SHOPKEEPER = "misc_shopkeeper"

    # ── Life Insurance (11 subcategories + generic) ──
    LIFE_TERM = "life_term"
    LIFE_TERM_ROP = "life_term_rop"
    LIFE_ULIP = "life_ulip"
    LIFE_ENDOWMENT = "life_endowment"
    LIFE_MONEY_BACK = "life_money_back"
    LIFE_WHOLE = "life_whole"
    LIFE_PENSION = "life_pension"
    LIFE_CHILD = "life_child"
    LIFE_GROUP = "life_group"
    LIFE_MICRO = "life_micro"
    LIFE_SAVINGS = "life_savings"
    LIFE_GENERIC = "life_generic"

    # ── Fallback ──
    UNKNOWN = "unknown"


class ConfidenceLevel(Enum):
    """Classification confidence routing"""
    DEFINITIVE = "definitive"        # > 0.95 — UIN/product name match
    HIGH = "high"                    # 0.85-0.95 — Strong multi-signal
    MODERATE = "moderate"            # 0.70-0.85 — Needs audit flag
    LOW = "low"                      # 0.50-0.70 — Route to LLM
    AMBIGUOUS = "ambiguous"          # < 0.50 — Route to human review


@dataclass
class ClassificationResult:
    """Complete classification output"""
    policy_type: PolicyType
    policy_category: PolicyCategory
    confidence: float
    confidence_level: ConfidenceLevel
    tier_used: int                          # Which tier resolved it (1, 2, or 3)
    primary_signals: List[str]              # What signals drove the classification
    secondary_labels: List[PolicyType]      # For combo products (riders, add-ons)
    requires_human_review: bool = False
    classification_reasoning: str = ""
    raw_scores: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_type": self.policy_type.value,
            "policy_category": self.policy_category.value,
            "confidence": round(self.confidence, 4),
            "confidence_level": self.confidence_level.value,
            "tier_used": self.tier_used,
            "primary_signals": self.primary_signals,
            "secondary_labels": [l.value for l in self.secondary_labels],
            "requires_human_review": self.requires_human_review,
            "classification_reasoning": self.classification_reasoning,
            "raw_scores": {k: round(v, 4) for k, v in self.raw_scores.items()},
            "warnings": self.warnings,
        }

    def to_db_fields(self) -> Dict[str, Any]:
        """
        Returns classification output mapped to DB schema fields.
        All strings match EXACTLY what's in 01_foundation.sql and 01_enums.sql.
        """
        mapping = POLICY_TYPE_TO_DB_MAPPING.get(self.policy_type, {})
        return {
            "category_name": mapping.get("category_name", "Unknown"),
            "subcategory_name": mapping.get("subcategory_name", "Unknown"),
            "product_type": mapping.get("default_product_type", "individual"),
            "linked_type": mapping.get("default_linked_type", "not_applicable"),
            "par_type": mapping.get("default_par_type", "not_applicable"),
            "company_type": mapping.get("company_type", "general"),
            "confidence": self._map_confidence_to_db(),
        }

    def _map_confidence_to_db(self) -> str:
        """Map float confidence to DB confidence_enum values."""
        if self.confidence >= 0.95:
            return "verified"
        elif self.confidence >= 0.85:
            return "high"
        elif self.confidence >= 0.70:
            return "medium"
        elif self.confidence >= 0.50:
            return "low"
        return "not_available"

    def get_analysis_type(self) -> str:
        """
        Returns the canonical analysis type string used by the Analysis Framework.
        Maps granular types back to the 12 core categories.
        """
        ANALYSIS_TYPE_MAP = {
            # Health
            PolicyType.HEALTH: "health", PolicyType.HEALTH_FAMILY_FLOATER: "health",
            PolicyType.HEALTH_SUPER_TOPUP: "health", PolicyType.HEALTH_GROUP: "health",
            PolicyType.HEALTH_CRITICAL_ILLNESS: "health", PolicyType.HEALTH_SENIOR_CITIZEN: "health",
            PolicyType.HEALTH_AROGYA_SANJEEVANI: "health", PolicyType.HEALTH_HOSPITAL_CASH: "health",
            PolicyType.HEALTH_DISEASE_SPECIFIC: "health", PolicyType.HEALTH_MATERNITY: "health",
            PolicyType.HEALTH_PA: "health",
            # Motor
            PolicyType.MOTOR: "motor", PolicyType.MOTOR_COMPREHENSIVE: "motor",
            PolicyType.MOTOR_THIRD_PARTY: "motor", PolicyType.MOTOR_TWO_WHEELER: "motor",
            PolicyType.MOTOR_TWO_WHEELER_TP: "motor", PolicyType.MOTOR_COMMERCIAL: "motor",
            PolicyType.MOTOR_STANDALONE_OD: "motor", PolicyType.MOTOR_ADDON: "motor",
            # Fire
            PolicyType.FIRE: "fire", PolicyType.FIRE_IAR: "fire",
            PolicyType.FIRE_BUSINESS_INTERRUPTION: "fire", PolicyType.FIRE_BURGLARY: "fire",
            # Marine
            PolicyType.MARINE: "marine", PolicyType.MARINE_CARGO: "marine",
            PolicyType.MARINE_HULL: "marine", PolicyType.MARINE_INLAND: "marine",
            PolicyType.MARINE_LIABILITY: "marine",
            # Travel
            PolicyType.TRAVEL: "travel", PolicyType.TRAVEL_DOMESTIC: "travel",
            PolicyType.TRAVEL_INTERNATIONAL: "travel", PolicyType.TRAVEL_STUDENT: "travel",
            PolicyType.TRAVEL_CORPORATE: "travel",
            # Home
            PolicyType.HOME: "home", PolicyType.HOME_BHARAT_GRIHA_RAKSHA: "home",
            PolicyType.HOME_STRUCTURE: "home", PolicyType.HOME_CONTENTS: "home",
            PolicyType.HOME_PACKAGE: "home",
            # Liability
            PolicyType.LIABILITY: "liability", PolicyType.LIABILITY_PUBLIC: "liability",
            PolicyType.LIABILITY_PRODUCT: "liability", PolicyType.LIABILITY_PROFESSIONAL: "liability",
            PolicyType.LIABILITY_DNO: "liability", PolicyType.LIABILITY_CYBER: "liability",
            PolicyType.LIABILITY_WORKMEN: "liability", PolicyType.LIABILITY_CGL: "liability",
            # Engineering
            PolicyType.ENGINEERING: "engineering", PolicyType.ENGINEERING_CAR: "engineering",
            PolicyType.ENGINEERING_EAR: "engineering", PolicyType.ENGINEERING_MACHINERY: "engineering",
            PolicyType.ENGINEERING_ELECTRONIC: "engineering", PolicyType.ENGINEERING_BOILER: "engineering",
            # Crop
            PolicyType.CROP: "crop", PolicyType.CROP_PMFBY: "crop",
            PolicyType.CROP_WEATHER: "crop", PolicyType.CROP_LIVESTOCK: "crop",
            # Personal Accident
            PolicyType.PERSONAL_ACCIDENT: "personal_accident",
            PolicyType.PA_GROUP: "personal_accident", PolicyType.PA_PMSBY: "personal_accident",
            # Miscellaneous
            PolicyType.MISC: "miscellaneous", PolicyType.MISC_SURETY: "miscellaneous",
            PolicyType.MISC_CREDIT: "miscellaneous", PolicyType.MISC_CYBER_RETAIL: "miscellaneous",
            PolicyType.MISC_FIDELITY: "miscellaneous", PolicyType.MISC_SME: "miscellaneous",
            PolicyType.MISC_SHOPKEEPER: "miscellaneous",
            # Life
            PolicyType.LIFE_TERM: "life", PolicyType.LIFE_TERM_ROP: "life",
            PolicyType.LIFE_ULIP: "life", PolicyType.LIFE_ENDOWMENT: "life",
            PolicyType.LIFE_MONEY_BACK: "life", PolicyType.LIFE_WHOLE: "life",
            PolicyType.LIFE_PENSION: "life", PolicyType.LIFE_CHILD: "life",
            PolicyType.LIFE_GROUP: "life", PolicyType.LIFE_MICRO: "life",
            PolicyType.LIFE_SAVINGS: "life", PolicyType.LIFE_GENERIC: "life",
        }
        return ANALYSIS_TYPE_MAP.get(self.policy_type, "unknown")

    def get_legacy_type(self) -> str:
        """
        Returns backward-compatible type string matching the old
        identify_policy_type_deepseek() output.
        Maps to: "health", "motor", "life", "travel", "pa", "fire", "marine",
                 "home", "liability", "engineering", "crop", "misc", "unknown"
        """
        analysis = self.get_analysis_type()
        # Legacy mapping: "personal_accident" → "pa", "miscellaneous" → "misc"
        _LEGACY_REMAP = {"personal_accident": "pa", "miscellaneous": "misc"}
        return _LEGACY_REMAP.get(analysis, analysis)


# ───────────────────────────────────────────────────────────────────────────────
# SECTION 1B: DB SCHEMA MAPPING
# Every string below EXACTLY matches 01_foundation.sql and 01_enums.sql.
# ───────────────────────────────────────────────────────────────────────────────

POLICY_TYPE_TO_DB_MAPPING: Dict[str, Dict[str, str]] = {
    # ── Life Insurance ──
    PolicyType.LIFE_TERM: {
        "category_name": "Life Insurance", "subcategory_name": "Term Life Insurance",
        "default_product_type": "individual", "default_linked_type": "non_linked",
        "default_par_type": "non_participating", "company_type": "life",
    },
    PolicyType.LIFE_TERM_ROP: {
        "category_name": "Life Insurance", "subcategory_name": "Term with Return of Premium",
        "default_product_type": "individual", "default_linked_type": "non_linked",
        "default_par_type": "non_participating", "company_type": "life",
    },
    PolicyType.LIFE_ENDOWMENT: {
        "category_name": "Life Insurance", "subcategory_name": "Endowment Plans",
        "default_product_type": "individual", "default_linked_type": "non_linked",
        "default_par_type": "participating", "company_type": "life",
    },
    PolicyType.LIFE_MONEY_BACK: {
        "category_name": "Life Insurance", "subcategory_name": "Money-Back Plans",
        "default_product_type": "individual", "default_linked_type": "non_linked",
        "default_par_type": "participating", "company_type": "life",
    },
    PolicyType.LIFE_WHOLE: {
        "category_name": "Life Insurance", "subcategory_name": "Whole Life Insurance",
        "default_product_type": "individual", "default_linked_type": "non_linked",
        "default_par_type": "participating", "company_type": "life",
    },
    PolicyType.LIFE_ULIP: {
        "category_name": "Life Insurance", "subcategory_name": "ULIP - Unit Linked Plans",
        "default_product_type": "individual", "default_linked_type": "linked",
        "default_par_type": "not_applicable", "company_type": "life",
    },
    PolicyType.LIFE_CHILD: {
        "category_name": "Life Insurance", "subcategory_name": "Child Plans",
        "default_product_type": "individual", "default_linked_type": "non_linked",
        "default_par_type": "participating", "company_type": "life",
    },
    PolicyType.LIFE_PENSION: {
        "category_name": "Life Insurance", "subcategory_name": "Pension / Annuity Plans",
        "default_product_type": "individual", "default_linked_type": "non_linked",
        "default_par_type": "non_participating", "company_type": "life",
    },
    PolicyType.LIFE_GROUP: {
        "category_name": "Life Insurance", "subcategory_name": "Group Term Life",
        "default_product_type": "group", "default_linked_type": "non_linked",
        "default_par_type": "non_participating", "company_type": "life",
    },
    PolicyType.LIFE_MICRO: {
        "category_name": "Life Insurance", "subcategory_name": "Micro Insurance (Life)",
        "default_product_type": "micro", "default_linked_type": "non_linked",
        "default_par_type": "non_participating", "company_type": "life",
    },
    PolicyType.LIFE_SAVINGS: {
        "category_name": "Life Insurance", "subcategory_name": "Savings Plans",
        "default_product_type": "individual", "default_linked_type": "non_linked",
        "default_par_type": "participating", "company_type": "life",
    },
    PolicyType.LIFE_GENERIC: {
        "category_name": "Life Insurance", "subcategory_name": "Term Life Insurance",
        "default_product_type": "individual", "default_linked_type": "non_linked",
        "default_par_type": "non_participating", "company_type": "life",
    },

    # ── Health Insurance ──
    PolicyType.HEALTH: {
        "category_name": "Health Insurance", "subcategory_name": "Individual Health Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_FAMILY_FLOATER: {
        "category_name": "Health Insurance", "subcategory_name": "Family Floater Health Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_CRITICAL_ILLNESS: {
        "category_name": "Health Insurance", "subcategory_name": "Critical Illness Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_SENIOR_CITIZEN: {
        "category_name": "Health Insurance", "subcategory_name": "Senior Citizen Health Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_GROUP: {
        "category_name": "Health Insurance", "subcategory_name": "Group Health Insurance",
        "default_product_type": "group", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_SUPER_TOPUP: {
        "category_name": "Health Insurance", "subcategory_name": "Top-Up / Super Top-Up",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_HOSPITAL_CASH: {
        "category_name": "Health Insurance", "subcategory_name": "Hospital Daily Cash",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_AROGYA_SANJEEVANI: {
        "category_name": "Health Insurance", "subcategory_name": "Arogya Sanjeevani (Standard)",
        "default_product_type": "standard", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_DISEASE_SPECIFIC: {
        "category_name": "Health Insurance", "subcategory_name": "Disease-Specific Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_MATERNITY: {
        "category_name": "Health Insurance", "subcategory_name": "Maternity Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },
    PolicyType.HEALTH_PA: {
        "category_name": "Health Insurance", "subcategory_name": "Personal Accident (Health)",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "health",
    },

    # ── Motor Insurance ──
    PolicyType.MOTOR: {
        "category_name": "Motor Insurance", "subcategory_name": "Private Car - Comprehensive",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MOTOR_COMPREHENSIVE: {
        "category_name": "Motor Insurance", "subcategory_name": "Private Car - Comprehensive",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MOTOR_THIRD_PARTY: {
        "category_name": "Motor Insurance", "subcategory_name": "Private Car - Third Party Only",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MOTOR_TWO_WHEELER: {
        "category_name": "Motor Insurance", "subcategory_name": "Two-Wheeler - Comprehensive",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MOTOR_TWO_WHEELER_TP: {
        "category_name": "Motor Insurance", "subcategory_name": "Two-Wheeler - Third Party Only",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MOTOR_COMMERCIAL: {
        "category_name": "Motor Insurance", "subcategory_name": "Commercial Vehicle Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MOTOR_STANDALONE_OD: {
        "category_name": "Motor Insurance", "subcategory_name": "Standalone Own Damage",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MOTOR_ADDON: {
        "category_name": "Motor Insurance", "subcategory_name": "Motor Add-Ons / Riders",
        "default_product_type": "add_on", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },

    # ── Fire Insurance ──
    PolicyType.FIRE: {
        "category_name": "Fire Insurance", "subcategory_name": "Standard Fire & Special Perils",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.FIRE_IAR: {
        "category_name": "Fire Insurance", "subcategory_name": "Industrial All Risk (IAR)",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.FIRE_BUSINESS_INTERRUPTION: {
        "category_name": "Fire Insurance", "subcategory_name": "Business Interruption",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.FIRE_BURGLARY: {
        "category_name": "Fire Insurance", "subcategory_name": "Burglary Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },

    # ── Marine Insurance ──
    PolicyType.MARINE: {
        "category_name": "Marine Insurance", "subcategory_name": "Marine Cargo",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MARINE_CARGO: {
        "category_name": "Marine Insurance", "subcategory_name": "Marine Cargo",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MARINE_HULL: {
        "category_name": "Marine Insurance", "subcategory_name": "Marine Hull",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MARINE_INLAND: {
        "category_name": "Marine Insurance", "subcategory_name": "Inland Transit",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MARINE_LIABILITY: {
        "category_name": "Marine Insurance", "subcategory_name": "Marine Liability",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },

    # ── Travel Insurance ──
    PolicyType.TRAVEL: {
        "category_name": "Travel Insurance", "subcategory_name": "International Travel Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.TRAVEL_DOMESTIC: {
        "category_name": "Travel Insurance", "subcategory_name": "Domestic Travel Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.TRAVEL_INTERNATIONAL: {
        "category_name": "Travel Insurance", "subcategory_name": "International Travel Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.TRAVEL_STUDENT: {
        "category_name": "Travel Insurance", "subcategory_name": "Student Travel Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.TRAVEL_CORPORATE: {
        "category_name": "Travel Insurance", "subcategory_name": "Corporate / Multi-Trip Travel",
        "default_product_type": "group", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },

    # ── Home Insurance ──
    PolicyType.HOME: {
        "category_name": "Home Insurance", "subcategory_name": "Householder Package Policy",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.HOME_BHARAT_GRIHA_RAKSHA: {
        "category_name": "Home Insurance", "subcategory_name": "Bharat Griha Raksha (Standard)",
        "default_product_type": "standard", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.HOME_STRUCTURE: {
        "category_name": "Home Insurance", "subcategory_name": "Home Structure Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.HOME_CONTENTS: {
        "category_name": "Home Insurance", "subcategory_name": "Home Contents Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.HOME_PACKAGE: {
        "category_name": "Home Insurance", "subcategory_name": "Householder Package Policy",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },

    # ── Liability Insurance ──
    PolicyType.LIABILITY: {
        "category_name": "Liability Insurance", "subcategory_name": "Commercial General Liability (CGL)",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.LIABILITY_PUBLIC: {
        "category_name": "Liability Insurance", "subcategory_name": "Public Liability Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.LIABILITY_PRODUCT: {
        "category_name": "Liability Insurance", "subcategory_name": "Product Liability Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.LIABILITY_PROFESSIONAL: {
        "category_name": "Liability Insurance", "subcategory_name": "Professional Indemnity / E&O",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.LIABILITY_DNO: {
        "category_name": "Liability Insurance", "subcategory_name": "Directors & Officers Liability",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.LIABILITY_CYBER: {
        "category_name": "Liability Insurance", "subcategory_name": "Cyber Liability Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.LIABILITY_WORKMEN: {
        "category_name": "Liability Insurance", "subcategory_name": "Workmen Compensation",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.LIABILITY_CGL: {
        "category_name": "Liability Insurance", "subcategory_name": "Commercial General Liability (CGL)",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },

    # ── Engineering Insurance ──
    PolicyType.ENGINEERING: {
        "category_name": "Engineering Insurance", "subcategory_name": "Contractor All Risk (CAR)",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.ENGINEERING_CAR: {
        "category_name": "Engineering Insurance", "subcategory_name": "Contractor All Risk (CAR)",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.ENGINEERING_EAR: {
        "category_name": "Engineering Insurance", "subcategory_name": "Erection All Risk (EAR)",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.ENGINEERING_MACHINERY: {
        "category_name": "Engineering Insurance", "subcategory_name": "Machinery Breakdown",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.ENGINEERING_ELECTRONIC: {
        "category_name": "Engineering Insurance", "subcategory_name": "Electronic Equipment Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.ENGINEERING_BOILER: {
        "category_name": "Engineering Insurance", "subcategory_name": "Boiler & Pressure Plant",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },

    # ── Crop Insurance ──
    PolicyType.CROP: {
        "category_name": "Crop Insurance", "subcategory_name": "PMFBY - Crop Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.CROP_PMFBY: {
        "category_name": "Crop Insurance", "subcategory_name": "PMFBY - Crop Insurance",
        "default_product_type": "group", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.CROP_WEATHER: {
        "category_name": "Crop Insurance", "subcategory_name": "Weather-Based Crop Insurance",
        "default_product_type": "group", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.CROP_LIVESTOCK: {
        "category_name": "Crop Insurance", "subcategory_name": "Livestock Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },

    # ── Personal Accident ──
    PolicyType.PERSONAL_ACCIDENT: {
        "category_name": "Personal Accident", "subcategory_name": "Individual Personal Accident",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.PA_GROUP: {
        "category_name": "Personal Accident", "subcategory_name": "Group Personal Accident",
        "default_product_type": "group", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.PA_PMSBY: {
        "category_name": "Personal Accident", "subcategory_name": "PMSBY",
        "default_product_type": "group", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },

    # ── Miscellaneous ──
    PolicyType.MISC: {
        "category_name": "Miscellaneous", "subcategory_name": "SME Package Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MISC_SURETY: {
        "category_name": "Miscellaneous", "subcategory_name": "Surety Bond Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MISC_CREDIT: {
        "category_name": "Miscellaneous", "subcategory_name": "Credit Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MISC_CYBER_RETAIL: {
        "category_name": "Miscellaneous", "subcategory_name": "Cyber Insurance (Retail)",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MISC_FIDELITY: {
        "category_name": "Miscellaneous", "subcategory_name": "Fidelity Guarantee",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MISC_SME: {
        "category_name": "Miscellaneous", "subcategory_name": "SME Package Insurance",
        "default_product_type": "individual", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
    PolicyType.MISC_SHOPKEEPER: {
        "category_name": "Miscellaneous", "subcategory_name": "Shopkeeper Insurance",
        "default_product_type": "standard", "default_linked_type": "not_applicable",
        "default_par_type": "not_applicable", "company_type": "general",
    },
}


# ───────────────────────────────────────────────────────────────────────────────
# SECTION 2: KNOWLEDGE BASE — DISCRIMINATIVE FEATURES
# This is the core intelligence. Every entry is battle-tested against real
# Indian insurance policy documents.
# ───────────────────────────────────────────────────────────────────────────────

# —— 2A: IRDAI STANDARDIZED PRODUCT NAMES (100% classification confidence) ——

IRDAI_STANDARD_PRODUCTS = {
    # Product name → PolicyType (these are identical across ALL insurers)
    "arogya sanjeevani": PolicyType.HEALTH_AROGYA_SANJEEVANI,
    "saral jeevan bima": PolicyType.LIFE_TERM,
    "saral suraksha bima": PolicyType.PERSONAL_ACCIDENT,
    "bharat yatra suraksha": PolicyType.TRAVEL_DOMESTIC,
    "bharat griha raksha": PolicyType.HOME_BHARAT_GRIHA_RAKSHA,
    "bharat sookshma udyam suraksha": PolicyType.MISC_SHOPKEEPER,
    "bharat laghu udyam suraksha": PolicyType.MISC_SME,
    "saral pension": PolicyType.LIFE_PENSION,
}

# —— 2B: INSURER PRODUCT NAME PATTERNS ——
# These are high-confidence product name → type mappings based on
# real product names from major Indian insurers.

PRODUCT_NAME_PATTERNS = {
    # ——— TRAVEL (nearly always contains "travel" or destination refs) ———
    PolicyType.TRAVEL: [
        r"\btravel\s*(guard|companion|elite|prime|protect|insurance|suraksha|yatra)\b",
        r"\b(overseas|international|abroad)\s*(travel|medical|insurance)\b",
        r"\b(explorer|travelsure|globetrotter|wanderlust)\b",
        r"\bbharat\s*yatra\b",
        r"\b(schengen|visa)\s*(travel|insurance|compliant)\b",
        r"\bstudent\s*(travel|overseas|abroad)\b",
        r"\b(inbound|outbound)\s*travel\b",
        r"\btrip\s*(insurance|protect|shield|secure)\b",
    ],

    # ——— HEALTH (branded product families from major insurers) ———
    PolicyType.HEALTH: [
        # HDFC ERGO
        r"\boptima\s*(secure|lite|super\s*secure|restore|senior)\b",
        r"\bmedisure\b",
        # Star Health
        r"\bstar\s*(comprehensive|family\s*health\s*optima|health\s*assure|women\s*care|senior\s*citizen)\b",
        r"\bstar\s*(cardiac\s*care|cancer\s*care)\b",
        # Care Health
        r"\bcare\s*(supreme|advantage|plus|freedom|joy|classic|heart)\b",
        # Tata AIG
        r"\bmedicare\s*(protect|premier)?\b",
        # Niva Bupa
        r"\b(reassure|health\s*companion|heartbeat|aspire)\b",
        # ICICI Lombard
        r"\b(complete\s*health|health\s*booster|il\s*take\s*care)\b",
        # Bajaj Allianz
        r"\b(health\s*guard|health\s*ensure|health\s*infinity)\b",
        # Digit
        r"\bdigit\s*health\b",
        # IRDAI Standard
        r"\barogya\s*sanjeevani\b",
        # Generic strong indicators
        r"\b(mediclaim|health\s*insurance\s*policy|indemnity\s*health)\b",
    ],

    # ——— MOTOR (generic names but strong pattern) ———
    PolicyType.MOTOR: [
        r"\b(car|motor|vehicle|two\s*wheeler|bike|auto|commercial\s*vehicle)\s*insurance\b",
        r"\b(comprehensive|third\s*party|own\s*damage)\s*(motor|car|vehicle|policy)\b",
        r"\bpackage\s*policy\s*-?\s*(private\s*car|two\s*wheeler|commercial\s*vehicle)\b",
        r"\bmotor\s*(od|tp|package|floater)\b",
    ],

    # ——— LIFE: TERM ———
    PolicyType.LIFE_TERM: [
        r"\b(click\s*2\s*protect|smart\s*term|e\s*?shield|tech\s*term|i?\s*term)\b",
        r"\b(amulya\s*jeevan|jeevan\s*amar|saral\s*jeevan)\b",
        r"\bterm\s*(plan|insurance|life|protect|assure)\b",
        r"\bpure\s*(term|protection|life\s*cover)\b",
        r"\bonline\s*term\b",
    ],

    # ——— LIFE: ULIP ———
    PolicyType.LIFE_ULIP: [
        r"\b(click\s*2\s*wealth|smart\s*wealth\s*builder|signature|wealth\s*plus)\b",
        r"\b(unit\s*linked|ulip)\b",
        r"\b(nav|net\s*asset\s*value)\b.*\b(fund|unit)\b",
        r"\b(equity|debt|balanced)\s*fund\s*(option|choice)\b",
        r"\bfund\s*(switch|value|management\s*charge)\b",
    ],

    # ——— LIFE: ENDOWMENT ———
    PolicyType.LIFE_ENDOWMENT: [
        r"\b(sanchay|jeevan\s*labh|jeevan\s*anand|jeevan\s*lakshya|jeevan\s*umang)\b",
        r"\bendowment\s*(plan|policy|assurance)\b",
        r"\b(money\s*back|moneyback)\s*(plan|policy)\b",
        r"\bguaranteed\s*(return|income|savings|maturity)\b",
        r"\bparticipating\s*(policy|plan|endowment)\b",
    ],

    # ——— PERSONAL ACCIDENT ———
    PolicyType.PERSONAL_ACCIDENT: [
        r"\b(personal\s*accident|pa\s*cover|pa\s*policy|pa\s*insurance)\b",
        r"\bsaral\s*suraksha\s*bima\b",
        r"\b(accidental\s*death|accident\s*guard|accident\s*shield)\b",
        r"\b(group\s*personal\s*accident|gpa)\b",
        r"\bpradhan\s*mantri\s*suraksha\s*bima\s*yojana\b",
        r"\bpmsby\b",
    ],

    # ——— FIRE INSURANCE ———
    PolicyType.FIRE: [
        r"\b(standard\s*fire|sfsp|fire\s*and\s*special\s*perils?)\b",
        r"\b(fire\s*insurance|fire\s*policy)\b",
        r"\bindustrial\s*all\s*risk\b",
        r"\b(business\s*interruption|consequential\s*loss)\s*(policy|insurance)\b",
        r"\b(burglary|housebreaking)\s*(insurance|policy)\b",
        r"\b(mega\s*risk|property\s*all\s*risk)\s*(insurance|policy)\b",
    ],

    # ——— MARINE INSURANCE ———
    PolicyType.MARINE: [
        r"\bmarine\s*(cargo|hull|insurance|policy|transit)\b",
        r"\b(inland\s*transit|inland\s*cargo)\s*(insurance|policy)\b",
        r"\bicc\s*(a|b|c)\s*(clause)?\b",
        r"\b(open\s*cover|open\s*policy|declaration\s*policy)\s*(marine)?\b",
        r"\bprotection\s*(&|and)\s*indemnity\b",
        r"\bbill\s*of\s*lading\b",
    ],

    # ——— HOME INSURANCE ———
    PolicyType.HOME: [
        r"\b(home\s*insurance|home\s*protect|home\s*shield)\b",
        r"\bbharat\s*griha\s*raksha\b",
        r"\bhouseholder\s*(comprehensive|package|policy)\b",
        r"\b(dwelling|residential)\s*(insurance|policy|cover)\b",
        r"\b(home\s*structure|home\s*content|home\s*building)\s*(insurance|policy|cover)?\b",
    ],

    # ——— LIABILITY INSURANCE ———
    PolicyType.LIABILITY: [
        r"\b(public\s*liability|pl\s*insurance|pl\s*policy)\b",
        r"\b(product\s*liability)\s*(insurance|policy)?\b",
        r"\b(professional\s*indemnity|pi\s*policy|errors?\s*(&|and)\s*omissions?)\b",
        r"\b(directors?\s*(&|and)\s*officers?|d\s*&\s*o)\s*(liability|insurance|policy)?\b",
        r"\b(cyber\s*liability|cyber\s*insurance)\s*(policy)?\b",
        r"\b(workmen|workers?)\s*(compensation|comp)\b",
        r"\b(commercial\s*general\s*liability|cgl)\b",
        r"\b(umbrella|excess)\s*liability\b",
        r"\b(medical\s*malpractice)\s*(insurance|policy)?\b",
    ],

    # ——— ENGINEERING INSURANCE ———
    PolicyType.ENGINEERING: [
        r"\b(contractor\s*all\s*risk|car\s*policy|car\s*insurance)\b",
        r"\b(erection\s*all\s*risk|ear\s*policy|ear\s*insurance)\b",
        r"\b(machinery\s*breakdown|mb\s*policy|mb\s*insurance)\b",
        r"\b(electronic\s*equipment)\s*(insurance|policy)\b",
        r"\b(boiler|pressure\s*plant)\s*(insurance|policy|explosion)\b",
        r"\b(loss\s*of\s*profits?)\s*(following|due\s*to)\s*(machinery|mb)\b",
        r"\b(it\s*infrastructure)\s*(insurance|policy)\b",
    ],

    # ——— CROP INSURANCE ———
    PolicyType.CROP: [
        r"\bpmfby\b",
        r"\bpradhan\s*mantri\s*fasal\s*bima\b",
        r"\b(crop|fasal)\s*(insurance|bima|suraksha)\b",
        r"\b(weather[\s-]*based|wbcis|rwbcis)\s*(crop)?\s*(insurance)?\b",
        r"\b(livestock|cattle|poultry)\s*(insurance|policy)\b",
        r"\b(kharif|rabi)\s*(season|crop)\b",
    ],

    # ——— MISCELLANEOUS ———
    PolicyType.MISC: [
        r"\b(surety\s*bond)\s*(insurance|policy|guarantee)?\b",
        r"\b(fidelity\s*guarantee|fidelity\s*insurance)\b",
        r"\b(trade\s*credit|credit\s*insurance)\b",
        r"\b(cyber\s*sachet|retail\s*cyber)\b",
        r"\b(jeweller|jeweler)s?\s*(block|insurance)\b",
        r"\b(political\s*risk)\s*(insurance|policy)\b",
        r"\b(bankers?\s*indemnity)\b",
        r"\bbharat\s*(sookshma|laghu)\s*udyam\b",
        r"\b(sme|shopkeeper|office)\s*(package|insurance|policy)\b",
        r"\b(gadget\s*insurance|mobile\s*insurance|device\s*protect)\b",
    ],
}

# —— 2C: DETERMINISTIC FIELD SIGNATURES ——
# Fields whose MERE PRESENCE definitively classifies the document.
# These are structural signals, not content signals.

DETERMINISTIC_FIELDS = {
    PolicyType.TRAVEL: [
        r"\bpassport\s*(no|number|#)\b",
        r"\bdestination\s*(country|countries)\b",
        r"\b(departure|arrival|travel)\s*date\b",
        r"\b(inbound|outbound)\s*journey\b",
        r"\bvisa\s*(type|number|compliance)\b",
        r"\bschengen\b",
    ],
    PolicyType.MOTOR: [
        r"\b(registration\s*(no|number)|reg\.?\s*no)\b",
        r"\b(engine\s*no|engine\s*number)\b",
        r"\b(chassis\s*no|chassis\s*number)\b",
        r"\b(make\s*[&/]\s*model|vehicle\s*make)\b",
        r"\bidv\b",
        r"\b(cubic\s*capacity|cc)\s*:?\s*\d+\b",
        r"\brto\s*(code|zone|location)\b",
    ],
    PolicyType.LIFE_ULIP: [
        r"\bnet\s*asset\s*value\b",
        r"\bfund\s*switch(ing)?\b",
        r"\b(premium\s*allocation|policy\s*admin)\s*charge\b",
        r"\b(equity|debt|balanced|money\s*market)\s*fund\b",
        r"\b5[\s-]*year\s*lock[\s-]*in\b",
    ],
    PolicyType.FIRE: [
        r"\bsum\s*insured\s*(on|for)\s*(building|stock|machinery|plant)\b",
        r"\bfire\s*and\s*special\s*perils?\b",
        r"\b(riot|strike|malicious\s*damage)\s*(cover|extension)\b",
        r"\b(earthquake|flood|storm)\s*(extension|peril|cover)\b",
        r"\b(spontaneous\s*combustion|forest\s*fire)\b",
    ],
    PolicyType.MARINE: [
        r"\bvessel\s*(name|type|tonnage)\b",
        r"\bvoyage\s*(from|to|route)\b",
        r"\bbill\s*of\s*lading\b",
        r"\b(port\s*of|loading|discharge)\s*(embarkation|loading|discharge)\b",
        r"\bicc\s*[abc]\b",
        r"\b(cargo|consignment)\s*(description|value)\b",
    ],
    PolicyType.HOME: [
        r"\b(dwelling|carpet\s*area|built[\s-]*up\s*area)\b",
        r"\b(construction\s*type|building\s*age|year\s*of\s*construction)\b",
        r"\b(structure|content)\s*(sum\s*insured|value|cover)\b",
        r"\b(burglar|theft)\s*(alarm|protection)\b",
    ],
    PolicyType.LIABILITY: [
        r"\b(indemnity|liability)\s*limit\b",
        r"\bretroactive\s*date\b",
        r"\bjurisdiction\s*(clause|territory)\b",
        r"\b(each\s*occurrence|aggregate)\s*limit\b",
        r"\b(defence|legal)\s*costs?\s*(in\s*addition|within)\b",
    ],
    PolicyType.ENGINEERING: [
        r"\b(project|contract)\s*(value|sum\s*insured)\b",
        r"\b(testing|commissioning)\s*period\b",
        r"\b(maintenance|defects?\s*liability)\s*period\b",
        r"\b(erection|construction)\s*period\b",
        r"\b(principal|contractor|sub[\s-]*contractor)\b",
    ],
    PolicyType.CROP: [
        r"\b(kharif|rabi)\s*(season|crop)?\b",
        r"\b(survey\s*number|plot\s*number|khasra)\b",
        r"\b(crop\s*name|crop\s*type|crop\s*sown)\b",
        r"\b(hectare|acre|bigha)\s*:?\s*\d\b",
        r"\b(notified\s*area|gram\s*panchayat)\b",
    ],
}

# —— 2D: DISCRIMINATIVE PHRASES — The Core Classification Intelligence ——
# Each phrase has a WEIGHT (how discriminative it is) and can appear in
# ONLY ONE category (exclusive) or be shared with context.
#
# Weight scale:
#   1.0  = DEFINITIVE (appears ONLY in this category, period)
#   0.8  = VERY STRONG (95%+ exclusive to this category)
#   0.6  = STRONG (80%+ exclusive, rarely bleeds into other categories)
#   0.4  = MODERATE (useful signal but shared vocabulary)
#   0.2  = WEAK (helpful with other signals, noisy alone)
#  -0.5  = NEGATIVE (presence REDUCES likelihood of this category)

DISCRIMINATIVE_FEATURES: Dict[PolicyType, List[Tuple[str, float]]] = {

    # ─────────────────────────────────────────────────────────────────────
    # TRAVEL INSURANCE — 40+ discriminative phrases
    # Key insight: Travel's uniqueness is trip-bound, destination-bound,
    # and short-duration. Health is ongoing, renewal-based, India-centric.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.TRAVEL: [
        # —— DEFINITIVE (1.0) — NEVER appear in Health/Motor/Life/PA ——
        (r"\btrip\s*cancellation\b", 1.0),
        (r"\btrip\s*interruption\b", 1.0),
        (r"\btrip\s*curtailment\b", 1.0),
        (r"\btrip\s*delay\b", 1.0),
        (r"\bbaggage\s*(loss|delay|damage|theft)\b", 1.0),
        (r"\bflight\s*delay\s*(compensation|benefit|cover)\b", 1.0),
        (r"\bmissed\s*(connection|departure|flight)\b", 1.0),
        (r"\bhijack\s*(distress|allowance|benefit)\b", 1.0),
        (r"\bloss\s*of\s*passport\b", 1.0),
        (r"\brepatriation\s*of\s*(mortal\s*)?remains\b", 1.0),
        (r"\b(medical\s*)?evacuation\s*(to|from)\s*(nearest|home\s*country)\b", 1.0),
        (r"\bcompassionate\s*visit\b", 1.0),
        (r"\bhome\s*burglary\s*(while|during)\s*travel\b", 1.0),
        (r"\bsponsor\s*protection\b", 1.0),
        (r"\bstudy\s*abroad\b", 1.0),
        (r"\b(adventure|winter)\s*sports\s*(cover|rider|add[\s-]?on)\b", 1.0),
        (r"\bpersonal\s*liability\s*abroad\b", 1.0),
        (r"\bbharat\s*yatra\s*suraksha\b", 1.0),
        (r"\bper\s*trip\b", 1.0),
        (r"\btravel\s*document\s*loss\b", 1.0),
        (r"\b(single|multi|annual)\s*trip\b", 1.0),

        # —— VERY STRONG (0.8) — Rarely in other categories ——
        (r"\b(USD|EUR|GBP)\s*\d", 0.8),
        (r"\$\s*\d{2,3},?\d{3}", 0.8),  # Dollar amounts like $50,000
        (r"\u20ac\s*\d{2,3},?\d{3}", 0.8),   # Euro amounts
        (r"\bschengen\s*(complian|visa|requirement)\b", 0.8),
        (r"\bdestination\s*(country|zone|region)\b", 0.8),
        (r"\b(inbound|outbound)\s*(travel|journey|trip)\b", 0.8),
        (r"\bemergency\s*medical\s*evacuation\b", 0.8),
        (r"\bmedical\s*expenses\s*(overseas|abroad|outside\s*india)\b", 0.8),
        (r"\btravel\s*insurance\b", 0.8),
        (r"\bperiod\s*of\s*(travel|trip|journey)\b", 0.8),
        (r"\b(worldwide|global)\s*(excl|incl|excluding|including)\s*(usa|us|canada)\b", 0.8),

        # —— STRONG (0.6) — Mostly travel but can appear in health context ——
        (r"\bpersonal\s*liability\b", 0.6),
        (r"\bemergency\s*cash\s*advance\b", 0.6),
        (r"\b(country|countries)\s*covered\b", 0.6),
        (r"\bdeductible\s*per\s*(claim|incident|event)\b", 0.6),

        # —— NEGATIVE SIGNALS — If present, REDUCES Travel likelihood ——
        (r"\broom\s*rent\b", -0.5),
        (r"\bcumulative\s*bonus\b", -0.5),
        (r"\bno\s*claim\s*bonus\b", -0.5),
        (r"\bday\s*care\s*procedure\b", -0.5),
        (r"\bayush\b", -0.5),
        (r"\bdomiciliary\s*hospitali[sz]ation\b", -0.5),
        (r"\brestoration\s*benefit\b", -0.5),
        (r"\blifetime\s*renewab\b", -0.5),
        (r"\brenewal\s*(premium|notice|date)\b", -0.5),
        (r"\btpa\b", -0.5),
        (r"\bnetwork\s*hospital\b", -0.5),
        # Cross-category negatives
        (r"\bfire\s*and\s*special\s*perils?\b", -0.5),
        (r"\bidv\b", -0.5),
        (r"\bvessel\b", -0.5),
        (r"\bdwelling\b", -0.3),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # HEALTH INSURANCE — 50+ discriminative phrases
    # Key insight: Health is defined by ONGOING coverage, Indian hospital
    # network, renewal mechanics, and indemnity-based claims.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.HEALTH: [
        # —— DEFINITIVE (1.0) — NEVER appear in Travel/Motor/Life/PA ——
        (r"\broom\s*rent\s*(limit|sub[\s-]?limit|cap|capping|restrict)\b", 1.0),
        (r"\bcumulative\s*bonus\b", 1.0),
        (r"\bno\s*claim\s*bonus\s*(protect|accumulat|increase|percentage)\b", 1.0),
        (r"\bday\s*care\s*(procedure|treatment|surgery)\b", 1.0),
        (r"\bayush\s*(treatment|coverage|benefit|hospital)\b", 1.0),
        (r"\bdomiciliary\s*hospitali[sz]ation\b", 1.0),
        (r"\brestoration\s*(benefit|of\s*sum\s*insured)\b", 1.0),
        (r"\borgan\s*donor\s*(expense|cover|benefit)\b", 1.0),
        (r"\bbariatric\s*surgery\b", 1.0),
        (r"\bmaternity\s*(cover|benefit|expense|waiting)\b", 1.0),
        (r"\bnewborn\s*(baby|cover|expense)\b", 1.0),
        (r"\bmental\s*(health|illness)\s*(cover|treat|benefit)\b", 1.0),
        (r"\bannual\s*health\s*check[\s-]?up\b", 1.0),
        (r"\btpa\s*(\(|name|third\s*party\s*admin)\b", 1.0),
        (r"\bnetwork\s*hospital\s*(list|panel|access)\b", 1.0),
        (r"\bcashless\s*(facility|treatment|claim|hospital)\b", 1.0),
        (r"\bsub[\s-]?limit\s*(on|for|per)\s*(disease|illness|treatment|room)\b", 1.0),
        (r"\barogya\s*sanjeevani\b", 1.0),
        (r"\blifetime\s*renewab(le|ility)\b", 1.0),
        (r"\bportability\s*(of\s*health|from\s*previous)\b", 1.0),
        (r"\bmoratorium\s*period\b", 1.0),  # IRDAI health-specific: 8-year moratorium
        (r"\bconvalescence\s*benefit\b", 1.0),
        (r"\bsecond\s*(medical\s*)?opinion\b", 1.0),

        # —— VERY STRONG (0.8) ——
        (r"\bpre[\s-]?existing\s*disease.*waiting\s*period\b", 0.8),
        (r"\bped\s*waiting\b", 0.8),
        (r"\b(initial|specific)\s*waiting\s*period\b", 0.8),
        (r"\bpre[\s-]?hospitali[sz]ation\b", 0.8),
        (r"\bpost[\s-]?hospitali[sz]ation\b", 0.8),
        (r"\bco[\s-]?pay(ment)?\s*(\d+%|clause|percent)\b", 0.8),
        (r"\bsum\s*insured\s*(per|for)\s*(family|person|insured|individual)\b", 0.8),
        (r"\b(individual|family|floater)\s*(health|mediclaim)\b", 0.8),
        (r"\brenewal\s*(premium|date|notice)\b", 0.8),
        (r"\b(ambulance|air\s*ambulance)\s*(charge|cover|expense)\s*(up\s*to|max|rs|\u20b9)\b", 0.8),
        (r"\bice\s*treatment\b", 0.8),  # In-patient, Critical, Emergency
        (r"\bmodern\s*treatment\b", 0.8),

        # —— STRONG (0.6) ——
        (r"\bhospitali[sz]ation\s*(expense|cover|benefit)\b", 0.6),
        (r"\b(in[\s-]?patient|out[\s-]?patient)\s*(treatment|care|department)\b", 0.6),
        (r"\bsum\s*insured\b", 0.6),
        (r"\bexclusion\b", 0.4),  # Appears in all categories
        (r"\bwaiting\s*period\b", 0.4),  # Appears in health and some life

        # —— SUPER TOP-UP SPECIFIC SIGNALS ——
        # These FURTHER classify within Health
        (r"\baggregate\s*deductible\b", 0.8),  # Definitive super top-up signal
        (r"\bdeductible\s*(of|amount)\s*\u20b9?\s*\d+\s*(lakh|lac)\b", 0.6),
        (r"\bcoverage\s*(trigger|activat)\w*\s*(after|once|when)\s*(cumulative|aggregate)\b", 0.8),

        # —— NEGATIVE SIGNALS ——
        (r"\btrip\s*cancellation\b", -0.5),
        (r"\bbaggage\s*(loss|delay)\b", -0.5),
        (r"\bflight\s*delay\b", -0.5),
        (r"\bpassport\s*(loss|number)\b", -0.5),
        (r"\bdestination\s*country\b", -0.5),
        (r"\b(USD|EUR)\s*\d", -0.5),
        (r"\bper\s*trip\b", -0.5),
        # Cross-category negatives
        (r"\bfire\s*and\s*special\s*perils?\b", -0.5),
        (r"\bvessel\b", -0.5),
        (r"\bcargo\b", -0.5),
        (r"\bdwelling\b", -0.3),
        (r"\b(erection|contractor)\s*all\s*risk\b", -0.5),
        (r"\b(crop|fasal|pmfby)\b", -0.5),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # MOTOR INSURANCE
    # Key insight: Vehicle identifiers are unique. No other category has
    # IDV, chassis numbers, or RTO references.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.MOTOR: [
        # —— DEFINITIVE (1.0) ——
        (r"\bidv\s*(\(|insured\s*declared\s*value)\b", 1.0),
        (r"\b(engine|chassis)\s*(no|number)\s*:?\s*[A-Z0-9]", 1.0),
        (r"\bregistration\s*(no|number)\s*:?\s*[A-Z]{2}\s*\d", 1.0),
        (r"\bzero\s*dep(reciation)?\s*(cover|add[\s-]?on|rider)\b", 1.0),
        (r"\breturn\s*to\s*invoice\b", 1.0),
        (r"\b(engine|gearbox)\s*protect(ion|or)\b", 1.0),
        (r"\bhydrostatic\s*lock\b", 1.0),
        (r"\broadside\s*assistance\b", 1.0),
        (r"\bconsumable(s)?\s*(cover|expense)\b", 1.0),
        (r"\btyre\s*(cover|protect|damage)\b", 1.0),
        (r"\bkey\s*replacement\b", 1.0),
        (r"\brto\s*(code|zone|office)\b", 1.0),
        (r"\bncb\s*(protect|certificate|transfer|discount|percentage)\b", 1.0),
        (r"\b(own\s*damage|od)\s*(premium|cover|section)\b", 1.0),
        (r"\bthird\s*party\s*(liability|premium|section|cover)\b", 1.0),
        (r"\b(private\s*car|two[\s-]?wheeler|commercial\s*vehicle)\s*(package|policy)\b", 1.0),
        (r"\bmotor\s*vehicles?\s*act\b", 1.0),
        (r"\bfuel\s*type\s*:?\s*(petrol|diesel|cng|electric|hybrid)\b", 1.0),
        (r"\bcubic\s*capacity\b", 1.0),
        (r"\belectrical\s*(accessories|fitment)\b", 0.8),
        (r"\bnon[\s-]?electrical\s*(accessories|fitment)\b", 0.8),
        (r"\bgeographical\s*(area|extension)\b", 0.6),
        (r"\b(compulsory|cpa|owner[\s-]?driver)\s*(pa|personal\s*accident)\b", 0.8),
        (r"\bvehicle\s*(make|model|variant|year)\b", 0.8),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # LIFE INSURANCE — Catch-all for Life category
    # Sub-classification into Term/ULIP/Endowment happens in Tier 2
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.LIFE_TERM: [
        # —— DEFINITIVE (1.0) — Term-specific ——
        (r"\bterm\s*(plan|insurance|assurance|life)\b", 1.0),
        (r"\bpure\s*(protection|risk\s*cover|life\s*cover)\b", 1.0),
        (r"\bdeath\s*benefit\s*only\b", 1.0),
        (r"\bno\s*(maturity|survival)\s*benefit\b", 1.0),
        (r"\blevel\s*(cover|premium|term)\b", 0.8),
        (r"\b(increasing|decreasing)\s*(cover|sum\s*assured)\b", 0.8),

        # —— STRONG (0.6) — Life insurance general ——
        (r"\bsum\s*assured\b", 0.6),
        (r"\bdeath\s*benefit\b", 0.6),
        (r"\bnominee\b", 0.6),
        (r"\bpolicy\s*term\s*:?\s*\d+\s*years\b", 0.6),
        (r"\bpremium\s*paying\s*term\b", 0.6),
        (r"\bcritical\s*illness\s*rider\b", 0.6),
        (r"\baccidental\s*death\s*benefit\s*rider\b", 0.6),
        (r"\bwaiver\s*of\s*premium\b", 0.6),
        (r"\bterminal\s*illness\s*benefit\b", 0.6),
        (r"\bsurrender\s*value\b", 0.6),
        (r"\b(free[\s-]?look|cooling[\s-]?off)\s*period\b", 0.4),

        # —— NEGATIVE SIGNALS ——
        (r"\broom\s*rent\b", -0.5),
        (r"\bhospitali[sz]ation\b", -0.3),
        (r"\btrip\s*cancellation\b", -0.5),
        (r"\bidv\b", -0.5),
        (r"\bregistration\s*number\b", -0.5),
    ],

    PolicyType.LIFE_ULIP: [
        # —— DEFINITIVE (1.0) ——
        (r"\bunit\s*linked\b", 1.0),
        (r"\bulip\b", 1.0),
        (r"\bnet\s*asset\s*value\b", 1.0),
        (r"\bnav\b", 1.0),
        (r"\bfund\s*(value|switch|option|choice)\b", 1.0),
        (r"\b(equity|debt|balanced|money\s*market)\s*fund\b", 1.0),
        (r"\bpremium\s*allocation\s*charge\b", 1.0),
        (r"\bfund\s*management\s*charge\b", 1.0),
        (r"\bmortality\s*charge\b", 1.0),
        (r"\b5[\s-]*year\s*lock[\s-]*in\b", 1.0),
        (r"\bpartial\s*withdrawal\b", 0.8),
        (r"\b(loyalty|wealth)\s*(addition|booster)\b", 0.8),
        (r"\bhigher\s*of\s*(sum\s*assured|fund\s*value)\b", 1.0),
    ],

    PolicyType.LIFE_ENDOWMENT: [
        # —— DEFINITIVE (1.0) ——
        (r"\b(simple|compound)\s*reversionary\s*bonus\b", 1.0),
        (r"\bfinal\s*additional\s*bonus\b", 1.0),
        (r"\bmaturity\s*(benefit|amount|proceed)\b", 1.0),
        (r"\bsurvival\s*benefit\b", 1.0),
        (r"\bguaranteed\s*(surrender\s*value|maturity|addition)\b", 1.0),
        (r"\bpaid[\s-]?up\s*value\b", 1.0),
        (r"\bparticipating\s*(plan|policy)\b", 1.0),
        (r"\bwith[\s-]?profit\b", 0.8),
        (r"\bloan\s*against\s*(policy|surrender\s*value)\b", 0.8),
        (r"\bendowment\s*(plan|policy|assurance)\b", 1.0),
        (r"\bmoney[\s-]?back\s*(plan|policy)\b", 1.0),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # PERSONAL ACCIDENT
    # Key insight: PA is about the DISABILITY SCHEDULE. Only PA has
    # detailed body-part percentage tables.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.PERSONAL_ACCIDENT: [
        # —— DEFINITIVE (1.0) ——
        (r"\bpermanent\s*total\s*disability\b", 1.0),
        (r"\bpermanent\s*partial\s*disability\b", 1.0),
        (r"\btemporary\s*total\s*disability\b", 1.0),
        (r"\bdisability\s*(schedule|percentage|table|benefit)\b", 1.0),
        (r"\bcapital\s*sum\s*insured\b", 1.0),
        (r"\baccidental\s*death\s*benefit\s*:?\s*(100%|\u20b9|rs)\b", 1.0),
        (r"\b(loss\s*of)\s*(limb|eye|finger|thumb|toe|hearing|speech)\b", 1.0),
        (r"\b(violent|external|visible)\s*(means|event|cause)\b", 1.0),
        (r"\bweekly\s*(benefit|compensation|allowance)\b", 0.8),
        (r"\bsaral\s*suraksha\s*bima\b", 1.0),
        (r"\bgroup\s*personal\s*accident\b", 1.0),
        (r"\bhospital\s*cash\s*(daily|per\s*day|benefit|allowance)\b", 0.8),
        (r"\baccident[\s-]?only\b", 1.0),

        # —— NEGATIVE SIGNALS ——
        (r"\bdeath\s*due\s*to\s*(illness|disease|natural)\b", -0.5),
        (r"\bmaturity\s*benefit\b", -0.5),
        (r"\broom\s*rent\b", -0.5),
        (r"\btrip\s*cancellation\b", -0.5),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # FIRE INSURANCE
    # Key insight: Fire is about PROPERTY damage from fire and allied perils.
    # Sum insured on building/stock/machinery is definitive.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.FIRE: [
        # —— DEFINITIVE (1.0) ——
        (r"\bstandard\s*fire\s*(&|and)\s*special\s*perils?\b", 1.0),
        (r"\bsfsp\b", 1.0),
        (r"\bindustrial\s*all\s*risk\b", 1.0),
        (r"\bfire\s*insurance\s*policy\b", 1.0),
        (r"\bsum\s*insured\s*(on|for)\s*(building|stock|machinery|plant|furniture)\b", 1.0),
        (r"\b(riot|strike|malicious\s*damage)\s*(damage|extension|cover)\b", 1.0),
        (r"\b(spontaneous\s*combustion)\b", 1.0),
        (r"\b(lightning|explosion|implosion)\s*(damage|cover|peril)\b", 0.8),
        (r"\b(storm|tempest|typhoon|cyclone|flood|inundation)\s*(peril|cover|extension)\b", 0.8),
        (r"\b(earthquake|fire|e\.?f\.?i\.?)\s*(cover|extension)\b", 0.8),
        (r"\b(subsidence|landslide)\s*(peril|cover)\b", 0.8),
        (r"\b(consequential\s*loss|loss\s*of\s*profit|business\s*interruption)\b", 0.8),
        (r"\b(burglary|housebreaking)\s*(insurance|policy)\b", 0.8),
        (r"\b(mega\s*risk|material\s*damage)\s*(policy|insurance)\b", 0.6),
        (r"\breinstatement\s*value\b", 0.6),
        # —— NEGATIVE ——
        (r"\broom\s*rent\b", -0.5),
        (r"\bidv\b", -0.5),
        (r"\btrip\s*cancellation\b", -0.5),
        (r"\bvessel\b", -0.5),
        (r"\bcargo\b", -0.5),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # MARINE INSURANCE
    # Key insight: Marine is about GOODS IN TRANSIT or VESSELS.
    # Voyage, bill of lading, ICC clauses are definitive.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.MARINE: [
        # —— DEFINITIVE (1.0) ——
        (r"\bmarine\s*(cargo|hull|transit)\s*(insurance|policy)\b", 1.0),
        (r"\b(bill\s*of\s*lading|b/l|airway\s*bill|awb)\b", 1.0),
        (r"\bicc\s*(\(?\s*[abc]\s*\)?|clause)\b", 1.0),
        (r"\bvessel\s*(name|type|age|tonnage)\b", 1.0),
        (r"\bvoyage\s*(from|to|route|clause)\b", 1.0),
        (r"\b(port\s*of\s*loading|port\s*of\s*discharge)\b", 1.0),
        (r"\b(inland\s*transit|inland\s*cargo)\b", 1.0),
        (r"\b(open\s*cover|open\s*policy|declaration\s*policy)\b", 0.8),
        (r"\b(general\s*average|particular\s*average|total\s*loss)\b", 0.8),
        (r"\b(jettison|barratry|piracy)\b", 0.8),
        (r"\bprotection\s*(&|and)\s*indemnity\b", 0.8),
        (r"\b(freight|tranship|consignment)\b", 0.6),
        (r"\b(seaworthiness|perils?\s*of\s*the\s*sea)\b", 0.8),
        # —— NEGATIVE ——
        (r"\broom\s*rent\b", -0.5),
        (r"\bidv\b", -0.5),
        (r"\bregistration\s*number\b", -0.5),
        (r"\bdwelling\b", -0.5),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # HOME INSURANCE
    # Key insight: Residential property coverage — dwelling, contents,
    # carpet area, construction type.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.HOME: [
        # —— DEFINITIVE (1.0) ——
        (r"\bhome\s*(insurance|protect|shield|cover)\s*(policy|plan)?\b", 1.0),
        (r"\bbharat\s*griha\s*raksha\b", 1.0),
        (r"\bhouseholder\s*(comprehensive|package|policy)\b", 1.0),
        (r"\b(dwelling|residential\s*property)\s*(insurance|cover|policy)\b", 1.0),
        (r"\b(home\s*structure|home\s*building)\s*(insurance|cover|sum\s*insured)\b", 1.0),
        (r"\b(home\s*content|household\s*content)\s*(insurance|cover|sum\s*insured)\b", 1.0),
        (r"\bcarpet\s*area\b", 0.8),
        (r"\b(built[\s-]*up|plinth)\s*area\b", 0.8),
        (r"\bconstruction\s*type\s*:?\s*(pucca|kutcha|rcc|semi[\s-]*pucca)\b", 0.8),
        (r"\b(burglar\s*alarm|theft\s*protection)\b", 0.6),
        (r"\b(tenant|landlord|owner[\s-]*occupier)\b", 0.6),
        # —— NEGATIVE ——
        (r"\btrip\s*cancellation\b", -0.5),
        (r"\bidv\b", -0.5),
        (r"\bvessel\b", -0.5),
        (r"\bcrop\b", -0.5),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # LIABILITY INSURANCE
    # Key insight: Legal liability, indemnity limits, retroactive dates,
    # defence costs, jurisdiction clauses.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.LIABILITY: [
        # —— DEFINITIVE (1.0) ——
        (r"\bpublic\s*liability\s*(insurance|policy|act)\b", 1.0),
        (r"\bproduct\s*liability\s*(insurance|policy|cover)\b", 1.0),
        (r"\bprofessional\s*indemnity\b", 1.0),
        (r"\bdirectors?\s*(&|and)\s*officers?\s*(liability|insurance)\b", 1.0),
        (r"\bcyber\s*liability\s*(insurance|policy)\b", 1.0),
        (r"\b(workmen|workers?)\s*(compensation|comp)\s*(act|insurance|policy)\b", 1.0),
        (r"\bcommercial\s*general\s*liability\b", 1.0),
        (r"\bcgl\s*(policy|insurance|cover)\b", 1.0),
        (r"\bumbrella\s*liability\b", 1.0),
        (r"\b(errors?\s*(&|and)\s*omissions?|e\s*&\s*o)\b", 1.0),
        (r"\bretroactive\s*date\b", 0.8),
        (r"\b(defence|legal)\s*costs?\s*(in\s*addition|within|included)\b", 0.8),
        (r"\b(each\s*occurrence|aggregate)\s*(limit|liability)\b", 0.8),
        (r"\b(bodily\s*injury|property\s*damage)\s*(liability|to\s*third)\b", 0.8),
        (r"\b(third[\s-]*party)\s*(liability|claim|bodily)\b", 0.6),
        (r"\bmedical\s*malpractice\b", 1.0),
        # —— NEGATIVE ——
        (r"\broom\s*rent\b", -0.5),
        (r"\bidv\b", -0.5),
        (r"\btrip\s*cancellation\b", -0.5),
        (r"\bdwelling\b", -0.3),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # ENGINEERING INSURANCE
    # Key insight: Construction/erection projects, machinery, testing
    # periods, maintenance periods. Very B2B/industrial vocabulary.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.ENGINEERING: [
        # —— DEFINITIVE (1.0) ——
        (r"\bcontractor\s*all\s*risk\b", 1.0),
        (r"\berection\s*all\s*risk\b", 1.0),
        (r"\bmachinery\s*breakdown\s*(insurance|policy)?\b", 1.0),
        (r"\belectronic\s*equipment\s*(insurance|policy)\b", 1.0),
        (r"\bboiler\s*(&|and)\s*pressure\s*plant\b", 1.0),
        (r"\b(testing|commissioning)\s*period\b", 0.8),
        (r"\b(maintenance|defects?\s*liability)\s*period\b", 0.8),
        (r"\b(erection|construction)\s*(period|phase|site)\b", 0.8),
        (r"\b(principal|contractor|sub[\s-]*contractor)\s*(name|liability|clause)\b", 0.8),
        (r"\b(civil|mechanical|electrical)\s*(works?|erection|installation)\b", 0.6),
        (r"\b(loss\s*of\s*profits?)\s*(following|due\s*to)\s*(machinery|mb|breakdown)\b", 1.0),
        (r"\b(it\s*infrastructure|server|data\s*centre)\s*(insurance|policy)\b", 0.8),
        (r"\boverheating\s*(damage|failure)\b", 0.6),
        (r"\b(short[\s-]*circuit|electrical\s*surge|voltage\s*fluctuation)\b", 0.6),
        # —— NEGATIVE ——
        (r"\broom\s*rent\b", -0.5),
        (r"\bidv\b", -0.5),
        (r"\btrip\s*cancellation\b", -0.5),
        (r"\bcrop\b", -0.5),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # CROP INSURANCE
    # Key insight: Agricultural vocabulary — kharif, rabi, PMFBY,
    # survey numbers, hectares, government scheme language.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.CROP: [
        # —— DEFINITIVE (1.0) ——
        (r"\bpradhan\s*mantri\s*fasal\s*bima\b", 1.0),
        (r"\bpmfby\b", 1.0),
        (r"\b(crop|fasal)\s*(insurance|bima|suraksha)\b", 1.0),
        (r"\b(weather[\s-]*based|wbcis|rwbcis)\s*(crop)?\s*(insurance)?\b", 1.0),
        (r"\b(livestock|cattle|buffalo|goat|sheep|poultry)\s*(insurance|policy)\b", 1.0),
        (r"\b(kharif|rabi)\s*(season|crop)?\b", 0.8),
        (r"\b(survey\s*number|khasra|gata)\s*(no|number)?\b", 0.8),
        (r"\b(crop\s*loss|yield\s*loss|prevented\s*sowing)\b", 0.8),
        (r"\b(notified\s*area|gram\s*panchayat|block[\s-]*level)\b", 0.8),
        (r"\b(hectare|acre|bigha)\s*:?\s*[\d.]+\b", 0.6),
        (r"\b(crop\s*cutting|cce|threshold\s*yield)\b", 0.8),
        (r"\b(locali[sz]ed\s*calamit|hailstorm|drought|pest\s*attack)\b", 0.6),
        (r"\bstate\s*(government|share|subsidy)\b", 0.4),
        # —— NEGATIVE ——
        (r"\broom\s*rent\b", -0.5),
        (r"\bidv\b", -0.5),
        (r"\bvessel\b", -0.5),
        (r"\btrip\s*cancellation\b", -0.5),
    ],

    # ─────────────────────────────────────────────────────────────────────
    # MISCELLANEOUS INSURANCE
    # Key insight: Catch-all for specialty lines — surety, credit,
    # fidelity, cyber retail, SME packages.
    # ─────────────────────────────────────────────────────────────────────
    PolicyType.MISC: [
        # —— DEFINITIVE (1.0) ——
        (r"\bsurety\s*bond\s*(insurance|policy|guarantee)?\b", 1.0),
        (r"\b(bid|performance|advance\s*payment)\s*bond\b", 1.0),
        (r"\b(fidelity\s*guarantee|employee\s*dishonesty)\b", 1.0),
        (r"\b(trade\s*credit|credit\s*insurance|buyer\s*default)\b", 1.0),
        (r"\b(cyber\s*sachet|retail\s*cyber)\b", 1.0),
        (r"\bbankers?\s*indemnity\b", 1.0),
        (r"\b(jeweller|jeweler)s?\s*block\b", 1.0),
        (r"\bpolitical\s*risk\s*(insurance|policy)\b", 1.0),
        (r"\bbharat\s*(sookshma|laghu)\s*udyam\s*suraksha\b", 1.0),
        (r"\b(shopkeeper|office)\s*(package|policy|insurance)\b", 0.8),
        (r"\b(sme|small\s*business)\s*(package|policy|insurance)\b", 0.8),
        (r"\b(gadget|mobile|device)\s*(insurance|protect|cover)\b", 0.8),
        (r"\b(embezzlement|forgery|misappropriation)\b", 0.6),
        (r"\b(phishing|cyber\s*fraud|identity\s*theft)\b", 0.6),
        # —— NEGATIVE ——
        (r"\broom\s*rent\b", -0.5),
        (r"\bidv\b", -0.5),
        (r"\bcrop\b", -0.5),
        (r"\bvessel\b", -0.5),
    ],
}


# —— 2E: INSURER → CATEGORY MAPPING ——
# Some insurers are EXCLUSIVELY in one category, which provides a strong prior.

# All 60 IRDAI-registered companies — exact legal_name and short_name from DB
LIFE_ONLY_INSURERS = {
    # 26 life insurers
    "lic", "life insurance corporation", "hdfc life", "icici prudential life",
    "icici pru life", "sbi life", "max life", "axis max life",
    "kotak mahindra life", "kotak life", "aditya birla sun life", "absli",
    "tata aia", "tata aia life", "bajaj life", "bajaj allianz life",
    "pnb metlife", "indusind nippon", "reliance nippon life",
    "aviva life", "sahara life", "shriram life",
    "bharti axa life", "generali central life", "generali life",
    "ageas federal", "ageas federal life", "canara hsbc", "canara hsbc life",
    "bandhan life", "pramerica life",
    "star union dai-ichi", "sud life",
    "indiafirst life", "edelweiss life", "edelweiss tokio life",
    "creditaccess life", "acko life insurance", "digit life", "go digit life",
}

HEALTH_ONLY_INSURERS = {
    # 7 standalone health insurers
    "star health", "care health", "religare health",
    "niva bupa", "max bupa",
    "aditya birla health", "ab health",
    "manipal cigna", "cigna ttk",
    "galaxy health", "narayana health",
}

GENERAL_INSURERS = {
    # 27 general insurers
    "new india", "new india assurance",
    "national insurance", "national ins",
    "oriental insurance", "oriental ins",
    "united india",
    "icici lombard",
    "hdfc ergo",
    "bajaj allianz general", "bajaj allianz gi", "bajaj general",
    "tata aig",
    "cholamandalam ms", "chola ms",
    "sbi general",
    "go digit", "digit gi", "digit insurance",
    "iffco tokio",
    "royal sundaram",
    "zurich kotak",
    "shriram gi", "shriram general",
    "universal sompo",
    "acko", "acko general", "acko gi",
    "generali central insurance", "generali gi", "future generali",
    "indusind general", "indusind gi", "reliance general",
    "raheja qbe",
    "liberty general", "liberty gi",
    "magma general", "magma gi", "magma hdi",
    "navi general", "navi gi",
    "zuno", "zuno general",
    "kshema", "kshema general",
    "aic", "agriculture insurance company",
    "ecgc",
}


# —— 2F: UIN PARSING PATTERNS ——

UIN_PATTERNS = {
    "life_linked": re.compile(r"\d{3}L\d{3}V\d{2}"),        # e.g., 101L083V09
    "life_nonlinked": re.compile(r"\d{3}N\d{3}V\d{2}"),     # e.g., 111N083V09
    "general": re.compile(r"IRDAN\d{3}(RP|CP)(\w{2})\d{4}V\d{2}"),
    "health_star": re.compile(r"SHAHLIP\d+V\d+"),
    "health_niva": re.compile(r"NBHIHLIP\d+V\d+"),
    "health_care": re.compile(r"RHEHLIP\d+V\d+"),
    "general_alt": re.compile(r"IRDA/HLT/\w+/P-[A-Z]/V\.\d+/\d+/\d{4}-\d{2}"),
}

# General insurer LOB codes (from IRDAI UIN structure)
LOB_CODES = {
    "MT": PolicyType.MOTOR,
    "HT": PolicyType.HEALTH,
    "HL": PolicyType.HEALTH,
    "PA": PolicyType.PERSONAL_ACCIDENT,
    "TR": PolicyType.TRAVEL,
    "FI": PolicyType.FIRE,
    "FR": PolicyType.FIRE,
    "PR": PolicyType.FIRE,          # Property → Fire category
    "MR": PolicyType.MARINE,
    "MC": PolicyType.MARINE_CARGO,
    "MH": PolicyType.MARINE_HULL,
    "HM": PolicyType.HOME,
    "EN": PolicyType.ENGINEERING,
    "LB": PolicyType.LIABILITY,
    "CR": PolicyType.CROP,
    "AG": PolicyType.CROP,          # Agriculture → Crop category
    "SU": PolicyType.MISC_SURETY,
    "MS": PolicyType.MISC,
    "AV": PolicyType.MISC,          # Aviation → Misc
    "RP": PolicyType.UNKNOWN,       # General retail product — needs further classification
    "CP": PolicyType.UNKNOWN,       # Commercial product — needs further classification
}


# ───────────────────────────────────────────────────────────────────────────────
# SECTION 3: THE CLASSIFIER ENGINE
# ───────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("hibiscus.classifier")


class HibiscusPolicyClassifier:
    """
    Production-grade insurance policy classifier for the Indian market.

    Usage:
        classifier = HibiscusPolicyClassifier()
        result = classifier.classify(
            document_text="...",
            product_name="Star Health Comprehensive",
            insurer_name="Star Health",
            uin="SHAHLIP22031V022122"
        )
        print(result.policy_type)           # PolicyType.HEALTH
        print(result.confidence)            # 0.98
        print(result.get_analysis_type())   # "health"
    """

    def __init__(self, confidence_thresholds: Optional[Dict] = None):
        self.thresholds = confidence_thresholds or {
            "auto_classify": 0.85,
            "audit_flag": 0.70,
            "llm_route": 0.50,
        }
        # Pre-compile all regex patterns for performance
        self._compiled_features = self._compile_features()
        self._compiled_deterministic = self._compile_deterministic()
        self._compiled_product_names = self._compile_product_names()
        self._compiled_uin = {k: v for k, v in UIN_PATTERNS.items()}
        logger.info("HibiscusPolicyClassifier initialized. All patterns compiled.")

    def _compile_features(self) -> Dict[PolicyType, List[Tuple[re.Pattern, float]]]:
        compiled = {}
        for ptype, features in DISCRIMINATIVE_FEATURES.items():
            compiled[ptype] = [
                (re.compile(pattern, re.IGNORECASE), weight)
                for pattern, weight in features
            ]
        return compiled

    def _compile_deterministic(self) -> Dict[PolicyType, List[re.Pattern]]:
        compiled = {}
        for ptype, patterns in DETERMINISTIC_FIELDS.items():
            compiled[ptype] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        return compiled

    def _compile_product_names(self) -> Dict[PolicyType, List[re.Pattern]]:
        compiled = {}
        for ptype, patterns in PRODUCT_NAME_PATTERNS.items():
            compiled[ptype] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        return compiled

    # ───────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ───────────────────────────────────────────────────────────────────

    def classify(
        self,
        document_text: str,
        product_name: str = "",
        insurer_name: str = "",
        uin: str = "",
        user_declared_type: str = "",
    ) -> ClassificationResult:
        """
        Main classification entry point.
        Runs through Tier 1 → Tier 2 → Tier 3 cascade.

        Args:
            document_text: Full extracted text from the policy document
            product_name: Product/plan name if available
            insurer_name: Name of the insurance company
            uin: IRDAI Unique Identification Number if found
            user_declared_type: What the user said it is (lowest trust signal)

        Returns:
            ClassificationResult with type, confidence, and reasoning
        """
        signals = []
        warnings = []

        # Normalize inputs
        doc_lower = document_text.lower() if document_text else ""
        product_lower = product_name.lower().strip() if product_name else ""
        insurer_lower = insurer_name.lower().strip() if insurer_name else ""
        uin_clean = uin.strip().upper() if uin else ""

        # ——————— TIER 1: RULE-BASED (Deterministic Signals) ———————
        tier1_result = self._tier1_classify(
            doc_lower, product_lower, insurer_lower, uin_clean, signals, warnings
        )
        if tier1_result and tier1_result.confidence >= self.thresholds["auto_classify"]:
            tier1_result.tier_used = 1
            logger.info(f"Tier 1 resolved: {tier1_result.policy_type.value} "
                       f"(conf={tier1_result.confidence:.3f})")
            return tier1_result

        # ——————— TIER 2: MULTI-SIGNAL SCORING ———————
        tier2_result = self._tier2_classify(
            doc_lower, product_lower, insurer_lower, signals, warnings,
            tier1_hint=tier1_result
        )
        if tier2_result and tier2_result.confidence >= self.thresholds["llm_route"]:
            tier2_result.tier_used = 2
            if tier2_result.confidence < self.thresholds["audit_flag"]:
                tier2_result.warnings.append("AUDIT_FLAG: Moderate confidence — periodic review recommended")
            logger.info(f"Tier 2 resolved: {tier2_result.policy_type.value} "
                       f"(conf={tier2_result.confidence:.3f})")
            return tier2_result

        # ——————— TIER 3: LLM CHAIN-OF-THOUGHT (Stub for integration) ———————
        tier3_result = self._tier3_classify(
            document_text, product_name, insurer_name, uin,
            signals, warnings, tier2_result
        )
        tier3_result.tier_used = 3
        return tier3_result

    # ───────────────────────────────────────────────────────────────────
    # TIER 1: RULE-BASED CLASSIFICATION
    # ───────────────────────────────────────────────────────────────────

    def _tier1_classify(
        self,
        doc_lower: str,
        product_lower: str,
        insurer_lower: str,
        uin_clean: str,
        signals: List[str],
        warnings: List[str],
    ) -> Optional[ClassificationResult]:
        """
        Tier 1: Deterministic classification using UIN, product names,
        and structural field presence.
        Returns result if confident, None if needs Tier 2.
        """
        results = []

        # —— 1A: UIN-BASED CLASSIFICATION ——
        uin_result = self._classify_by_uin(uin_clean, signals)
        if uin_result:
            results.append(uin_result)

        # —— 1B: IRDAI STANDARD PRODUCT NAME ——
        for std_name, ptype in IRDAI_STANDARD_PRODUCTS.items():
            if std_name in product_lower or std_name in doc_lower[:2000]:
                signals.append(f"IRDAI_STANDARD_PRODUCT: {std_name}")
                results.append((ptype, 0.98))

        # —— 1C: INSURER-BASED PRIOR ——
        insurer_category = self._classify_by_insurer(insurer_lower)
        if insurer_category:
            signals.append(f"INSURER_CATEGORY: {insurer_category}")

        # —— 1D: PRODUCT NAME PATTERN MATCHING ——
        name_results = self._classify_by_product_name(product_lower, signals)
        results.extend(name_results)

        # —— 1E: DETERMINISTIC FIELD PRESENCE ——
        field_results = self._classify_by_deterministic_fields(doc_lower, signals)
        results.extend(field_results)

        # —— RESOLVE TIER 1 ——
        if not results:
            return None

        # Find best result
        best_type, best_conf = max(results, key=lambda x: x[1])

        # Cross-validate with insurer category
        if insurer_category:
            category = self._get_category(best_type)
            if insurer_category == "life" and category != PolicyCategory.LIFE:
                warnings.append(
                    f"CONFLICT: Classified as {best_type.value} but insurer "
                    f"'{insurer_lower}' is Life-only. Reducing confidence."
                )
                best_conf *= 0.6
            elif insurer_category == "health" and category != PolicyCategory.HEALTH:
                warnings.append(
                    f"CONFLICT: Classified as {best_type.value} but insurer "
                    f"'{insurer_lower}' is Health-only. Reducing confidence."
                )
                best_conf *= 0.6

        if best_conf >= self.thresholds["auto_classify"]:
            # Sub-classify within category for finer granularity
            best_type = self._tier1_sub_classify(best_type, doc_lower, signals)
            return ClassificationResult(
                policy_type=best_type,
                policy_category=self._get_category(best_type),
                confidence=min(best_conf, 1.0),
                confidence_level=self._get_confidence_level(best_conf),
                tier_used=1,
                primary_signals=signals[:10],
                secondary_labels=[],
                classification_reasoning=f"Tier 1 deterministic: {', '.join(signals[:5])}",
                warnings=warnings,
            )
        return None

    def _tier1_sub_classify(self, best_type: PolicyType, doc_lower: str, signals: List[str]) -> PolicyType:
        """Apply sub-classification at Tier 1 for types that resolve to a generic top-level."""
        sub_map = {
            PolicyType.HEALTH: self._sub_classify_health,
            PolicyType.MOTOR: self._sub_classify_motor,
            PolicyType.TRAVEL: self._sub_classify_travel,
            PolicyType.PERSONAL_ACCIDENT: self._sub_classify_pa,
            PolicyType.FIRE: self._sub_classify_fire,
            PolicyType.MARINE: self._sub_classify_marine,
            PolicyType.HOME: self._sub_classify_home,
            PolicyType.LIABILITY: self._sub_classify_liability,
            PolicyType.ENGINEERING: self._sub_classify_engineering,
            PolicyType.CROP: self._sub_classify_crop,
            PolicyType.MISC: self._sub_classify_misc,
        }
        sub_fn = sub_map.get(best_type)
        if sub_fn:
            refined = sub_fn(doc_lower)
            if refined != best_type:
                signals.append(f"TIER1_SUB_CLASS: {best_type.value} → {refined.value}")
            return refined
        return best_type

    def _classify_by_uin(self, uin: str, signals: List[str]) -> Optional[Tuple[PolicyType, float]]:
        """Parse UIN format to extract category and LOB."""
        if not uin:
            return None

        # Life Insurance — Linked (ULIP)
        if UIN_PATTERNS["life_linked"].search(uin):
            signals.append(f"UIN_LIFE_LINKED: {uin}")
            return (PolicyType.LIFE_ULIP, 0.95)

        # Life Insurance — Non-Linked
        if UIN_PATTERNS["life_nonlinked"].search(uin):
            signals.append(f"UIN_LIFE_NONLINKED: {uin}")
            return (PolicyType.LIFE_TERM, 0.85)  # Could be term or endowment

        # General Insurance with LOB code
        match = UIN_PATTERNS["general"].search(uin)
        if match:
            lob_code = match.group(2)
            ptype = LOB_CODES.get(lob_code, PolicyType.UNKNOWN)
            if ptype != PolicyType.UNKNOWN:
                signals.append(f"UIN_GENERAL_LOB_{lob_code}: {uin}")
                return (ptype, 0.95)
            signals.append(f"UIN_GENERAL_UNKNOWN_LOB_{lob_code}: {uin}")
            return None

        # Health-only insurer UINs
        for pattern_name in ["health_star", "health_niva", "health_care"]:
            if UIN_PATTERNS[pattern_name].search(uin):
                signals.append(f"UIN_{pattern_name.upper()}: {uin}")
                return (PolicyType.HEALTH, 0.95)

        return None

    def _classify_by_insurer(self, insurer_lower: str) -> Optional[str]:
        """Determine if insurer is category-exclusive.
        Check General FIRST to prevent false life/health matches on shared names
        like 'acko' (general) vs 'acko life insurance' (life).
        """
        if not insurer_lower:
            return None
        # Check General first (most insurers, and prevents false matches)
        for name in GENERAL_INSURERS:
            if name == insurer_lower or name in insurer_lower or insurer_lower in name:
                return "general"
        for name in HEALTH_ONLY_INSURERS:
            if name == insurer_lower or name in insurer_lower or insurer_lower in name:
                return "health"
        for name in LIFE_ONLY_INSURERS:
            if name == insurer_lower or name in insurer_lower or insurer_lower in name:
                return "life"
        return None

    def _classify_by_product_name(
        self, product_lower: str, signals: List[str]
    ) -> List[Tuple[PolicyType, float]]:
        """Match product name against known patterns."""
        if not product_lower:
            return []
        results = []
        for ptype, patterns in self._compiled_product_names.items():
            for pattern in patterns:
                if pattern.search(product_lower):
                    signals.append(f"PRODUCT_NAME_MATCH: {ptype.value} ({pattern.pattern})")
                    results.append((ptype, 0.92))
                    break  # One match per category is enough
        return results

    def _classify_by_deterministic_fields(
        self, doc_lower: str, signals: List[str]
    ) -> List[Tuple[PolicyType, float]]:
        """Check for fields whose presence is definitive."""
        results = []
        # Only check first 5000 chars for field presence (efficiency + these
        # are typically in the header/schedule section)
        header = doc_lower[:5000]

        for ptype, patterns in self._compiled_deterministic.items():
            match_count = sum(1 for p in patterns if p.search(header))
            if match_count >= 2:  # Need at least 2 deterministic fields
                conf = min(0.90 + (match_count - 2) * 0.02, 0.98)
                signals.append(
                    f"DETERMINISTIC_FIELDS: {ptype.value} ({match_count} fields)"
                )
                results.append((ptype, conf))
        return results

    # ───────────────────────────────────────────────────────────────────
    # TIER 2: MULTI-SIGNAL SCORING
    # ───────────────────────────────────────────────────────────────────

    def _tier2_classify(
        self,
        doc_lower: str,
        product_lower: str,
        insurer_lower: str,
        signals: List[str],
        warnings: List[str],
        tier1_hint: Optional[ClassificationResult] = None,
    ) -> Optional[ClassificationResult]:
        """
        Tier 2: Score document against all category feature sets.
        Uses weighted feature matching with positive AND negative signals.
        """
        scores: Dict[PolicyType, float] = {}
        match_details: Dict[PolicyType, List[str]] = {}

        for ptype, features in self._compiled_features.items():
            score = 0.0
            matches = []
            for pattern, weight in features:
                found = pattern.findall(doc_lower)
                if found:
                    # Count occurrences but with diminishing returns
                    # (first match is most important, subsequent less so)
                    count = len(found)
                    effective_weight = weight * (1 + 0.1 * min(count - 1, 5))
                    score += effective_weight
                    if weight > 0:
                        matches.append(f"+{weight:.1f}: {pattern.pattern[:50]}")
                    else:
                        matches.append(f"{weight:.1f}: {pattern.pattern[:50]}")

            scores[ptype] = score
            match_details[ptype] = matches

        # —— NORMALIZE SCORES TO 0-1 RANGE ——
        if not scores or max(scores.values()) <= 0:
            return None

        max_score = max(scores.values())
        min_score = min(scores.values())
        score_range = max_score - min_score if max_score != min_score else 1.0

        normalized = {}
        for ptype, score in scores.items():
            normalized[ptype] = max(0, (score - min_score) / score_range)

        # —— FIND TOP 2 FOR MARGIN ANALYSIS ——
        sorted_types = sorted(normalized.items(), key=lambda x: x[1], reverse=True)
        best_type, best_score = sorted_types[0]
        second_type, second_score = sorted_types[1] if len(sorted_types) > 1 else (None, 0)

        # —— CONFIDENCE CALCULATION ——
        # Confidence depends on:
        # 1. Absolute score (how many features matched)
        # 2. Margin (how much better than the next category)
        # 3. Whether negative signals are firing

        margin = best_score - second_score
        raw_confidence = 0.5 + (margin * 0.4) + (best_score * 0.1)

        # Boost for high absolute score (many matching features)
        feature_count = len([m for m in match_details.get(best_type, []) if m.startswith("+")])
        if feature_count >= 8:
            raw_confidence += 0.1
        elif feature_count >= 5:
            raw_confidence += 0.05

        # Reduce for negative signals firing
        negative_count = len([m for m in match_details.get(best_type, []) if m.startswith("-")])
        if negative_count >= 3:
            raw_confidence -= 0.15
            warnings.append(f"NEGATIVE_SIGNALS: {negative_count} counter-indicators for {best_type.value}")
        elif negative_count >= 1:
            raw_confidence -= 0.05

        confidence = max(0.0, min(1.0, raw_confidence))

        # —— DETECT COMBO PRODUCTS (Multi-Label) ——
        secondary_labels = []
        if second_type and second_score > 0.5 and margin < 0.25:
            secondary_labels.append(second_type)
            warnings.append(
                f"POSSIBLE_COMBO: {best_type.value} + {second_type.value} "
                f"(scores: {best_score:.2f} vs {second_score:.2f})"
            )

        # —— SUB-CLASSIFICATION: Refine within top-level category ——
        if best_type == PolicyType.HEALTH:
            best_type = self._sub_classify_health(doc_lower)
            signals.append(f"SUB_CLASS: Health → {best_type.value}")

        elif best_type == PolicyType.MOTOR:
            best_type = self._sub_classify_motor(doc_lower)
            signals.append(f"SUB_CLASS: Motor → {best_type.value}")

        elif best_type in (PolicyType.LIFE_TERM, PolicyType.LIFE_GENERIC):
            life_sub = self._sub_classify_life(doc_lower, scores)
            if life_sub != best_type:
                best_type = life_sub
                signals.append(f"SUB_CLASS: Life → {best_type.value}")

        elif best_type == PolicyType.TRAVEL:
            best_type = self._sub_classify_travel(doc_lower)
            signals.append(f"SUB_CLASS: Travel → {best_type.value}")

        elif best_type == PolicyType.PERSONAL_ACCIDENT:
            best_type = self._sub_classify_pa(doc_lower)
            signals.append(f"SUB_CLASS: PA → {best_type.value}")

        elif best_type == PolicyType.FIRE:
            best_type = self._sub_classify_fire(doc_lower)
            signals.append(f"SUB_CLASS: Fire → {best_type.value}")

        elif best_type == PolicyType.MARINE:
            best_type = self._sub_classify_marine(doc_lower)
            signals.append(f"SUB_CLASS: Marine → {best_type.value}")

        elif best_type == PolicyType.HOME:
            best_type = self._sub_classify_home(doc_lower)
            signals.append(f"SUB_CLASS: Home → {best_type.value}")

        elif best_type == PolicyType.LIABILITY:
            best_type = self._sub_classify_liability(doc_lower)
            signals.append(f"SUB_CLASS: Liability → {best_type.value}")

        elif best_type == PolicyType.ENGINEERING:
            best_type = self._sub_classify_engineering(doc_lower)
            signals.append(f"SUB_CLASS: Engineering → {best_type.value}")

        elif best_type == PolicyType.CROP:
            best_type = self._sub_classify_crop(doc_lower)
            signals.append(f"SUB_CLASS: Crop → {best_type.value}")

        elif best_type == PolicyType.MISC:
            best_type = self._sub_classify_misc(doc_lower)
            signals.append(f"SUB_CLASS: Misc → {best_type.value}")

        signals.append(f"TIER2_SCORES: {', '.join(f'{t.value}={s:.2f}' for t, s in sorted_types[:4])}")

        return ClassificationResult(
            policy_type=best_type,
            policy_category=self._get_category(best_type),
            confidence=confidence,
            confidence_level=self._get_confidence_level(confidence),
            tier_used=2,
            primary_signals=signals[:15],
            secondary_labels=secondary_labels,
            classification_reasoning=(
                f"Tier 2 scoring: {best_type.value}={scores.get(best_type, 0):.1f} "
                f"(normalized={best_score:.2f}), "
                f"margin over {second_type.value if second_type else 'N/A'}="
                f"{margin:.2f}, {feature_count} positive features, "
                f"{negative_count} negative signals"
            ),
            raw_scores={t.value: s for t, s in sorted_types[:6]},
            warnings=warnings,
        )

    def _is_super_topup(self, doc_lower: str) -> bool:
        """Detect super top-up within Health classification."""
        explicit_signals = [
            r"\bsuper\s*top[\s-]?up\b",
            r"\btop[\s-]?up\s*(health|plan|policy)\b",
        ]
        if any(re.search(p, doc_lower) for p in explicit_signals):
            return True

        deductible_keywords = [
            r"\baggregate\s*deductible\b",
            r"\bcumulative\s*deductible\b",
        ]
        has_deductible_keyword = any(re.search(p, doc_lower) for p in deductible_keywords)
        if has_deductible_keyword:
            deductible_value_patterns = [
                r"(?:aggregate|cumulative)\s*deductible\s*(?:\(.*?\))?\s*[:=]?\s*(?:rs\.?\s*|₹\s*|inr\s*)?([0-9,]+)",
                r"(?:aggregate|cumulative)\s*deductible\s*(?:\(.*?\))?\s*[:=]?\s*(nil|not\s*opted|not\s*applicable|n\.?a\.?|none|0)\b",
            ]
            zero_match = re.search(deductible_value_patterns[1], doc_lower)
            if zero_match:
                return False
            value_match = re.search(deductible_value_patterns[0], doc_lower)
            if value_match:
                try:
                    val = float(value_match.group(1).replace(",", ""))
                    if val > 0:
                        return True
                except (ValueError, TypeError):
                    pass
            return False

        activation_signal = r"\bcoverage\s*(trigger|activat)\w*\s*(after|once|when)\s*(cumulative|aggregate|total)\b"
        if re.search(activation_signal, doc_lower):
            return True
        return False

    def _sub_classify_health(self, doc_lower: str) -> PolicyType:
        """Refine Health into 11 subcategories."""
        # Super Top-Up (highest priority — very specific vocabulary)
        if self._is_super_topup(doc_lower):
            return PolicyType.HEALTH_SUPER_TOPUP
        # Arogya Sanjeevani
        if re.search(r"\barogya\s*sanjeevani\b", doc_lower):
            return PolicyType.HEALTH_AROGYA_SANJEEVANI
        # Critical Illness (lump-sum, not indemnity)
        if re.search(r"\bcritical\s*illness\s*(plan|policy|cover|insurance)\b", doc_lower):
            if re.search(r"\blump[\s-]?sum\s*(payout|benefit|payment)\b", doc_lower):
                return PolicyType.HEALTH_CRITICAL_ILLNESS
        # Disease-Specific
        if re.search(r"\b(cancer|cardiac|dengue|diabetes|vector[\s-]*borne)\s*(care|plan|cover|insurance)\b", doc_lower):
            return PolicyType.HEALTH_DISEASE_SPECIFIC
        # Hospital Daily Cash
        if re.search(r"\bhospital\s*(daily\s*)?cash\s*(benefit|plan|policy)\b", doc_lower):
            return PolicyType.HEALTH_HOSPITAL_CASH
        # Maternity
        if re.search(r"\bmaternity\s*(insurance|plan|health|cover)\b", doc_lower):
            return PolicyType.HEALTH_MATERNITY
        # PA under Health
        if re.search(r"\bpersonal\s*accident\s*health\b", doc_lower):
            return PolicyType.HEALTH_PA
        # Senior Citizen
        if re.search(r"\bsenior\s*citizen\s*(health|plan|policy)\b", doc_lower):
            return PolicyType.HEALTH_SENIOR_CITIZEN
        # Group Health
        if re.search(r"\bgroup\s*(health|mediclaim|medical)\s*(insurance|plan|policy)\b", doc_lower):
            return PolicyType.HEALTH_GROUP
        # Family Floater
        if re.search(r"\bfamily\s*(floater|health\s*optima|plan)\b", doc_lower):
            return PolicyType.HEALTH_FAMILY_FLOATER
        return PolicyType.HEALTH

    def _sub_classify_motor(self, doc_lower: str) -> PolicyType:
        """Refine Motor into 7 subcategories."""
        is_two_wheeler = bool(re.search(
            r"\b(two[\s-]*wheeler|bike|scooter|motorcycle|moped)\b", doc_lower
        ))
        is_commercial = bool(re.search(
            r"\b(commercial\s*vehicle|truck|bus|taxi|auto[\s-]*rickshaw|fleet|hcv|lcv|goods\s*vehicle)\b", doc_lower
        ))
        has_own_damage = bool(re.search(
            r"\b(own\s*damage|section\s*i|od\s*(premium|cover))\b", doc_lower
        ))
        has_tp = bool(re.search(
            r"\b(third\s*party|section\s*ii|tp\s*(premium|cover))\b", doc_lower
        ))
        is_addon = bool(re.search(
            r"\b(add[\s-]*on|rider|endorsement)\s*(cover|option|package)\b", doc_lower
        ))
        is_standalone_od = bool(re.search(
            r"\bstandalone\s*(own\s*damage|od)\b", doc_lower
        ))

        if is_addon:
            return PolicyType.MOTOR_ADDON
        if is_standalone_od:
            return PolicyType.MOTOR_STANDALONE_OD
        if is_commercial:
            return PolicyType.MOTOR_COMMERCIAL
        if is_two_wheeler:
            if has_tp and not has_own_damage:
                return PolicyType.MOTOR_TWO_WHEELER_TP
            return PolicyType.MOTOR_TWO_WHEELER
        if has_own_damage and has_tp:
            return PolicyType.MOTOR_COMPREHENSIVE
        if has_tp and not has_own_damage:
            return PolicyType.MOTOR_THIRD_PARTY
        return PolicyType.MOTOR

    def _sub_classify_life(self, doc_lower: str, scores: Dict) -> PolicyType:
        """Refine Life into 12 subcategories."""
        ulip_score = scores.get(PolicyType.LIFE_ULIP, 0)
        endowment_score = scores.get(PolicyType.LIFE_ENDOWMENT, 0)
        term_score = scores.get(PolicyType.LIFE_TERM, 0)

        if ulip_score > term_score and ulip_score > endowment_score:
            return PolicyType.LIFE_ULIP
        if endowment_score > term_score and endowment_score > ulip_score:
            # Differentiate endowment vs money-back
            if re.search(r"\bmoney[\s-]?back\b", doc_lower):
                return PolicyType.LIFE_MONEY_BACK
            return PolicyType.LIFE_ENDOWMENT
        # Term — check for ROP variant
        if re.search(r"\breturn\s*of\s*premium\b", doc_lower):
            return PolicyType.LIFE_TERM_ROP
        # Whole Life
        if re.search(r"\bwhole\s*life\s*(insurance|plan|policy)\b", doc_lower):
            return PolicyType.LIFE_WHOLE
        # Pension / Annuity
        if re.search(r"\b(pension|annuity|retirement)\s*(plan|policy|scheme)\b", doc_lower):
            return PolicyType.LIFE_PENSION
        # Child Plan
        if re.search(r"\b(child|children)\s*(plan|education|future|insurance)\b", doc_lower):
            return PolicyType.LIFE_CHILD
        # Group Term Life
        if re.search(r"\bgroup\s*(term\s*)?life\b", doc_lower):
            return PolicyType.LIFE_GROUP
        # Micro Insurance
        if re.search(r"\bmicro\s*(insurance|life)\b", doc_lower):
            return PolicyType.LIFE_MICRO
        # Savings Plan
        if re.search(r"\b(savings?|guaranteed\s*income)\s*(plan|policy|insurance)\b", doc_lower):
            return PolicyType.LIFE_SAVINGS
        return PolicyType.LIFE_TERM

    def _sub_classify_travel(self, doc_lower: str) -> PolicyType:
        """Refine Travel into 4 subcategories."""
        if re.search(r"\b(corporate|multi[\s-]*trip|annual\s*multi|business\s*travel)\b", doc_lower):
            return PolicyType.TRAVEL_CORPORATE
        if re.search(r"\bstudent\s*(travel|overseas|abroad)\b", doc_lower):
            return PolicyType.TRAVEL_STUDENT
        if re.search(r"\b(domestic|within\s*india|bharat\s*yatra)\b", doc_lower):
            return PolicyType.TRAVEL_DOMESTIC
        if re.search(r"\b(international|overseas|abroad|schengen)\b", doc_lower):
            return PolicyType.TRAVEL_INTERNATIONAL
        return PolicyType.TRAVEL

    def _sub_classify_pa(self, doc_lower: str) -> PolicyType:
        """Refine Personal Accident into 3 subcategories."""
        if re.search(r"\bpradhan\s*mantri\s*suraksha\s*bima\s*yojana\b", doc_lower) or \
           re.search(r"\bpmsby\b", doc_lower):
            return PolicyType.PA_PMSBY
        if re.search(r"\bgroup\s*personal\s*accident\b", doc_lower):
            return PolicyType.PA_GROUP
        return PolicyType.PERSONAL_ACCIDENT

    def _sub_classify_fire(self, doc_lower: str) -> PolicyType:
        """Refine Fire into 4 subcategories."""
        if re.search(r"\bindustrial\s*all\s*risk\b", doc_lower):
            return PolicyType.FIRE_IAR
        if re.search(r"\b(business\s*interruption|consequential\s*loss|loss\s*of\s*profit)\b", doc_lower):
            return PolicyType.FIRE_BUSINESS_INTERRUPTION
        if re.search(r"\b(burglary|housebreaking)\s*(insurance|policy)\b", doc_lower):
            return PolicyType.FIRE_BURGLARY
        return PolicyType.FIRE

    def _sub_classify_marine(self, doc_lower: str) -> PolicyType:
        """Refine Marine into 4 subcategories."""
        # P&I / Marine Liability first (most specific)
        if re.search(r"\b(protection\s*(&|and)\s*indemnity|p\s*&\s*i|marine\s*liability)\b", doc_lower):
            return PolicyType.MARINE_LIABILITY
        # Inland Transit
        if re.search(r"\b(inland\s*transit|itc[\s-]*[ab])\b", doc_lower):
            return PolicyType.MARINE_INLAND
        # Marine Cargo (check cargo keywords before hull)
        if re.search(r"\b(marine\s*cargo|cargo\s*(insurance|policy)|icc\s*(\(?\s*[abc]))\b", doc_lower):
            return PolicyType.MARINE_CARGO
        # Marine Hull (vessel, ship, tonnage)
        if re.search(r"\b(marine\s*hull|hull\s*(insurance|policy)|ship\s*(insurance|owner)|tonnage)\b", doc_lower):
            return PolicyType.MARINE_HULL
        return PolicyType.MARINE_CARGO

    def _sub_classify_home(self, doc_lower: str) -> PolicyType:
        """Refine Home into 4 subcategories."""
        if re.search(r"\bbharat\s*griha\s*raksha\b", doc_lower):
            return PolicyType.HOME_BHARAT_GRIHA_RAKSHA
        if re.search(r"\bhouseholder\s*(comprehensive|package)\b", doc_lower):
            return PolicyType.HOME_PACKAGE
        if re.search(r"\b(home\s*content|household\s*content)\b", doc_lower):
            return PolicyType.HOME_CONTENTS
        if re.search(r"\b(home\s*structure|building\s*insurance)\b", doc_lower):
            return PolicyType.HOME_STRUCTURE
        return PolicyType.HOME

    def _sub_classify_liability(self, doc_lower: str) -> PolicyType:
        """Refine Liability into 7 subcategories."""
        if re.search(r"\bdirectors?\s*(&|and)\s*officers?\b", doc_lower):
            return PolicyType.LIABILITY_DNO
        if re.search(r"\b(cyber\s*liability|data\s*breach\s*liability)\b", doc_lower):
            return PolicyType.LIABILITY_CYBER
        if re.search(r"\bproduct\s*liability\b", doc_lower):
            return PolicyType.LIABILITY_PRODUCT
        if re.search(r"\b(professional\s*indemnity|errors?\s*(&|and)\s*omissions?|medical\s*malpractice)\b", doc_lower):
            return PolicyType.LIABILITY_PROFESSIONAL
        if re.search(r"\b(workmen|workers?)\s*(compensation|comp)\b", doc_lower):
            return PolicyType.LIABILITY_WORKMEN
        if re.search(r"\bpublic\s*liability\b", doc_lower):
            return PolicyType.LIABILITY_PUBLIC
        if re.search(r"\bcommercial\s*general\s*liability\b", doc_lower):
            return PolicyType.LIABILITY_CGL
        return PolicyType.LIABILITY

    def _sub_classify_engineering(self, doc_lower: str) -> PolicyType:
        """Refine Engineering into 5 subcategories."""
        if re.search(r"\berection\s*all\s*risk\b", doc_lower):
            return PolicyType.ENGINEERING_EAR
        if re.search(r"\bcontractor\s*all\s*risk\b", doc_lower):
            return PolicyType.ENGINEERING_CAR
        if re.search(r"\belectronic\s*equipment\b", doc_lower):
            return PolicyType.ENGINEERING_ELECTRONIC
        if re.search(r"\bboiler\s*(&|and)?\s*pressure\s*plant\b", doc_lower):
            return PolicyType.ENGINEERING_BOILER
        if re.search(r"\bmachinery\s*breakdown\b", doc_lower):
            return PolicyType.ENGINEERING_MACHINERY
        return PolicyType.ENGINEERING

    def _sub_classify_crop(self, doc_lower: str) -> PolicyType:
        """Refine Crop into 3 subcategories."""
        if re.search(r"\b(livestock|cattle|buffalo|goat|sheep|poultry)\b", doc_lower):
            return PolicyType.CROP_LIVESTOCK
        if re.search(r"\b(weather[\s-]*based|wbcis|rwbcis)\b", doc_lower):
            return PolicyType.CROP_WEATHER
        return PolicyType.CROP_PMFBY

    def _sub_classify_misc(self, doc_lower: str) -> PolicyType:
        """Refine Miscellaneous into 6 subcategories."""
        if re.search(r"\bsurety\s*bond\b", doc_lower):
            return PolicyType.MISC_SURETY
        if re.search(r"\b(trade\s*credit|credit\s*insurance|buyer\s*default)\b", doc_lower):
            return PolicyType.MISC_CREDIT
        if re.search(r"\b(cyber\s*sachet|retail\s*cyber|cyber\s*fraud)\b", doc_lower):
            return PolicyType.MISC_CYBER_RETAIL
        if re.search(r"\b(fidelity\s*guarantee|employee\s*dishonesty)\b", doc_lower):
            return PolicyType.MISC_FIDELITY
        if re.search(r"\bbharat\s*sookshma\s*udyam\b", doc_lower) or \
           re.search(r"\bshopkeeper\s*(insurance|policy)\b", doc_lower):
            return PolicyType.MISC_SHOPKEEPER
        if re.search(r"\b(sme|bharat\s*laghu\s*udyam|small\s*business)\s*(package|suraksha|insurance|policy)?\b", doc_lower):
            return PolicyType.MISC_SME
        return PolicyType.MISC

    # ───────────────────────────────────────────────────────────────────
    # TIER 3: LLM CHAIN-OF-THOUGHT (Integration Point)
    # ───────────────────────────────────────────────────────────────────

    def _tier3_classify(
        self,
        document_text: str,
        product_name: str,
        insurer_name: str,
        uin: str,
        signals: List[str],
        warnings: List[str],
        tier2_result: Optional[ClassificationResult] = None,
    ) -> ClassificationResult:
        """
        Tier 3: Generate LLM prompt for chain-of-thought classification.
        Returns the prompt and a default result.
        Actual LLM call should be made by the caller.

        Integration: Replace the return statement with your LLM API call
        to Claude/GPT-4/DeepSeek and parse the structured response.
        """
        tier2_hint = ""
        if tier2_result:
            tier2_hint = (
                f"\nPrevious automated analysis suggests: {tier2_result.policy_type.value} "
                f"(confidence: {tier2_result.confidence:.2f}). "
                f"Scores: {tier2_result.raw_scores}. "
                f"Warnings: {tier2_result.warnings}"
            )

        # —— THE CHAIN-OF-THOUGHT CLASSIFICATION PROMPT ——
        llm_prompt = self._build_llm_classification_prompt(
            document_text, product_name, insurer_name, uin, tier2_hint
        )

        # —— Store the prompt for the caller to use ——
        warnings.append("TIER3_LLM_REQUIRED: Confidence too low for automated classification")
        signals.append("LLM_PROMPT_GENERATED")

        # Default return (caller should replace with actual LLM response)
        default_type = tier2_result.policy_type if tier2_result else PolicyType.UNKNOWN
        default_conf = tier2_result.confidence * 0.8 if tier2_result else 0.3

        result = ClassificationResult(
            policy_type=default_type,
            policy_category=self._get_category(default_type),
            confidence=default_conf,
            confidence_level=ConfidenceLevel.AMBIGUOUS,
            tier_used=3,
            primary_signals=signals,
            secondary_labels=tier2_result.secondary_labels if tier2_result else [],
            requires_human_review=True,
            classification_reasoning=f"Tier 3 LLM required. Prompt generated. {tier2_hint}",
            warnings=warnings,
        )
        # Attach the prompt for the caller
        result._llm_prompt = llm_prompt  # type: ignore
        return result

    def _build_llm_classification_prompt(
        self,
        document_text: str,
        product_name: str,
        insurer_name: str,
        uin: str,
        tier2_hint: str,
    ) -> str:
        """
        Build a structured CoT prompt for LLM classification.
        Designed for Claude/GPT-4 with structured output.
        """
        # Truncate document for LLM context (first 4000 + last 2000 chars)
        doc_excerpt = document_text[:4000]
        if len(document_text) > 6000:
            doc_excerpt += "\n\n[...MIDDLE SECTION TRUNCATED...]\n\n"
            doc_excerpt += document_text[-2000:]

        prompt = f"""You are an expert Indian insurance policy classifier. Your task is to classify the following insurance policy document into EXACTLY ONE primary category.

AVAILABLE CATEGORIES (12 insurance categories, ~69 subcategories):
LIFE: life_term, life_term_rop, life_ulip, life_endowment, life_money_back, life_whole, life_pension, life_child, life_group, life_micro, life_savings
HEALTH: health, health_family_floater, health_super_topup, health_group, health_critical_illness, health_senior_citizen, health_arogya_sanjeevani, health_hospital_cash, health_disease_specific, health_maternity, health_pa
MOTOR: motor_comprehensive, motor_third_party, motor_two_wheeler, motor_two_wheeler_tp, motor_commercial, motor_standalone_od, motor_addon
FIRE: fire, fire_iar, fire_business_interruption, fire_burglary
MARINE: marine_cargo, marine_hull, marine_inland, marine_liability
TRAVEL: travel_domestic, travel_international, travel_student, travel_corporate
HOME: home, home_bharat_griha_raksha, home_structure, home_contents, home_package
LIABILITY: liability_public, liability_product, liability_professional, liability_dno, liability_cyber, liability_workmen, liability_cgl
ENGINEERING: engineering_car, engineering_ear, engineering_machinery, engineering_electronic, engineering_boiler
CROP: crop_pmfby, crop_weather, crop_livestock
PERSONAL ACCIDENT: personal_accident, pa_group, pa_pmsby
MISCELLANEOUS: misc_surety, misc_credit, misc_cyber_retail, misc_fidelity, misc_sme, misc_shopkeeper

CRITICAL DISAMBIGUATION RULES:
1. TRAVEL vs HEALTH: Trip dates, destination countries, passport, baggage, flight delay → TRAVEL. Room rent, NCB, AYUSH, network hospitals, lifetime renewability → HEALTH.
2. PA vs LIFE: Accident-only + disability schedule → PA. Death from any cause + sum assured → LIFE.
3. MOTOR: Vehicle registration, engine/chassis number, IDV, zero depreciation → MOTOR (ignore embedded CPA).
4. ULIP vs ENDOWMENT: NAV, fund switching → ULIP. Reversionary bonuses, maturity benefit → ENDOWMENT.
5. FIRE vs HOME: Commercial/industrial property, SFSP → FIRE. Residential/dwelling, contents, carpet area → HOME.
6. MARINE: Vessel, bill of lading, ICC clauses, cargo/hull → MARINE. Not general transit/logistics.
7. LIABILITY vs ENGINEERING: Legal liability, indemnity limits, D&O → LIABILITY. Construction site, erection/commissioning period, machinery breakdown → ENGINEERING.
8. CROP: PMFBY, kharif/rabi, survey number, livestock → CROP. Not general agriculture business.
9. MISC: Surety bonds, fidelity guarantee, trade credit, cyber sachet, SME package → MISCELLANEOUS.

POLICY METADATA:
- Product Name: {product_name or 'Not available'}
- Insurer: {insurer_name or 'Not available'}
- UIN: {uin or 'Not available'}
{tier2_hint}

POLICY DOCUMENT TEXT:
{doc_excerpt}

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "classification_reasoning": "Step 1: [What type of document structure do I see?] Step 2: [What discriminative features are present?] Step 3: [What features are ABSENT that I'd expect for other categories?] Step 4: [Final classification decision]",
    "primary_type": "<category_from_list_above>",
    "secondary_type": "<if_combo_product_otherwise_null>",
    "confidence": <0.0_to_1.0>,
    "key_evidence": ["evidence1", "evidence2", "evidence3"],
    "counter_evidence": ["any_conflicting_signals"]
}}"""

        return prompt

    # ───────────────────────────────────────────────────────────────────
    # UTILITY METHODS
    # ───────────────────────────────────────────────────────────────────

    def _get_category(self, policy_type: PolicyType) -> PolicyCategory:
        """Map specific type to Life vs General vs Health category (matches DB company_type_enum)."""
        LIFE_TYPES = {
            PolicyType.LIFE_TERM, PolicyType.LIFE_TERM_ROP, PolicyType.LIFE_ULIP,
            PolicyType.LIFE_ENDOWMENT, PolicyType.LIFE_MONEY_BACK, PolicyType.LIFE_WHOLE,
            PolicyType.LIFE_PENSION, PolicyType.LIFE_CHILD, PolicyType.LIFE_GROUP,
            PolicyType.LIFE_MICRO, PolicyType.LIFE_SAVINGS, PolicyType.LIFE_GENERIC,
        }
        HEALTH_TYPES = {
            PolicyType.HEALTH, PolicyType.HEALTH_FAMILY_FLOATER,
            PolicyType.HEALTH_SUPER_TOPUP, PolicyType.HEALTH_GROUP,
            PolicyType.HEALTH_CRITICAL_ILLNESS, PolicyType.HEALTH_SENIOR_CITIZEN,
            PolicyType.HEALTH_AROGYA_SANJEEVANI, PolicyType.HEALTH_HOSPITAL_CASH,
            PolicyType.HEALTH_DISEASE_SPECIFIC, PolicyType.HEALTH_MATERNITY,
            PolicyType.HEALTH_PA,
        }
        GENERAL_TYPES = {
            PolicyType.MOTOR, PolicyType.MOTOR_COMPREHENSIVE, PolicyType.MOTOR_THIRD_PARTY,
            PolicyType.MOTOR_TWO_WHEELER, PolicyType.MOTOR_TWO_WHEELER_TP,
            PolicyType.MOTOR_COMMERCIAL, PolicyType.MOTOR_STANDALONE_OD, PolicyType.MOTOR_ADDON,
            PolicyType.FIRE, PolicyType.FIRE_IAR, PolicyType.FIRE_BUSINESS_INTERRUPTION,
            PolicyType.FIRE_BURGLARY,
            PolicyType.MARINE, PolicyType.MARINE_CARGO, PolicyType.MARINE_HULL,
            PolicyType.MARINE_INLAND, PolicyType.MARINE_LIABILITY,
            PolicyType.TRAVEL, PolicyType.TRAVEL_DOMESTIC, PolicyType.TRAVEL_INTERNATIONAL,
            PolicyType.TRAVEL_STUDENT, PolicyType.TRAVEL_CORPORATE,
            PolicyType.HOME, PolicyType.HOME_BHARAT_GRIHA_RAKSHA, PolicyType.HOME_STRUCTURE,
            PolicyType.HOME_CONTENTS, PolicyType.HOME_PACKAGE,
            PolicyType.LIABILITY, PolicyType.LIABILITY_PUBLIC, PolicyType.LIABILITY_PRODUCT,
            PolicyType.LIABILITY_PROFESSIONAL, PolicyType.LIABILITY_DNO, PolicyType.LIABILITY_CYBER,
            PolicyType.LIABILITY_WORKMEN, PolicyType.LIABILITY_CGL,
            PolicyType.ENGINEERING, PolicyType.ENGINEERING_CAR, PolicyType.ENGINEERING_EAR,
            PolicyType.ENGINEERING_MACHINERY, PolicyType.ENGINEERING_ELECTRONIC,
            PolicyType.ENGINEERING_BOILER,
            PolicyType.CROP, PolicyType.CROP_PMFBY, PolicyType.CROP_WEATHER,
            PolicyType.CROP_LIVESTOCK,
            PolicyType.PERSONAL_ACCIDENT, PolicyType.PA_GROUP, PolicyType.PA_PMSBY,
            PolicyType.MISC, PolicyType.MISC_SURETY, PolicyType.MISC_CREDIT,
            PolicyType.MISC_CYBER_RETAIL, PolicyType.MISC_FIDELITY,
            PolicyType.MISC_SME, PolicyType.MISC_SHOPKEEPER,
        }
        if policy_type in LIFE_TYPES:
            return PolicyCategory.LIFE
        elif policy_type in HEALTH_TYPES:
            return PolicyCategory.HEALTH
        elif policy_type in GENERAL_TYPES:
            return PolicyCategory.GENERAL
        return PolicyCategory.UNKNOWN

    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        if confidence >= 0.95:
            return ConfidenceLevel.DEFINITIVE
        elif confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.70:
            return ConfidenceLevel.MODERATE
        elif confidence >= 0.50:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.AMBIGUOUS


# ───────────────────────────────────────────────────────────────────────────────
# SECTION 4: CONVENIENCE FUNCTION (Drop-in replacement for existing code)
# ───────────────────────────────────────────────────────────────────────────────

# Singleton instance
_classifier_instance: Optional[HibiscusPolicyClassifier] = None

def get_classifier() -> HibiscusPolicyClassifier:
    """Get or create the singleton classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = HibiscusPolicyClassifier()
    return _classifier_instance


def classify_policy(
    document_text: str,
    product_name: str = "",
    insurer_name: str = "",
    uin: str = "",
    user_declared_type: str = "",
) -> ClassificationResult:
    """
    One-call classification function.
    Drop-in replacement for existing policy type detection.

    Returns ClassificationResult with .get_analysis_type() method
    that maps to the 5 core analysis frameworks (health/travel/motor/life/personal_accident).
    """
    return get_classifier().classify(
        document_text=document_text,
        product_name=product_name,
        insurer_name=insurer_name,
        uin=uin,
        user_declared_type=user_declared_type,
    )


def get_policy_type_for_analysis(
    document_text: str,
    product_name: str = "",
    insurer_name: str = "",
    uin: str = "",
) -> str:
    """
    Legacy-compatible function that returns a simple string type.
    Maps to: "health", "travel", "motor", "life", "pa", "unknown"

    This is the DIRECT REPLACEMENT for the old identify_policy_type_deepseek().
    """
    result = classify_policy(document_text, product_name, insurer_name, uin)
    return result.get_legacy_type()


# ───────────────────────────────────────────────────────────────────────────────
# SECTION 4B: DATABASE INTEGRATION (Optional — requires psycopg2)
# ───────────────────────────────────────────────────────────────────────────────

try:
    import psycopg2
    import psycopg2.extras
    _HAS_PSYCOPG2 = True
except ImportError:
    _HAS_PSYCOPG2 = False


class DatabaseMatcher:
    """
    Optional PostgreSQL integration for classifier validation and product lookup.
    Uses the insurance_india database v_products_full view for matching.

    Usage:
        matcher = DatabaseMatcher("postgresql://insurance_admin:ins_db_2026_secure@localhost:5432/insurance_india")
        result = classifier.classify(document_text)
        matches = matcher.find_matching_products(result, limit=5)
        validation = matcher.validate_classification(result)
        matcher.close()
    """

    def __init__(self, dsn: str):
        if not _HAS_PSYCOPG2:
            raise ImportError(
                "psycopg2 is required for DatabaseMatcher. "
                "Install with: pip install psycopg2-binary"
            )
        self.conn = psycopg2.connect(dsn)
        self.conn.set_session(readonly=True)
        logger.info("DatabaseMatcher connected to insurance_india")

    def find_matching_products(
        self, result: ClassificationResult, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find DB products matching classifier output using category + trigram similarity."""
        db_fields = result.to_db_fields()
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT product_id, product_name, uin, company_name, category_name,
                       sub_category_name, product_type, is_active,
                       similarity(product_name, %(search_term)s) AS sim_score
                FROM insurance.v_products_full
                WHERE category_name = %(category)s
                ORDER BY similarity(product_name, %(search_term)s) DESC
                LIMIT %(limit)s
            """, {
                "category": db_fields["category_name"],
                "search_term": result.policy_type.value.replace("_", " "),
                "limit": limit,
            })
            return [dict(row) for row in cur.fetchall()]

    def validate_classification(self, result: ClassificationResult) -> Dict[str, Any]:
        """Check if classifier output maps to a valid DB category/subcategory pair."""
        db_fields = result.to_db_fields()
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT c.id AS category_id, c.name AS category_name,
                       sc.id AS subcategory_id, sc.name AS subcategory_name
                FROM insurance.insurance_categories c
                LEFT JOIN insurance.insurance_sub_categories sc
                    ON sc.category_id = c.id AND sc.name = %(subcat)s
                WHERE c.name = %(cat)s
            """, {
                "cat": db_fields["category_name"],
                "subcat": db_fields["subcategory_name"],
            })
            row = cur.fetchone()
            if row:
                return {
                    "valid": True,
                    "category_id": row["category_id"],
                    "subcategory_id": row["subcategory_id"],
                    "category_name": row["category_name"],
                    "subcategory_name": row["subcategory_name"],
                }
            return {"valid": False, "error": f"No match for {db_fields['category_name']}/{db_fields['subcategory_name']}"}

    def get_company_id(self, insurer_name: str) -> Optional[int]:
        """Lookup company ID by name (fuzzy match using trigram)."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id FROM insurance.insurance_companies
                WHERE lower(legal_name) LIKE %(pattern)s
                   OR lower(short_name) LIKE %(pattern)s
                ORDER BY similarity(lower(short_name), %(name)s) DESC
                LIMIT 1
            """, {
                "pattern": f"%{insurer_name.lower()}%",
                "name": insurer_name.lower(),
            })
            row = cur.fetchone()
            return row[0] if row else None

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
            logger.info("DatabaseMatcher connection closed")


# ───────────────────────────────────────────────────────────────────────────────
# SECTION 5: SELF-TEST / VALIDATION
# ───────────────────────────────────────────────────────────────────────────────

def run_classifier_tests():
    """
    Built-in test suite covering known failure modes.
    Run this after any changes to the feature dictionaries.
    """
    classifier = HibiscusPolicyClassifier()
    test_cases = [
        {
            "name": "Travel: Schengen policy with medical coverage",
            "text": (
                "Policy Schedule. ICICI Lombard International Travel Insurance. "
                "Destination: France, Germany, Italy. Departure Date: 15-Mar-2026. "
                "Return Date: 30-Mar-2026. Passport No: J1234567. "
                "Medical Expenses (Illness/Injury): USD 100,000. "
                "Emergency Medical Evacuation: USD 50,000. "
                "Trip Cancellation: USD 5,000. Baggage Loss: USD 2,000. "
                "Flight Delay: USD 500 per 12 hours. "
                "Schengen Compliant: Yes. Personal Liability: USD 50,000. "
                "Sum Insured per trip: USD 100,000. Single Trip."
            ),
            "product_name": "ICICI Lombard International Travel Insurance",
            "insurer_name": "ICICI Lombard",
            "expected": "travel",
        },
        {
            "name": "Travel: Domestic Bharat Yatra Suraksha",
            "text": (
                "Bharat Yatra Suraksha Policy. Standard Domestic Travel Insurance. "
                "Travel by Air. Trip dates: 10-Apr-2026 to 15-Apr-2026. "
                "Accidental Death: Rs 5,00,000. Medical Expenses: Rs 50,000. "
                "Loss of Baggage: Rs 5,000. Trip Cancellation: Rs 10,000."
            ),
            "product_name": "Bharat Yatra Suraksha",
            "insurer_name": "New India Assurance",
            "expected": "travel",
        },
        {
            "name": "Health: Star Comprehensive with medical terms",
            "text": (
                "Star Comprehensive Insurance Policy. Sum Insured: Rs 10,00,000. "
                "Room Rent: No sub-limit. Day Care Procedures: 587 procedures covered. "
                "AYUSH Treatment: Covered up to sum insured. "
                "Pre-existing Disease Waiting Period: 36 months. "
                "Initial Waiting Period: 30 days. Cumulative Bonus: 25% per year max 100%. "
                "Restoration Benefit: 100% automatic. No Claim Bonus Protection available. "
                "Network Hospitals: 14,000+. Cashless facility at network hospitals. "
                "Domiciliary Hospitalization: Covered. Organ Donor Expenses: Covered. "
                "Annual Health Checkup benefit. Lifetime renewability."
            ),
            "product_name": "Star Comprehensive Insurance Policy",
            "insurer_name": "Star Health",
            "expected": "health",
        },
        {
            "name": "Health: Super Top-Up with deductible",
            "text": (
                "HDFC ERGO Medisure Super Top Up Policy. Sum Insured: Rs 50,00,000. "
                "Aggregate Deductible: Rs 5,00,000. Coverage triggers after cumulative "
                "annual expenses exceed Rs 5 lakhs. Room Rent: No sub-limit. "
                "Day Care: 541 procedures. AYUSH: Covered. "
                "Pre/Post Hospitalization: 60/180 days. Restoration: Available."
            ),
            "product_name": "Medisure Super Top Up",
            "insurer_name": "HDFC ERGO",
            "expected": "health",
        },
        {
            "name": "Motor: Comprehensive with embedded PA",
            "text": (
                "Private Car Package Policy. Registration No: MH02AB1234. "
                "Engine No: K12M3456789. Chassis No: MA3EYD81S00123456. "
                "Make & Model: Maruti Suzuki Swift. Fuel Type: Petrol. "
                "IDV: Rs 4,50,000. Cubic Capacity: 1197cc. "
                "Section I - Own Damage Premium: Rs 8,500. "
                "Section II - Third Party Premium: Rs 2,094. "
                "Compulsory PA Cover for Owner-Driver: Rs 15,00,000. "
                "Zero Depreciation: Yes. Engine Protection: Yes. "
                "NCB Protection: 50% NCB protected. Roadside Assistance: 24/7."
            ),
            "product_name": "Private Car Package Policy",
            "insurer_name": "ICICI Lombard",
            "expected": "motor",
        },
        {
            "name": "Life Term: Pure protection",
            "text": (
                "HDFC Life Click 2 Protect 3D Plus. Term Plan. "
                "Sum Assured: Rs 1,50,00,000. Policy Term: 30 years. "
                "Premium Paying Term: 30 years. Annual Premium: Rs 12,500. "
                "Death Benefit Only. No Maturity Benefit. No Survival Benefit. "
                "Critical Illness Rider: Rs 50,00,000. "
                "Accidental Death Benefit Rider: Rs 1,00,00,000. "
                "Waiver of Premium on Critical Illness. "
                "Terminal Illness Benefit: Accelerated payout."
            ),
            "product_name": "Click 2 Protect 3D Plus",
            "insurer_name": "HDFC Life",
            "expected": "life",
        },
        {
            "name": "Life ULIP: Investment component",
            "text": (
                "ICICI Prudential Signature Unit Linked Plan. "
                "Net Asset Value based returns. Fund Options: Equity Growth, "
                "Balanced Advantage, Debt Plus, Money Market. "
                "Fund Switching: 12 free switches per year. "
                "Premium Allocation Charge: 2% of premium. "
                "Fund Management Charge: 1.35% p.a. Mortality Charge: As per age. "
                "5-year lock-in period. Partial Withdrawal after 5 years. "
                "Death Benefit: Higher of Sum Assured or Fund Value. "
                "Loyalty Addition: 1% of fund value from year 6."
            ),
            "product_name": "Signature",
            "insurer_name": "ICICI Prudential Life",
            "uin": "105L185V03",
            "expected": "life",
        },
        {
            "name": "PA: Standalone accident policy",
            "text": (
                "Saral Suraksha Bima - Personal Accident Insurance Policy. "
                "Capital Sum Insured: Rs 25,00,000. "
                "Accidental Death Benefit: 100% of CSI. "
                "Permanent Total Disability: 100% of CSI. "
                "Permanent Partial Disability: As per schedule. "
                "Loss of both eyes: 100%. Loss of one eye: 50%. "
                "Loss of one limb: 50%. Loss of thumb and index finger: 25%. "
                "Temporary Total Disability: Rs 5,000 per week, max 104 weeks. "
                "Accident only. Violent, external, visible means."
            ),
            "product_name": "Saral Suraksha Bima",
            "insurer_name": "Bajaj Allianz General",
            "expected": "personal_accident",
        },
        {
            "name": "Edge: Travel policy with health-like language",
            "text": (
                "Tata AIG Travel Guard International Policy. "
                "Medical Expenses (Overseas): USD 250,000. "
                "Hospitalization abroad covered. Pre-existing conditions excluded "
                "except in medical emergency. Medical evacuation to nearest hospital. "
                "Repatriation of mortal remains. Destination: USA, Canada. "
                "Departure: 01-May-2026. Return: 15-May-2026. "
                "Passport No: K9876543. Trip Cancellation: USD 5,000. "
                "Baggage Delay: USD 500. Flight Delay: USD 300/12hrs. "
                "Single Trip. Schengen compliant for Europe add-on."
            ),
            "product_name": "Travel Guard",
            "insurer_name": "Tata AIG",
            "expected": "travel",
        },
        # ── NEW CATEGORY TEST CASES ──
        {
            "name": "Fire: Standard Fire & Special Perils Policy",
            "text": (
                "Standard Fire and Special Perils Policy. "
                "Sum Insured on Building: Rs 5,00,00,000. "
                "Sum Insured on Stock: Rs 2,00,00,000. "
                "Sum Insured on Machinery & Plant: Rs 3,00,00,000. "
                "Perils covered: Fire, Lightning, Explosion, Implosion, "
                "Riot Strike Malicious Damage, Storm Tempest Typhoon Cyclone, "
                "Flood Inundation, Earthquake Fire Shock. "
                "Reinstatement value clause applicable. "
                "Spontaneous combustion extension added."
            ),
            "product_name": "Standard Fire & Special Perils Policy",
            "insurer_name": "New India Assurance",
            "expected": "fire",
        },
        {
            "name": "Marine: Cargo transit policy",
            "text": (
                "Marine Cargo Insurance Policy. ICC (A) Clause. "
                "Voyage: Mumbai Port to Rotterdam Port. "
                "Bill of Lading No: MAEU1234567. "
                "Vessel Name: MSC Mediterranean. Vessel Type: Container Ship. "
                "Cargo Description: Electronic Components. "
                "Sum Insured: USD 500,000. "
                "Port of Loading: Jawaharlal Nehru Port Trust. "
                "Port of Discharge: Rotterdam. "
                "General Average and Particular Average covered. "
                "Jettison and barratry of master covered."
            ),
            "product_name": "Marine Cargo Insurance Policy",
            "insurer_name": "ICICI Lombard",
            "expected": "marine",
        },
        {
            "name": "Home: Bharat Griha Raksha standard product",
            "text": (
                "Bharat Griha Raksha Policy. Standard Home Insurance. "
                "Dwelling Type: Pucca Construction (RCC). "
                "Carpet Area: 1200 sq ft. Building Age: 8 years. "
                "Sum Insured on Structure: Rs 50,00,000. "
                "Sum Insured on Contents: Rs 10,00,000. "
                "Construction Type: RCC. Owner-Occupier. "
                "Perils: Fire, Lightning, Storm, Flood, Earthquake, "
                "Burglary, Theft, Impact Damage."
            ),
            "product_name": "Bharat Griha Raksha",
            "insurer_name": "SBI General",
            "expected": "home",
        },
        {
            "name": "Liability: Directors & Officers policy",
            "text": (
                "Directors and Officers Liability Insurance Policy. "
                "Limit of Liability: Rs 10,00,00,000 each claim and aggregate. "
                "Retroactive Date: 01-Jan-2020. "
                "Defence costs in addition to limit of liability. "
                "Coverage for securities claims, wrongful acts, "
                "breach of duty, misstatement, misleading statements. "
                "Jurisdiction: India. Bodily injury to third party excluded. "
                "Property damage liability excluded."
            ),
            "product_name": "Directors & Officers Liability Policy",
            "insurer_name": "HDFC ERGO",
            "expected": "liability",
        },
        {
            "name": "Engineering: Contractor All Risk",
            "text": (
                "Contractor All Risk Insurance Policy. "
                "Project: Construction of 6-lane highway NH-48. "
                "Contract Value: Rs 250 Crores. Project Period: 24 months. "
                "Testing Period: 4 weeks. Maintenance Period: 12 months. "
                "Principal: NHAI. Contractor: L&T Construction. "
                "Sub-Contractors: 3 listed. "
                "Section I: Material Damage to contract works. "
                "Section II: Third Party Liability Rs 5 Crores."
            ),
            "product_name": "Contractor All Risk Policy",
            "insurer_name": "New India Assurance",
            "expected": "engineering",
        },
        {
            "name": "Crop: PMFBY Kharif Season",
            "text": (
                "Pradhan Mantri Fasal Bima Yojana - Kharif 2025. "
                "Farmer: Ram Prasad. Survey Number: 45/2. "
                "Village: Wardha, District: Wardha, Maharashtra. "
                "Crop Name: Soyabean. Area Sown: 2.5 Hectares. "
                "Kharif Season. Notified Area: Wardha Taluka. "
                "Sum Insured: Rs 37,500 per hectare. "
                "Premium Rate: 2% of sum insured. "
                "Crop Cutting Experiment (CCE) based yield assessment. "
                "Prevented sowing coverage: 25% of sum insured."
            ),
            "product_name": "PMFBY Crop Insurance",
            "insurer_name": "Agriculture Insurance Company",
            "expected": "crop",
        },
        {
            "name": "Miscellaneous: Surety Bond Insurance",
            "text": (
                "Surety Bond Insurance Policy. "
                "Bond Type: Performance Bond. "
                "Principal (Contractor): ABC Infrastructure Ltd. "
                "Obligee: Municipal Corporation of Greater Mumbai. "
                "Bond Amount: Rs 15,00,00,000. "
                "Project: Construction of Sewage Treatment Plant. "
                "Bond Period: 36 months. "
                "IRDAI Guidelines 2022 on Surety Bond Insurance."
            ),
            "product_name": "Surety Bond Insurance",
            "insurer_name": "Bajaj Allianz General",
            "expected": "miscellaneous",
        },
        {
            "name": "Health: Arogya Sanjeevani (Standard)",
            "text": (
                "Arogya Sanjeevani Policy. IRDAI Standard Health Product. "
                "Sum Insured: Rs 5,00,000. Room Rent: 2% of SI per day. "
                "Day Care: 541 procedures. ICU: 5% of SI per day. "
                "AYUSH Treatment: Covered. Ambulance: Rs 2,000 per hospitalization. "
                "Co-pay: 5% of admissible claim. "
                "Pre-existing disease: 48 months waiting. "
                "Cataract: After 24 months. Maternity: Not covered."
            ),
            "product_name": "Arogya Sanjeevani",
            "insurer_name": "Star Health",
            "expected": "health",
        },
        {
            "name": "Life: Child Education Plan",
            "text": (
                "HDFC Life YoungStar Super Premium. Child Education Plan. "
                "Life Assured: Parent. Child Name: Arjun. "
                "Sum Assured: Rs 50,00,000. Policy Term: 20 years. "
                "Premium Paying Term: 12 years. "
                "Premium Waiver on death of life assured. "
                "Maturity Benefit: Guaranteed additions + bonuses. "
                "Survival Benefit: Paid at child milestone ages (18, 21, 25). "
                "Education Fund for child's higher education."
            ),
            "product_name": "YoungStar Super Premium",
            "insurer_name": "HDFC Life",
            "expected": "life",
        },
        {
            "name": "Motor: Two-Wheeler Comprehensive",
            "text": (
                "Two Wheeler Package Policy. "
                "Registration No: MH01AB1234. "
                "Vehicle: Honda Activa 6G. Cubic Capacity: 109cc. "
                "Make: Honda. Model: Activa 6G. Fuel: Petrol. "
                "IDV: Rs 65,000. RTO: Mumbai. "
                "Section I - Own Damage Premium: Rs 2,500. "
                "Section II - Third Party Premium: Rs 1,680 (5 year TP). "
                "Zero Depreciation: Yes. Roadside Assistance: Yes. "
                "Compulsory PA Cover for Owner-Driver: Rs 15,00,000."
            ),
            "product_name": "Two Wheeler Package Policy",
            "insurer_name": "Acko",
            "expected": "motor",
        },
    ]

    print("=" * 70)
    print("HIBISCUS POLICY CLASSIFIER — TEST SUITE")
    print("=" * 70)

    passed = 0
    failed = 0

    for tc in test_cases:
        result = classifier.classify(
            document_text=tc["text"],
            product_name=tc.get("product_name", ""),
            insurer_name=tc.get("insurer_name", ""),
            uin=tc.get("uin", ""),
        )
        analysis_type = result.get_analysis_type()
        status = "PASS" if analysis_type == tc["expected"] else "FAIL"

        if analysis_type == tc["expected"]:
            passed += 1
        else:
            failed += 1

        print(f"\n{status}  {tc['name']}")
        print(f"  Expected: {tc['expected']}  |  Got: {analysis_type}")
        print(f"  Type: {result.policy_type.value}  |  Confidence: {result.confidence:.3f}")
        print(f"  Tier: {result.tier_used}  |  Level: {result.confidence_level.value}")
        db = result.to_db_fields()
        print(f"  DB: {db['category_name']} → {db['subcategory_name']} ({db['confidence']})")
        if result.warnings:
            print(f"  Warnings: {result.warnings[:3]}")

    print(f"\n{'=' * 70}")
    print(f"RESULTS: {passed}/{passed + failed} passed ({failed} failed)")
    print(f"{'=' * 70}")

    return failed == 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_classifier_tests()
