"""
Sub-Category Mapper — botproject sub_category → KG category + type
====================================================================
Maps the formal IRDAI sub-category taxonomy from botproject SQL
to the KG's simpler category/type scheme.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Dict, Tuple

from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.subcat_mapper")


# ── Sub-Category → (KG category, KG type) ────────────────────────────────────
# Maps botproject insurance_sub_categories.name → (Product.category, Product.type)

_SUBCAT_MAP: Dict[str, Tuple[str, str]] = {
    # Life Insurance (category_id = 1)
    "Term Life Insurance": ("life_term", "term"),
    "Term with Return of Premium": ("life_term", "term_rop"),
    "Endowment Plans": ("life_endowment", "endowment"),
    "Money-Back Plans": ("life_money_back", "money_back"),
    "Whole Life Insurance": ("life_endowment", "whole_life"),
    "ULIP - Unit Linked Plans": ("ulip", "ulip"),
    "Child Plans": ("life_savings", "child"),
    "Pension / Annuity Plans": ("life_savings", "pension_annuity"),
    "Group Term Life": ("life_term", "group_term"),
    "Micro Insurance (Life)": ("life_savings", "micro"),
    "Savings Plans": ("life_savings", "savings"),

    # Health Insurance (category_id = 2)
    "Individual Health Insurance": ("health", "individual_health"),
    "Family Floater Health Insurance": ("health", "family_floater"),
    "Critical Illness Insurance": ("health", "critical_illness"),
    "Senior Citizen Health Insurance": ("health", "senior_citizen"),
    "Group Health Insurance": ("health", "group_health"),
    "Top-Up / Super Top-Up": ("health", "top_up"),
    "Hospital Daily Cash": ("health", "hospital_cash"),
    "Arogya Sanjeevani (Standard)": ("health", "arogya_sanjeevani"),
    "Disease-Specific Insurance": ("health", "disease_specific"),
    "Maternity Insurance": ("health", "maternity"),
    "Personal Accident (Health)": ("personal_accident", "individual_pa"),

    # Motor Insurance (category_id = 3)
    "Private Car - Comprehensive": ("motor", "car_comprehensive"),
    "Private Car - Third Party Only": ("motor", "car_third_party"),
    "Two-Wheeler - Comprehensive": ("motor", "two_wheeler_comprehensive"),
    "Two-Wheeler - Third Party Only": ("motor", "two_wheeler_third_party"),
    "Commercial Vehicle Insurance": ("motor", "commercial_vehicle"),
    "Standalone Own Damage": ("motor", "standalone_od"),
    "Motor Add-Ons / Riders": ("motor", "add_ons"),

    # Fire Insurance (category_id = 4)
    "Standard Fire & Special Perils": ("fire", "sfsp"),
    "Industrial All Risk (IAR)": ("fire", "industrial_all_risk"),
    "Business Interruption": ("fire", "business_interruption"),
    "Burglary Insurance": ("fire", "burglary"),

    # Marine Insurance (category_id = 5)
    "Marine Cargo": ("marine", "cargo"),
    "Marine Hull": ("marine", "hull"),
    "Inland Transit": ("marine", "inland"),
    "Marine Liability": ("marine", "liability"),

    # Travel Insurance (category_id = 6)
    "Domestic Travel Insurance": ("travel", "domestic"),
    "International Travel Insurance": ("travel", "international"),
    "Student Travel Insurance": ("travel", "student"),
    "Corporate / Multi-Trip Travel": ("travel", "corporate"),

    # Home Insurance (category_id = 7)
    "Bharat Griha Raksha (Standard)": ("home", "bharat_griha_raksha"),
    "Home Structure Insurance": ("home", "structure"),
    "Home Contents Insurance": ("home", "contents"),
    "Householder Package Policy": ("home", "package"),

    # Liability Insurance (category_id = 8)
    "Public Liability Insurance": ("liability", "public"),
    "Product Liability Insurance": ("liability", "product"),
    "Professional Indemnity / E&O": ("liability", "professional_indemnity"),
    "Directors & Officers Liability": ("liability", "dno"),
    "Cyber Liability Insurance": ("liability", "cyber"),
    "Workmen Compensation": ("liability", "workmen_comp"),
    "Commercial General Liability (CGL)": ("liability", "cgl"),

    # Engineering Insurance (category_id = 9)
    "Contractor All Risk (CAR)": ("engineering", "car"),
    "Erection All Risk (EAR)": ("engineering", "ear"),
    "Machinery Breakdown": ("engineering", "machinery"),
    "Electronic Equipment Insurance": ("engineering", "electronic"),
    "Boiler & Pressure Plant": ("engineering", "boiler"),

    # Crop Insurance (category_id = 10)
    "PMFBY - Crop Insurance": ("crop", "pmfby"),
    "Weather-Based Crop Insurance": ("crop", "weather"),
    "Livestock Insurance": ("crop", "livestock"),

    # Personal Accident (category_id = 11)
    "Individual Personal Accident": ("personal_accident", "individual_pa"),
    "Group Personal Accident": ("personal_accident", "group_pa"),
    "PMSBY": ("personal_accident", "pmsby"),

    # Miscellaneous (category_id = 12)
    "Surety Bond Insurance": ("miscellaneous", "surety"),
    "Credit Insurance": ("miscellaneous", "credit"),
    "Cyber Insurance (Retail)": ("miscellaneous", "cyber_retail"),
    "Fidelity Guarantee": ("miscellaneous", "fidelity"),
    "SME Package Insurance": ("miscellaneous", "sme_package"),
    "Shopkeeper Insurance": ("miscellaneous", "shopkeeper"),
}


def map_sub_category(sub_category_name: str) -> Tuple[str, str]:
    """
    Map a botproject sub_category name to (KG category, KG type).

    Returns:
        (category, type) tuple. Falls back to ("unknown", sub_category_name)
        if not found in the map.
    """
    result = _SUBCAT_MAP.get(sub_category_name)
    if result:
        return result

    # Fuzzy fallback: try lowercase match
    lower = sub_category_name.lower()
    for name, mapping in _SUBCAT_MAP.items():
        if name.lower() == lower:
            return mapping

    logger.warning("subcat_mapper_no_match", sub_category=sub_category_name)
    return ("unknown", sub_category_name.lower().replace(" ", "_"))
