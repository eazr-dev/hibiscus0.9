"""
Prompt builder that routes to the correct type-specific extraction prompt.

Given a detected policy type string, returns the appropriate PRD v2
extraction prompt and system prompt.
"""
import logging

from policy_analysis.extraction.prompts.health_prompt import (
    V2_SYSTEM_PROMPT as HEALTH_SYSTEM,
    build_health_extraction_prompt,
)
from policy_analysis.extraction.prompts.motor_prompt import (
    V2_SYSTEM_PROMPT as MOTOR_SYSTEM,
    build_motor_extraction_prompt,
)
from policy_analysis.extraction.prompts.life_prompt import (
    V2_SYSTEM_PROMPT as LIFE_SYSTEM,
    build_life_extraction_prompt,
)
from policy_analysis.extraction.prompts.pa_prompt import (
    V2_SYSTEM_PROMPT as PA_SYSTEM,
    build_pa_extraction_prompt,
)
from policy_analysis.extraction.prompts.travel_prompt import (
    V2_SYSTEM_PROMPT as TRAVEL_SYSTEM,
    build_travel_extraction_prompt,
)

logger = logging.getLogger(__name__)

# Maximum characters for extraction text (~12K tokens at ~4 chars/token)
# Full text is still used for verification (Check 5) — only extraction is truncated
_MAX_EXTRACTION_CHARS = 48000

# Keywords for type detection (matches existing logic in policy_upload.py)
_MOTOR_KEYWORDS = {"motor", "car", "vehicle", "auto", "two wheeler", "bike"}
_HEALTH_KEYWORDS = {"health", "mediclaim", "medical"}
_LIFE_KEYWORDS = {"life", "term", "endowment", "ulip", "whole life", "money back"}
_PA_KEYWORDS = {"accidental", "accident", "pa", "personal accident"}
_TRAVEL_KEYWORDS = {"travel"}


def _detect_category(detected_policy_type: str) -> str:
    """Map the raw detected_policy_type string to a canonical category.

    Returns one of: health, motor, life, pa, travel, unknown.

    Priority order: exact match first, then motor (most specific keywords),
    travel, PA, life, health (broadest, checked last to avoid false matches).
    """
    t = (detected_policy_type or "").lower().strip()

    # Exact canonical match (from identify_policy_type_deepseek)
    if t in ("health", "motor", "life", "pa", "travel"):
        return t

    # Check specificity order: motor/travel/PA first (narrower keywords),
    # then life/health (broader keywords that can false-match)
    if any(kw in t for kw in _MOTOR_KEYWORDS):
        return "motor"
    if any(kw in t for kw in _TRAVEL_KEYWORDS):
        return "travel"
    if any(kw in t for kw in _PA_KEYWORDS):
        return "pa"
    if any(kw in t for kw in _LIFE_KEYWORDS):
        return "life"
    if any(kw in t for kw in _HEALTH_KEYWORDS):
        return "health"
    return "unknown"


def build_v2_extraction_prompt(
    extracted_text: str,
    detected_policy_type: str,
) -> tuple[str, str, str]:
    """Build a PRD v2 type-specific extraction prompt.

    Args:
        extracted_text: Document text with [Page N] markers.
        detected_policy_type: Raw policy type string from detection step.

    Returns:
        Tuple of (system_prompt, user_prompt, category).
        If type is unknown, falls back to health prompt.
    """
    category = _detect_category(detected_policy_type)

    # Truncate very large PDFs to prevent token overflow / slow extraction
    if len(extracted_text) > _MAX_EXTRACTION_CHARS:
        logger.warning(
            f"Extracted text ({len(extracted_text)} chars) exceeds limit "
            f"({_MAX_EXTRACTION_CHARS}), truncating for extraction"
        )
        extracted_text = extracted_text[:_MAX_EXTRACTION_CHARS] + "\n\n[... text truncated for extraction ...]"

    builders = {
        "health": (HEALTH_SYSTEM, build_health_extraction_prompt),
        "motor": (MOTOR_SYSTEM, build_motor_extraction_prompt),
        "life": (LIFE_SYSTEM, build_life_extraction_prompt),
        "pa": (PA_SYSTEM, build_pa_extraction_prompt),
        "travel": (TRAVEL_SYSTEM, build_travel_extraction_prompt),
    }

    if category in builders:
        system_prompt, builder_fn = builders[category]
        logger.info(f"Using PRD v2 {category} extraction prompt")
        return system_prompt, builder_fn(extracted_text), category

    # Fallback to health (most common type) for unknown
    logger.warning(
        f"Unknown policy type '{detected_policy_type}', falling back to health prompt"
    )
    return HEALTH_SYSTEM, build_health_extraction_prompt(extracted_text), "health"
