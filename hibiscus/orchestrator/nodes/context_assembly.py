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
"""
import time

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


async def run(state: HibiscusState) -> dict:
    """Assemble context from all memory layers."""
    plog = PipelineLogger(
        component="context_assembly",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    start = time.time()
    plog.step_start("context_assembly")

    updates = {}

    # ── L1: Session Memory ─────────────────────────────────────────────
    try:
        from hibiscus.memory.layers.session import get_session
        session_data = await get_session(state["session_id"])
        if session_data:
            history = session_data.get("messages", [])
            # Keep last 10 turns for context window efficiency
            updates["session_history"] = history[-10:] if len(history) > 10 else history
            plog.step_start("session_loaded", turn_count=len(updates["session_history"]))
    except Exception as e:
        plog.warning("session_memory_unavailable", error=str(e))
        updates["session_history"] = state.get("session_history", [])

    # ── L6: Document Memory ────────────────────────────────────────────
    doc_context = None
    message = state.get("message", "").lower()
    _doc_keywords = [
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
    message_refs_doc = any(kw in message for kw in _doc_keywords)
    should_load_doc = bool(state.get("uploaded_files")) or state.get("has_document") or message_refs_doc
    if should_load_doc:
        try:
            from hibiscus.memory.layers.document import get_latest_document
            doc_context = await get_latest_document(state["user_id"])
            if doc_context:
                plog.step_start("document_context_loaded", doc_id=doc_context.get("doc_id", "?"))
        except Exception as e:
            plog.warning("document_memory_unavailable", error=str(e))

    updates["document_context"] = doc_context

    # ── User Profile & Portfolio: stub for Phase 1 ────────────────────
    # In Phase 2, these will pull from PostgreSQL
    if not state.get("user_profile"):
        updates["user_profile"] = None
    if not state.get("policy_portfolio"):
        updates["policy_portfolio"] = []

    # ── Relevant Memories: stub for Phase 1 (Qdrant in Phase 2) ─────────
    updates["relevant_memories"] = []
    updates["relevant_conversations"] = []

    latency_ms = int((time.time() - start) * 1000)
    plog.step_complete(
        "context_assembly",
        latency_ms=latency_ms,
        has_session=bool(updates.get("session_history")),
        has_document=bool(doc_context),
        has_profile=bool(updates.get("user_profile")),
    )

    return updates
