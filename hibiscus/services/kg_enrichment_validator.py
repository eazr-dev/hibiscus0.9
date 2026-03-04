"""
KG Enrichment Validator
=======================
Validates enrichment data before writing to the Knowledge Graph.
Prevents bad data from corrupting the KG.

Checks:
- Fuzzy match insurer names against known list
- Validate product categories
- Validate numeric ranges (premium, sum insured)
- Flag anomalies for manual review
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Valid product categories (must match KG schema) ──────────────────────────
_VALID_CATEGORIES = {
    "health", "life", "term_life", "endowment", "ulip", "money_back",
    "whole_life", "motor", "travel", "pa", "critical_illness", "home",
    "fire", "marine", "cyber", "pension", "annuity",
}

# ── Numeric range validation ────────────────────────────────────────────────
_PREMIUM_MIN = 500             # ₹500
_PREMIUM_MAX = 50_00_000       # ₹50 lakh
_SI_MIN = 10_000               # ₹10,000
_SI_MAX = 100_00_00_000        # ₹100 crore
_CSR_MIN = 50.0
_CSR_MAX = 100.0
_AGE_MIN = 0
_AGE_MAX = 120

# ── Common insurer name variations for fuzzy matching ───────────────────────
_INSURER_ALIASES = {
    "star health": "Star Health and Allied Insurance",
    "star": "Star Health and Allied Insurance",
    "hdfc ergo": "HDFC ERGO General Insurance",
    "hdfc": "HDFC ERGO General Insurance",
    "icici lombard": "ICICI Lombard General Insurance",
    "icici": "ICICI Lombard General Insurance",
    "bajaj allianz": "Bajaj Allianz General Insurance",
    "bajaj": "Bajaj Allianz General Insurance",
    "care health": "Care Health Insurance",
    "care": "Care Health Insurance",
    "niva bupa": "Niva Bupa Health Insurance",
    "max bupa": "Niva Bupa Health Insurance",
    "lic": "Life Insurance Corporation of India",
    "lic of india": "Life Insurance Corporation of India",
    "sbi life": "SBI Life Insurance",
    "hdfc life": "HDFC Life Insurance",
    "icici pru": "ICICI Prudential Life Insurance",
    "icici prudential": "ICICI Prudential Life Insurance",
    "max life": "Max Life Insurance",
    "tata aia": "Tata AIA Life Insurance",
    "kotak life": "Kotak Mahindra Life Insurance",
    "aditya birla": "Aditya Birla Health Insurance",
    "aditya birla health": "Aditya Birla Health Insurance",
    "new india": "New India Assurance",
    "united india": "United India Insurance",
    "national insurance": "National Insurance Company",
    "oriental insurance": "Oriental Insurance Company",
    "digit": "Go Digit General Insurance",
    "go digit": "Go Digit General Insurance",
    "acko": "Acko General Insurance",
    "royal sundaram": "Royal Sundaram General Insurance",
    "cholamandalam": "Cholamandalam MS General Insurance",
    "chola ms": "Cholamandalam MS General Insurance",
    "reliance general": "Reliance General Insurance",
    "future generali": "Future Generali India Insurance",
    "magma hdi": "Magma HDI General Insurance",
    "iffco tokio": "IFFCO Tokio General Insurance",
    "manipal cigna": "ManipalCigna Health Insurance",
    "cigna": "ManipalCigna Health Insurance",
}


def _tokenize(text: str) -> set:
    """Tokenize text into lowercase words for comparison."""
    return set(re.findall(r'[a-z]+', text.lower()))


def _token_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two strings based on word tokens."""
    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


class EnrichmentValidator:
    """Validates extraction data before KG enrichment."""

    def validate_insurer_name(
        self,
        name: str,
        existing_names: Optional[List[str]] = None,
    ) -> Tuple[str, float, bool]:
        """
        Validate and normalize insurer name.

        Returns:
            (normalized_name, similarity_score, is_new)
            - normalized_name: canonical name from alias map or best fuzzy match
            - similarity_score: 0.0-1.0 confidence in the match
            - is_new: True if this is a genuinely new insurer
        """
        if not name:
            return name, 0.0, False

        name_lower = name.strip().lower()

        # Check alias map first (exact match on common variations)
        if name_lower in _INSURER_ALIASES:
            return _INSURER_ALIASES[name_lower], 1.0, False

        # Fuzzy match against existing KG names
        best_match = None
        best_score = 0.0
        candidates = list(_INSURER_ALIASES.values())
        if existing_names:
            candidates.extend(existing_names)

        seen = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            score = _token_similarity(name, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= 0.7:
            return best_match, best_score, False

        # Genuinely new insurer
        return name.strip(), 0.0, True

    def validate_product_category(self, category: str) -> Tuple[str, bool]:
        """
        Validate and normalize product category.

        Returns:
            (normalized_category, is_valid)
        """
        if not category:
            return "unknown", False

        cat_lower = category.strip().lower().replace(" ", "_").replace("-", "_")

        # Direct match
        if cat_lower in _VALID_CATEGORIES:
            return cat_lower, True

        # Common mappings
        category_map = {
            "health_insurance": "health",
            "health insurance": "health",
            "life_insurance": "life",
            "life insurance": "life",
            "term_insurance": "term_life",
            "term insurance": "term_life",
            "motor_insurance": "motor",
            "car_insurance": "motor",
            "travel_insurance": "travel",
            "personal_accident": "pa",
            "accident": "pa",
        }

        if cat_lower in category_map:
            return category_map[cat_lower], True

        return cat_lower, False

    def validate_numeric_range(
        self,
        value: Any,
        field: str,
    ) -> Tuple[Optional[float], List[str]]:
        """
        Validate a numeric field against expected ranges.

        Returns:
            (validated_value, warnings)
        """
        warnings = []

        if value is None:
            return None, []

        try:
            num = float(value)
        except (ValueError, TypeError):
            return None, [f"{field}: non-numeric value '{value}'"]

        if num < 0:
            return None, [f"{field}: negative value {num}"]

        if field == "premium" or field == "annual_premium":
            if num < _PREMIUM_MIN:
                warnings.append(f"premium unusually low: ₹{num}")
            if num > _PREMIUM_MAX:
                warnings.append(f"premium unusually high: ₹{num}")
                return None, warnings

        elif field in ("sum_insured", "sum_assured"):
            if num < _SI_MIN:
                warnings.append(f"sum_insured unusually low: ₹{num}")
            if num > _SI_MAX:
                warnings.append(f"sum_insured exceeds ₹100 crore: ₹{num}")
                return None, warnings

        elif field == "csr":
            if num < _CSR_MIN or num > _CSR_MAX:
                warnings.append(f"CSR out of range: {num}%")
                return None, warnings

        elif field == "age":
            if num < _AGE_MIN or num > _AGE_MAX:
                return None, [f"age out of range: {num}"]

        return num, warnings

    def validate_extraction(
        self,
        extraction: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """
        Validate a full extraction dict for KG enrichment.

        Returns:
            (is_valid, cleaned_data, warnings)
        """
        warnings = []
        cleaned = {}

        # Insurer name (required)
        insurer = extraction.get("insurer") or extraction.get("insurer_name")
        if not insurer:
            return False, {}, ["missing insurer name"]
        insurer_name, score, is_new = self.validate_insurer_name(insurer)
        cleaned["insurer_name"] = insurer_name
        cleaned["insurer_is_new"] = is_new
        cleaned["insurer_match_score"] = score
        if is_new:
            warnings.append(f"new insurer detected: '{insurer}' (no KG match)")

        # Product name
        product = extraction.get("product_name") or extraction.get("plan_name")
        if product:
            cleaned["product_name"] = product.strip()

        # Category
        cat = extraction.get("policy_type") or extraction.get("category")
        if cat:
            norm_cat, cat_valid = self.validate_product_category(cat)
            cleaned["category"] = norm_cat
            if not cat_valid:
                warnings.append(f"unknown product category: '{cat}'")

        # Numeric fields
        for field in ("annual_premium", "premium"):
            val = extraction.get(field)
            if val is not None:
                validated, field_warnings = self.validate_numeric_range(val, "premium")
                warnings.extend(field_warnings)
                if validated is not None:
                    cleaned["annual_premium"] = validated
                break

        for field in ("sum_insured", "sum_assured"):
            val = extraction.get(field)
            if val is not None:
                validated, field_warnings = self.validate_numeric_range(val, "sum_insured")
                warnings.extend(field_warnings)
                if validated is not None:
                    cleaned["sum_insured"] = validated
                break

        # Features (pass through as-is)
        for feature in ("copay", "room_rent_limit", "deductible", "network_hospitals",
                        "waiting_period", "restoration_benefit", "no_claim_bonus"):
            val = extraction.get(feature)
            if val is not None:
                cleaned[feature] = val

        # At minimum need insurer + some meaningful data
        is_valid = bool(cleaned.get("insurer_name")) and (
            cleaned.get("product_name") or cleaned.get("category") or
            cleaned.get("annual_premium") or cleaned.get("sum_insured")
        )

        return is_valid, cleaned, warnings


# ── Module-level singleton ──────────────────────────────────────────────────
enrichment_validator = EnrichmentValidator()
