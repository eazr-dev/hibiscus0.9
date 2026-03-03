"""
Notification Models for Firebase Cloud Messaging
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications"""
    POLICY_RENEWAL = "policy_renewal"
    POLICY_EXPIRY = "policy_expiry"
    CLAIM_UPDATE = "claim_update"
    PAYMENT_REMINDER = "payment_reminder"
    PROTECTION_SCORE = "protection_score"
    NEW_RECOMMENDATION = "new_recommendation"
    PROMOTIONAL = "promotional"
    SYSTEM = "system"
    CHAT_MESSAGE = "chat_message"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


# ========================================
# Request Models
# ========================================

class RegisterDeviceRequest(BaseModel):
    """Request to register a device token"""
    user_id: str = Field(..., description="User ID")
    fcm_token: str = Field(..., description="Firebase Cloud Messaging device token")
    device_type: str = Field(default="mobile", description="Device type: mobile, web, ios, android")
    device_name: Optional[str] = Field(None, description="Device name/model")
    app_version: Optional[str] = Field(None, description="App version")


class UnregisterDeviceRequest(BaseModel):
    """Request to unregister a device token"""
    user_id: str = Field(..., description="User ID")
    fcm_token: str = Field(..., description="FCM token to unregister")


class LogoutAllDevicesRequest(BaseModel):
    """Request to logout from all devices"""
    user_id: str = Field(..., description="User ID")


class SendNotificationRequest(BaseModel):
    """Request to send a notification to a user"""
    user_id: str = Field(..., description="Target user ID")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    notification_type: NotificationType = Field(default=NotificationType.SYSTEM)
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    data: Optional[Dict[str, str]] = Field(default=None, description="Additional data payload")
    image_url: Optional[str] = Field(None, description="Image URL for rich notification")


class SendBulkNotificationRequest(BaseModel):
    """Request to send notification to multiple users"""
    user_ids: List[str] = Field(..., description="List of target user IDs")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    notification_type: NotificationType = Field(default=NotificationType.SYSTEM)
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    data: Optional[Dict[str, str]] = Field(default=None, description="Additional data payload")


class SendTopicNotificationRequest(BaseModel):
    """Request to send notification to a topic"""
    topic: str = Field(..., description="Topic name")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    notification_type: NotificationType = Field(default=NotificationType.SYSTEM)
    data: Optional[Dict[str, str]] = Field(default=None, description="Additional data payload")


class SubscribeTopicRequest(BaseModel):
    """Request to subscribe to a topic"""
    user_id: str = Field(..., description="User ID")
    topic: str = Field(..., description="Topic to subscribe to")


class UnsubscribeTopicRequest(BaseModel):
    """Request to unsubscribe from a topic"""
    user_id: str = Field(..., description="User ID")
    topic: str = Field(..., description="Topic to unsubscribe from")


class MarkNotificationReadRequest(BaseModel):
    """Request to mark notification as read"""
    user_id: str = Field(..., description="User ID")
    notification_id: str = Field(..., description="Notification ID to mark as read")


class MarkAllNotificationsReadRequest(BaseModel):
    """Request to mark all notifications as read"""
    user_id: str = Field(..., description="User ID")


class NotificationSettingsUpdateRequest(BaseModel):
    """Request to update notification settings - supports partial updates"""
    user_id: str = Field(..., description="User ID")
    policy_renewal: Optional[bool] = None
    policy_expiry: Optional[bool] = None
    claim_updates: Optional[bool] = None
    payment_reminders: Optional[bool] = None
    protection_score: Optional[bool] = None
    recommendations: Optional[bool] = None
    promotional: Optional[bool] = None


# ========================================
# Response Models
# ========================================

class NotificationResponse(BaseModel):
    """Response for notification operations"""
    success: bool
    message: str
    message_id: Optional[str] = None
    failed_tokens: Optional[List[str]] = None


class DeviceRegistrationResponse(BaseModel):
    """Response for device registration"""
    success: bool
    message: str
    device_id: Optional[str] = None


class NotificationHistoryItem(BaseModel):
    """Single notification history item"""
    notification_id: str
    title: str
    body: str
    notification_type: NotificationType
    sent_at: datetime
    read: bool = False
    read_at: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None


class NotificationHistoryResponse(BaseModel):
    """Response for notification history"""
    success: bool
    notifications: List[NotificationHistoryItem]
    total: int
    unread_count: int


class NotificationSettingsResponse(BaseModel):
    """Response for notification settings"""
    success: bool
    settings: Dict[str, bool]


# ========================================
# MongoDB Document Models
# ========================================

class DeviceToken(BaseModel):
    """Device token document for MongoDB"""
    user_id: str
    fcm_token: str
    device_type: str
    device_name: Optional[str] = None
    app_version: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None


class NotificationLog(BaseModel):
    """Notification log document for MongoDB"""
    user_id: str
    title: str
    body: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivered: bool = False
    read: bool = False
    read_at: Optional[datetime] = None
    fcm_message_id: Optional[str] = None
    error: Optional[str] = None


class UserNotificationSettings(BaseModel):
    """User notification settings document"""
    user_id: str
    policy_renewal: bool = True
    policy_expiry: bool = True
    claim_updates: bool = True
    payment_reminders: bool = True
    protection_score: bool = True
    recommendations: bool = True
    promotional: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)
