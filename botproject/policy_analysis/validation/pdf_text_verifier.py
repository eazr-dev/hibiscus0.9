"""
PRD v2 Check 5: PDF Text Verification.

Verifies extracted field values against the raw PDF text to catch
LLM hallucinations and extraction errors. Pure Python text matching
— NO additional LLM calls.

For each verifiable field, checks if the extracted value can be found
(after normalization) in the raw PDF text. Produces a mismatch report
with severity levels.

Usage:
    from policy_analysis.validation.pdf_text_verifier import verify_against_pdf_text
    result = verify_against_pdf_text(v2_raw_extraction, extracted_text, category)
"""
import logging
import re
from datetime import datetime
from typing import Any

from policy_analysis.schemas.base import (
    FieldCriticality,
    CRITICALITY_MAPS,
)

logger = logging.getLogger(__name__)

# ==================== MATCH TYPE CONSTANTS ====================

EXACT_STRING = "exact_string"
NUMERIC = "numeric"
DATE = "date"
PERCENTAGE = "percentage"
NAME_STRING = "name_string"

# ==================== PER-TYPE VERIFIABLE FIELD MAPS ====================

PHONE_NUMBER = "phone_number"

_COMMON_VERIFIABLE = {
    "policyNumber": EXACT_STRING,
    "uin": EXACT_STRING,
    "insurerName": NAME_STRING,
    "policyPeriodStart": DATE,
    "policyPeriodEnd": DATE,
    "insurerTollFree": PHONE_NUMBER,
    "claimEmail": EXACT_STRING,
}

_HEALTH_VERIFIABLE = {
    **_COMMON_VERIFIABLE,
    "policyHolderName": NAME_STRING,
    "sumInsured": NUMERIC,
    "basePremium": NUMERIC,
    "gst": NUMERIC,
    "totalPremium": NUMERIC,
    "roomRentLimit": NUMERIC,
    "ambulanceCover": NUMERIC,
    "preHospitalization": EXACT_STRING,
    "postHospitalization": EXACT_STRING,
    "preExistingDiseaseWaiting": EXACT_STRING,
    "generalCopay": PERCENTAGE,
    "ncbPercentage": PERCENTAGE,
    "policyIssueDate": DATE,
}

_MOTOR_VERIFIABLE = {
    **_COMMON_VERIFIABLE,
    "ownerName": NAME_STRING,
    "ownerPan": EXACT_STRING,
    "ownerEmail": EXACT_STRING,
    "ownerContact": PHONE_NUMBER,
    "registrationNumber": EXACT_STRING,
    "engineNumber": EXACT_STRING,
    "chassisNumber": EXACT_STRING,
    "vehicleMake": NAME_STRING,
    "vehicleModel": NAME_STRING,
    "idv": NUMERIC,
    "odPremium": NUMERIC,
    "tpPremium": NUMERIC,
    "grossPremium": NUMERIC,
    "gst": NUMERIC,
    "totalPremium": NUMERIC,
    "ncbPercentage": PERCENTAGE,
    "compulsoryDeductible": NUMERIC,
    "paOwnerCover": NUMERIC,
    "registrationDate": DATE,
}

_LIFE_VERIFIABLE = {
    **_COMMON_VERIFIABLE,
    "policyholderName": NAME_STRING,
    "lifeAssuredName": NAME_STRING,
    "sumAssured": NUMERIC,
    "premiumAmount": NUMERIC,
    "basePremium": NUMERIC,
    "gst": NUMERIC,
    "totalPremium": NUMERIC,
    "policyTerm": NUMERIC,
    "premiumPayingTerm": NUMERIC,
    "surrenderValue": NUMERIC,
    "policyIssueDate": DATE,
    "maturityDate": DATE,
    "policyholderDob": DATE,
    "lifeAssuredDob": DATE,
}

_PA_VERIFIABLE = {
    **_COMMON_VERIFIABLE,
    "policyHolderName": NAME_STRING,
    "paSumInsured": NUMERIC,
    "accidentalDeathBenefitPercentage": PERCENTAGE,
    "permanentTotalDisabilityPercentage": PERCENTAGE,
    "totalPremium": NUMERIC,
    "basePremium": NUMERIC,
    "gst": NUMERIC,
}

_TRAVEL_VERIFIABLE = {
    **_COMMON_VERIFIABLE,
    "policyHolderName": NAME_STRING,
    "medicalExpenses": NUMERIC,
    "tripCancellation": NUMERIC,
    "baggageLoss": NUMERIC,
    "personalLiability": NUMERIC,
    "totalPremium": NUMERIC,
    "travelTotalPremium": NUMERIC,
    "tripStartDate": DATE,
    "tripEndDate": DATE,
    "policyIssueDate": DATE,
    "emergencyMedicalEvacuation": NUMERIC,
}

_VERIFIABLE_FIELDS_MAP = {
    "health": _HEALTH_VERIFIABLE,
    "motor": _MOTOR_VERIFIABLE,
    "life": _LIFE_VERIFIABLE,
    "pa": _PA_VERIFIABLE,
    "travel": _TRAVEL_VERIFIABLE,
}

# Fields that should NEVER be verified (interpretive, computed, boolean)
_SKIP_FIELDS = {
    # Interpretive / summarized text
    "keyBenefits", "exclusions", "permanentExclusions", "conditionalExclusions",
    "preExistingConditions", "pedSpecificExclusions", "specificDiseasesList",
    "otherSubLimits", "otherExclusions", "claimDocuments",
    "coverageIncludes", "tripCancellationCoveredReasons",
    "tripCancellationNotCoveredReasons", "tripDelayCoveredExpenses",
    "ptdConditions", "paStandardExclusions", "claimProcess",
    # Company stats (not in PDF)
    "claimSettlementRatio", "networkHospitalsCount",
    # Computed / boolean / status
    "pedWaitingPeriodCompleted", "accidentCoveredFromDay1",
    "cashlessFacility", "mentalHealthCovered",
    "consumablesCoverage", "claimShield", "ncbShield", "inflationShield",
    "pedStatus", "policyStatus", "policyType", "coverType", "productType",
    "vehicleClass", "vehicleCategory", "fuelType", "ownerType",
    "tripType", "travelType", "geographicCoverage",
    "paInsuranceType", "paPolicySubType",
    # Boolean add-on flags
    "zeroDepreciation", "engineProtection", "returnToInvoice",
    "roadsideAssistance", "consumables", "tyreCover", "keyCover",
    "ncbProtect", "ncbProtection", "emiBreakerCover", "passengerCover",
    "windshieldCover", "electricVehicleCover", "batteryProtect",
    "hasAddOn", "dayCareProcedures", "ayushTreatment",
    "covidTreatmentCovered", "covidQuarantineCovered",
    "preExistingCovered", "maternityCovered",
    "doubleIndemnityApplicable", "permanentTotalDisabilityCovered",
    "permanentPartialDisabilityCovered", "temporaryTotalDisabilityCovered",
    "medicalExpensesCovered", "cashlessNetworkAvailable",
    "schengenCompliant",
    # Complex nested objects (verified separately if needed)
    "hypothecation", "portability", "fundOptions", "ageBasedCopay",
    "diseaseSpecificCopay", "addOnPoliciesList", "riders", "nominees",
    "ppdSchedule", "modalPremiumBreakdown", "otherAddOnPremiums",
    # Frequency / category strings
    "premiumFrequency", "paPremiumFrequency", "bonusType",
    "ttdBenefitType", "medicalExpensesLimitType",
    # Restoration / descriptions
    "restoration", "deathBenefit",
}

# ==================== HELPERS ====================


def _is_confidence_field(val: Any) -> bool:
    """Check if a value looks like a ConfidenceField dict."""
    return (
        isinstance(val, dict)
        and "confidence" in val
        and "value" in val
    )


# ==================== NORMALIZATION HELPERS ====================


def _normalize_text_for_search(text: str) -> str:
    """Lowercase, collapse whitespace, strip."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.lower()).strip()


def _normalize_number(value: Any) -> float | None:
    """Parse numeric value from various formats.

    Handles: 500000, 5,00,000, Rs. 5,00,000, ₹500000, 5 Lakh, 1 Crore
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None

    text = value.strip()
    if not text:
        return None

    # Strip currency symbols and common prefixes
    text = re.sub(r'[₹$]', '', text)
    text = re.sub(r'\b(Rs\.?|INR|USD|EUR)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'/-$', '', text).strip()

    # Handle "N Lakh" / "N Crore" forms
    lakh_match = re.match(r'^([\d,.]+)\s*(?:lakh|lakhs|lac)\b', text, re.IGNORECASE)
    if lakh_match:
        try:
            return float(lakh_match.group(1).replace(',', '')) * 100000
        except ValueError:
            pass

    crore_match = re.match(r'^([\d,.]+)\s*(?:crore|crores|cr)\b', text, re.IGNORECASE)
    if crore_match:
        try:
            return float(crore_match.group(1).replace(',', '')) * 10000000
        except ValueError:
            pass

    # Strip commas and try direct parse
    cleaned = text.replace(',', '').strip()
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _normalize_policy_number(value: str) -> str:
    """Strip spaces, hyphens, slashes, dots for policy number comparison."""
    if not value:
        return ""
    return re.sub(r'[\s\-/.\\\']', '', value).lower()


def _parse_date(value: str) -> datetime | None:
    """Try to parse a date string in multiple formats."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d-%b-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%B %d, %Y",
        "%d.%m.%Y",
        "%d-%B-%Y",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _date_search_variants(dt: datetime) -> list[str]:
    """Generate all plausible text representations of a date for searching.

    Given a datetime object, produce variants like:
    23/03/2025, 23-03-2025, 23 Mar 2025, 23-Mar-2025, March 23, 2025, 2025-03-23, etc.
    """
    variants = []
    day = dt.day
    month = dt.month
    year = dt.year

    # DD/MM/YYYY and DD-MM-YYYY (with and without zero-padding)
    for sep in ('/', '-', '.'):
        variants.append(f"{day:02d}{sep}{month:02d}{sep}{year}")
        if day < 10 or month < 10:
            variants.append(f"{day}{sep}{month}{sep}{year}")

    # DD Mon YYYY, DD-Mon-YYYY
    short_month = dt.strftime("%b")  # "Mar"
    long_month = dt.strftime("%B")   # "March"
    variants.append(f"{day:02d} {short_month} {year}")
    variants.append(f"{day} {short_month} {year}")
    variants.append(f"{day:02d}-{short_month}-{year}")
    variants.append(f"{day}-{short_month}-{year}")
    variants.append(f"{day:02d} {long_month} {year}")
    variants.append(f"{day} {long_month} {year}")

    # Month DD, YYYY
    variants.append(f"{long_month} {day}, {year}")
    variants.append(f"{long_month} {day:02d}, {year}")

    # ISO: YYYY-MM-DD
    variants.append(f"{year}-{month:02d}-{day:02d}")

    return variants


# ==================== SEARCH HELPERS ====================


def _extract_all_numbers_from_text(text: str) -> list[float]:
    """Pre-extract all numeric values from PDF text for fast lookup.

    Handles Indian notation (5,00,000), standard commas, decimals,
    and Lakh/Crore text forms.
    """
    numbers = set()

    # Pattern: numbers with optional commas and decimal
    for match in re.finditer(r'\b(\d[\d,]*(?:\.\d+)?)\b', text):
        raw = match.group(1)
        cleaned = raw.replace(',', '')
        try:
            num = float(cleaned)
            if num > 0:
                numbers.add(num)
        except ValueError:
            pass

    # "N Lakh" / "N Lakhs" / "N Lac"
    for match in re.finditer(
        r'(\d+(?:[.,]\d+)?)\s*(?:lakh|lakhs|lac)\b', text, re.IGNORECASE
    ):
        try:
            numbers.add(float(match.group(1).replace(',', '')) * 100000)
        except ValueError:
            pass

    # "N Crore" / "N Cr"
    for match in re.finditer(
        r'(\d+(?:[.,]\d+)?)\s*(?:crore|crores|cr)\b', text, re.IGNORECASE
    ):
        try:
            numbers.add(float(match.group(1).replace(',', '')) * 10000000)
        except ValueError:
            pass

    return sorted(numbers)


def _text_contains_number(
    pdf_numbers: list[float],
    target: float,
    tolerance_pct: float = 0.005,
) -> bool:
    """Check if target number appears in the pre-extracted numbers list.

    Uses tolerance of max(1.0, target * tolerance_pct) to handle rounding.
    """
    if target == 0:
        return True
    abs_tolerance = max(1.0, abs(target) * tolerance_pct)
    for num in pdf_numbers:
        if abs(num - target) <= abs_tolerance:
            return True
    return False


def _text_contains_string(normalized_text: str, target: str) -> bool:
    """Case-insensitive substring search after whitespace normalization."""
    if not target:
        return True
    normalized_target = re.sub(r'\s+', ' ', target.lower()).strip()
    if not normalized_target:
        return True
    return normalized_target in normalized_text


def _text_contains_date(normalized_text: str, date_str: str) -> bool:
    """Check if any normalized date representation appears in text."""
    dt = _parse_date(date_str)
    if dt is None:
        return True  # Can't parse date — don't flag as mismatch

    variants = _date_search_variants(dt)
    for variant in variants:
        if variant.lower() in normalized_text:
            return True
    return False


def _text_contains_percentage(normalized_text: str, value: Any) -> bool:
    """Check if percentage value appears in text."""
    num = _normalize_number(value)
    if num is None:
        return True  # Can't parse — don't flag

    # Search for "N%" and "N %" and bare "N"
    candidates = [
        f"{int(num)}%",
        f"{int(num)} %",
        f"{num}%",
        f"{num} %",
    ]
    # Also try without decimal if it's a whole number
    if num == int(num):
        candidates.append(str(int(num)))

    for candidate in candidates:
        if candidate.lower() in normalized_text:
            return True
    return False


def _text_contains_phone(normalized_text: str, phone: str) -> bool:
    """Check if phone number appears in PDF text (digits-only comparison).

    Strips all non-digit characters from both the phone value and PDF text,
    then checks if the digit sequence appears. This handles formatting
    differences like "1800-2666-336" vs "18002666336" vs "1800 2666 336".
    """
    if not phone:
        return True
    digits = re.sub(r'\D', '', str(phone))
    if len(digits) < 6:
        return True  # Too short to verify meaningfully
    # Build a digits-only version of the PDF text for searching
    text_digits = re.sub(r'\D', '', normalized_text)
    return digits in text_digits


def _text_contains_name(normalized_text: str, name: str) -> bool:
    """Check if all significant parts of a name appear in text.

    Split name into words, check each exists in text.
    Require all words to match for names with <= 3 words,
    or at least (total - 1) words for longer names.
    """
    if not name:
        return True
    words = [w for w in name.lower().split() if len(w) > 1]
    if not words:
        return True

    matched_words = sum(1 for w in words if w in normalized_text)

    if len(words) <= 3:
        return matched_words >= len(words)
    else:
        return matched_words >= len(words) - 1


# ==================== CORE VERIFICATION ====================


def _verify_single_field(
    field_name: str,
    field_data: dict,
    pdf_text_normalized: str,
    pdf_text_original: str,
    pdf_numbers: list[float],
    match_type: str,
    criticality: FieldCriticality | None,
) -> dict | None:
    """Verify one field against PDF text.

    Returns mismatch dict if NOT found, or None if matched/skipped.
    """
    value = field_data.get("value")
    if value is None or value == "":
        return None  # Nothing to verify

    # Skip numeric zero values
    if isinstance(value, (int, float)) and value == 0:
        return None

    matched = False

    if match_type == EXACT_STRING:
        if field_name in ("policyNumber", "uin", "registrationNumber",
                          "engineNumber", "chassisNumber"):
            norm_val = _normalize_policy_number(str(value))
            if len(norm_val) < 3:
                return None  # Too short to verify meaningfully
            norm_text = _normalize_policy_number(pdf_text_original)
            matched = norm_val in norm_text
        else:
            # For text like "60 days", "30 Days", "24 months"
            str_val = str(value).strip()
            if not str_val:
                return None
            matched = _text_contains_string(pdf_text_normalized, str_val)
            # Also try just the numeric part (e.g., "60" for "60 days")
            if not matched:
                num_part = re.search(r'\d+', str_val)
                if num_part:
                    matched = num_part.group() in pdf_text_normalized

    elif match_type == NUMERIC:
        num = _normalize_number(value)
        if num is None or num <= 0:
            return None  # Can't verify non-numeric/zero
        matched = _text_contains_number(pdf_numbers, num)

    elif match_type == DATE:
        matched = _text_contains_date(pdf_text_normalized, str(value))

    elif match_type == PERCENTAGE:
        matched = _text_contains_percentage(pdf_text_normalized, value)

    elif match_type == NAME_STRING:
        matched = _text_contains_name(pdf_text_normalized, str(value))

    elif match_type == PHONE_NUMBER:
        matched = _text_contains_phone(pdf_text_normalized, str(value))

    if matched:
        return None  # Verified successfully

    # Determine severity
    severity_str = "standard"
    if criticality == FieldCriticality.CRITICAL:
        severity_str = "critical"
    elif criticality == FieldCriticality.IMPORTANT:
        severity_str = "important"

    display_value = value if not isinstance(value, (list, dict)) else str(value)[:200]

    return {
        "field": field_name,
        "extractedValue": display_value,
        "matchType": match_type,
        "severity": severity_str,
        "message": f"Extracted '{display_value}' for '{field_name}' but could not find this value in the PDF text",
    }


def _verify_array_field(
    field_name: str,
    field_data: dict,
    pdf_text_normalized: str,
    pdf_numbers: list[float],
) -> tuple[int, int, list[dict]]:
    """Verify individual elements within array fields (insuredMembers, etc.).

    Returns: (verified_count, matched_count, mismatches)
    """
    value = field_data.get("value") if _is_confidence_field(field_data) else field_data
    if not isinstance(value, list):
        return 0, 0, []

    verified = 0
    matched = 0
    mismatches = []

    for i, item in enumerate(value):
        if not isinstance(item, dict):
            continue

        # Check member name
        name = (
            item.get("memberName")
            or item.get("name")
            or item.get("nomineeName")
            or item.get("travellerName")
        )
        if name and isinstance(name, str) and name.strip():
            verified += 1
            if _text_contains_name(pdf_text_normalized, name):
                matched += 1
            else:
                mismatches.append({
                    "field": f"{field_name}[{i}].name",
                    "extractedValue": name,
                    "matchType": NAME_STRING,
                    "severity": "important",
                    "message": f"Member name '{name}' not found in PDF text",
                })

        # Check member age (as a number in PDF)
        age = item.get("memberAge") or item.get("age")
        if age and isinstance(age, (int, float)) and age > 0:
            verified += 1
            if _text_contains_number(pdf_numbers, float(age)):
                matched += 1
            # Don't flag age mismatches — ages appear in many contexts

    return verified, matched, mismatches


# ==================== PUBLIC API ====================


def verify_against_pdf_text(
    v2_raw_extraction: dict,
    extracted_text: str,
    category: str,
) -> dict:
    """Verify extracted field values against raw PDF text.

    Compares each verifiable field's value against the original PDF text
    using type-appropriate matching (exact string, numeric with tolerance,
    multi-format dates, percentage, name matching).

    Args:
        v2_raw_extraction: Raw v2 extraction dict (ConfidenceField format).
        extracted_text: Full PDF text (pre-enrichment, without web data).
        category: Detected policy category (health/motor/life/pa/travel).

    Returns:
        {
            "passed": bool,           # True if no critical mismatches
            "fieldsVerified": int,    # Fields we attempted to verify
            "fieldsMatched": int,     # Fields found in PDF text
            "fieldsMismatched": int,  # Fields NOT found in PDF text
            "fieldsSkipped": int,     # Fields not verifiable
            "mismatches": [...],      # Details of each mismatch
            "verifiedFields": [...]   # Field names confirmed in PDF
        }
    """
    if not v2_raw_extraction or not extracted_text:
        return {
            "passed": True,
            "fieldsVerified": 0,
            "fieldsMatched": 0,
            "fieldsMismatched": 0,
            "fieldsSkipped": 0,
            "mismatches": [],
            "verifiedFields": [],
        }

    # Pre-compute (done ONCE for performance)
    pdf_text_normalized = _normalize_text_for_search(extracted_text)
    pdf_numbers = _extract_all_numbers_from_text(extracted_text)

    verifiable_fields = _VERIFIABLE_FIELDS_MAP.get(category, {})
    criticality_map = CRITICALITY_MAPS.get(category, {})

    verified_count = 0
    matched_count = 0
    skipped_count = 0
    mismatches = []
    verified_fields = []

    # Array fields to handle specially
    array_fields = {"insuredMembers", "travellers", "nominees", "paInsuredMembers"}

    for field_name, field_data in v2_raw_extraction.items():
        # Skip non-ConfidenceField entries
        if not _is_confidence_field(field_data):
            skipped_count += 1
            continue

        value = field_data.get("value")

        # Skip null values
        if value is None:
            skipped_count += 1
            continue

        # Skip fields in the skip list
        if field_name in _SKIP_FIELDS:
            skipped_count += 1
            continue

        # Handle array fields
        if field_name in array_fields:
            v, m, mm = _verify_array_field(
                field_name, field_data,
                pdf_text_normalized, pdf_numbers,
            )
            verified_count += v
            matched_count += m
            mismatches.extend(mm)
            if v > 0 and not mm:
                verified_fields.append(field_name)
            continue

        # Get match type for this field
        match_type = verifiable_fields.get(field_name)
        if match_type is None:
            skipped_count += 1
            continue

        # Verify the field
        criticality = criticality_map.get(field_name)
        mismatch = _verify_single_field(
            field_name, field_data,
            pdf_text_normalized, extracted_text,
            pdf_numbers, match_type, criticality,
        )

        verified_count += 1
        if mismatch is None:
            matched_count += 1
            verified_fields.append(field_name)
        else:
            mismatches.append(mismatch)

    # "passed" = no critical mismatches
    has_critical_mismatch = any(
        m.get("severity") == "critical" for m in mismatches
    )
    passed = not has_critical_mismatch

    logger.info(
        f"Check 5 PDF text verification [{category}]: "
        f"verified={verified_count}, matched={matched_count}, "
        f"mismatched={len(mismatches)}, skipped={skipped_count}, "
        f"passed={'PASS' if passed else 'FAIL'}"
    )

    return {
        "passed": passed,
        "fieldsVerified": verified_count,
        "fieldsMatched": matched_count,
        "fieldsMismatched": len(mismatches),
        "fieldsSkipped": skipped_count,
        "mismatches": mismatches,
        "verifiedFields": verified_fields,
    }
