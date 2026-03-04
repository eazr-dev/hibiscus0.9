"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Memory storage node — persists conversation, profile updates, and outcomes post-response.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
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
                # Only store if there is actual new extraction data (avoid overwriting seeded/cached docs)
                extraction = output.get("structured_data", {}).get("extraction") or {}
                uploaded_files = state.get("uploaded_files", [])
                if extraction and uploaded_files:
                    # Only persist when a real file was uploaded AND extraction was computed
                    filename = (uploaded_files[0].get("filename") or "policy.pdf") if uploaded_files else "policy.pdf"
                    analysis_id = (uploaded_files[0].get("analysis_id")) if uploaded_files else None
                    doc_id = f"doc_{state['user_id']}_{int(time.time())}"
                    structured = output.get("structured_data", {})
                    await store_document(
                        user_id=state["user_id"],
                        session_id=state["session_id"],
                        doc_id=doc_id,
                        filename=filename,
                        file_type="pdf",
                        extraction=extraction,
                        extraction_confidence=output.get("confidence", 0.0),
                        analysis_id=analysis_id,
                        eazr_score=structured.get("eazr_score"),
                        score_breakdown=structured.get("score_breakdown"),
                        gaps=structured.get("gaps"),
                        validation=structured.get("validation"),
                    )
                plog.step_start("document_analysis_stored")
            except Exception as e:
                plog.warning("document_storage_failed", error=str(e))

    # ── Enqueue KG enrichment from policy extractions ────────────────────
    for output in agent_outputs:
        if output.get("agent") == "policy_analyzer" and output.get("success"):
            extraction = output.get("structured_data", {}).get("extraction") or {}
            confidence = output.get("confidence", 0.0)
            if extraction and confidence >= 0.85:
                try:
                    from hibiscus.services.kg_enrichment import kg_enrichment
                    kg_enrichment.enqueue(extraction, confidence, state["user_id"])
                except Exception as e:
                    plog.warning("kg_enrichment_enqueue_failed", error=str(e))

    # ── Log fraud alerts if present ────────────────────────────────────
    fraud_alerts = state.get("fraud_alerts", [])
    if fraud_alerts:
        for alert in fraud_alerts:
            severity = alert.get("severity", "LOW")
            log_fn = plog.error if severity == "CRITICAL" else plog.warning
            log_fn(
                "fraud_alert",
                alert_type=alert.get("alert_type"),
                severity=severity,
                evidence=alert.get("evidence", "")[:200],
            )
        try:
            from hibiscus.observability.metrics import record_fraud_alert
            for alert in fraud_alerts:
                record_fraud_alert(alert.get("severity", "LOW"), alert.get("alert_type", "unknown"))
        except Exception:
            pass

    # ── Record outcomes for advice-giving agents ─────────────────────────
    _ADVICE_AGENTS = {"recommender", "surrender_calculator", "claims_guide",
                      "tax_advisor", "calculator", "risk_detector", "portfolio_optimizer"}
    for output in agent_outputs:
        agent_name = output.get("agent", "")
        if agent_name in _ADVICE_AGENTS and output.get("success") and output.get("response"):
            try:
                from hibiscus.services.outcome_collector import outcome_collector
                await outcome_collector.record_advice_outcome(
                    user_id=state["user_id"],
                    session_id=state["session_id"],
                    conversation_id=state.get("conversation_id"),
                    agent_name=agent_name,
                    response_text=output["response"],
                    policy_type=state.get("category"),
                    insurer=state.get("document_context", {}).get("extraction", {}).get("insurer") if state.get("document_context") else None,
                )
            except Exception as e:
                plog.warning("outcome_record_failed", agent=agent_name, error=str(e))

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
