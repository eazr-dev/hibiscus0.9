"""
Chat Handler Service
Modular handlers for /ask endpoint - extracted from monolithic function
"""
import logging
import time
import secrets
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from fastapi import UploadFile, HTTPException

from models.chat_request import AskRequest, ChatContext, ChatMetadata
from core.dependencies import get_session as get_cached_session, store_session
from session_security.session_manager import session_manager
from utils.auth_verification import verify_user_authentication, should_verify_token

logger = logging.getLogger(__name__)

# Constants
USER_SESSION_EXPIRY = 15 * 24 * 60 * 60  # 15 days
CHAT_SESSION_EXPIRY = 24 * 60 * 60  # 24 hours
GUEST_SESSION_EXPIRY = 1 * 60 * 60  # 1 hour

# Restricted actions for guest users
RESTRICTED_GUEST_ACTIONS = [
    # Financial assistance
    "select_financial_assistance_type",
    "show_financial_assistance_eligibility",
    "start_financial_assistance_application",
    "start_loan_application",

    # Insurance
    "select_insurance_type",
    "show_insurance_eligibility",
    "start_insurance_application",
    "show_policy_details",
    "accept_policy_and_start_application",
    "review_application",
    "confirm_submit_application",
    "check_policy_status",
    "download_policy",

    # Wallet
    "start_wallet_setup",
    "wallet_setup",

    # Account services
    "check_balance",
    "view_transactions",
    "view_bills",
    "view_financial_assistance",
    "view_insurance",

    # Applications
    "continue_application",
    "submit_application",
    "cancel_application",
    "view_my_applications"
]


class ChatHandlerService:
    """Service for handling chat requests in modular way"""

    @staticmethod
    def determine_user_authentication(
        request: AskRequest
    ) -> Tuple[bool, Optional[int], Optional[str], Optional[str], bool, Optional[str]]:
        """
        Determine if user is authenticated

        Returns:
            Tuple of (is_guest, user_id, access_token, user_phone, was_regenerated, original_session_id)
        """
        # Handle backward compatibility
        user_session_id = request.user_session_id or request.session_id

        is_guest = True
        user_id = request.user_id
        access_token = request.access_token
        user_phone = request.user_phone
        was_regenerated = False
        original_session_id = None

        # Check if user has valid authentication session
        if user_session_id:
            user_session_data = get_cached_session(user_session_id)

            if user_session_data and user_session_data.get('active'):
                # Valid session found
                if not user_id:
                    user_id = user_session_data.get('user_id')
                if not access_token:
                    access_token = user_session_data.get('access_token')
                if not user_phone:
                    user_phone = user_session_data.get('phone')

                # Check if we have valid credentials
                if user_id and user_id > 0 and access_token:
                    is_guest = False
                    logger.info(f"Authenticated user detected - user_id: {user_id}")

                # Update session activity
                user_session_data['last_activity'] = datetime.now().isoformat()
                store_session(user_session_id, user_session_data, expire_seconds=USER_SESSION_EXPIRY)

            elif user_session_data:
                # Try session regeneration
                original_session_id = user_session_id
                user_session_id, user_session_data, was_regenerated = session_manager.validate_and_regenerate_session(
                    user_session_id,
                    get_cached_session,
                    store_session,
                    user_data={'user_id': user_id, 'access_token': access_token}
                )

                if was_regenerated and user_session_data:
                    user_id = user_session_data.get('user_id')
                    access_token = user_session_data.get('access_token')
                    user_phone = user_session_data.get('phone')

                    if user_id and user_id > 0 and access_token:
                        is_guest = False

        # Additional check: if credentials provided directly
        if user_id and user_id > 0 and access_token and is_guest:
            is_guest = False
            logger.info(f"User authenticated via direct credentials - user_id: {user_id}")

        logger.info(f"=== USER STATUS: {'GUEST' if is_guest else 'AUTHENTICATED'} | user_id: {user_id} ===")

        return is_guest, user_id, access_token, user_phone, was_regenerated, original_session_id

    @staticmethod
    def verify_authenticated_user(
        access_token: Optional[str],
        user_id: Optional[int],
        user_phone: Optional[str]
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Verify authenticated user credentials

        Validates:
        - Access token is valid JWT
        - User ID matches token
        - Phone number matches token

        Returns:
            Tuple of (is_valid, error_message, token_payload)
        """
        return verify_user_authentication(access_token, user_id, user_phone)

    @staticmethod
    def create_guest_context(chat_session_id: Optional[str] = None) -> ChatContext:
        """Create context for guest user"""
        timestamp = datetime.now().isoformat()

        if not chat_session_id:
            chat_session_id = f"guest_{int(time.time())}_{secrets.token_hex(4)}"

        guest_session_data = {
            'session_id': chat_session_id,
            'user_id': 0,
            'is_guest': True,
            'created_at': timestamp,
            'last_activity': timestamp,
            'active': True,
            'guest_mode': True
        }

        store_session(chat_session_id, guest_session_data, expire_seconds=GUEST_SESSION_EXPIRY)

        return ChatContext(
            user_id=0,
            user_session_id=None,
            chat_session_id=chat_session_id,
            is_guest=True,
            access_token=None,
            user_phone=None,
            timestamp=timestamp
        )

    @staticmethod
    def handle_or_create_chat_session(
        user_id: int,
        chat_session_id: Optional[str],
        user_session_id: Optional[str],
        has_content: bool  # query, action, or file
    ) -> Tuple[str, bool]:
        """
        Handle existing or create new chat session

        Returns:
            Tuple of (chat_session_id, was_created)
        """
        timestamp = datetime.now().isoformat()
        chat_session_created = False

        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
        except ImportError:
            mongodb_chat_manager = None

        if chat_session_id:
            chat_session_data = get_cached_session(chat_session_id)

            if not chat_session_data or not chat_session_data.get('active'):
                # Create/restore with SAME ID (preserve incoming ID)
                chat_session_created = True

                chat_session_data = {
                    'user_id': user_id,
                    'session_type': 'chat_session',
                    'created_at': timestamp,
                    'last_activity': timestamp,
                    'title': 'Chat Session',
                    'active': True,
                    'message_count': 0,
                    'user_session_id': user_session_id
                }

                store_session(chat_session_id, chat_session_data, expire_seconds=CHAT_SESSION_EXPIRY)

                if mongodb_chat_manager:
                    mongodb_chat_manager.create_new_chat_session(
                        user_id=user_id,
                        session_id=chat_session_id,
                        title="Chat Session"
                    )

                logger.info(f"Chat session created/restored: {chat_session_id}")
            else:
                # Session exists and is active - update activity
                chat_session_data['last_activity'] = timestamp
                chat_session_data['message_count'] = chat_session_data.get('message_count', 0) + 1
                store_session(chat_session_id, chat_session_data, expire_seconds=CHAT_SESSION_EXPIRY)
                logger.info(f"Chat session continued: {chat_session_id}")

        elif user_id and has_content:
            # Auto-create session
            chat_session_id = f"chat_{user_id}_{int(time.time())}_{secrets.token_hex(4)}"
            chat_session_created = True

            chat_session_data = {
                'user_id': user_id,
                'session_type': 'chat_session',
                'created_at': timestamp,
                'last_activity': timestamp,
                'title': 'Auto Chat',
                'active': True,
                'message_count': 0,
                'user_session_id': user_session_id
            }

            store_session(chat_session_id, chat_session_data, expire_seconds=CHAT_SESSION_EXPIRY)

            if mongodb_chat_manager:
                result = mongodb_chat_manager.create_new_chat_session(
                    user_id=user_id,
                    session_id=chat_session_id,
                    title="Auto Chat"
                )
                if result.get("success"):
                    logger.info(f"Auto-created chat session: {chat_session_id}")

        return chat_session_id, chat_session_created

    @staticmethod
    def create_metadata(
        query: Optional[str],
        chat_session_id: str,
        user_session_id: Optional[str],
        chat_session_created: bool,
        is_guest: bool,
        was_regenerated: bool,
        original_user_session_id: Optional[str]
    ) -> ChatMetadata:
        """Create metadata dict for response"""
        timestamp = datetime.now().isoformat()

        # Import to get active sessions count
        from routers.chat import chatbot_sessions

        return ChatMetadata(
            message_id=hashlib.md5(f"{chat_session_id}_{query}_{timestamp}".encode()).hexdigest()[:16] if query else None,
            original_query=query,
            processed_query=query,
            user_session_id=user_session_id,
            chat_session_id=chat_session_id,
            chat_session_created=chat_session_created,
            chat_session_regenerated=False,
            is_guest=is_guest,
            active_sessions=len([s for s in chatbot_sessions.values() if not s.completed]),
            conversation_length=0,
            session_continuation=False,
            context_used=False,
            topics_discussed=[],
            last_user_question=None,
            language_detected="en",
            language_confidence=1.0,
            intent=None,
            file_processed=False,
            user_session_regenerated=was_regenerated,
            original_user_session_id=original_user_session_id if was_regenerated else None,
            original_chat_session_id=None,
            timestamp=timestamp
        )

    @staticmethod
    def validate_file_types(files: List[UploadFile]) -> Optional[str]:
        """
        Validate uploaded file types

        Returns:
            Error message if invalid, None if valid
        """
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.webp'}

        for f in files:
            import os
            file_ext = os.path.splitext(f.filename.lower())[1]
            if file_ext not in allowed_extensions:
                return f"File '{f.filename}' has unsupported type. Allowed: PDF, PNG, JPG, JPEG, WEBP"

        return None


# Create singleton instance
chat_handler_service = ChatHandlerService()
