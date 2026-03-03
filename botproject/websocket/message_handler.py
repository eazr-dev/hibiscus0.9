"""
WebSocket Message Handler for EAZR Chat
Routes and processes incoming WebSocket messages.
"""

from typing import Dict, Any, Optional
from fastapi import WebSocket
from datetime import datetime, timezone
import json
import logging
import time

from websocket.models import (
    WebSocketMessageType,
    WebSocketErrorCode,
    PresenceStatus,
    parse_client_message,
    create_error_response,
    AuthenticateMessage,
    ChatMessage,
    TypingMessage,
    PresenceMessage,
    PingMessage,
    PongMessage,
    JoinChatMessage,
    LeaveChatMessage,
    AuthSuccessResponse,
    AuthFailureResponse,
    PongResponse,
    TypingIndicatorResponse,
    PresenceStatusResponse,
    ErrorResponse,
    # Notification messages
    MarkNotificationReadMessage,
    MarkAllReadMessage,
    GetNotificationsMessage,
    SetDNDMessage,
    UpdateNotificationSettingsMessage,
    SubscribeTopicMessage,
    UnsubscribeTopicMessage,
)
from websocket.connection_manager import WebSocketConnectionManager, ConnectionInfo
from websocket.auth_handler import WebSocketAuthHandler
from websocket.presence_manager import PresenceManager

# Import WebSocket rate limiter
try:
    from core.rate_limiter import ws_rate_limiter
    WS_RATE_LIMITER_AVAILABLE = True
except ImportError:
    ws_rate_limiter = None
    WS_RATE_LIMITER_AVAILABLE = False

logger = logging.getLogger(__name__)


class WebSocketMessageHandler:
    """
    Routes and processes WebSocket messages.

    Responsibilities:
    - Parse incoming messages
    - Route to appropriate handlers
    - Manage connection lifecycle
    - Handle errors gracefully
    """

    def __init__(
        self,
        connection_manager: WebSocketConnectionManager,
        auth_handler: WebSocketAuthHandler,
        presence_manager: PresenceManager,
        chat_service=None,  # Will be injected
        notification_handler=None  # Will be injected
    ):
        self.connections = connection_manager
        self.auth = auth_handler
        self.presence = presence_manager
        self.chat_service = chat_service
        self._notification_handler = notification_handler

        # Track pending authentications (connections without auth yet)
        # Maps temp_connection_id -> (WebSocket, timestamp)
        self._pending_auth: Dict[str, tuple] = {}
        self._max_pending_auth: int = 1000

    @property
    def notification_handler(self):
        """Lazy load notification handler"""
        if self._notification_handler is None:
            try:
                from websocket.notification_handler import notification_handler
                self._notification_handler = notification_handler
            except ImportError:
                logger.warning("Notification handler not available")
        return self._notification_handler

    def set_chat_service(self, chat_service) -> None:
        """Inject chat service dependency"""
        self.chat_service = chat_service

    async def handle_connection(
        self,
        websocket: WebSocket,
        temp_connection_id: str
    ) -> None:
        """
        Handle a new WebSocket connection that needs authentication.

        Args:
            websocket: The WebSocket connection
            temp_connection_id: Temporary ID for tracking before auth
        """
        # Enforce size limit — clean stale entries first, then reject if still full
        if len(self._pending_auth) >= self._max_pending_auth:
            self.cleanup_stale_pending_auth()
        if len(self._pending_auth) >= self._max_pending_auth:
            logger.warning(f"Pending auth limit reached ({self._max_pending_auth}), rejecting connection")
            return
        self._pending_auth[temp_connection_id] = (websocket, datetime.now(timezone.utc))

    async def handle_message(
        self,
        websocket: WebSocket,
        connection_id: Optional[str],
        raw_message: str
    ) -> Optional[str]:
        """
        Main entry point for handling WebSocket messages.

        Args:
            websocket: The WebSocket connection
            connection_id: Connection ID (None if not yet authenticated)
            raw_message: Raw JSON message string

        Returns:
            connection_id (may be newly assigned after auth)
        """
        try:
            # Parse JSON
            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                await self._send_error(
                    websocket,
                    "Invalid JSON format",
                    WebSocketErrorCode.INVALID_JSON
                )
                return connection_id

            # Get message type
            msg_type = data.get("type")
            if not msg_type:
                await self._send_error(
                    websocket,
                    "Message type is required",
                    WebSocketErrorCode.INVALID_MESSAGE
                )
                return connection_id

            # Handle authentication (allowed without connection_id)
            if msg_type == "authenticate":
                # Rate limit auth attempts by IP to prevent brute force
                if WS_RATE_LIMITER_AVAILABLE and ws_rate_limiter:
                    client_ip = websocket.client.host if websocket.client else "unknown"
                    is_allowed, rate_info = ws_rate_limiter.check_message_rate_limit(
                        user_id=0,  # No user yet, rate limit by IP via identifier
                        connection_id=f"auth_{client_ip}",
                        message_type="authenticate"
                    )
                    if not is_allowed:
                        await self._send_error(
                            websocket,
                            "Too many authentication attempts. Please slow down.",
                            WebSocketErrorCode.RATE_LIMIT_EXCEEDED,
                            details={"retry_after": rate_info.get("reset_after", 60)},
                            recoverable=True
                        )
                        return connection_id
                result = await self._handle_authenticate(websocket, data)
                # Clean up pending auth entry for this websocket
                self._cleanup_pending_auth_for(websocket)
                return result

            # All other messages require authentication
            if not connection_id:
                await self._send_error(
                    websocket,
                    "Authentication required. Send authenticate message first.",
                    WebSocketErrorCode.NOT_AUTHENTICATED,
                    recoverable=True
                )
                return None

            # Update activity timestamp
            await self.connections.update_activity(connection_id)

            # Parse and route message
            message = parse_client_message(data)
            if not message:
                await self._send_error(
                    websocket,
                    f"Unknown or invalid message type: {msg_type}",
                    WebSocketErrorCode.INVALID_MESSAGE_TYPE
                )
                return connection_id

            # Get user_id for notification handlers
            conn_info = self.connections.get_connection(connection_id)
            user_id = conn_info.user_id if conn_info else None

            # Check rate limit for this message type
            if WS_RATE_LIMITER_AVAILABLE and ws_rate_limiter and user_id:
                # Skip rate limiting for ping/pong (heartbeat)
                if msg_type not in ["ping", "pong"]:
                    is_allowed, rate_info = ws_rate_limiter.check_message_rate_limit(
                        user_id=user_id,
                        connection_id=connection_id,
                        message_type=msg_type
                    )
                    if not is_allowed:
                        await self._send_error(
                            websocket,
                            f"Rate limit exceeded for {msg_type}. Please slow down.",
                            WebSocketErrorCode.RATE_LIMIT_EXCEEDED,
                            details={
                                "limit": rate_info.get("limit", 0),
                                "remaining": rate_info.get("remaining", 0),
                                "reset_after": rate_info.get("reset_after", 60)
                            },
                            recoverable=True
                        )
                        logger.warning(f"WebSocket rate limit exceeded: user={user_id}, type={msg_type}")
                        return connection_id

                    # Additional burst check for chat messages
                    if msg_type == "chat":
                        burst_allowed, burst_info = ws_rate_limiter.check_chat_burst(user_id)
                        if not burst_allowed:
                            await self._send_error(
                                websocket,
                                "Too many messages too quickly. Please wait a moment.",
                                WebSocketErrorCode.RATE_LIMIT_EXCEEDED,
                                details={"retry_after": burst_info.get("reset_after", 1)},
                                recoverable=True
                            )
                            return connection_id

            # Route to appropriate handler
            handled = True
            if msg_type == "chat":
                _chat_start = time.monotonic()
                await self._handle_chat(websocket, connection_id, message)
                self.connections.record_response_time(time.monotonic() - _chat_start)
            elif msg_type == "typing_start":
                await self._handle_typing(websocket, connection_id, message, is_typing=True)
            elif msg_type == "typing_stop":
                await self._handle_typing(websocket, connection_id, message, is_typing=False)
            elif msg_type == "presence_update":
                await self._handle_presence_update(websocket, connection_id, message)
            elif msg_type == "ping":
                await self._handle_ping(websocket, connection_id, message)
            elif msg_type == "pong":
                await self._handle_pong(websocket, connection_id, message)
            elif msg_type == "join_chat":
                await self._handle_join_chat(websocket, connection_id, message)
            elif msg_type == "leave_chat":
                await self._handle_leave_chat(websocket, connection_id, message)
            # Notification message handlers
            elif msg_type == "mark_notification_read" and self.notification_handler and user_id:
                await self.notification_handler.handle_mark_notification_read(websocket, user_id, message)
            elif msg_type == "mark_all_read" and self.notification_handler and user_id:
                await self.notification_handler.handle_mark_all_read(websocket, user_id, message)
            elif msg_type == "get_notifications" and self.notification_handler and user_id:
                await self.notification_handler.handle_get_notifications(websocket, user_id, message)
            elif msg_type == "set_dnd" and self.notification_handler and user_id:
                await self.notification_handler.handle_set_dnd(websocket, user_id, message)
            elif msg_type == "update_notification_settings" and self.notification_handler and user_id:
                await self.notification_handler.handle_update_notification_settings(websocket, user_id, message)
            elif msg_type == "subscribe_topic" and self.notification_handler and user_id:
                await self.notification_handler.handle_subscribe_topic(websocket, user_id, message)
            elif msg_type == "unsubscribe_topic" and self.notification_handler and user_id:
                await self.notification_handler.handle_unsubscribe_topic(websocket, user_id, message)
            else:
                handled = False
                await self._send_error(
                    websocket,
                    f"Unhandled message type: {msg_type}",
                    WebSocketErrorCode.INVALID_MESSAGE_TYPE
                )

            # Record message stats
            if handled and connection_id:
                self.connections.record_message(connection_id, msg_type)

            return connection_id

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}", exc_info=True)
            await self._send_error(
                websocket,
                "Internal server error",
                WebSocketErrorCode.INTERNAL_ERROR,
                recoverable=True
            )
            return connection_id

    async def _handle_authenticate(
        self,
        websocket: WebSocket,
        data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Handle authentication request.

        Returns:
            connection_id on success, None on failure
        """
        try:
            message = AuthenticateMessage(**data)
        except Exception as e:
            logger.warning(f"Invalid authenticate message: {e}")
            await self._send_error(
                websocket,
                "Invalid authentication message format",
                WebSocketErrorCode.INVALID_MESSAGE
            )
            return None

        # Authenticate using auth handler
        success, auth_data = await self.auth.authenticate(
            access_token=message.access_token,
            user_id=message.user_id,
            chat_session_id=message.chat_session_id,
            device_id=message.device_id,
            user_session_id=message.user_session_id
        )

        if not success:
            logger.warning(f"Authentication failed: {auth_data.get('error')}")

            response = AuthFailureResponse(
                error=auth_data.get("error", "Authentication failed"),
                error_code=auth_data.get("error_code", "AUTH_FAILED")
            )
            await websocket.send_json(response.model_dump(mode='json'))
            return None

        # Register connection
        try:
            connection_id = await self.connections.connect(
                websocket=websocket,
                user_id=auth_data["user_id"],
                chat_session_id=auth_data["chat_session_id"],
                user_session_id=auth_data["user_session_id"],
                device_id=auth_data["device_id"],
                access_token=auth_data["access_token"],
                user_name=auth_data.get("user_name")
            )
        except ConnectionError as e:
            logger.warning(f"Connection limit exceeded for user {auth_data['user_id']}: {e}")
            response = AuthFailureResponse(
                error="Too many active connections. Please close other sessions first.",
                error_code="CONNECTION_LIMIT_EXCEEDED"
            )
            await websocket.send_json(response.model_dump(mode='json'))
            return None

        # Set user online
        await self.presence.set_online(
            user_id=auth_data["user_id"],
            device_id=auth_data["device_id"],
            user_name=auth_data.get("user_name")
        )

        # Send success response
        response = AuthSuccessResponse(
            user_id=auth_data["user_id"],
            user_session_id=auth_data["user_session_id"],
            chat_session_id=auth_data["chat_session_id"],
            connection_id=connection_id,
            user_name=auth_data.get("user_name"),
            is_new_session=auth_data.get("session_regenerated", False)
        )
        await websocket.send_json(response.model_dump(mode='json'))

        # Send initial notification state
        if self.notification_handler:
            try:
                await self.notification_handler.send_initial_state(
                    websocket=websocket,
                    user_id=auth_data["user_id"]
                )
            except Exception as e:
                logger.warning(f"Failed to send initial notification state: {e}")

        # Notify notification manager of connection
        try:
            from websocket.notification_manager import notification_manager
            await notification_manager.user_connected(
                user_id=auth_data["user_id"],
                device_id=auth_data["device_id"]
            )
        except Exception as e:
            logger.warning(f"Failed to notify notification manager: {e}")

        logger.info(
            f"WebSocket authenticated: user_id={auth_data['user_id']}, "
            f"connection_id={connection_id}"
        )

        return connection_id

    async def _handle_chat(
        self,
        websocket: WebSocket,
        connection_id: str,
        message: ChatMessage
    ) -> None:
        """Handle chat message"""
        conn_info = self.connections.get_connection(connection_id)
        if not conn_info:
            await self._send_error(
                websocket,
                "Connection not found",
                WebSocketErrorCode.INTERNAL_ERROR
            )
            return

        # Update presence activity
        await self.presence.update_activity(conn_info.user_id)

        # Validate chat session ownership if a specific session is requested
        if message.chat_session_id:
            session_valid = await self._validate_chat_session_ownership(
                chat_session_id=message.chat_session_id,
                user_id=conn_info.user_id
            )
            if not session_valid:
                await self._send_error(
                    websocket,
                    "Chat session does not belong to this user",
                    WebSocketErrorCode.UNAUTHORIZED
                )
                return

        # Process chat message using chat service
        if self.chat_service:
            try:
                await self.chat_service.process_chat_message(
                    websocket=websocket,
                    connection_id=connection_id,
                    user_id=conn_info.user_id,
                    chat_session_id=message.chat_session_id,
                    user_session_id=conn_info.user_session_id,
                    access_token=conn_info.access_token,
                    query=message.query,
                    action=message.action,
                    assistance_type=message.assistance_type,
                    insurance_type=message.insurance_type,
                    service_type=message.service_type,
                    policy_id=message.policy_id,
                    model=message.model,
                    stream=message.stream if hasattr(message, 'stream') and message.stream is not None else True
                )
            except Exception as e:
                logger.error(f"Chat processing error: {e}", exc_info=True)
                await self._send_error(
                    websocket,
                    "Failed to process chat message",
                    WebSocketErrorCode.INTERNAL_ERROR
                )
        else:
            logger.warning("Chat service not configured")
            await self._send_error(
                websocket,
                "Chat service not available",
                WebSocketErrorCode.INTERNAL_ERROR
            )

    async def _handle_typing(
        self,
        websocket: WebSocket,
        connection_id: str,
        message: TypingMessage,
        is_typing: bool
    ) -> None:
        """Handle typing indicator"""
        conn_info = await self.connections.set_typing_status(connection_id, is_typing)
        if not conn_info:
            return

        # Broadcast typing indicator to other devices of the same user
        # and potentially to other users in the chat
        response = TypingIndicatorResponse(
            chat_session_id=message.chat_session_id,
            user_id=conn_info.user_id,
            is_typing=is_typing,
            device_id=conn_info.device_id,
            user_name=conn_info.user_name
        )

        # Broadcast to all other connections in the same chat session
        await self.connections.broadcast_to_chat_session(
            chat_session_id=message.chat_session_id,
            message=response.model_dump(mode='json'),
            exclude_connection=connection_id
        )

    async def _handle_presence_update(
        self,
        websocket: WebSocket,
        connection_id: str,
        message: PresenceMessage
    ) -> None:
        """Handle manual presence status update"""
        conn_info = self.connections.get_connection(connection_id)
        if not conn_info:
            return

        # Update presence
        status_changed = await self.presence.set_status(
            user_id=conn_info.user_id,
            status=message.status
        )

        if status_changed:
            # Broadcast presence change to user's other devices
            response = PresenceStatusResponse(
                user_id=conn_info.user_id,
                status=message.status,
                last_seen=datetime.now(timezone.utc),
                user_name=conn_info.user_name
            )

            await self.connections.broadcast_to_user(
                user_id=conn_info.user_id,
                message=response.model_dump(mode='json'),
                exclude_connection=connection_id
            )

    async def _handle_ping(
        self,
        websocket: WebSocket,
        connection_id: str,
        message: PingMessage
    ) -> None:
        """Handle heartbeat ping from client, respond with pong"""
        await self.connections.handle_heartbeat(connection_id)

        response = PongResponse(server_time=datetime.now(timezone.utc))
        await websocket.send_json(response.model_dump(mode='json'))

    async def _handle_pong(
        self,
        websocket: WebSocket,
        connection_id: str,
        message: PongMessage
    ) -> None:
        """Handle heartbeat pong from client (response to server ping)"""
        # Update heartbeat timestamp - this keeps the connection alive
        await self.connections.handle_heartbeat(connection_id)
        logger.debug(f"Pong received from connection: {connection_id}")

    async def _handle_join_chat(
        self,
        websocket: WebSocket,
        connection_id: str,
        message: JoinChatMessage
    ) -> None:
        """Handle joining a different chat session"""
        conn_info = self.connections.get_connection(connection_id)
        if not conn_info:
            return

        # Validate chat session belongs to the authenticated user
        session_valid = await self._validate_chat_session_ownership(
            chat_session_id=message.chat_session_id,
            user_id=conn_info.user_id
        )
        if not session_valid:
            await self._send_error(
                websocket,
                "Chat session not found or access denied",
                WebSocketErrorCode.CHAT_SESSION_NOT_FOUND
            )
            return

        success = await self.connections.update_chat_session(
            connection_id=connection_id,
            new_chat_session_id=message.chat_session_id
        )

        if success:
            await websocket.send_json({
                "type": "chat_joined",
                "chat_session_id": message.chat_session_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            await self._send_error(
                websocket,
                "Failed to join chat session",
                WebSocketErrorCode.CHAT_SESSION_NOT_FOUND
            )

    async def _handle_leave_chat(
        self,
        websocket: WebSocket,
        connection_id: str,
        message: LeaveChatMessage
    ) -> None:
        """Handle leaving a chat session"""
        conn_info = self.connections.get_connection(connection_id)
        if not conn_info:
            return

        # Use public API to leave chat session (handles locking and cleanup internally)
        success = await self.connections.leave_chat_session(
            connection_id=connection_id,
            chat_session_id=message.chat_session_id
        )

        if not success:
            await self._send_error(
                websocket,
                "Not in the specified chat session",
                WebSocketErrorCode.CHAT_SESSION_NOT_FOUND
            )
            return

        await websocket.send_json({
            "type": "chat_left",
            "chat_session_id": message.chat_session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def handle_disconnect(self, connection_id: str) -> None:
        """
        Handle WebSocket disconnection.

        Args:
            connection_id: The disconnecting connection
        """
        conn_info = await self.connections.disconnect(connection_id)
        if conn_info:
            # Update presence (will go offline only if no other devices)
            await self.presence.set_offline(
                user_id=conn_info.user_id,
                device_id=conn_info.device_id
            )

            # Notify notification manager of disconnection
            try:
                from websocket.notification_manager import notification_manager
                await notification_manager.user_disconnected(
                    user_id=conn_info.user_id,
                    device_id=conn_info.device_id
                )
            except Exception as e:
                logger.warning(f"Failed to notify notification manager of disconnect: {e}")

            logger.info(
                f"WebSocket disconnected: user_id={conn_info.user_id}, "
                f"connection_id={connection_id}"
            )

    def _cleanup_pending_auth_for(self, websocket: WebSocket) -> None:
        """Remove pending auth entries matching this websocket"""
        to_remove = [
            tid for tid, (ws, _) in self._pending_auth.items()
            if ws is websocket
        ]
        for tid in to_remove:
            del self._pending_auth[tid]

    def cleanup_stale_pending_auth(self, max_age_seconds: int = 120) -> int:
        """Remove pending auth entries older than max_age_seconds. Returns count removed."""
        now = datetime.now(timezone.utc)
        stale = [
            tid for tid, (_, created) in self._pending_auth.items()
            if (now - created).total_seconds() > max_age_seconds
        ]
        for tid in stale:
            del self._pending_auth[tid]
        if stale:
            logger.debug(f"Cleaned up {len(stale)} stale pending auth entries")
        return len(stale)

    async def _validate_chat_session_ownership(
        self,
        chat_session_id: str,
        user_id: int
    ) -> bool:
        """
        Validate that a chat session belongs to the given user.

        Checks session storage (Redis/fallback) and optionally MongoDB
        to verify the session's user_id matches.
        """
        try:
            # Check via auth handler's session getter
            if self.auth._get_session:
                session_data = self.auth._get_session(chat_session_id)
                if session_data:
                    session_user_id = session_data.get("user_id")
                    return session_user_id == user_id
                # Session not found in store — deny access
                return False

            # If no session getter available, check if the chat_session_id
            # embeds the user_id (format: chat_{user_id}_{timestamp}_{hex})
            parts = chat_session_id.split("_")
            if len(parts) >= 2:
                try:
                    embedded_uid = int(parts[1])
                    return embedded_uid == user_id
                except (ValueError, IndexError):
                    pass

            return False
        except Exception as e:
            logger.error(f"Error validating chat session ownership: {e}")
            return False

    async def _send_error(
        self,
        websocket: WebSocket,
        error: str,
        error_code: WebSocketErrorCode,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = True
    ) -> None:
        """Send error response to client"""
        response = create_error_response(
            error=error,
            error_code=error_code,
            details=details,
            recoverable=recoverable
        )

        try:
            await websocket.send_json(response.model_dump(mode='json'))
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")
