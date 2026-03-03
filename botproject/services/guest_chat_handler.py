"""
Guest User Chat Handler
Handles all guest user interactions with strict limitations
"""
import logging
from typing import Dict, Any

from models.chat_request import AskRequest, ChatContext
from services.chat_handler_service import RESTRICTED_GUEST_ACTIONS

logger = logging.getLogger(__name__)


class GuestChatHandler:
    """Handler for guest user chat requests"""

    @staticmethod
    def handle_guest_request(
        request: AskRequest,
        context: ChatContext,
        has_files: bool
    ) -> Dict[str, Any]:
        """
        Handle guest user request with strict blocking

        GUESTS CAN ONLY:
        - Send text messages (casual conversation)
        - Ask general questions
        - Get information about services (RAG queries)

        BLOCKED:
        - File uploads
        - Restricted actions (loans, insurance, wallet, account)
        - Financial assistance queries
        """
        # Lazy imports to avoid circular dependency
        from routers.chat import create_standardized_response

        logger.warning(f"GUEST USER ACCESS - Session: {context.chat_session_id}")

        # ===== BLOCK 1: FILE UPLOADS (STRICTLY FORBIDDEN) =====
        if has_files:
            logger.warning("BLOCKED: Guest attempted file upload")
            return create_standardized_response(
                response_type="error",
                data={
                    "error": "Authentication required",
                    "message": "Please login to upload and analyze insurance documents. Create a free account to unlock all features!",
                    "action": "auth_required",
                    "show_service_options": False,
                    "quick_actions": [
                        {"title": "Sign Up", "action": "signup"},
                        {"title": "Login", "action": "login"},
                        {"title": "Learn More", "action": "learn_more"}
                    ]
                },
                session_id=context.chat_session_id,
                metadata={"is_guest": True, "intent": "guest_file_upload"}
            )

        # ===== BLOCK 2: RESTRICTED ACTIONS =====
        if request.action and request.action in RESTRICTED_GUEST_ACTIONS:
            logger.warning(f"BLOCKED: Guest attempted restricted action: {request.action}")
            return create_standardized_response(
                response_type="info",
                data={
                    "response": "To access this feature, please create a free account. It only takes a minute!",
                    "message": "Authentication Required",
                    "action": "auth_required",
                    "show_service_options": False,
                    "quick_actions": [
                        {"title": "Sign Up Now", "action": "signup"},
                        {"title": "Login", "action": "login"},
                        {"title": "Learn More", "action": "learn_more"},
                        {"title": "Continue as Guest", "action": "continue_guest"}
                    ]
                },
                session_id=context.chat_session_id,
                metadata={"is_guest": True, "intent": "guest_limitation", "blocked_action": request.action}
            )

        # ===== ALLOWED: TEXT QUERIES ONLY =====
        if request.query:
            return GuestChatHandler._handle_guest_text_query(
                request.query,
                context
            )

        # Default guest greeting
        return create_standardized_response(
            response_type="guest_message",
            data={
                "response": "Welcome! To access full features including chat history, loans, insurance, and personalized assistance, please create a free account.",
                "action": "guest_greeting",
                "show_service_options": False,
                "language": "en",
                "is_guest": True,
                "quick_actions": [
                    {"title": "Sign Up Now", "action": "signup"},
                    {"title": "Login", "action": "login"},
                    {"title": "Learn More", "action": "learn_more"}
                ],
                "suggestions": [
                    "What services do you offer?",
                    "How do I create an account?",
                    "Tell me about loan requirements",
                    "What insurance types are available?"
                ]
            },
            session_id=context.chat_session_id,
            metadata={"is_guest": True, "intent": "guest_greeting"}
        )

    @staticmethod
    def _handle_guest_text_query(query: str, context: ChatContext) -> Dict[str, Any]:
        """Handle text query from guest user"""
        # Lazy imports to avoid circular dependency
        from routers.chat import (
            create_standardized_response,
            add_to_conversation_memory,
            get_conversation_history,
            detect_intent_with_context,
            rag_handler,
            generate_casual_response_with_context
        )

        # Add to conversation memory
        add_to_conversation_memory(context.chat_session_id, "user", query)

        # Get conversation history
        conversation_history = get_conversation_history(context.chat_session_id, limit=10)
        combined_history = [
            {
                'role': msg.get('role', 'user'),
                'content': msg.get('content', ''),
                'timestamp': msg.get('timestamp', context.timestamp)
            }
            for msg in conversation_history
        ]

        # Detect intent
        intent = detect_intent_with_context(query, combined_history)
        logger.info(f"Guest Intent: {intent}")

        result = None

        # Block financial/insurance/wallet intents - require authentication
        if intent in ["financial_assistance", "insurance_plan", "wallet_setup", "task"]:
            result = {
                "response": "I'd be happy to help you with that! To access loans, insurance, account services, or wallet features, you'll need to create a free account first. It only takes a minute to sign up!",
                "action": "auth_required",
                "show_service_options": False,
                "language": "en",
                "quick_actions": [
                    {"title": "Sign Up Now", "action": "signup"},
                    {"title": "Login", "action": "login"},
                    {"title": "Learn More", "action": "learn_more"}
                ],
                "suggestions": [
                    "What types of loans do you offer?",
                    "Tell me about insurance options",
                    "How does the application process work?",
                    "What documents do I need?"
                ]
            }

        # Allow RAG queries (information about services)
        elif intent == "rag_query":
            response = rag_handler(query)
            result = {
                "response": response.get("response", ""),
                "action": "information_retrieved",
                "source_documents": response.get("source_documents", []),
                "show_service_options": False,
                "language": "en",
                "is_guest": True,
                "suggestions": [
                    "What services are available?",
                    "How do I create an account?",
                    "Tell me about loan requirements",
                    "What insurance types do you offer?"
                ]
            }

        # Allow casual conversation
        else:
            casual_response = generate_casual_response_with_context(query, combined_history)
            result = {
                "response": casual_response,
                "action": "casual_conversation",
                "show_service_options": False,
                "language": "en",
                "is_guest": True,
                "suggestions": [
                    "What can you help me with?",
                    "How do I apply for a loan?",
                    "Tell me about insurance options",
                    "How do I create an account?"
                ]
            }

        # Add assistant response to memory
        if result:
            add_to_conversation_memory(context.chat_session_id, "assistant", result.get("response", ""))
            result["is_guest"] = True
            result["guest_session_id"] = context.chat_session_id

        return create_standardized_response(
            response_type="chat_message",
            data=result,
            session_id=context.chat_session_id,
            metadata={"is_guest": True, "intent": intent, "original_query": query}
        )


# Create singleton instance
guest_chat_handler = GuestChatHandler()
