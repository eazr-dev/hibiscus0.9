"""
Chat Service
Business logic for chat session management and conversation operations
Note: The massive /ask endpoint remains in the router due to its size and complexity
"""
import logging
import time
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat session operations"""

    def __init__(self):
        """Initialize chat service"""
        from core.dependencies import MONGODB_AVAILABLE
        if MONGODB_AVAILABLE:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self.mongodb_manager = mongodb_chat_manager
        else:
            self.mongodb_manager = None
            logger.warning("MongoDB not available for ChatService")

    async def create_chat_session(
        self,
        user_id: int,
        user_session_id: str,
        title: str = "New Chat"
    ) -> Dict[str, Any]:
        """
        Create a new chat session

        Args:
            user_id: User ID
            user_session_id: User's session ID
            title: Chat session title

        Returns:
            Dictionary with new chat session details

        Raises:
            ValueError: If MongoDB unavailable or creation fails
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        current_timestamp = datetime.now()

        # Create NEW chat session
        chat_session_id = f"chat_{user_id}_{int(time.time())}_{secrets.token_hex(4)}"

        # Store in MongoDB
        result = self.mongodb_manager.create_new_chat_session(
            user_id=user_id,
            session_id=chat_session_id,
            title=title
        )

        if not result.get("success"):
            raise ValueError("Failed to create chat session in MongoDB")

        # Update user profile
        self.mongodb_manager.users_collection.update_one(
            {"user_id": user_id},
            {
                "$addToSet": {"chat_session_history": chat_session_id},
                "$set": {
                    "last_chat_session_id": chat_session_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        logger.info(f"Created new chat {chat_session_id} for user {user_id}")

        return {
            "chat_session_id": chat_session_id,
            "user_session_id": user_session_id,
            "user_id": user_id,
            "title": title,
            "created_at": current_timestamp.isoformat()
        }

    async def load_chat_session(
        self,
        session_id: str,
        user_id: int,
        message_limit: int = 100
    ) -> Dict[str, Any]:
        """
        Load a specific chat session with all messages

        Args:
            session_id: Chat session ID to load
            user_id: User ID for ownership verification
            message_limit: Maximum messages to load

        Returns:
            Dictionary with session info and messages

        Raises:
            ValueError: If session not found or access denied
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import load_specific_chat

        # Load chat data
        chat_data = load_specific_chat(session_id, message_limit)

        if not chat_data.get("success"):
            raise ValueError("Chat session not found")

        # Get session info
        session_info = chat_data.get("session", {})
        session_user_id = session_info.get("user_id")

        # Convert both to same type for comparison
        try:
            session_user_id_int = int(session_user_id) if session_user_id else None
            request_user_id_int = int(user_id) if user_id else None
        except (ValueError, TypeError):
            raise ValueError("Invalid user ID format")

        # Verify ownership
        if session_user_id_int != request_user_id_int:
            # Try to verify via messages as fallback
            messages = chat_data.get("messages", [])
            if messages:
                message_user_ids = set()
                for msg in messages:
                    try:
                        msg_user_id = int(msg.get("user_id", 0))
                        message_user_ids.add(msg_user_id)
                    except (ValueError, TypeError):
                        continue

                if request_user_id_int not in message_user_ids:
                    raise ValueError("Access denied to this chat")
                else:
                    # User has messages in this chat, update session owner
                    logger.info(f"Fixing session ownership for {session_id}: updating to user {request_user_id_int}")
                    self.mongodb_manager.sessions_collection.update_one(
                        {"session_id": session_id},
                        {"$set": {"user_id": request_user_id_int}}
                    )
                    session_info["user_id"] = request_user_id_int
            else:
                raise ValueError("Access denied to this chat")

        return {
            "session_id": session_id,
            "session_info": session_info,
            "messages": chat_data.get("messages", []),
            "total_messages": chat_data.get("total_messages", 0)
        }

    async def update_chat_title(
        self,
        session_id: str,
        user_id: int,
        new_title: str
    ) -> bool:
        """
        Update chat session title

        Args:
            session_id: Chat session ID
            user_id: User ID for ownership verification
            new_title: New title for the chat

        Returns:
            True if successful

        Raises:
            ValueError: If access denied or update fails
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import update_chat_session_title

        # Verify ownership
        session = self.mongodb_manager.sessions_collection.find_one({"session_id": session_id})
        if not session or session.get("user_id") != user_id:
            raise ValueError("Access denied")

        success = update_chat_session_title(session_id, new_title)

        if not success:
            raise ValueError("Failed to update chat title")

        return True

    async def delete_chat_session(
        self,
        session_id: str,
        user_id: int,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a chat session

        Args:
            session_id: Chat session ID
            user_id: User ID for ownership verification
            hard_delete: If True, permanently delete; if False, soft delete

        Returns:
            True if successful

        Raises:
            ValueError: If access denied or deletion fails
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import delete_chat_session_by_id

        # Verify ownership
        session = self.mongodb_manager.sessions_collection.find_one({"session_id": session_id})
        if not session or session.get("user_id") != user_id:
            raise ValueError("Access denied")

        success = delete_chat_session_by_id(session_id, hard_delete)

        if not success:
            raise ValueError("Failed to delete chat")

        return True

    async def search_user_chats(
        self,
        user_id: int,
        search_query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search through user's chat history

        Args:
            user_id: User ID
            search_query: Search query string
            limit: Maximum results to return

        Returns:
            List of matching chat sessions

        Raises:
            ValueError: If MongoDB unavailable
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import search_user_chats

        results = search_user_chats(
            user_id=user_id,
            search_query=search_query,
            limit=limit
        )

        return results

    async def archive_chat(
        self,
        session_id: str,
        user_id: int
    ) -> bool:
        """
        Archive a chat session

        Args:
            session_id: Chat session ID
            user_id: User ID for ownership verification

        Returns:
            True if successful

        Raises:
            ValueError: If access denied or archiving fails
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        # Verify ownership
        session = self.mongodb_manager.sessions_collection.find_one({"session_id": session_id})
        if not session or session.get("user_id") != user_id:
            raise ValueError("Access denied")

        success = self.mongodb_manager.archive_chat_session(session_id)

        if not success:
            raise ValueError("Failed to archive chat")

        return True

    async def get_user_chat_sessions(
        self,
        user_id: int,
        limit: int = 50,
        include_archived: bool = False
    ) -> Dict[str, Any]:
        """
        Get all chat sessions for a user

        Args:
            user_id: User ID
            limit: Maximum sessions to return
            include_archived: Whether to include archived chats

        Returns:
            Dictionary with chat sessions organized by date

        Raises:
            ValueError: If MongoDB unavailable
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        from database_storage.mongodb_chat_manager import get_all_user_chats

        # Convert user_id to int
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise ValueError("Invalid user ID")

        # Get chats
        chats = get_all_user_chats(user_id_int, limit, include_archived)

        # If no chats found, try with string user_id as fallback
        if not chats:
            logger.info(f"No chats found for user_id {user_id_int}, trying string format")
            query = {
                "$or": [
                    {"user_id": user_id_int},
                    {"user_id": str(user_id_int)}
                ],
                "deleted": False
            }
            if not include_archived:
                query["is_archived"] = False

            sessions = list(self.mongodb_manager.sessions_collection.find(query).sort("last_activity", -1).limit(limit))

            # Fix user_id format in found sessions
            for session in sessions:
                if session.get("user_id") != user_id_int:
                    self.mongodb_manager.sessions_collection.update_one(
                        {"_id": session["_id"]},
                        {"$set": {"user_id": user_id_int}}
                    )
                    logger.info(f"Fixed user_id format for session {session.get('session_id')}")

            # Retry getting chats
            chats = get_all_user_chats(user_id_int, limit, include_archived)

        # Filter out empty "New Chat" sessions
        chats = [chat for chat in chats if not (chat.get("title") == "New Chat" and chat.get("message_count", 0) == 0)]

        # Organize by date
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)

        organized_chats = {
            "today": [],
            "yesterday": [],
            "last_7_days": [],
            "last_30_days": [],
            "older": []
        }

        for chat in chats:
            try:
                last_activity_date = datetime.fromisoformat(chat["last_activity"]).date()

                if last_activity_date == today:
                    organized_chats["today"].append(chat)
                elif last_activity_date == yesterday:
                    organized_chats["yesterday"].append(chat)
                elif last_activity_date > last_7_days:
                    organized_chats["last_7_days"].append(chat)
                elif last_activity_date > last_30_days:
                    organized_chats["last_30_days"].append(chat)
                else:
                    organized_chats["older"].append(chat)
            except:
                organized_chats["older"].append(chat)

        return {
            "chats": chats,
            "organized_chats": organized_chats,
            "total_chats": len(chats)
        }

    async def clear_user_history(
        self,
        user_id: int,
        session_id: str,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Backup and clear ALL conversation history for a user

        Args:
            user_id: User ID
            session_id: Current session ID
            confirm: Must be True to proceed

        Returns:
            Dictionary with backup details and stats

        Raises:
            ValueError: If not confirmed or backup fails
        """
        if not self.mongodb_manager:
            raise ValueError("MongoDB service unavailable")

        if not confirm:
            raise ValueError("Please confirm chat history backup and deletion")

        from database_storage.mongodb_chat_manager import backup_and_clear_user_chat_history

        # Backup and clear user chat history
        result = backup_and_clear_user_chat_history(
            user_id,
            backup_reason="user_requested_clear"
        )

        if result["success"]:
            # Log the activity
            self.mongodb_manager.log_user_activity(
                user_id=user_id,
                session_id=session_id,
                activity_type="chat_history_backed_up_and_cleared",
                metadata={
                    "backup_id": result.get("backup_id"),
                    "backup_stats": result.get("backup_stats"),
                    "cleared_stats": result.get("cleared_stats")
                }
            )

        return result


# Create singleton instance
chat_service = ChatService()
