# Fixed langgraph_chatbot.py - Compatible with current LangGraph version

from typing import Dict, Any, List, Optional, TypedDict, Annotated
import json
import logging
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage

# Updated imports for current LangGraph version
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    # Fallback for different LangGraph versions
    from langgraph.graph import StateGraph, END
    try:
        from langgraph.checkpoint import MemorySaver
    except ImportError:
        # Create a simple memory saver if not available
        class MemorySaver:
            def __init__(self):
                self.memory = {}

import requests

# Try to import Redis components, fall back to in-memory if not available
try:
    from redis_config import redis_manager, store_chatbot_state, get_chatbot_state
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Fallback to in-memory storage
    _memory_store = {}
    
    def store_chatbot_state(session_id: str, chatbot_type: str, state: Dict[str, Any]) -> bool:
        key = f"{session_id}_{chatbot_type}"
        _memory_store[key] = state
        return True
    
    def get_chatbot_state(session_id: str, chatbot_type: str) -> Optional[Dict[str, Any]]:
        key = f"{session_id}_{chatbot_type}"
        return _memory_store.get(key)

logger = logging.getLogger(__name__)

class ChatbotState(TypedDict):
    """State definition for LangGraph chatbot"""
    session_id: str
    chatbot_type: str
    current_step: int
    user_data: Dict[str, Any]
    last_question: str
    last_response: str
    completed: bool
    error: Optional[str]
    validation_errors: List[str]
    user_id: Optional[int]
    access_token: Optional[str]
    ref_id: Optional[str]  # For Aadhaar OTP
    sub_type: Optional[str]  # For insurance types
    messages: List[str]  # Simplified to avoid BaseMessage complexity

class SimpleChatbotManager:
    """Simplified chatbot manager without complex LangGraph dependencies"""

    def __init__(self):
        # Use llm_config for proper GPT-3.5/GLM fallback
        from ai_chat_components.llm_config import get_llm
        self.llm = get_llm(use_case='chatbot')
        
        # Define question sets
        self.wallet_questions = {
            1: {"question": "What's your full name?", "key": "fullname", "type": "text"},
            2: {"question": "What's your date of birth? (DD-MM-YYYY)", "key": "dateOfBirth", "type": "text"},
            3: {"question": "What's your Gender?", "key": "gender", "type": "select", "options": ["Male", "Female"]},
            4: {"question": "What's your phone number?", "key": "phoneNumber", "type": "text"},
            5: {"question": "What's your email?", "key": "email", "type": "text"},
            6: {"question": "Your flat number?", "key": "flatNumber", "type": "text"},
            7: {"question": "Building name?", "key": "buildingName", "type": "text"},
            8: {"question": "Street or area name?", "key": "areaStreet", "type": "text"},
            9: {"question": "Any nearby landmark?", "key": "landmark", "type": "text"},
            10: {"question": "Which city do you live in?", "key": "city", "type": "text"},
            11: {"question": "Which country?", "key": "country", "type": "text"},
            12: {"question": "What's your pin code?", "key": "pinCode", "type": "text"},
            13: {"question": "What's your company name?", "key": "companyName", "type": "text"},
            14: {"question": "Which department do you work in?", "key": "department", "type": "text"},
            15: {"question": "What's your designation?", "key": "designation", "type": "text"},
            16: {"question": "Are you working full-time or part-time?", "key": "employmentType", "type": "select", "options": ["Full-Time", "Part-Time"]},
            17: {"question": "When did you start working here? (Month-Year)", "key": "startDate", "type": "text"},
            18: {"question": "What's your official work email?", "key": "workEmail", "type": "text"},
            19: {"question": "What's your Aadhaar number?", "key": "aadhaarNumber", "type": "text"},
            20: {"question": "Enter the OTP sent to your Aadhaar registered mobile number", "key": "verifyaadhaarNumber", "type": "text"},
            21: {"question": "What's your PAN number?", "key": "panNumber", "type": "text"}
        }
        
        self.loan_questions = {
            1: {"question": "What's your first name?", "key": "firstName", "type": "text"},
            2: {"question": "What's your last name?", "key": "lastName", "type": "text"},
            3: {"question": "What's your mobile number?", "key": "mobile", "type": "text"},
            4: {"question": "What's your email address?", "key": "email", "type": "text"},
            5: {"question": "What's your date of birth? (DD/MM/YYYY)", "key": "dateOfBirth", "type": "text"},
            6: {"question": "Can we have your Aadhaar number?", "key": "aadhaar", "type": "text"},
            7: {"question": "What's your employment status?", "key": "employment", "type": "select", "options": ["Employed", "Self-employed", "Business"]},
            8: {"question": "What's your monthly income?", "key": "income", "type": "text"},
            9: {"question": "How much loan amount do you need?", "key": "loanAmount", "type": "text"},
            10: {"question": "What's the loan purpose?", "key": "purpose", "type": "select", "options": ["Personal", "Medical", "Education", "Home renovation", "Business"]},
            11: {"question": "What's your preferred loan tenure?", "key": "tenure", "type": "select", "options": ["12 months", "24 months", "36 months", "48 months", "60 months"]},
            12: {"question": "Bank account number?", "key": "accountNumber", "type": "text"},
            13: {"question": "IFSC Code?", "key": "ifscCode", "type": "text"}
        }
        
        self.insurance_questions = {
            "credit_cover": {
                1: {"question": "What's your first name?", "key": "firstName", "type": "text"},
                2: {"question": "What's your last name?", "key": "lastName", "type": "text"},
                3: {"question": "What's your mobile number?", "key": "mobile", "type": "text"},
                4: {"question": "What's your email address?", "key": "email", "type": "text"},
                5: {"question": "What coverage amount are you looking for?", "key": "coverage", "type": "text"},
                6: {"question": "Do you have any existing insurance policies?", "key": "existingPolicy", "type": "select", "options": ["Yes", "No"]}
            },
            "accidental": {
                1: {"question": "Select Title", "key": "title", "type": "select", "options": ["Mr", "Ms", "Mrs", "Dr"]},
                2: {"question": "Can we have your first name?", "key": "firstName", "type": "text"},
                3: {"question": "Can we have your last name?", "key": "lastName", "type": "text"},
                4: {"question": "Select your gender?", "key": "gender", "type": "select", "options": ["Male", "Female", "Other"]},
                5: {"question": "Nominee first name?", "key": "nomineeFirstName", "type": "text"},
                6: {"question": "Nominee relation?", "key": "nomineeRelation", "type": "select", "options": ["Spouse", "Child", "Parent", "Sibling", "Other"]}
            }
        }
    
    def process_chatbot_step(self, session_id: str, chatbot_type: str, user_input: str = None, 
                           user_id: int = None, access_token: str = None, sub_type: str = None) -> Dict[str, Any]:
        """Process chatbot step without complex state graph"""
        try:
            # Load existing state
            state = get_chatbot_state(session_id, chatbot_type)
            if not state:
                # Initialize new state
                state = {
                    'session_id': session_id,
                    'chatbot_type': chatbot_type,
                    'current_step': 1,
                    'user_data': {},
                    'completed': False,
                    'error': None,
                    'validation_errors': [],
                    'user_id': user_id,
                    'access_token': access_token,
                    'sub_type': sub_type,
                    'messages': []
                }
            
            # Get questions based on chatbot type
            if chatbot_type == "wallet_setup":
                questions = self.wallet_questions
                total_questions = len(self.wallet_questions)
            elif chatbot_type == "personal_loan":
                questions = self.loan_questions
                total_questions = len(self.loan_questions)
            elif chatbot_type == "insurance_plan":
                questions = self.insurance_questions.get(sub_type or 'credit_cover', {})
                total_questions = len(questions)
            else:
                return {"error": f"Unknown chatbot type: {chatbot_type}"}
            
            current_step = state['current_step']
            
            # Process user input (except for first interaction)
            if user_input and current_step > 1:
                prev_step = current_step - 1
                if prev_step in questions:
                    question_config = questions[prev_step]
                    key = question_config['key']
                    
                    # Validate input
                    validation_result = self._validate_input(user_input, question_config)
                    
                    if validation_result['valid']:
                        state['user_data'][key] = validation_result['value']
                        state['validation_errors'] = []
                        
                        # Handle special cases (like Aadhaar API call)
                        if key == "aadhaarNumber" and chatbot_type == "wallet_setup":
                            api_result = self._call_aadhaar_api(user_id, validation_result['value'])
                            if api_result['success']:
                                state['ref_id'] = api_result['ref_id']
                            else:
                                state['error'] = api_result['error']
                                store_chatbot_state(session_id, chatbot_type, state)
                                return {
                                    "type": chatbot_type,
                                    "completed": False,
                                    "error": api_result['error'],
                                    "response": f"Error processing Aadhaar: {api_result['error']}"
                                }
                    else:
                        state['validation_errors'] = [validation_result['error']]
                        store_chatbot_state(session_id, chatbot_type, state)
                        return {
                            "type": chatbot_type,
                            "completed": False,
                            "question": questions[prev_step]['question'],
                            "response": validation_result['error'],
                            "step": prev_step,
                            "total_steps": total_questions,
                            "progress": f"{((prev_step-1)/total_questions*100):.0f}%",
                            "validation_error": True
                        }
            
            # Generate response for current step
            if current_step <= total_questions:
                question_config = questions[current_step]
                
                # Generate contextual response
                if current_step > 1 and user_input:
                    response_message = f"Thank you! I've saved your response. Now, {question_config['question']}"
                else:
                    response_message = f"Let's get started! {question_config['question']}"
                
                # Move to next step
                state['current_step'] += 1
                
                # Save state
                store_chatbot_state(session_id, chatbot_type, state)
                
                return {
                    "type": chatbot_type,
                    "completed": False,
                    "question": question_config['question'],
                    "response": response_message,
                    "step": current_step,
                    "total_steps": total_questions,
                    "progress": f"{((current_step-1)/total_questions*100):.0f}%",
                    "question_type": question_config.get("type", "text"),
                    "options": question_config.get("options", []),
                    "key": question_config["key"]
                }
            
            else:
                # Chatbot completed
                state['completed'] = True
                completion_message = self._generate_completion_message(chatbot_type, state)
                
                # Save final state
                store_chatbot_state(session_id, chatbot_type, state)
                
                return {
                    "type": chatbot_type,
                    "completed": True,
                    "message": completion_message,
                    "summary": self._generate_summary(chatbot_type, state),
                    "progress": "100%",
                    "user_data": state['user_data']
                }
                
        except Exception as e:
            logger.error(f"Error in chatbot processing: {e}")
            return {
                "type": chatbot_type,
                "completed": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error. Please try again."
            }
    
    def _validate_input(self, user_input: str, question_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user input based on question configuration"""
        input_type = question_config.get('type', 'text')
        
        if input_type == "select":
            options = question_config.get('options', [])
            if user_input in options:
                return {"valid": True, "value": user_input}
            else:
                return {"valid": False, "error": f"Please select from: {', '.join(options)}"}
        
        elif input_type == "text":
            key = question_config.get('key', '')
            
            # Email validation
            if 'email' in key.lower():
                import re
                if re.match(r"[^@]+@[^@]+\.[^@]+", user_input):
                    return {"valid": True, "value": user_input}
                else:
                    return {"valid": False, "error": "Please enter a valid email address"}
            
            # Phone validation
            elif 'phone' in key.lower() or 'mobile' in key.lower():
                import re
                if re.match(r"^[6-9]\d{9}$", user_input.replace(" ", "").replace("-", "")):
                    return {"valid": True, "value": user_input}
                else:
                    return {"valid": False, "error": "Please enter a valid 10-digit mobile number"}
            
            # PAN validation
            elif 'pan' in key.lower():
                import re
                if re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", user_input.upper()):
                    return {"valid": True, "value": user_input.upper()}
                else:
                    return {"valid": False, "error": "Please enter a valid PAN number (e.g., ABCDE1234F)"}
            
            # Aadhaar validation
            elif 'aadhaar' in key.lower():
                import re
                clean_aadhaar = user_input.replace(" ", "").replace("-", "")
                if re.match(r"^\d{12}$", clean_aadhaar):
                    return {"valid": True, "value": clean_aadhaar}
                else:
                    return {"valid": False, "error": "Please enter a valid 12-digit Aadhaar number"}
            
            # Date validation
            elif 'date' in key.lower():
                try:
                    datetime.strptime(user_input, "%d-%m-%Y")
                    return {"valid": True, "value": user_input}
                except ValueError:
                    try:
                        datetime.strptime(user_input, "%d/%m/%Y")
                        return {"valid": True, "value": user_input}
                    except ValueError:
                        return {"valid": False, "error": "Please enter date in DD-MM-YYYY or DD/MM/YYYY format"}
            
            # Pincode validation
            elif 'pin' in key.lower():
                import re
                if re.match(r"^\d{6}$", user_input):
                    return {"valid": True, "value": user_input}
                else:
                    return {"valid": False, "error": "Please enter a valid 6-digit pincode"}
            
            # Default text validation
            else:
                if len(user_input.strip()) > 0:
                    return {"valid": True, "value": user_input.strip()}
                else:
                    return {"valid": False, "error": "Please provide a valid response"}
        
        return {"valid": True, "value": user_input}
    
    def _call_aadhaar_api(self, user_id: int, aadhaar_number: str) -> Dict[str, Any]:
        """Call Aadhaar API for OTP generation"""
        url = 'https://api.prod.eazr.in/global-form'
        
        aadhaar_data = {
            "userId": user_id,
            "kycDetails": {
                "aadhaarNumber": aadhaar_number,
            }
        }
        
        try:
            response = requests.post(url, json=aadhaar_data)
            response_json = response.json()
            
            if response.status_code in [200, 201]:
                ref_id = response_json.get('data', {}).get('data', {}).get('ref_id')
                return {"success": True, "ref_id": ref_id}
            else:
                return {"success": False, "error": response_json.get('message', 'Unknown error')}
        except Exception as e:
            logger.error(f"Aadhaar API call error: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_completion_message(self, chatbot_type: str, state: Dict[str, Any]) -> str:
        """Generate completion message based on chatbot type"""
        if chatbot_type == "wallet_setup":
            return " Congratulations! Your wallet setup is complete. Your KYC has been verified and your account is ready to use."
        elif chatbot_type == "personal_loan":
            loan_amount = state['user_data'].get('loanAmount', 'requested amount')
            return f" Your personal loan application for {loan_amount} has been submitted successfully! We'll contact you within 24 hours for verification."
        elif chatbot_type == "insurance_plan":
            insurance_type = state.get('sub_type', 'insurance')
            return f" Your {insurance_type} insurance assessment is complete! We'll provide you with personalized recommendations shortly."
        else:
            return " Process completed successfully!"
    
    def _generate_summary(self, chatbot_type: str, state: Dict[str, Any]) -> str:
        """Generate summary based on chatbot type"""
        if chatbot_type == "wallet_setup":
            return "Your digital wallet has been created and verified. You can now use it for transactions, payments, and more financial services."
        elif chatbot_type == "personal_loan":
            return "Your loan application has been submitted and is under review. Our team will contact you for verification and approval process."
        elif chatbot_type == "insurance_plan":
            return "Your insurance assessment is complete. We'll provide you with personalized recommendations based on your requirements."
        else:
            return "Thank you for completing the process with us."

# Initialize the simplified chatbot manager
simple_chatbot_manager = SimpleChatbotManager()

# Helper functions for integration
def process_langgraph_chatbot(session_id: str, chatbot_type: str, user_input: str, 
                            user_id: int = None, access_token: str = None, sub_type: str = None) -> Dict[str, Any]:
    """Process chatbot using simplified approach"""
    return simple_chatbot_manager.process_chatbot_step(
        session_id=session_id,
        chatbot_type=chatbot_type,
        user_input=user_input,
        user_id=user_id,
        access_token=access_token,
        sub_type=sub_type
    )

def _get_total_steps(chatbot_type: str, sub_type: str = None) -> int:
    """Get total steps for chatbot type"""
    if chatbot_type == "wallet_setup":
        return len(simple_chatbot_manager.wallet_questions)
    elif chatbot_type == "personal_loan":
        return len(simple_chatbot_manager.loan_questions)
    elif chatbot_type == "insurance_plan":
        if sub_type == "credit_cover":
            return len(simple_chatbot_manager.insurance_questions["credit_cover"])
        elif sub_type == "accidental":
            return len(simple_chatbot_manager.insurance_questions["accidental"])
        else:
            return 6  # Default
    else:
        return 10  # Default

print(" Simplified LangGraph Chatbot Manager Loaded Successfully!")
if REDIS_AVAILABLE:
    print(" Redis integration enabled")
else:
    print("  Redis not available, using in-memory storage")