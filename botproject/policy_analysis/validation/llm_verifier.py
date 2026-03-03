"""
PRD v2 Check 6: LLM-Powered Verification & Auto-Correction.

Makes a second DeepSeek call to cross-verify the initial extraction
against the PDF text. Corrects any wrong values and returns a
correction report with full audit trail.

This is a VERIFICATION task, not re-extraction. The LLM receives:
1. The full PDF text (with [Page N] markers)
2. The current extraction JSON (critical/important fields only)
3. Instructions to verify and return ONLY corrections

Usage:
    from policy_analysis.validation.llm_verifier import llm_verify_and_correct
    result = await llm_verify_and_correct(
        deepseek_client, v2_raw_extraction, pdf_text, category
    )
"""
import asyncio
import json
import logging
import re
import time
from typing import Any

from policy_analysis.schemas.base import (
    FieldCriticality,
    CRITICALITY_MAPS,
)

logger = logging.getLogger(__name__)

# ==================== FIELDS TO VERIFY PER TYPE ====================
# Only CRITICAL and IMPORTANT fields get LLM verification.

_VERIFY_FIELDS: dict[str, list[str]] = {
    "health": [
        "policyNumber", "insurerName", "sumInsured", "totalPremium",
        "basePremium", "gst", "policyPeriodStart", "policyPeriodEnd",
        "roomRentLimit", "generalCopay", "preExistingDiseaseWaiting",
        "insuredMembers", "uin", "coverType", "preHospitalization",
        "postHospitalization", "ncbPercentage", "policyHolderName",
        "policyIssueDate", "initialWaitingPeriod", "ambulanceCover",
        "dayCareProcedures", "restoration",
        "intermediaryCode", "previousPolicyNumber", "consumablesCoverage",
    ],
    "motor": [
        "policyNumber", "insurerName", "idv", "odPremium", "tpPremium",
        "totalPremium", "grossPremium", "gst", "policyPeriodStart",
        "policyPeriodEnd", "registrationNumber", "productType", "uin",
        "vehicleMake", "vehicleModel", "ncbPercentage",
        "zeroDepreciation", "engineProtection", "paOwnerCover",
        "compulsoryDeductible", "ownerName",
        "engineNumber", "chassisNumber",
    ],
    "life": [
        "policyNumber", "insurerName", "sumAssured", "premiumAmount",
        "policyTerm", "policyType", "policyPeriodStart", "maturityDate",
        "uin", "premiumPayingTerm", "riders", "nominees",
        "surrenderValue", "bonusType", "policyholderName",
        "lifeAssuredName", "basePremium", "gst", "totalPremium",
        "policyIssueDate", "deathBenefit",
    ],
    "pa": [
        "policyNumber", "insurerName", "paSumInsured",
        "accidentalDeathBenefitPercentage",
        "permanentTotalDisabilityPercentage",
        "permanentPartialDisabilityCovered",
        "temporaryTotalDisabilityCovered",
        "medicalExpensesCovered",
        "policyPeriodStart", "policyPeriodEnd", "uin",
        "totalPremium", "basePremium", "gst", "policyHolderName",
        "ppdSchedule",
    ],
    "travel": [
        "policyNumber", "insurerName", "medicalExpenses",
        "tripStartDate", "tripEndDate", "totalPremium",
        "travelTotalPremium", "destinationCountries", "uin",
        "tripType", "tripCancellation", "baggageLoss",
        "personalLiability", "emergencyMedicalEvacuation",
        "preExistingCovered", "policyHolderName", "policyIssueDate",
    ],
}


# ==================== PROMPT TEMPLATES ====================

VERIFICATION_SYSTEM_PROMPT = (
    "You are an expert insurance policy data auditor for the Indian market. "
    "Your job is to VERIFY extracted data against the original document text "
    "and CORRECT any errors. You are NOT re-extracting — you are cross-checking. "
    "Return ONLY valid JSON. Do not use ```json or ``` markers. "
    "Be extremely precise with numbers, dates, names, and identifiers. "
    "Every correction must be backed by evidence from the document text."
)


def _build_verification_prompt(
    pdf_text: str,
    extraction_json: dict,
    category: str,
    fields_to_verify: list[str],
    check5_mismatches: list[dict] | None = None,
) -> str:
    """Build the user prompt for the verification LLM call.

    Args:
        check5_mismatches: Optional list of mismatch dicts from Check 5
            (pdf_text_verifier). Each has: field, extractedValue, matchType,
            severity, message. These are fields where the Python text matcher
            could NOT find the extracted value in the PDF text.
    """
    # Build subset containing only fields to verify
    subset = {}
    for field in fields_to_verify:
        if field in extraction_json:
            fd = extraction_json[field]
            if isinstance(fd, dict) and "value" in fd:
                subset[field] = {
                    "value": fd.get("value"),
                    "source_page": fd.get("source_page"),
                    "confidence": fd.get("confidence"),
                }
            else:
                subset[field] = fd

    extraction_str = json.dumps(subset, indent=2, default=str, ensure_ascii=False)

    # Build the mismatch alert section if Check 5 found issues
    mismatch_section = ""
    if check5_mismatches:
        mismatch_lines = []
        for m in check5_mismatches:
            field = m.get("field", "?")
            extracted = m.get("extractedValue", "?")
            severity = m.get("severity", "standard")
            mismatch_lines.append(
                f"  - {field}: extracted '{extracted}' (severity: {severity}) "
                f"— this value was NOT found in the PDF text by automated check"
            )
        mismatch_section = (
            "\n\nKNOWN ISSUES (automated text matching flagged these fields as likely WRONG):\n"
            + "\n".join(mismatch_lines)
            + "\n\nPay EXTRA attention to the fields above — they are the most likely to need correction.\n"
        )

    return f"""TASK: Verify the extracted {category.upper()} insurance policy data against the original document and correct any errors.

ORIGINAL DOCUMENT TEXT:
{pdf_text}

CURRENT EXTRACTION (to verify):
{extraction_str}{mismatch_section}

INSTRUCTIONS:
1. For EACH field above, find the actual value in the document text (search ALL pages).
2. Compare the extracted value against what the document actually says.
3. Return ONLY fields that have WRONG values — do NOT return fields that are already correct.
4. For each wrong field, provide the corrected value.

VERIFICATION RULES:
- Numbers: Check exact amounts (sum insured, premiums, IDV, deductibles, limits). Even small differences matter (500000 vs 550000).
- Dates: Verify exact dates match the document. Return in YYYY-MM-DD format.
- Names: Insurer name, policyholder name, vehicle make/model must match exactly as printed.
- Policy Number / UIN: Must match the document exactly including separators.
- Percentages: Copay, NCB, disability percentages must be exact.
- Waiting periods: pre/post hospitalization days, PED waiting months must match document.
- insuredMembers/nominees/riders: verify names, ages, relationships, sum insured for each.
- source_page: provide the [Page N] number where you found the correct value.
- If a field was extracted as null but the value IS in the document, include the correction.

RESPONSE FORMAT — Return ONLY a JSON object:
- For each WRONG field: "{{"fieldName": {{"value": <correct_value>, "source_page": <page_number>, "confidence": <0.9_to_1.0>}}}}"
- If ALL fields are correct (no errors found): {{"_noCorrections": true}}
- Return NOTHING else — no explanations, no markdown, just the JSON object.

CRITICAL:
- Only correct factual data extractable from the document.
- Do NOT invent values not present in the document.
- Do NOT return fields that are already correct.
- Set confidence to 0.95 for certain corrections, 0.9 for high-confidence corrections."""


def _build_targeted_retry_prompt(
    pdf_text: str,
    extraction_json: dict,
    remaining_mismatches: list[dict],
    category: str,
) -> str:
    """Build a focused prompt for the targeted third pass.

    Only sends the specific fields that still have mismatches after
    the first verification pass. Asks the LLM to search harder.
    """
    # Build subset of ONLY the mismatched fields
    mismatch_fields = {m.get("field", "").split("[")[0] for m in remaining_mismatches}
    subset = {}
    for field in mismatch_fields:
        if field in extraction_json:
            fd = extraction_json[field]
            if isinstance(fd, dict) and "value" in fd:
                subset[field] = {
                    "value": fd.get("value"),
                    "source_page": fd.get("source_page"),
                    "confidence": fd.get("confidence"),
                }

    if not subset:
        return ""

    extraction_str = json.dumps(subset, indent=2, default=str, ensure_ascii=False)

    mismatch_details = []
    for m in remaining_mismatches:
        mismatch_details.append(
            f"  - {m.get('field')}: current value is '{m.get('extractedValue')}' "
            f"— automated check says this does NOT match the PDF text"
        )

    return f"""TASK: FOCUSED RE-VERIFICATION of {len(mismatch_fields)} specific {category.upper()} insurance fields that failed automated validation.

These fields were extracted but their values could NOT be confirmed in the PDF text. You must search the ENTIRE document carefully and provide the CORRECT values.

ORIGINAL DOCUMENT TEXT:
{pdf_text}

FIELDS THAT NEED CORRECTION:
{extraction_str}

SPECIFIC ISSUES:
{chr(10).join(mismatch_details)}

INSTRUCTIONS:
1. For EACH field above, search the ENTIRE document text page by page.
2. Find the EXACT value as it appears in the document.
3. If the current extracted value is wrong, return the correction.
4. If the field genuinely does not exist in the document, return it with value null and confidence 0.0.

RESPONSE FORMAT — Return ONLY a JSON object:
- For each field: "{{"fieldName": {{"value": <correct_value_or_null>, "source_page": <page_number_or_null>, "confidence": <0.0_to_1.0>}}}}"
- Return ALL fields listed above (even if the current value is correct — confirm them).
- Return NOTHING else — no explanations, no markdown, just the JSON object."""


# ==================== RESPONSE PARSING ====================


def _parse_correction_response(response_text: str) -> dict:
    """Parse the LLM verification response into a corrections dict.

    Returns empty dict if no corrections or parse failure.
    """
    if not response_text:
        return {}

    text = response_text.strip()

    # Strip markdown code block wrappers
    text = re.sub(r'^```(?:json|JSON)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    text = text.strip()

    # Extract JSON object
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        text = json_match.group(0)

    # Fix common JSON issues
    text = re.sub(r',\s*([}\]])', r'\1', text)
    open_braces = text.count('{') - text.count('}')
    open_brackets = text.count('[') - text.count(']')
    if open_brackets > 0:
        text += ']' * open_brackets
    if open_braces > 0:
        text += '}' * open_braces

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning(f"LLM verifier: failed to parse correction JSON: {e}")
        logger.debug(f"LLM verifier: raw response was: {response_text[:500]}")
        return {}

    if not isinstance(parsed, dict):
        logger.warning("LLM verifier: parsed result is not a dict")
        return {}

    # Check for "no corrections" signal
    if parsed.get("_noCorrections") is True:
        logger.info("LLM verifier: no corrections needed (all fields verified correct)")
        return {}

    # Filter to only ConfidenceField entries
    corrections = {}
    for field_name, field_data in parsed.items():
        if field_name.startswith("_"):
            continue
        if isinstance(field_data, dict) and "value" in field_data:
            corrections[field_name] = field_data
        else:
            logger.warning(
                f"LLM verifier: skipping non-ConfidenceField correction "
                f"for '{field_name}': {str(field_data)[:100]}"
            )

    return corrections


# ==================== CORRECTION MERGE LOGIC ====================


def _normalize_date_to_iso(val: Any) -> str | None:
    """Try to parse a value as a date and return YYYY-MM-DD, or None."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        from dateutil import parser as dateparser
        dt = dateparser.parse(s, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def _values_equal(a: Any, b: Any) -> bool:
    """Compare two values for equality with type coercion."""
    if a == b:
        return True
    if a is None or b is None:
        return False

    str_a = str(a).strip().lower()
    str_b = str(b).strip().lower()
    if str_a == str_b:
        return True

    # Numeric comparison
    try:
        clean_a = str(a).replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
        clean_b = str(b).replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
        num_a = float(clean_a)
        num_b = float(clean_b)
        if abs(num_a - num_b) < 0.01:
            return True
    except (ValueError, TypeError):
        pass

    # Date comparison — treat "2027-01-02" and "02/Jan/2027" as equal
    iso_a = _normalize_date_to_iso(a)
    iso_b = _normalize_date_to_iso(b)
    if iso_a and iso_b and iso_a == iso_b:
        return True

    return False


def _should_apply_correction(
    field_name: str,
    old_field: dict,
    new_field: dict,
) -> bool:
    """Determine whether a correction should be applied.

    Rules:
    1. New confidence must be >= 0.85
    2. Value must actually be different
    3. New confidence must be >= old confidence (never downgrade)
    4. null -> value corrections always apply if confident
    """
    new_confidence = new_field.get("confidence", 0.0)
    if not isinstance(new_confidence, (int, float)):
        try:
            new_confidence = float(new_confidence)
        except (ValueError, TypeError):
            new_confidence = 0.0

    if new_confidence < 0.85:
        logger.info(
            f"LLM verifier: skipping correction for '{field_name}' "
            f"(confidence {new_confidence} < 0.85 threshold)"
        )
        return False

    new_value = new_field.get("value")

    # No existing field — accept if new value is not None
    if not old_field or not isinstance(old_field, dict):
        return new_value is not None

    old_value = old_field.get("value")
    old_confidence = old_field.get("confidence", 0.0)
    if not isinstance(old_confidence, (int, float)):
        old_confidence = 0.0

    # null -> value: always accept
    if old_value is None and new_value is not None:
        return True

    # Values must be different
    if _values_equal(old_value, new_value):
        return False

    # New confidence must be >= old confidence
    if new_confidence < old_confidence:
        logger.info(
            f"LLM verifier: skipping correction for '{field_name}' "
            f"(new confidence {new_confidence} < old {old_confidence})"
        )
        return False

    return True


# Date fields that must always be stored in YYYY-MM-DD format
_DATE_FIELDS = {
    "policyPeriodStart", "policyPeriodEnd", "policyIssueDate",
    "maturityDate", "tripStartDate", "tripEndDate",
    "registrationDate", "firstEnrollmentDate", "insuredSinceDate",
}


def _merge_corrections(
    v2_raw_extraction: dict,
    corrections: dict,
) -> list[dict]:
    """Apply verified corrections to the extraction. Mutates v2_raw_extraction.

    Returns list of audit records for each applied correction.
    """
    audit_log = []

    for field_name, new_field in corrections.items():
        old_field = v2_raw_extraction.get(field_name, {})

        if not _should_apply_correction(field_name, old_field, new_field):
            continue

        # Normalize date fields to ISO YYYY-MM-DD format
        if field_name in _DATE_FIELDS:
            raw_val = new_field.get("value")
            iso_val = _normalize_date_to_iso(raw_val)
            if iso_val:
                new_field = dict(new_field)  # don't mutate original
                new_field["value"] = iso_val

        # Record the change
        old_value = old_field.get("value") if isinstance(old_field, dict) else None
        old_confidence = old_field.get("confidence", 0.0) if isinstance(old_field, dict) else 0.0

        audit_record = {
            "field": field_name,
            "oldValue": old_value if not isinstance(old_value, (list, dict)) else str(old_value)[:200],
            "newValue": new_field.get("value") if not isinstance(new_field.get("value"), (list, dict)) else str(new_field.get("value"))[:200],
            "oldConfidence": round(old_confidence, 3) if isinstance(old_confidence, (int, float)) else 0.0,
            "newConfidence": round(new_field.get("confidence", 0.95), 3),
            "source_page": new_field.get("source_page"),
        }
        audit_log.append(audit_record)

        # Apply the correction
        if field_name in v2_raw_extraction and isinstance(v2_raw_extraction[field_name], dict):
            v2_raw_extraction[field_name]["value"] = new_field.get("value")
            if new_field.get("source_page") is not None:
                v2_raw_extraction[field_name]["source_page"] = new_field["source_page"]
            v2_raw_extraction[field_name]["confidence"] = new_field.get("confidence", 0.95)
        else:
            # Field didn't exist — create it
            v2_raw_extraction[field_name] = {
                "value": new_field.get("value"),
                "source_page": new_field.get("source_page"),
                "confidence": new_field.get("confidence", 0.95),
            }

        logger.info(
            f"LLM verifier CORRECTED '{field_name}': "
            f"'{audit_record['oldValue']}' -> '{audit_record['newValue']}' "
            f"(confidence: {audit_record['oldConfidence']} -> {audit_record['newConfidence']}, "
            f"page: {new_field.get('source_page')})"
        )

    return audit_log


# ==================== PUBLIC API ====================


def _call_deepseek_verification(
    deepseek_client,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """Synchronous DeepSeek call for verification (runs via asyncio.to_thread)."""
    response = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
        max_tokens=4000,
    )
    return response.choices[0].message.content.strip()


async def llm_verify_and_correct(
    deepseek_client,
    v2_raw_extraction: dict,
    pdf_text: str,
    category: str,
    check5_mismatches: list[dict] | None = None,
    pdf_text_verify_fn=None,
    original_pdf_text: str | None = None,
) -> dict:
    """Run LLM verification and auto-correction on the extraction.

    Makes a second DeepSeek call to cross-verify critical/important fields
    against the PDF text. If Check 5 mismatches are provided, they are
    highlighted in the prompt so the LLM pays extra attention to them.

    After the first verification pass, if there are still mismatches
    (re-checked via Check 5), a targeted third pass is made on just
    those remaining problem fields.

    Args:
        deepseek_client: OpenAI client configured for DeepSeek.
        v2_raw_extraction: Current extraction dict (MUTATED with corrections).
        pdf_text: Full PDF text with [Page N] markers.
        category: Detected policy category (health/motor/life/pa/travel).
        check5_mismatches: Optional list of mismatch dicts from Check 5.
        pdf_text_verify_fn: Optional callable(v2_raw_extraction, text, category)
            to re-run Check 5 after corrections. Pass verify_against_pdf_text.
        original_pdf_text: Original PDF text (without page markers) for
            re-running Check 5 verification.

    Returns:
        {
            "verified": bool,
            "correctionsApplied": int,
            "corrections": [audit records],
            "totalFieldsVerified": int,
            "durationMs": int,
            "passes": int,               # 1 = verification only, 2 = + targeted retry
            "remainingMismatches": int,   # mismatches still present after all passes
            "error": str | None,
        }
    """
    _empty_result = {
        "verified": False,
        "correctionsApplied": 0,
        "corrections": [],
        "totalFieldsVerified": 0,
        "durationMs": 0,
        "passes": 0,
        "remainingMismatches": 0,
        "error": None,
    }

    if not v2_raw_extraction or not pdf_text:
        _empty_result["error"] = "Missing extraction or PDF text"
        return _empty_result

    fields_to_verify = _VERIFY_FIELDS.get(category, [])
    if not fields_to_verify:
        _empty_result["error"] = f"No verification fields defined for category '{category}'"
        return _empty_result

    start_time = time.monotonic()
    all_corrections = []
    passes = 0

    try:
        # ==================== PASS 1: Full verification ====================
        user_prompt = _build_verification_prompt(
            pdf_text, v2_raw_extraction, category, fields_to_verify,
            check5_mismatches=check5_mismatches,
        )

        response_text = await asyncio.to_thread(
            _call_deepseek_verification,
            deepseek_client,
            VERIFICATION_SYSTEM_PROMPT,
            user_prompt,
        )
        passes = 1

        pass1_ms = int((time.monotonic() - start_time) * 1000)
        logger.info(
            f"LLM verifier pass 1 [{category}]: response received "
            f"({len(response_text)} chars, {pass1_ms}ms)"
        )

        corrections = _parse_correction_response(response_text)
        if corrections:
            audit_log = _merge_corrections(v2_raw_extraction, corrections)
            all_corrections.extend(audit_log)
            logger.info(
                f"LLM verifier pass 1 [{category}]: {len(audit_log)} corrections applied"
            )

        # ==================== PASS 2: Targeted retry on remaining mismatches ====================
        # Re-run Check 5 to see if mismatches remain after pass 1 corrections
        remaining_mismatches = []
        if pdf_text_verify_fn and original_pdf_text:
            recheck = pdf_text_verify_fn(v2_raw_extraction, original_pdf_text, category)
            remaining_mismatches = recheck.get("mismatches", [])

            # Filter to only critical/important severity
            important_remaining = [
                m for m in remaining_mismatches
                if m.get("severity") in ("critical", "important")
            ]

            if important_remaining:
                logger.info(
                    f"LLM verifier [{category}]: {len(important_remaining)} "
                    f"critical/important mismatches remain after pass 1, starting targeted pass 2"
                )

                retry_prompt = _build_targeted_retry_prompt(
                    pdf_text, v2_raw_extraction, important_remaining, category
                )

                if retry_prompt:
                    retry_response = await asyncio.to_thread(
                        _call_deepseek_verification,
                        deepseek_client,
                        VERIFICATION_SYSTEM_PROMPT,
                        retry_prompt,
                    )
                    passes = 2

                    retry_corrections = _parse_correction_response(retry_response)
                    if retry_corrections:
                        retry_audit = _merge_corrections(v2_raw_extraction, retry_corrections)
                        all_corrections.extend(retry_audit)
                        logger.info(
                            f"LLM verifier pass 2 [{category}]: "
                            f"{len(retry_audit)} additional corrections applied"
                        )

                    # Final re-check
                    final_check = pdf_text_verify_fn(v2_raw_extraction, original_pdf_text, category)
                    remaining_mismatches = final_check.get("mismatches", [])

        duration_ms = int((time.monotonic() - start_time) * 1000)

        final_critical = [
            m for m in remaining_mismatches
            if m.get("severity") in ("critical", "important")
        ]

        logger.info(
            f"LLM verifier DONE [{category}]: "
            f"{len(all_corrections)} total corrections in {passes} pass(es), "
            f"{len(final_critical)} critical/important mismatches remaining, "
            f"{duration_ms}ms total"
        )

        return {
            "verified": True,
            "correctionsApplied": len(all_corrections),
            "corrections": all_corrections,
            "totalFieldsVerified": len(fields_to_verify),
            "durationMs": duration_ms,
            "passes": passes,
            "remainingMismatches": len(final_critical),
            "error": None,
        }

    except Exception as e:
        duration_ms = int((time.monotonic() - start_time) * 1000)
        logger.error(
            f"LLM verifier [{category}]: FAILED after {duration_ms}ms: {e}",
            exc_info=True,
        )
        return {
            "verified": False,
            "correctionsApplied": len(all_corrections),
            "corrections": all_corrections,
            "totalFieldsVerified": len(fields_to_verify),
            "durationMs": duration_ms,
            "passes": passes,
            "remainingMismatches": 0,
            "error": str(e),
        }
