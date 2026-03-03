"""
PRD v2 Universal Scores — VFM, Coverage Strength, Claim Readiness.

Three scores computed purely algorithmically from v2 extraction data.
Each score is 0-100 with a label and breakdown. No LLM calls.

Usage:
    from policy_analysis.scoring.universal_scores import compute_universal_scores
    result = compute_universal_scores(v2_raw_extraction, category, insurer_name)
"""
import logging
import re

logger = logging.getLogger(__name__)

# Shared helpers — single source of truth (avoid duplication with zone_classifier)
from policy_analysis.scoring.helpers import (
    val as _val, num as _num, bool_field as _bool_field,
    has_value as _has_value, has_maternity as _has_maternity,
    label as _label, clamp as _clamp,
    lookup_network_hospitals as _lookup_network_hospitals,
    is_schedule_only_health as _is_schedule_only_health,
    is_tp_only_motor as _is_tp_only_motor,
    travel_to_inr as _travel_to_inr,
    effective_ncb_pct as _effective_ncb_pct,
    is_room_rent_unlimited as _is_room_rent_unlimited,
)

# CSR lookup — centralized in utils.py
from policy_analysis.utils import lookup_csr as _lookup_csr


# ==================== COPAY HELPER ====================

def _safe_copay(v2: dict) -> float:
    """Extract copay percentage safely, ignoring age thresholds.

    Handles cases like "None for members below 61 years; 20% co-payment
    for members aged 61 years and above" — extracts 20, NOT 61.
    """
    raw = _val(v2, "generalCopay") or _val(v2, "copay")
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw) if 0 <= raw <= 50 else 0.0
    s = str(raw).lower()
    # If text contains age-related words, only look for explicit N% patterns
    if any(w in s for w in ("year", "age", "member", "above", "below")):
        pcts = re.findall(r'(\d+)\s*%', s)
        return max(float(p) for p in pcts) if pcts else 0.0
    # Normal numeric extraction, but cap at 50% (no real copay exceeds this)
    n = _num(v2, "generalCopay") or _num(v2, "copay")
    return n if 0 <= n <= 50 else 0.0


# ==================== VFM SCORE ====================

def _vfm_health(v2: dict) -> dict:
    """Value for Money: Health insurance."""
    score = 50  # baseline
    breakdown = {}

    si = _num(v2, "sumInsured")
    premium = _num(v2, "totalPremium") or _num(v2, "basePremium")

    # Premium-to-SI ratio (0-35 pts)
    if si > 0 and premium > 0:
        ratio = premium / si
        if ratio <= 0.01:       # <= 1% — excellent
            pts = 35
        elif ratio <= 0.02:     # <= 2%
            pts = 28
        elif ratio <= 0.03:     # <= 3%
            pts = 20
        elif ratio <= 0.05:     # <= 5%
            pts = 12
        else:
            pts = 5
        breakdown["premiumToSiRatio"] = {"ratio": round(ratio, 4), "points": pts}
        score = pts
    else:
        score = 25
        breakdown["premiumToSiRatio"] = {"ratio": None, "points": 25, "note": "Insufficient data"}

    # Feature count bonus (0-30 pts, 3 pts each)
    features = [
        ("restoration", "restoration"),
        ("dayCareProcedures", "dayCareProcedures"),
        ("ambulanceCover", "ambulanceCover"),
        ("ayushTreatment", "ayushTreatment"),
        ("healthCheckup", "healthCheckup"),
        ("noClaimBonus", "ncbPercentage"),
        ("preHospitalization", "preHospitalization"),
        ("postHospitalization", "postHospitalization"),
        ("domiciliaryHospitalization", "domiciliaryTreatment"),
    ]
    feat_count = sum(1 for _, f in features if _has_value(v2, f))
    # Maternity uses dynamic detection (checks multiple fields across insurers)
    if _has_maternity(v2):
        feat_count += 1

    # Schedule-only documents: assume average feature availability (5/10)
    # so the score isn't unfairly penalized for missing document data
    schedule_only = _is_schedule_only_health(v2)
    if schedule_only and feat_count < 5:
        feat_count = 5
        logger.info("Schedule-only document detected: using neutral feature count for VFM")

    feat_pts = min(30, feat_count * 3)
    breakdown["featureCount"] = {"count": feat_count, "maxFeatures": len(features), "points": feat_pts,
                                  **({"scheduleOnly": True} if schedule_only else {})}
    score += feat_pts

    # Room rent (0-15 pts)
    room = _val(v2, "roomRentLimit")
    room_str = str(room).lower() if room else ""
    if _is_room_rent_unlimited(room_str):
        room_pts = 15
    elif room and room_str.strip():
        room_pts = 8  # has limit but exists
    else:
        room_pts = 5
    breakdown["roomRent"] = {"value": room_str[:50] if room else "unknown", "points": room_pts}
    score += room_pts

    # Copay (0-10 pts) — safe extraction handles age-based copay text
    copay = _safe_copay(v2)
    if copay <= 0:
        copay_pts = 10
    elif copay <= 10:
        copay_pts = 6
    elif copay <= 20:
        copay_pts = 3
    else:
        copay_pts = 0
    breakdown["copay"] = {"percentage": copay, "points": copay_pts}
    score += copay_pts

    # NCB bonus (0-10 pts) — uses effective NCB (accumulated bonus vs annual rate)
    ncb = _effective_ncb_pct(v2)
    if ncb >= 50:
        ncb_pts = 10
    elif ncb >= 25:
        ncb_pts = 6
    elif ncb > 0:
        ncb_pts = 3
    else:
        ncb_pts = 0
    breakdown["ncb"] = {"percentage": ncb, "points": ncb_pts}
    score += ncb_pts

    return {"score": _clamp(score), "breakdown": breakdown}


def _vfm_motor(v2: dict) -> dict:
    """Value for Money: Motor insurance."""
    score = 0
    breakdown = {}
    tp_only = _is_tp_only_motor(v2)

    idv = _num(v2, "idv")
    premium = _num(v2, "totalPremium")

    if tp_only:
        # TP-only: IDV ratio not applicable. Use premium affordability instead.
        # TP premiums are regulated by IRDAI, so most are fair by default.
        if premium > 0 and premium <= 5000:
            pts = 30  # very affordable TP
        elif premium <= 15000:
            pts = 25
        else:
            pts = 20
        breakdown["premiumAffordability"] = {"premium": premium, "points": pts, "note": "TP-only: IDV ratio N/A"}
        score += pts
    else:
        # Premium-to-IDV ratio (0-35 pts)
        if idv > 0 and premium > 0:
            ratio = premium / idv
            if ratio <= 0.02:
                pts = 35
            elif ratio <= 0.03:
                pts = 28
            elif ratio <= 0.05:
                pts = 20
            elif ratio <= 0.08:
                pts = 12
            else:
                pts = 5
            breakdown["premiumToIdvRatio"] = {"ratio": round(ratio, 4), "points": pts}
            score += pts
        else:
            score += 20
            breakdown["premiumToIdvRatio"] = {"ratio": None, "points": 20, "note": "Insufficient data"}

    # NCB discount (0-20 pts) — not applicable for TP-only
    ncb = _num(v2, "ncbPercentage")
    if tp_only:
        ncb_pts = 10  # neutral for TP-only (NCB doesn't apply)
        breakdown["ncbDiscount"] = {"percentage": 0, "points": ncb_pts, "note": "TP-only: NCB N/A"}
    elif ncb >= 50:
        ncb_pts = 20
    elif ncb >= 35:
        ncb_pts = 15
    elif ncb >= 20:
        ncb_pts = 10
    elif ncb > 0:
        ncb_pts = 5
    else:
        ncb_pts = 0
    if not tp_only:
        breakdown["ncbDiscount"] = {"percentage": ncb, "points": ncb_pts}
    score += ncb_pts

    # Add-on count bonus (0-30 pts) — not applicable for TP-only
    addons = [
        "zeroDepreciation", "engineProtection", "returnToInvoice",
        "roadsideAssistance", "consumables", "tyreCover", "keyCover",
        "ncbProtect", "personalBaggage", "outstationEmergency",
        "windshieldCover", "passengerCover", "dailyAllowance",
        "emiBreakerCover", "electricVehicleCover", "batteryProtect",
    ]
    if tp_only:
        addon_pts = 15  # neutral — TP-only doesn't have OD add-ons by design
        breakdown["addonCount"] = {"count": 0, "maxAddons": len(addons), "points": addon_pts,
                                   "note": "TP-only: OD add-ons N/A, neutral score applied"}
    else:
        addon_count = sum(1 for a in addons if _bool_field(v2, a) is True)
        addon_pts = min(30, addon_count * 3)
        breakdown["addonCount"] = {"count": addon_count, "maxAddons": len(addons), "points": addon_pts}
    score += addon_pts

    # PA cover included (0-15 pts) — important for both TP and comprehensive
    pa = _num(v2, "paOwnerCover")
    if pa >= 1500000:
        pa_pts = 15
    elif pa > 0:
        pa_pts = 10
    else:
        pa_pts = 0
    breakdown["paCover"] = {"amount": pa, "points": pa_pts}
    score += pa_pts

    if tp_only:
        breakdown["tpOnly"] = True

    return {"score": _clamp(score), "breakdown": breakdown}


def _vfm_life(v2: dict) -> dict:
    """Value for Money: Life insurance."""
    score = 0
    breakdown = {}

    sa = _num(v2, "sumAssured")
    premium = _num(v2, "premiumAmount") or _num(v2, "totalPremium")

    # Premium-to-SA ratio (0-35 pts)
    if sa > 0 and premium > 0:
        ratio = premium / sa
        if ratio <= 0.005:
            pts = 35
        elif ratio <= 0.01:
            pts = 28
        elif ratio <= 0.02:
            pts = 20
        elif ratio <= 0.05:
            pts = 12
        else:
            pts = 5
        breakdown["premiumToSaRatio"] = {"ratio": round(ratio, 5), "points": pts}
        score += pts
    else:
        score += 20
        breakdown["premiumToSaRatio"] = {"ratio": None, "points": 20}

    # Policy term adequacy (0-20 pts)
    term = _num(v2, "policyTerm")
    if term >= 30:
        term_pts = 20
    elif term >= 20:
        term_pts = 15
    elif term >= 10:
        term_pts = 10
    elif term > 0:
        term_pts = 5
    else:
        term_pts = 0
    breakdown["policyTerm"] = {"years": term, "points": term_pts}
    score += term_pts

    # Riders (0-25 pts, 5 pts each)
    riders = _val(v2, "riders")
    rider_count = len(riders) if isinstance(riders, list) else 0
    rider_pts = min(25, rider_count * 5)
    breakdown["riders"] = {"count": rider_count, "points": rider_pts}
    score += rider_pts

    # Death benefit adequacy (0-20 pts)
    death = _num(v2, "deathBenefit")
    if death > 0 and sa > 0:
        if death >= sa:
            death_pts = 20
        elif death >= sa * 0.5:
            death_pts = 12
        else:
            death_pts = 5
    else:
        death_pts = 10  # no data, neutral
    breakdown["deathBenefit"] = {"amount": death, "points": death_pts}
    score += death_pts

    return {"score": _clamp(score), "breakdown": breakdown}


def _vfm_pa(v2: dict) -> dict:
    """Value for Money: Personal Accident insurance."""
    score = 0
    breakdown = {}

    si = _num(v2, "paSumInsured")
    premium = _num(v2, "totalPremium")

    # Premium-to-SI ratio (0-35 pts)
    if si > 0 and premium > 0:
        ratio = premium / si
        if ratio <= 0.005:
            pts = 35
        elif ratio <= 0.01:
            pts = 28
        elif ratio <= 0.02:
            pts = 20
        else:
            pts = 10
        breakdown["premiumToSiRatio"] = {"ratio": round(ratio, 5), "points": pts}
        score += pts
    else:
        score += 20
        breakdown["premiumToSiRatio"] = {"ratio": None, "points": 20}

    # Coverage breadth (0-40 pts)
    # Use field-type-aware counting: bool fields require True, numeric fields require > 0
    cov_count = 0
    if _num(v2, "accidentalDeathBenefitPercentage") > 0:
        cov_count += 1
    for _bf in ("permanentTotalDisabilityCovered", "permanentPartialDisabilityCovered",
                "temporaryTotalDisabilityCovered", "medicalExpensesCovered"):
        if _bool_field(v2, _bf) is True:
            cov_count += 1
    cov_pts = min(40, cov_count * 8)
    breakdown["coverageBreadth"] = {"count": cov_count, "maxCoverages": 5, "points": cov_pts}
    score += cov_pts

    # Additional benefits (0-25 pts) — only count explicitly True booleans
    extras = [
        "educationBenefitCovered", "loanEmiCoverCovered", "ambulanceChargesCovered",
        "transportMortalRemainsCovered", "funeralExpensesCovered",
    ]
    extra_count = sum(1 for f in extras if _bool_field(v2, f) is True)
    extra_pts = min(25, extra_count * 5)
    breakdown["additionalBenefits"] = {"count": extra_count, "points": extra_pts}
    score += extra_pts

    return {"score": _clamp(score), "breakdown": breakdown}


def _vfm_travel(v2: dict) -> dict:
    """Value for Money: Travel insurance."""
    score = 0
    breakdown = {}

    med = _num(v2, "medicalExpenses")
    premium = _num(v2, "travelTotalPremium") or _num(v2, "totalPremium")

    # Premium-to-medical ratio (0-30 pts)
    # Use INR-converted medical for ratio with INR premium
    med_inr = _travel_to_inr(v2, med)
    if med_inr > 0 and premium > 0:
        ratio = premium / med_inr
        if ratio <= 0.005:
            pts = 30
        elif ratio <= 0.01:
            pts = 24
        elif ratio <= 0.02:
            pts = 16
        else:
            pts = 8
        breakdown["premiumToMedicalRatio"] = {"ratio": round(ratio, 5), "points": pts}
        score += pts
    else:
        score += 15
        breakdown["premiumToMedicalRatio"] = {"ratio": None, "points": 15}

    # Coverage breadth (0-45 pts, 5 pts each)
    coverages = [
        "tripCancellation", "tripInterruption", "baggageLoss", "baggageDelay",
        "flightDelay", "personalLiability", "accidentalDeath",
        "emergencyMedicalEvacuation", "passportLoss",
    ]
    cov_count = sum(1 for f in coverages if _has_value(v2, f))
    cov_pts = min(45, cov_count * 5)
    breakdown["coverageBreadth"] = {"count": cov_count, "maxCoverages": len(coverages), "points": cov_pts}
    score += cov_pts

    # Schengen compliance (0-10 pts)
    schengen = _bool_field(v2, "schengenCompliant")
    schengen_pts = 10 if schengen else 0
    breakdown["schengenCompliant"] = {"value": schengen, "points": schengen_pts}
    score += schengen_pts

    # PED coverage (0-15 pts)
    ped = _bool_field(v2, "preExistingCovered")
    ped_pts = 15 if ped else 0
    breakdown["preExistingCovered"] = {"value": ped, "points": ped_pts}
    score += ped_pts

    return {"score": _clamp(score), "breakdown": breakdown}


# ==================== COVERAGE STRENGTH SCORE ====================

def _coverage_health(v2: dict) -> dict:
    """Coverage Strength: Health insurance."""
    score = 0
    breakdown = {}
    schedule_only = _is_schedule_only_health(v2)

    # Sum Insured adequacy (0-20 pts)
    si = _num(v2, "sumInsured")
    if si >= 2500000:       # >= 25L
        si_pts = 20
    elif si >= 1000000:     # >= 10L
        si_pts = 15
    elif si >= 500000:      # >= 5L
        si_pts = 10
    elif si > 0:
        si_pts = 5
    else:
        si_pts = 0
    breakdown["sumInsured"] = {"amount": si, "points": si_pts}
    score += si_pts

    # Room rent (0-12 pts)
    room = _val(v2, "roomRentLimit")
    room_str = str(room).lower() if room else ""
    if _is_room_rent_unlimited(room_str):
        room_pts = 12
    elif room and room_str.strip():
        room_pts = 6
    else:
        room_pts = 6 if schedule_only else 2  # neutral for schedule-only
    breakdown["roomRent"] = {"points": room_pts}
    score += room_pts

    # Copay (0-10 pts) — safe extraction handles age-based copay text
    copay = _safe_copay(v2)
    copay_pts = 10 if copay <= 0 else (6 if copay <= 10 else (3 if copay <= 20 else 0))
    breakdown["copay"] = {"percentage": copay, "points": copay_pts}
    score += copay_pts

    # For schedule-only documents, give neutral (assumed) scores for missing
    # benefit features rather than 0, since the data is simply not in the PDF.
    _neutral = 4 if schedule_only else 0  # ~50% of max for each missing feature

    # Restoration (0-8 pts)
    restore_pts = 8 if _has_value(v2, "restoration") else _neutral
    breakdown["restoration"] = {"available": _has_value(v2, "restoration"), "points": restore_pts,
                                **({"assumed": True} if schedule_only and not _has_value(v2, "restoration") else {})}
    score += restore_pts

    # Day care (0-6 pts)
    dc_pts = 6 if _has_value(v2, "dayCareProcedures") else (3 if schedule_only else 0)
    breakdown["dayCareProcedures"] = {"points": dc_pts}
    score += dc_pts

    # Pre/post hospitalization (0-8 pts)
    pre = _has_value(v2, "preHospitalization")
    post = _has_value(v2, "postHospitalization")
    if schedule_only and not pre and not post:
        hosp_pts = _neutral  # assume partial coverage
    else:
        hosp_pts = (4 if pre else 0) + (4 if post else 0)
    breakdown["hospitalizationCoverage"] = {"pre": pre, "post": post, "points": hosp_pts}
    score += hosp_pts

    # AYUSH (0-5 pts) — cross-reference with exclusions
    # If benefit table explicitly lists AYUSH (e.g. "Covered up to Sum Insured"),
    # trust the benefit table over general exclusion list.
    _ayush_in_excl = False
    _ayush_has_benefit = _has_value(v2, "ayushTreatment")
    _perm_excl = _val(v2, "permanentExclusions")
    if isinstance(_perm_excl, list):
        for _excl_item in _perm_excl:
            _excl_str = str(_excl_item).lower()
            if any(kw in _excl_str for kw in ("ayush", "ayurveda", "homeopath", "unani", "siddha")):
                _ayush_in_excl = True
                break
    if _ayush_in_excl and _ayush_has_benefit:
        ayush_pts = 3  # benefit table overrides exclusion, but partial credit
    elif _ayush_in_excl:
        ayush_pts = 0
    else:
        ayush_pts = 5 if _ayush_has_benefit else (3 if schedule_only else 0)
    breakdown["ayush"] = {"points": ayush_pts}
    score += ayush_pts

    # Ambulance (0-5 pts)
    amb_pts = 5 if _has_value(v2, "ambulanceCover") else (3 if schedule_only else 0)
    breakdown["ambulance"] = {"points": amb_pts}
    score += amb_pts

    # Modern treatments (0-5 pts) — extraction outputs "modernTreatment" (singular)
    modern_pts = 5 if (_has_value(v2, "modernTreatment") or _has_value(v2, "modernTreatments")) else (3 if schedule_only else 0)
    breakdown["modernTreatments"] = {"points": modern_pts}
    score += modern_pts

    # Maternity (0-5 pts) — dynamic detection across multiple field names
    mat_pts = 5 if _has_maternity(v2) else 0  # don't assume maternity
    breakdown["maternity"] = {"points": mat_pts}
    score += mat_pts

    # Mental health (0-5 pts) — extraction outputs "mentalHealthCovered"
    mh_pts = 5 if (_has_value(v2, "mentalHealthCovered") or _has_value(v2, "mentalHealthCover")) else (3 if schedule_only else 0)
    breakdown["mentalHealth"] = {"points": mh_pts}
    score += mh_pts

    # NCB (0-6 pts) — uses effective NCB (accumulated bonus vs annual rate)
    ncb = _effective_ncb_pct(v2)
    ncb_pts = 6 if ncb >= 50 else (4 if ncb >= 20 else (2 if ncb > 0 else 0))
    breakdown["ncb"] = {"points": ncb_pts}
    score += ncb_pts

    # Insured members (0-5 pts)
    members = _val(v2, "insuredMembers")
    mem_count = len(members) if isinstance(members, list) else 0
    mem_pts = 5 if mem_count > 1 else (3 if mem_count == 1 else 0)
    breakdown["insuredMembers"] = {"count": mem_count, "points": mem_pts}
    score += mem_pts

    if schedule_only:
        breakdown["scheduleOnly"] = True
        logger.info("Schedule-only document detected: using neutral coverage scores for missing features")

    return {"score": _clamp(score), "breakdown": breakdown}


def _coverage_motor(v2: dict) -> dict:
    """Coverage Strength: Motor insurance."""
    score = 0
    breakdown = {}
    tp_only = _is_tp_only_motor(v2)

    if tp_only:
        # TP-only scoring: focus on TP-relevant features only
        # Max ~65 pts (PA cover + legal compliance + CSR implied)
        score = 35  # base: TP provides legal-minimum third-party coverage

        # PA cover (0-25 pts) — most important for TP policies
        pa = _num(v2, "paOwnerCover")
        if pa >= 1500000:
            pa_pts = 25
        elif pa > 0:
            pa_pts = 15
        else:
            pa_pts = 0
        breakdown["paCover"] = {"amount": pa, "points": pa_pts}
        score += pa_pts

        # Legal compliance: TP meets IRDAI mandate
        breakdown["legalCompliance"] = {"met": True, "points": 0, "note": "TP policy meets legal minimum"}
        breakdown["tpOnly"] = True

        return {"score": _clamp(score), "breakdown": breakdown}

    # --- Comprehensive / Standalone OD scoring ---

    # IDV adequacy (0-20 pts)
    idv = _num(v2, "idv")
    if idv >= 500000:
        idv_pts = 20
    elif idv >= 300000:
        idv_pts = 15
    elif idv >= 100000:
        idv_pts = 10
    elif idv > 0:
        idv_pts = 5
    else:
        idv_pts = 0
    breakdown["idv"] = {"amount": idv, "points": idv_pts}
    score += idv_pts

    # Product type (0-15 pts)
    ptype = str(_val(v2, "productType") or "").lower()
    if "comprehensive" in ptype or "comp" in ptype:
        ptype_pts = 15
    elif "standalone" in ptype or "own damage" in ptype or "od" in ptype:
        ptype_pts = 10
    else:
        ptype_pts = 8
    breakdown["productType"] = {"value": ptype, "points": ptype_pts}
    score += ptype_pts

    # Add-on coverage (0-42 pts — weighted by importance)
    key_addons = {
        "zeroDepreciation": 8,
        "engineProtection": 7,
        "returnToInvoice": 5,
        "roadsideAssistance": 5,
        "consumables": 5,
        "tyreCover": 4,
        "keyCover": 3,
        "ncbProtect": 5,
    }
    addon_pts = 0
    addon_details = {}
    for addon, pts in key_addons.items():
        bf = _bool_field(v2, addon)
        present = bf is True
        if present:
            addon_pts += pts
        addon_details[addon] = present
    addon_pts = min(42, addon_pts)
    breakdown["addons"] = {"details": addon_details, "points": addon_pts}
    score += addon_pts

    # PA cover (0-10 pts)
    pa = _num(v2, "paOwnerCover")
    pa_pts = 10 if pa >= 1500000 else (7 if pa > 0 else 0)
    breakdown["paCover"] = {"amount": pa, "points": pa_pts}
    score += pa_pts

    # NCB protection (0-8 pts)
    ncb_protect = _bool_field(v2, "ncbProtection")
    ncb_pts = 8 if ncb_protect else 0
    breakdown["ncbProtection"] = {"value": ncb_protect, "points": ncb_pts}
    score += ncb_pts

    # Deductible (0-5 pts — lower is better)
    ded = _num(v2, "compulsoryDeductible")
    ded_pts = 5 if ded <= 1000 else (3 if ded <= 2500 else 0)
    breakdown["deductible"] = {"amount": ded, "points": ded_pts}
    score += ded_pts

    return {"score": _clamp(score), "breakdown": breakdown}


def _coverage_life(v2: dict) -> dict:
    """Coverage Strength: Life insurance."""
    score = 0
    breakdown = {}

    # Sum Assured adequacy (0-25 pts)
    sa = _num(v2, "sumAssured")
    if sa >= 10000000:      # >= 1Cr
        sa_pts = 25
    elif sa >= 5000000:     # >= 50L
        sa_pts = 20
    elif sa >= 2500000:     # >= 25L
        sa_pts = 15
    elif sa > 0:
        sa_pts = 8
    else:
        sa_pts = 0
    breakdown["sumAssured"] = {"amount": sa, "points": sa_pts}
    score += sa_pts

    # Policy term (0-15 pts)
    term = _num(v2, "policyTerm")
    term_pts = 15 if term >= 30 else (12 if term >= 20 else (8 if term >= 10 else (4 if term > 0 else 0)))
    breakdown["policyTerm"] = {"years": term, "points": term_pts}
    score += term_pts

    # Death benefit (0-15 pts)
    death = _num(v2, "deathBenefit")
    death_pts = 15 if death >= sa and sa > 0 else (10 if death > 0 else 5)
    breakdown["deathBenefit"] = {"amount": death, "points": death_pts}
    score += death_pts

    # Riders (0-20 pts, 5 pts each)
    riders = _val(v2, "riders")
    rider_count = len(riders) if isinstance(riders, list) else 0
    rider_pts = min(20, rider_count * 5)
    breakdown["riders"] = {"count": rider_count, "points": rider_pts}
    score += rider_pts

    # Nominees (0-10 pts)
    nominees = _val(v2, "nominees")
    nom_count = len(nominees) if isinstance(nominees, list) else 0
    nom_pts = 10 if nom_count > 0 else 0
    breakdown["nominees"] = {"count": nom_count, "points": nom_pts}
    score += nom_pts

    # Bonus (0-10 pts)
    bonus_pts = 10 if _has_value(v2, "bonusType") else 0
    breakdown["bonus"] = {"points": bonus_pts}
    score += bonus_pts

    # Surrender value (0-5 pts)
    surr_pts = 5 if _has_value(v2, "surrenderValue") else 0
    breakdown["surrenderValue"] = {"points": surr_pts}
    score += surr_pts

    return {"score": _clamp(score), "breakdown": breakdown}


def _coverage_pa(v2: dict) -> dict:
    """Coverage Strength: PA insurance."""
    score = 0
    breakdown = {}

    # Sum Insured (0-20 pts)
    si = _num(v2, "paSumInsured")
    si_pts = 20 if si >= 5000000 else (15 if si >= 2500000 else (10 if si >= 1000000 else (5 if si > 0 else 0)))
    breakdown["sumInsured"] = {"amount": si, "points": si_pts}
    score += si_pts

    # AD benefit (0-15 pts)
    ad_pct = _num(v2, "accidentalDeathBenefitPercentage")
    ad_pts = 15 if ad_pct >= 100 else (10 if ad_pct > 0 else 0)
    breakdown["accidentalDeath"] = {"percentage": ad_pct, "points": ad_pts}
    score += ad_pts

    # PTD (0-15 pts)
    ptd = _bool_field(v2, "permanentTotalDisabilityCovered")
    ptd_pts = 15 if ptd else 0
    breakdown["ptd"] = {"covered": ptd, "points": ptd_pts}
    score += ptd_pts

    # PPD (0-15 pts)
    ppd = _bool_field(v2, "permanentPartialDisabilityCovered")
    ppd_pts = 15 if ppd else 0
    breakdown["ppd"] = {"covered": ppd, "points": ppd_pts}
    score += ppd_pts

    # TTD (0-10 pts)
    ttd = _bool_field(v2, "temporaryTotalDisabilityCovered")
    ttd_pts = 10 if ttd else 0
    breakdown["ttd"] = {"covered": ttd, "points": ttd_pts}
    score += ttd_pts

    # Medical expenses (0-10 pts)
    med = _bool_field(v2, "medicalExpensesCovered")
    med_pts = 10 if med else 0
    breakdown["medicalExpenses"] = {"covered": med, "points": med_pts}
    score += med_pts

    # Additional benefits (0-15 pts)
    extras = ["educationBenefitCovered", "loanEmiCoverCovered", "ambulanceChargesCovered",
              "transportMortalRemainsCovered", "funeralExpensesCovered"]
    extra_count = sum(1 for f in extras if _bool_field(v2, f) is True)
    extra_pts = min(15, extra_count * 3)
    breakdown["additionalBenefits"] = {"count": extra_count, "points": extra_pts}
    score += extra_pts

    return {"score": _clamp(score), "breakdown": breakdown}


def _coverage_travel(v2: dict) -> dict:
    """Coverage Strength: Travel insurance."""
    score = 0
    breakdown = {}

    # Medical expenses (0-20 pts) — currency-aware thresholds
    med = _num(v2, "medicalExpenses")
    med_inr = _travel_to_inr(v2, med)
    if med_inr >= 5000000:      # >= ₹50L (~$60K)
        med_pts = 20
    elif med_inr >= 2500000:    # >= ₹25L (~$30K)
        med_pts = 15
    elif med_inr >= 1000000:    # >= ₹10L (~$12K)
        med_pts = 10
    elif med_inr > 0:
        med_pts = 5
    else:
        med_pts = 0
    breakdown["medicalExpenses"] = {"amount": med, "points": med_pts}
    score += med_pts

    # Trip cancellation (0-12 pts)
    tc = _has_value(v2, "tripCancellation")
    breakdown["tripCancellation"] = {"available": tc, "points": 12 if tc else 0}
    score += 12 if tc else 0

    # Trip interruption (0-8 pts)
    ti = _has_value(v2, "tripInterruption")
    breakdown["tripInterruption"] = {"available": ti, "points": 8 if ti else 0}
    score += 8 if ti else 0

    # Baggage (0-10 pts)
    bag = _has_value(v2, "baggageLoss")
    bag_delay = _has_value(v2, "baggageDelay")
    bag_pts = (6 if bag else 0) + (4 if bag_delay else 0)
    breakdown["baggage"] = {"loss": bag, "delay": bag_delay, "points": bag_pts}
    score += bag_pts

    # Flight delay (0-8 pts)
    fd = _has_value(v2, "flightDelay")
    breakdown["flightDelay"] = {"available": fd, "points": 8 if fd else 0}
    score += 8 if fd else 0

    # Emergency evacuation (0-12 pts)
    evac = _has_value(v2, "emergencyMedicalEvacuation")
    breakdown["evacuation"] = {"available": evac, "points": 12 if evac else 0}
    score += 12 if evac else 0

    # Personal liability (0-10 pts)
    pl = _has_value(v2, "personalLiability")
    breakdown["personalLiability"] = {"available": pl, "points": 10 if pl else 0}
    score += 10 if pl else 0

    # PED coverage (0-10 pts)
    ped = _bool_field(v2, "preExistingCovered")
    breakdown["preExistingCovered"] = {"value": ped, "points": 10 if ped else 0}
    score += 10 if ped else 0

    # Adventure sports (0-10 pts)
    adv = _bool_field(v2, "adventureSportsExclusion")
    # If exclusion is False, adventure IS covered
    adv_covered = adv is False
    breakdown["adventureSports"] = {"covered": adv_covered, "points": 10 if adv_covered else 0}
    score += 10 if adv_covered else 0

    return {"score": _clamp(score), "breakdown": breakdown}


# ==================== CLAIM READINESS SCORE ====================

def _claim_health(v2: dict, insurer_name: str) -> dict:
    """Claim Readiness: Health. Start at 100, deduct for issues."""
    score = 100
    deductions = []

    # Room rent cap (-15 if capped)
    room = _val(v2, "roomRentLimit")
    room_str = str(room).lower() if room else ""
    if room and not _is_room_rent_unlimited(room_str):
        score -= 15
        deductions.append({"reason": "Room rent has cap/limit", "deduction": 15})

    # Copay (-10 to -20) — safe extraction handles age-based copay text
    copay = _safe_copay(v2)
    if copay > 20:
        score -= 20
        deductions.append({"reason": f"High copay ({copay}%)", "deduction": 20})
    elif copay > 10:
        score -= 15
        deductions.append({"reason": f"Moderate copay ({copay}%)", "deduction": 15})
    elif copay > 0:
        score -= 10
        deductions.append({"reason": f"Copay present ({copay}%)", "deduction": 10})

    # Waiting periods
    # PEC: skip deduction if waiting period has been completed (long-standing policies)
    pec = _val(v2, "preExistingDiseaseWaiting")
    pec_str = str(pec).lower() if pec else ""
    pec_completed = _bool_field(v2, "pedWaitingPeriodCompleted") is True
    pec_months = 0
    if pec_str:
        m = re.search(r'(\d+)', pec_str)
        if m:
            val = int(m.group(1))
            # Could be months or years
            pec_months = val if val > 12 else val * 12 if "year" in pec_str else val
    if not pec_completed and "waiv" not in pec_str:
        if pec_months > 48:
            score -= 15
            deductions.append({"reason": f"Long PEC waiting ({pec_months} months)", "deduction": 15})
        elif pec_months > 24:
            score -= 8
            deductions.append({"reason": f"PEC waiting ({pec_months} months)", "deduction": 8})

    initial_wait = _val(v2, "initialWaitingPeriod")
    iw_str = str(initial_wait).lower() if initial_wait else ""
    if not iw_str.strip():
        pass  # no data
    elif "no" in iw_str and "wait" in iw_str:
        pass  # "No waiting period" / "No waiting" — best case, no deduction
    elif "nil" in iw_str or iw_str.strip() == "0" or "0 day" in iw_str:
        pass  # zero waiting — no deduction
    elif "waiv" in iw_str:
        pass  # "Waived Off" / "Waived" — no deduction
    elif "30" in iw_str or "1 month" in iw_str:
        pass  # standard 30 days, no deduction
    elif initial_wait and iw_str.strip():
        score -= 3
        deductions.append({"reason": f"Initial waiting: {iw_str[:30]}", "deduction": 3})

    # CSR (-5 to -15)
    csr = _lookup_csr(insurer_name)
    if csr > 0:
        if csr >= 95:
            pass  # excellent
        elif csr >= 85:
            score -= 5
            deductions.append({"reason": f"CSR is good but not excellent ({csr}%)", "deduction": 5})
        elif csr >= 70:
            score -= 10
            deductions.append({"reason": f"CSR is moderate ({csr}%)", "deduction": 10})
        else:
            score -= 15
            deductions.append({"reason": f"Low CSR ({csr}%)", "deduction": 15})

    # Network hospitals
    hospitals = _num(v2, "networkHospitalsCount") or _lookup_network_hospitals(insurer_name)
    if hospitals > 0:
        if hospitals >= 10000:
            pass
        elif hospitals >= 5000:
            score -= 3
            deductions.append({"reason": f"Network ({hospitals} hospitals)", "deduction": 3})
        elif hospitals >= 2000:
            score -= 8
            deductions.append({"reason": f"Limited network ({hospitals} hospitals)", "deduction": 8})
        else:
            score -= 12
            deductions.append({"reason": f"Small network ({hospitals} hospitals)", "deduction": 12})

    # No restoration (-5) — skip for schedule-only documents (data not in PDF)
    if not _has_value(v2, "restoration"):
        if _is_schedule_only_health(v2):
            deductions.append({"reason": "Restoration: not found in document (schedule-only)", "deduction": 0})
        else:
            score -= 5
            deductions.append({"reason": "No restoration benefit", "deduction": 5})

    return {"score": _clamp(score), "deductions": deductions, "csr": csr}


def _claim_motor(v2: dict, insurer_name: str) -> dict:
    """Claim Readiness: Motor. Start at 100, deduct for issues."""
    score = 100
    deductions = []
    tp_only = _is_tp_only_motor(v2)

    if tp_only:
        # TP-only: only deduct for TP-relevant issues (CSR, PA cover)
        # OD-specific features (zero dep, engine, consumables) don't apply.
        csr = _lookup_csr(insurer_name)
        if 0 < csr < 90:
            deduct = 10 if csr < 80 else 5
            score -= deduct
            deductions.append({"reason": f"CSR ({csr}%)", "deduction": deduct})

        # PA cover check
        pa = _num(v2, "paOwnerCover")
        if pa < 1500000:
            score -= 10
            deductions.append({"reason": "PA cover below IRDAI ₹15L minimum", "deduction": 10})

        # TP context deduction (mild — it IS the legal minimum)
        score -= 5
        deductions.append({"reason": "TP-only: no own damage coverage", "deduction": 5})

        return {"score": _clamp(score), "deductions": deductions, "csr": csr}

    # --- Comprehensive / Standalone OD ---

    # No zero dep (-15)
    zd = _bool_field(v2, "zeroDepreciation")
    if not zd:
        score -= 15
        deductions.append({"reason": "No zero depreciation cover", "deduction": 15})

    # Deductible
    ded = _num(v2, "compulsoryDeductible")
    vol_ded = _num(v2, "voluntaryDeductible")
    total_ded = ded + vol_ded
    if total_ded > 5000:
        score -= 10
        deductions.append({"reason": f"High total deductible ({total_ded:,.0f})", "deduction": 10})
    elif total_ded > 2500:
        score -= 5
        deductions.append({"reason": f"Moderate deductible ({total_ded:,.0f})", "deduction": 5})

    # No engine protection (-8)
    if not (_bool_field(v2, "engineProtection") is True):
        score -= 8
        deductions.append({"reason": "No engine protection", "deduction": 8})

    # No RSA (-5)
    if not (_bool_field(v2, "roadsideAssistance") is True):
        score -= 5
        deductions.append({"reason": "No roadside assistance", "deduction": 5})

    # CSR
    csr = _lookup_csr(insurer_name)
    if 0 < csr < 90:
        deduct = 10 if csr < 80 else 5
        score -= deduct
        deductions.append({"reason": f"CSR ({csr}%)", "deduction": deduct})

    # No NCB protection (-5)
    if not (_bool_field(v2, "ncbProtection") is True):
        score -= 5
        deductions.append({"reason": "No NCB protection", "deduction": 5})

    return {"score": _clamp(score), "deductions": deductions, "csr": csr}


def _claim_life(v2: dict, insurer_name: str) -> dict:
    """Claim Readiness: Life. Start at 100, deduct for issues."""
    score = 100
    deductions = []

    # CSR
    csr = _lookup_csr(insurer_name)
    if 0 < csr < 95:
        deduct = 15 if csr < 85 else (8 if csr < 90 else 3)
        score -= deduct
        deductions.append({"reason": f"CSR ({csr}%)", "deduction": deduct})

    # No nominees (-10)
    nominees = _val(v2, "nominees")
    if not isinstance(nominees, list) or len(nominees) == 0:
        score -= 10
        deductions.append({"reason": "No nominee designated", "deduction": 10})

    # No riders (-8)
    riders = _val(v2, "riders")
    if not isinstance(riders, list) or len(riders) == 0:
        score -= 8
        deductions.append({"reason": "No riders attached", "deduction": 8})

    # Suicide clause (-3)
    suicide = _val(v2, "suicideClause")
    if suicide:
        score -= 3
        deductions.append({"reason": "Suicide exclusion clause present", "deduction": 3})

    # Low SA
    sa = _num(v2, "sumAssured")
    if 0 < sa < 1000000:
        score -= 10
        deductions.append({"reason": f"Low Sum Assured ({sa:,.0f})", "deduction": 10})

    # Short term
    term = _num(v2, "policyTerm")
    if 0 < term < 10:
        score -= 5
        deductions.append({"reason": f"Short policy term ({term} years)", "deduction": 5})

    return {"score": _clamp(score), "deductions": deductions, "csr": csr}


def _claim_pa(v2: dict, insurer_name: str) -> dict:
    """Claim Readiness: PA. Start at 100, deduct for issues."""
    score = 100
    deductions = []

    # CSR
    csr = _lookup_csr(insurer_name)
    if 0 < csr < 90:
        deduct = 10 if csr < 80 else 5
        score -= deduct
        deductions.append({"reason": f"CSR ({csr}%)", "deduction": deduct})

    # No PTD coverage (-12)
    ptd = _bool_field(v2, "permanentTotalDisabilityCovered")
    if not ptd:
        score -= 12
        deductions.append({"reason": "No PTD coverage", "deduction": 12})

    # No PPD coverage (-10)
    ppd = _bool_field(v2, "permanentPartialDisabilityCovered")
    if not ppd:
        score -= 10
        deductions.append({"reason": "No PPD coverage", "deduction": 10})

    # No TTD (-8)
    ttd = _bool_field(v2, "temporaryTotalDisabilityCovered")
    if not ttd:
        score -= 8
        deductions.append({"reason": "No TTD coverage", "deduction": 8})

    # No medical expenses (-8)
    med = _bool_field(v2, "medicalExpensesCovered")
    if not med:
        score -= 8
        deductions.append({"reason": "No medical expenses coverage", "deduction": 8})

    # Occupation restrictions (-5)
    restrictions = _val(v2, "paOccupationRestrictions")
    if isinstance(restrictions, list) and len(restrictions) > 0:
        score -= 5
        deductions.append({"reason": f"Occupation restrictions ({len(restrictions)} items)", "deduction": 5})

    # Low SI
    si = _num(v2, "paSumInsured")
    if 0 < si < 500000:
        score -= 8
        deductions.append({"reason": f"Low Sum Insured ({si:,.0f})", "deduction": 8})

    return {"score": _clamp(score), "deductions": deductions, "csr": csr}


def _claim_travel(v2: dict, insurer_name: str) -> dict:
    """Claim Readiness: Travel. Start at 100, deduct for issues."""
    score = 100
    deductions = []

    # PED not covered (-15)
    ped = _bool_field(v2, "preExistingCovered")
    if not ped:
        score -= 15
        deductions.append({"reason": "Pre-existing conditions not covered", "deduction": 15})

    # No trip cancellation (-10)
    if not _has_value(v2, "tripCancellation"):
        score -= 10
        deductions.append({"reason": "No trip cancellation cover", "deduction": 10})

    # No evacuation (-10)
    if not _has_value(v2, "emergencyMedicalEvacuation"):
        score -= 10
        deductions.append({"reason": "No emergency evacuation cover", "deduction": 10})

    # High deductible — check both field names, convert to INR for thresholds
    ded = _num(v2, "deductiblePerClaim") or _num(v2, "medicalDeductible")
    ded_inr = _travel_to_inr(v2, ded) if ded > 0 else 0
    if ded_inr > 5000:
        score -= 8
        deductions.append({"reason": f"High deductible per claim ({ded:,.0f})", "deduction": 8})
    elif ded_inr > 0:
        score -= 3
        deductions.append({"reason": f"Deductible per claim ({ded:,.0f})", "deduction": 3})

    # No cashless
    cashless = _bool_field(v2, "cashlessNetworkAvailable")
    if cashless is False:
        score -= 8
        deductions.append({"reason": "No cashless network", "deduction": 8})

    # Adventure sports excluded
    adv_excl = _bool_field(v2, "adventureSportsExclusion")
    if adv_excl is True:
        score -= 5
        deductions.append({"reason": "Adventure sports excluded", "deduction": 5})

    # No personal liability
    if not _has_value(v2, "personalLiability"):
        score -= 5
        deductions.append({"reason": "No personal liability cover", "deduction": 5})

    # CSR
    csr = _lookup_csr(insurer_name)
    if 0 < csr < 90:
        deduct = 8 if csr < 80 else 4
        score -= deduct
        deductions.append({"reason": f"CSR ({csr}%)", "deduction": deduct})

    return {"score": _clamp(score), "deductions": deductions, "csr": csr}


# ==================== ROUTER FUNCTIONS ====================

_VFM_ROUTER = {
    "health": _vfm_health,
    "motor": _vfm_motor,
    "life": _vfm_life,
    "pa": _vfm_pa,
    "travel": _vfm_travel,
}

_COVERAGE_ROUTER = {
    "health": _coverage_health,
    "motor": _coverage_motor,
    "life": _coverage_life,
    "pa": _coverage_pa,
    "travel": _coverage_travel,
}

_CLAIM_ROUTER = {
    "health": _claim_health,
    "motor": _claim_motor,
    "life": _claim_life,
    "pa": _claim_pa,
    "travel": _claim_travel,
}


# ==================== PUBLIC API ====================

def compute_universal_scores(
    v2_raw_extraction: dict,
    category: str,
    insurer_name: str = "",
) -> dict:
    """Compute 3 universal scores from v2 extraction data.

    Args:
        v2_raw_extraction: Raw v2 extraction (ConfidenceField format).
        category: Detected category (health/motor/life/pa/travel).
        insurer_name: Insurer name for CSR lookup.

    Returns:
        {
            "vfm": {"score": int, "label": str, "breakdown": {...}},
            "coverageStrength": {"score": int, "label": str, "breakdown": {...}},
            "claimReadiness": {"score": int, "label": str, "deductions": [...], "csr": float},
        }
    """
    if not v2_raw_extraction:
        empty = {"score": 0, "label": "Weak", "breakdown": {}}
        return {
            "vfm": empty,
            "coverageStrength": empty,
            "claimReadiness": {"score": 0, "label": "Weak", "deductions": [], "csr": 0.0},
        }

    # Resolve insurer from extraction if not provided
    if not insurer_name:
        insurer_name = str(_val(v2_raw_extraction, "insurerName") or "")

    # VFM
    vfm_fn = _VFM_ROUTER.get(category, _vfm_health)
    vfm = vfm_fn(v2_raw_extraction)
    vfm["label"] = _label(vfm["score"])

    # Coverage Strength
    cov_fn = _COVERAGE_ROUTER.get(category, _coverage_health)
    cov = cov_fn(v2_raw_extraction)
    cov["label"] = _label(cov["score"])

    # Claim Readiness
    claim_fn = _CLAIM_ROUTER.get(category, _claim_health)
    claim = claim_fn(v2_raw_extraction, insurer_name)
    claim["label"] = _label(claim["score"])

    logger.info(
        f"Universal scores [{category}]: "
        f"VFM={vfm['score']} ({vfm['label']}), "
        f"Coverage={cov['score']} ({cov['label']}), "
        f"ClaimReady={claim['score']} ({claim['label']})"
    )

    return {
        "vfm": vfm,
        "coverageStrength": cov,
        "claimReadiness": claim,
    }
