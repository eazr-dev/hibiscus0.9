"""
Indian Market Data Service
Fetches live/current data from Indian market using DeepSeek LLM
for accurate insurance report generation.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import lru_cache
import hashlib

logger = logging.getLogger(__name__)

# DeepSeek API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Initialize OpenAI client for DeepSeek
try:
    from openai import OpenAI
    deepseek_client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com"
    )
except Exception as e:
    logger.error(f"Failed to initialize DeepSeek client: {e}")
    deepseek_client = None

# Cache for market data (expires after 24 hours)
_market_data_cache: Dict[str, Dict[str, Any]] = {}
_cache_expiry: Dict[str, datetime] = {}
CACHE_DURATION_HOURS = 24


def _get_cache_key(data_type: str) -> str:
    """Generate cache key for market data"""
    return f"market_data_{data_type}_{datetime.now().strftime('%Y-%m-%d')}"


def _is_cache_valid(cache_key: str) -> bool:
    """Check if cache is still valid"""
    if cache_key not in _cache_expiry:
        return False
    return datetime.now() < _cache_expiry[cache_key]


def _set_cache(cache_key: str, data: Dict[str, Any]):
    """Set cache with expiry"""
    _market_data_cache[cache_key] = data
    _cache_expiry[cache_key] = datetime.now() + timedelta(hours=CACHE_DURATION_HOURS)


def _get_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached data if valid"""
    if _is_cache_valid(cache_key):
        return _market_data_cache.get(cache_key)
    return None


def _call_deepseek(prompt: str, max_tokens: int = 500) -> Optional[str]:
    """Call DeepSeek LLM API"""
    if not deepseek_client:
        logger.error("DeepSeek client not initialized")
        return None

    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial data expert specializing in Indian markets. Provide accurate, current data with sources. Always respond in valid JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=0.1  # Low temperature for factual accuracy
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"DeepSeek API call failed: {e}")
        return None


def get_life_insurance_market_data() -> Dict[str, Any]:
    """
    Fetch live Indian market data for life insurance reports:
    - PPF interest rate
    - Bank FD rates
    - Survival benefit rates
    - Other relevant rates
    """
    cache_key = _get_cache_key("life_insurance")
    cached_data = _get_cache(cache_key)
    if cached_data:
        logger.info("📊 Life Insurance: Using cached market data")
        return cached_data

    prompt = """
Provide the current Indian market data for life insurance comparison (as of today):

1. PPF (Public Provident Fund) current interest rate (from Government of India)
2. Bank Fixed Deposit rates for major banks (SBI, HDFC, ICICI) for 5-year FD
3. Standard survival benefit rate for endowment/Jeevan Umang type policies
4. Post Office Senior Citizens Savings Scheme (SCSS) rate
5. National Savings Certificate (NSC) rate

Respond ONLY with valid JSON in this exact format:
{
    "ppf_rate": 7.1,
    "ppf_source": "Government of India FY 2024-25",
    "bank_fd_rates": {
        "sbi": 6.5,
        "hdfc": 7.0,
        "icici": 6.9,
        "average": 6.8
    },
    "survival_benefit_rate": 8.0,
    "survival_benefit_note": "Standard for Jeevan Umang type policies",
    "scss_rate": 8.2,
    "nsc_rate": 7.7,
    "data_date": "2024-01",
    "disclaimer": "Rates are indicative and may vary"
}
"""

    response = _call_deepseek(prompt)

    # Default fallback data
    default_data = {
        "ppf_rate": 7.1,
        "ppf_source": "Government of India",
        "bank_fd_rates": {
            "sbi": 6.5,
            "hdfc": 7.0,
            "icici": 6.9,
            "average": 7.0
        },
        "survival_benefit_rate": 8.0,
        "survival_benefit_note": "Standard for endowment policies",
        "scss_rate": 8.2,
        "nsc_rate": 7.7,
        "data_date": datetime.now().strftime("%Y-%m"),
        "disclaimer": "Rates are indicative and may vary",
        "source": "default"
    }

    if response:
        try:
            # Clean response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()

            data = json.loads(clean_response)
            data["source"] = "deepseek_live"
            data["fetched_at"] = datetime.now().isoformat()
            _set_cache(cache_key, data)
            logger.info(f"📊 Life Insurance: Fetched live market data - PPF: {data.get('ppf_rate')}%")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepSeek response: {e}")

    logger.warning("📊 Life Insurance: Using default market data")
    default_data["source"] = "default_fallback"
    _set_cache(cache_key, default_data)
    return default_data


def get_motor_insurance_market_data() -> Dict[str, Any]:
    """
    Fetch live Indian market data for motor insurance reports:
    - IRDAI depreciation rates
    - Compulsory deductible amounts
    - PA cover amounts
    - Third party coverage limits
    - Traffic violation fines
    """
    cache_key = _get_cache_key("motor_insurance")
    cached_data = _get_cache(cache_key)
    if cached_data:
        logger.info("🚗 Motor Insurance: Using cached market data")
        return cached_data

    prompt = """
Provide the current Indian motor insurance market data as per IRDAI regulations:

1. Metal/Body part depreciation rates by vehicle age (as per IRDAI guidelines)
2. Plastic/Rubber/Fibre parts depreciation rate
3. Paint depreciation rate
4. IRDAI compulsory deductible amount for cars
5. Compulsory Personal Accident (PA) cover for owner-driver
6. Third party bodily injury liability (as per Motor Vehicles Act)
7. Third party property damage liability limit
8. Traffic violation fine for driving without insurance (Motor Vehicles Act 2019)
9. Imprisonment term for driving without insurance
10. Typical parts breakdown percentage (plastic, metal, paint, labour) for claim calculation

Respond ONLY with valid JSON in this exact format:
{
    "depreciation_rates": {
        "metal": {
            "0_to_6_months": 0,
            "6_months_to_1_year": 5,
            "1_to_2_years": 10,
            "2_to_3_years": 15,
            "3_to_4_years": 25,
            "4_to_5_years": 30,
            "5_to_10_years": 35,
            "above_10_years": 40
        },
        "plastic_rubber_fibre": 50,
        "paint": 30,
        "glass": 0,
        "tyres_tubes": 50,
        "batteries": 50
    },
    "parts_breakdown": {
        "plastic_percentage": 30,
        "metal_percentage": 50,
        "paint_percentage": 15,
        "labour_percentage": 5
    },
    "compulsory_deductible": 1000,
    "compulsory_deductible_note": "As per IRDAI for private cars",
    "pa_cover_owner_driver": 1500000,
    "pa_cover_note": "Mandatory as per Motor Vehicles Act 2019",
    "tp_bodily_injury": "Unlimited",
    "tp_property_damage": 750000,
    "tp_property_damage_note": "As per IRDAI guidelines",
    "driving_without_insurance_fine": 2000,
    "driving_without_insurance_imprisonment_months": 3,
    "fine_note": "As per Motor Vehicles (Amendment) Act 2019",
    "data_date": "2024-01",
    "source": "IRDAI Guidelines",
    "disclaimer": "Rates as per current IRDAI regulations"
}
"""

    response = _call_deepseek(prompt)

    # Default fallback data based on current IRDAI guidelines
    default_data = {
        "depreciation_rates": {
            "metal": {
                "0_to_6_months": 0,
                "6_months_to_1_year": 5,
                "1_to_2_years": 10,
                "2_to_3_years": 15,
                "3_to_4_years": 25,
                "4_to_5_years": 30,
                "5_to_10_years": 35,
                "above_10_years": 40
            },
            "plastic_rubber_fibre": 50,
            "paint": 30,
            "glass": 0,
            "tyres_tubes": 50,
            "batteries": 50
        },
        "parts_breakdown": {
            "plastic_percentage": 30,
            "metal_percentage": 50,
            "paint_percentage": 15,
            "labour_percentage": 5
        },
        "compulsory_deductible": 1000,
        "compulsory_deductible_note": "As per IRDAI for private cars",
        "pa_cover_owner_driver": 1500000,
        "pa_cover_note": "Mandatory as per Motor Vehicles Act 2019",
        "tp_bodily_injury": "Unlimited",
        "tp_property_damage": 750000,
        "tp_property_damage_note": "As per IRDAI guidelines",
        "driving_without_insurance_fine": 2000,
        "driving_without_insurance_imprisonment_months": 3,
        "fine_note": "As per Motor Vehicles (Amendment) Act 2019",
        "data_date": datetime.now().strftime("%Y-%m"),
        "source": "IRDAI Guidelines (default)",
        "disclaimer": "Rates as per current IRDAI regulations"
    }

    if response:
        try:
            # Clean response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()

            data = json.loads(clean_response)
            data["source"] = "deepseek_live"
            data["fetched_at"] = datetime.now().isoformat()
            _set_cache(cache_key, data)
            logger.info(f"🚗 Motor Insurance: Fetched live market data - Compulsory Deductible: ₹{data.get('compulsory_deductible')}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepSeek response: {e}")

    logger.warning("🚗 Motor Insurance: Using default market data")
    default_data["source"] = "default_fallback"
    _set_cache(cache_key, default_data)
    return default_data


def get_health_insurance_market_data() -> Dict[str, Any]:
    """
    Fetch live Indian market data for health insurance reports:
    - City-wise healthcare costs (room rent, ICU, surgeries)
    - Average room rent in metro and tier-2 cities
    - Medical inflation rate
    - Recommended sum insured amounts
    """
    cache_key = _get_cache_key("health_insurance")
    cached_data = _get_cache(cache_key)
    if cached_data:
        logger.info("🏥 Health Insurance: Using cached market data")
        return cached_data

    prompt = """
Provide the current Indian healthcare market data for health insurance analysis:

1. Average daily hospital room rent in major Indian cities (private room rates)
2. ICU daily charges in metros
3. Cost ranges for common surgeries/treatments in metros vs tier-2 cities
4. Medical inflation rate in India
5. Recommended health insurance sum insured for different profiles

Respond ONLY with valid JSON in this exact format:
{
    "metro_healthcare_costs": {
        "room_rent_avg": 8000,
        "icu_avg": 25000,
        "cardiac_surgery": [400000, 800000],
        "cancer_treatment": [1000000, 2500000],
        "knee_replacement": [250000, 400000],
        "normal_delivery": [80000, 150000],
        "csection": [150000, 300000],
        "appendectomy": [80000, 150000],
        "tier": "Tier-1 Metro"
    },
    "tier2_healthcare_costs": {
        "room_rent_avg": 5000,
        "icu_avg": 15000,
        "cardiac_surgery": [300000, 600000],
        "cancer_treatment": [800000, 1800000],
        "knee_replacement": [180000, 300000],
        "normal_delivery": [50000, 100000],
        "csection": [100000, 200000],
        "appendectomy": [50000, 100000],
        "tier": "Tier-2 City"
    },
    "city_healthcare_costs": {
        "mumbai": {
            "room_rent_avg": 10000,
            "icu_avg": 30000
        },
        "delhi": {
            "room_rent_avg": 8000,
            "icu_avg": 25000
        },
        "bangalore": {
            "room_rent_avg": 8000,
            "icu_avg": 25000
        },
        "chennai": {
            "room_rent_avg": 6000,
            "icu_avg": 20000
        },
        "kolkata": {
            "room_rent_avg": 5000,
            "icu_avg": 18000
        },
        "hyderabad": {
            "room_rent_avg": 6000,
            "icu_avg": 22000
        },
        "pune": {
            "room_rent_avg": 7000,
            "icu_avg": 22000
        }
    },
    "medical_inflation_rate": 14,
    "medical_inflation_note": "Annual healthcare cost increase in India",
    "recommended_sum_insured": {
        "senior_citizen": 2500000,
        "family_with_children": 1500000,
        "individual_young": 1000000,
        "note": "Based on current healthcare costs in metros"
    },
    "tier1_cities": ["mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", "kolkata", "pune", "gurgaon", "noida"],
    "data_date": "2024-01",
    "source": "Industry estimates based on hospital data",
    "disclaimer": "Costs are indicative and vary by hospital and location"
}
"""

    response = _call_deepseek(prompt)

    # Default fallback data
    default_data = {
        "metro_healthcare_costs": {
            "room_rent_avg": 8000,
            "icu_avg": 25000,
            "cardiac_surgery": [400000, 800000],
            "cancer_treatment": [1000000, 2500000],
            "knee_replacement": [250000, 400000],
            "normal_delivery": [80000, 150000],
            "csection": [150000, 300000],
            "appendectomy": [80000, 150000],
            "tier": "Tier-1 Metro"
        },
        "tier2_healthcare_costs": {
            "room_rent_avg": 5000,
            "icu_avg": 15000,
            "cardiac_surgery": [300000, 600000],
            "cancer_treatment": [800000, 1800000],
            "knee_replacement": [180000, 300000],
            "normal_delivery": [50000, 100000],
            "csection": [100000, 200000],
            "appendectomy": [50000, 100000],
            "tier": "Tier-2 City"
        },
        "city_healthcare_costs": {
            "mumbai": {
                "room_rent_avg": 10000,
                "icu_avg": 30000
            },
            "delhi": {
                "room_rent_avg": 8000,
                "icu_avg": 25000
            },
            "bangalore": {
                "room_rent_avg": 8000,
                "icu_avg": 25000
            },
            "chennai": {
                "room_rent_avg": 6000,
                "icu_avg": 20000
            },
            "kolkata": {
                "room_rent_avg": 5000,
                "icu_avg": 18000
            },
            "hyderabad": {
                "room_rent_avg": 6000,
                "icu_avg": 22000
            },
            "pune": {
                "room_rent_avg": 7000,
                "icu_avg": 22000
            }
        },
        "medical_inflation_rate": 14,
        "medical_inflation_note": "Annual healthcare cost increase in India",
        "recommended_sum_insured": {
            "senior_citizen": 2500000,
            "family_with_children": 1500000,
            "individual_young": 1000000,
            "note": "Based on current healthcare costs in metros"
        },
        "tier1_cities": ["mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", "kolkata", "pune", "gurgaon", "noida"],
        "data_date": datetime.now().strftime("%Y-%m"),
        "source": "Industry estimates (default)",
        "disclaimer": "Costs are indicative and vary by hospital and location"
    }

    if response:
        try:
            # Clean response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            clean_response = clean_response.strip()

            data = json.loads(clean_response)
            data["source"] = "deepseek_live"
            data["fetched_at"] = datetime.now().isoformat()
            _set_cache(cache_key, data)
            logger.info(f"🏥 Health Insurance: Fetched live market data - Medical Inflation: {data.get('medical_inflation_rate')}%")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepSeek response: {e}")

    logger.warning("🏥 Health Insurance: Using default market data")
    default_data["source"] = "default_fallback"
    _set_cache(cache_key, default_data)
    return default_data


# Helper functions to get specific values
def get_ppf_rate() -> float:
    """Get current PPF rate"""
    data = get_life_insurance_market_data()
    return data.get("ppf_rate", 7.1)


def get_bank_fd_rate() -> float:
    """Get average bank FD rate"""
    data = get_life_insurance_market_data()
    fd_rates = data.get("bank_fd_rates", {})
    return fd_rates.get("average", 7.0)


def get_survival_benefit_rate() -> float:
    """Get standard survival benefit rate"""
    data = get_life_insurance_market_data()
    return data.get("survival_benefit_rate", 8.0)


def get_metal_depreciation_rate(vehicle_age: float) -> int:
    """Get metal depreciation rate based on vehicle age"""
    data = get_motor_insurance_market_data()
    metal_rates = data.get("depreciation_rates", {}).get("metal", {})

    if vehicle_age < 0.5:
        return metal_rates.get("0_to_6_months", 0)
    elif vehicle_age < 1:
        return metal_rates.get("6_months_to_1_year", 5)
    elif vehicle_age < 2:
        return metal_rates.get("1_to_2_years", 10)
    elif vehicle_age < 3:
        return metal_rates.get("2_to_3_years", 15)
    elif vehicle_age < 4:
        return metal_rates.get("3_to_4_years", 25)
    elif vehicle_age < 5:
        return metal_rates.get("4_to_5_years", 30)
    elif vehicle_age < 10:
        return metal_rates.get("5_to_10_years", 35)
    else:
        return metal_rates.get("above_10_years", 40)


def get_parts_breakdown() -> Dict[str, int]:
    """Get parts breakdown percentages"""
    data = get_motor_insurance_market_data()
    return data.get("parts_breakdown", {
        "plastic_percentage": 30,
        "metal_percentage": 50,
        "paint_percentage": 15,
        "labour_percentage": 5
    })


def get_compulsory_deductible() -> int:
    """Get compulsory deductible amount"""
    data = get_motor_insurance_market_data()
    return data.get("compulsory_deductible", 1000)


def get_pa_cover_amount() -> int:
    """Get PA cover amount for owner-driver"""
    data = get_motor_insurance_market_data()
    return data.get("pa_cover_owner_driver", 1500000)


def get_tp_property_damage_limit() -> int:
    """Get third party property damage limit"""
    data = get_motor_insurance_market_data()
    return data.get("tp_property_damage", 750000)


def get_driving_fine_details() -> Dict[str, Any]:
    """Get driving without insurance fine details"""
    data = get_motor_insurance_market_data()
    return {
        "fine": data.get("driving_without_insurance_fine", 2000),
        "imprisonment_months": data.get("driving_without_insurance_imprisonment_months", 3),
        "note": data.get("fine_note", "As per Motor Vehicles (Amendment) Act 2019")
    }


def get_city_healthcare_costs(city: str) -> Dict[str, Any]:
    """Get comprehensive healthcare costs for a specific city (for health insurance reports)"""
    data = get_health_insurance_market_data()
    city_costs = data.get("city_healthcare_costs", {})
    metro_costs = data.get("metro_healthcare_costs", {})
    tier2_costs = data.get("tier2_healthcare_costs", {})
    tier1_cities = data.get("tier1_cities", ["mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad", "kolkata", "pune", "gurgaon", "noida"])

    # Normalize city name
    city_lower = city.lower().strip() if city else "metro"

    # Check if it's a tier-1 city
    is_metro = any(tier1 in city_lower for tier1 in tier1_cities)

    # Get base costs based on city tier
    base_costs = metro_costs if is_metro else tier2_costs

    # Get city-specific room rent if available
    city_specific = city_costs.get(city_lower, {})

    # Build the response matching the format expected by health_insurance_report_generator
    return {
        "room_rent_avg": city_specific.get("room_rent_avg", base_costs.get("room_rent_avg", 5000)),
        "icu_avg": city_specific.get("icu_avg", base_costs.get("icu_avg", 15000)),
        "cardiac_surgery": tuple(base_costs.get("cardiac_surgery", [400000, 800000])),
        "cancer_treatment": tuple(base_costs.get("cancer_treatment", [1000000, 2500000])),
        "knee_replacement": tuple(base_costs.get("knee_replacement", [250000, 400000])),
        "normal_delivery": tuple(base_costs.get("normal_delivery", [80000, 150000])),
        "csection": tuple(base_costs.get("csection", [150000, 300000])),
        "appendectomy": tuple(base_costs.get("appendectomy", [80000, 150000])),
        "tier": base_costs.get("tier", "Tier-1 Metro" if is_metro else "Tier-2 City")
    }


def get_recommended_sum_insured(profile_type: str = "individual") -> int:
    """Get recommended sum insured based on profile type"""
    data = get_health_insurance_market_data()
    recommendations = data.get("recommended_sum_insured", {})

    profile_lower = profile_type.lower()
    if "senior" in profile_lower or "elderly" in profile_lower or "60" in profile_lower:
        return recommendations.get("senior_citizen", 2500000)
    elif "family" in profile_lower or "children" in profile_lower:
        return recommendations.get("family_with_children", 1500000)
    else:
        return recommendations.get("individual_young", 1000000)


def get_medical_inflation_rate() -> float:
    """Get medical inflation rate"""
    data = get_health_insurance_market_data()
    return data.get("medical_inflation_rate", 14)


def clear_market_data_cache():
    """Clear all cached market data"""
    global _market_data_cache, _cache_expiry
    _market_data_cache = {}
    _cache_expiry = {}
    logger.info("🗑️ Market data cache cleared")


def get_all_market_data() -> Dict[str, Any]:
    """Get all market data for debugging/admin purposes"""
    return {
        "life_insurance": get_life_insurance_market_data(),
        "motor_insurance": get_motor_insurance_market_data(),
        "health_insurance": get_health_insurance_market_data()
    }
