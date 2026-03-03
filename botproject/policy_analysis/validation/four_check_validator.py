"""
PRD v2 Four-Check Validation System.

Validates every v2 extraction through 4 independent checks:
1. Evidence Grounding  — Critical/important fields must have source_page
2. Cross-Field Logic   — Type-specific sanity rules (premium vs SI, dates, etc.)
3. Format Validation   — Dates, currency, percentages in expected formats
4. Confidence Scoring  — Weighted average (critical 3x, important 2x, standard 1x)

Usage:
    from policy_analysis.validation.four_check_validator import run_four_checks
    result = run_four_checks(v2_raw_extraction, category)
"""
import logging
import re
from typing import Any

from policy_analysis.schemas.base import (
    FieldCriticality,
    CRITICALITY_MAPS,
)

logger = logging.getLogger(__name__)

# Weight multipliers for confidence scoring
_WEIGHTS = {
    FieldCriticality.CRITICAL: 3,
    FieldCriticality.IMPORTANT: 2,
    FieldCriticality.STANDARD: 1,
}

# Minimum weighted confidence to pass check 4
_MIN_WEIGHTED_CONFIDENCE = 0.6


# ==================== HELPERS ====================

def _is_confidence_field(val: Any) -> bool:
    """Check if a value looks like a ConfidenceField dict."""
    return (
        isinstance(val, dict)
        and "confidence" in val
        and "value" in val
    )


def _extract_bare(val: Any) -> Any:
    """Get bare value from a ConfidenceField or return as-is."""
    if _is_confidence_field(val):
        return val.get("value")
    return val


def _safe_float(val: Any) -> float | None:
    """Try to coerce to float. Returns None on failure."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = (
            val.replace(",", "")
            .replace("₹", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .replace("$", "")
            .replace("%", "")
            .strip()
        )
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    return None


def _looks_like_date(val: Any) -> bool:
    """Check if a string value looks like a date."""
    if not isinstance(val, str) or not val.strip():
        return False
    # ISO-8601: YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}", val):
        return True
    # DD/MM/YYYY or DD-MM-YYYY
    if re.match(r"^\d{1,2}[/\-]\d{1,2}[/\-]\d{4}", val):
        return True
    # Common text dates like "01 Jan 2024"
    if re.match(r"^\d{1,2}\s+\w{3,9}\s+\d{4}", val):
        return True
    return False


# ==================== CHECK 1: EVIDENCE GROUNDING ====================

def _check_evidence_grounding(v2_extraction: dict, category: str) -> dict:
    """Critical/important fields must have source_page citation.

    Returns:
        {"passed": bool, "issues": [{"field": str, "criticality": str, "issue": str}]}
    """
    criticality_map = CRITICALITY_MAPS.get(category, {})
    issues = []

    for field_name, field_data in v2_extraction.items():
        if not _is_confidence_field(field_data):
            continue

        criticality = criticality_map.get(field_name)
        if criticality not in (FieldCriticality.CRITICAL, FieldCriticality.IMPORTANT):
            continue

        value = field_data.get("value")
        source_page = field_data.get("source_page")

        # Only flag if field has a value but no source page
        if value is not None and source_page is None:
            issues.append({
                "field": field_name,
                "criticality": criticality.value,
                "issue": f"{criticality.value.title()} field '{field_name}' has value but no source_page citation",
            })

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "fieldsChecked": sum(
            1 for f, d in v2_extraction.items()
            if _is_confidence_field(d) and criticality_map.get(f) in (
                FieldCriticality.CRITICAL, FieldCriticality.IMPORTANT
            )
        ),
        "fieldsWithEvidence": sum(
            1 for f, d in v2_extraction.items()
            if _is_confidence_field(d)
            and criticality_map.get(f) in (
                FieldCriticality.CRITICAL, FieldCriticality.IMPORTANT
            )
            and d.get("source_page") is not None
        ),
    }


# ==================== CHECK 2: CROSS-FIELD LOGIC ====================

# Type-specific validation rules
_COVERAGE_FIELD = {
    "health": "sumInsured",
    "motor": "idv",
    "life": "sumAssured",
    "pa": "paSumInsured",
    "travel": "medicalExpenses",
}

_PREMIUM_FIELDS = ["totalPremium", "travelTotalPremium", "premiumAmount"]

_START_DATE_FIELDS = ["policyPeriodStart", "policyIssueDate", "tripStartDate"]
_END_DATE_FIELDS = ["policyPeriodEnd", "tripEndDate", "maturityDate"]


def _get_field_value(v2_extraction: dict, field_name: str) -> Any:
    """Get bare value from a field in v2 extraction."""
    field_data = v2_extraction.get(field_name)
    return _extract_bare(field_data) if field_data else None


def _check_cross_field_logic(v2_extraction: dict, category: str) -> dict:
    """Type-specific sanity checks on extracted values.

    Rules:
    - Coverage amount should be positive
    - Premium should be positive and less than coverage amount
    - Start date should exist if end date exists
    - Type-specific: health SI range, motor IDV range, etc.
    """
    issues = []

    # --- Coverage amount ---
    cov_field = _COVERAGE_FIELD.get(category)
    coverage = _safe_float(_get_field_value(v2_extraction, cov_field)) if cov_field else None

    if coverage is not None and coverage <= 0:
        issues.append({
            "field": cov_field,
            "issue": f"Coverage amount ({cov_field}) is zero or negative: {coverage}",
            "severity": "high",
        })

    # --- Premium ---
    premium = None
    premium_field_used = None
    for pf in _PREMIUM_FIELDS:
        val = _safe_float(_get_field_value(v2_extraction, pf))
        if val is not None and val > 0:
            premium = val
            premium_field_used = pf
            break

    if premium is not None and coverage is not None and coverage > 0:
        if premium > coverage:
            issues.append({
                "field": premium_field_used,
                "issue": f"Premium ({premium:,.0f}) exceeds coverage amount ({coverage:,.0f})",
                "severity": "high",
            })
        # Premium should be reasonable — typically < 20% of coverage for health/life
        if category in ("health", "life") and premium > coverage * 0.5:
            issues.append({
                "field": premium_field_used,
                "issue": f"Premium ({premium:,.0f}) is over 50% of coverage ({coverage:,.0f}) — unusually high",
                "severity": "medium",
            })

    # --- Date logic ---
    start_val = None
    end_val = None
    for sf in _START_DATE_FIELDS:
        v = _get_field_value(v2_extraction, sf)
        if v and _looks_like_date(str(v)):
            start_val = str(v)
            break
    for ef in _END_DATE_FIELDS:
        v = _get_field_value(v2_extraction, ef)
        if v and _looks_like_date(str(v)):
            end_val = str(v)
            break

    if end_val and not start_val:
        issues.append({
            "field": "policyPeriodStart",
            "issue": "End date found but no start date — extraction may be incomplete",
            "severity": "medium",
        })

    # --- Type-specific rules ---
    if category == "health":
        _check_health_logic(v2_extraction, issues)
    elif category == "motor":
        _check_motor_logic(v2_extraction, issues)
    elif category == "life":
        _check_life_logic(v2_extraction, issues)
    elif category == "pa":
        _check_pa_logic(v2_extraction, issues)
    elif category == "travel":
        _check_travel_logic(v2_extraction, issues)

    return {
        "passed": len(issues) == 0,
        "issues": issues,
    }


def _check_health_logic(v2: dict, issues: list):
    """Health-specific cross-field rules."""
    si = _safe_float(_get_field_value(v2, "sumInsured"))

    # SI range check (Indian health insurance typically 1L to 10Cr)
    if si is not None and si > 0:
        if si < 50000:
            issues.append({
                "field": "sumInsured",
                "issue": f"Sum Insured ({si:,.0f}) is unusually low for health insurance",
                "severity": "medium",
            })
        if si > 100000000:  # 10 Cr
            issues.append({
                "field": "sumInsured",
                "issue": f"Sum Insured ({si:,.0f}) exceeds 10 Cr — verify extraction",
                "severity": "medium",
            })

    # Copay should be 0-100% — extraction uses "generalCopay"
    copay = _safe_float(_get_field_value(v2, "generalCopay")) or _safe_float(_get_field_value(v2, "copay"))
    if copay is not None and (copay < 0 or copay > 100):
        issues.append({
            "field": "copay",
            "issue": f"Copay percentage ({copay}) is outside 0-100% range",
            "severity": "high",
        })


def _check_motor_logic(v2: dict, issues: list):
    """Motor-specific cross-field rules."""
    idv = _safe_float(_get_field_value(v2, "idv"))
    od = _safe_float(_get_field_value(v2, "odPremium"))
    tp = _safe_float(_get_field_value(v2, "tpPremium"))
    total = _safe_float(_get_field_value(v2, "totalPremium"))

    # PAN entity confusion: 4th char of Indian PAN indicates entity type
    # P=Person, C=Company, F=Firm, H=HUF, A=AOP, T=Trust
    pan = _get_field_value(v2, "ownerPan")
    if pan and isinstance(pan, str) and len(pan) == 10:
        fourth = pan[3].upper()
        if fourth != "P":
            entity_map = {"C": "Company", "F": "Firm", "H": "HUF", "A": "AOP/BOI", "T": "Trust"}
            entity_type = entity_map.get(fourth, "non-personal")
            issues.append({
                "field": "ownerPan",
                "issue": (
                    f"PAN '{pan}' has 4th letter '{fourth}' indicating {entity_type} "
                    f"(not Personal). This is likely the insurer/company PAN, not the policyholder's."
                ),
                "severity": "high",
            })

    # Email entity confusion: detect known insurer/intermediary domain patterns
    owner_email = _get_field_value(v2, "ownerEmail")
    insurer_name = str(_get_field_value(v2, "insurerName") or "").lower()
    if owner_email and isinstance(owner_email, str) and "@" in owner_email:
        email_domain = owner_email.split("@")[-1].lower()
        # Known insurer domains — email from these is the insurer's, not the policyholder's
        _INSURER_DOMAINS = {
            "hdfcergo.com", "icicilombard.com", "bajajallianz.com", "tataaig.com",
            "newindia.co.in", "uiic.co.in", "starhealth.in", "careinsurance.com",
            "nivabupa.com", "godigit.com", "acko.com", "fgiinsurance.in",
            "futuregenerali.in", "reliancegeneral.co.in", "sbigeneral.in",
            "royalsundaram.in", "cholainsurance.com", "iffcotokio.co.in",
            "kotakgi.com", "libertyinsurance.in", "magmahdi.com",
        }
        if email_domain in _INSURER_DOMAINS:
            issues.append({
                "field": "ownerEmail",
                "issue": (
                    f"Email '{owner_email}' uses insurer domain '{email_domain}' — "
                    f"this is the insurer's email, not the policyholder's."
                ),
                "severity": "high",
            })

    # IDV range (Indian motor: typically 50K to 1Cr+)
    if idv is not None and idv > 0 and idv < 10000:
        issues.append({
            "field": "idv",
            "issue": f"IDV ({idv:,.0f}) is unusually low",
            "severity": "medium",
        })

    # Motor premium validation — works across ALL Indian insurers
    # Different insurers structure premiums differently:
    #   Tata AIG: OD (excl. add-ons) + AddOns + TP = gross
    #   ACKO: OD (incl. add-ons) + PA = gross (Standalone OD, no TP)
    # The ONLY reliable universal check is: grossPremium + GST ≈ totalPremium
    gst = _safe_float(_get_field_value(v2, "gst")) or 0
    gross = _safe_float(_get_field_value(v2, "grossPremium"))

    if gross is not None and gross > 0 and total is not None and total > 0 and gst >= 0:
        expected_total = gross + gst
        if abs(expected_total - total) > max(500, total * 0.03):  # 3% tolerance or ₹500 min
            issues.append({
                "field": "totalPremium",
                "issue": (
                    f"Net premium ({gross:,.0f}) + GST ({gst:,.0f}) "
                    f"= {expected_total:,.0f} differs from total ({total:,.0f})"
                ),
                "severity": "medium",
            })

    # NCB percentage should be 0-65%
    ncb = _safe_float(_get_field_value(v2, "ncbPercentage"))
    if ncb is not None and (ncb < 0 or ncb > 65):
        issues.append({
            "field": "ncbPercentage",
            "issue": f"NCB percentage ({ncb}) is outside 0-65% range",
            "severity": "medium",
        })


def _check_life_logic(v2: dict, issues: list):
    """Life-specific cross-field rules."""
    sa = _safe_float(_get_field_value(v2, "sumAssured"))
    premium = _safe_float(_get_field_value(v2, "premiumAmount"))
    term = _safe_float(_get_field_value(v2, "policyTerm"))

    # SA range (typically 1L to 100Cr for life)
    if sa is not None and sa > 0 and sa < 50000:
        issues.append({
            "field": "sumAssured",
            "issue": f"Sum Assured ({sa:,.0f}) is unusually low for life insurance",
            "severity": "medium",
        })

    # Policy term should be reasonable (1 to 100 years)
    if term is not None and term > 0:
        if term > 100:
            issues.append({
                "field": "policyTerm",
                "issue": f"Policy term ({term} years) exceeds 100 years",
                "severity": "high",
            })

    # Premium paying term vs policy term
    ppt = _safe_float(_get_field_value(v2, "premiumPayingTerm"))
    if ppt is not None and term is not None and ppt > 0 and term > 0:
        if ppt > term:
            issues.append({
                "field": "premiumPayingTerm",
                "issue": f"Premium paying term ({ppt}) exceeds policy term ({term})",
                "severity": "high",
            })


def _check_pa_logic(v2: dict, issues: list):
    """PA-specific cross-field rules."""
    si = _safe_float(_get_field_value(v2, "paSumInsured"))
    death_pct = _safe_float(_get_field_value(v2, "accidentalDeathBenefitPercentage"))

    if death_pct is not None and (death_pct < 0 or death_pct > 200):
        issues.append({
            "field": "accidentalDeathBenefitPercentage",
            "issue": f"Accidental death benefit percentage ({death_pct}%) is outside expected range",
            "severity": "medium",
        })

    ptd_pct = _safe_float(_get_field_value(v2, "permanentTotalDisabilityPercentage"))
    if ptd_pct is not None and (ptd_pct < 0 or ptd_pct > 200):
        issues.append({
            "field": "permanentTotalDisabilityPercentage",
            "issue": f"PTD percentage ({ptd_pct}%) is outside expected range",
            "severity": "medium",
        })


def _check_travel_logic(v2: dict, issues: list):
    """Travel-specific cross-field rules."""
    med = _safe_float(_get_field_value(v2, "medicalExpenses"))
    trip_cancel = _safe_float(_get_field_value(v2, "tripCancellation"))

    # Trip cancellation should not exceed medical expenses (usually)
    if med is not None and trip_cancel is not None and med > 0 and trip_cancel > 0:
        if trip_cancel > med * 2:
            issues.append({
                "field": "tripCancellation",
                "issue": (
                    f"Trip cancellation cover ({trip_cancel:,.0f}) is over 2x "
                    f"medical cover ({med:,.0f}) — verify extraction"
                ),
                "severity": "low",
            })


# ==================== CHECK 3: FORMAT VALIDATION ====================

# Fields expected to contain date values
_DATE_FIELDS = {
    "policyPeriodStart", "policyPeriodEnd", "policyIssueDate",
    "tripStartDate", "tripEndDate", "maturityDate",
    "policyholderDob", "lifeAssuredDob", "registrationDate",
    "premiumDueDate",
}

# Fields expected to contain numeric currency values
_CURRENCY_FIELDS = {
    "sumInsured", "totalPremium", "basePremium", "gst",
    "idv", "odPremium", "tpPremium", "grossPremium",
    "sumAssured", "premiumAmount", "deathBenefit",
    "paSumInsured", "medicalExpenses", "travelTotalPremium",
    "travelBasePremium", "travelGst",
    "surrenderValue", "paidUpValue", "loanValue",
    "accidentalDeathBenefitAmount", "tripCancellation",
    "baggageLoss", "personalLiability",
}

# Fields expected to contain percentage values (numeric 0-100)
_PERCENTAGE_FIELDS = {
    "copay", "ncbPercentage", "accidentalDeathBenefitPercentage",
    "permanentTotalDisabilityPercentage", "declaredBonusRate",
}


def _check_format_validation(v2_extraction: dict, category: str) -> dict:
    """Check that field values are in the expected formats.

    - Date fields: should be recognizable date strings
    - Currency fields: should be numeric (not string with ₹)
    - Percentage fields: should be numeric 0-100
    - Policy number: should be non-empty string
    - UIN: should match IRDAI format if present (IRDA/xxx/xxx/...)
    """
    issues = []

    for field_name, field_data in v2_extraction.items():
        if not _is_confidence_field(field_data):
            continue
        value = field_data.get("value")
        if value is None:
            continue

        # Date format check
        if field_name in _DATE_FIELDS:
            if isinstance(value, str) and value.strip() and not _looks_like_date(value):
                issues.append({
                    "field": field_name,
                    "issue": f"Date field '{field_name}' value '{value[:50]}' is not in a recognized date format",
                    "severity": "low",
                })

        # Currency format check — value should be numeric, not string with symbols
        elif field_name in _CURRENCY_FIELDS:
            if isinstance(value, str):
                num = _safe_float(value)
                if num is None:
                    issues.append({
                        "field": field_name,
                        "issue": f"Currency field '{field_name}' value '{value[:50]}' is not numeric",
                        "severity": "low",
                    })

        # Percentage format check
        elif field_name in _PERCENTAGE_FIELDS:
            num = _safe_float(value)
            if num is not None and (num < 0 or num > 100):
                issues.append({
                    "field": field_name,
                    "issue": f"Percentage field '{field_name}' value {num} is outside 0-100 range",
                    "severity": "low",
                })

    # UIN format check
    uin_val = _get_field_value(v2_extraction, "uin")
    if uin_val and isinstance(uin_val, str) and uin_val.strip():
        # IRDAI UIN format: typically alphanumeric with / or -
        uin = uin_val.strip()
        if len(uin) < 5:
            issues.append({
                "field": "uin",
                "issue": f"UIN '{uin}' seems too short (expected IRDAI format)",
                "severity": "low",
            })

    # Policy number check
    pol_val = _get_field_value(v2_extraction, "policyNumber")
    if pol_val is not None and isinstance(pol_val, str) and not pol_val.strip():
        issues.append({
            "field": "policyNumber",
            "issue": "Policy number is empty string",
            "severity": "medium",
        })

    return {
        "passed": len(issues) == 0,
        "issues": issues,
    }


# ==================== CHECK 4: CONFIDENCE SCORING ====================

def _check_confidence_scoring(v2_extraction: dict, category: str) -> dict:
    """Compute weighted confidence and check against threshold.

    Weight: CRITICAL=3x, IMPORTANT=2x, STANDARD=1x.
    Threshold: weighted average must be >= 0.6.
    """
    criticality_map = CRITICALITY_MAPS.get(category, {})

    weighted_sum = 0.0
    weight_total = 0.0
    field_scores = []

    for field_name, field_data in v2_extraction.items():
        if not _is_confidence_field(field_data):
            continue

        confidence = field_data.get("confidence", 0.0)
        if not isinstance(confidence, (int, float)):
            confidence = 0.0

        criticality = criticality_map.get(field_name, FieldCriticality.STANDARD)
        weight = _WEIGHTS[criticality]

        weighted_sum += confidence * weight
        weight_total += weight

        field_scores.append({
            "field": field_name,
            "confidence": round(confidence, 3),
            "criticality": criticality.value,
            "weight": weight,
        })

    weighted_confidence = round(weighted_sum / weight_total, 3) if weight_total > 0 else 0.0
    passed = weighted_confidence >= _MIN_WEIGHTED_CONFIDENCE

    # Identify low-confidence critical fields
    low_confidence_critical = [
        fs for fs in field_scores
        if fs["criticality"] == "critical" and fs["confidence"] < 0.5
    ]

    return {
        "passed": passed,
        "weightedConfidence": weighted_confidence,
        "threshold": _MIN_WEIGHTED_CONFIDENCE,
        "totalFieldsScored": len(field_scores),
        "lowConfidenceCriticalFields": low_confidence_critical,
    }


# ==================== PUBLIC API ====================

def run_four_checks(v2_raw_extraction: dict, category: str) -> dict:
    """Run all 4 validation checks on a v2 extraction result.

    Args:
        v2_raw_extraction: Raw v2 extraction dict (ConfidenceField format).
        category: Detected policy category (health/motor/life/pa/travel).

    Returns:
        {
            "evidenceGrounding": {"passed": bool, "issues": [...]},
            "crossFieldLogic": {"passed": bool, "issues": [...]},
            "formatValidation": {"passed": bool, "issues": [...]},
            "confidenceScoring": {"passed": bool, "weightedConfidence": float},
            "overallValid": bool,
        }
    """
    if not v2_raw_extraction:
        return {
            "evidenceGrounding": {"passed": False, "issues": [{"field": "_", "issue": "No extraction data"}]},
            "crossFieldLogic": {"passed": False, "issues": [{"field": "_", "issue": "No extraction data"}]},
            "formatValidation": {"passed": True, "issues": []},
            "confidenceScoring": {"passed": False, "weightedConfidence": 0.0, "threshold": _MIN_WEIGHTED_CONFIDENCE, "totalFieldsScored": 0, "lowConfidenceCriticalFields": []},
            "overallValid": False,
        }

    check1 = _check_evidence_grounding(v2_raw_extraction, category)
    check2 = _check_cross_field_logic(v2_raw_extraction, category)
    check3 = _check_format_validation(v2_raw_extraction, category)
    check4 = _check_confidence_scoring(v2_raw_extraction, category)

    overall = all([check1["passed"], check2["passed"], check3["passed"], check4["passed"]])

    logger.info(
        f"4-check validation [{category}]: "
        f"evidence={'PASS' if check1['passed'] else 'FAIL'}, "
        f"logic={'PASS' if check2['passed'] else 'FAIL'}, "
        f"format={'PASS' if check3['passed'] else 'FAIL'}, "
        f"confidence={'PASS' if check4['passed'] else 'FAIL'} "
        f"(weighted={check4.get('weightedConfidence', 0)}), "
        f"overall={'VALID' if overall else 'INVALID'}"
    )

    return {
        "evidenceGrounding": check1,
        "crossFieldLogic": check2,
        "formatValidation": check3,
        "confidenceScoring": check4,
        "overallValid": overall,
    }
