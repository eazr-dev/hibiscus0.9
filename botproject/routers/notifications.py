"""
Notification Router - API endpoints for push notifications

POST methods: user_id is passed in JSON body
GET methods: user_id is passed as query parameter

Note: Sending notifications is handled by the backend scheduler service.
Frontend only handles device registration and reading notifications.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from models.notification import (
    RegisterDeviceRequest,
    UnregisterDeviceRequest,
    LogoutAllDevicesRequest,
    SubscribeTopicRequest,
    UnsubscribeTopicRequest,
    MarkNotificationReadRequest,
    MarkAllNotificationsReadRequest,
    NotificationSettingsUpdateRequest,
    DeviceRegistrationResponse,
    NotificationHistoryResponse,
    NotificationSettingsResponse,
    NotificationHistoryItem,
)
from services.notification_service import notification_service
from database_storage.firebase_config import is_firebase_available

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ========================================
# Health Check
# ========================================

@router.get("/health")
async def notification_health():
    """Check notification service health"""
    return {
        "success": True,
        "firebase_available": is_firebase_available(),
        "service": "notification_service",
    }


# ========================================
# Device Registration (Frontend APIs)
# ========================================

@router.post("/register-device", response_model=DeviceRegistrationResponse)
async def register_device(request: RegisterDeviceRequest):
    """
    Register a device for push notifications.

    Call this endpoint when:
    - User logs in
    - App starts and user is authenticated
    - FCM token refreshes

    Request Body:
    ```json
    {
        "user_id": "282",
        "fcm_token": "fMhVK9xXQ8Gy7...",
        "device_type": "android",
        "device_name": "Samsung Galaxy S24",
        "app_version": "1.2.0"
    }
    ```
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    success, message, device_id = await notification_service.register_device_token(
        user_id=request.user_id,
        fcm_token=request.fcm_token,
        device_type=request.device_type,
        device_name=request.device_name,
        app_version=request.app_version,
    )

    return DeviceRegistrationResponse(
        success=success,
        message=message,
        device_id=device_id,
    )


@router.post("/unregister-device")
async def unregister_device(request: UnregisterDeviceRequest):
    """
    Unregister a device token.

    Call this endpoint when:
    - User logs out from a specific device
    - FCM token becomes invalid

    Request Body:
    ```json
    {
        "user_id": "282",
        "fcm_token": "fMhVK9xXQ8Gy7..."
    }
    ```
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    success = await notification_service.deactivate_device_token(request.fcm_token)
    return {
        "success": success,
        "message": "Device unregistered" if success else "Device not found"
    }


@router.post("/logout-all-devices")
async def logout_all_devices(request: LogoutAllDevicesRequest):
    """
    Unregister all devices for a user (logout from all devices).

    Request Body:
    ```json
    {
        "user_id": "282"
    }
    ```
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    count = await notification_service.deactivate_user_devices(request.user_id)
    return {"success": True, "message": f"Unregistered {count} devices"}


# ========================================
# Topic Subscriptions (Frontend APIs)
# ========================================

@router.post("/subscribe-topic")
async def subscribe_to_topic(request: SubscribeTopicRequest):
    """
    Subscribe to a notification topic.

    Request Body:
    ```json
    {
        "user_id": "282",
        "topic": "policy_updates"
    }
    ```
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    success, message = await notification_service.subscribe_to_topic(request.user_id, request.topic)
    return {"success": success, "message": message}


@router.post("/unsubscribe-topic")
async def unsubscribe_from_topic(request: UnsubscribeTopicRequest):
    """
    Unsubscribe from a notification topic.

    Request Body:
    ```json
    {
        "user_id": "282",
        "topic": "promotions"
    }
    ```
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    success, message = await notification_service.unsubscribe_from_topic(request.user_id, request.topic)
    return {"success": success, "message": message}


# ========================================
# Notification History (Frontend APIs)
# ========================================

@router.get("/history", response_model=NotificationHistoryResponse)
async def get_notification_history(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, description="Number of notifications to return"),
    offset: int = Query(0, description="Pagination offset"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
):
    """
    Get notification history for a user.

    Query Parameters:
    - user_id: User ID (required)
    - limit: Number of notifications (default: 50)
    - offset: Pagination offset (default: 0)
    - unread_only: Only unread notifications (default: false)

    Example: GET /notifications/history?user_id=282&limit=20&offset=0
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    notifications, total, unread_count = await notification_service.get_notification_history(
        user_id=user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )

    # Convert to response model
    history_items = []
    for n in notifications:
        history_items.append(
            NotificationHistoryItem(
                notification_id=n["notification_id"],
                title=n["title"],
                body=n["body"],
                notification_type=n["notification_type"],
                sent_at=n["sent_at"],
                read=n.get("read", False),
                read_at=n.get("read_at"),
                data=n.get("data"),
            )
        )

    return NotificationHistoryResponse(
        success=True,
        notifications=history_items,
        total=total,
        unread_count=unread_count,
    )


@router.post("/mark-read")
async def mark_notification_read(request: MarkNotificationReadRequest):
    """
    Mark a notification as read.

    Request Body:
    ```json
    {
        "user_id": "282",
        "notification_id": "507f1f77bcf86cd799439011"
    }
    ```
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    success = await notification_service.mark_notification_read(request.user_id, request.notification_id)
    return {"success": success}


@router.post("/mark-all-read")
async def mark_all_notifications_read(request: MarkAllNotificationsReadRequest):
    """
    Mark all notifications as read for a user.

    Request Body:
    ```json
    {
        "user_id": "282"
    }
    ```
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    count = await notification_service.mark_all_notifications_read(request.user_id)
    return {"success": True, "marked_count": count}


# ========================================
# Notification Settings (Frontend APIs)
# ========================================

@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    user_id: str = Query(..., description="User ID"),
):
    """
    Get notification settings for a user.

    Query Parameters:
    - user_id: User ID (required)

    Example: GET /notifications/settings?user_id=282
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    settings = await notification_service.get_notification_settings(user_id)
    return NotificationSettingsResponse(success=True, settings=settings)


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(request: NotificationSettingsUpdateRequest):
    """
    Update notification settings for a user. Supports partial updates.

    Request Body (all fields except user_id are optional):
    ```json
    {
        "user_id": "282",
        "protection_score": true
    }
    ```

    Or full update:
    ```json
    {
        "user_id": "282",
        "policy_renewal": true,
        "policy_expiry": true,
        "claim_updates": true,
        "payment_reminders": true,
        "protection_score": true,
        "recommendations": true,
        "promotional": false
    }
    ```
    """
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    try:
        # Get current settings first
        current_settings = await notification_service.get_notification_settings(request.user_id)

        # Build settings dict - only update fields that were provided (not None)
        settings_dict = {}
        if request.policy_renewal is not None:
            settings_dict["policy_renewal"] = request.policy_renewal
        if request.policy_expiry is not None:
            settings_dict["policy_expiry"] = request.policy_expiry
        if request.claim_updates is not None:
            settings_dict["claim_updates"] = request.claim_updates
        if request.payment_reminders is not None:
            settings_dict["payment_reminders"] = request.payment_reminders
        if request.protection_score is not None:
            settings_dict["protection_score"] = request.protection_score
        if request.recommendations is not None:
            settings_dict["recommendations"] = request.recommendations
        if request.promotional is not None:
            settings_dict["promotional"] = request.promotional

        # If no settings to update, return current settings
        if not settings_dict:
            return NotificationSettingsResponse(success=True, settings=current_settings)

        success = await notification_service.update_notification_settings(request.user_id, settings_dict)

        if success:
            # Merge current settings with updated settings for response
            merged_settings = {**current_settings, **settings_dict}
            return NotificationSettingsResponse(success=True, settings=merged_settings)
        else:
            raise HTTPException(status_code=500, detail="Failed to update settings")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification settings for user {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
