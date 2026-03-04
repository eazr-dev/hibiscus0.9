"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Hallucination guardrail — cross-references claims against KG/RAG sources, flags unsupported facts.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HallucinationCheckResult:
    passed: bool
    reason: str
    modified_response: Optional[str] = None
    confidence_adjustment: float = 0.0
    suspicious_numbers: List[str] = field(default_factory=list)


# ── Patterns that indicate potentially hallucinated numbers ────────────────
# These patterns detect specific financial numbers that MUST come from extraction
_SUSPICIOUS_NUMBER_PATTERNS = [
    r'copay(?:ment)?\s+(?:of\s+)?(\d+)\s*%',
    r'sub[-\s]?limit\s+(?:of\s+)?₹?\s*(\d[\d,]*)',
    r'deductible\s+(?:of\s+)?₹?\s*(\d[\d,]*)',
    r'(?:annual\s+)?premium\s+(?:of\s+)?₹?\s*(\d[\d,]*)',
    r'sum\s+insured\s+(?:of\s+)?₹?\s*(\d[\d,]*)',
    r'waiting\s+period\s+(?:of\s+)?(\d+)\s+(?:years?|months?)',
    r'network\s+(?:of\s+)?(\d[\d,]*)\s+hospitals?',
]

# ── Domain-aware number ranges (for context-sensitive suspicious number detection)
# CSR (Claim Settlement Ratio) should be 50-100%
# Premiums: health ₹3K-5L, life ₹1K-50L, motor ₹500-10L
# Sum Insured: health ₹1L-5Cr, life ₹50K-50Cr, motor ₹10K-1Cr
_DOMAIN_RANGES = {
    "csr": {
        "pattern": r'(?:claim\s+settlement\s+ratio|csr)\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
        "range": (50.0, 100.0),
        "label": "CSR",
    },
    "copay": {
        "pattern": r'copay(?:ment)?\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
        "range": (0.0, 50.0),
        "label": "Copay percentage",
    },
    "ncb": {
        "pattern": r'(?:no\s+claim\s+bonus|ncb)\s*(?:of\s+)?(\d+(?:\.\d+)?)\s*%',
        "range": (0.0, 65.0),
        "label": "NCB percentage",
    },
}

# ── Phrase patterns indicating confident assertions ─────────────────────────
_CONFIDENT_ASSERTION_MARKERS = [
    "your policy has",
    "your copay is",
    "your premium is",
    "your sum insured is",
    "your deductible is",
    "your waiting period is",
    "this policy covers",
    "your policy excludes",
]

# ── Safe uncertainty phrases (these indicate agent is being honest) ────────
_UNCERTAINTY_PHRASES = [
    "i couldn't find",
    "not found in your document",
    "i don't have information",
    "please verify",
    "based on available data",
    "i believe",
    "i'm not certain",
    "recommend verifying",
    "i'd recommend checking",
]

def check_hallucination(
    response: str,
    sources: List[Dict[str, Any]],
    confidence: float,
) -> HallucinationCheckResult:
    """
    Check response for potential hallucinations.

    Returns HallucinationCheckResult with:
    - passed: bool
    - reason: explanation
    - modified_response: response with uncertainty qualifiers added (if needed)
    """
    response_lower = response.lower()

    # ── Check 1: Confidence threshold ─────────────────────────────────────
    from hibiscus.config import settings as _settings
    _low_threshold = _settings.confidence_threshold_low
    if confidence < _low_threshold:
        return HallucinationCheckResult(
            passed=False,
            reason=f"Response confidence too low ({confidence:.0%}, threshold {_low_threshold:.0%})",
            modified_response=_add_low_confidence_header(response),
            confidence_adjustment=-0.1,
        )

    # ── Check 2: Domain-aware suspicious number detection ─────────────────
    suspicious_numbers: List[str] = []
    for domain_key, domain_info in _DOMAIN_RANGES.items():
        for match in re.finditer(domain_info["pattern"], response_lower):
            try:
                value = float(match.group(1))
                lo, hi = domain_info["range"]
                if value < lo or value > hi:
                    suspicious_numbers.append(
                        f"{domain_info['label']} {value}% outside expected range [{lo}-{hi}%]"
                    )
            except (ValueError, IndexError):
                pass

    if suspicious_numbers:
        return HallucinationCheckResult(
            passed=False,
            reason=f"Domain-implausible numbers detected: {suspicious_numbers}",
            modified_response=_add_verification_caveat(response),
            confidence_adjustment=-0.2,
            suspicious_numbers=suspicious_numbers,
        )

    # ── Check 3: Specific number claims without document source ───────────
    source_types = [s.get("type", "unknown") for s in sources]
    has_doc_source = "document_extraction" in source_types or "knowledge_graph" in source_types

    if not has_doc_source:
        # Check if response makes specific number claims
        for pattern in _SUSPICIOUS_NUMBER_PATTERNS:
            matches = re.findall(pattern, response_lower)
            if matches:
                # Numbers found in response without document grounding
                return HallucinationCheckResult(
                    passed=False,
                    reason=f"Specific financial numbers without document source: {matches}",
                    modified_response=_add_verification_caveat(response),
                    confidence_adjustment=-0.15,
                    suspicious_numbers=[str(m) for m in matches],
                )

    # ── Check 4: Confident assertions about specific policy details ────────
    has_confident_assertions = any(
        marker in response_lower
        for marker in _CONFIDENT_ASSERTION_MARKERS
    )

    if has_confident_assertions and not has_doc_source and confidence < 0.70:
        return HallucinationCheckResult(
            passed=False,
            reason="Confident assertions about policy details without document source",
            modified_response=_add_verification_caveat(response),
        )

    # ── Check 5: Is the response already expressing appropriate uncertainty? ──
    if confidence < 0.70:
        has_uncertainty_phrase = any(
            phrase in response_lower
            for phrase in _UNCERTAINTY_PHRASES
        )
        if not has_uncertainty_phrase and has_confident_assertions:
            # Add uncertainty qualifiers
            return HallucinationCheckResult(
                passed=True,  # Not a failure, just adjustment
                reason="Added uncertainty qualifier for medium confidence",
                modified_response=_add_caveat_prefix(response, confidence),
            )

    return HallucinationCheckResult(
        passed=True,
        reason="Response passed hallucination check",
        modified_response=response,
    )


def _add_low_confidence_header(response: str) -> str:
    return (
        "⚠️ *Note: I'm not confident about all details in this response. "
        "Please verify with your insurer or policy document.*\n\n"
        + response
    )


def _add_verification_caveat(response: str) -> str:
    caveat = (
        "\n\n---\n"
        "*Note: Specific numbers above are based on general knowledge and may not "
        "reflect your actual policy. Please upload your policy document for accurate, "
        "document-grounded analysis.*"
    )
    return response + caveat


def _add_caveat_prefix(response: str, confidence: float) -> str:
    if confidence >= 0.60:
        prefix = "Based on available information: "
    else:
        prefix = "I believe (please verify): "
    return prefix + response
