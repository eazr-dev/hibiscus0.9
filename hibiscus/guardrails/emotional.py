"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Emotional guardrail — detects distress signals, adjusts tone, suggests professional help.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class EmotionalCheckResult:
    passed: bool
    emotional_state: str          # From HibiscusState (neutral|curious|concerned|distressed|urgent|frustrated)
    empathy_prefix: str           # Prepend to response if distressed/urgent/frustrated (empty if neutral)
    escalate_to_claude: bool      # True for distressed/urgent — hint to use Tier 3
    reason: str
    modified_response: Optional[str] = None


# ── Empathy prefix pool (tone-matched) ────────────────────────────────────────

_EMPATHY_PREFIXES = {
    "distressed": (
        "I'm truly sorry to hear this — I can imagine how stressful this must be. "
        "Let me help you navigate this step by step.\n\n"
    ),
    "urgent": (
        "I understand this is urgent. Here are the most important steps you should take right now:\n\n"
    ),
    "frustrated": (
        "I understand this isn't the experience you expected, and I'm sorry for that. "
        "Let me be direct and clear:\n\n"
    ),
}

# ── Empathy phrases that indicate response already leads with empathy ──────────
_EMPATHY_ALREADY_PRESENT = [
    "i'm sorry",
    "i'm truly sorry",
    "i understand this",
    "i understand how",
    "i can imagine",
    "this must be",
    "that must be",
    "yeh sunke",          # Hinglish: "hearing this"
    "bahut mushkil",      # Hinglish: "very difficult"
    "i know this is hard",
    "i know how difficult",
    "my deepest sympathies",
    "i hear you",
]

# ── Defensive language patterns that frustrate users ──────────────────────────
_DEFENSIVE_PATTERNS = [
    (r"\bi cannot\b", "I may not be able to"),
    (r"\bi can't\b", "I may not be able to"),
    (r"\bthat's not possible\b", "that may be challenging, though let's explore options"),
    (r"\bit's not possible\b", "it may be challenging, though let's explore options"),
    (r"\bi don't have access to\b", "I don't currently have access to"),
    (r"\bthere's nothing i can do\b", "let me see what options are available"),
]


def check_emotional(
    response: str,
    emotional_state: str,
    intent: str = "general_chat",
) -> EmotionalCheckResult:
    """
    Adapt response tone for user's emotional state.

    Args:
        response: The LLM-generated response to check/modify
        emotional_state: From HibiscusState (neutral|curious|concerned|distressed|urgent|frustrated)
        intent: The classified intent (used for context)

    Returns:
        EmotionalCheckResult — always passes (this guard modifies, never blocks)
    """
    response_lower = response.lower()

    # ── Pass through if emotional state doesn't require adaptation ────────────
    if emotional_state in ("neutral", "curious", "concerned"):
        return EmotionalCheckResult(
            passed=True,
            emotional_state=emotional_state,
            empathy_prefix="",
            escalate_to_claude=False,
            reason=f"Emotional state '{emotional_state}' — no adaptation needed",
            modified_response=response,
        )

    # ── Distressed / Urgent: lead with empathy ────────────────────────────────
    if emotional_state in ("distressed", "urgent"):
        empathy_prefix = _EMPATHY_PREFIXES.get(emotional_state, _EMPATHY_PREFIXES["distressed"])

        # Check if response already leads with empathy — don't double up
        already_empathetic = any(
            phrase in response_lower[:200]  # Only check first 200 chars (the lead)
            for phrase in _EMPATHY_ALREADY_PRESENT
        )

        if already_empathetic:
            return EmotionalCheckResult(
                passed=True,
                emotional_state=emotional_state,
                empathy_prefix="",
                escalate_to_claude=True,  # Still flag for Claude escalation
                reason=f"Distressed user — response already leads with empathy",
                modified_response=response,
            )

        modified = empathy_prefix + response
        return EmotionalCheckResult(
            passed=True,
            emotional_state=emotional_state,
            empathy_prefix=empathy_prefix,
            escalate_to_claude=True,
            reason=f"Distressed/urgent user — prepended empathy prefix",
            modified_response=modified,
        )

    # ── Frustrated: soften defensive language ─────────────────────────────────
    if emotional_state == "frustrated":
        empathy_prefix = _EMPATHY_PREFIXES["frustrated"]
        modified = response

        # Apply defensive language softening
        for pattern, replacement in _DEFENSIVE_PATTERNS:
            modified = re.sub(pattern, replacement, modified, flags=re.IGNORECASE)

        # Prepend acknowledgment unless response already acknowledges
        already_acknowledges = any(
            phrase in response_lower[:200]
            for phrase in _EMPATHY_ALREADY_PRESENT
        )
        if not already_acknowledges:
            modified = empathy_prefix + modified

        return EmotionalCheckResult(
            passed=True,
            emotional_state=emotional_state,
            empathy_prefix=empathy_prefix if not already_acknowledges else "",
            escalate_to_claude=False,
            reason="Frustrated user — softened language and prepended acknowledgment",
            modified_response=modified,
        )

    # ── Fallback (unknown emotional state) ────────────────────────────────────
    return EmotionalCheckResult(
        passed=True,
        emotional_state=emotional_state,
        empathy_prefix="",
        escalate_to_claude=False,
        reason=f"Unknown emotional state '{emotional_state}' — no modification",
        modified_response=response,
    )
