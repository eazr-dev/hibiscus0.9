"""
Authenticated User Chat Handler
Handles all authenticated user interactions with full feature access
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import UploadFile

from models.chat_request import AskRequest, ChatContext, ChatMetadata
from services.chat_handler_service import chat_handler_service

logger = logging.getLogger(__name__)

# Claim-related keywords
CLAIM_KEYWORDS = [
    'claim', 'settlement', 'reimbursement', 'cashless', 'claim process',
    'claim status', 'claim form', 'hospital bills', 'claim rejection',
    'claim approval', 'claim amount', 'insurance claim', 'how to claim'
]


class AuthenticatedChatHandler:
    """Handler for authenticated user chat requests"""

    @staticmethod
    async def handle_authenticated_request(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata,
        files: Optional[List[UploadFile]] = None
    ) -> Dict[str, Any]:
        """
        Route authenticated user request to appropriate handler

        Priority:
        1. File uploads (if files provided)
        2. Actions (if action specified)
        3. Claim queries (if claim keywords detected)
        4. Text queries (general chat)
        """
        # Lazy import to avoid circular dependency
        from routers.chat import create_standardized_response

        logger.info(f"Processing AUTHENTICATED user - user_id: {context.user_id}")

        # Priority 1: File Uploads
        if files:
            return await AuthenticatedChatHandler._handle_file_upload(
                files, request, context, metadata
            )

        # Priority 2: Actions
        if request.action:
            return await AuthenticatedChatHandler._handle_action(
                request, context, metadata
            )

        # Priority 3: Text Queries
        if request.query:
            # Check for claim-related query
            if any(keyword in request.query.lower() for keyword in CLAIM_KEYWORDS):
                return await AuthenticatedChatHandler._handle_claim_query(
                    request, context, metadata
                )

            # Check for protection score request without file
            if request.query.lower().strip() in ['quote_ka_court', 'protection score']:
                return AuthenticatedChatHandler._request_file_upload(
                    request.query, context.chat_session_id, metadata
                )

            # General text query
            return await AuthenticatedChatHandler._handle_text_query(
                request, context, metadata
            )

        # Default response
        return create_standardized_response(
            response_type="info",
            data={
                "message": "How can I help you today?",
                "show_service_options": True,
                "language": "en"
            },
            session_id=context.chat_session_id,
            metadata=metadata.dict()
        )

    @staticmethod
    async def _handle_file_upload(
        files: List[UploadFile],
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle file upload and analysis"""
        # Lazy import to avoid circular dependency
        from routers.chat import create_standardized_response

        logger.info(f"File upload by authenticated user - user_id: {context.user_id}, files: {len(files)}")

        # Validate file types
        error_msg = chat_handler_service.validate_file_types(files)
        if error_msg:
            return create_standardized_response(
                response_type="error",
                data={
                    "error": "Invalid file type",
                    "message": error_msg,
                    "action": "file_error",
                    "show_service_options": False
                },
                session_id=context.chat_session_id,
                metadata={**metadata.dict(), "intent": "file_upload_error"}
            )

        metadata.file_processed = True

        # Import handlers (lazy import to avoid circular dependencies)
        from routers.chat import (
            handle_insurance_analysis_dynamic,
            handle_insurance_pdf_analysis
        )

        # Route to appropriate file handler
        if request.file_action == "analyze_insurance_dynamic":
            return await handle_insurance_analysis_dynamic(
                files,
                context.user_id,
                context.chat_session_id,
                metadata.dict(),
                context.was_regenerated,
                context.original_user_session_id
            )

        elif request.file_action == "analyze_pdf" or (
            request.query and request.query.lower() in ['protection score', 'quote_ka_court']
        ):
            return await handle_insurance_pdf_analysis(
                files,
                context.user_id,
                context.chat_session_id,
                metadata.dict(),
                context.was_regenerated,
                context.original_user_session_id,
                request.vehicle_market_value or 500000,
                request.annual_income or 600000
            )

        else:
            # Default to PDF analysis
            return await handle_insurance_pdf_analysis(
                files,
                context.user_id,
                context.chat_session_id,
                metadata.dict(),
                context.was_regenerated,
                context.original_user_session_id,
                request.vehicle_market_value or 500000,
                request.annual_income or 600000
            )

    @staticmethod
    async def _handle_action(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle action-based requests"""
        from services.action_handler import action_handler

        logger.info(f"ACTION: {request.action} | USER_ID: {context.user_id}")

        return await action_handler.handle_action(
            request, context, metadata
        )

    @staticmethod
    async def _handle_claim_query(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle insurance claim-related queries"""
        from routers.chat import handle_claim_guidance

        logger.info(f"Claim query detected: {request.query}")

        return await handle_claim_guidance(
            request.query,
            request.insurance_type,
            context.chat_session_id,
            context.user_id,
            metadata.dict(),
            context.was_regenerated,
            context.original_user_session_id
        )

    @staticmethod
    async def _handle_text_query(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle general text queries from authenticated users"""
        # Lazy imports to avoid circular dependency
        from routers.chat import (
            create_standardized_response,
            add_to_conversation_memory,
            get_conversation_history,
            detect_intent_with_context,
            rag_handler,
            generate_casual_response_with_context,
            handle_insurance_policy_selection
        )
        from ai_chat_components.enhanced_chatbot_handlers import route_enhanced_chatbot

        query = request.query
        logger.info(f"Text query from user {context.user_id}: {query}")

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

        # Check if query is about user's insurance report (RAG)
        from services.report_rag_handler import report_rag_handler

        if report_rag_handler.detect_report_query(query, combined_history, metadata.dict()):
            logger.info("Detected report-related query, using Report RAG")
            result = await report_rag_handler.answer_report_query(
                query,
                context.user_id,
                context.chat_session_id,
                combined_history
            )

            # Add response to conversation memory
            add_to_conversation_memory(context.chat_session_id, "assistant", result.get("response", ""))

            # Return standardized response
            return create_standardized_response(
                response_type="chat_message",
                data=result,
                session_id=context.chat_session_id,
                metadata={**metadata.dict(), "intent": "report_query", "source": "user_report_rag"}
            )

        # Detect intent
        intent = detect_intent_with_context(query, combined_history)
        metadata.intent = intent
        logger.info(f"Detected intent: {intent}")

        result = None

        # Route based on intent - using same approach as old /ask endpoint
        if intent == "financial_assistance":
            # Route through enhanced chatbot
            result = await route_enhanced_chatbot(
                action="select_financial_assistance_type",
                session_id=context.chat_session_id,
                user_input=None,
                access_token=context.access_token,
                user_id=context.user_id,
                assistance_type=None,
                insurance_type=None,
                service_type=None,
                policy_id=None
            )
            result["chat_session_id"] = context.chat_session_id
            result["user_session_id"] = context.user_session_id

        elif intent == "insurance_analysis":
            # User wants to add/upload/analyze their existing policy
            # Prompt them to upload their policy PDF
            return create_standardized_response(
                response_type="file_upload_request",
                data={
                    "message": "Please upload your insurance policy PDF for analysis",
                    "response": "I'd love to help you add your policy! Please upload your insurance policy document in PDF format, and I'll analyze it for you.",
                    "action": "request_insurance_file_upload",
                    "file_action_needed": "analyze_insurance_dynamic",
                    "show_service_options": False,
                    "language": "en"
                },
                session_id=context.chat_session_id,
                metadata={**metadata.dict(), "intent": "insurance_analysis", "original_query": query}
            )

        elif intent == "insurance_plan":
            # Route to insurance policy selection
            result = await handle_insurance_policy_selection(
                query,
                context.chat_session_id,
                context.user_id,
                metadata.dict(),
                context.access_token
            )
            return result  # This already returns a standardized response

        elif intent == "task":
            # Route through enhanced chatbot for account services
            result = await route_enhanced_chatbot(
                action="select_service_type",
                session_id=context.chat_session_id,
                user_input=None,
                access_token=context.access_token,
                user_id=context.user_id,
                assistance_type=None,
                insurance_type=None,
                service_type=None,
                policy_id=None
            )
            result["chat_session_id"] = context.chat_session_id
            result["user_session_id"] = context.user_session_id

        elif intent == "rag_query":
            response = rag_handler(query)
            result = {
                "response": response.get("response", ""),
                "action": "information_retrieved",
                "source_documents": response.get("source_documents", []),
                "show_service_options": False,
                "language": "en"
            }

        else:
            # Casual conversation
            casual_response = generate_casual_response_with_context(query, combined_history)
            result = {
                "response": casual_response,
                "action": "casual_conversation",
                "show_service_options": False,
                "language": "en"
            }

        # Add assistant response to memory
        if result and result.get("response"):
            add_to_conversation_memory(
                context.chat_session_id,
                "assistant",
                result.get("response", "")
            )

        return create_standardized_response(
            response_type="chat_message",
            data=result,
            session_id=context.chat_session_id,
            metadata={**metadata.dict(), "intent": intent, "original_query": query}
        )

    @staticmethod
    def _request_file_upload(
        query: str,
        chat_session_id: str,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Request file upload for protection score/analysis"""
        # Lazy import to avoid circular dependency
        from routers.chat import create_standardized_response

        file_action_needed = (
            "analyze_insurance_dynamic" if query.lower() == 'quote_ka_court'
            else "analyze_pdf"
        )

        response_msg = (
            "Let's unlock your insurance insights! Upload your policy document in PDF format, and I'll analyze it."
            if query.lower() == 'quote_ka_court'
            else "Don't wait! Upload your insurance file and score to complete your audit quickly and easily."
        )

        return create_standardized_response(
            response_type="file_upload_request",
            data={
                "message": "Please upload your insurance policy PDF for analysis",
                "response": response_msg,
                "action": "request_insurance_file_upload",
                "file_action_needed": file_action_needed,
                "show_service_options": False,
                "language": "en"
            },
            session_id=chat_session_id,
            metadata={**metadata.dict(), "intent": "protection_score_request"}
        )


# Create singleton instance
authenticated_chat_handler = AuthenticatedChatHandler()
