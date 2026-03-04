"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Memory assembler — merges 6 memory layers into unified context for each conversation turn.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
from typing import Any, Dict, List, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# Maximum total characters across all layers to prevent context overflow.
# At ~4 chars per token, 12000 chars is roughly 3000 tokens.
MAX_CONTEXT_CHARS = 12000

# Priority-based character limits per layer (higher priority = more budget).
# Must sum to <= MAX_CONTEXT_CHARS.
_LAYER_CHAR_LIMITS = {
    "document_context": 4000,     # Highest priority — active policy data
    "session_history": 3000,      # Recent conversation for continuity
    "user_profile": 800,          # Compact demographics
    "policy_portfolio": 1500,     # Known policies
    "knowledge_memories": 1500,   # Relevant past insights
    "conversation_history": 1200, # Past session context
}

async def assemble_context(
    user_id: str,
    session_id: str,
    query: str,
    uploaded_files: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build full context for a request by pulling from all available memory layers.

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

    has_doc = bool(uploaded_files) or _references_document(query)

    # ── Parallel fetch all memory layers with asyncio.gather() ──────────────
    # All 6 layers run concurrently — cuts total assembly time by ~5x vs sequential
    async def _fetch_session() -> List[Dict]:
        try:
            from hibiscus.memory.layers.session import get_session_messages
            messages = await get_session_messages(session_id, limit=10)
            logger.info("context_session_loaded", session_id=session_id, turns=len(messages))
            return messages
        except Exception as e:
            logger.warning("context_session_failed", error=str(e))
            return []

    async def _fetch_document() -> Optional[Dict]:
        if not has_doc:
            return None
        try:
            from hibiscus.memory.layers.document import get_latest_document
            doc = await get_latest_document(user_id)
            if doc:
                logger.info(
                    "context_document_loaded",
                    doc_id=doc.get("doc_id", "?"),
                    has_extraction=bool(doc.get("extraction")),
                )
            return doc
        except Exception as e:
            logger.warning("context_document_failed", error=str(e))
            return None

    async def _fetch_profile() -> Optional[Dict]:
        try:
            from hibiscus.memory.layers.profile import get_user_profile
            profile = await get_user_profile(user_id)
            if profile:
                logger.info(
                    "context_profile_loaded",
                    user_id=user_id,
                    age=profile.get("age"),
                    city=profile.get("city"),
                )
            else:
                logger.info("context_profile_not_found", user_id=user_id)
            return profile
        except Exception as e:
            logger.warning("context_profile_failed", user_id=user_id, error=str(e))
            return None

    async def _fetch_portfolio() -> List:
        try:
            from hibiscus.memory.layers.portfolio import get_user_portfolio
            portfolio = await get_user_portfolio(user_id)
            logger.info(
                "context_portfolio_loaded",
                user_id=user_id,
                policy_count=len(portfolio),
            )
            return portfolio
        except Exception as e:
            logger.warning("context_portfolio_failed", user_id=user_id, error=str(e))
            return []

    async def _fetch_knowledge() -> List:
        try:
            from hibiscus.memory.layers.knowledge import get_relevant_insights
            insights = await get_relevant_insights(user_id, query, top_k=10)
            logger.info(
                "context_knowledge_loaded",
                user_id=user_id,
                insight_count=len(insights),
            )
            return insights
        except Exception as e:
            logger.warning("context_knowledge_failed", user_id=user_id, error=str(e))
            return []

    async def _fetch_conversations() -> List:
        try:
            from hibiscus.memory.layers.conversation import search_conversation_history
            past_convos = await search_conversation_history(user_id, query, top_k=5)
            logger.info(
                "context_conversations_loaded",
                user_id=user_id,
                conv_count=len(past_convos),
            )
            return past_convos
        except Exception as e:
            logger.warning("context_conversations_failed", user_id=user_id, error=str(e))
            return []

    async def _fetch_outcomes() -> List:
        try:
            from hibiscus.memory.layers.outcome import get_user_outcomes
            outcomes = await get_user_outcomes(user_id, limit=10)
            logger.info(
                "context_outcomes_loaded",
                user_id=user_id,
                outcome_count=len(outcomes),
            )
            return outcomes
        except Exception as e:
            logger.warning("context_outcomes_failed", user_id=user_id, error=str(e))
            return []

    (
        session_history,
        document_context,
        user_profile,
        policy_portfolio,
        relevant_memories,
        relevant_conversations,
        outcome_memories,
    ) = await asyncio.gather(
        _fetch_session(),
        _fetch_document(),
        _fetch_profile(),
        _fetch_portfolio(),
        _fetch_knowledge(),
        _fetch_conversations(),
        _fetch_outcomes(),
    )

    context["session_history"] = session_history
    context["document_context"] = document_context
    context["user_profile"] = user_profile
    context["policy_portfolio"] = policy_portfolio
    context["relevant_memories"] = relevant_memories
    context["relevant_conversations"] = relevant_conversations
    context["outcome_memories"] = outcome_memories

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


def _truncate_section(text: str, max_chars: int) -> str:
    """Truncate a context section to max_chars, preserving whole lines."""
    if len(text) <= max_chars:
        return text
    # Truncate at the last newline before the limit
    truncated = text[:max_chars]
    last_nl = truncated.rfind("\n")
    if last_nl > max_chars // 2:
        truncated = truncated[:last_nl]
    return truncated + "\n... (truncated)"


def format_context_for_prompt(context: Dict[str, Any]) -> str:
    """Format assembled context as a string for injection into prompts.

    Each layer is truncated to its priority-based character limit
    (see _LAYER_CHAR_LIMITS) so the total stays under MAX_CONTEXT_CHARS.
    """
    parts = []

    # ── Session history ───────────────────────────────────────────────────────
    if context.get("session_history"):
        section_parts = ["## Recent Conversation History"]
        for msg in context["session_history"][-6:]:   # Last 6 for context
            role = "User" if msg.get("role") == "user" else "Hibiscus"
            content = msg.get("content", "")[:300]     # Truncate long messages
            section_parts.append(f"{role}: {content}")
        section_text = _truncate_section("\n".join(section_parts), _LAYER_CHAR_LIMITS["session_history"])
        parts.append(section_text)

    # ── Document context ──────────────────────────────────────────────────────
    if context.get("document_context"):
        doc = context["document_context"]
        doc_parts = ["\n## User's Policy Document"]
        if doc.get("filename"):
            doc_parts.append(f"File: {doc['filename']}")
        if doc.get("extraction"):
            extraction = doc["extraction"]
            doc_parts.append(f"Policy Type: {extraction.get('policy_type', 'Insurance Policy')}")
            doc_parts.append(f"Insurer: {extraction.get('insurer', 'Unknown')}")
            if extraction.get("sum_insured"):
                doc_parts.append(f"Sum Insured: ₹{extraction['sum_insured']:,}")
        section_text = _truncate_section("\n".join(doc_parts), _LAYER_CHAR_LIMITS["document_context"])
        parts.append(section_text)

    # ── User profile ──────────────────────────────────────────────────────────
    if context.get("user_profile"):
        profile = context["user_profile"]
        profile_section = ["\n## User Profile"]
        profile_parts = []
        if profile.get("age"):
            profile_parts.append(f"Age: {profile['age']}")
        if profile.get("city"):
            city_str = profile["city"]
            if profile.get("state"):
                city_str += f", {profile['state']}"
            if profile.get("city_tier"):
                city_str += f" (Tier {profile['city_tier']})"
            profile_parts.append(f"Location: {city_str}")
        if profile.get("income_band"):
            profile_parts.append(f"Income: {profile['income_band']}")
        if profile.get("family_structure"):
            fam = profile["family_structure"].replace("_", " ").title()
            if profile.get("num_dependents"):
                fam += f" ({profile['num_dependents']} dependents)"
            profile_parts.append(f"Family: {fam}")
        if profile.get("risk_tolerance"):
            profile_parts.append(f"Risk tolerance: {profile['risk_tolerance']}")
        if profile.get("health_conditions_categories"):
            cats = ", ".join(profile["health_conditions_categories"])
            profile_parts.append(f"Health categories: {cats}")
        if profile_parts:
            profile_section.append(", ".join(profile_parts))
        section_text = _truncate_section("\n".join(profile_section), _LAYER_CHAR_LIMITS["user_profile"])
        parts.append(section_text)

    # ── Policy portfolio ──────────────────────────────────────────────────────
    if context.get("policy_portfolio"):
        portfolio = context["policy_portfolio"]
        port_parts = ["\n## Known Policies"]
        for p in portfolio[:5]:   # Cap at 5 to guard token budget
            line_parts = []
            if p.get("policy_type"):
                line_parts.append(p["policy_type"].replace("_", " ").title())
            if p.get("insurer"):
                line_parts.append(f"by {p['insurer']}")
            if p.get("sum_insured"):
                line_parts.append(f"SI: ₹{int(p['sum_insured']):,}")
            if p.get("annual_premium"):
                line_parts.append(f"Premium: ₹{int(p['annual_premium']):,}/yr")
            if p.get("payment_status"):
                line_parts.append(f"[{p['payment_status']}]")
            port_parts.append("  - " + ", ".join(line_parts))
        section_text = _truncate_section("\n".join(port_parts), _LAYER_CHAR_LIMITS["policy_portfolio"])
        parts.append(section_text)

    # ── Knowledge insights ────────────────────────────────────────────────────
    if context.get("relevant_memories"):
        know_parts = ["\n## User Insights (from past conversations)"]
        for ins in context["relevant_memories"][:5]:
            itype = ins.get("type", "fact").upper()
            content = ins.get("content", "")[:200]
            know_parts.append(f"  [{itype}] {content}")
        section_text = _truncate_section("\n".join(know_parts), _LAYER_CHAR_LIMITS["knowledge_memories"])
        parts.append(section_text)

    # ── Relevant past conversations ───────────────────────────────────────────
    if context.get("relevant_conversations"):
        conv_parts = ["\n## Relevant Past Sessions"]
        for conv in context["relevant_conversations"][:3]:
            content = conv.get("content", "")[:200]
            intent = conv.get("intent", "")
            if intent:
                conv_parts.append(f"  [{intent}] {content}")
            else:
                conv_parts.append(f"  {content}")
        section_text = _truncate_section("\n".join(conv_parts), _LAYER_CHAR_LIMITS["conversation_history"])
        parts.append(section_text)

    # Final safety: truncate entire context to MAX_CONTEXT_CHARS
    result = "\n".join(parts) if parts else ""
    if len(result) > MAX_CONTEXT_CHARS:
        result = result[:MAX_CONTEXT_CHARS] + "\n... (context truncated)"
    return result
