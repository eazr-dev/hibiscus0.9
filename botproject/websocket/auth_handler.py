"""
WebSocket Authentication Handler for EAZR Chat
Handles JWT authentication for WebSocket connections.
"""

from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone
import time
import secrets
import logging

logger = logging.getLogger(__name__)


class WebSocketAuthHandler:
    """
    Handles WebSocket authentication.

    Authentication flow:
    1. Client sends authenticate message with JWT token
    2. Server validates token via verify_jwt_token()
    3. Server validates/regenerates session via session_manager
    4. Server sends auth_success or auth_failure

    Reuses existing authentication components:
    - verify_jwt_token() from session_security/token_genrations.py
    - session_manager from session_security/session_manager.py
    - get_session(), store_session() from core/dependencies.py
    """

    def __init__(self):
        """Initialize auth handler with lazy imports for dependencies"""
        self._verify_jwt_token = None
        self._session_manager = None
        self._get_session = None
        self._store_session = None
        self._mongodb_chat_manager = None
        self._initialized = False
        # Instance-level fallback session storage (not class-level to avoid sharing across instances)
        self._fallback_sessions: Dict[str, Dict[str, Any]] = {}

    def _ensure_initialized(self) -> bool:
        """Lazy initialize dependencies"""
        if self._initialized:
            return True

        try:
            from session_security.token_genrations import verify_jwt_token
            self._verify_jwt_token = verify_jwt_token
        except ImportError as e:
            logger.error(f"Failed to import verify_jwt_token: {e}")
            return False

        try:
            from session_security.session_manager import session_manager
            self._session_manager = session_manager
        except ImportError as e:
            logger.warning(f"Session manager not available: {e}")
            self._session_manager = None

        try:
            from core.dependencies import get_session, store_session
            self._get_session = get_session
            self._store_session = store_session
        except ImportError as e:
            logger.warning(f"Session storage not available: {e}")
            # Fallback to simple in-memory storage
            self._get_session = self._fallback_get_session
            self._store_session = self._fallback_store_session

        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self._mongodb_chat_manager = mongodb_chat_manager
        except ImportError as e:
            logger.warning(f"MongoDB chat manager not available: {e}")
            self._mongodb_chat_manager = None

        self._initialized = True
        return True

    def _fallback_get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fallback session getter"""
        return self._fallback_sessions.get(session_id)

    def _fallback_store_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        expire_seconds: int = 86400
    ) -> bool:
        """Fallback session storage"""
        self._fallback_sessions[session_id] = data
        return True

    async def authenticate(
        self,
        access_token: str,
        user_id: Optional[int] = None,
        chat_session_id: Optional[str] = None,
        device_id: Optional[str] = None,
        user_session_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Authenticate a WebSocket connection.

        Args:
            access_token: JWT access token
            user_id: Optional user ID from client (will be verified against token)
            chat_session_id: Optional existing chat session to join
            device_id: Device identifier for multi-device tracking
            user_session_id: Optional existing user session

        Returns:
            Tuple of (success, auth_data or error_data)
            On success: {"user_id": int, "user_session_id": str, "chat_session_id": str, ...}
            On failure: {"error": str, "error_code": str}
        """
        if not self._ensure_initialized():
            return False, {
                "error": "Authentication service not available",
                "error_code": "AUTH_SERVICE_UNAVAILABLE"
            }

        # Step 1: Validate JWT token
        is_valid, token_data = await self.validate_token(access_token)
        if not is_valid:
            return False, token_data  # Contains error info

        payload = token_data["payload"]
        verified_user_id = payload.get("id")
        user_phone = payload.get("contactNumber", "")
        user_name = payload.get("name", "")

        # Verify user_id if provided by client
        if user_id is not None and user_id != verified_user_id:
            logger.warning(
                f"User ID mismatch: client={user_id}, token={verified_user_id}"
            )
            return False, {
                "error": "User ID does not match token",
                "error_code": "USER_ID_MISMATCH"
            }

        # Use verified user_id
        user_id = verified_user_id

        # Step 2: Get or create user session
        session_id, session_data, was_regenerated = await self.get_or_create_user_session(
            user_id=user_id,
            user_session_id=user_session_id,
            user_data={
                "user_id": user_id,
                "access_token": access_token,
                "phone": user_phone,
                "user_name": user_name
            }
        )

        # Step 3: Get or create chat session
        final_chat_session_id = await self.get_or_create_chat_session(
            user_id=user_id,
            chat_session_id=chat_session_id
        )

        logger.info(
            f"WebSocket authentication successful: user_id={user_id}, "
            f"user_session_id={session_id}, chat_session_id={final_chat_session_id}, "
            f"session_regenerated={was_regenerated}"
        )

        return True, {
            "user_id": user_id,
            "user_session_id": session_id,
            "chat_session_id": final_chat_session_id,
            "access_token": access_token,
            "user_name": user_name or f"User{user_id}",
            "user_phone": user_phone,
            "session_regenerated": was_regenerated,
            "device_id": device_id or f"device_{secrets.token_hex(4)}"
        }

    async def validate_token(
        self,
        access_token: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate JWT token.

        Args:
            access_token: JWT token string

        Returns:
            Tuple of (is_valid, {"payload": ...} or {"error": ..., "error_code": ...})
        """
        if not self._ensure_initialized():
            return False, {
                "error": "Token validation service not available",
                "error_code": "AUTH_SERVICE_UNAVAILABLE"
            }

        if not access_token:
            return False, {
                "error": "Access token is required",
                "error_code": "TOKEN_MISSING"
            }

        try:
            result = self._verify_jwt_token(access_token)

            if not result.get("valid"):
                error_msg = result.get("error", "Invalid token")
                error_code = "TOKEN_EXPIRED" if "expired" in error_msg.lower() else "TOKEN_INVALID"
                logger.warning(f"Token validation failed: {error_msg}")
                return False, {
                    "error": error_msg,
                    "error_code": error_code
                }

            payload = result.get("payload", {})

            # Verify required fields in payload
            if not payload.get("id"):
                return False, {
                    "error": "Token missing user ID",
                    "error_code": "TOKEN_INVALID"
                }

            return True, {"payload": payload}

        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, {
                "error": "Token validation failed",
                "error_code": "TOKEN_VALIDATION_ERROR"
            }

    async def get_or_create_user_session(
        self,
        user_id: int,
        user_session_id: Optional[str] = None,
        user_data: Dict[str, Any] = None
    ) -> Tuple[str, Dict[str, Any], bool]:
        """
        Get existing or create new user session.

        Args:
            user_id: User identifier
            user_session_id: Optional existing session ID
            user_data: User data to store in session

        Returns:
            Tuple of (session_id, session_data, was_regenerated)
        """
        was_regenerated = False
        session_data = None

        # Try to get existing session
        if user_session_id:
            session_data = self._get_session(user_session_id)

            if session_data and session_data.get("active"):
                # Valid session exists, update activity
                session_data["last_activity"] = datetime.now(timezone.utc).isoformat()
                self._store_session(user_session_id, session_data, expire_seconds=1296000)
                return user_session_id, session_data, False

            # Try session regeneration if session_manager available
            if self._session_manager and session_data:
                try:
                    new_session_id, new_session_data, was_regenerated = \
                        self._session_manager.validate_and_regenerate_session(
                            session_id=user_session_id,
                            get_session_func=self._get_session,
                            store_session_func=self._store_session,
                            user_data=user_data
                        )

                    if was_regenerated and new_session_data:
                        return new_session_id, new_session_data, True

                except Exception as e:
                    logger.warning(f"Session regeneration failed: {e}")

        # Create new session
        current_time = datetime.now(timezone.utc).isoformat()
        phone = user_data.get("phone", "") if user_data else ""

        new_session_id = f"user_{int(time.time())}_{user_id}_{secrets.token_hex(4)}"

        session_data = {
            "session_id": new_session_id,
            "user_id": user_id,
            "phone": phone,
            "user_name": user_data.get("user_name", f"User{user_id}") if user_data else f"User{user_id}",
            "access_token": user_data.get("access_token") if user_data else None,
            "created_at": current_time,
            "last_activity": current_time,
            "active": True,
            "session_type": "user_session",
            "created_via": "websocket"
        }

        self._store_session(new_session_id, session_data, expire_seconds=1296000)  # 15 days

        logger.info(f"Created new user session: {new_session_id} for user {user_id}")

        return new_session_id, session_data, False

    async def get_or_create_chat_session(
        self,
        user_id: int,
        chat_session_id: Optional[str] = None
    ) -> str:
        """
        Get existing or create new chat session.

        Args:
            user_id: User identifier
            chat_session_id: Optional existing chat session ID

        Returns:
            chat_session_id (existing or newly created)
        """
        current_time = datetime.now(timezone.utc).isoformat()

        # Check if existing chat session is valid
        if chat_session_id:
            session_data = self._get_session(chat_session_id)
            if session_data and session_data.get("active"):
                # Valid chat session, update activity
                session_data["last_activity"] = current_time
                self._store_session(chat_session_id, session_data, expire_seconds=86400)
                return chat_session_id

        # Create new chat session
        new_chat_session_id = f"chat_{user_id}_{int(time.time())}_{secrets.token_hex(4)}"

        chat_session_data = {
            "session_id": new_chat_session_id,
            "user_id": user_id,
            "session_type": "chat_session",
            "created_at": current_time,
            "last_activity": current_time,
            "title": "WebSocket Chat",
            "active": True,
            "message_count": 0,
            "created_via": "websocket"
        }

        self._store_session(new_chat_session_id, chat_session_data, expire_seconds=86400)  # 24 hours

        # Create chat session in MongoDB if available
        if self._mongodb_chat_manager:
            try:
                self._mongodb_chat_manager.create_new_chat_session(
                    user_id=user_id,
                    session_id=new_chat_session_id,
                    title="WebSocket Chat"
                )
            except Exception as e:
                logger.warning(f"Failed to create MongoDB chat session: {e}")

        logger.info(f"Created new chat session: {new_chat_session_id} for user {user_id}")

        return new_chat_session_id

    async def refresh_token_if_needed(
        self,
        access_token: str,
        user_id: int,
        user_session_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if token needs refresh and refresh if possible.

        Args:
            access_token: Current access token
            user_id: User identifier
            user_session_id: User session identifier

        Returns:
            Tuple of (was_refreshed, new_token or None)
        """
        # Validate current token
        is_valid, result = await self.validate_token(access_token)

        if is_valid:
            return False, None  # Token still valid, no refresh needed

        # Check if error is due to expiration
        if result.get("error_code") != "TOKEN_EXPIRED":
            return False, None  # Not an expiration issue

        # Try to refresh using session data
        session_data = self._get_session(user_session_id)
        if not session_data or not session_data.get("active"):
            return False, None

        # Create new token
        try:
            from session_security.token_genrations import create_jwt_token

            new_token = create_jwt_token(
                user_id=user_id,
                phone=session_data.get("phone", ""),
                name=session_data.get("user_name", f"User{user_id}")
            )

            # Update session with new token
            session_data["access_token"] = new_token
            session_data["token_refreshed_at"] = datetime.now(timezone.utc).isoformat()
            self._store_session(user_session_id, session_data, expire_seconds=1296000)

            logger.info(f"Token refreshed for user {user_id}")
            return True, new_token

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return False, None


# Global auth handler instance
auth_handler = WebSocketAuthHandler()
