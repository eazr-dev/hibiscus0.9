"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Emotional router — tone adjustment and escalation logic for emotional states.

NOTE: Emotional state *detection* is handled by intent_classification._fast_classify().
This module provides tone instructions and escalation decisions based on the detected state.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Optional


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
