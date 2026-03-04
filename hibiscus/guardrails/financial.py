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


def check_financial(response: str) -> FinancialCheckResult:
    """
    Basic financial sanity checks on response content.
    Flags obviously wrong numbers without blocking the response.
    """
    suspicious = []

    # Extract all currency amounts from response
    amounts = _extract_amounts(response)

    # Check for obviously wrong amounts
    for amount_str, amount_val in amounts:
        # Negative amounts are suspicious
        if amount_val < 0:
            suspicious.append(f"Negative amount: {amount_str}")

        # Premium > 10L is very unusual for individual policies
        if "premium" in response.lower() and amount_val > 1_000_000:
            suspicious.append(f"Unusually high premium: {amount_str}")

        # Sum insured of less than ₹1L is unusual for health insurance
        if "sum insured" in response.lower() and 0 < amount_val < 100_000:
            suspicious.append(f"Very low sum insured: {amount_str} — verify this is correct")

    if suspicious:
        return FinancialCheckResult(
            passed=False,
            reason=f"Suspicious financial figures detected: {suspicious}",
            suspicious_numbers=suspicious,
        )

    return FinancialCheckResult(
        passed=True,
        reason="Financial figures within expected ranges",
        suspicious_numbers=[],
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
