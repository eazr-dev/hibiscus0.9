# dynamic_universal_insurance_analyzer.py - FIXED VERSION
import os
import re
import json
from openai import OpenAI
from typing import Dict, List, Any, Optional, Tuple
import PyPDF2
import pdfplumber
from dataclasses import dataclass, asdict, field
from datetime import datetime
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UniversalInsuranceAnalysis:
    """Universal analysis for any insurance type"""
    # Basic Information
    insurance_type: str
    company_name: str
    policy_number: str
    premium_amount: float
    coverage_amount: float
    
    # Market Analysis
    market_average_premium: float
    premium_percentile: str
    value_for_money_score: float
    is_overpriced: bool
    potential_savings: float
    
    # Detailed Scoring (out of 100)
    coverage_adequacy_score: float
    pricing_competitiveness_score: float
    benefits_quality_score: float
    company_reputation_score: float
    overall_score: float
    
    # Verdict and Recommendations
    verdict: str
    verdict_explanation: str
    key_findings: List[str]
    specific_issues: List[str]
    actionable_recommendations: List[str]
    better_alternatives: List[Dict[str, Any]]
    
    # Type-specific details
    policy_details: Dict[str, Any]
    extracted_data: Dict[str, Any]
    analysis_timestamp: str

class UniversalDynamicAnalyzer:
    """Universal analyzer for Auto, Health, and Life Insurance - FIXED VERSION"""
    
    def __init__(self, openai_api_key: str = None):
        self.client = None
        self.ai_enabled = False
        
        # FIX 1: Proper API key validation and initialization
        if openai_api_key and openai_api_key != "your-api-key" and len(openai_api_key) > 20:
            try:
                self.client = OpenAI(api_key=openai_api_key)
                self.ai_enabled = True
                logger.info("AI extraction enabled with OpenAI")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}. Using regex extraction only.")
                self.client = None
                self.ai_enabled = False
        else:
            logger.info("AI extraction disabled - using regex extraction only")
        
        # Market data remains the same
        self.market_data = {
            'health': {
                'family_floater': {
                    'base_rates': {
                        'age_below_35': 2200,
                        'age_35_45': 3500,
                        'age_45_60': 5500,
                        'age_above_60': 8500
                    },
                    'company_multipliers': {
                        'HDFC ERGO': 1.1,
                        'Star Health': 0.95,
                        'ICICI Lombard': 1.05,
                        'Bajaj Allianz': 1.0,
                        'Care Health': 0.9,
                        'Niva Bupa': 1.15
                    }
                },
                'individual': {
                    'base_rates': {
                        'age_below_35': 1500,
                        'age_35_45': 2500,
                        'age_45_60': 4000,
                        'age_above_60': 6500
                    }
                }
            },
            'auto': {
                'comprehensive': {
                    'two_wheeler': {
                        'below_150cc': {'min': 2500, 'avg': 4000, 'max': 6000},
                        'above_150cc': {'min': 4000, 'avg': 7000, 'max': 12000}
                    },
                    'four_wheeler': {
                        'hatchback': {'min': 8000, 'avg': 15000, 'max': 25000},
                        'sedan': {'min': 12000, 'avg': 22000, 'max': 35000},
                        'suv': {'min': 18000, 'avg': 30000, 'max': 50000},
                        'luxury': {'min': 35000, 'avg': 60000, 'max': 100000}
                    },
                    'ncb_discounts': {0: 0, 20: 0.2, 25: 0.25, 35: 0.35, 45: 0.45, 50: 0.5}
                },
                'third_party': {
                    'two_wheeler': {'below_150cc': 750, 'above_150cc': 1200},
                    'four_wheeler': {'below_1000cc': 2500, '1000_1500cc': 3500, 'above_1500cc': 5000}
                }
            },
            'life': {
                'term': {
                    'per_crore_coverage': {
                        'age_below_30': {'smoker': 12000, 'non_smoker': 8000},
                        'age_30_40': {'smoker': 18000, 'non_smoker': 12000},
                        'age_40_50': {'smoker': 35000, 'non_smoker': 25000},
                        'age_above_50': {'smoker': 65000, 'non_smoker': 45000}
                    }
                },
                'endowment': {
                    'returns': 4.5,
                    'premium_multiplier': 3.5
                },
                'ulip': {
                    'returns': 8.5,
                    'charges': 4.0,
                    'premium_multiplier': 4.0
                }
            }
        }
        
        self.company_ratings = {
            'HDFC ERGO': {
                'claims_ratio': 95.2,
                'settlement_time': 7,
                'network_size': 13000,
                'customer_rating': 4.2,
                'financial_strength': 'AAA'
            },
            'ICICI Lombard': {
                'claims_ratio': 89.5,
                'settlement_time': 10,
                'network_size': 11000,
                'customer_rating': 4.0,
                'financial_strength': 'AAA'
            },
            'Star Health': {
                'claims_ratio': 91.0,
                'settlement_time': 8,
                'network_size': 14000,
                'customer_rating': 4.1,
                'financial_strength': 'AA+'
            },
            'Bajaj Allianz': {
                'claims_ratio': 87.5,
                'settlement_time': 12,
                'network_size': 9000,
                'customer_rating': 3.8,
                'financial_strength': 'AA'
            },
            'New India': {
                'claims_ratio': 85.0,
                'settlement_time': 15,
                'network_size': 15000,
                'customer_rating': 3.5,
                'financial_strength': 'A+'
            }
        }
    
    def extract_text_from_pdf_bytes(self, pdf_content: bytes) -> str:
        """Extract text from PDF bytes with error handling"""
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                    
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            text += "\n[TABLE]\n"
                            for row in table:
                                if row:
                                    text += " | ".join([str(cell) if cell else "" for cell in row]) + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying PyPDF2: {e}")
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted
            except Exception as e2:
                logger.error(f"All PDF extraction methods failed: {e2}")
        
        return text
    
    def detect_insurance_type(self, text: str) -> Tuple[str, str]:
        """
        Detect insurance type and subtype from text.
        Types: health, auto, life, travel
        """
        text_lower = text.lower()
        # Normalize: collapse whitespace and remove invisible chars for better matching
        import re as _re
        text_lower = _re.sub(r'[\u00ad\u200b\u200c\u200d\ufeff]', '', text_lower)
        text_lower = _re.sub(r'\s+', ' ', text_lower)

        # Travel detection — checked FIRST because travel policies from health
        # insurers (e.g. Care Health Explore Asia/Europe) contain many health
        # keywords that would otherwise win in the scoring below.
        travel_keywords = [
            'travel insurance', 'trip cancellation', 'trip interruption',
            'trip delay', 'trip curtailment', 'geographical scope', 'passport number',
            'checked-in baggage', 'loss of passport', 'repatriation of mortal remains',
            'medical evacuation', 'explore europe', 'explore asia', 'schengen',
            'baggage delay', 'baggage loss', 'flight delay', 'hijack',
            'country of travel', 'destination country', 'overseas medical',
            'overseas travel', 'international travel', 'personal liability overseas',
            'explore worldwide', 'travel guard', 'asia guard', 'asia guard gold',
            'compassionate visit', 'loss of travel documents', 'sponsor protection',
            'travel protect', 'travel shield', 'travel secure',
        ]
        travel_score = sum(1 for kw in travel_keywords if kw in text_lower)
        if travel_score >= 2:
            subtype = 'single' if 'single trip' in text_lower else ('multi' if 'multi trip' in text_lower else 'standard')
            logger.info(f"Type detection: Travel (score={travel_score}) → travel/{subtype}")
            return 'travel', subtype

        # Standard keyword scoring for health/auto/life
        health_keywords = [
            'hospitalization', 'room rent', 'day care', 'mediclaim',
            'pre hospitalization', 'post hospitalization', 'cashless treatment',
            'network hospital', 'family floater', 'ayush', 'domiciliary',
            'copayment', 'co-payment', 'sum insured', 'restore benefit',
            'maternity', 'critical illness', 'health insurance',
            'organ donor', 'icu charges', 'waiting period'
        ]
        health_score = sum(1 for kw in health_keywords if kw in text_lower)

        auto_keywords = [
            'vehicle', 'motor', 'car insurance', 'bike', 'two wheeler',
            'four wheeler', 'engine number', 'chassis number', 'idv',
            'own damage', 'third party liability', 'zero depreciation',
            'roadside assistance'
        ]
        auto_score = sum(1 for kw in auto_keywords if kw in text_lower)

        life_keywords = [
            'life insurance', 'term plan', 'death benefit', 'sum assured',
            'nominee', 'endowment', 'ulip', 'whole life',
            'surrender value', 'paid up value', 'life assured'
        ]
        life_score = sum(1 for kw in life_keywords if kw in text_lower)

        scores = {'health': health_score, 'auto': auto_score, 'life': life_score}
        insurance_type = max(scores, key=scores.get)

        # Determine subtype
        subtype = 'standard'
        if insurance_type == 'health':
            if 'family floater' in text_lower or 'floater' in text_lower:
                subtype = 'family_floater'
            elif 'individual' in text_lower:
                subtype = 'individual'
        elif insurance_type == 'auto':
            if 'comprehensive' in text_lower:
                subtype = 'comprehensive'
            elif 'third party' in text_lower:
                subtype = 'third_party'
        elif insurance_type == 'life':
            if 'term' in text_lower:
                subtype = 'term'
            elif 'endowment' in text_lower:
                subtype = 'endowment'
            elif 'ulip' in text_lower:
                subtype = 'ulip'

        logger.info(f"Type detection scores: health={health_score}, auto={auto_score}, life={life_score} → {insurance_type}/{subtype}")
        return insurance_type, subtype
    
    def ai_extract_data(self, text: str, insurance_type: str) -> Dict[str, Any]:
        """AI extraction helper - FIXED VERSION with PA support"""
        if not self.client or not self.ai_enabled:
            return {}

        try:
            # Truncate text if too long
            max_chars = 10000
            if len(text) > max_chars:
                text = text[:max_chars]

            # Type-specific extraction prompts
            if insurance_type == 'health':
                prompt = f"""Extract Health insurance data from this document.
Return ONLY valid JSON with these exact keys. Use 0 for missing numeric values, empty string for missing text:
{{
    "policy_number": "string",
    "premium": 0,
    "company": "string",
    "insured_name": "string",
    "coverage_amount": 0,
    "sum_insured": 0,
    "benefits": []
}}"""
            else:
                prompt = f"""Extract insurance data from this {insurance_type} document.
Return ONLY valid JSON with these exact keys. Use 0 for missing numeric values, empty string for missing text:
{{
    "policy_number": "string",
    "premium": 0,
    "company": "string",
    "insured_name": "string",
    "coverage_amount": 0,
    "members": [],
    "vehicle_details": {{}},
    "life_details": {{}},
    "benefits": []
}}

Document text:
{text}
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data extraction expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                timeout=10
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            
            ai_data = json.loads(content)
            
            # FIX 2: Validate and sanitize numeric values
            if 'premium' in ai_data:
                try:
                    ai_data['premium'] = float(ai_data['premium']) if ai_data['premium'] else 0
                except (ValueError, TypeError):
                    ai_data['premium'] = 0
            
            if 'coverage_amount' in ai_data:
                try:
                    ai_data['coverage_amount'] = float(ai_data['coverage_amount']) if ai_data['coverage_amount'] else 0
                except (ValueError, TypeError):
                    ai_data['coverage_amount'] = 0
            
            logger.info(f"AI extraction successful: premium={ai_data.get('premium', 0)}")
            return ai_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"AI returned invalid JSON: {e}")
            return {}
        except Exception as e:
            logger.warning(f"AI extraction failed: {e}")
            return {}
    
    def extract_universal_data(self, text: str, insurance_type: str) -> Dict[str, Any]:
        """Extract data with FIXED error handling"""
        data = {'raw_text_length': len(text)}
        
        # Try AI extraction first
        ai_data = {}
        if self.ai_enabled:
            ai_data = self.ai_extract_data(text, insurance_type)
        
        # FIX 3: Safe extraction with defaults
        def safe_float(value, default=0.0):
            """Safely convert to float"""
            if value is None or value == '':
                return default
            try:
                if isinstance(value, str):
                    value = value.replace(',', '').replace('', '').replace('Rs.', '').strip()
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # Extract policy number
        data['policy_number'] = ai_data.get('policy_number', '')
        if not data['policy_number']:
            match = re.search(r'Policy\s*(?:No|Number)\.?\s*:?\s*([A-Z0-9\-/]+)', text, re.IGNORECASE)
            if match:
                data['policy_number'] = match.group(1).strip()
        
        # Extract company
        data['company'] = ai_data.get('company', '')
        if not data['company']:
            company_pattern = r'(HDFC ERGO|ICICI Lombard|Bajaj Allianz|Star Health|New India|LIC|SBI Life|Max Life|Niva Bupa|Care Health)'
            match = re.search(company_pattern, text, re.IGNORECASE)
            if match:
                data['company'] = match.group(1)
        
        # FIX 4: Premium extraction with multiple fallbacks
        data['premium'] = safe_float(ai_data.get('premium', 0))
        
        if data['premium'] == 0:
            # Try multiple premium patterns
            premium_patterns = [
                r'Total\s+Premium.*?(?:|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)',
                r'Premium\s+Amount.*?(?:|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)',
                r'Annual\s+Premium.*?(?:|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)',
                r'(?:|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*(?:/-)?',
            ]
            
            for pattern in premium_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    premium_value = safe_float(match.group(1))
                    # Validate premium is reasonable
                    if insurance_type == 'health' and 1000 <= premium_value <= 500000:
                        data['premium'] = premium_value
                        break
                    elif insurance_type == 'auto' and 1000 <= premium_value <= 200000:
                        data['premium'] = premium_value
                        break
                    elif insurance_type == 'life' and 1000 <= premium_value <= 1000000:
                        data['premium'] = premium_value
                        break
        
        # Extract insured name
        data['insured_name'] = ai_data.get('insured_name', '')
        if not data['insured_name']:
            match = re.search(r'(?:Insured|Policy\s+Holder)\s*(?:Name)?\s*:?\s*([A-Z][A-Za-z\s]+)', text)
            if match:
                data['insured_name'] = match.group(1).strip()
        
        # Type-specific extraction
        if insurance_type == 'health':
            health_data = self._extract_health_data(text)
            if ai_data.get('coverage_amount'):
                health_data['sum_insured'] = safe_float(ai_data['coverage_amount'], 1000000)
            if ai_data.get('members'):
                health_data['members'] = ai_data['members']
                health_data['member_count'] = len(ai_data['members'])
            data.update(health_data)
        elif insurance_type == 'auto':
            data.update(self._extract_auto_data(text))
        elif insurance_type == 'life':
            data.update(self._extract_life_data(text))

        logger.info(f"Extracted data: premium={data.get('premium', 0)}, company={data.get('company', 'Unknown')}")
        return data
    
    def _extract_health_data(self, text: str) -> Dict[str, Any]:
        """Extract health insurance specific data with safe defaults"""
        data = {}
        
        # FIX 5: Safe numeric extraction helper
        def safe_extract_float(pattern, default=0):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    return value if value > 0 else default
                except (ValueError, TypeError):
                    return default
            return default
        
        # Sum insured with validation
        data['sum_insured'] = safe_extract_float(
            r'(?:Sum\s+Insured|Coverage\s+Amount).*?(?:|Rs\.?)?\s*([\d,]+)',
            1000000  # Default 10L
        )
        
        # If sum insured is unreasonably low, set to default
        if data['sum_insured'] < 100000:
            data['sum_insured'] = 1000000
        
        # Member details
        member_pattern = r'(\d{10,})\s+([A-Z][A-Za-z\s]+)\s+(\d{2}/\d{2}/\d{4})\s+(\d+)'
        members = []
        for match in re.finditer(member_pattern, text):
            try:
                members.append({
                    'id': match.group(1),
                    'name': match.group(2).strip(),
                    'dob': match.group(3),
                    'age': int(match.group(4))
                })
            except (ValueError, IndexError):
                continue
        
        data['members'] = members
        data['member_count'] = len(members) if members else 1
        
        # Benefits detection
        data['has_restore_benefit'] = 'restore benefit' in text.lower()
        data['has_cashless'] = 'cashless' in text.lower()
        data['room_rent_limit'] = 'single private' in text.lower()
        
        # Co-payment
        copay_match = re.search(r'Co[\-\s]*payment\s*:?\s*([\d]+)%', text, re.IGNORECASE)
        data['copayment'] = int(copay_match.group(1)) if copay_match else 0
        
        return data
    
    def _extract_auto_data(self, text: str) -> Dict[str, Any]:
        """Extract auto insurance specific data"""
        data = {}
        
        reg_match = re.search(r'Registration\s*(?:No|Number).*?([A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,2}\s*\d{1,4})', text)
        if reg_match:
            data['registration'] = reg_match.group(1)
        
        make_match = re.search(r'(?:Make/Model|Vehicle).*?:?\s*([^\n]+)', text)
        if make_match:
            data['vehicle_make_model'] = make_match.group(1).strip()
        
        idv_match = re.search(r'IDV.*?(?:|Rs\.?)?\s*([\d,]+)', text, re.IGNORECASE)
        if idv_match:
            try:
                data['idv'] = float(idv_match.group(1).replace(',', ''))
            except ValueError:
                data['idv'] = 500000  # Default
        
        ncb_match = re.search(r'NCB.*?(\d+)%', text, re.IGNORECASE)
        data['ncb_percentage'] = int(ncb_match.group(1)) if ncb_match else 0
        
        addons = []
        addon_keywords = ['zero depreciation', 'engine protection', 'roadside assistance', 
                         'key replacement', 'consumables cover']
        for addon in addon_keywords:
            if addon in text.lower():
                addons.append(addon)
        data['addons'] = addons
        
        return data
    
    def _extract_life_data(self, text: str) -> Dict[str, Any]:
        """Extract life insurance specific data"""
        data = {}
        
        sum_match = re.search(r'Sum\s+Assured.*?(?:|Rs\.?)?\s*([\d,]+)', text, re.IGNORECASE)
        if sum_match:
            try:
                data['sum_assured'] = float(sum_match.group(1).replace(',', ''))
            except ValueError:
                data['sum_assured'] = 10000000  # Default 1 Cr
        
        term_match = re.search(r'Policy\s+Term.*?(\d+)\s*(?:Years?|Yrs?)', text, re.IGNORECASE)
        data['policy_term'] = int(term_match.group(1)) if term_match else 20
        
        pay_match = re.search(r'Premium\s+(?:Paying\s+)?Term.*?(\d+)\s*(?:Years?|Yrs?)', text, re.IGNORECASE)
        data['premium_paying_term'] = int(pay_match.group(1)) if pay_match else 20
        
        nominee_match = re.search(r'Nominee.*?:?\s*([A-Z][A-Za-z\s]+)', text)
        if nominee_match:
            data['nominee'] = nominee_match.group(1).strip()
        
        riders = []
        rider_keywords = ['critical illness', 'accidental death', 'waiver of premium', 
                         'disability', 'income benefit']
        for rider in rider_keywords:
            if rider in text.lower():
                riders.append(rider)
        data['riders'] = riders
        
        return data
    
    def calculate_market_premium(self, insurance_type: str, subtype: str,
                                extracted_data: Dict) -> Dict[str, Any]:
        """Calculate expected market premium"""
        market_analysis = {
            'estimated_market_premium': 0,
            'market_range_min': 0,
            'market_range_max': 0,
            'factors_considered': []
        }
        
        if insurance_type == 'health':
            sum_insured = extracted_data.get('sum_insured', 1000000)
            member_count = extracted_data.get('member_count', 1)
            avg_age = 35
            
            if extracted_data.get('members'):
                ages = [m.get('age', 35) for m in extracted_data['members']]
                avg_age = sum(ages) / len(ages) if ages else 35
            
            if avg_age < 35:
                base_rate = self.market_data['health']['family_floater']['base_rates']['age_below_35']
            elif avg_age < 45:
                base_rate = self.market_data['health']['family_floater']['base_rates']['age_35_45']
            elif avg_age < 60:
                base_rate = self.market_data['health']['family_floater']['base_rates']['age_45_60']
            else:
                base_rate = self.market_data['health']['family_floater']['base_rates']['age_above_60']
            
            coverage_in_lakhs = sum_insured / 100000
            base_premium = base_rate * coverage_in_lakhs
            
            if member_count > 2:
                base_premium *= (1 + (member_count - 2) * 0.15)
            
            market_analysis['estimated_market_premium'] = base_premium
            market_analysis['market_range_min'] = base_premium * 0.8
            market_analysis['market_range_max'] = base_premium * 1.3
            market_analysis['factors_considered'] = [
                f"Sum Insured: {sum_insured:,.0f}",
                f"Members: {member_count}",
                f"Average Age: {avg_age:.0f} years"
            ]
            
        elif insurance_type == 'auto':
            idv = extracted_data.get('idv', 500000)
            ncb = extracted_data.get('ncb_percentage', 0)
            vehicle_type = 'sedan'
            
            if 'hatchback' in str(extracted_data.get('vehicle_make_model', '')).lower():
                vehicle_type = 'hatchback'
            elif 'suv' in str(extracted_data.get('vehicle_make_model', '')).lower():
                vehicle_type = 'suv'
            
            if subtype == 'comprehensive':
                market_rates = self.market_data['auto']['comprehensive']['four_wheeler'].get(
                    vehicle_type, {'avg': 20000}
                )
                base_premium = market_rates['avg']
                
                ncb_discount = self.market_data['auto']['comprehensive']['ncb_discounts'].get(ncb, 0)
                base_premium *= (1 - ncb_discount)
                
                market_analysis['estimated_market_premium'] = base_premium
                market_analysis['market_range_min'] = market_rates.get('min', base_premium * 0.7)
                market_analysis['market_range_max'] = market_rates.get('max', base_premium * 1.5)
            else:
                base_premium = 3500
                market_analysis['estimated_market_premium'] = base_premium
                market_analysis['market_range_min'] = 2500
                market_analysis['market_range_max'] = 5000
            
            market_analysis['factors_considered'] = [
                f"Vehicle Type: {vehicle_type}",
                f"IDV: {idv:,.0f}",
                f"NCB: {ncb}%"
            ]
            
        elif insurance_type == 'life':
            sum_assured = extracted_data.get('sum_assured', 10000000)
            age = 35
            policy_term = extracted_data.get('policy_term', 20)
            
            coverage_in_crores = sum_assured / 10000000
            
            if age < 30:
                base_rate = self.market_data['life']['term']['per_crore_coverage']['age_below_30']['non_smoker']
            elif age < 40:
                base_rate = self.market_data['life']['term']['per_crore_coverage']['age_30_40']['non_smoker']
            elif age < 50:
                base_rate = self.market_data['life']['term']['per_crore_coverage']['age_40_50']['non_smoker']
            else:
                base_rate = self.market_data['life']['term']['per_crore_coverage']['age_above_50']['non_smoker']
            
            base_premium = base_rate * coverage_in_crores
            
            if policy_term > 20:
                base_premium *= 1.2
            elif policy_term < 15:
                base_premium *= 0.8
            
            market_analysis['estimated_market_premium'] = base_premium
            market_analysis['market_range_min'] = base_premium * 0.7
            market_analysis['market_range_max'] = base_premium * 1.4
            market_analysis['factors_considered'] = [
                f"Sum Assured: {sum_assured:,.0f}",
                f"Policy Term: {policy_term} years"
            ]

        return market_analysis

    def evaluate_premium_value(self, actual_premium: float, market_analysis: Dict) -> Dict[str, Any]:
        """Evaluate if premium offers good value"""
        market_avg = market_analysis['estimated_market_premium']
        market_min = market_analysis['market_range_min']
        market_max = market_analysis['market_range_max']
        
        evaluation = {
            'actual_premium': actual_premium,
            'market_average': market_avg,
            'difference': actual_premium - market_avg,
            'percentage_difference': ((actual_premium - market_avg) / market_avg * 100) if market_avg > 0 else 0
        }
        
        if actual_premium < market_min * 0.8:
            evaluation['category'] = 'SUSPICIOUSLY_CHEAP'
            evaluation['score'] = 40
            evaluation['explanation'] = 'Premium is unusually low - verify coverage details carefully'
        elif actual_premium <= market_avg * 0.9:
            evaluation['category'] = 'EXCELLENT_VALUE'
            evaluation['score'] = 95
            evaluation['explanation'] = 'Premium is significantly below market average - great deal!'
        elif actual_premium <= market_avg * 1.1:
            evaluation['category'] = 'FAIR_VALUE'
            evaluation['score'] = 75
            evaluation['explanation'] = 'Premium is close to market average - reasonable pricing'
        elif actual_premium <= market_max:
            evaluation['category'] = 'EXPENSIVE'
            evaluation['score'] = 55
            evaluation['explanation'] = 'Premium is above average - consider shopping around'
        else:
            evaluation['category'] = 'OVERPRICED'
            evaluation['score'] = 35
            evaluation['explanation'] = 'Premium is significantly overpriced - strongly recommend switching'
        
        if actual_premium > market_avg:
            evaluation['potential_annual_savings'] = actual_premium - market_avg
            evaluation['potential_10year_savings'] = (actual_premium - market_avg) * 10
        else:
            evaluation['potential_annual_savings'] = 0
            evaluation['potential_10year_savings'] = 0
        
        return evaluation
    
    def calculate_comprehensive_score(self, insurance_type: str, extracted_data: Dict,
                                     premium_evaluation: Dict) -> Dict[str, Any]:
        """Calculate detailed scoring"""
        scores = {
            'coverage_adequacy': 0,
            'pricing_competitiveness': 0,
            'benefits_quality': 0,
            'company_reputation': 0
        }
        
        if insurance_type == 'health':
            sum_insured = extracted_data.get('sum_insured', 0)
            member_count = extracted_data.get('member_count', 1)
            per_person_coverage = sum_insured / member_count if member_count > 0 else 0
            
            if per_person_coverage >= 1000000:
                scores['coverage_adequacy'] = 90
            elif per_person_coverage >= 500000:
                scores['coverage_adequacy'] = 70
            elif per_person_coverage >= 300000:
                scores['coverage_adequacy'] = 50
            else:
                scores['coverage_adequacy'] = 30
                
        elif insurance_type == 'auto':
            if extracted_data.get('idv'):
                scores['coverage_adequacy'] = 80
            if extracted_data.get('addons'):
                scores['coverage_adequacy'] += len(extracted_data['addons']) * 5
            scores['coverage_adequacy'] = min(scores['coverage_adequacy'], 100)
            
        elif insurance_type == 'life':
            sum_assured = extracted_data.get('sum_assured', 0)
            if sum_assured >= 50000000:
                scores['coverage_adequacy'] = 95
            elif sum_assured >= 10000000:
                scores['coverage_adequacy'] = 75
            else:
                scores['coverage_adequacy'] = 50

        scores['pricing_competitiveness'] = premium_evaluation.get('score', 50)
        
        if insurance_type == 'health':
            benefit_score = 50
            if extracted_data.get('has_restore_benefit'):
                benefit_score += 20
            if extracted_data.get('has_cashless'):
                benefit_score += 15
            if not extracted_data.get('copayment'):
                benefit_score += 15
            scores['benefits_quality'] = min(benefit_score, 100)
        else:
            scores['benefits_quality'] = 70
        
        company = extracted_data.get('company', '')
        if company in self.company_ratings:
            rating = self.company_ratings[company]
            scores['company_reputation'] = (
                (rating['claims_ratio'] / 100) * 40 +
                (5 - rating['customer_rating']) * 10 +
                min(rating['network_size'] / 15000, 1) * 30 +
                (1 - rating['settlement_time'] / 30) * 20
            )
        else:
            scores['company_reputation'] = 60
        
        overall = (
            scores['coverage_adequacy'] * 0.3 +
            scores['pricing_competitiveness'] * 0.35 +
            scores['benefits_quality'] * 0.2 +
            scores['company_reputation'] * 0.15
        )
        
        scores['overall'] = overall
        
        if overall >= 80:
            verdict = 'EXCELLENT'
            explanation = 'This policy offers outstanding value and comprehensive protection'
        elif overall >= 65:
            verdict = 'GOOD'
            explanation = 'This policy provides solid coverage at a reasonable price'
        elif overall >= 50:
            verdict = 'FAIR'
            explanation = 'This policy is adequate but has room for improvement'
        else:
            verdict = 'POOR'
            explanation = 'This policy has significant gaps - consider alternatives'
        
        scores['verdict'] = verdict
        scores['verdict_explanation'] = explanation
        
        return scores
    
    def generate_actionable_recommendations(self, insurance_type: str, extracted_data: Dict,
                                          scores: Dict, premium_evaluation: Dict) -> Dict[str, Any]:
        """Generate specific recommendations"""
        recommendations = {
            'key_findings': [],
            'specific_issues': [],
            'actionable_recommendations': [],
            'better_alternatives': []
        }
        
        if scores['overall'] >= 70:
            recommendations['key_findings'].append("Policy offers good overall value")
        if scores['coverage_adequacy'] >= 80:
            recommendations['key_findings'].append("Coverage amount is adequate for your needs")
        if premium_evaluation['category'] in ['EXCELLENT_VALUE', 'FAIR_VALUE']:
            recommendations['key_findings'].append(f"Premium is {premium_evaluation['category'].replace('_', ' ').lower()}")
        
        if scores['coverage_adequacy'] < 60:
            recommendations['specific_issues'].append("Coverage amount is insufficient")
        if premium_evaluation['category'] in ['EXPENSIVE', 'OVERPRICED']:
            savings = premium_evaluation.get('potential_annual_savings', 0)
            recommendations['specific_issues'].append(f"Overpaying by {savings:,.0f} annually")
        
        if insurance_type == 'health':
            sum_insured = extracted_data.get('sum_insured', 0)
            if sum_insured < 1000000:
                recommendations['actionable_recommendations'].append(
                    f"URGENT: Increase sum insured from {sum_insured:,.0f} to at least 15,00,000"
                )
            
            if extracted_data.get('copayment', 0) > 10:
                recommendations['actionable_recommendations'].append(
                    "Negotiate to reduce or eliminate co-payment clause"
                )
            
            if not extracted_data.get('has_restore_benefit'):
                recommendations['actionable_recommendations'].append(
                    "Add Restore Benefit for 100% sum insured restoration"
                )
            
            market_avg = premium_evaluation.get('market_average', 20000)
            recommendations['better_alternatives'] = [
                {
                    'provider': 'Star Health Comprehensive',
                    'premium': market_avg * 0.9,
                    'benefits': '15L coverage, Restore benefit, No room rent limit',
                    'annual_savings': max(0, extracted_data.get('premium', 0) - market_avg * 0.9)
                },
                {
                    'provider': 'Care Supreme',
                    'premium': market_avg * 0.85,
                    'benefits': '10L coverage, Unlimited restoration, Global coverage',
                    'annual_savings': max(0, extracted_data.get('premium', 0) - market_avg * 0.85)
                }
            ]
            
        elif insurance_type == 'auto':
            if not extracted_data.get('addons') or 'zero depreciation' not in extracted_data.get('addons', []):
                recommendations['actionable_recommendations'].append(
                    "Add Zero Depreciation cover for claim without deduction"
                )
            
            ncb = extracted_data.get('ncb_percentage', 0)
            if ncb < 50:
                recommendations['actionable_recommendations'].append(
                    f"Maintain claim-free record to increase NCB from {ncb}% to 50%"
                )
            
        elif insurance_type == 'life':
            sum_assured = extracted_data.get('sum_assured', 0)
            if sum_assured < 10000000:
                recommendations['actionable_recommendations'].append(
                    "Increase sum assured to at least 1 crore (10-15x annual income)"
                )

            if not extracted_data.get('riders'):
                recommendations['actionable_recommendations'].append(
                    "Add Critical Illness and Accidental Death riders"
                )

        return recommendations
    
    def analyze_insurance_universal(self, pdf_content: bytes, filename: str) -> UniversalInsuranceAnalysis:
        """Main analysis function - FIXED VERSION"""
        try:
            text = self.extract_text_from_pdf_bytes(pdf_content)
            if not text:
                raise ValueError("Could not extract text from PDF")
            
            insurance_type, subtype = self.detect_insurance_type(text)
            logger.info(f"Detected insurance type: {insurance_type}, subtype: {subtype}")
            
            extracted_data = self.extract_universal_data(text, insurance_type)
            
            # FIX 6: Validate premium was extracted
            actual_premium = extracted_data.get('premium', 0)
            if actual_premium == 0 or actual_premium is None:
                raise ValueError(
                    f"Could not extract premium amount. Please ensure the PDF contains clear premium information. "
                    f"Extracted data: {extracted_data}"
                )
            
            logger.info(f"Extracted premium: {actual_premium:,.2f}")
            
            market_analysis = self.calculate_market_premium(insurance_type, subtype, extracted_data)
            premium_evaluation = self.evaluate_premium_value(actual_premium, market_analysis)
            scores = self.calculate_comprehensive_score(insurance_type, extracted_data, premium_evaluation)
            recommendations = self.generate_actionable_recommendations(
                insurance_type, extracted_data, scores, premium_evaluation
            )
            
            if insurance_type == 'health':
                coverage_amount = extracted_data.get('sum_insured', 0)
            elif insurance_type == 'auto':
                coverage_amount = extracted_data.get('idv', 0)
            elif insurance_type == 'life':
                coverage_amount = extracted_data.get('sum_assured', 0)
            else:
                coverage_amount = 0
            
            analysis = UniversalInsuranceAnalysis(
                insurance_type=insurance_type,
                company_name=extracted_data.get('company', 'Unknown'),
                policy_number=extracted_data.get('policy_number', 'N/A'),
                premium_amount=actual_premium,
                coverage_amount=coverage_amount,
                market_average_premium=market_analysis['estimated_market_premium'],
                premium_percentile=premium_evaluation['category'].replace('_', ' ').title(),
                value_for_money_score=premium_evaluation['score'],
                is_overpriced=premium_evaluation['category'] in ['EXPENSIVE', 'OVERPRICED'],
                potential_savings=premium_evaluation.get('potential_annual_savings', 0),
                coverage_adequacy_score=scores['coverage_adequacy'],
                pricing_competitiveness_score=scores['pricing_competitiveness'],
                benefits_quality_score=scores['benefits_quality'],
                company_reputation_score=scores['company_reputation'],
                overall_score=scores['overall'],
                verdict=scores['verdict'],
                verdict_explanation=scores['verdict_explanation'],
                key_findings=recommendations['key_findings'],
                specific_issues=recommendations['specific_issues'],
                actionable_recommendations=recommendations['actionable_recommendations'],
                better_alternatives=recommendations['better_alternatives'],
                policy_details={
                    'insurance_type': insurance_type,
                    'subtype': subtype,
                    'premium': actual_premium,
                    'coverage': coverage_amount,
                    **extracted_data
                },
                extracted_data=extracted_data,
                analysis_timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"Analysis complete. Overall score: {scores['overall']:.1f}/100")
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            raise

# Usage function
def analyze_any_insurance(pdf_content: bytes, filename: str, openai_api_key: str = None) -> Dict[str, Any]:
    """Analyze any type of insurance - FIXED VERSION
    
    Args:
        pdf_content: PDF file content as bytes
        filename: Name of the file
        openai_api_key: Optional OpenAI API key for AI-enhanced extraction
    
    Returns:
        Dictionary with analysis results
    """
    try:
        analyzer = UniversalDynamicAnalyzer(openai_api_key=openai_api_key)
        result = analyzer.analyze_insurance_universal(pdf_content, filename)
        
        response = {
            'success': True,
            'insurance_type': result.insurance_type,
            'company_name': result.company_name,
            'policy_number': result.policy_number,
            'premium_amount': result.premium_amount,
            'coverage_amount': result.coverage_amount,
            'recommendation_score': result.overall_score,
            'verdict': result.verdict,
            'verdict_explanation': result.verdict_explanation,
            'is_good_value': result.overall_score >= 65,
            'is_overpriced': result.is_overpriced,
            'potential_savings': result.potential_savings,
            'market_comparison': {
                'your_premium': result.premium_amount,
                'market_average': result.market_average_premium,
                'value_category': result.premium_percentile,
                'value_score': result.value_for_money_score
            },
            'detailed_scores': {
                'coverage_adequacy': result.coverage_adequacy_score,
                'pricing': result.pricing_competitiveness_score,
                'benefits': result.benefits_quality_score,
                'company': result.company_reputation_score,
                'overall': result.overall_score
            },
            'suggestions': result.actionable_recommendations,
            'alternatives': result.better_alternatives,
            'key_findings': result.key_findings,
            'issues': result.specific_issues,
            'analysis_data': result.extracted_data,
            'summary': f"Your {result.insurance_type} insurance from {result.company_name} scores {result.overall_score:.0f}/100 ({result.verdict}). " + 
                      (f"You can save {result.potential_savings:,.0f}/year by switching." if result.potential_savings > 0 else "Premium is competitively priced.")
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to analyze insurance document. Please check if the PDF is valid and contains readable insurance information.'
        }
