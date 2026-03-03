"""
WebSocket Notification Handler for EAZR Chat
Handles notification-related WebSocket messages.
"""

from typing import Dict, Any, Optional, List
from fastapi import WebSocket
from datetime import datetime, timedelta, timezone
import logging

from websocket.models import (
    MarkNotificationReadMessage,
    MarkAllReadMessage,
    GetNotificationsMessage,
    SetDNDMessage,
    UpdateNotificationSettingsMessage,
    SubscribeTopicMessage,
    UnsubscribeTopicMessage,
    NotificationListResponse,
    NotificationItem,
    UnreadCountResponse,
    DNDStatusResponse,
    NotificationSettingsResponse,
    TopicSubscribedResponse,
    TopicUnsubscribedResponse,
    WebSocketErrorCode,
    create_error_response,
)

logger = logging.getLogger(__name__)


class WebSocketNotificationHandler:
    """
    Handles notification-related WebSocket messages.

    Integrates with:
    - NotificationService (FCM + MongoDB)
    - WebSocketNotificationManager (real-time delivery)
    """

    def __init__(self):
        self._notification_service = None
        self._notification_manager = None

    @property
    def notification_service(self):
        """Lazy load notification service"""
        if self._notification_service is None:
            try:
                from services.notification_service import notification_service
                self._notification_service = notification_service
            except ImportError:
                logger.warning("Notification service not available")
        return self._notification_service

    @property
    def notification_manager(self):
        """Lazy load notification manager"""
        if self._notification_manager is None:
            try:
                from websocket.notification_manager import notification_manager
                self._notification_manager = notification_manager
            except ImportError:
                logger.warning("Notification manager not available")
        return self._notification_manager

    async def handle_mark_notification_read(
        self,
        websocket: WebSocket,
        user_id: int,
        message: MarkNotificationReadMessage
    ) -> None:
        """Handle mark notification as read"""
        try:
            if self.notification_manager:
                count = await self.notification_manager.mark_as_read(
                    user_id=user_id,
                    notification_id=message.notification_id
                )
            elif self.notification_service:
                success = await self.notification_service.mark_notification_read(
                    str(user_id), message.notification_id
                )
                count = 1 if success else 0
            else:
                await self._send_error(websocket, "Notification service not available")
                return

            # Send updated unread count
            unread = await self._get_unread_count(user_id)
            response = UnreadCountResponse(unread_count=unread)
            await websocket.send_json(response.model_dump(mode='json'))

            logger.debug(f"User {user_id} marked notification {message.notification_id} as read")

        except Exception as e:
            logger.error(f"Error marking notification read: {e}")
            await self._send_error(websocket, "Failed to mark notification as read")

    async def handle_mark_all_read(
        self,
        websocket: WebSocket,
        user_id: int,
        message: MarkAllReadMessage
    ) -> None:
        """Handle mark all notifications as read"""
        try:
            if self.notification_manager:
                count = await self.notification_manager.mark_as_read(user_id=user_id)
            elif self.notification_service:
                count = await self.notification_service.mark_all_notifications_read(str(user_id))
            else:
                await self._send_error(websocket, "Notification service not available")
                return

            # Send updated unread count (should be 0)
            response = UnreadCountResponse(unread_count=0)
            await websocket.send_json(response.model_dump(mode='json'))

            logger.info(f"User {user_id} marked {count} notifications as read")

        except Exception as e:
            logger.error(f"Error marking all notifications read: {e}")
            await self._send_error(websocket, "Failed to mark all notifications as read")

    async def handle_get_notifications(
        self,
        websocket: WebSocket,
        user_id: int,
        message: GetNotificationsMessage
    ) -> None:
        """Handle get notifications request"""
        try:
            if not self.notification_service:
                await self._send_error(websocket, "Notification service not available")
                return

            notifications, total, unread = await self.notification_service.get_notification_history(
                user_id=str(user_id),
                limit=message.limit,
                offset=message.offset,
                unread_only=message.unread_only
            )

            # Convert to NotificationItem list
            items = []
            for n in notifications:
                items.append(NotificationItem(
                    notification_id=n.get("notification_id", ""),
                    notification_type=n.get("notification_type", "system"),
                    title=n.get("title", ""),
                    body=n.get("body", ""),
                    data=n.get("data"),
                    image_url=n.get("image_url"),
                    action_url=n.get("action_url"),
                    priority=n.get("priority", "normal"),
                    sent_at=n.get("sent_at", datetime.now(timezone.utc)),
                    read=n.get("read", False),
                    read_at=n.get("read_at")
                ))

            has_more = message.offset + len(items) < total

            response = NotificationListResponse(
                notifications=items,
                total=total,
                unread_count=unread,
                has_more=has_more
            )
            await websocket.send_json(response.model_dump(mode='json'))

            logger.debug(f"Sent {len(items)} notifications to user {user_id}")

        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            await self._send_error(websocket, "Failed to get notifications")

    async def handle_set_dnd(
        self,
        websocket: WebSocket,
        user_id: int,
        message: SetDNDMessage
    ) -> None:
        """Handle set Do Not Disturb"""
        try:
            if self.notification_manager:
                await self.notification_manager.set_dnd(
                    user_id=user_id,
                    enabled=message.enabled,
                    duration_minutes=message.duration_minutes
                )

            # Calculate until time
            until = None
            if message.enabled and message.duration_minutes:
                until = datetime.now(timezone.utc) + timedelta(minutes=message.duration_minutes)

            response = DNDStatusResponse(
                enabled=message.enabled,
                until=until
            )
            await websocket.send_json(response.model_dump(mode='json'))

            logger.info(f"User {user_id} set DND: {message.enabled} (duration: {message.duration_minutes})")

        except Exception as e:
            logger.error(f"Error setting DND: {e}")
            await self._send_error(websocket, "Failed to set DND status")

    async def handle_update_notification_settings(
        self,
        websocket: WebSocket,
        user_id: int,
        message: UpdateNotificationSettingsMessage
    ) -> None:
        """Handle update notification settings"""
        try:
            if not self.notification_service:
                await self._send_error(websocket, "Notification service not available")
                return

            # Update settings in MongoDB
            success = await self.notification_service.update_notification_settings(
                str(user_id), message.settings
            )

            if success:
                # Get updated settings
                settings = await self.notification_service.get_notification_settings(str(user_id))
                response = NotificationSettingsResponse(settings=settings)
                await websocket.send_json(response.model_dump(mode='json'))
                logger.info(f"User {user_id} updated notification settings")
            else:
                await self._send_error(websocket, "Failed to update settings")

        except Exception as e:
            logger.error(f"Error updating notification settings: {e}")
            await self._send_error(websocket, "Failed to update notification settings")

    async def handle_subscribe_topic(
        self,
        websocket: WebSocket,
        user_id: int,
        message: SubscribeTopicMessage
    ) -> None:
        """Handle subscribe to topic"""
        try:
            if not self.notification_service:
                await self._send_error(websocket, "Notification service not available")
                return

            success, msg = await self.notification_service.subscribe_to_topic(
                str(user_id), message.topic
            )

            response = TopicSubscribedResponse(
                topic=message.topic,
                success=success,
                message=msg
            )
            await websocket.send_json(response.model_dump(mode='json'))

            logger.info(f"User {user_id} subscribed to topic {message.topic}: {success}")

        except Exception as e:
            logger.error(f"Error subscribing to topic: {e}")
            await self._send_error(websocket, "Failed to subscribe to topic")

    async def handle_unsubscribe_topic(
        self,
        websocket: WebSocket,
        user_id: int,
        message: UnsubscribeTopicMessage
    ) -> None:
        """Handle unsubscribe from topic"""
        try:
            if not self.notification_service:
                await self._send_error(websocket, "Notification service not available")
                return

            success, msg = await self.notification_service.unsubscribe_from_topic(
                str(user_id), message.topic
            )

            response = TopicUnsubscribedResponse(
                topic=message.topic,
                success=success,
                message=msg
            )
            await websocket.send_json(response.model_dump(mode='json'))

            logger.info(f"User {user_id} unsubscribed from topic {message.topic}: {success}")

        except Exception as e:
            logger.error(f"Error unsubscribing from topic: {e}")
            await self._send_error(websocket, "Failed to unsubscribe from topic")

    async def send_initial_state(
        self,
        websocket: WebSocket,
        user_id: int
    ) -> None:
        """
        Send initial notification state after authentication.
        Called when user connects to WebSocket.
        """
        try:
            # Get unread count
            unread = await self._get_unread_count(user_id)

            # Send unread count
            unread_response = UnreadCountResponse(unread_count=unread)
            await websocket.send_json(unread_response.model_dump(mode='json'))

            # Get notification settings
            if self.notification_service:
                settings = await self.notification_service.get_notification_settings(str(user_id))
                settings_response = NotificationSettingsResponse(settings=settings)
                await websocket.send_json(settings_response.model_dump(mode='json'))

            # Check DND status
            if self.notification_manager:
                is_dnd = self.notification_manager.is_dnd_active(user_id)
                state = self.notification_manager._user_states.get(user_id)
                # Safe access to dnd_until - check both state exists and has dnd_until attribute
                dnd_until = None
                if state is not None:
                    dnd_until = getattr(state, 'dnd_until', None)
                dnd_response = DNDStatusResponse(
                    enabled=is_dnd,
                    until=dnd_until
                )
                await websocket.send_json(dnd_response.model_dump(mode='json'))

            logger.debug(f"Sent initial notification state to user {user_id}")

        except Exception as e:
            logger.error(f"Error sending initial notification state: {e}")

    async def _get_unread_count(self, user_id: int) -> int:
        """Get unread notification count"""
        if self.notification_manager:
            return await self.notification_manager.get_unread_count(user_id)
        elif self.notification_service:
            _, _, unread = await self.notification_service.get_notification_history(
                str(user_id), limit=0, unread_only=True
            )
            return unread
        return 0

    async def _send_error(
        self,
        websocket: WebSocket,
        error: str,
        error_code: WebSocketErrorCode = WebSocketErrorCode.INTERNAL_ERROR
    ) -> None:
        """Send error response"""
        response = create_error_response(
            error=error,
            error_code=error_code,
            recoverable=True
        )
        try:
            await websocket.send_json(response.model_dump(mode='json'))
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")


# Global instance
notification_handler = WebSocketNotificationHandler()
