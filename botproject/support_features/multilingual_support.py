import re
from deep_translator import GoogleTranslator
import langdetect
from typing import Dict, Tuple, List
import logging
import os
import dotenv
import json

# Add your OpenAI key here or load from env

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# openai.api_key = OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Enhanced Hindi patterns for better detection
HINDI_PATTERNS = {
    'devanagari_script': r'[\u0900-\u097F]',
    'hindi_keywords': [
        '', '', '', '', '', '', '', '', '', '', 
        '', '', '', '', '', '', '', '', '', 
        '', '', '', '', '', '', '', '',
        '', '', '', '', ''
    ],
    'romanized_hindi': [
        'muje', 'mujhe', 'mere', 'mera', 'tumhe', 'tumhare', 'tumhara', 
        'kidhar', 'kaise', 'kya', 'kab', 'kaun', 'kyu', 'kyun', 'kahan',
        'hai', 'hain', 'tha', 'thi', 'paisa', 'paise', 'rupaya', 'rupaye', 
        'loan', 'beema', 'khata', 'balance', 'aap', 'namaste', 'dhanyawad',
        'maddat', 'madad', 'chahiye', 'jarurat', 'samasya', 'samadhan',
        'batao', 'bataiye', 'dikhao', 'dekho', 'suno', 'samjhao', 'help',
        'theek', 'achha', 'nahi', 'haa', 'ji', 'sahab', 'madam', 'sir'
    ]
}

# Global language preferences storage
user_language_preferences = {}



from langchain_openai import ChatOpenAI
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Import LLM manager with fallback system
try:
    from ai_chat_components.llm_config import get_llm
    # Get LLM with automatic fallback (tries GPT-3.5 first, then GLM)
    llm = get_llm(use_case='multilingual')
except ImportError:
    # Fallback to direct initialization if llm_config not available
    import os
    from dotenv import load_dotenv
    load_dotenv()
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        temperature=0.0
    )

def detect_hindi_or_english(text: str) -> Tuple[str, float]:
    """
    Detects if the input text is in Hindi or English using GPT-3.5 via LangChain.
    Supports Devanagari and Romanized Hindi.
    Returns: ('hi' or 'en', confidence)
    """
    if not text or not text.strip():
        return 'en', 0.5

    prompt = f"""
You are a language classification assistant.

Your task is to determine if the following sentence is in:

- Hindi (including Hindi written using Latin script, e.g., "muje loan chahiye")
- English

Only return one of the following values:
- hi
- en

Do not add any extra words.

Text: "{text}"
"""

    try:
        response = llm.invoke(prompt)
        print(response)
        response_text = str(response.content)
        print(response_text)
        # if response in ['hi', 'en']:
        #     confidence = 0.95 if response == 'hi' else 0.90
        #     return response, confidence
        # return 'en', 0.80  # fallback if unexpected output
        if response_text == 'en':
            return 'en', 0.90
        elif response_text == 'hi':
            return 'hi', 0.90
        else:
            return 'en', 0.90



    except Exception as e:
        logger.error(f"LangChain LLM language detection failed: {e}")
        return 'en', 0.70  # fallback on error



def translate_to_target_language(text: str, target_lang: str) -> str:
    """Improved translation with better error handling"""
    if not text or not text.strip():
        return text
    
    try:
        # Quick predefined translations for common phrases
        if target_lang == 'hi':
            quick_translations = {
                "hello": "",
                "thank you": "",
                "yes": "",
                "no": "",
                "help": "",
                "balance": "",
                "money": "",
                "loan": "",
                "insurance": ""
            }
            for eng, hin in quick_translations.items():
                if eng.lower() in text.lower():
                    text = text.lower().replace(eng.lower(), hin)
        
        # Detect source language
        source_lang, _ = detect_hindi_or_english(text)
        
        # If already in target language, return as is
        if source_lang == target_lang:
            return text
        
        # Use Google Translator
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated = translator.translate(text)
        return translated if translated else text
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

def process_user_input_with_language_detection(query: str, session_id: str) -> Dict:
    """Process user input and detect language"""
    detected_lang, confidence = detect_hindi_or_english(query)
    
    # Translate to English for processing if needed
    english_query = query
    if detected_lang == 'hi':
        english_query = translate_to_target_language(query, 'en')
    
    return {
        'original_query': query,
        'detected_language': detected_lang,
        'confidence': confidence,
        'english_query': english_query,
        'language_name': 'Hindi' if detected_lang == 'hi' else 'English'
    }

def set_user_language_preference(session_id: str, language: str):
    """Set user language preference for session"""
    global user_language_preferences
    user_language_preferences[session_id] = language

def get_user_language_preference(session_id: str) -> str:
    """Get user language preference for session"""
    global user_language_preferences
    return user_language_preferences.get(session_id, 'en')

# Predefined responses in both languages
PREDEFINED_RESPONSES = {
    'casual': {
        'en': {
            'joke': "Sure! Why did the scarecrow win an award? Because he was outstanding in his field! ",
            'greeting': "Hello! How can I help you with your financial needs today?",
            'thanks': "You're welcome! Is there anything else I can help you with?",
            'help': "I can help you with loans, insurance, wallet setup, and account management."
        },
        'hi': {
            'joke': "!      ?   ''  ! ",
            'greeting': "!           ?",
            'thanks': "  !          ?",
            'help': "  , ,          "
        }
    },
    'financial_assistance': {
        'en': "I understand you need financial assistance. Life brings unexpected expenses and financial challenges. Let me help you find the right funding solution that suits your needs and gives you peace of mind.",
        'hi': "                                 "
    }
}

def get_predefined_response(response_type: str, language: str, sub_type: str = None) -> str:
    """Get predefined response in specified language"""
    if response_type in PREDEFINED_RESPONSES:
        if isinstance(PREDEFINED_RESPONSES[response_type], dict):
            if sub_type and sub_type in PREDEFINED_RESPONSES[response_type].get(language, {}):
                return PREDEFINED_RESPONSES[response_type][language][sub_type]
            elif language in PREDEFINED_RESPONSES[response_type]:
                return PREDEFINED_RESPONSES[response_type][language]
    return ""

def translate_chatbot_response(chatbot_result: dict, session_id: str) -> dict:
    """Translate all relevant chatbot response fields"""
    try:
        user_lang = get_user_language_preference(session_id)
        
        if user_lang == 'en':
            return chatbot_result
        
        # Translate main response fields
        fields_to_translate = ['response', 'question', 'message', 'summary']
        for field in fields_to_translate:
            if field in chatbot_result and chatbot_result[field]:
                chatbot_result[field] = translate_to_target_language(chatbot_result[field], 'hi')
        
        # Translate options if present
        if 'options' in chatbot_result and isinstance(chatbot_result['options'], dict):
            for option_key, option_data in chatbot_result['options'].items():
                if isinstance(option_data, dict):
                    if 'title' in option_data:
                        option_data['title'] = translate_to_target_language(option_data['title'], 'hi')
                    if 'description' in option_data:
                        option_data['description'] = translate_to_target_language(option_data['description'], 'hi')
        
        return chatbot_result
        
    except Exception as e:
        logger.error(f"Error in translate_chatbot_response: {e}")
        return chatbot_result

# Updated compatibility functions
def process_multilingual_input(query: str, session_id: str) -> Dict:
    """Compatibility function"""
    result = process_user_input_with_language_detection(query, session_id)
    set_user_language_preference(session_id, result['detected_language'])
    return {
        'original_query': result['original_query'],
        'detected_language': result['detected_language'],
        'language_name': result['language_name'],
        'english_query': result['english_query'],
        'confidence': result['confidence'],
        'success': True
    }

def translate_response(response: str, session_id: str) -> str:
    """Compatibility function"""
    user_lang = get_user_language_preference(session_id)
    if user_lang == 'hi':
        return translate_to_target_language(response, 'hi')
    return response

def get_user_language(session_id: str) -> str:
    """Compatibility function"""
    return get_user_language_preference(session_id)