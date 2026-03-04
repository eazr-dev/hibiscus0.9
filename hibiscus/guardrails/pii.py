"""
PII Guard — Personally Identifiable Information Protection
==========================================================
Two functions:
1. mask_pii_for_logging(text) — mask PII before writing to logs
2. check_pii(response, user_id) — ensure PII isn't leaked in response text

Patterns masked:
- Aadhaar number
- PAN card number
- Indian mobile number
- Policy number (heuristic)
- Email address
- Date of birth
- Bank account number (heuristic)
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

_PII_PATTERNS = [
    # Aadhaar: 12 digits with optional spaces/hyphens between groups of 4
    (r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", "XXXX-XXXX-XXXX", "aadhaar"),

    # PAN: 5 uppercase letters, 4 digits, 1 uppercase letter
    (r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "XXXXXXXXXX", "pan"),

    # Indian mobile: starts with 6-9, total 10 digits
    (r"\b[6-9]\d{9}\b", "XXXXXXXXXX", "phone"),

    # Policy number heuristic: 2-4 uppercase letters optionally followed by / or -, then 6-12 digits
    # e.g. HDFC/123456789, STAR-123456, NB0123456789
    (r"\b[A-Z]{2,4}[/\-]?\d{6,12}\b", "POL-XXXXXXXX", "policy_number"),

    # Email address
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "user@***.com", "email"),

    # Date of birth (DD/MM/YYYY or DD-MM-YYYY)
    (r"\b\d{2}[/\-]\d{2}[/\-]\d{4}\b", "XX/XX/XXXX", "dob"),

    # Bank account number heuristic: 9-18 digit sequence (standalone)
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
