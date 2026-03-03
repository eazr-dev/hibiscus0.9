from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import logging
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from io import BytesIO
import openai
from datetime import datetime
import os
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
# from report_genrate import create_insurance_analysis_pdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Unified Insurance Protection Score Analyzer",
    description="AI-powered insurance policy analysis with AIPS, HIPS, and LIPS scoring frameworks",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

logger.info(f"OpenAI API Key loaded: {OPENAI_API_KEY[:20]}..." if OPENAI_API_KEY else "No API key found")

# Pydantic models for request/response
class AnalysisParameters(BaseModel):
    vehicle_market_value: Optional[float] = 500000
    annual_income: Optional[float] = 600000

class PolicyComparisonResponse(BaseModel):
    comparison_summary: Dict[str, Any]
    individual_results: List[Dict[str, Any]]
    total_policies: int

def safe_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_str(value, default=''):
    return str(value) if value is not None else default

# ==================== DATA CLASSES ====================

# Auto Insurance Data Classes
@dataclass
class AutoPolicyData:
    vehicle_value: float = 0.0
    idv_amount: float = 0.0
    annual_premium: float = 0.0
    vehicle_age: int = 0
    vehicle_make: str = ""
    vehicle_model: str = ""
    registration_number: str = ""
    engine_number: str = ""
    chassis_number: str = ""
    
    # Vehicle Protection (40 points)
    idv_efficiency: str = "unknown"
    zero_depreciation_coverage: str = "none"
    engine_protection: str = "none"
    return_to_invoice: str = "none"
    consumables_coverage: str = "none"
    electrical_coverage: str = "none"
    cng_lpg_coverage: str = "none"
    vintage_coverage: str = "none"
    weather_protection: str = "none"
    tyre_protection: str = "none"
    paint_protection: str = "none"
    
    # Personal Protection (15 points)
    owner_pa_coverage: float = 0.0
    passenger_pa_coverage: str = "none"
    paid_driver_liability: str = "none"
    
    # Third-party Coverage (20 points)
    tp_property_damage: float = 0.0
    tp_bodily_injury: str = "unlimited"
    commercial_use_coverage: str = "none"
    geographic_coverage: str = "domestic"
    
    # Additional Benefits (15 points)
    key_replacement: str = "none"
    ncb_protection: str = "none"
    roadside_assistance: str = "none"
    towing_distance: str = "none"
    transport_allowance: float = 0.0
    telematics_discount: str = "none"
    antitheft_discount: str = "none"
    garage_network: int = 0
    
    # Cost Efficiency (10 points)
    deductible_options: str = "none"
    multi_year_policy: str = "none"
    mileage_discount: str = "none"
    membership_discount: str = "none"
    premium_vs_idv_ratio: float = 0.0
    
    # Company and Service Quality
    insurer_name: str = ""
    policy_name: str = ""
    claim_settlement_ratio: float = 90.0
    network_garages: int = 0
    service_quality: str = "average"
    cashless_approval_rate: float = 90.0
    
    extraction_confidence: float = 0.0

@dataclass
class AutoUserData:
    owner_name: str = ""
    date_of_birth: str = ""
    age: int = 0
    license_number: str = ""
    aadhar_number: str = ""
    pan_number: str = ""
    policy_number: str = ""
    policy_start_date: str = ""
    policy_end_date: str = ""
    mobile_number: str = ""
    email_id: str = ""
    address: str = ""
    vehicle_registration: str = ""
    vehicle_make_model: str = ""
    manufacturing_year: int = 0
    fuel_type: str = ""
    cc_capacity: int = 0
    seating_capacity: int = 0
    nominee_details: Dict = field(default_factory=dict)
    driving_experience: int = 0

# Health Insurance Data Classes
@dataclass
class HealthPolicyData:
    sum_insured: float = 0.0
    annual_premium: float = 0.0
    room_rent_limit: str = "unknown"
    icu_coverage: str = "unknown"
    daycare_procedures: int = 0
    pre_hospitalization_days: int = 0
    post_hospitalization_days: int = 0
    critical_illness_count: int = 0
    ped_waiting_period: int = 4
    maternity_coverage: str = "not_available"
    maternity_waiting_period: int = 4
    disease_sublimits: int = 10
    copayment_percentage: float = 0.0
    ambulance_coverage: float = 0.0
    ayush_coverage: str = "none"
    domiciliary_days: int = 0
    organ_donor_coverage: bool = False
    restoration_benefit: str = "none"
    ncb_percentage: float = 0.0
    network_hospital_count: int = 0
    hospital_quality: str = "average"
    cashless_approval_rate: float = 90.0
    claim_settlement_ratio: float = 90.0
    claim_turnaround_days: int = 15
    zone_efficiency: str = "good"
    wellness_program: str = "none"
    preventive_checkup: str = "none"
    inflation_adjustment: str = "none"
    insurer_name: str = ""
    policy_name: str = ""
    extraction_confidence: float = 0.0

@dataclass
class HealthUserData:
    user_name: str = ""
    date_of_birth: str = ""
    age: int = 0
    aadhar_number: str = ""
    pan_number: str = ""
    policy_number: str = ""
    policy_start_date: str = ""
    policy_end_date: str = ""
    mobile_number: str = ""
    email_id: str = ""
    address: str = ""
    family_members: List[Dict] = field(default_factory=list)
    family_count: int = 0
    nominee_details: Dict = field(default_factory=dict)
    sum_insured_per_member: float = 0.0

# Life Insurance Data Classes
@dataclass
class LifePolicyData:
    # Coverage Adequacy (40 points)
    sum_assured: float = 0.0
    annual_income: float = 0.0
    coverage_duration: str = "unknown"
    policy_type: str = "unknown"
    accidental_death_multiplier: float = 0.0
    terminal_illness_coverage: str = "none"
    disability_coverage: str = "none"
    income_replacement_ratio: float = 0.0
    inflation_adjustment: str = "none"
    
    # Policy Structure (25 points)
    term_investment_ratio: str = "unknown"
    premium_payment_term: str = "unknown"
    loan_coverage_ratio: float = 0.0
    convertibility_options: str = "none"
    policy_flexibility: str = "none"
    
    # Riders & Add-ons (20 points)
    critical_illness_rider: str = "none"
    accident_disability_rider: str = "none"
    hospital_cash_rider: float = 0.0
    waiver_of_premium: str = "none"
    income_benefit_rider: float = 0.0
    
    # Financial Returns (10 points)
    paid_up_value_terms: str = "none"
    surrender_value_terms: str = "none"
    bonus_accumulation: str = "none"
    return_of_premium: str = "none"
    investment_track_record: str = "none"
    
    # Service Quality (5 points)
    claim_settlement_ratio: float = 95.0
    claim_settlement_time: str = "unknown"
    policy_revival_flexibility: str = "unknown"
    global_coverage: str = "domestic"
    
    # Company and Service Quality
    insurer_name: str = ""
    policy_name: str = ""
    network_hospitals: int = 0
    service_quality: str = "average"
    
    extraction_confidence: float = 0.0

@dataclass
class LifeUserData:
    policyholder_name: str = ""
    date_of_birth: str = ""
    age: int = 0
    gender: str = ""
    occupation: str = ""
    annual_income: float = 0.0
    policy_number: str = ""
    policy_start_date: str = ""
    policy_end_date: str = ""
    premium_amount: float = 0.0
    premium_frequency: str = ""
    mobile_number: str = ""
    email_id: str = ""
    address: str = ""
    nominee_details: Dict = field(default_factory=dict)
    nominee_relationship: str = ""
    medical_history: str = ""
    smoking_status: str = "unknown"
    existing_loans: float = 0.0
    dependents: int = 0
    marital_status: str = "unknown"
    life_stage: str = "unknown"

# ==================== PDF EXTRACTOR ====================

class PDFExtractor:
    """Advanced PDF text extraction using multiple methods"""
    
    def extract_text_pdfplumber(self, pdf_content: bytes) -> str:
        try:
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            logger.error(f"PDFPlumber extraction failed: {e}")
            return ""
    
    def extract_text_pymupdf(self, pdf_content: bytes) -> str:
        try:
            import fitz  # Make sure PyMuPDF is installed: pip install PyMuPDF
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text() + "\n"
            doc.close()
            return text
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed: {e}")
            return ""
    
    def extract_text_pypdf2(self, pdf_content: bytes) -> str:
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            return ""
    
    def extract_text(self, pdf_content: bytes) -> str:
        methods = [
            ('pdfplumber', self.extract_text_pdfplumber),
            ('pymupdf', self.extract_text_pymupdf),
            ('pypdf2', self.extract_text_pypdf2)
        ]
        
        texts = []
        for method_name, method_func in methods:
            text = method_func(pdf_content)
            if text and len(text.strip()) > 100:
                texts.append((method_name, text, len(text)))
        
        if texts:
            best_method, best_text, _ = max(texts, key=lambda x: x[2])
            logger.info(f"Best extraction method: {best_method}")
            return best_text
        
        logger.error("All PDF extraction methods failed")
        return ""

# ==================== INSURANCE TYPE DETECTOR ====================

class InsuranceTypeDetector:
    """
    Detect insurance type from extracted PDF text.
    Types: health, auto, life, travel
    """

    def __init__(self):
        self.auto_keywords = [
            'vehicle', 'car insurance', 'motor', 'idv', 'engine number',
            'chassis number', 'third party', 'zero depreciation',
            'roadside assistance', 'own damage', 'two wheeler', 'four wheeler'
        ]

        self.health_keywords = [
            'hospitalization', 'room rent', 'daycare', 'day care',
            'pre hospitalization', 'post hospitalization', 'maternity',
            'critical illness', 'ayush', 'domiciliary', 'copayment', 'co-payment',
            'network hospital', 'cashless treatment', 'family floater',
            'restore benefit', 'mediclaim', 'health insurance',
            'organ donor', 'icu charges', 'sum insured', 'waiting period'
        ]

        self.life_keywords = [
            'life insurance', 'sum assured', 'death benefit',
            'term insurance', 'whole life', 'endowment', 'ulip',
            'surrender value', 'paid up value', 'life assured'
        ]

        self.travel_keywords = [
            'travel insurance', 'trip cancellation', 'trip interruption',
            'trip delay', 'geographical scope', 'passport number',
            'checked-in baggage', 'loss of passport', 'repatriation of mortal remains',
            'medical evacuation', 'explore europe', 'explore asia', 'schengen'
        ]

    def detect_insurance_type(self, text: str) -> str:
        """
        Detect insurance type.
        Keyword scoring for health/auto/life/travel
        """
        text_lower = text.lower()

        # Travel detection
        travel_score = sum(1 for kw in self.travel_keywords if kw in text_lower)
        if travel_score >= 3:
            return 'travel'

        # Standard keyword scoring for health/auto/life
        auto_score = sum(1 for kw in self.auto_keywords if kw in text_lower)
        health_score = sum(1 for kw in self.health_keywords if kw in text_lower)
        life_score = sum(1 for kw in self.life_keywords if kw in text_lower)

        scores = {'auto': auto_score, 'health': health_score, 'life': life_score}
        detected_type = max(scores, key=scores.get)
        max_score = scores[detected_type]

        if max_score < 2:
            return 'unknown'

        return detected_type

# ==================== INTELLIGENT POLICY PARSER ====================

class IntelligentPolicyParser:
    """AI-enhanced parser for extracting structured data from policy text"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Company quality mapping
        self.auto_company_quality = {
            'bajaj allianz': {'quality': 'premium', 'network': 4000, 'settlement': 96.5},
            'hdfc ergo': {'quality': 'premium', 'network': 6500, 'settlement': 95.8},
            'icici lombard': {'quality': 'premium', 'network': 4500, 'settlement': 97.2},
            'tata aig': {'quality': 'good', 'network': 2800, 'settlement': 94.1},
            'reliance general': {'quality': 'good', 'network': 3200, 'settlement': 93.7},
            'new india assurance': {'quality': 'average', 'network': 2500, 'settlement': 91.2},
            'oriental insurance': {'quality': 'average', 'network': 2200, 'settlement': 90.8},
            'national insurance': {'quality': 'average', 'network': 2000, 'settlement': 89.5},
            'united india': {'quality': 'average', 'network': 1800, 'settlement': 88.9},
            'cholamandalam': {'quality': 'good', 'network': 3500, 'settlement': 94.8},
            'digit insurance': {'quality': 'good', 'network': 3000, 'settlement': 95.2},
            'acko': {'quality': 'good', 'network': 2500, 'settlement': 94.6}
        }
        
        self.health_company_quality = {
            'star health': {'quality': 'good', 'network': 9000, 'settlement': 94.2},
            'niva bupa': {'quality': 'good', 'network': 6500, 'settlement': 89.5},
            'icici lombard': {'quality': 'premium', 'network': 7000, 'settlement': 96.8},
            'hdfc ergo': {'quality': 'premium', 'network': 10000, 'settlement': 95.1},
            'bajaj allianz': {'quality': 'good', 'network': 6500, 'settlement': 93.4},
            'care health': {'quality': 'good', 'network': 6000, 'settlement': 92.1},
            'max bupa': {'quality': 'premium', 'network': 4000, 'settlement': 97.2},
            'apollo munich': {'quality': 'premium', 'network': 5000, 'settlement': 95.8},
            'religare': {'quality': 'average', 'network': 3500, 'settlement': 88.7},
            'new india': {'quality': 'average', 'network': 3000, 'settlement': 87.5}
        }
        
        self.life_company_quality = {
            'lic': {'quality': 'premium', 'settlement': 98.5, 'time': 'under_30'},
            'hdfc life': {'quality': 'premium', 'settlement': 98.2, 'time': 'under_30'},
            'icici prudential': {'quality': 'premium', 'settlement': 97.8, 'time': 'under_30'},
            'sbi life': {'quality': 'good', 'settlement': 96.5, 'time': '31_60'},
            'bajaj allianz': {'quality': 'good', 'settlement': 96.2, 'time': '31_60'},
            'max life': {'quality': 'good', 'settlement': 95.8, 'time': '31_60'},
            'tata aia': {'quality': 'good', 'settlement': 95.5, 'time': '31_60'},
            'birla sun life': {'quality': 'average', 'settlement': 94.2, 'time': '31_60'},
            'kotak life': {'quality': 'good', 'settlement': 95.1, 'time': '31_60'},
            'pnb metlife': {'quality': 'average', 'settlement': 93.8, 'time': 'over_60'},
            'aegon life': {'quality': 'average', 'settlement': 92.5, 'time': 'over_60'},
            'reliance nippon': {'quality': 'average', 'settlement': 91.8, 'time': 'over_60'}
        }
    
    def extract_numeric_value(self, text: str, pattern_list: List[str]) -> Optional[float]:
        """Extract numeric values with unit conversion"""
        multipliers = {'lakh': 100000, 'lakhs': 100000, 'l': 100000, 
                      'crore': 10000000, 'crores': 10000000, 'cr': 10000000}
        
        text_lower = text.lower()
        for pattern in pattern_list:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                for match in matches:
                    try:
                        value_str = str(match).replace(',', '').strip()
                        
                        if '%' in value_str:
                            return float(value_str.replace('%', ''))
                        
                        if any(word in value_str for word in ['no limit', 'unlimited', 'nil']):
                            return 0.0
                        
                        numeric_match = re.search(r'(\d+(?:\.\d+)?)', value_str)
                        if numeric_match:
                            base_value = float(numeric_match.group(1))
                            
                            for unit, multiplier in multipliers.items():
                                if unit in text_lower:
                                    return base_value * multiplier
                            
                            return base_value
                    except (ValueError, AttributeError):
                        continue
        return None

    def extract_string_value(self, text: str, pattern_list: List[str]) -> Optional[str]:
        """Extract string values using regex patterns"""
        for pattern in pattern_list:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return str(matches[0]).strip()
        return None
    
    def optimize_gpt_extraction(self, text: str, insurance_type: str) -> Dict[str, Any]:
        """Optimized GPT extraction with reduced token usage"""
        if not self.openai_api_key:
            return {}
        
        # Truncate text to reduce tokens
        truncated_text = text[:4000]
        
        if insurance_type == 'auto':
            prompt = f"""Extract auto insurance data as JSON. Use null for missing values:
    {{
    "vehicle": {{
        "idv_amount": float,
        "premium": float,
        "make": string,
        "model": string,
        "registration": "XX00XX0000",
        "manufacturing_year": int,
        "fuel_type": "petrol|diesel|cng|electric",
        "zero_depreciation_years": int,
        "engine_protection": "comprehensive|basic|none",
        "pa_cover_lakhs": float
    }},
    "user": {{
        "name": string,
        "dob": "DD/MM/YYYY",
        "age": int,
        "license_no": string,
        "aadhar": "XXXX XXXX XXXX",
        "pan": "XXXXX1234X",
        "policy_no": string,
        "mobile": "10digits",
        "email": string
    }},
    "coverage": {{
        "third_party_property": float,
        "roadside_assistance": "comprehensive|basic|none",
        "ncb_protection": "full|partial|none",
        "insurer": string
    }}
    }}

    Text: {truncated_text}"""
        
        elif insurance_type == 'health':
            prompt = f"""Extract health insurance data as JSON. Use null for missing values:
    {{
    "policy": {{
        "sum_insured": float,
        "premium": float,
        "room_rent_limit": "no_limit|5%|3%|2%|1%",
        "daycare_count": int,
        "copay_percent": float,
        "ambulance_amount": float,
        "insurer": string,
        "waiting_period_years": int
    }},
    "user": {{
        "name": string,
        "dob": "DD/MM/YYYY",
        "age": int,
        "aadhar": "XXXX XXXX XXXX",
        "pan": "XXXXX1234X",
        "policy_no": string,
        "mobile": "10digits",
        "email": string,
        "family_size": int
    }}
    }}

    Text: {truncated_text}"""
        
        elif insurance_type == 'life':
            prompt = f"""Extract life insurance data as JSON. Use null for missing values:
    {{
    "coverage": {{
        "sum_assured": float,
        "annual_premium": float,
        "policy_type": "term|ulip|endowment|whole_life",
        "coverage_duration": "lifetime|extended|good|standard",
        "accidental_death_multiplier": float,
        "critical_illness_count": int,
        "terminal_illness_coverage": "comprehensive|good|moderate|limited|none",
        "disability_coverage": "premium_waiver+income|premium_waiver|limited|none"
    }},
    "user": {{
        "name": string,
        "dob": "DD/MM/YYYY",
        "age": int,
        "gender": "male|female",
        "occupation": string,
        "annual_income": float,
        "policy_no": string,
        "mobile": "10digits",
        "email": string,
        "smoking_status": "yes|no",
        "nominee": string
    }},
    "policy_features": {{
        "inflation_adjustment": "automatic|optional|none",
        "convertibility": "multiple|limited|none",
        "waiver_of_premium": "death_disability_illness|death_only|none",
        "hospital_cash_daily": float,
        "insurer": string
    }}
    }}

    Text: {truncated_text}"""
        
        try:
            # Updated for OpenAI 1.0.0+
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Extract JSON only. Be concise."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=3000
            )
            
            result_text = response.choices[0].message.content.strip()
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]
            
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"GPT extraction failed: {e}")
            return {}
    
    def parse_auto_insurance(self, text: str) -> Tuple[AutoPolicyData, AutoUserData]:
        """Parse auto insurance policy text"""
        gpt_data = self.optimize_gpt_extraction(text, 'auto')
        
        policy_data = AutoPolicyData()
        user_data = AutoUserData()
        
        # Policy data mapping
        if gpt_data.get('vehicle'):
            gpt_vehicle = gpt_data['vehicle']
            
            policy_data.idv_amount = safe_float(gpt_vehicle.get('idv_amount'))
            policy_data.annual_premium = safe_float(gpt_vehicle.get('premium'))
            policy_data.vehicle_make = safe_str(gpt_vehicle.get('make'))
            policy_data.vehicle_model = safe_str(gpt_vehicle.get('model'))
            policy_data.registration_number = safe_str(gpt_vehicle.get('registration'))
            
            years = gpt_vehicle.get('zero_depreciation_years')
            if years:
                policy_data.zero_depreciation_coverage = f"{years}_years"
            
            policy_data.engine_protection = safe_str(gpt_vehicle.get('engine_protection'))
            policy_data.owner_pa_coverage = safe_float(gpt_vehicle.get('pa_cover_lakhs'))
        
        if gpt_data.get('coverage'):
            gpt_coverage = gpt_data['coverage']
            policy_data.tp_property_damage = safe_float(gpt_coverage.get('third_party_property'))
            policy_data.roadside_assistance = safe_str(gpt_coverage.get('roadside_assistance'))
            policy_data.ncb_protection = safe_str(gpt_coverage.get('ncb_protection'))
            policy_data.insurer_name = safe_str(gpt_coverage.get('insurer'))
        
        # User data mapping
        if gpt_data.get('user'):
            gpt_user = gpt_data['user']
            user_data.owner_name = safe_str(gpt_user.get('name'))
            user_data.date_of_birth = safe_str(gpt_user.get('dob'))
            user_data.age = safe_int(gpt_user.get('age'))
            user_data.license_number = safe_str(gpt_user.get('license_no'))
            user_data.aadhar_number = safe_str(gpt_user.get('aadhar'))
            user_data.pan_number = safe_str(gpt_user.get('pan'))
            user_data.policy_number = safe_str(gpt_user.get('policy_no'))
            user_data.mobile_number = safe_str(gpt_user.get('mobile'))
            user_data.email_id = safe_str(gpt_user.get('email'))
        
        # Set company quality
        if policy_data.insurer_name and policy_data.insurer_name.lower() in self.auto_company_quality:
            company_info = self.auto_company_quality[policy_data.insurer_name.lower()]
            policy_data.service_quality = company_info['quality']
            policy_data.network_garages = company_info['network']
            policy_data.claim_settlement_ratio = company_info['settlement']
        
        if policy_data.idv_amount > 0 and policy_data.vehicle_make:
            policy_data.idv_efficiency = "good"
        
        # Calculate vehicle age
        if gpt_data.get('vehicle', {}).get('manufacturing_year'):
            year = safe_int(gpt_data['vehicle']['manufacturing_year'])
            if year > 0:
                user_data.manufacturing_year = year
                policy_data.vehicle_age = datetime.now().year - year
        
        # Set extraction confidence
        all_extracted = {**gpt_data.get('vehicle', {}), **gpt_data.get('user', {}), **gpt_data.get('coverage', {})}
        filled_fields = sum(1 for value in all_extracted.values() if value)
        policy_data.extraction_confidence = filled_fields / max(len(all_extracted), 1)
        
        return policy_data, user_data
    
    def parse_health_insurance(self, text: str) -> Tuple[HealthPolicyData, HealthUserData]:
        """Parse health insurance policy text"""
        gpt_data = self.optimize_gpt_extraction(text, 'health')
        print('dddddddddddd',gpt_data)
        
        policy_data = HealthPolicyData()
        user_data = HealthUserData()
        
        # Policy data mapping
        if gpt_data.get('policy'):
            gpt_policy = gpt_data['policy']
            
            policy_data.sum_insured = safe_float(gpt_policy.get('sum_insured'))
            policy_data.annual_premium = safe_float(gpt_policy.get('premium'))
            policy_data.room_rent_limit = safe_str(gpt_policy.get('room_rent_limit'))
            policy_data.daycare_procedures = safe_int(gpt_policy.get('daycare_count'))
            policy_data.ped_waiting_period = safe_int(gpt_policy.get('waiting_period_years', 4))
            policy_data.copayment_percentage = safe_float(gpt_policy.get('copay_percent'))
            policy_data.ambulance_coverage = safe_float(gpt_policy.get('ambulance_amount'))
            policy_data.insurer_name = safe_str(gpt_policy.get('insurer'))
        
        # User data mapping
        if gpt_data.get('user'):
            gpt_user = gpt_data['user']
            user_data.user_name = safe_str(gpt_user.get('name'))
            user_data.date_of_birth = safe_str(gpt_user.get('dob'))
            user_data.age = safe_int(gpt_user.get('age'))
            user_data.aadhar_number = safe_str(gpt_user.get('aadhar'))
            user_data.pan_number = safe_str(gpt_user.get('pan'))
            user_data.policy_number = safe_str(gpt_user.get('policy_no'))
            user_data.mobile_number = safe_str(gpt_user.get('mobile'))
            user_data.email_id = safe_str(gpt_user.get('email'))
            user_data.family_count = safe_int(gpt_user.get('family_size', 1))
        
        # Set company quality
        if policy_data.insurer_name and policy_data.insurer_name.lower() in self.health_company_quality:
            company_info = self.health_company_quality[policy_data.insurer_name.lower()]
            policy_data.hospital_quality = company_info['quality']
            policy_data.network_hospital_count = company_info['network']
            policy_data.claim_settlement_ratio = company_info['settlement']
        
        # Set extraction confidence
        all_extracted = {**gpt_data.get('policy', {}), **gpt_data.get('user', {})}
        filled_fields = sum(1 for value in all_extracted.values() if value)
        policy_data.extraction_confidence = filled_fields / max(len(all_extracted), 1)
        
        return policy_data, user_data
    
    def parse_life_insurance(self, text: str) -> Tuple[LifePolicyData, LifeUserData]:
        """Parse life insurance policy text"""
        gpt_data = self.optimize_gpt_extraction(text, 'life')
        
        policy_data = LifePolicyData()
        user_data = LifeUserData()
        
        # Policy data mapping
        if gpt_data.get('coverage'):
            gpt_coverage = gpt_data['coverage']
            
            policy_data.sum_assured = safe_float(gpt_coverage.get('sum_assured'))
            policy_data.annual_income = safe_float(gpt_coverage.get('annual_income'))
            policy_data.policy_type = safe_str(gpt_coverage.get('policy_type'))
            policy_data.coverage_duration = safe_str(gpt_coverage.get('coverage_duration'))
            policy_data.accidental_death_multiplier = safe_float(gpt_coverage.get('accidental_death_multiplier'))
            policy_data.terminal_illness_coverage = safe_str(gpt_coverage.get('terminal_illness_coverage'))
            policy_data.disability_coverage = safe_str(gpt_coverage.get('disability_coverage'))
            
            ci_count = safe_int(gpt_coverage.get('critical_illness_count'))
            if ci_count >= 25:
                policy_data.critical_illness_rider = "25+_illnesses"
            elif ci_count >= 20:
                policy_data.critical_illness_rider = "20_24"
            elif ci_count >= 15:
                policy_data.critical_illness_rider = "15_19"
            elif ci_count >= 10:
                policy_data.critical_illness_rider = "10_14"
            elif ci_count >= 5:
                policy_data.critical_illness_rider = "5_9"
            elif ci_count > 0:
                policy_data.critical_illness_rider = "limited"
        
        if gpt_data.get('policy_features'):
            gpt_features = gpt_data['policy_features']
            policy_data.inflation_adjustment = safe_str(gpt_features.get('inflation_adjustment'))
            policy_data.convertibility_options = safe_str(gpt_features.get('convertibility'))
            policy_data.waiver_of_premium = safe_str(gpt_features.get('waiver_of_premium'))
            policy_data.hospital_cash_rider = safe_float(gpt_features.get('hospital_cash_daily'))
            policy_data.insurer_name = safe_str(gpt_features.get('insurer'))
        
        # User data mapping
        if gpt_data.get('user'):
            gpt_user = gpt_data['user']
            user_data.policyholder_name = safe_str(gpt_user.get('name'))
            user_data.date_of_birth = safe_str(gpt_user.get('dob'))
            user_data.age = safe_int(gpt_user.get('age'))
            user_data.gender = safe_str(gpt_user.get('gender'))
            user_data.occupation = safe_str(gpt_user.get('occupation'))
            user_data.annual_income = safe_float(gpt_user.get('annual_income'))
            user_data.policy_number = safe_str(gpt_user.get('policy_no'))
            user_data.mobile_number = safe_str(gpt_user.get('mobile'))
            user_data.email_id = safe_str(gpt_user.get('email'))
            user_data.smoking_status = safe_str(gpt_user.get('smoking_status'))
            
            if gpt_user.get('nominee'):
                user_data.nominee_details = {'name': gpt_user.get('nominee')}
        
        # Calculate income replacement ratio
        if policy_data.sum_assured > 0 and policy_data.annual_income > 0:
            policy_data.income_replacement_ratio = (policy_data.sum_assured / policy_data.annual_income) * 100
        elif policy_data.sum_assured > 0 and user_data.annual_income > 0:
            policy_data.income_replacement_ratio = (policy_data.sum_assured / user_data.annual_income) * 100
        
        # Map policy type for scoring
        policy_type_lower = policy_data.policy_type.lower()
        if 'term' in policy_type_lower:
            policy_data.term_investment_ratio = "pure_term"
        elif 'ulip' in policy_type_lower:
            policy_data.term_investment_ratio = "ulip_high"
        elif 'endowment' in policy_type_lower:
            policy_data.term_investment_ratio = "endowment"
        elif 'whole' in policy_type_lower:
            policy_data.term_investment_ratio = "term_with_return"
        
        # Determine life stage
        if user_data.age > 0:
            if user_data.age <= 35:
                user_data.life_stage = "young_professional"
            elif user_data.age <= 50:
                user_data.life_stage = "peak_earning"
            elif user_data.age <= 60:
                user_data.life_stage = "pre_retirement"
            else:
                user_data.life_stage = "post_retirement"
        
        # Set company quality
        if policy_data.insurer_name and policy_data.insurer_name.lower() in self.life_company_quality:
            company_info = self.life_company_quality[policy_data.insurer_name.lower()]
            policy_data.service_quality = company_info['quality']
            policy_data.claim_settlement_ratio = company_info['settlement']
            policy_data.claim_settlement_time = company_info['time']
        
        # Set extraction confidence
        all_extracted = {**gpt_data.get('coverage', {}), **gpt_data.get('user', {}), **gpt_data.get('policy_features', {})}
        filled_fields = sum(1 for value in all_extracted.values() if value)
        policy_data.extraction_confidence = filled_fields / max(len(all_extracted), 1)
        
        return policy_data, user_data

# ==================== CALCULATORS ====================

class AIPSCalculator:
    """AIPS Calculator for Auto Insurance"""
    
    def calculate_aips_score(self, policy_data: AutoPolicyData, user_data: AutoUserData, vehicle_market_value: float = 500000) -> Dict:
        """Calculate complete AIPS score"""
        
        # 1. VEHICLE PROTECTION (40 Points Total)
        vehicle_score = 0
        
        # IDV vs Market Value Ratio (6 Points)
        if policy_data.idv_amount > 0 and vehicle_market_value > 0:
            idv_ratio = (policy_data.idv_amount / vehicle_market_value) * 100
            if idv_ratio >= 95:
                vehicle_score += 6
            elif idv_ratio >= 90:
                vehicle_score += 5
            elif idv_ratio >= 85:
                vehicle_score += 4
            elif idv_ratio >= 80:
                vehicle_score += 3
            elif idv_ratio >= 75:
                vehicle_score += 2
            else:
                vehicle_score += 1
        
        # Zero Depreciation Coverage (6 Points)
        if "5" in policy_data.zero_depreciation_coverage:
            vehicle_score += 6
        elif "3" in policy_data.zero_depreciation_coverage:
            vehicle_score += 5
        elif "2" in policy_data.zero_depreciation_coverage:
            vehicle_score += 4
        elif "1" in policy_data.zero_depreciation_coverage:
            vehicle_score += 3
        elif policy_data.zero_depreciation_coverage == "limited":
            vehicle_score += 2
        
        # Engine Protection Add-on (5 Points)
        engine_scores = {"comprehensive": 5, "engine_only": 4, "hydrostatic": 3, "basic": 2, "conditional": 1}
        vehicle_score += engine_scores.get(policy_data.engine_protection, 0)
        
        # Other vehicle protections (default scores)
        vehicle_score += 23  # Default for remaining categories
        vehicle_score = min(vehicle_score, 40)
        
        # 2. PERSONAL PROTECTION (15 Points Total)
        personal_score = 0
        
        if policy_data.owner_pa_coverage >= 15:
            personal_score += 6
        elif policy_data.owner_pa_coverage >= 10:
            personal_score += 5
        elif policy_data.owner_pa_coverage >= 5:
            personal_score += 4
        elif policy_data.owner_pa_coverage >= 2:
            personal_score += 3
        elif policy_data.owner_pa_coverage >= 1:
            personal_score += 2
        elif policy_data.owner_pa_coverage > 0:
            personal_score += 1
        
        personal_score += 9  # Default for other personal protection
        personal_score = min(personal_score, 15)
        
        # 3. THIRD-PARTY COVERAGE (20 Points Total)
        third_party_score = 0
        
        if policy_data.tp_property_damage == 0:  # Unlimited
            third_party_score += 12
        elif policy_data.tp_property_damage >= 750000:
            third_party_score += 10
        elif policy_data.tp_property_damage >= 500000:
            third_party_score += 8
        elif policy_data.tp_property_damage >= 250000:
            third_party_score += 6
        elif policy_data.tp_property_damage >= 100000:
            third_party_score += 4
        elif policy_data.tp_property_damage >= 100:
            third_party_score += 2
        
        third_party_score += 8  # Default for other third-party coverage
        third_party_score = min(third_party_score, 20)
        
        # 4. ADDITIONAL BENEFITS (15 Points Total)
        benefits_score = 0
        
        ncb_scores = {"full": 3, "partial": 2, "limited": 1}
        benefits_score += ncb_scores.get(policy_data.ncb_protection, 0)
        
        rsa_scores = {"comprehensive": 3, "good": 2, "basic": 1}
        benefits_score += rsa_scores.get(policy_data.roadside_assistance, 0)
        
        benefits_score += 9  # Default for other benefits
        benefits_score = min(benefits_score, 15)
        
        # 5. COST EFFICIENCY (10 Points Total)
        efficiency_score = 8  # Default efficiency score
        if policy_data.idv_amount > 0 and policy_data.annual_premium > 0:
            premium_ratio = (policy_data.annual_premium / policy_data.idv_amount) * 100
            if premium_ratio < 4:
                efficiency_score = 10
            elif premium_ratio <= 6:
                efficiency_score = 8
            else:
                efficiency_score = 6
        
        total_score = vehicle_score + personal_score + third_party_score + benefits_score + efficiency_score
        
        # Generate recommendations
        recommendations = self.generate_auto_recommendations(policy_data, user_data, total_score)
        
        # Determine protection level
        if total_score >= 90:
            protection_level = "Excellent Protection"
            general_recommendation = "Outstanding auto insurance policy! Maintain current coverage."
        elif total_score >= 75:
            protection_level = "Very Good Protection"
            general_recommendation = "Strong policy with minor gaps."
        elif total_score >= 60:
            protection_level = "Good Protection"
            general_recommendation = "Adequate coverage with some limitations."
        elif total_score >= 45:
            protection_level = "Fair Protection"
            general_recommendation = "Basic coverage with significant gaps."
        else:
            protection_level = "Poor Protection"
            general_recommendation = "Inadequate coverage. Policy upgrade recommended."
        
        return {
            'insurance_type': 'auto',
            'total_score': round(total_score, 1),
            'protection_level': protection_level,
            'general_recommendation': general_recommendation,
            'personalized_recommendations': recommendations,
            'extraction_confidence': round(policy_data.extraction_confidence * 100, 1),
            'category_scores': {
                'vehicle_protection': round(vehicle_score, 1),
                'personal_protection': round(personal_score, 1),
                'third_party_coverage': round(third_party_score, 1),
                'additional_benefits': round(benefits_score, 1),
                'cost_efficiency': round(efficiency_score, 1)
            },
            'policy_info': {
                'insurer_name': policy_data.insurer_name,
                'idv_amount': policy_data.idv_amount,
                'annual_premium': policy_data.annual_premium,
                'vehicle_make': policy_data.vehicle_make,
                'vehicle_model': policy_data.vehicle_model,
                'vehicle_age': policy_data.vehicle_age,
                'registration_number': policy_data.registration_number,
                'zero_depreciation': policy_data.zero_depreciation_coverage,
                'engine_protection': policy_data.engine_protection,
                'pa_coverage': policy_data.owner_pa_coverage,
                'roadside_assistance': policy_data.roadside_assistance,
                'ncb_protection': policy_data.ncb_protection
            },
            'user_info': {
                'name': user_data.owner_name,
                'age': user_data.age,
                'date_of_birth': user_data.date_of_birth,
                'license_number': user_data.license_number,
                'policy_number': user_data.policy_number,
                'mobile_number': user_data.mobile_number,
                'email_id': user_data.email_id,
                'aadhar_number': user_data.aadhar_number,
                'pan_number': user_data.pan_number,
                'manufacturing_year': user_data.manufacturing_year,
                'fuel_type': user_data.fuel_type
            }
        }
    
    def generate_auto_recommendations(self, policy_data: AutoPolicyData, user_data: AutoUserData, total_score: float) -> List[Dict[str, str]]:
        """Generate auto insurance recommendations"""
        recommendations = []
        
        # Age-based recommendations
        if user_data.age > 0:
            if user_data.age >= 50:
                recommendations.append({
                    "category": "Age-Specific Advice",
                    "recommendation": f"At age {user_data.age}, consider comprehensive coverage including enhanced personal accident benefits.",
                    "priority": "High"
                })
            elif user_data.age <= 25:
                recommendations.append({
                    "category": "Age-Specific Advice", 
                    "recommendation": f"Young drivers benefit from comprehensive engine protection and zero depreciation coverage.",
                    "priority": "Medium"
                })
        
        # Vehicle age recommendations
        if policy_data.vehicle_age >= 5:
            recommendations.append({
                "category": "Vehicle Age Considerations",
                "recommendation": f"Your {policy_data.vehicle_age}-year-old vehicle needs comprehensive engine protection.",
                "priority": "High"
            })
        elif policy_data.vehicle_age <= 2:
            recommendations.append({
                "category": "Vehicle Age Considerations",
                "recommendation": f"New vehicle - maximize zero depreciation coverage and return-to-invoice benefits.",
                "priority": "High"
            })
        
        # IDV adequacy recommendations
        if policy_data.idv_amount < 300000:
            recommendations.append({
                "category": "IDV Coverage",
                "recommendation": "Your IDV appears low for current market values. Consider increasing IDV.",
                "priority": "Critical"
            })
        
        # Zero depreciation recommendations
        if policy_data.zero_depreciation_coverage == "none":
            recommendations.append({
                "category": "Zero Depreciation",
                "recommendation": "Add zero depreciation coverage to avoid out-of-pocket expenses.",
                "priority": "High"
            })
        
        # Engine protection recommendations
        if policy_data.engine_protection == "none":
            recommendations.append({
                "category": "Engine Protection",
                "recommendation": "Engine protection is crucial for monsoon flooding and water damage.",
                "priority": "High"
            })
        
        return recommendations

class HIPSCalculator:
    """HIPS Calculator for Health Insurance"""
    
    def calculate_hips_score(self, policy_data: HealthPolicyData, user_data: HealthUserData, annual_income: float = 600000) -> Dict:
        """Calculate complete HIPS score"""
        
        # Coverage Adequacy (35 points)
        coverage_score = 0
        if policy_data.sum_insured > 0 and annual_income > 0:
            ratio = policy_data.sum_insured / annual_income
            if ratio >= 1.0:
                coverage_score += 8
            elif ratio >= 0.75:
                coverage_score += 6
            elif ratio >= 0.50:
                coverage_score += 4
            else:
                coverage_score += 2
        
        # Room rent scoring
        room_scores = {'no_limit': 6, '5%': 4, '3%': 3, '2%': 2, '1%': 1, 'unknown': 2}
        coverage_score += room_scores.get(policy_data.room_rent_limit, 2)
        
        # Daycare procedures
        if policy_data.daycare_procedures >= 200:
            coverage_score += 5
        elif policy_data.daycare_procedures >= 100:
            coverage_score += 3
        elif policy_data.daycare_procedures >= 50:
            coverage_score += 2
        else:
            coverage_score += 1
        
        coverage_score += 16  # Default for other coverage elements
        coverage_score = min(coverage_score, 35)
        
        # Waiting Periods (20 points)
        waiting_score = 0
        ped_scores = {0: 6, 1: 6, 2: 5, 3: 3, 4: 1}
        waiting_score += ped_scores.get(policy_data.ped_waiting_period, 0)
        
        if policy_data.copayment_percentage == 0:
            waiting_score += 5
        elif policy_data.copayment_percentage <= 10:
            waiting_score += 3
        else:
            waiting_score += 1
        
        waiting_score += 9  # Default for other waiting components
        waiting_score = min(waiting_score, 20)
        
        # Additional Benefits (20 points)
        benefits_score = 0
        if policy_data.ambulance_coverage >= 5000:
            benefits_score += 3
        elif policy_data.ambulance_coverage > 0:
            benefits_score += 2
        
        benefits_score += 17  # Default for other benefits
        benefits_score = min(benefits_score, 20)
        
        # Service Quality (15 points)
        service_score = 0
        if policy_data.network_hospital_count > 8000:
            service_score += 3
        elif policy_data.network_hospital_count > 5000:
            service_score += 2
        elif policy_data.network_hospital_count > 0:
            service_score += 1
        
        quality_scores = {'premium': 3, 'good': 2, 'average': 1, 'poor': 0}
        service_score += quality_scores.get(policy_data.hospital_quality, 1)
        
        if policy_data.claim_settlement_ratio >= 95:
            service_score += 3
        elif policy_data.claim_settlement_ratio >= 90:
            service_score += 2
        else:
            service_score += 1
        
        service_score += 6  # Default for other service components
        service_score = min(service_score, 15)
        
        # Cost Efficiency (10 points)
        efficiency_score = 8  # Default efficiency score
        
        total_score = coverage_score + waiting_score + benefits_score + service_score + efficiency_score
        
        # Generate recommendations
        recommendations = self.generate_health_recommendations(policy_data, user_data, total_score)
        
        # Determine protection level
        if total_score >= 90:
            protection_level = "Excellent Protection"
            general_recommendation = "Outstanding policy! Maintain current coverage."
        elif total_score >= 75:
            protection_level = "Very Good Protection"
            general_recommendation = "Strong policy with minor gaps."
        elif total_score >= 60:
            protection_level = "Good Protection"
            general_recommendation = "Adequate coverage with some limitations."
        elif total_score >= 45:
            protection_level = "Fair Protection"
            general_recommendation = "Basic coverage with significant gaps."
        else:
            protection_level = "Poor Protection"
            general_recommendation = "Inadequate coverage. Policy replacement recommended."
        
        return {
            'insurance_type': 'health',
            'total_score': round(total_score, 1),
            'protection_level': protection_level,
            'general_recommendation': general_recommendation,
            'personalized_recommendations': recommendations,
            'extraction_confidence': round(policy_data.extraction_confidence * 100, 1),
            'category_scores': {
                'coverage_adequacy': round(coverage_score, 1),
                'waiting_periods': round(waiting_score, 1),
                'additional_benefits': round(benefits_score, 1),
                'service_quality': round(service_score, 1),
                'cost_efficiency': round(efficiency_score, 1)
            },
            'policy_info': {
                'insurer_name': policy_data.insurer_name,
                'sum_insured': policy_data.sum_insured,
                'annual_premium': policy_data.annual_premium,
                'room_rent_limit': policy_data.room_rent_limit,
                'daycare_procedures': policy_data.daycare_procedures,
                'waiting_period': policy_data.ped_waiting_period,
                'copayment': policy_data.copayment_percentage,
                'ambulance_coverage': policy_data.ambulance_coverage
            },
            'user_info': {
                'name': user_data.user_name,
                'age': user_data.age,
                'date_of_birth': user_data.date_of_birth,
                'policy_number': user_data.policy_number,
                'mobile_number': user_data.mobile_number,
                'email_id': user_data.email_id,
                'aadhar_number': user_data.aadhar_number,
                'pan_number': user_data.pan_number,
                'family_count': user_data.family_count
            }
        }
    
    def generate_health_recommendations(self, policy_data: HealthPolicyData, user_data: HealthUserData, total_score: float) -> List[Dict[str, str]]:
        """Generate health insurance recommendations"""
        recommendations = []
        
        # Age-based recommendations
        if user_data.age >= 45:
            recommendations.append({
                "category": "Age-Specific Advice",
                "recommendation": f"At age {user_data.age}, consider increasing coverage as medical costs rise with age.",
                "priority": "High"
            })
        elif user_data.age <= 30:
            recommendations.append({
                "category": "Age-Specific Advice", 
                "recommendation": f"Great time to invest in comprehensive health insurance at age {user_data.age}.",
                "priority": "Medium"
            })
        
        # Coverage adequacy recommendations
        if policy_data.sum_insured < 500000:
            recommendations.append({
                "category": "Coverage Amount",
                "recommendation": "Your sum insured appears low. Consider increasing to at least 5 lakhs minimum.",
                "priority": "Critical"
            })
        
        # Room rent recommendations
        if policy_data.room_rent_limit not in ['no_limit', 'unknown']:
            recommendations.append({
                "category": "Room Rent Limit",
                "recommendation": f"Room rent capping may limit hospital choices. Consider upgrading to no-limit room rent.",
                "priority": "Medium"
            })
        
        # Waiting period recommendations
        if policy_data.ped_waiting_period >= 3:
            recommendations.append({
                "category": "Waiting Periods",
                "recommendation": f"{policy_data.ped_waiting_period}-year waiting period is high. Look for policies with shorter waiting periods.",
                "priority": "Medium"
            })
        
        return recommendations

class LIPSCalculator:
    """LIPS Calculator for Life Insurance"""
    
    def calculate_lips_score(self, policy_data: LifePolicyData, user_data: LifeUserData) -> Dict:
        """Calculate complete LIPS score"""
        
        # 1. COVERAGE ADEQUACY (40 Points Total)
        coverage_score = 0
        
        # Life Cover vs Annual Income Ratio (10 Points)
        income_for_calculation = policy_data.annual_income or user_data.annual_income
        if policy_data.sum_assured > 0 and income_for_calculation > 0:
            income_multiple = policy_data.sum_assured / income_for_calculation
            if income_multiple >= 20:
                coverage_score += 10
            elif income_multiple >= 15:
                coverage_score += 9
            elif income_multiple >= 12:
                coverage_score += 8
            elif income_multiple >= 10:
                coverage_score += 7
            elif income_multiple >= 8:
                coverage_score += 6
            elif income_multiple >= 5:
                coverage_score += 4
            elif income_multiple >= 3:
                coverage_score += 2
        
        # Coverage Duration (6 Points)
        duration_scores = {
            "lifetime": 6, "till_age_80+": 6,
            "extended": 5, "till_age_75-79": 5,
            "good": 4, "till_age_70-74": 4,
            "standard": 3, "till_age_65-69": 3,
            "basic": 2, "limited": 1
        }
        coverage_score += duration_scores.get(policy_data.coverage_duration, 0)
        
        # Accidental Death Benefit Multiplier (5 Points)
        if policy_data.accidental_death_multiplier >= 5:
            coverage_score += 5
        elif policy_data.accidental_death_multiplier >= 4:
            coverage_score += 4
        elif policy_data.accidental_death_multiplier >= 3:
            coverage_score += 3
        elif policy_data.accidental_death_multiplier >= 2:
            coverage_score += 2
        elif policy_data.accidental_death_multiplier >= 1.5:
            coverage_score += 1
        
        # Terminal Illness Coverage (5 Points)
        terminal_scores = {
            "comprehensive": 5, "100%_advance": 5,
            "good": 4, "75-99%_advance": 4,
            "moderate": 3, "50-74%_advance": 3,
            "limited": 2, "25-49%_advance": 2
        }
        coverage_score += terminal_scores.get(policy_data.terminal_illness_coverage, 0)
        
        # Disability Coverage Adequacy (6 Points)
        disability_scores = {
            "premium_waiver+income": 6,
            "premium_waiver+lump": 5,
            "premium_waiver": 4,
            "limited": 1
        }
        coverage_score += disability_scores.get(policy_data.disability_coverage, 0)
        
        # Other coverage components
        coverage_score += 8  # Default for remaining coverage elements
        coverage_score = min(coverage_score, 40)
        
        # 2. POLICY STRUCTURE (25 Points Total)
        structure_score = 0
        
        # Term vs Investment Component Ratio (8 Points)
        term_investment_scores = {
            "pure_term": 8,
            "term_with_return": 7,
            "ulip_high": 6,
            "endowment": 4,
            "ulip_low": 2,
            "pure_investment": 0
        }
        structure_score += term_investment_scores.get(policy_data.term_investment_ratio, 0)
        
        structure_score += 17  # Default for other structure components
        structure_score = min(structure_score, 25)
        
        # 3. RIDERS & ADD-ONS (20 Points Total)
        riders_score = 0
        
        # Critical Illness Rider (6 Points)
        ci_scores = {
            "25+_illnesses": 6,
            "20_24": 5,
            "15_19": 4,
            "10_14": 3,
            "5_9": 2,
            "limited": 1
        }
        riders_score += ci_scores.get(policy_data.critical_illness_rider, 0)
        
        # Hospital Cash Rider (3 Points)
        if policy_data.hospital_cash_rider >= 2000:
            riders_score += 3
        elif policy_data.hospital_cash_rider >= 1000:
            riders_score += 2
        elif policy_data.hospital_cash_rider >= 500:
            riders_score += 1
        
        # Waiver of Premium Benefit (4 Points)
        waiver_scores = {
            "death_disability_illness": 4,
            "death_disability": 3,
            "death_illness": 3,
            "death_only": 2,
            "disability_only": 2
        }
        riders_score += waiver_scores.get(policy_data.waiver_of_premium, 0)
        
        riders_score += 7  # Default for other riders
        riders_score = min(riders_score, 20)
        
        # 4. FINANCIAL RETURNS (10 Points Total)
        returns_score = 0
        
        if policy_data.policy_type.lower() in ['ulip', 'endowment', 'whole_life']:
            returns_score = 6  # Default for investment-linked policies
        
        returns_score = min(returns_score, 10)
        
        # 5. SERVICE QUALITY (5 Points Total)
        service_score = 0
        
        # Claim Settlement Ratio (2 Points)
        if policy_data.claim_settlement_ratio >= 98:
            service_score += 2
        elif policy_data.claim_settlement_ratio >= 95:
            service_score += 1.5
        elif policy_data.claim_settlement_ratio >= 90:
            service_score += 1
        
        service_score += 3  # Default for other service components
        service_score = min(service_score, 5)
        
        total_score = coverage_score + structure_score + riders_score + returns_score + service_score
        
        # Generate recommendations
        recommendations = self.generate_life_recommendations(policy_data, user_data, total_score)
        
        # Determine protection level
        if total_score >= 90:
            protection_level = "Excellent Protection"
            general_recommendation = "Outstanding life insurance coverage! Maintain current policy."
        elif total_score >= 75:
            protection_level = "Very Good Protection"
            general_recommendation = "Strong life insurance policy with minor gaps."
        elif total_score >= 60:
            protection_level = "Good Protection"
            general_recommendation = "Adequate coverage with some limitations."
        elif total_score >= 45:
            protection_level = "Fair Protection"
            general_recommendation = "Basic coverage with significant gaps."
        else:
            protection_level = "Poor Protection"
            general_recommendation = "Inadequate life insurance coverage. Immediate action required."
        
        return {
            'insurance_type': 'life',
            'total_score': round(total_score, 1),
            'protection_level': protection_level,
            'general_recommendation': general_recommendation,
            'personalized_recommendations': recommendations,
            'extraction_confidence': round(policy_data.extraction_confidence * 100, 1),
            'category_scores': {
                'coverage_adequacy': round(coverage_score, 1),
                'policy_structure': round(structure_score, 1),
                'riders_addons': round(riders_score, 1),
                'financial_returns': round(returns_score, 1),
                'service_quality': round(service_score, 1)
            },
            'policy_info': {
                'insurer_name': policy_data.insurer_name,
                'sum_assured': policy_data.sum_assured,
                'annual_income': income_for_calculation,
                'income_multiple': round(policy_data.sum_assured / income_for_calculation, 1) if income_for_calculation > 0 else 0,
                'policy_type': policy_data.policy_type,
                'coverage_duration': policy_data.coverage_duration,
                'accidental_death_multiplier': policy_data.accidental_death_multiplier,
                'critical_illness_rider': policy_data.critical_illness_rider,
                'terminal_illness_coverage': policy_data.terminal_illness_coverage,
                'disability_coverage': policy_data.disability_coverage,
                'waiver_of_premium': policy_data.waiver_of_premium
            },
            'user_info': {
                'name': user_data.policyholder_name,
                'age': user_data.age,
                'gender': user_data.gender,
                'occupation': user_data.occupation,
                'life_stage': user_data.life_stage,
                'annual_income': user_data.annual_income,
                'policy_number': user_data.policy_number,
                'mobile_number': user_data.mobile_number,
                'email_id': user_data.email_id,
                'smoking_status': user_data.smoking_status,
                'nominee_details': user_data.nominee_details
            }
        }
    
    def generate_life_recommendations(self, policy_data: LifePolicyData, user_data: LifeUserData, total_score: float) -> List[Dict[str, str]]:
        """Generate life insurance recommendations"""
        recommendations = []
        
        # Age-based recommendations
        if user_data.age <= 35:
            recommendations.append({
                "category": "Young Professional Strategy",
                "recommendation": f"At age {user_data.age}, focus on high coverage (15-20x income) with term insurance.",
                "priority": "High"
            })
        elif user_data.age <= 50:
            recommendations.append({
                "category": "Peak Earning Years",
                "recommendation": f"At age {user_data.age}, ensure 12-15x income coverage with comprehensive rider portfolio.",
                "priority": "High"
            })
        elif user_data.age <= 60:
            recommendations.append({
                "category": "Pre-Retirement Planning",
                "recommendation": f"At age {user_data.age}, focus on cash value optimization and estate planning features.",
                "priority": "Medium"
            })
        else:
            recommendations.append({
                "category": "Post-Retirement Focus",
                "recommendation": f"At age {user_data.age}, prioritize existing policy optimization and legacy planning.",
                "priority": "Medium"
            })
        
        # Coverage adequacy recommendations
        income_for_calculation = policy_data.annual_income or user_data.annual_income
        if income_for_calculation > 0:
            income_multiple = policy_data.sum_assured / income_for_calculation if policy_data.sum_assured > 0 else 0
            
            if income_multiple < 10:
                recommendations.append({
                    "category": "Coverage Adequacy",
                    "recommendation": f"Current coverage of {income_multiple:.1f}x income is insufficient. Increase to minimum 10-15x annual income.",
                    "priority": "Critical"
                })
        
        # Critical illness recommendations
        if policy_data.critical_illness_rider == "none":
            recommendations.append({
                "category": "Critical Illness Protection",
                "recommendation": "Add comprehensive critical illness rider covering 25+ diseases.",
                "priority": "High"
            })
        
        # Disability coverage recommendations
        if policy_data.disability_coverage == "none":
            recommendations.append({
                "category": "Disability Protection",
                "recommendation": "Add disability coverage with premium waiver and income benefit.",
                "priority": "High"
            })
        
        # Gender-specific recommendations
        if user_data.gender.lower() == "female":
            recommendations.append({
                "category": "Women-Specific Benefits",
                "recommendation": "Consider adding maternity benefits and women-specific illness coverage.",
                "priority": "Medium"
            })
        
        # Smoking status recommendations
        if user_data.smoking_status and "yes" in user_data.smoking_status.lower():
            recommendations.append({
                "category": "Smoking-Related Risks",
                "recommendation": "As a smoker, prioritize critical illness coverage for cancer, heart disease, and respiratory conditions.",
                "priority": "High"
            })
        
        return recommendations

# ==================== MAIN ANALYZER CLASS ====================

class UnifiedInsuranceAnalyzer:
    """Main analyzer class for all insurance types"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.pdf_extractor = PDFExtractor()
        self.type_detector = InsuranceTypeDetector()
        self.parser = IntelligentPolicyParser(openai_api_key)
        self.aips_calculator = AIPSCalculator()
        self.hips_calculator = HIPSCalculator()
        self.lips_calculator = LIPSCalculator()
        
    def analyze_pdf(self, pdf_content: bytes, vehicle_market_value: float = 500000, annual_income: float = 600000) -> Dict:
        """Analyze insurance PDF and return appropriate score"""
        try:
            # Extract text from PDF
            text = self.pdf_extractor.extract_text(pdf_content)
            
            if not text or len(text.strip()) < 100:
                raise ValueError("Failed to extract sufficient text from PDF")
            
            # Detect insurance type
            insurance_type = self.type_detector.detect_insurance_type(text)
            
            if insurance_type == 'unknown':
                return {
                    'error': 'Unable to determine insurance type',
                    'extracted_text_length': len(text),
                    'suggestion': 'Please ensure the PDF contains clear insurance policy information'
                }
            
            # Parse and calculate based on insurance type
            if insurance_type == 'auto':
                policy_data, user_data = self.parser.parse_auto_insurance(text)
                result = self.aips_calculator.calculate_aips_score(policy_data, user_data, vehicle_market_value)
            
            elif insurance_type == 'health':
                policy_data, user_data = self.parser.parse_health_insurance(text)
                result = self.hips_calculator.calculate_hips_score(policy_data, user_data, annual_income)
            
            elif insurance_type == 'life':
                policy_data, user_data = self.parser.parse_life_insurance(text)
                result = self.lips_calculator.calculate_lips_score(policy_data, user_data)
            
            # Add extraction metadata
            result['extraction_info'] = {
                'detected_type': insurance_type,
                'text_length': len(text),
                'timestamp': datetime.now().isoformat(),
                'gpt_usage': 'optimized'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")
            return {
                'error': f"Analysis failed: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }

# Initialize analyzer
analyzer = UnifiedInsuranceAnalyzer(openai_api_key=OPENAI_API_KEY)

# ==================== FASTAPI ROUTES ====================

@app.get("/", tags=["Info"])
async def home():
    """Home endpoint with API information"""
    return {
        "service": "Unified Insurance Protection Score Analyzer",
        "version": "2.0.0",
        "supported_types": ["Auto Insurance (AIPS)", "Health Insurance (HIPS)", "Life Insurance (LIPS)"],
        "endpoints": {
            "analyze": "/analyze-pdf",
            "analyze_with_params": "/analyze-pdf-with-params",
            "compare": "/compare-policies",
            "health": "/health",
            "info": "/info",
            "supported_types": "/supported-types"
        },
        "features": [
            "Automatic insurance type detection",
            "AI-powered data extraction",
            "Comprehensive scoring frameworks",
            "Personalized recommendations",
            "Cost-optimized processing"
        ]
    }

@app.post("/analyze-pdf", tags=["Analysis"])
async def analyze_insurance_pdf(
    file: UploadFile = File(...),
    vehicle_market_value: Optional[float] = Form(500000),
    annual_income: Optional[float] = Form(600000),
    generate_pdf: bool = Form(False)  # Add this parameter
):
    """
    Analyze insurance PDF and return comprehensive protection score
    
    Automatically detects insurance type and calculates appropriate score:
    - Auto Insurance: AIPS (Auto Insurance Protection Score)
    - Health Insurance: HIPS (Health Insurance Protection Score)  
    - Life Insurance: LIPS (Life Insurance Protection Score)
    
    Parameters:
    - file: PDF file containing insurance policy
    - vehicle_market_value: Current market value of vehicle (for auto insurance)
    - annual_income: Annual income for coverage adequacy calculation
    - generate_pdf: Set to true to return PDF report instead of JSON
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Read file content
        pdf_content = await file.read()
        
        if len(pdf_content) == 0:
            raise HTTPException(status_code=400, detail="Empty PDF file")
        
        # Analyze PDF with parameters
        result = analyzer.analyze_pdf(pdf_content, vehicle_market_value, annual_income)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Return PDF if requested, otherwise return JSON
        if generate_pdf:
            try:
                # Generate PDF report
                pdf_buffer = create_insurance_analysis_pdf(result)
                
                # Prepare filename
                insurance_type = result.get('insurance_type', 'insurance')
                user_name = result.get('user_info', {}).get('name', 'policy')
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{insurance_type}_{user_name}_{timestamp}_analysis.pdf".replace(' ', '_').replace('.', '')
                
                return StreamingResponse(
                    BytesIO(pdf_buffer.getvalue()),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={filename}"}
                )
            except Exception as pdf_error:
                logger.error(f"PDF generation failed: {pdf_error}")
                # Fall back to JSON response if PDF generation fails
                result['pdf_generation_error'] = str(pdf_error)
                return result
        else:
            return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/analyze-pdf-with-params", tags=["Analysis"])
async def analyze_insurance_pdf_with_params(
    file: UploadFile = File(...),
    parameters: str = Form(...)
):
    """
    Analyze insurance PDF with custom parameters as JSON string
    
    Parameters format:
    {
        "vehicle_market_value": 800000,
        "annual_income": 1200000
    }
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Parse parameters
        params = json.loads(parameters)
        vehicle_market_value = params.get('vehicle_market_value', 500000)
        annual_income = params.get('annual_income', 600000)
        
        # Read file content
        pdf_content = await file.read()
        
        if len(pdf_content) == 0:
            raise HTTPException(status_code=400, detail="Empty PDF file")
        
        # Analyze PDF with parameters
        result = analyzer.analyze_pdf(pdf_content, vehicle_market_value, annual_income)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in parameters")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/compare-policies", tags=["Analysis"])
async def compare_multiple_policies(
    files: List[UploadFile] = File(...),
    vehicle_market_value: Optional[float] = Form(500000),
    annual_income: Optional[float] = Form(600000)
):
    """
    Compare multiple insurance policies of the same type
    
    Maximum 5 policies can be compared at once.
    """
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 policies can be compared at once")
    
    try:
        results = []
        insurance_types = set()
        
        for i, file in enumerate(files):
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {i+1}: Only PDF files are allowed")
            
            pdf_content = await file.read()
            if len(pdf_content) == 0:
                raise HTTPException(status_code=400, detail=f"File {i+1}: Empty PDF file")
            
            # Analyze each policy
            result = analyzer.analyze_pdf(pdf_content, vehicle_market_value, annual_income)
            if 'error' in result:
                raise HTTPException(status_code=400, detail=f"File {i+1}: {result['error']}")
            
            result['file_name'] = file.filename
            result['policy_rank'] = i + 1
            results.append(result)
            insurance_types.add(result.get('insurance_type', 'unknown'))
        
        # Check if all policies are of the same type
        if len(insurance_types) > 1:
            raise HTTPException(
                status_code=400,
                detail={
                    'error': 'All policies must be of the same insurance type for comparison',
                    'detected_types': list(insurance_types)
                }
            )
        
        # Sort by score
        results.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Add comparative insights
        comparative_analysis = {
            "insurance_type": list(insurance_types)[0],
            "best_policy": {
                "file_name": results[0]['file_name'],
                "score": results[0]['total_score'],
                "strengths": results[0]['category_scores']
            },
            "score_range": {
                "highest": results[0]['total_score'],
                "lowest": results[-1]['total_score'],
                "spread": results[0]['total_score'] - results[-1]['total_score']
            },
            "category_leaders": {},
            "recommendations": []
        }
        
        # Find category leaders
        category_keys = list(results[0]['category_scores'].keys())
        for category in category_keys:
            best_in_category = max(results, key=lambda x: x['category_scores'][category])
            comparative_analysis['category_leaders'][category] = {
                "policy": best_in_category['file_name'],
                "score": best_in_category['category_scores'][category]
            }
        
        # Generate comparative recommendations
        if results[0]['total_score'] - results[-1]['total_score'] > 20:
            comparative_analysis['recommendations'].append({
                "type": "Clear Winner",
                "message": f"{results[0]['file_name']} significantly outperforms other policies."
            })
        
        return {
            "comparison_summary": comparative_analysis,
            "individual_results": results,
            "total_policies": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail="Policy comparison failed")
    

@app.post("/analyze-pdf-with-report", tags=["Analysis", "Reports"])
async def analyze_insurance_pdf_with_report(
    file: UploadFile = File(...),
    vehicle_market_value: Optional[float] = Form(500000),
    annual_income: Optional[float] = Form(600000),
    return_format: str = Form("json")  # "json" or "pdf"
):
    """
    Analyze insurance PDF and optionally return as PDF report
    
    Parameters:
    - file: PDF file containing insurance policy
    - vehicle_market_value: Current market value of vehicle (for auto insurance)
    - annual_income: Annual income for coverage adequacy calculation
    - return_format: "json" for JSON response, "pdf" for PDF report download
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Read file content
        pdf_content = await file.read()
        
        if len(pdf_content) == 0:
            raise HTTPException(status_code=400, detail="Empty PDF file")
        
        # Analyze PDF with parameters
        result = analyzer.analyze_pdf(pdf_content, vehicle_market_value, annual_income)
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Return based on format requested
        if return_format.lower() == "pdf":
            # Generate PDF report
            pdf_buffer = create_insurance_analysis_pdf(result)
            
            # Prepare filename
            insurance_type = result.get('insurance_type', 'insurance')
            user_name = result.get('user_info', {}).get('name', 'policy')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{insurance_type}_{user_name}_{timestamp}_analysis.pdf".replace(' ', '_').replace('.', '')
            
            return StreamingResponse(
                BytesIO(pdf_buffer.getvalue()),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # Return JSON response
            return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/generate-pdf-from-analysis", tags=["Reports"])
async def generate_pdf_from_analysis(analysis_data: dict):
    """
    Generate a professional PDF report from analysis data
    
    Args:
        analysis_data: The JSON response from any insurance analysis endpoint
        
    Returns:
        PDF file as downloadable response
    """
    try:
        # Generate PDF
        pdf_buffer = create_insurance_analysis_pdf(analysis_data)
        
        # Prepare filename
        insurance_type = analysis_data.get('insurance_type', 'insurance')
        user_name = analysis_data.get('user_info', {}).get('name', 'policy')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{insurance_type}_{user_name}_{timestamp}_analysis.pdf".replace(' ', '_').replace('.', '')
        
        return StreamingResponse(
            BytesIO(pdf_buffer.getvalue()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
    
    

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Unified Insurance Analyzer"
    }

@app.get("/info", tags=["Info"])
async def get_info():
    """Get information about all supported frameworks and scoring methodology"""
    return {
        "frameworks": {
            "AIPS": {
                "name": "Auto Insurance Protection Score",
                "total_points": 100,
                "categories": {
                    "vehicle_protection": {"points": 40, "description": "IDV efficiency, zero depreciation, engine protection"},
                    "personal_protection": {"points": 15, "description": "Owner/driver PA, passenger PA coverage"},
                    "third_party_coverage": {"points": 20, "description": "Property damage limit, commercial use coverage"},
                    "additional_benefits": {"points": 15, "description": "NCB protection, roadside assistance, towing"},
                    "cost_efficiency": {"points": 10, "description": "Premium ratios, deductible options, discounts"}
                }
            },
            "HIPS": {
                "name": "Health Insurance Protection Score",
                "total_points": 100,
                "categories": {
                    "coverage_adequacy": {"points": 35, "description": "Sum insured, room rent, daycare procedures"},
                    "waiting_periods": {"points": 20, "description": "PED waiting period, copayment terms"},
                    "additional_benefits": {"points": 20, "description": "Ambulance, AYUSH, wellness programs"},
                    "service_quality": {"points": 15, "description": "Network hospitals, claim settlement ratio"},
                    "cost_efficiency": {"points": 10, "description": "Premium vs coverage ratio, deductibles"}
                }
            },
            "LIPS": {
                "name": "Life Insurance Protection Score",
                "total_points": 100,
                "categories": {
                    "coverage_adequacy": {"points": 40, "description": "Income multiple, coverage duration, terminal illness"},
                    "policy_structure": {"points": 25, "description": "Term vs investment ratio, premium payment terms"},
                    "riders_addons": {"points": 20, "description": "Critical illness, accident disability, waiver of premium"},
                    "financial_returns": {"points": 10, "description": "Paid-up value, surrender terms, bonus accumulation"},
                    "service_quality": {"points": 5, "description": "Claim settlement ratio, revival flexibility"}
                }
            }
        },
        "scoring_bands": {
            "90-100": "Excellent Protection",
            "75-89": "Very Good Protection", 
            "60-74": "Good Protection",
            "45-59": "Fair Protection",
            "0-44": "Poor Protection"
        },
        "detection_process": {
            "step_1": "Extract text from PDF using multiple methods",
            "step_2": "Analyze keywords to detect insurance type",
            "step_3": "Apply appropriate parsing and scoring framework",
            "step_4": "Generate personalized recommendations"
        },
        "key_features": {
            "automatic_detection": "Identifies auto, health, or life insurance automatically",
            "ai_extraction": "Uses GPT for comprehensive data extraction",
            "personalized_recommendations": "Age, profile, and coverage-based suggestions",
            "cost_optimization": "Smart AI usage to minimize processing costs",
            "comprehensive_analysis": "40+ data points extracted and analyzed per policy type"
        }
    }

@app.get("/supported-types", tags=["Info"])
async def get_supported_types():
    """Get detailed information about supported insurance types"""
    return {
        "auto_insurance": {
            "framework": "AIPS (Auto Insurance Protection Score)",
            "key_extractions": [
                "Vehicle details (make, model, year, registration)",
                "IDV amount and premium details",
                "Coverage features (zero depreciation, engine protection)",
                "Personal accident coverage",
                "Third-party coverage limits",
                "Add-on benefits and riders"
            ],
            "scoring_focus": "Vehicle protection, personal safety, third-party liability, cost efficiency"
        },
        "health_insurance": {
            "framework": "HIPS (Health Insurance Protection Score)", 
            "key_extractions": [
                "Sum insured and premium amounts",
                "Room rent and daycare limits",
                "Waiting periods and copayment terms",
                "Network hospital count",
                "Pre-existing disease coverage",
                "Family member details"
            ],
            "scoring_focus": "Coverage adequacy, waiting periods, service quality, additional benefits"
        },
        "life_insurance": {
            "framework": "LIPS (Life Insurance Protection Score)",
            "key_extractions": [
                "Sum assured and income details",
                "Policy type and coverage duration", 
                "Riders (critical illness, accident, disability)",
                "Premium payment terms",
                "Nominee and beneficiary details",
                "Investment performance (for ULIPs/endowment)"
            ],
            "scoring_focus": "Coverage adequacy, policy structure, riders portfolio, financial returns"
        },
        "detection_keywords": {
            "auto": ["vehicle", "IDV", "engine number", "chassis number", "zero depreciation", "third party"],
            "health": ["hospitalization", "room rent", "daycare", "waiting period", "medical insurance"], 
            "life": ["sum assured", "death benefit", "term insurance", "life cover", "nominee", "maturity"]
        }
    }

