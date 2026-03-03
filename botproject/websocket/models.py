"""
WebSocket Message Models for EAZR Chat
Pydantic models for all WebSocket message types.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal, Union
from datetime import datetime, timezone
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WebSocketMessageType(str, Enum):
    """Types of WebSocket messages"""
    # Client -> Server
    AUTHENTICATE = "authenticate"
    CHAT = "chat"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    PRESENCE_UPDATE = "presence_update"
    PING = "ping"
    JOIN_CHAT = "join_chat"
    LEAVE_CHAT = "leave_chat"

    # Client -> Server (Notifications)
    MARK_NOTIFICATION_READ = "mark_notification_read"
    MARK_ALL_READ = "mark_all_read"
    GET_NOTIFICATIONS = "get_notifications"
    SET_DND = "set_dnd"
    UPDATE_NOTIFICATION_SETTINGS = "update_notification_settings"
    SUBSCRIBE_TOPIC = "subscribe_topic"
    UNSUBSCRIBE_TOPIC = "unsubscribe_topic"

    # Server -> Client
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    CHAT_MESSAGE = "chat_message"
    CHAT_STREAM = "chat_stream"
    CHAT_STREAM_END = "chat_stream_end"
    TYPING_INDICATOR = "typing_indicator"
    PRESENCE_STATUS = "presence_status"
    PONG = "pong"
    ERROR = "error"
    NOTIFICATION = "notification"
    CONNECTION_ACK = "connection_ack"

    # Server -> Client (Notifications)
    UNREAD_COUNT = "unread_count"
    NOTIFICATION_LIST = "notification_list"
    DND_STATUS = "dnd_status"
    NOTIFICATION_SETTINGS = "notification_settings"
    TOPIC_SUBSCRIBED = "topic_subscribed"
    TOPIC_UNSUBSCRIBED = "topic_unsubscribed"


class PresenceStatus(str, Enum):
    """User presence status"""
    ONLINE = "online"
    OFFLINE = "offline"
    AWAY = "away"
    BUSY = "busy"


class WebSocketErrorCode(str, Enum):
    """WebSocket error codes"""
    AUTH_FAILED = "AUTH_FAILED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    INVALID_MESSAGE = "INVALID_MESSAGE"
    INVALID_MESSAGE_TYPE = "INVALID_MESSAGE_TYPE"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    CHAT_SESSION_NOT_FOUND = "CHAT_SESSION_NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    INVALID_JSON = "INVALID_JSON"


# WebSocket close codes (standard + custom)
class WebSocketCloseCode:
    """WebSocket close codes"""
    NORMAL = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    POLICY_VIOLATION = 1008
    INTERNAL_ERROR = 1011
    # Custom codes (4000-4999)
    AUTH_FAILED = 4001
    TOKEN_EXPIRED = 4002
    RATE_LIMITED = 4003
    SESSION_NOT_FOUND = 4004
    INVALID_MESSAGE = 4005


# ============= Base Message =============

class BaseWSMessage(BaseModel):
    """Base WebSocket message structure"""
    type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    message_id: Optional[str] = None

    class Config:
        use_enum_values = True


# ============= Client -> Server Messages =============

class AuthenticateMessage(BaseWSMessage):
    """Initial authentication message from client"""
    type: Literal["authenticate"] = "authenticate"
    access_token: str
    user_id: Optional[int] = None  # Optional, extracted from token if not provided
    chat_session_id: Optional[str] = None  # Optional: join existing chat
    device_id: Optional[str] = None
    user_session_id: Optional[str] = None  # Optional: existing user session


class ChatMessage(BaseWSMessage):
    """Chat message from client"""
    type: Literal["chat"] = "chat"
    chat_session_id: str
    query: str = Field(..., max_length=10000)
    # Optional fields for enhanced chatbot (same as HTTP /ask)
    action: Optional[str] = None
    user_input: Optional[str] = None
    assistance_type: Optional[str] = None
    insurance_type: Optional[str] = None
    service_type: Optional[str] = None
    policy_id: Optional[str] = None
    model: Optional[str] = Field(default="policy_analysis")  # policy_analysis, coverage_advisory, claim_support
    stream: Optional[bool] = Field(default=True)  # Whether to stream LLM response tokens


class TypingMessage(BaseWSMessage):
    """Typing indicator message from client"""
    type: Literal["typing_start", "typing_stop"]
    chat_session_id: str


class PresenceMessage(BaseWSMessage):
    """Presence update message from client"""
    type: Literal["presence_update"] = "presence_update"
    status: PresenceStatus


class PingMessage(BaseWSMessage):
    """Heartbeat ping message from client"""
    type: Literal["ping"] = "ping"


class PongMessage(BaseWSMessage):
    """Heartbeat pong message from client (response to server ping)"""
    type: Literal["pong"] = "pong"


class JoinChatMessage(BaseWSMessage):
    """Join a different chat session"""
    type: Literal["join_chat"] = "join_chat"
    chat_session_id: str


class LeaveChatMessage(BaseWSMessage):
    """Leave current chat session"""
    type: Literal["leave_chat"] = "leave_chat"
    chat_session_id: str


# ============= Client -> Server Messages (Notifications) =============

class MarkNotificationReadMessage(BaseWSMessage):
    """Mark a notification as read"""
    type: Literal["mark_notification_read"] = "mark_notification_read"
    notification_id: str


class MarkAllReadMessage(BaseWSMessage):
    """Mark all notifications as read"""
    type: Literal["mark_all_read"] = "mark_all_read"


class GetNotificationsMessage(BaseWSMessage):
    """Request notification history"""
    type: Literal["get_notifications"] = "get_notifications"
    limit: int = 20
    offset: int = 0
    unread_only: bool = False


class SetDNDMessage(BaseWSMessage):
    """Set Do Not Disturb mode"""
    type: Literal["set_dnd"] = "set_dnd"
    enabled: bool
    duration_minutes: Optional[int] = None  # None = until manually disabled


class UpdateNotificationSettingsMessage(BaseWSMessage):
    """Update notification preferences"""
    type: Literal["update_notification_settings"] = "update_notification_settings"
    settings: Dict[str, bool]  # e.g., {"policy_renewal": true, "promotional": false}


class SubscribeTopicMessage(BaseWSMessage):
    """Subscribe to a notification topic"""
    type: Literal["subscribe_topic"] = "subscribe_topic"
    topic: str


class UnsubscribeTopicMessage(BaseWSMessage):
    """Unsubscribe from a notification topic"""
    type: Literal["unsubscribe_topic"] = "unsubscribe_topic"
    topic: str


# ============= Server -> Client Messages =============

class ConnectionAckResponse(BaseWSMessage):
    """Connection acknowledgment (before full auth)"""
    type: Literal["connection_ack"] = "connection_ack"
    connection_id: str
    requires_auth: bool = True
    server_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuthSuccessResponse(BaseWSMessage):
    """Authentication success response"""
    type: Literal["auth_success"] = "auth_success"
    user_id: int
    user_session_id: str
    chat_session_id: Optional[str] = None
    connection_id: str
    user_name: Optional[str] = None
    is_new_session: bool = False


class AuthFailureResponse(BaseWSMessage):
    """Authentication failure response"""
    type: Literal["auth_failure"] = "auth_failure"
    error: str
    error_code: str


class ChatMessageResponse(BaseWSMessage):
    """Complete chat response from assistant (non-streaming)"""
    type: Literal["chat_message"] = "chat_message"
    chat_session_id: str
    response_type: str  # Same as HTTP: chat_message, selection_menu, question, etc.
    data: Dict[str, Any]  # Standardized response data (same format as HTTP /ask)
    metadata: Optional[Dict[str, Any]] = None


class ChatStreamResponse(BaseWSMessage):
    """Streaming token for AI response"""
    type: Literal["chat_stream"] = "chat_stream"
    chat_session_id: str
    token: str
    token_index: int = 0
    is_final: bool = False


class ChatStreamEndResponse(BaseWSMessage):
    """End of streaming response with full data"""
    type: Literal["chat_stream_end"] = "chat_stream_end"
    chat_session_id: str
    full_response: str
    response_type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    total_tokens: int = 0


class TypingIndicatorResponse(BaseWSMessage):
    """Typing indicator broadcast to other devices/users"""
    type: Literal["typing_indicator"] = "typing_indicator"
    chat_session_id: str
    user_id: int
    is_typing: bool
    device_id: Optional[str] = None
    user_name: Optional[str] = None


class PresenceStatusResponse(BaseWSMessage):
    """Presence status update broadcast"""
    type: Literal["presence_status"] = "presence_status"
    user_id: int
    status: PresenceStatus
    last_seen: Optional[datetime] = None
    user_name: Optional[str] = None


class PongResponse(BaseWSMessage):
    """Heartbeat pong response"""
    type: Literal["pong"] = "pong"
    server_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorResponse(BaseWSMessage):
    """Error response"""
    type: Literal["error"] = "error"
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    recoverable: bool = True  # Whether client should retry


class NotificationResponse(BaseWSMessage):
    """Push notification via WebSocket"""
    type: Literal["notification"] = "notification"
    notification_id: str
    notification_type: str  # policy_renewal, claim_update, payment_due, etc.
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    action_url: Optional[str] = None
    priority: str = "normal"  # low, normal, high


class UnreadCountResponse(BaseWSMessage):
    """Unread notification count update"""
    type: Literal["unread_count"] = "unread_count"
    unread_count: int


class NotificationItem(BaseModel):
    """Single notification item in list"""
    notification_id: str
    notification_type: str
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    action_url: Optional[str] = None
    priority: str = "normal"
    sent_at: datetime
    read: bool = False
    read_at: Optional[datetime] = None


class NotificationListResponse(BaseWSMessage):
    """List of notifications"""
    type: Literal["notification_list"] = "notification_list"
    notifications: List[NotificationItem]
    total: int
    unread_count: int
    has_more: bool = False


class DNDStatusResponse(BaseWSMessage):
    """DND status response"""
    type: Literal["dnd_status"] = "dnd_status"
    enabled: bool
    until: Optional[datetime] = None


class NotificationSettingsResponse(BaseWSMessage):
    """Notification settings response"""
    type: Literal["notification_settings"] = "notification_settings"
    settings: Dict[str, bool]


class TopicSubscribedResponse(BaseWSMessage):
    """Topic subscription confirmation"""
    type: Literal["topic_subscribed"] = "topic_subscribed"
    topic: str
    success: bool
    message: str


class TopicUnsubscribedResponse(BaseWSMessage):
    """Topic unsubscription confirmation"""
    type: Literal["topic_unsubscribed"] = "topic_unsubscribed"
    topic: str
    success: bool
    message: str


# ============= Message Parsing Helpers =============

def parse_client_message(raw_data: Dict[str, Any]) -> Union[
    AuthenticateMessage,
    ChatMessage,
    TypingMessage,
    PresenceMessage,
    PingMessage,
    PongMessage,
    JoinChatMessage,
    LeaveChatMessage,
    MarkNotificationReadMessage,
    MarkAllReadMessage,
    GetNotificationsMessage,
    SetDNDMessage,
    UpdateNotificationSettingsMessage,
    SubscribeTopicMessage,
    UnsubscribeTopicMessage,
    None
]:
    """
    Parse raw JSON data into appropriate client message type.

    Returns:
        Parsed message object or None if invalid
    """
    msg_type = raw_data.get("type")

    try:
        if msg_type == "authenticate":
            return AuthenticateMessage(**raw_data)
        elif msg_type == "chat":
            return ChatMessage(**raw_data)
        elif msg_type in ["typing_start", "typing_stop"]:
            return TypingMessage(**raw_data)
        elif msg_type == "presence_update":
            return PresenceMessage(**raw_data)
        elif msg_type == "ping":
            return PingMessage(**raw_data)
        elif msg_type == "pong":
            return PongMessage(**raw_data)
        elif msg_type == "join_chat":
            return JoinChatMessage(**raw_data)
        elif msg_type == "leave_chat":
            return LeaveChatMessage(**raw_data)
        # Notification messages
        elif msg_type == "mark_notification_read":
            return MarkNotificationReadMessage(**raw_data)
        elif msg_type == "mark_all_read":
            return MarkAllReadMessage(**raw_data)
        elif msg_type == "get_notifications":
            return GetNotificationsMessage(**raw_data)
        elif msg_type == "set_dnd":
            return SetDNDMessage(**raw_data)
        elif msg_type == "update_notification_settings":
            return UpdateNotificationSettingsMessage(**raw_data)
        elif msg_type == "subscribe_topic":
            return SubscribeTopicMessage(**raw_data)
        elif msg_type == "unsubscribe_topic":
            return UnsubscribeTopicMessage(**raw_data)
        else:
            # Unknown message type - log for debugging
            logger.warning(f"Unknown message type: {msg_type}")
            return None
    except Exception as e:
        # Log parsing errors for debugging
        logger.error(f"Error parsing message type '{msg_type}': {e}", exc_info=True)
        return None


def create_error_response(
    error: str,
    error_code: Union[str, WebSocketErrorCode],
    details: Optional[Dict[str, Any]] = None,
    recoverable: bool = True
) -> ErrorResponse:
    """Helper to create error response"""
    return ErrorResponse(
        error=error,
        error_code=error_code.value if isinstance(error_code, WebSocketErrorCode) else error_code,
        details=details,
        recoverable=recoverable
    )
