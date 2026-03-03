"""
Hallucination Guard — PRIORITY ZERO GUARDRAIL
=============================================
Rule: Every factual claim must have a source.

Sources (in order of trust):
1. Document extraction (confidence 0.85-0.95)
2. Knowledge Graph (confidence 0.90+, pre-verified)
3. RAG retrieval (confidence = similarity × source trust)
4. Web search (confidence 0.60-0.80)
5. LLM reasoning only (confidence 0.30-0.50)
6. No source → NEVER present as fact

BEHAVIOR:
  confidence ≥ 0.85 → State as fact
  0.70 ≤ confidence < 0.85 → Add caveat
  0.50 ≤ confidence < 0.70 → Explicit uncertainty
  confidence < 0.50 → Don't state, ask user

SPECIAL RULE FOR NUMBERS:
Copay %, sub-limits, premiums, sum insured → MUST come from extraction or KG.
If LLM-only → flag and don't present as specific numbers.
"""
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class HallucinationCheckResult:
    passed: bool
    reason: str
    modified_response: Optional[str] = None
    confidence_adjustment: float = 0.0


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

# ── Source type trust levels ───────────────────────────────────────────────
_SOURCE_TRUST = {
    "document_extraction": 0.90,
    "knowledge_graph": 0.92,
    "rag_retrieval": 0.75,
    "web_search": 0.65,
    "llm_reasoning": 0.45,
}


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
    if confidence < 0.30:
        return HallucinationCheckResult(
            passed=False,
            reason=f"Response confidence too low ({confidence:.0%})",
            modified_response=_add_low_confidence_header(response),
            confidence_adjustment=-0.1,
        )

    # ── Check 2: Specific number claims without document source ───────────
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
                )

    # ── Check 3: Confident assertions about specific policy details ────────
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

    # ── Check 4: Is the response already expressing appropriate uncertainty? ──
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
