"""
V1 Compatibility Mapper — PRD v2 ConfidenceField → v1 nested format.

Converts the new {value, source_page, confidence} extraction format back
to the nested format used by the existing pipeline:
  extracted_data = {
      "policyNumber": "...",
      "insuranceProvider": "...",
      "categorySpecificData": { ... all type-specific flat fields ... },
      ...
  }

This allows the existing 6000-line orchestrator body to work unchanged while
we ship PRD v2 extraction under the hood.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---- Top-level field mappings ----
# v2 field name → v1 top-level field name
# These fields are read via extracted_data.get("v1_name") in the orchestrator.
_TOP_LEVEL_MAP = {
    "policyNumber": "policyNumber",
    "insurerName": "insuranceProvider",
    "policyHolderName": "policyHolderName",
    "policyholderName": "policyHolderName",     # life variant
    "ownerName": "policyHolderName",             # motor variant
    "lifeAssuredName": "policyHolderName",       # life variant
    "travellerName": "policyHolderName",         # travel variant
    "primaryTravellerName": "policyHolderName",  # travel variant
    "policyType": "policyType",
    "uin": "uin",
    "productName": "productName",
    "policyPeriodStart": "startDate",
    "policyPeriodEnd": "endDate",
    "policyIssueDate": "startDate",              # life variant
    "premiumFrequency": "premiumFrequency",
    "paPremiumFrequency": "premiumFrequency",    # PA variant
}

# Fields that provide coverage amount (checked in priority order per type)
_COVERAGE_FIELDS = {
    "health": ["sumInsured"],
    "motor": ["idv"],
    "life": ["sumAssured"],
    "pa": ["paSumInsured"],
    "travel": ["medicalExpenses"],
}

# Fields that provide premium (checked in priority order)
_PREMIUM_FIELDS = ["totalPremium", "travelTotalPremium", "premiumAmount"]


def _extract_value(field_data: Any) -> Any:
    """Extract the bare value from a ConfidenceField or pass through raw values.

    Handles:
    - dict with "value" key → returns the value
    - list of dicts with "value" keys → recursively extracts
    - anything else → returns as-is (backward compat)
    """
    if isinstance(field_data, dict):
        if "value" in field_data and ("confidence" in field_data or "source_page" in field_data):
            inner = field_data["value"]
            if isinstance(inner, list):
                return [_extract_value(item) for item in inner]
            if isinstance(inner, dict):
                return {k: _extract_value(v) for k, v in inner.items()}
            return inner
        else:
            return {k: _extract_value(v) for k, v in field_data.items()}
    elif isinstance(field_data, list):
        return [_extract_value(item) for item in field_data]
    else:
        return field_data


def _safe_num(val: Any) -> float:
    """Safely coerce a value to a number."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("$", "").strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0
    return 0


def v2_to_v1(v2_extraction: dict, category: str) -> dict:
    """Convert PRD v2 extraction result to v1 nested format.

    Produces the exact structure the orchestrator expects:
    {
        "policyNumber": "...",
        "insuranceProvider": "...",
        "policyType": "...",
        "coverageAmount": 0,
        "premium": 0,
        "premiumFrequency": "...",
        "startDate": "...",
        "endDate": "...",
        "policyHolderName": "...",
        "uin": "...",
        "productName": "...",
        "keyBenefits": [...],
        "exclusions": [...],
        "waitingPeriods": [...],
        "criticalAreas": [...],
        "categorySpecificData": { ...all flat type-specific values... }
    }

    Args:
        v2_extraction: Raw LLM response parsed as dict (ConfidenceField format).
        category: Detected category (health/motor/life/pa/travel).

    Returns:
        Dict matching v1 extracted_data format.
    """
    if not v2_extraction:
        return {}

    # Step 1: Strip ConfidenceField wrappers → flat type-specific data
    flat = {}
    for key, field_data in v2_extraction.items():
        flat[key] = _extract_value(field_data)

    # Step 2: Build top-level fields
    top = {}
    for v2_name, v1_name in _TOP_LEVEL_MAP.items():
        val = flat.get(v2_name)
        if val is not None and v1_name not in top:
            top[v1_name] = val

    # Step 3: Derive coverageAmount
    coverage_fields = _COVERAGE_FIELDS.get(category, [])
    for f in coverage_fields:
        val = flat.get(f)
        if val is not None:
            top["coverageAmount"] = _safe_num(val)
            break
    top.setdefault("coverageAmount", 0)

    # Step 4: Derive premium
    for f in _PREMIUM_FIELDS:
        val = flat.get(f)
        if val is not None:
            top["premium"] = _safe_num(val)
            break
    top.setdefault("premium", 0)

    # Step 5: Build arrays from type-specific fields
    # keyBenefits — not directly in v2 prompts, synthesize empty
    top.setdefault("keyBenefits", [])
    # exclusions — combine from various exclusion fields
    exclusions = []
    for exc_field in ["permanentExclusions", "otherExclusions", "paStandardExclusions"]:
        exc = flat.get(exc_field)
        if isinstance(exc, list):
            exclusions.extend(exc)
    top["exclusions"] = exclusions if exclusions else []

    # waitingPeriods — structured objects
    waitings = []
    _wp_labels = {
        "initialWaitingPeriod": "Initial Waiting",
        "preExistingDiseaseWaiting": "Pre-Existing Disease",
        "specificDiseaseWaiting": "Specific Disease",
        "maternityWaiting": "Maternity",
    }
    for wp_field, wp_label in _wp_labels.items():
        wp_val = flat.get(wp_field)
        if wp_val and wp_val is not None:
            waitings.append({"type": wp_label, "period": str(wp_val), "field": wp_field})
    top["waitingPeriods"] = waitings

    # criticalAreas — leave empty (computed downstream)
    top.setdefault("criticalAreas", [])

    # Step 6: Put ALL flat data into categorySpecificData
    top["categorySpecificData"] = flat

    # Step 7: Derive insuredName from insuredMembers when policyHolder ≠ primary insured
    # For dependant policies (e.g., parent policies), the policyholder is the proposer
    # but the actual insured person is the dependant member marked as "Self"
    _policy_holder = top.get("policyHolderName", "")
    _insured_members = flat.get("insuredMembers")
    if isinstance(_insured_members, list) and _insured_members:
        # Find the "Self" member
        _self_member = None
        for _m in _insured_members:
            if isinstance(_m, dict) and str(_m.get("memberRelationship", "")).lower() == "self":
                _self_member = _m
                break
        # If only one member and no "Self", use first member
        if not _self_member and len(_insured_members) == 1:
            _self_member = _insured_members[0] if isinstance(_insured_members[0], dict) else None

        if _self_member and _self_member.get("memberName"):
            _member_name = str(_self_member["memberName"]).strip()
            if _member_name and _member_name.lower() != _policy_holder.lower():
                top["insuredName"] = _member_name
                logger.info(f"insuredName derived from Self member: '{_member_name}' (policyholder: '{_policy_holder}')")

    # Ensure defaults
    top.setdefault("policyNumber", "")
    top.setdefault("insuranceProvider", "")
    top.setdefault("policyType", category)
    top.setdefault("policyHolderName", "")
    top.setdefault("uin", "")
    top.setdefault("productName", "")
    top.setdefault("startDate", "")
    top.setdefault("endDate", "")
    top.setdefault("premiumFrequency", "annual")

    logger.info(
        f"V2→V1 mapped: {len(flat)} type fields, "
        f"policyNumber={top.get('policyNumber', '')[:20]}, "
        f"coverage={top.get('coverageAmount')}, premium={top.get('premium')}"
    )

    return top


def v2_to_v1_flat(v2_extraction: dict) -> dict:
    """Convert PRD v2 extraction result to a simple flat format.

    Strips ConfidenceField wrappers, returning plain key→value pairs.
    Use v2_to_v1() for the full nested format expected by the orchestrator.
    """
    if not v2_extraction:
        return {}
    return {key: _extract_value(val) for key, val in v2_extraction.items()}


def build_extraction_metadata(v2_extraction: dict, category: str) -> dict:
    """Build extraction metadata from v2 extraction results.

    Computes overall confidence, field counts, and identifies
    low-confidence fields for the extractionV2 response.
    """
    if not v2_extraction:
        return {
            "overall_confidence": 0.0,
            "fields_extracted": 0,
            "fields_expected": 0,
            "low_confidence_fields": [],
            "category": category,
        }

    fields_expected = 0
    fields_with_value = 0
    confidence_sum = 0.0
    confidence_count = 0
    low_confidence_fields = []

    for key, field_data in v2_extraction.items():
        if not isinstance(field_data, dict):
            continue
        if "confidence" not in field_data:
            continue

        fields_expected += 1
        conf = field_data.get("confidence", 0.0)
        value = field_data.get("value")

        if value is not None:
            fields_with_value += 1

        confidence_sum += conf
        confidence_count += 1

        if conf < 0.5 and value is not None:
            low_confidence_fields.append({
                "field": key,
                "confidence": conf,
                "value_preview": str(value)[:50] if value else None,
            })

    overall_confidence = round(confidence_sum / confidence_count, 3) if confidence_count > 0 else 0.0

    result = {
        "overall_confidence": overall_confidence,
        "fields_extracted": fields_with_value,
        "fields_expected": fields_expected,
        "low_confidence_fields": low_confidence_fields,
        "category": category,
    }

    # Detect document completeness per category
    _completeness_fields = {
        "health": [
            "dayCareProcedures", "restoration", "ayushTreatment",
            "preHospitalization", "postHospitalization", "ambulanceCover", "modernTreatment",
        ],
        "motor": [
            "idv", "vehicleRegistrationNumber", "vehicleMake", "vehicleModel",
            "productType", "ncbPercentage", "paOwnerCover",
        ],
        "life": [
            "sumAssured", "policyTerm", "deathBenefit", "maturityDate",
            "riders", "nominees", "surrenderValue",
        ],
        "pa": [
            "paSumInsured", "accidentalDeathBenefitPercentage",
            "permanentTotalDisabilityCovered", "permanentPartialDisabilityCovered",
            "temporaryTotalDisabilityCovered",
        ],
        "travel": [
            "medicalExpenses", "tripCancellation", "emergencyMedicalEvacuation",
            "baggageLoss", "personalLiability", "flightDelay",
        ],
    }

    _critical = _completeness_fields.get(category, [])
    if _critical:
        _threshold = 5 if category == "health" else max(3, len(_critical) // 2)
        _missing = sum(
            1 for f in _critical
            if not (isinstance(v2_extraction.get(f), dict) and v2_extraction[f].get("value") not in (None, "", 0))
        )
        if _missing >= _threshold:
            result["documentCompleteness"] = "partial"
            result["documentNote"] = (
                "This appears to be a policy schedule without full benefit details. "
                "Upload the complete policy document for a more accurate analysis."
            )
        else:
            result["documentCompleteness"] = "full"

    return result
