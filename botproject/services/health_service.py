"""
Health Service - System Health Check Business Logic
Extracted from routers/health.py for better separation of concerns
"""
import logging
from datetime import datetime
from typing import Dict, Any

# Core dependencies
from core.dependencies import (
    REDIS_AVAILABLE,
    MONGODB_AVAILABLE,
    LANGGRAPH_AVAILABLE,
    VOICE_AVAILABLE,
    MULTILINGUAL_AVAILABLE,
    check_storage_health,
    get_storage_stats
)

logger = logging.getLogger(__name__)


class HealthService:
    """
    Business logic for system health checks and monitoring

    This service provides health check functionality for:
    - Basic system status
    - Service availability (Redis, MongoDB, etc.)
    - Feature availability
    - Memory and storage statistics
    """

    def __init__(self):
        self.logger = logger
        self.version = "4.0.0"
        self.service_name = "Enhanced Financial Assistant API"

    def get_basic_health(self) -> Dict[str, Any]:
        """
        Get basic health status

        Returns:
            dict: Basic health information with status and timestamp
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": self.service_name,
            "version": self.version
        }

    def get_enhanced_health(self) -> Dict[str, Any]:
        """
        Get enhanced health status with service availability

        Returns:
            dict: Enhanced health information including service status
        """
        storage_health = check_storage_health()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": self.version,
            "services": {
                "redis": {
                    "available": REDIS_AVAILABLE,
                    "health": storage_health if REDIS_AVAILABLE else None
                },
                "mongodb": {
                    "available": MONGODB_AVAILABLE
                },
                "langgraph": {
                    "available": LANGGRAPH_AVAILABLE
                },
                "voice_recognition": {
                    "available": VOICE_AVAILABLE
                },
                "multilingual": {
                    "available": MULTILINGUAL_AVAILABLE
                }
            },
            "features": {
                "chat_memory": True,
                "enhanced_chatbot": True,
                "insurance_analysis": True,
                "financial_assistance": True,
                "wallet_services": True,
                "quick_actions": True
            }
        }

    def get_health_with_memory(self) -> Dict[str, Any]:
        """
        Get comprehensive health status including memory statistics

        Returns:
            dict: Complete health information with memory stats
        """
        from ai_chat_components.chat_memory import chat_memory

        storage_health = check_storage_health()
        storage_stats = get_storage_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": self.version,
            "services": {
                "redis": {
                    "available": REDIS_AVAILABLE,
                    "health": storage_health if REDIS_AVAILABLE else None,
                    "stats": storage_stats if REDIS_AVAILABLE else None
                },
                "mongodb": {
                    "available": MONGODB_AVAILABLE
                },
                "langgraph": {
                    "available": LANGGRAPH_AVAILABLE
                },
                "voice_recognition": {
                    "available": VOICE_AVAILABLE
                },
                "multilingual": {
                    "available": MULTILINGUAL_AVAILABLE
                }
            },
            "features": {
                "chat_memory": True,
                "enhanced_chatbot": True,
                "insurance_analysis": True,
                "financial_assistance": True,
                "wallet_services": True,
                "quick_actions": True,
                "persistent_storage": MONGODB_AVAILABLE,
                "session_caching": REDIS_AVAILABLE
            },
            "memory_stats": {
                "active_sessions": len(chat_memory.conversations),
                "total_messages": sum(len(conv) for conv in chat_memory.conversations.values())
            }
        }

    def check_service_availability(self) -> Dict[str, bool]:
        """
        Check availability of all services

        Returns:
            dict: Service availability flags
        """
        return {
            "redis": REDIS_AVAILABLE,
            "mongodb": MONGODB_AVAILABLE,
            "langgraph": LANGGRAPH_AVAILABLE,
            "voice_recognition": VOICE_AVAILABLE,
            "multilingual": MULTILINGUAL_AVAILABLE
        }

    def get_storage_health_status(self) -> Dict[str, Any]:
        """
        Get detailed storage health status

        Returns:
            dict: Storage health and statistics
        """
        return {
            "health": check_storage_health() if REDIS_AVAILABLE else None,
            "stats": get_storage_stats() if REDIS_AVAILABLE else None,
            "available": REDIS_AVAILABLE
        }
