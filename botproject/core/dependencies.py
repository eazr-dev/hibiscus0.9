"""
Dependency injection and feature flags
"""
import logging
from typing import Optional, Dict
from fastapi import HTTPException, Depends, Header

logger = logging.getLogger(__name__)

# -------------------- Feature Flags --------------------

# MongoDB availability
MONGODB_AVAILABLE = False
try:
    from database_storage.mongodb_chat_manager import mongodb_chat_manager
    if mongodb_chat_manager and mongodb_chat_manager.db is not None:
        MONGODB_AVAILABLE = True
        logger.info("✓ MongoDB integration available")
    else:
        logger.warning("⚠ MongoDB connection exists but database not accessible")
except Exception as e:
    logger.error(f"✗ MongoDB initialization error: {e}")
    MONGODB_AVAILABLE = False

# Redis availability
REDIS_AVAILABLE = False
try:
    from database_storage.simple_redis_config import (
        store_session,
        get_session,
        delete_session,
        cache_api_call,
        get_cached_api_call,
        get_storage_stats,
        check_storage_health
    )
    REDIS_AVAILABLE = True
    logger.info("✓ Redis integration available")
except ImportError:
    logger.info("⚠ Redis not available, using in-memory storage")

    # Fallback to in-memory storage
    _sessions = {}
    _cache = {}

    def store_session(session_id: str, data: Dict, expire_seconds: int = 1209600) -> bool:
        _sessions[session_id] = data
        return True

    def get_session(session_id: str) -> Optional[Dict]:
        return _sessions.get(session_id)

    def delete_session(session_id: str) -> bool:
        if session_id in _sessions:
            del _sessions[session_id]
            return True
        return False

    def cache_api_call(cache_key: str, data, expire_seconds: int = 300) -> bool:
        _cache[cache_key] = data
        return True

    def get_cached_api_call(cache_key: str):
        return _cache.get(cache_key)

    def get_storage_stats():
        return {"storage_type": "in_memory", "total_sessions": len(_sessions)}

    def check_storage_health():
        return {"status": "healthy", "storage_type": "in_memory"}

# LangGraph availability
LANGGRAPH_AVAILABLE = False
try:
    from ai_chat_components.langgraph_chatbot import process_langgraph_chatbot
    LANGGRAPH_AVAILABLE = True
    logger.info("✓ LangGraph chatbot available")
except ImportError:
    logger.info("⚠ LangGraph not available, using enhanced chatbot")

# Voice recognition availability
VOICE_AVAILABLE = False
try:
    from support_features.voice_recognition import (
        handle_voice_upload,
        handle_voice_base64,
        handle_live_recording,
        SUPPORTED_LANGUAGES
    )
    VOICE_AVAILABLE = True
    logger.info("✓ Voice recognition available")
except ImportError:
    logger.info("⚠ Voice recognition not available")

# Multilingual support availability
MULTILINGUAL_AVAILABLE = False
try:
    from support_features.multilingual_support import (
        get_predefined_response,
        process_user_input_with_language_detection,
        translate_chatbot_response,
        set_user_language_preference,
        get_user_language_preference,
        detect_hindi_or_english,
        translate_response,
    )
    MULTILINGUAL_AVAILABLE = True
    logger.info("✓ Multilingual support available")
except ImportError as e:
    logger.info(f"⚠ Multilingual support not available: {e}")

    # Fallback functions
    def process_multilingual_input(query: str, session_id: str) -> Dict:
        return {
            'original_query': query,
            'detected_language': 'en',
            'language_name': 'English',
            'english_query': query,
            'success': True
        }

    def translate_response(response: str, session_id: str) -> str:
        return response

    def get_language_prompts(session_id: str) -> Dict:
        return {'help': "I can help you with loans, insurance, and wallet services."}

    def get_language_suggestions(session_id: str) -> list:
        return ["Apply for loan", "Get insurance", "Create wallet", "Check balance"]


# -------------------- User ID Manager --------------------

uid_manager = None
if MONGODB_AVAILABLE:
    try:
        from database_storage.mongodb_chat_manager import mongodb_chat_manager
        from support_features.user_id_manager import initialize_user_id_manager
        uid_manager = initialize_user_id_manager(mongodb_chat_manager)
        logger.info("✓ User ID Manager initialized")
    except Exception as e:
        logger.error(f"✗ User ID Manager initialization error: {e}")
        uid_manager = None


# -------------------- Dependency Functions --------------------

def get_session_data(session_id: str) -> Dict:
    """
    Dependency to get session data
    Raises HTTPException if session is invalid
    """
    session_data = get_session(session_id)
    if not session_data or not session_data.get('active'):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return session_data


async def verify_token(authorization: str = Header(None)) -> str:
    """
    Dependency to verify JWT token from Authorization header
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        from session_security.token_genrations import verify_jwt_token
        payload = verify_jwt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return payload
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


def get_mongodb_manager():
    """Dependency to get MongoDB manager"""
    if not MONGODB_AVAILABLE:
        raise HTTPException(status_code=503, detail="MongoDB service not available")
    from database_storage.mongodb_chat_manager import mongodb_chat_manager
    return mongodb_chat_manager


def get_user_id_manager():
    """Dependency to get User ID Manager"""
    if not uid_manager:
        raise HTTPException(status_code=503, detail="User ID Manager not available")
    return uid_manager
