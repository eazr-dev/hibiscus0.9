"""
Compliance Guard — IRDAI Guardrails
=====================================
Ensures every response complies with IRDAI regulations:

1. Every recommendation includes disclaimer
2. Never say "you should buy X" → "based on your profile, X may suit your needs"
3. Never guarantee returns on any insurance product
4. Never guarantee claim settlement
5. Always disclose: "EAZR provides information, not insurance advice"
6. Flag if conversation drifts into regulated territory

IRDAI Disclaimer (inject on recommendations):
"This information is provided for educational purposes only. EAZR is not a
licensed insurance distributor. Please consult a licensed insurance advisor
before making any insurance purchase decision."
"""
import re
from dataclasses import dataclass
from typing import Optional


IRDAI_DISCLAIMER = (
    "\n\n---\n"
    "*Disclaimer: This information is provided for educational purposes only. "
    "EAZR is not a licensed insurance distributor or advisor. Please consult a "
    "licensed insurance advisor before making any insurance purchase, surrender, "
    "or investment decision. Past performance does not guarantee future returns.*"
)

SHORT_DISCLAIMER = (
    " *(Educational information only — consult a licensed advisor before any purchase.)*"
)


@dataclass
class ComplianceCheckResult:
    passed: bool
    reason: str
    modified_response: str


# ── Intents that always require full disclaimer ────────────────────────────
_DISCLAIMER_REQUIRED_INTENTS = {
    "recommend",
    "surrender",
    "calculate",
    "portfolio",
    "tax",
    "claim",
    "educate",
    "regulate",
    "grievance",
    "analyze",
    "research",
}

# ── Patterns that violate compliance ─────────────────────────────────────────
_GUARANTEED_RETURNS_PATTERNS = [
    r'guaranteed?\s+return',
    r'guaranteed?\s+(?:interest|yield|profit|income)',
    r'guaranteed?\s+\d+[\s]*%',  # catches "guaranteed 9%", "guaranteed 12%"
    r'risk.?free\s+return',
    r'assured\s+return',
    r'sure\s+(?:to\s+)?return',
    r'definitely\s+(?:will\s+)?(?:return|grow|profit)',
]

_GUARANTEED_CLAIM_PATTERNS = [
    r'(?:claim\s+)?(?:will\s+be\s+)?(?:definitely\s+)?settled',
    r'guaranteed?\s+claim',
    r'claim\s+will\s+(?:be\s+)?approved',
    r'no\s+rejection',
]

_DIRECT_PURCHASE_ADVICE = [
    r'\byou\s+(?:should|must|need\s+to|have\s+to)\s+buy\b',
    r'\bpurchase\s+this\b',
    r'\bbuy\s+(?:this|that|it)\s+(?:policy|plan|insurance)\b',
    r'\bi\s+(?:recommend|suggest)\s+you\s+buy\b',
]

# ── Patterns we want to ensure are present ───────────────────────────────────
_DISCLAIMER_PATTERNS = [
    "educational purposes",
    "not a licensed",
    "consult a licensed",
    "licensed advisor",
    "licensed insurance",
    "not insurance advice",
    "disclaimer",
]


def check_compliance(
    response: str,
    intent: str = "general_chat",
) -> ComplianceCheckResult:
    """
    Check response for IRDAI compliance issues.
    Always returns a modified_response (may add disclaimer even if passed=True).
    """
    response_lower = response.lower()
    modified_response = response

    # ── Check 1: Guaranteed returns ────────────────────────────────────────
    for pattern in _GUARANTEED_RETURNS_PATTERNS:
        if re.search(pattern, response_lower):
            modified_response = _fix_guaranteed_returns(modified_response)
            modified_response += (
                "\n\n⚠️ *Note: No insurance product can guarantee returns. "
                "Returns, if any, depend on market conditions and policy terms.*"
            )
            # Also add IRDAI disclaimer (guaranteed-returns responses need compliance context)
            if not any(phrase in modified_response.lower() for phrase in _DISCLAIMER_PATTERNS):
                modified_response += IRDAI_DISCLAIMER
            return ComplianceCheckResult(
                passed=False,
                reason=f"Response implies guaranteed returns (pattern: {pattern})",
                modified_response=modified_response,
            )

    # ── Check 2: Guaranteed claim settlement ──────────────────────────────
    for pattern in _GUARANTEED_CLAIM_PATTERNS:
        if re.search(pattern, response_lower):
            modified_response += (
                "\n\n⚠️ *Note: Claim settlement is subject to policy terms, "
                "documentation, and insurer review. No claim settlement can be guaranteed.*"
            )
            return ComplianceCheckResult(
                passed=False,
                reason=f"Response implies guaranteed claim settlement",
                modified_response=modified_response,
            )

    # ── Check 3: Direct purchase advice ───────────────────────────────────
    for pattern in _DIRECT_PURCHASE_ADVICE:
        if re.search(pattern, response_lower):
            # Replace directive language with information language
            modified_response = _soften_purchase_language(modified_response)
            break

    # ── Check 4: Add disclaimer if required by intent ──────────────────────
    has_disclaimer = any(phrase in response_lower for phrase in _DISCLAIMER_PATTERNS)

    if intent in _DISCLAIMER_REQUIRED_INTENTS and not has_disclaimer:
        modified_response = modified_response + IRDAI_DISCLAIMER

    elif not has_disclaimer:
        # Every insurance response should have at minimum a short disclaimer
        modified_response = modified_response + SHORT_DISCLAIMER

    return ComplianceCheckResult(
        passed=True,
        reason="Response passed compliance check",
        modified_response=modified_response,
    )


def _fix_guaranteed_returns(response: str) -> str:
    """Replace guaranteed return language with appropriate hedging."""
    replacements = [
        (r'guaranteed\s+\d+\.?\d*\s*%', 'a stated percentage (not guaranteed — returns depend on policy terms and fund performance)'),
        (r'guaranteed returns?', 'potential returns (subject to policy terms)'),
        (r'guaranteed interest', 'stated interest rate (subject to terms)'),
        (r'assured returns?', 'projected returns (not guaranteed)'),
    ]
    for pattern, replacement in replacements:
        response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
    return response


def _soften_purchase_language(response: str) -> str:
    """Replace directive purchase language with informational language."""
    replacements = [
        (r'\byou should buy\b', 'you may consider'),
        (r'\byou must buy\b', 'based on your profile, you may want to consider'),
        (r'\bpurchase this\b', 'this may suit your needs'),
        (r'\bbuy this policy\b', 'this policy may be suitable for your needs'),
    ]
    for pattern, replacement in replacements:
        response = re.sub(pattern, replacement, response, flags=re.IGNORECASE)
    return response


def _has_recommendation_language(response_lower: str) -> bool:
    """Check if response contains recommendation-like language."""
    return any(phrase in response_lower for phrase in [
        "recommend", "suggest", "consider", "suitable for", "may suit",
        "best plan", "good option", "ideal for",
    ])


def inject_disclaimer(response: str) -> str:
    """Force-inject IRDAI disclaimer. Use for recommendation responses."""
    if not any(p in response.lower() for p in _DISCLAIMER_PATTERNS):
        return response + IRDAI_DISCLAIMER
    return response
