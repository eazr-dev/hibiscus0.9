"""
Policy Analysis Constants
Supported/unsupported insurance types and document classification keywords.
"""
from typing import List, Set


# ==================== SUPPORTED INSURANCE TYPES ====================
# These are the insurance types that Eazr can analyze

SUPPORTED_POLICY_TYPES: Set[str] = {
    # Health Insurance
    "health", "medical", "mediclaim", "health insurance", "medical insurance",
    # Life Insurance
    "life", "term", "endowment", "ulip", "whole life", "life insurance", "term insurance", "term life",
    # Motor Insurance
    "motor", "car", "vehicle", "bike", "two-wheeler", "four-wheeler", "auto",
    "motor insurance", "car insurance", "vehicle insurance", "two wheeler", "four wheeler",
    # Travel Insurance
    "travel", "travel insurance",
    # Personal Accident Insurance
    "pa", "personal accident", "accidental", "accident",
    "personal accident insurance", "pa insurance",
}

# Insurance types we explicitly DO NOT support (for clear error messages)
UNSUPPORTED_POLICY_TYPES: Set[str] = {
    # Agricultural/Crop Insurance
    "crop", "agricultural", "agriculture", "farm", "livestock", "pmfby",
    "crop insurance", "agricultural insurance", "farm insurance",
    # Business Insurance
    "business", "commercial", "liability", "professional indemnity", "cyber",
    "business insurance", "commercial insurance", "cyber insurance",
    # Specialty Insurance
    "marine", "aviation", "engineering", "marine insurance", "aviation insurance",
    # Home/Property Insurance (not yet supported)
    "home", "property", "fire", "burglary", "home insurance", "property insurance"
}

# Keywords that indicate this is likely NOT an insurance document
NON_INSURANCE_KEYWORDS: List[str] = [
    "invoice", "receipt", "bill", "quotation", "quote", "proposal form",
    "application form", "kyc", "bank statement", "salary slip", "payslip",
    "tax return", "itr", "form 16", "pan card", "aadhaar", "passport",
    "driving license", "voter id", "electricity bill", "phone bill",
    "rent agreement", "lease agreement", "sale deed", "registration"
]

# Keywords that indicate this IS an insurance document
INSURANCE_DOCUMENT_KEYWORDS: List[str] = [
    "policy", "insurance", "coverage", "sum insured", "sum assured",
    "premium", "insured", "policyholder", "policy holder", "nominee",
    "claim", "exclusion", "waiting period", "uin", "irda", "irdai",
    "certificate of insurance", "policy schedule", "policy document"
]
