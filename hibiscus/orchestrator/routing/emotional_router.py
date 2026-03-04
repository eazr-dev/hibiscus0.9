"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Emotional router — detects user sentiment to adjust response tone and agent selection.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Dict, Any, Optional
import re


# Emotional state keyword patterns
_DISTRESS_PATTERNS = [
    r'\b(hospital|hospitali[sz]ed|icu|critical|dying|emergency|accident)\b',
    r'\b(claim\s+rejected|denied|repudiated)\b',
    r'\b(passed\s+away|died|death|demise)\b',
    r'\b(cancer|heart\s+attack|stroke|surgery)\b',
]

_URGENT_PATTERNS = [
    r'\b(urgent|immediately|asap|deadline|expiring\s+today|lapsing)\b',
    r'\b(tomorrow|tonight|within\s+hours)\b',
]

_FRUSTRATED_PATTERNS = [
    r'\b(useless|pathetic|waste|terrible|horrible|worst)\b',
    r'\b(cheated|fraud|scam|lied|misleading)\b',
    r'\b(not\s+working|doesn.t\s+work|broken|wrong)\b',
    r'[!]{2,}',  # Multiple exclamation marks
]

_CONCERNED_PATTERNS = [
    r'\b(worried|confused|not\s+sure|help\s+me\s+understand)\b',
    r'\b(scared|anxious|nervous|unsure)\b',
]


def detect_emotional_state(message: str) -> str:
    """
    Detect the user's emotional state from their message.

    Returns: neutral | curious | concerned | distressed | urgent | frustrated
    """
    msg_lower = message.lower()

    # Check distress first (highest priority)
    for pattern in _DISTRESS_PATTERNS:
        if re.search(pattern, msg_lower):
            return "distressed"

    # Check urgency
    for pattern in _URGENT_PATTERNS:
        if re.search(pattern, msg_lower):
            return "urgent"

    # Check frustration
    for pattern in _FRUSTRATED_PATTERNS:
        if re.search(pattern, msg_lower):
            return "frustrated"

    # Check concern
    for pattern in _CONCERNED_PATTERNS:
        if re.search(pattern, msg_lower):
            return "concerned"

    # Check curiosity (educational questions)
    curiosity_markers = ["what is", "how does", "explain", "difference between", "what are"]
    for marker in curiosity_markers:
        if marker in msg_lower:
            return "curious"

    return "neutral"


def get_tone_instruction(emotional_state: str) -> Optional[str]:
    """
    Get tone adjustment instruction for the LLM based on emotional state.

    Returns None for neutral (no adjustment needed).
    """
    instructions = {
        "distressed": (
            "TONE: The user is in a stressful situation. "
            "Start with ONE empathetic sentence acknowledging their difficulty. "
            "Then provide clear, actionable steps. Keep it simple — don't overwhelm. "
            "End with an empowering statement about their rights."
        ),
        "urgent": (
            "TONE: The user has time pressure. "
            "Lead with the most important action item. "
            "Be direct and concise. Skip background context."
        ),
        "frustrated": (
            "TONE: The user is frustrated. "
            "Acknowledge their frustration briefly without being defensive. "
            "Be direct and solution-focused. "
            "Offer specific next steps."
        ),
        "concerned": (
            "TONE: The user is worried. "
            "Be reassuring but honest. "
            "Explain clearly without jargon. "
            "Help them understand their options."
        ),
        "curious": (
            "TONE: The user is learning. "
            "Use simple language with Indian examples. "
            "Analogies are helpful. "
            "Encourage further questions."
        ),
    }
    return instructions.get(emotional_state)


def should_escalate_emotional(emotional_state: str) -> bool:
    """Check if emotional state warrants Claude (Tier 3) escalation."""
    return emotional_state in ("distressed", "urgent")
