"""
Memory Storage Node
===================
After generating a response, stores:
1. The conversation turn in session memory (Redis)
2. Key insights extracted from the conversation
3. Document analysis results if a document was processed

All storage is fire-and-forget via asyncio.create_task() — returns immediately
so the response is not delayed by memory I/O.
"""
import asyncio
import time

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


async def _do_store(state: HibiscusState, plog: PipelineLogger) -> None:
    """Background task: all memory writes. Never raises — errors are logged."""
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
                from hibiscus.memory.layers.document import store_analysis_result, store_document
                await store_analysis_result(
                    user_id=state["user_id"],
                    session_id=state["session_id"],
                    analysis=output,
                )
                # Also store in hibiscus_documents so get_latest_document() can find it
                extraction = output.get("structured_data", {}).get("extraction") or {}
                uploaded_files = state.get("uploaded_files", [])
                filename = (uploaded_files[0].get("filename") or "policy.pdf") if uploaded_files else "policy.pdf"
                analysis_id = (uploaded_files[0].get("analysis_id")) if uploaded_files else None
                doc_id = f"doc_{state['user_id']}_{int(time.time())}"
                await store_document(
                    user_id=state["user_id"],
                    session_id=state["session_id"],
                    doc_id=doc_id,
                    filename=filename,
                    file_type="pdf",
                    extraction=extraction,
                    extraction_confidence=output.get("confidence", 0.0),
                    analysis_id=analysis_id,
                )
                plog.step_start("document_analysis_stored")
            except Exception as e:
                plog.warning("document_storage_failed", error=str(e))

    # ── Trigger async memory extraction (L2-L4 updates) ───────────────────
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


async def run(state: HibiscusState) -> dict:
    """
    Fire all memory writes in the background — returns immediately.
    The response has already been computed; memory I/O must not delay it.
    """
    plog = PipelineLogger(
        component="memory_storage",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    plog.step_start("memory_storage")

    # Schedule background storage — non-blocking
    asyncio.create_task(_do_store(state, plog))

    # Return immediately; memory_storage never modifies state
    return {}
