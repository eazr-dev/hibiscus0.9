"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
WebSocket endpoint — real-time bidirectional chat with session persistence.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
import uuid
from collections import deque
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from hibiscus.observability.logger import get_logger, PipelineLogger
from hibiscus.orchestrator.state import initial_state

logger = get_logger(__name__)
router = APIRouter()

# ── Per-connection rate limiter ──────────────────────────────────────────────
MAX_MESSAGES_PER_MINUTE = 30
_RATE_WINDOW_SECONDS = 60


class ConnectionRateLimiter:
    """Sliding-window rate limiter for a single WebSocket connection."""

    def __init__(self, max_messages: int = MAX_MESSAGES_PER_MINUTE, window_seconds: int = _RATE_WINDOW_SECONDS):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self._timestamps: deque = deque()

    def is_allowed(self) -> bool:
        """Check if a new message is allowed. Returns False if rate limit exceeded."""
        now = time.time()
        # Remove timestamps outside the window
        while self._timestamps and self._timestamps[0] < now - self.window_seconds:
            self._timestamps.popleft()
        if len(self._timestamps) >= self.max_messages:
            return False
        self._timestamps.append(now)
        return True


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming conversations.

    Maintains a persistent connection for the duration of the session.
    Each message goes through the full Hibiscus pipeline with token streaming.
    Rate limited to MAX_MESSAGES_PER_MINUTE messages per connection.
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    rate_limiter = ConnectionRateLimiter()
    logger.info("websocket_connected", session_id=session_id)

    try:
        while True:
            raw = await websocket.receive_text()

            # Rate limit check
            if not rate_limiter.is_allowed():
                await websocket.send_json({
                    "type": "error",
                    "message": f"Rate limit exceeded ({MAX_MESSAGES_PER_MINUTE} messages/minute). Please slow down.",
                })
                logger.warning("websocket_rate_limited", session_id=session_id)
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type", "message")

            # Keepalive
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type != "message":
                await websocket.send_json({"type": "error", "message": f"Unknown type: {msg_type}"})
                continue

            # Process message through pipeline
            await _handle_message(websocket, data, session_id)

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", session_id=session_id)
    except Exception as e:
        logger.error("websocket_error", session_id=session_id, error=str(e))
        try:
            await websocket.send_json({"type": "error", "message": "Internal error"})
            await websocket.close()
        except Exception:
            pass


async def _handle_message(
    websocket: WebSocket,
    data: Dict[str, Any],
    default_session_id: str,
):
    """Process a single message through the Hibiscus pipeline."""
    request_id = str(uuid.uuid4())
    start_time = time.time()

    plog = PipelineLogger(
        component="websocket",
        request_id=request_id,
        session_id=data.get("session_id", default_session_id),
        user_id=data.get("user_id", "anonymous"),
    )
    plog.log("ws_message_received", message_length=len(data.get("message", "")))

    try:
        from hibiscus.orchestrator.graph import hibiscus_graph

        state = initial_state()
        state.update({
            "message": data.get("message", ""),
            "user_id": data.get("user_id", "anonymous"),
            "session_id": data.get("session_id", default_session_id),
            "request_id": request_id,
            "uploaded_files": data.get("uploaded_files", []),
        })

        # Run the graph
        result = await hibiscus_graph.ainvoke(state)

        response_text = result.get("response", "I'm sorry, I couldn't process that.")
        confidence = result.get("confidence", 0.0)

        # Stream the response token by token (simulated chunking for WS)
        chunk_size = 20
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i + chunk_size]
            await websocket.send_json({"type": "token", "content": chunk})

        # Send metadata
        latency_ms = int((time.time() - start_time) * 1000)
        await websocket.send_json({
            "type": "metadata",
            "confidence": confidence,
            "agents_invoked": result.get("agents_invoked", []),
            "category": result.get("category", ""),
            "intent": result.get("intent", ""),
            "latency_ms": latency_ms,
            "sources": result.get("sources", []),
            "follow_up_suggestions": result.get("follow_up_suggestions", []),
        })

        # Send complete signal
        await websocket.send_json({
            "type": "complete",
            "response": response_text,
            "request_id": request_id,
        })

        plog.log("ws_response_sent", latency_ms=latency_ms, confidence=confidence)

    except Exception as e:
        plog.error("ws_pipeline_error", error=str(e))
        await websocket.send_json({
            "type": "error",
            "message": "I encountered an issue processing your request. Please try again.",
            "request_id": request_id,
        })
