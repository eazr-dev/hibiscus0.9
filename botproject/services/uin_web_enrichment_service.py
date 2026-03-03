"""
UIN Web Enrichment Service
When a policy PDF has insufficient data, this service uses the UIN (Unique Identification Number)
to find the policy's full T&C, benefits, exclusions, waiting periods, etc.

Supports ALL policy types: health, motor, travel, life, PA.

Strategy:
  1. Parse UIN to identify insurer/product type
  2. Query DeepSeek LLM for policy T&C (uses its training knowledge of IRDAI products)
  3. If DeepSeek knowledge is thin, supplement with Jina web search
  4. Validate, cache, and return structured data

Flow: Check cache → Parse UIN → DeepSeek knowledge → (Jina web search if needed) → Validate → Cache & return
"""

import os
import re
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

# ============= DeepSeek Client =============
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

_deepseek_client = None


def _get_deepseek_client():
    global _deepseek_client
    if _deepseek_client is None:
        try:
            from openai import OpenAI
            _deepseek_client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
        except Exception as e:
            logger.error(f"UIN enrichment: Failed to init DeepSeek client: {e}")
    return _deepseek_client


# ============= Cache (24-hour, by UIN) =============
_enrichment_cache: Dict[str, Dict[str, Any]] = {}
_cache_expiry: Dict[str, datetime] = {}
CACHE_DURATION_HOURS = 24


def _cache_key(uin: str) -> str:
    return f"uin_enrichment_{uin.upper()}_{datetime.now().strftime('%Y-%m-%d')}"


def _get_cached(uin: str) -> Optional[Dict[str, Any]]:
    key = _cache_key(uin)
    expiry = _cache_expiry.get(key)
    if expiry and datetime.now() < expiry:
        return _enrichment_cache.get(key)
    return None


def _set_cached(uin: str, data: Dict[str, Any]):
    key = _cache_key(uin)
    _enrichment_cache[key] = data
    _cache_expiry[key] = datetime.now() + timedelta(hours=CACHE_DURATION_HOURS)


# ============= 1. Insufficiency Detection (All Policy Types) =============

# Type-specific detailed T&C indicators
_HEALTH_TC_INDICATORS = [
    'standard exclusion', 'permanent exclusion', 'list of exclusions',
    'general exclusion', 'not payable', 'shall not be liable',
    'is not covered', 'treatment is excluded',
    'initial waiting period of', 'waiting period of 30',
    'waiting period of 48', 'waiting period of 24', 'moratorium period',
    'room rent limit', 'room rent per day', 'single standard ac room',
    'ambulance charges', 'ambulance cover up to',
    'pre-hospitalisation', 'pre hospitalization',
    'post-hospitalisation', 'post hospitalization',
    'daycare procedure', 'day care procedure',
    'restoration of sum insured', 'restoration benefit', 'recharge of sum insured',
    'co-payment of', 'copayment of', 'co-pay of',
    'sub-limit', 'sublimit', 'internal limit',
    'cataract', 'hernia', 'ayush treatment',
    'domiciliary hospitalization', 'organ donor', 'bariatric surgery',
]

_MOTOR_TC_INDICATORS = [
    'own damage', 'third party liability', 'tp liability',
    'insured declared value', 'idv', 'insured\'s declared value',
    'no claim bonus', 'ncb', 'no-claim bonus',
    'zero depreciation', 'nil depreciation', 'bumper to bumper',
    'engine protection', 'engine protect', 'engine & gearbox',
    'roadside assistance', 'rsa', 'towing charges',
    'return to invoice', 'rti', 'invoice cover',
    'consumable cover', 'consumables', 'nut and bolt',
    'key replacement', 'key protect', 'key loss',
    'tyre protection', 'tyre cover', 'tyre damage',
    'personal accident cover', 'pa cover for owner',
    'electrical accessories', 'non-electrical accessories',
    'bi-fuel kit', 'cng', 'lpg kit',
    'geographical area', 'garage cash', 'daily allowance',
    'exclusion', 'not covered', 'shall not be liable',
    'depreciation schedule', 'depreciation rate',
    'cashless garage', 'network garage', 'authorized workshop',
]

_TRAVEL_TC_INDICATORS = [
    'medical emergency', 'medical expenses abroad', 'overseas medical',
    'emergency evacuation', 'medical evacuation', 'repatriation',
    'trip cancellation', 'trip curtailment', 'trip interruption',
    'baggage loss', 'baggage delay', 'checked baggage',
    'passport loss', 'passport theft', 'travel document',
    'flight delay', 'flight cancellation', 'missed connection',
    'personal liability', 'third party liability abroad',
    'adventure sports', 'hazardous activity', 'winter sports',
    'pre-existing disease', 'pre-existing condition',
    'deductible', 'excess amount', 'co-payment',
    'geographic coverage', 'schengen', 'worldwide',
    'sum insured usd', 'sum insured eur', 'cover amount',
    'exclusion', 'not covered', 'shall not be liable',
    'hijack cover', 'personal accident', 'accidental death',
    'hospital cash', 'daily hospital allowance',
]

_LIFE_TC_INDICATORS = [
    'death benefit', 'sum assured on death', 'life cover',
    'maturity benefit', 'maturity amount', 'maturity value',
    'surrender value', 'surrender charge', 'paid-up value',
    'premium waiver', 'waiver of premium', 'premium holiday',
    'bonus', 'reversionary bonus', 'terminal bonus', 'loyalty addition',
    'fund value', 'nav', 'unit linked', 'ulip',
    'settlement option', 'annuity option', 'pension',
    'rider', 'accidental death benefit', 'critical illness rider',
    'grace period', 'revival period', 'lapse',
    'loan against policy', 'policy loan', 'assignment',
    'nomination', 'nominee', 'free look period',
    'exclusion', 'not covered', 'suicide clause',
    'tax benefit', 'section 80c', 'section 10(10d)',
    'guaranteed return', 'guaranteed addition',
]

_PA_TC_INDICATORS = [
    'accidental death', 'accidental death benefit', 'ad benefit',
    'permanent total disability', 'ptd', 'permanent disability',
    'permanent partial disability', 'ppd', 'partial disability',
    'temporary total disability', 'ttd', 'temporary disability',
    'weekly benefit', 'monthly benefit', 'disability benefit',
    'hospitalization expense', 'medical expense due to accident',
    'education benefit', 'children education', 'funeral expense',
    'transportation of mortal', 'ambulance', 'modification expense',
    'exclusion', 'not covered', 'shall not be liable',
    'self-inflicted', 'suicide', 'war', 'nuclear',
    'adventure sports', 'hazardous activity', 'professional sport',
    'cumulative bonus', 'no claim bonus',
]

# Generic schedule signals (common across all types)
_SCHEDULE_SIGNALS = [
    'policy schedule', 'premium certificate', 'tax invoice',
    'certificate of insurance', 'policy no.', 'policy no :',
    'period of insurance', 'total premium', 'schedule of insurance',
    'policy bond', 'cover note',
]


def _get_tc_indicators(policy_type: str = None) -> List[str]:
    """Get T&C indicators for the given policy type."""
    ptype = (policy_type or "").lower().strip()
    if ptype in ('motor', 'car', 'vehicle', 'bike', 'two-wheeler', 'four-wheeler', 'auto'):
        return _MOTOR_TC_INDICATORS
    elif ptype in ('travel', 'overseas', 'international'):
        return _TRAVEL_TC_INDICATORS
    elif ptype in ('life', 'term', 'endowment', 'ulip', 'whole life', 'whole_life'):
        return _LIFE_TC_INDICATORS
    elif ptype in ('pa', 'personal accident', 'personal_accident', 'accidental'):
        return _PA_TC_INDICATORS
    elif ptype in ('health', 'medical', 'mediclaim'):
        return _HEALTH_TC_INDICATORS
    else:
        # Unknown type — combine all for broader detection
        return _HEALTH_TC_INDICATORS + _MOTOR_TC_INDICATORS[:10] + _TRAVEL_TC_INDICATORS[:10]


def is_data_insufficient(extracted_text: str, page_count: int = None, policy_type: str = None) -> Tuple[bool, str]:
    """
    Check if extracted PDF data is too sparse for a good analysis.
    Detects schedule-only documents across ALL policy types.

    Args:
        extracted_text: The raw text extracted from PDF
        page_count: Number of pages in the PDF (optional)
        policy_type: Detected policy type (health, motor, travel, life, pa)

    Returns:
        (is_insufficient: bool, reason: str)
    """
    if not extracted_text or not extracted_text.strip():
        return True, "no text extracted"

    text_len = len(extracted_text.strip())
    text_lower = extracted_text.lower()

    # Very short text — almost certainly insufficient
    if text_len < 1500:
        return True, f"very short text ({text_len} chars)"

    # Short text — likely a schedule/certificate page only
    if text_len < 3000:
        return True, f"short text ({text_len} chars)"

    # Page count hint
    if page_count is not None and page_count <= 5 and text_len < 8000:
        return True, f"short document ({page_count} pages, {text_len} chars)"

    # ============= Schedule-only detection =============
    schedule_count = sum(1 for s in _SCHEDULE_SIGNALS if s in text_lower)

    # Get type-specific indicators
    tc_indicators = _get_tc_indicators(policy_type)
    detailed_count = sum(1 for d in tc_indicators if d in text_lower)

    if schedule_count >= 2 and detailed_count < 4:
        return True, f"schedule-only document ({schedule_count} schedule signals, only {detailed_count} detailed T&C indicators for {policy_type or 'unknown'} type)"

    if detailed_count < 3 and text_len < 15000:
        return True, f"missing detailed T&C content ({detailed_count}/{len(tc_indicators)} indicators found for {policy_type or 'unknown'} type)"

    return False, "data appears sufficient"


# ============= 2. UIN Company Identification =============

UIN_COMPANY_MAP = {
    "SHAH": "Star Health and Allied Insurance Company",
    "STAR": "Star Health and Allied Insurance Company",
    "HDFC": "HDFC ERGO General Insurance Company",
    "ICIC": "ICICI Lombard General Insurance Company",
    "BAJA": "Bajaj Allianz General Insurance Company",
    "CARE": "Care Health Insurance (formerly Religare Health)",
    "CHI": "Care Health Insurance Limited",
    "NIVA": "Niva Bupa Health Insurance Company",
    "MAX": "Niva Bupa Health Insurance (formerly Max Bupa)",
    "TATA": "Tata AIG General Insurance Company",
    "RELI": "Religare Health Insurance (now Care Health)",
    "MAXI": "Max Bupa Health Insurance (now Niva Bupa)",
    "NIAC": "New India Assurance Company",
    "UNIT": "United India Insurance Company",
    "OICL": "Oriental Insurance Company",
    "GOIC": "National Insurance Company",
    "IRDA": "IRDAI Registered Product",
    "KOMP": "Kotak Mahindra General Insurance Company",
    "ADIT": "Aditya Birla Health Insurance Company",
    "MANI": "Manipal Cigna Health Insurance Company",
    "CHOL": "Cholamandalam MS General Insurance Company",
    "SBIN": "SBI General Insurance Company",
    "ROYA": "Royal Sundaram General Insurance Company",
    "FUTU": "Future Generali India Insurance Company",
    "SHRI": "Shriram General Insurance Company",
    "ACKO": "Acko General Insurance Company",
    "GODT": "Go Digit General Insurance Company",
    "LICI": "Life Insurance Corporation of India",
    "HDFL": "HDFC Life Insurance Company",
    "ICIP": "ICICI Prudential Life Insurance Company",
    "SBIL": "SBI Life Insurance Company",
    "MAXL": "Max Life Insurance Company",
    "BIRL": "Aditya Birla Sun Life Insurance Company",
    "TALI": "Tata AIA Life Insurance Company",
    "KOLI": "Kotak Life Insurance Company",
    "PPFL": "PNB MetLife India Insurance Company",
}


def _parse_uin_company(uin: str) -> Optional[str]:
    """Extract company name from UIN prefix."""
    uin_upper = uin.strip().upper()
    # Try 4-char prefix first, then 3-char
    for prefix_len in (4, 3):
        prefix = uin_upper[:prefix_len]
        if prefix in UIN_COMPANY_MAP:
            return UIN_COMPANY_MAP[prefix]
    # Fallback: check all prefixes
    for prefix, company in UIN_COMPANY_MAP.items():
        if uin_upper.startswith(prefix):
            return company
    return None


def _parse_uin_type_hint(uin: str) -> Optional[str]:
    """Extract product type hint from UIN pattern."""
    uin_upper = uin.strip().upper()
    # Health indicators
    if any(x in uin_upper for x in ('HLI', 'HEA', 'MED', 'HIP', 'HGP', 'HFP')):
        return 'health'
    # Motor indicators (RP = Rating Plan for motor)
    if any(x in uin_upper for x in ('MOT', 'VEH', 'AUT', 'MTP')):
        return 'motor'
    if 'RP' in uin_upper and any(x in uin_upper for x in ('V0', 'V01', 'V02', 'V03')):
        return 'motor'
    # Life indicators
    if any(x in uin_upper for x in ('LIF', 'TER', 'END', 'ULI', 'WHL', 'LIP')):
        return 'life'
    # Travel indicators
    if any(x in uin_upper for x in ('TRA', 'TIO', 'OVE')):
        return 'travel'
    # PA indicators
    if any(x in uin_upper for x in ('PAI', 'PAP', 'PAC', 'ACC')):
        return 'pa'
    return None


# ============= 3. Type-Specific JSON Schemas =============

_TC_SCHEMA_HEALTH = """{
    "plan_name": "Full official plan/product name as registered with IRDAI",
    "insurer": "Insurance company full name",
    "plan_type": "Individual/Family Floater/Group etc.",
    "benefits": ["benefit 1 with details", "benefit 2 with details", ...],
    "key_features": ["feature 1", "feature 2", ...],
    "exclusions": ["exclusion 1", "exclusion 2", ...],
    "waiting_periods": {
        "initial_waiting": "e.g. 30 days",
        "pre_existing_disease": "e.g. 48 months",
        "specific_disease": "e.g. 24 months for specified diseases"
    },
    "co_payment": "e.g. 20% for policyholders aged 61+ or None",
    "room_rent_limit": "e.g. Single AC room, or 1% of SI per day, or No limit",
    "sub_limits": ["sub-limit 1 with amount", "sub-limit 2 with amount", ...],
    "pre_post_hospitalization": "e.g. 60 days pre, 90 days post",
    "daycare_procedures": "Covered/Not covered + details",
    "ambulance_cover": "e.g. Up to Rs 2,500 per hospitalization",
    "restoration_benefit": "e.g. 100% restoration, conditions",
    "no_claim_bonus": "e.g. 10% cumulative bonus per claim-free year, max 50%",
    "claim_process": "Brief description of claim process",
    "network_hospitals": "Number or description of network",
    "sum_insured_options": "Available sum insured ranges",
    "special_conditions": ["condition 1", "condition 2", ...]
}"""

_TC_SCHEMA_MOTOR = """{
    "plan_name": "Full official plan/product name as registered with IRDAI",
    "insurer": "Insurance company full name",
    "plan_type": "Comprehensive/Third Party Only/Standalone OD",
    "benefits": ["benefit 1 with details", "benefit 2 with details", ...],
    "key_features": ["feature 1", "feature 2", ...],
    "exclusions": ["exclusion 1", "exclusion 2", ...],
    "own_damage_cover": "Details of OD coverage, depreciation basis",
    "third_party_liability": "TP liability limits and coverage",
    "idv_basis": "How IDV is calculated, depreciation schedule",
    "ncb_schedule": "No Claim Bonus percentage schedule (e.g. 20%/25%/35%/45%/50%)",
    "zero_depreciation": "Covered/Not covered, terms, claim limits",
    "engine_protection": "Covered/Not covered, terms",
    "roadside_assistance": "Covered/Not covered, details (towing, flat tyre, battery, fuel)",
    "return_to_invoice": "Covered/Not covered, terms",
    "consumable_cover": "Covered/Not covered, items covered",
    "key_replacement": "Covered/Not covered, limit",
    "tyre_protection": "Covered/Not covered, terms",
    "pa_cover_owner": "Personal accident cover for owner-driver, amount",
    "electrical_accessories": "Coverage limit for electrical accessories",
    "non_electrical_accessories": "Coverage limit for non-electrical accessories",
    "geographical_area": "India/specific regions",
    "depreciation_schedule": {"rubber/nylon": "50%", "plastic": "30%", "glass": "nil", "metal": "varies by age"},
    "cashless_garages": "Number or description of network garages",
    "claim_process": "Brief description of claim process",
    "special_conditions": ["condition 1", "condition 2", ...]
}"""

_TC_SCHEMA_TRAVEL = """{
    "plan_name": "Full official plan/product name as registered with IRDAI",
    "insurer": "Insurance company full name",
    "plan_type": "Individual/Family/Student/Senior Citizen/Business",
    "benefits": ["benefit 1 with details", "benefit 2 with details", ...],
    "key_features": ["feature 1", "feature 2", ...],
    "exclusions": ["exclusion 1", "exclusion 2", ...],
    "medical_cover": "Medical expenses cover amount and details",
    "emergency_evacuation": "Emergency medical evacuation cover and limits",
    "repatriation": "Repatriation of mortal remains cover",
    "trip_cancellation": "Trip cancellation cover amount and conditions",
    "trip_curtailment": "Trip curtailment/interruption cover",
    "baggage_loss": "Checked baggage loss/damage cover amount",
    "baggage_delay": "Baggage delay cover amount and hours threshold",
    "flight_delay": "Flight delay compensation amount and hours threshold",
    "passport_loss": "Passport loss cover amount",
    "personal_liability": "Personal liability cover amount",
    "adventure_sports": "Covered/Excluded, list of covered activities",
    "pre_existing_conditions": "Coverage terms for PED",
    "deductible": "Deductible/excess amount per claim",
    "geographic_coverage": "Countries/regions covered (Asia/Worldwide/Schengen etc.)",
    "sum_insured_options": "Available cover amounts (in USD/EUR/INR)",
    "covid_coverage": "COVID-19 coverage terms",
    "hijack_cover": "Hijack distress allowance",
    "hospital_cash": "Daily hospital cash allowance abroad",
    "claim_process": "Brief description of claim process",
    "special_conditions": ["condition 1", "condition 2", ...]
}"""

_TC_SCHEMA_LIFE = """{
    "plan_name": "Full official plan/product name as registered with IRDAI",
    "insurer": "Insurance company full name",
    "plan_type": "Term/Endowment/ULIP/Whole Life/Money Back/Pension",
    "benefits": ["benefit 1 with details", "benefit 2 with details", ...],
    "key_features": ["feature 1", "feature 2", ...],
    "exclusions": ["exclusion 1", "exclusion 2", ...],
    "death_benefit": "Death benefit details and calculation",
    "maturity_benefit": "Maturity benefit details (if applicable)",
    "surrender_value": "Surrender value terms and charges",
    "premium_waiver": "Premium waiver benefit conditions",
    "bonus_details": "Reversionary bonus/terminal bonus/loyalty additions",
    "riders_available": ["rider 1 with details", "rider 2 with details", ...],
    "grace_period": "Grace period for premium payment",
    "revival_period": "Revival/reinstatement period and conditions",
    "free_look_period": "Free look cancellation period",
    "loan_facility": "Policy loan availability and terms",
    "tax_benefits": "Section 80C/10(10D) benefits",
    "settlement_options": "Lump sum/installments/annuity options",
    "sum_assured_options": "Available sum assured ranges",
    "premium_payment_modes": "Annual/Semi-annual/Quarterly/Monthly",
    "policy_term_options": "Available policy term durations",
    "claim_process": "Brief description of claim process",
    "special_conditions": ["condition 1", "condition 2", ...]
}"""

_TC_SCHEMA_PA = """{
    "plan_name": "Full official plan/product name as registered with IRDAI",
    "insurer": "Insurance company full name",
    "plan_type": "Individual/Family/Group",
    "benefits": ["benefit 1 with details", "benefit 2 with details", ...],
    "key_features": ["feature 1", "feature 2", ...],
    "exclusions": ["exclusion 1", "exclusion 2", ...],
    "accidental_death_benefit": "AD benefit amount and terms",
    "permanent_total_disability": "PTD benefit amount and conditions",
    "permanent_partial_disability": "PPD benefit schedule/percentage table",
    "temporary_total_disability": "TTD weekly/monthly benefit and max period",
    "medical_expenses": "Medical expenses reimbursement due to accident",
    "hospitalization_benefit": "Hospital cash/daily allowance if any",
    "education_benefit": "Children education benefit if any",
    "funeral_expenses": "Funeral/cremation expense cover",
    "transportation_mortal_remains": "Transport of mortal remains cover",
    "loan_shield": "EMI/loan protection benefit if any",
    "modification_expenses": "Home/vehicle modification for disability",
    "cumulative_bonus": "No claim bonus details",
    "sum_insured_options": "Available cover amounts",
    "claim_process": "Brief description of claim process",
    "special_conditions": ["condition 1", "condition 2", ...]
}"""


def _get_tc_schema(policy_type: str = None) -> str:
    """Get the appropriate JSON schema for the policy type."""
    ptype = (policy_type or "").lower().strip()
    if ptype in ('motor', 'car', 'vehicle', 'bike', 'two-wheeler', 'four-wheeler', 'auto'):
        return _TC_SCHEMA_MOTOR
    elif ptype in ('travel', 'overseas', 'international'):
        return _TC_SCHEMA_TRAVEL
    elif ptype in ('life', 'term', 'endowment', 'ulip', 'whole life', 'whole_life'):
        return _TC_SCHEMA_LIFE
    elif ptype in ('pa', 'personal accident', 'personal_accident', 'accidental'):
        return _TC_SCHEMA_PA
    else:
        return _TC_SCHEMA_HEALTH


def _get_meaningful_fields(policy_type: str = None) -> List[str]:
    """Get meaningful field names to check for richness per policy type."""
    ptype = (policy_type or "").lower().strip()
    if ptype in ('motor', 'car', 'vehicle', 'bike', 'two-wheeler', 'four-wheeler', 'auto'):
        return ['benefits', 'exclusions', 'key_features', 'special_conditions',
                'ncb_schedule', 'depreciation_schedule']
    elif ptype in ('travel', 'overseas', 'international'):
        return ['benefits', 'exclusions', 'key_features', 'special_conditions']
    elif ptype in ('life', 'term', 'endowment', 'ulip', 'whole life', 'whole_life'):
        return ['benefits', 'exclusions', 'key_features', 'riders_available', 'special_conditions']
    elif ptype in ('pa', 'personal accident', 'personal_accident', 'accidental'):
        return ['benefits', 'exclusions', 'key_features', 'special_conditions']
    else:
        return ['benefits', 'exclusions', 'waiting_periods', 'key_features', 'sub_limits']


# ============= 4. DeepSeek LLM Knowledge Query =============

def _query_deepseek_knowledge(
    uin: str,
    policy_type: str = None,
    company_name: str = None,
    extracted_text_snippet: str = None,
) -> Optional[Dict[str, Any]]:
    """
    Query DeepSeek's training knowledge for comprehensive policy T&C.
    Uses type-specific schema to get the right fields per policy type.
    """
    client = _get_deepseek_client()
    if not client:
        logger.error("UIN enrichment: DeepSeek client unavailable")
        return None

    company = company_name or _parse_uin_company(uin) or "Unknown"
    type_hint = policy_type or _parse_uin_type_hint(uin) or "insurance"
    tc_schema = _get_tc_schema(policy_type)

    schedule_context = ""
    if extracted_text_snippet:
        schedule_context = f"""
Here is the policy schedule/certificate from the PDF (this is what the policyholder received):
---
{extracted_text_snippet[:4000]}
---
Use this to identify the exact product and plan variant.
"""

    # Type-specific prompt details
    type_specific_instruction = ""
    ptype = (policy_type or "").lower().strip()
    if ptype in ('motor', 'car', 'vehicle', 'bike', 'auto'):
        type_specific_instruction = """
For motor insurance, provide details on:
- Own damage vs third party coverage, IDV calculation
- NCB schedule (exact percentages per year)
- All available add-ons (zero depreciation, engine protection, RSA, RTI, consumables, etc.)
- Depreciation schedule for parts (rubber, plastic, glass, fibre, metal)
- Exclusions specific to motor (drunk driving, racing, unlicensed, commercial use, etc.)
- Cashless garage network size
"""
    elif ptype in ('travel', 'overseas', 'international'):
        type_specific_instruction = """
For travel insurance, provide details on:
- Medical emergency cover amount (in USD/EUR)
- Emergency evacuation and repatriation limits
- Trip cancellation/curtailment conditions and limits
- Baggage loss/delay covers and thresholds
- Flight delay compensation
- Adventure sports coverage
- Pre-existing condition terms
- Deductible/excess amounts
- Geographic scope (specific countries/regions)
"""
    elif ptype in ('life', 'term', 'endowment', 'ulip', 'whole life'):
        type_specific_instruction = """
For life insurance, provide details on:
- Death benefit calculation (sum assured, fund value, etc.)
- Maturity benefit details
- Surrender value and charges at different years
- Available riders
- Bonus/loyalty details
- Tax benefits
- Grace period, revival, free look period
"""
    elif ptype in ('pa', 'personal accident', 'accidental'):
        type_specific_instruction = """
For personal accident insurance, provide details on:
- Accidental death benefit amount
- Permanent total disability (PTD) benefit
- Permanent partial disability (PPD) schedule/percentages
- Temporary total disability (TTD) weekly benefit and max period
- Medical expenses reimbursement
- Education benefit, funeral expenses, transport of remains
- Exclusions (self-inflicted, war, nuclear, adventure sports, etc.)
"""

    prompt = f"""You are an expert on Indian insurance products registered with IRDAI.

I need the COMPLETE Terms & Conditions for the {type_hint} insurance product with:
- UIN: {uin}
- Insurance Company: {company}
- Policy Type: {type_hint} insurance
{schedule_context}
From your knowledge of IRDAI-registered insurance products in India (from official IRDAI product filings, insurer product brochures, PolicyBazaar, Beshak, CoverFox, and insurer websites), provide the comprehensive terms and conditions for this specific product.

Search your knowledge thoroughly for UIN {uin}. This is an IRDAI-registered product — all such products have publicly filed T&C documents.
{type_specific_instruction}
IMPORTANT:
- Provide DETAILED information — list ALL benefits, ALL exclusions
- For exclusions, list at least the major standard and permanent exclusions
- For benefits, include specific amounts/limits where known
- If you are not confident about a specific detail, use empty string "" or empty list []
- Do NOT fabricate or guess — only provide what you know from training data

Return ONLY valid JSON in this exact format:
{tc_schema}"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an Indian {type_hint} insurance product expert with comprehensive knowledge "
                        "of IRDAI-registered products. You have detailed knowledge from official "
                        "product filings, insurer websites, PolicyBazaar, Beshak, and insurance "
                        "comparison portals. Provide accurate, detailed policy information based "
                        "on the UIN. Return ONLY valid JSON, no explanations."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )

        raw = response.choices[0].message.content.strip()
        return _parse_deepseek_json(raw, uin, "knowledge")

    except Exception as e:
        logger.error(f"UIN enrichment: DeepSeek knowledge query failed: {e}")
        return None


# ============= 5. Jina Web Search (Supplementary) =============

JINA_SEARCH_URL = "https://s.jina.ai/"
JINA_READER_URL = "https://r.jina.ai/"


async def _search_web_jina(uin: str, company_name: str = None, policy_type: str = None) -> str:
    """
    Search the web using Jina Search API (free, LLM-optimized results).
    Returns search results as clean text.
    """
    company = company_name or _parse_uin_company(uin) or ""
    type_hint = policy_type or _parse_uin_type_hint(uin) or "insurance"

    queries = [
        f"{uin} {company} {type_hint} policy terms conditions benefits exclusions",
        f"{uin} IRDAI {type_hint} insurance policy wording",
    ]

    all_results = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True) as client:
        for query in queries:
            try:
                url = JINA_SEARCH_URL + quote(query, safe='')
                response = await client.get(url, headers={
                    "Accept": "application/json",
                    "X-No-Cache": "true",
                })
                if response.status_code == 200:
                    data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    results = data.get("data", [])
                    for r in results[:5]:
                        content = r.get("content", "").strip()
                        title = r.get("title", "").strip()
                        if content and len(content) > 100:
                            all_results.append(f"[{title}]\n{content[:5000]}")
                    logger.info(f"UIN enrichment: Jina search '{query[:50]}...' returned {len(results)} results")
                else:
                    text = response.text.strip()
                    if len(text) > 200:
                        all_results.append(text[:8000])
                        logger.info(f"UIN enrichment: Jina search returned {len(text)} chars (plain text)")

            except Exception as e:
                logger.warning(f"UIN enrichment: Jina search failed for '{query[:50]}...': {e}")

    return "\n\n---\n\n".join(all_results) if all_results else ""


async def _fetch_page_jina(url: str) -> str:
    """Fetch a web page using Jina Reader API (returns clean markdown)."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0), follow_redirects=True) as client:
            reader_url = JINA_READER_URL + url
            response = await client.get(reader_url, headers={
                "Accept": "text/markdown",
                "X-No-Cache": "true",
            })
            if response.status_code == 200:
                text = response.text.strip()
                if len(text) > 200:
                    logger.info(f"UIN enrichment: Jina reader fetched {len(text)} chars from {url[:60]}")
                    return text[:10000]
    except Exception as e:
        logger.debug(f"UIN enrichment: Jina reader failed for {url[:60]}: {e}")
    return ""


def _extract_tc_from_web_content(web_content: str, uin: str, policy_type: str = None) -> Optional[Dict[str, Any]]:
    """Extract structured T&C from web content using DeepSeek with type-specific schema."""
    client = _get_deepseek_client()
    if not client:
        return None

    type_hint = policy_type or "insurance"
    tc_schema = _get_tc_schema(policy_type)

    prompt = f"""Extract the {type_hint} insurance policy Terms & Conditions for UIN: {uin} from the web search results below.

Return ONLY valid JSON with these fields (use empty string "" or empty list [] if not found):

{tc_schema}

Web Search Results:
---
{web_content[:15000]}
---"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert at extracting Indian {type_hint} insurance policy terms and conditions from web content. Extract accurate, structured data. Return ONLY valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=4000
        )

        raw = response.choices[0].message.content.strip()
        return _parse_deepseek_json(raw, uin, "web_extraction")

    except Exception as e:
        logger.error(f"UIN enrichment: DeepSeek web extraction failed: {e}")
        return None


# ============= 6. JSON Parsing & Validation =============

def _parse_deepseek_json(raw: str, uin: str, source: str) -> Optional[Dict[str, Any]]:
    """Parse and validate DeepSeek's JSON response."""
    try:
        # Clean markdown code blocks
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        # Sometimes DeepSeek adds trailing text after JSON
        brace_depth = 0
        json_end = -1
        for i, ch in enumerate(raw):
            if ch == '{':
                brace_depth += 1
            elif ch == '}':
                brace_depth -= 1
                if brace_depth == 0:
                    json_end = i + 1
                    break

        if json_end > 0:
            raw = raw[:json_end]

        data = json.loads(raw)

        # Validate: must have at least 2 non-empty meaningful fields
        # Check common fields across all types
        all_check_fields = [
            'benefits', 'exclusions', 'waiting_periods', 'key_features', 'sub_limits',
            'special_conditions', 'riders_available', 'depreciation_schedule',
            'ncb_schedule',
        ]
        non_empty_count = sum(
            1 for f in all_check_fields
            if data.get(f) and (
                (isinstance(data[f], list) and len(data[f]) > 0) or
                (isinstance(data[f], dict) and any(v for v in data[f].values() if v)) or
                (isinstance(data[f], str) and data[f].strip())
            )
        )

        if non_empty_count < 2:
            logger.warning(f"UIN enrichment ({source}): Too sparse ({non_empty_count} fields) for {uin}")
            return None

        logger.info(f"UIN enrichment ({source}): Extracted {non_empty_count} meaningful fields for {uin}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"UIN enrichment ({source}): JSON parse failed for {uin}: {e}")
        return None


def _merge_enrichment_data(knowledge: Dict, web: Dict) -> Dict:
    """Merge DeepSeek knowledge + web search results. Web data fills gaps in knowledge."""
    merged = dict(knowledge)

    for key, val in web.items():
        if key.startswith("_"):
            continue

        existing = merged.get(key)

        # If knowledge result is empty/missing, use web result
        if not existing or (isinstance(existing, str) and not existing.strip()) or (isinstance(existing, list) and not existing):
            merged[key] = val
        # If both are lists, merge (deduplicate)
        elif isinstance(existing, list) and isinstance(val, list):
            existing_lower = {str(e).lower() for e in existing}
            for item in val:
                if str(item).lower() not in existing_lower:
                    existing.append(item)
        # If both are dicts, fill missing keys
        elif isinstance(existing, dict) and isinstance(val, dict):
            for k, v in val.items():
                if not existing.get(k):
                    existing[k] = v

    return merged


# ============= 7. Format for Prompt Injection (All Types) =============

def format_enrichment_for_prompt(enrichment_data: Dict[str, Any]) -> str:
    """Format the enriched T&C data as readable text for the extraction prompt.
    Works for all policy types — outputs whatever fields are present."""
    lines = []

    # Common fields
    if enrichment_data.get("plan_name"):
        lines.append(f"Plan Name: {enrichment_data['plan_name']}")
    if enrichment_data.get("insurer"):
        lines.append(f"Insurer: {enrichment_data['insurer']}")
    if enrichment_data.get("plan_type"):
        lines.append(f"Plan Type: {enrichment_data['plan_type']}")

    # List fields (common across types)
    _format_list(lines, enrichment_data, "benefits", "Key Benefits")
    _format_list(lines, enrichment_data, "key_features", "Key Features")
    _format_list(lines, enrichment_data, "exclusions", "Exclusions")

    # ---- Health-specific fields ----
    wp = enrichment_data.get("waiting_periods")
    if wp and isinstance(wp, dict):
        lines.append("\nWaiting Periods:")
        for k, v in wp.items():
            if v:
                lines.append(f"  - {k.replace('_', ' ').title()}: {v}")

    _format_str(lines, enrichment_data, "co_payment", "Co-Payment")
    _format_str(lines, enrichment_data, "room_rent_limit", "Room Rent Limit")
    _format_list(lines, enrichment_data, "sub_limits", "Sub-Limits")
    _format_str(lines, enrichment_data, "pre_post_hospitalization", "Pre/Post Hospitalization")
    _format_str(lines, enrichment_data, "daycare_procedures", "Daycare Procedures")
    _format_str(lines, enrichment_data, "ambulance_cover", "Ambulance Cover")
    _format_str(lines, enrichment_data, "restoration_benefit", "Restoration Benefit")
    _format_str(lines, enrichment_data, "no_claim_bonus", "No Claim Bonus")
    _format_str(lines, enrichment_data, "network_hospitals", "Network Hospitals")

    # ---- Motor-specific fields ----
    _format_str(lines, enrichment_data, "own_damage_cover", "Own Damage Cover")
    _format_str(lines, enrichment_data, "third_party_liability", "Third Party Liability")
    _format_str(lines, enrichment_data, "idv_basis", "IDV Basis")
    _format_str(lines, enrichment_data, "ncb_schedule", "NCB Schedule")
    _format_str(lines, enrichment_data, "zero_depreciation", "Zero Depreciation")
    _format_str(lines, enrichment_data, "engine_protection", "Engine Protection")
    _format_str(lines, enrichment_data, "roadside_assistance", "Roadside Assistance")
    _format_str(lines, enrichment_data, "return_to_invoice", "Return to Invoice")
    _format_str(lines, enrichment_data, "consumable_cover", "Consumable Cover")
    _format_str(lines, enrichment_data, "key_replacement", "Key Replacement")
    _format_str(lines, enrichment_data, "tyre_protection", "Tyre Protection")
    _format_str(lines, enrichment_data, "pa_cover_owner", "PA Cover (Owner-Driver)")
    _format_str(lines, enrichment_data, "electrical_accessories", "Electrical Accessories")
    _format_str(lines, enrichment_data, "non_electrical_accessories", "Non-Electrical Accessories")
    _format_str(lines, enrichment_data, "geographical_area", "Geographical Area")
    _format_str(lines, enrichment_data, "cashless_garages", "Cashless Garages")

    dep = enrichment_data.get("depreciation_schedule")
    if dep and isinstance(dep, dict):
        lines.append("\nDepreciation Schedule:")
        for part, rate in dep.items():
            lines.append(f"  - {part}: {rate}")

    # ---- Travel-specific fields ----
    _format_str(lines, enrichment_data, "medical_cover", "Medical Cover")
    _format_str(lines, enrichment_data, "emergency_evacuation", "Emergency Evacuation")
    _format_str(lines, enrichment_data, "repatriation", "Repatriation")
    _format_str(lines, enrichment_data, "trip_cancellation", "Trip Cancellation")
    _format_str(lines, enrichment_data, "trip_curtailment", "Trip Curtailment")
    _format_str(lines, enrichment_data, "baggage_loss", "Baggage Loss")
    _format_str(lines, enrichment_data, "baggage_delay", "Baggage Delay")
    _format_str(lines, enrichment_data, "flight_delay", "Flight Delay")
    _format_str(lines, enrichment_data, "passport_loss", "Passport Loss")
    _format_str(lines, enrichment_data, "personal_liability", "Personal Liability")
    _format_str(lines, enrichment_data, "adventure_sports", "Adventure Sports")
    _format_str(lines, enrichment_data, "pre_existing_conditions", "Pre-Existing Conditions")
    _format_str(lines, enrichment_data, "deductible", "Deductible")
    _format_str(lines, enrichment_data, "geographic_coverage", "Geographic Coverage")
    _format_str(lines, enrichment_data, "covid_coverage", "COVID-19 Coverage")
    _format_str(lines, enrichment_data, "hijack_cover", "Hijack Cover")
    _format_str(lines, enrichment_data, "hospital_cash", "Hospital Cash")

    # ---- Life-specific fields ----
    _format_str(lines, enrichment_data, "death_benefit", "Death Benefit")
    _format_str(lines, enrichment_data, "maturity_benefit", "Maturity Benefit")
    _format_str(lines, enrichment_data, "surrender_value", "Surrender Value")
    _format_str(lines, enrichment_data, "premium_waiver", "Premium Waiver")
    _format_str(lines, enrichment_data, "bonus_details", "Bonus Details")
    _format_list(lines, enrichment_data, "riders_available", "Riders Available")
    _format_str(lines, enrichment_data, "grace_period", "Grace Period")
    _format_str(lines, enrichment_data, "revival_period", "Revival Period")
    _format_str(lines, enrichment_data, "free_look_period", "Free Look Period")
    _format_str(lines, enrichment_data, "loan_facility", "Policy Loan Facility")
    _format_str(lines, enrichment_data, "tax_benefits", "Tax Benefits")
    _format_str(lines, enrichment_data, "settlement_options", "Settlement Options")
    _format_str(lines, enrichment_data, "premium_payment_modes", "Premium Payment Modes")
    _format_str(lines, enrichment_data, "policy_term_options", "Policy Term Options")

    # ---- PA-specific fields ----
    _format_str(lines, enrichment_data, "accidental_death_benefit", "Accidental Death Benefit")
    _format_str(lines, enrichment_data, "permanent_total_disability", "Permanent Total Disability")
    _format_str(lines, enrichment_data, "permanent_partial_disability", "Permanent Partial Disability")
    _format_str(lines, enrichment_data, "temporary_total_disability", "Temporary Total Disability")
    _format_str(lines, enrichment_data, "medical_expenses", "Medical Expenses")
    _format_str(lines, enrichment_data, "hospitalization_benefit", "Hospitalization Benefit")
    _format_str(lines, enrichment_data, "education_benefit", "Education Benefit")
    _format_str(lines, enrichment_data, "funeral_expenses", "Funeral Expenses")
    _format_str(lines, enrichment_data, "transportation_mortal_remains", "Transportation of Mortal Remains")
    _format_str(lines, enrichment_data, "loan_shield", "Loan Shield")
    _format_str(lines, enrichment_data, "modification_expenses", "Modification Expenses")
    _format_str(lines, enrichment_data, "cumulative_bonus", "Cumulative Bonus")

    # Common trailing fields
    _format_str(lines, enrichment_data, "claim_process", "Claim Process")
    _format_str(lines, enrichment_data, "sum_insured_options", "Sum Insured Options")
    _format_str(lines, enrichment_data, "sum_assured_options", "Sum Assured Options")
    _format_list(lines, enrichment_data, "special_conditions", "Special Conditions")

    return "\n".join(lines)


def _format_str(lines: list, data: dict, key: str, label: str):
    """Append a string field if present."""
    val = data.get(key)
    if val and isinstance(val, str) and val.strip():
        lines.append(f"\n{label}: {val}")
    elif val and not isinstance(val, (str, list, dict)):
        lines.append(f"\n{label}: {val}")


def _format_list(lines: list, data: dict, key: str, label: str):
    """Append a list field if present."""
    val = data.get(key)
    if val and isinstance(val, list) and len(val) > 0:
        lines.append(f"\n{label}:")
        for item in val:
            lines.append(f"  - {item}")


# ============= 8. Main Entry Point =============

async def enrich_policy_via_uin(
    uin: str,
    policy_type: str = None,
    company_name: str = None,
    extracted_text_snippet: str = None,
) -> Optional[Dict[str, Any]]:
    """
    Main entry point for UIN-based enrichment. Works for ALL policy types.

    Flow:
      1. Check cache
      2. Parse UIN for company/type hints
      3. Query DeepSeek knowledge (primary)
      4. If knowledge is thin, supplement with Jina web search
      5. Merge, validate, cache & return

    Args:
        uin: The UIN extracted from the policy PDF
        policy_type: Detected policy type (health, motor, travel, life, pa, etc.)
        company_name: Company name if known from PDF extraction
        extracted_text_snippet: First few thousand chars of extracted PDF text (for context)

    Returns:
        Dict with structured T&C data, or None if enrichment fails.
    """
    if not uin or len(uin) < 8:
        logger.debug("UIN enrichment: Skipped — no valid UIN provided")
        return None

    uin = uin.strip().upper()

    # Check cache first
    cached = _get_cached(uin)
    if cached:
        logger.info(f"UIN enrichment: Cache hit for {uin}")
        return cached

    # Resolve company from UIN if not provided
    if not company_name:
        company_name = _parse_uin_company(uin)
    if not policy_type:
        policy_type = _parse_uin_type_hint(uin)

    logger.info(f"UIN enrichment: Starting for {uin} (company={company_name}, type={policy_type})")

    # ---- Step 1: DeepSeek Knowledge Query (primary) ----
    logger.info(f"UIN enrichment: Querying DeepSeek knowledge for {uin} (type={policy_type})")
    knowledge_data = await asyncio.to_thread(
        _query_deepseek_knowledge, uin, policy_type, company_name, extracted_text_snippet
    )

    if knowledge_data:
        logger.info(f"UIN enrichment: DeepSeek knowledge returned data for {uin}")

        # Check if knowledge is rich enough using type-specific fields
        meaningful_fields = _get_meaningful_fields(policy_type)
        rich_count = sum(
            1 for f in meaningful_fields
            if knowledge_data.get(f) and (
                (isinstance(knowledge_data[f], list) and len(knowledge_data[f]) >= 3) or
                (isinstance(knowledge_data[f], dict) and sum(1 for v in knowledge_data[f].values() if v) >= 2)
            )
        )

        if rich_count >= 3:
            logger.info(f"UIN enrichment: DeepSeek knowledge is rich ({rich_count} rich fields), skipping web search")
            knowledge_data["_enrichment_meta"] = {
                "uin": uin,
                "source": "deepseek_knowledge",
                "policy_type": policy_type or "unknown",
                "fetched_at": datetime.now().isoformat(),
                "company_identified": company_name or "unknown",
            }
            _set_cached(uin, knowledge_data)
            return knowledge_data

    # ---- Step 2: Jina Web Search (supplementary) ----
    logger.info(f"UIN enrichment: Supplementing with Jina web search for {uin}")
    web_content = await _search_web_jina(uin, company_name, policy_type)

    web_data = None
    if web_content and len(web_content) > 200:
        logger.info(f"UIN enrichment: Jina returned {len(web_content)} chars, extracting via DeepSeek")
        web_data = await asyncio.to_thread(
            _extract_tc_from_web_content, web_content, uin, policy_type
        )

    # ---- Step 3: Merge results ----
    final_data = None

    if knowledge_data and web_data:
        final_data = _merge_enrichment_data(knowledge_data, web_data)
        source = "deepseek_knowledge+jina_web"
        logger.info(f"UIN enrichment: Merged knowledge + web data for {uin}")
    elif knowledge_data:
        final_data = knowledge_data
        source = "deepseek_knowledge"
    elif web_data:
        final_data = web_data
        source = "jina_web_search"
    else:
        logger.warning(f"UIN enrichment: No data from either source for {uin}")
        return None

    # Add metadata
    final_data["_enrichment_meta"] = {
        "uin": uin,
        "source": source,
        "policy_type": policy_type or "unknown",
        "fetched_at": datetime.now().isoformat(),
        "company_identified": company_name or "unknown",
        "knowledge_available": knowledge_data is not None,
        "web_search_available": web_data is not None,
    }

    # Cache the result
    _set_cached(uin, final_data)
    logger.info(f"UIN enrichment: Successfully enriched {uin} ({policy_type}) via {source} — cached for {CACHE_DURATION_HOURS}h")

    return final_data
