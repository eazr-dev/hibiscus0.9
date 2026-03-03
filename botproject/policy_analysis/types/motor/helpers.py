"""Motor Insurance Helper Functions (EAZR_03 Spec)
Scoring, scenarios, gaps, recommendations for motor insurance policies.
"""

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== MOTOR INSURANCE HELPER FUNCTIONS (EAZR_03 Spec) ====================

def detect_motor_product_type(extracted_data: dict, category_data: dict = None) -> str:
    """Determine motor insurance product type per EAZR_03 Section 2.1"""
    vehicle_type = str(extracted_data.get('vehicleClass', '') or extracted_data.get('vehicle_type', '') or '').lower()
    od_premium = extracted_data.get('odPremium', 0) or 0
    tp_premium = extracted_data.get('tpPremium', 0) or 0
    product_type = str(extracted_data.get('productType', '') or '').lower()

    # Also check categorySpecificData.policyIdentification.productType (more reliable source)
    if category_data:
        cat_product_type = str(category_data.get("policyIdentification", {}).get("productType", "") or "").lower()
        if cat_product_type and not product_type:
            product_type = cat_product_type
        elif cat_product_type:
            # Category data product type takes precedence if it's more specific
            for keyword in ['standalone', 'saod', 'third party', 'tp only', 'liability only']:
                if keyword in cat_product_type:
                    product_type = cat_product_type
                    break

    try:
        od_premium = float(od_premium)
    except (ValueError, TypeError):
        od_premium = 0
    try:
        tp_premium = float(tp_premium)
    except (ValueError, TypeError):
        tp_premium = 0

    # For SAOD policies, TP premium may only be PA premium (statutory PA owner-driver)
    # Check if TP premium is just PA premium — not real TP liability
    pa_premium = 0
    if category_data:
        pb = category_data.get("premiumBreakdown", {})
        pa_premium = float(pb.get("paOwnerDriverPremium", 0) or 0)
    actual_tp = tp_premium - pa_premium if pa_premium > 0 else tp_premium

    has_od = od_premium > 0
    has_tp = actual_tp > 0

    # Determine vehicle category
    if any(term in vehicle_type for term in ['car', 'sedan', 'suv', 'hatchback', 'private car', 'four wheeler']):
        vehicle_cat = 'CAR'
    elif any(term in vehicle_type for term in ['bike', 'scooter', 'motorcycle', '2w', 'two wheeler', 'moped']):
        vehicle_cat = '2W'
    elif any(term in vehicle_type for term in ['truck', 'bus', 'commercial', 'goods', 'pcv', 'gcv']):
        vehicle_cat = 'CV'
    else:
        vehicle_cat = 'CAR'

    # Check product type string first
    if 'standalone' in product_type or 'saod' in product_type or 'stand alone' in product_type:
        return 'SAOD'
    if 'third party' in product_type or 'tp only' in product_type or 'liability only' in product_type:
        return f'TP_{vehicle_cat}'

    # Determine coverage type from premiums
    if has_od and has_tp:
        return f'COMP_{vehicle_cat}'
    elif has_tp and not has_od:
        return f'TP_{vehicle_cat}'
    elif has_od and not has_tp:
        return 'SAOD'

    return f'COMP_{vehicle_cat}'


def _calculate_coverage_adequacy(policy_data: dict, vehicle_age: int, idv: float, market_value: float) -> dict:
    """Score 1: Coverage Adequacy (0-100) per EAZR_03 Section 5.2"""
    score = 0
    factors = []

    # Factor 1: IDV vs Market Value (25 pts)
    idv_ratio = idv / market_value if market_value > 0 else 1
    if idv_ratio >= 0.95:
        f1 = 25
    elif idv_ratio >= 0.90:
        f1 = 22
    elif idv_ratio >= 0.85:
        f1 = 18
    elif idv_ratio >= 0.80:
        f1 = 14
    else:
        f1 = 8
    score += f1
    factors.append({"name": "IDV vs Market Value", "score": f1, "maxScore": 25, "detail": f"IDV is {idv_ratio*100:.0f}% of market value"})

    # Factor 2: Add-ons for Vehicle Age (25 pts)
    addons = policy_data.get("addons_map", {})
    if vehicle_age <= 3:
        required = ['zero_depreciation', 'return_to_invoice', 'engine_protect']
    elif vehicle_age <= 5:
        required = ['zero_depreciation', 'engine_protect', 'roadside_assistance']
    else:
        required = ['roadside_assistance', 'consumables_cover']
    have = sum(1 for r in required if addons.get(r))
    f2 = int((have / len(required)) * 25) if required else 25
    score += f2
    factors.append({"name": "Add-ons for Vehicle Age", "score": f2, "maxScore": 25, "detail": f"{have}/{len(required)} relevant add-ons active"})

    # Factor 3: PA Cover (15 pts)
    pa_owner = policy_data.get("pa_owner_covered", False)
    pa_passengers = policy_data.get("pa_passengers_covered", False)
    # §1 FIX: Proportional PA scoring per IRDAI structure
    # PA sits under Liability (Section II/III), NOT under add-ons
    # Owner-Driver PA (mandatory since 2019): 10 pts
    # Unnamed Passengers PA (IMT 16): +3 pts
    # Named Persons PA (IMT 15): +2 pts
    # Enhanced PA (above ₹15L standard): +2 bonus pts
    # Cap at 15
    f3 = 0
    pa_details = []
    pa_owner_sum = policy_data.get("pa_owner_sum", 0)
    pa_named_persons = policy_data.get("pa_named_persons_covered", False)
    if pa_owner:
        f3 += 10
        pa_details.append("Owner-Driver PA")
        if pa_owner_sum > 1500000:  # Enhanced PA above ₹15L standard
            f3 += 2
            pa_details.append("Enhanced PA")
    if pa_passengers:
        f3 += 3
        pa_details.append("Unnamed Passengers (IMT 16)")
    if pa_named_persons:
        f3 += 2
        pa_details.append("Named Persons (IMT 15)")
    f3 = min(f3, 15)
    score += f3
    pa_detail_str = " + ".join(pa_details) if pa_details else "No PA cover detected"
    factors.append({"name": "PA Cover", "score": f3, "maxScore": 15, "detail": pa_detail_str})

    # Factor 4: TP Limit (10 pts) - check if TP coverage exists based on product type
    product_type = policy_data.get("product_type", "COMP_CAR")
    if product_type == "SAOD":
        f4 = 0
        tp_detail = "Standalone OD policy — no TP coverage (must be purchased separately)"
    else:
        f4 = 10
        tp_detail = "Statutory TP cover active"
    score += f4
    factors.append({"name": "TP Limit", "score": f4, "maxScore": 10, "detail": tp_detail})

    # Factor 5: Deductible (10 pts)
    deductible = policy_data.get("voluntary_deductible", 0)
    if deductible <= 1000:
        f5 = 10
    elif deductible <= 2500:
        f5 = 8
    elif deductible <= 5000:
        f5 = 5
    else:
        f5 = 3
    score += f5
    factors.append({"name": "Deductible Level", "score": f5, "maxScore": 10, "detail": f"Voluntary deductible: ₹{deductible:,.0f}"})

    # Factor 6: Accessories (10 pts)
    if policy_data.get("electrical_accessories_premium", 0) > 0 or policy_data.get("non_electrical_accessories_premium", 0) > 0:
        f6 = 10
    else:
        f6 = 5
    score += f6
    factors.append({"name": "Accessories Coverage", "score": f6, "maxScore": 10, "detail": "Accessories covered" if f6 == 10 else "No accessories premium"})

    # Factor 7: Geographic Scope (5 pts)
    f7 = 3
    score += f7
    factors.append({"name": "Geographic Scope", "score": f7, "maxScore": 5, "detail": "India standard scope"})

    return {"score": min(score, 100), "factors": factors}


def _calculate_claim_readiness(policy_data: dict, insurer_name: str) -> dict:
    """Score 2: Claim Readiness (0-100) per EAZR_03 Section 5.3"""
    score = 0
    factors = []
    addons = policy_data.get("addons_map", {})

    # Factor 1: Network Garages (25 pts)
    f1 = 15  # Default moderate
    score += f1
    factors.append({"name": "Network Garages", "score": f1, "maxScore": 25, "detail": "Network garage availability"})

    # Factor 2: Cashless Facility (20 pts)
    f2 = 20
    score += f2
    factors.append({"name": "Cashless Facility", "score": f2, "maxScore": 20, "detail": "Cashless repair available"})

    # Factor 3: Claim-friendly Add-ons (20 pts)
    claim_addons = ['zero_depreciation', 'consumables_cover']
    have = sum(1 for a in claim_addons if addons.get(a))
    f3 = int((have / len(claim_addons)) * 20) if claim_addons else 20
    score += f3
    factors.append({"name": "Claim-friendly Add-ons", "score": f3, "maxScore": 20, "detail": f"{have}/{len(claim_addons)} claim add-ons"})

    # Factor 4: RSA Available (15 pts)
    f4 = 15 if addons.get('roadside_assistance') else 0
    score += f4
    factors.append({"name": "RSA Available", "score": f4, "maxScore": 15, "detail": "RSA active" if f4 > 0 else "No RSA"})

    # Factor 5: Insurer Claim Reputation (15 pts)
    top_insurers = ['icici lombard', 'hdfc ergo', 'bajaj allianz', 'tata aig', 'new india']
    f5 = 12 if any(ins in insurer_name.lower() for ins in top_insurers) else 8
    score += f5
    factors.append({"name": "Insurer Reputation", "score": f5, "maxScore": 15, "detail": insurer_name})

    # Factor 6: Documentation (5 pts)
    f6 = 5
    score += f6
    factors.append({"name": "Documentation Ready", "score": f6, "maxScore": 5, "detail": "Policy uploaded to EAZR"})

    return {"score": min(score, 100), "factors": factors}


def _calculate_value_for_money(policy_data: dict, ncb_percentage: int, idv: float, total_premium: float) -> dict:
    """Score 3: Value for Money (0-100) per EAZR_03 Section 5.4"""
    score = 0
    factors = []

    # Factor 1: NCB Utilization (30 pts)
    if ncb_percentage >= 50:
        f1 = 30
    elif ncb_percentage >= 45:
        f1 = 25
    elif ncb_percentage >= 35:
        f1 = 20
    elif ncb_percentage >= 20:
        f1 = 15
    else:
        f1 = 5
    score += f1
    factors.append({"name": "NCB Utilization", "score": f1, "maxScore": 30, "detail": f"{ncb_percentage}% NCB applied"})

    # Factor 2: Premium vs Market (25 pts)
    f2 = 18  # Default adequate
    score += f2
    factors.append({"name": "Premium vs Market", "score": f2, "maxScore": 25, "detail": "Market rate comparison"})

    # Factor 3: Discounts Applied (20 pts)
    discounts_found = 0
    if ncb_percentage > 0:
        discounts_found += 1
    if policy_data.get("voluntary_deductible", 0) > 0:
        discounts_found += 1
    f3 = min(discounts_found * 10, 20)
    score += f3
    factors.append({"name": "Discounts Applied", "score": f3, "maxScore": 20, "detail": f"{discounts_found} discount(s) applied"})

    # Factor 4: Coverage per Rupee (15 pts) - tiered by addon count dynamically
    addon_count = sum(1 for v in policy_data.get("addons_map", {}).values() if v)
    if total_premium > 0:
        coverage_ratio = idv / total_premium
        # Dynamic benchmark — policies with more add-ons have lower ratio, which is expected
        if addon_count > 3:
            thresholds = (35, 25, 15)
        elif addon_count >= 1:
            thresholds = (50, 35, 20)
        else:
            thresholds = (80, 50, 30)
        if coverage_ratio >= thresholds[0]:
            f4 = 15
        elif coverage_ratio >= thresholds[1]:
            f4 = 12
        elif coverage_ratio >= thresholds[2]:
            f4 = 8
        else:
            f4 = 5
    else:
        f4 = 8
    score += f4
    factors.append({"name": "Coverage per Rupee", "score": f4, "maxScore": 15, "detail": f"₹{idv:,.0f} IDV for ₹{total_premium:,.0f} premium"})

    # Factor 5: Unnecessary Add-ons (10 pts) - assume none wasteful
    f5 = 8
    score += f5
    factors.append({"name": "No Wasteful Add-ons", "score": f5, "maxScore": 10, "detail": "Add-on efficiency check"})

    return {"score": min(score, 100), "factors": factors}


def _get_score_label(score: int) -> dict:
    """Return label and color for score per EAZR_03 Section 5.5"""
    if score >= 90:
        return {"label": "Excellent", "color": "#22C55E"}
    elif score >= 75:
        return {"label": "Strong", "color": "#84CC16"}
    elif score >= 60:
        return {"label": "Adequate", "color": "#EAB308"}
    elif score >= 40:
        return {"label": "Basic", "color": "#F97316"}
    else:
        return {"label": "Minimal", "color": "#6B7280"}


def _simulate_motor_scenarios(policy_data: dict, idv: float, ncb_percentage: int, od_premium: float, vehicle_age: int) -> list:
    """Generate 5 scenario simulations per EAZR_03 Section 6"""
    scenarios = []
    addons = policy_data.get("addons_map", {})
    has_rti = addons.get('return_to_invoice', False)
    has_zero_dep = addons.get('zero_depreciation', False)
    has_engine_protect = addons.get('engine_protect', False)
    has_ncb_protect = addons.get('ncb_protect', False)
    estimated_on_road = idv * 1.25 if idv > 0 else 0
    product_type = policy_data.get("product_type", "COMP_CAR")
    compulsory_deductible = int(policy_data.get("compulsory_deductible", 1000))
    plan_copay = int(policy_data.get("plan_copay", 0))
    voluntary_deductible = int(policy_data.get("voluntary_deductible", 0))
    claim_deductible = compulsory_deductible + voluntary_deductible + plan_copay

    # §9 FIX: Hypothecation/loan info for M001
    hypothecation_bank = policy_data.get("hypothecation_bank", "")
    has_loan = bool(hypothecation_bank)

    # M001: Total Loss - Theft
    gap_without_rti = estimated_on_road - idv if estimated_on_road > idv else 0
    m001_protected_oop = 0 if has_rti else gap_without_rti
    m001_loan_note = ""
    if has_loan:
        m001_loan_note = f"Vehicle is financed with {hypothecation_bank}. In total loss/theft, the insurer settles the outstanding loan first. You receive only the balance after loan settlement."
    scenarios.append({
        "scenarioId": "M001",
        "name": "Vehicle Stolen - Total Loss",
        "description": "Your vehicle is stolen and not recovered. What do you get?",
        "icon": "lock_open",
        "severity": "high",
        "withoutAddon": {
            "label": "Without RTI",
            "claimAmount": idv,
            "claimAmountFormatted": f"₹{idv:,.0f}",
            "gap": gap_without_rti,
            "gapFormatted": f"₹{gap_without_rti:,.0f}",
            "description": f"You receive IDV (₹{idv:,.0f}) but on-road value is ~₹{estimated_on_road:,.0f}"
        },
        "withAddon": {
            "label": "With RTI",
            "claimAmount": estimated_on_road,
            "claimAmountFormatted": f"₹{estimated_on_road:,.0f}",
            "gap": 0,
            "gapFormatted": "₹0",
            "description": "Full on-road price recovered"
        },
        # §2 FIX: Summary fields use PROTECTED (post-addon) values
        "yourStatus": "protected" if has_rti else "at_risk",
        "summaryOop": m001_protected_oop,
        "summaryOopFormatted": f"₹{m001_protected_oop:,.0f}",
        "summaryStatus": "Protected" if has_rti else "At Risk",
        "adjustedOop": m001_protected_oop,
        "adjustedOopFormatted": f"₹{m001_protected_oop:,.0f}",
        # §2 FIX: Dual display — shows what user WOULD pay vs what they ACTUALLY pay
        "yourPolicyResult": {
            "addonActive": has_rti,
            "addonName": "Return to Invoice",
            "youPay": m001_protected_oop,
            "youPayFormatted": f"₹{m001_protected_oop:,.0f}",
            "addonSaves": gap_without_rti if has_rti else 0,
            "addonSavesFormatted": f"₹{gap_without_rti:,.0f}" if has_rti else "₹0",
            "explanation": f"RTI active — full on-road price (₹{estimated_on_road:,.0f}) recovered" if has_rti else f"Without RTI, you lose ₹{gap_without_rti:,.0f} (gap between IDV and on-road value)"
        },
        "loanWarning": m001_loan_note,
        "recommendation": "RTI add-on active - you're protected!" if has_rti else "Consider RTI add-on for new vehicles (0-3 years). Costs ₹2,000-4,000/year"
    })

    # M002: Major Accident - Parts Replacement
    total_parts = 63000
    labor_painting = 20000
    total_repair = total_parts + labor_painting
    depreciation_amount = int(total_parts * 0.27)  # ~27% average depreciation
    m002_protected_oop = claim_deductible if has_zero_dep else depreciation_amount + claim_deductible
    m002_savings = depreciation_amount if has_zero_dep else 0
    scenarios.append({
        "scenarioId": "M002",
        "name": "Major Accident - Parts Replacement",
        "description": "Front-end collision requiring bumper, headlights, bonnet replacement",
        "icon": "car_crash",
        "severity": "high",
        "repairBreakdown": {
            "parts": [
                {"name": "Front Bumper", "cost": 15000},
                {"name": "Headlight Assembly (Both)", "cost": 25000},
                {"name": "Bonnet", "cost": 18000},
                {"name": "Radiator Grill", "cost": 5000}
            ],
            "totalParts": total_parts,
            "labor": 12000,
            "painting": 8000,
            "totalRepairCost": total_repair
        },
        "withoutAddon": {
            "label": "Without Zero Dep",
            "depreciationDeducted": depreciation_amount,
            "claimPayable": total_repair - depreciation_amount,
            "outOfPocket": depreciation_amount + claim_deductible,
            "outOfPocketFormatted": f"₹{depreciation_amount + claim_deductible:,}",
            "description": f"Depreciation of ₹{depreciation_amount:,} deducted from parts + ₹{claim_deductible:,} deductible"
        },
        "withAddon": {
            "label": "With Zero Dep (YOUR POLICY)" if has_zero_dep else "With Zero Dep",
            "depreciationDeducted": 0,
            "claimPayable": total_repair,
            "outOfPocket": claim_deductible,
            "outOfPocketFormatted": f"₹{claim_deductible:,}" if claim_deductible > 0 else "₹0",
            "description": f"Full claim amount — you pay only ₹{claim_deductible:,} deductible" if claim_deductible > 0 else "Full claim amount - no depreciation deduction"
        },
        # §2 FIX: Summary fields use PROTECTED (post-addon) values
        "yourStatus": "protected" if has_zero_dep else "at_risk",
        "summaryOop": m002_protected_oop,
        "summaryOopFormatted": f"₹{m002_protected_oop:,}",
        "summaryStatus": "Protected" if has_zero_dep else "At Risk",
        "adjustedOop": m002_protected_oop,
        "adjustedOopFormatted": f"₹{m002_protected_oop:,}",
        # §2 FIX: Dual display
        "yourPolicyResult": {
            "addonActive": has_zero_dep,
            "addonName": "Zero Depreciation",
            "youPay": m002_protected_oop,
            "youPayFormatted": f"₹{m002_protected_oop:,}",
            "addonSaves": m002_savings,
            "addonSavesFormatted": f"₹{m002_savings:,}",
            "explanation": f"Zero Dep active — saves you ₹{m002_savings:,} depreciation. You pay only ₹{claim_deductible:,} deductible." if has_zero_dep else f"Without Zero Dep, you pay ₹{depreciation_amount:,} depreciation + ₹{claim_deductible:,} deductible"
        },
        "recommendation": "Zero Dep active - full claim amount!" if has_zero_dep else "Zero Dep saves ₹15-25K on typical claims. Costs ₹3,000-8,000/year"
    })

    # M003: Engine Damage - Waterlogging
    engine_repair_cost = 150000
    m003_protected_oop = claim_deductible if has_engine_protect else engine_repair_cost
    m003_savings = engine_repair_cost if has_engine_protect else 0
    scenarios.append({
        "scenarioId": "M003",
        "name": "Engine Damage - Waterlogging",
        "description": "Vehicle driven through waterlogged road, engine hydro-locked",
        "icon": "water_drop",
        "severity": "medium",
        "withoutAddon": {
            "label": "Without Engine Protect",
            "covered": False,
            "claimPayable": 0,
            "outOfPocket": engine_repair_cost,
            "outOfPocketFormatted": f"₹{engine_repair_cost:,}",
            "description": "Engine damage from water NOT covered under standard policy"
        },
        "withAddon": {
            "label": "With Engine Protect (YOUR POLICY)" if has_engine_protect else "With Engine Protect",
            "covered": True,
            "claimPayable": engine_repair_cost,
            "outOfPocket": claim_deductible,
            "outOfPocketFormatted": f"₹{claim_deductible:,}" if claim_deductible > 0 else "₹0",
            "description": f"Full engine repair covered — you pay only ₹{claim_deductible:,} deductible" if has_engine_protect else "Full engine repair covered"
        },
        # §2 FIX: Summary fields use PROTECTED (post-addon) values
        "yourStatus": "protected" if has_engine_protect else "at_risk",
        "summaryOop": m003_protected_oop,
        "summaryOopFormatted": f"₹{m003_protected_oop:,}",
        "summaryStatus": "Protected" if has_engine_protect else "At Risk",
        "adjustedOop": m003_protected_oop,
        "adjustedOopFormatted": f"₹{m003_protected_oop:,}",
        # §2 FIX: Dual display
        "yourPolicyResult": {
            "addonActive": has_engine_protect,
            "addonName": "Engine Protect",
            "youPay": m003_protected_oop,
            "youPayFormatted": f"₹{m003_protected_oop:,}",
            "addonSaves": m003_savings,
            "addonSavesFormatted": f"₹{m003_savings:,}",
            "explanation": f"Engine Protect active — saves you ₹{m003_savings:,}. You pay only ₹{claim_deductible:,} deductible." if has_engine_protect else f"Without Engine Protect, you pay full ₹{engine_repair_cost:,} out of pocket"
        },
        "recommendation": "Engine Protect active!" if has_engine_protect else "Engine replacement costs ₹50K-3L. Add-on costs ₹500-2,500/year"
    })

    # M004: Third Party Accident — check product type dynamically
    if product_type == "SAOD":
        tp_status = "not_covered"
        tp_coverage_info = {
            "deathBodilyInjury": "NOT COVERED",
            "propertyDamage": "NOT COVERED",
            "description": "This is a Standalone OD policy. Third-party liability is NOT included. You need a separate TP policy to comply with the Motor Vehicles Act."
        }
        tp_recommendation = "CRITICAL: Purchase separate TP liability policy immediately — mandatory by law under Motor Vehicles Act"
        tp_adjusted_oop = -1  # Unlimited liability
        tp_adjusted_oop_formatted = "Unlimited — no cap on personal exposure"
    elif 'TP_' in product_type:
        tp_status = "covered"
        tp_coverage_info = {
            "deathBodilyInjury": "Unlimited",
            "propertyDamage": "₹7,50,000",
            "description": "TP Only policy — full third-party liability covered, but no own damage protection"
        }
        tp_recommendation = "TP covered, but no own damage protection. Consider upgrading to Comprehensive."
        tp_adjusted_oop = 0
        tp_adjusted_oop_formatted = "₹0"
    else:
        tp_status = "covered"
        tp_coverage_info = {
            "deathBodilyInjury": "Unlimited",
            "propertyDamage": "₹7,50,000",
            "description": "Full TP coverage active: Unlimited for death/injury, ₹7.5L for property damage"
        }
        tp_recommendation = "TP liability is covered as part of your comprehensive policy"
        tp_adjusted_oop = 0
        tp_adjusted_oop_formatted = "₹0"

    scenarios.append({
        "scenarioId": "M004",
        "name": "Third Party Accident",
        "description": "Accident causing injury to third party pedestrian",
        "icon": "person_alert",
        "severity": "high",
        "coverage": tp_coverage_info,
        "typicalClaims": [
            {"type": "Minor injury", "range": "₹50,000 - ₹2,00,000"},
            {"type": "Major injury", "range": "₹2,00,000 - ₹10,00,000"},
            {"type": "Death", "range": "₹5,00,000 - ₹50,00,000+"},
            {"type": "Property damage", "range": "Up to ₹7,50,000"}
        ],
        # §2 FIX: Summary fields for M004
        "yourStatus": tp_status,
        "summaryOop": tp_adjusted_oop,
        "summaryOopFormatted": tp_adjusted_oop_formatted,
        "summaryStatus": "CRITICAL — No TP Coverage" if product_type == "SAOD" else "Covered",
        "adjustedOop": tp_adjusted_oop,
        "adjustedOopFormatted": tp_adjusted_oop_formatted,
        "recommendation": tp_recommendation
    })

    # M005: Minor Accident - Should I Claim?
    repair_cost = 8000
    ncb_value = int(od_premium * ncb_percentage / 100) if ncb_percentage > 0 and od_premium > 0 else 0
    claim_threshold = ncb_value
    if_claim_net = repair_cost - ncb_value
    if_no_claim_net = -repair_cost + ncb_value

    scenarios.append({
        "scenarioId": "M005",
        "name": "Minor Accident - Should I Claim?",
        "description": f"Minor dent and scratch. Repair cost ₹{repair_cost:,}",
        "icon": "help_outline",
        "severity": "low",
        "inputs": {
            "repairCost": repair_cost,
            "repairCostFormatted": f"₹{repair_cost:,}",
            "currentNcb": f"{ncb_percentage}%",
            "currentOdPremium": od_premium,
            "ncbProtect": has_ncb_protect
        },
        "ifClaim": {
            "claimAmount": repair_cost,
            "claimAmountFormatted": f"₹{repair_cost:,}",
            "ncbImpact": f"{ncb_percentage}% → 0%",
            "premiumIncrease": ncb_value,
            "premiumIncreaseFormatted": f"₹{ncb_value:,}",
            "netPosition": if_claim_net,
            "netPositionFormatted": f"₹{abs(if_claim_net):,} {'loss' if if_claim_net < 0 else 'gain'}"
        },
        "ifNoClaim": {
            "outOfPocket": repair_cost,
            "outOfPocketFormatted": f"₹{repair_cost:,}",
            "ncbRetained": f"{ncb_percentage}%",
            "ncbValue": ncb_value,
            "ncbValueFormatted": f"₹{ncb_value:,}",
            "netPosition": if_no_claim_net,
            "netPositionFormatted": f"₹{abs(if_no_claim_net):,} {'saved' if if_no_claim_net > 0 else 'cost'}"
        },
        "recommendation": "CLAIM - NCB Protect covers this" if has_ncb_protect else (
            f"DO NOT CLAIM - Pay from pocket. For repairs below ₹{claim_threshold:,} (your NCB value), pay yourself." if repair_cost < ncb_value
            else "CLAIM - Repair cost exceeds NCB value"
        ),
        "claimThreshold": {
            "value": claim_threshold,
            "valueFormatted": f"₹{claim_threshold:,}",
            "message": f"For minor damages below ₹{claim_threshold:,}, paying from pocket saves money"
        },
        "ncbProtectImpact": {
            "active": has_ncb_protect,
            "message": "NCB Protect active - claim without losing NCB!" if has_ncb_protect else f"Add NCB Protect (₹300-1,500/year) to claim freely"
        },
        # §2 FIX: Summary fields for M005
        "summaryOop": 0 if has_ncb_protect else (repair_cost if repair_cost < ncb_value else 0),
        "summaryOopFormatted": "₹0" if has_ncb_protect else (f"₹{repair_cost:,}" if repair_cost < ncb_value else "₹0"),
        "summaryStatus": "NCB Protected" if has_ncb_protect else ("Pay from pocket" if repair_cost < ncb_value else "Claim it"),
        "adjustedOop": 0 if has_ncb_protect else (repair_cost if repair_cost < ncb_value else 0),
        "adjustedOopFormatted": "₹0 (NCB Protect active)" if has_ncb_protect else (
            f"₹{repair_cost:,} (pay from pocket)" if repair_cost < ncb_value else "₹0 (claim it)"
        ),
    })

    # Add plan co-pay info to all scenarios when applicable
    if plan_copay > 0:
        for s in scenarios:
            if s.get("scenarioId") != "M004" and s.get("scenarioId") != "M005":
                if "planCopayNote" not in s:
                    s["planCopayNote"] = f"Note: Your plan includes a ₹{plan_copay:,} co-pay per claim (above standard deductible)"

    # §2 FIX: Compute worst-case OOP from PROTECTED (summaryOop) values
    # Excludes M004 (unlimited = -1) and M005 (decision-based)
    summary_oops = [s.get("summaryOop", s.get("adjustedOop", 0)) for s in scenarios if s.get("summaryOop", s.get("adjustedOop", 0)) >= 0 and s.get("scenarioId") not in ("M004", "M005")]
    worst_case_oop = max(summary_oops) if summary_oops else 0
    for s in scenarios:
        s["_worstCaseOop"] = worst_case_oop
        s["_worstCaseOopFormatted"] = f"₹{worst_case_oop:,}"

    return scenarios


def _analyze_motor_gaps(policy_data: dict, vehicle_age: int, idv: float, market_value: float, ncb_percentage: int, od_premium: float, user_city: str = "") -> list:
    """Deterministic gap analysis per EAZR_03 Section 7"""
    gaps = []
    addons = policy_data.get("addons_map", {})
    product_type = policy_data.get("product_type", "COMP_CAR")
    # When addon extraction is unreliable (AI returned no explicit boolean values),
    # skip addon-based gaps (G002-G006) to avoid false positives for every policy
    addons_reliable = policy_data.get("addons_reliable", True)

    # G001: IDV Below Market Value
    if market_value > 0 and idv < market_value * 0.85:
        below_pct = int((1 - idv / market_value) * 100)
        idv_gap = market_value - idv
        g001_cost = max(1000, int(idv_gap * 0.008))
        gaps.append({
            "gapId": "G001",
            "severity": "high",
            "severityColor": "#EF4444",
            "title": "IDV Below Market Value",
            "description": f"IDV ₹{idv:,.0f} is {below_pct}% below market value ₹{market_value:,.0f}",
            "impact": f"In total loss, you receive ₹{idv_gap:,.0f} less than replacement cost",
            "solution": "Request higher IDV at renewal",
            "estimatedCost": f"~₹{g001_cost:,} additional premium",
            "ipfEligible": True
        })

    # G002-G006: Addon-based gaps — ONLY when addon extraction is reliable
    # When AI extraction fails (all addOnCovers values are None), all addons default to False
    # causing the same static gaps to show for every policy. Skip these when unreliable.
    if addons_reliable:
        # G002: No Zero Dep (New Car)
        if vehicle_age <= 3 and not addons.get('zero_depreciation'):
            g002_cost = max(2000, int(od_premium * 0.08)) if od_premium > 0 else max(2000, int(idv * 0.005))
            dep_pct = 15 + (vehicle_age * 5)  # rough: 15-30% based on age
            gaps.append({
                "gapId": "G002",
                "severity": "high",
                "severityColor": "#EF4444",
                "title": "Zero Depreciation Not Active",
                "description": f"Vehicle is {vehicle_age} year(s) old without Zero Dep cover",
                "impact": f"Parts claims will have ~{dep_pct}% depreciation deduction",
                "solution": "Add Zero Dep at renewal",
                "estimatedCost": f"~₹{g002_cost:,}/year",
                "ipfEligible": True
            })

        # G003: No Engine Protect (Flood-prone cities)
        flood_prone = ['mumbai', 'chennai', 'kolkata', 'bangalore', 'bengaluru', 'hyderabad', 'pune', 'gurgaon', 'gurugram', 'delhi']
        city_lower = user_city.lower() if user_city else ""
        if city_lower in flood_prone and not addons.get('engine_protect'):
            g003_cost = max(500, int(idv * 0.002))
            gaps.append({
                "gapId": "G003",
                "severity": "medium",
                "severityColor": "#F97316",
                "title": "Engine Protect Missing",
                "description": f"{user_city or 'Your city'} is flood-prone. Engine damage not covered.",
                "impact": f"Engine replacement can cost ₹{max(50000, int(idv * 0.15)):,}–₹{max(100000, int(idv * 0.40)):,}",
                "solution": "Add Engine Protect at renewal",
                "estimatedCost": f"~₹{g003_cost:,}/year",
                "ipfEligible": True
            })

        # G004: No RTI (New Vehicle)
        if vehicle_age <= 2 and not addons.get('return_to_invoice'):
            gap_amount = int(market_value * 0.2) if market_value > 0 else 0
            gaps.append({
                "gapId": "G004",
                "severity": "medium",
                "severityColor": "#F97316",
                "title": "Return to Invoice Not Active",
                "description": f"Vehicle is {vehicle_age} year(s) old without RTI protection",
                "impact": f"In total loss, gap of ₹{gap_amount:,}+ between IDV and on-road price",
                "solution": "Add RTI at renewal (available for <3 year old vehicles)",
                "estimatedCost": f"~₹{max(1500, int(idv * 0.003)):,}/year",
                "ipfEligible": True
            })

        # G005: No NCB Protect (High NCB)
        if ncb_percentage >= 35 and not addons.get('ncb_protect'):
            ncb_value = int(od_premium * ncb_percentage / 100) if od_premium > 0 else 0
            g005_cost = max(300, int(ncb_value * 0.15)) if ncb_value > 0 else max(300, int(od_premium * 0.03))
            gaps.append({
                "gapId": "G005",
                "severity": "medium",
                "severityColor": "#F97316",
                "title": "NCB Not Protected",
                "description": f"{ncb_percentage}% NCB (₹{ncb_value:,} value) at risk",
                "impact": f"One claim resets NCB to 0% — you lose ₹{ncb_value:,}/year",
                "solution": "Add NCB Protect at renewal",
                "estimatedCost": f"~₹{g005_cost:,}/year",
                "ipfEligible": True
            })

        # G006: No Roadside Assistance
        if not addons.get('roadside_assistance'):
            g006_cost = max(500, min(1500, int(od_premium * 0.02))) if od_premium > 0 else 800
            gaps.append({
                "gapId": "G006",
                "severity": "low",
                "severityColor": "#EAB308",
                "title": "No Roadside Assistance",
                "description": "No 24x7 RSA coverage",
                "impact": "Towing, battery jump-start, flat tyre not covered",
                "solution": "Add RSA at renewal",
                "estimatedCost": f"~₹{g006_cost:,}/year",
                "ipfEligible": True
            })

    # G007: High Deductible
    voluntary_ded = policy_data.get("voluntary_deductible", 0)
    if voluntary_ded > 5000:
        gaps.append({
            "gapId": "G007",
            "severity": "low",
            "severityColor": "#EAB308",
            "title": "High Voluntary Deductible",
            "description": f"Voluntary deductible of ₹{voluntary_ded:,} is high",
            "impact": f"You pay ₹{voluntary_ded:,} from pocket on every claim",
            "solution": "Consider reducing voluntary deductible at renewal",
            "estimatedCost": f"Premium may increase by ~₹{max(500, int(voluntary_ded * 0.15)):,}",
            "ipfEligible": False
        })

    # G008: SAOD - No TP Cover (BUG #4 FIX: Also check for SAOD missing TP)
    if product_type == "SAOD":
        gaps.append({
            "gapId": "G008",
            "severity": "high",
            "severityColor": "#EF4444",
            "title": "No Third Party Liability Coverage",
            "description": "Standalone OD policy — Third-party liability is NOT included",
            "impact": "Unlimited personal liability for death/injury to others. Legally required under Motor Vehicles Act.",
            "solution": "Purchase separate TP liability policy immediately (mandatory by law)",
            "estimatedCost": f"~₹{max(2000, int(idv * 0.005)):,}/year for TP cover",
            "ipfEligible": True
        })
    # G008b: TP Only - No OD
    elif 'TP_' in product_type:
        gaps.append({
            "gapId": "G008",
            "severity": "info",
            "severityColor": "#6B7280",
            "title": "Third Party Only - No OD Cover",
            "description": "Your policy covers only third-party liability, not own damage",
            "impact": f"Any damage to YOUR vehicle (IDV ₹{idv:,.0f}) is not covered at all",
            "solution": "Upgrade to Comprehensive at renewal",
            "estimatedCost": f"~₹{max(3000, int(idv * 0.03)):,}/year for OD cover",
            "ipfEligible": True
        })

    return sorted(gaps, key=lambda x: {'high': 0, 'medium': 1, 'low': 2, 'info': 3}.get(x['severity'], 4))


def _generate_motor_recommendations(policy_data: dict, gaps: list, vehicle_age: int, ncb_percentage: int, idv: float, market_value: float) -> list:
    """Generate structured recommendations per EAZR_03 Section 8"""
    recommendations = []
    addons = policy_data.get("addons_map", {})
    product_type = policy_data.get("product_type", "COMP_CAR")
    ncb_value = int(policy_data.get("od_premium", 0) * ncb_percentage / 100) if ncb_percentage > 0 else 0

    # Check each gap and generate corresponding recommendation
    gap_ids = {g['gapId'] for g in gaps}

    if 'G001' in gap_ids:
        idv_gap_r = max(0, market_value - idv)
        r_g001_cost = max(1000, int(idv_gap_r * 0.008))
        recommendations.append({
            "id": "increase_idv",
            "category": "enhancement",
            "priority": 1,
            "title": "Increase IDV to Market Value",
            "description": f"Request IDV of ₹{market_value:,.0f} at renewal for adequate coverage",
            "estimatedCost": f"~₹{r_g001_cost:,} additional premium",
            "ipfEligible": True,
            "icon": "trending_up"
        })

    if 'G002' in gap_ids:
        od_p = policy_data.get("od_premium", 0) or 0
        r_g002_cost = max(2000, int(od_p * 0.08)) if od_p > 0 else max(2000, int(idv * 0.005))
        recommendations.append({
            "id": "add_zero_dep",
            "category": "addon",
            "priority": 2,
            "title": "Add Zero Depreciation Cover",
            "description": f"Avoid depreciation deductions on parts claims — saves significant amount for {vehicle_age}-year vehicle",
            "estimatedCost": f"~₹{r_g002_cost:,}/year",
            "ipfEligible": True,
            "icon": "verified"
        })

    if 'G003' in gap_ids:
        r_g003_cost = max(500, int(idv * 0.002))
        recommendations.append({
            "id": "add_engine_protect",
            "category": "addon",
            "priority": 3,
            "title": "Add Engine Protection",
            "description": "Protect against water/flood damage — essential in your city",
            "estimatedCost": f"~₹{r_g003_cost:,}/year",
            "ipfEligible": True,
            "icon": "settings"
        })

    if 'G004' in gap_ids:
        r_g004_cost = max(1500, int(idv * 0.003))
        recommendations.append({
            "id": "add_rti",
            "category": "addon",
            "priority": 4,
            "title": "Add Return to Invoice",
            "description": "Get full on-road price in total loss for new vehicles",
            "estimatedCost": f"~₹{r_g004_cost:,}/year",
            "ipfEligible": True,
            "icon": "receipt_long"
        })

    if 'G005' in gap_ids:
        r_g005_cost = max(300, int(ncb_value * 0.15)) if ncb_value > 0 else max(300, int((policy_data.get("od_premium", 0) or 0) * 0.03))
        recommendations.append({
            "id": "add_ncb_protect",
            "category": "addon",
            "priority": 5,
            "title": "Add NCB Protection",
            "description": f"Protect your {ncb_percentage}% NCB worth ₹{ncb_value:,}/year",
            "estimatedCost": f"~₹{r_g005_cost:,}/year",
            "ipfEligible": True,
            "icon": "shield"
        })

    # §11 FIX: Renewal recommendations must match policy type
    # SAOD → "Buy separate TP policy" (NEVER say "Add OD cover")
    # TP Only → "Add OD cover / Upgrade to Comprehensive" (NEVER say "Add TP cover")
    # Comprehensive → NEVER say "Upgrade to Comprehensive"
    if 'G008' in gap_ids:
        if product_type == "SAOD":
            # Standalone OD — needs separate TP, already HAS OD
            r_g008_cost = max(2000, int(idv * 0.005))
            recommendations.append({
                "id": "buy_tp_policy",
                "category": "critical",
                "priority": 1,
                "title": "Purchase Separate TP Liability Policy",
                "description": "Third-party liability is mandatory by law under Motor Vehicles Act. Purchase a separate TP policy immediately.",
                "estimatedCost": f"~₹{r_g008_cost:,}/year for TP cover",
                "ipfEligible": True,
                "icon": "gavel"
            })
            recommendations.append({
                "id": "consider_comprehensive",
                "category": "upgrade",
                "priority": 3,
                "title": "Consider Switching to Comprehensive at Renewal",
                "description": "A comprehensive policy combines OD + TP in one policy for simpler management",
                "estimatedCost": "Varies by insurer",
                "ipfEligible": True,
                "icon": "swap_horiz"
            })
        elif 'TP_' in product_type:
            # TP Only — needs OD cover, already HAS TP
            r_g008_cost = max(3000, int(idv * 0.03))
            recommendations.append({
                "id": "add_od_cover",
                "category": "upgrade",
                "priority": 1,
                "title": "Add Own Damage Coverage",
                "description": f"Protect your ₹{idv:,.0f} vehicle from damage/theft — currently not covered",
                "estimatedCost": f"~₹{r_g008_cost:,}/year for OD cover",
                "ipfEligible": True,
                "icon": "security"
            })
        # NOTE: Comprehensive policies should NEVER have G008, so no else branch needed

    # §11 SAFEGUARD: Never recommend something the user already has
    _final_recs = []
    for rec in sorted(recommendations, key=lambda x: x['priority']):
        _rec_title_lower = rec.get("title", "").lower()
        if product_type == "SAOD" and "add od" in _rec_title_lower:
            continue  # Already has OD
        if 'COMP' in product_type and "upgrade to comprehensive" in _rec_title_lower:
            continue  # Already is comprehensive
        if 'TP_' in product_type and "add tp" in _rec_title_lower:
            continue  # Already has TP
        _final_recs.append(rec)

    return _final_recs


def _calculate_motor_ipf(premium: float, vehicle_type: str = 'car') -> dict:
    """Calculate EAZR EMI for motor premium per EAZR_03 Section 9.2"""
    if vehicle_type in ['two_wheeler', '2W', 'COMP_2W', 'TP_2W'] and premium < 5000:
        return {"eligible": False, "reason": "Premium below minimum for 2-wheeler"}

    if premium < 8000:
        return {"eligible": False, "reason": "Premium below minimum for financing"}

    tenure_options = [3, 6, 9, 12]
    interest_rate = 0.12
    options = []

    for tenure in tenure_options:
        monthly_rate = interest_rate / 12
        if monthly_rate > 0:
            emi = premium * monthly_rate * (1 + monthly_rate) ** tenure
            emi = emi / ((1 + monthly_rate) ** tenure - 1)
        else:
            emi = premium / tenure
        options.append({
            "tenure": tenure,
            "tenureLabel": f"{tenure} months",
            "emi": round(emi),
            "emiFormatted": f"₹{round(emi):,}/month",
            "total": round(emi * tenure),
            "totalFormatted": f"₹{round(emi * tenure):,}",
            "interest": round(emi * tenure - premium),
            "interestFormatted": f"₹{round(emi * tenure - premium):,}"
        })

    recommended = options[1] if len(options) > 1 else options[0]  # 6 months
    return {
        "eligible": True,
        "premium": premium,
        "premiumFormatted": f"₹{premium:,.0f}",
        "options": options,
        "recommended": recommended,
        "display": f"₹{recommended['emi']:,}/month × {recommended['tenure']} months",
        "interestRate": "12% per annum"
    }


def _get_insurer_logo_url(insurer_name: str) -> str:
    """Build a usable logo URL for the insurer. Uses known domain mappings first, falls back to clearbit."""
    if not insurer_name:
        return ""
    logo_map = {
        'icici lombard': 'icicilombard.com',
        'hdfc ergo': 'hdfcergo.com',
        'bajaj allianz': 'bajajallianz.com',
        'new india': 'newindia.co.in',
        'united india': 'uiic.co.in',
        'national insurance': 'nationalinsurance.nic.co.in',
        'oriental insurance': 'orientalinsurance.org.in',
        'tata aig': 'tataaig.com',
        'reliance general': 'reliancegeneral.co.in',
        'iffco tokio': 'iffcotokio.co.in',
        'sbi general': 'sbigeneral.in',
        'acko': 'acko.com',
        'go digit': 'godigit.com',
        'digit': 'godigit.com',
        'cholamandalam': 'cholainsurance.com',
        'royal sundaram': 'royalsundaram.in',
        'future generali': 'fgiinsurance.in',
        'kotak general': 'kotakgi.com',
        'magma hdi': 'magmahdi.com',
        'star health': 'starhealth.in',
        'care health': 'careinsurance.com',
        'niva bupa': 'nivabupa.com',
    }
    insurer_lower = insurer_name.lower()
    for key, domain in logo_map.items():
        if key in insurer_lower:
            return f"https://logo.clearbit.com/{domain}"
    # Fallback: strip suffixes like Ltd., Co., Inc. and punctuation
    cleaned = re.sub(r'\b(ltd|limited|co|inc|pvt|private|general|insurance|company)\b', '', insurer_lower)
    cleaned = re.sub(r'[^a-z0-9]', '', cleaned).strip()
    return f"https://logo.clearbit.com/{cleaned}.com" if cleaned else ""


# ==================== MOTOR V10 SCORING HELPERS ====================

def _parse_number_from_string_safe(text: str) -> float:
    """Safely extract a number from a string, returning 0 on failure."""
    if not text:
        return 0
    try:
        cleaned = re.sub(r'[^\d.]', '', str(text).replace(',', ''))
        return float(cleaned) if cleaned else 0
    except (ValueError, TypeError):
        return 0


def _get_motor_vehicle_age(category_data: dict, policy_start_date: str = "") -> int:
    """Extract vehicle age from category data. Uses policy start date (not report date) for accuracy."""
    mfg_year = category_data.get("vehicleDetails", {}).get("manufacturingYear", "")
    # BUG #6 FIX: Use policy start year instead of current year
    reference_year = datetime.now().year
    if not policy_start_date:
        # Try to get from category_data
        policy_start_date = category_data.get("policyIdentification", {}).get("policyPeriodStart", "")
    if policy_start_date:
        year_match = re.search(r'(20\d{2})', str(policy_start_date))
        if year_match:
            reference_year = int(year_match.group(1))
    try:
        return max(0, reference_year - int(mfg_year)) if mfg_year else 3
    except (ValueError, TypeError):
        return 3


def _get_motor_ncb_pct(category_data: dict) -> int:
    """Extract NCB percentage from category data."""
    ncb_raw = category_data.get("ncb", {}).get("ncbPercentage", "0")
    try:
        return int(float(str(ncb_raw).replace("%", "").strip()))
    except (ValueError, TypeError):
        return 0


def _build_motor_policy_data_for_scoring(category_data: dict, extracted_data: dict) -> dict:
    """Build the policy_data dict needed by motor scoring functions.

    §10 ARCHITECTURE: This function READS from category_data (AI extraction output)
    but NEVER modifies it. Data extraction is universal and type-agnostic.
    Policy type only affects downstream scoring/gaps/simulations, never extraction.
    This ensures fixing TP logic doesn't break addon extraction for any policy type.
    """
    add_on_covers = category_data.get("addOnCovers", {}) or {}
    coverage_details = category_data.get("coverageDetails", {}) or {}
    ncb_info = category_data.get("ncb", {}) or {}
    premium_breakdown = category_data.get("premiumBreakdown", {}) or {}
    category_str = str(category_data).lower()

    # Build addons_map — keys MUST match actual addOnCovers keys from AI extraction (line 14304)
    addon_key_mapping = {
        "zeroDepreciation": "zero_depreciation",
        "engineProtection": "engine_protect",
        "returnToInvoice": "return_to_invoice",
        "roadsideAssistance": "roadside_assistance",
        "consumables": "consumables_cover",
        "ncbProtect": "ncb_protect",
        "keyCover": "key_replacement",
        "tyreCover": "tyre_protect",
        "personalBaggage": "personal_baggage",
        "emiBreakerCover": "emi_protect",
        "dailyAllowance": "daily_allowance",
        "windshieldCover": "windshield_cover",
        "electricVehicleCover": "electric_vehicle_cover",
        "batteryProtect": "battery_protect",
    }
    addons_map = {}
    for cat_key, map_key in addon_key_mapping.items():
        # Check both addOnCovers and coverageDetails (mirror _build_motor_policy_details_ui)
        val = add_on_covers.get(cat_key) or coverage_details.get(cat_key)
        addons_map[map_key] = bool(val) if val is not None else False

    # Additional cross-check for key addons with alternate key names
    if not addons_map.get("zero_depreciation"):
        addons_map["zero_depreciation"] = bool(coverage_details.get("zeroDep"))
    if not addons_map.get("ncb_protect"):
        addons_map["ncb_protect"] = bool(ncb_info.get("ncbProtection") or coverage_details.get("ncbProtection"))
    if not addons_map.get("consumables_cover"):
        addons_map["consumables_cover"] = bool(coverage_details.get("consumablesCover"))

    # BUG #8 FIX: Expanded keyword fallback detection for all IRDAI-recognized motor add-ons
    # Dynamic patterns — not insurer-specific, covers all India motor insurance
    if not addons_map.get("zero_depreciation") and ("zero dep" in category_str or "nil dep" in category_str or "bumper to bumper" in category_str or "zero depreciation" in category_str):
        addons_map["zero_depreciation"] = True
    if not addons_map.get("engine_protect") and ("engine protect" in category_str or "engine guard" in category_str or "hydrostatic" in category_str or "engine cover" in category_str):
        addons_map["engine_protect"] = True
    if not addons_map.get("roadside_assistance") and ("roadside" in category_str or " rsa " in category_str or "breakdown assist" in category_str or "road side" in category_str):
        addons_map["roadside_assistance"] = True
    if not addons_map.get("ncb_protect") and ("ncb protect" in category_str or "ncb preservation" in category_str or "no claim bonus protect" in category_str or "ncb shield" in category_str):
        addons_map["ncb_protect"] = True
    if not addons_map.get("return_to_invoice") and ("return to invoice" in category_str or "rti cover" in category_str or "invoice cover" in category_str or "invoice value" in category_str):
        addons_map["return_to_invoice"] = True
    if not addons_map.get("consumables_cover") and ("consumable" in category_str):
        addons_map["consumables_cover"] = True
    if not addons_map.get("tyre_protect") and ("tyre" in category_str or "tire protect" in category_str or "tyre guard" in category_str):
        addons_map["tyre_protect"] = True
    if not addons_map.get("key_replacement") and ("key cover" in category_str or "key replace" in category_str or "key protect" in category_str or "loss of key" in category_str or "theft of key" in category_str):
        addons_map["key_replacement"] = True
    # NEW: Personal Effects / Personal Baggage (same coverage, different names across insurers)
    if not addons_map.get("personal_baggage") and ("personal effect" in category_str or "personal belonging" in category_str or "personal baggage" in category_str or "loss of personal" in category_str):
        addons_map["personal_baggage"] = True
    # NEW: Legal Liability to Paid Driver
    if not addons_map.get("legal_liability_driver"):
        if "legal liability" in category_str and ("paid driver" in category_str or "driver" in category_str):
            addons_map["legal_liability_driver"] = True
        elif "ll to paid driver" in category_str or "ll paid driver" in category_str:
            addons_map["legal_liability_driver"] = True
        elif coverage_details.get("llPaidDriver"):
            addons_map["legal_liability_driver"] = True
    # NEW: Legal Liability to Employees
    if not addons_map.get("legal_liability_employees"):
        if "legal liability" in category_str and "employee" in category_str:
            addons_map["legal_liability_employees"] = True
        elif "workmen compensation" in category_str:
            addons_map["legal_liability_employees"] = True
        elif coverage_details.get("llEmployees"):
            addons_map["legal_liability_employees"] = True
    # NEW: PA to Unnamed Passengers
    if not addons_map.get("pa_passengers"):
        if "unnamed passenger" in category_str or "pa to unnamed" in category_str:
            addons_map["pa_passengers"] = True
        elif add_on_covers.get("passengerCover") or coverage_details.get("paUnnamedPassengers"):
            addons_map["pa_passengers"] = True
    # NEW: Windshield Cover (expanded keywords)
    if not addons_map.get("windshield_cover") and ("windshield" in category_str or "windscreen" in category_str or "glass cover" in category_str):
        addons_map["windshield_cover"] = True
    # NEW: Daily Allowance / Loss of Use
    if not addons_map.get("daily_allowance") and ("daily allowance" in category_str or "loss of use" in category_str or "vehicle downtime" in category_str):
        addons_map["daily_allowance"] = True
    # NEW: EMI Protect
    if not addons_map.get("emi_protect") and ("emi protect" in category_str or "emi protection" in category_str or "loan protect" in category_str or "emi breaker" in category_str):
        addons_map["emi_protect"] = True

    # Track addon extraction reliability — when AI returns no explicit boolean values
    # for addons, all default to False causing false-positive gaps for every policy
    _explicit_count = sum(1 for v in add_on_covers.values() if isinstance(v, bool))
    addons_reliable = _explicit_count >= 2 or any(addons_map.get(v) for v in ["zero_depreciation", "engine_protect", "ncb_protect", "return_to_invoice", "roadside_assistance"])

    # PA Owner-Driver: check multiple dynamic sources (liability section, endorsements, premiums, keywords)
    pa_owner_cover_amount = _parse_number_from_string_safe(str(coverage_details.get("paOwnerCover", 0)))
    pa_owner_driver_premium = _parse_number_from_string_safe(str(premium_breakdown.get("paOwnerDriverPremium", 0)))
    pa_owner = bool(
        pa_owner_cover_amount > 0
        or coverage_details.get("personalAccidentCover")
        or pa_owner_driver_premium > 0
        or "personal accident" in category_str
        or "compulsory pa" in category_str
        or "pa owner" in category_str
        or "pa cover" in category_str
    )

    # PA Passengers: check multiple dynamic sources
    pa_passengers_amount = _parse_number_from_string_safe(str(
        coverage_details.get("paUnnamedPassengers", 0) or add_on_covers.get("passengerCoverAmount", 0) or 0
    ))
    pa_passengers_premium = _parse_number_from_string_safe(str(premium_breakdown.get("paPassengersPremium", 0)))
    pa_passengers = bool(
        pa_passengers_amount > 0
        or add_on_covers.get("passengerCover")
        or pa_passengers_premium > 0
        or "unnamed passenger" in category_str
        or "pa to unnamed" in category_str
    )

    # §1 FIX: Named Persons PA (IMT 15) detection — dynamic from policy text
    pa_named_persons = bool(
        coverage_details.get("paNamedPersons")
        or add_on_covers.get("paNamedPersons")
        or "pa to named person" in category_str
        or "named person pa" in category_str
        or "imt 15" in category_str
    )

    od_premium = _parse_number_from_string_safe(str(premium_breakdown.get("basicOdPremium", 0)))

    # Compulsory deductible (default ₹1,000 for cars, ₹500 for 2-wheelers per IRDAI)
    compulsory_deductible = _parse_number_from_string_safe(str(coverage_details.get("compulsoryDeductible", 0)))
    if compulsory_deductible <= 0:
        _pt = detect_motor_product_type(extracted_data, category_data)
        compulsory_deductible = 500 if "2W" in _pt else 1000

    # Plan co-pay / additional excess detection — dynamic from policy text patterns
    plan_copay = 0
    additional_excess = _parse_number_from_string_safe(str(coverage_details.get("additionalExcess", 0)))
    # Search for co-pay patterns dynamically in the full category data text
    copay_patterns = [
        r'(?:co-?pay|excess|you\s+(?:just\s+)?pay)[^₹\d]*[₹rs\.?\s]*(\d[\d,]*)',
        r'[₹rs\.?\s]*(\d[\d,]*)\s*(?:co-?pay|excess|per\s+claim)',
        r'additional\s+excess[^₹\d]*[₹rs\.?\s]*(\d[\d,]*)',
    ]
    for pattern in copay_patterns:
        match = re.search(pattern, category_str, re.IGNORECASE)
        if match:
            detected_copay = _parse_number_from_string_safe(match.group(1))
            if 500 <= detected_copay <= 25000:  # Reasonable co-pay range
                plan_copay = max(plan_copay, int(detected_copay))
                break
    if additional_excess > 0 and additional_excess > plan_copay:
        plan_copay = int(additional_excess)

    # §9 FIX: Extract hypothecation/loan information
    vehicle_details = category_data.get("vehicleDetails", {}) or {}
    hypothecation_raw = vehicle_details.get("hypothecation") or {}
    hypothecation_bank = ""
    if isinstance(hypothecation_raw, dict):
        _financier = hypothecation_raw.get("financierName", "") or hypothecation_raw.get("bankName", "")
        _is_hyp = hypothecation_raw.get("isHypothecated", False)
        if _financier and str(_financier).strip().upper() not in ("NA", "NIL", "NOT APPLICABLE", "NONE", "0", ""):
            hypothecation_bank = str(_financier).strip()
        elif _is_hyp:
            hypothecation_bank = "Financier (name not extracted)"
    elif isinstance(hypothecation_raw, str):
        _hyp_str = hypothecation_raw.strip()
        if _hyp_str.upper() not in ("NA", "NIL", "NOT APPLICABLE", "NONE", "0", ""):
            hypothecation_bank = _hyp_str

    return {
        "addons_map": addons_map,
        "addons_reliable": addons_reliable,
        "product_type": detect_motor_product_type(extracted_data, category_data),
        "pa_owner_covered": pa_owner,
        "pa_owner_sum": pa_owner_cover_amount,
        "pa_passengers_covered": pa_passengers,
        "pa_named_persons_covered": pa_named_persons,
        "voluntary_deductible": _parse_number_from_string_safe(str(coverage_details.get("voluntaryDeductible", 0))),
        "compulsory_deductible": compulsory_deductible,
        "plan_copay": plan_copay,
        "electrical_accessories_premium": _parse_number_from_string_safe(str(premium_breakdown.get("electricalAccessoriesPremium", 0))),
        "non_electrical_accessories_premium": _parse_number_from_string_safe(str(premium_breakdown.get("nonElectricalAccessoriesPremium", 0))),
        "od_premium": od_premium,
        "hypothecation_bank": hypothecation_bank,
    }


def _select_motor_primary_scenario(category_data: dict, formatted_gaps: list, product_type: str) -> str:
    """Auto-select primary scenario per EAZR_03 Section 3.5"""
    pt = product_type.upper()

    if pt.startswith("TP"):
        return "M004"

    _ps_date = category_data.get("policyIdentification", {}).get("policyPeriodStart", "")
    vehicle_age = _get_motor_vehicle_age(category_data, _ps_date)
    add_on_covers = category_data.get("addOnCovers", {})
    has_zero_dep = bool(add_on_covers.get("zeroDepreciation"))
    has_engine_protect = bool(add_on_covers.get("engineProtection"))
    ncb_pct = _get_motor_ncb_pct(category_data)
    has_ncb_protect = bool(add_on_covers.get("ncbProtect"))

    # If new car without Zero Dep — show depreciation impact
    if vehicle_age <= 3 and not has_zero_dep:
        return "M002"

    # If flood-prone city without engine protect
    rto = str(category_data.get("vehicleDetails", {}).get("rtoLocation", "")).lower()
    flood_prone = ["mumbai", "chennai", "kolkata", "bangalore", "bengaluru", "hyderabad", "pune", "gurgaon", "gurugram", "delhi"]
    if any(city in rto for city in flood_prone) and not has_engine_protect:
        return "M003"

    # If IDV gap is the biggest issue
    gap_ids = {g.get("gapId") for g in formatted_gaps if isinstance(g, dict)}
    if "G001" in gap_ids:
        return "M001"

    # If high NCB without protect
    if ncb_pct >= 35 and not has_ncb_protect:
        return "M005"

    return "M001"  # Default: total loss


# ==================== END MOTOR INSURANCE HELPER FUNCTIONS ====================
