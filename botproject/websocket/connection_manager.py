"""
WebSocket Connection Manager for EAZR Chat
Manages multiple WebSocket connections with multi-device support.
"""

from typing import Dict, Set, List, Optional, Any
from collections import deque
from fastapi import WebSocket
from dataclasses import dataclass, field
from datetime import datetime, timezone
import asyncio
import logging
import secrets
import json
import time

logger = logging.getLogger(__name__)

# Maximum number of simultaneous WebSocket connections per user
MAX_CONNECTIONS_PER_USER = 10


@dataclass
class ConnectionInfo:
    """Information about a single WebSocket connection"""
    websocket: WebSocket
    user_id: int
    chat_session_id: str
    user_session_id: str
    device_id: str
    connection_id: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_ping: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_authenticated: bool = False
    access_token: Optional[str] = None
    user_name: Optional[str] = None
    is_typing: bool = False
    message_count: int = 0


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for real-time chat.

    Features:
    - Track multiple connections per user (multi-device support)
    - Broadcast to all user devices
    - Per-chat-session messaging
    - Connection health monitoring via heartbeat
    - Thread-safe operations with asyncio locks
    """

    def __init__(self, redis_client=None):
        """
        Initialize connection manager.

        Args:
            redis_client: Optional Redis client for distributed state
        """
        # In-memory connection storage
        # Key: connection_id -> ConnectionInfo
        self._connections: Dict[str, ConnectionInfo] = {}

        # User to connections mapping (one user can have multiple connections)
        # Key: user_id -> Set[connection_id]
        self._user_connections: Dict[int, Set[str]] = {}

        # Chat session to connections mapping
        # Key: chat_session_id -> Set[connection_id]
        self._chat_connections: Dict[str, Set[str]] = {}

        # Redis for distributed state (optional, for multi-server deployment)
        self._redis = redis_client

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        # ---- Message stats tracking ----
        # Counts by message type (lifetime)
        self._message_type_counts: Dict[str, int] = {
            "chat": 0,
            "typing": 0,
            "presence": 0,
            "notifications": 0,
            "ping": 0,
        }
        # Rolling window of message timestamps for messages-per-minute
        self._message_timestamps: deque = deque(maxlen=10000)
        # Rolling window of response times (seconds) for avg calculation
        self._response_times: deque = deque(maxlen=200)

    def _generate_connection_id(self) -> str:
        """Generate a unique connection ID"""
        return f"conn_{int(datetime.now(timezone.utc).timestamp())}_{secrets.token_hex(8)}"

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        chat_session_id: str,
        user_session_id: str,
        device_id: str,
        access_token: str,
        user_name: Optional[str] = None
    ) -> str:
        """
        Register a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: User identifier
            chat_session_id: Chat session identifier
            user_session_id: User session identifier
            device_id: Device identifier for multi-device tracking
            access_token: JWT access token
            user_name: Optional user display name

        Returns:
            connection_id: Unique identifier for this connection
        """
        async with self._lock:
            # Enforce per-user connection limit
            existing = self._user_connections.get(user_id, set())
            if len(existing) >= MAX_CONNECTIONS_PER_USER:
                logger.warning(
                    f"User {user_id} exceeded max connections ({MAX_CONNECTIONS_PER_USER}), "
                    f"rejecting new connection"
                )
                raise ConnectionError(
                    f"Maximum connections per user ({MAX_CONNECTIONS_PER_USER}) exceeded"
                )

            connection_id = self._generate_connection_id()

            # Create connection info
            conn_info = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
                chat_session_id=chat_session_id,
                user_session_id=user_session_id,
                device_id=device_id,
                connection_id=connection_id,
                access_token=access_token,
                is_authenticated=True,
                user_name=user_name
            )

            # Store connection
            self._connections[connection_id] = conn_info

            # Add to user connections
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(connection_id)

            # Add to chat session connections
            if chat_session_id not in self._chat_connections:
                self._chat_connections[chat_session_id] = set()
            self._chat_connections[chat_session_id].add(connection_id)

            logger.info(
                f"WebSocket connected: connection_id={connection_id}, "
                f"user_id={user_id}, device_id={device_id}, "
                f"chat_session_id={chat_session_id}"
            )

            # Store in Redis if available (for distributed state)
            if self._redis:
                try:
                    await self._store_connection_in_redis(connection_id, conn_info)
                except Exception as e:
                    logger.warning(f"Failed to store connection in Redis: {e}")

            return connection_id

    async def disconnect(self, connection_id: str) -> Optional[ConnectionInfo]:
        """
        Remove a WebSocket connection and cleanup mappings.

        Args:
            connection_id: The connection to remove

        Returns:
            ConnectionInfo of the removed connection, or None if not found
        """
        async with self._lock:
            if connection_id not in self._connections:
                logger.warning(f"Attempted to disconnect unknown connection: {connection_id}")
                return None

            conn_info = self._connections.pop(connection_id)

            # Remove from user connections
            user_id = conn_info.user_id
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(connection_id)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]

            # Remove from chat session connections
            chat_session_id = conn_info.chat_session_id
            if chat_session_id in self._chat_connections:
                self._chat_connections[chat_session_id].discard(connection_id)
                if not self._chat_connections[chat_session_id]:
                    del self._chat_connections[chat_session_id]

            logger.info(
                f"WebSocket disconnected: connection_id={connection_id}, "
                f"user_id={user_id}, device_id={conn_info.device_id}"
            )

            # Remove from Redis if available
            if self._redis:
                try:
                    await self._remove_connection_from_redis(connection_id)
                except Exception as e:
                    logger.warning(f"Failed to remove connection from Redis: {e}")

            return conn_info

    async def send_to_connection(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        Send message to a specific connection.

        Args:
            connection_id: Target connection
            message: Message payload (will be JSON serialized)

        Returns:
            True if sent successfully, False otherwise
        """
        conn_info = self._connections.get(connection_id)
        if not conn_info:
            logger.warning(f"Cannot send to unknown connection: {connection_id}")
            return False

        try:
            # Convert datetime objects to ISO strings for JSON serialization
            serializable_message = self._make_json_serializable(message)
            await conn_info.websocket.send_json(serializable_message)
            return True
        except Exception as e:
            logger.error(f"Failed to send to connection {connection_id}: {e}")
            # Connection might be dead, handle cleanup directly
            # Using direct call instead of create_task to avoid race conditions
            try:
                await self._handle_dead_connection(connection_id)
            except Exception as cleanup_error:
                logger.error(f"Error during dead connection cleanup: {cleanup_error}")
            return False

    async def broadcast_to_user(
        self,
        user_id: int,
        message: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ) -> int:
        """
        Broadcast message to all devices of a user.

        Args:
            user_id: Target user
            message: Message payload
            exclude_connection: Optional connection to skip (e.g., the sender)

        Returns:
            Number of successful deliveries
        """
        connection_ids = self._user_connections.get(user_id, set())
        if not connection_ids:
            return 0

        success_count = 0
        for conn_id in list(connection_ids):
            if exclude_connection and conn_id == exclude_connection:
                continue

            if await self.send_to_connection(conn_id, message):
                success_count += 1

        return success_count

    async def broadcast_to_chat_session(
        self,
        chat_session_id: str,
        message: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ) -> int:
        """
        Broadcast message to all connections in a chat session.

        Args:
            chat_session_id: Target chat session
            message: Message payload
            exclude_connection: Optional connection to skip

        Returns:
            Number of successful deliveries
        """
        connection_ids = self._chat_connections.get(chat_session_id, set())
        if not connection_ids:
            return 0

        success_count = 0
        for conn_id in list(connection_ids):
            if exclude_connection and conn_id == exclude_connection:
                continue

            if await self.send_to_connection(conn_id, message):
                success_count += 1

        return success_count

    async def broadcast_to_all(
        self,
        message: Dict[str, Any],
        exclude_connection: Optional[str] = None
    ) -> int:
        """
        Broadcast message to all connected clients.

        Args:
            message: Message payload
            exclude_connection: Optional connection to skip

        Returns:
            Number of successful deliveries
        """
        success_count = 0
        for conn_id in list(self._connections.keys()):
            if exclude_connection and conn_id == exclude_connection:
                continue

            if await self.send_to_connection(conn_id, message):
                success_count += 1

        return success_count

    def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection info by ID"""
        return self._connections.get(connection_id)

    def get_user_connections(self, user_id: int) -> List[ConnectionInfo]:
        """Get all active connections for a user"""
        connection_ids = self._user_connections.get(user_id, set())
        return [
            self._connections[conn_id]
            for conn_id in connection_ids
            if conn_id in self._connections
        ]

    def get_chat_session_connections(self, chat_session_id: str) -> List[ConnectionInfo]:
        """Get all connections for a chat session"""
        connection_ids = self._chat_connections.get(chat_session_id, set())
        return [
            self._connections[conn_id]
            for conn_id in connection_ids
            if conn_id in self._connections
        ]

    def get_online_users(self) -> Set[int]:
        """Get set of all currently online user IDs"""
        return set(self._user_connections.keys())

    def is_user_online(self, user_id: int) -> bool:
        """Check if a user has any active connections"""
        return user_id in self._user_connections and len(self._user_connections[user_id]) > 0

    def get_user_device_count(self, user_id: int) -> int:
        """Get number of connected devices for a user"""
        return len(self._user_connections.get(user_id, set()))

    async def update_activity(self, connection_id: str) -> None:
        """Update last activity timestamp for a connection"""
        if connection_id in self._connections:
            self._connections[connection_id].last_activity = datetime.now(timezone.utc)

    async def handle_heartbeat(self, connection_id: str) -> None:
        """Update last ping timestamp for a connection"""
        if connection_id in self._connections:
            self._connections[connection_id].last_ping = datetime.now(timezone.utc)
            self._connections[connection_id].last_activity = datetime.now(timezone.utc)

    async def set_typing_status(
        self,
        connection_id: str,
        is_typing: bool
    ) -> Optional[ConnectionInfo]:
        """
        Set typing status for a connection.

        Returns:
            ConnectionInfo if found, None otherwise
        """
        if connection_id in self._connections:
            self._connections[connection_id].is_typing = is_typing
            return self._connections[connection_id]
        return None

    async def update_chat_session(
        self,
        connection_id: str,
        new_chat_session_id: str
    ) -> bool:
        """
        Move a connection to a different chat session.

        Args:
            connection_id: The connection to move
            new_chat_session_id: The new chat session

        Returns:
            True if successful, False otherwise
        """
        async with self._lock:
            if connection_id not in self._connections:
                return False

            conn_info = self._connections[connection_id]
            old_chat_session_id = conn_info.chat_session_id

            # Remove from old chat session
            if old_chat_session_id in self._chat_connections:
                self._chat_connections[old_chat_session_id].discard(connection_id)
                if not self._chat_connections[old_chat_session_id]:
                    del self._chat_connections[old_chat_session_id]

            # Add to new chat session
            if new_chat_session_id not in self._chat_connections:
                self._chat_connections[new_chat_session_id] = set()
            self._chat_connections[new_chat_session_id].add(connection_id)

            # Update connection info
            conn_info.chat_session_id = new_chat_session_id

            logger.info(
                f"Connection {connection_id} moved from chat {old_chat_session_id} "
                f"to {new_chat_session_id}"
            )

            return True

    async def leave_chat_session(self, connection_id: str, chat_session_id: str) -> bool:
        """
        Remove a connection from a chat session without disconnecting it.

        Args:
            connection_id: The connection to remove from the session
            chat_session_id: The chat session to leave

        Returns:
            True if successful, False otherwise
        """
        async with self._lock:
            if connection_id not in self._connections:
                return False

            conn_info = self._connections[connection_id]

            # Verify connection is actually in this chat session
            if conn_info.chat_session_id != chat_session_id:
                return False

            # Remove from chat session mapping
            if chat_session_id in self._chat_connections:
                self._chat_connections[chat_session_id].discard(connection_id)
                if not self._chat_connections[chat_session_id]:
                    del self._chat_connections[chat_session_id]

            # Clear chat session on the connection
            conn_info.chat_session_id = ""

            logger.info(f"Connection {connection_id} left chat session {chat_session_id}")
            return True

    async def cleanup_stale_connections(self, timeout_seconds: int = 120) -> int:
        """
        Remove connections that haven't sent heartbeat recently.

        Args:
            timeout_seconds: Seconds since last ping to consider stale

        Returns:
            Number of connections cleaned up
        """
        now = datetime.now(timezone.utc)
        stale_connections = []

        for conn_id, conn_info in list(self._connections.items()):
            elapsed = (now - conn_info.last_ping).total_seconds()
            if elapsed > timeout_seconds:
                stale_connections.append(conn_id)

        cleaned = 0
        for conn_id in stale_connections:
            try:
                conn_info = await self.disconnect(conn_id)
                if conn_info:
                    # Try to close the WebSocket gracefully
                    try:
                        await conn_info.websocket.close(code=1000)
                    except Exception:
                        pass
                    cleaned += 1
            except Exception as e:
                logger.error(f"Error cleaning up connection {conn_id}: {e}")

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} stale WebSocket connections")

        return cleaned

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return len(self._connections)

    def get_user_count(self) -> int:
        """Get number of unique online users"""
        return len(self._user_connections)

    def record_message(self, connection_id: str, msg_type: str) -> None:
        """
        Record a message event for stats tracking.

        Args:
            connection_id: The connection that sent the message
            msg_type: The message type (chat, typing_start, typing_stop, presence_update, etc.)
        """
        now = time.monotonic()
        self._message_timestamps.append(now)

        # Map message types to stat categories
        if msg_type == "chat":
            self._message_type_counts["chat"] += 1
        elif msg_type in ("typing_start", "typing_stop"):
            self._message_type_counts["typing"] += 1
        elif msg_type == "presence_update":
            self._message_type_counts["presence"] += 1
        elif msg_type in ("ping", "pong"):
            self._message_type_counts["ping"] += 1
        elif msg_type in (
            "mark_notification_read", "mark_all_read", "get_notifications",
            "set_dnd", "update_notification_settings",
            "subscribe_topic", "unsubscribe_topic",
        ):
            self._message_type_counts["notifications"] += 1

        # Increment per-connection counter
        conn = self._connections.get(connection_id)
        if conn:
            conn.message_count += 1

    def record_response_time(self, duration_seconds: float) -> None:
        """Record a chat response time for avg calculation."""
        self._response_times.append(duration_seconds)

    def _get_messages_per_minute(self) -> int:
        """Calculate messages in the last 60 seconds."""
        now = time.monotonic()
        cutoff = now - 60
        # Prune old timestamps
        while self._message_timestamps and self._message_timestamps[0] < cutoff:
            self._message_timestamps.popleft()
        return len(self._message_timestamps)

    def _get_avg_response_time_ms(self) -> int:
        """Calculate average response time in milliseconds."""
        if not self._response_times:
            return 0
        return int((sum(self._response_times) / len(self._response_times)) * 1000)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": self.get_connection_count(),
            "unique_users": self.get_user_count(),
            "active_chat_sessions": len(self._chat_connections),
            "messages_per_minute": self._get_messages_per_minute(),
            "avg_response_time": self._get_avg_response_time_ms(),
            "message_stats": dict(self._message_type_counts),
            "connections_per_user_distribution": {
                str(count): sum(1 for c in self._user_connections.values() if len(c) == count)
                for count in set(len(c) for c in self._user_connections.values())
            }
        }

    async def _handle_dead_connection(self, connection_id: str) -> None:
        """Handle a connection that appears to be dead"""
        logger.warning(f"Handling potentially dead connection: {connection_id}")
        await self.disconnect(connection_id)

    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'model_dump'):
            return self._make_json_serializable(obj.model_dump())
        elif hasattr(obj, 'value'):  # Enum
            return obj.value
        return obj

    async def _store_connection_in_redis(
        self,
        connection_id: str,
        conn_info: ConnectionInfo
    ) -> None:
        """Store connection info in Redis for distributed state"""
        if not self._redis:
            return

        key = f"ws:connection:{connection_id}"
        data = {
            "user_id": conn_info.user_id,
            "chat_session_id": conn_info.chat_session_id,
            "user_session_id": conn_info.user_session_id,
            "device_id": conn_info.device_id,
            "connected_at": conn_info.connected_at.isoformat(),
            "is_authenticated": conn_info.is_authenticated
        }
        await self._redis.setex(key, 3600, json.dumps(data))  # 1 hour TTL

        # Add to user's connection set
        user_key = f"ws:user:{conn_info.user_id}:connections"
        await self._redis.sadd(user_key, connection_id)
        await self._redis.expire(user_key, 3600)

    async def _remove_connection_from_redis(self, connection_id: str) -> None:
        """Remove connection info from Redis"""
        if not self._redis:
            return

        key = f"ws:connection:{connection_id}"
        data = await self._redis.get(key)
        if data:
            conn_data = json.loads(data)
            user_id = conn_data.get("user_id")
            if user_id:
                user_key = f"ws:user:{user_id}:connections"
                await self._redis.srem(user_key, connection_id)

        await self._redis.delete(key)


# Global connection manager instance — pass async Redis for distributed state
try:
    from database_storage.simple_redis_config import async_redis_client as _async_redis
except ImportError:
    _async_redis = None

connection_manager = WebSocketConnectionManager(redis_client=_async_redis)
