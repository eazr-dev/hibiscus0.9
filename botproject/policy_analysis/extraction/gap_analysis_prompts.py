"""
Gap Analysis Prompt Templates for Policy Analysis

Contains the policy-type-specific analysis frameworks and the main gap analysis
prompt builder. Covers Health, Motor, Life, Personal Accident, and Travel
insurance types with IRDAI-standard analysis criteria.
"""
import logging

logger = logging.getLogger(__name__)


# System prompt used for the gap analysis LLM call
GAP_ANALYSIS_SYSTEM_PROMPT = (
    "You are a certified insurance advisor (IRDAI licensed) with 15+ years experience. "
    "Analyze policies thoroughly and provide specific, actionable recommendations based on "
    "the actual policy document. Return ONLY valid JSON array without any explanation or markdown."
)


# ==================== POLICY TYPE CONTEXT TEMPLATES ====================

HEALTH_ANALYSIS_CONTEXT = """
HEALTH INSURANCE ANALYSIS FRAMEWORK:
- Sum Insured Adequacy: Check if SI >= Rs.10L (metro), Rs.5L (non-metro) per person
- Room Rent Limits: Sub-limits reduce claim payouts significantly (1% or 2% of SI limits are restrictive)
- Co-payment: Any mandatory co-pay (10-20%) reduces effective coverage
- Disease-wise Sub-limits: Cataract, joint replacement, AYUSH limits
- Waiting Periods: Initial (30 days), PED (2-4 years), specific diseases (2 years)
- No Claim Bonus: Check if NCB protection available
- Restoration Benefit: Full restoration vs partial
- Day Care Procedures: 500+ procedures covered?
- Pre/Post Hospitalization: 60/180 days is standard
- Network Hospitals: Access to quality hospitals
- Mental Health Coverage: Now mandatory by IRDAI
- Maternity Coverage: If applicable
- Critical Illness: Not covered in base health plan

COMMON HEALTH GAPS TO CHECK:
1. Room rent limit causing claim reduction
2. Co-payment reducing effective coverage
3. Sub-limits on specific diseases
4. Long waiting periods for PED
5. No NCB protection
6. Limited restoration benefit
7. Missing critical illness cover
8. No personal accident cover"""

MOTOR_ANALYSIS_CONTEXT = """
MOTOR INSURANCE ANALYSIS FRAMEWORK:
- IDV (Insured Declared Value): Should reflect current market value
- Zero Depreciation: Critical for new cars (< 5 years), saves 20-40% on claims
- Engine & Gearbox Protection: Covers hydrostatic lock damage
- NCB Protection: Protects accumulated no-claim bonus
- Return to Invoice: Covers gap between IDV and invoice value
- Roadside Assistance: 24/7 breakdown support
- Consumables Cover: Covers oil, nuts, bolts, bearings
- Tyre Cover: Expensive to replace, often excluded
- Key Replacement: Covers lost/stolen key
- Personal Accident Cover: Rs.15L mandatory for owner-driver

COMMON MOTOR GAPS TO CHECK:
1. No zero depreciation (major claim reduction)
2. Missing engine protection (hydrostatic lock not covered)
3. No NCB protection (lose years of bonus on one claim)
4. No roadside assistance
5. Missing consumables cover
6. Low PA cover (only Rs.15L statutory)
7. No return to invoice (gap on total loss)
8. No key replacement cover"""

LIFE_ANALYSIS_CONTEXT = """
LIFE INSURANCE ANALYSIS FRAMEWORK:
- Sum Assured Adequacy: Should be 10-15x annual income
- Premium Paying Term: Shorter PPT vs policy term
- Critical Illness Rider: Covers major illnesses
- Accidental Death Benefit: Additional cover for accidents
- Disability Rider: Income replacement on disability
- Waiver of Premium: Premiums waived on disability
- Terminal Illness Benefit: Early payout on terminal diagnosis
- Return of Premium: Gets premiums back on survival

COMMON LIFE GAPS TO CHECK:
1. Inadequate sum assured (< 10x income)
2. No critical illness rider
3. No accidental death benefit
4. Missing waiver of premium
5. No disability coverage
6. No terminal illness benefit
7. Policy term not aligned with liabilities
8. No inflation protection"""

PA_ANALYSIS_CONTEXT = """
PERSONAL ACCIDENT ANALYSIS FRAMEWORK:
- Sum Insured: Minimum 5-10x monthly income
- Accidental Death Benefit: 100% of SI
- Permanent Total Disability (PTD): 100% of SI
- Permanent Partial Disability (PPD): As per schedule
- Temporary Total Disability: Weekly benefit
- Medical Expenses: Post-accident medical costs
- Hospital Cash: Daily allowance during hospitalization

COMMON PA GAPS TO CHECK:
1. Low sum insured (should be 10x monthly income)
2. Limited PPD coverage (only high % disabilities)
3. No temporary disability benefit
4. No medical expense cover
5. No hospital cash benefit
6. Adventure sports exclusion
7. No worldwide coverage"""

TRAVEL_ANALYSIS_CONTEXT = """
TRAVEL INSURANCE ANALYSIS FRAMEWORK:
- Medical Expenses Adequacy: USA needs $100K-$250K, Europe/Schengen needs min EUR 30,000 ($50K), Asia needs $50K
- Emergency Medical Evacuation: Should cover air ambulance ($50K-$100K in USA, $25K-$50K elsewhere)
- Trip Cancellation: Should cover at least non-refundable trip costs (flights, hotels, tours)
- Trip Interruption: Return travel + unused accommodation costs
- Baggage Loss/Delay: Typical $1,500-$3,000 for loss, $300-$500 for delay
- Personal Liability: Minimum $50,000 recommended for international travel
- Flight Delay Compensation: Reasonable daily allowance after 6-12 hour delay
- Adventure Sports: Skiing, scuba, trekking - often excluded without add-on
- Schengen Compliance: Min EUR 30,000 medical, valid for entire trip, covers all Schengen states
- Pre-existing Conditions: Most policies exclude - check if declared conditions covered
- Passport Loss: Emergency passport replacement and travel costs
- Accidental Death/Disability: Coverage during travel period
- Deductible per Claim: Higher deductible means more out-of-pocket per incident
- Coverage Currency: Check if amounts are in USD, EUR, or INR

COMMON TRAVEL GAPS TO CHECK:
1. Medical cover insufficient for destination (USA needs $250K, getting only $50K)
2. No emergency evacuation cover (air ambulance can cost $50K-$100K)
3. Adventure sports excluded (skiing/scuba injury = 100% out of pocket)
4. Pre-existing conditions not covered (heart attack abroad = denied claim)
5. Non-Schengen compliant (visa rejection risk or claim denial in Europe)
6. Low trip cancellation cover (doesn't cover full non-refundable costs)
7. No flight delay compensation (stuck at airport with no support)
8. High per-claim deductible (reduces effective coverage on small claims)"""


def get_policy_type_context(policy_type: str) -> str:
    """
    Return the appropriate analysis framework context based on policy type.

    Args:
        policy_type: The detected policy type string (e.g. "health", "motor", "life", etc.)

    Returns:
        The policy-type-specific analysis context string, or empty string if
        the policy type is not recognized.
    """
    policy_type_lower = policy_type.lower()

    if "health" in policy_type_lower or "medical" in policy_type_lower:
        return HEALTH_ANALYSIS_CONTEXT
    elif "motor" in policy_type_lower or "car" in policy_type_lower or "vehicle" in policy_type_lower:
        return MOTOR_ANALYSIS_CONTEXT
    elif "life" in policy_type_lower or "term" in policy_type_lower:
        return LIFE_ANALYSIS_CONTEXT
    elif "accidental" in policy_type_lower or "accident" in policy_type_lower or "pa" in policy_type_lower:
        return PA_ANALYSIS_CONTEXT
    elif "travel" in policy_type_lower:
        return TRAVEL_ANALYSIS_CONTEXT

    return ""


def build_gap_analysis_prompt(
    policy_type: str,
    extracted_data: dict,
    name: str,
    gender: str,
    user_age: int,
    extracted_text: str,
) -> str:
    """
    Build the comprehensive gap analysis prompt for DeepSeek.

    Args:
        policy_type: The detected policy type (e.g. "health", "motor").
        extracted_data: The dict returned by the extraction step.
        name: Policy holder name.
        gender: Policy holder gender.
        user_age: Calculated age of the policy holder.
        extracted_text: The raw text extracted from the policy document.

    Returns:
        The fully-formed gap analysis prompt string ready for the LLM.
    """
    policy_type_context = get_policy_type_context(policy_type)

    gap_analysis_prompt = f"""
You are an EXPERT insurance analyst with deep knowledge of Indian insurance regulations (IRDAI guidelines).
Analyze this insurance policy like a senior insurance advisor would for a high-net-worth client.

POLICY INFORMATION:
- Policy Type: {policy_type}
- Coverage Amount: Rs.{(extracted_data.get('coverageAmount') or 0):,}
- Policy Holder: {name}
- Gender: {gender}
- Age: {user_age} years
- City: India (consider metropolitan healthcare costs)

{policy_type_context}

POLICY DOCUMENT TEXT:
{extracted_text[:15000]}

YOUR TASK:
Perform a comprehensive gap analysis comparing this policy against:
1. IRDAI recommended standards
2. Industry best practices
3. Policyholder's profile (age, gender)
4. Current market offerings

Identify 4-6 SPECIFIC, ACTIONABLE coverage gaps with:
1. category: Specific coverage area (e.g., "Room Rent Sub-limit", "No Zero Depreciation", "Inadequate Sum Assured")
2. severity: "high" (will significantly impact claims), "medium" (moderate impact), "low" (minor inconvenience)
3. description: SPECIFIC issue found in THIS policy (not generic statements)
4. recommendation: PRECISE action to take (e.g., "Add Super Top-up of Rs.25L", "Add Zero Dep add-on @ Rs.2,500/year")
5. estimatedCost: Realistic annual cost in INR to fix this gap (integer only)

IMPORTANT RULES:
- Be SPECIFIC to this policy - don't give generic advice
- If the policy is strong in an area, don't list it as a gap
- Consider the policyholder's age and gender for relevance
- estimatedCost must be a realistic market rate (integer only, e.g., 3500)
- Focus on gaps that will actually impact claims

Return ONLY a valid JSON array:
[{{"category": "...", "severity": "...", "description": "...", "recommendation": "...", "estimatedCost": 3500}}]"""

    return gap_analysis_prompt
