"""
Database & Storage Module
==========================

This module contains all database and storage-related components including:
- MongoDB chat manager
- Redis configuration and monitoring
- AWS S3 bucket integration
"""

# Import commonly used components
try:
    from .mongodb_chat_manager import (
        mongodb_chat_manager,
        add_user_message_to_mongodb,
        add_assistant_message_to_mongodb,
        get_conversation_context_from_mongodb,
    )
except ImportError:
    mongodb_chat_manager = None

try:
    from .simple_redis_config import (
        store_session,
        get_session,
        delete_session,
        cache_api_call,
        get_cached_api_call,
        get_storage_stats,
        check_storage_health,
    )
except ImportError:
    pass

try:
    from .s3_bucket import upload_to_s3, generate_s3_url
except ImportError:
    pass

__all__ = [
    'mongodb_chat_manager',
    'add_user_message_to_mongodb',
    'add_assistant_message_to_mongodb',
    'get_conversation_context_from_mongodb',
    'store_session',
    'get_session',
    'delete_session',
    'cache_api_call',
    'get_cached_api_call',
    'get_storage_stats',
    'check_storage_health',
    'upload_to_s3',
    'generate_s3_url',
]
