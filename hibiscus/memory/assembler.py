"""
Context Assembler
=================
Builds the optimal context window for each query by pulling from all 6 memory layers.

ASSEMBLY PRIORITY ORDER (blueprint spec):
1. Session memory (always — current conversation)
2. Document memory (always if doc uploaded)
3. User profile (always if exists)
4. Policy portfolio (always if exists)
5. Knowledge memories (semantic search — relevant past insights) [Phase 2]
6. Conversation history (semantic search — past relevant convos) [Phase 2]
7. Outcome memories [Phase 2]

TOKEN BUDGET:
128K context - 4K system prompt - 2K tools - 4K response reserve = ~118K available
"""
from typing import Any, Dict, List, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# Max tokens to allocate per memory layer
TOKEN_BUDGET = {
    "session_history": 8000,     # ~40 turns at 200 tokens/turn
    "document_context": 20000,   # Large extractions can be detailed
    "user_profile": 500,
    "policy_portfolio": 3000,
    "knowledge_memories": 5000,  # Phase 2
    "conversation_history": 5000, # Phase 2
    "outcome_memories": 2000,    # Phase 2
}


async def assemble_context(
    user_id: str,
    session_id: str,
    query: str,
    uploaded_files: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Build full context for a request by pulling from all available memory layers.

    Returns dict that populates HibiscusState context fields.
    """
    context: Dict[str, Any] = {
        "session_history": [],
        "document_context": None,
        "user_profile": None,
        "policy_portfolio": [],
        "relevant_memories": [],
        "relevant_conversations": [],
    }

    # ── Layer 1: Session Memory (Redis) ──────────────────────────────────
    try:
        from hibiscus.memory.layers.session import get_session_messages
        messages = await get_session_messages(session_id, limit=10)
        context["session_history"] = messages
        logger.info("context_session_loaded", session_id=session_id, turns=len(messages))
    except Exception as e:
        logger.warning("context_session_failed", error=str(e))

    # ── Layer 6: Document Memory (MongoDB) ───────────────────────────────
    has_doc = bool(uploaded_files) or _references_document(query)
    if has_doc:
        try:
            from hibiscus.memory.layers.document import get_latest_document
            doc = await get_latest_document(user_id)
            if doc:
                context["document_context"] = doc
                logger.info(
                    "context_document_loaded",
                    doc_id=doc.get("doc_id", "?"),
                    has_extraction=bool(doc.get("extraction")),
                )
        except Exception as e:
            logger.warning("context_document_failed", error=str(e))

    # ── Layer 3: User Profile (PostgreSQL) ── Phase 2 ────────────────────
    # context["user_profile"] = await get_user_profile(user_id)

    # ── Layer 3b: Policy Portfolio (PostgreSQL) ── Phase 2 ───────────────
    # context["policy_portfolio"] = await get_policy_portfolio(user_id)

    # ── Layers 4, 5, 7: Qdrant semantic search ── Phase 2 ────────────────
    # context["relevant_memories"] = await search_knowledge(user_id, query)
    # context["relevant_conversations"] = await search_conversations(user_id, query)

    return context


def _references_document(message: str) -> bool:
    """Check if the message references an uploaded document."""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in [
        "my policy", "this policy", "the document", "uploaded",
        "what did i upload", "my insurance", "the policy i",
    ])


def estimate_tokens(text: str) -> int:
    """Rough token estimate (4 chars ≈ 1 token for English, 2-3 chars for Hindi)."""
    return len(text) // 3


def format_context_for_prompt(context: Dict[str, Any]) -> str:
    """Format assembled context as a string for injection into prompts."""
    parts = []

    if context.get("session_history"):
        parts.append("## Recent Conversation History")
        for msg in context["session_history"][-6:]:  # Last 6 for context
            role = "User" if msg.get("role") == "user" else "Hibiscus"
            content = msg.get("content", "")[:300]  # Truncate long messages
            parts.append(f"{role}: {content}")

    if context.get("document_context"):
        doc = context["document_context"]
        parts.append("\n## User's Policy Document")
        if doc.get("filename"):
            parts.append(f"File: {doc['filename']}")
        if doc.get("extraction"):
            extraction = doc["extraction"]
            parts.append(f"Policy Type: {extraction.get('policy_type', 'Insurance Policy')}")
            parts.append(f"Insurer: {extraction.get('insurer', 'Unknown')}")
            if extraction.get("sum_insured"):
                parts.append(f"Sum Insured: {extraction['sum_insured']}")

    if context.get("user_profile"):
        profile = context["user_profile"]
        parts.append("\n## User Profile")
        parts.append(f"Age: {profile.get('age', 'Unknown')}, Location: {profile.get('city', 'India')}")

    return "\n".join(parts) if parts else ""
