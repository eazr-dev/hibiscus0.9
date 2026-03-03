"""
Presence Manager for EAZR Chat WebSocket
Manages user presence status (online/offline/away).
"""

from typing import Dict, Set, Optional, List, Any
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from websocket.models import PresenceStatus
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class PresenceInfo:
    """User presence information"""
    user_id: int
    status: PresenceStatus = PresenceStatus.OFFLINE
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    connected_devices: Set[str] = field(default_factory=set)
    user_name: Optional[str] = None
    custom_status: Optional[str] = None


class PresenceManager:
    """
    Manages user presence status (online/offline/away).

    Features:
    - Track user presence across multiple devices
    - Auto-away after inactivity
    - Broadcast presence changes to interested parties
    - Device-level tracking (user is offline only when ALL devices disconnect)
    """

    def __init__(
        self,
        redis_client=None,
        away_timeout_minutes: int = 5,
        offline_grace_period_seconds: int = 30
    ):
        """
        Initialize presence manager.

        Args:
            redis_client: Optional Redis for distributed state
            away_timeout_minutes: Minutes of inactivity before auto-away
            offline_grace_period_seconds: Seconds to wait before marking offline
                                          (allows for brief reconnections)
        """
        # User presence: user_id -> PresenceInfo
        self._presence: Dict[int, PresenceInfo] = {}

        # Pending offline transitions: user_id -> scheduled_time
        # Used for grace period before going offline
        self._pending_offline: Dict[int, datetime] = {}

        # Presence change callbacks: List of async functions to call on change
        self._callbacks: List[Any] = []

        self._redis = redis_client
        self._away_timeout = timedelta(minutes=away_timeout_minutes)
        self._offline_grace_period = timedelta(seconds=offline_grace_period_seconds)
        self._lock = asyncio.Lock()

    async def set_online(
        self,
        user_id: int,
        device_id: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Mark user as online from a specific device.

        Args:
            user_id: User identifier
            device_id: Device identifier
            user_name: Optional user display name

        Returns:
            True if status changed (was not online before)
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            status_changed = False

            # Cancel any pending offline transition
            if user_id in self._pending_offline:
                del self._pending_offline[user_id]

            if user_id not in self._presence:
                # New user coming online
                self._presence[user_id] = PresenceInfo(
                    user_id=user_id,
                    status=PresenceStatus.ONLINE,
                    last_seen=now,
                    last_activity=now,
                    connected_devices={device_id},
                    user_name=user_name
                )
                status_changed = True
                logger.info(f"User {user_id} is now ONLINE (device: {device_id})")
            else:
                presence = self._presence[user_id]
                old_status = presence.status

                # Add device and update status
                presence.connected_devices.add(device_id)
                presence.status = PresenceStatus.ONLINE
                presence.last_seen = now
                presence.last_activity = now

                if user_name and not presence.user_name:
                    presence.user_name = user_name

                status_changed = old_status != PresenceStatus.ONLINE
                if status_changed:
                    logger.info(
                        f"User {user_id} is now ONLINE "
                        f"(was {old_status.value}, devices: {len(presence.connected_devices)})"
                    )

            # Notify callbacks if status changed
            if status_changed:
                await self._notify_presence_change(user_id, PresenceStatus.ONLINE)

            return status_changed

    async def set_offline(
        self,
        user_id: int,
        device_id: str,
        immediate: bool = False
    ) -> bool:
        """
        Mark user as offline from a specific device.
        Only goes offline if no other devices are connected.

        Args:
            user_id: User identifier
            device_id: Device identifier
            immediate: If True, skip grace period

        Returns:
            True if status changed to offline
        """
        async with self._lock:
            if user_id not in self._presence:
                return False

            presence = self._presence[user_id]
            now = datetime.now(timezone.utc)

            # Remove this device
            presence.connected_devices.discard(device_id)
            presence.last_seen = now

            # If other devices still connected, stay online
            if presence.connected_devices:
                logger.debug(
                    f"User {user_id} device {device_id} disconnected, "
                    f"but {len(presence.connected_devices)} device(s) still connected"
                )
                return False

            # No devices connected
            if immediate:
                # Immediate offline
                old_status = presence.status
                presence.status = PresenceStatus.OFFLINE
                logger.info(f"User {user_id} is now OFFLINE (immediate)")

                if old_status != PresenceStatus.OFFLINE:
                    await self._notify_presence_change(user_id, PresenceStatus.OFFLINE)
                return True
            else:
                # Schedule offline transition with grace period
                self._pending_offline[user_id] = now + self._offline_grace_period
                logger.debug(
                    f"User {user_id} scheduled for offline in "
                    f"{self._offline_grace_period.seconds}s"
                )
                return False

    async def process_pending_offline(self) -> List[int]:
        """
        Process pending offline transitions.
        Should be called periodically (e.g., every 10 seconds).

        Returns:
            List of user_ids that transitioned to offline
        """
        now = datetime.now(timezone.utc)
        transitioned = []

        async with self._lock:
            for user_id, scheduled_time in list(self._pending_offline.items()):
                if now >= scheduled_time:
                    # Check if user reconnected
                    presence = self._presence.get(user_id)
                    if presence and not presence.connected_devices:
                        old_status = presence.status
                        presence.status = PresenceStatus.OFFLINE
                        presence.last_seen = now

                        if old_status != PresenceStatus.OFFLINE:
                            logger.info(f"User {user_id} is now OFFLINE (grace period expired)")
                            transitioned.append(user_id)

                    del self._pending_offline[user_id]

        # Notify outside lock
        for user_id in transitioned:
            await self._notify_presence_change(user_id, PresenceStatus.OFFLINE)

        return transitioned

    async def set_away(self, user_id: int) -> bool:
        """
        Mark user as away.

        Args:
            user_id: User identifier

        Returns:
            True if status changed
        """
        async with self._lock:
            if user_id not in self._presence:
                return False

            presence = self._presence[user_id]
            old_status = presence.status

            # Can only go away if currently online
            if old_status == PresenceStatus.ONLINE:
                presence.status = PresenceStatus.AWAY
                presence.last_seen = datetime.now(timezone.utc)
                logger.info(f"User {user_id} is now AWAY")

                await self._notify_presence_change(user_id, PresenceStatus.AWAY)
                return True

            return False

    async def set_status(
        self,
        user_id: int,
        status: PresenceStatus,
        custom_status: Optional[str] = None
    ) -> bool:
        """
        Manually set user presence status.

        Args:
            user_id: User identifier
            status: New status
            custom_status: Optional custom status message

        Returns:
            True if status changed
        """
        async with self._lock:
            if user_id not in self._presence:
                return False

            presence = self._presence[user_id]
            old_status = presence.status

            # Don't allow setting online if no devices connected
            if status == PresenceStatus.ONLINE and not presence.connected_devices:
                return False

            presence.status = status
            presence.last_seen = datetime.now(timezone.utc)
            if custom_status is not None:
                presence.custom_status = custom_status

            if old_status != status:
                logger.info(f"User {user_id} status changed: {old_status.value} -> {status.value}")
                await self._notify_presence_change(user_id, status)
                return True

            return False

    async def get_status(self, user_id: int) -> PresenceStatus:
        """
        Get current presence status for a user.

        Args:
            user_id: User identifier

        Returns:
            PresenceStatus (defaults to OFFLINE if user not tracked)
        """
        presence = self._presence.get(user_id)
        return presence.status if presence else PresenceStatus.OFFLINE

    async def get_presence_info(self, user_id: int) -> Optional[PresenceInfo]:
        """
        Get full presence info for a user.

        Args:
            user_id: User identifier

        Returns:
            PresenceInfo or None if not tracked
        """
        return self._presence.get(user_id)

    async def get_last_seen(self, user_id: int) -> Optional[datetime]:
        """
        Get last activity timestamp for a user.

        Args:
            user_id: User identifier

        Returns:
            Last seen datetime or None if not tracked
        """
        presence = self._presence.get(user_id)
        return presence.last_seen if presence else None

    async def update_activity(self, user_id: int) -> None:
        """
        Update last activity timestamp (e.g., on message).
        Also resets away status back to online.

        Args:
            user_id: User identifier
        """
        async with self._lock:
            if user_id in self._presence:
                presence = self._presence[user_id]
                presence.last_activity = datetime.now(timezone.utc)
                presence.last_seen = datetime.now(timezone.utc)

                # Reset away to online on activity
                if presence.status == PresenceStatus.AWAY:
                    presence.status = PresenceStatus.ONLINE
                    await self._notify_presence_change(user_id, PresenceStatus.ONLINE)

    async def check_auto_away(self) -> Set[int]:
        """
        Check for users who should be marked as away due to inactivity.
        Should be called periodically (e.g., every minute).

        Returns:
            Set of user_ids that were marked away
        """
        now = datetime.now(timezone.utc)
        marked_away = set()

        async with self._lock:
            for user_id, presence in self._presence.items():
                if presence.status != PresenceStatus.ONLINE:
                    continue

                elapsed = now - presence.last_activity
                if elapsed >= self._away_timeout:
                    presence.status = PresenceStatus.AWAY
                    marked_away.add(user_id)
                    logger.info(f"User {user_id} auto-marked as AWAY (inactive for {elapsed})")

        # Notify outside lock
        for user_id in marked_away:
            await self._notify_presence_change(user_id, PresenceStatus.AWAY)

        return marked_away

    def get_online_users(self) -> Set[int]:
        """Get set of all currently online user IDs"""
        return {
            user_id
            for user_id, presence in self._presence.items()
            if presence.status == PresenceStatus.ONLINE
        }

    def get_all_presence(self) -> Dict[int, PresenceInfo]:
        """Get all presence information"""
        return self._presence.copy()

    def get_stats(self) -> Dict[str, Any]:
        """Get presence statistics"""
        online_count = sum(
            1 for p in self._presence.values()
            if p.status == PresenceStatus.ONLINE
        )
        away_count = sum(
            1 for p in self._presence.values()
            if p.status == PresenceStatus.AWAY
        )
        offline_count = sum(
            1 for p in self._presence.values()
            if p.status == PresenceStatus.OFFLINE
        )

        return {
            "total_tracked": len(self._presence),
            "online": online_count,
            "away": away_count,
            "offline": offline_count,
            "pending_offline": len(self._pending_offline)
        }

    def register_callback(self, callback) -> None:
        """
        Register a callback for presence changes.

        Callback signature: async def callback(user_id: int, status: PresenceStatus)
        """
        self._callbacks.append(callback)

    def unregister_callback(self, callback) -> None:
        """Unregister a presence change callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def _notify_presence_change(
        self,
        user_id: int,
        status: PresenceStatus
    ) -> None:
        """Notify all registered callbacks of presence change"""
        for callback in self._callbacks:
            try:
                await callback(user_id, status)
            except Exception as e:
                logger.error(f"Presence callback error: {e}")

    def cleanup_inactive_users(self, max_offline_hours: int = 24) -> int:
        """
        Remove users who have been offline for too long.

        Args:
            max_offline_hours: Hours after which to remove offline users

        Returns:
            Number of users removed
        """
        now = datetime.now(timezone.utc)
        threshold = timedelta(hours=max_offline_hours)
        to_remove = []

        for user_id, presence in self._presence.items():
            if presence.status == PresenceStatus.OFFLINE:
                elapsed = now - presence.last_seen
                if elapsed >= threshold:
                    to_remove.append(user_id)

        for user_id in to_remove:
            del self._presence[user_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} inactive users from presence tracking")

        return len(to_remove)


# Global presence manager instance — pass async Redis for distributed state
try:
    from database_storage.simple_redis_config import async_redis_client as _async_redis
except ImportError:
    _async_redis = None

presence_manager = PresenceManager(redis_client=_async_redis)
