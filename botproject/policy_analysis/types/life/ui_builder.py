"""Life Insurance UI Builder (EAZR_02 Spec)
Build Flutter UI-specific structure for life insurance policies.
"""
import logging
import re
from datetime import datetime

from policy_analysis.utils import safe_num, get_score_label

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: premium due alert
# ---------------------------------------------------------------------------

def _check_premium_due_alert(due_date_str: str) -> bool:
    """Check if premium due date is within next 30 days"""
    if not due_date_str or due_date_str in ("N/A", "Not Available", ""):
        return False
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            due_dt = datetime.strptime(str(due_date_str).strip(), fmt)
            days_until = (due_dt.date() - datetime.now().date()).days
            return 0 <= days_until <= 30
        except Exception:
            continue
    return False


# ---------------------------------------------------------------------------
# Local helpers (kept private to this module)
# ---------------------------------------------------------------------------

def _safe_str(val, default="Not Available"):
    if val is None or val == "" or val == "N/A":
        return default
    return str(val)


def _format_currency(amount):
    """Format amount as Indian-style currency string."""
    if amount is None or amount == 0:
        return "₹0"
    try:
        amount = float(amount)
        if amount >= 10000000:
            return f"₹{amount/10000000:.2f} Cr"
        elif amount >= 100000:
            return f"₹{amount/100000:.2f} L"
        else:
            return f"₹{amount:,.0f}"
    except Exception:
        return f"₹{amount}"


def _parse_date(date_str):
    """Try to parse date from various formats."""
    if not date_str or date_str in ("N/A", "Not Available", ""):
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except Exception:
            continue
    return None


def _extract_years(term_str):
    """Extract numeric year value from a term string like '20 years'."""
    if not term_str:
        return 0
    m = re.search(r'(\d+)', str(term_str))
    return int(m.group(1)) if m else 0


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_life_policy_details_ui(
    extracted_data: dict,
    category_data: dict,
    policy_type: str = "",
    policy_status: str = "active"
) -> dict:
    """
    Build Flutter UI-specific structure for Life Insurance Policy Details Tab.
    Follows EAZR_02_Life_Insurance.md specification.
    Sections: Emergency Info, Policy Overview, Coverage Details, Premium Details,
    Policy Values (SVF Critical), Nominee Details, Tax Benefits.
    """

    category_data = category_data or {}

    # Extract nested sections from category_data
    policy_identification = category_data.get("policyIdentification", {})
    policyholder_info = category_data.get("policyholderLifeAssured", {})
    coverage_details = category_data.get("coverageDetails", {})
    premium_details = category_data.get("premiumDetails", {})
    riders_list = category_data.get("riders", [])
    bonus_value = category_data.get("bonusValue", {})
    ulip_details = category_data.get("ulipDetails", {})
    nomination = category_data.get("nomination", {})
    key_terms = category_data.get("keyTerms", {})
    exclusions = category_data.get("exclusions", {})

    # Ensure riders_list is a list
    if not isinstance(riders_list, list):
        riders_list = []

    # Basic extracted fields
    insurer_name = policy_identification.get("insurerName") or extracted_data.get("insuranceProvider", "")
    policy_number = policy_identification.get("policyNumber") or extracted_data.get("policyNumber", "")
    product_name = policy_identification.get("productName") or extracted_data.get("policyName", "")
    product_type = policy_identification.get("policyType") or policy_type or ""
    current_status = policy_identification.get("policyStatus") or policy_status or "Active"

    # Helpline lookup
    helplines = {
        'lic': '022-68276827',
        'life insurance corporation': '022-68276827',
        'hdfc life': '1800-266-9777',
        'hdfc': '1800-266-9777',
        'icici prudential': '1860-266-7766',
        'icici pru': '1860-266-7766',
        'sbi life': '1800-267-9090',
        'max life': '1860-120-5577',
        'bajaj allianz life': '1800-209-5858',
        'bajaj': '1800-209-5858',
        'kotak life': '1800-209-8800',
        'kotak': '1800-209-8800',
        'tata aia': '1800-266-9966',
        'tata': '1800-266-9966',
        'birla sun life': '1800-270-7000',
        'aditya birla': '1800-270-7000',
        'pnb metlife': '1800-425-6969',
        'metlife': '1800-425-6969',
        'canara hsbc': '1800-103-0003',
        'star union': '1800-266-8833',
        'india first': '1800-209-7225',
        'shriram': '1800-103-0123',
        'edelweiss': '1800-419-5999',
        'future generali': '1800-220-233',
    }
    helpline_number = "See policy document"
    if insurer_name:
        insurer_lower = insurer_name.lower()
        for key, number in helplines.items():
            if key in insurer_lower:
                helpline_number = number
                break

    # ==================== KEY VALUES ====================
    sum_assured = safe_num(coverage_details.get("sumAssured") or extracted_data.get("coverageAmount"))
    premium_amount = safe_num(premium_details.get("premiumAmount") or extracted_data.get("premium"))
    premium_frequency = _safe_str(premium_details.get("premiumFrequency") or extracted_data.get("premiumFrequency"), "Annual")
    premium_due_date = _safe_str(premium_details.get("premiumDueDate"), "")
    grace_period = _safe_str(premium_details.get("gracePeriod"), "30 days")
    policy_term_str = _safe_str(coverage_details.get("policyTerm"), "")
    ppt_str = _safe_str(coverage_details.get("premiumPayingTerm"), "")
    start_date = _safe_str(policy_identification.get("policyIssueDate") or extracted_data.get("startDate"), "")
    maturity_date = _safe_str(coverage_details.get("maturityDate") or extracted_data.get("endDate"), "")
    death_benefit_desc = _safe_str(coverage_details.get("deathBenefit"), "Sum Assured + Accrued Bonuses")
    surrender_value = safe_num(bonus_value.get("surrenderValue"))
    paid_up_value = safe_num(bonus_value.get("paidUpValue"))
    loan_value = safe_num(bonus_value.get("loanValue"))
    accrued_bonus = safe_num(bonus_value.get("accruedBonus"))
    bonus_type = _safe_str(bonus_value.get("bonusType"), "")
    declared_bonus_rate = _safe_str(bonus_value.get("declaredBonusRate"), "")
    fund_value = safe_num(ulip_details.get("fundValue"))

    # Parse numeric from policy term
    policy_term_years = _extract_years(policy_term_str)
    ppt_years = _extract_years(ppt_str)

    # Calculate progress
    start_dt = _parse_date(start_date)
    maturity_dt = _parse_date(maturity_date)
    now = datetime.now()

    policy_term_progress = 0
    years_completed = 0
    years_remaining = 0
    if start_dt and policy_term_years > 0:
        years_completed = min(policy_term_years, max(0, (now - start_dt).days / 365.25))
        years_remaining = max(0, policy_term_years - years_completed)
        policy_term_progress = min(100, int((years_completed / policy_term_years) * 100))
    elif start_dt and maturity_dt:
        total_days = (maturity_dt - start_dt).days
        elapsed_days = (now - start_dt).days
        if total_days > 0:
            policy_term_progress = min(100, max(0, int((elapsed_days / total_days) * 100)))
            years_completed = elapsed_days / 365.25
            years_remaining = max(0, total_days - elapsed_days) / 365.25

    ppt_progress = 0
    premiums_paid_count = 0
    premiums_remaining_count = 0
    if ppt_years > 0 and years_completed > 0:
        premiums_paid_est = min(ppt_years, int(years_completed))
        premiums_remaining_count = max(0, ppt_years - premiums_paid_est)
        premiums_paid_count = premiums_paid_est
        ppt_progress = min(100, int((premiums_paid_est / ppt_years) * 100))

    total_premiums_paid = premium_amount * premiums_paid_count if premium_amount > 0 else 0

    # ==================== DETECT LIFE PRODUCT SUB-TYPE ====================
    product_name_lower = (product_name + " " + product_type).lower()

    def _detect_life_subtype():
        if any(t in product_name_lower for t in ['term', 'jeevan amar', 'iprotect', 'click2protect', 'saral jeevan bima']):
            return "TERM"
        if any(t in product_name_lower for t in ['ulip', 'unit linked', 'fortune', 'wealth']):
            return "ULIP"
        if any(t in product_name_lower for t in ['money back', 'money-back', 'moneyback']):
            return "MONEY_BACK"
        if any(t in product_name_lower for t in ['pension', 'annuity', 'retirement']):
            return "PENSION"
        if any(t in product_name_lower for t in ['child', 'vidya', 'shiksha', 'education']):
            return "CHILD"
        if 'whole life' in product_name_lower:
            return "WHOLE"
        return "ENDOW"

    life_subtype = _detect_life_subtype()

    # Subtype display config
    subtype_config = {
        "TERM": {"label": "Term Life", "color": "#3B82F6", "svfEligible": False},
        "ENDOW": {"label": "Endowment", "color": "#22C55E", "svfEligible": True},
        "ULIP": {"label": "ULIP", "color": "#8B5CF6", "svfEligible": True},
        "WHOLE": {"label": "Whole Life", "color": "#F59E0B", "svfEligible": True},
        "MONEY_BACK": {"label": "Money-back", "color": "#EC4899", "svfEligible": True},
        "PENSION": {"label": "Pension", "color": "#6B7280", "svfEligible": True},
        "CHILD": {"label": "Child Plan", "color": "#14B8A6", "svfEligible": True},
    }
    subtype_info = subtype_config.get(life_subtype, subtype_config["ENDOW"])

    # ==================== 1. EMERGENCY INFO ====================
    emergency_info = {
        "policyNumber": policy_number,
        "premiumDueDate": premium_due_date,
        "premiumDueAlert": _check_premium_due_alert(premium_due_date) if premium_due_date else False,
        "helpline": helpline_number,
        "helplineAction": "call",
        "policyStatus": current_status,
        "statusColor": "#22C55E" if current_status.lower() == "active" else "#EF4444" if current_status.lower() == "lapsed" else "#F59E0B"
    }

    # ==================== 2. POLICY OVERVIEW ====================
    policy_overview = {
        "insurer": {
            "name": insurer_name,
            "logo": f"https://logo.clearbit.com/{insurer_name.lower().replace(' ', '').replace(',', '').replace('of', '').replace('the', '')}.com" if insurer_name else "",
        },
        "product": {
            "name": product_name,
            "type": subtype_info["label"],
            "typeColor": subtype_info["color"],
            "svfEligible": subtype_info["svfEligible"],
        },
        "sumAssured": {
            "amount": sum_assured,
            "formatted": _format_currency(sum_assured),
            "description": "Current Death Benefit Coverage"
        },
        "policyTerm": {
            "totalYears": policy_term_years,
            "yearsCompleted": round(years_completed, 1),
            "yearsRemaining": round(years_remaining, 1),
            "progressPercent": policy_term_progress,
            "description": f"{round(years_completed, 1)} of {policy_term_years} years completed" if policy_term_years > 0 else policy_term_str
        },
        "premiumPaymentTerm": {
            "totalYears": ppt_years,
            "yearsPaid": premiums_paid_count,
            "yearsRemaining": premiums_remaining_count,
            "progressPercent": ppt_progress,
            "description": f"{premiums_paid_count} of {ppt_years} premiums paid" if ppt_years > 0 else ppt_str
        },
        "keyDates": {
            "startDate": start_date,
            "maturityDate": maturity_date,
            "nextPremiumDue": premium_due_date
        },
        "policyholder": {
            "name": policyholder_info.get("policyholderName") or extracted_data.get("policyHolderName", ""),
            "age": _safe_str(policyholder_info.get("policyholderAge"), ""),
            "gender": _safe_str(policyholder_info.get("policyholderGender"), ""),
        },
        "lifeAssured": {
            "name": _safe_str(policyholder_info.get("lifeAssuredName"), ""),
            "age": _safe_str(policyholder_info.get("lifeAssuredAge"), ""),
            "isSameAsPolicyholder": (policyholder_info.get("lifeAssuredName") or "") == "" or (policyholder_info.get("lifeAssuredName") or "").lower() == (policyholder_info.get("policyholderName") or "").lower()
        }
    }

    # ==================== 3. COVERAGE DETAILS ====================
    # 3.1 Death Benefit
    death_benefit_amount = sum_assured + accrued_bonus if accrued_bonus > 0 else sum_assured
    death_benefit = {
        "type": _safe_str(coverage_details.get("coverType"), "Level Sum Assured"),
        "currentAmount": death_benefit_amount,
        "currentAmountFormatted": _format_currency(death_benefit_amount),
        "formula": death_benefit_desc,
        "breakdown": []
    }
    if sum_assured > 0:
        death_benefit["breakdown"].append({
            "label": "Sum Assured",
            "amount": sum_assured,
            "formatted": _format_currency(sum_assured)
        })
    if accrued_bonus > 0:
        death_benefit["breakdown"].append({
            "label": "Accrued Bonuses",
            "amount": accrued_bonus,
            "formatted": _format_currency(accrued_bonus)
        })

    # 3.2 Maturity Benefit (not applicable for Term)
    maturity_benefit = None
    if life_subtype != "TERM":
        guaranteed_maturity = sum_assured + accrued_bonus if accrued_bonus > 0 else sum_assured
        # Project @4% and @8% if available
        projected_4pct = 0
        projected_8pct = 0
        if total_premiums_paid > 0 and years_remaining > 0:
            projected_4pct = total_premiums_paid * ((1 + 0.04) ** years_remaining)
            projected_8pct = total_premiums_paid * ((1 + 0.08) ** years_remaining)

        maturity_benefit = {
            "applicable": True,
            "guaranteedAmount": guaranteed_maturity,
            "guaranteedFormatted": _format_currency(guaranteed_maturity),
            "projected4pct": projected_4pct,
            "projected4pctFormatted": _format_currency(projected_4pct) if projected_4pct > 0 else "Not Available",
            "projected8pct": projected_8pct,
            "projected8pctFormatted": _format_currency(projected_8pct) if projected_8pct > 0 else "Not Available",
            "maturityDate": maturity_date,
        }

        # Survival benefits for money-back
        if life_subtype == "MONEY_BACK":
            maturity_benefit["survivalBenefits"] = {
                "applicable": True,
                "description": "Periodic survival payouts as per policy terms"
            }
    else:
        maturity_benefit = {
            "applicable": False,
            "description": "Term insurance has no maturity benefit"
        }

    # 3.3 Riders
    riders_section = []
    for i, rider in enumerate(riders_list):
        rider_entry = {
            "id": f"rider_{i+1}",
            "name": rider.get("riderName", "Unknown Rider") if isinstance(rider, dict) else str(rider),
            "sumAssured": safe_num(rider.get("riderSumAssured", 0)) if isinstance(rider, dict) else 0,
            "sumAssuredFormatted": _format_currency(safe_num(rider.get("riderSumAssured", 0))) if isinstance(rider, dict) else "N/A",
            "premium": safe_num(rider.get("riderPremium", 0)) if isinstance(rider, dict) else 0,
            "premiumFormatted": _format_currency(safe_num(rider.get("riderPremium", 0))) if isinstance(rider, dict) else "N/A",
            "term": _safe_str(rider.get("riderTerm", ""), "") if isinstance(rider, dict) else "",
            "status": "Active"
        }
        riders_section.append(rider_entry)

    coverage_section = {
        "deathBenefit": death_benefit,
        "maturityBenefit": maturity_benefit,
        "riders": riders_section,
        "ridersCount": len(riders_section),
        "hasCI": any("critical" in (r.get("name", "") or "").lower() or "critical" in (r.get("riderName", "") if isinstance(r, dict) else "").lower() for r in riders_list),
        "hasADB": any("accidental" in (r.get("name", "") or "").lower() or "accidental" in (r.get("riderName", "") if isinstance(r, dict) else "").lower() for r in riders_list),
        "hasWoP": any("waiver" in (r.get("name", "") or "").lower() or "waiver" in (r.get("riderName", "") if isinstance(r, dict) else "").lower() for r in riders_list),
    }

    # ==================== 4. PREMIUM DETAILS ====================
    modal_breakdown = premium_details.get("modalPremiumBreakdown") or {}
    base_premium = safe_num(modal_breakdown.get("base")) if isinstance(modal_breakdown, dict) else 0
    gst_amount = safe_num(modal_breakdown.get("gst")) if isinstance(modal_breakdown, dict) else 0
    rider_premium = safe_num(modal_breakdown.get("rider")) if isinstance(modal_breakdown, dict) else 0

    premium_section = {
        "annualPremium": premium_amount,
        "annualPremiumFormatted": _format_currency(premium_amount),
        "frequency": premium_frequency,
        "modalBreakdown": {
            "basePremium": base_premium,
            "basePremiumFormatted": _format_currency(base_premium) if base_premium > 0 else "N/A",
            "gst": gst_amount,
            "gstFormatted": _format_currency(gst_amount) if gst_amount > 0 else "N/A",
            "riderPremium": rider_premium,
            "riderPremiumFormatted": _format_currency(rider_premium) if rider_premium > 0 else "N/A",
        },
        "premiumsPaid": {
            "count": premiums_paid_count,
            "totalAmount": total_premiums_paid,
            "totalFormatted": _format_currency(total_premiums_paid)
        },
        "premiumsRemaining": {
            "count": premiums_remaining_count,
            "totalAmount": premium_amount * premiums_remaining_count if premium_amount > 0 else 0,
            "totalFormatted": _format_currency(premium_amount * premiums_remaining_count) if premium_amount > 0 else "N/A"
        },
        "nextDueDate": premium_due_date,
        "gracePeriod": grace_period,
        "totalProjectedPremium": {
            "amount": premium_amount * (premiums_paid_count + premiums_remaining_count) if premium_amount > 0 else 0,
            "formatted": _format_currency(premium_amount * (premiums_paid_count + premiums_remaining_count)) if premium_amount > 0 else "N/A"
        },
        "ipfEligible": True,
        "ipfCta": {
            "label": "Pay Premium in EMIs",
            "action": "ipf_apply",
            "description": "Convert your annual premium to easy EMIs with EAZR IPF"
        }
    }

    # ==================== 5. POLICY VALUES (SVF Critical) ====================
    is_savings_plan = life_subtype != "TERM"

    # 5.1 Surrender Value
    surrender_value_card = None
    if is_savings_plan:
        sv_ratio = (surrender_value / total_premiums_paid * 100) if total_premiums_paid > 0 and surrender_value > 0 else 0
        surrender_value_card = {
            "applicable": True,
            "guaranteedSV": surrender_value,
            "guaranteedSVFormatted": _format_currency(surrender_value),
            "specialSV": 0,
            "specialSVFormatted": "Not Available",
            "totalSurrenderValue": surrender_value,
            "totalSVFormatted": _format_currency(surrender_value),
            "svRatio": round(sv_ratio, 1),
            "svRatioDescription": f"{round(sv_ratio, 1)}% of premiums paid" if sv_ratio > 0 else "Contact insurer for current value",
            "svfCta": {
                "label": "Check SVF Eligibility",
                "action": "svf_check",
                "description": f"Access up to {_format_currency(surrender_value * 0.9)} without surrendering your policy",
                "highlight": True
            } if surrender_value >= 50000 else None
        }
    else:
        surrender_value_card = {
            "applicable": False,
            "description": "Term insurance has no surrender value"
        }

    # 5.2 Fund Value (ULIP only)
    fund_value_card = None
    if life_subtype == "ULIP":
        fund_options = ulip_details.get("fundOptions") or []
        current_nav = ulip_details.get("currentNav") or {}
        units_held = safe_num(ulip_details.get("unitsHeld"))
        switch_options = _safe_str(ulip_details.get("switchOptions"), "")
        partial_withdrawal = _safe_str(ulip_details.get("partialWithdrawal"), "")

        fund_breakdown = []
        if isinstance(current_nav, dict):
            for fund_name, nav in current_nav.items():
                fund_breakdown.append({
                    "fundName": fund_name,
                    "nav": safe_num(nav),
                    "navFormatted": f"₹{safe_num(nav):.2f}"
                })

        fund_value_card = {
            "applicable": True,
            "totalFundValue": fund_value,
            "totalFundValueFormatted": _format_currency(fund_value),
            "navDate": "As per last update",
            "unitsHeld": units_held,
            "fundBreakdown": fund_breakdown,
            "fundOptions": fund_options if isinstance(fund_options, list) else [],
            "switchOptions": switch_options,
            "partialWithdrawal": partial_withdrawal
        }
    else:
        fund_value_card = {
            "applicable": False,
            "description": "Fund value applicable only for ULIP policies"
        }

    # 5.3 Bonus Accrued (Traditional plans)
    bonus_card = None
    if is_savings_plan and life_subtype != "ULIP":
        bonus_card = {
            "applicable": True,
            "bonusType": bonus_type,
            "declaredRate": declared_bonus_rate,
            "totalAccruedBonus": accrued_bonus,
            "totalAccruedFormatted": _format_currency(accrued_bonus),
            "terminalBonus": {
                "applicable": True,
                "description": "Terminal bonus may be applicable at maturity/claim"
            },
            "loyaltyAdditions": {
                "applicable": True,
                "description": "Loyalty additions may apply after completing specified years"
            }
        }
    else:
        bonus_card = {
            "applicable": False,
            "description": "Bonus not applicable for this policy type"
        }

    # 5.4 Loan Eligibility
    loan_interest_rate = _safe_str(key_terms.get("policyLoanInterestRate"), "")
    loan_card = None
    if is_savings_plan:
        max_loan = surrender_value * 0.9 if surrender_value > 0 else loan_value
        loan_card = {
            "applicable": True,
            "eligibleForLoan": loan_value > 0 or surrender_value > 50000,
            "maxLoanAmount": max_loan if max_loan > 0 else loan_value,
            "maxLoanFormatted": _format_currency(max_loan) if max_loan > 0 else _format_currency(loan_value),
            "currentOutstanding": 0,
            "currentOutstandingFormatted": "₹0",
            "interestRate": loan_interest_rate,
            "compareSvfCta": {
                "label": "Compare with EAZR SVF",
                "action": "svf_compare",
                "description": "EAZR SVF may offer better terms than policy loan"
            } if (max_loan > 0 or loan_value > 0) else None
        }
    else:
        loan_card = {
            "applicable": False,
            "description": "Loan not available for term insurance"
        }

    policy_values = {
        "isSavingsPlan": is_savings_plan,
        "surrenderValue": surrender_value_card,
        "fundValue": fund_value_card,
        "bonusAccrued": bonus_card,
        "loanEligibility": loan_card
    }

    # ==================== 6. NOMINEE DETAILS ====================
    nominees_list = nomination.get("nominees") or []
    if not isinstance(nominees_list, list):
        nominees_list = []

    nominee_entries = []
    for i, nominee in enumerate(nominees_list):
        if isinstance(nominee, dict):
            nominee_name = nominee.get("nomineeName") or nominee.get("name", "")
            nominee_rel = nominee.get("nomineeRelationship") or nominee.get("relationship", "")
            nominee_share = safe_num(nominee.get("nomineeShare") or nominee.get("share") or nominee.get("allocation_percentage"), 100)
            nominee_age = safe_num(nominee.get("nomineeAge") or nominee.get("age"), 0)
            is_minor = nominee_age > 0 and nominee_age < 18

            entry = {
                "id": f"nominee_{i+1}",
                "name": nominee_name,
                "relationship": nominee_rel,
                "allocationPercent": nominee_share,
                "age": nominee_age if nominee_age > 0 else None,
                "isMinor": is_minor,
            }
            if is_minor:
                entry["appointee"] = {
                    "name": _safe_str(nomination.get("appointeeName"), ""),
                    "relationship": _safe_str(nomination.get("appointeeRelationship"), "")
                }
            nominee_entries.append(entry)
        elif isinstance(nominee, str) and nominee:
            nominee_entries.append({
                "id": f"nominee_{i+1}",
                "name": nominee,
                "relationship": "",
                "allocationPercent": 100,
                "age": None,
                "isMinor": False,
            })

    nominee_section = {
        "nominees": nominee_entries,
        "nomineeCount": len(nominee_entries),
        "allocationValid": True,
        "updatePrompt": {
            "label": "Review Nominee Details",
            "action": "update_nominee",
            "description": "Ensure nominee details are up to date for hassle-free claim settlement"
        }
    }

    # ==================== 7. TAX BENEFITS ====================
    # Section 80C eligibility
    annual_premium_for_tax = premium_amount
    sa_10_pct = sum_assured * 0.10 if sum_assured > 0 else 0
    # After Apr 2012: premium <= 10% of SA for 80C
    eligible_80c = min(annual_premium_for_tax, 150000)
    if sa_10_pct > 0 and annual_premium_for_tax > sa_10_pct:
        eligible_80c = min(sa_10_pct, 150000)

    # Section 10(10D) - maturity exempt if annual premium <= 5L (post Apr 2023)
    maturity_taxable = annual_premium_for_tax > 500000

    # Estimate tax saved (30% bracket)
    tax_saved_estimate = eligible_80c * 0.312  # 30% + 4% cess

    tax_benefits = {
        "section80C": {
            "eligible": True,
            "eligibleAmount": eligible_80c,
            "eligibleFormatted": _format_currency(eligible_80c),
            "maxLimit": 150000,
            "maxLimitFormatted": "₹1,50,000",
            "condition": "Premium ≤ 10% of Sum Assured (policies after 01-Apr-2012)",
            "description": f"Claim up to {_format_currency(eligible_80c)} under Section 80C"
        },
        "section10_10D": {
            "eligible": not maturity_taxable,
            "maturityTaxable": maturity_taxable,
            "condition": "Annual premium ≤ ₹5L (policies after 01-Apr-2023)",
            "description": "Maturity proceeds are tax-free" if not maturity_taxable else "Maturity proceeds may be taxable (premium > ₹5L/year)"
        },
        "taxSaved": {
            "estimatedAnnual": tax_saved_estimate,
            "estimatedFormatted": _format_currency(tax_saved_estimate),
            "description": f"Estimated annual tax saving at 30% slab + cess",
            "note": "Actual savings depend on your tax slab"
        }
    }

    # ==================== 8. KEY TERMS & EXCLUSIONS ====================
    key_terms_section = {
        "revivalPeriod": _safe_str(key_terms.get("revivalPeriod"), "5 years from date of first unpaid premium"),
        "freelookPeriod": _safe_str(key_terms.get("freelookPeriod"), "15 days (30 days for distance marketing)"),
        "policyLoanInterestRate": loan_interest_rate,
        "autoPayMode": key_terms.get("autoPayMode")
    }

    exclusions_section = {
        "suicideClause": _safe_str(exclusions.get("suicideClause"), "Claim limited to premiums paid (excl. extra/rider) if death by suicide within 12 months"),
        "otherExclusions": exclusions.get("otherExclusions") or [],
        "collapsed": True
    }

    # ==================== BUILD FINAL STRUCTURE ====================
    return {
        "emergencyInfo": emergency_info,
        "policyOverview": policy_overview,
        "coverageDetails": coverage_section,
        "premiumDetails": premium_section,
        "policyValues": policy_values,
        "nomineeDetails": nominee_section,
        "taxBenefits": tax_benefits,
        "keyTerms": key_terms_section,
        "exclusions": exclusions_section
    }
