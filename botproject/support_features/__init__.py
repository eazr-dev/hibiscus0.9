"""
Support Features Module
========================

This module contains all support feature components including:
- Multilingual support
- Voice recognition
- User ID management
- Tool registration
- Live information
"""

# Import commonly used components
try:
    from .multilingual_support import (
        get_predefined_response,
        process_user_input_with_language_detection,
        translate_chatbot_response,
        detect_hindi_or_english,
        translate_response,
    )
except ImportError:
    pass

try:
    from .voice_recognition import (
        handle_voice_upload,
        handle_voice_base64,
        handle_live_recording,
        SUPPORTED_LANGUAGES,
    )
except ImportError:
    pass

try:
    from .user_id_manager import initialize_user_id_manager
except ImportError:
    pass

__all__ = [
    'get_predefined_response',
    'process_user_input_with_language_detection',
    'translate_chatbot_response',
    'detect_hindi_or_english',
    'translate_response',
    'handle_voice_upload',
    'handle_voice_base64',
    'handle_live_recording',
    'SUPPORTED_LANGUAGES',
    'initialize_user_id_manager',
]
