"""
V2 Response Parser for PRD v2 ConfidenceField extraction format.

Parses LLM responses where every field is {value, source_page, confidence}.
Uses the same recovery strategy as the v1 parser but understands the nested
ConfidenceField structure.
"""
import json
import re
import logging

logger = logging.getLogger(__name__)


def _strip_markdown(text: str) -> str:
    """Remove markdown code block wrappers and extract JSON object."""
    text = re.sub(r'^```(?:json|JSON)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    text = text.strip()
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        text = json_match.group(0)
    return text


def _fix_json(text: str) -> str:
    """Fix common JSON issues: trailing commas, unclosed brackets."""
    fixed = re.sub(r',\s*([}\]])', r'\1', text)
    open_braces = fixed.count('{') - fixed.count('}')
    open_brackets = fixed.count('[') - fixed.count(']')
    if open_brackets > 0:
        fixed += ']' * open_brackets
    if open_braces > 0:
        fixed += '}' * open_braces
    return fixed


def parse_v2_extraction_response(analysis_text: str) -> dict:
    """Parse a PRD v2 extraction response (ConfidenceField format).

    The LLM returns JSON where each field is:
        {"value": <val>, "source_page": <int|null>, "confidence": <float>}

    This parser attempts:
    1. Direct JSON parse
    2. Fix common JSON issues
    3. Return partial result if possible

    Args:
        analysis_text: Raw LLM response text.

    Returns:
        Dict of field_name -> ConfidenceField dicts.
        On total failure returns empty dict.
    """
    if not analysis_text:
        return {}

    analysis_text = analysis_text.strip()
    logger.info(f"V2 extraction response (first 200 chars): {analysis_text[:200]}")

    cleaned = _strip_markdown(analysis_text)

    # Attempt 1: Direct parse
    try:
        parsed = json.loads(cleaned)
        logger.info(f"V2 extraction parsed successfully ({len(parsed)} top-level fields)")
        return parsed
    except json.JSONDecodeError as e:
        logger.warning(f"V2 JSON parse error: {e}. Attempting recovery...")

    # Attempt 2: Fix common issues
    fixed = _fix_json(cleaned)
    try:
        parsed = json.loads(fixed)
        logger.info(f"V2 extraction recovered ({len(parsed)} fields)")
        return parsed
    except json.JSONDecodeError:
        logger.warning("V2 JSON recovery failed")

    # Attempt 3: Try to salvage whatever we can
    # Look for individual field patterns: "fieldName": {"value": ..., "confidence": ...}
    salvaged = {}
    # Match: "key": {"value": <something>, ...}
    field_pattern = r'"(\w+)"\s*:\s*\{\s*"value"\s*:\s*((?:"[^"]*"|\d+(?:\.\d+)?|true|false|null|\[.*?\]|\{.*?\}))\s*,\s*"source_page"\s*:\s*(\d+|null)\s*,\s*"confidence"\s*:\s*(\d+(?:\.\d+)?)\s*\}'
    for match in re.finditer(field_pattern, analysis_text, re.DOTALL):
        field_name = match.group(1)
        raw_value = match.group(2)
        source_page = match.group(3)
        confidence = match.group(4)
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value.strip('"')
        salvaged[field_name] = {
            "value": value,
            "source_page": int(source_page) if source_page != "null" else None,
            "confidence": float(confidence),
        }

    if salvaged:
        logger.info(f"V2 extraction salvaged {len(salvaged)} fields via regex")
    else:
        logger.error("V2 extraction: total failure, returning empty dict")

    return salvaged
