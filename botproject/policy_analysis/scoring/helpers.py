"""
Shared helper functions for scoring and zone classification modules.

Centralized to avoid duplication between universal_scores.py and zone_classifier.py.
"""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# ==================== VALUE EXTRACTION HELPERS ====================

def val(v2: dict, field: str) -> Any:
    """Get bare value from a ConfidenceField in v2 extraction."""
    fd = v2.get(field)
    if isinstance(fd, dict) and "value" in fd:
        return fd["value"]
    return fd


def num(v2: dict, field: str) -> float:
    """Get numeric value from a field, returning 0 on failure."""
    raw = val(v2, field)
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        cleaned = (
            raw.replace(",", "").replace("₹", "").replace("Rs.", "")
            .replace("Rs", "").replace("$", "").replace("%", "").strip()
        )
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            m = re.search(r'(\d+(?:\.\d+)?)', cleaned)
            if m:
                return float(m.group(1))
            return 0.0
    return 0.0


def bool_field(v2: dict, field: str) -> bool | None:
    """Get boolean-ish value from a field."""
    raw = val(v2, field)
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        low = raw.lower().strip()
        if low in ("yes", "true", "covered", "included", "available", "applicable"):
            return True
        if low in ("no", "false", "not covered", "not included", "not available",
                    "not applicable", "na", "n/a", "nil", "none"):
            return False
    return None


def has_value(v2: dict, field: str) -> bool:
    """Check if field exists and has a non-null, non-empty, non-zero value."""
    raw = val(v2, field)
    if raw is None:
        return False
    if isinstance(raw, bool):
        return raw  # False → no value, True → has value
    if isinstance(raw, str) and not raw.strip():
        return False
    if isinstance(raw, list) and len(raw) == 0:
        return False
    if isinstance(raw, (int, float)) and raw == 0:
        return False
    return True


def has_maternity(v2: dict) -> bool:
    """Dynamically detect maternity coverage from any available extraction field."""
    if has_value(v2, "maternityCover") or has_value(v2, "maternityCovered"):
        return True
    mw = val(v2, "maternityWaiting")
    if mw:
        mw_str = str(mw).lower().strip()
        if mw_str and mw_str not in ("na", "n/a", "nil", "none", "not applicable",
                                      "not available", "not covered", "null", "0"):
            # Exclude "if opted" / "if add-on" patterns — indicates maternity is optional, not active
            if any(kw in mw_str for kw in ("if opted", "if add-on", "if maternity", "optional",
                                            "on opting", "add on is opted")):
                return False
            return True
    sub_limits = val(v2, "otherSubLimits")
    if isinstance(sub_limits, list):
        for item in sub_limits:
            item_str = str(item).lower()
            if "maternity" in item_str:
                if not any(neg in item_str for neg in ("not covered", "not available",
                                                        "excluded", "not applicable")):
                    return True
    return False


# ==================== ROOM RENT HELPER ====================

def is_room_rent_unlimited(room_str: str) -> bool:
    """Check if a room rent string indicates no cap / unlimited.

    Covers common phrasings:
    - "No limit", "No cap", "No restriction", "No capping"
    - "Unlimited", "All categories", "Any category"
    - "All Room Categories Covered" (Tata AIG style)
    - "Single Private AC Room" (Star Health style - no sub-limit)
    """
    if not room_str:
        return False
    low = room_str.lower()
    # Explicit "no limit/cap/restriction" patterns
    if "no" in low and any(w in low for w in ("limit", "cap", "restrict", "capping")):
        return True
    # Other unlimited indicators
    if "unlimited" in low:
        return True
    if "all categor" in low:
        return True
    if "any categor" in low:
        return True
    if "no sub" in low and "limit" in low:
        return True
    # "All Room Categories Covered" — "all" + "categor" separated by other words
    if "all" in low and "categor" in low and "covered" in low:
        return True
    return False


# ==================== NCB / CUMULATIVE BONUS HELPER ====================

def effective_ncb_pct(v2: dict) -> float:
    """Return the effective NCB percentage for health insurance scoring.

    Checks both the annual NCB rate (ncbPercentage) and the accumulated
    cumulative bonus amount (cumulativeBonusAmount / accumulatedNcbAmount).
    If an accumulated amount is available AND the sum insured is known,
    computes the accumulated-to-SI ratio and returns whichever is higher.

    Also handles text-based CB descriptions like "50% of SI, max up to 100%"
    by extracting the percentage directly rather than treating it as an amount.

    For motor policies, ncbPercentage is already the discount percentage
    (e.g. 50%), so callers should continue using num(v2, "ncbPercentage")
    directly for motor.
    """
    annual_rate = num(v2, "ncbPercentage")

    # Check maxNcbPercentage as a fallback for annual rate
    if annual_rate <= 0:
        max_ncb = num(v2, "maxNcbPercentage")
        if max_ncb > 0:
            # maxNcb exists but annual rate is 0 — policy has NCB feature
            # Use a conservative estimate; allow up to 100% for products like Star Health FHO
            annual_rate = min(max_ncb, 100)

    # Try accumulated amount from multiple possible fields
    # First check if the field contains percentage text (e.g. "50% of SI")
    # vs an actual numeric amount (e.g. 500000)
    best_pct = annual_rate
    si = num(v2, "sumInsured")

    for field_name in ("cumulativeBonusAmount", "accumulatedNcbAmount", "ncbAmount"):
        raw = val(v2, field_name)
        if raw is None:
            continue
        raw_str = str(raw).lower() if isinstance(raw, str) else ""

        # If the field contains "%" and "si" — it's a percentage description, not an amount
        if raw_str and "%" in raw_str and ("si" in raw_str or "sum" in raw_str):
            pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', raw_str)
            if pct_match:
                pct_val = float(pct_match.group(1))
                best_pct = max(best_pct, pct_val)
            continue

        # Otherwise treat as an accumulated amount
        accum = num(v2, field_name)
        if accum > 0 and si > 0:
            accum_pct = (accum / si) * 100
            best_pct = max(best_pct, accum_pct)
        elif accum > 0:
            best_pct = max(best_pct, accum)  # fallback: treat as percentage if no SI

    return best_pct


# ==================== LABEL & UTILITY HELPERS ====================

def label(score: int) -> str:
    """Convert score to human-readable label."""
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Strong"
    if score >= 60:
        return "Good"
    if score >= 45:
        return "Adequate"
    if score >= 30:
        return "Moderate"
    return "Weak"


def clamp(val_: float, lo: float = 0, hi: float = 100) -> int:
    """Clamp and round to int."""
    return max(lo, min(hi, round(val_)))


def parse_months(raw_str: str) -> int:
    """Parse a waiting period string into months."""
    if not raw_str:
        return 0
    low = raw_str.lower()
    m = re.search(r'(\d+)', low)
    if not m:
        return 0
    v = int(m.group(1))
    if "year" in low:
        return v * 12
    return v


# ==================== NETWORK HOSPITAL LOOKUP ====================

def lookup_network_hospitals(insurer_name: str) -> int:
    """Look up network hospital count from provider info service."""
    try:
        from services.insurance_provider_info import get_insurance_provider_info
        provider = get_insurance_provider_info(insurer_name)
        if provider:
            network_size = provider.get("networkSize", "")
            if network_size and network_size != "N/A":
                match = re.search(r'([\d,]+)\+?\s*(?:Network\s*)?Hospital', str(network_size), re.IGNORECASE)
                if match:
                    return int(match.group(1).replace(",", ""))
    except Exception:
        pass
    return 0


# ==================== ZONE FEATURE BUILDER ====================

_EXCLUDED_VALUES = frozenset({
    "not found in document",
    "unknown",
})


def _truncate_to_limit(text: str, limit: int = 15) -> str:
    """Truncate text to *limit* chars without cutting a word mid-way."""
    if len(text) <= limit:
        return text
    # Find the last space at or before the limit
    cut = text.rfind(" ", 0, limit + 1)
    if cut <= 0:
        # Single long word — hard cut is the only option
        return text[:limit]
    return text[:cut]


def feature(
    feature_id: str,
    feature_name: str,
    zone: str,
    current_value: str,
    explanation: str,
    recommendation: str = "",
) -> dict:
    """Build a single feature classification entry."""
    # Suppress placeholder values — never surface "Not found in document" etc.
    sanitized = current_value.strip() if current_value else ""
    if sanitized.lower() in _EXCLUDED_VALUES:
        sanitized = ""

    # Cap at 15 characters (word-boundary aware)
    sanitized = _truncate_to_limit(sanitized, 15)

    entry = {
        "featureId": feature_id,
        "featureName": feature_name,
        "zone": zone,
        "explanation": explanation,
    }
    # Only include currentValue when there is an actual value
    if sanitized:
        entry["currentValue"] = sanitized
    return entry


# ==================== DOCUMENT TYPE DETECTION ====================

def is_schedule_only_health(v2: dict) -> bool:
    """Detect if a health policy document appears to be a schedule-only PDF.

    Returns True if >=5 of 7 critical benefit features are missing.
    """
    critical_features = [
        "dayCareProcedures", "restoration", "ayushTreatment",
        "preHospitalization", "postHospitalization",
        "ambulanceCover", "modernTreatment",
    ]
    missing = sum(1 for f in critical_features if not has_value(v2, f))
    return missing >= 5


def is_tp_only_motor(v2: dict) -> bool:
    """Check if this is a Third Party Only motor policy.

    Uses flexible regex to match various TP naming conventions.
    """
    ptype = str(val(v2, "productType") or "").lower()
    if "comprehensive" in ptype or "comp" in ptype:
        return False
    return bool(re.search(r'(?:third\s*party|tp\s*(?:only)?|liability\s*only)', ptype))


# ==================== TRAVEL CURRENCY CONVERSION ====================

def travel_to_inr(v2: dict, amount: float) -> float:
    """Convert a travel coverage amount to INR based on coverageCurrency.

    Always checks the currency field first. Only uses heuristic fallback
    if currency field is missing/empty AND amount is clearly foreign
    (< 1,00,000 — no legitimate INR travel coverage is this low).
    """
    if amount <= 0:
        return 0.0
    currency = val(v2, "coverageCurrency")
    if isinstance(currency, str) and currency.strip():
        cur = currency.strip().upper()
        if cur in ("USD", "$", "US DOLLAR", "US DOLLARS"):
            return amount * 83.0
        if cur in ("EUR", "€", "EURO", "EUROS"):
            return amount * 91.0
        if cur in ("GBP", "£", "POUND", "POUNDS"):
            return amount * 105.0
        if cur in ("INR", "₹", "RUPEE", "RUPEES"):
            return amount
    # No currency info — heuristic: only convert if amount < 100,000
    # (legitimate INR travel coverage is typically >= ₹1 lakh)
    # This prevents ₹4L INR from being wrongly multiplied by 83
    if amount < 100000:
        return amount * 83.0  # likely USD/EUR
    return amount  # likely already INR


def travel_currency_symbol(v2: dict) -> str:
    """Get the display currency symbol for travel policies."""
    currency = val(v2, "coverageCurrency")
    if isinstance(currency, str):
        cur = currency.strip().upper()
        if cur in ("USD", "$", "US DOLLAR", "US DOLLARS"):
            return "$"
        if cur in ("EUR", "€", "EURO", "EUROS"):
            return "€"
        if cur in ("GBP", "£", "POUND", "POUNDS"):
            return "£"
    return "₹"
