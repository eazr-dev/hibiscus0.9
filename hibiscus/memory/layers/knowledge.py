"""
Knowledge Memory — Layer 4 (Qdrant)
=====================================
Stores key facts extracted from conversations about the user.

Examples:
  "User's primary concern is child's education planning"
  "User was mis-sold a ULIP by SBI agent in 2019"
  "User's company provides ₹5L group health cover"
  "User prefers term insurance over investment-linked"

Collection: user_knowledge
Lifetime:   Indefinite — user preferences don't expire quickly.
            However, `get_relevant_insights` weights recent entries higher
            by boosting the score with a recency factor.

Why Qdrant?  Insights are free-text facts.  A new question about "best
coverage for children" should surface the stored insight "User concerned about
child's education" even though the wording differs.  Semantic search enables
this without manual keyword matching.

Insight types:
  preference  — things the user explicitly prefers ("I prefer online insurers")
  concern     — worries or fears ("worried about cancer coverage")
  fact        — objective facts ("company provides ₹5L group cover")
  history     — past events ("filed a claim in 2021, rejected")
  family      — family structure facts ("wife is diabetic, 2 kids")
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
import uuid
from typing import Any, Dict, List, Optional

import openai
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qdrant_models

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
COLLECTION_NAME = settings.qdrant_collection_insights
VECTOR_DIM = 1536
VALID_INSIGHT_TYPES = {"preference", "concern", "fact", "history", "family"}

# Recency weight: insights from the last 30 days get a +0.1 boost at scoring time
RECENCY_WINDOW_SECS = 30 * 86400
RECENCY_BOOST = 0.10

# ── Client singletons ─────────────────────────────────────────────────────────
_qdrant: Optional[AsyncQdrantClient] = None
_openai_client: Optional[openai.AsyncOpenAI] = None

# ── In-memory fallback ────────────────────────────────────────────────────────
_fallback_insights: List[Dict[str, Any]] = []


# ── Initialisation ────────────────────────────────────────────────────────────

async def _get_qdrant() -> Optional[AsyncQdrantClient]:
    """Lazily initialise Qdrant and ensure the user_knowledge collection exists."""
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

        existing = {c.name for c in (await client.get_collections()).collections}
        if COLLECTION_NAME not in existing:
            await client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=qdrant_models.VectorParams(
                    size=VECTOR_DIM,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )
            # Index user_id and insight_type for fast filtered search
            for field, schema in [
                ("user_id", qdrant_models.PayloadSchemaType.KEYWORD),
                ("insight_type", qdrant_models.PayloadSchemaType.KEYWORD),
            ]:
                await client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field,
                    field_schema=schema,
                )
            logger.info("qdrant_knowledge_collection_created", collection=COLLECTION_NAME)

        _qdrant = client
        logger.info("qdrant_knowledge_connected", collection=COLLECTION_NAME)
    except Exception as exc:
        logger.warning("qdrant_knowledge_unavailable", error=str(exc), fallback="in_memory")
        _qdrant = None

    return _qdrant


def _get_openai() -> openai.AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


async def _embed(text: str) -> Optional[List[float]]:
    """Embed text using OpenAI text-embedding-3-small."""
    if not settings.openai_api_key:
        return None
    try:
        resp = await _get_openai().embeddings.create(
            model=settings.embedding_model,
            input=text[:8000],
        )
        return resp.data[0].embedding
    except Exception as exc:
        logger.warning("knowledge_embed_failed", error=str(exc))
        return None


# ── Public API ────────────────────────────────────────────────────────────────

async def store_insight(
    user_id: str,
    insight_text: str,
    insight_type: str,
    confidence: float = 0.8,
) -> bool:
    """Embed and persist a single user insight.

    Args:
        user_id:      EAZR user identifier.
        insight_text: Plain-text fact / preference / concern (1-3 sentences).
        insight_type: One of: preference, concern, fact, history, family.
        confidence:   Extraction confidence 0.0–1.0.

    Returns:
        True on success (Qdrant or fallback), False if nothing was stored.
    """
    if insight_type not in VALID_INSIGHT_TYPES:
        logger.warning(
            "knowledge_invalid_type",
            insight_type=insight_type,
            valid=list(VALID_INSIGHT_TYPES),
        )
        insight_type = "fact"   # Default to generic

    vector = await _embed(insight_text)
    now = time.time()

    payload = {
        "user_id": user_id,
        "content": insight_text,
        "insight_type": insight_type,
        "confidence": round(confidence, 4),
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
                "knowledge_insight_stored",
                user_id=user_id,
                insight_type=insight_type,
                content_preview=insight_text[:80],
                confidence=confidence,
            )
            return True
        except Exception as exc:
            logger.warning("knowledge_store_failed", error=str(exc))

    # Fallback
    _fallback_insights.append({"id": point_id, "payload": payload, "vector": vector})
    logger.info("knowledge_insight_fallback_stored", user_id=user_id, insight_type=insight_type)
    return False


async def get_relevant_insights(
    user_id: str,
    query: str,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """Return the most semantically relevant stored insights for the current query.

    Recency boost: insights stored in the last 30 days have their similarity
    score boosted by RECENCY_BOOST so that fresh context surfaces ahead of
    stale (but semantically similar) facts.

    Args:
        user_id: EAZR user identifier.
        query:   Current user message or intent description.
        top_k:   Maximum results to return.

    Returns:
        List of dicts: {content, type, confidence, timestamp, score}
    """
    vector = await _embed(query)
    if not vector:
        return _fallback_get_insights(user_id, top_k)

    client = await _get_qdrant()
    if not client:
        return _fallback_get_insights(user_id, top_k)

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
            limit=top_k * 2,   # Fetch extra; we re-rank and trim
            with_payload=True,
            score_threshold=0.35,
        )

        now = time.time()
        ranked = []
        for r in results:
            p = r.payload or {}
            raw_score = float(r.score)
            ts = p.get("timestamp", 0)
            is_recent = (now - ts) <= RECENCY_WINDOW_SECS
            boosted_score = round(raw_score + (RECENCY_BOOST if is_recent else 0.0), 4)
            ranked.append({
                "content": p.get("content", ""),
                "type": p.get("insight_type", "fact"),
                "confidence": p.get("confidence", 0.5),
                "timestamp": ts,
                "score": boosted_score,
            })

        # Re-sort by boosted score descending
        ranked.sort(key=lambda x: x["score"], reverse=True)
        ranked = ranked[:top_k]

        logger.info(
            "knowledge_insights_retrieved",
            user_id=user_id,
            query_preview=query[:60],
            results=len(ranked),
        )
        return ranked

    except Exception as exc:
        logger.warning("knowledge_search_failed", error=str(exc))
        return _fallback_get_insights(user_id, top_k)


async def get_all_insights(user_id: str) -> List[Dict[str, Any]]:
    """Return every stored insight for a user (for profile display / admin).

    Results are sorted most-recent first.
    """
    client = await _get_qdrant()
    if client:
        try:
            results, _ = await client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="user_id",
                            match=qdrant_models.MatchValue(value=user_id),
                        )
                    ]
                ),
                limit=200,
                with_payload=True,
                with_vectors=False,
            )
            insights = []
            for r in results:
                p = r.payload or {}
                insights.append({
                    "id": str(r.id),
                    "content": p.get("content", ""),
                    "type": p.get("insight_type", "fact"),
                    "confidence": p.get("confidence", 0.5),
                    "timestamp": p.get("timestamp", 0),
                })
            # Sort most-recent first
            insights.sort(key=lambda x: x["timestamp"], reverse=True)
            return insights
        except Exception as exc:
            logger.warning("knowledge_get_all_failed", user_id=user_id, error=str(exc))

    # Fallback
    return _fallback_get_insights(user_id, top_k=500)


# ── Fallback helpers ──────────────────────────────────────────────────────────

def _fallback_get_insights(user_id: str, top_k: int) -> List[Dict[str, Any]]:
    """Return in-memory insights for a user, most-recent first."""
    user_insights = [
        i["payload"]
        for i in _fallback_insights
        if i["payload"].get("user_id") == user_id
    ]
    user_insights.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return [
        {
            "content": i.get("content", ""),
            "type": i.get("insight_type", "fact"),
            "confidence": i.get("confidence", 0.5),
            "timestamp": i.get("timestamp", 0),
            "score": 0.5,
        }
        for i in user_insights[:top_k]
    ]
