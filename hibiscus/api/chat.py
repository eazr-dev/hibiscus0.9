"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Chat endpoint — primary interface between frontend and AI engine (JSON + SSE streaming).
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import json
import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from hibiscus.api.schemas.chat import ChatRequest, ChatResponse, StreamChunk
from hibiscus.api.schemas.common import Source
from hibiscus.config import ENGINE_LABEL_INLINE
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
        from hibiscus.observability.cost_tracker import get_conversation_cost
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
            products_relevant=final_state.get("eazr_products_relevant", []),
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
            detail=f"{ENGINE_LABEL_INLINE} Pipeline error: {str(e)}. Please try again.",
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
    """
    Generate SSE-formatted streaming response.

    Two paths:
    1. Fast path (L1/L2 simple queries, no agents needed):
       - Check cache → instant if hit
       - Stream tokens directly from LLM as they arrive (TTFT ~2-4s)
    2. Full path (L3/L4 complex queries with agents):
       - Run full LangGraph pipeline → simulate streaming from completed response
    """

    async def send_chunk(chunk: StreamChunk) -> str:
        return f"data: {json.dumps(chunk.model_dump())}\n\n"

    yield await send_chunk(StreamChunk(
        type="metadata",
        metadata={"request_id": request_id, "status": "processing"},
    ))

    try:
        # ── Fast keyword pre-classification (no LLM, instant) ────────────
        from hibiscus.orchestrator.nodes.intent_classification import (
            _fast_classify, _determine_agents, _determine_complexity,
        )
        message = state.get("message", "")
        uploaded_files = state.get("uploaded_files", [])
        fast = _fast_classify(message, uploaded_files)
        agents_needed = _determine_agents(fast["intent"], fast["category"], fast["has_document"])
        complexity = _determine_complexity(fast["intent"], fast["has_document"], agents_needed)

        # ── Decide path ───────────────────────────────────────────────────
        is_simple = complexity in ("L1", "L2") and not agents_needed

        if is_simple:
            # ── Fast path: cache check then direct LLM stream ─────────────
            from hibiscus.memory.layers.response_cache import (
                is_cacheable, get_cached_response, set_cached_response,
            )
            from hibiscus.llm.router import stream_llm
            from pathlib import Path

            _PROMPT_DIR = Path(__file__).parent.parent / "llm" / "prompts"
            _SYSTEM_PROMPT = (_PROMPT_DIR / "system" / "hibiscus_core.txt").read_text()

            use_cache = is_cacheable(
                intent=fast["intent"],
                has_document=fast["has_document"],
                uploaded_files=uploaded_files,
                document_context=state.get("document_context"),
            )

            # Cache hit → stream cached chunks immediately
            if use_cache and not state.get("session_history"):
                cached = await get_cached_response(message)
                if cached:
                    response_text = cached.get("response", "")
                    chunk_size = 15
                    for i in range(0, len(response_text), chunk_size):
                        yield await send_chunk(StreamChunk(type="token", content=response_text[i:i + chunk_size]))
                    total_latency_ms = int((time.time() - start_time) * 1000)
                    yield await send_chunk(StreamChunk(
                        type="done",
                        metadata={
                            "confidence": cached.get("confidence", 0.75),
                            "agents_invoked": [],
                            "latency_ms": total_latency_ms,
                            "follow_up_suggestions": cached.get("follow_up_suggestions", []),
                            "products_relevant": [],
                            "cache_hit": True,
                        },
                    ))
                    return

            # Cache miss → stream tokens from LLM as they arrive (true streaming)
            full_response = []
            async for token in stream_llm(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                tier="deepseek_v3",
                conversation_id=state.get("conversation_id", "?"),
                agent="direct_llm_stream",
            ):
                full_response.append(token)
                yield await send_chunk(StreamChunk(type="token", content=token))

            response_text = "".join(full_response)

            # Ensure every streamed response has at minimum a short disclaimer
            from hibiscus.guardrails.compliance import _DISCLAIMER_PATTERNS, SHORT_DISCLAIMER
            if not any(p in response_text.lower() for p in _DISCLAIMER_PATTERNS):
                response_text += SHORT_DISCLAIMER
                yield await send_chunk(StreamChunk(type="token", content=SHORT_DISCLAIMER))

            total_latency_ms = int((time.time() - start_time) * 1000)

            # Cache the response for future requests
            if use_cache and not state.get("session_history"):
                result_payload = {
                    "response": response_text,
                    "confidence": 0.75,
                    "sources": [{"type": "llm_reasoning", "confidence": 0.75}],
                    "follow_up_suggestions": [],
                    "agents_invoked": [],
                }
                import asyncio
                asyncio.create_task(set_cached_response(message, result_payload))

            # Fire memory storage in background
            import asyncio
            from hibiscus.orchestrator.nodes.memory_storage import _do_store
            from hibiscus.observability.logger import PipelineLogger as _PLog
            bg_state = {**state, "response": response_text, "intent": fast["intent"],
                        "category": fast["category"], "confidence": 0.75, "agents_invoked": []}
            bg_plog = _PLog(component="memory_storage_bg", request_id=request_id,
                            session_id=state.get("session_id", "?"), user_id=state.get("user_id", "?"))
            asyncio.create_task(_do_store(bg_state, bg_plog))

            yield await send_chunk(StreamChunk(
                type="done",
                metadata={
                    "confidence": 0.75,
                    "agents_invoked": [],
                    "latency_ms": total_latency_ms,
                    "follow_up_suggestions": [],
                    "products_relevant": [],
                    "cache_hit": False,
                },
            ))

        else:
            # ── Full path: complex queries with agents ─────────────────────
            from hibiscus.orchestrator.graph import run_graph
            config = {"configurable": {"thread_id": state.get("conversation_id", "unknown")}}
            final_state = await run_graph(state, config)

            # Chunk the completed response
            response_text = final_state.get("response", "")
            chunk_size = 15
            for i in range(0, len(response_text), chunk_size):
                yield await send_chunk(StreamChunk(type="token", content=response_text[i:i + chunk_size]))

            total_latency_ms = int((time.time() - start_time) * 1000)
            yield await send_chunk(StreamChunk(
                type="done",
                metadata={
                    "confidence": final_state.get("confidence", 0.0),
                    "agents_invoked": final_state.get("agents_invoked", []),
                    "latency_ms": total_latency_ms,
                    "follow_up_suggestions": final_state.get("follow_up_suggestions", []),
                    "products_relevant": final_state.get("eazr_products_relevant", []),
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
