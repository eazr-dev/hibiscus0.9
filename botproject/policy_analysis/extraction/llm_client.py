"""
LLM Client Wrappers for Policy Extraction

Provides thin wrapper functions around the DeepSeek API calls used during
policy extraction, gap analysis, and insights generation. Each function
is designed to be called via ``asyncio.to_thread()`` from the async
endpoint handler.

The ``deepseek_client`` (an ``openai.OpenAI`` instance pointed at
``https://api.deepseek.com``) must be passed in by the caller -- this
module does NOT create its own client so that the existing initialization
in ``routers/chat.py`` remains the single source of truth.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)

# Timeout for DeepSeek API calls (seconds)
_LLM_TIMEOUT = 45


# ==================== PROMPT IMPORTS ====================
from policy_analysis.extraction.v1_prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_prompt,
)
from policy_analysis.extraction.gap_analysis_prompts import (
    GAP_ANALYSIS_SYSTEM_PROMPT,
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
)


# ==================== RAW LLM CALL WRAPPERS ====================
# These are synchronous functions meant to be dispatched with
# ``await asyncio.to_thread(fn)`` from an async context.


def call_deepseek_extraction(deepseek_client, extraction_prompt: str):
    """
    Call DeepSeek chat completions for policy data extraction.

    Uses ``deepseek-chat`` model with temperature=0.0 for deterministic
    JSON extraction. Max tokens set to 4000 to prevent truncation of
    large policy schemas.

    Args:
        deepseek_client: An ``openai.OpenAI`` client configured for DeepSeek.
        extraction_prompt: The fully-formed extraction prompt string.

    Returns:
        The raw ``ChatCompletion`` response object.
    """
    return deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": EXTRACTION_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": extraction_prompt
            }
        ],
        temperature=0.0,
        max_tokens=4000  # Increased from 2000 to prevent truncation
    )


def call_deepseek_gap_analysis(deepseek_client, gap_analysis_prompt: str):
    """
    Call DeepSeek chat completions for gap analysis.

    Uses ``deepseek-chat`` model with temperature=0.2 for slightly more
    creative but still accurate analysis. Max tokens set to 2500 for
    detailed analysis output.

    Args:
        deepseek_client: An ``openai.OpenAI`` client configured for DeepSeek.
        gap_analysis_prompt: The fully-formed gap analysis prompt string.

    Returns:
        The raw ``ChatCompletion`` response object.
    """
    return deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": GAP_ANALYSIS_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": gap_analysis_prompt
            }
        ],
        temperature=0.2,  # Lower temperature for more accurate analysis
        max_tokens=2500  # More tokens for detailed analysis
    )


def call_deepseek_insights(deepseek_client, insights_prompt: str):
    """
    Call DeepSeek chat completions for policy insights generation.

    Uses ``deepseek-chat`` model with temperature=0.2 and max_tokens=2000.

    Args:
        deepseek_client: An ``openai.OpenAI`` client configured for DeepSeek.
        insights_prompt: The fully-formed insights prompt string.

    Returns:
        The raw ``ChatCompletion`` response object.
    """
    return deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": INSIGHTS_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": insights_prompt
            }
        ],
        temperature=0.2,
        max_tokens=2000
    )


# ==================== HIGH-LEVEL ORCHESTRATION HELPERS ====================
# These async helpers combine prompt building, LLM call, and response
# parsing into single awaitable calls for use by the upload endpoint.


async def extract_policy_data(deepseek_client, extracted_text: str) -> dict:
    """
    End-to-end policy data extraction: build prompt -> call LLM -> parse response.

    Args:
        deepseek_client: An ``openai.OpenAI`` client configured for DeepSeek.
        extracted_text: The raw text extracted from the policy PDF/images.

    Returns:
        A dict of extracted policy fields. May be partial on truncation/error.

    Raises:
        Exception: Propagated from the LLM call if there is a network or API error.
    """
    extraction_prompt = build_extraction_prompt(extracted_text)

    try:
        analysis_response = await asyncio.wait_for(
            asyncio.to_thread(call_deepseek_extraction, deepseek_client, extraction_prompt),
            timeout=_LLM_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error(f"DeepSeek extraction timed out after {_LLM_TIMEOUT}s")
        return get_default_extracted_data()

    analysis_text = analysis_response.choices[0].message.content.strip()
    extracted_data = parse_extraction_response(analysis_text)
    return extracted_data


async def extract_gap_analysis(
    deepseek_client,
    policy_type: str,
    extracted_data: dict,
    name: str,
    gender: str,
    user_age: int,
    extracted_text: str,
) -> list:
    """
    End-to-end gap analysis: build prompt -> call LLM -> parse response.

    Args:
        deepseek_client: An ``openai.OpenAI`` client configured for DeepSeek.
        policy_type: The detected policy type.
        extracted_data: The dict returned by the extraction step.
        name: Policy holder name.
        gender: Policy holder gender.
        user_age: Calculated age of the policy holder.
        extracted_text: The raw text extracted from the policy document.

    Returns:
        A list of gap analysis dicts. Returns empty list on failure.
    """
    gap_prompt = build_gap_analysis_prompt(
        policy_type, extracted_data, name, gender, user_age, extracted_text
    )

    try:
        gap_response = await asyncio.wait_for(
            asyncio.to_thread(call_deepseek_gap_analysis, deepseek_client, gap_prompt),
            timeout=_LLM_TIMEOUT,
        )
        gap_text = gap_response.choices[0].message.content.strip()
        gaps = parse_gap_analysis_response(gap_text)
        return gaps
    except asyncio.TimeoutError:
        logger.error(f"DeepSeek gap analysis timed out after {_LLM_TIMEOUT}s")
        return []
    except Exception as e:
        logger.error(f"Error in gap analysis: {e}")
        return []


async def extract_policy_insights(
    deepseek_client,
    policy_type: str,
    extracted_data: dict,
    user_age: int,
    extracted_text: str,
) -> dict:
    """
    End-to-end policy insights extraction: build prompt -> call LLM -> parse response.

    Updates ``extracted_data`` in-place with enhanced keyBenefits and exclusions
    if the LLM returns them.

    Args:
        deepseek_client: An ``openai.OpenAI`` client configured for DeepSeek.
        policy_type: The detected policy type.
        extracted_data: The dict returned by the extraction step (mutated in-place).
        user_age: Calculated age of the policy holder.
        extracted_text: The raw text extracted from the policy document.

    Returns:
        A dict with keyBenefits, keyExclusions, keyConcerns, policyStrengths,
        and suggestedImprovements. Returns default structure on failure.
    """
    # Default insights structure (fallback)
    enhanced_insights = {
        "keyBenefits": extracted_data.get("keyBenefits") or [],
        "keyExclusions": extracted_data.get("exclusions") or [],
        "keyConcerns": [],
        "policyStrengths": [],
        "suggestedImprovements": []
    }

    try:
        insights_prompt = build_insights_prompt(
            policy_type, extracted_data, user_age, extracted_text
        )

        insights_response = await asyncio.wait_for(
            asyncio.to_thread(call_deepseek_insights, deepseek_client, insights_prompt),
            timeout=_LLM_TIMEOUT,
        )
        insights_text = insights_response.choices[0].message.content.strip()

        parsed_insights = parse_insights_response(insights_text)

        if parsed_insights:
            # Update extracted_data with enhanced insights
            if parsed_insights.get("keyBenefits"):
                extracted_data["keyBenefits"] = parsed_insights["keyBenefits"]
            if parsed_insights.get("keyExclusions"):
                extracted_data["exclusions"] = parsed_insights["keyExclusions"]

            enhanced_insights = parsed_insights
            logger.info(
                f"Generated comprehensive policy insights with "
                f"{len(enhanced_insights.get('keyBenefits', []))} benefits, "
                f"{len(enhanced_insights.get('keyConcerns', []))} concerns"
            )

    except asyncio.TimeoutError:
        logger.error(f"DeepSeek insights timed out after {_LLM_TIMEOUT}s")
    except Exception as e:
        logger.error(f"Error generating policy insights: {e}")

    return enhanced_insights
