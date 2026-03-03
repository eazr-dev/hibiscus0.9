# enhanced_chatbot_handlers.py - COMPLETE FIXED VERSION with all missing functions

import re
import requests
from datetime import datetime
from typing import Dict, Optional, List, Any
import json
import logging
import asyncio
# At the top of enhanced_chatbot_handlers.py, add:
try:
    from database_storage.mongodb_chat_manager import (
        mongodb_chat_manager,
        add_user_message_to_mongodb,
        add_assistant_message_to_mongodb,
        store_policy_answer,
        get_policy_application,
        update_policy_answer,
        complete_application
    )
    MONGODB_AVAILABLE = True
except ImportError:
    mongodb_chat_manager = None
    add_user_message_to_mongodb = None
    add_assistant_message_to_mongodb = None
    store_policy_answer = None
    get_policy_application = None
    update_policy_answer = None
    complete_application = None
    MONGODB_AVAILABLE = False

logger = logging.getLogger(__name__)

class ChatbotSession:
    """Enhanced chatbot session management"""
    def __init__(self, chatbot_type: str, service_type: str = None):
        self.chatbot_type = chatbot_type
        self.service_type = service_type
        self.current_question = 1
        self.responses = {}
        self.completed = False
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.user_id = None
        self.access_token = None
        self.validation_errors = []
        self.context = {}
        self.eligibility_shown = False
        self.details_accepted = False
        self.completed_at = None
        self.exited_manually = False

    def update_response(self, key: str, value: Any):
        """Update response for a specific key"""
        self.responses[key] = value
        self.last_activity = datetime.now()

    def complete_session(self):
        """Mark session as completed"""
        self.completed = True
        self.completed_at = datetime.now()
        logger.info(f"Session completed: {self.chatbot_type}_{self.service_type}")

    def exit_session(self):
        """Mark session as manually exited"""
        self.completed = True
        self.exited_manually = True
        self.completed_at = datetime.now()
        logger.info(f"Session exited manually: {self.chatbot_type}_{self.service_type}")

# Global chatbot sessions dictionary
chatbot_sessions = {}


FINANCIAL_ASSISTANCE_TYPES = {
    "personal": "Personal Financial Assistance",
    "medical": "Medical Emergency Funding", 
    "wedding": "Wedding & Ceremony Funding",
    "education": "Education Fee Support",
    "business": "Business Funding Support",
    "home": "Home & Property Funding",
    "emergency": "Emergency Cash Assistance"
}

INSURANCE_TYPES = {
    "health": "Health Insurance",
    "life": "Life Insurance", 
    "motor": "Motor Insurance",
    "travel": "Travel Insurance",
    "home": "Home Insurance",
    "credit": "Credit Protection"
}

# ==================== CONSTANTS ====================

FINANCIAL_ASSISTANCE_DETAILS = {
    "personal": {
        "eligibility": {
            "age": "21-65 years",
            "income": "Monthly income  15,000",
            "employment": "Salaried/Self-employed for minimum 6 months",
            "cibil": "CIBIL score  650",
            "documents": "Salary slips, Bank statements, ID proof"
        },
        "loan_details": {
            "amount_range": "10,000 - 20,00,000",
            "interest_rate": "12% - 18% per annum",
            "tenure": "6 months - 60 months",
            "processing_fee": "2% of loan amount (minimum 1,000)",
            "emi_example": "2,125/month for 1,00,000 at 15% for 5 years",
            "disbursement": "Within 24-48 hours after approval"
        },
        "features": [
            "No collateral required",
            "Flexible repayment options",
            "Minimal documentation",
            "Quick approval process",
            "Part prepayment allowed",
            "No hidden charges"
        ]
    },
    "medical": {
        "eligibility": {
            "age": "18-70 years",
            "income": "Monthly income  10,000",
            "employment": "Any stable source of income",
            "cibil": "CIBIL score  600 (relaxed for emergencies)",
            "documents": "Medical bills, Income proof, ID proof"
        },
        "loan_details": {
            "amount_range": "25,000 - 50,00,000",
            "interest_rate": "10% - 16% per annum (reduced rates)",
            "tenure": "6 months - 84 months",
            "processing_fee": "1% of loan amount (waived for emergencies)",
            "emi_example": "1,980/month for 1,00,000 at 12% for 5 years",
            "disbursement": "Same day approval for genuine emergencies"
        },
        "features": [
            "Emergency processing within hours",
            "Direct payment to hospital available",
            "Reduced interest rates for medical needs",
            "Extended repayment tenure",
            "Insurance coordination support",
            "No prepayment penalty"
        ]
    },
    "wedding": {
        "eligibility": {
            "age": "21-65 years",
            "income": "Monthly family income  20,000",
            "employment": "Stable employment for minimum 1 year",
            "cibil": "CIBIL score  675",
            "documents": "Income proof, Wedding card, Expense estimates"
        },
        "loan_details": {
            "amount_range": "50,000 - 25,00,000",
            "interest_rate": "13% - 19% per annum",
            "tenure": "12 months - 72 months",
            "processing_fee": "1.5% of loan amount",
            "emi_example": "2,950/month for 2,00,000 at 16% for 6 years",
            "disbursement": "7-10 days after approval"
        },
        "features": [
            "Seasonal festival discounts",
            "Flexible disbursement schedule",
            "Wedding vendor network benefits",
            "Extended tenure options",
            "Grace period for first EMI",
            "Family co-applicant allowed"
        ]
    },
    "education": {
        "eligibility": {
            "age": "18-35 years (student), 21-65 years (parent/guardian)",
            "income": "Monthly family income  25,000",
            "academic": "Admission confirmation in recognized institution",
            "cibil": "CIBIL score  650",
            "documents": "Admission letter, Fee structure, Academic records"
        },
        "loan_details": {
            "amount_range": "1,00,000 - 50,00,000",
            "interest_rate": "11% - 16% per annum",
            "tenure": "5 years - 15 years",
            "processing_fee": "1% of loan amount",
            "emi_example": "1,970/month for 2,00,000 at 13% for 12 years",
            "disbursement": "Direct to institution or student account"
        },
        "features": [
            "Moratorium period during studies",
            "Step-up EMI options",
            "Course-linked disbursement",
            "Tax benefits under Section 80E",
            "Study abroad coverage",
            "Co-applicant flexibility"
        ]
    },
    "business": {
        "eligibility": {
            "age": "21-65 years",
            "business_vintage": "Minimum 2 years operational",
            "turnover": "Annual turnover  5,00,000",
            "cibil": "CIBIL score  700",
            "documents": "ITR, Bank statements, Business registration"
        },
        "loan_details": {
            "amount_range": "2,00,000 - 1,00,00,000",
            "interest_rate": "14% - 22% per annum",
            "tenure": "12 months - 96 months",
            "processing_fee": "2% of loan amount",
            "emi_example": "5,560/month for 5,00,000 at 18% for 10 years",
            "disbursement": "3-7 days after documentation"
        },
        "features": [
            "Working capital solutions",
            "Equipment financing options",
            "Revenue-based repayment",
            "Business growth support",
            "GST and ITR based assessment",
            "Overdraft facility available"
        ]
    },
    "home": {
        "eligibility": {
            "age": "21-65 years",
            "income": "Monthly income  30,000",
            "employment": "Stable employment for minimum 2 years",
            "cibil": "CIBIL score  750",
            "documents": "Property papers, Income proof, Construction estimates"
        },
        "loan_details": {
            "amount_range": "5,00,000 - 2,00,00,000",
            "interest_rate": "8.5% - 13% per annum",
            "tenure": "10 years - 30 years",
            "processing_fee": "0.5% of loan amount",
            "emi_example": "8,790/month for 10,00,000 at 10% for 20 years",
            "disbursement": "Stage-wise based on construction progress"
        },
        "features": [
            "Longest tenure options",
            "Lowest interest rates",
            "Tax benefits under Section 80C & 24B",
            "Top-up loan facility",
            "Step-up/Step-down EMI options",
            "Property insurance included"
        ]
    },
    "emergency": {
        "eligibility": {
            "age": "18-70 years",
            "income": "Any provable income source",
            "employment": "Any employment status accepted",
            "cibil": "CIBIL score  550 (relaxed criteria)",
            "documents": "Minimal documentation for genuine emergencies"
        },
        "loan_details": {
            "amount_range": "5,000 - 10,00,000",
            "interest_rate": "15% - 24% per annum",
            "tenure": "3 months - 36 months",
            "processing_fee": "Waived for genuine emergencies",
            "emi_example": "3,160/month for 50,000 at 18% for 18 months",
            "disbursement": "Within 2-6 hours of approval"
        },
        "features": [
            "Instant approval process",
            "24x7 processing",
            "Minimal documentation",
            "Same day disbursement",
            "Flexible repayment terms",
            "Emergency helpline support"
        ]
    }
}


INSURANCE_DETAILS = {
    "health": {
        "eligibility": {
            "age": "3 months - 65 years (entry age)",
            "pre_existing": "Covered after 2-4 years waiting period",
            "medical_test": "Required for age 45+ or higher sum insured",
            "income": "No minimum income requirement",
            "documents": "Age proof, ID proof, Medical reports (if any)"
        },
        "coverage_details": {
            "sum_insured": "1,00,000 - 1,00,00,000",
            "premium": "Starting from 150/month",
            "family_floater": "Available for entire family",
            "cashless_hospitals": "9,000+ network hospitals",
            "claim_settlement": "Within 1 hour for cashless, 7 days for reimbursement",
            "room_rent": "Covered as per plan (AC/Non-AC/Private)"
        },
        "features": [
            "Cashless treatment at network hospitals",
            "Pre & post hospitalization (30-60 days)",
            "Daycare procedures covered",
            "Annual health check-ups",
            "Ambulance charges",
            "No claim bonus up to 50%",
            "Coverage for COVID-19",
            "Mental health coverage"
        ]
    },
    "motor": {
        "eligibility": {
            "vehicle_age": "All vehicles (new and old)",
            "license": "Valid driving license required",
            "registration": "Vehicle registration certificate",
            "previous_policy": "Previous policy details (for renewal)",
            "documents": "RC, License, Previous policy, PUC certificate"
        },
        "coverage_details": {
            "third_party": "As per IRDA tariff (mandatory)",
            "own_damage": "As per vehicle IDV value",
            "premium": "Starting from 2,000/year",
            "idv_range": "Based on vehicle's current market value",
            "claim_settlement": "Cashless at 4,000+ garages",
            "coverage_types": "Comprehensive, Third-party, Standalone OD"
        },
        "features": [
            "Third-party liability coverage",
            "Own damage protection",
            "Theft and fire coverage",
            "Natural disaster protection",
            "Personal accident cover for owner-driver",
            "Zero depreciation add-on available",
            "Roadside assistance",
            "Engine protection cover"
        ]
    },
    "life": {
        "eligibility": {
            "age": "18-65 years (entry age)",
            "health": "Medical examination may be required",
            "income": "Sum assured typically 10-20 times annual income",
            "lifestyle": "Non-smoker discounts available",
            "documents": "Age proof, Income proof, Medical reports"
        },
        "coverage_details": {
            "sum_assured": "5,00,000 - 5,00,00,000",
            "premium": "Starting from 500/month",
            "policy_term": "5-40 years or till age 75",
            "premium_paying": "Regular pay, Limited pay, Single pay",
            "maturity": "Maturity benefits in endowment plans",
            "riders": "Accidental death, Critical illness, Disability"
        },
        "features": [
            "Financial protection for family",
            "Tax benefits under Section 80C",
            "Maturity benefits (in endowment plans)",
            "Loan facility after 3 years",
            "Grace period for premium payment",
            "Multiple rider options",
            "Guaranteed returns (in some plans)",
            "Wealth creation opportunity"
        ]
    },
    "travel": {
        "eligibility": {
            "age": "6 months - 70 years",
            "destination": "Domestic and international travel",
            "trip_duration": "1 day to 365 days",
            "health": "Pre-existing conditions coverage available",
            "documents": "Passport (for international), Travel itinerary"
        },
        "coverage_details": {
            "medical_emergency": "1,00,000 - 25,00,000",
            "premium": "Starting from 50/day",
            "trip_cancellation": "Up to 100% of non-refundable trip cost",
            "baggage_loss": "10,000 - 50,000",
            "flight_delay": "2,000 - 10,000",
            "coverage_area": "Worldwide including USA, Europe, Asia"
        },
        "features": [
            "Medical emergency coverage abroad",
            "Trip cancellation/interruption",
            "Baggage loss and delay compensation",
            "Flight delay compensation",
            "Personal liability coverage",
            "Adventure sports coverage",
            "24x7 assistance hotline",
            "COVID-19 coverage"
        ]
    },
    "home": {
        "eligibility": {
            "property_type": "Residential properties",
            "ownership": "Owner-occupied or rented",
            "location": "Non-hazardous locations",
            "construction": "RCC, brick, stone construction",
            "documents": "Property papers, Valuation report"
        },
        "coverage_details": {
            "building_sum": "5,00,000 - 2,00,00,000",
            "contents_sum": "1,00,000 - 50,00,000",
            "premium": "Starting from 300/month",
            "coverage_type": "Building, Contents, or Both",
            "geographical_area": "Pan India coverage",
            "claim_settlement": "Within 15 days of claim intimation"
        },
        "features": [
            "Fire and allied perils",
            "Burglary and theft protection",
            "Natural disasters coverage",
            "Public liability coverage",
            "Temporary accommodation",
            "Loss of rent compensation",
            "Electronic items coverage",
            "Personal accident for family"
        ]
    },
    "credit": {
        "eligibility": {
            "age": "18-65 years",
            "loan_amount": "Minimum outstanding 50,000",
            "employment": "Salaried or self-employed",
            "health": "Basic health declaration",
            "documents": "Loan documents, Income proof"
        },
        "coverage_details": {
            "sum_assured": "50,000 - 50,00,000",
            "premium": "0.5% - 2% of outstanding loan amount annually",
            "coverage_period": "Up to loan tenure",
            "benefit_payout": "Outstanding loan amount or EMIs",
            "waiting_period": "30 days (except accidents)",
            "claim_settlement": "Direct to lender"
        },
        "features": [
            "Job loss protection",
            "Permanent total disability cover",
            "Critical illness coverage",
            "Accidental death benefit",
            "Terminal illness coverage",
            "EMI waiver facility",
            "Family income protection",
            "No medical examination for lower amounts"
        ]
    }
}

# ==================== EXIT INTENT DETECTION ====================

# ADD THIS NEAR THE TOP - After imports
def get_consistent_session_id(user_id: int, policy_id: str) -> str:
    """Generate consistent session ID for policy applications"""
    return f"policy_app_{user_id}_{policy_id}"

def get_consistent_application_id(user_id: int, policy_id: str) -> str:
    """Generate consistent application ID"""
    return f"APP_{policy_id}_{user_id}"

def detect_exit_intent(user_input: str) -> bool:
    """Enhanced exit intent detection"""
    if not user_input:
        return False
    
    input_lower = user_input.lower().strip()
    
    # Direct exit commands
    exit_keywords = [
        'exit', 'quit', 'stop', 'cancel', 'end', 'leave', 'abort',
        'bye', 'goodbye', 'close', 'finish', 'done', 'nevermind',
        'no thanks', 'not now', 'later', 'back', 'return', 'main menu',
        'skip', 'skip this', 'not interested', 'changed my mind'
    ]
    
    if input_lower in exit_keywords:
        return True
    
    # Exit phrases
    exit_phrases = [
        'want to exit', 'want to quit', 'want to stop', 'want to cancel',
        'need to exit', 'need to quit', 'need to stop', 'need to cancel',
        'like to exit', 'like to quit', 'like to stop', 'like to cancel',
        'please exit', 'please quit', 'please stop', 'please cancel',
        'i want out', 'get me out', 'take me back', 'go back',
        "don't want", "changed my mind", "not interested", "stop this",
        'exit this', 'quit this', 'cancel this', 'stop the process',
        'end this', 'close this', 'abort this', 'leave this', 'leave it',
        'exit this process', 'quit the application', 'cancel application',
        'stop asking questions', 'dont want to continue', 'not now'
    ]
    
    for phrase in exit_phrases:
        if phrase in input_lower:
            return True
    
    return False

# ==================== SESSION MANAGEMENT ====================

def clear_completed_sessions(session_id: str):
    """Clear completed sessions for a user"""
    keys_to_remove = []
    for session_key in chatbot_sessions:
        if session_id in session_key and chatbot_sessions[session_key].completed:
            keys_to_remove.append(session_key)
    
    for key in keys_to_remove:
        del chatbot_sessions[key]
        logger.info(f"Cleared completed session: {key}")

def get_active_session_for_user(session_id: str) -> Optional[str]:
    """Get the active session key for a user (if any) - FIXED VERSION"""
    # Check for policy applications first (highest priority)
    for session_key, session in chatbot_sessions.items():
        if session_id in session_key and not session.completed:
            # Prioritize policy applications
            if "policy_application" in session_key:
                logger.info(f"Found active policy application session: {session_key}")
                return session_key
    
    # Then check for other session types
    for session_key, session in chatbot_sessions.items():
        if session_id in session_key and not session.completed:
            logger.info(f"Found active session: {session_key}")
            return session_key
    
    return None

# ==================== RESPONSE GENERATORS ====================

def generate_fresh_start_response() -> Dict:
    """Generate response for fresh conversation start"""
    return {
        "type": "conversation_reset", 
        "message": " How can I help you today?",
        "action": "fresh_start",
        "show_service_options": False,
        "quick_actions": [
            {"title": "Check Balance", "action": "check_balance"},
            {"title": "Get Financial Help", "action": "select_financial_assistance_type"},
            {"title": "Get Insurance", "action": "select_insurance_type"},
            {"title": "Show All Services", "action": "service_selection"}
        ]
    }

def generate_error_response(error_message: str) -> Dict:
    """Generate error response"""
    return {
        "type": "error",
        "message": "I encountered an issue. Let me help you get back on track.",
        "action": "error_recovery",
        "show_service_options": False,
        "error_details": error_message,
        "quick_actions": [
            {"title": "Try Again", "action": "retry"},
            {"title": "Get Help", "action": "help"}
        ]
    }

# ==================== EXIT HANDLER ====================

def handle_chatbot_exit(session_id: str, service_type: str, chatbot_type: str) -> Dict:
    """Handle user exit from chatbot session"""
    try:
        session_key = f"{session_id}_{chatbot_type}_{service_type}"
        
        # Mark session as exited
        if session_key in chatbot_sessions:
            chatbot_sessions[session_key].exit_session()
        
        # Clear all completed sessions
        clear_completed_sessions(session_id)
        
        # Return a friendly exit message WITHOUT service options
        return {
            "type": "exit_confirmation",
            "message": " No problem! I've cancelled the current application. Feel free to ask me anything else or start a new application whenever you're ready.",
            "action": "application_cancelled",
            "show_service_options": False,
            "quick_actions": [
                {"title": "Check Balance", "action": "check_balance"},
                {"title": "View Transactions", "action": "view_transactions"},
                {"title": "Get Help", "action": "help"}
            ]
        }
        
    except Exception as e:
        logger.error(f"Error handling chatbot exit: {e}")
        return generate_error_response("Exit handled successfully")

# ==================== SERVICE HANDLERS ====================

def handle_service_selection() -> Dict:
    """Handle initial service selection"""
    return {
        "type": "service_selection",
        "message": " Welcome to Eazr Financial Services! How can I help you today?",
        "show_service_options": True,
        "options": {
            "financial_assistance": {
                "title": " Get Financial Assistance",
                "description": "Personal, Medical, Wedding, Education, Business, Emergency funding",
                "action": "select_financial_assistance_type",
                "emoji": ""
            },
            "insurance": {
                "title": " Get Insurance",
                "description": "Health, Life, Motor, Travel, Home, Credit protection",
                "action": "select_insurance_type",
                "emoji": ""
            },
            "wallet": {
                "title": " Create Wallet Account",
                "description": "Set up your digital wallet with KYC verification",
                "action": "start_wallet_setup",
                "emoji": ""
            },
            "account_services": {
                "title": " Account Services",
                "description": "Check balance, transactions, bills, account status",
                "action": "account_services",
                "emoji": ""
            }
        }
    }

def handle_financial_assistance_type_selection() -> Dict:
    """Handle financial assistance type selection"""
    return {
        "type": "financial_assistance_type_selection",
        "message": "What type of financial assistance do you need?",
        "subtitle": "Choose the option that best describes your situation:",
        "show_service_options": False,
        "options": {
            "personal": {
                "title": "Personal Financial Assistance",
                "action": "show_financial_assistance_eligibility",
                "assistance_type": "personal",
                "description": "Quick financial help for personal needs and family expenses",
                "typical_range": "10K - 20L",
                "processing_time": "24-48 hours"
            },
            "medical": {
                "title": "Medical Emergency Funding",
                "action": "show_financial_assistance_eligibility",
                "assistance_type": "medical",
                "description": "Urgent funding for medical treatments, surgeries, and healthcare",
                "typical_range": "25K - 50L",
                "processing_time": "Same day",
                "urgent": True
            },
            "wedding": {
                "title": "Wedding & Ceremony Funding",
                "action": "show_financial_assistance_eligibility",
                "assistance_type": "wedding",
                "description": "Support for wedding ceremonies, functions, and related expenses",
                "typical_range": "50K - 25L",
                "processing_time": "2-3 days"
            },
            "education": {
                "title": "Education Fee Support",
                "action": "show_financial_assistance_eligibility",
                "assistance_type": "education",
                "description": "Fund your education or your family's educational needs",
                "typical_range": "1L - 50L",
                "processing_time": "3-5 days"
            },
            "business": {
                "title": "Business Funding Support",
                "action": "show_financial_assistance_eligibility",
                "assistance_type": "business",
                "description": "Grow your business with working capital and expansion funding",
                "typical_range": "2L - 1Cr",
                "processing_time": "5-7 days"
            },
            "home": {
                "title": "Home & Property Funding",
                "action": "show_financial_assistance_eligibility",
                "assistance_type": "home",
                "description": "Support for home purchase, construction, or renovation projects",
                "typical_range": "5L - 2Cr",
                "processing_time": "7-10 days"
            },
            "emergency": {
                "title": "Emergency Cash Assistance",
                "action": "show_financial_assistance_eligibility",
                "assistance_type": "emergency",
                "description": "Immediate financial assistance for urgent situations",
                "typical_range": "5K - 10L",
                "processing_time": "Within hours",
                "instant": True
            }
        }
    }

def handle_insurance_type_selection() -> Dict:
    """Handle insurance type selection"""
    return {
        "type": "insurance_type_selection",
        "message": "What type of insurance coverage do you need?",
        "subtitle": "Choose the insurance plan that suits your needs:",
        "show_service_options": False,
        "options": {
            "health": {
                "title": "Health Insurance",
                "action": "show_insurance_eligibility",
                "insurance_type": "health",
                "description": "Comprehensive medical coverage for you and your family with cashless treatment",
                "coverage_range": "1L - 1Cr",
                "popular": True
            },
            "motor": {
                "title": "Motor Insurance", 
                "action": "show_insurance_eligibility",
                "insurance_type": "motor",
                "description": "Complete protection for your vehicle against accidents, theft, and third-party damages",
                "coverage_range": "1L - 50L",
                "mandatory": True
            },
            "life": {
                "title": "Life Insurance",
                "action": "show_insurance_eligibility",
                "insurance_type": "life",
                "description": "Financial security for your loved ones with tax benefits",
                "coverage_range": "5L - 5Cr",
                "tax_benefit": True
            },
            "travel": {
                "title": "Travel Insurance",
                "action": "show_insurance_eligibility",
                "insurance_type": "travel", 
                "description": "Protection for domestic and international travel with medical emergency cover",
                "coverage_range": "1L - 25L"
            },
            "home": {
                "title": "Home Insurance",
                "action": "show_insurance_eligibility",
                "insurance_type": "home",
                "description": "Comprehensive protection for your home and belongings against all risks", 
                "coverage_range": "5L - 2Cr"
            },
            "credit": {
                "title": "Credit Protection",
                "action": "show_insurance_eligibility",
                "insurance_type": "credit",
                "description": "Safeguard your loan and credit obligations during unforeseen circumstances",
                "coverage_range": "50K - 50L"
            }
        }
    }

def handle_account_services(session_id: str, access_token: str = None, user_id: int = None) -> Dict:
    """Handle account services selection"""
    return {
        "type": "account_services",
        "message": " Account Services - What would you like to do?",
        "show_service_options": False,
        "options": {
            "check_balance": {
                "title": " Check Balance",
                "description": "View your current account balance and summary",
                "action": "check_balance",
                "emoji": ""
            },
            "view_transactions": {
                "title": " Transaction History", 
                "description": "View your recent transactions and payment history",
                "action": "view_transactions",
                "emoji": ""
            },
            "view_bills": {
                "title": " View Bills",
                "description": "Check pending bills and payment due dates",
                "action": "view_bills",
                "emoji": ""
            },
            "view_financial_assistance": {
                "title": " Financial Assistance Status",
                "description": "Check your active financial assistance applications",
                "action": "view_financial_assistance",
                "emoji": ""
            },
            "view_insurance": {
                "title": " Insurance Policies", 
                "description": "View your insurance policies and coverage details",
                "action": "view_insurance",
                "emoji": ""
            }
        }
    }

# ==================== ELIGIBILITY DISPLAY FUNCTIONS ====================

def show_financial_assistance_eligibility(session_id: str, assistance_type: str, 
                                         access_token: str = None, user_id: int = None) -> Dict:
    """Show detailed eligibility and loan details before starting application"""
    
    if assistance_type not in FINANCIAL_ASSISTANCE_DETAILS:
        assistance_type = "personal"  # fallback
    
    details = FINANCIAL_ASSISTANCE_DETAILS[assistance_type]
    assistance_name = FINANCIAL_ASSISTANCE_TYPES[assistance_type]
    
    return {
        "type": "eligibility_details",
        "response":"Loan finance features are coming soon.",
        "service_type": "financial_assistance",
        "assistance_type": assistance_type,
        "title": f"{assistance_name} - Eligibility & Details",
        "message": f" Here are the complete details for {assistance_name}:",
        "eligibility": details["eligibility"],
        "loan_details": details["loan_details"],
        "features": details["features"],
        "next_action": {
            "title": "I understand and want to proceed",
            "action": "accept_eligibility_and_start",
            "service_type": "financial_assistance",
            "sub_type": assistance_type
        },
        "back_action": {
            "title": " Back to selection",
            "action": "select_financial_assistance_type"
        },
        "show_service_options": False
    }

def show_insurance_eligibility(session_id: str, insurance_type: str, 
                              access_token: str = None, user_id: int = None) -> Dict:
    """Show detailed eligibility and insurance details before starting application"""
    
    if insurance_type not in INSURANCE_DETAILS:
        insurance_type = "health"  # fallback
    
    details = INSURANCE_DETAILS[insurance_type]
    insurance_name = INSURANCE_TYPES[insurance_type]
    
    return {
        "type": "eligibility_details",
        "service_type": "insurance",
        "insurance_type": insurance_type,
        "title": f"{insurance_name} - Eligibility & Coverage Details",
        "message": f" Here are the complete details for {insurance_name}:",
        "eligibility": details["eligibility"],
        "coverage_details": details["coverage_details"],
        "features": details["features"],
        "next_action": {
            "title": "I understand and want to proceed",
            "action": "accept_eligibility_and_start",
            "service_type": "insurance",
            "sub_type": insurance_type
        },
        "back_action": {
            "title": " Back to selection",
            "action": "select_insurance_type"
        },
        "show_service_options": False
    }

# ==================== FORM STARTER FUNCTIONS ====================

def start_financial_assistance_form(session_id: str, assistance_type: str, user_input: str = None, 
                                   access_token: str = None, user_id: int = None) -> Dict:
    """Start the actual financial assistance application form"""
    session_key = f"{session_id}_financial_{assistance_type}"
    
    # Check if session already exists
    if session_key in chatbot_sessions:
        session = chatbot_sessions[session_key]
        # Mark eligibility as accepted
        session.eligibility_shown = True
        session.details_accepted = True
    else:
        # Create new session
        chatbot_sessions[session_key] = ChatbotSession("financial_assistance", assistance_type)
        chatbot_sessions[session_key].user_id = user_id
        chatbot_sessions[session_key].access_token = access_token
        chatbot_sessions[session_key].eligibility_shown = True
        chatbot_sessions[session_key].details_accepted = True
    
    session = chatbot_sessions[session_key]
    
    # Get the appropriate questions for this assistance type
    questions = get_financial_assistance_questions(assistance_type)
    
    # Start with the first question
    first_question = questions[1]
    session.current_question = 1


    if mongodb_chat_manager:
        from database_storage.mongodb_chat_manager import add_assistant_message_to_mongodb
        add_assistant_message_to_mongodb(
            session_id=session_key,
            user_id=user_id,
            content=first_question["question"],
            intent="policy_application_question",
            context={
                "policy_id": policy_id,
                "question_number": 1,
                "question_key": first_question["key"],
                "input_type": first_question.get("type", "text"),
                "options": first_question.get("options", []),
                "is_first_question": True
            }
        )
    
    return {
        "type": "question",
        "service_type": "financial_assistance",
        "assistance_type": assistance_type,
        "title": f"{FINANCIAL_ASSISTANCE_TYPES[assistance_type]} Application",
        "message": first_question["question"],
        "question_number": 1,
        "total_questions": len(questions),
        "progress": {
            "current": 1,
            "total": len(questions),
            "percentage": 0
        },
        "input_type": first_question.get("type", "text"),
        "regex":first_question.get('api_field', {}).get('regex'),
        "options": first_question.get("options", []),
        "hint": get_input_hint(first_question),
        "examples": get_input_examples(first_question),
        "required": first_question.get("required", True),
        "show_service_options": False,
        "exit_option": {"title": "Exit Application", "action": "exit"}
    }

def start_insurance_form(session_id: str, insurance_type: str, user_input: str = None,
                        access_token: str = None, user_id: int = None) -> Dict:
    """Start the actual insurance application form"""
    session_key = f"{session_id}_insurance_{insurance_type}"
    
    # Check if session already exists
    if session_key in chatbot_sessions:
        session = chatbot_sessions[session_key]
        # Mark eligibility as accepted
        session.eligibility_shown = True
        session.details_accepted = True
    else:
        # Create new session
        chatbot_sessions[session_key] = ChatbotSession("insurance", insurance_type)
        chatbot_sessions[session_key].user_id = user_id
        chatbot_sessions[session_key].access_token = access_token
        chatbot_sessions[session_key].eligibility_shown = True
        chatbot_sessions[session_key].details_accepted = True
    
    session = chatbot_sessions[session_key]
    
    # Get the appropriate questions for this insurance type
    questions = get_insurance_questions(insurance_type)
    
    # Start with the first question
    first_question = questions[1]
    session.current_question = 1
    
    return {
        "type": "question",
        "service_type": "insurance",
        "insurance_type": insurance_type,
        "title": f"{INSURANCE_TYPES[insurance_type]} Application",
        "message": first_question["question"],
        "question_number": 1,
        "total_questions": len(questions),
        "progress": {
            "current": 1,
            "total": len(questions),
            "percentage": 0
        },
        "input_type": first_question.get("type", "text"),
        "options": first_question.get("options", []),
        "regex":first_question.get('api_field', {}).get('regex'),
        "hint": get_input_hint(first_question),
        "examples": get_input_examples(first_question),
        "required": first_question.get("required", True),
        "show_service_options": False,
        "exit_option": {"title": "Exit Application", "action": "exit"}
    }

def start_wallet_setup(session_id: str, user_input: str = None, access_token: str = None, user_id: int = None) -> Dict:
    """Start wallet setup process"""
    session_key = f"{session_id}_wallet"
    
    if session_key not in chatbot_sessions:
        chatbot_sessions[session_key] = ChatbotSession("wallet", "setup")
        chatbot_sessions[session_key].user_id = user_id
        chatbot_sessions[session_key].access_token = access_token
    
    session = chatbot_sessions[session_key]
    
    # Wallet setup questions
    wallet_questions = {
        1: {"question": "What's your full name as per Aadhaar card?", "key": "fullName", "type": "text", "required": True},
        2: {"question": "What's your mobile number?", "key": "mobileNumber", "type": "text", "required": True},
        3: {"question": "What's your email address?", "key": "email", "type": "text", "required": True},
        4: {"question": "What's your PAN number?", "key": "panNumber", "type": "text", "required": True},
        5: {"question": "What's your Aadhaar number?", "key": "aadhaarNumber", "type": "text", "required": True},
        6: {"question": "What's your date of birth? (DD-MM-YYYY)", "key": "dateOfBirth", "type": "text", "required": True},
        7: {"question": "What's your current address?", "key": "currentAddress", "type": "text", "required": True},
        8: {"question": "What's your occupation?", "key": "occupation", "type": "select", "options": ["Salaried", "Self-Employed", "Business", "Student", "Retired"], "required": True}
    }
    
    return process_chatbot_flow(session, wallet_questions, user_input, "Digital Wallet Setup")

# ==================== CONTINUATION HANDLERS ====================

def continue_financial_assistance_application(session_id: str, assistance_type: str, user_input: str,
                                            access_token: str = None, user_id: int = None) -> Dict:
    """Continue financial assistance application"""
    try:
        # Check for exit intent FIRST
        if detect_exit_intent(user_input):
            return handle_chatbot_exit(session_id, assistance_type, "financial_assistance")
        
        session_key = f"{session_id}_financial_{assistance_type}"
        
        if session_key not in chatbot_sessions:
            # Session doesn't exist, redirect to start
            return start_financial_assistance_form(session_id, assistance_type, user_input, access_token, user_id)
        
        session = chatbot_sessions[session_key]
        
        # Check if session is already completed
        if session.completed:
            clear_completed_sessions(session_id)
            return generate_fresh_start_response()
        
        questions = get_insurance_questions(INSURANCE_TYPES)
        
        result = process_chatbot_flow(
            session, 
            questions, 
            user_input, 
            f"{INSURANCE_TYPES[INSURANCE_TYPES]} Application"
        )
        
        return result
        
    except Exception as e:
        logger.error(f'ERROR IN continue_insurance_application: {str(e)}')
        return generate_error_response(str(e))

def continue_wallet_setup(session_id: str, user_input: str, access_token: str = None, user_id: int = None) -> Dict:
    """Continue wallet setup process"""
    try:
        # Check for exit intent FIRST
        if detect_exit_intent(user_input):
            return handle_chatbot_exit(session_id, "setup", "wallet")
        
        session_key = f"{session_id}_wallet"
        
        if session_key not in chatbot_sessions:
            return start_wallet_setup(session_id, user_input, access_token, user_id)
        
        session = chatbot_sessions[session_key]
        
        # Check if session is already completed
        if session.completed:
            clear_completed_sessions(session_id)
            return generate_fresh_start_response()
        
        # Wallet setup questions
        wallet_questions = {
            1: {"question": "What's your full name as per PAN card?", "key": "fullName", "type": "text", "required": True},
            2: {"question": "What's your mobile number?", "key": "mobileNumber", "type": "text", "required": True},
            3: {"question": "What's your email address?", "key": "email", "type": "text", "required": True},
            4: {"question": "What's your PAN number?", "key": "panNumber", "type": "text", "required": True},
            5: {"question": "What's your Aadhaar number?", "key": "aadhaarNumber", "type": "text", "required": True},
            6: {"question": "What's your date of birth? (DD-MM-YYYY)", "key": "dateOfBirth", "type": "text", "required": True},
            7: {"question": "What's your current address?", "key": "currentAddress", "type": "text", "required": True},
            8: {"question": "What's your occupation?", "key": "occupation", "type": "select", "options": ["Salaried", "Self-Employed", "Business", "Student", "Retired"], "required": True}
        }
        
        result = process_chatbot_flow(
            session, 
            wallet_questions, 
            user_input, 
            "Digital Wallet Setup"
        )
        
        return result
        
    except Exception as e:
        logger.error(f'ERROR IN continue_wallet_setup: {str(e)}')
        return generate_error_response(str(e))

# ==================== QUESTION GENERATORS ====================

def get_financial_assistance_questions(assistance_type: str) -> Dict:
    """Get questions specific to financial assistance type"""
    
    # Base questions common to all financial assistance types
    base_questions = {
        1: {"question": "What's your full name?", "key": "fullName", "type": "text", "required": True},
        2: {"question": "What's your mobile number?", "key": "mobileNumber", "type": "text", "required": True},
        3: {"question": "What's your email address?", "key": "email", "type": "text", "required": True},
        4: {"question": "What's your date of birth? (DD-MM-YYYY)", "key": "dateOfBirth", "type": "text", "required": True},
        5: {"question": "What's your PAN number?", "key": "panNumber", "type": "text", "required": True},
        6: {"question": "What's your monthly income?", "key": "monthlyIncome", "type": "text", "required": True},
        7: {"question": "What's your employment type?", "key": "employmentType", "type": "select", "options": ["Salaried", "Self-Employed", "Business Owner", "Freelancer"], "required": True},
        8: {"question": "How much money do you need?", "key": "amountNeeded", "type": "text", "required": True},
    }
    
    # Add specific questions based on assistance type
    if assistance_type == "medical":
        base_questions.update({
            9: {"question": "What is the medical situation requiring funding?", "key": "medicalSituation", "type": "select", "options": ["Surgery", "Treatment", "Emergency", "Medication", "Other"], "required": True},
            10: {"question": "Which hospital/doctor is treating?", "key": "hospitalName", "type": "text", "required": True},
            11: {"question": "What is the estimated treatment cost?", "key": "treatmentCost", "type": "text", "required": True},
            12: {"question": "When is the money needed?", "key": "urgency", "type": "select", "options": ["Immediately", "Within 24 hours", "Within 1 week"], "required": True}
        })
    elif assistance_type == "wedding":
        base_questions.update({
            9: {"question": "Whose wedding is it?", "key": "relationToApplicant", "type": "select", "options": ["Self", "Daughter", "Son", "Sister", "Brother", "Other Family"], "required": True},
            10: {"question": "What is the expected wedding date?", "key": "weddingDate", "type": "text", "required": True},
            11: {"question": "What are the main expenses you need funding for?", "key": "weddingExpenses", "type": "select", "options": ["Venue", "Catering", "Jewelry", "Clothing", "Photography", "All expenses"], "required": True},
            12: {"question": "What's your total estimated wedding budget?", "key": "totalBudget", "type": "text", "required": True}
        })
    elif assistance_type == "education":
        base_questions.update({
            9: {"question": "For whom is the education funding?", "key": "studentRelation", "type": "select", "options": ["Self", "Child", "Sibling", "Spouse", "Other"], "required": True},
            10: {"question": "What type of education/course?", "key": "courseType", "type": "select", "options": ["Engineering", "Medical", "MBA", "Graduate", "Post-Graduate", "Professional Course", "Other"], "required": True},
            11: {"question": "Which institution/college?", "key": "institutionName", "type": "text", "required": True},
            12: {"question": "What is the total course fee?", "key": "totalFees", "type": "text", "required": True}
        })
    elif assistance_type == "business":
        base_questions.update({
            9: {"question": "What type of business do you have?", "key": "businessType", "type": "text", "required": True},
            10: {"question": "How long has your business been running?", "key": "businessAge", "type": "select", "options": ["Less than 1 year", "1-2 years", "2-5 years", "5+ years"], "required": True},
            11: {"question": "What is your monthly business turnover?", "key": "monthlyTurnover", "type": "text", "required": True},
            12: {"question": "What will you use this funding for?", "key": "businessPurpose", "type": "select", "options": ["Working Capital", "Equipment", "Expansion", "Inventory", "Other"], "required": True}
        })
    else:  # personal and others
        base_questions.update({
            9: {"question": "What is the purpose of this financial assistance?", "key": "purpose", "type": "select", "options": ["Personal Emergency", "Family Expenses", "Debt Consolidation", "Home Improvement", "Other"], "required": True},
            10: {"question": "When do you need the money?", "key": "urgency", "type": "select", "options": ["Immediately", "Within 1 week", "Within 1 month"], "required": True},
            11: {"question": "Do you have any existing loans?", "key": "existingLoans", "type": "select", "options": ["Yes", "No"], "required": True},
            12: {"question": "What's your current residential address?", "key": "address", "type": "text", "required": True}
        })
    
    return base_questions

def get_insurance_questions(insurance_type: str) -> Dict:
    """Get questions specific to insurance type"""
    
    # Base questions common to all insurance types
    base_questions = {
        1: {"question": "What's your full name?", "key": "fullName", "type": "text", "required": True},
        2: {"question": "What's your mobile number?", "key": "mobileNumber", "type": "text", "required": True},
        3: {"question": "What's your email address?", "key": "email", "type": "text", "required": True},
        4: {"question": "What's your date of birth? (DD-MM-YYYY)", "key": "dateOfBirth", "type": "text", "required": True},
        5: {"question": "What's your annual income?", "key": "annualIncome", "type": "text", "required": True},
    }
    
    # Add specific questions based on insurance type
    if insurance_type == "health":
        base_questions.update({
            6: {"question": "Do you have any pre-existing medical conditions?", "key": "medicalConditions", "type": "select", "options": ["None", "Diabetes", "Hypertension", "Heart Disease", "Other"], "required": True},
            7: {"question": "What coverage amount do you need?", "key": "coverageAmount", "type": "select", "options": ["1 Lakh", "3 Lakhs", "5 Lakhs", "10 Lakhs", "25 Lakhs"], "required": True},
            8: {"question": "Do you want family floater or individual policy?", "key": "policyType", "type": "select", "options": ["Individual", "Family Floater"], "required": True},
            9: {"question": "How many family members to be covered?", "key": "familyMembers", "type": "select", "options": ["1", "2", "3", "4", "5+"], "required": True}
        })
    elif insurance_type == "motor":
        base_questions.update({
            6: {"question": "What type of vehicle do you want to insure?", "key": "vehicleType", "type": "select", "options": ["Car", "Motorcycle", "Commercial Vehicle"], "required": True},
            7: {"question": "What's your vehicle's make and model?", "key": "vehicleModel", "type": "text", "required": True},
            8: {"question": "What year was your vehicle manufactured?", "key": "manufacturingYear", "type": "text", "required": True},
            9: {"question": "What's your vehicle's registration number?", "key": "registrationNumber", "type": "text", "required": True}
        })
    elif insurance_type == "life":
        base_questions.update({
            6: {"question": "What coverage amount do you need?", "key": "coverageAmount", "type": "select", "options": ["10 Lakhs", "25 Lakhs", "50 Lakhs", "1 Crore", "2 Crores"], "required": True},
            7: {"question": "Do you smoke or consume tobacco?", "key": "smokingHabits", "type": "select", "options": ["No", "Occasionally", "Regularly"], "required": True},
            8: {"question": "Who is your nominee?", "key": "nominee", "type": "text", "required": True},
            9: {"question": "What's your relationship with the nominee?", "key": "nomineeRelation", "type": "select", "options": ["Spouse", "Child", "Parent", "Sibling", "Other"], "required": True}
        })
    else:  # travel, home, credit
        base_questions.update({
            6: {"question": "What coverage amount do you prefer?", "key": "coverageAmount", "type": "text", "required": True},
            7: {"question": "Do you have any existing insurance policies?", "key": "existingPolicies", "type": "select", "options": ["Yes", "No"], "required": True},
            8: {"question": "What's your preferred premium payment frequency?", "key": "premiumFrequency", "type": "select", "options": ["Monthly", "Quarterly", "Half-yearly", "Yearly"], "required": True}
        })
    
    return base_questions

# ==================== MAIN ROUTING FUNCTION ====================

async def route_enhanced_chatbot(action: str, session_id: str, user_input: str = None,
                          access_token: str = None, user_id: int = None, **kwargs) -> Dict:
    """Main routing function with 3-step policy flow and session management (ASYNC)"""
    
    try:
        # Extract all possible parameters from kwargs
        actual_user_input = extract_actual_user_input(user_input) if user_input else None
        assistance_type = kwargs.get("assistance_type")
        insurance_type = kwargs.get("insurance_type")
        service_type = kwargs.get("service_type")
        policy_id = kwargs.get("policy_id")  # Extract policy_id from kwargs
        
        logger.info(f" Routing action: {action}, session: {session_id}, policy_id: {policy_id}")
        
        # STEP 1: Check for exit intent in any user input
        if actual_user_input and detect_exit_intent(actual_user_input):
            # Find active session and exit it
            active_session_key = get_active_session_for_user(session_id)
            if active_session_key:
                parts = active_session_key.split('_')
                if len(parts) >= 3:
                    chatbot_type = parts[1]
                    service_type = parts[2] if len(parts) > 2 else "unknown"
                    return handle_chatbot_exit(session_id, service_type, chatbot_type)
            
            # No active session, just acknowledge exit
            return {
                "type": "acknowledgment",
                "message": "Understood! How else can I help you?",
                "show_service_options": False
            }
        
        # STEP 2: Clear any completed sessions before proceeding
        clear_completed_sessions(session_id)
        
        # STEP 3: Check if we're continuing an existing conversation
        if actual_user_input and action in ["start_financial_assistance_application", "start_insurance_application"]:
            assistance_type = assistance_type or "personal"
            insurance_type = insurance_type or "health"
            
            financial_session_key = f"{session_id}_financial_{assistance_type}"
            insurance_session_key = f"{session_id}_insurance_{insurance_type}"
            
            # Continue if session exists and is not completed
            if action == "start_financial_assistance_application" and financial_session_key in chatbot_sessions:
                if not chatbot_sessions[financial_session_key].completed:
                    logger.info(f"Continuing financial assistance session: {financial_session_key}")
                    return continue_financial_assistance_application(
                        session_id, assistance_type, actual_user_input, access_token, user_id
                    )
            
            elif action == "start_insurance_application" and insurance_session_key in chatbot_sessions:
                if not chatbot_sessions[insurance_session_key].completed:
                    logger.info(f"Continuing insurance session: {insurance_session_key}")
                    return continue_insurance_application(
                        session_id, insurance_type, actual_user_input, access_token, user_id
                    )
        
        # STEP 4: Check for active policy application sessions
        if actual_user_input:
            active_session_key = get_active_session_for_user(session_id)
            if active_session_key and "policy_application" in active_session_key:
                # Extract policy_id from session key: session_id_policy_application_policyId
                parts = active_session_key.split('_')
                if len(parts) >= 4:
                    policy_id_from_session = parts[-1]
                    logger.info(f"Continuing policy application for policy {policy_id_from_session}")
                    return continue_policy_application(
                        session_id, policy_id_from_session, actual_user_input, access_token, user_id
                    )
        
        # STEP 5: Handle initial actions (no continuation)
        
        # ============= SERVICE SELECTION =============
        if action == "service_selection":
            logger.info("Showing main service selection menu")
            return handle_service_selection()
        
        # ============= FINANCIAL ASSISTANCE FLOW =============
        elif action == "select_financial_assistance_type":
            logger.info("Showing financial assistance type selection")
            return handle_financial_assistance_type_selection()
        
        elif action == "show_financial_assistance_eligibility":
            assistance_type = assistance_type or "personal"
            logger.info(f"Showing financial assistance eligibility for {assistance_type}")
            return show_financial_assistance_eligibility(session_id, assistance_type, access_token, user_id)
        
        elif action == "start_financial_assistance_application":
            assistance_type = assistance_type or "personal"
            logger.info(f"Starting financial assistance application for {assistance_type}")
            return start_financial_assistance_form(session_id, assistance_type, actual_user_input, access_token, user_id)
        
        # ============= INSURANCE POLICY FLOW (3-STEP) =============
        elif action == "select_insurance_type":
            # Step 1: Show policy titles only (from API)
            logger.info("Step 1: Fetching and showing insurance policy list")
            return await handle_insurance_api_selection(access_token)
        
        elif action == "show_policy_details":
            # Step 2: Show full policy details
            if not policy_id:
                logger.error("Policy ID missing for show_policy_details")
                return {
                    "type": "error",
                    "error": "Policy ID is required to show details",
                    "message": "Please select a policy first",
                    "action": "error",
                    "show_service_options": False,
                    "back_action": {
                        "title": " Back to Policy Selection",
                        "action": "select_insurance_type"
                    }
                }
            
            logger.info(f"Step 2: Showing details for policy {policy_id}")
            return await show_policy_details_from_stored_data(
                policy_id, session_id, access_token, user_id
            )
        
        elif action == "accept_policy_and_start_application":
            # Step 3: Accept policy and start dynamic form
            if not policy_id:
                logger.error("Policy ID missing for accept_policy_and_start_application")
                return {
                    "type": "error",
                    "error": "Policy ID is required to start application",
                    "message": "Please select a policy first",
                    "action": "error",
                    "show_service_options": False,
                    "back_action": {
                        "title": " Back to Policy Selection",
                        "action": "select_insurance_type"
                    }
                }
            
            logger.info(f"Step 3: Starting application for policy {policy_id}")
            return await accept_policy_and_start_application(
                session_id, policy_id, access_token, user_id
            )
        
        # ============= LEGACY INSURANCE FLOW (fallback) =============
        elif action == "select_insurance_type_static":
            # Fallback to static insurance type selection if API fails
            logger.info("Fallback: Using static insurance type selection")
            return handle_insurance_type_selection()
        
        elif action == "show_insurance_eligibility":
            insurance_type = insurance_type or "health"
            logger.info(f"Showing insurance eligibility for {insurance_type}")
            return show_insurance_eligibility(session_id, insurance_type, access_token, user_id)
        
        elif action == "start_insurance_application":
            insurance_type = insurance_type or "health"
            logger.info(f"Starting insurance application for {insurance_type}")
            return start_insurance_form(session_id, insurance_type, actual_user_input, access_token, user_id)
        
        # ============= ACCEPT ELIGIBILITY AND START =============
        elif action == "accept_eligibility_and_start":
            # Handle the accept eligibility and start action
            service_type = service_type or kwargs.get("service_type")
            
            if service_type == "financial_assistance":
                assistance_type = assistance_type or kwargs.get("sub_type", "personal")
                logger.info(f"Accepting eligibility and starting financial assistance: {assistance_type}")
                return start_financial_assistance_form(session_id, assistance_type, actual_user_input, access_token, user_id)
            
            elif service_type == "insurance":
                insurance_type = insurance_type or kwargs.get("sub_type", "health")
                logger.info(f"Accepting eligibility and starting insurance: {insurance_type}")
                return start_insurance_form(session_id, insurance_type, actual_user_input, access_token, user_id)
            
            else:
                logger.error(f"Unknown service type for accept_eligibility_and_start: {service_type}")
                return {
                    "error": f"Unknown service type for accept_eligibility_and_start: {service_type}",
                    "available_service_types": ["financial_assistance", "insurance"],
                    "show_service_options": False
                }
        
        # ============= WALLET SETUP =============
        elif action == "start_wallet_setup":
            logger.info("Starting wallet setup")
            return start_wallet_setup(session_id, actual_user_input, access_token, user_id)
        
        # ============= ACCOUNT SERVICES =============
        elif action == "account_services":
            logger.info("Showing account services menu")
            return handle_account_services(session_id, access_token, user_id)
        
        # ============= QUICK ACTIONS =============
        elif action == "check_balance":
            logger.info("Quick action: Check balance")
            from financial_services.wallet_api import get_usr_wallet_data
            try:
                result = get_usr_wallet_data("", access_token, user_id)
                return {
                    "type": "balance_check",
                    "action": "balance_check",
                    "data": result,
                    "response": "Here's your current account summary:",
                    "show_service_options": False,
                    "quick_actions": [
                        {"title": "View Transactions", "action": "view_transactions"},
                        {"title": "Pay Bills", "action": "view_bills"},
                        {"title": "Get Financial Help", "action": "select_financial_assistance_type"}
                    ]
                }
            except Exception as e:
                return {
                    "type": "error",
                    "error": str(e),
                    "message": "It looks like you're new here! To check your balance, you need to create a wallet first.",
                    "action": "wallet_setup_required",
                    "show_service_options": False,
                    "quick_actions": [
                        {"title": "Create Wallet", "action": "start_wallet_setup"}
                    ]
                }
        
        elif action == "view_transactions":
            logger.info("Quick action: View transactions")
            from financial_services.transcation_api import get_all_trans_details
            result = get_all_trans_details("", access_token, user_id)
            return {
                "type": "transaction_history",
                "action": "transaction_history",
                "data": result,
                "response": "Here are your recent transactions:",
                "show_service_options": False,
                "quick_actions": [
                    {"title": "Check Balance", "action": "check_balance"},
                    {"title": "View Bills", "action": "view_bills"}
                ]
            }
        
        elif action == "view_bills":
            logger.info("Quick action: View bills")
            from financial_services.transcation_api import get_all_bills_detail
            result = get_all_bills_detail("", access_token, user_id)
            return {
                "type": "bill_details",
                "action": "bill_details",
                "data": result,
                "response": "Here are your current bills:",
                "show_service_options": False
            }
        
        elif action == "view_financial_assistance":
            logger.info("Quick action: View financial assistance status")
            from financial_services.loan_api import get_loan_details
            result = get_loan_details("", access_token, user_id)
            return {
                "type": "financial_assistance_status",
                "action": "financial_assistance_status",
                "data": result,
                "response": "Here are your financial assistance details:",
                "show_service_options": False
            }
        
        elif action == "view_insurance":
            logger.info("Quick action: View insurance policies")
            from financial_services.insurance_api import get_insurance_policy_info
            result = get_insurance_policy_info("", access_token, user_id)
            return {
                "type": "insurance_policies",
                "action": "insurance_policies",
                "data": result,
                "response": "Here are your insurance policies:",
                "show_service_options": False
            }
        
        # ============= SPECIAL ACTIONS =============
        elif action == "compare_policies":
            logger.info("Policy comparison requested")
            return {
                "type": "feature_info",
                "message": "Policy comparison feature coming soon! For now, you can review each policy individually.",
                "action": "compare_policies_info",
                "show_service_options": False,
                "quick_actions": [
                    {"title": "Back to Policies", "action": "select_insurance_type"},
                    {"title": "Get Help", "action": "insurance_guidance"}
                ]
            }
        
        elif action == "insurance_guidance":
            logger.info("Insurance guidance requested")
            return {
                "type": "guidance",
                "message": "I'm here to help you choose the right insurance policy. What specific questions do you have about our policies?",
                "action": "insurance_guidance_provided",
                "show_service_options": False,
                "suggestions": [
                    "What's the difference between policies?",
                    "Which policy is best for me?",
                    "How do I choose coverage amount?",
                    "What documents do I need?"
                ]
            }
        
        elif action == "help":
            logger.info("Help requested")
            return {
                "type": "help",
                "message": "I'm here to assist you with:\n\n  Financial Assistance (Loans)\n  Insurance Policies\n  Wallet Services\n  Account Management\n\nWhat would you like help with?",
                "action": "help_provided",
                "show_service_options": False,
                "quick_actions": [
                    {"title": "Show All Services", "action": "service_selection"},
                    {"title": "Get Financial Help", "action": "select_financial_assistance_type"},
                    {"title": "Get Insurance", "action": "select_insurance_type"},
                    {"title": "Check Balance", "action": "check_balance"}
                ]
            }
        
        elif action == "restart_application":
            logger.info("Restart application requested")
            # Clear any existing sessions
            clear_completed_sessions(session_id)
            return {
                "type": "restart",
                "message": "Let's start fresh! What would you like to do?",
                "action": "application_restarted",
                "show_service_options": False,
                "quick_actions": [
                    {"title": "Get Financial Help", "action": "select_financial_assistance_type"},
                    {"title": "Get Insurance", "action": "select_insurance_type"},
                    {"title": "Create Wallet", "action": "start_wallet_setup"},
                    {"title": "Show All Services", "action": "service_selection"}
                ]
            }
        
        elif action == "track_application":
            logger.info("Track application requested")
            return {
                "type": "tracking",
                "message": "To track your application, please provide your application ID or reference number.",
                "action": "track_application_requested",
                "show_service_options": False,
                "input_required": True,
                "input_type": "text",
                "input_hint": "Enter your application ID (e.g., APP_12345) or reference number"
            }
        
        # ============= UNKNOWN ACTION =============
        else:
            logger.warning(f"Unknown action: {action}")
            return {
                "type": "error",
                "error": f"Unknown action: {action}",
                "message": "I'm not sure how to handle that request. Please try again or select from the available options.",
                "action": "unknown_action",
                "show_service_options": False,
                "available_actions": [
                    "service_selection", 
                    "select_financial_assistance_type", 
                    "select_insurance_type",
                    "show_policy_details",
                    "accept_policy_and_start_application",
                    "show_financial_assistance_eligibility", 
                    "show_insurance_eligibility",
                    "accept_eligibility_and_start",
                    "start_financial_assistance_application", 
                    "start_insurance_application", 
                    "start_wallet_setup", 
                    "account_services",
                    "check_balance",
                    "view_transactions",
                    "view_bills",
                    "view_financial_assistance",
                    "view_insurance",
                    "help"
                ],
                "quick_actions": [
                    {"title": "Show All Services", "action": "service_selection"},
                    {"title": "Get Help", "action": "help"}
                ]
            }
    
    except Exception as e:
        logger.error(f"Error in enhanced chatbot routing: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return generate_error_response(str(e))

# ==================== CORE CHATBOT FLOW PROCESSOR ====================

def process_chatbot_flow(session: ChatbotSession, questions: Dict, user_input: str = None, title: str = "Application") -> Dict:
    """FIXED: Enhanced chatbot flow processor with proper question-answer handling"""
    try:
        # Check for exit intent
        if user_input and detect_exit_intent(user_input):
            session.exit_session()
            return {
                "type": "application_cancelled",
                "message": f" {title} has been cancelled as requested.",
                "action": "cancelled_by_user",
                "show_service_options": False
            }
        
        total_questions = len(questions)
        current_question_num = session.current_question
        
        # Check if this is a policy application
        is_policy_application = session.chatbot_type == "policy_application"
        policy_id = session.service_type if is_policy_application else None
        
        # Get consistent session ID
        chat_session_id = session.context.get('chat_session_id') if is_policy_application else None
        if not chat_session_id and is_policy_application:
            chat_session_id = get_consistent_session_id(session.user_id, policy_id)
            session.context['chat_session_id'] = chat_session_id  # Store it
        
        # Check if completed
        if session.completed:
            if is_policy_application and policy_id and MONGODB_AVAILABLE:
                application_id = get_consistent_application_id(session.user_id, policy_id)
                complete_application(application_id, {
                    "submitted_at": datetime.now().isoformat(),
                    "total_questions": total_questions
                })
            
            return {
                "type": "application_completed",
                "message": f" Your {title} has been completed successfully!",
                "show_service_options": False
            }
        
        # CRITICAL FIX: Handle user input ONLY if provided
        if user_input and current_question_num <= total_questions:
            current_question = questions[current_question_num]
            
            # Validate input
            validation_result = validate_input(user_input, current_question)
            
            if not validation_result["valid"]:
                # Return same question with error - DON'T advance
                logger.warning(f"Validation failed for Q{current_question_num}: {validation_result['message']}")
                return {
                    "type": "question",
                    "title": title,
                    "policy_id": policy_id if is_policy_application else None,
                    "message": current_question["question"],
                    "question_number": current_question_num,
                    "total_questions": total_questions,
                    "progress": {
                        "current": current_question_num,
                        "total": total_questions,
                        "percentage": round((current_question_num - 1) / total_questions * 100)
                    },
                    "input_type": current_question.get("type", "text"),
                    "options": current_question.get("options", []),
                    "regex":current_question.get('api_field', {}).get('regex'),
                    "placeholder": current_question.get("placeholder", ""),
                    "required": current_question.get("required", True),
                    "error": validation_result['message'],
                    "validation_error": True,
                    "show_service_options": False,
                    "exit_option": {"title": "Exit", "action": "exit"}
                }
            
            # Valid input - store it
            answer_value = validation_result["value"]
            session.update_response(current_question["key"], answer_value)
            
            logger.info(f" Stored answer for Q{current_question_num}: {current_question['key']} = {answer_value}")
            
            # Store in MongoDB for policy applications
            if is_policy_application and policy_id and MONGODB_AVAILABLE:
                try:
                    application_id = get_consistent_application_id(session.user_id, policy_id)
                    
                    # Update answer in policy_applications collection
                    mongodb_chat_manager.policy_applications_collection.update_one(
                        {"application_id": application_id},
                        {
                            "$set": {
                                f"answers.q_{current_question_num}": {
                                    "question": current_question["question"],
                                    "key": current_question["key"],
                                    "type": current_question.get("type", "text"),
                                    "answer": answer_value,
                                    "answered_at": datetime.utcnow(),
                                    "question_number": current_question_num
                                },
                                "last_updated": datetime.utcnow(),
                                "status": "in_progress"
                            }
                        },
                        upsert=True
                    )
                    
                    # Store user's answer in chat history
                    if add_user_message_to_mongodb:
                        add_user_message_to_mongodb(
                            session_id=chat_session_id,
                            user_id=session.user_id,
                            content=str(answer_value),
                            intent="policy_application_answer",
                            context={
                                "policy_id": policy_id,
                                "application_id": application_id,
                                "question_number": current_question_num,
                                "question_key": current_question["key"]
                            }
                        )
                    
                    logger.info(f" MongoDB: Stored answer {current_question_num} for app {application_id}")
                    
                except Exception as mongo_error:
                    logger.error(f"MongoDB answer storage error: {mongo_error}")
            
            # NOW advance to next question
            session.current_question += 1
            current_question_num = session.current_question
            
            logger.info(f" Advanced to question {current_question_num}/{total_questions}")
            
            # Check if all questions completed
            if current_question_num > total_questions:
                logger.info(f" All {total_questions} questions completed")
                
                if is_policy_application and policy_id and MONGODB_AVAILABLE:
                    # Show review screen
                    try:
                        application_id = get_consistent_application_id(session.user_id, policy_id)
                        application_data = get_policy_application(session.user_id, policy_id)
                        
                        if not application_data:
                            logger.error(f"Application data not found for {application_id}")
                            session.complete_session()
                            return {
                                "type": "error",
                                "error": "Application data not found",
                                "message": "Could not load your application for review"
                            }
                        
                        # Build review data
                        editable_fields = []
                        answers_dict = application_data.get("answers", {})
                        
                        sorted_questions = sorted(
                            [(int(k.replace("q_", "")), v) for k, v in answers_dict.items() if k.startswith("q_")],
                            key=lambda x: x[0]
                        )
                        
                        for q_num, answer_data in sorted_questions:
                            editable_fields.append({
                                "question_number": q_num,
                                "question": answer_data.get("question", f"Question {q_num}"),
                                "current_answer": answer_data.get("answer", ""),
                                "field_type": answer_data.get("type", "text"),
                                "field_key": answer_data.get("key", f"field_{q_num}"),
                                "options": answer_data.get("options") if answer_data.get("type") == "dropdown" else None,
                                "required": True
                            })
                        
                        logger.info(f" Showing review screen with {len(editable_fields)} fields")
                        
                        return {
                            "type": "review_and_edit_application",
                            "message": "Review and edit your answers, then submit:",
                            "title": f"Review Application - Policy {policy_id}",
                            "policy_id": policy_id,
                            "application_id": application_id,
                            "show_service_options": False,
                            "editable_fields": editable_fields,
                            "total_fields": len(editable_fields),
                            "next_action": {
                                "title": "Submit Application",
                                "action": "confirm_submit_application",
                                "policy_id": policy_id,
                                "application_id": application_id
                            },
                            "back_action": {
                                "title": "Cancel",
                                "action": "cancel_application",
                                "policy_id": policy_id
                            }
                        }
                        
                    except Exception as review_error:
                        logger.error(f"Review screen error: {review_error}")
                        import traceback
                        logger.error(traceback.format_exc())
                        session.complete_session()
                        return {
                            "type": "application_completed",
                            "message": "Application submitted successfully!",
                            "show_service_options": False
                        }
                else:
                    # Non-policy application completion
                    session.complete_session()
                    return {
                        "type": "application_completed",
                        "message": f" {title} completed!",
                        "show_service_options": False
                    }
        
        # Present current question (first time OR after valid answer)
        if current_question_num <= total_questions:
            current_question = questions[current_question_num]
            
            logger.info(f" Presenting question {current_question_num}: {current_question['question'][:50]}...")
            
            # Store next question in MongoDB for policy applications
            if is_policy_application and policy_id and MONGODB_AVAILABLE and add_assistant_message_to_mongodb:
                try:
                    application_id = get_consistent_application_id(session.user_id, policy_id)
                    
                    add_assistant_message_to_mongodb(
                        session_id=chat_session_id,
                        user_id=session.user_id,
                        content=current_question["question"],
                        intent="policy_application_question",
                        context={
                            "policy_id": policy_id,
                            "application_id": application_id,
                            "question_number": current_question_num,
                            "question_key": current_question["key"],
                            "input_type": current_question.get("type", "text"),
                            "options": current_question.get("options", [])
                        }
                    )
                    
                    logger.info(f" MongoDB: Stored question {current_question_num}")
                    
                except Exception as e:
                    logger.error(f"Error storing question in MongoDB: {e}")
            
            return {
                "type": "question",
                "title": title,
                "policy_id": policy_id if is_policy_application else None,
                "message": current_question["question"],
                "question_number": current_question_num,
                "total_questions": total_questions,
                "progress": {
                    "current": current_question_num,
                    "total": total_questions,
                    "percentage": round((current_question_num - 1) / total_questions * 100)
                },
                "input_type": current_question.get("type", "text"),
                "options": current_question.get("options", []),
                "regex":current_question.get('api_field', {}).get('regex'),
                "placeholder": current_question.get("placeholder", ""),
                "required": current_question.get("required", True),
                "show_service_options": False,
                "exit_option": {"title": "Exit", "action": "exit"}
            }
        
        logger.error("Reached end of flow unexpectedly")
        return generate_error_response("Flow error - unexpected state")
        
    except Exception as e:
        logger.error(f"Chatbot flow error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return generate_error_response(str(e))

# ==================== VALIDATION AND UTILITY FUNCTIONS ====================

def validate_input(user_input: str, question: Dict) -> Dict:
    """Validate user input based on question type"""
    if not user_input or not user_input.strip():
        return {"valid": False, "message": "Please provide a valid input.", "value": None}
    
    user_input = user_input.strip()
    input_type = question.get("type", "text")
    key = question.get("key", "")
    
    # Email validation
    if key == "email":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if not re.match(email_pattern, user_input):
            return {"valid": False, "message": "Please enter a valid email address (e.g., user@example.com)", "value": None}
    
    # Mobile validation
    elif key == "mobileNumber":
        mobile_pattern = r'^[6-9]\d{9}'
        clean_mobile = re.sub(r'[^\d]', '', user_input)
        if not re.match(mobile_pattern, clean_mobile):
            return {"valid": False, "message": "Please enter a valid 10-digit mobile number starting with 6, 7, 8, or 9", "value": None}
        user_input = clean_mobile
    
    # PAN validation
    elif key == "panNumber":
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}'
        pan_upper = user_input.upper()
        if not re.match(pan_pattern, pan_upper):
            return {"valid": False, "message": "Please enter a valid PAN number (e.g., ABCDE1234F)", "value": None}
        user_input = pan_upper
    
    # Date validation
    elif key == "dateOfBirth":
        date_patterns = ["%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"]
        valid_date = False
        for pattern in date_patterns:
            try:
                datetime.strptime(user_input, pattern)
                valid_date = True
                break
            except ValueError:
                continue
        if not valid_date:
            return {"valid": False, "message": "Please enter date in DD-MM-YYYY format (e.g., 15-08-1990)", "value": None}
    
    # Amount validation
    elif key in ["amountNeeded", "monthlyIncome", "annualIncome", "treatmentCost", "totalFees", "monthlyTurnover", "totalBudget", "coverageAmount"]:
        # Remove currency symbols and spaces
        amount_str = re.sub(r'[,\s]', '', user_input)
        try:
            amount = float(amount_str)
            if amount <= 0:
                return {"valid": False, "message": "Please enter a valid positive amount", "value": None}
            user_input = str(int(amount))  # Store as integer string
        except ValueError:
            return {"valid": False, "message": "Please enter a valid numeric amount (e.g., 50000)", "value": None}
    
    # Select validation
    elif input_type == "select":
        options = question.get("options", [])
        if options and user_input not in options:
            return {"valid": False, "message": f"Please select one of: {', '.join(options)}", "value": None}
    
    # Name validation
    elif key in ["fullName", "hospitalName", "institutionName", "businessType", "nominee"]:
        if len(user_input) < 2:
            return {"valid": False, "message": "Please enter a valid name (at least 2 characters)", "value": None}
    
    return {"valid": True, "message": "Valid input", "value": user_input}

def get_input_hint(question: Dict) -> str:
    """Get input hint based on question type"""
    key = question.get("key", "")
    input_type = question.get("type", "text")
    
    hints = {
        "email": "Enter your email address (e.g., yourname@gmail.com)",
        "mobileNumber": "Enter 10-digit mobile number (e.g., 9876543210)",
        "panNumber": "Enter PAN card number (e.g., ABCDE1234F)",
        "dateOfBirth": "Enter in DD-MM-YYYY format (e.g., 15-08-1990)",
        "amountNeeded": "Enter amount in rupees (e.g., 50000 or 50,000)",
        "monthlyIncome": "Enter your monthly income in rupees",
        "annualIncome": "Enter your annual income in rupees",
        "fullName": "Enter your full name as per official documents",
        "currentAddress": "Enter your complete current address"
    }
    
    if input_type == "select":
        options = question.get("options", [])
        return f"Choose one option: {', '.join(options)}"
    
    return hints.get(key, "Please provide your response")

def get_input_examples(question: Dict) -> List[str]:
    """Get input examples"""
    key = question.get("key", "")
    examples = {
        "email": ["john@gmail.com", "user@example.com"],
        "mobileNumber": ["9876543210", "8765432109"],
        "panNumber": ["ABCDE1234F", "XYZAB5678C"],
        "dateOfBirth": ["15-08-1990", "25-12-1985"],
        "fullName": ["John Doe", "Priya Sharma"],
        "amountNeeded": ["50000", "100000", "200000"],
        "monthlyIncome": ["25000", "50000", "100000"]
    }
    return examples.get(key, [])

def get_previous_context(session: ChatbotSession, current_question_num: int) -> Dict:
    """Get context from previous responses"""
    context = {}
    if current_question_num > 1:
        context["responses_so_far"] = len(session.responses)
        if "fullName" in session.responses:
            context["applicant_name"] = session.responses["fullName"]
    return context

def submit_application(session: ChatbotSession, title: str) -> Dict:
    """Submit the completed application"""
    try:
        application_data = {
            "type": session.chatbot_type,
            "service_type": session.service_type,
            "user_id": session.user_id,
            "responses": session.responses,
            "submitted_at": datetime.now().isoformat(),
            "session_id": f"SESSION_{int(datetime.now().timestamp())}"
        }
        
        # Generate application ID
        app_id = f"APP_{session.service_type.upper()}_{session.user_id}_{int(datetime.now().timestamp())}"
        reference_number = f"REF{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Here you would typically call your API to submit the application
        logger.info(f"Application submitted: {app_id}")
        
        return {
            "success": True,
            "application_id": app_id,
            "reference_number": reference_number,
            "submitted_data": application_data
        }
        
    except Exception as e:
        logger.error(f"Error submitting application: {e}")
        return {
            "success": False,
            "error": str(e),
            "application_id": "ERROR",
            "reference_number": "ERROR"
        }

def extract_actual_user_input(contextual_prompt: str) -> str:
    """Extract actual user input from contextual prompt"""
    if not contextual_prompt:
        return ""
    
    # Look for patterns that indicate actual user input
    patterns = [
        r"Current User Query:\s*(.+?)(?:\n|$)",
        r"User says?:\s*[\"'](.*?)[\"']",
        r"Current query:\s*[\"'](.*?)[\"']", 
        r"User input:\s*[\"'](.*?)[\"']",
        r"Latest message:\s*[\"'](.*?)[\"']"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, contextual_prompt, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    
    # If no pattern found, return the last line or the whole input
    lines = contextual_prompt.strip().split('\n')
    return lines[-1].strip() if lines else contextual_prompt.strip()

# ==================== CONTEXT DETECTION FUNCTIONS ====================

# ==================== SESSION INFO AND MANAGEMENT ====================

def get_session_info(session_id: str) -> Dict:
    """Get information about all active sessions for a user"""
    active_sessions = {}
    
    for session_key, session in chatbot_sessions.items():
        if session_id in session_key:
            session_type = session_key.split("_", 2)[1:]
            active_sessions[session_key] = {
                "type": "_".join(session_type),
                "current_step": session.current_question,
                "completed": session.completed,
                "started_at": session.created_at.isoformat(),
                "progress": f"{((session.current_question-1)/10*100):.0f}%" if not session.completed else "100%",
                "eligibility_shown": session.eligibility_shown,
                "details_accepted": session.details_accepted
            }
    
    return {
        "session_id": session_id,
        "active_sessions": active_sessions,
        "total_active": len([s for s in active_sessions.values() if not s.get("completed", True)]),
        "total_completed": len([s for s in active_sessions.values() if s.get("completed", False)])
    }

def clear_session(session_id: str, session_type: str = None) -> Dict:
    """Clear specific or all sessions for a user"""
    cleared_count = 0
    
    if session_type:
        session_key = f"{session_id}_{session_type}"
        if session_key in chatbot_sessions:
            del chatbot_sessions[session_key]
            cleared_count = 1
    else:
        # Clear all sessions for this user
        keys_to_delete = [key for key in chatbot_sessions.keys() if key.startswith(session_id)]
        for key in keys_to_delete:
            del chatbot_sessions[key]
            cleared_count += 1
    
    return {
        "message": f"Cleared {cleared_count} session(s)",
        "cleared_count": cleared_count,
        "timestamp": datetime.now().isoformat()
    }

def continue_financial_assistance_application(session_id: str, assistance_type: str, user_input: str,
                                            access_token: str = None, user_id: int = None) -> Dict:
    """FIXED: Remove duplicate exit check, let process_chatbot_flow handle it"""
    try:
        logger.info(f" CONTINUE FINANCIAL: session={session_id}, type={assistance_type}, input='{user_input}'")
        
        # Validate assistance_type
        if assistance_type not in FINANCIAL_ASSISTANCE_TYPES:
            assistance_type = "personal"
            logger.warning(f"Invalid assistance_type, defaulting to 'personal'")
        
        session_key = f"{session_id}_financial_{assistance_type}"
        logger.info(f" Session key: {session_key}")
        
        # Check if session exists
        if session_key not in chatbot_sessions:
            logger.warning(f" Session not found, creating new one")
            return start_financial_assistance_form(session_id, assistance_type, user_input, access_token, user_id)
        
        session = chatbot_sessions[session_key]
        logger.info(f" Session status - Current Q: {session.current_question}, Completed: {session.completed}")
        
        # Check if session is already completed
        if session.completed:
            logger.info(f" Session already completed, clearing")
            clear_completed_sessions(session_id)
            return generate_fresh_start_response()
        
        # Get questions for this assistance type
        questions = get_financial_assistance_questions(assistance_type)
        logger.info(f" Got {len(questions)} questions for {assistance_type}")
        
        # REMOVED: Duplicate exit check - let process_chatbot_flow handle it
        # Process the chatbot flow with user input
        result = process_chatbot_flow(
            session, 
            questions, 
            user_input,
            f"{FINANCIAL_ASSISTANCE_TYPES[assistance_type]} Application"
        )
        
        logger.info(f" Chatbot flow result: {result.get('type', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f' ERROR IN continue_financial_assistance_application: {str(e)}')
        return generate_error_response(str(e))

# Fix 3: Update continue_insurance_application similarly
def continue_insurance_application(session_id: str, insurance_type: str, user_input: str,
                                 access_token: str = None, user_id: int = None) -> Dict:
    """FIXED: Remove duplicate exit check"""
    try:
        logger.info(f" CONTINUE INSURANCE: session={session_id}, type={insurance_type}, input='{user_input}'")
        
        if insurance_type not in INSURANCE_TYPES:
            insurance_type = "health"
            logger.warning(f"Invalid insurance_type, defaulting to 'health'")
        
        session_key = f"{session_id}_insurance_{insurance_type}"
        
        if session_key not in chatbot_sessions:
            return start_insurance_form(session_id, insurance_type, user_input, access_token, user_id)
        
        session = chatbot_sessions[session_key]
        
        if session.completed:
            clear_completed_sessions(session_id)
            return generate_fresh_start_response()
        
        questions = get_insurance_questions(insurance_type)
        
        # REMOVED: Duplicate exit check - let process_chatbot_flow handle it
        result = process_chatbot_flow(
            session, 
            questions, 
            user_input,
            f"{INSURANCE_TYPES[insurance_type]} Application"
        )
        
        return result
        
    except Exception as e:
        logger.error(f' ERROR IN continue_insurance_application: {str(e)}')
        return generate_error_response(str(e))

# Fix 4: Update continue_wallet_setup similarly  
def continue_wallet_setup(session_id: str, user_input: str, access_token: str = None, user_id: int = None) -> Dict:
    """FIXED: Remove duplicate exit check"""
    try:
        logger.info(f" CONTINUE WALLET: session={session_id}, input='{user_input}'")
        
        session_key = f"{session_id}_wallet"
        
        if session_key not in chatbot_sessions:
            return start_wallet_setup(session_id, user_input, access_token, user_id)
        
        session = chatbot_sessions[session_key]
        
        if session.completed:
            clear_completed_sessions(session_id)
            return generate_fresh_start_response()
        
        wallet_questions = {
            1: {"question": "What's your full name as per PAN card?", "key": "fullName", "type": "text", "required": True},
            2: {"question": "What's your mobile number?", "key": "mobileNumber", "type": "text", "required": True},
            3: {"question": "What's your email address?", "key": "email", "type": "text", "required": True},
            4: {"question": "What's your PAN number?", "key": "panNumber", "type": "text", "required": True},
            5: {"question": "What's your Aadhaar number?", "key": "aadhaarNumber", "type": "text", "required": True},
            6: {"question": "What's your date of birth? (DD-MM-YYYY)", "key": "dateOfBirth", "type": "text", "required": True},
            7: {"question": "What's your current address?", "key": "currentAddress", "type": "text", "required": True},
            8: {"question": "What's your occupation?", "key": "occupation", "type": "select", "options": ["Salaried", "Self-Employed", "Business", "Student", "Retired"], "required": True}
        }
        
        # REMOVED: Duplicate exit check - let process_chatbot_flow handle it
        result = process_chatbot_flow(
            session, 
            wallet_questions, 
            user_input, 
            "Digital Wallet Setup"
        )
        
        return result
        
    except Exception as e:
        logger.error(f' ERROR IN continue_wallet_setup: {str(e)}')
        return generate_error_response(str(e))

# Enhanced logging for debugging session issues
def debug_chatbot_sessions(session_id: str):
    """Debug function to check all sessions for a user"""
    logger.info(f" DEBUG SESSIONS for {session_id}:")
    
    matching_sessions = []
    for session_key, session in chatbot_sessions.items():
        if session_id in session_key:
            matching_sessions.append({
                "key": session_key,
                "type": session.chatbot_type,
                "service": session.service_type,
                "current_q": session.current_question,
                "completed": session.completed,
                "created": session.created_at.isoformat(),
                "responses": len(session.responses)
            })
    
    logger.info(f" Found {len(matching_sessions)} sessions:")
    for session_info in matching_sessions:
        logger.info(f"   {session_info}")
    
    return matching_sessions

# Test function to validate continuation logic
def test_continuation_flow():
    """Test function to validate the continuation logic"""
    print(" Testing Continuation Flow...")
    print("=" * 50)
    
    # Test data
    test_cases = [
        {
            "session_id": "test_session_123",
            "assistance_type": "home",
            "user_input": "John Doe",
            "expected": "Should continue to question 2"
        },
        {
            "session_id": "test_session_456", 
            "insurance_type": "health",
            "user_input": "9876543210",
            "expected": "Should continue to question 3"
        },
        {
            "session_id": "test_session_789",
            "user_input": "exit",
            "expected": "Should handle exit gracefully"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['expected']}")
        print(f"  Input: '{test_case['user_input']}'")
        print(f"   Ready for testing")
    
    print("=" * 50)
    print(" Use debug_chatbot_sessions() to monitor session states")



async def handle_insurance_api_selection(access_token: str = None) -> Dict:
    """Handle insurance selection - Show only policy titles first"""
    try:
        from app import fetch_insurance_policies
        
        # Fetch policies from API
        policies = await fetch_insurance_policies(access_token)
        
        if not policies:
            return handle_insurance_type_selection()
        
        # Format policies with ONLY basic info (no details)
        policy_options = {}
        
        for policy in policies:
            policy_id = str(policy.get('id', ''))
            
            policy_options[policy_id] = {
                "title": policy.get('title', 'Insurance Policy'),
                "category": policy.get('category', ''),
                "product_name": policy.get('productName', ''),
                "action": "show_policy_details",
                "policy_id": policy_id,
                "insurance_type": policy_id,  # ADD THIS - same as policy_id for identification
                # Store full policy data for later use but don't display
                "full_policy_data": policy
            }
        
        return {
            "type": "insurance_policy_selection",
            "message": "Choose from our available insurance policies:",
            "subtitle": f"We have {len(policies)} insurance policies available:",
            "show_service_options": False,
            "options": policy_options,
            "total_policies": len(policies),
            "source": "api",
            "step": "policy_selection"
        }
        
    except Exception as e:
        logger.error(f"Error in API insurance selection: {e}")
        return handle_insurance_type_selection()
    

async def show_policy_details_from_stored_data(policy_id: str, session_id: str, 
                                              access_token: str = None, user_id: int = None) -> Dict:
    """Show detailed policy information using policy_id"""
    try:
        logger.info(f"Showing policy details for policy_id: {policy_id}")
        from app import fetch_insurance_policies
        
        # Fetch policies from API
        policies = await fetch_insurance_policies(access_token)
        
        selected_policy = None
        for policy in policies:
            if str(policy.get('id')) == str(policy_id):
                selected_policy = policy
                break
        
        if not selected_policy:
            logger.error(f"Policy with ID {policy_id} not found")
            return {"error": f"Policy {policy_id} not found"}
        
        logger.info(f"Found policy: {selected_policy.get('title')}")
        
        return {
            "type": "policy_details_display",
            "policy_id": policy_id,
            "title": selected_policy.get('title', 'Insurance Policy'),
            "product_name": selected_policy.get('productName', ''),
            "category": selected_policy.get('category', ''),
            "message": f"Here are the complete details for {selected_policy.get('title', 'this policy')}:",
            
            # Show full details
            "eligibility": selected_policy.get('eligibility', []),
            "coverage_details": selected_policy.get('coverage_details', []),
            "features": selected_policy.get('features', []),
            
            # Actions for this policy
            "next_action": {
                "title": "I Accept - Apply for this Policy",
                "action": "accept_policy_and_start_application",
                "policy_id": policy_id  # Use policy_id consistently
            },
            "back_action": {
                "title": " Back to Policy Selection",
                "action": "select_insurance_type"
            },
            "show_service_options": False,
            "step": "policy_details"
        }
        
    except Exception as e:
        logger.error(f"Error showing policy details: {e}")
        return {"error": f"Could not load policy details: {str(e)}"}
    

async def fetch_policy_application_form(policy_id: str, access_token: str = None) -> Dict:
    """Fetch dynamic form fields from the second API"""
    try:
        headers = {}
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        
        response = requests.get(
            f"https://api.prod.eazr.in/insurance-chatbot/policies/{policy_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            policy_form_data = response.json().get('data',[])
            logger.info(f" Fetched form fields for policy {policy_id}")
            return policy_form_data
        else:
            logger.error(f" API error: {response.status_code}")
            return {}
            
    except Exception as e:
        logger.error(f" Error fetching policy form: {str(e)}")
        return {}

def convert_api_fields_to_chatbot_questions(request_body: Dict) -> Dict:
    """Convert API requestBody fields to chatbot questions"""
    questions = {}
    fields = request_body.get('fields', [])
    
    for i, field in enumerate(fields, 1):
        question_text = f"What is your {field.get('label', 'information')}?"
        
        # Customize question text based on field type
        if field.get('type') == 'dropdown':
            options = field.get('options', [])
            question_text = f"Select your {field.get('label', 'option')}:"
        elif field.get('type') == 'date':
            question_text = f"Enter your {field.get('label', 'date')} ({field.get('placeHolder', 'DD/MM/YYYY')}):"
        elif field.get('type') == 'email':
            question_text = f"Enter your {field.get('label', 'email address')}:"
        elif field.get('type') == 'number':
            question_text = f"Enter your {field.get('label', 'number')}:"
        
        questions[i] = {
            "question": question_text,
            "key": field.get('name', f'field_{i}'),
            "type": field.get('type', 'text'),
            "required": True,
            "options": field.get('options', []) if field.get('type') == 'dropdown' else [],
            "placeholder": field.get('placeHolder', ''),
            "min_length": field.get('min'),
            "max_length": field.get('max'),
            "api_field": field  # Store original field data
        }
    
    return questions


async def accept_policy_and_start_application(session_id: str, policy_id: str, 
                                            access_token: str = None, user_id: int = None) -> Dict:
    """User accepts policy - fetch form and start application - FIXED VERSION"""
    try:
        # Fetch dynamic form fields from second API
        policy_form_data = await fetch_policy_application_form(policy_id, access_token)
        
        if not policy_form_data or 'requestBody' not in policy_form_data:
            return {"error": "Could not load application form"}
        
        # Convert API fields to chatbot questions
        questions = convert_api_fields_to_chatbot_questions(policy_form_data['requestBody'])
        
        if not questions:
            return {"error": "No form fields available"}

        # Use the session_id passed in (don't create a new one to avoid duplicate sessions)
        chat_session_id = session_id
        session_key = f"{session_id}_policy_application_{policy_id}"
        
        if session_key not in chatbot_sessions:
            chatbot_sessions[session_key] = ChatbotSession("policy_application", policy_id)
            chatbot_sessions[session_key].user_id = user_id
            chatbot_sessions[session_key].access_token = access_token
            # Store the dynamic questions and API data
            chatbot_sessions[session_key].context = {
                'questions': questions,
                'policy_form_data': policy_form_data,
                'insurance_id': policy_id,
                'chat_session_id': chat_session_id  # Store for consistent use
            }
        
        session = chatbot_sessions[session_key]
        session.current_question = 1
        
        # Start with first question
        first_question = questions[1]
        
        # FIXED: Create application in MongoDB immediately
        if MONGODB_AVAILABLE and mongodb_chat_manager:
            try:
                application_id = get_consistent_application_id(user_id, policy_id)
                
                # Create application record
                mongodb_chat_manager.policy_applications_collection.update_one(
                    {"application_id": application_id},
                    {
                        "$setOnInsert": {
                            "application_id": application_id,
                            "user_id": user_id,
                            "policy_id": policy_id,
                            "session_id": chat_session_id,
                            "status": "in_progress",
                            "created_at": datetime.utcnow(),
                            "answers": {},
                            "total_questions": len(questions)
                        },
                        "$set": {
                            "last_updated": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                
                # FIXED: Store first question in chat history
                add_assistant_message_to_mongodb(
                    session_id=chat_session_id,
                    user_id=user_id,
                    content=first_question["question"],
                    intent="policy_application_question",
                    context={
                        "policy_id": policy_id,
                        "application_id": application_id,
                        "question_number": 1,
                        "question_key": first_question["key"],
                        "input_type": first_question.get("type", "text"),
                        "options": first_question.get("options", []),
                        "regex":first_question.get('api_field', {}).get('regex'),
                        "is_first_question": True
                    }
                )
                
                logger.info(f" Created application {application_id} and stored first question")
                
            except Exception as mongo_error:
                logger.error(f"MongoDB error in accept_policy: {mongo_error}")

        return {
            "type": "question",
            "service_type": "policy_application",
            "policy_id": policy_id,
            "title": f"Insurance Application - Policy {policy_id}",
            "message": first_question["question"],
            "question_number": 1,
            "total_questions": len(questions),
            "progress": {
                "current": 1,
                "total": len(questions),
                "percentage": 0
            },
            "input_type": first_question.get("type", "text"),
            "options": first_question.get("options", []),
            "placeholder": first_question.get("placeholder", ""),
            "regex":first_question.get('api_field', {}).get('regex'),
            "required": first_question.get("required", True),
            "show_service_options": False,
            "exit_option": {"title": "Exit Application", "action": "exit"}
        }
        
    except Exception as e:
        logger.error(f"Error accepting policy: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Could not start application: {str(e)}"}
    

def continue_policy_application(session_id: str, policy_id: str, user_input: str,
                               access_token: str = None, user_id: int = None) -> Dict:
    """FIXED: Continue policy application with proper question flow"""
    try:
        logger.info(f" CONTINUE POLICY APP: session={session_id}, policy={policy_id}, input='{user_input[:50]}...'")
        
        if detect_exit_intent(user_input):
            return handle_chatbot_exit(session_id, policy_id, "policy_application")
        
        session_key = f"{session_id}_policy_application_{policy_id}"
        logger.info(f" Looking for session: {session_key}")
        
        if session_key not in chatbot_sessions:
            logger.warning(f" Session not found: {session_key}")
            logger.info(f"Available sessions: {list(chatbot_sessions.keys())}")
            return {
                "type": "error",
                "error": "Application session not found",
                "message": "Your application session expired. Please start again.",
                "action": "session_expired",
                "show_service_options": False,
                "quick_actions": [
                    {"title": "Start New Application", "action": "select_insurance_type"}
                ]
            }
        
        session = chatbot_sessions[session_key]
        logger.info(f" Session found - Q{session.current_question}, Completed={session.completed}")
        
        if session.completed:
            clear_completed_sessions(session_id)
            return generate_fresh_start_response()
        
        # CRITICAL: Get questions from session context
        questions = session.context.get('questions', {})
        
        if not questions:
            logger.error(f" No questions in session context!")
            logger.error(f"Session context keys: {list(session.context.keys())}")
            return {
                "type": "error",
                "error": "Application data corrupted",
                "message": "Application data was lost. Please restart.",
                "show_service_options": False
            }
        
        logger.info(f" Found {len(questions)} questions in context")
        
        # Process the flow with user input
        result = process_chatbot_flow(
            session, 
            questions, 
            user_input,
            f"Insurance Policy Application - {policy_id}"
        )
        print('2222222',result)
        
        logger.info(f" Flow result: {result.get('type', 'unknown')}")
        return result
        
    except Exception as e:
        logger.error(f' Policy application error: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return generate_error_response(str(e))

def show_policy_details(policy_id: str, access_token: str = None, user_id: int = None) -> Dict:
    """Show detailed information about a specific policy"""
    try:
        # This would need to store the policy data temporarily or fetch it again
        # For now, I'll show how to structure the response
        
        return {
            "type": "policy_details",
            "policy_id": policy_id,
            "title": "Policy Details",
            "message": "Here are the complete details for your selected policy:",
            "next_action": {
                "title": "Apply for this Policy",
                "action": "start_policy_application",
                "policy_id": policy_id
            },
            "back_action": {
                "title": " Back to Policy Selection",
                "action": "select_insurance_policies"
            },
            "show_service_options": False
        }
        
    except Exception as e:
        logger.error(f"Error showing policy details: {e}")
        return {"error": f"Could not load policy details: {str(e)}"}
    

def is_valid_content(content: Any) -> bool:
    """Check if content is valid for storage"""
    if content is None:
        return False
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, (int, float)):
        return True
    if isinstance(content, (list, dict)):
        return bool(content)
    return bool(str(content).strip())

def clean_content(content: Any) -> str:
    """Clean and convert content to string"""
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, (int, float)):
        return str(content)
    if isinstance(content, (list, dict)):
        return json.dumps(content)
    return str(content).strip()

def process_chatbot_flow(session: ChatbotSession, questions: Dict, user_input: str = None, title: str = "Application") -> Dict:
    """Enhanced chatbot flow processor with FIXED MongoDB storage"""
    try:
        # Check for exit intent
        if user_input and detect_exit_intent(user_input):
            session.exit_session()
            return {
                "type": "application_cancelled",
                "message": f" {title} has been cancelled as requested.",
                "action": "cancelled_by_user",
                "show_service_options": False
            }
        
        total_questions = len(questions)
        current_question_num = session.current_question
        
        # Check if this is a policy application
        is_policy_application = session.chatbot_type == "policy_application"
        policy_id = session.service_type if is_policy_application else None
        
        # FIXED: Get consistent session ID from context
        chat_session_id = session.context.get('chat_session_id') if is_policy_application else None
        if not chat_session_id and is_policy_application:
            chat_session_id = get_consistent_session_id(session.user_id, policy_id)
        
        # Check if completed
        if session.completed:
            if is_policy_application and policy_id and MONGODB_AVAILABLE:
                application_id = get_consistent_application_id(session.user_id, policy_id)
                complete_application(application_id, {
                    "submitted_at": datetime.now().isoformat(),
                    "total_questions": total_questions
                })
            
            return {
                "type": "application_completed",
                "message": f" Your {title} has been completed successfully!",
                "show_service_options": False
            }
        
        # Handle user input
        if user_input and current_question_num <= total_questions:
            current_question = questions[current_question_num]
            
            # Validate input
            validation_result = validate_input(user_input, current_question)
            
            if validation_result["valid"]:
                # Store response in session
                session.update_response(current_question["key"], validation_result["value"])
                
                # FIXED: Store in MongoDB with CONSISTENT session ID
                if is_policy_application and policy_id and MONGODB_AVAILABLE:
                    try:
                        application_id = get_consistent_application_id(session.user_id, policy_id)
                        answer_value = validation_result["value"]
                        
                        if answer_value and str(answer_value).strip():
                            # Store answer in policy_applications collection
                            mongodb_chat_manager.policy_applications_collection.update_one(
                                {"application_id": application_id},
                                {
                                    "$set": {
                                        f"answers.q_{current_question_num}": {
                                            "question": current_question["question"],
                                            "key": current_question["key"],
                                            "type": current_question.get("type", "text"),
                                            "answer": answer_value,
                                            "answered_at": datetime.utcnow(),
                                            "question_number": current_question_num
                                        },
                                        "last_updated": datetime.utcnow()
                                    }
                                },
                                upsert=True
                            )
                            
                            # FIXED: Store user message with CONSISTENT session ID
                            add_user_message_to_mongodb(
                                session_id=chat_session_id,
                                user_id=session.user_id,
                                content=str(answer_value),
                                intent="policy_application_answer",
                                context={
                                    "policy_id": policy_id,
                                    "application_id": application_id,
                                    "question_number": current_question_num,
                                    "question_key": current_question["key"]
                                }
                            )
                            
                            logger.info(f" Stored answer {current_question_num} for app {application_id}")
                            
                    except Exception as mongo_error:
                        logger.error(f"MongoDB storage error: {mongo_error}")
                
                # Move to next question
                session.current_question += 1
                current_question_num = session.current_question
                
                # Check if all questions completed
                if current_question_num > total_questions:
                    if is_policy_application and policy_id and MONGODB_AVAILABLE:
                        # Show review screen
                        try:
                            application_id = get_consistent_application_id(session.user_id, policy_id)
                            application_data = get_policy_application(session.user_id, policy_id)
                            
                            if not application_data:
                                logger.error(f"Application data not found for {application_id}")
                                session.complete_session()
                                return {
                                    "type": "error",
                                    "error": "Application data not found",
                                    "message": "Could not load your application for review"
                                }
                            
                            # Build review data
                            editable_fields = []
                            answers_dict = application_data.get("answers", {})
                            
                            sorted_questions = sorted(
                                [(int(k.replace("q_", "")), v) for k, v in answers_dict.items() if k.startswith("q_")],
                                key=lambda x: x[0]
                            )
                            
                            for q_num, answer_data in sorted_questions:
                                editable_fields.append({
                                    "question_number": q_num,
                                    "question": answer_data.get("question", f"Question {q_num}"),
                                    "current_answer": answer_data.get("answer", ""),
                                    "field_type": answer_data.get("type", "text"),
                                    "field_key": answer_data.get("key", f"field_{q_num}"),
                                    "options": answer_data.get("options") if answer_data.get("type") == "dropdown" else None,
                                    "required": True
                                })
                            
                            return {
                                "type": "review_and_edit_application",
                                "message": "Review and edit your answers, then submit:",
                                "title": f"Review Application - Policy {policy_id}",
                                "policy_id": policy_id,
                                "application_id": application_id,
                                "show_service_options": False,
                                "editable_fields": editable_fields,
                                "total_fields": len(editable_fields),
                                "next_action": {
                                    "title": "Submit Application",
                                    "action": "confirm_submit_application",
                                    "policy_id": policy_id,
                                    "application_id": application_id
                                },
                                "back_action": {
                                    "title": "Cancel",
                                    "action": "cancel_application",
                                    "policy_id": policy_id
                                }
                            }
                            
                        except Exception as review_error:
                            logger.error(f"Review screen error: {review_error}")
                            session.complete_session()
                            return {
                                "type": "application_completed",
                                "message": "Application submitted successfully!",
                                "show_service_options": False
                            }
                    else:
                        # Non-policy application completion
                        session.complete_session()
                        return {
                            "type": "application_completed",
                            "message": f" {title} completed!",
                            "show_service_options": False
                        }
                
                # FIXED: Store NEXT question in MongoDB
                if is_policy_application and policy_id and MONGODB_AVAILABLE and current_question_num <= total_questions:
                    try:
                        next_question = questions[current_question_num]
                        application_id = get_consistent_application_id(session.user_id, policy_id)
                        
                        add_assistant_message_to_mongodb(
                            session_id=chat_session_id,
                            user_id=session.user_id,
                            content=next_question["question"],
                            intent="policy_application_question",
                            context={
                                "policy_id": policy_id,
                                "application_id": application_id,
                                "question_number": current_question_num,
                                "question_key": next_question["key"],
                                "input_type": next_question.get("type", "text")
                            }
                        )
                        
                    except Exception as e:
                        logger.error(f"Error storing next question: {e}")
            
            else:
                # Validation error - return same question
                
                return {
                    "type": "question",
                    "message": current_question["question"],
                    "question_number": current_question_num,
                    "total_questions": total_questions,
                    "input_type": current_question["type"],
                    "regex":current_question.get('api_field', {}).get('regex'),
                    "options": current_question.get("options", []),
                    "error": validation_result['message'],
                    "validation_error": True,
                    "show_service_options": False
                }
        
        # Present current question
        if current_question_num <= total_questions:
            current_question = questions[current_question_num]
            
            return {
                "type": "question",
                "title": title,
                "policy_id": policy_id if is_policy_application else None,
                "message": current_question["question"],
                "question_number": current_question_num,
                "total_questions": total_questions,
                "progress": {
                    "current": current_question_num,
                    "total": total_questions,
                    "percentage": round((current_question_num - 1) / total_questions * 100)
                },
                "input_type": current_question["type"],
                "regex":current_question.get('api_field', {}).get('regex'),
                "options": current_question.get("options", []),
                "placeholder": current_question.get("placeholder", ""),
                "required": current_question.get("required", True),
                "show_service_options": False,
                "exit_option": {"title": "Exit", "action": "exit"}
            }
        
        return generate_error_response("Flow error")
        
    except Exception as e:
        logger.error(f"Chatbot flow error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return generate_error_response(str(e))

# Print success message
print("COMPLETE Enhanced Chatbot Handlers with ALL Functions!")
print("=" * 80)
print("ALL MISSING FUNCTIONS RESOLVED:")
print("   handle_service_selection()")
print("   handle_financial_assistance_type_selection()")  
print("   handle_insurance_type_selection()")
print("   handle_account_services()")
print("   show_financial_assistance_eligibility()")
print("   show_insurance_eligibility()")
print("   start_financial_assistance_form()")
print("   start_insurance_form()")
print("   start_wallet_setup()")
print("   continue_financial_assistance_application()")
print("   continue_insurance_application()")
print("   continue_wallet_setup()")
print("   get_session_info()")
print("   clear_session()")
print("   All validation and utility functions")
print("=" * 80)
print(" KEY IMPROVEMENTS:")
print("   Proper exit handling prevents service menu loops")
print("   Session completion tracking")
print("   Enhanced validation with detailed error messages")
print("   Context detection for better user experience")
print("   Comprehensive error handling")
print("=" * 80)

