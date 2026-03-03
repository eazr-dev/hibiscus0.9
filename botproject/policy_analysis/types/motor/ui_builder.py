"""Motor Insurance UI Builder (EAZR_03 Spec)
Build Flutter UI-specific structure for motor insurance policies.
"""
import logging
import re
from datetime import datetime

from policy_analysis.utils import safe_num, get_score_label, get_insurer_logo_url
from policy_analysis.types.motor.helpers import (
    detect_motor_product_type,
    _calculate_coverage_adequacy,
    _calculate_claim_readiness,
    _calculate_value_for_money,
    _simulate_motor_scenarios,
    _analyze_motor_gaps,
    _generate_motor_recommendations,
    _calculate_motor_ipf,
)

logger = logging.getLogger(__name__)


def _build_motor_policy_details_ui(
    extracted_data: dict,
    category_data: dict,
    policy_type: str = "",
    policy_status: str = "active"
) -> dict:
    """
    Build Flutter UI-specific structure for Motor Insurance Policy.
    Full implementation per EAZR_03_Motor_Insurance.md specification.
    Includes: Emergency Info, Policy Overview, Vehicle Details, Coverage Details,
    Add-ons (active + missing), NCB Tracker, IDV Analysis, Scoring Engine (3 scores),
    Scenario Simulations (5), Gap Analysis (8 rules), Recommendations, IPF, Claims, Premium.
    """

    vehicle_details = category_data.get("vehicleDetails", {})
    owner_details = category_data.get("ownerDetails", {})
    coverage_details = category_data.get("coverageDetails", {})
    premium_breakdown = category_data.get("premiumBreakdown", {})
    ncb_info = category_data.get("ncb", {})
    policy_identification = category_data.get("policyIdentification", {})
    add_on_covers = category_data.get("addOnCovers", {})

    insurer_name = policy_identification.get("insurerName") or extracted_data.get("insuranceProvider", "")
    policy_number = policy_identification.get("policyNumber") or extracted_data.get("policyNumber", "")
    reg_number = vehicle_details.get("registrationNumber", "")

    # ==================== DETECT PRODUCT TYPE (EAZR_03 S2) ====================
    product_type = detect_motor_product_type({
        "vehicleClass": vehicle_details.get("vehicleClass", ""),
        "odPremium": coverage_details.get("odPremium", 0),
        "tpPremium": coverage_details.get("tpPremium", 0),
        "productType": policy_identification.get("productType", "")
    }, category_data)

    # ==================== SAFE NUMERIC HELPERS ====================
    def _safe_float(val, default=0):
        if val is None or val == "":
            return default
        try:
            return float(val) if not isinstance(val, (int, float)) else float(val)
        except (ValueError, TypeError):
            return default

    def _safe_int(val, default=0):
        if val is None or val == "":
            return default
        try:
            ncb_m = re.search(r'\d+', str(val))
            return int(ncb_m.group()) if ncb_m else default
        except (ValueError, TypeError):
            return default

    # ==================== EXTRACT CORE VALUES ====================
    idv = _safe_float(coverage_details.get("idv") or extracted_data.get("coverageAmount"), 0)
    od_premium = _safe_float(premium_breakdown.get("odPremium") or premium_breakdown.get("basicOdPremium") or coverage_details.get("odPremium"), 0)
    tp_premium = _safe_float(premium_breakdown.get("tpPremium") or coverage_details.get("tpPremium"), 0)
    ncb_pct = _safe_int(ncb_info.get("ncbPercentage") or ncb_info.get("current"), 0)
    gst_amount = _safe_float(premium_breakdown.get("gst") or coverage_details.get("gst"), 0)
    total_premium = _safe_float(premium_breakdown.get("totalPremium") or extracted_data.get("premium"), 0)

    # Calculate if total is missing
    if total_premium == 0 and (od_premium > 0 or tp_premium > 0):
        gross = od_premium + tp_premium
        gst_amount = gst_amount if gst_amount > 0 else round(gross * 0.18, 2)
        total_premium = gross + gst_amount

    ncb_discount = _safe_float(premium_breakdown.get("ncbDiscount"), 0)
    add_on_total_premium = _safe_float(premium_breakdown.get("addOnPremium"), 0)
    # Determine manufacturing year: use extracted value, or infer from registration/policy dates
    raw_mfg_year = vehicle_details.get("manufacturingYear")
    current_year_val = datetime.now().year
    if raw_mfg_year and _safe_int(raw_mfg_year, 0) > 1990:
        manufacturing_year = _safe_int(raw_mfg_year, current_year_val - 3)
    else:
        # Infer from registration date or policy start date
        reg_date_str = vehicle_details.get("registrationDate") or ""
        policy_start_str = policy_identification.get("policyPeriodStart") or extracted_data.get("startDate", "")
        inferred_year = 0
        for date_str in [reg_date_str, policy_start_str]:
            if date_str:
                year_match = re.search(r'(20\d{2})', str(date_str))
                if year_match:
                    inferred_year = int(year_match.group(1))
                    break
        if inferred_year > 1990:
            # Registration/policy year approximates vehicle purchase year
            manufacturing_year = inferred_year
        else:
            manufacturing_year = current_year_val - 3
    vehicle_age = max(0, current_year_val - manufacturing_year)
    # §7 FIX: IDV comparison at policy inception — IDV is set at inception,
    # so estimated market value should reflect the inception-period value.
    # IDV is typically 90-95% of market value at inception (IRDAI GR.36 depreciation).
    # Using idv * 1.08 gives a reasonable inception-period market estimate.
    estimated_market_value = round(idv * 1.08) if idv > 0 else 0

    # Add-on flags from both coverageDetails and addOnCovers
    has_zero_dep = bool(coverage_details.get("zeroDepreciation") or coverage_details.get("zeroDep") or add_on_covers.get("zeroDepreciation"))
    has_engine_protect = bool(coverage_details.get("engineProtection") or add_on_covers.get("engineProtection"))
    has_rti = bool(coverage_details.get("returnToInvoice") or add_on_covers.get("returnToInvoice"))
    has_rsa = bool(coverage_details.get("roadsideAssistance") or add_on_covers.get("roadsideAssistance"))
    has_consumables = bool(coverage_details.get("consumables") or coverage_details.get("consumablesCover") or add_on_covers.get("consumables"))
    has_ncb_protect = bool(ncb_info.get("ncbProtection") or coverage_details.get("ncbProtection") or add_on_covers.get("ncbProtect"))
    has_key_replace = bool(add_on_covers.get("keyCover"))
    has_tyre_protect = bool(add_on_covers.get("tyreCover"))
    # BUG #8 FIX: Expanded detection — "Personal Baggage" and "Loss of Personal Effects" are the same coverage
    _cat_str_addon = str(category_data).lower()
    has_personal_baggage = bool(add_on_covers.get("personalBaggage") or "personal effect" in _cat_str_addon or "personal belonging" in _cat_str_addon or "loss of personal" in _cat_str_addon)
    has_emi_protect = bool(add_on_covers.get("emiBreakerCover"))
    has_outstation = bool(add_on_covers.get("outstationEmergency"))
    has_daily_allowance = bool(add_on_covers.get("dailyAllowance"))
    has_windshield = bool(add_on_covers.get("windshieldCover"))
    has_ev_cover = bool(add_on_covers.get("electricVehicleCover"))
    has_battery_protect = bool(add_on_covers.get("batteryProtect"))
    # BUG #1 FIX: Comprehensive PA detection from multiple dynamic sources
    pa_owner_cover = _safe_float(coverage_details.get("paOwnerCover"), 0)
    # Also check PA premium — if premium exists, coverage exists
    if pa_owner_cover <= 0:
        _pa_prem = _safe_float(premium_breakdown.get("paOwnerDriverPremium"), 0)
        if _pa_prem > 0:
            pa_owner_cover = 1500000  # Statutory minimum ₹15L
    pa_passengers = _safe_float(add_on_covers.get("passengerCoverAmount") or coverage_details.get("paUnnamedPassengers"), 0)
    # Also check passenger PA premium
    if pa_passengers <= 0:
        _pa_pass_prem = _safe_float(premium_breakdown.get("paPassengersPremium"), 0)
        if _pa_pass_prem > 0:
            pa_passengers = 1  # At least some coverage exists
    pa_paid_driver = _safe_float(coverage_details.get("paPaidDriver"), 0)
    # Also check paid driver PA premium
    if pa_paid_driver <= 0:
        _pa_driver_prem = _safe_float(premium_breakdown.get("paPaidDriverPremium"), 0)
        if _pa_driver_prem > 0:
            pa_paid_driver = 1  # At least some coverage exists
    # BUG #8 FIX: Detect Legal Liability to Paid Driver from coverageDetails
    has_ll_paid_driver = bool(coverage_details.get("llPaidDriver") or _safe_float(premium_breakdown.get("llPaidDriverPremium"), 0) > 0 or "legal liability" in _cat_str_addon and "paid driver" in _cat_str_addon)
    has_ll_employees = bool(coverage_details.get("llEmployees") or "legal liability" in _cat_str_addon and "employee" in _cat_str_addon or "workmen compensation" in _cat_str_addon)
    voluntary_deductible = _safe_float(coverage_details.get("voluntaryDeductible"), 0)
    compulsory_deductible = _safe_float(coverage_details.get("compulsoryDeductible"), 0)

    # Build addons map for helper functions
    addons_map = {
        "zero_depreciation": has_zero_dep,
        "engine_protect": has_engine_protect,
        "return_to_invoice": has_rti,
        "roadside_assistance": has_rsa,
        "consumables_cover": has_consumables,
        "ncb_protect": has_ncb_protect,
        "key_replacement": has_key_replace,
        "tyre_protect": has_tyre_protect,
        "personal_baggage": has_personal_baggage,
        "emi_protect": has_emi_protect,
        "outstation_emergency": has_outstation,
        "daily_allowance": has_daily_allowance,
        "windshield_cover": has_windshield,
        "electric_vehicle_cover": has_ev_cover,
        "battery_protect": has_battery_protect
    }

    # BUG #3 FIX: Detect plan-specific co-pays/excesses dynamically from policy text
    _category_str_lower = str(category_data).lower()
    _plan_copay = 0
    _additional_excess = _safe_float(coverage_details.get("additionalExcess"), 0)
    # Search for co-pay/excess patterns dynamically — not insurer-specific
    _copay_patterns = [
        r'(?:co-?pay|excess|you\s+(?:just\s+)?pay)[^₹\d]*[₹rs\.?\s]*(\d[\d,]*)',
        r'[₹rs\.?\s]*(\d[\d,]*)\s*(?:co-?pay|excess|per\s+claim)',
        r'additional\s+excess[^₹\d]*[₹rs\.?\s]*(\d[\d,]*)',
    ]
    for _cp_pattern in _copay_patterns:
        _cp_match = re.search(_cp_pattern, _category_str_lower, re.IGNORECASE)
        if _cp_match:
            _detected_copay = _safe_float(_cp_match.group(1).replace(",", ""), 0)
            if 500 <= _detected_copay <= 25000:  # Reasonable co-pay range
                _plan_copay = max(_plan_copay, int(_detected_copay))
                break
    if _additional_excess > 0 and _additional_excess > _plan_copay:
        _plan_copay = int(_additional_excess)

    # §9 FIX: Extract hypothecation/loan info for simulation display
    _hyp_raw = vehicle_details.get("hypothecation") or {}
    _hyp_bank = ""
    if isinstance(_hyp_raw, dict):
        _fin_name = _hyp_raw.get("financierName", "") or _hyp_raw.get("bankName", "")
        if _fin_name and str(_fin_name).strip().upper() not in ("NA", "NIL", "NOT APPLICABLE", "NONE", "0", ""):
            _hyp_bank = str(_fin_name).strip()
        elif _hyp_raw.get("isHypothecated", False):
            _hyp_bank = "Financier (name not extracted)"
    elif isinstance(_hyp_raw, str) and _hyp_raw.strip().upper() not in ("NA", "NIL", "NOT APPLICABLE", "NONE", "0", ""):
        _hyp_bank = _hyp_raw.strip()

    policy_data = {
        "addons_map": addons_map,
        "product_type": product_type,
        "pa_owner_covered": pa_owner_cover > 0,
        "pa_owner_sum": pa_owner_cover,
        "pa_passengers_covered": pa_passengers > 0,
        "pa_named_persons_covered": bool(coverage_details.get("paNamedPersons") or add_on_covers.get("paNamedPersons") or "pa to named person" in _cat_str_addon or "imt 15" in _cat_str_addon),
        "voluntary_deductible": voluntary_deductible,
        "compulsory_deductible": int(compulsory_deductible),
        "plan_copay": _plan_copay,
        "electrical_accessories_premium": _safe_float(premium_breakdown.get("electricalAccessoriesPremium"), 0),
        "non_electrical_accessories_premium": _safe_float(premium_breakdown.get("nonElectricalAccessoriesPremium"), 0),
        "od_premium": od_premium,
        "hypothecation_bank": _hyp_bank,
    }

    # Validity calculation
    start_date = policy_identification.get("policyPeriodStart") or extracted_data.get("startDate", "")
    end_date = policy_identification.get("policyPeriodEnd") or extracted_data.get("endDate", "")
    days_remaining = 0
    progress_percent = 0

    # BUG #6 FIX: Use policy start year for vehicle age, not current year
    _policy_start_year = None
    if start_date:
        _start_year_match = re.search(r'(20\d{2})', str(start_date))
        if _start_year_match:
            _policy_start_year = int(_start_year_match.group(1))
    # Override vehicle_age to use policy start year instead of report/current date
    if _policy_start_year:
        vehicle_age = max(0, _policy_start_year - manufacturing_year)

    try:
        if end_date:
            parts = str(end_date).split("-")
            if len(parts) == 3 and len(parts[0]) == 4:
                end_dt = datetime.strptime(str(end_date), "%Y-%m-%d")
            elif len(parts) == 3:
                end_dt = datetime.strptime(str(end_date), "%d-%m-%Y")
            else:
                end_dt = datetime.strptime(str(end_date), "%Y-%m-%d")
            days_remaining = max(0, (end_dt.date() - datetime.now().date()).days)
            if start_date:
                s_parts = str(start_date).split("-")
                if len(s_parts) == 3 and len(s_parts[0]) == 4:
                    start_dt = datetime.strptime(str(start_date), "%Y-%m-%d")
                else:
                    start_dt = datetime.strptime(str(start_date), "%d-%m-%Y")
                total_days = (end_dt - start_dt).days
                days_elapsed = (datetime.now() - start_dt).days
                if total_days > 0:
                    progress_percent = max(0, min(100, int((days_elapsed / total_days) * 100)))
    except Exception:
        pass

    # BUG #5 FIX: Use basicOdPremium (before NCB) as the consistent NCB calculation base
    basic_od = _safe_float(premium_breakdown.get("basicOdPremium"), 0)
    if basic_od <= 0:
        basic_od = od_premium  # Fallback to odPremium if basicOdPremium not available
    ncb_amount = round(basic_od * ncb_pct / 100, 2) if ncb_pct > 0 and basic_od > 0 else 0

    # ==================== 1. EMERGENCY INFO (EAZR_03 S4) ====================
    # Insurer helpline lookup
    helpline_map = {
        'icici lombard': '1800-266-9725',
        'hdfc ergo': '1800-266-0700',
        'bajaj allianz': '1800-209-5858',
        'new india': '1800-209-1415',
        'united india': '1800-425-3333',
        'national insurance': '1800-345-0330',
        'oriental insurance': '1800-118-485',
        'tata aig': '1800-266-7780',
        'reliance general': '1800-102-1010',
        'iffco tokio': '1800-103-5499',
        'sbi general': '1800-102-1111',
        'acko': '18004250005',
        'go digit': '1800-258-5956',
        'cholamandalam': '1800-200-5544',
        'royal sundaram': '1800-568-9999',
        'future generali': '1800-220-233',
        'kotak general': '1800-266-4545',
        'magma hdi': '1800-200-9444',
        'star health': '1800-425-2255',
    }
    insurer_lower = insurer_name.lower() if insurer_name else ""
    helpline = policy_identification.get("insurerTollFree") or ""
    if not helpline:
        for key, val in helpline_map.items():
            if key in insurer_lower:
                helpline = val
                break
    if not helpline:
        helpline = "1800-XXX-XXXX"

    claim_email = extracted_data.get("claimEmail") or policy_identification.get("claimEmail") or ""
    claim_app = extracted_data.get("claimApp") or policy_identification.get("claimApp") or ""

    emergency_info = {
        "policyNumber": policy_number,
        "registrationNumber": reg_number,
        "insurerName": insurer_name,
        "helpline": helpline,
        "claimEmail": claim_email,
        "claimApp": claim_app,
        "roadsideAssistance": has_rsa,
        "roadsideAssistanceNumber": helpline if has_rsa else "",
        "actions": [
            {"label": "Copy Policy No.", "action": "copy", "value": policy_number, "icon": "copy"},
            {"label": "Copy Reg. No.", "action": "copy", "value": reg_number, "icon": "copy"},
            {"label": "Call Helpline", "action": "call", "value": helpline, "icon": "phone"},
            {"label": "Find Nearest Garage", "action": "open_map", "value": "network_garages", "icon": "map"}
        ]
    }

    # ==================== 2. POLICY OVERVIEW (EAZR_03 S4) ====================
    # Product type display
    product_display_map = {
        "COMP_CAR": "Comprehensive (OD + TP)",
        "COMP_2W": "Comprehensive (OD + TP)",
        "TP_CAR": "Third Party Only",
        "TP_2W": "Third Party Only",
        "SAOD": "Standalone OD",
        "COMP_CV": "Commercial Vehicle - Comprehensive",
        "TP_CV": "Commercial Vehicle - TP Only"
    }
    product_type_display = product_display_map.get(product_type, "Comprehensive")

    vehicle = {
        "registrationNumber": reg_number,
        "make": vehicle_details.get("vehicleMake", ""),
        "model": vehicle_details.get("vehicleModel", ""),
        "variant": vehicle_details.get("vehicleVariant", ""),
        "manufacturingYear": manufacturing_year,
        "vehicleAge": vehicle_age,
        "fuelType": vehicle_details.get("fuelType", ""),
        "vehicleType": vehicle_details.get("vehicleClass", "Private Car"),
        "vehicleCategory": vehicle_details.get("vehicleCategory", ""),
        "cubicCapacity": vehicle_details.get("cubicCapacity", ""),
        "seatingCapacity": vehicle_details.get("seatingCapacity", ""),
        "color": vehicle_details.get("vehicleColor", ""),
        "registrationDate": vehicle_details.get("registrationDate", ""),
        "engineNumber": vehicle_details.get("engineNumber", ""),
        "chassisNumber": vehicle_details.get("chassisNumber", ""),
        "rtoLocation": vehicle_details.get("rtoLocation", ""),
        "hypothecation": vehicle_details.get("hypothecation") or {},
        # §9 FIX: Display-ready hypothecation bank name
        "financedBy": _hyp_bank if _hyp_bank else None,
    }

    # Owner details
    owner = {
        "name": owner_details.get("ownerName") or extracted_data.get("policyHolderName", ""),
        "type": owner_details.get("ownerType", "individual"),
        "contactNumber": owner_details.get("ownerContact", ""),
        "email": owner_details.get("ownerEmail", ""),
        "address": owner_details.get("ownerAddress", ""),
        "panNumber": owner_details.get("panNumber", "")
    }

    policy_overview = {
        "insurer": {
            "name": insurer_name,
            "logo": get_insurer_logo_url(insurer_name),
        },
        "productType": product_type,
        "productTypeDisplay": product_type_display,
        "vehicle": vehicle,
        "coverage": {
            "idv": idv,
            "idvFormatted": f"₹{idv:,.0f}" if idv > 0 else "N/A",
            "ncbPercentage": ncb_pct,
            "ncbAmount": ncb_amount,
            "ncbAmountFormatted": f"₹{ncb_amount:,.0f}",
        },
        "validity": {
            "startDate": start_date,
            "endDate": end_date,
            "status": policy_status,
            "daysRemaining": days_remaining,
            "progressPercent": progress_percent
        },
        "previousPolicy": {
            "previousInsurer": policy_identification.get("previousInsurer") or extracted_data.get("previousInsurer", ""),
            "previousPolicyNumber": policy_identification.get("previousPolicyNumber") or ""
        },
        "owner": owner
    }

    # ==================== 3. COVERAGE DETAILS (EAZR_03 S3.3, S4) ====================
    # IDV Card
    adequacy_pct = round((idv / estimated_market_value) * 100, 1) if estimated_market_value > 0 else 0
    idv_card = {
        "currentIdv": idv,
        "currentIdvFormatted": f"₹{idv:,.0f}" if idv > 0 else "N/A",
        "marketValueEstimate": estimated_market_value,
        "marketValueFormatted": f"₹{estimated_market_value:,.0f}" if estimated_market_value > 0 else "N/A",
        "adequacyPercentage": adequacy_pct,
        "adequacyStatus": "adequate" if adequacy_pct >= 90 else ("under" if adequacy_pct >= 80 else "low"),
        "adequacyColor": "#22C55E" if adequacy_pct >= 90 else ("#EAB308" if adequacy_pct >= 80 else "#EF4444"),
        "whatIsIdv": "IDV is the maximum amount you receive in case of total loss or theft. It represents your vehicle's current market value minus depreciation."
    }

    # OD Coverage
    has_od = 'TP_' not in product_type
    od_coverage = {
        "covered": has_od,
        "premium": od_premium,
        "premiumFormatted": f"₹{od_premium:,.0f}" if od_premium > 0 else "N/A",
        "deductible": {
            "compulsory": compulsory_deductible,
            "compulsoryFormatted": f"₹{compulsory_deductible:,.0f}" if compulsory_deductible > 0 else "₹0",
            "voluntary": voluntary_deductible,
            "voluntaryFormatted": f"₹{voluntary_deductible:,.0f}" if voluntary_deductible > 0 else "₹0",
            "planCopay": _plan_copay,
            "planCopayFormatted": f"₹{_plan_copay:,.0f}" if _plan_copay > 0 else "₹0",
            "totalPerClaim": int(compulsory_deductible + voluntary_deductible + _plan_copay),
            "totalPerClaimFormatted": f"₹{int(compulsory_deductible + voluntary_deductible + _plan_copay):,}",
        },
        "geographicScope": "India"
    }

    # TP Coverage - SAOD policies have no TP component
    has_tp = product_type != 'SAOD'
    tp_coverage = {
        "covered": has_tp,
        "premium": tp_premium if has_tp else 0,
        "premiumFormatted": f"₹{tp_premium:,.0f}" if has_tp and tp_premium > 0 else "N/A",
        "deathBodilyInjury": "Unlimited" if has_tp else "Not covered (SAOD policy)",
        "propertyDamageLimit": 750000 if has_tp else 0,
        "propertyDamageLimitFormatted": "₹7,50,000" if has_tp else "Not covered",
        "description": "As per Motor Vehicles Act - mandatory" if has_tp else "Standalone OD policy - TP coverage must be purchased separately"
    }

    # PA Coverage
    pa_coverage = {
        "ownerDriver": {
            "covered": pa_owner_cover > 0,
            "sumInsured": pa_owner_cover,
            "sumInsuredFormatted": f"₹{pa_owner_cover:,.0f}" if pa_owner_cover > 0 else "₹15,00,000 (statutory)",
            "compulsory": True,
            "description": "Personal Accident cover for owner-driver (statutory minimum ₹15L)"
        },
        "unnamedPassengers": {
            "covered": pa_passengers > 0,
            "sumInsuredPerPassenger": pa_passengers,
            "sumInsuredFormatted": f"₹{pa_passengers:,.0f}" if pa_passengers > 0 else "Not covered"
        },
        "paidDriver": {
            "covered": pa_paid_driver > 0,
            "sumInsured": pa_paid_driver,
            "sumInsuredFormatted": f"₹{pa_paid_driver:,.0f}" if pa_paid_driver > 0 else "Not covered"
        },
        "legalLiabilityPaidDriver": {
            "covered": has_ll_paid_driver
        },
        "legalLiabilityEmployees": {
            "covered": has_ll_employees
        }
    }

    coverage_section = {
        "idvCard": idv_card,
        "odCoverage": od_coverage,
        "tpCoverage": tp_coverage,
        "paCoverage": pa_coverage,
    }

    # ==================== 4. ADD-ONS (EAZR_03 S3.4, S4) ====================
    # All 15 add-on types from spec
    addon_defs = [
        {"code": "zero_depreciation", "name": "Zero Depreciation", "icon": "verified", "has": has_zero_dep,
         "description": "No depreciation deduction on parts during claim",
         "benefit": "Save ₹15,000-40,000 on parts replacement claims",
         "importanceByAge": {"0-3": "highly_recommended", "3-5": "recommended", "5+": "optional"}},
        {"code": "engine_protect", "name": "Engine Protection", "icon": "settings", "has": has_engine_protect,
         "description": "Engine damage from water ingression/oil leakage covered",
         "benefit": "Covers engine repairs worth ₹50,000-3,00,000",
         "importanceByRegion": "Highly recommended in flood-prone areas"},
        {"code": "roadside_assistance", "name": "24x7 Roadside Assistance", "icon": "local_shipping", "has": has_rsa,
         "description": "Towing, flat tyre, battery jumpstart, fuel delivery, key lockout",
         "benefit": "Unlimited towing + on-spot repair assistance"},
        {"code": "return_to_invoice", "name": "Return to Invoice (RTI)", "icon": "receipt_long", "has": has_rti,
         "description": "Get on-road price (not IDV) in case of total loss",
         "benefit": "Full on-road price recovered in total loss/theft",
         "importanceByAge": {"0-2": "highly_recommended", "2-3": "recommended", "3+": "not_available"}},
        {"code": "consumables_cover", "name": "Consumables Cover", "icon": "build", "has": has_consumables,
         "description": "Covers nuts, bolts, screws, oil, coolant during claim",
         "benefit": "Save ₹2,000-10,000 per claim"},
        {"code": "ncb_protect", "name": "NCB Protection", "icon": "shield", "has": has_ncb_protect,
         "description": "Retain NCB even after making a claim (1-2 claims/year)",
         "benefit": f"Protect {ncb_pct}% NCB worth ₹{ncb_amount:,.0f}/year" if ncb_pct > 0 else "Protect future NCB"},
        {"code": "key_replacement", "name": "Key Replacement", "icon": "key", "has": has_key_replace,
         "description": "Covers cost of replacing lost/damaged vehicle keys",
         "benefit": "Key replacement can cost ₹5,000-50,000 for modern cars"},
        {"code": "tyre_protect", "name": "Tyre Protection", "icon": "tire_repair", "has": has_tyre_protect,
         "description": "Covers tyre damage from road hazards",
         "benefit": "Tyre replacement costs ₹3,000-15,000 per tyre"},
        {"code": "personal_baggage", "name": "Personal Effects & Baggage", "icon": "luggage", "has": has_personal_baggage,
         "description": "Covers loss of personal effects and belongings inside the vehicle",
         "benefit": "Protection for valuables during transit — covers theft/damage of personal items"},
        {"code": "emi_protect", "name": "EMI Protector", "icon": "payments", "has": has_emi_protect,
         "description": "Covers EMIs during repair period if vehicle is on loan",
         "benefit": "EMI coverage during vehicle downtime"},
        {"code": "outstation_emergency", "name": "Outstation Emergency", "icon": "flight", "has": has_outstation,
         "description": "Hotel, travel expenses during breakdown outstation",
         "benefit": "Emergency support during outstation breakdown"},
        {"code": "daily_allowance", "name": "Daily Allowance", "icon": "calendar_today", "has": has_daily_allowance,
         "description": "Daily cash allowance during repair period",
         "benefit": "₹500-1,500/day during vehicle repair"},
        {"code": "windshield_cover", "name": "Windshield Cover", "icon": "window", "has": has_windshield,
         "description": "Covers windshield replacement without affecting NCB",
         "benefit": "Windshield replacement: ₹5,000-30,000"},
        {"code": "electric_vehicle_cover", "name": "EV Cover", "icon": "ev_station", "has": has_ev_cover,
         "description": "Covers EV-specific components: charger, wallbox, cables",
         "benefit": "Protection for EV charging infrastructure"},
        {"code": "battery_protect", "name": "Battery Protection", "icon": "battery_full", "has": has_battery_protect,
         "description": "Covers battery damage/replacement for EV/Hybrid vehicles",
         "benefit": "EV battery replacement can cost ₹3L-10L"},
    ]

    active_addons = []
    missing_recommended = []
    addon_idx = 0
    for ad in addon_defs:
        if ad["has"]:
            addon_idx += 1
            active_addons.append({
                "id": f"addon_{addon_idx}",
                "addonCode": ad["code"],
                "name": ad["name"],
                "value": "Covered",
                "icon": ad["icon"],
                "covered": True,
                "description": ad["description"],
                "benefit": ad["benefit"]
            })
        else:
            # Check if this addon is recommended based on vehicle age/context
            is_recommended = False
            if ad["code"] == "zero_depreciation" and vehicle_age <= 5:
                is_recommended = True
            elif ad["code"] == "engine_protect":
                is_recommended = True
            elif ad["code"] == "return_to_invoice" and vehicle_age <= 2:
                is_recommended = True
            elif ad["code"] == "roadside_assistance":
                is_recommended = True
            elif ad["code"] == "ncb_protect" and ncb_pct >= 35:
                is_recommended = True
            elif ad["code"] == "consumables_cover":
                is_recommended = True

            if is_recommended:
                missing_recommended.append({
                    "addonCode": ad["code"],
                    "name": ad["name"],
                    "icon": ad["icon"],
                    "description": ad["description"],
                    "benefit": ad["benefit"],
                    "recommended": True,
                    "reason": f"Recommended for {vehicle_age}-year old vehicle" if "Age" in ad.get("importanceByAge", {}) else "Recommended for comprehensive protection"
                })

    addons_section = {
        "activeAddons": active_addons,
        "activeCount": len(active_addons),
        "missingRecommended": missing_recommended,
        "missingCount": len(missing_recommended),
        "totalAvailable": 15
    }

    # ==================== 5. NCB TRACKER (EAZR_03 S4, S10.1) ====================
    ncb_progression_map = {0: 0, 20: 1, 25: 2, 35: 3, 45: 4, 50: 5}
    claim_free_years = ncb_progression_map.get(ncb_pct, 0)
    next_ncb_map = {0: 20, 20: 25, 25: 35, 35: 45, 45: 50, 50: 50}
    next_ncb_pct = next_ncb_map.get(ncb_pct, 50)

    ncb_tracker = {
        "current": {
            "percentage": ncb_pct,
            "claimFreeYears": claim_free_years,
            "description": f"{claim_free_years} claim-free year(s)" if ncb_pct > 0 else "No NCB - first year or claim made"
        },
        "progression": [
            {"year": 0, "percentage": 0, "label": "Year 0", "active": ncb_pct >= 0, "current": ncb_pct == 0},
            {"year": 1, "percentage": 20, "label": "Year 1", "active": ncb_pct >= 20, "current": ncb_pct == 20},
            {"year": 2, "percentage": 25, "label": "Year 2", "active": ncb_pct >= 25, "current": ncb_pct == 25},
            {"year": 3, "percentage": 35, "label": "Year 3", "active": ncb_pct >= 35, "current": ncb_pct == 35},
            {"year": 4, "percentage": 45, "label": "Year 4", "active": ncb_pct >= 45, "current": ncb_pct == 45},
            {"year": 5, "percentage": 50, "label": "Year 5+", "active": ncb_pct >= 50, "current": ncb_pct == 50},
        ],
        "nextTarget": {
            "percentage": next_ncb_pct,
            "yearsRemaining": 1 if ncb_pct < 50 else 0,
            "description": f"1 more claim-free year to reach {next_ncb_pct}% NCB" if ncb_pct < 50 else "Maximum NCB achieved!"
        },
        "savings": {
            "ncbAmount": ncb_amount,
            "ncbAmountFormatted": f"₹{ncb_amount:,.0f}",
            "description": f"Saving ₹{ncb_amount:,.0f} this year due to {ncb_pct}% NCB" if ncb_amount > 0 else "Build NCB with claim-free years"
        },
        "ncbProtectActive": has_ncb_protect,
        "claimImpact": {
            "withoutProtect": f"NCB resets to 0% - lose ₹{ncb_amount:,.0f}/year",
            "withProtect": "NCB retained even after claim (1-2 claims/year)"
        },
        "rules": {
            "claimImpact": "Resets to 0% on claim (unless NCB Protect active)",
            "transfer": "Transferable to new vehicle of same class",
            "portability": "Transferable to new insurer with NCB certificate",
            "validity": "NCB valid for 90 days after policy expiry"
        }
    }

    # ==================== 6. IDV ANALYSIS (EAZR_03 S3.3, S10.2) ====================
    depreciation_schedule = [
        {"age": "0-6 months", "depreciation": 5, "idvCalc": "95% of Invoice Price"},
        {"age": "6-12 months", "depreciation": 15, "idvCalc": "85% of Invoice Price"},
        {"age": "1-2 years", "depreciation": 20, "idvCalc": "80% of Invoice Price"},
        {"age": "2-3 years", "depreciation": 30, "idvCalc": "70% of Invoice Price"},
        {"age": "3-4 years", "depreciation": 40, "idvCalc": "60% of Invoice Price"},
        {"age": "4-5 years", "depreciation": 50, "idvCalc": "50% of Invoice Price"},
    ]

    gap_in_total_loss = round(max(0, estimated_market_value - idv), 2)
    idv_analysis = {
        "current": {
            "idv": idv,
            "idvFormatted": f"₹{idv:,.0f}" if idv > 0 else "N/A",
            "description": "Insured Declared Value - max claim in total loss"
        },
        "marketValue": {
            "estimated": estimated_market_value,
            "estimatedFormatted": f"₹{estimated_market_value:,.0f}" if estimated_market_value > 0 else "N/A",
        },
        "adequacy": {
            "percentage": adequacy_pct,
            "status": "adequate" if adequacy_pct >= 90 else ("under" if adequacy_pct >= 80 else "low"),
            "color": "#22C55E" if adequacy_pct >= 90 else ("#EAB308" if adequacy_pct >= 80 else "#EF4444"),
            "description": f"IDV is {adequacy_pct}% of estimated market value"
        },
        "gapInTotalLoss": gap_in_total_loss,
        "gapFormatted": f"₹{gap_in_total_loss:,.0f}",
        "depreciationSchedule": depreciation_schedule,
        "vehicleAge": vehicle_age,
        "recommendation": "Consider requesting higher IDV at renewal" if adequacy_pct < 90 else "IDV is adequate for your vehicle"
    }

    # ==================== 7. PREMIUM BREAKDOWN (EAZR_03 S3.6) ====================
    # Build detailed premium breakdown per spec
    od_premium_details = {
        "basicOdPremium": _safe_float(premium_breakdown.get("basicOdPremium"), od_premium),
        "basicOdPremiumFormatted": f"₹{_safe_float(premium_breakdown.get('basicOdPremium'), od_premium):,.0f}",
        "ncbDiscount": ncb_discount,
        "ncbDiscountFormatted": f"-₹{ncb_discount:,.0f}" if ncb_discount > 0 else "₹0",
        "voluntaryDeductibleDiscount": _safe_float(premium_breakdown.get("voluntaryDeductibleDiscount"), 0),
        "electricalAccessoriesPremium": _safe_float(premium_breakdown.get("electricalAccessoriesPremium"), 0),
        "nonElectricalAccessoriesPremium": _safe_float(premium_breakdown.get("nonElectricalAccessoriesPremium"), 0),
        "cngLpgKitPremium": _safe_float(premium_breakdown.get("cngLpgKitPremium"), 0),
        "addonPremiums": add_on_total_premium,
        "addonPremiumsFormatted": f"₹{add_on_total_premium:,.0f}",
        "netOdPremium": od_premium,
        "netOdPremiumFormatted": f"₹{od_premium:,.0f}",
    }

    tp_premium_details = {
        "basicTpPremium": tp_premium,
        "basicTpPremiumFormatted": f"₹{tp_premium:,.0f}",
        "paOwnerDriverPremium": _safe_float(premium_breakdown.get("paOwnerDriverPremium"), 0),
        "paPassengersPremium": _safe_float(premium_breakdown.get("paPassengersPremium"), 0),
        "paPaidDriverPremium": _safe_float(premium_breakdown.get("paPaidDriverPremium"), 0),
        "llPaidDriverPremium": _safe_float(premium_breakdown.get("llPaidDriverPremium"), 0),
        "netTpPremium": tp_premium,
        "netTpPremiumFormatted": f"₹{tp_premium:,.0f}",
    }

    gross_premium = od_premium + tp_premium
    per_month = round(total_premium / 12, 2) if total_premium > 0 else 0

    premium_section = {
        "odPremium": od_premium_details,
        "tpPremium": tp_premium_details,
        "grossPremium": round(gross_premium, 2),
        "grossPremiumFormatted": f"₹{gross_premium:,.0f}",
        "gst": round(gst_amount, 2),
        "gstFormatted": f"₹{gst_amount:,.0f}",
        "gstRate": "18%",
        "totalPremium": round(total_premium, 2),
        "totalPremiumFormatted": f"₹{total_premium:,.0f}",
        "frequency": "Annual",
        "perMonth": per_month,
        "perMonthFormatted": f"₹{per_month:,.0f}/month",
        "taxBenefit": {
            "eligible": False,
            "description": "Motor insurance not eligible for tax deduction under Section 80D"
        }
    }

    # ==================== 8. CLAIMS INFO (EAZR_03 S3.7) ====================
    claims_info = {
        "claimHelpline": helpline,
        "claimEmail": claim_email,
        "claimApp": claim_app,
        "cashlessProcess": [
            {"step": 1, "title": "Visit Network Garage", "description": "Drive to nearest network garage or call for towing", "icon": "directions_car"},
            {"step": 2, "title": "Show Documents", "description": "Show policy and vehicle registration", "icon": "description"},
            {"step": 3, "title": "Garage Sends Estimate", "description": "Garage submits repair estimate to insurer", "icon": "receipt"},
            {"step": 4, "title": "Insurer Approval", "description": "Approval typically within 2-4 hours", "icon": "check_circle"},
            {"step": 5, "title": "Vehicle Repaired", "description": "Repair done at network garage", "icon": "build"},
            {"step": 6, "title": "Cashless Settlement", "description": "Payment directly to garage - pay only deductible/non-covered items", "icon": "payment"}
        ],
        "claimIntimationTimeline": {
            "ownDamage": "Within 24-48 hours",
            "thirdParty": "Immediately",
            "theft": "Immediately to police, then insurer within 24 hours"
        },
        "networkGarages": {
            "description": "Network garages for cashless repairs"
        }
    }

    # ==================== 9. EXCLUSIONS ====================
    # Use policy-extracted exclusions if available, fall back to standard defaults
    extracted_exclusions = category_data.get("exclusions", {})
    policy_exclusions = extracted_exclusions.get("otherExclusions", [])
    if not isinstance(policy_exclusions, list):
        policy_exclusions = []

    # Standard permanent exclusions (always applicable per Motor Vehicles Act)
    default_permanent = [
        "Driving under influence of alcohol/drugs",
        "Driver without valid driving license",
        "Normal wear and tear, mechanical/electrical breakdown",
        "Consequential loss - depreciation, wear & tear",
        "Contractual liability",
        "Damage to tyres/tubes (unless vehicle damaged simultaneously)",
        "Use outside geographical area"
    ]

    # Merge extracted exclusions with defaults, avoiding duplicates
    if policy_exclusions:
        # Use extracted as primary, add any standard ones not already captured
        combined_permanent = list(policy_exclusions)
        existing_lower = {e.lower() for e in combined_permanent}
        for de in default_permanent:
            if de.lower() not in existing_lower:
                combined_permanent.append(de)
    else:
        combined_permanent = default_permanent

    exclusions_section = {
        "permanent": combined_permanent,
        "conditional": [
            "Driven by person not covered (unless nominated)",
            "PA cover for paid driver (unless specified)",
            "Accessories damage (unless manufacturer-fitted)",
            "Business use (unless stated in policy)",
        ],
        "collapsed": True
    }

    # ==================== 10. RENEWAL INFO (EAZR_03 S4) ====================
    renewal_info = {
        "renewalDueDate": end_date,
        "daysUntilRenewal": days_remaining,
        "estimatedRenewalPremium": total_premium,
        "estimatedRenewalPremiumFormatted": f"₹{total_premium:,.0f}",
        "ncbAtRenewal": next_ncb_pct if ncb_pct < 50 else 50,
        "ncbAtRenewalDescription": f"NCB will be {next_ncb_pct}% at renewal if no claims" if ncb_pct < 50 else "Maximum 50% NCB maintained",
        "ncbAtStake": {
            "percentage": ncb_pct,
            "amount": ncb_amount,
            "amountFormatted": f"₹{ncb_amount:,.0f}",
            "warning": f"Don't let policy lapse! You'll lose {ncb_pct}% NCB worth ₹{ncb_amount:,.0f}" if ncb_pct > 0 else ""
        },
        "actions": [
            {"label": "Set Reminder", "action": "set_renewal_reminder", "icon": "notifications"},
            {"label": "Renew Now", "action": "renew_policy", "icon": "autorenew"}
        ]
    }

    # ==================== 11. SCORING ENGINE (EAZR_03 S5) ====================
    score_s1 = _calculate_coverage_adequacy(policy_data, vehicle_age, idv, estimated_market_value)
    score_s2 = _calculate_claim_readiness(policy_data, insurer_name)
    score_s3 = _calculate_value_for_money(policy_data, ncb_pct, idv, total_premium)

    s1_label = get_score_label(score_s1["score"])
    s2_label = get_score_label(score_s2["score"])
    s3_label = get_score_label(score_s3["score"])

    # Weighted overall score
    overall_score = round(score_s1["score"] * 0.40 + score_s2["score"] * 0.35 + score_s3["score"] * 0.25)
    overall_label = get_score_label(overall_score)

    scoring_engine = {
        "overallScore": overall_score,
        "overallLabel": overall_label["label"],
        "overallColor": overall_label["color"],
        "scores": [
            {
                "scoreId": "S1",
                "name": "Coverage Adequacy",
                "purpose": "How well your vehicle is protected",
                "weight": "40%",
                "score": score_s1["score"],
                "label": s1_label["label"],
                "color": s1_label["color"],
                "factors": score_s1["factors"]
            },
            {
                "scoreId": "S2",
                "name": "Claim Readiness",
                "purpose": "How smooth your claim experience will be",
                "weight": "35%",
                "score": score_s2["score"],
                "label": s2_label["label"],
                "color": s2_label["color"],
                "factors": score_s2["factors"]
            },
            {
                "scoreId": "S3",
                "name": "Value for Money",
                "purpose": "Premium efficiency and savings",
                "weight": "25%",
                "score": score_s3["score"],
                "label": s3_label["label"],
                "color": s3_label["color"],
                "factors": score_s3["factors"]
            }
        ]
    }

    # ==================== 12. SCENARIO SIMULATIONS (EAZR_03 S6) ====================
    scenarios = _simulate_motor_scenarios(policy_data, idv, ncb_pct, od_premium, vehicle_age)

    # ==================== 13. GAP ANALYSIS (EAZR_03 S7) ====================
    rto_city = vehicle_details.get("rtoLocation", "")
    gaps = _analyze_motor_gaps(policy_data, vehicle_age, idv, estimated_market_value, ncb_pct, od_premium, rto_city)

    gap_analysis = {
        "totalGaps": len(gaps),
        "highSeverity": len([g for g in gaps if g["severity"] == "high"]),
        "mediumSeverity": len([g for g in gaps if g["severity"] == "medium"]),
        "lowSeverity": len([g for g in gaps if g["severity"] in ["low", "info"]]),
        "gaps": gaps,
        "summary": f"{len(gaps)} coverage gap(s) identified" if gaps else "No significant coverage gaps found"
    }

    # ==================== 14. RECOMMENDATIONS (EAZR_03 S8) ====================
    recommendations = _generate_motor_recommendations(policy_data, gaps, vehicle_age, ncb_pct, idv, estimated_market_value)

    recommendations_section = {
        "totalRecommendations": len(recommendations),
        "recommendations": recommendations,
        "summary": f"{len(recommendations)} recommendation(s) to improve your coverage" if recommendations else "Your policy coverage looks good!"
    }

    # ==================== 15. IPF INTEGRATION (EAZR_03 S9) ====================
    ipf = _calculate_motor_ipf(total_premium, product_type)

    ipf_touchpoints = []
    if days_remaining <= 30 and days_remaining > 0:
        ipf_touchpoints.append({
            "touchpoint": "renewal_reminder",
            "trigger": f"Renewal due in {days_remaining} days",
            "cta": "Finance renewal premium",
            "icon": "notifications"
        })
    if total_premium > 15000:
        ipf_touchpoints.append({
            "touchpoint": "premium_financing",
            "trigger": f"Premium ₹{total_premium:,.0f} eligible for EMI",
            "cta": "Pay in EMIs",
            "icon": "payments"
        })
    if gaps:
        ipf_eligible_gaps = [g for g in gaps if g.get("ipfEligible")]
        if ipf_eligible_gaps:
            ipf_touchpoints.append({
                "touchpoint": "gap_analysis",
                "trigger": f"{len(ipf_eligible_gaps)} add-on(s) recommended",
                "cta": "Add and finance",
                "icon": "add_circle"
            })
    if 'TP_' in product_type:
        ipf_touchpoints.append({
            "touchpoint": "upgrade_comprehensive",
            "trigger": "TP-only policy - upgrade to Comprehensive",
            "cta": "Upgrade with EMIs",
            "icon": "upgrade"
        })

    ipf_section = {
        "emiOptions": ipf,
        "touchpoints": ipf_touchpoints
    }

    # ==================== BUILD FINAL STRUCTURE ====================
    return {
        "emergencyInfo": emergency_info,
        "policyOverview": policy_overview,
        "coverageDetails": coverage_section,
        "addOns": addons_section,
        "ncbTracker": ncb_tracker,
        "idvAnalysis": idv_analysis,
        "premiumBreakdown": premium_section,
        "claims": claims_info,
        "exclusions": exclusions_section,
        "renewalInfo": renewal_info,
        "scoringEngine": scoring_engine,
        "scenarioSimulations": scenarios,
        "gapAnalysis": gap_analysis,
        "recommendations": recommendations_section,
        "ipfIntegration": ipf_section
    }
