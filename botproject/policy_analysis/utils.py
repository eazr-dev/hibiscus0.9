"""
Shared Utility Functions for Policy Analysis
Common helpers used across multiple insurance types.
"""
import logging
import re

logger = logging.getLogger(__name__)


def parse_number_from_string_safe(text: str) -> float:
    """Safely extract a number from a string, returning 0 on failure."""
    if not text:
        return 0
    try:
        cleaned = re.sub(r'[^\d.]', '', str(text).replace(',', ''))
        return float(cleaned) if cleaned else 0
    except (ValueError, TypeError):
        return 0


def get_score_label(score: int) -> dict:
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


def safe_num(val, default=0):
    """Safely parse a numeric value from various input types."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return default
    return default


# ==================== CSR LOOKUP (Single Source of Truth) ====================
# Claim Settlement Ratios — sourced from IRDAI Annual Report FY 2023-24
# Updated centrally; imported by universal_scores.py and zone_classifier.py

CSR_DATA = {
    # Standalone Health Insurers (SAHI) — CSR from IRDAI FY 2022-23
    "star health": 90.37, "star health and allied insurance": 90.37,
    "niva bupa": 96.30, "niva bupa health insurance": 96.30, "max bupa": 96.30,
    "care health": 96.74, "care health insurance": 96.74, "religare health": 96.74,
    "aditya birla": 95.21, "aditya birla health insurance": 95.21, "abhi": 95.21,
    "manipal cigna": 90.66, "manipalcigna": 90.66, "cigna ttk": 90.66,
    # General Insurers (overall CSR — includes health + motor + other)
    "hdfc ergo": 98.50, "hdfc ergo general insurance": 98.50,
    "icici lombard": 97.00, "icici lombard general insurance": 97.00,
    "bajaj allianz": 98.00, "bajaj allianz general insurance": 98.00,
    "tata aig": 87.08, "tata aig general insurance": 87.08,
    "new india assurance": 95.00, "the new india assurance": 95.00,
    "united india insurance": 92.00, "united india": 92.00,
    "national insurance": 90.00, "national insurance company": 90.00,
    "oriental insurance": 88.00, "oriental insurance company": 88.00,
    "sbi general": 93.00, "sbi general insurance": 93.00,
    "kotak mahindra": 89.00, "kotak mahindra general insurance": 89.00,
    "go digit": 97.00, "digit insurance": 97.00,
    "acko": 98.50, "acko general insurance": 98.50,
    "acko general insurance limited": 98.50, "acko general insurance ltd.": 98.50,
    "chola ms": 91.00, "cholamandalam ms": 91.00,
    "future generali": 92.00, "future generali india insurance": 92.00,
    "iffco tokio": 94.00, "iffco tokio general insurance": 94.00,
    "reliance general": 96.00, "reliance general insurance": 96.00,
    "magma hdi": 87.00,
    "liberty general": 86.00, "liberty general insurance": 86.00,
    "royal sundaram": 89.00, "royal sundaram general insurance": 89.00,
    "raheja qbe": 84.00,
    "zuno": 92.00, "zuno general insurance": 92.00,
    # Life Insurers
    "lic": 98.50, "life insurance corporation": 98.50,
    "hdfc life": 99.00, "hdfc standard life": 99.00,
    "icici prudential": 97.80, "icici pru life": 97.80,
    "sbi life": 95.00, "sbi life insurance": 95.00,
    "max life": 99.34, "max life insurance": 99.34,
    "tata aia life": 98.00,
    "bajaj allianz life": 98.59,
    "kotak life": 96.00,
    "birla sun life": 97.00, "aditya birla sun life": 97.00,
    "pnb metlife": 96.00,
    "canara hsbc life": 95.00,
    "aegon life": 94.00,
}


def lookup_csr(insurer_name: str) -> float:
    """Look up Claim Settlement Ratio for an insurer.

    Central lookup used by all scoring/zone modules.
    Returns 0.0 if insurer not found.
    """
    if not insurer_name:
        return 0.0
    name_lower = insurer_name.lower().strip()
    if name_lower in CSR_DATA:
        return CSR_DATA[name_lower]
    for key, val in CSR_DATA.items():
        if key in name_lower or name_lower in key:
            return val
    return 0.0


def inject_page_markers(pages_text: list[str]) -> str:
    """Inject [Page N] markers into extracted text for evidence grounding.

    Args:
        pages_text: List of text strings, one per PDF page.

    Returns:
        Single string with [Page 1], [Page 2], ... markers prepended
        to each page's text.
    """
    parts = []
    for i, page_text in enumerate(pages_text, start=1):
        text = (page_text or "").strip()
        if text:
            parts.append(f"[Page {i}]\n{text}")
    return "\n\n".join(parts)


def get_insurer_logo_url(insurer_name: str) -> str:
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
