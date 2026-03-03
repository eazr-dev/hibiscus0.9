"""
Policy Upload Router
Simplified single-endpoint API for policy upload and analysis
Based on Insurance Policy Upload & Analysis API specification

Rate Limiting Applied (Redis-backed):
- /api/policy/upload: 10 requests per minute per user
- Prevents abuse of expensive PDF processing and AI analysis

Supported Insurance Types (5 types):
- Health (Health, Medical, Mediclaim)
- Life (Life, Term, Endowment, ULIP, Whole Life)
- Motor (Motor, Car, Vehicle, Bike, Two-Wheeler, Four-Wheeler, Auto)
- Accidental (Personal Accident, PA, Accidental)
- Travel

Unsupported/Rejected:
- Home Insurance / Property Insurance (coming soon)
- Crop Insurance / Agricultural Insurance
- Business Insurance / Commercial Insurance
- Marine / Aviation / Engineering Insurance
- Non-insurance documents
"""
import logging
import secrets
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header, Request

from services.policy_locker_service import policy_locker_service
from core.rate_limiter import limiter, RATE_LIMITS, redis_rate_limiter, get_user_identifier

# Policy analysis modules (extracted from monolith)
from policy_analysis.document_validator import validate_insurance_document, is_unsupported_policy_type
from policy_analysis.image_extractor import is_image_file, extract_text_from_images_deepseek
from policy_analysis.utils import (
    get_score_label as _get_score_label,
    parse_number_from_string_safe as _parse_number_from_string_safe,
)
from policy_analysis.types.pa.helpers import (
    _calculate_pa_income_replacement_score,
    _calculate_pa_disability_protection_score,
    _analyze_pa_gaps,
    _generate_pa_recommendations,
)
from policy_analysis.types.motor.helpers import (
    detect_motor_product_type,
    _analyze_motor_gaps,
    _generate_motor_recommendations,
    _get_motor_vehicle_age,
    _get_motor_ncb_pct,
    _build_motor_policy_data_for_scoring,
    _select_motor_primary_scenario,
)
from policy_analysis.types.motor.light_analysis import _build_motor_light_analysis
from policy_analysis.types.travel.light_analysis import _build_travel_light_analysis
from policy_analysis.light_analysis_builder import _build_light_analysis
from policy_analysis.markdown_generators import _generate_light_analysis_md
from policy_analysis.types.health.ui_builder import _build_policy_details_ui

# PRD v2 extraction modules
from policy_analysis.utils import inject_page_markers
from policy_analysis.extraction.prompts.prompt_builder import build_v2_extraction_prompt
from policy_analysis.extraction.v2_response_parser import parse_v2_extraction_response
from policy_analysis.compat.v1_mapper import v2_to_v1, build_extraction_metadata
from policy_analysis.validation.four_check_validator import run_four_checks
from policy_analysis.validation.pdf_text_verifier import verify_against_pdf_text
from policy_analysis.validation.llm_verifier import llm_verify_and_correct
from policy_analysis.scoring.universal_scores import compute_universal_scores
from policy_analysis.scoring.zone_classifier import classify_zones
from policy_analysis.verdict.headline_generator import generate_verdict
from policy_analysis.compliance.irdai_checker import check_irdai_compliance
from policy_analysis.recommendations.zone_recommender import generate_zone_recommendations

logger = logging.getLogger(__name__)


def _compute_ped_completed(ai_data: dict) -> bool:
    """Compute pedWaitingPeriodCompleted from dates instead of trusting AI.

    Logic:
    1. If PED waiting is "No waiting period" / "nil" / "0" → True
    2. If firstEnrollmentDate/insuredSinceDate exists, compute elapsed years
       and compare against waiting period → True if elapsed >= waiting
    3. If continuousCoverageYears exists and >= waiting period → True
    4. Fall back to AI's value
    """
    import re

    # Get PED waiting period string
    pec_raw = ai_data.get("preExistingDiseaseWaiting")
    if isinstance(pec_raw, dict):
        pec_raw = pec_raw.get("value")
    pec_str = str(pec_raw).lower().strip() if pec_raw else ""

    # "No waiting period" / "nil" / "0" → completed
    if pec_str and ("no" in pec_str and "wait" in pec_str):
        return True
    if pec_str in ("nil", "0", "0 months", "0 days", "none"):
        return True

    # Parse waiting period in months
    waiting_months = 0
    if pec_str:
        m = re.search(r'(\d+)', pec_str)
        if m:
            val = int(m.group(1))
            waiting_months = val * 12 if "year" in pec_str else val

    # Get enrollment date
    enrollment_raw = ai_data.get("firstEnrollmentDate") or ai_data.get("insuredSinceDate")
    if isinstance(enrollment_raw, dict):
        enrollment_raw = enrollment_raw.get("value")

    if enrollment_raw and waiting_months > 0:
        enrollment_str = str(enrollment_raw).strip()
        for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d/%m/%Y", "%d / %m / %Y",
                     "%d-%m-%Y", "%d %b %Y", "%d %B %Y", "%Y/%m/%d"):
            try:
                enrollment_date = datetime.strptime(enrollment_str, fmt)
                elapsed_months = (datetime.now() - enrollment_date).days / 30.44
                if elapsed_months >= waiting_months:
                    return True
                break
            except (ValueError, TypeError):
                continue

    # Check continuousCoverageYears
    ccy_raw = ai_data.get("continuousCoverageYears")
    if isinstance(ccy_raw, dict):
        ccy_raw = ccy_raw.get("value")
    if ccy_raw is not None:
        try:
            ccy = float(ccy_raw)
            if waiting_months > 0 and ccy * 12 >= waiting_months:
                return True
        except (ValueError, TypeError):
            pass

    # Fall back to AI's extraction
    ai_val = ai_data.get("pedWaitingPeriodCompleted")
    if isinstance(ai_val, dict):
        ai_val = ai_val.get("value")
    return bool(ai_val)


def _life_val(v2: dict, field: str):
    """Extract bare value from a life extraction ConfidenceField."""
    raw = v2.get(field)
    if isinstance(raw, dict):
        return raw.get("value")
    return raw


def _life_set(v2: dict, field: str, value, confidence: float = 0.9, source_page=None):
    """Set a ConfidenceField in the v2 extraction dict."""
    existing = v2.get(field)
    if isinstance(existing, dict) and "confidence" in existing:
        existing["value"] = value
        existing["confidence"] = confidence
        if source_page is not None:
            existing["source_page"] = source_page
    else:
        v2[field] = {"value": value, "source_page": source_page, "confidence": confidence}


def _postprocess_life_extraction(v2: dict) -> None:
    """Dynamic post-processing overrides for life insurance extractions.

    Fixes common AI mistakes across all Indian life insurers:
    1. Maturity date confused with rider expiry (use the later date)
    2. policyTerm derived from wrong end date
    3. Rider premium misattributed to GST
    4. policyholderDob/Age missing when policyholder = life assured
    5. policyType misclassification (Whole Life vs Endowment)
    """
    import re
    from dateutil import parser as dateparser

    def _parse_date(date_val):
        """Parse a date string flexibly, return datetime or None."""
        if not date_val:
            return None
        s = str(date_val).strip()
        if not s or s.lower() in ("null", "none", "na", "n/a"):
            return None
        try:
            return dateparser.parse(s, dayfirst=True)
        except (ValueError, TypeError):
            return None

    # ── Fix 1: Maturity date vs rider expiry ──────────────────────────
    # Strategy: (a) If the two dates differ, use the LATER one.
    #           (b) For Whole Life plans, validate against DOB — Indian
    #               whole life plans run until age 99-100 (IRDAI standard).
    maturity_val = _life_val(v2, "maturityDate")
    period_end_val = _life_val(v2, "policyPeriodEnd")
    maturity_dt = _parse_date(maturity_val)
    period_end_dt = _parse_date(period_end_val)
    start_val = _life_val(v2, "policyPeriodStart") or _life_val(v2, "policyIssueDate")
    start_dt = _parse_date(start_val)

    # Step (a): Use the LATER date if the two differ
    if maturity_dt and period_end_dt:
        true_maturity = max(maturity_dt, period_end_dt)
        if maturity_dt != true_maturity:
            _life_set(v2, "maturityDate", true_maturity.strftime("%Y-%m-%d"))
            logger.info(f"Life override: maturityDate corrected from {maturity_val} to {true_maturity.strftime('%Y-%m-%d')}")
        if period_end_dt != true_maturity:
            _life_set(v2, "policyPeriodEnd", true_maturity.strftime("%Y-%m-%d"))
            logger.info(f"Life override: policyPeriodEnd corrected from {period_end_val} to {true_maturity.strftime('%Y-%m-%d')}")
    elif maturity_dt and not period_end_dt:
        _life_set(v2, "policyPeriodEnd", maturity_dt.strftime("%Y-%m-%d"))
    elif period_end_dt and not maturity_dt:
        _life_set(v2, "maturityDate", period_end_dt.strftime("%Y-%m-%d"))

    # Step (b): Whole Life cross-check with DOB
    # Indian whole life plans (LIC Jeevan Umang, SBI Shubh Nivesh, HDFC Sanchay Plus
    # Whole Life, Max Whole Life, etc.) run until the life assured reaches age 99-100.
    # If detected as Whole Life but maturity term is < 50 years, likely rider confusion.
    product_name_raw = str(_life_val(v2, "productName") or "").lower()
    whole_life_keywords = [
        "whole life", "jeevan umang", "sampurna", "sampurn",
        "lifetime", "life long", "lifelong", "till age 100",
        "till age 99", "saral jeevan bima",
    ]
    is_likely_whole_life = any(kw in product_name_raw for kw in whole_life_keywords)

    la_dob_val = _life_val(v2, "lifeAssuredDob")
    la_dob_dt = _parse_date(la_dob_val)

    if is_likely_whole_life and la_dob_dt and start_dt:
        # Re-read current maturity after step (a)
        current_mat_val = _life_val(v2, "maturityDate")
        current_mat_dt = _parse_date(current_mat_val)
        current_term = round((current_mat_dt - start_dt).days / 365.25) if current_mat_dt else 0

        if current_term < 50:
            # Almost certainly wrong — compute from DOB + 100 years
            from dateutil.relativedelta import relativedelta
            expected_maturity = la_dob_dt + relativedelta(years=100)
            # Align to policy anniversary (use start month/day)
            expected_maturity = expected_maturity.replace(
                month=start_dt.month, day=start_dt.day
            )
            expected_term = round((expected_maturity - start_dt).days / 365.25)

            logger.info(
                f"Life override (Whole Life): maturity corrected from {current_mat_val} "
                f"to {expected_maturity.strftime('%Y-%m-%d')} "
                f"(DOB={la_dob_val}, term {current_term}→{expected_term})"
            )
            _life_set(v2, "maturityDate", expected_maturity.strftime("%Y-%m-%d"))
            _life_set(v2, "policyPeriodEnd", expected_maturity.strftime("%Y-%m-%d"))

    # ── Fix 2: policyTerm from correct dates ──────────────────────────
    # Recompute policyTerm from start date → corrected maturity date
    # Re-read corrected maturity
    corrected_maturity_val = _life_val(v2, "maturityDate")
    corrected_maturity_dt = _parse_date(corrected_maturity_val)

    if start_dt and corrected_maturity_dt:
        computed_term = round((corrected_maturity_dt - start_dt).days / 365.25)
        ai_term = _life_val(v2, "policyTerm")
        ai_term_num = None
        if ai_term is not None:
            try:
                ai_term_num = int(float(str(ai_term)))
            except (ValueError, TypeError):
                pass
        if ai_term_num and abs(ai_term_num - computed_term) > 2:
            logger.info(f"Life override: policyTerm corrected from {ai_term_num} to {computed_term}")
            _life_set(v2, "policyTerm", computed_term)

    # ── Fix 3: Rider premium vs GST confusion ────────────────────────
    # If GST equals total rider premiums, it's likely misattributed
    riders = _life_val(v2, "riders")
    total_rider_premium = 0.0
    if isinstance(riders, list):
        for r in riders:
            if isinstance(r, dict):
                rp = r.get("riderPremium", 0)
                try:
                    total_rider_premium += float(rp) if rp else 0
                except (ValueError, TypeError):
                    pass

    gst_val = _life_val(v2, "gst")
    base_val = _life_val(v2, "basePremium")
    total_val = _life_val(v2, "totalPremium")

    try:
        gst_num = float(gst_val) if gst_val else 0
        base_num = float(base_val) if base_val else 0
        total_num = float(total_val) if total_val else 0
    except (ValueError, TypeError):
        gst_num = base_num = total_num = 0

    if gst_num > 0 and total_rider_premium == 0 and base_num > 0 and total_num > 0:
        # GST is non-zero but rider premium is 0 — check if GST is actually rider premium
        # Condition: base + gst ≈ total AND gst matches what rider premium should be
        if abs((base_num + gst_num) - total_num) < 1.0:
            # Check if GST is plausible: GST on insurance is 18%, so expected ≈ base * 0.18
            expected_gst = base_num * 0.18
            # If the "GST" value is way off from 18% but there are riders with 0 premium
            if isinstance(riders, list) and len(riders) > 0 and abs(gst_num - expected_gst) > expected_gst * 0.3:
                # This GST is actually the rider premium — redistribute
                per_rider = gst_num / len(riders)
                for r in riders:
                    if isinstance(r, dict) and (not r.get("riderPremium") or float(r.get("riderPremium", 0)) == 0):
                        r["riderPremium"] = round(per_rider, 2)
                _life_set(v2, "riders", riders)

                # Fix modalPremiumBreakdown
                modal = _life_val(v2, "modalPremiumBreakdown")
                if isinstance(modal, dict):
                    modal["rider"] = gst_num
                    modal["gst"] = 0
                    _life_set(v2, "modalPremiumBreakdown", modal)

                # Set GST to 0
                _life_set(v2, "gst", 0)
                logger.info(f"Life override: GST {gst_num} reassigned as rider premium (not GST)")

    # ── Fix 4: policyholderDob/Age from life assured when Self ───────
    relationship = _life_val(v2, "relationshipWithPolicyholder")
    rel_str = str(relationship).lower().strip() if relationship else ""

    ph_dob = _life_val(v2, "policyholderDob")
    ph_age = _life_val(v2, "policyholderAge")
    la_dob = _life_val(v2, "lifeAssuredDob")
    la_age = _life_val(v2, "lifeAssuredAge")
    ph_name = _life_val(v2, "policyholderName") or ""
    la_name = _life_val(v2, "lifeAssuredName") or ""

    # If relationship is Self OR names match, copy DOB/age from life assured
    is_self = rel_str == "self" or (
        ph_name and la_name and ph_name.strip().lower() == la_name.strip().lower()
    )

    if is_self:
        if not ph_dob and la_dob:
            _life_set(v2, "policyholderDob", la_dob)
            logger.info(f"Life override: policyholderDob set from lifeAssuredDob ({la_dob})")
        if not ph_age and la_age:
            _life_set(v2, "policyholderAge", la_age)
            logger.info(f"Life override: policyholderAge set from lifeAssuredAge ({la_age})")

    # ── Fix 5: policyType — detect Whole Life dynamically ────────────
    policy_type = _life_val(v2, "policyType")
    product_name = str(_life_val(v2, "productName") or "").lower()
    pt_str = str(policy_type).lower().strip() if policy_type else ""

    # Get corrected policy term
    corrected_term = _life_val(v2, "policyTerm")
    try:
        term_num = int(float(str(corrected_term))) if corrected_term else 0
    except (ValueError, TypeError):
        term_num = 0

    # Detect Whole Life from product name keywords (works across all Indian insurers)
    whole_life_keywords = [
        "whole life", "jeevan umang", "sampurna", "sampurn",
        "lifetime", "life long", "lifelong", "till age 100",
        "till age 99", "saral jeevan bima",
    ]
    is_whole_life_by_name = any(kw in product_name for kw in whole_life_keywords)

    # Detect from term: if term >= 50 years, very likely Whole Life
    is_whole_life_by_term = term_num >= 50

    if pt_str != "whole life" and (is_whole_life_by_name or is_whole_life_by_term):
        _life_set(v2, "policyType", "Whole Life")
        logger.info(
            f"Life override: policyType corrected from '{policy_type}' to 'Whole Life' "
            f"(name_match={is_whole_life_by_name}, term={term_num})"
        )


# ── Travel insurance helpers ─────────────────────────────────────────

def _travel_val(v2: dict, field: str):
    """Extract bare value from a travel extraction ConfidenceField."""
    raw = v2.get(field)
    if isinstance(raw, dict):
        return raw.get("value")
    return raw


def _travel_set(v2: dict, field: str, value, confidence: float = 0.9, source_page=None):
    """Set a ConfidenceField in the v2 extraction dict."""
    existing = v2.get(field)
    if isinstance(existing, dict) and "confidence" in existing:
        existing["value"] = value
        existing["confidence"] = confidence
        if source_page is not None:
            existing["source_page"] = source_page
    else:
        v2[field] = {"value": value, "source_page": source_page, "confidence": confidence}


def _postprocess_travel_extraction(v2: dict) -> None:
    """Dynamic post-processing overrides for travel insurance extractions.

    Fixes common AI mistakes across all travel insurers worldwide:
    1. policyPeriodStart/End missing (should equal trip dates)
    2. Evacuation/Repatriation shown as INCLUDED but not extracted
    3. deductiblePerClaim missing (should use medicalDeductible)
    4. Traveller age not computed from DOB
    5. premiumFrequency wrong for single-trip policies
    """
    from dateutil import parser as dateparser

    def _parse_date(date_val):
        if not date_val:
            return None
        s = str(date_val).strip()
        if not s or s.lower() in ("null", "none", "na", "n/a"):
            return None
        try:
            return dateparser.parse(s, dayfirst=True)
        except (ValueError, TypeError):
            return None

    # ── Fix 1: policyPeriodStart/End from trip dates ─────────────────
    period_start = _travel_val(v2, "policyPeriodStart")
    period_end = _travel_val(v2, "policyPeriodEnd")
    trip_start = _travel_val(v2, "tripStartDate")
    trip_end = _travel_val(v2, "tripEndDate")

    if not period_start and trip_start:
        _travel_set(v2, "policyPeriodStart", trip_start)
        logger.info(f"Travel override: policyPeriodStart set from tripStartDate ({trip_start})")
    if not period_end and trip_end:
        _travel_set(v2, "policyPeriodEnd", trip_end)
        logger.info(f"Travel override: policyPeriodEnd set from tripEndDate ({trip_end})")

    # ── Fix 2: Evacuation / Repatriation "INCLUDED" handling ─────────
    # Many travel policies list evacuation/repatriation as "INCLUDED*" under
    # the overall medical limit. If the AI missed these or returned null,
    # check coverageIncludes or the raw string and set to medical expenses.
    med_val = _travel_val(v2, "medicalExpenses")
    try:
        med_num = float(med_val) if med_val else 0
    except (ValueError, TypeError):
        med_num = 0

    for field_name in ("emergencyMedicalEvacuation", "repatriationOfRemains"):
        current = _travel_val(v2, field_name)
        if current is None or current == 0 or current == "":
            # If medical expenses exist, evacuation/repatriation are commonly
            # included under the same limit for travel policies
            if med_num > 0:
                # Check if coverageIncludes mentions it
                includes = _travel_val(v2, "coverageIncludes") or []
                includes_str = " ".join(str(i).lower() for i in includes) if isinstance(includes, list) else str(includes).lower()

                # Also check if the field has a string value like "INCLUDED"
                raw_field = v2.get(field_name)
                raw_str = ""
                if isinstance(raw_field, dict):
                    raw_str = str(raw_field.get("value", "")).lower()
                elif isinstance(raw_field, str):
                    raw_str = raw_field.lower()

                keyword = "evacuation" if "evacuation" in field_name.lower() else "repatriation"
                if ("included" in raw_str or keyword in includes_str or
                        "included" in str(current).lower()):
                    _travel_set(v2, field_name, med_num)
                    logger.info(f"Travel override: {field_name} set to {med_num} (INCLUDED under medical limit)")

    # ── Fix 3: deductiblePerClaim from medicalDeductible ─────────────
    ded_per_claim = _travel_val(v2, "deductiblePerClaim")
    med_deductible = _travel_val(v2, "medicalDeductible")
    if (ded_per_claim is None or ded_per_claim == 0) and med_deductible:
        try:
            ded_num = float(med_deductible)
            if ded_num > 0:
                _travel_set(v2, "deductiblePerClaim", ded_num)
                logger.info(f"Travel override: deductiblePerClaim set from medicalDeductible ({ded_num})")
        except (ValueError, TypeError):
            pass

    # ── Fix 4: Compute traveller ages from DOB ───────────────────────
    issue_date = _travel_val(v2, "policyIssueDate")
    issue_dt = _parse_date(issue_date)
    travellers = _travel_val(v2, "travellers")
    if isinstance(travellers, list) and issue_dt:
        changed = False
        for t in travellers:
            if isinstance(t, dict):
                dob_val = t.get("dateOfBirth")
                age_val = t.get("age")
                if dob_val and (not age_val or age_val == 0):
                    dob_dt = _parse_date(dob_val)
                    if dob_dt:
                        age = issue_dt.year - dob_dt.year
                        if (issue_dt.month, issue_dt.day) < (dob_dt.month, dob_dt.day):
                            age -= 1
                        t["age"] = age
                        changed = True
        if changed:
            _travel_set(v2, "travellers", travellers)
            logger.info("Travel override: computed traveller ages from DOB")

    # ── Fix 5: premiumFrequency for single-trip ──────────────────────
    trip_type = _travel_val(v2, "tripType")
    trip_type_str = str(trip_type).lower() if trip_type else ""
    if "single" in trip_type_str or "one" in trip_type_str:
        _travel_set(v2, "premiumFrequency", "Single Premium")
        logger.info("Travel override: premiumFrequency set to 'Single Premium' for single trip")


# Create router WITHOUT prefix (direct /api path)
router = APIRouter(prefix="/api", tags=["Policy Upload"])


@router.post("/policy/upload")
@limiter.limit(RATE_LIMITS["policy_upload"])
async def upload_and_analyze_policy(
    request: Request,  # Required for rate limiter
    policyDocument: UploadFile = File(None, description="Insurance policy PDF document (optional if images provided)"),
    policyImages: List[UploadFile] = File(default=[], description="Insurance policy images (JPG, PNG, WEBP) - multiple files allowed"),
    policyFor: str = Form(..., description="Type of policy holder: 'self' or 'family'"),
    name: str = Form(..., description="Full name of policy holder"),
    gender: str = Form(..., description="Gender: 'male', 'female', or 'other'"),
    dateOfBirth: Optional[str] = Form(None, description="Date of birth in YYYY-MM-DD format (optional — extracted from policy if not provided)"),
    relationship: str = Form(..., description="Relationship: 'self', 'son', 'daughter', 'sister', 'brother', 'friend', 'mother', 'father', 'spouse', 'other'"),
    uploadedAt: str = Form(..., description="Upload timestamp in ISO 8601 format"),
    userId: str = Form(..., description="User ID from session"),
    session_id: Optional[str] = Form(None, description="User session ID (optional)"),
    authorization: Optional[str] = Header(None, description="Bearer token (optional)", alias="Authorization"),
    access_token: Optional[str] = Header(None, description="Access token (optional)", alias="access-token")
):
    """
    Upload and Analyze Insurance Policy (Simplified API)

    **Rate Limited:** 10 requests per minute per user
    This prevents abuse of expensive PDF processing and AI analysis.

    This endpoint accepts policy details and either PDF document OR image(s) in a single request,
    performs AI analysis using DeepSeek, and returns complete policy analysis with gap detection.

    **Request Format:** multipart/form-data

    **Headers (Optional):**
    - Authorization: Bearer {token}
    - access-token: {access_token}

    **Required Fields:**
    - policyFor: "self" or "family"
    - name: Full name (2-100 characters)
    - gender: "male", "female", or "other"
    - dateOfBirth: YYYY-MM-DD (optional — extracted from policy if not provided)
    - relationship: "self", "spouse", "child", "parent", "sibling"
    - uploadedAt: ISO 8601 timestamp
    - userId: User ID from session
    - policyDocument: PDF file (max 10MB) - OR - policyImages

    **Document Upload Options:**
    1. **PDF Upload**: Single PDF file via `policyDocument` field
    2. **Image Upload**: Multiple image files via `policyImages` field (multipart/form-data)
       - Send multiple files with the same field name: `policyImages`
       - Supported formats: JPG, JPEG, PNG, WEBP, GIF, BMP
       - Max 10 images, total size max 20MB
       - Images are processed using DeepSeek Vision AI for text extraction

    **Authentication (Optional):**
    You can authenticate using any of these methods:
    1. Authorization header: `Authorization: Bearer {token}`
    2. Access token header: `access-token: {token}`
    3. Session ID: `session_id` form field

    **Returns:**
    - Complete policy analysis with extracted data
    - Coverage gaps and recommendations
    - Protection score and summary
    """
    try:
        # ==================== VALIDATION ====================

        # 1. Validate Authorization (Optional - Bearer token OR access_token OR session_id)
        # NOTE: For now, authentication is optional to allow testing
        # In production, you should enforce authentication
        has_auth = bool(authorization and authorization.startswith("Bearer "))
        has_access_token = bool(access_token)
        has_session = bool(session_id)

        # Log authentication method for debugging
        if has_access_token:
            logger.info(f"Request authenticated with access-token header")
        elif has_auth:
            logger.info(f"Request authenticated with Authorization Bearer token")
        elif has_session:
            logger.info(f"Request authenticated with session_id")
        else:
            logger.info(f"Request without authentication (testing mode)")

        # Optional: Validate session if provided
        if session_id:
            try:
                user_id_int = int(userId)
                from core.dependencies import get_session, store_session
                from session_security.session_manager import session_manager

                session_id, session_data, was_regenerated = session_manager.validate_and_regenerate_session(
                    session_id,
                    get_session,
                    store_session
                )

                if not session_data or not session_data.get('active'):
                    raise HTTPException(
                        status_code=401,
                        detail={
                            "success": False,
                            "error_code": "AUTH_1001",
                            "message": "Invalid or expired session"
                        }
                    )
            except Exception as e:
                logger.warning(f"Session validation failed: {e}")
                # Continue without session validation for now

        # 2. Validate policyFor enum
        if policyFor not in ["self", "family"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": f"Invalid value for policyFor: '{policyFor}'. Allowed values are: self, family"
                }
            )

        # 3. Validate name length
        if not name or len(name) < 2 or len(name) > 100:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": "Name must be between 2 and 100 characters"
                }
            )

        # 4. Validate gender enum
        if gender not in ["male", "female", "other"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": f"Invalid value for gender: '{gender}'. Allowed values are: male, female, other"
                }
            )

        # 5. Validate date format and age (18+) — only if dateOfBirth provided
        if dateOfBirth:
            try:
                dob = datetime.strptime(dateOfBirth, "%Y-%m-%d")
                age = (datetime.now() - dob).days // 365
                if age < 18:
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "success": False,
                            "error_code": "VAL_2001",
                            "message": "User must be 18+ years old to upload policies"
                        }
                    )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error_code": "VAL_2001",
                        "message": "Date of birth must be in YYYY-MM-DD format"
                    }
                )

        # 6. Validate relationship enum
        valid_relationships = ["self", "son", "daughter", "sister", "brother", "friend", "mother", "father", "spouse", "other"]
        if relationship not in valid_relationships:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": f"Invalid value for relationship: '{relationship}'. Allowed values are: {', '.join(valid_relationships)}"
                }
            )

        # 7. Validate document upload (PDF or Images required)
        has_pdf = policyDocument is not None and policyDocument.filename
        # Filter out empty file uploads (browsers may send empty entries)
        valid_image_files = [img for img in policyImages if img and img.filename] if policyImages else []
        has_images = len(valid_image_files) > 0

        if not has_pdf and not has_images:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "POL_8003",
                    "message": "Please provide either a PDF document (policyDocument) or image(s) (policyImages)"
                }
            )

        # Track upload type for later processing
        is_pdf_upload = False
        is_image_upload = False
        content = None
        image_contents = []
        image_filenames = []
        original_filename = ""

        if has_pdf:
            # Validate PDF file type
            if not policyDocument.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error_code": "POL_8003",
                        "message": "policyDocument must be a PDF file. For images, use the policyImages field."
                    }
                )

            # Read PDF content
            content = await policyDocument.read()
            file_size = len(content)
            max_size = 10 * 1024 * 1024  # 10MB

            if file_size > max_size:
                raise HTTPException(
                    status_code=413,
                    detail={
                        "success": False,
                        "error_code": "VAL_2002",
                        "message": "PDF file size exceeds maximum limit of 10MB"
                    }
                )

            is_pdf_upload = True
            original_filename = policyDocument.filename
            logger.info(f"📄 PDF upload detected: {original_filename} ({file_size / 1024:.1f} KB)")

        elif has_images:
            # Process multiple image file uploads (multipart/form-data)
            max_images = 10
            max_total_size = 20 * 1024 * 1024  # 20MB total for images

            if len(valid_image_files) > max_images:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error_code": "VAL_2002",
                        "message": f"Maximum {max_images} images allowed. You uploaded {len(valid_image_files)}."
                    }
                )

            total_size = 0
            for img in valid_image_files:
                filename = img.filename

                # Validate file extension
                if not is_image_file(filename):
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "success": False,
                            "error_code": "POL_8003",
                            "message": f"Invalid image format: {filename}. Supported formats: JPG, JPEG, PNG, WEBP, GIF, BMP"
                        }
                    )

                # Read image content
                img_content = await img.read()
                img_size = len(img_content)
                total_size += img_size

                if total_size > max_total_size:
                    raise HTTPException(
                        status_code=413,
                        detail={
                            "success": False,
                            "error_code": "VAL_2002",
                            "message": f"Total image size exceeds maximum limit of 20MB"
                        }
                    )

                image_contents.append(img_content)
                image_filenames.append(filename)

            is_image_upload = True
            # Create combined content hash for duplicate detection
            import hashlib
            combined_hash = hashlib.md5()
            for img_content in image_contents:
                combined_hash.update(img_content)
            content = combined_hash.digest()  # Use hash as "content" for duplicate detection

            original_filename = f"policy_images_{len(image_contents)}_files.zip"  # Virtual filename
            logger.info(f"📷 Image upload detected: {len(image_contents)} image(s) ({total_size / 1024:.1f} KB total)")

        # ==================== PROCESSING ====================

        # Convert userId to int if needed
        try:
            user_id_int = int(userId)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_code": "VAL_2001",
                    "message": "userId must be a valid number"
                }
            )

        # ==================== DUPLICATE DETECTION (EARLY CHECK) ====================
        # Check for duplicate using file hash BEFORE expensive processing
        import hashlib
        file_hash = hashlib.md5(content).hexdigest()
        logger.info(f"📋 File hash calculated: {file_hash}")

        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager

            if mongodb_chat_manager is not None and mongodb_chat_manager.db is not None:
                db = mongodb_chat_manager.db
                policy_analysis_collection = db['policy_analysis']

                # Check if policy with same file hash already exists for this user
                existing_policy = policy_analysis_collection.find_one({
                    "user_id": user_id_int,
                    "fileHash": file_hash,
                    "$or": [
                        {"isDeleted": {"$exists": False}},
                        {"isDeleted": False}
                    ]
                })

                if existing_policy:
                    # Extract existing policy details for navigation
                    existing_policy_id = str(existing_policy.get("_id", ""))
                    existing_analysis_id = existing_policy.get("analysisId", "")
                    existing_policy_number = existing_policy.get("extractedData", {}).get("policyNumber", "")
                    existing_policy_type = existing_policy.get("extractedData", {}).get("policyType", "")
                    existing_insurer = existing_policy.get("extractedData", {}).get("insuranceProvider", "")

                    logger.warning(f"⚠️ Duplicate policy detected (by file hash): {file_hash} already exists for user {userId} (policyId: {existing_policy_id})")
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "success": False,
                            "error_code": "POL_8005",
                            "message": f"This policy document has already been uploaded to your account.",
                            "isDuplicate": True,
                            "existingPolicy": {
                                "policyId": existing_policy_id,
                                "analysisId": existing_analysis_id,
                                "userId": user_id_int,
                                "policyNumber": existing_policy_number,
                                "policyType": existing_policy_type,
                                "insuranceProvider": existing_insurer,
                                "uploadedAt": existing_policy.get("uploadedAt", ""),
                                "createdAt": existing_policy.get("created_at").isoformat() + "Z" if existing_policy.get("created_at") else ""
                            }
                        }
                    )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"⚠️ Could not check for duplicate (will continue): {str(e)}")

        # Determine if policy is for self or family member
        is_for_self = (policyFor == "self")
        member_id = None

        # Step 1: Upload the document(s)
        if is_pdf_upload:
            logger.info(f"📄 Uploading PDF document for user {userId}, policyFor={policyFor}")
            upload_result = await policy_locker_service.upload_policy_document(
                user_id=user_id_int,
                file_content=content,
                filename=original_filename,
                member_id=member_id,
                is_for_self=is_for_self
            )
        elif is_image_upload:
            # For images, upload the first image as the primary document
            # (or could combine into a single archive - for now upload first image)
            logger.info(f"📷 Uploading {len(image_contents)} image(s) for user {userId}, policyFor={policyFor}")

            # Upload first image as primary document
            primary_image_content = image_contents[0]
            primary_image_filename = image_filenames[0]

            upload_result = await policy_locker_service.upload_policy_document(
                user_id=user_id_int,
                file_content=primary_image_content,
                filename=primary_image_filename,
                member_id=member_id,
                is_for_self=is_for_self
            )

            # TODO: If needed, upload additional images as supplementary documents
            # For now, all images are processed together for text extraction

        upload_id = upload_result.get("uploadId")
        original_document_url = upload_result.get("documentUrl")  # Get original document S3 URL

        if not upload_id:
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error_code": "POL_8004",
                    "message": "Upload failed - no upload ID returned"
                }
            )

        # Step 2: Perform ACTUAL document analysis with DeepSeek
        logger.info(f"Analyzing policy document with DeepSeek AI, uploadId={upload_id}")

        # Import the actual PDF analysis function from chat router
        from routers.chat import (
            extract_uin_from_text_deepseek,
            _extract_uin_regex,
            fetch_policy_from_db_deepseek,
            deepseek_client
        )
        from policy_analysis.classification import classify_policy as _hibiscus_classify
        from policy_analysis.classification import match_product_from_db, get_product_by_uin
        import PyPDF2
        import pdfplumber
        from io import BytesIO
        import json
        import re

        # Extract text based on upload type (PDF or Images)
        extracted_text = ""
        extracted_text_with_pages = ""  # PRD v2: text with [Page N] markers

        if is_pdf_upload:
            # Extract text from PDF
            logger.info("📄 Extracting text from PDF document...")
            try:
                pdf_file = BytesIO(content)
                pdf_reader = PyPDF2.PdfReader(pdf_file)

                page_texts = []
                for page in pdf_reader.pages:
                    page_text = page.extract_text() or ""
                    page_texts.append(page_text)
                    extracted_text += page_text + "\n"

                # Fallback to pdfplumber if PyPDF2 fails
                if not extracted_text.strip():
                    page_texts = []
                    pdf_file.seek(0)
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text() or ""
                            page_texts.append(page_text)
                            extracted_text += page_text + "\n"

                # Build page-marked text for PRD v2 extraction
                extracted_text_with_pages = inject_page_markers(page_texts)
            except Exception as e:
                logger.error(f"Error extracting PDF text: {e}")
                raise HTTPException(
                    status_code=422,
                    detail={
                        "success": False,
                        "error_code": "POL_8003",
                        "message": f"Unable to extract information from PDF: {str(e)}"
                    }
                )

            if not extracted_text.strip():
                raise HTTPException(
                    status_code=422,
                    detail={
                        "success": False,
                        "error_code": "POL_8003",
                        "message": "Unable to extract information from PDF: No text content found in the uploaded file"
                    }
                )

        elif is_image_upload:
            # Extract text from images using DeepSeek Vision
            logger.info(f"📷 Extracting text from {len(image_contents)} image(s) using DeepSeek Vision...")
            try:
                extracted_text = await asyncio.to_thread(
                    extract_text_from_images_deepseek,
                    image_contents,
                    image_filenames
                )
            except Exception as e:
                logger.error(f"Error extracting text from images: {e}")
                raise HTTPException(
                    status_code=422,
                    detail={
                        "success": False,
                        "error_code": "POL_8003",
                        "message": f"Unable to extract information from images: {str(e)}"
                    }
                )

            if not extracted_text.strip():
                raise HTTPException(
                    status_code=422,
                    detail={
                        "success": False,
                        "error_code": "POL_8003",
                        "message": "Unable to extract information from images: No text content could be recognized. Please ensure the images are clear and readable."
                    }
                )

            logger.info(f"✅ Successfully extracted {len(extracted_text)} characters from images")
            # For images, treat each image as a page
            extracted_text_with_pages = inject_page_markers(
                [extracted_text]  # Single "page" for image-based extraction
            )

        # Use DeepSeek to extract policy information
        # IMPORTANT: Run blocking DeepSeek calls in thread pool to avoid blocking event loop
        logger.info("Extracting policy information with DeepSeek (non-blocking)...")

        # Extract UIN - DeepSeek AI first, then deterministic regex fallback
        extracted_uin = await asyncio.to_thread(extract_uin_from_text_deepseek, extracted_text)
        if not extracted_uin:
            extracted_uin = _extract_uin_regex(extracted_text)
            if extracted_uin:
                logger.info(f"UIN extracted via regex fallback: {extracted_uin}")
        logger.info(f"Extracted UIN: {extracted_uin}")

        # Identify policy type — Hibiscus 3-tier classifier (Rule → Scoring → LLM stub)
        classification_result = await asyncio.to_thread(
            _hibiscus_classify, extracted_text, "", "", extracted_uin or ""
        )
        policy_type = classification_result.get_legacy_type()
        logger.info(
            f"Hibiscus classification: {policy_type} "
            f"(detail={classification_result.policy_type.value}, "
            f"conf={classification_result.confidence:.3f}, "
            f"tier={classification_result.tier_used})"
        )

        # ==================== VALIDATE DOCUMENT & POLICY TYPE ====================
        # Check if this is a valid insurance document and if the policy type is supported

        # 1. Validate if document appears to be insurance
        validation_result = validate_insurance_document(extracted_text, policy_type)

        if not validation_result["is_valid"]:
            logger.warning(f"Document validation failed: {validation_result['error_message']}")
            raise HTTPException(
                status_code=422,
                detail={
                    "success": False,
                    "error_code": validation_result["error_code"],
                    "message": validation_result["error_message"],
                    "isInsurance": validation_result.get("is_insurance", False),
                    "isSupported": validation_result.get("is_supported", False),
                    "unsupportedType": validation_result.get("unsupported_type")
                }
            )

        # 2. Additional check for explicitly unsupported policy types from AI detection
        unsupported_category = is_unsupported_policy_type(policy_type)
        if unsupported_category:
            logger.warning(f"Unsupported policy type detected: {policy_type} ({unsupported_category})")
            raise HTTPException(
                status_code=422,
                detail={
                    "success": False,
                    "error_code": "POL_8011",
                    "message": f"Sorry, Eazr currently does not support {unsupported_category}. We support Health, Life, Motor, Accidental, and Travel insurance policies.",
                    "isInsurance": True,
                    "isSupported": False,
                    "detectedType": policy_type,
                    "unsupportedType": unsupported_category,
                    "supportedTypes": ["Health", "Life", "Motor", "Accidental", "Travel"]
                }
            )

        logger.info(f"✅ Document validation passed. Policy type: {policy_type}")

        # Fetch policy details from database if UIN is found
        db_policy_data = None
        if extracted_uin and policy_type != "unknown":
            db_policy_data = await asyncio.to_thread(fetch_policy_from_db_deepseek, extracted_uin, policy_type)

        # ==================== INSURANCE_INDIA DB MATCHING ====================
        # Match classification result against the insurance_india PostgreSQL DB
        # for validated category/subcategory IDs and product enrichment
        db_match_result = await asyncio.to_thread(match_product_from_db, classification_result)
        if db_match_result.get("matched"):
            logger.info(
                f"DB match: category_id={db_match_result['validation'].get('category_id')}, "
                f"subcategory_id={db_match_result['validation'].get('subcategory_id')}, "
                f"products_found={len(db_match_result.get('products', []))}"
            )
        else:
            logger.info(f"DB match: no match ({db_match_result.get('reason', 'no valid mapping')})")

        # If UIN found, also try direct product lookup from insurance_india
        db_product_by_uin = None
        if extracted_uin:
            db_product_by_uin = await asyncio.to_thread(get_product_by_uin, extracted_uin)
            if db_product_by_uin:
                logger.info(f"UIN match in insurance_india: {db_product_by_uin.get('product_name', 'unknown')}")

        # Save original PDF text before enrichment for Check 5 verification
        _original_pdf_text = extracted_text

        # ==================== UIN WEB ENRICHMENT ====================
        # If PDF data is sparse (short doc, missing T&C), search the web using UIN
        # to fetch full policy terms, benefits, exclusions, waiting periods, etc.
        from services.uin_web_enrichment_service import is_data_insufficient, enrich_policy_via_uin, format_enrichment_for_prompt

        _text_to_check = extracted_text_with_pages or extracted_text
        insufficient, insufficiency_reason = is_data_insufficient(_text_to_check, policy_type=policy_type)

        if insufficient and extracted_uin:
            logger.info(f"UIN enrichment: Data insufficient ({insufficiency_reason}), enriching via web for UIN {extracted_uin}")
            try:
                enrichment_data = await enrich_policy_via_uin(
                    extracted_uin, policy_type,
                    extracted_text_snippet=(_text_to_check or "")[:4000]
                )
                if enrichment_data:
                    enrichment_text = "\n\n[Web-Enriched Policy Terms & Conditions]\n" + format_enrichment_for_prompt(enrichment_data)
                    extracted_text += enrichment_text
                    if extracted_text_with_pages:
                        extracted_text_with_pages += enrichment_text
                    logger.info(f"UIN enrichment: Appended {len(enrichment_text)} chars of enriched T&C data")
                else:
                    logger.info("UIN enrichment: No enrichment data found, continuing with PDF data only")
            except Exception as e:
                logger.warning(f"UIN enrichment: Failed ({e}), continuing with PDF data only")
        elif insufficient:
            logger.info(f"UIN enrichment: Data insufficient ({insufficiency_reason}) but no UIN available, skipping")

        # Extract policy details using DeepSeek (deepseek_client already imported above)
        # PRD v2: Use type-specific extraction prompt with ConfidenceField format
        v2_system_prompt, extraction_prompt, v2_category = build_v2_extraction_prompt(
            extracted_text_with_pages or extracted_text,
            policy_type,
        )
        logger.info(f"Using PRD v2 {v2_category} extraction prompt ({len(extraction_prompt)} chars)")
        # Store raw v2 extraction for extractionV2 response field
        v2_raw_extraction = {}
        v2_extraction_metadata = {}
        four_check_result = {}
        pdf_text_verification = {}
        llm_verification_result = {}
        universal_scores = {}
        zone_classification = {}
        verdict = {}
        irdai_compliance = {}
        zone_recommendations = {}


        try:
            # ==================== PRD v2 EXTRACTION (DeepSeek Call #1) ====================
            # Uses type-specific prompt with ConfidenceField format {value, source_page, confidence}
            # Run in thread pool to avoid blocking the event loop
            def _call_deepseek_analysis():
                return deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": v2_system_prompt
                        },
                        {
                            "role": "user",
                            "content": extraction_prompt
                        }
                    ],
                    temperature=0.0,
                    max_tokens=4000
                )

            analysis_response = await asyncio.to_thread(_call_deepseek_analysis)
            analysis_text = analysis_response.choices[0].message.content.strip()
            logger.info(f"DeepSeek v2 extraction response (first 200 chars): {analysis_text[:200]}")

            # Parse v2 response (ConfidenceField format)
            v2_raw_extraction = parse_v2_extraction_response(analysis_text)
            v2_extraction_metadata = build_extraction_metadata(v2_raw_extraction, v2_category)
            logger.info(
                f"V2 extraction: {v2_extraction_metadata.get('fields_extracted', 0)} fields, "
                f"confidence={v2_extraction_metadata.get('overall_confidence', 0)}"
            )

            # Map v2 → v1 format for backward compatibility with existing pipeline
            extracted_data = v2_to_v1(v2_raw_extraction, v2_category)

            # Override pedWaitingPeriodCompleted with computed value (date-based, not AI guess)
            if v2_category == "health" and v2_raw_extraction:
                computed_ped = _compute_ped_completed(v2_raw_extraction)
                if "pedWaitingPeriodCompleted" in v2_raw_extraction:
                    v2_raw_extraction["pedWaitingPeriodCompleted"]["value"] = computed_ped
                else:
                    v2_raw_extraction["pedWaitingPeriodCompleted"] = {
                        "value": computed_ped,
                        "source_page": None,
                        "confidence": 0.9,
                    }

                # ── Fix: Normalize string consumablesCoverage to boolean ──
                cons_field = v2_raw_extraction.get("consumablesCoverage", {})
                if isinstance(cons_field, dict):
                    _cons_v = cons_field.get("value")
                    if isinstance(_cons_v, str) and _cons_v.strip():
                        _cons_lower = _cons_v.lower().strip()
                        if _cons_lower in ("false", "no", "not covered", "not available", "nil", "none", "0"):
                            cons_field["value"] = False
                        elif _cons_lower not in ("", "null"):
                            # Any meaningful string like "Upto Sum Insured", "Covered", etc. → True
                            cons_field["value"] = True
                            logger.info(f"consumablesCoverage string→bool: '{_cons_v}' → True")

                # Validate consumablesCoverage: only keep true if the details text
                # actually contains "consumable" — prevents false positives from
                # generic coverage phrases the AI may misinterpret
                cons_field = v2_raw_extraction.get("consumablesCoverage", {})
                if isinstance(cons_field, dict) and cons_field.get("value") is True:
                    details_field = v2_raw_extraction.get("consumablesCoverageDetails", {})
                    details_text = str(details_field.get("value", "") if isinstance(details_field, dict) else details_field).lower()
                    # Check if the details actually mention consumables explicitly
                    if "consumable" not in details_text:
                        cons_field["value"] = False
                        cons_field["confidence"] = 0.9
                        logger.info("Consumables override: set to false (details don't mention consumables)")
                # Reverse sync: if boolean is false/null but details have a meaningful value
                elif isinstance(cons_field, dict) and cons_field.get("value") is not True:
                    details_field = v2_raw_extraction.get("consumablesCoverageDetails", {})
                    details_val = details_field.get("value", "") if isinstance(details_field, dict) else details_field
                    details_text = str(details_val).lower().strip() if details_val else ""
                    if details_text and details_text not in ("details", "null", "none", "", "0"):
                        cons_field["value"] = True
                        cons_field["confidence"] = 0.85
                        logger.info(f"Consumables reverse-sync: set to true (details: '{details_text[:50]}')")

                # Bug fix: If Claim Shield add-on is present, it covers consumables
                # (non-payable items including consumables). Override consumablesCoverage to true.
                claim_shield_field = v2_raw_extraction.get("claimShield", {})
                claim_shield_val = claim_shield_field.get("value") if isinstance(claim_shield_field, dict) else claim_shield_field
                if claim_shield_val is True:
                    cons_field = v2_raw_extraction.get("consumablesCoverage", {})
                    if isinstance(cons_field, dict) and cons_field.get("value") is not True:
                        cons_field["value"] = True
                        cons_field["confidence"] = 0.9
                        logger.info("Consumables override: set to true (Claim Shield add-on covers consumables)")
                    elif not isinstance(cons_field, dict):
                        v2_raw_extraction["consumablesCoverage"] = {
                            "value": True, "source_page": None, "confidence": 0.9,
                        }
                        logger.info("Consumables override: created as true (Claim Shield add-on covers consumables)")

                # ── Fix 3: Infer missing member genders from relationship ──
                members_field = v2_raw_extraction.get("insuredMembers", {})
                members_list = members_field.get("value") if isinstance(members_field, dict) else members_field
                if isinstance(members_list, list):
                    _FEMALE_RELS = {"wife", "spouse", "daughter", "mother", "sister",
                                    "daughter-in-law", "mother-in-law"}
                    _MALE_RELS = {"husband", "son", "father", "brother",
                                  "son-in-law", "father-in-law"}
                    for _m in members_list:
                        if not _m.get("memberGender"):
                            _rel = str(_m.get("memberRelationship", "")).lower().strip()
                            if _rel in _FEMALE_RELS:
                                _m["memberGender"] = "Female"
                                logger.info(f"Gender inferred: {_m.get('memberName','')} → Female (rel={_rel})")
                            elif _rel in _MALE_RELS:
                                _m["memberGender"] = "Male"
                                logger.info(f"Gender inferred: {_m.get('memberName','')} → Male (rel={_rel})")

                # ── Fix: Compute totalSumInsuredAllMembers for Individual policies ──
                # When members have different SIs (Individual policy), sumInsured may only
                # capture one member's SI. Compute aggregate for accurate scoring.
                if isinstance(members_list, list) and len(members_list) > 1:
                    _per_member_sis = []
                    for _m in members_list:
                        _msi = _m.get("memberSumInsured")
                        if _msi is not None:
                            try:
                                _msi_val = float(str(_msi).replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip())
                                if _msi_val > 0:
                                    _per_member_sis.append(_msi_val)
                            except (ValueError, TypeError):
                                pass
                    if len(_per_member_sis) > 1 and len(set(_per_member_sis)) > 1:
                        _total_si = sum(_per_member_sis)
                        _max_si = max(_per_member_sis)
                        v2_raw_extraction["totalSumInsuredAllMembers"] = {
                            "value": _total_si, "source_page": None, "confidence": 0.85,
                        }
                        # If the extracted sumInsured only captured one member's SI, note it
                        _extracted_si_field = v2_raw_extraction.get("sumInsured", {})
                        _extracted_si = _extracted_si_field.get("value") if isinstance(_extracted_si_field, dict) else _extracted_si_field
                        try:
                            _extracted_si_num = float(str(_extracted_si).replace(",", "")) if _extracted_si else 0
                        except (ValueError, TypeError):
                            _extracted_si_num = 0
                        if _extracted_si_num > 0 and _extracted_si_num == _max_si and _total_si > _max_si:
                            logger.info(
                                f"Individual policy: sumInsured={_extracted_si_num} is only highest member SI. "
                                f"Per-member SIs: {_per_member_sis}, total={_total_si}"
                            )

                # ── Fix 4: Clear previousPolicyNumber if same as current (strengthened) ──
                _prev_f = v2_raw_extraction.get("previousPolicyNumber", {})
                _curr_f = v2_raw_extraction.get("policyNumber", {})
                _prev_v = _prev_f.get("value") if isinstance(_prev_f, dict) else _prev_f
                _curr_v = _curr_f.get("value") if isinstance(_curr_f, dict) else _curr_f
                # Normalize both to strings for comparison, handle int/float values
                _prev_s = str(_prev_v).strip() if _prev_v is not None else ""
                _curr_s = str(_curr_v).strip() if _curr_v is not None else ""
                if _prev_s and _curr_s and (_prev_s == _curr_s or _prev_s in _curr_s or _curr_s in _prev_s):
                    if isinstance(_prev_f, dict):
                        _prev_f["value"] = None
                        _prev_f["confidence"] = 0.0
                    else:
                        v2_raw_extraction["previousPolicyNumber"] = {"value": None, "source_page": None, "confidence": 0.0}
                    logger.warning(f"previousPolicyNumber '{_prev_s}' same as/subset of current '{_curr_s}' — cleared")

                # ── Fix 5: Normalize policyType/coverType from product variant names ──
                _PLAN_TO_TYPE = {
                    "family first": "Family Floater", "reassure": "Family Floater",
                    "family health optima": "Family Floater", "fho": "Family Floater",
                }
                for _tf_name in ("policyType", "coverType"):
                    _tf_data = v2_raw_extraction.get(_tf_name, {})
                    _tf_val = _tf_data.get("value") if isinstance(_tf_data, dict) else _tf_data
                    if _tf_val and str(_tf_val).lower().strip() in _PLAN_TO_TYPE:
                        _new_type = _PLAN_TO_TYPE[str(_tf_val).lower().strip()]
                        if isinstance(_tf_data, dict):
                            _tf_data["value"] = _new_type
                        logger.info(f"{_tf_name} normalized: '{_tf_val}' → '{_new_type}'")

                # ── Fix: Infer coverType=Floater when Individual + multiple same-SI members ──
                _ct_field = v2_raw_extraction.get("coverType", {})
                _ct_val = str(_ct_field.get("value", "") if isinstance(_ct_field, dict) else (_ct_field or "")).lower().strip()
                if _ct_val == "individual" and isinstance(members_list, list) and len(members_list) > 1:
                    # Check if all members share the same SI (floater characteristic)
                    _member_sis = set()
                    for _m in members_list:
                        _msi = _m.get("memberSumInsured")
                        try:
                            _msi_val = float(str(_msi).replace(",", "").replace("₹", "").strip()) if _msi else 0
                        except (ValueError, TypeError):
                            _msi_val = 0
                        if _msi_val > 0:
                            _member_sis.add(_msi_val)
                    # Inline SI extraction (_safe_num_v2 not yet defined at this point)
                    _si_f = v2_raw_extraction.get("sumInsured", {})
                    _si_v = _si_f.get("value") if isinstance(_si_f, dict) else _si_f
                    try:
                        _policy_si = float(str(_si_v).replace(",", "").replace("₹", "").strip()) if _si_v else 0.0
                    except (ValueError, TypeError):
                        _policy_si = 0.0
                    # Floater: all members share same SI OR all member SIs == policy SI
                    if len(_member_sis) <= 1 or (_policy_si > 0 and all(s == _policy_si for s in _member_sis)):
                        if isinstance(_ct_field, dict):
                            _ct_field["value"] = "Floater"
                            _ct_field["confidence"] = 0.85
                        logger.info(f"coverType: Individual → Floater ({len(members_list)} members, same SI)")

                # Bug fix: Compute cumulativeBonusAmount from totalEffectiveCoverage - sumInsured
                # when CB is 0/missing but totalEffectiveCoverage > sumInsured (e.g. Tata AIG Medicare)
                def _safe_num_v2(field_name):
                    f = v2_raw_extraction.get(field_name, {})
                    v = f.get("value") if isinstance(f, dict) else f
                    if v is None:
                        return 0.0
                    if isinstance(v, (int, float)):
                        return float(v)
                    if isinstance(v, str):
                        cleaned = v.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
                        try:
                            return float(cleaned)
                        except (ValueError, TypeError):
                            return 0.0
                    return 0.0

                _si = _safe_num_v2("sumInsured")
                _cb = _safe_num_v2("cumulativeBonusAmount")
                _ncb_amt = _safe_num_v2("accumulatedNcbAmount") or _safe_num_v2("ncbAmount")
                _total_eff = _safe_num_v2("totalEffectiveCoverage")
                _inflation = _safe_num_v2("inflationShieldAmount")

                if _si > 0 and _cb == 0 and _ncb_amt == 0 and _total_eff > _si:
                    # totalEffective = SI + CB + inflation. Derive CB.
                    _derived_cb = _total_eff - _si - _inflation
                    if _derived_cb > 0:
                        v2_raw_extraction["cumulativeBonusAmount"] = {
                            "value": _derived_cb, "source_page": None, "confidence": 0.8,
                        }
                        # Also update totalEffectiveCoverage if it wasn't set
                        logger.info(f"CB derivation: totalEffective={_total_eff} - SI={_si} - inflation={_inflation} = CB={_derived_cb}")

                # Bug fix: Correct maxNcbPercentage when accumulated bonus exceeds stated max
                # (e.g., Star Health FHO allows up to 100% but prompt defaults to 50%)
                _max_ncb_field = v2_raw_extraction.get("maxNcbPercentage", {})
                _max_ncb_val = _safe_num_v2("maxNcbPercentage")
                _accum_bonus = max(_safe_num_v2("cumulativeBonusAmount"),
                                   _safe_num_v2("accumulatedNcbAmount"),
                                   _safe_num_v2("ncbAmount"))
                if _si > 0 and _accum_bonus > 0:
                    _actual_accum_pct = (_accum_bonus / _si) * 100
                    if _actual_accum_pct > _max_ncb_val and _max_ncb_val > 0:
                        # Accumulated bonus exceeds stated max — max is wrong
                        _corrected_max = min(round(_actual_accum_pct / 10) * 10 + 10, 100)
                        if isinstance(_max_ncb_field, dict):
                            _max_ncb_field["value"] = f"{_corrected_max}%"
                            _max_ncb_field["confidence"] = 0.8
                        else:
                            v2_raw_extraction["maxNcbPercentage"] = {
                                "value": f"{_corrected_max}%", "source_page": None, "confidence": 0.8,
                            }
                        logger.info(f"maxNCB correction: accumulated {_actual_accum_pct:.0f}% > stated max {_max_ncb_val}% → corrected to {_corrected_max}%")

                # ── Fix: Fill ncbPercentage from cumulativeBonusAmount when missing ──
                _ncb_pct_f = v2_raw_extraction.get("ncbPercentage", {})
                _ncb_pct_v = _ncb_pct_f.get("value") if isinstance(_ncb_pct_f, dict) else _ncb_pct_f
                _ncb_empty = (
                    _ncb_pct_v is None
                    or str(_ncb_pct_v).lower().strip() in ("", "null", "none", "0", "0%", "n/a")
                )
                if _ncb_empty:
                    _cb_for_ncb = max(_safe_num_v2("cumulativeBonusAmount"),
                                      _safe_num_v2("accumulatedNcbAmount"),
                                      _safe_num_v2("ncbAmount"))
                    _si_for_ncb = _safe_num_v2("sumInsured")
                    if _cb_for_ncb > 0 and _si_for_ncb > 0:
                        _derived_ncb = round((_cb_for_ncb / _si_for_ncb) * 100)
                        if isinstance(_ncb_pct_f, dict):
                            _ncb_pct_f["value"] = f"{_derived_ncb}%"
                            _ncb_pct_f["confidence"] = 0.80
                        else:
                            v2_raw_extraction["ncbPercentage"] = {
                                "value": f"{_derived_ncb}%", "source_page": None, "confidence": 0.80,
                            }
                        logger.info(f"ncbPercentage derived: CB={_cb_for_ncb}/SI={_si_for_ncb} → {_derived_ncb}%")

                # Bug fix: Compute continuousCoverageYears from firstEnrollmentDate if available
                _enrollment_field = v2_raw_extraction.get("firstEnrollmentDate") or v2_raw_extraction.get("insuredSinceDate")
                if isinstance(_enrollment_field, dict):
                    _enrollment_val = _enrollment_field.get("value")
                else:
                    _enrollment_val = _enrollment_field
                if _enrollment_val:
                    _enrollment_str = str(_enrollment_val).strip()
                    for _fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d/%m/%Y", "%d / %m / %Y",
                                 "%d-%m-%Y", "%d %b %Y", "%d %B %Y", "%Y/%m/%d"):
                        try:
                            _enrollment_date = datetime.strptime(_enrollment_str, _fmt)
                            _elapsed_years = (datetime.now() - _enrollment_date).days / 365.25
                            _computed_ccy = int(_elapsed_years)
                            _current_ccy = _safe_num_v2("continuousCoverageYears")
                            # Only override if computed value is significantly larger (>2x)
                            # to avoid overriding legitimate short tenure from current insurer
                            if _computed_ccy > 1 and (_current_ccy == 0 or _computed_ccy > _current_ccy * 2):
                                v2_raw_extraction["continuousCoverageYears"] = {
                                    "value": _computed_ccy, "source_page": None, "confidence": 0.8,
                                }
                                logger.info(f"continuousCoverageYears override: {_current_ccy} → {_computed_ccy} (from firstEnrollmentDate {_enrollment_str})")
                            break
                        except (ValueError, TypeError):
                            continue

                # ── Fix: Family Floater memberSumInsured fill ──────────────────
                # In Family Floater policies, all members share the same SI.
                # LLM often extracts 0 for non-primary members. Fill with policy SI.
                _cover_type_f = v2_raw_extraction.get("coverType", {})
                _cover_type_v = str(
                    _cover_type_f.get("value", "") if isinstance(_cover_type_f, dict) else (_cover_type_f or "")
                ).lower().strip()
                _policy_type_f = v2_raw_extraction.get("policyType", {})
                _policy_type_v = str(
                    _policy_type_f.get("value", "") if isinstance(_policy_type_f, dict) else (_policy_type_f or "")
                ).lower().strip()
                _is_floater = "floater" in _cover_type_v or "floater" in _policy_type_v
                if _is_floater and isinstance(members_list, list) and len(members_list) > 0:
                    _policy_si = _safe_num_v2("sumInsured")
                    if _policy_si > 0:
                        for _m in members_list:
                            _msi = _m.get("memberSumInsured")
                            try:
                                _msi_num = float(str(_msi).replace(",", "").replace("₹", "").strip()) if _msi else 0
                            except (ValueError, TypeError):
                                _msi_num = 0
                            if _msi_num == 0:
                                _m["memberSumInsured"] = int(_policy_si)
                                logger.info(f"Floater SI fill: {_m.get('memberName', '')} SI=0 → {int(_policy_si)}")

                # ── Fix: basePremium consistency check ────────────────────────
                # If totalPremium is known, validate basePremium makes sense.
                # For policies with GST: totalPremium ≈ basePremium * 1.18
                # For GST-exempt: totalPremium ≈ basePremium
                # If basePremium looks like one member's share, derive from total.
                _bp = _safe_num_v2("basePremium")
                _tp = _safe_num_v2("totalPremium")
                _gst_val = _safe_num_v2("gst")
                if _tp > 0 and _bp > 0:
                    # Check: basePremium + GST should ≈ totalPremium
                    _expected_bp = _tp - _gst_val if _gst_val > 0 else _tp / 1.18
                    # If basePremium is significantly less than expected (< 80%), it's likely one member's
                    if _bp < _expected_bp * 0.80:
                        # Try to derive correct basePremium from totalPremium - GST
                        if _gst_val > 0:
                            _corrected_bp = _tp - _gst_val
                        else:
                            # GST is typically 18% on health insurance
                            _corrected_bp = round(_tp / 1.18, 2)
                        if _corrected_bp > _bp:
                            _bp_field = v2_raw_extraction.get("basePremium", {})
                            if isinstance(_bp_field, dict):
                                _bp_field["value"] = _corrected_bp
                                _bp_field["confidence"] = 0.80
                            else:
                                v2_raw_extraction["basePremium"] = {
                                    "value": _corrected_bp, "source_page": None, "confidence": 0.80,
                                }
                            logger.info(
                                f"basePremium correction: {_bp} → {_corrected_bp} "
                                f"(totalPremium={_tp}, gst={_gst_val})"
                            )

                # ── Fix: GST confidence for explicitly zero/exempt ────────────
                # When GST is 0 but confidence is also 0.0, check if it's explicitly
                # mentioned as exempt/nil in the document (confidence should be 1.0).
                _gst_field = v2_raw_extraction.get("gst", {})
                if isinstance(_gst_field, dict):
                    _gst_v = _gst_field.get("value")
                    _gst_conf = _gst_field.get("confidence", 0)
                    # GST is 0 (or "0" or "Nil") with low confidence
                    _gst_is_zero = (
                        _gst_v == 0 or _gst_v == "0" or _gst_v is None
                        or str(_gst_v).lower().strip() in ("0", "nil", "exempt", "0.0", "0.00")
                    )
                    if _gst_is_zero and _gst_conf < 0.5:
                        # Check if totalPremium == basePremium (no GST component)
                        _tp_check = _safe_num_v2("totalPremium")
                        _bp_check = _safe_num_v2("basePremium")
                        if _tp_check > 0 and _bp_check > 0 and abs(_tp_check - _bp_check) < 2:
                            # totalPremium == basePremium means GST is genuinely 0
                            _gst_field["value"] = 0
                            _gst_field["confidence"] = 1.0
                            logger.info("GST confidence fix: 0.0 → 1.0 (totalPremium == basePremium, GST exempt)")
                        # Also check if source_page exists (LLM found "GST: 0" explicitly)
                        elif _gst_field.get("source_page") is not None:
                            _gst_field["value"] = 0
                            _gst_field["confidence"] = 1.0
                            logger.info("GST confidence fix: 0.0 → 1.0 (source_page present, explicitly stated)")

                # ── Fix: Brand-aware consumablesCoverage mapping ──────────────
                # Some insurers use branded names for consumables coverage:
                # - HDFC ERGO "Protect Benefit" = covers non-medical/consumable items
                # - Star Health "Claim Shield" (already handled above)
                # Check extracted text or addOnPoliciesList for these branded benefits.
                _insurer_name = str(
                    v2_raw_extraction.get("insurerName", {}).get("value", "")
                    if isinstance(v2_raw_extraction.get("insurerName"), dict)
                    else v2_raw_extraction.get("insurerName", "")
                ).lower()
                cons_field = v2_raw_extraction.get("consumablesCoverage", {})
                _cons_val = cons_field.get("value") if isinstance(cons_field, dict) else cons_field
                if _cons_val is not True:
                    # Check addOnPoliciesList for brand-named consumable add-ons
                    _addons_field = v2_raw_extraction.get("addOnPoliciesList", {})
                    _addons = _addons_field.get("value") if isinstance(_addons_field, dict) else _addons_field
                    _CONSUMABLE_ADDON_NAMES = {
                        "protect benefit", "protect", "non-medical expenses",
                        "non medical expenses", "consumable cover", "consumables",
                        "consumable expenses cover",
                    }
                    _found_consumable_addon = False
                    if isinstance(_addons, list):
                        for _addon in _addons:
                            _addon_name = str(_addon.get("addOnName", "") if isinstance(_addon, dict) else _addon).lower().strip()
                            if any(cn in _addon_name for cn in _CONSUMABLE_ADDON_NAMES):
                                _found_consumable_addon = True
                                break
                    # Also check otherAddOnPremiums dict keys
                    _other_addons_field = v2_raw_extraction.get("otherAddOnPremiums", {})
                    _other_addons = _other_addons_field.get("value") if isinstance(_other_addons_field, dict) else _other_addons_field
                    if isinstance(_other_addons, dict):
                        for _key in _other_addons:
                            if any(cn in str(_key).lower() for cn in _CONSUMABLE_ADDON_NAMES):
                                _found_consumable_addon = True
                                break
                    if _found_consumable_addon:
                        if isinstance(cons_field, dict):
                            cons_field["value"] = True
                            cons_field["confidence"] = 0.90
                        else:
                            v2_raw_extraction["consumablesCoverage"] = {
                                "value": True, "source_page": None, "confidence": 0.90,
                            }
                        logger.info("consumablesCoverage: set true (brand-named add-on detected)")

                # ── Fix: Brand-aware NCB/Cumulative Bonus mapping ─────────────
                # Some insurers use branded names for NCB-equivalent benefits:
                # - HDFC ERGO "Plus Benefit" = 50% SI increase per claim-free year (NCB)
                # - HDFC ERGO "Secure Benefit" = 200% SI multiplier (not NCB)
                _ncb_pct_field = v2_raw_extraction.get("ncbPercentage", {})
                _ncb_pct_val = _ncb_pct_field.get("value") if isinstance(_ncb_pct_field, dict) else _ncb_pct_field
                _ncb_is_missing = (
                    _ncb_pct_val is None
                    or str(_ncb_pct_val).lower().strip() in ("", "null", "none", "not covered", "0", "0%", "n/a")
                )
                if _ncb_is_missing:
                    _NCB_ADDON_NAMES = {
                        "plus benefit": "50%",
                        "cumulative bonus": None,  # Use extracted value
                        "no claim bonus": None,
                        "ncb benefit": None,
                    }
                    _found_ncb_addon = False
                    _ncb_value = None
                    # Check addOnPoliciesList
                    if isinstance(_addons, list):
                        for _addon in _addons:
                            _addon_name = str(_addon.get("addOnName", "") if isinstance(_addon, dict) else _addon).lower().strip()
                            for _ncb_name, _default_val in _NCB_ADDON_NAMES.items():
                                if _ncb_name in _addon_name:
                                    _found_ncb_addon = True
                                    _ncb_value = _default_val
                                    break
                            if _found_ncb_addon:
                                break
                    # Check otherAddOnPremiums dict keys
                    if not _found_ncb_addon and isinstance(_other_addons, dict):
                        for _key in _other_addons:
                            _key_lower = str(_key).lower()
                            for _ncb_name, _default_val in _NCB_ADDON_NAMES.items():
                                if _ncb_name in _key_lower:
                                    _found_ncb_addon = True
                                    _ncb_value = _default_val
                                    break
                            if _found_ncb_addon:
                                break
                    if _found_ncb_addon and _ncb_value:
                        if isinstance(_ncb_pct_field, dict):
                            _ncb_pct_field["value"] = _ncb_value
                            _ncb_pct_field["confidence"] = 0.85
                        else:
                            v2_raw_extraction["ncbPercentage"] = {
                                "value": _ncb_value, "source_page": None, "confidence": 0.85,
                            }
                        logger.info(f"ncbPercentage: set '{_ncb_value}' (brand-named NCB add-on detected)")

                # Re-map v2 → v1 after all health overrides
                extracted_data = v2_to_v1(v2_raw_extraction, v2_category)

            # ── Life insurance post-processing overrides ──────────────────
            if v2_category == "life" and v2_raw_extraction:
                _postprocess_life_extraction(v2_raw_extraction)
                # Re-map v2 → v1 after overrides so extracted_data stays in sync
                extracted_data = v2_to_v1(v2_raw_extraction, v2_category)

            # ── Travel insurance post-processing overrides ────────────────
            if v2_category == "travel" and v2_raw_extraction:
                _postprocess_travel_extraction(v2_raw_extraction)
                # Re-map v2 → v1 after overrides so extracted_data stays in sync
                extracted_data = v2_to_v1(v2_raw_extraction, v2_category)

            # Run PRD v2 4-check validation
            four_check_result = run_four_checks(v2_raw_extraction, v2_category)

            # Run Check 5: PDF text verification (catches hallucinated values)
            pdf_text_verification = verify_against_pdf_text(
                v2_raw_extraction, _original_pdf_text, v2_category
            )

            # Run Check 6: LLM verification & auto-correction
            # Pass Check 5 mismatches so the LLM knows which fields need extra attention
            # Also pass verify_against_pdf_text for re-checking after corrections
            _check5_mismatches = pdf_text_verification.get("mismatches", []) if pdf_text_verification else []
            llm_verification_result = await llm_verify_and_correct(
                deepseek_client,
                v2_raw_extraction,
                extracted_text_with_pages or _original_pdf_text,
                v2_category,
                check5_mismatches=_check5_mismatches if _check5_mismatches else None,
                pdf_text_verify_fn=verify_against_pdf_text,
                original_pdf_text=_original_pdf_text,
            )

            # If corrections were applied, re-map v2 -> v1 and re-run Check 5
            if llm_verification_result.get("correctionsApplied", 0) > 0:
                extracted_data = v2_to_v1(v2_raw_extraction, v2_category)
                # Re-run Check 5 on corrected data for final status
                pdf_text_verification = verify_against_pdf_text(
                    v2_raw_extraction, _original_pdf_text, v2_category
                )
                logger.info(
                    f"LLM verifier: {llm_verification_result['correctionsApplied']} "
                    f"corrections applied, re-mapped v2->v1, re-ran Check 5"
                )

            # ── Recompute pedWaitingPeriodCompleted AFTER LLM verification ──
            # The LLM verifier may have enriched preExistingDiseaseWaiting from web data
            # (e.g. "48 months") that wasn't in the PDF. Recompute now with the full data.
            if v2_category == "health" and v2_raw_extraction:
                recomputed_ped = _compute_ped_completed(v2_raw_extraction)
                ped_field = v2_raw_extraction.get("pedWaitingPeriodCompleted", {})
                old_val = ped_field.get("value") if isinstance(ped_field, dict) else ped_field
                if recomputed_ped != old_val:
                    if isinstance(ped_field, dict):
                        ped_field["value"] = recomputed_ped
                        ped_field["confidence"] = 0.9
                    else:
                        v2_raw_extraction["pedWaitingPeriodCompleted"] = {
                            "value": recomputed_ped, "source_page": None, "confidence": 0.9,
                        }
                    logger.info(f"pedWaitingPeriodCompleted recomputed after LLM verification: {old_val} → {recomputed_ped}")
                    # Re-map v2 → v1 to pick up the change
                    extracted_data = v2_to_v1(v2_raw_extraction, v2_category)

            # Compute PRD v2 universal scores (VFM, Coverage, Claim Readiness)
            universal_scores = compute_universal_scores(
                v2_raw_extraction, v2_category,
                insurer_name=extracted_data.get("insuranceProvider", ""),
            )

            # Classify features into 4 zones (green/lightGreen/amber/red)
            zone_classification = classify_zones(
                v2_raw_extraction, v2_category,
                insurer_name=extracted_data.get("insuranceProvider", ""),
            )

            # Generate PRD v2 verdict (headline, grade, action level)
            verdict = generate_verdict(universal_scores, zone_classification)

            # Check IRDAI regulatory compliance
            irdai_compliance = check_irdai_compliance(v2_raw_extraction, v2_category)

            # Generate zone-based recommendations from amber/red features
            zone_recommendations = generate_zone_recommendations(zone_classification, v2_category)

            # ==================== EAZR COMPANY PA OVERRIDE ====================
            # For EAZR complimentary PA policies only: override top-level scores/zones/
            # verdict/recommendations with positive framing. Detection uses the same
            # criteria as _is_eazr_company_pa() (groupPolicyholderName contains "EAZR").
            if v2_category == "pa":
                _gh = str(v2_raw_extraction.get("groupPolicyholderName", {}).get("value", "") if isinstance(v2_raw_extraction.get("groupPolicyholderName"), dict) else v2_raw_extraction.get("groupPolicyholderName", "")).upper()
                _pn = str(v2_raw_extraction.get("productName", {}).get("value", "") if isinstance(v2_raw_extraction.get("productName"), dict) else v2_raw_extraction.get("productName", "")).upper()
                _tp_raw = v2_raw_extraction.get("totalPremium", {})
                _tp_val = _tp_raw.get("value", 0) if isinstance(_tp_raw, dict) else _tp_raw
                try:
                    _tp = float(_tp_val or 0)
                except (ValueError, TypeError):
                    _tp = 0
                _is_eazr_pa = ("EAZR" in _gh) or ("EAZR DIGI" in _pn or "EAZR_DIGI" in _pn) or ("GC 360" in _pn and _tp <= 10)

                if _is_eazr_pa:
                    logger.info(">>> EAZR COMPANY PA detected — overriding top-level scores/zones/verdict/recommendations <<<")
                    _pa_si = 0
                    _pa_si_raw = v2_raw_extraction.get("paSumInsured", {})
                    try:
                        _pa_si = float((_pa_si_raw.get("value", 0) if isinstance(_pa_si_raw, dict) else _pa_si_raw) or 0)
                    except (ValueError, TypeError):
                        _pa_si = 0

                    universal_scores = {
                        "vfm": {
                            "score": 95,
                            "breakdown": {
                                "premiumToSiRatio": {"ratio": 0.0, "points": 35},
                                "coverageBreadth": {"count": 3, "maxCoverages": 5, "points": 30},
                                "additionalBenefits": {"count": 1, "points": 10},
                                "complimentaryNote": "This PA cover is provided as a complimentary benefit without any additional premium."
                            },
                            "label": "Excellent"
                        },
                        "coverageStrength": {
                            "score": 75,
                            "breakdown": {
                                "sumInsured": {"amount": _pa_si, "points": 10},
                                "accidentalDeath": {"percentage": 100.0, "points": 15},
                                "ptd": {"covered": True, "points": 15},
                                "ppd": {"covered": True, "points": 15},
                                "ttd": {"covered": False, "points": 0},
                                "medicalExpenses": {"covered": False, "points": 0},
                                "additionalBenefits": {"count": 1, "points": 5},
                                "complimentaryNote": "Accidental Death, Permanent Total Disability, and Permanent Partial Disability benefits are included under this complimentary cover."
                            },
                            "label": "Good"
                        },
                        "claimReadiness": {
                            "score": 90,
                            "deductions": [],
                            "csr": 96.74,
                            "label": "Excellent"
                        }
                    }

                    zone_classification = {
                        "summary": {"green": 4, "lightGreen": 2, "amber": 0, "red": 0},
                        "features": [
                            {
                                "featureId": "sum_insured", "featureName": "Sum Insured",
                                "zone": "green",
                                "explanation": f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{_pa_si:,.0f} is provided as a complimentary benefit under this policy, without any additional premium, and is subject to the applicable terms, conditions, and exclusions.",
                                "currentValue": f"\u20b9{_pa_si:,.0f}"
                            },
                            {
                                "featureId": "ad_benefit", "featureName": "Accidental Death Benefit",
                                "zone": "green",
                                "explanation": "Full Sum Insured payable on accidental death — 100% coverage.",
                                "currentValue": "100% of SI"
                            },
                            {
                                "featureId": "ptd", "featureName": "Permanent Total Disability",
                                "zone": "green",
                                "explanation": "PTD coverage included — financial support for permanent disabilities.",
                                "currentValue": "Covered"
                            },
                            {
                                "featureId": "ppd", "featureName": "Permanent Partial Disability",
                                "zone": "green",
                                "explanation": "PPD covered as per benefit schedule — partial disability protection included.",
                                "currentValue": "Covered"
                            },
                            {
                                "featureId": "ttd", "featureName": "Temporary Total Disability",
                                "zone": "lightGreen",
                                "explanation": "Temporary Total Disability benefit is not included under this complimentary PA cover. Hospitalization expenses, if any, are covered under your separate health insurance policy.",
                                "currentValue": "Not included"
                            },
                            {
                                "featureId": "medical_expenses", "featureName": "Medical Expenses",
                                "zone": "lightGreen",
                                "explanation": "Accident-related medical expenses are covered under your separate health insurance policy. This PA cover provides lump-sum benefits for accidental death and disability.",
                                "currentValue": "Covered under Health Insurance"
                            }
                        ]
                    }

                    verdict = {
                        "headline": "Complimentary PA Cover — No Additional Premium",
                        "overallGrade": "A",
                        "actionRequired": "none",
                        "explanation": f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{_pa_si:,.0f} is provided as a complimentary benefit under this policy, without any additional premium, and is subject to the applicable terms, conditions, and exclusions. Benefits include Accidental Death (100% of SI), Permanent Total Disability, and Permanent Partial Disability. Health Service — Doctors on Call is also included.",
                        "scoreSummary": {
                            "vfm": 95,
                            "coverage": 75,
                            "claimReadiness": 90,
                            "average": 86.7
                        },
                        "zoneSummary": {"green": 4, "lightGreen": 2, "amber": 0, "red": 0}
                    }

                    zone_recommendations = {
                        "urgent": [],
                        "recommended": [],
                        "totalAnnualCost": {"low": 0, "high": 0},
                        "totalMonthlyCost": {"low": 0, "high": 0},
                        "urgentCount": 0,
                        "recommendedCount": 0,
                        "note": "This PA cover is provided as a complimentary benefit without any additional premium. No actions are required at this time."
                    }

            # ==================== POLICY OWNERSHIP VALIDATION ====================
            # Name validation is skipped for both "self" and "family" policies.
            # The provided name is used as-is for policy records.
            original_extracted_policy_holder = extracted_data.get("policyHolderName", "").strip()
            original_extracted_insured_name = extracted_data.get("insuredName", "").strip()

            # Use original extracted name, fallback to insuredName
            extracted_policy_holder = original_extracted_policy_holder
            if not extracted_policy_holder:
                extracted_policy_holder = original_extracted_insured_name
            user_provided_name = name.strip()

            logger.info(f"ℹ️ Policy ownership info: policyFor='{policyFor}', providedName='{user_provided_name}', policyHolder='{extracted_policy_holder}' (from PDF). Name validation skipped.")

        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error: {je}")
            logger.error(f"Failed to parse: {analysis_text[:500] if 'analysis_text' in locals() else 'N/A'}")
            # Provide default extracted data
            extracted_data = {
                "policyNumber": "",
                "insuranceProvider": "",
                "policyType": policy_type,
                "coverageAmount": 0,
                "premium": 0,
                "premiumFrequency": "annually",
                "startDate": "",
                "endDate": "",
                "policyHolderName": name,
                "keyBenefits": [],
                "exclusions": [],
                "waitingPeriods": [],
                "criticalAreas": []
            }
        except HTTPException:
            # Re-raise HTTP exceptions (like POLICY_OWNERSHIP_MISMATCH) - don't catch them!
            raise
        except Exception as e:
            logger.error(f"Error in DeepSeek extraction: {e}")
            # Provide default extracted data
            extracted_data = {
                "policyNumber": "",
                "insuranceProvider": "",
                "policyType": policy_type,
                "coverageAmount": 0,
                "premium": 0,
                "premiumFrequency": "annually",
                "startDate": "",
                "endDate": "",
                "policyHolderName": name,
                "keyBenefits": [],
                "exclusions": [],
                "waitingPeriods": [],
                "criticalAreas": []
            }

        # Generate comprehensive gap analysis with industry-standard insights
        # Calculate age: prefer extracted member age from policy → form DOB → default 30
        user_age = 30  # Default
        _age_from_extraction = False
        if v2_raw_extraction:
            _gap_members_field = v2_raw_extraction.get("insuredMembers", {})
            _gap_members_val = _gap_members_field.get("value") if isinstance(_gap_members_field, dict) else _gap_members_field
            if isinstance(_gap_members_val, list) and _gap_members_val:
                for _gm in _gap_members_val:
                    if isinstance(_gm, dict) and str(_gm.get("memberRelationship", "")).lower() in ("self", "member", "primary", "proposer"):
                        _gm_age = _gm.get("memberAge")
                        if _gm_age and isinstance(_gm_age, (int, float)) and _gm_age > 0:
                            user_age = int(_gm_age)
                            _age_from_extraction = True
                        break
                if not _age_from_extraction and _gap_members_val:
                    _gm_first = _gap_members_val[0]
                    if isinstance(_gm_first, dict):
                        _gm_age = _gm_first.get("memberAge")
                        if _gm_age and isinstance(_gm_age, (int, float)) and _gm_age > 0:
                            user_age = int(_gm_age)
                            _age_from_extraction = True
        if not _age_from_extraction and dateOfBirth:
            try:
                user_age = (datetime.now() - datetime.strptime(dateOfBirth, "%Y-%m-%d")).days // 365
            except Exception:
                pass

        # Policy type specific analysis context
        policy_type_context = ""
        if "health" in policy_type.lower() or "medical" in policy_type.lower():
            policy_type_context = """
HEALTH INSURANCE ANALYSIS FRAMEWORK:
- Sum Insured Adequacy: Check if SI >= Rs.10L (metro), Rs.5L (non-metro) per person
- Room Rent Limits: Sub-limits reduce claim payouts significantly (1% or 2% of SI limits are restrictive)
- Co-payment: Any mandatory co-pay (10-20%) reduces effective coverage
- Disease-wise Sub-limits: Cataract, joint replacement, AYUSH limits
- Waiting Periods: Initial (30 days), PED (2-4 years), specific diseases (2 years)
- No Claim Bonus: Check if NCB protection available
- Restoration Benefit: Full restoration vs partial
- Day Care Procedures: 500+ procedures covered?
- Pre/Post Hospitalization: 60/180 days is standard
- Network Hospitals: Access to quality hospitals
- Mental Health Coverage: Now mandatory by IRDAI
- Maternity Coverage: If applicable
- Critical Illness: Not covered in base health plan

COMMON HEALTH GAPS TO CHECK:
1. Room rent limit causing claim reduction
2. Co-payment reducing effective coverage
3. Sub-limits on specific diseases
4. Long waiting periods for PED
5. No NCB protection
6. Limited restoration benefit
7. Missing critical illness cover
8. No personal accident cover"""
        elif "motor" in policy_type.lower() or "car" in policy_type.lower() or "vehicle" in policy_type.lower():
            policy_type_context = """
MOTOR INSURANCE ANALYSIS FRAMEWORK:
- IDV (Insured Declared Value): Should reflect current market value
- Zero Depreciation: Critical for new cars (< 5 years), saves 20-40% on claims
- Engine & Gearbox Protection: Covers hydrostatic lock damage
- NCB Protection: Protects accumulated no-claim bonus
- Return to Invoice: Covers gap between IDV and invoice value
- Roadside Assistance: 24/7 breakdown support
- Consumables Cover: Covers oil, nuts, bolts, bearings
- Tyre Cover: Expensive to replace, often excluded
- Key Replacement: Covers lost/stolen key
- Personal Accident Cover: Rs.15L mandatory for owner-driver

COMMON MOTOR GAPS TO CHECK:
1. No zero depreciation (major claim reduction)
2. Missing engine protection (hydrostatic lock not covered)
3. No NCB protection (lose years of bonus on one claim)
4. No roadside assistance
5. Missing consumables cover
6. Low PA cover (only Rs.15L statutory)
7. No return to invoice (gap on total loss)
8. No key replacement cover"""
        elif "life" in policy_type.lower() or "term" in policy_type.lower():
            policy_type_context = """
LIFE INSURANCE ANALYSIS FRAMEWORK:
- Sum Assured Adequacy: Should be 10-15x annual income
- Premium Paying Term: Shorter PPT vs policy term
- Critical Illness Rider: Covers major illnesses
- Accidental Death Benefit: Additional cover for accidents
- Disability Rider: Income replacement on disability
- Waiver of Premium: Premiums waived on disability
- Terminal Illness Benefit: Early payout on terminal diagnosis
- Return of Premium: Gets premiums back on survival

COMMON LIFE GAPS TO CHECK:
1. Inadequate sum assured (< 10x income)
2. No critical illness rider
3. No accidental death benefit
4. Missing waiver of premium
5. No disability coverage
6. No terminal illness benefit
7. Policy term not aligned with liabilities
8. No inflation protection"""
        elif "accidental" in policy_type.lower() or "accident" in policy_type.lower() or "pa" in policy_type.lower():
            policy_type_context = """
PERSONAL ACCIDENT ANALYSIS FRAMEWORK:
- Sum Insured: Minimum 5-10x monthly income
- Accidental Death Benefit: 100% of SI
- Permanent Total Disability (PTD): 100% of SI
- Permanent Partial Disability (PPD): As per schedule
- Temporary Total Disability: Weekly benefit
- Medical Expenses: Post-accident medical costs
- Hospital Cash: Daily allowance during hospitalization

COMMON PA GAPS TO CHECK:
1. Low sum insured (should be 10x monthly income)
2. Limited PPD coverage (only high % disabilities)
3. No temporary disability benefit
4. No medical expense cover
5. No hospital cash benefit
6. Adventure sports exclusion
7. No worldwide coverage"""
        elif "travel" in policy_type.lower():
            policy_type_context = """
TRAVEL INSURANCE ANALYSIS FRAMEWORK:
- Medical Expenses Adequacy: USA needs $100K-$250K, Europe/Schengen needs min EUR 30,000 ($50K), Asia needs $50K
- Emergency Medical Evacuation: Should cover air ambulance ($50K-$100K in USA, $25K-$50K elsewhere)
- Trip Cancellation: Should cover at least non-refundable trip costs (flights, hotels, tours)
- Trip Interruption: Return travel + unused accommodation costs
- Baggage Loss/Delay: Typical $1,500-$3,000 for loss, $300-$500 for delay
- Personal Liability: Minimum $50,000 recommended for international travel
- Flight Delay Compensation: Reasonable daily allowance after 6-12 hour delay
- Adventure Sports: Skiing, scuba, trekking - often excluded without add-on
- Schengen Compliance: Min EUR 30,000 medical, valid for entire trip, covers all Schengen states
- Pre-existing Conditions: Most policies exclude - check if declared conditions covered
- Passport Loss: Emergency passport replacement and travel costs
- Accidental Death/Disability: Coverage during travel period
- Deductible per Claim: Higher deductible means more out-of-pocket per incident
- Coverage Currency: Check if amounts are in USD, EUR, or INR

COMMON TRAVEL GAPS TO CHECK:
1. Medical cover insufficient for destination (USA needs $250K, getting only $50K)
2. No emergency evacuation cover (air ambulance can cost $50K-$100K)
3. Adventure sports excluded (skiing/scuba injury = 100% out of pocket)
4. Pre-existing conditions not covered (heart attack abroad = denied claim)
5. Non-Schengen compliant (visa rejection risk or claim denial in Europe)
6. Low trip cancellation cover (doesn't cover full non-refundable costs)
7. No flight delay compensation (stuck at airport with no support)
8. High per-claim deductible (reduces effective coverage on small claims)"""

        gap_analysis_prompt = f"""
You are an EXPERT insurance analyst with deep knowledge of Indian insurance regulations (IRDAI guidelines).
Analyze this insurance policy like a senior insurance advisor would for a high-net-worth client.

POLICY INFORMATION:
- Policy Type: {policy_type}
- Coverage Amount: Rs.{(extracted_data.get('coverageAmount') or 0):,}
- Policy Holder: {name}
- Gender: {gender}
- Age: {user_age} years
- City: India (consider metropolitan healthcare costs)

{policy_type_context}

POLICY DOCUMENT TEXT:
{extracted_text[:15000]}

YOUR TASK:
Perform a comprehensive gap analysis comparing this policy against:
1. IRDAI recommended standards
2. Industry best practices
3. Policyholder's profile (age, gender)
4. Current market offerings

Identify 4-6 SPECIFIC, ACTIONABLE coverage gaps with:
1. category: Specific coverage area (e.g., "Room Rent Sub-limit", "No Zero Depreciation", "Inadequate Sum Assured")
2. severity: "high" (will significantly impact claims), "medium" (moderate impact), "low" (minor inconvenience)
3. description: SPECIFIC issue found in THIS policy (not generic statements)
4. recommendation: PRECISE action to take (e.g., "Add Super Top-up of Rs.25L", "Add Zero Dep add-on @ Rs.2,500/year")
5. estimatedCost: Realistic annual cost in INR to fix this gap (integer only)

IMPORTANT RULES:
- Be SPECIFIC to this policy - don't give generic advice
- If the policy is strong in an area, don't list it as a gap
- Consider the policyholder's age and gender for relevance
- estimatedCost must be a realistic market rate (integer only, e.g., 3500)
- Focus on gaps that will actually impact claims

Return ONLY a valid JSON array:
[{{"category": "...", "severity": "...", "description": "...", "recommendation": "...", "estimatedCost": 3500}}]"""

        gaps = []
        try:
            # Use deepseek-chat for comprehensive gap analysis
            def _call_deepseek_gap_analysis():
                return deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a certified insurance advisor (IRDAI licensed) with 15+ years experience. Analyze policies thoroughly and provide specific, actionable recommendations based on the actual policy document. Return ONLY valid JSON array without any explanation or markdown."
                        },
                        {
                            "role": "user",
                            "content": gap_analysis_prompt
                        }
                    ],
                    temperature=0.2,  # Lower temperature for more accurate analysis
                    max_tokens=2500  # More tokens for detailed analysis
                )

            gap_response = await asyncio.to_thread(_call_deepseek_gap_analysis)

            gap_text = gap_response.choices[0].message.content.strip()
            logger.info(f"DeepSeek gap analysis response (first 200 chars): {gap_text[:200]}")

            # Remove markdown code blocks if present
            gap_text = re.sub(r'```json\s*', '', gap_text)
            gap_text = re.sub(r'```\s*$', '', gap_text)
            gap_text = gap_text.strip()

            # Try to extract JSON array from response
            json_array_match = re.search(r'\[[\s\S]*\]', gap_text)
            if json_array_match:
                gap_text = json_array_match.group(0)

            gaps = json.loads(gap_text)
            logger.info(f"Generated {len(gaps)} coverage gap recommendations")

        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error in gap analysis: {je}")
            logger.error(f"Failed to parse: {gap_text[:500] if 'gap_text' in locals() else 'N/A'}")
            gaps = []
        except Exception as e:
            logger.error(f"Error in gap analysis: {e}")
            gaps = []

        # ==================== COMPREHENSIVE POLICY INSIGHTS GENERATION ====================
        # Generate detailed key benefits, exclusions, and concerns based on policy analysis
        # Also generates verdictExplanation for PRD v2 Verdict Engine (Phase 5)

        # Build score context for verdict explanation
        _vfm_s = universal_scores.get("vfm", {}).get("score", 0) if universal_scores else 0
        _cov_s = universal_scores.get("coverageStrength", {}).get("score", 0) if universal_scores else 0
        _clm_s = universal_scores.get("claimReadiness", {}).get("score", 0) if universal_scores else 0
        _zone_summary = zone_classification.get("summary", {}) if zone_classification else {}
        _red_features = [f.get("featureName", "") for f in (zone_classification or {}).get("features", []) if f.get("zone") == "red"]
        _amber_features = [f.get("featureName", "") for f in (zone_classification or {}).get("features", []) if f.get("zone") == "amber"]

        # Extract primary insured member age from v2 extraction for accurate verdict
        _primary_member_age = user_age
        if v2_raw_extraction:
            _members_field = v2_raw_extraction.get("insuredMembers", {})
            _members_val = _members_field.get("value") if isinstance(_members_field, dict) else _members_field
            if isinstance(_members_val, list) and _members_val:
                # Find "Self"/"Member"/"Primary"/"Proposer" member or use first member
                for _m in _members_val:
                    if isinstance(_m, dict) and str(_m.get("memberRelationship", "")).lower() in ("self", "member", "primary", "proposer"):
                        _m_age = _m.get("memberAge")
                        if _m_age and isinstance(_m_age, (int, float)) and _m_age > 0:
                            _primary_member_age = int(_m_age)
                        break
                else:
                    # No "Self" found, use first member's age
                    _first = _members_val[0]
                    if isinstance(_first, dict):
                        _m_age = _first.get("memberAge")
                        if _m_age and isinstance(_m_age, (int, float)) and _m_age > 0:
                            _primary_member_age = int(_m_age)

        policy_insights_prompt = f"""
You are an expert insurance policy analyst. Analyze this {policy_type} insurance policy and extract DETAILED insights.

POLICY INFORMATION:
- Insurance Provider: {extracted_data.get('insuranceProvider', 'Unknown')}
- Policy Type: {policy_type}
- Sum Insured/IDV: Rs.{(extracted_data.get('coverageAmount') or 0):,}
- Premium: Rs.{(extracted_data.get('premium') or 0):,}
- Primary Insured Member Age: EXACTLY {_primary_member_age} years (DO NOT use any other age)

ANALYSIS SCORES:
- Value for Money: {_vfm_s}/100
- Coverage Strength: {_cov_s}/100
- Claim Readiness: {_clm_s}/100
- Red Zone Features: {', '.join(_red_features) if _red_features else 'None'}
- Amber Zone Features: {', '.join(_amber_features) if _amber_features else 'None'}

POLICY DOCUMENT (first 12000 chars):
{extracted_text[:12000]}

Analyze the policy and return a JSON object with these sections:

{{
  "keyBenefits": [
    // List 5-8 SPECIFIC benefits from THIS policy (not generic)
    // Format: "Benefit name: Specific detail from policy"
    // Examples: "Cashless at 16000+ hospitals", "No room rent capping", "100% sum insured restoration"
  ],
  "keyExclusions": [
    // List 4-6 IMPORTANT exclusions that will affect claims
    // Format: "Exclusion: Impact on policyholder"
    // Examples: "Pre-existing diseases: 4-year waiting period", "Cosmetic surgery: Not covered"
  ],
  "keyConcerns": [
    // List 3-5 concerns or limitations found in THIS policy
    // Be specific to the actual policy terms
    // Examples: "Room rent limit of 1% of SI will reduce claim payout", "Co-pay of 20% applicable"
  ],
  "policyStrengths": [
    // List 3-4 strong points of this policy
    // Examples: "No sub-limits on most treatments", "Includes AYUSH coverage", "Lifetime renewal guarantee"
  ],
  "suggestedImprovements": [
    // List 2-4 specific improvements based on policy analysis
    // Format: {{"suggestion": "What to do", "reason": "Why it's important", "priority": "high/medium/low"}}
  ],
  "verdictExplanation": "Write a 2-3 sentence plain-English summary explaining the overall quality of this policy. Reference the scores (VFM {_vfm_s}, Coverage {_cov_s}, Claim Readiness {_clm_s}), mention specific strengths and weaknesses from the policy document. Keep it conversational and helpful for a regular consumer. CRITICAL: If you mention the policyholder's age, you MUST use EXACTLY {_primary_member_age} years — do NOT guess, round, or infer a different age."
}}

IMPORTANT:
- Be SPECIFIC to this policy - extract actual terms, numbers, limits from the document
- Don't give generic benefits/exclusions - cite actual policy terms
- For concerns, identify actual limitations that will impact claims
- The verdictExplanation must reference actual policy features, not just scores
- CRITICAL: The primary insured member is EXACTLY {_primary_member_age} years old. NEVER mention any other age.
- Return ONLY valid JSON without explanation"""

        # Generate comprehensive insights
        enhanced_insights = {
            "keyBenefits": extracted_data.get("keyBenefits") or [],
            "keyExclusions": extracted_data.get("exclusions") or [],
            "keyConcerns": [],
            "policyStrengths": [],
            "suggestedImprovements": []
        }

        try:
            def _call_deepseek_insights():
                return deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a senior insurance advisor. Extract specific policy insights from the document. Return ONLY valid JSON without markdown or explanation."
                        },
                        {
                            "role": "user",
                            "content": policy_insights_prompt
                        }
                    ],
                    temperature=0.2,
                    max_tokens=2000
                )

            insights_response = await asyncio.to_thread(_call_deepseek_insights)
            insights_text = insights_response.choices[0].message.content.strip()

            # Clean JSON response
            insights_text = re.sub(r'```json\s*', '', insights_text)
            insights_text = re.sub(r'```\s*$', '', insights_text)
            insights_text = insights_text.strip()

            # Extract JSON object
            json_match = re.search(r'\{[\s\S]*\}', insights_text)
            if json_match:
                insights_text = json_match.group(0)

            parsed_insights = json.loads(insights_text)

            # Update extracted_data with enhanced insights
            if parsed_insights.get("keyBenefits"):
                extracted_data["keyBenefits"] = parsed_insights["keyBenefits"]
            if parsed_insights.get("keyExclusions"):
                extracted_data["exclusions"] = parsed_insights["keyExclusions"]

            enhanced_insights = parsed_insights

            # Inject LLM verdict explanation into the rule-based verdict (Phase 5)
            if verdict and parsed_insights.get("verdictExplanation"):
                verdict["explanation"] = parsed_insights["verdictExplanation"]
                logger.info(f"✅ Verdict explanation injected from LLM insights")

            logger.info(f"✅ Generated comprehensive policy insights with {len(enhanced_insights.get('keyBenefits', []))} benefits, {len(enhanced_insights.get('keyConcerns', []))} concerns")

        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error in policy insights: {je}")
        except Exception as e:
            logger.error(f"Error generating policy insights: {e}")

        # Store enhanced insights for use in analysis building
        extracted_data["_enhancedInsights"] = enhanced_insights

        # Store analysis in MongoDB
        analysis_id = f"ANL_{user_id_int}_{secrets.token_hex(6)}"
        analysis_result = {
            "analysisId": analysis_id,
            "extractedData": extracted_data,
            "gapAnalysis": gaps,
            "policyInsights": enhanced_insights
        }

        # ==================== RESPONSE ====================

        # Build comprehensive response matching the spec
        # Format gaps properly
        formatted_gaps = []
        high_count = 0
        medium_count = 0
        low_count = 0
        total_cost = 0

        for idx, gap in enumerate(gaps):
            severity = gap.get("severity", "medium").lower()
            estimated_cost_raw = gap.get("estimatedCost", 0)

            # Convert estimated_cost to int/float if it's a string
            try:
                if isinstance(estimated_cost_raw, str):
                    # Remove currency symbols and commas
                    clean_cost = estimated_cost_raw.replace('₹', '').replace('$', '').replace(',', '').strip()

                    # Try direct conversion first
                    try:
                        estimated_cost = float(clean_cost) if '.' in clean_cost else int(clean_cost)
                    except ValueError:
                        # Extract numeric values from text like "Approximately 1000 - 2000 annually"
                        # Find all numbers in the string
                        numbers = re.findall(r'(\d+(?:\.\d+)?)', clean_cost)
                        if numbers:
                            # If there's a range (e.g., "1000 - 2000"), take the average
                            numeric_values = [float(n) for n in numbers]
                            if len(numeric_values) >= 2:
                                # Take average of first two numbers (typically the range)
                                estimated_cost = int((numeric_values[0] + numeric_values[1]) / 2)
                            else:
                                estimated_cost = int(numeric_values[0])
                            logger.info(f"Extracted cost {estimated_cost} from text: '{estimated_cost_raw}'")
                        else:
                            estimated_cost = 0
                else:
                    estimated_cost = estimated_cost_raw
            except (ValueError, AttributeError) as e:
                logger.warning(f"Could not convert estimatedCost '{estimated_cost_raw}' to number: {e}, using 0")
                estimated_cost = 0

            gap_obj = {
                "gapId": f"gap_{str(idx + 1).zfill(3)}",
                "category": gap.get("category", "Coverage Gap"),
                "severity": severity,
                "description": gap.get("description", ""),
                "recommendation": gap.get("recommendation", ""),
                "estimatedCost": estimated_cost
            }

            formatted_gaps.append(gap_obj)

            if severity == "high":
                high_count += 1
            elif severity == "medium":
                medium_count += 1
            else:
                low_count += 1

            total_cost += estimated_cost

        # Calculate protection score based on policy type, gaps, and coverage adequacy
        # Import the new protection score calculator
        from services.protection_score_calculator import calculate_protection_score

        # Use the new calculator that considers policy type, severity, and coverage adequacy
        protection_score, protection_score_label = calculate_protection_score(
            policy_type=policy_type,
            gaps=formatted_gaps,
            extracted_data=extracted_data,
            category_specific_data=extracted_data.get("categorySpecificData", {})
        )

        logger.info(f"📊 Protection score calculated: {protection_score}% ({protection_score_label}) (based on policy-specific analysis)")

        # Build complete categorySpecificData with all fields from EAZR Production Templates V1.0 TAB 1
        category_data_from_ai = extracted_data.get("categorySpecificData") or {}

        # Determine detected policy type for organized response
        # IMPORTANT: Prioritize keyword-based detection (policy_type) over AI extraction
        # This fixes issues where DeepSeek incorrectly classifies PA policies as health
        detected_policy_type = (policy_type or extracted_data.get("policyType") or "").lower()

        # ==================== HELPER FUNCTIONS FOR INTELLIGENT FALLBACK ====================
        def extract_from_text_list(text_list, patterns):
            """Extract value from a list of text strings using pattern matching"""
            if not text_list:
                return None
            for text in text_list:
                if isinstance(text, str):
                    text_lower = text.lower()
                    for pattern, extractor in patterns:
                        if pattern.lower() in text_lower:
                            if callable(extractor):
                                return extractor(text)
                            return text
            return None

        def extract_days_value(text):
            """Extract days value from text like '30 days' or '60 Days'"""
            import re
            match = re.search(r'(\d+)\s*days?', text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} days"
            return text

        def extract_months_value(text):
            """Extract months value from text like '48 months' or '24 Months'"""
            import re
            match = re.search(r'(\d+)\s*months?', text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} months"
            return text

        def extract_rupee_value(text):
            """Extract rupee value from text"""
            import re
            match = re.search(r'(?:Rs\.?|₹)\s*([\d,]+)', text, re.IGNORECASE)
            if match:
                return f"₹{match.group(1)}"
            return text

        # Get the arrays from extracted data for fallback parsing
        critical_areas_list = extracted_data.get("criticalAreas") or []
        waiting_periods_list = extracted_data.get("waitingPeriods") or []
        exclusions_list = extracted_data.get("exclusions") or []
        key_benefits_list = extracted_data.get("keyBenefits") or []

        # Build comprehensive categorySpecificData based on EAZR Production Templates V1.0 - TAB 1
        complete_category_data = {}

        # ==================== LIFE INSURANCE (TAB 1) ====================
        if "life" in detected_policy_type or "term" in detected_policy_type or "endowment" in detected_policy_type or "ulip" in detected_policy_type:
            complete_category_data = {
                # 1.1 Policy Identification
                "policyIdentification": {
                    "policyNumber": category_data_from_ai.get("policyNumber") or extracted_data.get("policyNumber"),
                    "uin": category_data_from_ai.get("uin") or extracted_data.get("uin") or extracted_uin or "",
                    "productName": category_data_from_ai.get("productName"),
                    "policyType": category_data_from_ai.get("policyType"),
                    "insurerName": category_data_from_ai.get("insurerName") or extracted_data.get("insuranceProvider"),
                    "policyIssueDate": category_data_from_ai.get("policyIssueDate") or extracted_data.get("startDate"),
                    "policyStatus": category_data_from_ai.get("policyStatus") or "Active"
                },
                # 1.2 Policyholder & Life Assured
                "policyholderLifeAssured": {
                    "policyholderName": category_data_from_ai.get("policyholderName") or extracted_data.get("policyHolderName"),
                    "policyholderDob": category_data_from_ai.get("policyholderDob"),
                    "policyholderAge": category_data_from_ai.get("policyholderAge"),
                    "policyholderGender": category_data_from_ai.get("policyholderGender"),
                    "lifeAssuredName": category_data_from_ai.get("lifeAssuredName"),
                    "lifeAssuredDob": category_data_from_ai.get("lifeAssuredDob"),
                    "lifeAssuredAge": category_data_from_ai.get("lifeAssuredAge"),
                    "relationshipWithPolicyholder": category_data_from_ai.get("relationshipWithPolicyholder")
                },
                # 1.3 Coverage Details
                "coverageDetails": {
                    "sumAssured": category_data_from_ai.get("sumAssured") or extracted_data.get("coverageAmount"),
                    "coverType": category_data_from_ai.get("coverType"),
                    "policyTerm": category_data_from_ai.get("policyTerm"),
                    "premiumPayingTerm": category_data_from_ai.get("premiumPayingTerm"),
                    "maturityDate": category_data_from_ai.get("maturityDate") or extracted_data.get("endDate"),
                    "deathBenefit": category_data_from_ai.get("deathBenefit")
                },
                # 1.4 Premium Details
                "premiumDetails": {
                    "premiumAmount": category_data_from_ai.get("premiumAmount") or extracted_data.get("premium"),
                    "premiumFrequency": category_data_from_ai.get("premiumFrequency") or extracted_data.get("premiumFrequency"),
                    "premiumDueDate": category_data_from_ai.get("premiumDueDate"),
                    "gracePeriod": category_data_from_ai.get("gracePeriod"),
                    "modalPremiumBreakdown": category_data_from_ai.get("modalPremiumBreakdown")
                },
                # 1.5 Riders
                "riders": category_data_from_ai.get("riders") or [],
                # 1.6 Bonus & Value
                "bonusValue": {
                    "bonusType": category_data_from_ai.get("bonusType"),
                    "declaredBonusRate": category_data_from_ai.get("declaredBonusRate"),
                    "accruedBonus": category_data_from_ai.get("accruedBonus"),
                    "surrenderValue": category_data_from_ai.get("surrenderValue"),
                    "paidUpValue": category_data_from_ai.get("paidUpValue"),
                    "loanValue": category_data_from_ai.get("loanValue")
                },
                # 1.7 ULIP Details (if applicable)
                "ulipDetails": {
                    "fundOptions": category_data_from_ai.get("fundOptions"),
                    "currentNav": category_data_from_ai.get("currentNav"),
                    "unitsHeld": category_data_from_ai.get("unitsHeld"),
                    "fundValue": category_data_from_ai.get("fundValue"),
                    "switchOptions": category_data_from_ai.get("switchOptions"),
                    "partialWithdrawal": category_data_from_ai.get("partialWithdrawal")
                },
                # 1.8 Nomination
                "nomination": {
                    "nominees": category_data_from_ai.get("nominees") or [],
                    "appointeeName": category_data_from_ai.get("appointeeName"),
                    "appointeeRelationship": category_data_from_ai.get("appointeeRelationship")
                },
                # 1.9 Key Terms
                "keyTerms": {
                    "revivalPeriod": category_data_from_ai.get("revivalPeriod"),
                    "freelookPeriod": category_data_from_ai.get("freelookPeriod"),
                    "policyLoanInterestRate": category_data_from_ai.get("policyLoanInterestRate"),
                    "autoPayMode": category_data_from_ai.get("autoPayMode")
                },
                # 1.10 Exclusions
                "exclusions": {
                    "suicideClause": category_data_from_ai.get("suicideClause"),
                    "otherExclusions": category_data_from_ai.get("otherExclusions") or extracted_data.get("exclusions") or []
                }
            }

        # ==================== HEALTH INSURANCE (TAB 1) ====================
        elif "health" in detected_policy_type or "mediclaim" in detected_policy_type or "medical" in detected_policy_type:
            # -------- Intelligent Fallback for Health Insurance --------
            # Parse waiting periods from waitingPeriods array if not in categorySpecificData
            def find_waiting_period(pattern_keywords, text_list):
                """Find waiting period value from text list using keywords"""
                if not text_list:
                    return None
                for text in text_list:
                    if isinstance(text, str):
                        text_lower = text.lower()
                        for keyword in pattern_keywords:
                            if keyword.lower() in text_lower:
                                # Extract the period value
                                import re
                                # Look for patterns like "30 days", "48 months", "2 years"
                                match = re.search(r'(\d+)\s*(days?|months?|years?)', text, re.IGNORECASE)
                                if match:
                                    return f"{match.group(1)} {match.group(2)}"
                                return text
                return None

            # Parse room rent from critical areas
            def find_room_rent(critical_list, key_benefits):
                """Extract room rent info from critical areas or benefits"""
                all_texts = (critical_list or []) + (key_benefits or [])
                for text in all_texts:
                    if isinstance(text, str):
                        text_lower = text.lower()
                        if "room" in text_lower or "rent" in text_lower:
                            import re
                            # Look for Rs/₹ amount
                            match = re.search(r'(?:Rs\.?|₹)\s*([\d,]+)', text)
                            if match:
                                return f"₹{match.group(1)}/day"
                            # Look for room type descriptions
                            if "single" in text_lower:
                                return "Single Private Room"
                            if "shared" in text_lower:
                                return "Shared Room"
                            if "no limit" in text_lower or "no sub-limit" in text_lower:
                                return "No Limit"
                            return text
                return None

            # Parse pre/post hospitalization from key benefits
            def find_hospitalization_days(key_benefits, pattern):
                """Extract pre/post hospitalization days"""
                if not key_benefits:
                    return None
                for text in key_benefits:
                    if isinstance(text, str) and pattern.lower() in text.lower():
                        import re
                        match = re.search(r'(\d+)\s*days?', text, re.IGNORECASE)
                        if match:
                            return f"{match.group(1)} days"
                return None

            # Check key benefits for coverage features
            def has_benefit(key_benefits, keywords):
                """Check if a benefit exists in key benefits list"""
                if not key_benefits:
                    return None
                for text in key_benefits:
                    if isinstance(text, str):
                        text_lower = text.lower()
                        for keyword in keywords:
                            if keyword.lower() in text_lower:
                                return True
                return None

            complete_category_data = {
                # 1.1 Policy Identification
                "policyIdentification": {
                    "policyNumber": category_data_from_ai.get("policyNumber") or extracted_data.get("policyNumber"),
                    "uin": category_data_from_ai.get("uin") or extracted_data.get("uin") or extracted_uin or "",
                    "productName": category_data_from_ai.get("productName") or extracted_data.get("productName"),
                    "policyType": category_data_from_ai.get("policyType"),
                    "insurerName": category_data_from_ai.get("insurerName") or extracted_data.get("insuranceProvider"),
                    "insurerRegistrationNumber": category_data_from_ai.get("insurerRegistrationNumber"),
                    "insurerAddress": category_data_from_ai.get("insurerAddress"),
                    "insurerTollFree": category_data_from_ai.get("insurerTollFree"),
                    "tpaName": category_data_from_ai.get("tpaName"),
                    "intermediaryName": category_data_from_ai.get("intermediaryName"),
                    "intermediaryCode": category_data_from_ai.get("intermediaryCode"),
                    "intermediaryEmail": category_data_from_ai.get("intermediaryEmail"),
                    "policyIssueDate": category_data_from_ai.get("policyIssueDate") or extracted_data.get("startDate"),
                    "policyPeriod": category_data_from_ai.get("policyPeriod") or f"{extracted_data.get('startDate', '')} to {extracted_data.get('endDate', '')}",
                    "policyPeriodStart": category_data_from_ai.get("policyPeriodStart") or extracted_data.get("startDate"),
                    "policyPeriodEnd": category_data_from_ai.get("policyPeriodEnd") or extracted_data.get("endDate")
                },
                # 1.2 Insured Members
                "insuredMembers": category_data_from_ai.get("insuredMembers") or [{
                    "name": extracted_data.get("policyHolderName", ""),
                    "gender": extracted_data.get("gender", ""),
                    "dateOfBirth": category_data_from_ai.get("dateOfBirth"),
                    "age": category_data_from_ai.get("age"),
                    "relationship": "Self"
                }],
                # 1.3 Coverage Details - with intelligent fallback
                "coverageDetails": {
                    "sumInsured": category_data_from_ai.get("sumInsured") or extracted_data.get("coverageAmount"),
                    "coverType": category_data_from_ai.get("coverType"),
                    "roomRentLimit": category_data_from_ai.get("roomRentLimit") or find_room_rent(critical_areas_list, key_benefits_list),
                    "roomRentCopay": category_data_from_ai.get("roomRentCopay"),
                    "icuLimit": category_data_from_ai.get("icuLimit"),
                    "icuDailyLimit": category_data_from_ai.get("icuDailyLimit"),
                    "preHospitalization": category_data_from_ai.get("preHospitalization") or find_hospitalization_days(key_benefits_list, "pre-hospitalization"),
                    "postHospitalization": category_data_from_ai.get("postHospitalization") or find_hospitalization_days(key_benefits_list, "post-hospitalization"),
                    "dayCareProcedures": category_data_from_ai.get("dayCareProcedures") or has_benefit(key_benefits_list, ["day care", "daycare"]),
                    "domiciliaryHospitalization": category_data_from_ai.get("domiciliaryHospitalization") or has_benefit(key_benefits_list, ["domiciliary"]),
                    "ambulanceCover": category_data_from_ai.get("ambulanceCover") or has_benefit(key_benefits_list, ["ambulance"]),
                    "healthCheckup": category_data_from_ai.get("healthCheckup") or has_benefit(key_benefits_list, ["health check", "healthcheck"]),
                    "ayushTreatment": category_data_from_ai.get("ayushTreatment") or has_benefit(key_benefits_list, ["ayush", "alternative treatment"]),
                    "organDonor": category_data_from_ai.get("organDonor") or has_benefit(key_benefits_list, ["organ donor"]),
                    "restoration": category_data_from_ai.get("restoration") or has_benefit(key_benefits_list, ["restoration"]),
                    "restorationAmount": category_data_from_ai.get("restorationAmount"),
                    "modernTreatment": category_data_from_ai.get("modernTreatment") or has_benefit(key_benefits_list, ["modern treatment", "robotic", "stereotactic"]),
                    "dailyCashAllowance": category_data_from_ai.get("dailyCashAllowance") or has_benefit(key_benefits_list, ["daily cash", "hospital cash"]),
                    "convalescenceBenefit": category_data_from_ai.get("convalescenceBenefit") or has_benefit(key_benefits_list, ["recovery", "convalescence"]),
                    "consumablesCoverage": category_data_from_ai.get("consumablesCoverage") or has_benefit(key_benefits_list, ["consumable", "non-payable", "non payable", "waiver of non"]),
                    "consumablesCoverageDetails": category_data_from_ai.get("consumablesCoverageDetails")
                },
                # 1.4 Waiting Periods - with intelligent fallback from waitingPeriods array
                "waitingPeriods": {
                    "initialWaitingPeriod": category_data_from_ai.get("initialWaitingPeriod") or find_waiting_period(["initial waiting", "initial waiting period"], waiting_periods_list),
                    "preExistingDiseaseWaiting": category_data_from_ai.get("preExistingDiseaseWaiting") or find_waiting_period(["pre-existing", "ped", "pre existing"], waiting_periods_list),
                    "specificDiseaseWaiting": category_data_from_ai.get("specificDiseaseWaiting") or find_waiting_period(["specific", "specified"], waiting_periods_list),
                    "maternityWaiting": category_data_from_ai.get("maternityWaiting") or find_waiting_period(["maternity", "pregnancy"], waiting_periods_list),
                    "accidentCoveredFromDay1": category_data_from_ai.get("accidentCoveredFromDay1"),
                    "specificDiseasesList": category_data_from_ai.get("specificDiseasesList") or []
                },
                # 1.4b Co-pay Details
                "copayDetails": {
                    "generalCopay": category_data_from_ai.get("generalCopay"),
                    "ageBasedCopay": category_data_from_ai.get("ageBasedCopay") or [],
                    "diseaseSpecificCopay": category_data_from_ai.get("diseaseSpecificCopay") or []
                },
                # 1.5 Sub-Limits - with fallback from critical areas
                "subLimits": {
                    "cataractLimit": category_data_from_ai.get("cataractLimit"),
                    "jointReplacementLimit": category_data_from_ai.get("jointReplacementLimit"),
                    "internalProsthesisLimit": category_data_from_ai.get("internalProsthesisLimit"),
                    "kidneyStoneLimit": category_data_from_ai.get("kidneyStoneLimit"),
                    "gallStoneLimit": category_data_from_ai.get("gallStoneLimit"),
                    "modernTreatmentLimit": category_data_from_ai.get("modernTreatmentLimit"),
                    "otherSubLimits": category_data_from_ai.get("otherSubLimits") or []
                },
                # 1.6 Exclusions
                "exclusions": {
                    "permanentExclusions": category_data_from_ai.get("permanentExclusions") or [],
                    "conditionalExclusions": category_data_from_ai.get("conditionalExclusions") or [],
                    "preExistingConditions": category_data_from_ai.get("preExistingConditions") or [],
                    "pedSpecificExclusions": category_data_from_ai.get("pedSpecificExclusions") or []
                },
                # 1.7 Premium Breakdown - Detailed structure matching Eazr Health policy
                "premiumBreakdown": {
                    "basePremium": category_data_from_ai.get("basePremium") or category_data_from_ai.get("basicPremium"),
                    "gst": category_data_from_ai.get("gst") or category_data_from_ai.get("taxAmount"),
                    "totalPremium": category_data_from_ai.get("totalPremium") or extracted_data.get("premium"),
                    "premiumFrequency": category_data_from_ai.get("premiumFrequency") or extracted_data.get("premiumFrequency"),
                    "existingCustomerDiscount": category_data_from_ai.get("existingCustomerDiscount") or 0,
                    "addOnPremiums": {
                        "careShield": category_data_from_ai.get("careShieldPremium") or category_data_from_ai.get("addOnCareShield"),
                        "internationalCoverage": category_data_from_ai.get("internationalCoveragePremium") or category_data_from_ai.get("addOnInternational"),
                        "universalShield": category_data_from_ai.get("universalShieldPremium") or category_data_from_ai.get("addOnUniversalShield"),
                        "covidCare": category_data_from_ai.get("covidCarePremium") or category_data_from_ai.get("addOnCovidCare"),
                        "otherAddOns": category_data_from_ai.get("otherAddOnPremiums") or {}
                    },
                    "premiumBreakdownDetails": category_data_from_ai.get("premiumBreakdownDetails") or [],
                    "gracePeriod": category_data_from_ai.get("healthGracePeriod")
                },
                # 1.8 No Claim Bonus (NCB)
                "noClaimBonus": {
                    "available": bool(category_data_from_ai.get("ncbPercentage") or has_benefit(key_benefits_list, ["no claim bonus", "ncb", "cumulative bonus"])),
                    "currentNcbPercentage": category_data_from_ai.get("ncbPercentage") or category_data_from_ai.get("currentNcb"),
                    "accumulatedNcbPercentage": category_data_from_ai.get("accumulatedNcbPercentage") or category_data_from_ai.get("ncbAccumulated"),
                    "maxNcbPercentage": category_data_from_ai.get("maxNcbPercentage") or category_data_from_ai.get("ncbMaxPercentage"),
                    "ncbAmount": category_data_from_ai.get("ncbAmount") or category_data_from_ai.get("accumulatedNcbAmount"),
                    "ncbProtect": category_data_from_ai.get("ncbProtect") or has_benefit(key_benefits_list, ["ncb protect", "ncb shield"]),
                    "ncbBoost": category_data_from_ai.get("ncbBoost") or has_benefit(key_benefits_list, ["ncb boost", "ncb super"])
                },
                # 1.9 Add-on Policies (Care Shield, International Coverage, etc.)
                "addOnPolicies": {
                    "hasAddOn": bool(category_data_from_ai.get("addOnPolicyName") or category_data_from_ai.get("addOnPoliciesList") or has_benefit(key_benefits_list, ["care shield", "shield", "add-on", "addon", "international coverage", "universal shield"])),
                    "addOnPoliciesList": category_data_from_ai.get("addOnPoliciesList") or [],
                    "claimShield": bool(category_data_from_ai.get("claimShield") or has_benefit(key_benefits_list, ["claim shield"])),
                    "ncbShield": bool(category_data_from_ai.get("ncbShield") or has_benefit(key_benefits_list, ["ncb shield", "ncb protect"])),
                    "inflationShield": bool(category_data_from_ai.get("inflationShield") or has_benefit(key_benefits_list, ["inflation shield"]))
                },
                # 1.10 Declared PED
                "declaredPed": {
                    "declaredConditions": category_data_from_ai.get("declaredConditions") or [],
                    "pedWaitingPeriodCompleted": _compute_ped_completed(category_data_from_ai),
                    "pedStatus": category_data_from_ai.get("pedStatus") or "None Declared"
                },
                # 1.11 Benefits (structured for report generator)
                "benefits": {
                    "restoration": {
                        "available": bool(category_data_from_ai.get("restoration") or has_benefit(key_benefits_list, ["restoration", "automatic recharge", "recharge"])),
                        "type": category_data_from_ai.get("restorationAmount")
                    },
                    "noClaimBonus": {
                        "available": bool(category_data_from_ai.get("ncbPercentage") or has_benefit(key_benefits_list, ["no claim bonus", "ncb", "cumulative bonus"])),
                        "percentage": category_data_from_ai.get("ncbPercentage"),
                        "accumulatedAmount": category_data_from_ai.get("accumulatedNcbAmount"),
                        "maxPercentage": category_data_from_ai.get("ncbMaxPercentage")
                    },
                    "ayushCovered": bool(category_data_from_ai.get("ayushTreatment") or has_benefit(key_benefits_list, ["ayush", "alternative treatment", "ayurveda", "homeopathy"])),
                    "ayushLimit": category_data_from_ai.get("ayushTreatment") if isinstance(category_data_from_ai.get("ayushTreatment"), str) else None,
                    "mentalHealthCovered": bool(category_data_from_ai.get("mentalHealthCovered") or category_data_from_ai.get("mentalHealthCover") or has_benefit(key_benefits_list, ["mental health", "psychiatric"])),
                    "dayCareCovered": bool(category_data_from_ai.get("dayCareProcedures") or has_benefit(key_benefits_list, ["day care", "daycare"])),
                    "dayCareCoverageType": category_data_from_ai.get("dayCareProcedures") if isinstance(category_data_from_ai.get("dayCareProcedures"), str) else None
                },
                # 1.12 Accumulated Benefits (for renewal policies)
                "accumulatedBenefits": {
                    "accumulatedNcbAmount": category_data_from_ai.get("accumulatedNcbAmount") or category_data_from_ai.get("cumulativeBonusAmount"),
                    "accumulatedInflationShield": category_data_from_ai.get("accumulatedInflationShield") or category_data_from_ai.get("inflationShieldAmount"),
                    "totalEffectiveCoverage": category_data_from_ai.get("totalEffectiveCoverage") or category_data_from_ai.get("effectiveSumInsured")
                },
                # 1.13 Members Covered (for floater policies)
                "membersCovered": category_data_from_ai.get("insuredMembers") or category_data_from_ai.get("membersCovered") or [],
                # 1.14 Policy History (for continuous coverage) - CRITICAL for waiting period status
                "policyHistory": {
                    "firstEnrollmentDate": category_data_from_ai.get("firstEnrollmentDate") or category_data_from_ai.get("insuredSinceDate") or category_data_from_ai.get("policyInceptionDate"),
                    "insuredSinceDate": category_data_from_ai.get("insuredSinceDate") or category_data_from_ai.get("firstEnrollmentDate"),
                    "continuousCoverageYears": category_data_from_ai.get("continuousCoverageYears"),
                    "previousPolicyNumbers": category_data_from_ai.get("previousPolicyNumbers") or [],
                    "portability": category_data_from_ai.get("portability") or {
                        "available": True,
                        "waitingPeriodCredit": category_data_from_ai.get("waitingPeriodCredit") or "Available for porting"
                    }
                },
                # 1.15 Network Information
                "networkInfo": {
                    "networkHospitalsCount": category_data_from_ai.get("networkHospitalsCount"),
                    "ambulanceCover": category_data_from_ai.get("ambulanceCoverLimit") or category_data_from_ai.get("ambulanceCover"),
                    "cashlessFacility": category_data_from_ai.get("cashlessFacility"),
                    "networkType": category_data_from_ai.get("networkType"),
                    "preAuthTurnaround": category_data_from_ai.get("preAuthTurnaround")
                },
                # 1.16 Claim Information
                "claimInfo": {
                    "claimSettlementRatio": category_data_from_ai.get("claimSettlementRatio"),
                    "claimProcess": category_data_from_ai.get("claimProcess"),
                    "claimIntimation": category_data_from_ai.get("claimIntimation"),
                    "claimDocuments": category_data_from_ai.get("claimDocuments") or []
                }
            }

        # ==================== MOTOR INSURANCE (TAB 1) - EAZR_03 Spec ====================
        elif "motor" in detected_policy_type or "car" in detected_policy_type or "vehicle" in detected_policy_type or "auto" in detected_policy_type or "two wheeler" in detected_policy_type or "bike" in detected_policy_type:
            complete_category_data = {
                # 1.1 Policy Identification (EAZR_03 S3.1)
                "policyIdentification": {
                    "policyNumber": category_data_from_ai.get("policyNumber") or extracted_data.get("policyNumber"),
                    "uin": category_data_from_ai.get("uin") or extracted_data.get("uin") or extracted_uin or "",
                    "certificateNumber": category_data_from_ai.get("certificateNumber"),
                    "coverNoteNumber": category_data_from_ai.get("coverNoteNumber"),
                    "productType": category_data_from_ai.get("productType"),
                    "insurerName": category_data_from_ai.get("insurerName") or extracted_data.get("insuranceProvider"),
                    "policyPeriod": category_data_from_ai.get("policyPeriod"),
                    "policyPeriodStart": category_data_from_ai.get("policyPeriodStart") or extracted_data.get("startDate"),
                    "policyPeriodEnd": category_data_from_ai.get("policyPeriodEnd") or extracted_data.get("endDate"),
                    "policyTerm": category_data_from_ai.get("policyTerm"),
                    "previousPolicyNumber": category_data_from_ai.get("previousPolicyNumber"),
                    "previousInsurer": category_data_from_ai.get("previousInsurer"),
                    "insurerTollFree": category_data_from_ai.get("insurerTollFree"),
                    "claimEmail": category_data_from_ai.get("claimEmail"),
                    "claimApp": category_data_from_ai.get("claimApp"),
                },
                # 1.2 Vehicle Details (EAZR_03 S3.2)
                "vehicleDetails": {
                    "registrationNumber": category_data_from_ai.get("registrationNumber"),
                    "vehicleClass": category_data_from_ai.get("vehicleClass"),
                    "vehicleCategory": category_data_from_ai.get("vehicleCategory"),
                    "vehicleMake": category_data_from_ai.get("vehicleMake"),
                    "vehicleModel": category_data_from_ai.get("vehicleModel"),
                    "vehicleVariant": category_data_from_ai.get("vehicleVariant"),
                    "manufacturingYear": category_data_from_ai.get("manufacturingYear"),
                    "registrationDate": category_data_from_ai.get("registrationDate"),
                    "engineNumber": category_data_from_ai.get("engineNumber"),
                    "chassisNumber": category_data_from_ai.get("chassisNumber"),
                    "fuelType": category_data_from_ai.get("fuelType"),
                    "cubicCapacity": category_data_from_ai.get("cubicCapacity"),
                    "seatingCapacity": category_data_from_ai.get("seatingCapacity"),
                    "vehicleColor": category_data_from_ai.get("vehicleColor"),
                    "rtoLocation": category_data_from_ai.get("rtoLocation"),
                    "hypothecation": category_data_from_ai.get("hypothecation"),
                },
                # 1.3 Owner Details (EAZR_03 S3.8)
                "ownerDetails": {
                    "ownerName": category_data_from_ai.get("ownerName") or extracted_data.get("policyHolderName"),
                    "ownerType": category_data_from_ai.get("ownerType"),
                    "ownerAddress": category_data_from_ai.get("ownerAddress"),
                    "ownerAddressCity": category_data_from_ai.get("ownerAddressCity"),
                    "ownerAddressState": category_data_from_ai.get("ownerAddressState"),
                    "ownerAddressPincode": category_data_from_ai.get("ownerAddressPincode"),
                    "ownerContact": category_data_from_ai.get("ownerContact"),
                    "ownerEmail": category_data_from_ai.get("ownerEmail"),
                    "panNumber": category_data_from_ai.get("ownerPan"),
                },
                # 1.4 Coverage Details (EAZR_03 S3.3)
                "coverageDetails": {
                    "idv": category_data_from_ai.get("idv") or extracted_data.get("coverageAmount"),
                    "idvMinimum": category_data_from_ai.get("idvMinimum"),
                    "idvMaximum": category_data_from_ai.get("idvMaximum"),
                    "odPremium": category_data_from_ai.get("odPremium"),
                    "tpPremium": category_data_from_ai.get("tpPremium"),
                    "compulsoryDeductible": category_data_from_ai.get("compulsoryDeductible"),
                    "voluntaryDeductible": category_data_from_ai.get("voluntaryDeductible"),
                    "geographicScope": category_data_from_ai.get("geographicScope"),
                    "paOwnerCover": category_data_from_ai.get("paOwnerCover"),
                    "paUnnamedPassengers": category_data_from_ai.get("paUnnamedPassengers"),
                    "paUnnamedPassengersPerPerson": category_data_from_ai.get("paUnnamedPassengersPerPerson"),
                    "paPaidDriver": category_data_from_ai.get("paPaidDriver"),
                    "llPaidDriver": category_data_from_ai.get("llPaidDriver"),
                    "llEmployees": category_data_from_ai.get("llEmployees"),
                    "tppdCover": category_data_from_ai.get("tppdCover"),
                },
                # 1.5 NCB (EAZR_03 S3.5)
                "ncb": {
                    "ncbPercentage": category_data_from_ai.get("ncbPercentage"),
                    "ncbProtection": category_data_from_ai.get("ncbProtection"),
                    "ncbDeclaration": category_data_from_ai.get("ncbDeclaration"),
                    "claimFreeYears": category_data_from_ai.get("claimFreeYears"),
                },
                # 1.6 Add-On Covers (EAZR_03 S3.4 - expanded for all India motor add-ons)
                "addOnCovers": {
                    "zeroDepreciation": category_data_from_ai.get("zeroDepreciation"),
                    "engineProtection": category_data_from_ai.get("engineProtection"),
                    "returnToInvoice": category_data_from_ai.get("returnToInvoice"),
                    "roadsideAssistance": category_data_from_ai.get("roadsideAssistance"),
                    "consumables": category_data_from_ai.get("consumables"),
                    "tyreCover": category_data_from_ai.get("tyreCover"),
                    "keyCover": category_data_from_ai.get("keyCover"),
                    "ncbProtect": category_data_from_ai.get("ncbProtect"),
                    "emiBreakerCover": category_data_from_ai.get("emiBreakerCover"),
                    "passengerCover": category_data_from_ai.get("passengerCover"),
                    "passengerCoverAmount": category_data_from_ai.get("passengerCoverAmount"),
                    # BUG #8 FIX: "personalBaggage" and "personalEffects" map to the same coverage
                    "personalBaggage": category_data_from_ai.get("personalBaggage") or category_data_from_ai.get("personalEffects") or category_data_from_ai.get("lossOfPersonalEffects"),
                    "outstationEmergency": category_data_from_ai.get("outstationEmergency"),
                    "dailyAllowance": category_data_from_ai.get("dailyAllowance"),
                    "windshieldCover": category_data_from_ai.get("windshieldCover"),
                    "electricVehicleCover": category_data_from_ai.get("electricVehicleCover"),
                    "batteryProtect": category_data_from_ai.get("batteryProtect"),
                    # BUG #8 FIX: Additional IRDAI-recognized add-ons
                    "legalLiabilityPaidDriver": category_data_from_ai.get("legalLiabilityPaidDriver") or category_data_from_ai.get("llPaidDriver"),
                    "legalLiabilityEmployees": category_data_from_ai.get("legalLiabilityEmployees") or category_data_from_ai.get("llEmployees"),
                    "paNamedPersons": category_data_from_ai.get("paNamedPersons"),
                },
                # 1.7 Premium Breakdown (EAZR_03 S3.6 - detailed)
                "premiumBreakdown": {
                    "basicOdPremium": category_data_from_ai.get("basicOdPremium"),
                    "ncbDiscount": category_data_from_ai.get("ncbDiscount"),
                    "voluntaryDeductibleDiscount": category_data_from_ai.get("voluntaryDeductibleDiscount"),
                    "antiTheftDiscount": category_data_from_ai.get("antiTheftDiscount"),
                    "aaiMembershipDiscount": category_data_from_ai.get("aaiMembershipDiscount"),
                    "electricalAccessoriesPremium": category_data_from_ai.get("electricalAccessoriesPremium"),
                    "nonElectricalAccessoriesPremium": category_data_from_ai.get("nonElectricalAccessoriesPremium"),
                    "cngLpgKitPremium": category_data_from_ai.get("cngLpgKitPremium"),
                    "addOnPremium": category_data_from_ai.get("addOnPremium"),
                    "loading": category_data_from_ai.get("loading"),
                    "netOdPremium": category_data_from_ai.get("netOdPremium"),
                    "odPremium": category_data_from_ai.get("odPremium"),
                    "basicTpPremium": category_data_from_ai.get("basicTpPremium"),
                    "tpPremium": category_data_from_ai.get("tpPremium"),
                    "paOwnerDriverPremium": category_data_from_ai.get("paOwnerDriverPremium"),
                    "paPassengersPremium": category_data_from_ai.get("paPassengersPremium"),
                    "paPaidDriverPremium": category_data_from_ai.get("paPaidDriverPremium"),
                    "llPaidDriverPremium": category_data_from_ai.get("llPaidDriverPremium"),
                    "netTpPremium": category_data_from_ai.get("netTpPremium"),
                    "grossPremium": category_data_from_ai.get("grossPremium"),
                    "gst": category_data_from_ai.get("gst"),
                    "totalPremium": category_data_from_ai.get("totalPremium") or extracted_data.get("premium"),
                },
                # 1.8 Exclusions
                "exclusions": {
                    "electricalAccessoriesExclusion": category_data_from_ai.get("electricalAccessoriesExclusion"),
                    "nonElectricalAccessoriesExclusion": category_data_from_ai.get("nonElectricalAccessoriesExclusion"),
                    "biofuelKitExclusion": category_data_from_ai.get("biofuelKitExclusion"),
                    "otherExclusions": category_data_from_ai.get("otherExclusions") or extracted_data.get("exclusions") or []
                }
            }

            # POST-PROCESSING: Fix tpPremium vs paOwnerDriverPremium for Standalone OD policies
            # AI sometimes misclassifies CPA/PA premium as tpPremium for Standalone OD.
            # Standalone OD has NO TP liability — any small premium (~₹399-750) is CPA, not TP.
            _ptype = str(complete_category_data.get("policyIdentification", {}).get("productType", "") or "").lower()
            if "standalone" in _ptype or "stand alone" in _ptype or "saod" in _ptype:
                _cd = complete_category_data.get("coverageDetails", {})
                _pb = complete_category_data.get("premiumBreakdown", {})
                _tp_val = _cd.get("tpPremium")
                _pa_val = _pb.get("paOwnerDriverPremium")
                # If tpPremium is set but paOwnerDriverPremium is not, it's likely misclassified CPA
                try:
                    _tp_num = float(_tp_val) if _tp_val else 0
                except (ValueError, TypeError):
                    _tp_num = 0
                try:
                    _pa_num = float(_pa_val) if _pa_val else 0
                except (ValueError, TypeError):
                    _pa_num = 0
                if _tp_num > 0 and _pa_num == 0:
                    # Move misclassified TP to PA
                    _pb["paOwnerDriverPremium"] = _tp_val
                    _cd["tpPremium"] = 0
                    _pb["tpPremium"] = 0
                    _pb["basicTpPremium"] = 0
                    _pb["netTpPremium"] = 0
                    logger.info(f"Standalone OD fix: moved tpPremium ({_tp_val}) to paOwnerDriverPremium")
                elif _tp_num > 0 and _pa_num > 0 and _tp_num == _pa_num:
                    # Both set to same value — TP is duplicate of PA, zero it out
                    _cd["tpPremium"] = 0
                    _pb["tpPremium"] = 0
                    _pb["basicTpPremium"] = 0
                    _pb["netTpPremium"] = 0
                    logger.info(f"Standalone OD fix: zeroed duplicate tpPremium ({_tp_val}) — PA already set")

        # ==================== TRAVEL INSURANCE (TAB 1) - EAZR_05 Full Spec ====================
        elif "travel" in detected_policy_type:
            complete_category_data = {
                # 1.1 Policy Identification
                "policyIdentification": {
                    "policyNumber": category_data_from_ai.get("policyNumber") or extracted_data.get("policyNumber"),
                    "uin": category_data_from_ai.get("uin") or extracted_data.get("uin") or extracted_uin or "",
                    "productName": category_data_from_ai.get("productName"),
                    "tripType": category_data_from_ai.get("tripType"),
                    "travelType": category_data_from_ai.get("travelType"),
                    "insurerName": category_data_from_ai.get("insurerName") or extracted_data.get("insuranceProvider"),
                    "policyIssueDate": category_data_from_ai.get("policyIssueDate") or extracted_data.get("startDate")
                },
                # 1.2 Trip Details (enhanced with geographic coverage & status)
                "tripDetails": {
                    "tripStartDate": category_data_from_ai.get("tripStartDate") or extracted_data.get("startDate"),
                    "tripEndDate": category_data_from_ai.get("tripEndDate") or extracted_data.get("endDate"),
                    "tripDuration": category_data_from_ai.get("tripDuration"),
                    "destinationCountries": category_data_from_ai.get("destinationCountries") or [],
                    "originCountry": category_data_from_ai.get("originCountry"),
                    "purposeOfTravel": category_data_from_ai.get("purposeOfTravel"),
                    "geographicCoverage": category_data_from_ai.get("geographicCoverage"),
                    "policyStatus": category_data_from_ai.get("policyStatus")
                },
                # 1.3 Traveller Details (enhanced with DOB & PED)
                "travellerDetails": [
                    {**t, "dateOfBirth": t.get("dateOfBirth"), "preExistingConditionsDeclared": t.get("preExistingConditionsDeclared") or []}
                    for t in (category_data_from_ai.get("travellers") or [])
                ] if category_data_from_ai.get("travellers") else [],
                # 1.4 Coverage Summary (original 14 fields)
                "coverageSummary": {
                    "medicalExpenses": category_data_from_ai.get("medicalExpenses"),
                    "emergencyMedicalEvacuation": category_data_from_ai.get("emergencyMedicalEvacuation"),
                    "repatriationOfRemains": category_data_from_ai.get("repatriationOfRemains"),
                    "tripCancellation": category_data_from_ai.get("tripCancellation"),
                    "tripInterruption": category_data_from_ai.get("tripInterruption"),
                    "flightDelay": category_data_from_ai.get("flightDelay"),
                    "baggageLoss": category_data_from_ai.get("baggageLoss"),
                    "baggageDelay": category_data_from_ai.get("baggageDelay"),
                    "passportLoss": category_data_from_ai.get("passportLoss"),
                    "personalLiability": category_data_from_ai.get("personalLiability"),
                    "accidentalDeath": category_data_from_ai.get("accidentalDeath"),
                    "permanentDisability": category_data_from_ai.get("permanentDisability"),
                    "hijackDistress": category_data_from_ai.get("hijackDistress"),
                    "homeburglary": category_data_from_ai.get("homeburglary"),
                    "coverageCurrency": category_data_from_ai.get("coverageCurrency"),
                    "deductiblePerClaim": category_data_from_ai.get("deductiblePerClaim"),
                    "coverageIncludes": category_data_from_ai.get("coverageIncludes") or []
                },
                # 1.5 Medical Coverage Details (EAZR_05 §3.2)
                "medicalCoverage": {
                    "medicalDeductible": category_data_from_ai.get("medicalDeductible"),
                    "covidCoverage": {
                        "treatmentCovered": category_data_from_ai.get("covidTreatmentCovered"),
                        "quarantineCovered": category_data_from_ai.get("covidQuarantineCovered"),
                        "quarantineLimit": category_data_from_ai.get("covidQuarantineLimit")
                    },
                    "cashlessNetwork": {
                        "available": category_data_from_ai.get("cashlessNetworkAvailable"),
                        "networkName": category_data_from_ai.get("cashlessNetworkName"),
                        "hospitalsCount": category_data_from_ai.get("cashlessHospitalsCount"),
                        "assistanceHelpline": category_data_from_ai.get("assistanceHelplineForCashless")
                    },
                    "preExistingConditions": {
                        "covered": category_data_from_ai.get("preExistingCovered"),
                        "conditions": category_data_from_ai.get("preExistingConditions"),
                        "limit": category_data_from_ai.get("preExistingLimit"),
                        "ageRestriction": category_data_from_ai.get("preExistingAgeRestriction")
                    },
                    "maternityCoverage": {
                        "covered": category_data_from_ai.get("maternityCovered")
                    }
                },
                # 1.6 Trip Protection (EAZR_05 §3.3)
                "tripProtection": {
                    "tripCancellation": {
                        "covered": bool(category_data_from_ai.get("tripCancellation")),
                        "limit": category_data_from_ai.get("tripCancellation"),
                        "coveredReasons": category_data_from_ai.get("tripCancellationCoveredReasons") or [],
                        "notCoveredReasons": category_data_from_ai.get("tripCancellationNotCoveredReasons") or []
                    },
                    "tripCurtailment": {
                        "covered": category_data_from_ai.get("tripCurtailmentCovered"),
                        "limit": category_data_from_ai.get("tripCurtailmentLimit"),
                        "benefitType": category_data_from_ai.get("tripCurtailmentBenefitType")
                    },
                    "tripDelay": {
                        "covered": bool(category_data_from_ai.get("flightDelay")),
                        "triggerHours": category_data_from_ai.get("tripDelayTriggerHours"),
                        "benefitAmount": category_data_from_ai.get("flightDelay"),
                        "coveredExpenses": category_data_from_ai.get("tripDelayCoveredExpenses") or []
                    },
                    "missedConnection": {
                        "covered": category_data_from_ai.get("missedConnectionCovered"),
                        "triggerHours": category_data_from_ai.get("missedConnectionTriggerHours"),
                        "benefitAmount": category_data_from_ai.get("missedConnectionBenefitAmount")
                    },
                    "hijackDistress": {
                        "covered": bool(category_data_from_ai.get("hijackDistress")),
                        "benefitAmount": category_data_from_ai.get("hijackDistress")
                    }
                },
                # 1.7 Baggage Coverage (EAZR_05 §3.4)
                "baggageCoverage": {
                    "loss": {
                        "totalLimit": category_data_from_ai.get("baggageLoss"),
                        "perItemLimit": category_data_from_ai.get("baggagePerItemLimit"),
                        "valuablesLimit": category_data_from_ai.get("baggageValuablesLimit"),
                        "documentationRequired": category_data_from_ai.get("baggageDocumentationRequired") or []
                    },
                    "delay": {
                        "covered": bool(category_data_from_ai.get("baggageDelay")),
                        "benefitAmount": category_data_from_ai.get("baggageDelay")
                    },
                    "passportLoss": {
                        "covered": bool(category_data_from_ai.get("passportLoss")),
                        "limit": category_data_from_ai.get("passportLoss")
                    }
                },
                # 1.8 Exclusions (enhanced with adventure sports detail)
                "exclusions": {
                    "adventureSportsExclusion": category_data_from_ai.get("adventureSportsExclusion"),
                    "adventureSportsIncluded": category_data_from_ai.get("sportsCoveredList") or [],
                    "adventureSportsExcluded": category_data_from_ai.get("sportsExcludedList") or [],
                    "adventureAdditionalPremium": category_data_from_ai.get("adventureAdditionalPremium"),
                    "preExistingConditionExclusion": category_data_from_ai.get("preExistingConditionExclusion"),
                    "schengenCompliant": category_data_from_ai.get("schengenCompliant"),
                    "otherExclusions": category_data_from_ai.get("otherExclusions") or extracted_data.get("exclusions") or []
                },
                # 1.9 Premium (enhanced with per-day and factors)
                "premium": {
                    "basePremium": category_data_from_ai.get("travelBasePremium"),
                    "gst": category_data_from_ai.get("travelGst"),
                    "totalPremium": category_data_from_ai.get("travelTotalPremium") or extracted_data.get("premium"),
                    "premiumPerDay": category_data_from_ai.get("premiumPerDay"),
                    "premiumFactors": {
                        "ageBand": category_data_from_ai.get("premiumAgeBand"),
                        "destinationZone": category_data_from_ai.get("premiumDestinationZone"),
                        "tripDuration": category_data_from_ai.get("tripDuration"),
                        "coverageLevel": category_data_from_ai.get("premiumCoverageLevel")
                    }
                },
                # 1.10 Emergency Contacts (enhanced with primary & India emergency)
                "emergencyContacts": {
                    "emergencyHelpline24x7": category_data_from_ai.get("emergencyHelpline24x7"),
                    "claimsEmail": category_data_from_ai.get("claimsEmail"),
                    "insurerAddress": category_data_from_ai.get("insurerAddress"),
                    "cashlessHospitals": category_data_from_ai.get("cashlessHospitals"),
                    "primaryContact": {
                        "name": category_data_from_ai.get("primaryContactName"),
                        "phone": category_data_from_ai.get("primaryContactPhone"),
                        "email": category_data_from_ai.get("primaryContactEmail")
                    },
                    "emergencyContactIndia": {
                        "name": category_data_from_ai.get("emergencyContactIndiaName"),
                        "relationship": category_data_from_ai.get("emergencyContactIndiaRelationship"),
                        "phone": category_data_from_ai.get("emergencyContactIndiaPhone")
                    }
                }
            }

        # ==================== BUSINESS INSURANCE (TAB 1) ====================
        elif "business" in detected_policy_type or "commercial" in detected_policy_type or "fire" in detected_policy_type or "liability" in detected_policy_type or "marine" in detected_policy_type or "cyber" in detected_policy_type:
            complete_category_data = {
                # 1.1 Policy Identification
                "policyIdentification": {
                    "policyNumber": category_data_from_ai.get("policyNumber") or extracted_data.get("policyNumber"),
                    "uin": category_data_from_ai.get("uin") or extracted_data.get("uin") or extracted_uin or "",
                    "productName": category_data_from_ai.get("productName"),
                    "policyType": category_data_from_ai.get("policyType"),
                    "insurerName": category_data_from_ai.get("insurerName") or extracted_data.get("insuranceProvider"),
                    "policyPeriod": category_data_from_ai.get("policyPeriod")
                },
                # 1.2 Insured Entity
                "insuredEntity": {
                    "businessName": category_data_from_ai.get("businessName"),
                    "businessType": category_data_from_ai.get("businessType"),
                    "businessNature": category_data_from_ai.get("businessNature"),
                    "gstNumber": category_data_from_ai.get("gstNumber"),
                    "cinNumber": category_data_from_ai.get("cinNumber"),
                    "businessAddress": category_data_from_ai.get("businessAddress"),
                    "contactPerson": category_data_from_ai.get("contactPerson"),
                    "contactNumber": category_data_from_ai.get("contactNumber"),
                    "contactEmail": category_data_from_ai.get("contactEmail")
                },
                # 1.3 Property Coverage
                "propertyCoverage": {
                    "buildingValue": category_data_from_ai.get("buildingValue"),
                    "plantMachineryValue": category_data_from_ai.get("plantMachineryValue"),
                    "stocksValue": category_data_from_ai.get("stocksValue"),
                    "furnitureFixturesValue": category_data_from_ai.get("furnitureFixturesValue"),
                    "electricalInstallationsValue": category_data_from_ai.get("electricalInstallationsValue"),
                    "otherContentsValue": category_data_from_ai.get("otherContentsValue"),
                    "totalPropertyValue": category_data_from_ai.get("totalPropertyValue") or extracted_data.get("coverageAmount")
                },
                # 1.4 Perils Covered
                "perilsCovered": {
                    "fire": category_data_from_ai.get("fire"),
                    "lightning": category_data_from_ai.get("lightning"),
                    "explosion": category_data_from_ai.get("explosion"),
                    "riot": category_data_from_ai.get("riot"),
                    "earthquake": category_data_from_ai.get("earthquake"),
                    "flood": category_data_from_ai.get("flood"),
                    "storm": category_data_from_ai.get("storm"),
                    "burglary": category_data_from_ai.get("burglary"),
                    "terrorism": category_data_from_ai.get("terrorism"),
                    "additionalPerils": category_data_from_ai.get("additionalPerils") or []
                },
                # 1.5 Liability Coverage
                "liabilityCoverage": {
                    "publicLiability": category_data_from_ai.get("publicLiability"),
                    "productLiability": category_data_from_ai.get("productLiability"),
                    "professionalIndemnity": category_data_from_ai.get("professionalIndemnity"),
                    "employersLiability": category_data_from_ai.get("employersLiability"),
                    "directorsOfficersLiability": category_data_from_ai.get("directorsOfficersLiability"),
                    "cyberLiability": category_data_from_ai.get("cyberLiability")
                },
                # 1.6 Business Interruption
                "businessInterruption": {
                    "businessInterruptionCover": category_data_from_ai.get("businessInterruptionCover"),
                    "grossProfitInsured": category_data_from_ai.get("grossProfitInsured"),
                    "indemnityPeriod": category_data_from_ai.get("indemnityPeriod"),
                    "alternativePremises": category_data_from_ai.get("alternativePremises")
                },
                # 1.7 Premium
                "premium": {
                    "propertyPremium": category_data_from_ai.get("propertyPremium"),
                    "liabilityPremium": category_data_from_ai.get("liabilityPremium"),
                    "biPremium": category_data_from_ai.get("biPremium"),
                    "gst": category_data_from_ai.get("gst"),
                    "totalPremium": category_data_from_ai.get("totalPremium") or extracted_data.get("premium")
                },
                # 1.8 Key Exclusions
                "keyExclusions": {
                    "warExclusion": category_data_from_ai.get("warExclusion"),
                    "wearTearExclusion": category_data_from_ai.get("wearTearExclusion"),
                    "otherExclusions": category_data_from_ai.get("otherExclusions") or extracted_data.get("exclusions") or []
                }
            }

        # ==================== PERSONAL ACCIDENT / ACCIDENTAL INSURANCE (TAB 1) — EAZR_04 Spec ====================
        elif "accidental" in detected_policy_type or "accident" in detected_policy_type or "pa" in detected_policy_type or "personal accident" in detected_policy_type:
            # Helper to safely parse numeric values from AI extraction
            def _safe_pa_float(val, default=0):
                if val is None:
                    return default
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, str):
                    cleaned = val.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
                    try:
                        return float(cleaned)
                    except (ValueError, TypeError):
                        return default
                return default

            pa_si = _safe_pa_float(category_data_from_ai.get("paSumInsured") or category_data_from_ai.get("sumInsured") or extracted_data.get("coverageAmount"), 0)

            # Detect EAZR company PA policy (complimentary PA given to users)
            def _is_eazr_company_pa(group_holder, product_name, total_premium):
                """Check if this PA policy is an EAZR company complimentary PA cover."""
                gh = str(group_holder or "").upper()
                pn = str(product_name or "").upper()
                # Match: groupPolicyholderName contains "EAZR" OR productName contains "EAZR DIGI"/"GC 360"
                if "EAZR" in gh:
                    return True
                if "EAZR DIGI" in pn or "EAZR_DIGI" in pn:
                    return True
                if "GC 360" in pn and total_premium <= 10:
                    return True
                return False

            # Default IRDAI PPD schedule
            default_ppd_schedule = [
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

            complete_category_data = {
                # Section 1: Policy Basics (EAZR_04 Spec 3.1)
                "policyBasics": {
                    "policyNumber": category_data_from_ai.get("policyNumber") or extracted_data.get("policyNumber"),
                    "certificateNumber": category_data_from_ai.get("paCertificateNumber") or category_data_from_ai.get("certificateNumber"),
                    "uin": category_data_from_ai.get("uin") or extracted_data.get("uin") or extracted_uin or "",
                    "insurerName": category_data_from_ai.get("insurerName") or extracted_data.get("insuranceProvider"),
                    "productName": category_data_from_ai.get("productName") or category_data_from_ai.get("planName"),
                    "policyType": category_data_from_ai.get("paInsuranceType") or "Individual",
                    "policySubType": category_data_from_ai.get("paPolicySubType") or "IND_PA",
                    "policyStartDate": category_data_from_ai.get("policyPeriodStart") or extracted_data.get("startDate"),
                    "policyEndDate": category_data_from_ai.get("policyPeriodEnd") or extracted_data.get("endDate"),
                    "policyTerm": category_data_from_ai.get("policyTerm") or 1,
                    "policyStatus": "active",
                    "groupPolicyholderName": category_data_from_ai.get("groupPolicyholderName"),
                    "groupPolicyNumber": category_data_from_ai.get("groupPolicyNumber"),
                    "isCompanyPA": _is_eazr_company_pa(
                        category_data_from_ai.get("groupPolicyholderName"),
                        category_data_from_ai.get("productName") or category_data_from_ai.get("planName"),
                        _safe_pa_float(category_data_from_ai.get("totalPremium") or extracted_data.get("premium"), 0),
                    ),
                },
                # Section 2: Coverage Details (EAZR_04 Spec 3.2) — Nested structured objects
                "coverageDetails": {
                    "sumInsured": pa_si,
                    "accidentalDeath": {
                        "covered": True,
                        "benefitPercentage": _safe_pa_float(category_data_from_ai.get("accidentalDeathBenefitPercentage"), 100),
                        "benefitAmount": _safe_pa_float(category_data_from_ai.get("accidentalDeathBenefitAmount"), pa_si),
                        "doubleIndemnity": {
                            "applicable": bool(category_data_from_ai.get("doubleIndemnityApplicable")),
                            "conditions": category_data_from_ai.get("doubleIndemnityConditions") or ""
                        }
                    },
                    "permanentTotalDisability": {
                        "covered": bool(category_data_from_ai.get("permanentTotalDisabilityCovered", True)),
                        "benefitPercentage": _safe_pa_float(category_data_from_ai.get("permanentTotalDisabilityPercentage"), 100),
                        "benefitAmount": _safe_pa_float(category_data_from_ai.get("permanentTotalDisabilityAmount"), pa_si),
                        "conditionsList": category_data_from_ai.get("ptdConditions") or []
                    },
                    "permanentPartialDisability": {
                        "covered": bool(category_data_from_ai.get("permanentPartialDisabilityCovered", True)),
                        "benefitType": "As per schedule",
                        "schedule": category_data_from_ai.get("ppdSchedule") or default_ppd_schedule
                    },
                    "temporaryTotalDisability": {
                        "covered": bool(category_data_from_ai.get("temporaryTotalDisabilityCovered")),
                        "benefitType": category_data_from_ai.get("ttdBenefitType") or "weekly",
                        "benefitPercentage": _safe_pa_float(category_data_from_ai.get("ttdBenefitPercentage"), 1),
                        "benefitAmount": _safe_pa_float(category_data_from_ai.get("ttdBenefitAmount"), 0),
                        "maximumWeeks": int(_safe_pa_float(category_data_from_ai.get("ttdMaximumWeeks"), 52)),
                        "waitingPeriodDays": int(_safe_pa_float(category_data_from_ai.get("ttdWaitingPeriodDays"), 7))
                    },
                    "medicalExpenses": {
                        "covered": bool(category_data_from_ai.get("medicalExpensesCovered")),
                        "limitType": category_data_from_ai.get("medicalExpensesLimitType") or "percentage_of_si",
                        "limitPercentage": _safe_pa_float(category_data_from_ai.get("medicalExpensesLimitPercentage"), 10),
                        "limitAmount": _safe_pa_float(category_data_from_ai.get("medicalExpensesLimitAmount"), 0),
                        "perAccidentOrAnnual": category_data_from_ai.get("medicalExpensesPerAccidentOrAnnual") or "per_accident"
                    }
                },
                # Section 3: Additional Benefits (EAZR_04 Spec 3.3)
                "additionalBenefits": {
                    "educationBenefit": {
                        "covered": bool(category_data_from_ai.get("educationBenefitCovered")),
                        "benefitAmount": _safe_pa_float(category_data_from_ai.get("educationBenefitAmount"), 0),
                        "benefitType": category_data_from_ai.get("educationBenefitType") or "lump_sum"
                    },
                    "loanEmiCover": {
                        "covered": bool(category_data_from_ai.get("loanEmiCoverCovered")),
                        "maxMonths": int(_safe_pa_float(category_data_from_ai.get("loanEmiCoverMaxMonths"), 0)),
                        "maxAmountPerMonth": _safe_pa_float(category_data_from_ai.get("loanEmiCoverMaxAmountPerMonth"), 0)
                    },
                    "ambulanceCharges": {
                        "covered": bool(category_data_from_ai.get("ambulanceChargesCovered")),
                        "limit": _safe_pa_float(category_data_from_ai.get("ambulanceChargesLimit"), 0)
                    },
                    "transportationOfMortalRemains": {
                        "covered": bool(category_data_from_ai.get("transportMortalRemainsCovered")),
                        "limit": _safe_pa_float(category_data_from_ai.get("transportMortalRemainsLimit"), 0)
                    },
                    "funeralExpenses": {
                        "covered": bool(category_data_from_ai.get("funeralExpensesCovered")),
                        "limit": _safe_pa_float(category_data_from_ai.get("funeralExpensesLimit"), 0)
                    },
                    "homeModification": {
                        "covered": bool(category_data_from_ai.get("homeModificationCovered")),
                        "limit": _safe_pa_float(category_data_from_ai.get("homeModificationLimit"), 0)
                    },
                    "vehicleModification": {
                        "covered": bool(category_data_from_ai.get("vehicleModificationCovered")),
                        "limit": _safe_pa_float(category_data_from_ai.get("vehicleModificationLimit"), 0)
                    },
                    "carriageOfAttendant": {
                        "covered": bool(category_data_from_ai.get("carriageOfAttendantCovered")),
                        "limit": _safe_pa_float(category_data_from_ai.get("carriageOfAttendantLimit"), 0)
                    }
                },
                # Section 4: Exclusions (EAZR_04 Spec 3.4)
                "exclusions": {
                    "standardExclusions": category_data_from_ai.get("paStandardExclusions") or [],
                    "waitingPeriods": {
                        "initialWaiting": 0,
                        "ttdWaiting": int(_safe_pa_float(category_data_from_ai.get("ttdEliminationPeriod"), 7))
                    },
                    "ageLimits": {
                        "minimumEntryAge": int(_safe_pa_float(category_data_from_ai.get("paAgeMinimum"), 18)),
                        "maximumEntryAge": int(_safe_pa_float(category_data_from_ai.get("paAgeMaximum"), 65)),
                        "maximumRenewalAge": int(_safe_pa_float(category_data_from_ai.get("paMaxRenewalAge"), 70))
                    },
                    "occupationRestrictions": category_data_from_ai.get("paOccupationRestrictions") or []
                },
                # Section 5: Premium Details (EAZR_04 Spec 3.5)
                "premiumDetails": {
                    "basePremium": _safe_pa_float(category_data_from_ai.get("basePremium") or extracted_data.get("premium"), 0),
                    "gstAmount": _safe_pa_float(category_data_from_ai.get("gst"), 0),
                    "totalPremium": _safe_pa_float(category_data_from_ai.get("totalPremium") or extracted_data.get("premium"), 0),
                    "premiumFrequency": category_data_from_ai.get("paPremiumFrequency") or category_data_from_ai.get("premiumPaymentMode") or "annual",
                    "premiumFactors": {
                        "ageBand": category_data_from_ai.get("paAgeBand") or "",
                        "occupationClass": category_data_from_ai.get("paOccupationClass") or "",
                        "sumInsuredBand": ""
                    }
                },
                # Section 6: Insured Members (EAZR_04 Spec 3.6)
                "insuredMembers": category_data_from_ai.get("paInsuredMembers") or [{
                    "name": category_data_from_ai.get("insuredName") or extracted_data.get("policyHolderName") or "",
                    "relationship": "self",
                    "dateOfBirth": category_data_from_ai.get("dateOfBirth") or "",
                    "gender": category_data_from_ai.get("gender") or "",
                    "occupation": category_data_from_ai.get("occupation") or ""
                }],
                # Legacy sections (backward compatibility + claims/contact info)
                "nomination": {
                    "nomineeName": category_data_from_ai.get("nomineeName"),
                    "nomineeRelationship": category_data_from_ai.get("nomineeRelationship"),
                    "nomineeShare": category_data_from_ai.get("nomineeShare") or "100%"
                },
                "claimsInfo": {
                    "claimsProcess": category_data_from_ai.get("claimsProcess"),
                    "claimsEmail": category_data_from_ai.get("claimsEmail"),
                    "claimsHelpline": category_data_from_ai.get("claimsHelpline"),
                    "claimsDocumentsRequired": category_data_from_ai.get("claimsDocumentsRequired") or []
                },
                "contactInfo": {
                    "insurerAddress": category_data_from_ai.get("insurerAddress"),
                    "insurerWebsite": category_data_from_ai.get("insurerWebsite"),
                    "insurerEmail": category_data_from_ai.get("insurerEmail"),
                    "insurerPhone": category_data_from_ai.get("insurerPhone"),
                    "irdaiRegNo": category_data_from_ai.get("irdaiRegNo")
                }
            }

        # ==================== AGRICULTURE INSURANCE (TAB 1) ====================
        elif "agriculture" in detected_policy_type or "crop" in detected_policy_type or "farm" in detected_policy_type or "pmfby" in detected_policy_type:
            complete_category_data = {
                # 1.1 Policy Identification
                "policyIdentification": {
                    "policyNumber": category_data_from_ai.get("policyNumber") or extracted_data.get("policyNumber"),
                    "schemeName": category_data_from_ai.get("schemeName"),
                    "seasonYear": category_data_from_ai.get("seasonYear"),
                    "insurerName": category_data_from_ai.get("insurerName") or extracted_data.get("insuranceProvider"),
                    "policyIssueDate": category_data_from_ai.get("policyIssueDate") or extracted_data.get("startDate")
                },
                # 1.2 Farmer Details
                "farmerDetails": {
                    "farmerName": category_data_from_ai.get("farmerName") or extracted_data.get("policyHolderName"),
                    "farmerType": category_data_from_ai.get("farmerType"),
                    "farmerCategory": category_data_from_ai.get("farmerCategory"),
                    "farmerMobile": category_data_from_ai.get("farmerMobile"),
                    "farmerAddress": category_data_from_ai.get("farmerAddress"),
                    "farmerAadhaar": category_data_from_ai.get("farmerAadhaar"),
                    "bankName": category_data_from_ai.get("bankName"),
                    "bankAccountNumber": category_data_from_ai.get("bankAccountNumber"),
                    "ifscCode": category_data_from_ai.get("ifscCode")
                },
                # 1.3 Land & Crop Details
                "landCropDetails": {
                    "surveyNumbers": category_data_from_ai.get("surveyNumbers") or [],
                    "villageOrGramPanchayat": category_data_from_ai.get("villageOrGramPanchayat"),
                    "blockTalukaOrTehsil": category_data_from_ai.get("blockTalukaOrTehsil"),
                    "district": category_data_from_ai.get("district"),
                    "state": category_data_from_ai.get("state"),
                    "totalAreaInsured": category_data_from_ai.get("totalAreaInsured"),
                    "cropName": category_data_from_ai.get("cropName"),
                    "cropCode": category_data_from_ai.get("cropCode"),
                    "cropType": category_data_from_ai.get("cropType")
                },
                # 1.4 Coverage Details
                "coverageDetails": {
                    "sumInsuredPerHectare": category_data_from_ai.get("sumInsuredPerHectare"),
                    "totalSumInsured": category_data_from_ai.get("totalSumInsured") or extracted_data.get("coverageAmount"),
                    "premiumRateFarmer": category_data_from_ai.get("premiumRateFarmer"),
                    "premiumRateGov": category_data_from_ai.get("premiumRateGov"),
                    "farmerPremiumAmount": category_data_from_ai.get("farmerPremiumAmount"),
                    "govSubsidyAmount": category_data_from_ai.get("govSubsidyAmount"),
                    "totalPremium": category_data_from_ai.get("totalPremium") or extracted_data.get("premium")
                },
                # 1.5 Risks Covered
                "risksCovered": {
                    "preventedSowing": category_data_from_ai.get("preventedSowing"),
                    "midSeasonAdversity": category_data_from_ai.get("midSeasonAdversity"),
                    "localizedCalamity": category_data_from_ai.get("localizedCalamity"),
                    "postHarvestLosses": category_data_from_ai.get("postHarvestLosses"),
                    "wildAnimalAttack": category_data_from_ai.get("wildAnimalAttack"),
                    "addOnCovers": category_data_from_ai.get("addOnCovers") or []
                },
                # 1.6 Premium
                "premium": {
                    "farmerSharePremium": category_data_from_ai.get("farmerSharePremium"),
                    "stateSharePremium": category_data_from_ai.get("stateSharePremium"),
                    "centralSharePremium": category_data_from_ai.get("centralSharePremium"),
                    "totalPremium": category_data_from_ai.get("totalPremium") or extracted_data.get("premium"),
                    "premiumPaidDate": category_data_from_ai.get("premiumPaidDate")
                },
                # 1.7 Claim Process
                "claimProcess": {
                    "claimIntimationPeriod": category_data_from_ai.get("claimIntimationPeriod"),
                    "claimIntimationMethod": category_data_from_ai.get("claimIntimationMethod"),
                    "yieldBasedAssessment": category_data_from_ai.get("yieldBasedAssessment"),
                    "cropCuttingExperiments": category_data_from_ai.get("cropCuttingExperiments"),
                    "thresholdYield": category_data_from_ai.get("thresholdYield")
                },
                # 1.8 Exclusions
                "exclusions": {
                    "warExclusion": category_data_from_ai.get("warExclusion"),
                    "willfulDamage": category_data_from_ai.get("willfulDamage"),
                    "otherExclusions": category_data_from_ai.get("otherExclusions") or extracted_data.get("exclusions") or []
                }
            }

        # ==================== DEFAULT/GENERIC (fallback) ====================
        else:
            # Fallback for unknown policy types - include all extracted category data as-is
            complete_category_data = category_data_from_ai

        # ==================== DATA VALIDATION FUNCTIONS ====================
        # Validate extracted data for inconsistencies and redundant features

        def detect_redundant_addons(category_data: dict, policy_type: str) -> dict:
            """
            Detect redundant add-ons based on policy features.
            FIXED: Only flag add-ons that provide no additional value.

            Key insight: Add-ons that ENABLE features (like waiting period waivers) are NOT redundant.
            They are what makes the policy have "No waiting period".
            """
            redundant_addons = []
            total_wasted = 0

            # Only relevant for health insurance
            if not any(kw in policy_type for kw in ["health", "medical", "mediclaim"]):
                return {"redundantAddons": [], "totalWastedPremium": 0, "hasRedundantAddons": False}

            # Get waiting periods information
            waiting_periods = category_data.get("waitingPeriods", {})
            initial_waiting = str(waiting_periods.get("initialWaitingPeriod", "")).lower()
            ped_waiting = str(waiting_periods.get("preExistingDiseaseWaiting", "")).lower()
            specific_disease_waiting = str(waiting_periods.get("specificDiseaseWaiting", "")).lower()

            # Check if policy already HAS NO waiting periods (without add-ons)
            # This would be the base policy state before add-ons
            # If base policy already has "No waiting period", THEN waiver add-ons are redundant
            base_policy_has_no_waiting = (
                "no waiting" in initial_waiting or
                "nil" in initial_waiting or
                "not applicable" in initial_waiting or
                initial_waiting == "0"
            )

            # Get premium breakdown to find add-on premiums
            premium_breakdown = category_data.get("premiumBreakdown", {})
            add_on_premiums = premium_breakdown.get("addOnPremiums", {})
            other_add_ons = add_on_premiums.get("otherAddOns", {}) if isinstance(add_on_premiums, dict) else {}

            # Check for genuinely redundant add-ons
            for addon_name, premium in other_add_ons.items():
                if not premium or premium == 0:
                    continue

                premium_value = 0
                try:
                    premium_value = float(premium) if not isinstance(premium, (int, float)) else premium
                except (ValueError, TypeError):
                    continue

                addon_name_lower = addon_name.lower()
                is_redundant = False
                reason = ""

                # 1. ONLY flag waiting period add-ons if base policy ALREADY has no waiting
                # (meaning the add-on is not what's providing the benefit)
                if base_policy_has_no_waiting:
                    if "waiting period" in addon_name_lower:
                        is_redundant = True
                        reason = "Base policy already has no waiting period - this add-on doesn't add value"
                    elif "specific illness" in addon_name_lower:
                        is_redundant = True
                        reason = "Base policy already has no specific disease waiting - this add-on doesn't add value"
                    elif "initial waiting" in addon_name_lower:
                        is_redundant = True
                        reason = "Base policy already has no initial waiting - this add-on doesn't add value"

                # 2. Check for inflation shield redundancy (if already accumulated)
                # Only redundant if accumulated amount is >= add-on premium amount
                accumulated_benefits = category_data.get("accumulatedBenefits", {}) or {}
                accumulated_inflation = _parse_number_from_string_safe(str(accumulated_benefits.get("accumulatedInflationShield", 0) or 0))
                if accumulated_inflation and accumulated_inflation > 0:
                    # Only flag if the accumulated amount is substantial
                    # A small add-on premium might still provide some future benefit
                    if accumulated_inflation > premium_value * 2:  # Accumulated > 2x add-on premium
                        if "inflation protect" in addon_name_lower and "si" in addon_name_lower:
                            is_redundant = True
                            reason = f"Already accumulated ₹{accumulated_inflation:,.0f} in inflation shield - add-on premium is minimal benefit"

                # 3. Check for duplicate add-ons with same benefit
                # (e.g., "Restore SI" when restoration is already included in base policy)
                restoration = category_data.get("coverageDetails", {}).get("restoration", {})
                if isinstance(restoration, dict):
                    restoration_available = restoration.get("available")
                    restoration_type = restoration.get("type", "")

                    # If restoration is already in base policy, "Restore SI" add-on is redundant
                    if restoration_available and restoration_type and "restore si" in addon_name_lower:
                        is_redundant = True
                        reason = f"Restoration ({restoration_type}) already included in base policy - this add-on is redundant"

                if is_redundant:
                    redundant_addons.append({
                        "addOnName": addon_name,
                        "premium": premium_value,
                        "premiumFormatted": f"₹{premium_value:,.0f}",
                        "reason": reason,
                        "severity": "high" if premium_value > 1000 else "medium"
                    })
                    total_wasted += premium_value

            return {
                "redundantAddons": redundant_addons,
                "totalWastedPremium": total_wasted,
                "totalWastedFormatted": f"₹{total_wasted:,.0f}",
                "hasRedundantAddons": len(redundant_addons) > 0,
                "note": "Add-ons that enable features (like waiting period waivers) are NOT redundant"
            }

        def validate_policy_data(category_data: dict, policy_type: str) -> dict:
            """
            Validate extracted policy data for inconsistencies.
            Returns dict with warnings, errors, and recommendations.
            """
            import re
            warnings = []
            errors = []
            recommendations = []

            # 1. Cover Type Validation (Health Insurance)
            # Note: This is a DATA EXTRACTION check, not a policy issue
            # Mismatches indicate AI extraction errors, not problems with the actual policy
            if any(kw in policy_type for kw in ["health", "medical", "mediclaim"]):
                insured_members = category_data.get("insuredMembers", [])
                members_covered = category_data.get("membersCovered", [])

                member_count = len(insured_members) if isinstance(insured_members, list) else len(members_covered) if isinstance(members_covered, list) else 0
                cover_type = category_data.get("coverageDetails", {}).get("coverType", "")

                if member_count > 1:
                    if cover_type and "individual" in cover_type.lower():
                        # Check if this is a genuine Individual policy (policyType also says Individual
                        # or members have different SIs) vs a likely extraction error
                        _policy_type_val = category_data.get("policyDetails", {}).get("policyType", "")
                        _genuine_individual = False
                        if _policy_type_val and "individual" in str(_policy_type_val).lower():
                            _genuine_individual = True
                        # Check per-member sumInsured differences
                        _m_sis = []
                        for _m in (insured_members if isinstance(insured_members, list) else []):
                            _msi = _m.get("memberSumInsured") if isinstance(_m, dict) else None
                            if _msi and isinstance(_msi, (int, float)) and _msi > 0:
                                _m_sis.append(_msi)
                        if len(set(_m_sis)) > 1:
                            _genuine_individual = True
                        if not _genuine_individual:
                            warnings.append({
                                "field": "coverType",
                                "currentValue": cover_type,
                                "expectedValue": "Family Floater (likely)",
                                "issue": f"Data extraction inconsistency: {member_count} members found but cover type extracted as '{cover_type}'",
                                "recommendation": "This is likely an AI extraction error. The actual policy probably has 'Family Floater' cover type. Please verify from the policy document.",
                                "severity": "medium",
                                "issueType": "dataExtractionInconsistency"
                            })
                elif member_count <= 1 and cover_type and "family" in cover_type.lower():
                    warnings.append({
                        "field": "coverType",
                        "currentValue": cover_type,
                        "expectedValue": "Individual (likely)",
                        "issue": f"Data extraction inconsistency: {member_count} member found but cover type extracted as '{cover_type}'",
                        "recommendation": "This is likely an AI extraction error. For single member, the actual policy probably has 'Individual' cover type. Please verify from the policy document.",
                        "severity": "low",
                        "issueType": "dataExtractionInconsistency"  # Distinguish from policy issues
                    })

            # 2. Sum Insured Validation
            coverage_details = category_data.get("coverageDetails", {})
            sum_insured = coverage_details.get("sumInsured", 0)

            try:
                sum_insured = float(sum_insured) if not isinstance(sum_insured, (int, float)) else sum_insured
            except (ValueError, TypeError):
                sum_insured = 0

            if any(kw in policy_type for kw in ["health", "medical", "mediclaim"]):
                # Check if sum insured is adequate
                if sum_insured < 500000:
                    warnings.append({
                        "field": "sumInsured",
                        "currentValue": f"₹{sum_insured:,.0f}",
                        "issue": "Sum Insured is below recommended minimum",
                        "recommendation": "Consider increasing Sum Insured to at least ₹5,00,000 for adequate coverage",
                        "severity": "high"
                    })
                elif sum_insured < 1000000:
                    warnings.append({
                        "field": "sumInsured",
                        "currentValue": f"₹{sum_insured:,.0f}",
                        "issue": "Sum Insured is below recommended level for family coverage",
                        "recommendation": "Consider increasing Sum Insured to ₹10,00,000 - ₹15,00,000 for better protection",
                        "severity": "medium"
                    })

            # 3. Value Type Validation (correctly detect field types)
            def validate_value_type(value: any, field_id: str, field_label: str) -> tuple:
                """
                Validate and correct the value type for a field.
                Returns (corrected_value_type, reason_for_change).
                """

                if value is None:
                    return "null", None

                if isinstance(value, bool):
                    return "boolean", None

                if isinstance(value, (int, float)):
                    return "number", None

                if isinstance(value, list):
                    return "array", None

                if isinstance(value, dict):
                    return "object", None

                # String value type detection
                str_value = str(value).lower()
                field_lower = field_id.lower()

                # Address patterns - should be string, not date
                if any(keyword in field_lower for keyword in ["address", "location", "area", "city", "state", "pin", "zip"]):
                    if "date" in str_value or any(c.isdigit() for c in str_value):
                        return "string", "Address field detected - marked as string instead of date"

                # Currency patterns
                if any(symbol in str_value for symbol in ["₹", "rs.", "inr", "$", "€", "£", "¥"]):
                    return "currency", None

                # Date patterns - must have 4-digit year
                if any(separator in str_value for separator in ["-", "/"]) and re.search(r'\d{4}', str_value):
                    return "date", None

                # Phone number patterns
                if re.match(r'^[\d\s\-\+\(\)]+$', str(value)):
                    return "phone", None

                # Email patterns
                if "@" in str_value and "." in str_value:
                    return "email", None

                return "string", None

            # 3.1. Value Type Inconsistency Detection
            # Check key fields for obviously incorrect valueType assignments
            # This catches AI extraction errors where field context is ignored

            def get_actual_value_type(value: any, field_id: str = "") -> str:
                """Get the actual valueType using field context first, pattern matching second.

                Mirrors the logic in get_value_type() from build_unified_sections
                to avoid false positives (e.g., '/' in addresses triggering date detection).
                """
                if value is None:
                    return "null"
                if isinstance(value, bool):
                    return "boolean"
                if isinstance(value, (int, float)):
                    return "number"
                if isinstance(value, list):
                    return "array"
                if isinstance(value, dict):
                    return "object"

                # ---- Field context overrides (checked FIRST) ----
                field_lower = field_id.lower() if field_id else ""

                # Fields that are ALWAYS strings regardless of value patterns
                _string_fields = {
                    "productname", "policytype", "insurername", "insureraddress",
                    "intermediaryname", "intermediarycode", "registrationnumber",
                    "address", "location", "area", "city", "state", "pin", "zip",
                    "uin", "policynumber", "vehicleregistrationnumber",
                    "vehiclemake", "vehiclemodel", "covertype", "roomrentlimit",
                    "iculimit", "ambulancecover", "healthcheckup",
                    "restorationamount", "maxncbpercentage", "ncbpercentage",
                    "name", "nominee", "relation", "occupation", "plan",
                }
                if any(sf in field_lower for sf in _string_fields):
                    return "string"

                # Fields that are ALWAYS dates
                _date_fields = {
                    "date", "dob", "dateofbirth", "policyissuedate",
                    "policystartdate", "policyenddate", "policyperiodstart",
                    "policyperiodend", "startdate", "enddate", "maturitydate",
                    "inceptiondate", "renewaldate", "tripstartdate", "tripenddate",
                }
                if any(df in field_lower for df in _date_fields):
                    return "date"

                # Fields that are ALWAYS phone
                _phone_fields = {"tollfree", "phone", "mobile", "contactnumber", "helpline"}
                if any(pf in field_lower for pf in _phone_fields):
                    return "phone"

                # Fields that are ALWAYS email
                if "email" in field_lower:
                    return "email"

                # ---- Pattern matching fallback (when field context is unknown) ----
                str_val = str(value).lower()
                raw_val = str(value)
                if any(x in str_val for x in ["₹", "inr", "$", "€", "£", "¥"]):
                    return "currency"
                # Date: require actual date-like pattern (DD/MM/YYYY, YYYY-MM-DD, etc.)
                if re.search(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}', str(value)):
                    return "date"
                # Phone: require separators or Indian phone prefixes
                if re.match(r'^[\d\s\-\+\(\)]+$', raw_val):
                    has_sep = any(c in raw_val for c in [' ', '-', '+', '(', ')'])
                    if has_sep:
                        return "phone"
                    if re.match(r'^[6-9]\d{9}$', raw_val) or re.match(r'^(1800|1860)\d{6,}$', raw_val):
                        return "phone"
                    return "string"
                if "@" in str_val and "." in str_val:
                    return "email"
                return "string"

            # Known field type mappings (field_id -> expected_type)
            # Based on business logic, not just pattern matching
            expected_field_types = {
                # Policy identification
                "productName": "string",
                "policyNumber": "string",
                "uin": "string",
                "insurerName": "string",
                "insurerAddress": "string",
                "insurerRegistrationNumber": "string",
                "intermediaryName": "string",
                "intermediaryCode": "string",
                "intermediaryEmail": "email",
                "insurerTollFree": "phone",

                # Dates (these should actually be dates)
                "policyIssueDate": "date",
                "policyPeriodStart": "date",
                "policyPeriodEnd": "date",

                # Coverage
                "coverType": "string",
                "roomRentLimit": "string",  # "No limit" not a number
                "icuLimit": "string",  # "No limit" not a number
                "ambulanceCover": "string",  # "No limit" not a number

                # Benefits that are text
                "healthCheckup": "string",
                "restorationAmount": "string",  # "Unlimited restore"

                # NCB
                "maxNcbPercentage": "string",  # "50%" with symbol
                "ncbPercentage": "string",  # Percentage values
            }

            # Check for valueType inconsistencies in all fields
            for section_key, section_data in category_data.items():
                if not isinstance(section_data, dict):
                    continue

                for field_key, field_value in section_data.items():
                    if field_value is None or field_value == "":
                        continue

                    # Get the actual valueType as it would be assigned (with field context)
                    actual_type = get_actual_value_type(field_value, field_key)

                    # Check if this field has an expected type
                    if field_key in expected_field_types:
                        expected_type = expected_field_types[field_key]

                        # Flag if actual doesn't match expected
                        if actual_type != expected_type:
                            warnings.append({
                                "field": f"{section_key}.{field_key}",
                                "value": str(field_value)[:100] + "..." if len(str(field_value)) > 100 else str(field_value),
                                "actualValueType": actual_type,
                                "expectedValueType": expected_type,
                                "issue": f"Data extraction inconsistency: Field '{field_key}' has valueType '{actual_type}' but should be '{expected_type}'",
                                "recommendation": f"The field value is being incorrectly classified as '{actual_type}' due to pattern matching (e.g., 'rs' in 'Policy' triggers currency detection, or '/' in addresses triggers date detection). This should be corrected to '{expected_type}' for proper frontend rendering.",
                                "severity": "low",
                                "issueType": "dataExtractionInconsistency"
                            })

            # 4. Duplicate Field Detection
            seen_fields = {}
            for section_key, section_data in category_data.items():
                if isinstance(section_data, dict):
                    for field_key in section_data.keys():
                        if field_key in seen_fields:
                            warnings.append({
                                "field": field_key,
                                "issue": f"Duplicate field found in multiple sections: {seen_fields[field_key]} and {section_key}",
                                "recommendation": "Consolidate duplicate fields to avoid confusion",
                                "severity": "low"
                            })
                        seen_fields[field_key] = section_key

            # 5. Restoration Benefit Validation (Health Insurance)
            restoration = coverage_details.get("restoration", {})
            if isinstance(restoration, dict):
                restoration_available = restoration.get("available")
                restoration_type = restoration.get("type", "")

                if restoration_available and restoration_type:
                    # Check if restoration is mentioned elsewhere with different value
                    restoration_amount = coverage_details.get("restorationAmount", "")
                    if restoration_amount and restoration_amount != restoration_type:
                        warnings.append({
                            "field": "restoration",
                            "issue": f"Conflicting restoration values: '{restoration_type}' vs '{restoration_amount}'",
                            "recommendation": "Ensure restoration benefit is consistently documented",
                            "severity": "low"
                        })

            # 6. Premium Validation
            # Handle both health (basePremium) and motor (grossPremium) naming
            premium_breakdown = category_data.get("premiumBreakdown", {})

            def _prem_num(d, key):
                raw = d.get(key, 0)
                if isinstance(raw, dict):
                    raw = raw.get("value", 0)
                try:
                    return float(raw) if raw else 0
                except (ValueError, TypeError):
                    return 0

            if premium_breakdown and isinstance(premium_breakdown, dict):
                base_premium = _prem_num(premium_breakdown, "basePremium") or _prem_num(premium_breakdown, "grossPremium")
                total_premium = _prem_num(premium_breakdown, "totalPremium")
                gst = _prem_num(premium_breakdown, "gst")
            else:
                base_premium = _prem_num(category_data, "basePremium") or _prem_num(category_data, "grossPremium")
                total_premium = _prem_num(category_data, "totalPremium")
                gst = _prem_num(category_data, "gst")

            # Compute total add-on premiums and discounts for accurate validation
            addon_premiums_total = 0.0
            discount_total = 0.0
            addon_section = premium_breakdown.get("addOnPremiums", {}) if premium_breakdown else {}
            other_addons = addon_section.get("otherAddOns", {}) if isinstance(addon_section, dict) else {}
            if isinstance(other_addons, dict):
                for _addon_name, _addon_val in other_addons.items():
                    try:
                        addon_premiums_total += float(_addon_val) if _addon_val else 0
                    except (ValueError, TypeError):
                        pass
            # Check for discount
            for _disc_key in ("existingCustomerDiscount", "discount", "loyaltyDiscount"):
                _disc_val = _prem_num(premium_breakdown, _disc_key) if premium_breakdown else 0
                if not _disc_val:
                    _disc_val = _prem_num(category_data, _disc_key)
                if _disc_val > 0:
                    discount_total += _disc_val

            taxable_amount = base_premium + addon_premiums_total - discount_total

            # Check if GST is approximately 18% of taxable amount
            if base_premium > 0 and gst > 0:
                gst_base = taxable_amount if taxable_amount > base_premium else base_premium
                gst_percentage = (gst / gst_base) * 100

                if abs(gst_percentage - 18) > 3:  # More than 3% deviation
                    warnings.append({
                        "field": "gst",
                        "issue": f"GST amount ({gst_percentage:.1f}% of taxable base) seems incorrect. Expected ~18%",
                        "recommendation": "Verify GST calculation with insurer",
                        "severity": "low"
                    })

            # Check if total premium matches base + addons + GST - discounts
            if base_premium > 0 and gst > 0 and total_premium > 0:
                expected_total = base_premium + addon_premiums_total + gst - discount_total
                tolerance = max(500, total_premium * 0.02)
                if abs(total_premium - expected_total) > tolerance:
                    warnings.append({
                        "field": "totalPremium",
                        "issue": f"Total premium (₹{total_premium:,.2f}) doesn't match base + addons + GST - discounts (₹{expected_total:,.2f})",
                        "recommendation": "Check for additional charges or discounts not accounted for",
                        "severity": "low"
                    })

            # 7. Member Data Validation (Health Insurance)
            if any(kw in policy_type for kw in ["health", "medical", "mediclaim"]):
                for section_key in ["insuredMembers", "membersCovered"]:
                    members = category_data.get(section_key, [])
                    if isinstance(members, list):
                        for idx, member in enumerate(members):
                            if isinstance(member, dict):
                                # Check age
                                age = member.get("memberAge")
                                if age:
                                    try:
                                        age = int(age)
                                        if age < 0 or age > 120:
                                            errors.append({
                                                "field": f"{section_key}[{idx}].memberAge",
                                                "value": age,
                                                "issue": f"Invalid age: {age}. Must be between 0 and 120",
                                                "recommendation": "Verify member age with policy document",
                                                "severity": "high"
                                            })
                                    except (ValueError, TypeError):
                                        pass

                                # Check gender
                                gender = member.get("memberGender")
                                if gender and gender.lower() not in ["male", "female", "other"]:
                                    warnings.append({
                                        "field": f"{section_key}[{idx}].memberGender",
                                        "value": gender,
                                        "issue": f"Unusual gender value: '{gender}'",
                                        "recommendation": "Verify gender is one of: Male, Female, Other",
                                        "severity": "low"
                                    })

            return {
                "warnings": warnings,
                "errors": errors,
                "recommendations": recommendations,
                "hasWarnings": len(warnings) > 0,
                "hasErrors": len(errors) > 0,
                "totalIssues": len(warnings) + len(errors)
            }

        # ==================== UNIFIED SECTIONS BUILDER ====================
        # Convert categorySpecificData into a unified sections array for Flutter/Dart frontend
        # This provides a consistent data structure regardless of policy type

        def build_unified_sections(category_data: dict, policy_type: str) -> list:
            """
            Convert category-specific data into a unified sections array.
            Each section has: sectionId, sectionTitle, sectionType, displayOrder, fields[]
            Each field has: fieldId, label, value, valueType, icon (optional)
            """
            sections = []
            section_order = 0

            # Section title mappings for each policy type
            section_titles = {
                "policyIdentification": "Policy Identification",
                "policyholderLifeAssured": "Policyholder & Life Assured",
                "coverageDetails": "Coverage Details",
                "premiumDetails": "Premium Details",
                "riders": "Riders & Add-ons",
                "bonusValue": "Bonus & Value",
                "ulipDetails": "ULIP Details",
                "nomination": "Nomination Details",
                "keyTerms": "Key Terms",
                "exclusions": "Exclusions",
                "insuredMembers": "Insured Members",
                "waitingPeriods": "Waiting Periods",
                "subLimits": "Sub-Limits",
                "premiumNcb": "Premium & NCB",
                "declaredPed": "Declared Pre-existing Diseases",
                "vehicleDetails": "Vehicle Details",
                "ownerDetails": "Owner Details",
                "ncb": "No Claim Bonus",
                "addOnCovers": "Add-On Covers",
                "premiumBreakdown": "Premium Breakdown",
                "tripDetails": "Trip Details",
                "travellerDetails": "Traveller Details",
                "coverageSummary": "Coverage Summary",
                "emergencyContacts": "Emergency Contacts",
                "insuredEntity": "Insured Entity",
                "propertyCoverage": "Property Coverage",
                "perilsCovered": "Perils Covered",
                "liabilityCoverage": "Liability Coverage",
                "businessInterruption": "Business Interruption",
                "premium": "Premium Details",
                "keyExclusions": "Key Exclusions",
                "farmerDetails": "Farmer Details",
                "landCropDetails": "Land & Crop Details",
                "risksCovered": "Risks Covered",
                "claimProcess": "Claim Process",
                # Health Insurance - Additional Sections for Eazr Health
                "noClaimBonus": "No Claim Bonus",
                "addOnPolicies": "Add-On Policies",
                "benefits": "Benefits & Features",
                "accumulatedBenefits": "Accumulated Benefits",
                "membersCovered": "Members Covered",
                "policyHistory": "Policy History",
                "networkInfo": "Network Hospital Information",
                "claimInfo": "Claim Information"
            }

            # Field label mappings (snake_case/camelCase to display labels)
            field_labels = {
                # Common fields
                "policyNumber": "Policy Number",
                "uin": "UIN",
                "productName": "Product Name",
                "policyType": "Policy Type",
                "insurerName": "Insurance Company",
                "policyIssueDate": "Issue Date",
                "policyStatus": "Policy Status",
                "policyPeriod": "Policy Period",
                "tpaName": "TPA Name",
                # Life Insurance
                "policyholderName": "Policyholder Name",
                "policyholderDob": "Date of Birth",
                "policyholderAge": "Age",
                "policyholderGender": "Gender",
                "lifeAssuredName": "Life Assured Name",
                "lifeAssuredDob": "Life Assured DOB",
                "lifeAssuredAge": "Life Assured Age",
                "relationshipWithPolicyholder": "Relationship",
                "sumAssured": "Sum Assured",
                "coverType": "Cover Type",
                "policyTerm": "Policy Term",
                "premiumPayingTerm": "Premium Paying Term",
                "maturityDate": "Maturity Date",
                "deathBenefit": "Death Benefit",
                "premiumAmount": "Premium Amount",
                "premiumFrequency": "Premium Frequency",
                "premiumDueDate": "Premium Due Date",
                "gracePeriod": "Grace Period",
                "modalPremiumBreakdown": "Modal Premium",
                "bonusType": "Bonus Type",
                "declaredBonusRate": "Declared Bonus Rate",
                "accruedBonus": "Accrued Bonus",
                "surrenderValue": "Surrender Value",
                "paidUpValue": "Paid-up Value",
                "loanValue": "Loan Value",
                "fundOptions": "Fund Options",
                "currentNav": "Current NAV",
                "unitsHeld": "Units Held",
                "fundValue": "Fund Value",
                "switchOptions": "Switch Options",
                "partialWithdrawal": "Partial Withdrawal",
                "nominees": "Nominees",
                "appointeeName": "Appointee Name",
                "appointeeRelationship": "Appointee Relationship",
                "revivalPeriod": "Revival Period",
                "freelookPeriod": "Free Look Period",
                "policyLoanInterestRate": "Loan Interest Rate",
                "autoPayMode": "Auto Pay Mode",
                "suicideClause": "Suicide Clause",
                "otherExclusions": "Other Exclusions",
                # Health Insurance
                "sumInsured": "Sum Insured",
                "roomRentLimit": "Room Rent Limit",
                "roomRentCopay": "Room Rent Copay",
                "icuLimit": "ICU Limit",
                "icuDailyLimit": "ICU Daily Limit",
                "preHospitalization": "Pre-Hospitalization",
                "postHospitalization": "Post-Hospitalization",
                "dayCareProcedures": "Day Care Procedures",
                "domiciliaryHospitalization": "Domiciliary Hospitalization",
                "ambulanceCover": "Ambulance Cover",
                "healthCheckup": "Health Checkup",
                "ayushTreatment": "AYUSH Treatment",
                "organDonor": "Organ Donor Cover",
                "restoration": "Restoration Benefit",
                "restorationAmount": "Restoration Amount",
                "modernTreatment": "Modern Treatment",
                "dailyCashAllowance": "Daily Cash Allowance",
                "convalescenceBenefit": "Convalescence Benefit",
                "initialWaitingPeriod": "Initial Waiting Period",
                "preExistingDiseaseWaiting": "Pre-existing Disease Waiting",
                "specificDiseaseWaiting": "Specific Disease Waiting",
                "maternityWaiting": "Maternity Waiting",
                "accidentCoveredFromDay1": "Accident Covered From Day 1",
                "specificDiseasesList": "Specific Diseases List",
                "cataractLimit": "Cataract Limit",
                "jointReplacementLimit": "Joint Replacement Limit",
                "internalProsthesisLimit": "Internal Prosthesis Limit",
                "kidneyStoneLimit": "Kidney Stone Limit",
                "gallStoneLimit": "Gall Stone Limit",
                "modernTreatmentLimit": "Modern Treatment Limit",
                "otherSubLimits": "Other Sub-Limits",
                "permanentExclusions": "Permanent Exclusions",
                "conditionalExclusions": "Conditional Exclusions",
                "preExistingConditions": "Pre-Existing Conditions",
                "basePremium": "Base Premium",
                "gst": "GST",
                "totalPremium": "Total Premium",
                "premiumFrequency": "Premium Frequency",
                "careShieldPremium": "Care Shield Premium",
                "internationalCoveragePremium": "International Coverage Premium",
                "universalShieldPremium": "Universal Shield Premium",
                "covidCarePremium": "Covid Care Premium",
                "otherAddOnPremiums": "Other Add-On Premiums",
                "premiumBreakdownDetails": "Premium Breakdown Details",
                "ncbPercentage": "NCB Percentage",
                "ncbProtect": "NCB Protect",
                "ncbBoost": "NCB Boost",
                "currentNcbPercentage": "Current NCB %",
                "accumulatedNcbPercentage": "Accumulated NCB %",
                "maxNcbPercentage": "Max NCB %",
                "ncbAmount": "NCB Amount",
                "declaredConditions": "Declared Conditions",
                "pedWaitingPeriodCompleted": "PED Waiting Period Completed",
                "pedStatus": "PED Status",
                "hasAddOn": "Has Add-On",
                "addOnPoliciesList": "Add-On Policies List",
                "claimShield": "Claim Shield",
                "ncbShield": "NCB Shield",
                "inflationShield": "Inflation Shield",
                "insurerRegistrationNumber": "Insurer Registration Number",
                "insurerAddress": "Insurer Address",
                "insurerTollFree": "Insurer Toll Free",
                "intermediaryName": "Intermediary Name",
                "intermediaryCode": "Intermediary Code",
                "intermediaryEmail": "Intermediary Email",
                "policyPeriodStart": "Policy Period Start",
                "policyPeriodEnd": "Policy Period End",
                "networkHospitalsCount": "Network Hospitals Count",
                "cashlessFacility": "Cashless Facility",
                "networkType": "Network Type",
                "claimSettlementRatio": "Claim Settlement Ratio",
                "claimProcess": "Claim Process",
                "claimIntimation": "Claim Intimation",
                "claimDocuments": "Claim Documents",
                "portability": "Portability",
                "waitingPeriodCredit": "Waiting Period Credit",
                # Motor Insurance
                "certificateNumber": "Certificate Number",
                "coverNoteNumber": "Cover Note Number",
                "productType": "Product Type",
                "previousPolicyNumber": "Previous Policy Number",
                "registrationNumber": "Registration Number",
                "vehicleClass": "Vehicle Class",
                "vehicleMake": "Vehicle Make",
                "vehicleModel": "Vehicle Model",
                "vehicleVariant": "Vehicle Variant",
                "manufacturingYear": "Manufacturing Year",
                "registrationDate": "Registration Date",
                "engineNumber": "Engine Number",
                "chassisNumber": "Chassis Number",
                "fuelType": "Fuel Type",
                "cubicCapacity": "Cubic Capacity",
                "seatingCapacity": "Seating Capacity",
                "vehicleColor": "Vehicle Color",
                "rtoLocation": "RTO Location",
                "hypothecation": "Hypothecation",
                "ownerName": "Owner Name",
                "ownerAddress": "Owner Address",
                "ownerContact": "Contact Number",
                "ownerEmail": "Email",
                "idv": "IDV (Insured Declared Value)",
                "odPremium": "OD Premium",
                "tpPremium": "TP Premium",
                "paOwnerCover": "PA Owner Cover",
                "paPaidDriver": "PA Paid Driver",
                "llPaidDriver": "LL Paid Driver",
                "llEmployees": "LL Employees",
                "tppdCover": "TPPD Cover",
                "ncbProtection": "NCB Protection",
                "ncbDeclaration": "NCB Declaration",
                "zeroDepreciation": "Zero Depreciation",
                "engineProtection": "Engine Protection",
                "returnToInvoice": "Return to Invoice",
                "roadsideAssistance": "Roadside Assistance",
                "consumables": "Consumables Cover",
                "tyreCover": "Tyre Cover",
                "keyCover": "Key Cover",
                "emiBreakerCover": "EMI Breaker Cover",
                "passengerCover": "Passenger Cover",
                "passengerCoverAmount": "Passenger Cover Amount",
                "basicOdPremium": "Basic OD Premium",
                "ncbDiscount": "NCB Discount",
                "addOnPremium": "Add-on Premium",
                # Travel Insurance
                "tripType": "Trip Type",
                "travelType": "Travel Type",
                "tripStartDate": "Trip Start Date",
                "tripEndDate": "Trip End Date",
                "tripDuration": "Trip Duration",
                "destinationCountries": "Destination Countries",
                "originCountry": "Origin Country",
                "purposeOfTravel": "Purpose of Travel",
                "medicalExpenses": "Medical Expenses",
                "emergencyMedicalEvacuation": "Emergency Medical Evacuation",
                "repatriationOfRemains": "Repatriation of Remains",
                "tripCancellation": "Trip Cancellation",
                "tripInterruption": "Trip Interruption",
                "flightDelay": "Flight Delay",
                "baggageLoss": "Baggage Loss",
                "baggageDelay": "Baggage Delay",
                "passportLoss": "Passport Loss",
                "personalLiability": "Personal Liability",
                "accidentalDeath": "Accidental Death",
                "permanentDisability": "Permanent Disability",
                "hijackDistress": "Hijack Distress",
                "homeburglary": "Home Burglary",
                "adventureSportsExclusion": "Adventure Sports Exclusion",
                "preExistingConditionExclusion": "Pre-existing Condition Exclusion",
                "emergencyHelpline24x7": "24x7 Emergency Helpline",
                "claimsEmail": "Claims Email",
                "insurerAddress": "Insurer Address",
                # Business Insurance
                "businessName": "Business Name",
                "businessType": "Business Type",
                "businessNature": "Nature of Business",
                "gstNumber": "GST Number",
                "cinNumber": "CIN Number",
                "businessAddress": "Business Address",
                "contactPerson": "Contact Person",
                "contactNumber": "Contact Number",
                "contactEmail": "Contact Email",
                "buildingValue": "Building Value",
                "plantMachineryValue": "Plant & Machinery Value",
                "stocksValue": "Stocks Value",
                "furnitureFixturesValue": "Furniture & Fixtures Value",
                "electricalInstallationsValue": "Electrical Installations Value",
                "otherContentsValue": "Other Contents Value",
                "totalPropertyValue": "Total Property Value",
                "fire": "Fire",
                "lightning": "Lightning",
                "explosion": "Explosion",
                "riot": "Riot",
                "earthquake": "Earthquake",
                "flood": "Flood",
                "storm": "Storm",
                "burglary": "Burglary",
                "terrorism": "Terrorism",
                "additionalPerils": "Additional Perils",
                "publicLiability": "Public Liability",
                "productLiability": "Product Liability",
                "professionalIndemnity": "Professional Indemnity",
                "employersLiability": "Employers Liability",
                "directorsOfficersLiability": "D&O Liability",
                "cyberLiability": "Cyber Liability",
                "businessInterruptionCover": "BI Cover",
                "grossProfitInsured": "Gross Profit Insured",
                "indemnityPeriod": "Indemnity Period",
                "alternativePremises": "Alternative Premises",
                "propertyPremium": "Property Premium",
                "liabilityPremium": "Liability Premium",
                "biPremium": "BI Premium",
                "warExclusion": "War Exclusion",
                "wearTearExclusion": "Wear & Tear Exclusion",
                # Agriculture Insurance
                "schemeName": "Scheme Name",
                "seasonYear": "Season/Year",
                "farmerName": "Farmer Name",
                "farmerType": "Farmer Type",
                "farmerCategory": "Farmer Category",
                "farmerMobile": "Mobile Number",
                "farmerAddress": "Address",
                "farmerAadhaar": "Aadhaar Number",
                "bankName": "Bank Name",
                "bankAccountNumber": "Account Number",
                "ifscCode": "IFSC Code",
                "surveyNumbers": "Survey Numbers",
                "villageOrGramPanchayat": "Village/Gram Panchayat",
                "blockTalukaOrTehsil": "Block/Taluka/Tehsil",
                "district": "District",
                "state": "State",
                "totalAreaInsured": "Total Area Insured",
                "cropName": "Crop Name",
                "cropCode": "Crop Code",
                "cropType": "Crop Type",
                "sumInsuredPerHectare": "Sum Insured Per Hectare",
                "totalSumInsured": "Total Sum Insured",
                "premiumRateFarmer": "Premium Rate (Farmer)",
                "premiumRateGov": "Premium Rate (Govt)",
                "farmerPremiumAmount": "Farmer Premium Amount",
                "govSubsidyAmount": "Govt Subsidy Amount",
                "preventedSowing": "Prevented Sowing",
                "midSeasonAdversity": "Mid-Season Adversity",
                "localizedCalamity": "Localized Calamity",
                "postHarvestLosses": "Post-Harvest Losses",
                "wildAnimalAttack": "Wild Animal Attack",
                "addOnCovers": "Add-on Covers",
                "farmerSharePremium": "Farmer Share Premium",
                "stateSharePremium": "State Share Premium",
                "centralSharePremium": "Central Share Premium",
                "premiumPaidDate": "Premium Paid Date",
                "claimIntimationPeriod": "Claim Intimation Period",
                "claimIntimationMethod": "Claim Intimation Method",
                "yieldBasedAssessment": "Yield Based Assessment",
                "cropCuttingExperiments": "Crop Cutting Experiments",
                "thresholdYield": "Threshold Yield",
                "willfulDamage": "Willful Damage"
            }

            def get_value_type(value, field_id: str = "") -> str:
                """
                Determine the value type for frontend rendering.
                Uses field context (field_id) to make smarter decisions about value types.
                """
                import re

                if value is None:
                    return "null"
                if isinstance(value, bool):
                    return "boolean"
                if isinstance(value, (int, float)):
                    return "number"
                if isinstance(value, list):
                    return "array"
                if isinstance(value, dict):
                    return "object"

                # For string values, use field context to determine type
                str_val = str(value).lower()
                field_lower = field_id.lower()

                # ===== FIELD CONTEXT AWARE TYPE DETECTION =====
                # This prevents false positives from pattern matching

                # 1. Fields that should ALWAYS be strings (text/descriptions)
                string_fields = {
                    "productname", "policytype", "insurername", "insureraddress",
                    "intermediaryname", "intermediarycode", "intermediaryemail",
                    "covertype", "roomrentlimit", "iculimit", "ambulancecover",
                    "healthcheckup", "restorationamount", "moderntreatmentlimit",
                    "claimprocess", "claimintimation", "networktype",
                    "maxncbpercentage", "ncbpercentage", "percentage",
                    "totalpremium", "premiumfrequency", "policystatus",
                    "claimsettlementratio", "networkhospitalscount",
                    "policyperiod", "tpaname",
                    # Member fields
                    "membername", "memberrelationship", "membergender",
                    # Address/location fields
                    "address", "location", "area", "city", "state", "pin", "zip",
                    # Code/ID fields that aren't dates
                    "uin", "registrationnumber", "certificatenumber", "chassisnumber",
                    "enginenumber", "policynumber", "covernotenumber", "rto",
                    # Text description fields
                    "description", "notes", "remarks", "terms", "conditions",
                }

                # 2. Fields that should ALWAYS be dates
                date_fields = {
                    "policyissuedate", "policystartdate", "policyenddate",
                    "policystart", "policyend", "policyperiodstart", "policyperiodend",
                    "issuancedate", "maturitydate", "startdate", "enddate",
                    "dateofbirth", "dob", "registrationdate", "manufacturingyear",
                    "tripstartdate", "tripenddate", "firstenrollmentdate",
                    "insuredsincedate", "premiumpaiddate",
                    # Date fields with common suffixes
                    "date", "dob", "joining", "enrollment",
                }

                # 3. Fields that should ALWAYS be email
                email_fields = {
                    "email", "emailid", "intermediaryemail", "contactemail",
                    "claimsemail", "useremail",
                }

                # 4. Fields that should ALWAYS be phone
                phone_fields = {
                    "phone", "mobile", "contact", "contactnumber", "tollfree",
                    "insurertollfree", "ownercontact", "contactno", "helpline",
                }

                # 5. Fields that should be currency (contain ₹ symbol but not just text)
                # These need the currency symbol to be classified as currency
                # Don't auto-detect based on field name alone

                # Check field context first (more reliable than pattern matching)
                if any(field in field_lower for field in string_fields):
                    return "string"

                if any(field in field_lower for field in date_fields):
                    return "date"

                if any(field in field_lower for field in email_fields):
                    return "email"

                if any(field in field_lower for field in phone_fields):
                    return "phone"

                # ===== PATTERN MATCHING FALLBACK (for unknown fields) =====
                # Only use pattern matching if field context doesn't give us a clear answer

                # Currency: Must have explicit currency symbol
                if any(symbol in str_val for symbol in ["₹", "€", "£", "¥", "$"]):
                    # But avoid false positives - "rs" appears in many words
                    # Only trigger if symbol is present or explicit currency format
                    if any(symbol in str_val for symbol in ["₹", "€", "£", "¥", "$"]):
                        return "currency"
                    # Don't match "rs" alone - too many false positives (e.g., "Policy", "Person")

                # Date: require actual date-like pattern (DD/MM/YYYY, YYYY-MM-DD, etc.)
                # Avoid policy numbers like "DCOR00832176202/00", codes like "IRDAI/DB/885/2024"
                if re.search(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}', str(value)):
                    return "date"

                # Email pattern
                if "@" in str_val and "." in str_val.split("@")[-1]:
                    return "email"

                # Phone pattern — require separators or Indian phone prefixes
                # Pure digit strings (like policy numbers, customer IDs) should NOT match
                if re.match(r'^[\d\s\-\+\(\)]{10,}$', str(value)):
                    raw_val = str(value)
                    has_separator = any(c in raw_val for c in [' ', '-', '+', '(', ')'])
                    if has_separator:
                        return "phone"
                    # Pure digits: only classify as phone if starts with Indian phone prefix
                    if re.match(r'^[6-9]\d{9}$', raw_val) or re.match(r'^(1800|1860)\d{6,}$', raw_val):
                        return "phone"

                # Default to string
                return "string"

            def format_value(value):
                """Format value for display"""
                if value is None:
                    return None
                if isinstance(value, bool):
                    return "Yes" if value else "No"
                if isinstance(value, list):
                    if len(value) == 0:
                        return None
                    # For list of strings, join them
                    if all(isinstance(item, str) for item in value):
                        return value  # Keep as array for frontend
                    return value
                return value

            def build_fields(data: dict, parent_key: str = "") -> list:
                """Build fields array from a dictionary"""
                fields = []
                field_order = 0
                for key, value in data.items():
                    if value is None or value == "" or value == []:
                        continue  # Skip empty values

                    formatted_value = format_value(value)
                    if formatted_value is None:
                        continue

                    field_id = f"{parent_key}_{key}" if parent_key else key
                    label = field_labels.get(key, key.replace("_", " ").replace("camelCase", " ").title())

                    # Handle nested objects
                    if isinstance(value, dict) and not isinstance(formatted_value, (str, int, float, bool, list)):
                        # Flatten nested object into fields
                        nested_fields = build_fields(value, key)
                        fields.extend(nested_fields)
                    else:
                        fields.append({
                            "fieldId": field_id,
                            "label": label,
                            "value": formatted_value,
                            "valueType": get_value_type(value, key),
                            "displayOrder": field_order
                        })
                        field_order += 1

                return fields

            # Build sections from category data
            for section_key, section_data in category_data.items():
                if section_data is None:
                    continue

                section_order += 1
                section_title = section_titles.get(section_key, section_key.replace("_", " ").title())

                # Determine section type
                if isinstance(section_data, list):
                    section_type = "list"
                    # For list sections (like insuredMembers, riders)
                    items = []
                    for idx, item in enumerate(section_data):
                        if isinstance(item, dict):
                            item_fields = build_fields(item, f"{section_key}_{idx}")
                            items.append({
                                "itemId": f"{section_key}_item_{idx}",
                                "fields": item_fields
                            })
                        elif isinstance(item, str):
                            items.append({
                                "itemId": f"{section_key}_item_{idx}",
                                "value": item
                            })

                    if items:  # Only add section if it has items
                        sections.append({
                            "sectionId": section_key,
                            "sectionTitle": section_title,
                            "sectionType": section_type,
                            "displayOrder": section_order,
                            "items": items
                        })
                elif isinstance(section_data, dict):
                    section_type = "fields"
                    fields = build_fields(section_data, section_key)

                    if fields:  # Only add section if it has fields
                        sections.append({
                            "sectionId": section_key,
                            "sectionTitle": section_title,
                            "sectionType": section_type,
                            "displayOrder": section_order,
                            "fields": fields
                        })
                else:
                    # Simple value section
                    section_type = "value"
                    sections.append({
                        "sectionId": section_key,
                        "sectionTitle": section_title,
                        "sectionType": section_type,
                        "displayOrder": section_order,
                        "value": section_data,
                        "valueType": get_value_type(section_data, section_key)
                    })

            return sections

        # Build unified sections from category-specific data
        unified_sections = build_unified_sections(complete_category_data, detected_policy_type)

        # ==================== VALIDATION & QUALITY CHECKS ====================
        # Run validation checks on extracted data

        # 1. Detect redundant add-ons (waiting period waivers when no waiting period exists)
        redundant_addon_analysis = detect_redundant_addons(complete_category_data, detected_policy_type)

        if redundant_addon_analysis.get("hasRedundantAddons"):
            logger.warning(f"⚠️ Found {len(redundant_addon_analysis['redundantAddons'])} redundant add-ons totaling {redundant_addon_analysis['totalWastedFormatted']}")

        # 2. Validate policy data for inconsistencies
        data_validation = validate_policy_data(complete_category_data, detected_policy_type)

        if data_validation.get("hasErrors"):
            logger.error(f"❌ Found {len(data_validation['errors'])} validation errors in policy data")

        if data_validation.get("hasWarnings"):
            logger.warning(f"⚠️ Found {len(data_validation['warnings'])} validation warnings in policy data")

        # ==================== DEEP ANALYSIS BUILDER (EAZR Policy Intelligence Report V4.0) ====================
        # Build category-specific deep analysis sections based on EAZR Policy Intelligence Report templates

        def build_deep_analysis(policy_type: str, extracted_data: dict, category_data: dict,
                                 formatted_gaps: list, protection_score: int, protection_score_label: str,
                                 key_benefits: list, exclusions_list: list, waiting_periods_list: list,
                                 user_name: str, user_age: int, user_gender: str) -> dict:
            """
            Build comprehensive deep analysis based on EAZR Policy Intelligence Report V4.0 templates.
            Returns category-specific analysis sections.
            """
            analysis = {
                "reportVersion": "4.0",
                "analysisType": policy_type.upper() if policy_type else "GENERAL",
                "sections": []
            }

            # Common helper functions
            def create_section(section_id: str, title: str, subtitle: str, display_order: int, content: dict) -> dict:
                return {
                    "sectionId": section_id,
                    "sectionTitle": title,
                    "sectionSubtitle": subtitle,
                    "displayOrder": display_order,
                    "content": content
                }

            def calculate_coverage_adequacy(coverage_amount: int, annual_income: int = 500000) -> dict:
                """Calculate coverage adequacy based on standard financial planning principles"""
                recommended_min = annual_income * 10
                recommended_max = annual_income * 15
                gap = max(0, recommended_min - coverage_amount)
                adequacy_score = min(10, int((coverage_amount / recommended_min) * 10)) if recommended_min > 0 else 5

                if coverage_amount >= recommended_max:
                    level = "Excellent"
                elif coverage_amount >= recommended_min:
                    level = "Adequate"
                elif coverage_amount >= recommended_min * 0.7:
                    level = "Building"
                else:
                    level = "Needs Attention"

                return {
                    "coverageAmount": coverage_amount,
                    "recommendedMinimum": recommended_min,
                    "recommendedMaximum": recommended_max,
                    "coverageGap": gap,
                    "adequacyScore": adequacy_score,
                    "adequacyLevel": level
                }

            # Get common data - safely convert to numeric
            coverage_amount_raw = extracted_data.get("coverageAmount", 0) or 0
            premium_raw = extracted_data.get("premium", 0) or 0

            try:
                coverage_amount = int(float(str(coverage_amount_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if coverage_amount_raw else 0
            except (ValueError, TypeError):
                coverage_amount = 0

            try:
                premium = int(float(str(premium_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if premium_raw else 0
            except (ValueError, TypeError):
                premium = 0

            start_date = extracted_data.get("startDate", "")
            end_date = extracted_data.get("endDate", "")

            # ==================== LIFE INSURANCE ANALYSIS ====================
            if "life" in policy_type or "term" in policy_type or "endowment" in policy_type or "ulip" in policy_type:
                # Section 1: Your Protection at a Glance
                sum_assured_raw = category_data.get("coverageDetails", {}).get("sumAssured") or coverage_amount
                bonus_accumulated_raw = category_data.get("bonusValue", {}).get("accruedBonus") or 0

                # Convert to numeric (handle string values)
                try:
                    sum_assured = int(float(str(sum_assured_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if sum_assured_raw else 0
                except (ValueError, TypeError):
                    sum_assured = 0

                try:
                    bonus_accumulated = int(float(str(bonus_accumulated_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if bonus_accumulated_raw else 0
                except (ValueError, TypeError):
                    bonus_accumulated = 0

                rider_benefits = 0
                riders = category_data.get("riders", [])
                if isinstance(riders, list):
                    for rider in riders:
                        if isinstance(rider, dict):
                            rider_raw = rider.get("sumAssured", 0) or 0
                            try:
                                rider_benefits += int(float(str(rider_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if rider_raw else 0
                            except (ValueError, TypeError):
                                pass

                net_death_benefit = sum_assured + bonus_accumulated + rider_benefits
                coverage_adequacy = calculate_coverage_adequacy(sum_assured)

                analysis["sections"].append(create_section(
                    "protection_at_glance",
                    "Your Protection at a Glance",
                    "What your policy provides and how it compares to what your family would need",
                    1,
                    {
                        "protectionSummary": {
                            "title": "Policy Protection Summary",
                            "items": [
                                {"label": "Sum Assured", "value": sum_assured, "description": "The guaranteed amount your nominee receives"},
                                {"label": "Bonus Accumulated", "value": bonus_accumulated, "description": "Additional amount built up over time"},
                                {"label": "Rider Benefits", "value": rider_benefits, "description": "Extra protection for accidents, illness, etc."},
                                {"label": "Net Death Benefit", "value": net_death_benefit, "description": "Total amount payable to your family", "highlight": True}
                            ]
                        },
                        "protectionAdequacy": {
                            "title": "Protection Adequacy",
                            "description": "Based on standard financial planning principles (10-15x annual income)",
                            "currentCover": sum_assured,
                            "recommendedCover": f"{coverage_adequacy['recommendedMinimum']} - {coverage_adequacy['recommendedMaximum']}",
                            "coverageGap": coverage_adequacy["coverageGap"],
                            "protectionLevel": coverage_adequacy["adequacyScore"],
                            "protectionStatus": coverage_adequacy["adequacyLevel"]
                        }
                    }
                ))

                # Section 2: Policy Reliability
                policy_age_years = 0
                if start_date:
                    try:
                        from datetime import datetime
                        start = datetime.strptime(start_date.split("T")[0], "%Y-%m-%d")
                        policy_age_years = (datetime.now() - start).days // 365
                    except:
                        pass

                contestability_complete = policy_age_years >= 2
                nomination_status = "Valid" if category_data.get("nomination", {}).get("nominees") else "Needs update"
                policy_assignment = category_data.get("policyIdentification", {}).get("hypothecation") or "None"

                analysis["sections"].append(create_section(
                    "policy_reliability",
                    "Policy Reliability",
                    "Factors that determine how smoothly a claim would be processed",
                    2,
                    {
                        "claimReadinessStatus": {
                            "title": "Claim Readiness Status",
                            "factors": [
                                {
                                    "factor": "Contestability Period",
                                    "status": "Complete" if contestability_complete else f"{24 - (policy_age_years * 12)} months remaining",
                                    "impact": "Clear for claims" if contestability_complete else "Subject to verification"
                                },
                                {
                                    "factor": "Premium Status",
                                    "status": "Current",
                                    "impact": "Policy active"
                                },
                                {
                                    "factor": "Nomination",
                                    "status": nomination_status,
                                    "impact": "Smooth settlement" if nomination_status == "Valid" else "Potential delays"
                                },
                                {
                                    "factor": "Policy Assignment",
                                    "status": policy_assignment if policy_assignment != "None" else "None",
                                    "impact": "Full benefit to nominee" if policy_assignment == "None" else "Bank paid first"
                                }
                            ]
                        },
                        "policyAgeYears": policy_age_years,
                        "contestabilityComplete": contestability_complete
                    }
                ))

                # Section 3: Value Assessment
                policy_term = category_data.get("coverageDetails", {}).get("policyTerm")
                premium_frequency = extracted_data.get("premiumFrequency", "annually")
                annual_premium = premium
                if premium_frequency == "monthly":
                    annual_premium = premium * 12
                elif premium_frequency == "quarterly":
                    annual_premium = premium * 4
                elif premium_frequency == "half-yearly":
                    annual_premium = premium * 2

                premium_per_lakh = (annual_premium / (sum_assured / 100000)) if sum_assured > 0 else 0

                analysis["sections"].append(create_section(
                    "value_assessment",
                    "Value Assessment",
                    "Is this policy giving you good value for what you're paying?",
                    3,
                    {
                        "termInsuranceMetrics": {
                            "title": "For Term Insurance",
                            "metrics": [
                                {"metric": "Premium per Rs. 1 Lakh Cover", "yourPolicy": f"Rs. {int(premium_per_lakh)}/year", "marketBenchmark": "Rs. 500-800/year"},
                                {"metric": "Cost Efficiency", "yourPolicy": "Good" if premium_per_lakh < 800 else "Average" if premium_per_lakh < 1200 else "Review recommended"}
                            ]
                        },
                        "annualPremium": annual_premium,
                        "premiumPerLakh": premium_per_lakh
                    }
                ))

                # Section 4: What Needs Your Attention
                gaps_identified = []
                # Income Protection Gap
                if coverage_adequacy["coverageGap"] > 0:
                    gaps_identified.append({
                        "gap": "Income Protection",
                        "currentStatus": f"{int(sum_assured / 500000)}x annual income covered" if sum_assured > 0 else "Not covered",
                        "recommendation": f"Consider additional Rs. {coverage_adequacy['coverageGap']} term cover" if coverage_adequacy["coverageGap"] > 0 else "Adequate"
                    })

                # Critical Illness
                has_ci = any("critical" in str(r).lower() or "ci" in str(r).lower() for r in riders) if riders else False
                gaps_identified.append({
                    "gap": "Critical Illness",
                    "currentStatus": "Covered" if has_ci else "Not covered",
                    "recommendation": "Protected" if has_ci else "Consider CI rider"
                })

                # Add gaps from analysis
                for gap in formatted_gaps[:3]:
                    if isinstance(gap, dict):
                        gaps_identified.append({
                            "gap": gap.get("category", "Coverage Gap"),
                            "currentStatus": gap.get("severity", "medium").capitalize(),
                            "recommendation": gap.get("recommendation", "Review recommended")
                        })

                analysis["sections"].append(create_section(
                    "attention_needed",
                    "What Needs Your Attention",
                    "Areas that may benefit from review",
                    4,
                    {
                        "coverageGapsIdentified": {
                            "title": "Coverage Gaps Identified",
                            "gaps": gaps_identified
                        }
                    }
                ))

                # Section 5: Recommended Actions
                actions = []
                action_priority = 1
                for gap in formatted_gaps[:3]:
                    if isinstance(gap, dict):
                        actions.append({
                            "priority": action_priority,
                            "action": gap.get("recommendation", "Review coverage"),
                            "timeline": "At renewal" if gap.get("severity") != "high" else "Immediate",
                            "urgency": "Critical" if gap.get("severity") == "high" else "High" if gap.get("severity") == "medium" else "Medium"
                        })
                        action_priority += 1

                analysis["sections"].append(create_section(
                    "recommended_actions",
                    "Recommended Actions",
                    "Prioritized steps to strengthen your protection",
                    5,
                    {
                        "actions": actions,
                        "eazrServices": {
                            "title": "EAZR Can Help",
                            "services": [
                                {"service": "Premium Financing (IPF)", "eligibility": "Eligible" if annual_premium > 50000 else "Not eligible", "benefit": f"Convert Rs. {annual_premium} annual premium to EMI"},
                                {"service": "Surrender Value Loan (SVF)", "eligibility": "Eligible" if policy_age_years >= 3 else "Not eligible", "benefit": "Access funds without surrendering policy"}
                            ]
                        }
                    }
                ))

                # Section 6: Assessment
                if protection_score >= 80:
                    assessment_status = "WELL PROTECTED"
                elif protection_score >= 60:
                    assessment_status = "ADEQUATELY COVERED"
                else:
                    assessment_status = "ACTION RECOMMENDED"

                analysis["sections"].append(create_section(
                    "assessment",
                    "Assessment",
                    assessment_status,
                    6,
                    {
                        "status": assessment_status,
                        "keyFinding": f"Your coverage is {int(sum_assured / 500000)}x income. {'Contestability is clear and policy is well-maintained.' if contestability_complete else 'Policy is within contestability period.'}",
                        "recommendedAction": gaps_identified[0]["recommendation"] if gaps_identified else "Continue current coverage and review annually."
                    }
                ))

            # ==================== HEALTH INSURANCE ANALYSIS ====================
            elif "health" in policy_type or "mediclaim" in policy_type or "medical" in policy_type:
                # Safely convert to numeric values
                sum_insured_raw = category_data.get("coverageDetails", {}).get("sumInsured") or coverage_amount
                cumulative_bonus_raw = category_data.get("premiumNcb", {}).get("ncbPercentage") or 0

                # Convert to numeric (handle string values)
                try:
                    sum_insured = int(float(str(sum_insured_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if sum_insured_raw else 0
                except (ValueError, TypeError):
                    sum_insured = 0

                try:
                    cumulative_bonus = float(str(cumulative_bonus_raw).replace('%', '').strip()) if cumulative_bonus_raw else 0
                except (ValueError, TypeError):
                    cumulative_bonus = 0

                effective_coverage = sum_insured * (1 + cumulative_bonus / 100) if sum_insured > 0 else 0
                restoration = category_data.get("coverageDetails", {}).get("restoration")
                room_rent_limit = category_data.get("coverageDetails", {}).get("roomRentLimit") or "Not specified"

                # Section 1: Coverage Overview
                insured_members = category_data.get("insuredMembers", [])
                if not insured_members:
                    insured_members = [{"name": user_name, "age": user_age, "waitingPeriodStatus": "Check policy document"}]

                analysis["sections"].append(create_section(
                    "coverage_overview",
                    "Coverage Overview",
                    "What your policy actually covers when you need hospitalization",
                    1,
                    {
                        "coverageSummary": {
                            "title": "Your Coverage Summary",
                            "items": [
                                {"component": "Base Sum Insured", "value": f"Rs. {sum_insured:,}"},
                                {"component": "Cumulative Bonus", "value": f"Rs. {int(sum_insured * cumulative_bonus / 100):,} ({cumulative_bonus}%)" if cumulative_bonus else "Not accumulated yet"},
                                {"component": "Effective Coverage", "value": f"Rs. {int(effective_coverage):,}"},
                                {"component": "Restoration Benefit", "value": "Available - 100%" if restoration else "Not available"},
                                {"component": "Room Category", "value": str(room_rent_limit)}
                            ]
                        },
                        "familyMembersCovered": {
                            "title": "Family Members Covered",
                            "members": insured_members
                        }
                    }
                ))

                # Section 2: What You Actually Pay in a Claim
                room_rent_daily = 5000  # Default assumption
                if isinstance(room_rent_limit, str):
                    import re
                    match = re.search(r'(\d+,?\d*)', room_rent_limit.replace(',', ''))
                    if match:
                        room_rent_daily = int(match.group(1))

                co_payment_raw = category_data.get("coverageDetails", {}).get("coPayment") or 0
                deductible_raw = category_data.get("coverageDetails", {}).get("deductible") or 0

                # Convert to numeric (handle string values)
                try:
                    co_payment = float(str(co_payment_raw).replace('%', '').replace(',', '').strip()) if co_payment_raw else 0
                except (ValueError, TypeError):
                    co_payment = 0

                try:
                    deductible = float(str(deductible_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip()) if deductible_raw else 0
                except (ValueError, TypeError):
                    deductible = 0

                # Example calculation for Rs. 5 lakh bill
                example_bill = 500000
                room_adjustment = min(50000, example_bill * 0.1)  # Estimate 10% room adjustment
                co_pay_amount = example_bill * co_payment / 100 if co_payment else 0
                non_payable = example_bill * 0.05  # Estimate 5% non-payable
                insurer_pays = example_bill - room_adjustment - co_pay_amount - deductible - non_payable
                you_pay = example_bill - insurer_pays

                analysis["sections"].append(create_section(
                    "out_of_pocket",
                    "What You Actually Pay in a Claim",
                    "Health insurance rarely pays 100% of your hospital bill",
                    2,
                    {
                        "outOfPocketBreakdown": {
                            "title": f"If hospitalized with Rs. {example_bill:,} bill",
                            "items": [
                                {"item": "Hospital Bill", "amount": example_bill},
                                {"item": "(-) Room Rent Adjustment", "amount": -room_adjustment, "note": "if room exceeds limit"},
                                {"item": f"(-) Co-payment ({co_payment}%)", "amount": -co_pay_amount},
                                {"item": "(-) Deductible", "amount": -deductible},
                                {"item": "(-) Non-payable Items", "amount": -non_payable, "note": "consumables, etc."},
                                {"item": "Insurer Pays", "amount": insurer_pays, "highlight": True},
                                {"item": "You Pay from Pocket", "amount": you_pay, "highlight": True, "warning": you_pay > 50000}
                            ]
                        },
                        "roomRentImpact": {
                            "title": "Room Rent Impact",
                            "description": f"Your policy has a Rs. {room_rent_daily}/day room limit. If you choose a higher room, proportionate deduction applies to ALL charges.",
                            "warning": room_rent_daily < 10000
                        }
                    }
                ))

                # Section 3: Waiting Periods & Exclusions
                waiting_period_status = []
                initial_waiting = category_data.get("waitingPeriods", {}).get("initialWaitingPeriod") or "30 days"
                ped_waiting = category_data.get("waitingPeriods", {}).get("preExistingDiseaseWaiting") or "48 months"
                specific_waiting = category_data.get("waitingPeriods", {}).get("specificDiseaseWaiting") or "24 months"
                maternity_waiting = category_data.get("waitingPeriods", {}).get("maternityWaiting")

                # Calculate if waiting periods are complete based on policy start date
                policy_months = 0
                if start_date:
                    try:
                        start = datetime.strptime(start_date.split("T")[0], "%Y-%m-%d")
                        policy_months = (datetime.now() - start).days // 30
                    except:
                        pass

                waiting_period_status = [
                    {"condition": "General Illnesses", "waitingPeriod": "30 days", "status": "Complete ✓" if policy_months > 1 else "Active"},
                    {"condition": "Pre-existing Diseases", "waitingPeriod": ped_waiting, "status": "Complete ✓" if policy_months > 48 else f"{48 - policy_months} months left"},
                    {"condition": "Specific Diseases", "waitingPeriod": specific_waiting, "status": "Complete ✓" if policy_months > 24 else f"{24 - policy_months} months left"}
                ]
                if maternity_waiting:
                    waiting_period_status.append({"condition": "Maternity", "waitingPeriod": maternity_waiting, "status": "Check policy"})

                analysis["sections"].append(create_section(
                    "waiting_periods_exclusions",
                    "Waiting Periods & Exclusions",
                    "Conditions that affect when and what you can claim",
                    3,
                    {
                        "waitingPeriodStatus": {
                            "title": "Current Waiting Period Status",
                            "periods": waiting_period_status
                        },
                        "exclusions": {
                            "title": "Policy Exclusions",
                            "permanentExclusions": category_data.get("exclusions", {}).get("permanentExclusions") or exclusions_list[:5],
                            "conditionalExclusions": category_data.get("exclusions", {}).get("conditionalExclusions") or []
                        }
                    }
                ))

                # Section 4: Major Illness Preparedness
                critical_scenarios = [
                    {"scenario": "Heart Surgery (CABG)", "typicalCost": "Rs. 4-8 Lakhs", "yourCoverage": f"Rs. {sum_insured:,}", "gap": "Covered" if sum_insured >= 800000 else f"Gap: Rs. {800000 - sum_insured:,}"},
                    {"scenario": "Cancer Treatment (over 2 years)", "typicalCost": "Rs. 15-30 Lakhs", "yourCoverage": f"Rs. {sum_insured:,}", "gap": "Covered" if sum_insured >= 1500000 else f"Gap: Rs. {1500000 - sum_insured:,}"},
                    {"scenario": "Kidney Transplant", "typicalCost": "Rs. 8-15 Lakhs", "yourCoverage": f"Rs. {sum_insured:,}", "gap": "Covered" if sum_insured >= 800000 else f"Gap: Rs. {800000 - sum_insured:,}"},
                    {"scenario": "Major Accident (ICU + Surgery)", "typicalCost": "Rs. 10-20 Lakhs", "yourCoverage": f"Rs. {sum_insured:,}", "gap": "Covered" if sum_insured >= 1000000 else f"Gap: Rs. {1000000 - sum_insured:,}"}
                ]

                analysis["sections"].append(create_section(
                    "major_illness_preparedness",
                    "Major Illness Preparedness",
                    "How well does your policy handle serious health events",
                    4,
                    {
                        "coverageAdequacy": {
                            "title": "Coverage Adequacy for Critical Scenarios",
                            "scenarios": critical_scenarios,
                            "note": "Major illnesses often require multiple hospitalizations. With restoration benefit, your cover resets after each claim."
                        },
                        "hasRestoration": restoration is not None
                    }
                ))

                # Section 5: Improvement Opportunities
                improvement_gaps = []
                if room_rent_daily < 10000:
                    improvement_gaps.append({"gap": "Room rent limit", "impact": "Higher out-of-pocket in good hospitals", "solution": "Consider upgrade to no-limit plan at renewal"})
                if co_payment > 0:
                    improvement_gaps.append({"gap": f"{co_payment}% Co-payment", "impact": f"Pay {co_payment}% of every claim yourself", "solution": "Port to zero co-pay plan"})
                if not restoration:
                    improvement_gaps.append({"gap": "No restoration", "impact": "Second illness in same year = no cover", "solution": "Upgrade to plan with restoration"})
                if sum_insured < 1000000:
                    improvement_gaps.append({"gap": "Sum insured < Rs. 10L", "impact": "Major illness exhausts cover", "solution": "Add Super Top-up of Rs. 50L-1Cr"})

                analysis["sections"].append(create_section(
                    "improvement_opportunities",
                    "Improvement Opportunities",
                    "Areas where your coverage could be strengthened",
                    5,
                    {
                        "gaps": improvement_gaps,
                        "superTopUpOpportunity": {
                            "title": "Super Top-Up Opportunity",
                            "description": f"A Super Top-up of Rs. 1 Crore with Rs. {sum_insured} deductible costs only Rs. 5,000-12,000/year.",
                            "recommended": sum_insured < 2000000
                        }
                    }
                ))

                # Section 6: Recommended Actions
                actions = []
                if end_date:
                    actions.append({"priority": 1, "action": f"Renew before {end_date} to maintain NCB and waiting period credits", "timeline": "Before expiry", "urgency": "Critical"})

                for idx, gap in enumerate(improvement_gaps[:2]):
                    actions.append({"priority": idx + 2, "action": gap["solution"], "timeline": "At renewal", "urgency": "High"})

                analysis["sections"].append(create_section(
                    "recommended_actions",
                    "Recommended Actions",
                    "Prioritized steps to strengthen your coverage",
                    6,
                    {
                        "actions": actions,
                        "importantInfo": {
                            "title": "Know Before You're Hospitalized",
                            "items": [
                                {"info": "Room rent limit", "detail": str(room_rent_limit)},
                                {"info": "TPA Helpline", "detail": "Check policy document"},
                                {"info": "Claim Intimation Deadline", "detail": "Within 24 hours of admission"}
                            ]
                        }
                    }
                ))

                # Section 7: Assessment
                if sum_insured >= 1000000 and restoration and co_payment == 0:
                    assessment_status = "COMPREHENSIVE COVER"
                elif sum_insured >= 500000:
                    assessment_status = "ADEQUATE WITH GAPS"
                else:
                    assessment_status = "NEEDS ENHANCEMENT"

                analysis["sections"].append(create_section(
                    "assessment",
                    "Assessment",
                    assessment_status,
                    7,
                    {
                        "status": assessment_status,
                        "keyFinding": f"Coverage of Rs. {sum_insured:,} is {'adequate for routine hospitalization' if sum_insured >= 500000 else 'limited'}. {'Has restoration benefit.' if restoration else 'No restoration benefit - consider adding.'}",
                        "recommendedAction": improvement_gaps[0]["solution"] if improvement_gaps else "Maintain current coverage and review at renewal."
                    }
                ))

            # ==================== MOTOR INSURANCE ANALYSIS ====================
            elif "motor" in policy_type or "car" in policy_type or "vehicle" in policy_type or "auto" in policy_type or "bike" in policy_type:
                idv_raw = category_data.get("coverageDetails", {}).get("idv") or coverage_amount
                ncb_percentage_raw = category_data.get("ncb", {}).get("ncbPercentage") or 0

                # Convert to numeric (handle string values)
                try:
                    idv = int(float(str(idv_raw).replace(',', '').replace('Rs.', '').replace('Rs', '').strip())) if idv_raw else 0
                except (ValueError, TypeError):
                    idv = 0

                try:
                    ncb_percentage = float(str(ncb_percentage_raw).replace('%', '').strip()) if ncb_percentage_raw else 0
                except (ValueError, TypeError):
                    ncb_percentage = 0

                policy_type_motor = category_data.get("policyIdentification", {}).get("productType") or "Comprehensive"
                vehicle_details = category_data.get("vehicleDetails", {})

                # Section 1: Your Coverage Snapshot
                analysis["sections"].append(create_section(
                    "coverage_snapshot",
                    "Your Coverage Snapshot",
                    "Vehicle & Policy Details",
                    1,
                    {
                        "vehiclePolicyDetails": {
                            "title": "Vehicle & Policy Details",
                            "items": [
                                {"detail": "Vehicle", "value": f"{vehicle_details.get('vehicleMake', '')} {vehicle_details.get('vehicleModel', '')} — {vehicle_details.get('registrationNumber', '')}"},
                                {"detail": "Policy Type", "value": policy_type_motor},
                                {"detail": "IDV (Insured Value)", "value": f"Rs. {idv:,}" if idv else "Not specified"},
                                {"detail": "No Claim Bonus", "value": f"{ncb_percentage}%" if ncb_percentage else "0%"},
                                {"detail": "Policy Valid Until", "value": end_date or "Check policy"}
                            ]
                        },
                        "coverageBreakdown": {
                            "title": "Coverage Breakdown",
                            "coverages": [
                                {"type": "Own Damage (OD)", "limit": f"Up to IDV (Rs. {idv:,})" if idv else "Up to IDV", "status": "Covered" if "comprehensive" in policy_type_motor.lower() else "Not covered"},
                                {"type": "Third Party - Death/Injury", "limit": "Unlimited", "status": "Covered — Mandatory"},
                                {"type": "Third Party - Property", "limit": "Rs. 7,50,000", "status": "Covered — Mandatory"},
                                {"type": "Personal Accident (Owner)", "limit": "Rs. 15,00,000", "status": "Covered" if "comprehensive" in policy_type_motor.lower() else "Check policy"}
                            ]
                        }
                    }
                ))

                # Section 2: What You Get in a Claim
                deductible = category_data.get("coverageDetails", {}).get("compulsoryDeductible") or 1000
                voluntary_deductible = category_data.get("coverageDetails", {}).get("voluntaryDeductible") or 0

                vehicle_age = 0
                mfg_year = vehicle_details.get("manufacturingYear")
                if mfg_year:
                    try:
                        vehicle_age = datetime.now().year - int(mfg_year)
                    except:
                        pass

                # Depreciation rates based on vehicle age
                metal_depreciation = min(50, vehicle_age * 5) if vehicle_age > 0 else 0

                analysis["sections"].append(create_section(
                    "claim_payout",
                    "What You Get in a Claim",
                    "Depreciation and deductibles affect your claim amount",
                    2,
                    {
                        "totalLossCalculation": {
                            "title": "If Your Vehicle is Totaled or Stolen",
                            "items": [
                                {"item": "Insured Declared Value (IDV)", "amount": idv},
                                {"item": "(-) Compulsory Deductible", "amount": -deductible},
                                {"item": "(-) Voluntary Deductible", "amount": -voluntary_deductible, "note": "if opted"},
                                {"item": "Amount You Receive", "amount": idv - deductible - voluntary_deductible, "highlight": True}
                            ]
                        },
                        "depreciationRates": {
                            "title": "For Repair Claims — Depreciation Applies",
                            "rates": [
                                {"partCategory": "Rubber, Plastic, Nylon", "rate": "50%", "whatYouPay": "Half the part cost"},
                                {"partCategory": "Glass", "rate": "Nil", "whatYouPay": "Nothing (fully covered)"},
                                {"partCategory": f"Metal Parts (your car: {vehicle_age} years)", "rate": f"{metal_depreciation}%", "whatYouPay": f"{metal_depreciation}% of part cost"},
                                {"partCategory": "Battery", "rate": "50%", "whatYouPay": "Half the cost"},
                                {"partCategory": "Tyres", "rate": "50%", "whatYouPay": "Half the cost"}
                            ],
                            "example": f"On Rs. 80,000 repair with {25}% average depreciation, you pay approximately Rs. 20,000 + deductibles without Zero Depreciation."
                        }
                    }
                ))

                # Section 3: Your Liability Exposure
                analysis["sections"].append(create_section(
                    "liability_exposure",
                    "Your Liability Exposure",
                    "The most important part of motor insurance",
                    3,
                    {
                        "thirdPartyLiability": {
                            "title": "Third-Party Liability: Understanding the Stakes",
                            "description": "If you cause an accident injuring or killing someone, courts can award Rs. 20 Lakhs to Rs. 2+ Crores. Your TP insurance covers this — but ONLY if your policy is valid and you were driving legally.",
                            "warning": True
                        },
                        "whenNotCovered": {
                            "title": "When Third-Party Coverage Does NOT Protect You",
                            "situations": [
                                {"situation": "Driving under influence", "consequence": "Policy void — You pay full compensation personally"},
                                {"situation": "Driving without valid license", "consequence": "Policy void — Full personal liability"},
                                {"situation": "Commercial use (if private policy)", "consequence": "Coverage denied for that use"},
                                {"situation": "Policy expired (even by one day)", "consequence": "No coverage — Full personal liability"}
                            ]
                        }
                    }
                ))

                # Section 4: Add-On Coverage Analysis
                add_ons = category_data.get("addOnCovers", {})
                add_on_analysis = [
                    {"addOn": "Zero Depreciation", "status": "Yes" if add_ons.get("zeroDepreciation") else "No", "benefit": "Eliminates depreciation deduction", "value": "Essential for cars < 5 years"},
                    {"addOn": "Engine Protection", "status": "Yes" if add_ons.get("engineProtection") else "No", "benefit": "Covers water damage to engine", "value": "Important in flood-prone areas"},
                    {"addOn": "Roadside Assistance", "status": "Yes" if add_ons.get("roadsideAssistance") else "No", "benefit": "24x7 help for breakdown", "value": "Convenience at low cost"},
                    {"addOn": "NCB Protection", "status": "Yes" if add_ons.get("ncbProtect") else "No", "benefit": "Protects bonus after claim", "value": "Good for high NCB holders"},
                    {"addOn": "Return to Invoice", "status": "Yes" if add_ons.get("returnToInvoice") else "No", "benefit": "Get invoice price on total loss", "value": "Valuable for new cars"}
                ]

                analysis["sections"].append(create_section(
                    "addon_analysis",
                    "Add-On Coverage Analysis",
                    "Optional covers that reduce out-of-pocket costs",
                    4,
                    {
                        "addOns": add_on_analysis
                    }
                ))

                # Section 5: Your NCB Value
                ncb_saving = int(premium * ncb_percentage / 100) if ncb_percentage else 0
                analysis["sections"].append(create_section(
                    "ncb_value",
                    "Your NCB Value",
                    "No Claim Bonus is a valuable asset",
                    5,
                    {
                        "ncbStatus": {
                            "title": "NCB Status",
                            "items": [
                                {"status": "Current NCB Level", "value": f"{ncb_percentage}%"},
                                {"status": "Premium Saved This Year", "value": f"Rs. {ncb_saving:,}"},
                                {"status": "If You Make a Claim", "value": f"NCB resets to 0% — Next year premium increases by Rs. {ncb_saving:,}"},
                                {"status": "5-Year NCB Value", "value": f"Rs. {ncb_saving * 5:,} (potential savings if maintained)"}
                            ]
                        },
                        "smartClaimAdvice": "For repairs under Rs. 10,000-15,000, paying yourself may be better than losing years of NCB."
                    }
                ))

                # Section 6: Recommended Actions & Assessment
                actions = []
                if end_date:
                    actions.append({"priority": 1, "action": f"Renew before {end_date} — Any gap voids NCB", "timeline": "Before expiry", "urgency": "Critical"})
                if not add_ons.get("zeroDepreciation") and vehicle_age < 5:
                    actions.append({"priority": 2, "action": "Add Zero Depreciation at renewal", "timeline": "At renewal", "urgency": "High"})

                assessment_status = "WELL COVERED" if add_ons.get("zeroDepreciation") and ncb_percentage >= 20 else "STANDARD PROTECTION" if "comprehensive" in policy_type_motor.lower() else "ENHANCEMENT RECOMMENDED"

                analysis["sections"].append(create_section(
                    "recommended_actions",
                    "Recommended Actions",
                    "Prioritized steps",
                    6,
                    {"actions": actions}
                ))

                analysis["sections"].append(create_section(
                    "assessment",
                    "Assessment",
                    assessment_status,
                    7,
                    {
                        "status": assessment_status,
                        "keyFinding": f"{'Comprehensive' if 'comprehensive' in policy_type_motor.lower() else 'Third-party'} cover with {ncb_percentage}% NCB. {'Has Zero Depreciation.' if add_ons.get('zeroDepreciation') else 'No Zero Depreciation - significant out-of-pocket on repairs.'}",
                        "recommendedAction": actions[0]["action"] if actions else "Maintain current coverage."
                    }
                ))

            # ==================== TRAVEL INSURANCE ANALYSIS ====================
            elif "travel" in policy_type:
                trip_details = category_data.get("tripDetails", {})
                coverage_summary = category_data.get("coverageSummary", {})
                emergency_contacts = category_data.get("emergencyContacts", {})

                medical_expenses_raw = coverage_summary.get("medicalExpenses") or coverage_amount
                # Parse to numeric for comparisons; keep raw for display
                try:
                    medical_expenses = _parse_travel_cover_amount(medical_expenses_raw) if isinstance(medical_expenses_raw, str) else (float(medical_expenses_raw) if medical_expenses_raw else 0)
                except (ValueError, TypeError):
                    medical_expenses = 0
                destinations = trip_details.get("destinationCountries") or []
                trip_duration = trip_details.get("tripDuration") or "Check policy"

                # Section 1: Trip & Coverage Summary
                analysis["sections"].append(create_section(
                    "trip_coverage_summary",
                    "Trip & Coverage Summary",
                    "Your travel protection details",
                    1,
                    {
                        "tripDetails": {
                            "title": "Trip Details",
                            "items": [
                                {"detail": "Trip Type", "value": trip_details.get("tripType", "Single Trip")},
                                {"detail": "Destination(s)", "value": ", ".join(destinations) if destinations else "Check policy"},
                                {"detail": "Coverage Period", "value": f"{start_date} to {end_date}" if start_date and end_date else "Check policy"},
                                {"detail": "Trip Duration", "value": str(trip_duration)}
                            ]
                        },
                        "coverageLimits": {
                            "title": "Coverage Limits",
                            "coverages": [
                                {"coverage": "Medical Expenses", "limit": f"USD {medical_expenses:,}" if isinstance(medical_expenses, (int, float)) else str(medical_expenses)},
                                {"coverage": "Emergency Evacuation", "limit": str(coverage_summary.get("emergencyMedicalEvacuation", "Check policy"))},
                                {"coverage": "Trip Cancellation", "limit": str(coverage_summary.get("tripCancellation", "Check policy"))},
                                {"coverage": "Baggage Loss", "limit": str(coverage_summary.get("baggageLoss", "Check policy"))},
                                {"coverage": "Personal Accident", "limit": str(coverage_summary.get("accidentalDeath", "Check policy"))}
                            ]
                        }
                    }
                ))

                # Section 2: Medical Coverage Adequacy
                destination_costs = {
                    "usa": {"hospitalDay": "$3,000 - $5,000", "surgery": "$30,000 - $150,000", "recommended": "$100,000 - $250,000"},
                    "europe": {"hospitalDay": "$1,000 - $2,500", "surgery": "$15,000 - $50,000", "recommended": "$50,000 - $100,000"},
                    "asia": {"hospitalDay": "$300 - $1,200", "surgery": "$5,000 - $30,000", "recommended": "$50,000"}
                }

                analysis["sections"].append(create_section(
                    "medical_adequacy",
                    "Medical Coverage Adequacy",
                    "Medical costs vary by destination",
                    2,
                    {
                        "destinationCosts": destination_costs,
                        "yourAssessment": {
                            "title": "Your Coverage Assessment",
                            "description": f"Your medical limit provides coverage for typical hospitalization. Verify adequacy based on destination."
                        }
                    }
                ))

                # Section 3: What's Not Covered
                exclusions_travel = category_data.get("exclusions", {})
                analysis["sections"].append(create_section(
                    "not_covered",
                    "What's Not Covered",
                    "Common claim rejection reasons",
                    3,
                    {
                        "exclusions": [
                            {"exclusion": "Pre-existing conditions (undeclared)", "impact": "Any related illness — claim rejected"},
                            {"exclusion": "Adventure sports (without add-on)", "impact": "Skiing/Diving/Trekking injuries — not covered"},
                            {"exclusion": "Treatment without authorization", "impact": "Cashless denied; reimbursement reduced"},
                            {"exclusion": "Alcohol/drug related", "impact": "Most policies exclude completely"},
                            {"exclusion": "Travel against medical advice", "impact": "No coverage if doctor advised not to travel"}
                        ]
                    }
                ))

                # Section 4: Emergency Preparedness
                analysis["sections"].append(create_section(
                    "emergency_preparedness",
                    "Emergency Preparedness",
                    "Critical information for emergencies abroad",
                    4,
                    {
                        "emergencyInfo": {
                            "title": "Your Emergency Information",
                            "contacts": [
                                {"contact": "24x7 Assistance Helpline", "detail": emergency_contacts.get("emergencyHelpline24x7", "Check policy document")},
                                {"contact": "Claims Email", "detail": emergency_contacts.get("claimsEmail", "Check policy document")},
                                {"contact": "Policy Number", "detail": extracted_data.get("policyNumber", "")}
                            ]
                        },
                        "tip": "Save the assistance number in your phone. In an emergency, call FIRST — before going to hospital if possible."
                    }
                ))

                # Section 5 & 6: Actions and Assessment
                assessment_status = "ADEQUATELY PROTECTED" if medical_expenses and medical_expenses >= 50000 else "REVIEW MEDICAL LIMIT"
                analysis["sections"].append(create_section(
                    "assessment",
                    "Assessment",
                    assessment_status,
                    5,
                    {
                        "status": assessment_status,
                        "keyFinding": "Coverage appears adequate for standard travel. Verify medical limits for high-cost destinations like USA.",
                        "recommendedAction": "Save emergency contacts and policy document offline on phone before travel."
                    }
                ))

            # ==================== BUSINESS INSURANCE ANALYSIS ====================
            elif "business" in policy_type or "commercial" in policy_type or "fire" in policy_type:
                property_coverage = category_data.get("propertyCoverage", {})
                liability_coverage = category_data.get("liabilityCoverage", {})
                bi_coverage = category_data.get("businessInterruption", {})

                total_property_value = property_coverage.get("totalPropertyValue") or coverage_amount

                # Section 1: Coverage Overview
                analysis["sections"].append(create_section(
                    "coverage_overview",
                    "Coverage Overview",
                    "Your commercial protection details",
                    1,
                    {
                        "businessDetails": {
                            "title": "Business & Policy Details",
                            "items": [
                                {"detail": "Business Name", "value": category_data.get("insuredEntity", {}).get("businessName", user_name)},
                                {"detail": "Business Type", "value": category_data.get("insuredEntity", {}).get("businessType", "Check policy")},
                                {"detail": "Policy Type", "value": category_data.get("policyIdentification", {}).get("policyType", policy_type)},
                                {"detail": "Policy Period", "value": f"{start_date} to {end_date}" if start_date else "Check policy"}
                            ]
                        },
                        "propertyCoverage": {
                            "title": "Property Coverage",
                            "assets": [
                                {"category": "Building", "insuredValue": property_coverage.get("buildingValue", 0)},
                                {"category": "Plant & Machinery", "insuredValue": property_coverage.get("plantMachineryValue", 0)},
                                {"category": "Stock / Inventory", "insuredValue": property_coverage.get("stocksValue", 0)},
                                {"category": "TOTAL", "insuredValue": total_property_value, "highlight": True}
                            ]
                        }
                    }
                ))

                # Section 2: Underinsurance Problem
                analysis["sections"].append(create_section(
                    "underinsurance",
                    "The Underinsurance Problem",
                    "Average clause affects every claim",
                    2,
                    {
                        "averageClause": {
                            "title": "Average Clause Impact",
                            "description": "If your insured values are less than actual replacement values, all claims are reduced proportionately.",
                            "example": "If 20% underinsured, a Rs. 50 Lakh claim only pays Rs. 40 Lakhs.",
                            "recommendation": "Update Sum Insured to current replacement values at renewal."
                        }
                    }
                ))

                # Section 3: Business Interruption
                has_bi = bi_coverage.get("businessInterruptionCover") is not None
                analysis["sections"].append(create_section(
                    "business_interruption",
                    "Business Interruption Analysis",
                    "Income protection if operations stop",
                    3,
                    {
                        "biCoverage": {
                            "title": "Business Interruption Cover",
                            "covered": has_bi,
                            "indemnityPeriod": bi_coverage.get("indemnityPeriod", "N/A") if has_bi else "NOT COVERED",
                            "grossProfitInsured": bi_coverage.get("grossProfitInsured", "N/A") if has_bi else "N/A"
                        },
                        "warning": None if has_bi else "Without BI Cover, a fire or flood means zero revenue but continued expenses. This comes entirely from reserves or debt."
                    }
                ))

                # Section 4: Liability Coverage
                liabilities = [
                    {"type": "Public Liability", "coverage": liability_coverage.get("publicLiability", "Not covered")},
                    {"type": "Product Liability", "coverage": liability_coverage.get("productLiability", "Not covered")},
                    {"type": "Professional Indemnity", "coverage": liability_coverage.get("professionalIndemnity", "Not covered")},
                    {"type": "Cyber Liability", "coverage": liability_coverage.get("cyberLiability", "Not covered")}
                ]

                analysis["sections"].append(create_section(
                    "liability_coverage",
                    "Liability Coverage",
                    "Protection against third-party claims",
                    4,
                    {"liabilities": liabilities}
                ))

                # Section 5 & 6: Assessment
                assessment_status = "ADEQUATELY PROTECTED" if has_bi else "GAPS IN KEY AREAS"
                analysis["sections"].append(create_section(
                    "assessment",
                    "Assessment",
                    assessment_status,
                    5,
                    {
                        "status": assessment_status,
                        "keyFinding": f"Property coverage of Rs. {total_property_value:,}. {'Has BI cover.' if has_bi else 'NO Business Interruption cover - critical gap.'}",
                        "recommendedAction": "Update Sum Insured to current replacement values." if has_bi else "Add Business Interruption cover urgently."
                    }
                ))

            # ==================== PERSONAL ACCIDENT / ACCIDENTAL INSURANCE ANALYSIS (EAZR_04) ====================
            elif "accidental" in policy_type or "accident" in policy_type or "pa" in policy_type or "personal accident" in policy_type:
                # Extract PA-specific data (supports both old flat format and new EAZR_04 nested format)
                coverage_details = category_data.get("coverageDetails", {})
                additional_benefits = category_data.get("additionalBenefits", {})
                exclusions_data = category_data.get("exclusions", {})
                claims_info_pa = category_data.get("claimsInfo", {})

                # Safe numeric parser for deep analysis
                def _da_safe_num(val, default=0):
                    if val is None:
                        return default
                    if isinstance(val, (int, float)):
                        return float(val)
                    if isinstance(val, str):
                        cleaned = val.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
                        try:
                            return float(cleaned)
                        except (ValueError, TypeError):
                            return default
                    return default

                sum_insured = _da_safe_num(coverage_details.get("sumInsured"), 0) or _da_safe_num(coverage_amount, 0)
                annual_income = 1000000  # Default assumed income

                # Handle both old flat format and new nested format for coverage data
                ad = coverage_details.get("accidentalDeath", {}) if isinstance(coverage_details.get("accidentalDeath"), dict) else {}
                ptd_data = coverage_details.get("permanentTotalDisability", {}) if isinstance(coverage_details.get("permanentTotalDisability"), dict) else {}
                ppd_data = coverage_details.get("permanentPartialDisability", {}) if isinstance(coverage_details.get("permanentPartialDisability"), dict) else {}
                ttd_data = coverage_details.get("temporaryTotalDisability", {}) if isinstance(coverage_details.get("temporaryTotalDisability"), dict) else {}
                medical_data = coverage_details.get("medicalExpenses", {}) if isinstance(coverage_details.get("medicalExpenses"), dict) else {}

                ad_benefit = _da_safe_num(ad.get("benefitAmount"), sum_insured)
                ptd_benefit = _da_safe_num(ptd_data.get("benefitAmount"), sum_insured)

                # Detect if this is an EAZR company complimentary PA or a standalone paid PA
                is_company_pa = category_data.get("policyBasics", {}).get("isCompanyPA", False)

                # Section 1: PA Coverage Snapshot with 5 Coverage Cards
                analysis["sections"].append(create_section(
                    "coverage_snapshot",
                    "Your Complimentary PA Coverage" if is_company_pa else "Your PA Coverage",
                    (f"Complimentary PA Cover — Sum Insured: \u20b9{sum_insured:,}" if is_company_pa
                     else f"Personal Accident Cover — Sum Insured: Rs. {sum_insured:,}"),
                    1,
                    {
                        "sumInsured": sum_insured,
                        "sumInsuredFormatted": f"Rs. {sum_insured:,}",
                        "coverageCards": [
                            {
                                "type": "AD", "label": "Accidental Death", "covered": True,
                                "benefitAmount": ad_benefit,
                                "benefitFormatted": f"Rs. {ad_benefit:,}",
                                "detail": f"{ad.get('benefitPercentage', 100)}% of SI" + (" + Double Indemnity" if ad.get("doubleIndemnity", {}).get("applicable") else "")
                            },
                            {
                                "type": "PTD", "label": "Permanent Total Disability",
                                "covered": ptd_data.get("covered", True) if ptd_data else bool(coverage_details.get("permanentTotalDisability")),
                                "benefitAmount": ptd_benefit,
                                "benefitFormatted": f"Rs. {ptd_benefit:,}",
                                "detail": f"{ptd_data.get('benefitPercentage', 100)}% of SI"
                            },
                            {
                                "type": "PPD", "label": "Permanent Partial Disability",
                                "covered": ppd_data.get("covered", True) if ppd_data else bool(coverage_details.get("permanentPartialDisability")),
                                "detail": f"{len(ppd_data.get('schedule', []))} conditions in schedule" if ppd_data.get("schedule") else "As per IRDAI schedule"
                            },
                            {
                                "type": "TTD", "label": "Temporary Total Disability",
                                "covered": ttd_data.get("covered", False) if ttd_data else bool(coverage_details.get("temporaryTotalDisability")),
                                "detail": f"Rs. {_da_safe_num(ttd_data.get('benefitAmount'), 0):,.0f}/{ttd_data.get('benefitType', 'week')} for up to {ttd_data.get('maximumWeeks', 52)} weeks" if ttd_data.get("covered") else "Not covered"
                            },
                            {
                                "type": "Medical", "label": "Medical Expenses",
                                "covered": medical_data.get("covered", False) if medical_data else bool(coverage_details.get("medicalExpenses")),
                                "detail": f"{medical_data.get('limitPercentage', 0)}% of SI" if medical_data.get("covered") else "Not covered"
                            }
                        ],
                        "policyPeriod": f"{start_date} to {end_date}" if start_date else "Check policy"
                    }
                ))

                # Section 2: Scoring Engine
                s1 = _calculate_pa_income_replacement_score(coverage_details, additional_benefits, annual_income)
                s2 = _calculate_pa_disability_protection_score(coverage_details, additional_benefits)
                overall_score = round(s1["score"] * 0.6 + s2["score"] * 0.4)
                overall_label = _get_score_label(overall_score)

                analysis["sections"].append(create_section(
                    "scoring_engine",
                    "Coverage Overview",
                    (f"Complimentary PA Cover — Score: {overall_score}/100" if is_company_pa
                     else f"Protection Score: {overall_score}/100 — {overall_label['label']}"),
                    2,
                    {
                        "overallScore": overall_score,
                        "overallLabel": overall_label["label"],
                        "overallColor": overall_label["color"],
                        "contextNote": ("This PA cover is provided as a complimentary benefit without any additional premium. Scores are relative to standalone paid PA policies."
                                        if is_company_pa else None),
                        "scores": [
                            {
                                "name": "Income Replacement Adequacy", "weight": "60%",
                                "score": s1["score"],
                                "label": _get_score_label(s1["score"])["label"],
                                "color": _get_score_label(s1["score"])["color"],
                                "factors": s1["factors"]
                            },
                            {
                                "name": "Disability Protection Depth", "weight": "40%",
                                "score": s2["score"],
                                "label": _get_score_label(s2["score"])["label"],
                                "color": _get_score_label(s2["score"])["color"],
                                "factors": s2["factors"]
                            }
                        ]
                    }
                ))

                # Section 3: Gap Analysis / Coverage Notes
                pa_gaps_raw = _analyze_pa_gaps(coverage_details, additional_benefits, annual_income)

                if is_company_pa:
                    # Soften gaps for free cover: downgrade severity and adjust language
                    pa_gaps_display = []
                    for g in pa_gaps_raw:
                        soft_gap = dict(g)
                        soft_gap["severity"] = "info"
                        soft_gap["severityColor"] = "#6B7280"
                        if soft_gap.get("gapId") == "G001":
                            soft_gap["title"] = "PA Sum Insured (Complimentary Cover)"
                            soft_gap["description"] = f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{sum_insured:,} is provided as a complimentary benefit under this policy, without any additional premium."
                            soft_gap["impact"] = "This coverage is subject to the applicable terms, conditions, and exclusions of the policy."
                            soft_gap["solution"] = "For higher accident coverage, standalone PA plans may be explored separately."
                        elif soft_gap.get("gapId") == "G002":
                            soft_gap["title"] = "TTD Not Included"
                            soft_gap["description"] = "Temporary Total Disability benefit is not included under this complimentary PA cover."
                            soft_gap["impact"] = "Hospitalization expenses, if any, are covered under your separate health insurance policy."
                            soft_gap["solution"] = "Standalone PA plans with TTD benefit are available if required."
                        elif soft_gap.get("gapId") == "G004":
                            soft_gap["title"] = "Medical Expenses (Covered under Health Insurance)"
                            soft_gap["description"] = "Accident-related medical expenses are covered under your separate health insurance policy."
                            soft_gap["impact"] = "Your health insurance policy is the primary cover for medical treatment costs."
                            soft_gap["solution"] = "Ensure your health insurance policy is active for medical expense coverage."
                        pa_gaps_display.append(soft_gap)

                    analysis["sections"].append(create_section(
                        "gap_analysis",
                        "Coverage Notes",
                        "Coverage notes for this complimentary PA cover" if pa_gaps_display else "Complimentary PA cover details noted",
                        3,
                        {
                            "totalGaps": len(pa_gaps_display),
                            "highSeverity": 0,
                            "mediumSeverity": 0,
                            "lowSeverity": 0,
                            "infoNotes": len(pa_gaps_display),
                            "contextNote": "These are informational notes about your complimentary PA cover provided without any additional premium.",
                            "gaps": pa_gaps_display
                        }
                    ))
                else:
                    # Standalone PA: show real gaps with actual severity
                    high_count = sum(1 for g in pa_gaps_raw if g.get("severity") == "high")
                    medium_count = sum(1 for g in pa_gaps_raw if g.get("severity") == "medium")
                    low_count = sum(1 for g in pa_gaps_raw if g.get("severity") == "low")
                    gap_subtitle = f"{high_count} critical, {medium_count} moderate, {low_count} minor" if pa_gaps_raw else "No significant gaps found"
                    analysis["sections"].append(create_section(
                        "gap_analysis",
                        "Gap Analysis",
                        gap_subtitle,
                        3,
                        {
                            "totalGaps": len(pa_gaps_raw),
                            "highSeverity": high_count,
                            "mediumSeverity": medium_count,
                            "lowSeverity": low_count,
                            "gaps": pa_gaps_raw
                        }
                    ))

                # Section 4: Key Exclusions
                standard_exclusions = exclusions_data.get("standardExclusions", [])
                if not standard_exclusions:
                    # Fallback for old format
                    standard_exclusions = []
                    for key in ["suicideExclusion", "warExclusion", "intoxicationExclusion", "criminalActExclusion", "hazardousActivitiesExclusion"]:
                        val = exclusions_data.get(key)
                        if val:
                            standard_exclusions.append(str(val))
                    other_exc = exclusions_data.get("otherExclusions", [])
                    if isinstance(other_exc, list):
                        standard_exclusions.extend([str(e) for e in other_exc[:5]])

                exclusion_items = [{"exclusion": exc, "details": exc} for exc in standard_exclusions] if standard_exclusions else [
                    {"exclusion": "Self-inflicted Injuries", "details": "Suicide and self-harm not covered"},
                    {"exclusion": "War & Nuclear Perils", "details": "War, terrorism, nuclear events excluded"},
                    {"exclusion": "Intoxication", "details": "Injuries under influence of alcohol/drugs"},
                    {"exclusion": "Criminal Acts", "details": "Injuries during illegal activities"},
                    {"exclusion": "Hazardous Activities", "details": "Adventure sports may be excluded unless declared"}
                ]

                analysis["sections"].append(create_section(
                    "exclusions",
                    "Key Exclusions",
                    "What is NOT covered",
                    4,
                    {
                        "exclusions": exclusion_items,
                        "ageLimits": exclusions_data.get("ageLimits", {}),
                        "occupationRestrictions": exclusions_data.get("occupationRestrictions", []),
                        "importantNote": "PA insurance covers ACCIDENTS only, not illness. Refer to policy document for complete exclusions."
                    }
                ))

                # Section 5: Recommendations
                _pa_claims_process = {
                    "steps": [
                        {"step": 1, "title": "Intimate Claim", "description": "Report accident to insurer immediately (within 24-48 hours)"},
                        {"step": 2, "title": "File FIR", "description": "Lodge police FIR for accidents (mandatory for death/serious injury)"},
                        {"step": 3, "title": "Collect Documents", "description": "Medical reports, hospital bills, FIR copy, ID proof, policy copy"},
                        {"step": 4, "title": "Submit Claim Form", "description": "Fill claim form and submit with all documents"},
                        {"step": 5, "title": "Claim Settlement", "description": "Insurer verifies and settles claim (typically 30 days)"}
                    ],
                    "contact": {
                        "email": claims_info_pa.get("claimsEmail") or "Check policy",
                        "helpline": claims_info_pa.get("claimsHelpline") or "Check policy"
                    }
                }

                if is_company_pa:
                    pa_deep_recommendations = [
                        {
                            "id": "keep_active",
                            "category": "maintenance",
                            "priority": 1,
                            "title": "Keep Your PA Cover Active",
                            "description": "This PA cover is provided as a complimentary benefit without any additional premium. Ensure it stays active by maintaining the underlying policy.",
                            "estimatedCost": "No additional premium",
                            "ipfEligible": False,
                            "icon": "verified"
                        },
                        {
                            "id": "know_your_cover",
                            "category": "awareness",
                            "priority": 2,
                            "title": "Know Your Coverage",
                            "description": f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{sum_insured:,} is provided under this policy. Share the policy details with your nominee/family for their awareness.",
                            "estimatedCost": "No additional cost",
                            "ipfEligible": False,
                            "icon": "info"
                        },
                        {
                            "id": "review_at_renewal",
                            "category": "maintenance",
                            "priority": 3,
                            "title": "Review at Renewal",
                            "description": "Review the PA cover details at renewal to stay updated on any changes to benefits, terms, or conditions.",
                            "estimatedCost": "No additional cost",
                            "ipfEligible": False,
                            "icon": "rate_review"
                        }
                    ]
                    analysis["sections"].append(create_section(
                        "recommendations",
                        "Good to Know",
                        "Key information about your complimentary PA cover",
                        5,
                        {"recommendations": pa_deep_recommendations, "claimsProcess": _pa_claims_process}
                    ))
                else:
                    # Standalone PA: real recommendations from gap analysis
                    pa_policy_sub_type = category_data.get("policyBasics", {}).get("policySubType", "")
                    pa_deep_recommendations = _generate_pa_recommendations(pa_gaps_raw, coverage_details, additional_benefits, pa_policy_sub_type)
                    analysis["sections"].append(create_section(
                        "recommendations",
                        "Recommendations",
                        f"{len(pa_deep_recommendations)} recommendations to strengthen your PA cover",
                        5,
                        {"recommendations": pa_deep_recommendations, "claimsProcess": _pa_claims_process}
                    ))

                # Section 6: Assessment
                if is_company_pa:
                    assessment_status = "COMPLIMENTARY PROTECTION"
                    key_finding = f"A Personal Accident (PA) insurance cover with a sum insured of \u20b9{sum_insured:,} is provided as a complimentary benefit under this policy, without any additional premium, and is subject to the applicable terms, conditions, and exclusions."
                    rec_action = "Keep the policy active to continue availing this complimentary PA benefit."
                    analysis["sections"].append(create_section(
                        "assessment",
                        "Assessment",
                        assessment_status,
                        6,
                        {
                            "status": assessment_status,
                            "protectionScore": overall_score,
                            "scoreLabel": "Complimentary",
                            "scoreColor": "#3B82F6",
                            "keyFinding": key_finding,
                            "recommendedAction": rec_action,
                            "importantReminder": "This is a complimentary PA cover for accidents. Your Health Insurance covers illness and medical expenses, while Life Insurance provides comprehensive family protection."
                        }
                    ))
                else:
                    # Standalone PA: assessment based on actual score
                    if overall_score >= 70:
                        assessment_status = "WELL PROTECTED"
                        key_finding = f"Your PA cover of Rs. {sum_insured:,} provides strong accident protection with a score of {overall_score}/100."
                        rec_action = "Review your coverage annually to keep pace with income growth."
                    elif overall_score >= 40:
                        assessment_status = "GAPS IN KEY AREAS"
                        key_finding = f"Your PA cover of Rs. {sum_insured:,} has some gaps. Score: {overall_score}/100."
                        rec_action = "Consider addressing the high-severity gaps identified above to strengthen your accident protection."
                    else:
                        assessment_status = "NEEDS ATTENTION"
                        key_finding = f"Your PA cover of Rs. {sum_insured:,} has significant coverage gaps. Score: {overall_score}/100."
                        rec_action = "Upgrade to a comprehensive PA plan with higher sum insured, TTD benefit, and medical expenses cover."
                    analysis["sections"].append(create_section(
                        "assessment",
                        "Assessment",
                        assessment_status,
                        6,
                        {
                            "status": assessment_status,
                            "protectionScore": overall_score,
                            "scoreLabel": overall_label["label"],
                            "scoreColor": overall_label["color"],
                            "keyFinding": key_finding,
                            "recommendedAction": rec_action,
                            "importantReminder": "PA insurance covers accidents only. Ensure you have Health Insurance for illness and Life Insurance for comprehensive family protection."
                        }
                    ))

            # ==================== AGRICULTURE INSURANCE ANALYSIS ====================
            elif "agriculture" in policy_type or "crop" in policy_type or "farm" in policy_type or "pmfby" in policy_type:
                farmer_details = category_data.get("farmerDetails", {})
                land_crop = category_data.get("landCropDetails", {})
                risks_covered = category_data.get("risksCovered", {})
                premium_details = category_data.get("premium", {})

                total_sum_insured = category_data.get("coverageDetails", {}).get("totalSumInsured") or coverage_amount
                farmer_premium = premium_details.get("farmerSharePremium") or premium

                # Section 1: Enrollment Summary
                analysis["sections"].append(create_section(
                    "enrollment_summary",
                    "Enrollment Summary",
                    "Your crop protection under PMFBY/RWBCIS",
                    1,
                    {
                        "policyDetails": {
                            "title": "Policy Details",
                            "items": [
                                {"detail": "Scheme", "value": category_data.get("policyIdentification", {}).get("schemeName", "PMFBY")},
                                {"detail": "Season", "value": category_data.get("policyIdentification", {}).get("seasonYear", "Check policy")},
                                {"detail": "Farmer Category", "value": farmer_details.get("farmerCategory", "Check policy")},
                                {"detail": "Crop", "value": land_crop.get("cropName", "Check policy")},
                                {"detail": "Total Area Insured", "value": land_crop.get("totalAreaInsured", "Check policy")},
                                {"detail": "Total Sum Insured", "value": f"Rs. {total_sum_insured:,}" if total_sum_insured else "Check policy"}
                            ]
                        }
                    }
                ))

                # Section 2: Claim Calculation
                analysis["sections"].append(create_section(
                    "claim_calculation",
                    "How Your Claim is Calculated",
                    "PMFBY claims are based on VILLAGE-LEVEL yield",
                    2,
                    {
                        "claimFormula": {
                            "title": "Claim Calculation",
                            "description": "Your individual crop loss does not directly determine your claim. The Crop Cutting Experiment (CCE) in your village determines yield for all farmers.",
                            "formula": "Claim = Sum Insured × Shortfall × Indemnity Level",
                            "important": "Village-Level Assessment means all farmers with same crop in your area get same claim percentage."
                        }
                    }
                ))

                # Section 3: What's Covered
                covered_risks = [
                    {"risk": "Prevented Sowing", "status": "Covered", "notes": "If sowing prevented due to deficit rainfall"},
                    {"risk": "Standing Crop Loss", "status": "Covered", "notes": "Yield loss due to drought, flood, pests"},
                    {"risk": "Post-Harvest Loss", "status": "Covered (14 days)", "notes": "Cyclone, unseasonal rain after harvest"},
                    {"risk": "Localized Calamity", "status": "Covered", "notes": "Hailstorm, landslide — individual assessment"},
                    {"risk": "Wild Animal Attack", "status": str(risks_covered.get("wildAnimalAttack", "Check policy")), "notes": "If add-on opted"}
                ]

                analysis["sections"].append(create_section(
                    "coverage",
                    "What's Covered",
                    "Risks protected under the scheme",
                    3,
                    {"risks": covered_risks}
                ))

                # Section 4: Premium Contribution
                gov_subsidy = premium_details.get("stateSharePremium", 0) + premium_details.get("centralSharePremium", 0) if premium_details else 0
                leverage = int(total_sum_insured / farmer_premium) if farmer_premium and farmer_premium > 0 else 0

                analysis["sections"].append(create_section(
                    "premium_contribution",
                    "Your Premium Contribution",
                    "PMFBY is heavily subsidized",
                    4,
                    {
                        "premiumBreakdown": {
                            "title": "Premium Breakdown",
                            "items": [
                                {"component": "Your Contribution", "amount": farmer_premium, "note": "2% for Kharif / 1.5% for Rabi"},
                                {"component": "Government Subsidy", "amount": gov_subsidy},
                                {"component": "Leverage (SI ÷ Premium)", "amount": f"{leverage}x", "highlight": True}
                            ]
                        },
                        "valueAssessment": f"For every Rs. {farmer_premium:,} you pay, you receive Rs. {total_sum_insured:,} coverage. One of the most subsidized insurance products in India."
                    }
                ))

                # Section 5 & 6: Assessment
                analysis["sections"].append(create_section(
                    "assessment",
                    "Assessment",
                    "PROPERLY ENROLLED" if total_sum_insured else "VERIFICATION NEEDED",
                    5,
                    {
                        "status": "PROPERLY ENROLLED" if total_sum_insured else "VERIFICATION NEEDED",
                        "keyFinding": f"Enrolled for {land_crop.get('cropName', 'crop')} with Rs. {total_sum_insured:,} coverage.",
                        "recommendedAction": "Verify crop and area details match actual sowing. Report any loss within 72 hours."
                    }
                ))

            # ==================== GENERIC ANALYSIS (fallback) ====================
            else:
                analysis["sections"].append(create_section(
                    "coverage_overview",
                    "Coverage Overview",
                    "Your policy protection summary",
                    1,
                    {
                        "summary": {
                            "policyType": policy_type,
                            "coverageAmount": coverage_amount,
                            "premium": premium,
                            "status": "Active" if protection_score >= 50 else "Review Needed"
                        }
                    }
                ))

                analysis["sections"].append(create_section(
                    "assessment",
                    "Assessment",
                    protection_score_label,
                    2,
                    {
                        "status": protection_score_label,
                        "protectionScore": protection_score,
                        "keyFinding": f"Policy provides Rs. {coverage_amount:,} coverage.",
                        "recommendedAction": "Review policy details for specific coverage information."
                    }
                ))

            return analysis

        # Save to MongoDB
        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager

            if mongodb_chat_manager is not None and mongodb_chat_manager.db is not None:
                db = mongodb_chat_manager.db
                policy_analysis_collection = db['policy_analysis']

                # Check for duplicate policy before saving
                policy_number = extracted_data.get("policyNumber", "")
                if policy_number:
                    # Check if policy with same policyNumber already exists for this user (excluding soft-deleted)
                    existing_policy = policy_analysis_collection.find_one({
                        "user_id": int(userId),
                        "extractedData.policyNumber": policy_number,
                        "$or": [
                            {"isDeleted": {"$exists": False}},
                            {"isDeleted": False}
                        ]
                    })

                    if existing_policy:
                        # Extract existing policy details for navigation
                        existing_policy_id = str(existing_policy.get("_id", ""))
                        existing_analysis_id = existing_policy.get("analysisId", "")
                        existing_policy_type = existing_policy.get("extractedData", {}).get("policyType", "")
                        existing_insurer = existing_policy.get("extractedData", {}).get("insuranceProvider", "")

                        logger.warning(f"⚠️ Duplicate policy detected: {policy_number} already exists for user {userId} (policyId: {existing_policy_id})")
                        raise HTTPException(
                            status_code=409,
                            detail={
                                "success": False,
                                "error_code": "POL_8005",
                                "message": f"This policy (#{policy_number}) has already been uploaded to your account.",
                                "isDuplicate": True,
                                "existingPolicy": {
                                    "policyId": existing_policy_id,
                                    "analysisId": existing_analysis_id,
                                    "userId": int(userId),
                                    "policyNumber": policy_number,
                                    "policyType": existing_policy_type,
                                    "insuranceProvider": existing_insurer,
                                    "uploadedAt": existing_policy.get("uploadedAt", ""),
                                    "createdAt": existing_policy.get("created_at").isoformat() + "Z" if existing_policy.get("created_at") else ""
                                }
                            }
                        )

                # Prepare document to save (EAZR Production Templates V1.0 - TAB 1 structure)
                policy_document = {
                    "analysisId": analysis_id,
                    "uploadId": upload_id,  # Add uploadId to link with policy_uploads
                    "user_id": int(userId),
                    "policyFor": policyFor,
                    "policyHolder": {
                        "name": name,
                        "gender": gender,
                        "dateOfBirth": dateOfBirth or extracted_data.get("dateOfBirth") or "",
                        "relationship": relationship
                    },
                    "extractedData": {
                        "policyNumber": extracted_data.get("policyNumber", ""),
                        "uin": extracted_data.get("uin") or extracted_uin,  # Add UIN field
                        "insuranceProvider": extracted_data.get("insuranceProvider", ""),
                        "policyType": policy_type or extracted_data.get("policyType", ""),
                        "planName": extracted_data.get("planName", extracted_data.get("policyType", "Insurance Plan")),
                        "coverageAmount": extracted_data.get("coverageAmount", 0),
                        "premium": extracted_data.get("premium", 0),
                        "premiumFrequency": extracted_data.get("premiumFrequency", "annually"),
                        "startDate": extracted_data.get("startDate", ""),
                        "endDate": extracted_data.get("endDate", ""),
                        "policyHolderName": extracted_data.get("policyHolderName", name),
                        "insuredName": extracted_data.get("insuredName", extracted_data.get("policyHolderName", name)),
                        "keyBenefits": extracted_data.get("keyBenefits") or [],
                        "exclusions": extracted_data.get("exclusions") or [],
                        "waitingPeriods": extracted_data.get("waitingPeriods") or [],
                        "criticalAreas": extracted_data.get("criticalAreas") or [],
                        "_enhancedInsights": extracted_data.get("_enhancedInsights") or {},
                        # Category-specific data organized by policy type (TAB 1 structure)
                        "categorySpecificData": complete_category_data,
                        # PRD v2 extraction with confidence scoring
                        "extractionV2": {
                            v2_category: v2_raw_extraction,
                            "extraction_metadata": v2_extraction_metadata,
                        } if v2_raw_extraction else None,
                    },
                    "unifiedSections": unified_sections,  # Save unified sections to MongoDB
                    "gapAnalysis": formatted_gaps,
                    "protectionScore": protection_score,
                    "protectionScoreLabel": protection_score_label,
                    "summary": {
                        "totalGaps": len(formatted_gaps),
                        "highSeverityGaps": high_count,
                        "mediumSeverityGaps": medium_count,
                        "lowSeverityGaps": low_count,
                        "recommendedAdditionalCoverage": total_cost
                    },
                    # Validation & quality check results (for GET API parity)
                    "dataValidation": {
                        "hasIssues": data_validation.get("totalIssues", 0) > 0,
                        "hasWarnings": data_validation.get("hasWarnings", False),
                        "hasErrors": data_validation.get("hasErrors", False),
                        "totalIssues": data_validation.get("totalIssues", 0),
                        "warningCount": len(data_validation.get("warnings", [])),
                        "errorCount": len(data_validation.get("errors", [])),
                        "warnings": data_validation.get("warnings", []),
                        "errors": data_validation.get("errors", []),
                        "recommendations": data_validation.get("recommendations", []),
                        "fourCheckValidation": four_check_result if four_check_result else None,
                        "pdfTextVerification": pdf_text_verification if pdf_text_verification else None,
                        "llmVerification": llm_verification_result if llm_verification_result else None,
                    },
                    "redundantAddonAnalysis": {
                        "hasRedundantAddons": redundant_addon_analysis.get("hasRedundantAddons", False),
                        "redundantAddons": redundant_addon_analysis.get("redundantAddons", []),
                        "totalWastedPremium": redundant_addon_analysis.get("totalWastedPremium", 0),
                        "totalWastedFormatted": redundant_addon_analysis.get("totalWastedFormatted", "₹0"),
                        "redundantCount": len(redundant_addon_analysis.get("redundantAddons", [])),
                        "potentialAnnualSavings": redundant_addon_analysis.get("totalWastedPremium", 0)
                    },
                    "universalScores": universal_scores if universal_scores else None,
                    "zoneClassification": zone_classification if zone_classification else None,
                    "verdict": verdict if verdict else None,
                    "irdaiCompliance": irdai_compliance if irdai_compliance else None,
                    "zoneRecommendations": zone_recommendations if zone_recommendations else None,
                    "extractedUIN": extracted_uin,
                    "uploadedAt": uploadedAt,
                    "fileHash": file_hash,  # MD5 hash for duplicate detection
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }

                # Insert into MongoDB
                result = policy_analysis_collection.insert_one(policy_document)
                logger.info(f"✅ Policy saved to MongoDB with ID: {result.inserted_id}")
            else:
                logger.warning("⚠️ MongoDB not available, skipping database save")

        except HTTPException:
            # Re-raise HTTP exceptions (like duplicate policy error)
            raise
        except Exception as db_error:
            logger.error(f"❌ Failed to save policy to MongoDB: {str(db_error)}", exc_info=True)
            # Continue even if DB save fails

        # Extract key benefits for prominent display
        key_benefits = extracted_data.get("keyBenefits") or []

        # ==================== BUILD DEEP ANALYSIS (EAZR Policy Intelligence Report V4.0) ====================
        # Calculate user age: prefer extracted member age → form DOB → default 30
        user_age = 30  # Default age
        _deep_age_found = False
        if v2_raw_extraction:
            _deep_members_field = v2_raw_extraction.get("insuredMembers", {})
            _deep_members_val = _deep_members_field.get("value") if isinstance(_deep_members_field, dict) else _deep_members_field
            if isinstance(_deep_members_val, list) and _deep_members_val:
                for _dm in _deep_members_val:
                    if isinstance(_dm, dict) and str(_dm.get("memberRelationship", "")).lower() in ("self", "member", "primary", "proposer"):
                        _dm_age = _dm.get("memberAge")
                        if _dm_age and isinstance(_dm_age, (int, float)) and _dm_age > 0:
                            user_age = int(_dm_age)
                            _deep_age_found = True
                        break
                if not _deep_age_found and _deep_members_val:
                    _dm_first = _deep_members_val[0]
                    if isinstance(_dm_first, dict):
                        _dm_age = _dm_first.get("memberAge")
                        if _dm_age and isinstance(_dm_age, (int, float)) and _dm_age > 0:
                            user_age = int(_dm_age)
                            _deep_age_found = True
        if not _deep_age_found and dateOfBirth:
            try:
                birth_date = datetime.strptime(dateOfBirth, "%Y-%m-%d")
                user_age = (datetime.now() - birth_date).days // 365
            except Exception as age_err:
                logger.warning(f"⚠️ Could not calculate age from dateOfBirth: {str(age_err)}")

        # Build deep analysis with all required parameters now available
        deep_analysis = build_deep_analysis(
            policy_type=detected_policy_type,
            extracted_data=extracted_data,
            category_data=complete_category_data,
            formatted_gaps=formatted_gaps,
            protection_score=protection_score,
            protection_score_label=protection_score_label,
            key_benefits=key_benefits,
            exclusions_list=exclusions_list,
            waiting_periods_list=waiting_periods_list,
            user_name=name,
            user_age=user_age,
            user_gender=gender
        )
        logger.info(f"✅ Built deep analysis for {detected_policy_type} policy with {len(deep_analysis.get('sections', []))} sections")

        # Get policy holder and insured information
        policy_holder_name = extracted_data.get("policyHolderName", name)
        insured_name = extracted_data.get("insuredName", policy_holder_name)

        # Extract critical areas from extracted data
        critical_areas_raw = extracted_data.get("criticalAreas") or []
        critical_areas = []
        for idx, area in enumerate(critical_areas_raw):
            if isinstance(area, dict):
                critical_areas.append({
                    "areaId": f"critical_{str(idx + 1).zfill(3)}",
                    "name": area.get("name", ""),
                    "description": area.get("description", ""),
                    "status": area.get("status", "review_required"),
                    "importance": area.get("importance", "medium")
                })
            elif isinstance(area, str):
                # If it's just a string, create a simple structure
                critical_areas.append({
                    "areaId": f"critical_{str(idx + 1).zfill(3)}",
                    "name": area,
                    "description": area,
                    "status": "review_required",
                    "importance": "medium"
                })

        # Extract recommendations from gaps
        recommendations = []
        for idx, gap in enumerate(formatted_gaps):
            recommendation_text = gap.get("recommendation", "")
            if recommendation_text:
                recommendations.append({
                    "recommendationId": f"rec_{str(idx + 1).zfill(3)}",
                    "category": gap.get("category", "Coverage Enhancement"),
                    "priority": gap.get("severity", "medium"),
                    "suggestion": recommendation_text,
                    "estimatedCost": gap.get("estimatedCost", 0),
                    "relatedGapId": gap.get("gapId", "")
                })

        # ==================== CALCULATE POLICY STATUS ====================
        # Determine policy status based on start and end dates
        policy_status = "active"  # Default
        start_date_str = extracted_data.get("startDate", "")
        end_date_str = extracted_data.get("endDate", "")

        try:
            from dateutil import parser as dateparser

            def _parse_any_date(date_str: str):
                """Parse date string in any format (YYYY-MM-DD, DD-MM-YYYY, DD/Mon/YYYY, etc.)."""
                # Try ISO format first (fastest path)
                if "-" in date_str:
                    parts = date_str.split("-")
                    if len(parts) == 3 and len(parts[0]) == 4:
                        return datetime.strptime(date_str, "%Y-%m-%d").date()
                # Fall back to dateutil for any other format (DD/Mon/YYYY, DD-MM-YYYY, etc.)
                return dateparser.parse(date_str, dayfirst=True).date()

            if start_date_str and end_date_str:
                current_date = datetime.now().date()

                start_date = _parse_any_date(start_date_str)
                end_date = _parse_any_date(end_date_str)

                # Normalize dates to ISO format in extracted_data for consistent downstream usage
                extracted_data["startDate"] = start_date.strftime("%Y-%m-%d")
                extracted_data["endDate"] = end_date.strftime("%Y-%m-%d")

                # Determine status
                if current_date < start_date:
                    policy_status = "upcoming"
                    logger.info(f"Policy status: upcoming (starts on {start_date})")
                elif current_date > end_date:
                    policy_status = "expired"
                    logger.info(f"Policy status: expired (ended on {end_date})")
                else:
                    policy_status = "active"
                    logger.info(f"Policy status: active (valid from {start_date} to {end_date})")
        except Exception as e:
            logger.warning(f"Could not parse policy dates for status calculation: {str(e)}")
            policy_status = "unknown"  # Don't assume active if dates can't be parsed

        # ==================== BUILD LIGHT ANALYSIS (POLICY ANALYZER) ====================
        # Build the light analysis summary for quick understanding
        insurer_name = extracted_data.get("insuranceProvider", "Insurance Provider")
        plan_name = extracted_data.get("planName", extracted_data.get("policyType", "Insurance Plan"))
        sum_assured = extracted_data.get("coverageAmount", 0)

        # Use motor-specific analysis for motor insurance policies
        if "motor" in detected_policy_type or "car" in detected_policy_type or "vehicle" in detected_policy_type or "auto" in detected_policy_type:
            # BUG #6 FIX: Pass policy start date for accurate vehicle age calculation
            _motor_policy_start = extracted_data.get("startDate", "")
            # V10: Compute detailed motor scores for policyAnalyzer
            try:
                from services.protection_score_calculator import calculate_motor_scores_detailed
                _motor_scores_detailed = calculate_motor_scores_detailed(
                    policy_data=_build_motor_policy_data_for_scoring(complete_category_data, extracted_data),
                    vehicle_age=_get_motor_vehicle_age(complete_category_data, _motor_policy_start),
                    idv=sum_assured or 0,
                    market_value=(sum_assured or 0) * 1.08,  # §7 FIX: inception market value
                    ncb_percentage=_get_motor_ncb_pct(complete_category_data),
                    total_premium=_parse_number_from_string_safe(str(complete_category_data.get("premiumBreakdown", {}).get("totalPremium", 0))),
                    insurer_name=insurer_name,
                    product_type=detect_motor_product_type(extracted_data, complete_category_data),
                )
            except Exception as _mse:
                logger.warning(f"⚠️ Motor V10 scoring failed, using legacy: {_mse}")
                _motor_scores_detailed = None

            # V10: Use deterministic motor gaps instead of AI-generated ones
            # _analyze_motor_gaps is conditional (vehicle age, city, NCB, etc.) and uses actual policy values
            _motor_policy_data = _build_motor_policy_data_for_scoring(complete_category_data, extracted_data)
            _motor_vehicle_age = _get_motor_vehicle_age(complete_category_data, _motor_policy_start)
            _motor_ncb_pct = _get_motor_ncb_pct(complete_category_data)
            _motor_od_premium = _motor_policy_data.get("od_premium", 0)
            _motor_market_value = int((sum_assured or 0) * 1.08)  # §7 FIX: inception market value
            _motor_rto_city = complete_category_data.get("vehicleDetails", {}).get("rtoLocation", "")
            _motor_deterministic_gaps = _analyze_motor_gaps(
                _motor_policy_data, _motor_vehicle_age, sum_assured or 0,
                _motor_market_value, _motor_ncb_pct, _motor_od_premium, _motor_rto_city
            )
            # Use deterministic gaps as formatted_gaps for light analysis
            _motor_formatted_gaps = formatted_gaps if not _motor_deterministic_gaps else _motor_deterministic_gaps

            # Also generate deterministic recommendations
            _motor_deterministic_recs = _generate_motor_recommendations(
                _motor_policy_data, _motor_deterministic_gaps,
                _motor_vehicle_age, _motor_ncb_pct, sum_assured or 0, _motor_market_value
            )

            light_analysis = _build_motor_light_analysis(
                protection_score=protection_score,
                protection_score_label=protection_score_label,
                insurer_name=insurer_name,
                sum_assured=sum_assured,
                formatted_gaps=_motor_formatted_gaps,
                key_benefits=key_benefits,
                recommendations=_motor_deterministic_recs if _motor_deterministic_recs else recommendations,
                category_data=complete_category_data,
                policy_details={
                    "endDate": extracted_data.get("endDate", ""),
                    "startDate": extracted_data.get("startDate", ""),
                },
                enhanced_insights=extracted_data.get("_enhancedInsights", {}),
                scores_detailed=_motor_scores_detailed,
            )
            logger.info(f"✅ Built MOTOR V10 light analysis with protection score: {protection_score}")
        elif "travel" in detected_policy_type:
            # V10: Compute detailed travel scores for policyAnalyzer
            _travel_scores_detailed = None
            try:
                from services.protection_score_calculator import calculate_travel_scores_detailed
                # S1 + S2 use existing travel scoring helpers
                _t_coverage_summary = complete_category_data.get("coverageSummary", {})
                _t_medical_cov = complete_category_data.get("medicalCoverage", {})
                _t_trip_prot = complete_category_data.get("tripProtection", {})
                _t_baggage_cov = complete_category_data.get("baggageCoverage", {})
                _t_travellers = complete_category_data.get("travellerDetails", [])
                _t_dest_countries = complete_category_data.get("tripDetails", {}).get("destinationCountries", [])
                _t_destination = ", ".join(str(c) for c in _t_dest_countries) if isinstance(_t_dest_countries, list) and _t_dest_countries else "International"

                _t_coverage_with_medical = dict(_t_coverage_summary)
                _t_coverage_with_medical["_medicalCoverage"] = _t_medical_cov

                _t_s1 = _calculate_travel_medical_readiness(_t_coverage_with_medical, _t_destination, _t_travellers)
                _t_s2 = _calculate_travel_trip_protection(_t_coverage_summary, _t_trip_prot, _t_baggage_cov)

                _t_is_domestic = False
                if _t_dest_countries:
                    _t_is_domestic = all(
                        str(c).strip().lower() in ("india", "domestic", "")
                        for c in _t_dest_countries if c
                    )
                elif "domestic" in str(complete_category_data.get("tripDetails", {}).get("travelType", "")).lower():
                    _t_is_domestic = True

                _travel_scores_detailed = calculate_travel_scores_detailed(
                    s1_result=_t_s1,
                    s2_result=_t_s2,
                    destination=_t_destination,
                    is_domestic=_t_is_domestic,
                )
            except Exception as _tse:
                logger.warning(f"⚠️ Travel V10 scoring failed, using legacy: {_tse}")
                _travel_scores_detailed = None

            light_analysis = _build_travel_light_analysis(
                protection_score=protection_score,
                protection_score_label=protection_score_label,
                insurer_name=insurer_name,
                sum_assured=sum_assured,
                formatted_gaps=formatted_gaps,
                key_benefits=key_benefits,
                recommendations=recommendations,
                category_data=complete_category_data,
                policy_details={
                    "endDate": extracted_data.get("endDate", ""),
                    "startDate": extracted_data.get("startDate", ""),
                },
                enhanced_insights=extracted_data.get("_enhancedInsights", {}),
                scores_detailed=_travel_scores_detailed,
            )
            logger.info(f"✅ Built TRAVEL V10 light analysis with protection score: {protection_score}")
        else:
            light_analysis = _build_light_analysis(
                protection_score=protection_score,
                protection_score_label=protection_score_label,
                insurer_name=insurer_name,
                plan_name=plan_name,
                sum_assured=sum_assured,
                formatted_gaps=formatted_gaps,
                key_benefits=key_benefits,
                recommendations=recommendations,
                deep_analysis=deep_analysis,
                category_data=complete_category_data,
                policy_type=detected_policy_type,
                city=extracted_data.get("city") or extracted_data.get("location") or "",
                enhanced_insights=extracted_data.get("_enhancedInsights", {})
            )
            logger.info(f"✅ Built light analysis with protection score: {protection_score}")

        # Generate Markdown report content for the light analysis
        light_analysis_md = _generate_light_analysis_md(
            light_analysis=light_analysis,
            policy_details={
                "coverageAmount": sum_assured,
                "insuranceProvider": insurer_name,
                "planName": plan_name,
                "policyType": policy_type or extracted_data.get("policyType", ""),
                "startDate": extracted_data.get("startDate", ""),
                "endDate": extracted_data.get("endDate", "")
            },
            category_data=complete_category_data
        )

        # Note: lightAnalysisReport MD content removed from response as per requirement
        logger.info(f"✅ Generated light analysis (MD report not included in response)")

        # Build policy details UI first so we can move scenarioSimulations to policyAnalyzer
        try:
            policy_details_ui = _build_policy_details_ui(
                extracted_data=extracted_data,
                category_data=complete_category_data,
                policy_type=detected_policy_type,
                policy_status=policy_status,
                original_document_url=original_document_url
            )
        except Exception as ui_err:
            logger.error(f"❌ Error building policy details UI: {str(ui_err)}")
            policy_details_ui = {}

        # Move scenarioSimulations from policyDetailsUI into policyAnalyzer
        if isinstance(policy_details_ui, dict) and "scenarioSimulations" in policy_details_ui:
            sims = policy_details_ui.pop("scenarioSimulations")
            if any(kw in (detected_policy_type or "") for kw in ["motor", "car", "vehicle", "auto"]):
                # V10 motor: wrap into scenarios structure with primary scenario selection
                try:
                    product_type = detect_motor_product_type(extracted_data, complete_category_data) if extracted_data else "COMP_CAR"
                    primary_id = _select_motor_primary_scenario(complete_category_data, formatted_gaps, product_type)
                except Exception:
                    primary_id = "M001"
                light_analysis["scenarios"] = {
                    "primaryScenarioId": primary_id,
                    "simulations": sims if isinstance(sims, list) else [],
                }
            elif (light_analysis.get("protectionReadiness") is not None and
                  ("accidental" in (detected_policy_type or "").lower() or
                   "accident" in (detected_policy_type or "").lower())):
                # V10 PA: wrap scenarios with primaryScenarioId + keep backward compat
                _existing_scenarios = light_analysis.get("scenarios")
                _pa_primary = "PA001"
                if isinstance(_existing_scenarios, dict):
                    _pa_primary = _existing_scenarios.get("primaryScenarioId", "PA001")
                light_analysis["scenarios"] = {
                    "primaryScenarioId": _pa_primary,
                    "simulations": sims if isinstance(sims, list) else [],
                }
                light_analysis["scenarioSimulations"] = sims  # backward compat
            elif "travel" in (detected_policy_type or "").lower():
                # V10 travel: scenarios already has primaryScenarioId from _build_travel_light_analysis
                existing_scenarios = light_analysis.get("scenarios")
                if isinstance(existing_scenarios, dict) and "primaryScenarioId" in existing_scenarios:
                    existing_scenarios["simulations"] = sims if isinstance(sims, list) else []
                else:
                    light_analysis["scenarios"] = {
                        "primaryScenarioId": "T001",
                        "simulations": sims if isinstance(sims, list) else [],
                    }
                light_analysis["scenarioSimulations"] = sims  # backward compat
            else:
                light_analysis["scenarioSimulations"] = sims

        # Move gapAnalysis from policyDetailsUI into policyAnalyzer
        if isinstance(policy_details_ui, dict) and "gapAnalysis" in policy_details_ui:
            gap_analysis_data = policy_details_ui.pop("gapAnalysis")
            if any(kw in (detected_policy_type or "") for kw in ["motor", "car", "vehicle", "auto"]) and isinstance(gap_analysis_data, dict):
                # V10 motor: Merge structured gapAnalysis.gaps (G001-G008 with impact/solution)
                # into the existing coverageGaps to enrich them
                structured_gaps = gap_analysis_data.get("gaps", [])
                existing_coverage_gaps = light_analysis.get("coverageGaps", {})
                existing_gaps_list = existing_coverage_gaps.get("gaps", [])

                if structured_gaps and existing_gaps_list:
                    # Build lookup from structured gaps by gapId and title keywords
                    structured_lookup = {}
                    for sg in structured_gaps:
                        if isinstance(sg, dict):
                            sg_id = sg.get("gapId", "")
                            sg_title = sg.get("title", "").lower()
                            if sg_id:
                                structured_lookup[sg_id] = sg
                            if sg_title:
                                structured_lookup[sg_title] = sg

                    # Enrich existing coverageGaps with structured data
                    for eg in existing_gaps_list:
                        if not isinstance(eg, dict):
                            continue
                        eg_id = eg.get("gapId", "")
                        eg_title = eg.get("title", "").lower()

                        # Try matching by gapId first, then by title keywords
                        matched = structured_lookup.get(eg_id)
                        if not matched:
                            for sg_key, sg_val in structured_lookup.items():
                                if isinstance(sg_key, str) and sg_key in eg_title:
                                    matched = sg_val
                                    break
                                if isinstance(sg_key, str) and eg_title and any(w in sg_key for w in eg_title.split() if len(w) > 3):
                                    matched = sg_val
                                    break

                        if matched:
                            # Enrich with structured data where existing field is empty
                            if not eg.get("impact"):
                                eg["impact"] = matched.get("impact", "")
                            if not eg.get("solution"):
                                eg["solution"] = matched.get("solution", "")
                            if not eg.get("estimatedCost"):
                                eg["estimatedCost"] = matched.get("estimatedCost", "")
                            # Prefer structured gapId (G001-G008 format)
                            if matched.get("gapId", "").startswith("G"):
                                eg["gapId"] = matched["gapId"]

                    # Update summary counts from the enriched gaps
                    high = sum(1 for g in existing_gaps_list if g.get("severity") == "high")
                    medium = sum(1 for g in existing_gaps_list if g.get("severity") == "medium")
                    low = sum(1 for g in existing_gaps_list if g.get("severity") in ("low", "info"))
                    light_analysis["coverageGaps"] = {
                        "summary": {"high": high, "medium": medium, "low": low, "total": len(existing_gaps_list)},
                        "gaps": existing_gaps_list,
                    }
                # Do NOT keep separate gapAnalysis for motor — coverageGaps is the V10 structure
            elif "travel" in (detected_policy_type or "").lower() and light_analysis.get("protectionReadiness"):
                # V10 travel: coverageGaps already in V10 format (summary + gaps), keep gapAnalysis for backward compat
                light_analysis["gapAnalysis"] = gap_analysis_data
            else:
                # Non-motor/non-travel: keep gapAnalysis as-is
                light_analysis["gapAnalysis"] = gap_analysis_data

        # Move recommendations from policyDetailsUI into policyAnalyzer
        if isinstance(policy_details_ui, dict) and "recommendations" in policy_details_ui:
            recs = policy_details_ui.pop("recommendations")
            if any(kw in (detected_policy_type or "") for kw in ["motor", "car", "vehicle", "auto"]):
                # V10 motor: wrap into priorityUpgrades + totalUpgradeCost structure
                # recs can be a dict {"totalRecommendations": N, "recommendations": [list]} or a list
                recs_list = recs.get("recommendations", []) if isinstance(recs, dict) else (recs if isinstance(recs, list) else [])
                priority_upgrades = []
                total_annual = 0
                for rec in recs_list:
                    if isinstance(rec, dict):
                        est_cost = rec.get("estimatedCost", 0)
                        if isinstance(est_cost, str):
                            est_cost = _parse_number_from_string_safe(est_cost)
                        total_annual += est_cost
                        priority_upgrades.append(rec)
                monthly_emi = int(total_annual / 12) if total_annual > 0 else 0
                light_analysis["recommendations"] = {
                    "priorityUpgrades": priority_upgrades,
                    "totalUpgradeCost": {
                        "annual": int(total_annual),
                        "monthlyEmi": monthly_emi,
                    },
                }
            elif (light_analysis.get("protectionReadiness") is not None and
                  ("accidental" in (detected_policy_type or "").lower() or
                   "accident" in (detected_policy_type or "").lower())):
                # V10 PA: recommendations already set in cascade (quickWins + priorityUpgrades + totalUpgradeCost)
                # Keep V9 recs for backward compat only
                light_analysis["recommendationsLegacy"] = recs
            elif "travel" in (detected_policy_type or "").lower() and light_analysis.get("protectionReadiness"):
                # V10 travel: recommendations already set in _build_travel_light_analysis (quickWins + priorityUpgrades + totalUpgradeCost)
                # Keep V9 recs for backward compat only
                light_analysis["recommendationsLegacy"] = recs
            else:
                light_analysis["recommendations"] = recs

        # Remove scoringEngine from policyDetailsUI (not needed in response)
        if isinstance(policy_details_ui, dict) and "scoringEngine" in policy_details_ui:
            policy_details_ui.pop("scoringEngine")

        # Inject PRD v2 universal scores into policyAnalyzer
        if universal_scores:
            light_analysis["universalScores"] = universal_scores

        # Inject PRD v2 zone classification into policyAnalyzer
        if zone_classification:
            light_analysis["zoneClassification"] = zone_classification

        # Inject PRD v2 verdict into policyAnalyzer
        if verdict:
            light_analysis["verdict"] = verdict

        # ==================== OVERRIDE VERDICT FOR EXPIRED POLICIES ====================
        if policy_status == "expired" and verdict and isinstance(verdict, dict):
            verdict["headline"] = "Policy Expired - Renewal Required"
            verdict["actionRequired"] = "urgent"
            logger.info("🔴 Overrode verdict headline for expired policy")

        # ==================== INJECT RENEWAL WARNING FOR EXPIRED POLICIES ====================
        if policy_status == "expired":
            days_expired = 0
            try:
                days_expired = (datetime.now().date() - end_date).days
            except Exception:
                pass
            renewal_rec = {
                "featureId": "policy_expired",
                "featureName": "Policy Status",
                "zone": "red",
                "title": "Renew Expired Policy Immediately",
                "description": f"This policy expired {days_expired} day(s) ago. You currently have NO active coverage. Renew or replace this policy immediately to restore protection.",
                "currentValue": "Expired",
                "explanation": f"Policy ended on {end_date_str}. Any claims during the gap period will not be honoured.",
                "estimatedAnnualCost": {"low": 0, "high": 0},
                "priority": "urgent",
            }
            if isinstance(zone_recommendations, dict):
                urgent_list = zone_recommendations.get("urgent", [])
                urgent_list.insert(0, renewal_rec)
                zone_recommendations["urgent"] = urgent_list
                zone_recommendations["urgentCount"] = len(urgent_list)
            else:
                zone_recommendations = {
                    "urgent": [renewal_rec],
                    "recommended": [],
                    "totalAnnualCost": {"low": 0, "high": 0},
                    "totalMonthlyCost": {"low": 0, "high": 0},
                    "urgentCount": 1,
                    "recommendedCount": 0,
                }
            logger.info(f"🔴 Injected urgent renewal warning: policy expired {days_expired} days ago")

        # Inject PRD v2 zone-based recommendations into policyAnalyzer
        if zone_recommendations:
            # Nest under existing recommendations key if present, else create it
            if "recommendations" not in light_analysis or not isinstance(light_analysis.get("recommendations"), dict):
                # Keep existing recommendations as "legacy" if they're a list
                existing_recs = light_analysis.get("recommendations")
                if isinstance(existing_recs, list):
                    light_analysis["recommendationsLegacy"] = existing_recs
                light_analysis["recommendations"] = {}
            if isinstance(light_analysis["recommendations"], dict):
                light_analysis["recommendations"]["zoneBased"] = zone_recommendations

        response = {
            "success": True,
            "policyId": analysis_id,
            "message": "Policy uploaded and analyzed successfully",

            # ==================== POLICY INFO ====================
            "policy": {
                "policyNumber": extracted_data.get("policyNumber") or None,
                "uin": extracted_data.get("uin") or extracted_uin or None,
                "insuranceProvider": extracted_data.get("insuranceProvider") or None,
                "policyType": policy_type or extracted_data.get("policyType") or None,
                "policyHolderName": policy_holder_name or None,
                "insuredName": insured_name or None,
                "coverageAmount": extracted_data.get("coverageAmount") or None,
                "sumAssured": extracted_data.get("coverageAmount") or None,
                "premium": extracted_data.get("premium") or None,
                "premiumFrequency": extracted_data.get("premiumFrequency") or None,
                "startDate": extracted_data.get("startDate") or None,
                "endDate": extracted_data.get("endDate") or None,
                "status": policy_status,
                "relationship": relationship,
                "originalDocumentUrl": original_document_url or None,
            },

            # ==================== PRD v2 EXTRACTION ====================
            # Filter out null-value fields (confidence 0.0, value null) to keep response clean
            "extraction": {
                v2_category: {
                    k: v for k, v in v2_raw_extraction.items()
                    if not (isinstance(v, dict) and v.get("value") is None)
                },
                "metadata": v2_extraction_metadata,
            } if v2_raw_extraction else None,

            # ==================== CLASSIFICATION ====================
            "classification": classification_result.to_dict() if classification_result else None,
            "dbMatch": {
                "matched": db_match_result.get("matched", False),
                "categoryId": db_match_result.get("validation", {}).get("category_id"),
                "subcategoryId": db_match_result.get("validation", {}).get("subcategory_id"),
                "dbFields": db_match_result.get("db_fields"),
                "topProducts": db_match_result.get("products", [])[:3],
                "productByUin": db_product_by_uin,
            } if db_match_result.get("matched") else None,

            # ==================== VALIDATION ====================
            "validation": {
                "dataQuality": {
                    "hasIssues": data_validation.get("totalIssues", 0) > 0,
                    "hasWarnings": data_validation.get("hasWarnings", False),
                    "hasErrors": data_validation.get("hasErrors", False),
                    "totalIssues": data_validation.get("totalIssues", 0),
                    "warningCount": len(data_validation.get("warnings", [])),
                    "errorCount": len(data_validation.get("errors", [])),
                    "warnings": data_validation.get("warnings", []),
                    "errors": data_validation.get("errors", []),
                    "recommendations": data_validation.get("recommendations", []),
                },
                "fourChecks": four_check_result if four_check_result else None,
                "pdfTextVerification": pdf_text_verification if pdf_text_verification else None,
                "llmVerification": llm_verification_result if llm_verification_result else None,
            },

            # ==================== UNIVERSAL SCORES ====================
            "scores": universal_scores if universal_scores else None,

            # ==================== ZONE CLASSIFICATION ====================
            "zones": zone_classification if zone_classification else None,

            # ==================== VERDICT ====================
            "verdict": verdict if verdict else None,

            # ==================== IRDAI COMPLIANCE ====================
            "compliance": irdai_compliance if irdai_compliance else None,

            # ==================== RECOMMENDATIONS ====================
            "recommendations": zone_recommendations if zone_recommendations else None,

            # ==================== PROVIDER INFO ====================
            "provider": None,  # Populated below

            # ==================== REPORT ====================
            "report": {
                "url": None,
                "fileName": None,
                "error": None,
            },

            "processedAt": datetime.utcnow().isoformat() + "Z",
        }

        # ==================== GET INSURANCE PROVIDER INFORMATION ====================
        try:
            from services.insurance_provider_info import get_insurance_provider_info

            provider_name = extracted_data.get("insuranceProvider", "")
            provider_info = get_insurance_provider_info(provider_name)

            if provider_info:
                response["provider"] = {
                    "providerName": provider_name,
                    "fullName": provider_info.get("fullName"),
                    "type": provider_info.get("type"),
                    "founded": provider_info.get("founded"),
                    "headquarters": provider_info.get("headquarters"),
                    "about": provider_info.get("about"),
                    "claimSettlementRatio": provider_info.get("claimSettlementRatio"),
                    "claimSettlementYear": provider_info.get("claimSettlementYear"),
                    "customerSupport": provider_info.get("customerSupport"),
                    "specialties": provider_info.get("specialties"),
                    "networkSize": provider_info.get("networkSize")
                }
                logger.info(f"✅ Insurance provider info added for: {provider_name}")
        except Exception as e:
            logger.error(f"❌ Error getting provider info: {str(e)}")
            # Non-blocking: Continue even if provider info fails
            response["provider"] = None

        # ==================== GENERATE PDF REPORT AND UPLOAD TO S3 ====================
        report_url = None
        report_error_msg = None

        try:
            from services.policy_report_generator import generate_policy_analysis_report
            from services.life_insurance_report_generator import generate_life_insurance_report
            from services.health_insurance_report_generator import generate_health_insurance_report
            from services.travel_insurance_report_generator import generate_travel_insurance_report
            from services.motor_insurance_report_generator import generate_motor_insurance_report
            from services.pa_insurance_report_generator import generate_pa_insurance_report
            from database_storage.s3_bucket import upload_pdf_to_s3
            import os

            logger.info("🔄 Starting PDF report generation for policy analysis...")

            # Check AWS credentials
            aws_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
            aws_region = os.getenv('AWS_REGION', 'ap-south-1')
            bucket_name = os.getenv('AWS_S3_BUCKET_NAME', 'raceabove-dev')

            if not aws_key or not aws_secret:
                error_msg = "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file."
                logger.error(f"❌ {error_msg}")
                report_error_msg = error_msg
                response["report"]["error"] = report_error_msg
            else:
                logger.info(f"✓ AWS credentials found, bucket: {bucket_name}, region: {aws_region}")

                # Prepare data for PDF generation
                pdf_policy_data = response["policy"]

                # Determine policy type and use appropriate generator
                current_policy_type = response["policy"].get("policyType", "").lower()

                # Generate PDF based on policy type
                logger.info(f"📄 Generating PDF report for {current_policy_type} insurance...")

                if "life" in current_policy_type:
                    logger.info("📄 Using Life Insurance V9 Template generator...")
                    pdf_buffer = generate_life_insurance_report(pdf_policy_data, light_analysis)
                elif "health" in current_policy_type or "medical" in current_policy_type or "mediclaim" in current_policy_type:
                    logger.info("📄 Using Health Insurance V9 Template generator...")
                    pdf_buffer = generate_health_insurance_report(pdf_policy_data, light_analysis)
                elif "travel" in current_policy_type:
                    logger.info("📄 Using Travel Insurance V9 Template generator...")
                    pdf_buffer = generate_travel_insurance_report(pdf_policy_data, light_analysis)
                elif "motor" in current_policy_type or "car" in current_policy_type or "vehicle" in current_policy_type or "auto" in current_policy_type:
                    logger.info("📄 Using Motor Insurance V9 Template generator...")
                    pdf_buffer = generate_motor_insurance_report(pdf_policy_data, light_analysis)
                elif "accidental" in current_policy_type or "accident" in current_policy_type or "pa" in current_policy_type or "personal accident" in current_policy_type:
                    logger.info("📄 Using PA Insurance Template generator...")
                    pdf_buffer = generate_pa_insurance_report(pdf_policy_data, light_analysis)
                else:
                    # Use generic policy report generator for other types
                    pdf_policy_data_generic = {
                        "policyNumber": response["policy"]["policyNumber"],
                        "insuranceProvider": response["policy"]["insuranceProvider"],
                        "policyType": response["policy"]["policyType"],
                        "policyHolderName": response["policy"]["policyHolderName"],
                        "insuredName": response["policy"]["insuredName"],
                        "coverageAmount": response["policy"]["coverageAmount"],
                        "premium": response["policy"]["premium"],
                        "premiumFrequency": response["policy"]["premiumFrequency"],
                        "startDate": response["policy"]["startDate"],
                        "endDate": response["policy"]["endDate"],
                        "status": response["policy"]["status"]
                    }
                    pdf_buffer = generate_policy_analysis_report(pdf_policy_data_generic, light_analysis)

                logger.info("✓ PDF report generated successfully")

                # Upload to S3
                report_filename = f"policy_analysis_{analysis_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
                response["report"]["fileName"] = report_filename
                logger.info(f"☁️  Uploading to S3: {bucket_name}/reports/{report_filename}")

                s3_upload_result = upload_pdf_to_s3(pdf_buffer, report_filename, bucket_name)

                if s3_upload_result.get("success"):
                    report_url = s3_upload_result.get("s3_url")
                    logger.info(f"✅ PDF report uploaded successfully: {report_url}")

                    response["report"]["url"] = report_url
                    response["report"]["error"] = None

                    # Save reportUrl to database
                    try:
                        if mongodb_chat_manager is not None and mongodb_chat_manager.db is not None:
                            db = mongodb_chat_manager.db
                            policy_analysis_collection = db['policy_analysis']
                            policy_analysis_collection.update_one(
                                {"analysisId": analysis_id},
                                {"$set": {"reportUrl": report_url}}
                            )
                            logger.info(f"✅ Report URL saved to database for {analysis_id}")
                    except Exception as db_error:
                        logger.warning(f"Could not save report URL to database: {str(db_error)}")
                else:
                    error_msg = s3_upload_result.get('error', 'Unknown S3 upload error')
                    logger.error(f"❌ Failed to upload PDF to S3: {error_msg}")
                    report_error_msg = f"S3 upload failed: {error_msg}"
                    response["report"]["error"] = report_error_msg

        except Exception as report_error:
            error_msg = str(report_error)
            logger.error(f"❌ Error generating/uploading PDF report: {error_msg}", exc_info=True)
            report_error_msg = f"Report generation failed: {error_msg}"
            # Continue without report URL - don't fail the whole request
            response["report"]["error"] = report_error_msg

        # ==================== SAVE COMPUTED FIELDS TO MONGODB (for GET API parity) ====================
        # light_analysis, deep_analysis, policyDetailsUI are still computed above for MongoDB storage
        try:
            if mongodb_chat_manager is not None and mongodb_chat_manager.db is not None:
                db = mongodb_chat_manager.db
                policy_analysis_collection = db['policy_analysis']
                policy_analysis_collection.update_one(
                    {"analysisId": analysis_id},
                    {"$set": {
                        "policyDetailsUI": policy_details_ui,
                        "deepAnalysis": deep_analysis,
                        "lightAnalysis": light_analysis,
                        "detectedPolicyType": detected_policy_type,
                        "updated_at": datetime.utcnow()
                    }}
                )
                logger.info(f"✅ Computed fields (policyDetailsUI, deepAnalysis, lightAnalysis) saved to MongoDB for {analysis_id}")
        except Exception as db_error:
            logger.warning(f"Could not save computed fields to database: {str(db_error)}")

        # Strip all None values from response recursively
        def _strip_nulls(obj):
            if isinstance(obj, dict):
                return {k: _strip_nulls(v) for k, v in obj.items() if v is not None}
            elif isinstance(obj, list):
                return [_strip_nulls(item) for item in obj]
            return obj

        response = _strip_nulls(response)
        return response

    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he

    except Exception as e:
        logger.error(f"Error in upload_and_analyze_policy: {str(e)}", exc_info=True)

        # Check for specific error types
        if "PDF" in str(e).upper() or "CORRUPT" in str(e).upper() or "DECRYPT" in str(e).upper():
            raise HTTPException(
                status_code=422,
                detail={
                    "success": False,
                    "error_code": "POL_8003",
                    "message": "Unable to extract information from PDF: PDF is corrupted, password protected, or encrypted"
                }
            )

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_code": "SRV_5001",
                "message": "An unexpected error occurred while processing the request",
            }
        )
