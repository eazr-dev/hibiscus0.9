"""
Type-specific extraction prompts for PRD v2.

Each prompt is focused on a single insurance type and requests
{value, source_page, confidence} per field.
"""
from policy_analysis.extraction.prompts.prompt_builder import build_v2_extraction_prompt

__all__ = ["build_v2_extraction_prompt"]
