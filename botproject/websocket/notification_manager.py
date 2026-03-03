"""
Advanced WebSocket Notification Manager for EAZR Chat
Real-time push notifications with FCM integration, delivery tracking, and preferences.
"""

from typing import Dict, Set, Optional, List, Any, Callable, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
import json

from models.notification import (
    NotificationType,
    NotificationPriority,
)

logger = logging.getLogger(__name__)


class NotificationDeliveryStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"
    DELIVERED_WS = "delivered_ws"      # Delivered via WebSocket
    DELIVERED_FCM = "delivered_fcm"    # Delivered via FCM
    DELIVERED_BOTH = "delivered_both"  # Both channels
    FAILED = "failed"
    EXPIRED = "expired"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    WEBSOCKET = "websocket"
    FCM = "fcm"
    BOTH = "both"


@dataclass
class PendingNotification:
    """Notification waiting for delivery"""
    notification_id: str
    user_id: int
    title: str
    body: str
    notification_type: NotificationType
    priority: NotificationPriority
    data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    action_url: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    status: NotificationDeliveryStatus = NotificationDeliveryStatus.PENDING
    ws_delivered: bool = False
    fcm_delivered: bool = False


@dataclass
class UserNotificationState:
    """User's notification state"""
    user_id: int
    is_online: bool = False
    last_seen: Optional[datetime] = None
    connected_devices: Set[str] = field(default_factory=set)
    pending_notifications: List[str] = field(default_factory=list)  # notification_ids
    unread_count: int = 0
    dnd_enabled: bool = False  # Do Not Disturb
    dnd_until: Optional[datetime] = None


class WebSocketNotificationManager:
    """
    Advanced notification manager with WebSocket + FCM dual delivery.

    Features:
    - Real-time WebSocket delivery for online users
    - FCM fallback for offline users or important notifications
    - Notification queuing and retry
    - Delivery receipts and tracking
    - User preferences and DND support
    - Unread count sync across devices
    - Batch notification support
    """

    def __init__(
        self,
        connection_manager=None,
        notification_service=None,
        max_queue_size: int = 1000,
        notification_ttl_minutes: int = 60,
        retry_delay_seconds: int = 30
    ):
        """
        Initialize notification manager.

        Args:
            connection_manager: WebSocket connection manager
            notification_service: FCM notification service
            max_queue_size: Maximum pending notifications
            notification_ttl_minutes: Minutes before notification expires
            retry_delay_seconds: Delay between retries
        """
        # Will be injected lazily
        self._connection_manager = connection_manager
        self._notification_service = notification_service

        # Pending notifications: notification_id -> PendingNotification
        self._pending: Dict[str, PendingNotification] = {}

        # User states: user_id -> UserNotificationState
        self._user_states: Dict[int, UserNotificationState] = {}

        # Delivery callbacks: notification_type -> callback functions
        self._delivery_callbacks: Dict[str, List[Callable]] = {}

        # Configuration
        self._max_queue_size = max_queue_size
        self._notification_ttl = timedelta(minutes=notification_ttl_minutes)
        self._retry_delay = timedelta(seconds=retry_delay_seconds)

        # Background task
        self._process_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    def set_connection_manager(self, manager) -> None:
        """Inject connection manager dependency"""
        self._connection_manager = manager

    def set_notification_service(self, service) -> None:
        """Inject FCM notification service dependency"""
        self._notification_service = service

    @property
    def connection_manager(self):
        """Lazy load connection manager — uses the module-level singleton"""
        if self._connection_manager is None:
            try:
                from websocket.connection_manager import connection_manager as _cm
                self._connection_manager = _cm
            except ImportError:
                logger.warning("Connection manager not available")
        return self._connection_manager

    @property
    def notification_service(self):
        """Lazy load notification service"""
        if self._notification_service is None:
            try:
                from services.notification_service import notification_service
                self._notification_service = notification_service
            except ImportError:
                logger.warning("FCM notification service not available")
        return self._notification_service

    # ============= User State Management =============

    async def user_connected(
        self,
        user_id: int,
        device_id: str
    ) -> int:
        """
        Handle user connection - mark online and deliver pending notifications.

        Returns:
            Number of pending notifications delivered
        """
        async with self._lock:
            if user_id not in self._user_states:
                self._user_states[user_id] = UserNotificationState(user_id=user_id)

            state = self._user_states[user_id]
            state.is_online = True
            state.last_seen = datetime.now(timezone.utc)
            state.connected_devices.add(device_id)

            # Clear DND if expired
            if state.dnd_until and datetime.now(timezone.utc) > state.dnd_until:
                state.dnd_enabled = False
                state.dnd_until = None

        # Deliver pending notifications
        delivered = await self._deliver_pending_for_user(user_id)

        logger.info(f"User {user_id} connected (device: {device_id}), delivered {delivered} pending notifications")
        return delivered

    async def user_disconnected(
        self,
        user_id: int,
        device_id: str
    ) -> None:
        """Handle user disconnection from a device"""
        async with self._lock:
            if user_id not in self._user_states:
                return

            state = self._user_states[user_id]
            state.connected_devices.discard(device_id)
            state.last_seen = datetime.now(timezone.utc)

            # Only mark offline if no devices connected
            if not state.connected_devices:
                state.is_online = False
                logger.info(f"User {user_id} is now offline")
            else:
                logger.debug(f"User {user_id} device {device_id} disconnected, {len(state.connected_devices)} still online")

    def is_user_online(self, user_id: int) -> bool:
        """Check if user is currently online"""
        state = self._user_states.get(user_id)
        return state.is_online if state else False

    # ============= Notification Sending =============

    async def send_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
        action_url: Optional[str] = None,
        channel: NotificationChannel = NotificationChannel.BOTH,
        bypass_dnd: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Send notification to a user via best available channel.

        Args:
            user_id: Target user
            title: Notification title
            body: Notification body
            notification_type: Type of notification
            priority: Priority level
            data: Additional data payload
            image_url: Image URL for rich notifications
            action_url: URL for action button
            channel: Delivery channel preference
            bypass_dnd: Bypass Do Not Disturb mode

        Returns:
            Tuple of (success, message, notification_id)
        """
        # Check DND
        state = self._user_states.get(user_id)
        if state and state.dnd_enabled and not bypass_dnd:
            if priority != NotificationPriority.HIGH:
                return False, "User has Do Not Disturb enabled", None

        # Generate notification ID
        notification_id = f"notif_{user_id}_{datetime.now(timezone.utc).timestamp()}"

        # Create notification record
        notification = PendingNotification(
            notification_id=notification_id,
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            priority=priority,
            data=data or {},
            image_url=image_url,
            action_url=action_url,
            expires_at=datetime.now(timezone.utc) + self._notification_ttl
        )

        # Try WebSocket delivery first if user is online
        ws_success = False
        if channel in [NotificationChannel.WEBSOCKET, NotificationChannel.BOTH]:
            if self.is_user_online(user_id):
                ws_success = await self._deliver_via_websocket(notification)
                if ws_success:
                    notification.ws_delivered = True
                    notification.status = NotificationDeliveryStatus.DELIVERED_WS

        # FCM delivery (fallback or additional)
        fcm_success = False
        if channel in [NotificationChannel.FCM, NotificationChannel.BOTH]:
            # Send FCM if: not WS-only, and either WS failed or it's a priority notification
            should_send_fcm = (
                channel == NotificationChannel.FCM or
                (not ws_success) or
                (priority == NotificationPriority.HIGH)
            )

            if should_send_fcm and self.notification_service:
                fcm_success = await self._deliver_via_fcm(notification)
                if fcm_success:
                    notification.fcm_delivered = True
                    notification.status = (
                        NotificationDeliveryStatus.DELIVERED_BOTH
                        if notification.ws_delivered
                        else NotificationDeliveryStatus.DELIVERED_FCM
                    )

        # Queue if delivery failed
        if not ws_success and not fcm_success:
            await self._queue_notification(notification)
            return False, "Notification queued for delivery", notification_id

        # Update unread count
        await self._increment_unread(user_id)

        # Invoke callbacks
        await self._invoke_callbacks(notification)

        return True, "Notification delivered", notification_id

    async def send_notification_to_many(
        self,
        user_ids: List[int],
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send notification to multiple users concurrently.

        Returns:
            Summary with success_count, failed_count, queued_count
        """
        results = {
            "success_count": 0,
            "failed_count": 0,
            "queued_count": 0,
            "user_results": {}
        }

        # Build coroutines for all users
        coroutines = [
            self.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                priority=priority,
                data=data
            )
            for user_id in user_ids
        ]

        # Execute all sends concurrently with asyncio.gather
        gathered = await asyncio.gather(*coroutines, return_exceptions=True)

        for user_id, result in zip(user_ids, gathered):
            if isinstance(result, Exception):
                logger.error(f"Failed to send notification to {user_id}: {result}")
                results["failed_count"] += 1
                results["user_results"][str(user_id)] = {
                    "success": False,
                    "message": str(result),
                    "notification_id": None
                }
            else:
                success, message, notif_id = result
                results["user_results"][str(user_id)] = {
                    "success": success,
                    "message": message,
                    "notification_id": notif_id
                }
                if success:
                    results["success_count"] += 1
                elif "queued" in message.lower():
                    results["queued_count"] += 1
                else:
                    results["failed_count"] += 1

        return results

    # ============= Delivery Methods =============

    async def _deliver_via_websocket(self, notification: PendingNotification) -> bool:
        """Deliver notification via WebSocket"""
        if not self.connection_manager:
            return False

        try:
            message = {
                "type": "notification",
                "notification_id": notification.notification_id,
                "notification_type": notification.notification_type.value,
                "title": notification.title,
                "body": notification.body,
                "data": notification.data,
                "image_url": notification.image_url,
                "action_url": notification.action_url,
                "priority": notification.priority.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Broadcast to all user's connected devices
            delivered = await self.connection_manager.broadcast_to_user(
                user_id=notification.user_id,
                message=message
            )

            if delivered > 0:
                logger.debug(f"Delivered notification {notification.notification_id} to {delivered} WebSocket(s)")
                return True
            return False

        except Exception as e:
            logger.error(f"WebSocket delivery failed: {e}")
            return False

    async def _deliver_via_fcm(self, notification: PendingNotification) -> bool:
        """Deliver notification via Firebase Cloud Messaging"""
        if not self.notification_service:
            return False

        try:
            success, message, msg_id, failed = await self.notification_service.send_notification_to_user(
                user_id=str(notification.user_id),
                title=notification.title,
                body=notification.body,
                notification_type=notification.notification_type,
                priority=notification.priority,
                data={k: str(v) for k, v in (notification.data or {}).items()},
                image_url=notification.image_url
            )

            if success:
                logger.debug(f"Delivered notification {notification.notification_id} via FCM")
            return success

        except Exception as e:
            logger.error(f"FCM delivery failed: {e}")
            return False

    async def _deliver_pending_for_user(self, user_id: int) -> int:
        """Deliver all pending notifications for a user who just came online"""
        delivered_count = 0

        # Get user's pending notifications
        state = self._user_states.get(user_id)
        if not state or not state.pending_notifications:
            return 0

        pending_ids = list(state.pending_notifications)

        for notif_id in pending_ids:
            notification = self._pending.get(notif_id)
            if not notification:
                continue

            # Check expiry
            if notification.expires_at and datetime.now(timezone.utc) > notification.expires_at:
                notification.status = NotificationDeliveryStatus.EXPIRED
                await self._remove_pending(notif_id, user_id)
                continue

            # Try WebSocket delivery
            if await self._deliver_via_websocket(notification):
                notification.ws_delivered = True
                notification.status = NotificationDeliveryStatus.DELIVERED_WS
                delivered_count += 1
                await self._remove_pending(notif_id, user_id)

        return delivered_count

    # ============= Queue Management =============

    async def _queue_notification(self, notification: PendingNotification) -> bool:
        """Queue notification for later delivery"""
        async with self._lock:
            # Check queue size
            if len(self._pending) >= self._max_queue_size:
                # Remove oldest expired (inline, already under lock)
                self._cleanup_expired_unlocked()

                if len(self._pending) >= self._max_queue_size:
                    logger.warning(f"Notification queue full, dropping notification {notification.notification_id}")
                    return False

            # Add to pending
            self._pending[notification.notification_id] = notification

            # Track in user state
            if notification.user_id not in self._user_states:
                self._user_states[notification.user_id] = UserNotificationState(user_id=notification.user_id)

            self._user_states[notification.user_id].pending_notifications.append(notification.notification_id)

            logger.debug(f"Queued notification {notification.notification_id} for user {notification.user_id}")
            return True

    async def _remove_pending(self, notification_id: str, user_id: int) -> None:
        """Remove notification from pending queue (acquires lock)"""
        async with self._lock:
            self._remove_pending_unlocked(notification_id, user_id)

    def _remove_pending_unlocked(self, notification_id: str, user_id: int) -> None:
        """Remove notification from pending queue (caller must hold lock)"""
        if notification_id in self._pending:
            del self._pending[notification_id]

        state = self._user_states.get(user_id)
        if state and notification_id in state.pending_notifications:
            state.pending_notifications.remove(notification_id)

    def _cleanup_expired_unlocked(self) -> int:
        """Clean up expired notifications (caller must hold lock)"""
        now = datetime.now(timezone.utc)
        expired = []

        for notif_id, notif in self._pending.items():
            if notif.expires_at and now > notif.expires_at:
                expired.append((notif_id, notif.user_id))

        for notif_id, user_id in expired:
            self._remove_pending_unlocked(notif_id, user_id)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired notifications")

        return len(expired)

    async def _cleanup_expired(self) -> int:
        """Clean up expired notifications (acquires lock)"""
        async with self._lock:
            return self._cleanup_expired_unlocked()

    # ============= Unread Count Management =============

    async def _increment_unread(self, user_id: int) -> None:
        """Increment unread count for user"""
        async with self._lock:
            if user_id not in self._user_states:
                self._user_states[user_id] = UserNotificationState(user_id=user_id)
            self._user_states[user_id].unread_count += 1

        # Sync unread count to connected devices
        await self._sync_unread_count(user_id)

    async def mark_as_read(
        self,
        user_id: int,
        notification_id: Optional[str] = None
    ) -> int:
        """
        Mark notification(s) as read.

        Args:
            user_id: User ID
            notification_id: Specific notification ID, or None for all

        Returns:
            Number of notifications marked as read
        """
        async with self._lock:
            state = self._user_states.get(user_id)
            if not state:
                return 0

            if notification_id:
                # Mark single notification
                if state.unread_count > 0:
                    state.unread_count -= 1
                count = 1
            else:
                # Mark all as read
                count = state.unread_count
                state.unread_count = 0

        # Sync unread count
        await self._sync_unread_count(user_id)

        # Also update in notification service (MongoDB)
        if self.notification_service:
            try:
                if notification_id:
                    await self.notification_service.mark_notification_read(str(user_id), notification_id)
                else:
                    await self.notification_service.mark_all_notifications_read(str(user_id))
            except Exception as e:
                logger.error(f"Error updating notification read status in DB: {e}")

        return count

    async def get_unread_count(self, user_id: int) -> int:
        """Get unread notification count for user"""
        state = self._user_states.get(user_id)
        if state:
            return state.unread_count

        # Fetch from notification service if no state
        if self.notification_service:
            try:
                _, _, unread = await self.notification_service.get_notification_history(
                    str(user_id), limit=0, unread_only=True
                )
                return unread
            except Exception:
                pass

        return 0

    async def _sync_unread_count(self, user_id: int) -> None:
        """Sync unread count to all user's connected devices"""
        if not self.connection_manager:
            return

        state = self._user_states.get(user_id)
        unread = state.unread_count if state else 0

        message = {
            "type": "unread_count",
            "unread_count": unread,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self.connection_manager.broadcast_to_user(user_id, message)

    # ============= Do Not Disturb =============

    async def set_dnd(
        self,
        user_id: int,
        enabled: bool,
        duration_minutes: Optional[int] = None
    ) -> bool:
        """
        Set Do Not Disturb mode for user.

        Args:
            user_id: User ID
            enabled: Enable or disable DND
            duration_minutes: Optional duration (None = until manually disabled)
        """
        async with self._lock:
            if user_id not in self._user_states:
                self._user_states[user_id] = UserNotificationState(user_id=user_id)

            state = self._user_states[user_id]
            state.dnd_enabled = enabled

            if enabled and duration_minutes:
                state.dnd_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
            else:
                state.dnd_until = None

        logger.info(f"User {user_id} DND {'enabled' if enabled else 'disabled'}")
        return True

    def is_dnd_active(self, user_id: int) -> bool:
        """Check if user has DND active (read-only check, does not mutate state)"""
        state = self._user_states.get(user_id)
        if not state or not state.dnd_enabled:
            return False

        # Check if DND expired (read-only — actual cleanup happens in user_connected/set_dnd)
        if state.dnd_until and datetime.now(timezone.utc) > state.dnd_until:
            return False

        return True

    # ============= Callbacks =============

    def register_delivery_callback(
        self,
        notification_type: str,
        callback: Callable
    ) -> None:
        """
        Register callback for successful notification delivery.

        Callback signature: async def callback(notification: PendingNotification)
        """
        if notification_type not in self._delivery_callbacks:
            self._delivery_callbacks[notification_type] = []
        self._delivery_callbacks[notification_type].append(callback)

    def unregister_delivery_callback(
        self,
        notification_type: str,
        callback: Callable
    ) -> None:
        """Unregister a delivery callback"""
        if notification_type in self._delivery_callbacks:
            if callback in self._delivery_callbacks[notification_type]:
                self._delivery_callbacks[notification_type].remove(callback)

    async def _invoke_callbacks(self, notification: PendingNotification) -> None:
        """Invoke registered callbacks for delivered notification"""
        notif_type = notification.notification_type.value

        callbacks = self._delivery_callbacks.get(notif_type, [])
        for callback in callbacks:
            try:
                await callback(notification)
            except Exception as e:
                logger.error(f"Delivery callback error: {e}")

    # ============= Background Processing =============

    async def start_background_processor(self) -> None:
        """Start background task for processing pending notifications"""
        if self._process_task is None or self._process_task.done():
            self._process_task = asyncio.create_task(self._process_loop())
            logger.info("Notification background processor started")

    async def stop_background_processor(self) -> None:
        """Stop background processor"""
        if self._process_task and not self._process_task.done():
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
            logger.info("Notification background processor stopped")

    async def _process_loop(self) -> None:
        """Background loop to process pending notifications"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Clean up expired
                await self._cleanup_expired()

                # Retry pending for online users
                await self._retry_pending()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in notification processor: {e}")

    async def _retry_pending(self) -> None:
        """Retry delivery for pending notifications"""
        now = datetime.now(timezone.utc)

        for notif_id, notification in list(self._pending.items()):
            # Check if user is now online
            if not self.is_user_online(notification.user_id):
                continue

            # Check retry limit
            if notification.retry_count >= notification.max_retries:
                notification.status = NotificationDeliveryStatus.FAILED
                await self._remove_pending(notif_id, notification.user_id)
                continue

            # Try delivery
            notification.retry_count += 1
            if await self._deliver_via_websocket(notification):
                notification.ws_delivered = True
                notification.status = NotificationDeliveryStatus.DELIVERED_WS
                await self._remove_pending(notif_id, notification.user_id)
                await self._increment_unread(notification.user_id)

    # ============= Statistics =============

    def get_stats(self) -> Dict[str, Any]:
        """Get notification manager statistics"""
        online_users = sum(1 for s in self._user_states.values() if s.is_online)
        total_pending = len(self._pending)

        pending_by_priority = {
            "high": 0,
            "normal": 0,
            "low": 0
        }
        for notif in self._pending.values():
            pending_by_priority[notif.priority.value] += 1

        return {
            "total_users_tracked": len(self._user_states),
            "online_users": online_users,
            "pending_notifications": total_pending,
            "pending_by_priority": pending_by_priority,
            "max_queue_size": self._max_queue_size,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global instance
notification_manager = WebSocketNotificationManager()
