"""
Notification Service for Firebase Cloud Messaging
Handles sending push notifications, managing device tokens, and notification history
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from bson import ObjectId

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

from database_storage.firebase_config import is_firebase_available, get_firebase_app
from database_storage.mongodb_chat_manager import insurance_db
from models.notification import (
    NotificationType,
    NotificationPriority,
    DeviceToken,
    NotificationLog,
    UserNotificationSettings,
)

logger = logging.getLogger(__name__)


def get_ist_now():
    """Get current time in IST (Indian Standard Time - UTC+5:30)"""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None)


class NotificationService:
    """Service for managing push notifications via Firebase Cloud Messaging"""

    def __init__(self):
        self.device_tokens_collection = insurance_db["device_tokens"]
        self.notification_logs_collection = insurance_db["notification_logs"]
        self.notification_settings_collection = insurance_db["notification_settings"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure required indexes exist"""
        try:
            # Device tokens indexes
            self.device_tokens_collection.create_index("user_id")
            self.device_tokens_collection.create_index("fcm_token", unique=True)
            self.device_tokens_collection.create_index([("user_id", 1), ("is_active", 1)])

            # Notification logs indexes
            self.notification_logs_collection.create_index("user_id")
            self.notification_logs_collection.create_index([("user_id", 1), ("sent_at", -1)])
            self.notification_logs_collection.create_index([("user_id", 1), ("read", 1)])

            # Notification settings index
            self.notification_settings_collection.create_index("user_id", unique=True)

            logger.info("Notification indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating notification indexes: {e}")

    # ========================================
    # Device Token Management
    # ========================================

    async def register_device_token(
        self,
        user_id: str,
        fcm_token: str,
        device_type: str = "mobile",
        device_name: Optional[str] = None,
        app_version: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """Register or update a device token for a user"""
        try:
            now = get_ist_now()

            # Check if token already exists
            existing = self.device_tokens_collection.find_one({"fcm_token": fcm_token})

            if existing:
                # Update existing token
                self.device_tokens_collection.update_one(
                    {"fcm_token": fcm_token},
                    {
                        "$set": {
                            "user_id": user_id,
                            "device_type": device_type,
                            "device_name": device_name,
                            "app_version": app_version,
                            "is_active": True,
                            "updated_at": now,
                        }
                    },
                )
                device_id = str(existing["_id"])
                logger.info(f"Updated device token for user {user_id}")
            else:
                # Insert new token
                device_doc = {
                    "user_id": user_id,
                    "fcm_token": fcm_token,
                    "device_type": device_type,
                    "device_name": device_name,
                    "app_version": app_version,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                    "last_used_at": None,
                }
                result = self.device_tokens_collection.insert_one(device_doc)
                device_id = str(result.inserted_id)
                logger.info(f"Registered new device token for user {user_id}")

            return True, "Device registered successfully", device_id

        except Exception as e:
            logger.error(f"Error registering device token: {e}")
            return False, str(e), None

    async def get_user_device_tokens(self, user_id: str) -> List[str]:
        """Get all active FCM tokens for a user"""
        try:
            tokens = self.device_tokens_collection.find(
                {"user_id": user_id, "is_active": True},
                {"fcm_token": 1}
            )
            return [t["fcm_token"] for t in tokens]
        except Exception as e:
            logger.error(f"Error getting device tokens: {e}")
            return []

    async def deactivate_device_token(self, fcm_token: str) -> bool:
        """Deactivate a device token (e.g., on logout or token refresh)"""
        try:
            result = self.device_tokens_collection.update_one(
                {"fcm_token": fcm_token},
                {"$set": {"is_active": False, "updated_at": get_ist_now()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error deactivating device token: {e}")
            return False

    async def deactivate_user_devices(self, user_id: str) -> int:
        """Deactivate all device tokens for a user (on logout from all devices)"""
        try:
            result = self.device_tokens_collection.update_many(
                {"user_id": user_id},
                {"$set": {"is_active": False, "updated_at": get_ist_now()}}
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"Error deactivating user devices: {e}")
            return 0

    # ========================================
    # Send Notifications
    # ========================================

    async def send_notification_to_user(
        self,
        user_id: str,
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str], List[str]]:
        """Send notification to all devices of a user"""

        if not is_firebase_available():
            return False, "Firebase not available", None, []

        # Check user notification settings
        if not await self._check_notification_allowed(user_id, notification_type):
            return False, "Notification type disabled by user", None, []

        # Get user's device tokens
        tokens = await self.get_user_device_tokens(user_id)
        if not tokens:
            return False, "No registered devices", None, []

        # Prepare notification data
        notification_data = data or {}
        notification_data["notification_type"] = notification_type.value
        notification_data["timestamp"] = get_ist_now().isoformat()

        # Build FCM message
        android_config = messaging.AndroidConfig(
            priority="high" if priority == NotificationPriority.HIGH else "normal",
            notification=messaging.AndroidNotification(
                title=title,
                body=body,
                icon="ic_notification",
                color="#4A90D9",
                image=image_url,
                channel_id="eazr_notifications",
            ),
        )

        apns_config = messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    alert=messaging.ApsAlert(title=title, body=body),
                    badge=1,
                    sound="default",
                    mutable_content=True,
                ),
            ),
        )

        # Send to multiple devices
        message = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(
                title=title,
                body=body,
                image=image_url,
            ),
            data=notification_data,
            android=android_config,
            apns=apns_config,
        )

        try:
            response = messaging.send_each_for_multicast(message)

            # Process results
            failed_tokens = []
            success_count = response.success_count
            failure_count = response.failure_count

            for idx, send_response in enumerate(response.responses):
                if not send_response.success:
                    failed_tokens.append(tokens[idx])
                    # Deactivate invalid tokens
                    if send_response.exception and isinstance(
                        send_response.exception, messaging.UnregisteredError
                    ):
                        await self.deactivate_device_token(tokens[idx])

            # Log notification
            message_id = await self._log_notification(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=notification_type,
                priority=priority,
                data=data,
                image_url=image_url,
                delivered=success_count > 0,
            )

            logger.info(
                f"Notification sent to user {user_id}: "
                f"{success_count} success, {failure_count} failed"
            )

            return (
                success_count > 0,
                f"Sent to {success_count} devices, {failure_count} failed",
                message_id,
                failed_tokens,
            )

        except FirebaseError as e:
            logger.error(f"Firebase error sending notification: {e}")
            return False, str(e), None, []
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False, str(e), None, []

    async def send_notification_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
        data: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """Send notification to a topic"""

        if not is_firebase_available():
            return False, "Firebase not available", None

        notification_data = data or {}
        notification_data["notification_type"] = notification_type.value
        notification_data["timestamp"] = get_ist_now().isoformat()

        message = messaging.Message(
            topic=topic,
            notification=messaging.Notification(title=title, body=body),
            data=notification_data,
        )

        try:
            message_id = messaging.send(message)
            logger.info(f"Topic notification sent: {topic}, message_id: {message_id}")
            return True, "Notification sent", message_id
        except FirebaseError as e:
            logger.error(f"Firebase error: {e}")
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error sending topic notification: {e}")
            return False, str(e), None

    async def subscribe_to_topic(
        self, user_id: str, topic: str
    ) -> Tuple[bool, str]:
        """Subscribe user's devices to a topic"""

        if not is_firebase_available():
            return False, "Firebase not available"

        tokens = await self.get_user_device_tokens(user_id)
        if not tokens:
            return False, "No registered devices"

        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            success = response.success_count > 0
            logger.info(f"Subscribed {response.success_count} devices to topic {topic}")
            return success, f"Subscribed {response.success_count} devices"
        except Exception as e:
            logger.error(f"Error subscribing to topic: {e}")
            return False, str(e)

    async def unsubscribe_from_topic(
        self, user_id: str, topic: str
    ) -> Tuple[bool, str]:
        """Unsubscribe user's devices from a topic"""

        if not is_firebase_available():
            return False, "Firebase not available"

        tokens = await self.get_user_device_tokens(user_id)
        if not tokens:
            return False, "No registered devices"

        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            success = response.success_count > 0
            logger.info(f"Unsubscribed {response.success_count} devices from topic {topic}")
            return success, f"Unsubscribed {response.success_count} devices"
        except Exception as e:
            logger.error(f"Error unsubscribing from topic: {e}")
            return False, str(e)

    # ========================================
    # Notification History
    # ========================================

    async def get_notification_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> Tuple[List[Dict], int, int]:
        """Get notification history for a user"""
        try:
            query = {"user_id": user_id}
            if unread_only:
                query["read"] = False

            total = self.notification_logs_collection.count_documents({"user_id": user_id})
            unread_count = self.notification_logs_collection.count_documents(
                {"user_id": user_id, "read": False}
            )

            notifications = list(
                self.notification_logs_collection.find(query)
                .sort("sent_at", -1)
                .skip(offset)
                .limit(limit)
            )

            # Convert ObjectId to string
            for n in notifications:
                n["notification_id"] = str(n.pop("_id"))

            return notifications, total, unread_count

        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return [], 0, 0

    async def mark_notification_read(
        self, user_id: str, notification_id: str
    ) -> bool:
        """Mark a notification as read"""
        try:
            result = self.notification_logs_collection.update_one(
                {"_id": ObjectId(notification_id), "user_id": user_id},
                {"$set": {"read": True, "read_at": get_ist_now()}},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error marking notification read: {e}")
            return False

    async def mark_all_notifications_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        try:
            result = self.notification_logs_collection.update_many(
                {"user_id": user_id, "read": False},
                {"$set": {"read": True, "read_at": get_ist_now()}},
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"Error marking all notifications read: {e}")
            return 0

    # ========================================
    # Notification Settings
    # ========================================

    async def get_notification_settings(self, user_id: str) -> Dict[str, bool]:
        """Get notification settings for a user"""
        try:
            settings = self.notification_settings_collection.find_one({"user_id": user_id})
            if settings:
                return {
                    "policy_renewal": settings.get("policy_renewal", True),
                    "policy_expiry": settings.get("policy_expiry", True),
                    "claim_updates": settings.get("claim_updates", True),
                    "payment_reminders": settings.get("payment_reminders", True),
                    "protection_score": settings.get("protection_score", True),
                    "recommendations": settings.get("recommendations", True),
                    "promotional": settings.get("promotional", False),
                }
            # Return defaults
            return {
                "policy_renewal": True,
                "policy_expiry": True,
                "claim_updates": True,
                "payment_reminders": True,
                "protection_score": True,
                "recommendations": True,
                "promotional": False,
            }
        except Exception as e:
            logger.error(f"Error getting notification settings: {e}")
            return {}

    async def update_notification_settings(
        self, user_id: str, settings: Dict[str, bool]
    ) -> bool:
        """Update notification settings for a user"""
        try:
            # Create a copy to avoid mutating the input dict
            update_doc = dict(settings)
            update_doc["user_id"] = user_id
            update_doc["updated_at"] = get_ist_now()

            result = self.notification_settings_collection.update_one(
                {"user_id": user_id},
                {"$set": update_doc},
                upsert=True,
            )
            return True
        except Exception as e:
            logger.error(f"Error updating notification settings: {e}")
            return False

    # ========================================
    # Internal Helpers
    # ========================================

    async def _check_notification_allowed(
        self, user_id: str, notification_type: NotificationType
    ) -> bool:
        """Check if a notification type is allowed for the user"""
        try:
            settings = await self.get_notification_settings(user_id)

            type_to_setting = {
                NotificationType.POLICY_RENEWAL: "policy_renewal",
                NotificationType.POLICY_EXPIRY: "policy_expiry",
                NotificationType.CLAIM_UPDATE: "claim_updates",
                NotificationType.PAYMENT_REMINDER: "payment_reminders",
                NotificationType.PROTECTION_SCORE: "protection_score",
                NotificationType.NEW_RECOMMENDATION: "recommendations",
                NotificationType.PROMOTIONAL: "promotional",
                NotificationType.SYSTEM: None,  # Always allowed
                NotificationType.CHAT_MESSAGE: None,  # Always allowed
            }

            setting_key = type_to_setting.get(notification_type)
            if setting_key is None:
                return True  # System notifications always allowed

            return settings.get(setting_key, True)

        except Exception as e:
            logger.error(f"Error checking notification settings: {e}")
            return True  # Default to allowed on error

    async def _log_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
        delivered: bool = False,
        fcm_message_id: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[str]:
        """Log a notification to the database"""
        try:
            log_doc = {
                "user_id": user_id,
                "title": title,
                "body": body,
                "notification_type": notification_type.value,
                "priority": priority.value,
                "data": data,
                "image_url": image_url,
                "sent_at": get_ist_now(),
                "delivered": delivered,
                "read": False,
                "read_at": None,
                "fcm_message_id": fcm_message_id,
                "error": error,
            }
            result = self.notification_logs_collection.insert_one(log_doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
            return None


# Singleton instance
notification_service = NotificationService()
