"""
Hibiscus WebSocket Endpoint
============================
WS /hibiscus/ws — Real-time streaming conversation endpoint.

Alternative to the SSE-based streaming in chat.py.
Provides full bidirectional communication for the Flutter/Next.js frontend.

Protocol:
  Client → Server (JSON):
    {"type": "message", "session_id": "...", "user_id": "...", "message": "...", "uploaded_files": []}
    {"type": "ping"}

  Server → Client (JSON):
    {"type": "token", "content": "..."}           # Streaming token
    {"type": "metadata", "confidence": 0.85, ...} # Response metadata
    {"type": "complete", "response": "..."}        # Full response
    {"type": "error", "message": "..."}            # Error
    {"type": "pong"}                               # Keepalive
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
import uuid
from typing import Any, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from hibiscus.observability.logger import get_logger, PipelineLogger
from hibiscus.orchestrator.state import initial_state

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming conversations.

    Maintains a persistent connection for the duration of the session.
    Each message goes through the full Hibiscus pipeline with token streaming.
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info("websocket_connected", session_id=session_id)

    try:
        while True:
            raw = await websocket.receive_text()
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
