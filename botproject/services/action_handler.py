"""
Action Handler
Handles all action-based requests (applications, policies, wallet, etc.)
"""
import logging
import json
from typing import Dict, Any

from models.chat_request import AskRequest, ChatContext, ChatMetadata

logger = logging.getLogger(__name__)


class ActionHandler:
    """Handler for action-based chat requests"""

    @staticmethod
    async def handle_action(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """
        Route action to appropriate handler

        Actions handled:
        - Application review & submission
        - Policy selection & application
        - Financial assistance
        - Wallet setup
        - Account services
        """
        # Lazy import to avoid circular dependency
        from routers.chat import create_standardized_response

        action = request.action
        logger.info(f"Handling action: {action}")

        # Application Review & Submission
        if action == "review_application":
            return await ActionHandler._handle_review_application(
                request, context, metadata
            )

        elif action == "confirm_submit_application":
            return await ActionHandler._handle_confirm_submit_application(
                request, context, metadata
            )

        elif action == "cancel_application":
            return await ActionHandler._handle_cancel_application(
                request, context, metadata
            )

        # Policy & Insurance Actions
        elif action in ["select_insurance_type", "show_insurance_eligibility"]:
            from routers.chat import handle_insurance_policy_selection
            return await handle_insurance_policy_selection(
                request.user_input or "",
                context.chat_session_id,
                context.user_id,
                metadata.dict(),
                context.access_token
            )

        elif action == "accept_policy_and_start_application":
            return await ActionHandler._handle_start_policy_application(
                request, context, metadata
            )

        elif action == "show_policy_details":
            return await ActionHandler._handle_show_policy_details(
                request, context, metadata
            )

        elif action == "check_policy_status":
            return await ActionHandler._handle_check_policy_status(
                request, context, metadata
            )

        elif action == "download_policy":
            return await ActionHandler._handle_download_policy(
                request, context, metadata
            )

        # Financial Assistance Actions - Route through enhanced chatbot
        elif action in ["select_financial_assistance_type", "start_loan_application"]:
            from routers.chat import create_standardized_response
            from ai_chat_components.enhanced_chatbot_handlers import route_enhanced_chatbot
            result = await route_enhanced_chatbot(
                action=action,
                session_id=context.chat_session_id,
                user_input=request.user_input,
                access_token=context.access_token,
                user_id=context.user_id,
                assistance_type=request.assistance_type,
                insurance_type=None,
                service_type=None,
                policy_id=None
            )
            result["chat_session_id"] = context.chat_session_id
            result["user_session_id"] = context.user_session_id

            return create_standardized_response(
                response_type="general_response",
                data=result,
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        # Wallet Actions - Route through enhanced chatbot
        elif action in ["start_wallet_setup", "wallet_setup"]:
            from routers.chat import create_standardized_response
            from ai_chat_components.enhanced_chatbot_handlers import route_enhanced_chatbot
            result = await route_enhanced_chatbot(
                action=action,
                session_id=context.chat_session_id,
                user_input=request.user_input,
                access_token=context.access_token,
                user_id=context.user_id,
                assistance_type=None,
                insurance_type=None,
                service_type=None,
                policy_id=None
            )
            result["chat_session_id"] = context.chat_session_id
            result["user_session_id"] = context.user_session_id

            return create_standardized_response(
                response_type="general_response",
                data=result,
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        # Account Services - Route through enhanced chatbot
        elif action in ["check_balance", "view_transactions", "view_bills"]:
            return await ActionHandler._handle_account_service(
                action, context, metadata
            )

        # Default: Unknown action
        else:
            logger.warning(f"Unknown action: {action}")
            return create_standardized_response(
                response_type="error",
                data={
                    "error": "Unknown action",
                    "message": f"Action '{action}' is not supported",
                    "action": "unknown_action"
                },
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

    @staticmethod
    async def _handle_review_application(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle application review request"""
        # Lazy import to avoid circular dependency
        from routers.chat import create_standardized_response

        if not request.policy_id:
            return create_standardized_response(
                response_type="error",
                data={
                    "error": "Missing policy_id",
                    "message": "Policy ID is required to review application"
                },
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        from database_storage.mongodb_chat_manager import get_policy_application

        application_data = get_policy_application(context.user_id, request.policy_id)

        if not application_data:
            return create_standardized_response(
                response_type="error",
                data={
                    "error": "Application not found",
                    "message": "Could not find your application data",
                    "action": "application_not_found"
                },
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        # Build editable fields
        editable_fields = []
        answers_dict = application_data.get("answers", {})

        sorted_questions = sorted(
            [(int(k.replace("q_", "")), v) for k, v in answers_dict.items() if k.startswith("q_")],
            key=lambda x: x[0]
        )

        for q_num, answer_data in sorted_questions:
            editable_fields.append({
                "question_number": q_num,
                "question": answer_data.get("question", f"Question {q_num}"),
                "current_answer": answer_data.get("answer", ""),
                "field_type": answer_data.get("type", "text"),
                "field_key": answer_data.get("key", f"field_{q_num}"),
                "options": answer_data.get("options") if answer_data.get("type") == "dropdown" else None,
                "placeholder": answer_data.get("placeholder", ""),
                "required": True,
                "is_edited": answer_data.get("is_edited", False)
            })

        return create_standardized_response(
            response_type="review_and_edit_application",
            data={
                "type": "review_and_edit_application",
                "message": "Review and edit your answers, then submit:",
                "title": f"Review & Edit Application - Policy {request.policy_id}",
                "service_type": "policy_application",
                "policy_id": request.policy_id,
                "application_id": application_data.get("application_id"),
                "show_service_options": False,
                "editable_fields": editable_fields,
                "total_fields": len(editable_fields),
                "application_data": {
                    "application_id": application_data.get("application_id"),
                    "policy_id": request.policy_id,
                    "user_id": context.user_id,
                    "total_questions": len(editable_fields),
                    "created_at": application_data.get("created_at"),
                    "last_updated": application_data.get("last_updated"),
                    "status": application_data.get("status", "in_progress")
                },
                "current_answers": {
                    f"q_{field['question_number']}": field["current_answer"]
                    for field in editable_fields
                },
                "next_action": {
                    "title": "Submit Application",
                    "action": "confirm_submit_application",
                    "policy_id": request.policy_id,
                    "application_id": application_data.get("application_id"),
                    "requires_edited_answers": True
                },
                "back_action": {
                    "title": "Cancel Application",
                    "action": "cancel_application",
                    "policy_id": request.policy_id
                },
                "edit_mode": True,
                "instructions": "Edit any field below, then click 'Submit Application' to finalize.",
                "completion_percentage": 100,
                "ready_for_submission": True,
                "chat_session_id": context.chat_session_id,
                "user_session_id": context.user_session_id
            },
            session_id=context.chat_session_id,
            metadata={**metadata.dict(), "intent": "review_and_edit_application"}
        )

    @staticmethod
    async def _handle_confirm_submit_application(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle application confirmation and submission with payment"""
        # Lazy import to avoid circular dependency
        from routers.chat import create_standardized_response

        if not request.policy_id:
            return create_standardized_response(
                response_type="error",
                data={"error": "Missing policy_id"},
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        from database_storage.mongodb_chat_manager import get_policy_application, complete_application

        application_data = get_policy_application(context.user_id, request.policy_id)

        if not application_data:
            return create_standardized_response(
                response_type="error",
                data={"error": "Application not found"},
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        # Apply edited answers if provided
        if request.edited_answers:
            try:
                edited_data = json.loads(request.edited_answers)
                # Update application with edited answers
                # (implementation depends on your MongoDB structure)
                logger.info(f"Applying edited answers: {len(edited_data)} fields")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse edited_answers: {e}")

        # Complete application - use application_id from application_data
        application_id = application_data.get("application_id")
        if not application_id:
            return create_standardized_response(
                response_type="error",
                data={"error": "Missing application_id"},
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        # Prepare submission data
        submission_data = {
            "user_id": context.user_id,
            "policy_id": request.policy_id,
            "access_token": context.access_token
        }

        # complete_application returns bool (True/False)
        completion_success = complete_application(application_id, submission_data)

        if completion_success:
            return create_standardized_response(
                response_type="application_submitted",
                data={
                    "message": "Application submitted successfully!",
                    "application_id": application_data.get("application_id"),
                    "policy_id": request.policy_id,
                    "status": "completed",
                    "chat_session_id": context.chat_session_id,
                    "user_session_id": context.user_session_id
                },
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )
        else:
            return create_standardized_response(
                response_type="error",
                data={
                    "error": "Submission failed",
                    "message": "Failed to update application status. Please try again.",
                    "chat_session_id": context.chat_session_id,
                    "user_session_id": context.user_session_id
                },
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

    @staticmethod
    async def _handle_cancel_application(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle application cancellation"""
        # Lazy import to avoid circular dependency
        from routers.chat import create_standardized_response

        return create_standardized_response(
            response_type="info",
            data={
                "message": "Application cancelled",
                "action": "application_cancelled"
            },
            session_id=context.chat_session_id,
            metadata=metadata.dict()
        )

    @staticmethod
    async def _handle_start_policy_application(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle starting a policy application"""
        from routers.chat import create_standardized_response
        from ai_chat_components.enhanced_chatbot_handlers import accept_policy_and_start_application

        result = await accept_policy_and_start_application(
            context.chat_session_id,
            request.policy_id,
            context.access_token,
            context.user_id
        )

        result["chat_session_id"] = context.chat_session_id
        result["user_session_id"] = context.user_session_id

        return create_standardized_response(
            response_type="question",
            data=result,
            session_id=context.chat_session_id,
            metadata={**metadata.dict(), "intent": "start_policy_application"}
        )

    @staticmethod
    async def _handle_show_policy_details(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle showing policy details"""
        from routers.chat import create_standardized_response
        from ai_chat_components.enhanced_chatbot_handlers import show_policy_details_from_stored_data

        if not request.policy_id:
            return create_standardized_response(
                response_type="error",
                data={
                    "error": "Missing policy_id",
                    "message": "Policy ID is required to show policy details"
                },
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        result = await show_policy_details_from_stored_data(
            request.policy_id,
            context.chat_session_id,
            context.access_token,
            context.user_id
        )

        result["chat_session_id"] = context.chat_session_id
        result["user_session_id"] = context.user_session_id

        return create_standardized_response(
            response_type="policy_details",
            data=result,
            session_id=context.chat_session_id,
            metadata={**metadata.dict(), "intent": "show_policy_details"}
        )

    @staticmethod
    async def _handle_check_policy_status(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle policy status check"""
        from routers.chat import create_standardized_response
        from database_storage.mongodb_chat_manager import mongodb_chat_manager
        from datetime import datetime
        import httpx

        # Fetch proposalNum from MongoDB
        proposal_num = None
        application_data = None

        if request.policy_id:
            application_data = mongodb_chat_manager.policy_applications_collection.find_one(
                {"user_id": context.user_id, "policy_id": request.policy_id},
                sort=[("created_at", -1)]
            )
        else:
            application_data = mongodb_chat_manager.policy_applications_collection.find_one(
                {"user_id": context.user_id, "status": "completed"},
                sort=[("completed_at", -1)]
            )

        if application_data:
            proposal_num = application_data.get("submission_details", {}).get("proposalNum")

        if not proposal_num:
            return create_standardized_response(
                response_type="error",
                data={
                    "error": "Missing Proposal Number",
                    "message": "Proposal number is required to check policy status"
                },
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        # Check status via API
        try:
            status_url = f"https://api.prod.eazr.in/insurance-chatbot/policies/{context.user_id}/{proposal_num}/status"
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.get(status_url, headers={"Content-Type": "application/json"})

                if response.status_code not in [200, 201]:
                    return create_standardized_response(
                        response_type="error",
                        data={"error": "Status Check Failed", "message": "Unable to retrieve policy status"},
                        session_id=context.chat_session_id,
                        metadata=metadata.dict()
                    )

                status_result = response.json()
                policy_num = status_result.get("data", {}).get("policyNum")
                policy_status = status_result.get("data", {}).get("result", {}).get("status", "PENDING")

                # Update MongoDB
                if application_data and application_data.get("application_id"):
                    update_fields = {
                        "submission_details.policyStatus": policy_status,
                        "last_updated": datetime.now()
                    }
                    if policy_num:
                        update_fields["submission_details.policyNum"] = policy_num

                    mongodb_chat_manager.policy_applications_collection.update_one(
                        {"application_id": application_data.get("application_id")},
                        {"$set": update_fields}
                    )

                quick_actions = [{"title": "Check Balance", "action": "check_balance"}]
                if policy_num:
                    quick_actions.insert(0, {"title": "Download Policy", "action": "download_policy", "proposalNum": proposal_num})

                return create_standardized_response(
                    response_type="policy_status",
                    data={
                        "message": "Policy status checked successfully",
                        "proposalNum": proposal_num,
                        "policyNum": policy_num,
                        "policyStatus": policy_status,
                        "quick_actions": quick_actions,
                        "chat_session_id": context.chat_session_id,
                        "user_session_id": context.user_session_id
                    },
                    session_id=context.chat_session_id,
                    metadata={**metadata.dict(), "intent": "policy_status_checked"}
                )
        except Exception as e:
            logger.error(f"Error checking policy status: {e}")
            return create_standardized_response(
                response_type="error",
                data={"error": "Processing Error", "message": "An error occurred while checking policy status"},
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

    @staticmethod
    async def _handle_download_policy(
        request: AskRequest,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle policy document download"""
        from routers.chat import create_standardized_response
        from database_storage.mongodb_chat_manager import mongodb_chat_manager
        import httpx

        # Get proposal_num
        proposal_num = request.application_id

        if not proposal_num and request.policy_id:
            application_data = mongodb_chat_manager.policy_applications_collection.find_one(
                {"user_id": context.user_id, "policy_id": request.policy_id},
                sort=[("created_at", -1)]
            )
            if application_data:
                proposal_num = application_data.get("submission_details", {}).get("proposalNum")

        if not proposal_num:
            return create_standardized_response(
                response_type="error",
                data={"error": "Missing Proposal Number", "message": "Proposal number is required"},
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

        try:
            download_url = f"https://api.prod.eazr.in/insurance-chatbot/policies/{context.user_id}/{proposal_num}/download"
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                response = await client.get(download_url, headers={"Content-Type": "application/json"})

                if response.status_code not in [200, 201]:
                    return create_standardized_response(
                        response_type="error",
                        data={"error": "Download Failed", "message": "Unable to download policy document"},
                        session_id=context.chat_session_id,
                        metadata=metadata.dict()
                    )

                download_result = response.json()
                return create_standardized_response(
                    response_type="policy_downloaded",
                    data={
                        "message": "Your policy document is ready for download",
                        "policyNum": download_result.get("data", {}).get("policyNum"),
                        "documentUrl": download_result.get("data", {}).get("documentUrl"),
                        "chat_session_id": context.chat_session_id,
                        "user_session_id": context.user_session_id
                    },
                    session_id=context.chat_session_id,
                    metadata={**metadata.dict(), "intent": "policy_downloaded"}
                )
        except Exception as e:
            logger.error(f"Error downloading policy: {e}")
            return create_standardized_response(
                response_type="error",
                data={"error": "Processing Error", "message": "An error occurred"},
                session_id=context.chat_session_id,
                metadata=metadata.dict()
            )

    @staticmethod
    async def _handle_account_service(
        action: str,
        context: ChatContext,
        metadata: ChatMetadata
    ) -> Dict[str, Any]:
        """Handle account service requests"""
        from routers.chat import create_standardized_response
        from ai_chat_components.enhanced_chatbot_handlers import route_enhanced_chatbot

        # Route through enhanced chatbot
        result = await route_enhanced_chatbot(
            action=action,
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

        return create_standardized_response(
            response_type="general_response",
            data=result,
            session_id=context.chat_session_id,
            metadata=metadata.dict()
        )


# Create singleton instance
action_handler = ActionHandler()
