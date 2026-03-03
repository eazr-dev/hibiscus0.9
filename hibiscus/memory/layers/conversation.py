"""
Conversation Memory — Layer 2 (Qdrant)
=======================================
Stores past conversation summaries indexed semantically.
Enables: "As we discussed last time..." cross-session memory.

Collection: user_conversations
Lifetime:   90 days (TTL filter on retrieval)
Key:        user_id + semantic query for retrieval

Why Qdrant?  Every summary is embedded so the system can surface the most
semantically *relevant* past session, not just the most *recent* one.  A user
asking about maternity benefits today should get context from the session three
months ago where they also asked about maternity — even if they had many other
sessions in between.
"""
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import openai
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
COLLECTION_NAME = settings.qdrant_collection_conversations
VECTOR_DIM = 1536                       # text-embedding-3-small
CONVERSATION_TTL_DAYS = 90
SUMMARY_MAX_MESSAGES = 20               # Last N messages used for summarisation

# ── Client singletons ─────────────────────────────────────────────────────────
_qdrant: Optional[AsyncQdrantClient] = None
_openai: Optional[openai.AsyncOpenAI] = None

# ── In-memory fallback ────────────────────────────────────────────────────────
_fallback_store: List[Dict[str, Any]] = []


# ── Initialisation ────────────────────────────────────────────────────────────

async def _get_qdrant() -> Optional[AsyncQdrantClient]:
    """Lazily initialise Qdrant client and ensure collection exists."""
    global _qdrant
    if _qdrant is not None:
        return _qdrant

    try:
        client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=10,
        )
        await client.get_collections()   # Connection check

        # Create collection if it does not exist
        existing = {c.name for c in (await client.get_collections()).collections}
        if COLLECTION_NAME not in existing:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=qdrant_models.VectorParams(
                    size=VECTOR_DIM,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )
            # Index the user_id field for fast filtered search
            await client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="user_id",
                field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
            )
            logger.info("qdrant_conversation_collection_created", collection=COLLECTION_NAME)

        _qdrant = client
        logger.info("qdrant_conversation_connected", collection=COLLECTION_NAME)
    except Exception as exc:
        logger.warning("qdrant_conversation_unavailable", error=str(exc), fallback="in_memory")
        _qdrant = None

    return _qdrant


def _get_openai() -> openai.AsyncOpenAI:
    """Lazily initialise OpenAI client (used only for embeddings)."""
    global _openai
    if _openai is None:
        _openai = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai


async def _embed(text: str) -> Optional[List[float]]:
    """Generate a text embedding using OpenAI text-embedding-3-small."""
    if not settings.openai_api_key:
        logger.warning("embedding_skipped", reason="no_openai_key")
        return None
    try:
        client = _get_openai()
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=text[:8000],   # Guard against extremely long texts
        )
        return response.data[0].embedding
    except Exception as exc:
        logger.warning("embedding_failed", error=str(exc))
        return None


# ── TTL helper ────────────────────────────────────────────────────────────────

def _is_within_ttl(timestamp: float) -> bool:
    """Return True if the record is within the 90-day retention window."""
    age_days = (time.time() - timestamp) / 86400
    return age_days <= CONVERSATION_TTL_DAYS


# ── Public API ────────────────────────────────────────────────────────────────

async def store_conversation_summary(
    user_id: str,
    session_id: str,
    summary: str,
    intent: str,
    category: str,
) -> bool:
    """Embed and store a conversation summary in Qdrant.

    Args:
        user_id:    EAZR user identifier.
        session_id: The session being summarised.
        summary:    2–4 sentence plain-text summary of the conversation.
        intent:     Primary intent label (e.g. "policy_analysis", "gap_check").
        category:   Topic category (e.g. "health", "life_term", "tax").

    Returns:
        True on success, False on failure (caller does not need to retry).
    """
    vector = await _embed(summary)
    now = time.time()

    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "content": summary,
        "intent": intent,
        "category": category,
        "timestamp": now,
    }
    point_id = str(uuid.uuid4())

    client = await _get_qdrant()
    if client and vector:
        try:
            await client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    qdrant_models.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
            logger.info(
                "conversation_summary_stored",
                user_id=user_id,
                session_id=session_id,
                intent=intent,
                category=category,
            )
            return True
        except Exception as exc:
            logger.warning("conversation_summary_store_failed", error=str(exc))

    # Fallback: in-memory list (no vector search possible, but data is kept)
    _fallback_store.append({"id": point_id, "payload": payload, "vector": vector})
    logger.info("conversation_summary_fallback_stored", session_id=session_id)
    return False


async def search_conversation_history(
    user_id: str,
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Semantically search past conversation summaries for a user.

    Args:
        user_id: EAZR user identifier.
        query:   Current user message / intent.
        top_k:   Maximum number of results to return.

    Returns:
        List of dicts: {content, session_id, timestamp, intent, confidence}
        Empty list on any failure.
    """
    vector = await _embed(query)
    if not vector:
        return _fallback_search(user_id, top_k)

    client = await _get_qdrant()
    if not client:
        return _fallback_search(user_id, top_k)

    try:
        results = await client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            query_filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="user_id",
                        match=qdrant_models.MatchValue(value=user_id),
                    )
                ]
            ),
            limit=top_k * 2,   # Fetch extra to allow TTL filtering
            with_payload=True,
            score_threshold=0.40,
        )

        hits = []
        for r in results:
            p = r.payload or {}
            ts = p.get("timestamp", 0)
            if not _is_within_ttl(ts):
                continue   # Skip expired records (soft TTL)
            hits.append({
                "content": p.get("content", ""),
                "session_id": p.get("session_id", ""),
                "timestamp": ts,
                "intent": p.get("intent", ""),
                "category": p.get("category", ""),
                "confidence": round(float(r.score), 4),
            })
            if len(hits) >= top_k:
                break

        logger.info(
            "conversation_history_searched",
            user_id=user_id,
            query_preview=query[:60],
            results=len(hits),
        )
        return hits

    except Exception as exc:
        logger.warning("conversation_history_search_failed", error=str(exc))
        return _fallback_search(user_id, top_k)


def _fallback_search(user_id: str, top_k: int) -> List[Dict[str, Any]]:
    """Return most-recent in-memory summaries for a user (no semantic ranking)."""
    user_records = [
        r["payload"]
        for r in _fallback_store
        if r["payload"].get("user_id") == user_id
        and _is_within_ttl(r["payload"].get("timestamp", 0))
    ]
    # Sort most-recent first; no semantic ranking in fallback mode
    user_records.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return [
        {
            "content": r.get("content", ""),
            "session_id": r.get("session_id", ""),
            "timestamp": r.get("timestamp", 0),
            "intent": r.get("intent", ""),
            "category": r.get("category", ""),
            "confidence": 0.5,   # Unknown without vector similarity
        }
        for r in user_records[:top_k]
    ]


async def extract_and_store_summary(
    user_id: str,
    session_id: str,
    messages: List[Dict[str, Any]],
) -> Optional[str]:
    """Generate a 2-sentence conversation summary via DeepSeek V3.2 and store it.

    Args:
        user_id:    EAZR user identifier.
        session_id: Session being summarised.
        messages:   List of {role, content} message dicts.

    Returns:
        The generated summary string, or None on failure.
    """
    if not messages:
        return None

    # Use the last SUMMARY_MAX_MESSAGES turns
    recent = messages[-SUMMARY_MAX_MESSAGES:]
    conversation_text = "\n".join(
        f"{m.get('role', 'user').upper()}: {str(m.get('content', ''))[:500]}"
        for m in recent
    )

    prompt_messages = [
        {
            "role": "system",
            "content": (
                "You are a conversation summariser for an Indian insurance AI platform. "
                "Summarise the following conversation in exactly 2 sentences. "
                "Include: (1) what the user asked or was concerned about, "
                "(2) the key advice or information provided. "
                "Use concise, factual language. No bullet points. Plain sentences only."
            ),
        },
        {
            "role": "user",
            "content": f"Conversation to summarise:\n\n{conversation_text}",
        },
    ]

    try:
        from hibiscus.llm.router import call_llm

        result = await call_llm(
            messages=prompt_messages,
            tier="deepseek_v3",
            purpose="conversation_summary",
        )
        summary = result.get("content", "").strip()
        if not summary:
            return None

        # Detect a rough intent and category from the conversation text
        intent = _infer_intent(conversation_text)
        category = _infer_category(conversation_text)

        await store_conversation_summary(
            user_id=user_id,
            session_id=session_id,
            summary=summary,
            intent=intent,
            category=category,
        )
        logger.info(
            "conversation_summary_extracted",
            user_id=user_id,
            session_id=session_id,
            summary_len=len(summary),
            intent=intent,
        )
        return summary

    except Exception as exc:
        logger.warning("conversation_summary_extraction_failed", error=str(exc))
        return None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _infer_intent(text: str) -> str:
    """Heuristic intent detection from conversation text."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["upload", "analyze", "analysis", "pdf", "policy doc"]):
        return "policy_analysis"
    if any(kw in text_lower for kw in ["gap", "missing", "not covered", "inadequate"]):
        return "gap_check"
    if any(kw in text_lower for kw in ["premium", "cost", "price", "afford", "emi", "ipf"]):
        return "premium_finance"
    if any(kw in text_lower for kw in ["claim", "settle", "reject", "hospital"]):
        return "claim_support"
    if any(kw in text_lower for kw in ["tax", "80c", "80d", "deduction", "section"]):
        return "tax_planning"
    if any(kw in text_lower for kw in ["compare", "best", "recommend", "suggest", "which"]):
        return "recommendation"
    if any(kw in text_lower for kw in ["term", "life", "maturity", "death", "nominee"]):
        return "life_insurance"
    return "general_query"


def _infer_category(text: str) -> str:
    """Heuristic category detection from conversation text."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["health", "medical", "hospital", "mediclaim"]):
        return "health"
    if any(kw in text_lower for kw in ["term", "life", "ulip", "endowment", "lic"]):
        return "life"
    if any(kw in text_lower for kw in ["motor", "car", "bike", "vehicle", "accident"]):
        return "motor"
    if any(kw in text_lower for kw in ["travel", "overseas", "trip", "abroad"]):
        return "travel"
    if any(kw in text_lower for kw in ["tax", "80d", "80c", "section"]):
        return "tax"
    return "general"
