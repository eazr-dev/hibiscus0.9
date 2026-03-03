"""
MongoDB Chat Saver Utility
Automatically saves user questions and bot responses to MongoDB
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def save_interaction_to_mongodb(
    chat_session_id: str,
    user_id: int,
    user_query: Optional[str],
    bot_response: str,
    action: Optional[str] = None,
    intent: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    language: str = 'en'
) -> bool:
    """
    Save both user query and bot response to MongoDB in sequence

    Args:
        chat_session_id: Chat session identifier
        user_id: User ID
        user_query: User's question/message (if any)
        bot_response: Bot's response
        action: Action being performed (e.g., 'select_insurance_type')
        intent: Detected intent
        context: Additional context data
        language: Language of the conversation

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        from database_storage.mongodb_chat_manager import (
            mongodb_chat_manager,
            add_user_message_to_mongodb,
            add_assistant_message_to_mongodb
        )

        if not mongodb_chat_manager:
            logger.warning("MongoDB chat manager not available")
            return False

        # Save user message if provided
        if user_query:
            user_message_id = add_user_message_to_mongodb(
                session_id=chat_session_id,
                user_id=user_id,
                content=user_query,
                intent=intent or action,
                context=context or {},
                language=language
            )
            logger.info(f"✓ Saved user message to MongoDB: {chat_session_id}, message_id: {user_message_id}")

        # Save assistant response
        assistant_message_id = add_assistant_message_to_mongodb(
            session_id=chat_session_id,
            user_id=user_id,
            content=bot_response,
            intent=intent or action,
            context=context or {},
            language=language
        )
        logger.info(f"✓ Saved assistant response to MongoDB: {chat_session_id}, message_id: {assistant_message_id}")

        return True

    except Exception as e:
        logger.error(f"✗ Error saving interaction to MongoDB: {str(e)}")
        return False


def save_action_interaction(
    chat_session_id: str,
    user_id: int,
    action: str,
    user_input: Optional[str],
    response_data: Dict[str, Any],
    language: str = 'en'
) -> bool:
    """
    Save action-based interaction to MongoDB

    Specifically designed for insurance/loan application flows where
    user performs actions (select_insurance_type, start_application, etc.)

    Args:
        chat_session_id: Chat session ID
        user_id: User ID
        action: Action name (e.g., 'select_insurance_type')
        user_input: User's input/selection
        response_data: Bot's response data dictionary
        language: Language

    Returns:
        bool: True if saved successfully
    """
    try:
        # Extract bot response from response_data
        bot_response = (
            response_data.get('response') or
            response_data.get('message') or
            response_data.get('title') or
            f"Action: {action}"
        )

        # Build context with action details
        context = {
            'action': action,
            'response_type': response_data.get('type'),
            'has_options': bool(response_data.get('options')),
            'insurance_type': response_data.get('insurance_type'),
            'assistance_type': response_data.get('assistance_type'),
            'policy_id': response_data.get('policy_id'),
            'application_id': response_data.get('application_id')
        }

        return save_interaction_to_mongodb(
            chat_session_id=chat_session_id,
            user_id=user_id,
            user_query=user_input,
            bot_response=bot_response,
            action=action,
            intent=action,
            context=context,
            language=language
        )

    except Exception as e:
        logger.error(f"✗ Error in save_action_interaction: {str(e)}")
        return False


def extract_response_text(response_data: Dict[str, Any]) -> str:
    """
    Extract readable response text from response data dictionary

    Args:
        response_data: Response data dictionary

    Returns:
        str: Extracted response text
    """
    # Try different response fields in priority order
    response_text = (
        response_data.get('response') or
        response_data.get('message') or
        response_data.get('title') or
        response_data.get('subtitle')
    )

    if not response_text:
        # If no text found, create summary from available data
        if response_data.get('options'):
            response_text = f"Please select an option from {len(response_data['options'])} choices"
        elif response_data.get('action'):
            response_text = f"Action: {response_data['action']}"
        else:
            response_text = "Response provided"

    return str(response_text)
