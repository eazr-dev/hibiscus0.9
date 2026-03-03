"""
WebSocket Chat Router for EAZR Chat
Provides real-time chat endpoint with streaming AI responses and notifications.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Body, Depends
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import asyncio
import logging
import secrets

from websocket.connection_manager import WebSocketConnectionManager, connection_manager
from websocket.message_handler import WebSocketMessageHandler
from websocket.auth_handler import WebSocketAuthHandler, auth_handler
from websocket.presence_manager import PresenceManager, presence_manager
from websocket.models import WebSocketCloseCode
from services.websocket_chat_service import WebSocketChatService
from core.dependencies import verify_token

# Import WebSocket rate limiter
try:
    from core.rate_limiter import ws_rate_limiter
    WS_RATE_LIMITER_AVAILABLE = True
except ImportError:
    ws_rate_limiter = None
    WS_RATE_LIMITER_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

# Initialize components — use module-level singletons for connection_manager,
# auth_handler, presence_manager so that all modules share the same instances.
# Only chat_service needs a new instance (no global singleton exists).
chat_service = WebSocketChatService()

message_handler = WebSocketMessageHandler(
    connection_manager=connection_manager,
    auth_handler=auth_handler,
    presence_manager=presence_manager,
    chat_service=chat_service
)

# Background task tracking
_cleanup_task: Optional[asyncio.Task] = None
_notification_task: Optional[asyncio.Task] = None


# ============= Request/Response Models =============

class SendNotificationRequest(BaseModel):
    """Request to send notification via WebSocket"""
    user_id: int = Field(..., description="Target user ID")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    notification_type: str = Field(default="system", description="Notification type")
    priority: str = Field(default="normal", description="Priority: low, normal, high")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")
    image_url: Optional[str] = Field(default=None, description="Image URL")
    action_url: Optional[str] = Field(default=None, description="Action URL")
    channel: str = Field(default="both", description="Channel: websocket, fcm, both")


class BulkNotificationRequest(BaseModel):
    """Request to send notification to multiple users"""
    user_ids: List[int] = Field(..., description="Target user IDs")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    notification_type: str = Field(default="system", description="Notification type")
    priority: str = Field(default="normal", description="Priority")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for quick auth"),
    session_id: Optional[str] = Query(None, description="Existing chat session to join"),
    device_id: Optional[str] = Query(None, description="Device identifier")
):
    """
    Main WebSocket endpoint for real-time chat.

    Connection flow:
    1. Client connects to /ws/chat
    2. If token provided in query params, authenticate immediately
    3. Otherwise, client must send authenticate message
    4. After auth, client can send chat/typing/presence messages

    Query Parameters:
    - token: JWT token (alternative to authenticate message)
    - session_id: Existing chat session to join
    - device_id: Device identifier for multi-device tracking

    Message Protocol: JSON over WebSocket

    Example connection (JavaScript):
    ```javascript
    const ws = new WebSocket('wss://your-domain/ws/chat?token=YOUR_JWT_TOKEN');

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log('Received:', msg.type);
    };

    // Send chat message
    ws.send(JSON.stringify({
        type: 'chat',
        chat_session_id: 'your_chat_session_id',
        query: 'Hello, I need help with insurance'
    }));
    ```
    """
    # Get client IP for rate limiting
    client_ip = websocket.client.host if websocket.client else "unknown"

    # Check connection rate limit before accepting
    if WS_RATE_LIMITER_AVAILABLE and ws_rate_limiter:
        is_allowed, rate_info = ws_rate_limiter.check_connection_rate_limit(client_ip)
        if not is_allowed:
            logger.warning(f"WebSocket connection rate limit exceeded for IP: {client_ip}")
            await websocket.close(code=1008, reason="Too many connection attempts. Please try again later.")
            return

    await websocket.accept()

    connection_id = None
    temp_id = f"temp_{secrets.token_hex(8)}"

    try:
        # If token provided in query params, authenticate immediately
        if token:
            logger.info(f"WebSocket connection with token auth (device: {device_id})")

            success, auth_data = await auth_handler.authenticate(
                access_token=token,
                user_id=None,  # Will be extracted from token
                chat_session_id=session_id,
                device_id=device_id
            )

            if success:
                try:
                    connection_id = await connection_manager.connect(
                        websocket=websocket,
                        user_id=auth_data["user_id"],
                        chat_session_id=auth_data["chat_session_id"],
                        user_session_id=auth_data["user_session_id"],
                        device_id=auth_data.get("device_id", device_id or "default"),
                        access_token=token,
                        user_name=auth_data.get("user_name")
                    )
                except ConnectionError:
                    await websocket.send_json({
                        "type": "auth_failure",
                        "error": "Too many active connections. Please close other sessions first.",
                        "error_code": "CONNECTION_LIMIT_EXCEEDED",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    await websocket.close(code=WebSocketCloseCode.POLICY_VIOLATION)
                    return

                # Set presence online
                await presence_manager.set_online(
                    user_id=auth_data["user_id"],
                    device_id=auth_data.get("device_id", device_id or "default"),
                    user_name=auth_data.get("user_name")
                )

                # Send auth success
                await websocket.send_json({
                    "type": "auth_success",
                    "connection_id": connection_id,
                    "user_id": auth_data["user_id"],
                    "chat_session_id": auth_data["chat_session_id"],
                    "user_session_id": auth_data["user_session_id"],
                    "user_name": auth_data.get("user_name"),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                # Send initial notification state (matches message-based auth path)
                try:
                    from websocket.notification_handler import notification_handler as _nh
                    await _nh.send_initial_state(
                        websocket=websocket,
                        user_id=auth_data["user_id"]
                    )
                except Exception as e:
                    logger.warning(f"Failed to send initial notification state (query auth): {e}")

                # Notify notification manager of connection (matches message-based auth path)
                try:
                    from websocket.notification_manager import notification_manager as _nm
                    await _nm.user_connected(
                        user_id=auth_data["user_id"],
                        device_id=auth_data.get("device_id", device_id or "default")
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify notification manager (query auth): {e}")

                logger.info(
                    f"WebSocket authenticated via query param: "
                    f"user_id={auth_data['user_id']}, connection_id={connection_id}"
                )
            else:
                # Auth failed
                await websocket.send_json({
                    "type": "auth_failure",
                    "error": auth_data.get("error", "Authentication failed"),
                    "error_code": auth_data.get("error_code", "AUTH_FAILED"),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                await websocket.close(code=WebSocketCloseCode.AUTH_FAILED)
                return
        else:
            # No token provided, send connection ack and wait for auth message
            await websocket.send_json({
                "type": "connection_ack",
                "connection_id": temp_id,
                "requires_auth": True,
                "server_time": datetime.now(timezone.utc).isoformat(),
                "message": "Please send authenticate message with your access token"
            })

        # Main message loop
        while True:
            try:
                # Receive message with timeout for heartbeat checking
                raw_message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # 60 second timeout
                )

                # Reject oversized messages (64 KB limit)
                if len(raw_message) > 65536:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Message too large",
                        "error_code": "MESSAGE_TOO_LARGE",
                        "max_size": 65536,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    continue

                # Handle message and potentially get connection_id (after auth)
                new_connection_id = await message_handler.handle_message(
                    websocket=websocket,
                    connection_id=connection_id,
                    raw_message=raw_message
                )

                # Update connection_id if authentication happened
                if new_connection_id and not connection_id:
                    connection_id = new_connection_id
                    logger.info(f"Connection authenticated: {connection_id}")

            except asyncio.TimeoutError:
                # No message received, send ping to check if connection is alive
                if connection_id:
                    try:
                        await websocket.send_json({
                            "type": "ping",
                            "server_time": datetime.now(timezone.utc).isoformat()
                        })
                    except Exception:
                        logger.warning(f"Failed to send ping, closing connection: {connection_id}")
                        break
                else:
                    # Unauthenticated connection timed out
                    logger.info("Unauthenticated connection timed out")
                    await websocket.close(code=WebSocketCloseCode.AUTH_FAILED)
                    break

    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected: {connection_id}, code: {e.code}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Cleanup on disconnect
        if connection_id:
            await message_handler.handle_disconnect(connection_id)


@router.get("/ws/stats")
async def get_websocket_stats(_: str = Depends(verify_token)):
    """
    Get WebSocket connection statistics.

    Returns connection counts, presence information, and notification stats.
    Requires JWT authentication.
    """
    stats = {
        "connections": connection_manager.get_stats(),
        "presence": presence_manager.get_stats(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Add notification stats if available
    try:
        from websocket.notification_manager import notification_manager
        stats["notifications"] = notification_manager.get_stats()
    except Exception:
        pass

    return stats


@router.get("/ws/health")
async def websocket_health():
    """Health check for WebSocket service"""
    return {
        "status": "healthy",
        "service": "websocket_chat",
        "total_connections": connection_manager.get_connection_count(),
        "unique_users": connection_manager.get_user_count(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============= Notification HTTP Endpoints =============

@router.post("/ws/notifications/send")
async def send_realtime_notification(request: SendNotificationRequest, _: str = Depends(verify_token)):
    """
    Send a real-time notification to a user via WebSocket + FCM.
    Requires JWT authentication.

    This endpoint sends notifications through the advanced notification manager
    which handles:
    - WebSocket delivery for online users
    - FCM fallback for offline users
    - Delivery tracking and retry
    - User preferences and DND
    """
    try:
        from websocket.notification_manager import notification_manager
        from websocket.notification_manager import NotificationChannel
        from models.notification import NotificationType, NotificationPriority

        # Map string channel to enum
        channel_map = {
            "websocket": NotificationChannel.WEBSOCKET,
            "fcm": NotificationChannel.FCM,
            "both": NotificationChannel.BOTH
        }
        channel = channel_map.get(request.channel, NotificationChannel.BOTH)

        # Map strings to enums
        try:
            notif_type = NotificationType(request.notification_type)
        except ValueError:
            notif_type = NotificationType.SYSTEM

        try:
            priority = NotificationPriority(request.priority)
        except ValueError:
            priority = NotificationPriority.NORMAL

        success, message, notification_id = await notification_manager.send_notification(
            user_id=request.user_id,
            title=request.title,
            body=request.body,
            notification_type=notif_type,
            priority=priority,
            data=request.data,
            image_url=request.image_url,
            action_url=request.action_url,
            channel=channel
        )

        return {
            "success": success,
            "message": message,
            "notification_id": notification_id,
            "user_id": request.user_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="Notification manager not available")
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ws/notifications/send-bulk")
async def send_bulk_notification(request: BulkNotificationRequest, _: str = Depends(verify_token)):
    """
    Send notification to multiple users.
    Requires JWT authentication.

    Returns summary of delivery results for each user.
    """
    try:
        from websocket.notification_manager import notification_manager
        from models.notification import NotificationType, NotificationPriority

        try:
            notif_type = NotificationType(request.notification_type)
        except ValueError:
            notif_type = NotificationType.SYSTEM

        try:
            priority = NotificationPriority(request.priority)
        except ValueError:
            priority = NotificationPriority.NORMAL

        results = await notification_manager.send_notification_to_many(
            user_ids=request.user_ids,
            title=request.title,
            body=request.body,
            notification_type=notif_type,
            priority=priority,
            data=request.data
        )

        return {
            "success": results["success_count"] > 0,
            "summary": {
                "success_count": results["success_count"],
                "failed_count": results["failed_count"],
                "queued_count": results["queued_count"],
                "total": len(request.user_ids)
            },
            "user_results": results["user_results"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="Notification manager not available")
    except Exception as e:
        logger.error(f"Error sending bulk notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ws/notifications/user/{user_id}/status")
async def get_user_notification_status(user_id: int, _: str = Depends(verify_token)):
    """
    Get notification status for a user.
    Requires JWT authentication.

    Returns online status, unread count, and DND status.
    """
    try:
        from websocket.notification_manager import notification_manager

        is_online = notification_manager.is_user_online(user_id)
        is_dnd = notification_manager.is_dnd_active(user_id)
        unread_count = await notification_manager.get_unread_count(user_id)

        return {
            "user_id": user_id,
            "is_online": is_online,
            "unread_count": unread_count,
            "dnd_active": is_dnd,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="Notification manager not available")
    except Exception as e:
        logger.error(f"Error getting user notification status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ws/notifications/stats")
async def get_notification_stats(_: str = Depends(verify_token)):
    """Get notification system statistics. Requires JWT authentication."""
    try:
        from websocket.notification_manager import notification_manager
        return notification_manager.get_stats()
    except ImportError:
        raise HTTPException(status_code=503, detail="Notification manager not available")
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============= Background Tasks =============

async def cleanup_task():
    """
    Periodically clean up stale connections and process presence changes.
    Should be started on application startup.
    """
    logger.info("WebSocket cleanup task started")

    while True:
        try:
            await asyncio.sleep(60)  # Run every minute

            # Clean stale connections (no heartbeat for 2 minutes)
            cleaned = await connection_manager.cleanup_stale_connections(timeout_seconds=120)
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} stale WebSocket connections")

            # Clean stale pending auth entries (no auth within 2 minutes)
            message_handler.cleanup_stale_pending_auth(max_age_seconds=120)

            # Process pending offline transitions
            offline_users = await presence_manager.process_pending_offline()
            if offline_users:
                # Only notify the user's own remaining devices (not all users)
                for user_id in offline_users:
                    await connection_manager.broadcast_to_user(
                        user_id=user_id,
                        message={
                            "type": "presence_status",
                            "user_id": user_id,
                            "status": "offline",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )

            # Check auto-away
            away_users = await presence_manager.check_auto_away()
            if away_users:
                logger.info(f"Marked {len(away_users)} users as away")
                for user_id in away_users:
                    await connection_manager.broadcast_to_user(
                        user_id=user_id,
                        message={
                            "type": "presence_status",
                            "user_id": user_id,
                            "status": "away",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )

        except asyncio.CancelledError:
            logger.info("WebSocket cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in WebSocket cleanup task: {e}")


async def start_background_tasks():
    """Start background tasks for WebSocket management"""
    global _cleanup_task, _notification_task

    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(cleanup_task())
        logger.info("WebSocket cleanup task started")

    # Start notification manager background processor
    try:
        from websocket.notification_manager import notification_manager
        # Inject connection manager into notification manager
        notification_manager.set_connection_manager(connection_manager)
        await notification_manager.start_background_processor()
        logger.info("Notification manager background processor started")
    except Exception as e:
        logger.warning(f"Failed to start notification manager: {e}")


async def stop_background_tasks():
    """Stop background tasks"""
    global _cleanup_task, _notification_task

    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
        try:
            await _cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("WebSocket cleanup task stopped")

    # Stop notification manager
    try:
        from websocket.notification_manager import notification_manager
        await notification_manager.stop_background_processor()
        logger.info("Notification manager stopped")
    except Exception as e:
        logger.warning(f"Failed to stop notification manager: {e}")


# ============= Utility Functions =============

def get_connection_manager() -> WebSocketConnectionManager:
    """Get the global connection manager instance"""
    return connection_manager


def get_presence_manager() -> PresenceManager:
    """Get the global presence manager instance"""
    return presence_manager


async def broadcast_notification(
    user_id: int,
    notification_type: str,
    title: str,
    body: str,
    data: Optional[dict] = None
) -> int:
    """
    Send a notification to a user via WebSocket.

    Args:
        user_id: Target user
        notification_type: Type of notification (e.g., policy_renewal, claim_update)
        title: Notification title
        body: Notification body
        data: Additional data

    Returns:
        Number of devices notified
    """
    message = {
        "type": "notification",
        "notification_type": notification_type,
        "title": title,
        "body": body,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return await connection_manager.broadcast_to_user(user_id, message)
