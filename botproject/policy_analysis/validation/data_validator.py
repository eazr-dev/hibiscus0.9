"""
Policy Data Validator
Validates extracted policy data for inconsistencies, type mismatches,
and data quality issues. Returns warnings, errors, and recommendations.
"""
import re
import logging

logger = logging.getLogger(__name__)


def validate_policy_data(category_data: dict, policy_type: str) -> dict:
    """
    Validate extracted policy data for inconsistencies.
    Returns dict with warnings, errors, and recommendations.
    """
    warnings = []
    errors = []
    recommendations = []

    # 1. Cover Type Validation (Health Insurance)
    # Note: This is a DATA EXTRACTION check, not a policy issue
    # Mismatches indicate AI extraction errors, not problems with the actual policy
    if policy_type in ["health", "medical", "mediclaim"]:
        insured_members = category_data.get("insuredMembers", [])
        members_covered = category_data.get("membersCovered", [])

        member_count = len(insured_members) if isinstance(insured_members, list) else len(members_covered) if isinstance(members_covered, list) else 0
        cover_type = category_data.get("coverageDetails", {}).get("coverType", "")

        if member_count > 1:
            if cover_type and "individual" in cover_type.lower():
                # Check if this is a genuine Individual policy (members have different SIs)
                # or a likely extraction error (all members share one SI = Family Floater)
                policy_type_field = category_data.get("policyDetails", {}).get("policyType", "")
                _is_genuine_individual = False

                # If policyType ALSO says "Individual", both fields agree — trust it
                if policy_type_field and "individual" in str(policy_type_field).lower():
                    _is_genuine_individual = True

                # If members have different sumInsured values, it's definitely Individual
                _member_sis = []
                for _m in (insured_members if isinstance(insured_members, list) else []):
                    _msi = _m.get("memberSumInsured") if isinstance(_m, dict) else None
                    if _msi and isinstance(_msi, (int, float)) and _msi > 0:
                        _member_sis.append(_msi)
                if len(set(_member_sis)) > 1:
                    _is_genuine_individual = True

                if not _is_genuine_individual:
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

    if policy_type in ["health", "medical", "mediclaim"]:
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
    def validate_value_type(value, field_id: str, field_label: str) -> tuple:
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

    def get_actual_value_type(value) -> str:
        """Get the actual valueType as assigned by get_value_type() in build_unified_sections"""
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

        # String patterns (matching get_value_type logic)
        str_val = str(value).lower()
        raw_val = str(value)
        if any(x in str_val for x in ["₹", "inr", "$", "€", "£", "¥"]):
            return "currency"
        # Date: require actual date-like pattern (DD/MM/YYYY, YYYY-MM-DD, etc.)
        # Avoid false positives on policy numbers (DCOR00832176202/00), codes, etc.
        if re.search(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}', raw_val):
            return "date"
        # Phone: Must have separators (dashes, spaces, +, parens) to distinguish
        # from plain numeric IDs like policy numbers, customer IDs, etc.
        # Pure digits without separators are "string", not "phone"
        if re.match(r'^[\d\s\-\+\(\)]+$', raw_val):
            has_separator = any(c in raw_val for c in [' ', '-', '+', '(', ')'])
            if has_separator:
                return "phone"
            # Pure digits: only classify as phone if starts with common phone prefixes
            # Indian phone: 10 digits starting with 6-9, or 1800/1860 toll-free
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

            # Get the actual valueType as it would be assigned
            actual_type = get_actual_value_type(field_value)

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
    # Handle both nested (health: premiumBreakdown.basePremium) and
    # flat (motor: grossPremium, gst, totalPremium) premium structures
    premium_breakdown = category_data.get("premiumBreakdown", {})

    def _extract_num(d, key):
        """Extract numeric value from dict, handling {value: X} format."""
        raw = d.get(key, 0)
        if isinstance(raw, dict):
            raw = raw.get("value", 0)
        try:
            return float(raw) if raw else 0
        except (ValueError, TypeError):
            return 0

    if premium_breakdown and isinstance(premium_breakdown, dict):
        # Nested structure — health uses "basePremium", motor uses "grossPremium" for net premium
        base_premium = _extract_num(premium_breakdown, "basePremium") or _extract_num(premium_breakdown, "grossPremium")
        total_premium = _extract_num(premium_breakdown, "totalPremium")
        gst = _extract_num(premium_breakdown, "gst")
    else:
        # Flat structure — fields at category_data top level
        base_premium = _extract_num(category_data, "basePremium") or _extract_num(category_data, "grossPremium")
        total_premium = _extract_num(category_data, "totalPremium")
        gst = _extract_num(category_data, "gst")

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
    # Check for discount in category_data or premium_breakdown
    for _disc_key in ("existingCustomerDiscount", "discount", "loyaltyDiscount"):
        _disc_val = _extract_num(premium_breakdown, _disc_key) if premium_breakdown else 0
        if not _disc_val:
            _disc_val = _extract_num(category_data, _disc_key)
        if _disc_val > 0:
            discount_total += _disc_val

    # The taxable amount is base + addons - discounts
    taxable_amount = base_premium + addon_premiums_total - discount_total

    # Check if GST is approximately 18% of taxable amount
    # Many insurers include add-on premiums in basePremium, so try both:
    # 1. GST / basePremium (add-ons already included)
    # 2. GST / taxable_amount (add-ons separate)
    # Only warn if NEITHER approach gives ~18%
    if base_premium > 0 and gst > 0:
        gst_pct_base = (gst / base_premium) * 100
        gst_pct_taxable = (gst / taxable_amount) * 100 if taxable_amount > 0 else gst_pct_base
        # Accept if either calculation is within 3% of 18%
        if abs(gst_pct_base - 18) > 3 and abs(gst_pct_taxable - 18) > 3:
            # Use whichever is closer to 18% for the warning message
            closer_pct = gst_pct_base if abs(gst_pct_base - 18) < abs(gst_pct_taxable - 18) else gst_pct_taxable
            warnings.append({
                "field": "gst",
                "issue": f"GST amount ({closer_pct:.1f}% of premium base) seems incorrect. Expected ~18%",
                "recommendation": "Verify GST calculation with insurer",
                "severity": "low"
            })

    # Check if total premium matches base + GST (simple) or base + addons + GST - discounts
    # Try simple formula first (base + GST = total) since many policies include add-ons in base
    if base_premium > 0 and gst > 0 and total_premium > 0:
        simple_total = base_premium + gst
        full_total = base_premium + addon_premiums_total + gst - discount_total
        tolerance = max(500, total_premium * 0.02)
        # Accept if either formula matches
        if abs(total_premium - simple_total) > tolerance and abs(total_premium - full_total) > tolerance:
            # Use whichever is closer for the warning
            closer_total = simple_total if abs(total_premium - simple_total) < abs(total_premium - full_total) else full_total
            warnings.append({
                "field": "totalPremium",
                "issue": f"Total premium (₹{total_premium:,.2f}) doesn't match expected (₹{closer_total:,.2f})",
                "recommendation": "Check for additional charges or discounts not accounted for",
                "severity": "low"
            })

    # 7. Member Data Validation (Health Insurance)
    if policy_type in ["health", "medical", "mediclaim"]:
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
