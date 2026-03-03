"""
Motor Insurance Light Analysis
Builds motor-specific light analysis with V10 scoring, IDV/NCB snapshots,
and structured coverage gaps.
"""
import logging

from policy_analysis.utils import parse_number_from_string_safe as _parse_number_from_string_safe

logger = logging.getLogger(__name__)


def _build_motor_coverage_gaps_rich(formatted_gaps: list, addon_status: dict) -> list:
    """
    Build properly structured coverageGaps from rich formatted_gaps (from _analyze_motor_gaps).
    Each gap includes: area, title, status, statusType, severity, details, description, impact, solution, estimatedCost, gapId.
    Falls back to addon_status for gaps not covered by formatted_gaps.
    Enriches gaps with impact/solution from addon_gap_details when AI extraction doesn't provide them.
    """
    coverage_gaps = []
    covered_areas = set()

    severity_to_status_type = {"high": "high", "medium": "medium", "low": "low", "info": "info"}

    # Enrichment data — used for BOTH priority 1 (fill missing) and priority 2 (fallback)
    addon_gap_details = {
        "zeroDepreciation": {
            "area": "Zero Depreciation Cover",
            "gapId": "G002",
            "keywords": ["zero dep", "depreciation", "nil dep", "bumper to bumper"],
            "impact": "On a claim of Rs.1,00,000, you could pay Rs.15,000-30,000 extra due to parts depreciation deduction.",
            "solution": "Add Zero Depreciation cover at renewal for full parts cost reimbursement.",
            "estimatedCost": "Rs.3,000-8,000/year",
            "severity": "high",
            "statusType": "high"
        },
        "engineProtection": {
            "area": "Engine Protection Cover",
            "gapId": "G003",
            "keywords": ["engine", "waterlog", "hydrostatic"],
            "impact": "Engine repair can cost Rs.50,000-3,00,000. Entirely out of pocket without this cover.",
            "solution": "Add Engine Protection cover, especially for flood-prone areas or monsoon driving.",
            "estimatedCost": "Rs.500-2,500/year",
            "severity": "medium",
            "statusType": "medium"
        },
        "ncbProtection": {
            "area": "No Claim Bonus (NCB) Protection",
            "gapId": "G005",
            "keywords": ["ncb", "no claim bonus", "no-claim"],
            "impact": "One claim resets NCB to 0%, causing significant premium increase at renewal.",
            "solution": "Add NCB Protection at renewal to preserve your no-claim bonus even after claiming.",
            "estimatedCost": "Rs.300-1,500/year",
            "severity": "medium",
            "statusType": "medium"
        },
        "returnToInvoice": {
            "area": "Return to Invoice (RTI) Cover",
            "gapId": "G004",
            "keywords": ["return to invoice", "rti", "invoice value"],
            "impact": "Gap of Rs.50,000-2,00,000+ between IDV and on-road price in total loss.",
            "solution": "Add Return to Invoice cover at renewal for full invoice value on total loss.",
            "estimatedCost": "Rs.2,000-4,000/year",
            "severity": "medium",
            "statusType": "medium"
        },
        "roadsideAssistance": {
            "area": "Roadside Assistance (RSA)",
            "gapId": "G006",
            "keywords": ["roadside", "rsa", "breakdown", "towing"],
            "impact": "Private towing costs Rs.2,000-5,000 per incident. No on-spot repair support.",
            "solution": "Add Roadside Assistance at renewal for 24x7 breakdown support.",
            "estimatedCost": "Rs.500-1,500/year",
            "severity": "low",
            "statusType": "low"
        },
        "thirdParty": {
            "area": "Third Party Liability",
            "gapId": "G008",
            "keywords": ["third party", "tp liability", "liability coverage"],
            "impact": "No coverage for damage/injury to others. Legal liability is unlimited for death/injury.",
            "solution": "Purchase separate TP liability policy immediately (mandatory by law).",
            "estimatedCost": "Rs.2,000-5,000/year",
            "severity": "high",
            "statusType": "high"
        },
        "idv": {
            "area": "IDV Below Market Value",
            "gapId": "G001",
            "keywords": ["idv", "market value", "insured declared value", "total loss"],
            "impact": "In total loss, you receive less than replacement cost.",
            "solution": "Request higher IDV at renewal to match market value.",
            "estimatedCost": "Rs.1,500-3,000 additional premium",
            "severity": "high",
            "statusType": "high"
        },
        "tyreCover": {
            "area": "Tyre Protection Cover",
            "gapId": "G009",
            "keywords": ["tyre", "tire"],
            "impact": "Tyre damage covered with 50% depreciation deduction. Out-of-pocket Rs.5,000-15,000.",
            "solution": "Add Tyre Cover at renewal for full tyre replacement cost.",
            "estimatedCost": "Rs.500-1,500/year",
            "severity": "low",
            "statusType": "low"
        },
        "keyCover": {
            "area": "Key Replacement Cover",
            "gapId": "G010",
            "keywords": ["key", "key replacement", "key cover"],
            "impact": "Modern car key replacement costs Rs.10,000-20,000 out of pocket.",
            "solution": "Add Key Cover at renewal for key loss/theft protection.",
            "estimatedCost": "Rs.300-800/year",
            "severity": "low",
            "statusType": "low"
        },
    }

    # Collect all reserved gapIds from addon_gap_details to avoid conflicts
    _reserved_gap_ids = {detail["gapId"] for detail in addon_gap_details.values()}
    gap_counter = 1  # For generating gapId when no match
    _used_gap_ids = set()  # Track assigned gapIds to ensure uniqueness

    def _next_unique_gap_id():
        """Generate the next unique sequential gapId, skipping reserved ones."""
        nonlocal gap_counter
        while True:
            candidate = f"G{gap_counter:03d}"
            gap_counter += 1
            if candidate not in _reserved_gap_ids and candidate not in _used_gap_ids:
                return candidate

    def _match_addon_detail(title_lower: str):
        """Match a gap title to addon_gap_details by keywords."""
        for addon_key, detail in addon_gap_details.items():
            for kw in detail["keywords"]:
                if kw in title_lower:
                    return addon_key, detail
        return None, None

    def _format_estimated_cost(cost_val) -> str:
        """Format estimatedCost as string with Rs. prefix."""
        if isinstance(cost_val, str) and cost_val:
            return cost_val
        if isinstance(cost_val, (int, float)) and cost_val > 0:
            return f"Rs.{int(cost_val):,}/year"
        return ""

    # PRIORITY 1: Use formatted_gaps from AI/structured extraction
    for gap in formatted_gaps:
        if not isinstance(gap, dict):
            continue
        gap_title = gap.get("title", gap.get("category", "Coverage Gap"))
        gap_severity = str(gap.get("severity", "medium")).lower()
        gap_description = gap.get("description", gap.get("suggestion", ""))
        gap_impact = gap.get("impact", "")
        gap_solution = gap.get("solution", gap.get("recommendation", ""))
        gap_estimated_cost = gap.get("estimatedCost", "")
        gap_id = gap.get("gapId", "")

        # Track covered areas to avoid duplicates from addon_status fallback
        area_lower = gap_title.lower()
        matched_key, matched_detail = _match_addon_detail(area_lower)
        if matched_key:
            covered_areas.add(matched_key)

        # Enrich missing fields from addon_gap_details
        if matched_detail:
            if not gap_impact:
                gap_impact = matched_detail["impact"]
            if not gap_solution:
                gap_solution = matched_detail["solution"]
            if not gap_estimated_cost:
                gap_estimated_cost = matched_detail["estimatedCost"]
            # Use proper gapId format from the match
            if not gap_id or gap_id.startswith("gap_"):
                gap_id = matched_detail["gapId"]
        else:
            # No match — generate impact/solution from description if empty
            if not gap_impact and gap_description:
                # Use first sentence of description as impact
                first_sentence = gap_description.split('.')[0].strip()
                gap_impact = first_sentence if len(first_sentence) > 10 else gap_description[:120]
            if not gap_solution and gap.get("recommendation"):
                gap_solution = gap["recommendation"]
            elif not gap_solution:
                gap_solution = "Review at next renewal"
            # Generate unique sequential gapId (skips reserved IDs like G001-G010)
            if not gap_id or gap_id.startswith("gap_"):
                gap_id = _next_unique_gap_id()

        # Ensure gapId uniqueness — if already used, generate a new one
        if gap_id in _used_gap_ids:
            gap_id = _next_unique_gap_id()
        _used_gap_ids.add(gap_id)

        # Format estimatedCost as string
        gap_estimated_cost = _format_estimated_cost(gap_estimated_cost)

        coverage_gaps.append({
            "area": gap_title,
            "title": gap_title,
            "status": "Not Covered",
            "statusType": severity_to_status_type.get(gap_severity, "medium"),
            "severity": gap_severity,
            "details": gap_description,
            "description": gap_description,
            "impact": gap_impact,
            "solution": gap_solution,
            "estimatedCost": gap_estimated_cost,
            "gapId": gap_id,
        })

    # PRIORITY 2: Add addon-based gaps NOT already covered by formatted_gaps
    # Skip Priority 2 when formatted_gaps are from deterministic motor analysis (gapId format G001-G008)
    # — deterministic gaps already check vehicle age, city, NCB conditions
    _has_deterministic_gaps = any(
        isinstance(g, dict) and str(g.get("gapId", "")).startswith("G0")
        for g in formatted_gaps
    )
    if not _has_deterministic_gaps:
        for addon_key, gap_detail in addon_gap_details.items():
            if addon_key in covered_areas:
                continue
            addon_info = addon_status.get(addon_key, {})
            if addon_info.get("status") == "Not Covered":
                # Ensure unique gapId — skip if already used by Priority 1
                p2_gap_id = gap_detail["gapId"]
                if p2_gap_id in _used_gap_ids:
                    p2_gap_id = _next_unique_gap_id()
                _used_gap_ids.add(p2_gap_id)
                coverage_gaps.append({
                    "area": gap_detail["area"],
                    "title": gap_detail["area"],
                    "status": "Not Covered",
                    "statusType": gap_detail["statusType"],
                    "severity": gap_detail["severity"],
                    "details": addon_info.get("impact", gap_detail.get("impact", "")),
                    "description": addon_info.get("impact", gap_detail.get("impact", "")),
                    "impact": gap_detail["impact"],
                    "solution": gap_detail["solution"],
                    "estimatedCost": gap_detail["estimatedCost"],
                    "gapId": p2_gap_id,
                })

    # Sort by severity: high > medium > low > info
    severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    coverage_gaps.sort(key=lambda g: severity_order.get(g.get("severity", ""), 4))

    return coverage_gaps


def _build_motor_light_analysis(
    protection_score: int,
    protection_score_label: str,
    insurer_name: str,
    sum_assured: int,
    formatted_gaps: list,
    key_benefits: list,
    recommendations: list,
    category_data: dict,
    policy_details: dict,
    enhanced_insights: dict = None,
    scores_detailed: dict = None,
) -> dict:
    """
    Build motor insurance light analysis — V10 (EAZR_03 Policy Analysis Tab spec).
    Adds protectionReadiness (3-score), idvSnapshot, ncbSnapshot, restructured gaps/recommendations.
    Keeps all V9 backward-compat fields.
    """
    enhanced_insights = enhanced_insights or {}
    from datetime import datetime as dt

    # ---- Extract data from category_data ----
    vehicle_details = category_data.get("vehicleDetails", {})
    coverage_details = category_data.get("coverageDetails", {})
    add_on_covers = category_data.get("addOnCovers", {})
    ncb_data = category_data.get("ncb", {})
    premium_breakdown = category_data.get("premiumBreakdown", {})

    vehicle_make = vehicle_details.get("vehicleMake", "N/A")
    vehicle_model = vehicle_details.get("vehicleModel", "N/A")
    manufacturing_year = vehicle_details.get("manufacturingYear", "N/A")
    reg_number = vehicle_details.get("registrationNumber", "N/A")
    fuel_type = vehicle_details.get("fuelType", "N/A")
    engine_cc = vehicle_details.get("engineCapacity", vehicle_details.get("cubicCapacity", "N/A"))
    policy_end_date = policy_details.get("endDate", "N/A")
    policy_start_date = policy_details.get("startDate", "N/A")

    # BUG #6 FIX: Use policy start date for vehicle age, not report/current date
    import re as _re_date
    _policy_start_year = None
    if policy_start_date and policy_start_date != "N/A":
        _year_match = _re_date.search(r'(20\d{2})', str(policy_start_date))
        if _year_match:
            _policy_start_year = int(_year_match.group(1))
    _reference_year = _policy_start_year if _policy_start_year else dt.now().year

    # §7 FIX: IDV comparison at policy inception — use 1.08 multiplier (inception market value)
    # instead of 1.15 which inflates the gap against current market value
    idv = sum_assured
    market_value = int(idv * 1.08) if idv else 0  # Market value at policy inception
    current_on_road_price = int(idv * 1.25) if idv else 0  # On-road estimate for RTI comparison
    replacement_gap = current_on_road_price - idv if current_on_road_price > idv else 0

    # Loan information
    outstanding_loan = category_data.get("hypothecation", {}).get("outstandingAmount", 0)
    has_loan = outstanding_loan > 0
    loan_warning = "If car is totaled, insurance pays IDV only. You still owe the bank." if has_loan else ""

    # Zero Depreciation status
    has_zero_dep = bool(add_on_covers.get("zeroDepreciation", False))
    has_ncb_protect = bool(add_on_covers.get("ncbProtect", False))

    # ---- Claim Reality Check (unchanged logic) ----
    claim_amount = 100000
    compulsory_deductible = int(coverage_details.get("compulsoryDeductible", 1000) or 1000)
    voluntary_deductible = int(coverage_details.get("voluntaryDeductible", 0) or 0)

    if has_zero_dep:
        depreciation_amount = 0
        insurance_pays_1l = claim_amount - compulsory_deductible - voluntary_deductible
        you_pay_1l = compulsory_deductible + voluntary_deductible
        depreciation_percentage = 0
    else:
        vehicle_age = _reference_year - int(manufacturing_year) if str(manufacturing_year).isdigit() else 0
        if vehicle_age <= 1:
            depreciation_percentage = 5
        elif vehicle_age <= 2:
            depreciation_percentage = 10
        elif vehicle_age <= 3:
            depreciation_percentage = 15
        elif vehicle_age <= 4:
            depreciation_percentage = 20
        else:
            depreciation_percentage = 25
        depreciation_amount = int(claim_amount * depreciation_percentage / 100)
        insurance_pays_1l = claim_amount - compulsory_deductible - voluntary_deductible - depreciation_amount
        you_pay_1l = compulsory_deductible + voluntary_deductible + depreciation_amount

    # ---- NCB Information ----
    # BUG #5 FIX: Use consistent NCB calculation — ncb_savings = basicOdPremium × ncbPercentage / 100
    # basicOdPremium is the OD premium BEFORE NCB discount (correct base for NCB value)
    ncb_percentage_str = ncb_data.get("ncbPercentage", "0%")
    ncb_percentage = int(str(ncb_percentage_str).replace("%", "")) if ncb_percentage_str else 0
    basic_od_premium = _parse_number_from_string_safe(str(premium_breakdown.get("basicOdPremium", 0)))
    # If basicOdPremium not available, try odPremium or netOdPremium
    if basic_od_premium <= 0:
        basic_od_premium = _parse_number_from_string_safe(str(premium_breakdown.get("odPremium", 0)))
    if basic_od_premium <= 0:
        basic_od_premium = _parse_number_from_string_safe(str(premium_breakdown.get("netOdPremium", 0)))
    ncb_savings = int(basic_od_premium * ncb_percentage / 100) if basic_od_premium else 0

    if ncb_percentage >= 50:
        ncb_claim_consequence = f"Drops to 20% (loses Rs.{int(ncb_savings * 0.6):,})"
    elif ncb_percentage >= 20:
        ncb_claim_consequence = f"Drops to 0% (loses Rs.{ncb_savings:,})"
    else:
        ncb_claim_consequence = "Already at 0%"
    ncb_recommendation = "Avoid small claims to preserve NCB." if ncb_percentage > 0 else "Build NCB by not claiming."

    # NCB claim threshold — same formula as ncb_savings for consistency across all pages
    # BUG #5 FIX: Use ncb_savings directly (already calculated above) for a single source of truth
    ncb_claim_threshold = 0
    if has_ncb_protect:
        ncb_claim_threshold = 0
    elif ncb_percentage > 0:
        ncb_claim_threshold = ncb_savings  # Same value used everywhere

    # ---- Verdict (V10 uses scores_detailed if available) ----
    if scores_detailed:
        verdict = scores_detailed.get("verdict", {})
        verdict_label = verdict.get("label", protection_score_label)
        verdict_summary = verdict.get("summary", "")
        verdict_color = verdict.get("color", "#6B7280")
        composite_score = scores_detailed.get("compositeScore", protection_score)
    else:
        composite_score = protection_score
        verdict_label = protection_score_label
        verdict_summary = ""
        verdict_color = "#6B7280"

    if composite_score >= 80:
        verdict_emoji = "shield"
        if not verdict_summary:
            verdict_summary = "Your motor policy provides comprehensive coverage with excellent add-ons."
    elif composite_score >= 60:
        verdict_emoji = "warning"
        if not verdict_summary:
            verdict_summary = "Your policy covers the basics but has some gaps to address."
    else:
        verdict_emoji = "alert"
        if not verdict_summary:
            verdict_summary = "Your policy has significant gaps that should be addressed soon."

    # ---- IDV Snapshot (NEW V10) ----
    idv_ratio = idv / market_value if market_value > 0 else 1.0
    if idv_ratio >= 0.95:
        idv_indicator = {"status": "good", "color": "#22C55E", "verdict": "IDV is aligned with market value"}
    elif idv_ratio >= 0.90:
        idv_indicator = {"status": "info", "color": "#EAB308", "verdict": "Slight gap - consider increasing at renewal"}
    elif idv_ratio >= 0.85:
        idv_gap_amt = market_value - idv
        idv_indicator = {"status": "warning", "color": "#F97316", "verdict": f"Gap of Rs.{idv_gap_amt:,} in total loss. Request higher IDV."}
    else:
        idv_gap_amt = market_value - idv
        idv_indicator = {"status": "warning", "color": "#F97316", "verdict": f"Significant gap. You'll receive Rs.{idv_gap_amt:,} less than vehicle is worth."}

    idv_snapshot = {
        "yourIdv": idv,
        "marketValue": market_value,
        "onRoadPrice": current_on_road_price,
        "idvRatio": round(idv_ratio, 2),
        "gap": max(0, market_value - idv),
        "indicator": idv_indicator,
        "recommendation": f"Request IDV of Rs.{market_value:,} at renewal" if idv_ratio < 0.95 else "IDV is adequate for your vehicle",
    }

    # ---- NCB Snapshot (NEW V10) ----
    # Infer claim-free years from NCB percentage using standard NCB table
    _ncb_claim_free_years = ncb_data.get("claimFreeYears") or ncb_data.get("claim_free_years")
    if not _ncb_claim_free_years:
        _ncb_to_years = {0: 0, 20: 1, 25: 2, 35: 3, 45: 4, 50: 5}
        _ncb_claim_free_years = _ncb_to_years.get(ncb_percentage, max(0, ncb_percentage // 10))
    ncb_snapshot = {
        "percentage": ncb_percentage,
        "savings": ncb_savings,
        "claimFreeYears": _ncb_claim_free_years,
        "claimThreshold": ncb_claim_threshold,
        "ncbProtect": has_ncb_protect,
        "ifClaimImpact": {
            "ncbDropsTo": "0%",
            "premiumIncrease": ncb_savings,
            "yearsToRebuild": 5 if ncb_percentage >= 50 else max(1, ncb_percentage // 10),
        },
        "message": f"For repairs below Rs.{ncb_claim_threshold:,}, pay from pocket to save your {ncb_percentage}% NCB" if ncb_claim_threshold > 0 else ("NCB Protect active - claim any amount without losing NCB" if has_ncb_protect else "No NCB discount currently"),
    }

    # ---- Key Concerns (backward compat) ----
    key_concerns = []
    for gap in formatted_gaps[:3]:
        if isinstance(gap, dict):
            concern_title = gap.get("title", gap.get("category", "Coverage Gap"))
            concern_desc = gap.get("description", gap.get("suggestion", ""))
            key_concerns.append({
                "title": concern_title,
                "brief": concern_desc[:150] + "..." if len(concern_desc) > 150 else concern_desc,
                "severity": gap.get("severity", "medium"),
            })

    # ---- Add-Ons Status (backward compat) ----
    addon_status = {
        "zeroDepreciation": {
            "status": "Active" if has_zero_dep else "Not Covered",
            "emoji": "check" if has_zero_dep else "close",
            "impact": "Full parts cost covered" if has_zero_dep else "You pay depreciation on parts",
        },
        "engineProtection": {
            "status": "Active" if add_on_covers.get("engineProtection") else "Not Covered",
            "emoji": "check" if add_on_covers.get("engineProtection") else "close",
            "impact": "Engine damage covered" if add_on_covers.get("engineProtection") else "Engine repairs not covered",
        },
        "ncbProtection": {
            "status": "Active" if has_ncb_protect else "Not Covered",
            "emoji": "check" if has_ncb_protect else "close",
            "impact": "NCB preserved on claims" if has_ncb_protect else "NCB lost if you claim",
        },
        "returnToInvoice": {
            "status": "Active" if add_on_covers.get("returnToInvoice") else "Not Covered",
            "emoji": "check" if add_on_covers.get("returnToInvoice") else "close",
            "impact": "Full invoice value paid on total loss" if add_on_covers.get("returnToInvoice") else "Only IDV paid on total loss",
        },
        "roadsideAssistance": {
            "status": "Active" if add_on_covers.get("roadsideAssistance") else "Not Covered",
            "emoji": "check" if add_on_covers.get("roadsideAssistance") else "close",
            "impact": "24x7 breakdown support" if add_on_covers.get("roadsideAssistance") else "No breakdown support",
        },
    }

    # ---- Coverage Strengths (V10: title/reason/icon format) ----
    coverage_strengths = []
    strength_map = [
        ("zeroDepreciation", "Zero Depreciation Active", "Full parts cost covered — no depreciation deduction on claims", "verified"),
        ("engineProtection", "Engine Protection Active", "Engine damage from water/oil covered", "settings"),
        ("ncbProtection", "NCB Protection Active", "Your NCB is preserved even after a claim", "shield"),
        ("returnToInvoice", "Return to Invoice Active", "Full on-road price in total loss", "receipt_long"),
        ("roadsideAssistance", "Roadside Assistance Active", "24x7 breakdown support anywhere", "directions_car"),
    ]
    for addon_key, title, reason, icon in strength_map:
        if addon_status[addon_key]["status"] == "Active":
            coverage_strengths.append({"title": title, "reason": reason, "icon": icon})

    # Add deterministic non-addon strengths so coverage_strengths is never empty
    # (prevents fallback to AI-generated policyStrengths which can hallucinate)
    if idv > 0:
        coverage_strengths.append({"title": "Own Damage Coverage", "reason": "Vehicle damage from accidents, theft, natural calamities covered", "icon": "security"})
    if ncb_percentage >= 25:
        coverage_strengths.append({"title": f"{ncb_percentage}% NCB Discount", "reason": f"Saving Rs.{ncb_savings:,}/yr from claim-free driving", "icon": "savings"})
    if idv > 0 and idv_ratio >= 0.95:
        coverage_strengths.append({"title": "IDV Aligned with Market", "reason": "Your IDV adequately reflects vehicle value", "icon": "check_circle"})
    # BUG #4 FIX: TP liability strength should be dynamic based on product type
    _scores_product_type = (scores_detailed or {}).get("productType", "")
    if _scores_product_type == "SAOD":
        coverage_strengths.append({"title": "Third Party Liability", "reason": "NOT included — Standalone OD policy. Separate TP policy required by law.", "icon": "warning"})
    else:
        coverage_strengths.append({"title": "Third Party Liability", "reason": "Unlimited cover for death/injury + Rs.7.5L property damage", "icon": "gavel"})

    # ---- Coverage Gaps (V10: summary + gaps list) ----
    rich_gaps = _build_motor_coverage_gaps_rich(formatted_gaps, addon_status)
    gap_summary = {"high": 0, "medium": 0, "low": 0, "total": len(rich_gaps)}
    for g in rich_gaps:
        sev = str(g.get("severity", "")).lower()
        if sev == "high":
            gap_summary["high"] += 1
        elif sev == "medium":
            gap_summary["medium"] += 1
        elif sev in ("low", "info"):
            gap_summary["low"] += 1

    # ---- What You Should Do (backward compat) ----
    actions = {"immediate": None, "renewal": None, "ongoing": None}
    for rec in recommendations[:3]:
        if isinstance(rec, dict):
            priority = rec.get("priority", "medium")
            # Handle both string ("high") and int (1, 2) priority formats
            if isinstance(priority, int):
                priority_str = "high" if priority <= 2 else ("medium" if priority <= 4 else "low")
            else:
                priority_str = str(priority).lower()
            suggestion = rec.get("suggestion", rec.get("description", rec.get("title", "")))
            brief = suggestion[:100] + "..." if len(suggestion) > 100 else suggestion
            if priority_str == "high" and not actions["immediate"]:
                actions["immediate"] = {"action": rec.get("category", rec.get("title", "Take Action")), "brief": brief}
            elif priority_str == "medium" and not actions["renewal"]:
                actions["renewal"] = {"action": rec.get("category", rec.get("title", "Review Soon")), "brief": brief}
            elif not actions["ongoing"]:
                actions["ongoing"] = {"action": rec.get("category", rec.get("title", "Monitor")), "brief": brief}

    # ---- Policy Strengths (backward compat) ----
    policy_strengths = []
    ai_strengths = enhanced_insights.get("policyStrengths", [])
    if ai_strengths:
        for strength in ai_strengths[:4]:
            if isinstance(strength, str):
                policy_strengths.append(strength[:100] + "..." if len(strength) > 100 else strength)
            elif isinstance(strength, dict):
                policy_strengths.append(strength.get("description", strength.get("name", ""))[:100])
    else:
        for benefit in key_benefits[:3]:
            if isinstance(benefit, str):
                policy_strengths.append(benefit[:80] + "..." if len(benefit) > 80 else benefit)
            elif isinstance(benefit, dict):
                policy_strengths.append(benefit.get("description", benefit.get("name", ""))[:80])

    # ---- Claims helpline ----
    from services.motor_insurance_report_generator import get_motor_claims_helpline
    claims_helpline = get_motor_claims_helpline(insurer_name)

    # ---- Build V10 response ----
    motor_light_analysis = {
        # Policy identification
        "insurerName": insurer_name,
        "planName": "motor",
        "policyType": "motor",

        # Motor-specific metadata (V10: enriched)
        "vehicleInfo": {
            "make": vehicle_make,
            "model": vehicle_model,
            "year": manufacturing_year,
            "regNumber": reg_number,
            "fuelType": fuel_type,
            "cc": engine_cc,
        },

        # NEW V10: protectionReadiness (3-score system)
        "protectionReadiness": scores_detailed if scores_detailed else {
            "compositeScore": protection_score,
            "verdict": {"label": protection_score_label, "summary": verdict_summary, "color": verdict_color},
            "productType": "COMP_CAR",
            "renderMode": None,
            "scores": {"s1": None, "s2": None, "s3": None},
            "analyzedAt": dt.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        },

        # Backward compat
        "protectionScore": composite_score,
        "protectionScoreLabel": verdict_label,
        "coverageVerdict": {
            "emoji": verdict_emoji,
            "label": verdict_label,
            "oneLiner": verdict_summary,
        },
        "protectionVerdict": {
            "emoji": verdict_emoji,
            "label": verdict_label,
            "oneLiner": verdict_summary,
        },

        # NEW V10: IDV & NCB Snapshots
        "idvSnapshot": idv_snapshot,
        "ncbSnapshot": ncb_snapshot,

        # Claim Reality Check (unchanged)
        "claimRealityCheck": {
            "claimAmount": claim_amount,
            "insurancePays": insurance_pays_1l,
            "youPay": you_pay_1l,
            "hasZeroDep": has_zero_dep,
            "depreciationPercentage": depreciation_percentage,
            "oneLiner": "Zero depreciation covers full parts cost." if has_zero_dep else f"{depreciation_percentage}% depreciation will reduce your claim payout.",
            "currency": "INR",
        },

        # Numbers That Matter (unchanged)
        "numbersThatMatter": {
            "yourCover": idv,
            "yourNeed": current_on_road_price,
            "gap": replacement_gap,
            "gapOneLiner": f"You'll pay Rs.{replacement_gap:,} from pocket if car is totaled." if replacement_gap > 0 else "Your IDV covers replacement cost.",
        },

        # Replacement Gap (unchanged)
        "replacementGap": {
            "idv": idv,
            "currentOnRoadPrice": current_on_road_price,
            "gap": replacement_gap,
            "hasLoan": has_loan,
            "outstandingLoan": outstanding_loan,
            "loanWarning": loan_warning,
        },

        # V10 coverage strengths (new format)
        "coverageStrengths": coverage_strengths,

        # V10 coverage gaps (new format with summary)
        "coverageGaps": {
            "summary": gap_summary,
            "gaps": rich_gaps,
        },

        # Backward compat
        "addOnsStatus": addon_status,
        "ncb": {
            "percentage": ncb_percentage,
            "savings": ncb_savings,
            "claimConsequence": ncb_claim_consequence,
            "recommendation": ncb_recommendation,
        },
        "keyConcerns": key_concerns,
        "whatYouShouldDo": actions,
        "policyStrengths": policy_strengths,

        # Quick Reference
        "quickReference": {
            "claimsHelpline": claims_helpline,
            "policyExpiry": policy_end_date,
            "ncbPercentage": ncb_percentage,
        },

        # Report URL
        "reportUrl": None,
        "reportError": None,

        # Report metadata — V10
        "reportDate": dt.utcnow().strftime("%Y-%m-%d"),
        "analysisVersion": "10.0",
    }

    return motor_light_analysis


