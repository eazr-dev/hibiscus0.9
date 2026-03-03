"""
PRD v2 IRDAI Compliance Checker.

Validates extracted policy data against IRDAI regulatory mandates.
Rule-based, no LLM calls. Each check returns pass/fail with explanation.

Checks per type:
  Health: Mental health, AYUSH, modern treatments, day care, moratorium
  Motor:  TP cover mandatory, PA owner-driver ₹15L minimum
  Life:   Section 45 incontestability (3yr), free look period
  PA:     Coverage scope, SI adequacy
  Travel: Medical cover minimums, evacuation
  All:    UIN format validation, grievance escalation info

Usage:
    from policy_analysis.compliance import check_irdai_compliance
    result = check_irdai_compliance(v2_raw_extraction, category)
"""
import re
import logging

from policy_analysis.scoring.helpers import (
    val as _val,
    num as _num,
    bool_field as _bool_field,
    has_value as _has_value,
)

logger = logging.getLogger(__name__)


def _mandate(
    mandate_id: str,
    name: str,
    description: str,
    passed: bool,
    status: str,
    details: str = "",
    regulation: str = "",
) -> dict:
    """Build a single mandate check result."""
    entry = {
        "mandateId": mandate_id,
        "name": name,
        "description": description,
        "passed": passed,
        "status": status,  # "compliant" | "non_compliant" | "not_verified" | "partial"
        "details": details,
    }
    if regulation:
        entry["regulation"] = regulation
    return entry


# ==================== COMMON CHECKS (all types) ====================

def _check_common(v2: dict) -> list[dict]:
    """Checks applicable to all insurance types."""
    mandates = []

    # 1. UIN Format Validation
    # IRDAI UIN format: IRDA/xxx/xxx/xxxx or alphanumeric patterns
    uin = str(_val(v2, "uin") or "")
    if uin.strip():
        # Valid UIN patterns: IRDAI or IRDA prefix, or alphanumeric with slashes
        is_valid_uin = bool(
            re.match(r'^(IRDA[I]?[\s/\-]|[A-Z]{2,}\d{2,})', uin.strip(), re.IGNORECASE)
            or re.match(r'^[A-Z0-9]{5,}[/\-][A-Z0-9]+', uin.strip(), re.IGNORECASE)
        )
        if is_valid_uin:
            mandates.append(_mandate(
                "UIN_FORMAT", "UIN Registration",
                "Policy must have a valid IRDAI-registered UIN (Unique Identification Number).",
                True, "compliant",
                f"UIN: {uin}",
                "IRDAI (Insurance Regulatory and Development Authority) Registration"
            ))
        else:
            mandates.append(_mandate(
                "UIN_FORMAT", "UIN Registration",
                "Policy must have a valid IRDAI-registered UIN.",
                False, "not_verified",
                f"UIN '{uin}' format could not be verified. Please check with your insurer.",
                "IRDAI Registration"
            ))
    else:
        mandates.append(_mandate(
            "UIN_FORMAT", "UIN Registration",
            "Policy must have a valid IRDAI-registered UIN.",
            False, "not_verified",
            "UIN not found in policy document. All IRDAI-approved products must have a UIN.",
            "IRDAI Registration"
        ))

    # 2. Grievance Escalation Info
    # Check if insurer contact / grievance info is present
    has_grievance = (
        _has_value(v2, "insurerTollFree")
        or _has_value(v2, "insurerEmail")
        or _has_value(v2, "grievanceOfficer")
        or _has_value(v2, "ombudsmanDetails")
    )
    if has_grievance:
        mandates.append(_mandate(
            "GRIEVANCE_INFO", "Grievance Redressal Information",
            "Policy must include grievance redressal mechanism and escalation details.",
            True, "compliant",
            "Grievance/contact information found in policy document.",
            "IRDAI (Protection of Policyholders' Interests) Regulations 2017"
        ))
    else:
        mandates.append(_mandate(
            "GRIEVANCE_INFO", "Grievance Redressal Information",
            "Policy must include grievance redressal mechanism and escalation details.",
            False, "not_verified",
            "Grievance redressal information not detected. Your insurer must provide toll-free number, email, and Insurance Ombudsman details.",
            "IRDAI (Protection of Policyholders' Interests) Regulations 2017"
        ))

    # 3. Free Look Period
    free_look = _val(v2, "freeLookPeriod")
    if free_look:
        mandates.append(_mandate(
            "FREE_LOOK", "Free Look Period",
            "IRDAI mandates a free look period (typically 15-30 days) to cancel and get a refund.",
            True, "compliant",
            f"Free look period: {free_look}",
            "IRDAI Circular IRDA/LIFE/CIR/GLD/013/01/2020"
        ))

    return mandates


# ==================== HEALTH INSURANCE CHECKS ====================

def _check_health(v2: dict) -> list[dict]:
    """IRDAI health insurance mandates."""
    mandates = []

    # 1. Mental Health Coverage (mandatory since Oct 2022)
    mh = _bool_field(v2, "mentalHealthCovered") or _bool_field(v2, "mentalHealthCover")
    if mh is True:
        mandates.append(_mandate(
            "MENTAL_HEALTH", "Mental Health Coverage",
            "IRDAI mandates coverage for mental illness treatment in all health policies.",
            True, "compliant",
            "Mental health treatment coverage confirmed.",
            "Mental Healthcare Act 2017 + IRDAI Circular 2022"
        ))
    else:
        mandates.append(_mandate(
            "MENTAL_HEALTH", "Mental Health Coverage",
            "IRDAI mandates coverage for mental illness treatment in all health policies.",
            False, "non_compliant" if mh is False else "not_verified",
            "Mental health coverage not confirmed. As per IRDAI mandate, all health policies must cover mental illness treatment."
            if mh is False else
            "Mental health coverage status not detected in policy. Verify with your insurer.",
            "Mental Healthcare Act 2017 + IRDAI Circular 2022"
        ))

    # 2. AYUSH Treatment Coverage
    ayush = _bool_field(v2, "ayushTreatment") or _has_value(v2, "ayushTreatment")
    if ayush:
        mandates.append(_mandate(
            "AYUSH", "AYUSH Treatment Coverage",
            "IRDAI mandates coverage for Ayurveda, Yoga, Unani, Siddha, and Homeopathy treatments.",
            True, "compliant",
            "AYUSH treatment coverage confirmed.",
            "IRDAI (Health Insurance) Regulations 2016"
        ))
    else:
        mandates.append(_mandate(
            "AYUSH", "AYUSH Treatment Coverage",
            "IRDAI mandates coverage for AYUSH treatments.",
            False, "not_verified",
            "AYUSH coverage not detected. IRDAI requires all health policies to cover AYUSH treatments.",
            "IRDAI (Health Insurance) Regulations 2016"
        ))

    # 3. Modern Treatments / Advanced Procedures
    modern = _has_value(v2, "modernTreatment") or _has_value(v2, "modernTreatments")
    if modern:
        mandates.append(_mandate(
            "MODERN_TREATMENTS", "Modern Treatment Coverage",
            "IRDAI mandates coverage for modern treatments (robotic surgery, stem cell therapy, etc.).",
            True, "compliant",
            "Modern/advanced treatment coverage confirmed.",
            "IRDAI Master Circular on Standardization 2020"
        ))
    else:
        mandates.append(_mandate(
            "MODERN_TREATMENTS", "Modern Treatment Coverage",
            "IRDAI mandates coverage for modern treatments.",
            False, "not_verified",
            "Modern treatment coverage not detected. IRDAI mandates coverage for treatments like robotic surgery, balloon sinuplasty, etc.",
            "IRDAI Master Circular on Standardization 2020"
        ))

    # 4. Day Care Procedures
    dc = _has_value(v2, "dayCareProcedures")
    if dc:
        mandates.append(_mandate(
            "DAY_CARE", "Day Care Procedures",
            "Health policies must cover day care procedures that don't require 24-hour hospitalization.",
            True, "compliant",
            "Day care procedures coverage confirmed.",
            "IRDAI (Health Insurance) Regulations 2016"
        ))
    else:
        mandates.append(_mandate(
            "DAY_CARE", "Day Care Procedures",
            "Health policies must cover day care procedures.",
            False, "not_verified",
            "Day care coverage not detected. Most day care procedures (cataract, dialysis, chemotherapy) should be covered.",
            "IRDAI (Health Insurance) Regulations 2016"
        ))

    # 5. Moratorium Period (8 years)
    # After 8 years of continuous coverage, insurer cannot deny claims citing non-disclosure
    pec_waiting = _val(v2, "preExistingDiseaseWaiting")
    mandates.append(_mandate(
        "MORATORIUM", "8-Year Moratorium",
        "After 8 years of continuous renewal, insurer cannot reject claims citing non-disclosure of pre-existing conditions.",
        True, "compliant",
        f"PEC waiting period: {pec_waiting or 'Standard'}. After 8 years of continuous coverage, the moratorium applies.",
        "Section 45 of Insurance Act + IRDAI Circular 2020"
    ))

    # 6. Pre/Post Hospitalization (standard mandate)
    pre = _has_value(v2, "preHospitalization")
    post = _has_value(v2, "postHospitalization")
    if pre and post:
        mandates.append(_mandate(
            "PRE_POST_HOSP", "Pre/Post Hospitalization Coverage",
            "Health policies should cover pre-hospitalization (30-60 days) and post-hospitalization (60-180 days) expenses.",
            True, "compliant",
            f"Pre: {_val(v2, 'preHospitalization')}, Post: {_val(v2, 'postHospitalization')}",
            "IRDAI Standard Health Policy Guidelines"
        ))

    return mandates


# ==================== MOTOR INSURANCE CHECKS ====================

def _check_motor(v2: dict) -> list[dict]:
    """IRDAI motor insurance mandates."""
    mandates = []

    # 1. Third Party Liability (mandatory under Motor Vehicles Act)
    ptype = str(_val(v2, "productType") or "").lower()
    tp_premium = _num(v2, "tpPremium")
    has_tp = (
        "comprehensive" in ptype
        or "third party" in ptype
        or "tp" in ptype
        or "package" in ptype
        or tp_premium > 0
    )
    if has_tp:
        mandates.append(_mandate(
            "TP_COVER", "Third Party Liability Coverage",
            "Third party liability insurance is mandatory under the Motor Vehicles Act 1988.",
            True, "compliant",
            f"TP coverage {'included in comprehensive policy' if 'comp' in ptype else 'confirmed'}. TP Premium: ₹{tp_premium:,.0f}" if tp_premium > 0 else "TP coverage included.",
            "Motor Vehicles Act 1988, Section 146"
        ))
    elif "standalone" in ptype or "own damage" in ptype or "od" in ptype:
        mandates.append(_mandate(
            "TP_COVER", "Third Party Liability Coverage",
            "Third party liability insurance is mandatory under the Motor Vehicles Act 1988.",
            False, "partial",
            "This is a Standalone OD policy. You MUST have a separate active TP policy for legal compliance. Driving without TP cover is a punishable offence.",
            "Motor Vehicles Act 1988, Section 146"
        ))
    else:
        mandates.append(_mandate(
            "TP_COVER", "Third Party Liability Coverage",
            "Third party liability insurance is mandatory.",
            False, "not_verified",
            "TP coverage status could not be verified. Ensure you have valid third party insurance.",
            "Motor Vehicles Act 1988, Section 146"
        ))

    # 2. PA Owner-Driver Cover (₹15 lakhs mandatory)
    pa = _num(v2, "paOwnerCover")
    if pa >= 1500000:
        mandates.append(_mandate(
            "PA_OWNER", "PA Owner-Driver Cover (₹15 Lakhs)",
            "IRDAI mandates minimum ₹15 lakhs personal accident cover for owner-driver.",
            True, "compliant",
            f"PA cover: ₹{pa:,.0f} (meets ₹15L minimum).",
            "IRDAI Circular IRDAI/NL/CIR/MOT/116/11/2018"
        ))
    elif pa > 0:
        mandates.append(_mandate(
            "PA_OWNER", "PA Owner-Driver Cover (₹15 Lakhs)",
            "IRDAI mandates minimum ₹15 lakhs PA cover for owner-driver.",
            False, "non_compliant",
            f"PA cover: ₹{pa:,.0f} — below mandatory ₹15 lakhs minimum. Request your insurer to increase.",
            "IRDAI Circular IRDAI/NL/CIR/MOT/116/11/2018"
        ))
    else:
        mandates.append(_mandate(
            "PA_OWNER", "PA Owner-Driver Cover (₹15 Lakhs)",
            "IRDAI mandates minimum ₹15 lakhs PA cover for owner-driver.",
            False, "not_verified",
            "PA owner-driver cover not detected. This is mandatory (₹15L minimum) unless you have a standalone PA policy.",
            "IRDAI Circular IRDAI/NL/CIR/MOT/116/11/2018"
        ))

    # 3. Vehicle Registration Validation
    reg_no = str(_val(v2, "registrationNumber") or "")
    if reg_no.strip():
        # Indian registration format: XX-00-XX-0000 or XX00XX0000
        is_valid = bool(re.match(
            r'^[A-Z]{2}\s*[\-]?\s*\d{1,2}\s*[\-]?\s*[A-Z]{1,3}\s*[\-]?\s*\d{1,4}$',
            reg_no.strip().upper()
        ))
        mandates.append(_mandate(
            "REG_NUMBER", "Vehicle Registration",
            "Policy must be linked to a valid registered vehicle.",
            is_valid, "compliant" if is_valid else "not_verified",
            f"Registration: {reg_no}" + (" (valid format)" if is_valid else " (format could not be verified)"),
            "Motor Vehicles Act 1988"
        ))

    # 4. IDV Declaration
    idv = _num(v2, "idv")
    if idv > 0:
        mandates.append(_mandate(
            "IDV_DECLARED", "Insured Declared Value",
            "IDV must be declared and agreed upon as per IRDAI guidelines (within ±10% of market value).",
            True, "compliant",
            f"IDV: ₹{idv:,.0f}. Verify this is within IRDAI's recommended range for your vehicle.",
            "IRDAI Motor Insurance Guidelines"
        ))

    return mandates


# ==================== LIFE INSURANCE CHECKS ====================

def _check_life(v2: dict) -> list[dict]:
    """IRDAI life insurance mandates."""
    mandates = []

    # 1. Section 45 — Incontestability (3 years)
    mandates.append(_mandate(
        "SECTION_45", "Section 45 — Incontestability Clause",
        "After 3 years from policy inception, the insurer cannot contest the policy on grounds of misrepresentation (except fraud).",
        True, "compliant",
        "Section 45 of the Insurance Act protects you: after 3 years, your policy cannot be contested on grounds of misrepresentation.",
        "Insurance Act 1938, Section 45 (amended 2015)"
    ))

    # 2. Free Look Period (15-30 days)
    free_look = _val(v2, "freeLookPeriod")
    if free_look:
        mandates.append(_mandate(
            "FREE_LOOK_LIFE", "Free Look Period",
            "IRDAI mandates 15-day free look period (30 days for online/distance purchase).",
            True, "compliant",
            f"Free look period: {free_look}",
            "IRDAI (Protection of Policyholders' Interests) Regulations 2017"
        ))
    else:
        mandates.append(_mandate(
            "FREE_LOOK_LIFE", "Free Look Period",
            "IRDAI mandates 15-day free look period (30 days for online/distance purchase).",
            True, "compliant",
            "Free look period is mandatory by law even if not explicitly stated in the document. You have 15 days (30 for online purchase) to cancel.",
            "IRDAI (Protection of Policyholders' Interests) Regulations 2017"
        ))

    # 3. Nominee Designation
    nominees = _val(v2, "nominees")
    nom_count = len(nominees) if isinstance(nominees, list) else 0
    if nom_count > 0:
        mandates.append(_mandate(
            "NOMINEE", "Nominee Designation",
            "Life insurance policies must have at least one designated nominee.",
            True, "compliant",
            f"{nom_count} nominee(s) designated.",
            "Insurance Act 1938, Section 39"
        ))
    else:
        mandates.append(_mandate(
            "NOMINEE", "Nominee Designation",
            "Life insurance policies must have at least one designated nominee.",
            False, "non_compliant",
            "No nominee detected. Designate a nominee immediately to ensure smooth claim settlement.",
            "Insurance Act 1938, Section 39"
        ))

    # 4. Sum Assured Adequacy
    sa = _num(v2, "sumAssured")
    premium = _num(v2, "premiumAmount") or _num(v2, "totalPremium")
    if sa > 0 and premium > 0:
        sa_to_premium = sa / premium
        if sa_to_premium >= 10:
            mandates.append(_mandate(
                "SA_ADEQUACY", "Sum Assured Adequacy",
                "IRDAI recommends Sum Assured should be at least 10x annual premium for pure protection.",
                True, "compliant",
                f"SA-to-premium ratio: {sa_to_premium:.1f}x (meets 10x minimum).",
                "IRDAI Life Insurance Guidelines"
            ))
        else:
            mandates.append(_mandate(
                "SA_ADEQUACY", "Sum Assured Adequacy",
                "IRDAI recommends Sum Assured should be at least 10x annual premium.",
                False, "partial",
                f"SA-to-premium ratio: {sa_to_premium:.1f}x (below recommended 10x). This may be an investment-linked or endowment plan.",
                "IRDAI Life Insurance Guidelines"
            ))

    return mandates


# ==================== PA INSURANCE CHECKS ====================

def _check_pa(v2: dict) -> list[dict]:
    """IRDAI personal accident insurance mandates."""
    mandates = []

    # 1. Coverage Scope
    ptd = _bool_field(v2, "permanentTotalDisabilityCovered")
    ad = _has_value(v2, "accidentalDeathBenefitPercentage")
    if ptd and ad:
        mandates.append(_mandate(
            "PA_SCOPE", "PA Coverage Scope",
            "PA policy must cover both accidental death and permanent total disability at minimum.",
            True, "compliant",
            "Both accidental death and PTD coverage confirmed.",
            "IRDAI (Health Insurance) Regulations 2016 — PA Guidelines"
        ))
    else:
        missing = []
        if not ad:
            missing.append("Accidental Death")
        if not ptd:
            missing.append("Permanent Total Disability")
        mandates.append(_mandate(
            "PA_SCOPE", "PA Coverage Scope",
            "PA policy must cover both accidental death and permanent total disability.",
            False, "non_compliant" if missing else "not_verified",
            f"Missing coverage: {', '.join(missing)}. These are essential PA benefits.",
            "IRDAI PA Insurance Guidelines"
        ))

    # 2. SI Adequacy
    si = _num(v2, "paSumInsured")
    if si >= 1000000:
        mandates.append(_mandate(
            "PA_SI", "Sum Insured Adequacy",
            "PA Sum Insured should be adequate to cover income loss and expenses.",
            True, "compliant",
            f"PA Sum Insured: ₹{si:,.0f}.",
            "IRDAI PA Guidelines"
        ))
    elif si > 0:
        mandates.append(_mandate(
            "PA_SI", "Sum Insured Adequacy",
            "PA Sum Insured should be adequate to cover income loss.",
            False, "partial",
            f"PA Sum Insured: ₹{si:,.0f} — consider if this adequately covers your income for 2-3 years.",
            "IRDAI PA Guidelines"
        ))

    return mandates


# ==================== TRAVEL INSURANCE CHECKS ====================

def _check_travel(v2: dict) -> list[dict]:
    """Travel insurance compliance checks."""
    mandates = []

    # 1. Medical Cover Minimum (Schengen requirement)
    med = _num(v2, "medicalExpenses")
    schengen = _bool_field(v2, "schengenCompliant")
    # Currency-aware display and INR conversion for threshold comparison
    currency = _val(v2, "coverageCurrency")
    _cur = (currency.strip().upper() if isinstance(currency, str) and currency.strip() else "")
    if _cur in ("USD", "$", "US DOLLAR", "US DOLLARS"):
        _med_inr = med * 83.0
        _sym = "$"
    elif _cur in ("EUR", "€", "EURO", "EUROS"):
        _med_inr = med * 91.0
        _sym = "€"
    elif _cur in ("GBP", "£", "POUND", "POUNDS"):
        _med_inr = med * 105.0
        _sym = "£"
    elif _cur in ("INR", "₹", "RUPEE", "RUPEES"):
        _med_inr = med
        _sym = "₹"
    else:
        # Heuristic: small amounts likely foreign currency
        _med_inr = med * 83.0 if med < 100000 else med
        _sym = _cur or "₹"
    _med_display = f"{_sym}{med:,.0f}"
    if schengen or _med_inr >= 3000000:  # ~€30,000 Schengen minimum
        mandates.append(_mandate(
            "SCHENGEN", "Schengen Visa Compliance",
            "Schengen countries require minimum €30,000 (approx ₹30L) medical cover.",
            True, "compliant",
            f"Medical cover: {_med_display}. {'Schengen compliant confirmed.' if schengen else 'Meets Schengen minimum.'}",
            "EU Council Regulation (EC) No 810/2009"
        ))
    elif med > 0:
        mandates.append(_mandate(
            "SCHENGEN", "Schengen Visa Compliance",
            "Schengen countries require minimum €30,000 medical cover.",
            False, "partial",
            f"Medical cover: {_med_display} — may not meet Schengen minimum of €30,000 (~₹30 lakhs). Verify if travelling to EU.",
            "EU Council Regulation (EC) No 810/2009"
        ))

    # 2. Emergency Evacuation
    evac = _has_value(v2, "emergencyMedicalEvacuation")
    if evac:
        mandates.append(_mandate(
            "EVACUATION", "Emergency Medical Evacuation",
            "Travel policies should include emergency medical evacuation for international travel.",
            True, "compliant",
            "Emergency medical evacuation coverage confirmed.",
            "IRDAI Travel Insurance Guidelines"
        ))
    else:
        mandates.append(_mandate(
            "EVACUATION", "Emergency Medical Evacuation",
            "Emergency medical evacuation is critical for international travel.",
            False, "not_verified",
            "Emergency evacuation not detected. This is essential for international travel.",
            "IRDAI Travel Insurance Guidelines"
        ))

    return mandates


# ==================== ROUTER ====================

_TYPE_CHECKERS = {
    "health": _check_health,
    "motor": _check_motor,
    "life": _check_life,
    "pa": _check_pa,
    "travel": _check_travel,
}


# ==================== PUBLIC API ====================

def check_irdai_compliance(
    v2_raw_extraction: dict,
    category: str,
) -> dict:
    """Check IRDAI regulatory compliance for a policy.

    Args:
        v2_raw_extraction: Raw v2 extraction (ConfidenceField format).
        category: Detected category (health/motor/life/pa/travel).

    Returns:
        {
            "overallCompliant": bool,
            "totalMandates": int,
            "passedMandates": int,
            "failedMandates": int,
            "notVerified": int,
            "mandates": [
                {
                    "mandateId": str,
                    "name": str,
                    "description": str,
                    "passed": bool,
                    "status": "compliant"|"non_compliant"|"not_verified"|"partial",
                    "details": str,
                    "regulation": str (optional)
                }, ...
            ]
        }
    """
    if not v2_raw_extraction:
        return {
            "overallCompliant": False,
            "totalMandates": 0,
            "passedMandates": 0,
            "failedMandates": 0,
            "notVerified": 0,
            "mandates": [],
        }

    # Common checks (all types)
    mandates = _check_common(v2_raw_extraction)

    # Type-specific checks
    checker = _TYPE_CHECKERS.get(category)
    if checker:
        mandates.extend(checker(v2_raw_extraction))

    # Compute summary
    passed = sum(1 for m in mandates if m["passed"])
    failed = sum(1 for m in mandates if m["status"] == "non_compliant")
    not_verified = sum(1 for m in mandates if m["status"] == "not_verified")
    partial = sum(1 for m in mandates if m["status"] == "partial")

    # Overall compliant if no non_compliant mandates
    overall = failed == 0

    logger.info(
        f"IRDAI compliance [{category}]: "
        f"{passed}/{len(mandates)} passed, "
        f"{failed} non-compliant, {not_verified} not-verified, {partial} partial"
    )

    return {
        "overallCompliant": overall,
        "totalMandates": len(mandates),
        "passedMandates": passed,
        "failedMandates": failed,
        "notVerified": not_verified,
        "mandates": mandates,
    }
