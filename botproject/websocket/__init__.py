"""
WebSocket Module for EAZR Chat
Real-time chat with streaming AI responses, typing indicators, presence status, and notifications.
"""

from websocket.models import (
    WebSocketMessageType,
    PresenceStatus,
    # Client -> Server
    AuthenticateMessage,
    ChatMessage,
    TypingMessage,
    PresenceMessage,
    PingMessage,
    PongMessage,
    JoinChatMessage,
    LeaveChatMessage,
    # Client -> Server (Notifications)
    MarkNotificationReadMessage,
    MarkAllReadMessage,
    GetNotificationsMessage,
    SetDNDMessage,
    UpdateNotificationSettingsMessage,
    SubscribeTopicMessage,
    UnsubscribeTopicMessage,
    # Server -> Client
    AuthSuccessResponse,
    AuthFailureResponse,
    ChatMessageResponse,
    ChatStreamResponse,
    ChatStreamEndResponse,
    TypingIndicatorResponse,
    PresenceStatusResponse,
    PongResponse,
    ErrorResponse,
    NotificationResponse,
    ConnectionAckResponse,
    # Server -> Client (Notifications)
    UnreadCountResponse,
    NotificationListResponse,
    NotificationItem,
    DNDStatusResponse,
    NotificationSettingsResponse,
    TopicSubscribedResponse,
    TopicUnsubscribedResponse,
)

from websocket.connection_manager import (
    WebSocketConnectionManager,
    ConnectionInfo,
)

from websocket.auth_handler import WebSocketAuthHandler

from websocket.presence_manager import PresenceManager

from websocket.message_handler import WebSocketMessageHandler

from websocket.notification_manager import (
    WebSocketNotificationManager,
    NotificationChannel,
    NotificationDeliveryStatus,
    PendingNotification,
    notification_manager,
)

from websocket.notification_handler import (
    WebSocketNotificationHandler,
    notification_handler,
)

__all__ = [
    # Enums
    "WebSocketMessageType",
    "PresenceStatus",
    "NotificationChannel",
    "NotificationDeliveryStatus",
    # Client Messages
    "AuthenticateMessage",
    "ChatMessage",
    "TypingMessage",
    "PresenceMessage",
    "PingMessage",
    "PongMessage",
    "JoinChatMessage",
    "LeaveChatMessage",
    # Client Notification Messages
    "MarkNotificationReadMessage",
    "MarkAllReadMessage",
    "GetNotificationsMessage",
    "SetDNDMessage",
    "UpdateNotificationSettingsMessage",
    "SubscribeTopicMessage",
    "UnsubscribeTopicMessage",
    # Server Messages
    "AuthSuccessResponse",
    "AuthFailureResponse",
    "ChatMessageResponse",
    "ChatStreamResponse",
    "ChatStreamEndResponse",
    "TypingIndicatorResponse",
    "PresenceStatusResponse",
    "PongResponse",
    "ErrorResponse",
    "NotificationResponse",
    "ConnectionAckResponse",
    # Server Notification Messages
    "UnreadCountResponse",
    "NotificationListResponse",
    "NotificationItem",
    "DNDStatusResponse",
    "NotificationSettingsResponse",
    "TopicSubscribedResponse",
    "TopicUnsubscribedResponse",
    # Managers
    "WebSocketConnectionManager",
    "ConnectionInfo",
    "WebSocketAuthHandler",
    "PresenceManager",
    "WebSocketMessageHandler",
    # Notification
    "WebSocketNotificationManager",
    "PendingNotification",
    "notification_manager",
    "WebSocketNotificationHandler",
    "notification_handler",
]
