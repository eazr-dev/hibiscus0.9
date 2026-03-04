"""
Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
PII guardrail — detects and redacts Indian-specific PII: Aadhaar, PAN, IFSC,
UPI/VPA, passport, phone numbers, email addresses, and more.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class PIICheckResult:
    passed: bool
    pii_types_found: List[str]     # e.g. ["aadhaar", "phone"] if found in response
    modified_response: str
    reason: str


# ── PII patterns (pattern, replacement, label) ────────────────────────────────
# Order matters: more specific patterns should come before generic ones to avoid
# false positives (e.g., Aadhaar before generic digit sequences).

_PII_PATTERNS = [
    # ── Indian-specific identifiers ────────────────────────────────────────

    # Aadhaar: 12 digits in groups of 4, with optional spaces or hyphens.
    # Covers: "1234 5678 9012", "1234-5678-9012", "123456789012"
    # Uses word boundary + digit-group anchoring to avoid matching inside
    # longer numbers (e.g., bank account numbers already have their own rule).
    (r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", "XXXX-XXXX-XXXX", "aadhaar"),

    # PAN: 5 uppercase letters, 4 digits, 1 uppercase letter.
    # The 4th character encodes entity type: C=Company, P=Person, H=HUF, etc.
    # e.g. ABCDE1234F
    (r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "XXXXXXXXXX", "pan"),

    # IFSC Code: 4 uppercase letters (bank code) + "0" + 6 alphanumeric chars.
    # e.g. SBIN0001234, HDFC0BRANCH
    (r"\b[A-Z]{4}0[A-Z0-9]{6}\b", "XXXXXXXXXXX", "ifsc"),

    # UPI / VPA ID: user@provider pattern, e.g. name@okicici, phone@ybl
    # Kept before email to catch VPA-style addresses with known UPI handles.
    (r"\b[A-Za-z0-9._\-]+@(?:ok(?:icici|axis|sbi|hdfc)|ybl|upi|paytm|apl|ibl|axl|freecharge|okhdfcbank|oksbi)\b",
     "user@***.upi", "vpa_upi"),

    # Indian Passport: single uppercase letter + 7 digits.
    # e.g. J1234567, K9876543. Indian passports follow [A-Z]\d{7}.
    (r"\b[A-PR-WY-Z][0-9]{7}\b", "X0000000", "indian_passport"),

    # Indian mobile: starts with 6-9, total 10 digits.
    # With optional +91 or 0 prefix.
    (r"\b(?:\+91[\s\-]?|0)?[6-9]\d{9}\b", "XXXXXXXXXX", "phone"),

    # ── Financial identifiers ──────────────────────────────────────────────

    # Policy number heuristic: 2-4 uppercase letters optionally followed by / or -, then 6-12 digits
    # e.g. HDFC/123456789, STAR-123456, NB0123456789
    (r"\b[A-Z]{2,4}[/\-]?\d{6,12}\b", "POL-XXXXXXXX", "policy_number"),

    # Credit/Debit card number: 13-19 digits with optional spaces/hyphens
    (r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{1,7}\b", "XXXX-XXXX-XXXX-XXXX", "card_number"),

    # ── Contact / personal ─────────────────────────────────────────────────

    # Email address (general — placed after VPA so UPI handles are caught first)
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "user@***.com", "email"),

    # Date of birth (DD/MM/YYYY or DD-MM-YYYY)
    (r"\b\d{2}[/\-]\d{2}[/\-]\d{4}\b", "XX/XX/XXXX", "dob"),

    # Bank account number heuristic: 9-18 digit sequence (standalone).
    # Placed last since it is the most generic numeric pattern.
    (r"(?<!\d)\d{9,18}(?!\d)", "XXXXXXXXXX", "account_number"),
]

# Compile for performance
_COMPILED_PII_PATTERNS = [
    (re.compile(pattern), replacement, label)
    for pattern, replacement, label in _PII_PATTERNS
]


def mask_pii_for_logging(text: str) -> str:
    """
    Mask PII in text before writing to logs.

    Call this on any user-provided content before logging.
    The original text is NOT modified — only the copy returned here is masked.

    Args:
        text: Raw text that may contain PII

    Returns:
        Text with PII replaced by placeholder values
    """
    if not text:
        return text

    masked = text
    for compiled_pattern, replacement, _ in _COMPILED_PII_PATTERNS:
        masked = compiled_pattern.sub(replacement, masked)
    return masked


def check_pii(response: str, user_id: str = "") -> PIICheckResult:
    """
    Check if the response leaks PII verbatim.

    This shouldn't happen in normal flow since responses are LLM-generated,
    but guards against edge cases where extracted policy data gets echoed.

    Args:
        response: The final response text to check
        user_id: For logging context

    Returns:
        PIICheckResult — passes even if PII found (modifies response to mask)
    """
    if not response:
        return PIICheckResult(
            passed=True,
            pii_types_found=[],
            modified_response=response,
            reason="Empty response",
        )

    pii_types_found = []
    modified = response

    for compiled_pattern, replacement, label in _COMPILED_PII_PATTERNS:
        if compiled_pattern.search(modified):
            pii_types_found.append(label)
            modified = compiled_pattern.sub(replacement, modified)

    if pii_types_found:
        return PIICheckResult(
            passed=False,  # Flagged — but response is still modified and returned
            pii_types_found=pii_types_found,
            modified_response=modified,
            reason=f"PII detected and masked in response: {pii_types_found}",
        )

    return PIICheckResult(
        passed=True,
        pii_types_found=[],
        modified_response=response,
        reason="No PII detected in response",
    )
