"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Financial guardrail — validates numerical claims, prevents misleading projections.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class FinancialCheckResult:
    passed: bool
    reason: str
    suspicious_numbers: List[str]
    modified_response: Optional[str] = None


# ── Domain-specific validation ranges ────────────────────────────────────────
_FINANCIAL_RANGES = {
    "irr": {
        "pattern": r'(?:irr|internal\s+rate\s+of\s+return)\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
        "range": (-5.0, 30.0),
        "label": "IRR",
    },
    "tax_deduction": {
        "pattern": r'(?:deduction|tax\s+benefit)\s+(?:of\s+)?(?:up\s+to\s+)?₹?\s*(\d[\d,]*)',
        "range": (0, 2_50_000),  # Max 80C+80D combined
        "label": "Tax deduction",
        "multiplier": 1,
    },
    "surrender_value_pct": {
        "pattern": r'surrender\s+value\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
        "range": (0.0, 100.0),
        "label": "Surrender value %",
    },
    "premium_to_income": {
        "pattern": r'premium.to.income\s+ratio\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
        "range": (0.0, 40.0),
        "label": "Premium-to-income ratio",
    },
}

_FINANCIAL_CAVEAT = (
    "\n\n*Note: Some financial figures in this response may need verification. "
    "Please cross-check with your policy document or insurer.*"
)


def check_financial(response: str) -> FinancialCheckResult:
    """
    Financial sanity checks on response content.
    Flags obviously wrong numbers and appends caveats — never blocks the response.
    """
    suspicious = []
    response_lower = response.lower()

    # Extract all currency amounts from response
    amounts = _extract_amounts(response)

    # Check for obviously wrong amounts
    for amount_str, amount_val in amounts:
        # Negative amounts are suspicious
        if amount_val < 0:
            suspicious.append(f"Negative amount: {amount_str}")

        # Premium > 10L is very unusual for individual policies
        if "premium" in response_lower and amount_val > 1_000_000:
            suspicious.append(f"Unusually high premium: {amount_str}")

        # Sum insured of less than ₹1L is unusual for health insurance
        if "sum insured" in response_lower and 0 < amount_val < 100_000:
            suspicious.append(f"Very low sum insured: {amount_str} — verify this is correct")

    # Domain-specific range checks
    for key, info in _FINANCIAL_RANGES.items():
        for match in re.finditer(info["pattern"], response_lower):
            try:
                value = float(match.group(1).replace(",", ""))
                value *= info.get("multiplier", 1)
                lo, hi = info["range"]
                if value < lo or value > hi:
                    suspicious.append(
                        f"{info['label']} {value} outside expected range [{lo}-{hi}]"
                    )
            except (ValueError, IndexError):
                pass

    if suspicious:
        modified = response + _FINANCIAL_CAVEAT
        return FinancialCheckResult(
            passed=False,
            reason=f"Suspicious financial figures detected: {suspicious}",
            suspicious_numbers=suspicious,
            modified_response=modified,
        )

    return FinancialCheckResult(
        passed=True,
        reason="Financial figures within expected ranges",
        suspicious_numbers=[],
        modified_response=response,
    )


def _extract_amounts(text: str) -> List[Tuple[str, float]]:
    """Extract currency amounts from text."""
    amounts = []

    # Match ₹ amounts with lakhs/crores
    patterns = [
        (r'₹\s*(\d[\d,]*(?:\.\d+)?)\s*crore', 1e7),
        (r'₹\s*(\d[\d,]*(?:\.\d+)?)\s*lakh', 1e5),
        (r'₹\s*(\d[\d,]*(?:\.\d+)?)', 1),
        (r'Rs\.?\s*(\d[\d,]*(?:\.\d+)?)\s*(?:lakh|L)', 1e5),
        (r'Rs\.?\s*(\d[\d,]*(?:\.\d+)?)', 1),
    ]

    for pattern, multiplier in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            amount_str = match.group(0)
            try:
                raw = float(match.group(1).replace(",", ""))
                amount_val = raw * multiplier
                amounts.append((amount_str, amount_val))
            except ValueError:
                pass

    return amounts
