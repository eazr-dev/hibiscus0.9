"""
Policy Analysis - Extraction Subpackage

Contains modules for LLM-based policy data extraction:

- prompts: Main extraction prompt template builder
- gap_analysis_prompts: Gap analysis prompt templates per policy type
- insights_prompts: Policy insights/recommendations prompt templates
- response_parser: JSON parsing and recovery logic for LLM responses
- llm_client: DeepSeek API call wrappers and high-level orchestration helpers
"""

from policy_analysis.extraction.v1_prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_prompt,
)
from policy_analysis.extraction.v2_response_parser import parse_v2_extraction_response
from policy_analysis.extraction.prompts.prompt_builder import build_v2_extraction_prompt
from policy_analysis.extraction.gap_analysis_prompts import (
    GAP_ANALYSIS_SYSTEM_PROMPT,
    get_policy_type_context,
    build_gap_analysis_prompt,
)
from policy_analysis.extraction.insights_prompts import (
    INSIGHTS_SYSTEM_PROMPT,
    build_insights_prompt,
)
from policy_analysis.extraction.response_parser import (
    parse_extraction_response,
    parse_gap_analysis_response,
    parse_insights_response,
    get_default_extracted_data,
    strip_markdown_json,
    strip_markdown_json_array,
)
from policy_analysis.extraction.llm_client import (
    call_deepseek_extraction,
    call_deepseek_gap_analysis,
    call_deepseek_insights,
    extract_policy_data,
    extract_gap_analysis,
    extract_policy_insights,
)

__all__ = [
    # Prompts
    "EXTRACTION_SYSTEM_PROMPT",
    "build_extraction_prompt",
    "GAP_ANALYSIS_SYSTEM_PROMPT",
    "get_policy_type_context",
    "build_gap_analysis_prompt",
    "INSIGHTS_SYSTEM_PROMPT",
    "build_insights_prompt",
    # Response parsing
    "parse_extraction_response",
    "parse_gap_analysis_response",
    "parse_insights_response",
    "get_default_extracted_data",
    "strip_markdown_json",
    "strip_markdown_json_array",
    # LLM client
    "call_deepseek_extraction",
    "call_deepseek_gap_analysis",
    "call_deepseek_insights",
    "extract_policy_data",
    "extract_gap_analysis",
    "extract_policy_insights",
    # V2 extraction
    "parse_v2_extraction_response",
    "build_v2_extraction_prompt",
]
