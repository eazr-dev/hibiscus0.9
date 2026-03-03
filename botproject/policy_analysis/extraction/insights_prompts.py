"""
Insights / Recommendations Prompt Templates for Policy Analysis

Contains the prompt builder for generating comprehensive policy insights
including key benefits, exclusions, concerns, strengths, and suggested
improvements from the extracted policy data.
"""
import logging

logger = logging.getLogger(__name__)


# System prompt used for the insights LLM call
INSIGHTS_SYSTEM_PROMPT = (
    "You are a senior insurance advisor. Extract specific policy insights from the document. "
    "Return ONLY valid JSON without markdown or explanation."
)


def build_insights_prompt(
    policy_type: str,
    extracted_data: dict,
    user_age: int,
    extracted_text: str,
) -> str:
    """
    Build the comprehensive policy insights prompt for DeepSeek.

    Args:
        policy_type: The detected policy type (e.g. "health", "motor").
        extracted_data: The dict returned by the extraction step.
        user_age: Calculated age of the policy holder.
        extracted_text: The raw text extracted from the policy document.

    Returns:
        The fully-formed insights prompt string ready for the LLM.
    """
    policy_insights_prompt = f"""
You are an expert insurance policy analyst. Analyze this {policy_type} insurance policy and extract DETAILED insights.

POLICY INFORMATION:
- Insurance Provider: {extracted_data.get('insuranceProvider', 'Unknown')}
- Policy Type: {policy_type}
- Sum Insured/IDV: Rs.{(extracted_data.get('coverageAmount') or 0):,}
- Premium: Rs.{(extracted_data.get('premium') or 0):,}
- Policy Holder Age: {user_age} years

POLICY DOCUMENT (first 12000 chars):
{extracted_text[:12000]}

Analyze the policy and return a JSON object with these sections:

{{
  "keyBenefits": [
    // List 5-8 SPECIFIC benefits from THIS policy (not generic)
    // Format: "Benefit name: Specific detail from policy"
    // Examples: "Cashless at 16000+ hospitals", "No room rent capping", "100% sum insured restoration"
  ],
  "keyExclusions": [
    // List 4-6 IMPORTANT exclusions that will affect claims
    // Format: "Exclusion: Impact on policyholder"
    // Examples: "Pre-existing diseases: 4-year waiting period", "Cosmetic surgery: Not covered"
  ],
  "keyConcerns": [
    // List 3-5 concerns or limitations found in THIS policy
    // Be specific to the actual policy terms
    // Examples: "Room rent limit of 1% of SI will reduce claim payout", "Co-pay of 20% applicable"
  ],
  "policyStrengths": [
    // List 3-4 strong points of this policy
    // Examples: "No sub-limits on most treatments", "Includes AYUSH coverage", "Lifetime renewal guarantee"
  ],
  "suggestedImprovements": [
    // List 2-4 specific improvements based on policy analysis
    // Format: {{"suggestion": "What to do", "reason": "Why it's important", "priority": "high/medium/low"}}
  ]
}}

IMPORTANT:
- Be SPECIFIC to this policy - extract actual terms, numbers, limits from the document
- Don't give generic benefits/exclusions - cite actual policy terms
- For concerns, identify actual limitations that will impact claims
- Return ONLY valid JSON without explanation"""

    return policy_insights_prompt
