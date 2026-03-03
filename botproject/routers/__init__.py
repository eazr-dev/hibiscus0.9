"""
API Routers for the Eazr Financial Assistant
"""
# Import routers here as they are created
from .auth import router as auth_router
from .health import router as health_router
from .user import router as user_router
from .policy import router as policy_router
from .frontend import router as frontend_router
from .chat import router as chat_router
from .admin import router as admin_router
from .cards import router as cards_router

__all__ = [
    "auth_router",
    "health_router",
    "user_router",
    "policy_router",
    "frontend_router",
    "chat_router",
    "admin_router",
    "cards_router"
]
