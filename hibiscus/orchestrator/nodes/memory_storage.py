"""
Memory Storage Node
===================
After generating a response, stores:
1. The conversation turn in session memory (Redis)
2. Key insights extracted from the conversation
3. Document analysis results if a document was processed

Runs asynchronously — does not block the response.
"""
import time

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


async def run(state: HibiscusState) -> dict:
    """Store conversation turn and extract memories."""
    plog = PipelineLogger(
        component="memory_storage",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    plog.step_start("memory_storage")
    start = time.time()

    # ── Store conversation turn in session memory ──────────────────────
    try:
        from hibiscus.memory.layers.session import append_message
        await append_message(
            session_id=state["session_id"],
            role="user",
            content=state.get("message", ""),
        )
        await append_message(
            session_id=state["session_id"],
            role="assistant",
            content=state.get("response", ""),
            metadata={
                "confidence": state.get("confidence", 0.0),
                "agents_invoked": state.get("agents_invoked", []),
                "intent": state.get("intent", ""),
                "category": state.get("category", ""),
            },
        )
        plog.step_start("session_stored")
    except Exception as e:
        plog.warning("session_storage_failed", error=str(e))

    # ── Store document analysis result if applicable ────────────────────
    agent_outputs = state.get("agent_outputs", [])
    for output in agent_outputs:
        if output.get("agent") == "policy_analyzer" and output.get("success"):
            try:
                from hibiscus.memory.layers.document import store_analysis_result
                await store_analysis_result(
                    user_id=state["user_id"],
                    session_id=state["session_id"],
                    analysis=output,
                )
                plog.step_start("document_analysis_stored")
            except Exception as e:
                plog.warning("document_storage_failed", error=str(e))

    # ── Trigger async memory extraction (L2-L4 updates) ───────────────────
    # Fire-and-forget: does not block the response
    try:
        from hibiscus.memory.extraction.memory_extractor import schedule_extraction
        messages = state.get("conversation_history", [])
        if not messages:
            messages = [
                {"role": "user", "content": state.get("message", "")},
                {"role": "assistant", "content": state.get("response", "")},
            ]
        schedule_extraction(
            user_id=state["user_id"],
            session_id=state["session_id"],
            conversation_id=state.get("request_id", state["session_id"]),
            messages=messages,
            context={"category": state.get("category", ""), "intent": state.get("intent", "")},
        )
    except Exception as e:
        plog.warning("memory_extraction_schedule_failed", error=str(e))

    latency_ms = int((time.time() - start) * 1000)
    plog.step_complete("memory_storage", latency_ms=latency_ms)

    # Memory storage doesn't modify state (fire-and-forget)
    return {}
