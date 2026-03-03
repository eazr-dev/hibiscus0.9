"""
Hibiscus Chat Endpoint
======================
POST /hibiscus/chat — Main conversation endpoint
GET  /hibiscus/chat/history/{session_id} — Conversation history

This is the primary interface between the frontend and the Hibiscus AI engine.

Supports both:
1. Standard JSON response (stream=false)
2. Server-Sent Events streaming (stream=true)
"""
import json
import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from hibiscus.api.schemas.chat import ChatRequest, ChatResponse, StreamChunk
from hibiscus.api.schemas.common import Source
from hibiscus.observability.logger import get_logger, PipelineLogger
from hibiscus.orchestrator.state import initial_state

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to Hibiscus AI",
    description="Main conversation endpoint. Supports streaming via stream=true.",
)
async def chat(request: ChatRequest, http_request: Request) -> JSONResponse:
    """
    Process a chat message through the full Hibiscus pipeline:
    1. Assemble context from memory layers
    2. Classify intent
    3. Route to specialist agents OR direct LLM
    4. Apply guardrails
    5. Store in memory
    6. Return structured response
    """
    request_id = str(getattr(http_request.state, "request_id", uuid.uuid4()))
    conversation_id = request.conversation_id or f"conv_{request.session_id}_{int(time.time())}"

    plog = PipelineLogger(
        component="chat_endpoint",
        request_id=request_id,
        session_id=request.session_id,
        user_id=request.user_id,
    )

    start_time = time.time()
    plog.step_start(
        "chat_request_received",
        message_length=len(request.message),
        has_files=bool(request.uploaded_files),
        stream=request.stream,
    )

    # Build initial state
    uploaded = []
    if request.uploaded_files:
        uploaded = [f.model_dump() for f in request.uploaded_files]

    state = initial_state(
        user_id=request.user_id,
        session_id=request.session_id,
        request_id=request_id,
        conversation_id=conversation_id,
        message=request.message,
        uploaded_files=uploaded,
    )

    if request.stream:
        return StreamingResponse(
            _stream_response(state, request_id, plog, start_time),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # ── Non-streaming path ──────────────────────────────────────────────
    try:
        from hibiscus.orchestrator.graph import run_graph

        config = {
            "configurable": {
                "thread_id": conversation_id,
            }
        }

        final_state = await run_graph(state, config)

        total_latency_ms = int((time.time() - start_time) * 1000)

        # Get cost info
        from hibiscus.observability.cost_tracker import finalize_conversation, get_conversation_cost
        conv_cost = get_conversation_cost(conversation_id)
        cost_inr = conv_cost.total_cost_inr if conv_cost else 0.0

        plog.step_complete(
            "chat_response_sent",
            latency_ms=total_latency_ms,
            confidence=final_state.get("confidence", 0.0),
            agents_invoked=final_state.get("agents_invoked", []),
            guardrails_passed=all(final_state.get("guardrail_results", {}).values()),
        )

        # Build response
        sources = [
            Source(
                type=s.get("type", "unknown"),
                reference=s.get("reference", ""),
                confidence=s.get("confidence", 0.0),
                page=s.get("page"),
            )
            for s in final_state.get("sources", [])
        ]

        return JSONResponse(content=ChatResponse(
            response=final_state.get("response", ""),
            session_id=request.session_id,
            request_id=request_id,
            confidence=final_state.get("confidence", 0.0),
            sources=sources,
            follow_up_suggestions=final_state.get("follow_up_suggestions", []),
            eazr_products_relevant=final_state.get("eazr_products_relevant", []),
            agents_invoked=final_state.get("agents_invoked", []),
            guardrail_results=final_state.get("guardrail_results", {}),
            latency_ms=total_latency_ms,
            cost_inr=round(cost_inr, 4),
            response_type=final_state.get("response_type", "text"),
            structured_data=_get_structured_data(final_state),
        ).model_dump())

    except Exception as e:
        logger.error("chat_pipeline_error", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Hibiscus pipeline error: {str(e)}. Please try again.",
        )


@router.get(
    "/chat/history/{session_id}",
    summary="Get conversation history for a session",
)
async def get_history(session_id: str) -> JSONResponse:
    """Get the full conversation history for a session."""
    try:
        from hibiscus.memory.layers.session import get_session_messages
        messages = await get_session_messages(session_id, limit=50)
        return JSONResponse(content={
            "session_id": session_id,
            "messages": messages,
            "count": len(messages),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_response(
    state: dict,
    request_id: str,
    plog: PipelineLogger,
    start_time: float,
) -> AsyncGenerator[str, None]:
    """Generate SSE-formatted streaming response."""

    async def send_chunk(chunk: StreamChunk) -> str:
        return f"data: {json.dumps(chunk.model_dump())}\n\n"

    try:
        from hibiscus.orchestrator.graph import run_graph

        # Run the graph to get classification and routing
        # For streaming, we emit tokens as they come from the LLM
        config = {"configurable": {"thread_id": state.get("conversation_id", "unknown")}}

        # Phase 1: Emit metadata first (fast)
        yield await send_chunk(StreamChunk(
            type="metadata",
            metadata={"request_id": request_id, "status": "processing"},
        ))

        # Run full pipeline
        final_state = await run_graph(state, config)

        # Stream the response token by token (simulated for now — real streaming in Phase 2)
        response_text = final_state.get("response", "")
        chunk_size = 10  # Characters per chunk

        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i + chunk_size]
            yield await send_chunk(StreamChunk(type="token", content=chunk))

        # Final metadata chunk
        total_latency_ms = int((time.time() - start_time) * 1000)
        yield await send_chunk(StreamChunk(
            type="done",
            metadata={
                "confidence": final_state.get("confidence", 0.0),
                "agents_invoked": final_state.get("agents_invoked", []),
                "latency_ms": total_latency_ms,
                "follow_up_suggestions": final_state.get("follow_up_suggestions", []),
                "eazr_products_relevant": final_state.get("eazr_products_relevant", []),
            },
        ))

    except Exception as e:
        yield await send_chunk(StreamChunk(
            type="error",
            content=str(e),
        ))


def _get_structured_data(final_state: dict) -> dict | None:
    """Extract structured data from agent outputs for the response."""
    agent_outputs = final_state.get("agent_outputs", [])
    for output in agent_outputs:
        if output.get("agent") == "policy_analyzer" and output.get("structured_data"):
            return output["structured_data"]
    return None
