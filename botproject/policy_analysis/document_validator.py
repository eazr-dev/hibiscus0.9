"""
Document Validation
Validates whether uploaded documents are insurance policies and checks type support.
"""
from policy_analysis.constants import (
    SUPPORTED_POLICY_TYPES,
    UNSUPPORTED_POLICY_TYPES,
    NON_INSURANCE_KEYWORDS,
    INSURANCE_DOCUMENT_KEYWORDS,
)


def is_supported_policy_type(policy_type: str) -> bool:
    """Check if the detected policy type is supported by Eazr"""
    if not policy_type:
        return False
    policy_type_lower = policy_type.lower().strip()

    # Check if it matches any supported type
    for supported in SUPPORTED_POLICY_TYPES:
        if supported in policy_type_lower or policy_type_lower in supported:
            return True
    return False


def is_unsupported_policy_type(policy_type: str) -> str:
    """
    Check if the detected policy type is explicitly unsupported.
    Returns the category name if unsupported, None otherwise.
    """
    if not policy_type:
        return None
    policy_type_lower = policy_type.lower().strip()

    # Check agricultural
    if any(kw in policy_type_lower for kw in ["crop", "agricultural", "agriculture", "farm", "livestock", "pmfby"]):
        return "Agricultural/Crop Insurance"

    # Check business
    if any(kw in policy_type_lower for kw in ["business", "commercial", "liability", "professional indemnity", "cyber"]):
        return "Business/Commercial Insurance"

    # Check specialty
    if any(kw in policy_type_lower for kw in ["marine", "aviation", "engineering"]):
        return "Specialty Insurance (Marine/Aviation/Engineering)"

    # Check home/property
    if any(kw in policy_type_lower for kw in ["home", "property", "fire", "burglary"]):
        return "Home/Property Insurance"

    return None


def validate_insurance_document(text_content: str, detected_policy_type: str = None) -> dict:
    """
    Validate if the uploaded document is a valid insurance document.

    Returns:
        dict with keys:
        - is_valid: bool
        - is_insurance: bool
        - is_supported: bool
        - error_code: str (if invalid)
        - error_message: str (if invalid)
        - unsupported_type: str (if unsupported insurance type)
    """
    text_lower = text_content.lower() if text_content else ""

    # Check if document contains insurance keywords
    insurance_keyword_count = sum(1 for kw in INSURANCE_DOCUMENT_KEYWORDS if kw in text_lower)
    non_insurance_keyword_count = sum(1 for kw in NON_INSURANCE_KEYWORDS if kw in text_lower)

    # If more non-insurance keywords than insurance keywords, likely not insurance
    if non_insurance_keyword_count > insurance_keyword_count and insurance_keyword_count < 3:
        return {
            "is_valid": False,
            "is_insurance": False,
            "is_supported": False,
            "error_code": "POL_8010",
            "error_message": "The uploaded document does not appear to be an insurance policy. Please upload a valid insurance policy document (PDF)."
        }

    # If very few insurance keywords, might not be insurance
    if insurance_keyword_count < 2:
        return {
            "is_valid": False,
            "is_insurance": False,
            "is_supported": False,
            "error_code": "POL_8010",
            "error_message": "Unable to identify this as an insurance document. Please ensure you are uploading a valid insurance policy PDF."
        }

    # Check if detected policy type is unsupported
    if detected_policy_type:
        unsupported_category = is_unsupported_policy_type(detected_policy_type)
        if unsupported_category:
            return {
                "is_valid": False,
                "is_insurance": True,
                "is_supported": False,
                "error_code": "POL_8011",
                "error_message": f"Sorry, Eazr currently does not support {unsupported_category}. We support Health, Life, Motor, Accidental, and Travel insurance policies.",
                "unsupported_type": unsupported_category
            }

    # Document appears to be valid insurance
    return {
        "is_valid": True,
        "is_insurance": True,
        "is_supported": True,
        "error_code": None,
        "error_message": None
    }
