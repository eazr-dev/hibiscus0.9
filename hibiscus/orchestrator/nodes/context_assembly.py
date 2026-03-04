"""
Context Assembly Node
=====================
Pulls context from all available memory layers and assembles
the optimal context window for each request.

Priority order (blueprint spec):
1. Session memory (always — current conversation)
2. Document memory (always if doc uploaded)
3. User profile (always if exists)
4. Policy portfolio (always if exists)
5. Knowledge memories (semantic search — relevant past insights)
6. Conversation history (semantic search — relevant past conversations)
7. Outcome memories (if relevant)

All 6 layers are fetched in parallel with asyncio.gather() — ~5x faster
than sequential I/O.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import time

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

_DOC_KEYWORDS = [
    # Direct policy references
    "my policy", "this policy", "the document", "uploaded", "what did i upload",
    "my insurance", "the policy",
    # Coverage terms
    "not covered", "coverage", "exclusion", "copay", "co-pay", "deductible",
    "premium", "sum insured", "eazr score",
    # My-specific queries (policy detail questions)
    "room rent", "icu", "waiting period", "pre-existing", "network hospital",
    "cashless", "reimburs", "claim", "hospitali", "admission",
    # "My ___" patterns — user asking about their own policy
    "my plan", "my coverage", "my benefit", "my cover", "my sum", "my premium",
    "am i covered", "do i have", "will i be covered", "will my",
    "is my", "what is my", "what are my", "how much is my", "how much cover",
    "gap in my", "gaps in my", "what does my",
    # Product-name references (common insurers)
    "acko", "hdfc ergo", "star health", "care health", "care supreme",
    "optima", "family optima", "red carpet", "star comprehensive",
    "bajaj allianz", "icici lombard", "niva bupa", "max bupa",
]


async def run(state: HibiscusState) -> dict:
    """Assemble context from all memory layers in parallel."""
    plog = PipelineLogger(
        component="context_assembly",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    start = time.time()
    plog.step_start("context_assembly")

    user_id = state["user_id"]
    session_id = state["session_id"]
    message = state.get("message", "").lower()
    query = state.get("message", "")

    message_refs_doc = any(kw in message for kw in _DOC_KEYWORDS)
    should_load_doc = (
        bool(state.get("uploaded_files"))
        or state.get("has_document")
        or message_refs_doc
    )

    # ── Parallel fetch all 6 memory layers ────────────────────────────
    async def _fetch_session():
        try:
            from hibiscus.memory.layers.session import get_session
            session_data = await get_session(session_id)
            if session_data:
                history = session_data.get("messages", [])
                return history[-10:] if len(history) > 10 else history
        except Exception as e:
            plog.warning("session_memory_unavailable", error=str(e))
        return state.get("session_history", [])

    async def _fetch_document():
        if not should_load_doc:
            return None
        try:
            from hibiscus.memory.layers.document import get_latest_document
            doc = await get_latest_document(user_id)
            if doc:
                plog.step_start("document_context_loaded", doc_id=doc.get("doc_id", "?"))
            return doc
        except Exception as e:
            plog.warning("document_memory_unavailable", error=str(e))
        return None

    async def _fetch_profile():
        if state.get("user_profile"):
            return state["user_profile"]
        try:
            from hibiscus.memory.layers.profile import get_user_profile
            return await get_user_profile(user_id)
        except Exception as e:
            plog.warning("profile_memory_unavailable", error=str(e))
        return None

    async def _fetch_portfolio():
        if state.get("policy_portfolio"):
            return state["policy_portfolio"]
        try:
            from hibiscus.memory.layers.portfolio import get_user_portfolio
            return await get_user_portfolio(user_id)
        except Exception as e:
            plog.warning("portfolio_memory_unavailable", error=str(e))
        return []

    async def _fetch_knowledge():
        try:
            from hibiscus.memory.layers.knowledge import get_relevant_insights
            return await get_relevant_insights(user_id, query, top_k=10)
        except Exception as e:
            plog.warning("knowledge_memory_unavailable", error=str(e))
        return []

    async def _fetch_conversations():
        try:
            from hibiscus.memory.layers.conversation import search_conversation_history
            return await search_conversation_history(user_id, query, top_k=5)
        except Exception as e:
            plog.warning("conversations_memory_unavailable", error=str(e))
        return []

    async def _fetch_renewal_alerts():
        """Fetch renewal alerts for returning users with known policies."""
        try:
            from hibiscus.services.renewal_tracker import renewal_tracker
            return await renewal_tracker.get_renewal_context(user_id)
        except Exception as e:
            plog.warning("renewal_tracker_unavailable", error=str(e))
        return ""

    async def _fetch_outcome_followups():
        """Fetch pending outcome follow-ups for returning users."""
        try:
            from hibiscus.services.outcome_collector import outcome_collector
            return await outcome_collector.get_pending_followups(user_id)
        except Exception as e:
            plog.warning("outcome_followups_unavailable", error=str(e))
        return ""

    (
        session_history,
        document_context,
        user_profile,
        policy_portfolio,
        relevant_memories,
        relevant_conversations,
        renewal_alerts,
        outcome_followups,
    ) = await asyncio.gather(
        _fetch_session(),
        _fetch_document(),
        _fetch_profile(),
        _fetch_portfolio(),
        _fetch_knowledge(),
        _fetch_conversations(),
        _fetch_renewal_alerts(),
        _fetch_outcome_followups(),
    )

    latency_ms = int((time.time() - start) * 1000)
    plog.step_complete(
        "context_assembly",
        latency_ms=latency_ms,
        has_session=bool(session_history),
        has_document=bool(document_context),
        has_profile=bool(user_profile),
        has_portfolio=bool(policy_portfolio),
        knowledge_count=len(relevant_memories),
        conversation_count=len(relevant_conversations),
        has_renewal_alerts=bool(renewal_alerts),
        has_outcome_followups=bool(outcome_followups),
    )

    return {
        "session_history": session_history,
        "document_context": document_context,
        "user_profile": user_profile,
        "policy_portfolio": policy_portfolio,
        "relevant_memories": relevant_memories,
        "relevant_conversations": relevant_conversations,
        "renewal_alerts": renewal_alerts,
        "outcome_followups": outcome_followups,
    }
