"""
Name Mapper — botproject legal_name → Hibiscus KG insurer_name
===============================================================
Maps the full legal names used in botproject SQL to the shorter
names used in the Hibiscus Knowledge Graph.

Strategy:
1. Exact match from pre-built map (covers all 60 companies)
2. Token-overlap fuzzy fallback for future additions
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
from typing import Dict, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.name_mapper")


# ── Pre-built Map ─────────────────────────────────────────────────────────────
# botproject legal_name → Hibiscus KG insurer name
# Built by comparing 01_foundation.sql companies against insurers.py seed data.

_LEGAL_TO_KG: Dict[str, str] = {
    # Life Insurance Companies
    "Life Insurance Corporation of India": "Life Insurance Corporation of India",
    "HDFC Life Insurance Company Limited": "HDFC Life Insurance",
    "ICICI Prudential Life Insurance Company Limited": "ICICI Prudential Life Insurance",
    "SBI Life Insurance Company Limited": "SBI Life Insurance",
    "Axis Max Life Insurance Limited": "Max Life Insurance",
    "Kotak Mahindra Life Insurance Company Limited": "Kotak Mahindra Life Insurance",
    "Aditya Birla Sun Life Insurance Company Limited": "Aditya Birla Sun Life Insurance",
    "TATA AIA Life Insurance Company Limited": "Tata AIA Life Insurance",
    "Bajaj Life Insurance Limited": "Bajaj Allianz Life Insurance",
    "PNB MetLife India Insurance Company Limited": "PNB MetLife India Insurance",
    "IndusInd Nippon Life Insurance Company Limited": "IndusInd Nippon Life Insurance",
    "Aviva Life Insurance Company India Limited": "Aviva Life Insurance India",
    "Sahara India Life Insurance Company Limited": "Sahara India Life Insurance",
    "Shriram Life Insurance Company Limited": "Shriram Life Insurance",
    "Bharti AXA Life Insurance Company Limited": "Bharti AXA Life Insurance",
    "Generali Central Life Insurance Company Limited": "Future Generali India Life Insurance",
    "Ageas Federal Life Insurance Company Limited": "Ageas Federal Life Insurance",
    "Canara HSBC Life Insurance Company Limited": "Canara HSBC Life Insurance",
    "Bandhan Life Insurance Limited": "Bandhan Life Insurance",
    "Pramerica Life Insurance Company Limited": "Pramerica Life Insurance",
    "Star Union Dai-Ichi Life Insurance Company Limited": "Star Union Dai-ichi Life Insurance",
    "IndiaFirst Life Insurance Company Limited": "IndiaFirst Life Insurance",
    "Edelweiss Life Insurance Company Limited": "Edelweiss Tokio Life Insurance",
    "CreditAccess Life Insurance Limited": "CreditAccess Life Insurance",
    "Acko Life Insurance Limited": "Acko Life Insurance",
    "Go Digit Life Insurance Limited": "Go Digit Life Insurance",

    # General Insurance Companies
    "The New India Assurance Company Limited": "New India Assurance",
    "National Insurance Company Limited": "National Insurance",
    "The Oriental Insurance Company Limited": "Oriental Insurance",
    "United India Insurance Company Limited": "United India Insurance",
    "ICICI Lombard General Insurance Company Limited": "ICICI Lombard General Insurance",
    "HDFC ERGO General Insurance Company Limited": "HDFC ERGO General Insurance",
    "Bajaj General Insurance Limited": "Bajaj Allianz General Insurance",
    "Tata AIG General Insurance Company Limited": "TATA AIG General Insurance",
    "Cholamandalam MS General Insurance Company Limited": "Chola MS General Insurance",
    "SBI General Insurance Company Limited": "SBI General Insurance",
    "Go Digit General Insurance Limited": "Digit Insurance",
    "IFFCO TOKIO General Insurance Company Limited": "IFFCO Tokio General Insurance",
    "Royal Sundaram General Insurance Company Limited": "Royal Sundaram General Insurance",
    "Zurich Kotak General Insurance Company Limited": "Zurich Kotak General Insurance",
    "Shriram General Insurance Company Limited": "Shriram General Insurance",
    "Universal Sompo General Insurance Company Limited": "Universal Sompo General Insurance",
    "Acko General Insurance Limited": "Acko General Insurance",
    "Generali Central Insurance Company Limited": "Future Generali India Insurance",
    "IndusInd General Insurance Company Limited": "Reliance General Insurance",
    "Raheja QBE General Insurance Company Limited": "Raheja QBE General Insurance",
    "Liberty General Insurance Limited": "Liberty General Insurance",
    "Magma General Insurance Limited": "Magma HDI General Insurance",
    "Navi General Insurance Limited": "Navi General Insurance",
    "Zuno General Insurance Limited": "Zuno General Insurance",
    "Kshema General Insurance Limited": "Kshema General Insurance",
    "Agriculture Insurance Company of India Limited": "Agriculture Insurance Company of India",
    "ECGC Limited": "ECGC",

    # Standalone Health Insurance Companies
    "Star Health and Allied Insurance Company Limited": "Star Health and Allied Insurance",
    "Care Health Insurance Limited": "Care Health Insurance",
    "Niva Bupa Health Insurance Company Limited": "Niva Bupa Health Insurance",
    "Aditya Birla Health Insurance Company Limited": "Aditya Birla Health Insurance",
    "Manipal Cigna Health Insurance Company Limited": "ManipalCigna Health Insurance",
    "Galaxy Health Insurance Company Limited": "Galaxy Health Insurance",
    "Narayana Health Insurance Limited": "Narayana Health Insurance",
}

# Reverse map for lookups
_KG_TO_LEGAL: Dict[str, str] = {v: k for k, v in _LEGAL_TO_KG.items()}


def legal_to_kg(legal_name: str) -> str:
    """
    Map a botproject legal_name to the KG insurer name.
    Falls back to fuzzy matching, then to stripping common suffixes.
    """
    # Exact match
    if legal_name in _LEGAL_TO_KG:
        return _LEGAL_TO_KG[legal_name]

    # Fuzzy: strip common legal suffixes
    cleaned = _strip_legal_suffixes(legal_name)
    for legal, kg in _LEGAL_TO_KG.items():
        if _strip_legal_suffixes(legal) == cleaned:
            return kg

    # Token overlap
    best_match = _fuzzy_match(legal_name)
    if best_match:
        return best_match

    # Last resort: strip suffixes and use as-is (will create new Insurer node)
    logger.warning("name_mapper_no_match", legal_name=legal_name, using_cleaned=cleaned)
    return cleaned


def _strip_legal_suffixes(name: str) -> str:
    """Remove common legal entity suffixes."""
    suffixes = [
        " Limited", " Ltd", " Company", " of India",
        " Private", " Pvt", " Corporation",
    ]
    result = name
    for suffix in suffixes:
        result = re.sub(re.escape(suffix) + r"\.?$", "", result, flags=re.IGNORECASE)
        result = re.sub(re.escape(suffix) + r"\.?\s", " ", result, flags=re.IGNORECASE)
    return result.strip()


def _fuzzy_match(legal_name: str) -> Optional[str]:
    """Token-overlap fuzzy match against known KG names."""
    legal_tokens = set(_normalize_tokens(legal_name))
    if not legal_tokens:
        return None

    best_score = 0.0
    best_name = None

    for kg_name in _KG_TO_LEGAL:
        kg_tokens = set(_normalize_tokens(kg_name))
        if not kg_tokens:
            continue
        overlap = len(legal_tokens & kg_tokens)
        score = overlap / max(len(legal_tokens), len(kg_tokens))
        if score > best_score:
            best_score = score
            best_name = kg_name

    if best_score >= 0.5:
        return best_name
    return None


def _normalize_tokens(name: str) -> list:
    """Normalize name to lowercase tokens, removing filler words."""
    stop_words = {"limited", "ltd", "company", "of", "india", "the", "private", "pvt"}
    tokens = re.findall(r"\w+", name.lower())
    return [t for t in tokens if t not in stop_words]


def get_insurer_type_from_company_type(company_type: str, sector: str) -> str:
    """Map botproject company_type/sector to KG insurer type."""
    if company_type == "life":
        return "public_life" if sector == "public" else "private_life"
    if company_type == "health":
        return "standalone_health"
    if company_type == "general":
        if sector == "public":
            return "general"
        if sector == "specialized":
            return "general"
        return "private_general"
    return "general"
