"""
PRD v2 4-Zone Feature Classification.

Classifies every extracted feature into one of 4 zones:
  Zone 1 (green)      - Excellent / No issues
  Zone 2 (lightGreen) - Good / Minor limitations
  Zone 3 (amber)      - Needs attention / Moderate gaps
  Zone 4 (red)        - Critical gap / Immediate action needed

Rule-based, no LLM calls. Operates on v2 ConfidenceField extraction.

Usage:
    from policy_analysis.scoring.zone_classifier import classify_zones
    result = classify_zones(v2_raw_extraction, category, insurer_name)
"""
import logging
import re

logger = logging.getLogger(__name__)

# Shared helpers — single source of truth (avoid duplication with universal_scores)
from policy_analysis.scoring.helpers import (
    val as _val, num as _num, bool_field as _bool_field,
    has_value as _has_value, feature as _feature,
    lookup_network_hospitals as _lookup_network_hospitals,
    parse_months as _parse_months,
    is_schedule_only_health as _is_schedule_only_health,
    is_tp_only_motor as _is_tp_only_motor,
    travel_to_inr as _travel_to_inr,
    travel_currency_symbol as _travel_currency_symbol,
    effective_ncb_pct as _effective_ncb_pct,
    is_room_rent_unlimited as _is_room_rent_unlimited,
)

# CSR lookup — centralized in policy_analysis.utils
from policy_analysis.utils import lookup_csr as _lookup_csr


# ==================== HEALTH ZONE CLASSIFICATION ====================

def _zones_health(v2: dict, insurer_name: str) -> list[dict]:
    features = []
    si = _num(v2, "sumInsured")
    schedule_only = _is_schedule_only_health(v2)

    # 1. Room Rent
    room = _val(v2, "roomRentLimit")
    room_str = str(room).lower() if room else ""
    if not room or not room_str.strip():
        features.append(_feature("room_rent", "Room Rent Limit", "amber",
                                 "Unknown", "Room rent information not available in policy document.",
                                 "Verify room rent terms from your policy document."))
    elif _is_room_rent_unlimited(room_str):
        features.append(_feature("room_rent", "Room Rent Limit", "green",
                                 str(room), "No room rent cap - you can choose any room category without deductions."))
    elif "proportional" in room_str or "deduction" in room_str:
        features.append(_feature("room_rent", "Room Rent Limit", "red",
                                 str(room), "Room rent has proportional deduction clause - claim amounts reduced proportionally if room exceeds limit.",
                                 "Consider upgrading to a plan with no room rent cap."))
    elif si > 0:
        # Check if room_str already specifies a percentage (e.g. "1% of SI")
        pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', room_str)
        if pct_match:
            pct = float(pct_match.group(1))
            if pct >= 2:
                features.append(_feature("room_rent", "Room Rent Limit", "lightGreen",
                                         str(room), f"Room rent cap at {pct}% of Sum Insured - reasonable limit."))
            else:
                features.append(_feature("room_rent", "Room Rent Limit", "amber",
                                         str(room), f"Room rent cap at {pct}% of SI - may restrict hospital choice.",
                                         "Consider a plan with higher room rent limit or no cap."))
        else:
            # Try to extract numeric limit (absolute amount)
            limit_match = re.search(r'(\d[\d,]*)', room_str)
            if limit_match:
                limit_val = float(limit_match.group(1).replace(",", ""))
                ratio = limit_val / si if si > 0 else 0
                if ratio >= 0.02:
                    features.append(_feature("room_rent", "Room Rent Limit", "lightGreen",
                                             str(room), f"Room rent cap at {ratio*100:.1f}% of Sum Insured - reasonable limit."))
                else:
                    features.append(_feature("room_rent", "Room Rent Limit", "amber",
                                             str(room), f"Room rent cap at ₹{limit_val:,.0f} per day - may restrict hospital choice.",
                                             "Consider a plan with higher room rent limit or no cap."))
            else:
                features.append(_feature("room_rent", "Room Rent Limit", "lightGreen",
                                         str(room), "Room rent has a limit - check if it meets your needs."))
    else:
        features.append(_feature("room_rent", "Room Rent Limit", "lightGreen",
                                 str(room), "Room rent has a limit - check if it meets your needs."))

    # 2. Co-pay — extraction uses "generalCopay", fall back to "copay"
    copay = _num(v2, "generalCopay") or _num(v2, "copay")
    copay_str = str(_val(v2, "generalCopay") or _val(v2, "copay") or "")
    if copay <= 0 and ("no" in copay_str.lower() or "nil" in copay_str.lower() or "0" in copay_str or not copay_str.strip()):
        features.append(_feature("copay", "Co-payment", "green",
                                 "0%", "No co-payment - insurer pays 100% of eligible claim amount."))
    elif copay <= 5:
        features.append(_feature("copay", "Co-payment", "lightGreen",
                                 f"{copay}%", f"Low co-pay of {copay}% - minimal out-of-pocket expense during claims."))
    elif copay <= 15:
        features.append(_feature("copay", "Co-payment", "amber",
                                 f"{copay}%", f"Moderate co-pay of {copay}% - you pay {copay}% of every claim.",
                                 "Look for plans with lower or no co-pay to reduce claim-time expenses."))
    else:
        features.append(_feature("copay", "Co-payment", "red",
                                 f"{copay}%", f"High co-pay of {copay}% significantly reduces effective coverage.",
                                 "Strongly consider switching to a plan with lower co-pay."))

    # 3. Sum Insured
    if si >= 2500000:
        features.append(_feature("sum_insured", "Sum Insured", "green",
                                 f"₹{si:,.0f}", "Excellent Sum Insured - adequate for most medical emergencies."))
    elif si >= 1000000:
        features.append(_feature("sum_insured", "Sum Insured", "lightGreen",
                                 f"₹{si:,.0f}", "Good Sum Insured but may fall short for major surgeries or critical illness.",
                                 "Consider a super top-up plan for additional coverage."))
    elif si >= 500000:
        features.append(_feature("sum_insured", "Sum Insured", "amber",
                                 f"₹{si:,.0f}", "Sum Insured may be insufficient given rising healthcare costs.",
                                 "Increase SI to at least ₹10-15 lakhs or add a super top-up."))
    elif si > 0:
        features.append(_feature("sum_insured", "Sum Insured", "red",
                                 f"₹{si:,.0f}", "Sum Insured is critically low for current healthcare costs.",
                                 "Urgently increase SI to at least ₹5-10 lakhs."))

    # 4. Restoration
    restore = _val(v2, "restoration")
    restore_str = str(restore).lower() if restore else ""
    if not restore or not restore_str.strip() or "no" in restore_str or "not" in restore_str:
        if schedule_only:
            features.append(_feature("restoration", "Restoration Benefit", "amber",
                                     "Not found in document", "Restoration benefit details not available in uploaded document. Most comprehensive plans include this.",
                                     "Upload full policy document for complete analysis."))
        else:
            features.append(_feature("restoration", "Restoration Benefit", "red",
                                     "Not Available", "No restoration benefit - once SI is exhausted, no further claims possible in the policy year.",
                                     "Choose a plan with restoration benefit for continuous coverage."))
    elif ("unlimit" in restore_str or "100%" in restore_str or "full" in restore_str
          or "sum insured" in restore_str or "upto si" in restore_str or "up to si" in restore_str):
        features.append(_feature("restoration", "Restoration Benefit", "green",
                                 str(restore), "Full restoration up to Sum Insured - SI gets restored after a claim."))
    elif "50%" in restore_str or "partial" in restore_str:
        features.append(_feature("restoration", "Restoration Benefit", "amber",
                                 str(restore), "Partial restoration only - SI not fully restored after claims.",
                                 "Consider upgrading to a plan with full restoration."))
    elif restore_str in ("true", "yes", "available", "applicable"):
        features.append(_feature("restoration", "Restoration Benefit", "green",
                                 "Available", "Restoration benefit available - SI gets restored after claims."))
    else:
        features.append(_feature("restoration", "Restoration Benefit", "lightGreen",
                                 str(restore), "Restoration benefit available - SI gets restored after claims."))

    # 5. PEC Waiting Period
    pec = _val(v2, "preExistingDiseaseWaiting")
    pec_str = str(pec) if pec else ""
    pec_months = _parse_months(pec_str)
    # Check if PED waiting has already been served (long-standing policies)
    _pec_completed = _bool_field(v2, "pedWaitingPeriodCompleted") is True
    _continuous_yrs = _num(v2, "continuousCoverageYears")
    _pec_served = _pec_completed or (_continuous_yrs > 0 and pec_months > 0 and _continuous_yrs * 12 >= pec_months)
    # "Waived Off" also counts as green
    _pec_waived = "waiv" in pec_str.lower() if pec_str else False
    if pec_months <= 0 and not pec_str.strip() and not _pec_waived:
        pass  # Skip if no data
    elif _pec_waived or _pec_served:
        features.append(_feature("pec_waiting", "Pre-Existing Disease Waiting", "green",
                                 pec_str or "Waived Off",
                                 f"PEC waiting {'waived' if _pec_waived else 'fully served'} - pre-existing conditions covered now."))
    elif pec_months <= 24:
        features.append(_feature("pec_waiting", "Pre-Existing Disease Waiting", "green",
                                 pec_str, f"Short PEC waiting of {pec_months} months - pre-existing conditions covered sooner."))
    elif pec_months <= 36:
        features.append(_feature("pec_waiting", "Pre-Existing Disease Waiting", "lightGreen",
                                 pec_str, f"Standard PEC waiting of {pec_months} months."))
    elif pec_months <= 48:
        features.append(_feature("pec_waiting", "Pre-Existing Disease Waiting", "amber",
                                 pec_str, f"Long PEC waiting of {pec_months} months delays coverage for pre-existing conditions.",
                                 "Look for plans with shorter PEC waiting periods."))
    else:
        features.append(_feature("pec_waiting", "Pre-Existing Disease Waiting", "red",
                                 pec_str, f"Very long PEC waiting of {pec_months} months - significant delay in coverage.",
                                 "Consider plans with 24-36 month PEC waiting."))

    # 6. NCB — uses effective NCB (accumulated bonus vs annual rate)
    ncb = _effective_ncb_pct(v2)
    if ncb >= 50:
        features.append(_feature("ncb", "No Claim Bonus", "green",
                                 f"{ncb:.0f}%", f"Excellent NCB of {ncb:.0f}% - significant increase in SI for claim-free years."))
    elif ncb >= 20:
        features.append(_feature("ncb", "No Claim Bonus", "lightGreen",
                                 f"{ncb:.0f}%", f"Good NCB of {ncb:.0f}% - SI increases for claim-free years."))
    elif ncb > 0:
        features.append(_feature("ncb", "No Claim Bonus", "amber",
                                 f"{ncb:.0f}%", f"Low NCB of {ncb:.0f}% - limited SI increase for claim-free years.",
                                 "Look for plans with higher NCB benefits (50%+)."))
    elif _has_value(v2, "ncbPercentage"):
        features.append(_feature("ncb", "No Claim Bonus", "red",
                                 "None", "No NCB benefit - no reward for claim-free years.",
                                 "Consider plans offering NCB to grow your coverage over time."))

    # 7. Day Care
    dc = _has_value(v2, "dayCareProcedures")
    if dc:
        features.append(_feature("day_care", "Day Care Procedures", "green",
                                 "Covered", "Day care procedures covered - modern treatments that don't require 24hr hospitalization."))
    else:
        if schedule_only:
            features.append(_feature("day_care", "Day Care Procedures", "amber",
                                     "Not found in document", "Day care details not available in uploaded document. Most comprehensive plans cover this.",
                                     "Upload full policy document for complete analysis."))
        else:
            features.append(_feature("day_care", "Day Care Procedures", "red",
                                     "Not Covered", "Day care procedures not covered - many modern treatments excluded.",
                                     "Essential coverage - ensure your plan covers day care procedures."))

    # 8. Pre/Post Hospitalization
    pre = _has_value(v2, "preHospitalization")
    post = _has_value(v2, "postHospitalization")
    if pre and post:
        pre_val = str(_val(v2, "preHospitalization") or "")
        post_val = str(_val(v2, "postHospitalization") or "")
        features.append(_feature("pre_post_hosp", "Pre/Post Hospitalization", "green",
                                 f"Pre: {pre_val[:30]}, Post: {post_val[:30]}",
                                 "Both pre and post hospitalization expenses covered."))
    elif pre or post:
        features.append(_feature("pre_post_hosp", "Pre/Post Hospitalization", "lightGreen",
                                 "Partial", "Only partial pre/post hospitalization coverage.",
                                 "Ensure both pre and post hospitalization expenses are covered."))
    else:
        if schedule_only:
            features.append(_feature("pre_post_hosp", "Pre/Post Hospitalization", "amber",
                                     "Not found in document", "Pre/post hospitalization details not available in uploaded document.",
                                     "Upload full policy document for complete analysis."))
        else:
            features.append(_feature("pre_post_hosp", "Pre/Post Hospitalization", "amber",
                                     "Not Available", "Pre/post hospitalization expenses may not be covered.",
                                     "These expenses add up - look for plans covering both."))

    # 9. AYUSH — cross-reference with exclusions to detect contradictions
    ayush = _has_value(v2, "ayushTreatment")
    # Dynamically check if AYUSH appears in permanent exclusions
    _ayush_excluded = False
    _perm_excl = _val(v2, "permanentExclusions")
    if isinstance(_perm_excl, list):
        for _excl_item in _perm_excl:
            _excl_str = str(_excl_item).lower()
            if any(kw in _excl_str for kw in ("ayush", "ayurveda", "homeopath", "unani", "siddha")):
                if not any(neg in _excl_str for neg in ("not excluded", "covered", "included")):
                    _ayush_excluded = True
                    break
    # If AYUSH has an explicit benefit value (e.g. "Covered up to Sum Insured"),
    # the benefit table takes priority over a general exclusion list.
    if _ayush_excluded and ayush:
        # Benefit table overrides exclusion — treat as covered (lightGreen with note)
        features.append(_feature("ayush", "AYUSH Treatment", "lightGreen",
                                 str(_val(v2, "ayushTreatment")),
                                 "AYUSH covered per benefit table, though listed in general exclusions. Verify specific sub-limits with insurer."))
    elif _ayush_excluded:
        features.append(_feature("ayush", "AYUSH Treatment", "red",
                                 "Excluded", "AYUSH treatments found in permanent exclusions list despite being an IRDAI mandate.",
                                 "IRDAI mandates AYUSH coverage - raise this with your insurer or consider switching."))
    elif ayush:
        features.append(_feature("ayush", "AYUSH Treatment", "green",
                                 "Covered", "AYUSH treatments (Ayurveda, Yoga, Unani, Siddha, Homeopathy) covered."))
    else:
        if schedule_only:
            features.append(_feature("ayush", "AYUSH Treatment", "lightGreen",
                                     "Not found in document", "AYUSH details not in uploaded document. IRDAI mandates coverage - likely included.",
                                     "Upload full policy document for complete analysis."))
        else:
            features.append(_feature("ayush", "AYUSH Treatment", "amber",
                                     "Not Available", "AYUSH treatments not covered.",
                                     "IRDAI mandates AYUSH coverage - verify with your insurer."))

    # 10. Ambulance Cover
    amb = _val(v2, "ambulanceCover")
    amb_str = str(amb).lower() if amb else ""
    _is_unlimited_amb = any(kw in amb_str for kw in ("unlimited", "no limit", "no cap", "full", "100%")) or \
                         ("no" in amb_str and "limit" in amb_str) or \
                         ("up to" in amb_str and ("si" in amb_str or "sum insured" in amb_str))
    if amb and _is_unlimited_amb:
        features.append(_feature("ambulance", "Ambulance Cover", "green",
                                 str(amb), "Unlimited ambulance cover."))
    elif amb and amb_str.strip():
        features.append(_feature("ambulance", "Ambulance Cover", "lightGreen",
                                 str(amb), "Ambulance cover available with limits."))
    else:
        if schedule_only:
            features.append(_feature("ambulance", "Ambulance Cover", "lightGreen",
                                     "Not found in document", "Ambulance details not in uploaded document. Most plans include this.",
                                     "Upload full policy document for complete analysis."))
        else:
            features.append(_feature("ambulance", "Ambulance Cover", "amber",
                                     "Not Available", "Ambulance cover not mentioned.",
                                     "Ensure ambulance expenses are covered in your plan."))

    # 11. Network Hospitals
    hospitals = _num(v2, "networkHospitalsCount") or _lookup_network_hospitals(insurer_name)
    if hospitals >= 10000:
        features.append(_feature("network_hospitals", "Network Hospitals", "green",
                                 f"{hospitals:,.0f}+", "Extensive hospital network - easy cashless access across India."))
    elif hospitals >= 5000:
        features.append(_feature("network_hospitals", "Network Hospitals", "lightGreen",
                                 f"{hospitals:,.0f}+", "Good hospital network - cashless available in most cities."))
    elif hospitals >= 2000:
        features.append(_feature("network_hospitals", "Network Hospitals", "amber",
                                 f"{hospitals:,.0f}+", "Limited hospital network - may face issues in smaller cities.",
                                 "Check network hospital availability in your area."))
    elif hospitals > 0:
        features.append(_feature("network_hospitals", "Network Hospitals", "red",
                                 f"{hospitals:,.0f}", "Very limited hospital network - cashless may be difficult.",
                                 "Consider an insurer with a larger network (10,000+ hospitals)."))

    # 11b. Consumables Cover (Health) — cross-check boolean with details field
    _cons_bool = _bool_field(v2, "consumablesCoverage")
    _cons_details = _val(v2, "consumablesCoverageDetails")
    _cons_details_str = str(_cons_details).lower() if _cons_details else ""
    # Trust details field over boolean if details indicate coverage
    _cons_covered = _cons_bool is True or (
        _cons_details and _cons_details_str.strip() and
        _cons_details_str not in ("na", "n/a", "nil", "none", "not covered", "not available")
    )
    if _cons_covered:
        features.append(_feature("consumables_health", "Consumables Cover", "green",
                                 str(_cons_details or "Covered"), "Consumable expenses (syringes, gloves, etc.) covered during hospitalization."))
    elif not schedule_only and (_cons_bool is False or _has_value(v2, "consumablesCoverage")):
        features.append(_feature("consumables_health", "Consumables Cover", "amber",
                                 "Not Covered", "Consumable expenses during hospitalization not covered - adds to out-of-pocket costs.",
                                 "Look for plans that cover consumables to reduce claim-time expenses."))

    # 12. Modern Treatments — extraction outputs "modernTreatment" (singular)
    modern = _has_value(v2, "modernTreatment") or _has_value(v2, "modernTreatments")
    if modern:
        features.append(_feature("modern_treatments", "Modern Treatments", "green",
                                 "Covered", "Modern treatments (robotic surgery, stem cell, etc.) covered."))

    # 13. Mental Health — extraction outputs "mentalHealthCovered"
    mh = _has_value(v2, "mentalHealthCovered") or _has_value(v2, "mentalHealthCover")
    if mh:
        features.append(_feature("mental_health", "Mental Health Coverage", "green",
                                 "Covered", "Mental health treatment covered as per IRDAI mandate."))

    return features


# ==================== MOTOR ZONE CLASSIFICATION ====================

def _zones_motor(v2: dict, insurer_name: str) -> list[dict]:
    features = []
    tp_only = _is_tp_only_motor(v2)

    if tp_only:
        # TP-only: show only TP-relevant zones (policy type, PA cover)
        # Skip OD-specific zones (IDV, zero dep, engine, consumables, deductible)
        features.append(_feature("product_type", "Policy Type", "amber",
                                 "Third Party Only", "TP-only covers third-party liability but not your own vehicle damage. This is the legal minimum.",
                                 "Consider upgrading to Comprehensive when renewing for full OD + TP protection."))

        # PA Owner Cover — critical for TP policies
        pa = _num(v2, "paOwnerCover")
        if pa >= 1500000:
            features.append(_feature("pa_cover", "PA Owner-Driver Cover", "green",
                                     f"₹{pa:,.0f}", "PA cover meets/exceeds IRDAI minimum of ₹15 lakhs."))
        elif pa > 0:
            features.append(_feature("pa_cover", "PA Owner-Driver Cover", "amber",
                                     f"₹{pa:,.0f}", f"PA cover is ₹{pa:,.0f} - below IRDAI recommended ₹15 lakhs.",
                                     "Increase PA cover to at least ₹15 lakhs (IRDAI mandate)."))
        else:
            features.append(_feature("pa_cover", "PA Owner-Driver Cover", "red",
                                     "Not Found", "PA owner-driver cover not detected - mandatory under IRDAI.",
                                     "PA cover of ₹15 lakhs is mandatory - verify with your insurer."))

        return features

    # --- Comprehensive / Standalone OD zones ---

    # 1. IDV
    idv = _num(v2, "idv")
    if idv >= 500000:
        features.append(_feature("idv", "Insured Declared Value", "green",
                                 f"₹{idv:,.0f}", "Strong IDV ensuring adequate compensation in case of total loss."))
    elif idv >= 300000:
        features.append(_feature("idv", "Insured Declared Value", "lightGreen",
                                 f"₹{idv:,.0f}", "Reasonable IDV - ensure it reflects current market value."))
    elif idv > 0:
        features.append(_feature("idv", "Insured Declared Value", "amber",
                                 f"₹{idv:,.0f}", "IDV may be below vehicle market value - reduced payout on total loss.",
                                 "Request IDV increase to match current market value."))
    else:
        features.append(_feature("idv", "Insured Declared Value", "amber",
                                 "Not Found", "IDV not detected in policy document. Verify your IDV reflects current market value.",
                                 "Check your policy document for the IDV amount."))

    # 2. Product Type
    ptype = str(_val(v2, "productType") or "").lower()
    if "comprehensive" in ptype or "comp" in ptype:
        features.append(_feature("product_type", "Policy Type", "green",
                                 "Comprehensive", "Comprehensive cover - both OD and TP protection."))
    elif "standalone" in ptype or "own damage" in ptype or "od" in ptype:
        features.append(_feature("product_type", "Policy Type", "amber",
                                 "Standalone OD", "Own Damage only - no third party liability cover in this policy. TP cover is legally mandatory.",
                                 "Ensure you have a separate active TP policy for legal compliance."))
    elif ptype.strip():
        features.append(_feature("product_type", "Policy Type", "lightGreen",
                                 str(_val(v2, "productType") or ptype), "Policy type detected."))

    # 3. Zero Depreciation
    zd = _bool_field(v2, "zeroDepreciation")
    if zd is True:
        features.append(_feature("zero_dep", "Zero Depreciation", "green",
                                 "Included", "Zero depreciation cover - full claim without depreciation deduction on parts."))
    elif zd is False or not _has_value(v2, "zeroDepreciation"):
        features.append(_feature("zero_dep", "Zero Depreciation", "red",
                                 "Not Included", "No zero depreciation - significant deductions on plastic, rubber, glass parts during claims.",
                                 "Add zero depreciation cover - most valuable motor add-on."))

    # 4. Engine Protection
    eng = _bool_field(v2, "engineProtection")
    if eng is True:
        features.append(_feature("engine_protection", "Engine Protection", "green",
                                 "Included", "Engine protection cover - damage from water ingression, oil leakage covered."))
    elif eng is False or not _has_value(v2, "engineProtection"):
        features.append(_feature("engine_protection", "Engine Protection", "amber",
                                 "Not Included", "No engine protection - engine damage from flooding/water not covered.",
                                 "Consider adding engine protection, especially in flood-prone areas."))

    # 5. NCB
    ncb = _num(v2, "ncbPercentage")
    if ncb >= 50:
        features.append(_feature("ncb", "No Claim Bonus", "green",
                                 f"{ncb}%", f"Maximum NCB discount of {ncb}% - significant premium savings."))
    elif ncb >= 20:
        features.append(_feature("ncb", "No Claim Bonus", "lightGreen",
                                 f"{ncb}%", f"Good NCB discount of {ncb}%."))
    elif ncb > 0:
        features.append(_feature("ncb", "No Claim Bonus", "amber",
                                 f"{ncb}%", f"Low NCB of {ncb}% - will improve with claim-free years."))
    elif _has_value(v2, "ncbPercentage"):
        features.append(_feature("ncb", "No Claim Bonus", "red",
                                 "0%", "No NCB discount - new policy or recent claim.",
                                 "Maintain claim-free record to build NCB up to 50%."))

    # 6. NCB Protection
    ncb_prot = _bool_field(v2, "ncbProtection")
    if ncb_prot is True:
        features.append(_feature("ncb_protection", "NCB Protection", "green",
                                 "Included", "NCB protection - your NCB discount is protected even after a claim."))
    elif ncb_prot is False or not _has_value(v2, "ncbProtection"):
        features.append(_feature("ncb_protection", "NCB Protection", "amber",
                                 "Not Included", "No NCB protection - one claim resets your accumulated NCB discount.",
                                 "Add NCB protection to safeguard your premium discount."))

    # 7. Roadside Assistance
    rsa = _bool_field(v2, "roadsideAssistance")
    if rsa is True:
        features.append(_feature("rsa", "Roadside Assistance", "green",
                                 "Included", "24/7 roadside assistance - towing, flat tyre, battery jumpstart covered."))
    elif rsa is False or not _has_value(v2, "roadsideAssistance"):
        features.append(_feature("rsa", "Roadside Assistance", "amber",
                                 "Not Included", "No roadside assistance - you'll bear towing and breakdown costs.",
                                 "Consider adding RSA for peace of mind during breakdowns."))

    # 8. Consumables
    cons = _bool_field(v2, "consumables")
    if cons is True:
        features.append(_feature("consumables", "Consumables Cover", "green",
                                 "Included", "Consumables covered - nut, bolt, screw, oil, grease charges included in claims."))
    elif cons is False or not _has_value(v2, "consumables"):
        features.append(_feature("consumables", "Consumables Cover", "amber",
                                 "Not Included", "No consumables cover - workshop consumable charges not reimbursed.",
                                 "Add consumables cover to avoid out-of-pocket garage expenses."))

    # 9. PA Owner Cover
    pa = _num(v2, "paOwnerCover")
    if pa >= 1500000:
        features.append(_feature("pa_cover", "PA Owner-Driver Cover", "green",
                                 f"₹{pa:,.0f}", "PA cover meets/exceeds IRDAI minimum of ₹15 lakhs."))
    elif pa > 0:
        features.append(_feature("pa_cover", "PA Owner-Driver Cover", "amber",
                                 f"₹{pa:,.0f}", f"PA cover is ₹{pa:,.0f} - below IRDAI recommended ₹15 lakhs.",
                                 "Increase PA cover to at least ₹15 lakhs (IRDAI mandate)."))
    else:
        features.append(_feature("pa_cover", "PA Owner-Driver Cover", "red",
                                 "Not Found", "PA owner-driver cover not detected - mandatory under IRDAI.",
                                 "PA cover of ₹15 lakhs is mandatory - verify with your insurer."))

    # 10. Return to Invoice
    rti = _bool_field(v2, "returnToInvoice")
    if rti is True:
        features.append(_feature("rti", "Return to Invoice", "green",
                                 "Included", "RTI cover - get invoice value (not depreciated IDV) in case of total loss."))

    # 11. Tyre Cover
    tyre = _bool_field(v2, "tyreCover")
    if tyre is True:
        features.append(_feature("tyre_cover", "Tyre Cover", "green",
                                 "Included", "Tyre damage cover included."))

    # 12. Deductible
    ded = _num(v2, "compulsoryDeductible")
    vol_ded = _num(v2, "voluntaryDeductible")
    total_ded = ded + vol_ded
    if total_ded <= 1000:
        features.append(_feature("deductible", "Deductible", "green",
                                 f"₹{total_ded:,.0f}", "Low deductible - minimal out-of-pocket during claims."))
    elif total_ded <= 2500:
        features.append(_feature("deductible", "Deductible", "lightGreen",
                                 f"₹{total_ded:,.0f}", "Moderate deductible - reasonable out-of-pocket amount."))
    elif total_ded <= 5000:
        features.append(_feature("deductible", "Deductible", "amber",
                                 f"₹{total_ded:,.0f}", "Higher deductible increases out-of-pocket costs per claim.",
                                 "Consider reducing voluntary deductible for lower out-of-pocket."))
    elif total_ded > 5000:
        features.append(_feature("deductible", "Deductible", "red",
                                 f"₹{total_ded:,.0f}", "High deductible significantly reduces effective coverage.",
                                 "Reduce deductible to minimize out-of-pocket expenses."))

    return features


# ==================== LIFE ZONE CLASSIFICATION ====================

def _zones_life(v2: dict, insurer_name: str) -> list[dict]:
    features = []

    # 1. Sum Assured
    sa = _num(v2, "sumAssured")
    if sa >= 10000000:
        features.append(_feature("sum_assured", "Sum Assured", "green",
                                 f"₹{sa:,.0f}", "Excellent Sum Assured (₹1Cr+) - strong financial protection for family."))
    elif sa >= 5000000:
        features.append(_feature("sum_assured", "Sum Assured", "lightGreen",
                                 f"₹{sa:,.0f}", "Good Sum Assured - covers most family needs.",
                                 "Consider if this covers 10-15x annual income."))
    elif sa >= 2500000:
        features.append(_feature("sum_assured", "Sum Assured", "amber",
                                 f"₹{sa:,.0f}", "Sum Assured may be insufficient for family's long-term needs.",
                                 "Increase to at least 10-15x annual income."))
    elif sa > 0:
        features.append(_feature("sum_assured", "Sum Assured", "red",
                                 f"₹{sa:,.0f}", "Sum Assured is low - may not adequately protect family.",
                                 "Urgently increase life cover to at least ₹50 lakhs - 1 crore."))

    # 2. Policy Term
    term = _num(v2, "policyTerm")
    if term >= 30:
        features.append(_feature("policy_term", "Policy Term", "green",
                                 f"{term:.0f} years", "Long policy term - coverage extends well into retirement."))
    elif term >= 20:
        features.append(_feature("policy_term", "Policy Term", "lightGreen",
                                 f"{term:.0f} years", "Good policy term for most working professionals."))
    elif term >= 10:
        features.append(_feature("policy_term", "Policy Term", "amber",
                                 f"{term:.0f} years", "Medium-term policy - verify it covers your earning years.",
                                 "Consider extending term to cover until retirement."))
    elif term > 0:
        features.append(_feature("policy_term", "Policy Term", "red",
                                 f"{term:.0f} years", "Short policy term - significant coverage gap likely.",
                                 "Extend policy term or add another term plan."))

    # 3. CSR
    csr = _lookup_csr(insurer_name)
    if csr >= 98:
        features.append(_feature("csr", "Claim Settlement Ratio", "green",
                                 f"{csr}%", f"Excellent CSR of {csr}% - very high probability of claim approval."))
    elif csr >= 95:
        features.append(_feature("csr", "Claim Settlement Ratio", "lightGreen",
                                 f"{csr}%", f"Good CSR of {csr}% - strong track record."))
    elif csr >= 90:
        features.append(_feature("csr", "Claim Settlement Ratio", "amber",
                                 f"{csr}%", f"CSR of {csr}% is moderate for life insurance.",
                                 "Consider insurers with CSR above 95% for life coverage."))
    elif csr > 0:
        features.append(_feature("csr", "Claim Settlement Ratio", "red",
                                 f"{csr}%", f"Low CSR of {csr}% - claims may face rejection.",
                                 "Seriously consider switching to an insurer with higher CSR."))

    # 4. Riders
    riders = _val(v2, "riders")
    rider_count = len(riders) if isinstance(riders, list) else 0
    if rider_count >= 4:
        features.append(_feature("riders", "Riders", "green",
                                 f"{rider_count} riders", "Comprehensive rider coverage enhancing base policy."))
    elif rider_count >= 2:
        features.append(_feature("riders", "Riders", "lightGreen",
                                 f"{rider_count} riders", "Good rider coverage - consider adding critical illness or disability."))
    elif rider_count == 1:
        features.append(_feature("riders", "Riders", "amber",
                                 f"{rider_count} rider", "Limited rider coverage.",
                                 "Add riders for accidental death, critical illness, waiver of premium."))
    else:
        features.append(_feature("riders", "Riders", "red",
                                 "None", "No riders attached - base policy only.",
                                 "Add riders for comprehensive protection (critical illness, accidental death)."))

    # 5. Nominees
    nominees = _val(v2, "nominees")
    nom_count = len(nominees) if isinstance(nominees, list) else 0
    if nom_count > 0:
        features.append(_feature("nominees", "Nominee Designation", "green",
                                 f"{nom_count} nominee(s)", "Nominee designated - ensures smooth claim process."))
    else:
        features.append(_feature("nominees", "Nominee Designation", "red",
                                 "Not Designated", "No nominee designated - claim process will be complicated for family.",
                                 "Designate a nominee immediately to ensure hassle-free claims."))

    # 6. Death Benefit
    death = _num(v2, "deathBenefit")
    if death > 0 and sa > 0 and death >= sa:
        features.append(_feature("death_benefit", "Death Benefit", "green",
                                 f"₹{death:,.0f}", "Death benefit equals or exceeds Sum Assured."))
    elif death > 0:
        features.append(_feature("death_benefit", "Death Benefit", "lightGreen",
                                 f"₹{death:,.0f}", "Death benefit available."))

    # 7. Surrender Value
    if _has_value(v2, "surrenderValue"):
        features.append(_feature("surrender_value", "Surrender Value", "green",
                                 str(_val(v2, "surrenderValue")), "Surrender value available - provides liquidity if needed."))

    return features


# ==================== PA ZONE CLASSIFICATION ====================

def _zones_pa(v2: dict, insurer_name: str) -> list[dict]:
    features = []

    # 1. Sum Insured
    si = _num(v2, "paSumInsured")
    if si >= 5000000:
        features.append(_feature("sum_insured", "Sum Insured", "green",
                                 f"₹{si:,.0f}", "Strong PA Sum Insured for adequate accident coverage."))
    elif si >= 2500000:
        features.append(_feature("sum_insured", "Sum Insured", "lightGreen",
                                 f"₹{si:,.0f}", "Reasonable PA Sum Insured.",
                                 "Consider increasing to ₹50 lakhs+ for better protection."))
    elif si >= 1000000:
        features.append(_feature("sum_insured", "Sum Insured", "amber",
                                 f"₹{si:,.0f}", "PA Sum Insured may be insufficient for serious accidents.",
                                 "Increase to at least ₹25-50 lakhs."))
    elif si > 0:
        features.append(_feature("sum_insured", "Sum Insured", "red",
                                 f"₹{si:,.0f}", "PA Sum Insured is critically low.",
                                 "Urgently increase PA cover to at least ₹10-25 lakhs."))

    # 2. Accidental Death Benefit
    ad_pct = _num(v2, "accidentalDeathBenefitPercentage")
    if ad_pct >= 100:
        features.append(_feature("ad_benefit", "Accidental Death Benefit", "green",
                                 f"{ad_pct}% of SI", "Full Sum Insured payable on accidental death."))
    elif ad_pct > 0:
        features.append(_feature("ad_benefit", "Accidental Death Benefit", "amber",
                                 f"{ad_pct}% of SI", f"Only {ad_pct}% of SI payable on accidental death.",
                                 "Look for plans offering 100% of SI as death benefit."))

    # 3. PTD
    ptd = _bool_field(v2, "permanentTotalDisabilityCovered")
    if ptd is True:
        features.append(_feature("ptd", "Permanent Total Disability", "green",
                                 "Covered", "PTD coverage ensures financial support for permanent disabilities."))
    else:
        features.append(_feature("ptd", "Permanent Total Disability", "red",
                                 "Not Covered", "No PTD coverage - critical gap for accident insurance.",
                                 "PTD coverage is essential - consider adding or switching plans."))

    # 4. PPD
    ppd = _bool_field(v2, "permanentPartialDisabilityCovered")
    if ppd is True:
        ppd_schedule = _has_value(v2, "ppdSchedule")
        if ppd_schedule:
            features.append(_feature("ppd", "Permanent Partial Disability", "green",
                                     "Covered with Schedule", "PPD covered with defined benefit schedule."))
        else:
            features.append(_feature("ppd", "Permanent Partial Disability", "lightGreen",
                                     "Covered", "PPD covered - verify benefit percentage schedule."))
    else:
        features.append(_feature("ppd", "Permanent Partial Disability", "red",
                                 "Not Covered", "No PPD coverage - partial disabilities not compensated.",
                                 "Ensure PPD is included in your PA policy."))

    # 5. TTD
    ttd = _bool_field(v2, "temporaryTotalDisabilityCovered")
    if ttd is True:
        features.append(_feature("ttd", "Temporary Total Disability", "green",
                                 "Covered", "TTD covered - weekly/monthly benefit during temporary disability."))
    else:
        features.append(_feature("ttd", "Temporary Total Disability", "amber",
                                 "Not Covered", "No TTD coverage - no income replacement during temporary disability.",
                                 "Consider adding TTD for income protection during recovery."))

    # 6. Medical Expenses
    med = _bool_field(v2, "medicalExpensesCovered")
    if med is True:
        features.append(_feature("medical_expenses", "Medical Expenses", "green",
                                 "Covered", "Accident-related medical expenses covered."))
    else:
        features.append(_feature("medical_expenses", "Medical Expenses", "amber",
                                 "Not Covered", "Medical expenses from accidents not covered separately.",
                                 "Ensure you have health insurance to cover accident medical costs."))

    # 7. Occupation Restrictions
    restrictions = _val(v2, "paOccupationRestrictions")
    if isinstance(restrictions, list) and len(restrictions) > 0:
        features.append(_feature("occupation_restrictions", "Occupation Restrictions", "amber",
                                 f"{len(restrictions)} restriction(s)", "Policy has occupation-based restrictions that may limit coverage.",
                                 "Review the restrictions to ensure your occupation is covered."))

    # 8. Additional benefits
    edu = _bool_field(v2, "educationBenefitCovered")
    if edu is True:
        features.append(_feature("education_benefit", "Education Benefit", "green",
                                 "Covered", "Education benefit for children included."))

    loan = _bool_field(v2, "loanEmiCoverCovered")
    if loan is True:
        features.append(_feature("loan_emi", "Loan EMI Cover", "green",
                                 "Covered", "Loan EMI cover ensures ongoing EMIs are protected."))

    return features


# ==================== TRAVEL ZONE CLASSIFICATION ====================

def _zones_travel(v2: dict, insurer_name: str) -> list[dict]:
    features = []

    # 1. Medical Cover — currency-aware thresholds
    med = _num(v2, "medicalExpenses")
    med_inr = _travel_to_inr(v2, med)
    sym = _travel_currency_symbol(v2)
    med_display = f"{sym}{med:,.0f}"
    if med_inr >= 5000000:
        features.append(_feature("medical_cover", "Medical Cover", "green",
                                 med_display, "Strong medical cover for international travel."))
    elif med_inr >= 2500000:
        features.append(_feature("medical_cover", "Medical Cover", "lightGreen",
                                 med_display, "Adequate medical cover - sufficient for most destinations."))
    elif med_inr >= 1000000:
        features.append(_feature("medical_cover", "Medical Cover", "amber",
                                 med_display, "Medical cover may be insufficient for countries with high healthcare costs (USA, Europe).",
                                 "Increase medical cover to at least $50,000 for international travel."))
    elif med > 0:
        features.append(_feature("medical_cover", "Medical Cover", "red",
                                 med_display, "Medical cover is very low for international travel.",
                                 "Urgently increase medical cover - healthcare abroad is expensive."))

    # 2. PED
    ped = _bool_field(v2, "preExistingCovered")
    if ped is True:
        features.append(_feature("ped", "Pre-Existing Disease Coverage", "green",
                                 "Covered", "Pre-existing conditions covered during travel."))
    elif ped is False:
        features.append(_feature("ped", "Pre-Existing Disease Coverage", "red",
                                 "Not Covered", "Pre-existing conditions excluded - medical emergency from PED not covered.",
                                 "If you have pre-existing conditions, choose a plan that covers them."))

    # 3. Trip Cancellation
    tc = _has_value(v2, "tripCancellation")
    if tc:
        features.append(_feature("trip_cancellation", "Trip Cancellation", "green",
                                 "Covered", "Trip cancellation expenses covered - reimbursement for non-refundable costs."))
    else:
        features.append(_feature("trip_cancellation", "Trip Cancellation", "amber",
                                 "Not Covered", "No trip cancellation cover - non-refundable expenses at risk.",
                                 "Add trip cancellation cover, especially for expensive international trips."))

    # 4. Trip Interruption
    ti = _has_value(v2, "tripInterruption")
    if ti:
        features.append(_feature("trip_interruption", "Trip Interruption", "green",
                                 "Covered", "Trip interruption covered - additional expenses for early return."))

    # 5. Emergency Evacuation
    evac = _has_value(v2, "emergencyMedicalEvacuation")
    if evac:
        features.append(_feature("evacuation", "Emergency Medical Evacuation", "green",
                                 "Covered", "Emergency medical evacuation covered - critical for remote destinations."))
    else:
        features.append(_feature("evacuation", "Emergency Medical Evacuation", "red",
                                 "Not Covered", "No emergency evacuation cover - evacuation costs can be extremely high.",
                                 "Emergency evacuation is essential - add this cover immediately."))

    # 6. Baggage
    bag = _has_value(v2, "baggageLoss")
    bag_delay = _has_value(v2, "baggageDelay")
    if bag and bag_delay:
        features.append(_feature("baggage", "Baggage Protection", "green",
                                 "Loss + Delay covered", "Both baggage loss and delay covered."))
    elif bag:
        features.append(_feature("baggage", "Baggage Protection", "lightGreen",
                                 "Loss covered", "Baggage loss covered but delay compensation not included."))
    elif bag_delay:
        features.append(_feature("baggage", "Baggage Protection", "lightGreen",
                                 "Delay covered", "Baggage delay covered but loss not included."))
    else:
        features.append(_feature("baggage", "Baggage Protection", "amber",
                                 "Not Covered", "No baggage protection.",
                                 "Consider adding baggage loss/delay cover for international travel."))

    # 7. Flight Delay
    fd = _has_value(v2, "flightDelay")
    if fd:
        features.append(_feature("flight_delay", "Flight Delay", "green",
                                 "Covered", "Flight delay compensation available."))

    # 8. Personal Liability
    pl = _has_value(v2, "personalLiability")
    if pl:
        features.append(_feature("personal_liability", "Personal Liability", "green",
                                 "Covered", "Personal liability covered - protection against third-party claims."))
    else:
        features.append(_feature("personal_liability", "Personal Liability", "amber",
                                 "Not Covered", "No personal liability cover.",
                                 "Consider adding personal liability cover for international travel."))

    # 9. Adventure Sports
    adv_excl = _bool_field(v2, "adventureSportsExclusion")
    if adv_excl is False:
        features.append(_feature("adventure_sports", "Adventure Sports", "green",
                                 "Covered", "Adventure sports activities covered."))
    elif adv_excl is True:
        features.append(_feature("adventure_sports", "Adventure Sports", "red",
                                 "Excluded", "Adventure sports excluded - injuries during adventure activities not covered.",
                                 "If planning adventure activities, choose a plan that covers them."))

    # 10. Cashless Network
    cashless = _bool_field(v2, "cashlessNetworkAvailable")
    if cashless is True:
        features.append(_feature("cashless_network", "Cashless Network", "green",
                                 "Available", "Cashless network available for direct hospital billing."))
    elif cashless is False:
        features.append(_feature("cashless_network", "Cashless Network", "amber",
                                 "Not Available", "No cashless network - you may need to pay upfront and claim reimbursement.",
                                 "Choose a plan with cashless network for hassle-free claims abroad."))

    # 11. Deductible — check both field names, currency-aware display
    # Standard travel deductibles: $50-$100 (₹4K-₹8.3K) are normal
    ded = _num(v2, "deductiblePerClaim") or _num(v2, "medicalDeductible")
    ded_inr = _travel_to_inr(v2, ded) if ded > 0 else 0
    ded_display = f"{sym}{ded:,.0f}" if ded > 0 else "None"
    if ded_inr <= 0:
        features.append(_feature("deductible", "Deductible", "green",
                                 "None", "No deductible - full claim amount payable."))
    elif ded_inr <= 4000:
        features.append(_feature("deductible", "Deductible", "lightGreen",
                                 ded_display, "Low deductible per claim."))
    elif ded_inr <= 10000:
        features.append(_feature("deductible", "Deductible", "amber",
                                 ded_display, "Standard deductible - you pay this amount before coverage kicks in.",
                                 "Consider plans with lower or no deductible for smaller claims."))
    elif ded_inr > 10000:
        features.append(_feature("deductible", "Deductible", "red",
                                 ded_display, "High deductible significantly reduces effective coverage.",
                                 "Switch to a plan with lower deductible."))

    return features


# ==================== ROUTER ====================

_ZONE_ROUTER = {
    "health": _zones_health,
    "motor": _zones_motor,
    "life": _zones_life,
    "pa": _zones_pa,
    "travel": _zones_travel,
}


# ==================== PUBLIC API ====================

def classify_zones(
    v2_raw_extraction: dict,
    category: str,
    insurer_name: str = "",
) -> dict:
    """Classify extracted features into 4 zones.

    Args:
        v2_raw_extraction: Raw v2 extraction (ConfidenceField format).
        category: Detected category (health/motor/life/pa/travel).
        insurer_name: Insurer name for CSR/network lookups.

    Returns:
        {
            "summary": {"green": N, "lightGreen": N, "amber": N, "red": N},
            "features": [
                {
                    "featureId": str,
                    "featureName": str,
                    "zone": "green"|"lightGreen"|"amber"|"red",
                    "currentValue": str,
                    "explanation": str,
                    "recommendation": str (optional, for amber/red)
                }, ...
            ]
        }
    """
    if not v2_raw_extraction:
        return {"summary": {"green": 0, "lightGreen": 0, "amber": 0, "red": 0}, "features": []}

    if not insurer_name:
        insurer_name = str(_val(v2_raw_extraction, "insurerName") or "")

    zone_fn = _ZONE_ROUTER.get(category, _zones_health)
    features = zone_fn(v2_raw_extraction, insurer_name)

    # Build summary
    summary = {"green": 0, "lightGreen": 0, "amber": 0, "red": 0}
    for f in features:
        z = f.get("zone", "")
        if z in summary:
            summary[z] += 1

    logger.info(
        f"Zone classification [{category}]: "
        f"green={summary['green']}, lightGreen={summary['lightGreen']}, "
        f"amber={summary['amber']}, red={summary['red']} "
        f"({len(features)} features total)"
    )

    return {"summary": summary, "features": features}
