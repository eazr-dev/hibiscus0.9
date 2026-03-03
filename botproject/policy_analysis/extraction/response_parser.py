"""
Response Parser for LLM Extraction Outputs

Contains JSON parsing and recovery logic that processes DeepSeek responses.
Handles malformed JSON, truncated responses, markdown code block stripping,
and regex-based field extraction as a last resort.
"""
import json
import re
import logging

logger = logging.getLogger(__name__)


def strip_markdown_json(text: str) -> str:
    """
    Remove markdown code block wrappers (```json ... ```) from LLM output
    and extract the JSON object.

    Args:
        text: Raw LLM response text.

    Returns:
        Cleaned text with markdown wrappers removed and the outermost
        JSON object extracted if found.
    """
    # Handle ```json, ```JSON, ``` at start and end
    text = re.sub(r'^```(?:json|JSON)?\s*\n?', '', text)
    text = re.sub(r'\n?```\s*$', '', text)
    text = text.strip()

    # Try to extract JSON object from response
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        text = json_match.group(0)

    return text


def strip_markdown_json_array(text: str) -> str:
    """
    Remove markdown code block wrappers and extract a JSON array from LLM output.

    Args:
        text: Raw LLM response text.

    Returns:
        Cleaned text with markdown wrappers removed and the outermost
        JSON array extracted if found.
    """
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()

    # Try to extract JSON array from response
    json_array_match = re.search(r'\[[\s\S]*\]', text)
    if json_array_match:
        text = json_array_match.group(0)

    return text


def parse_extraction_response(analysis_text: str) -> dict:
    """
    Parse the LLM extraction response into a Python dict.

    Implements a multi-tier recovery strategy:
    1. Direct JSON parse after stripping markdown wrappers
    2. Fix trailing commas and unclosed brackets/braces
    3. Last-resort regex extraction of individual fields

    Args:
        analysis_text: The raw text from the LLM response
                       (``response.choices[0].message.content``).

    Returns:
        A dict with extracted policy fields. May be partial if the
        response was truncated or malformed.

    Raises:
        No exceptions are raised; on total failure an empty dict with
        manually extracted fields (if any) is returned.
    """
    analysis_text = analysis_text.strip()
    logger.info(f"DeepSeek extraction response (first 200 chars): {analysis_text[:200]}")

    # Remove markdown code blocks if present (more robust regex)
    analysis_text = strip_markdown_json(analysis_text)

    # Try to parse JSON, with recovery for truncated responses
    try:
        extracted_data = json.loads(analysis_text)
        logger.info("Successfully extracted policy data with DeepSeek")
        return extracted_data
    except json.JSONDecodeError as json_err:
        logger.warning(f"JSON parse error: {json_err}. Attempting recovery...")

        # Try to fix common JSON issues
        # 1. Remove trailing commas before } or ]
        fixed_text = re.sub(r',\s*([}\]])', r'\1', analysis_text)

        # 2. Try to close unclosed arrays and objects
        open_braces = fixed_text.count('{') - fixed_text.count('}')
        open_brackets = fixed_text.count('[') - fixed_text.count(']')

        # Add missing closing brackets/braces
        if open_brackets > 0:
            fixed_text += ']' * open_brackets
        if open_braces > 0:
            fixed_text += '}' * open_braces

        # 3. Try to fix truncated strings - find last complete key-value pair
        try:
            extracted_data = json.loads(fixed_text)
            logger.info("Successfully recovered JSON after fixing")
            return extracted_data
        except json.JSONDecodeError:
            # Last resort: try to extract at least the basic fields
            logger.warning("JSON recovery failed, extracting basic fields manually")
            extracted_data = {}

            # Extract basic fields using regex
            patterns = {
                "policyNumber": r'"policyNumber"\s*:\s*"([^"]*)"',
                "insuranceProvider": r'"insuranceProvider"\s*:\s*"([^"]*)"',
                "policyType": r'"policyType"\s*:\s*"([^"]*)"',
                "coverageAmount": r'"coverageAmount"\s*:\s*(\d+)',
                "premium": r'"premium"\s*:\s*(\d+)',
                "premiumFrequency": r'"premiumFrequency"\s*:\s*"([^"]*)"',
                "startDate": r'"startDate"\s*:\s*"([^"]*)"',
                "endDate": r'"endDate"\s*:\s*"([^"]*)"',
                "policyHolderName": r'"policyHolderName"\s*:\s*"([^"]*)"',
                "uin": r'"uin"\s*:\s*"([^"]*)"',
                "productName": r'"productName"\s*:\s*"([^"]*)"',
            }

            for field, pattern in patterns.items():
                match = re.search(pattern, analysis_text)
                if match:
                    value = match.group(1)
                    # Convert numeric fields
                    if field in ["coverageAmount", "premium"]:
                        try:
                            value = int(value)
                        except ValueError:
                            value = 0
                    extracted_data[field] = value

            # Extract arrays (keyBenefits, exclusions, etc.)
            array_patterns = {
                "keyBenefits": r'"keyBenefits"\s*:\s*\[(.*?)\]',
                "exclusions": r'"exclusions"\s*:\s*\[(.*?)\]',
                "waitingPeriods": r'"waitingPeriods"\s*:\s*\[(.*?)\]',
                "criticalAreas": r'"criticalAreas"\s*:\s*\[(.*?)\]',
            }

            for field, pattern in array_patterns.items():
                match = re.search(pattern, analysis_text, re.DOTALL)
                if match:
                    try:
                        # Try to parse the array content
                        array_content = '[' + match.group(1) + ']'
                        extracted_data[field] = json.loads(array_content)
                    except json.JSONDecodeError:
                        # Extract strings manually
                        strings = re.findall(r'"([^"]*)"', match.group(1))
                        extracted_data[field] = strings

            if extracted_data:
                logger.info(f"Manually extracted {len(extracted_data)} fields from malformed JSON")

            return extracted_data


def parse_gap_analysis_response(gap_text: str) -> list:
    """
    Parse the LLM gap analysis response into a Python list of gap dicts.

    Args:
        gap_text: The raw text from the LLM response
                  (``response.choices[0].message.content``).

    Returns:
        A list of gap analysis dicts, each containing category, severity,
        description, recommendation, and estimatedCost. Returns empty list
        on parse failure.
    """
    gap_text = gap_text.strip()
    logger.info(f"DeepSeek gap analysis response (first 200 chars): {gap_text[:200]}")

    gap_text = strip_markdown_json_array(gap_text)

    try:
        gaps = json.loads(gap_text)
        logger.info(f"Generated {len(gaps)} coverage gap recommendations")
        return gaps
    except json.JSONDecodeError as je:
        logger.error(f"JSON decode error in gap analysis: {je}")
        logger.error(f"Failed to parse: {gap_text[:500]}")
        return []


def parse_insights_response(insights_text: str) -> dict:
    """
    Parse the LLM insights response into a Python dict.

    Args:
        insights_text: The raw text from the LLM response
                       (``response.choices[0].message.content``).

    Returns:
        A dict with keyBenefits, keyExclusions, keyConcerns, policyStrengths,
        and suggestedImprovements. Returns empty dict on parse failure.
    """
    insights_text = insights_text.strip()

    # Clean JSON response
    insights_text = strip_markdown_json(insights_text)

    try:
        parsed_insights = json.loads(insights_text)
        return parsed_insights
    except json.JSONDecodeError as je:
        logger.error(f"JSON decode error in policy insights: {je}")
        return {}


def get_default_extracted_data(policy_type: str, name: str) -> dict:
    """
    Return a default/fallback extracted data dict when LLM extraction fails entirely.

    Args:
        policy_type: The detected policy type.
        name: The policy holder name to use as fallback.

    Returns:
        A dict with empty/default values for all core extraction fields.
    """
    return {
        "policyNumber": "",
        "insuranceProvider": "",
        "policyType": policy_type,
        "coverageAmount": 0,
        "premium": 0,
        "premiumFrequency": "annually",
        "startDate": "",
        "endDate": "",
        "policyHolderName": name,
        "keyBenefits": [],
        "exclusions": [],
        "waitingPeriods": [],
        "criticalAreas": []
    }
