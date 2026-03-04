"""
Qdrant RAG Client
=================
Async Qdrant connection with hybrid search (dense + sparse BM25 RRF fusion).

Collections:
  - insurance_knowledge   : IRDAI circulars, policy wordings, glossary, tax rules, claims processes
  - user_conversations    : Per-user conversation history for retrieval
  - user_knowledge        : Per-user extracted policy facts and insights

Hybrid search strategy:
  - Dense  : GLM embedding-2 (1024 dims) via Zhipu AI
  - Sparse : BM25 via Qdrant's built-in sparse vectors
  - Fusion : Reciprocal Rank Fusion (RRF) — balances semantic + keyword matching
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SparseVector,
)

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
VECTOR_SIZE = 1024          # GLM embedding-2 dimensions (changed from 1536 OpenAI)
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"

# RRF rank constant — standard value per the original paper
RRF_K = 60

# Collections managed by Hibiscus
COLLECTIONS = {
    settings.qdrant_collection_knowledge:    "Insurance knowledge base (circulars, glossary, rules)",
    settings.qdrant_collection_conversations: "User conversation history",
    settings.qdrant_collection_insights:     "Per-user extracted policy insights",
}


class QdrantRAGClient:
    """
    Production-grade async Qdrant client with hybrid search.

    Usage:
        await rag_client.init_collections()
        results = await rag_client.search("what is copay", "insurance_knowledge")
    """

    def __init__(self) -> None:
        self._client: Optional[AsyncQdrantClient] = None
        self._available: bool = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Establish Qdrant connection. Called at app startup."""
        try:
            self._client = AsyncQdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                timeout=10.0,
                check_compatibility=False,  # client 1.17 vs server 1.12 version mismatch
            )
            # Health-check by listing collections
            await self._client.get_collections()
            self._available = True
            logger.info(
                "qdrant_connected",
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
        except Exception as exc:
            self._available = False
            self._client = None
            logger.warning(
                "qdrant_connection_failed",
                error=str(exc),
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                fallback="graceful_degradation",
            )

    async def close(self) -> None:
        """Close Qdrant connection. Called at app shutdown."""
        if self._client:
            await self._client.close()
            self._client = None
            self._available = False
            logger.info("qdrant_disconnected")

    # ── Collection Management ─────────────────────────────────────────────────

    async def init_collections(self) -> None:
        """
        Create Qdrant collections if they do not exist.

        Each collection uses:
        - Named dense vector  : "dense"  — cosine similarity for semantic search
        - Named sparse vector : "sparse" — BM25 for keyword/exact-match search
        """
        if not self._available or not self._client:
            logger.warning("qdrant_init_collections_skipped", reason="qdrant_unavailable")
            return

        existing_collections = set()
        try:
            collection_list = await self._client.get_collections()
            existing_collections = {c.name for c in collection_list.collections}
        except Exception as exc:
            logger.error("qdrant_list_collections_failed", error=str(exc))
            return

        for collection_name, description in COLLECTIONS.items():
            if collection_name in existing_collections:
                logger.info(
                    "qdrant_collection_exists",
                    collection=collection_name,
                )
                continue

            try:
                await self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        DENSE_VECTOR_NAME: VectorParams(
                            size=VECTOR_SIZE,
                            distance=Distance.COSINE,
                            on_disk=False,  # Keep in RAM for fast retrieval
                        )
                    },
                    sparse_vectors_config={
                        SPARSE_VECTOR_NAME: SparseVectorParams(
                            index=SparseIndexParams(
                                on_disk=False,
                            )
                        )
                    },
                    optimizers_config=qmodels.OptimizersConfigDiff(
                        indexing_threshold=10_000,  # Start indexing after 10K vectors
                    ),
                    hnsw_config=qmodels.HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                        full_scan_threshold=10_000,
                    ),
                )
                logger.info(
                    "qdrant_collection_created",
                    collection=collection_name,
                    description=description,
                    vector_size=VECTOR_SIZE,
                )
            except Exception as exc:
                logger.error(
                    "qdrant_collection_create_failed",
                    collection=collection_name,
                    error=str(exc),
                )

    # ── Embedding ─────────────────────────────────────────────────────────────

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get OpenAI text-embedding-3-small embedding for a text string.
        Imported here to avoid circular imports with embeddings module.
        """
        from hibiscus.knowledge.rag.embeddings import get_embedding
        return await get_embedding(text)

    # ── BM25 Sparse Vector ────────────────────────────────────────────────────

    def _build_sparse_vector(self, text: str) -> SparseVector:
        """
        Build a lightweight BM25-style sparse vector from tokenized text.

        This is a client-side approximation. For production at scale, use
        Qdrant's fastembed sparse encoder (SPLADE++). This implementation
        uses TF-normalized token hashing for zero-dependency operation.

        Token hash → index, TF score → value.
        Sufficient for insurance domain keyword matching.
        """
        import re
        from collections import Counter

        # Tokenize: lowercase, split on non-alphanumeric, keep Indian numerals
        tokens = re.findall(r"[a-z0-9₹]+", text.lower())

        if not tokens:
            # Return a minimal sparse vector to avoid Qdrant validation error
            return SparseVector(indices=[0], values=[0.0])

        # Count term frequency
        tf_counts = Counter(tokens)
        total = len(tokens)

        indices: List[int] = []
        values: List[float] = []

        for token, count in tf_counts.items():
            # Hash to index in range [1, 2^20 - 1] (avoid 0)
            token_hash = hash(token) % (2**20 - 1) + 1
            # TF score (normalized)
            tf = count / total
            indices.append(token_hash)
            values.append(round(tf, 6))

        return SparseVector(indices=indices, values=values)

    # ── Search ────────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: dense (semantic) + sparse (BM25 keyword) with RRF fusion.

        Args:
            query          : Natural language query string
            collection     : Qdrant collection name
            top_k          : Number of results to return
            filter_metadata: Optional key-value filter on payload fields

        Returns:
            List of {content, source, score, metadata} dicts, sorted by RRF score desc.
            Returns [] on Qdrant unavailability (graceful degradation).
        """
        if not self._available or not self._client:
            logger.warning(
                "qdrant_search_skipped",
                reason="qdrant_unavailable",
                query_preview=query[:60],
            )
            return []

        start_ms = int(time.time() * 1000)

        try:
            # Build Qdrant filter if metadata filter provided
            qdrant_filter: Optional[Filter] = None
            if filter_metadata:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_metadata.items()
                ]
                qdrant_filter = Filter(must=conditions)

            # ── Dense search (qdrant-client >= 1.7 uses query_points) ─────
            dense_embedding = await self.get_embedding(query)

            dense_response = await self._client.query_points(
                collection_name=collection,
                query=dense_embedding,
                using=DENSE_VECTOR_NAME,
                query_filter=qdrant_filter,
                limit=top_k * 2,  # Fetch more for RRF fusion
                with_payload=True,
                with_vectors=False,
            )
            dense_results = dense_response.points

            # ── Sparse search ─────────────────────────────────────────────
            sparse_vector = self._build_sparse_vector(query)

            sparse_response = await self._client.query_points(
                collection_name=collection,
                query=sparse_vector,
                using=SPARSE_VECTOR_NAME,
                query_filter=qdrant_filter,
                limit=top_k * 2,
                with_payload=True,
                with_vectors=False,
            )
            sparse_results = sparse_response.points

            # ── RRF Fusion ────────────────────────────────────────────────
            fused = self._rrf_fusion(dense_results, sparse_results, k=RRF_K)

            # Take top_k after fusion
            top_results = fused[:top_k]

            latency_ms = int(time.time() * 1000) - start_ms
            logger.info(
                "qdrant_search_complete",
                collection=collection,
                query_preview=query[:60],
                results_dense=len(dense_results),
                results_sparse=len(sparse_results),
                results_fused=len(top_results),
                latency_ms=latency_ms,
            )

            return top_results

        except Exception as exc:
            latency_ms = int(time.time() * 1000) - start_ms
            logger.error(
                "qdrant_search_failed",
                collection=collection,
                query_preview=query[:60],
                error=str(exc),
                latency_ms=latency_ms,
            )
            return []

    def _rrf_fusion(
        self,
        dense_results: List[Any],
        sparse_results: List[Any],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) of dense and sparse result lists.

        Formula: RRF(d) = sum_r( 1 / (k + rank_r(d)) )
        Higher score = more relevant.
        """
        scores: Dict[str, float] = {}
        payloads: Dict[str, Any] = {}

        # Score dense results
        for rank, hit in enumerate(dense_results):
            doc_id = str(hit.id)
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
            payloads[doc_id] = hit.payload or {}

        # Score sparse results
        for rank, hit in enumerate(sparse_results):
            doc_id = str(hit.id)
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
            if doc_id not in payloads:
                payloads[doc_id] = hit.payload or {}

        # Sort by RRF score descending
        sorted_ids = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)

        results = []
        for doc_id in sorted_ids:
            payload = payloads[doc_id]
            results.append(
                {
                    "content": payload.get("content", ""),
                    "source": payload.get("source", ""),
                    "score": round(scores[doc_id], 6),
                    "metadata": {
                        k: v
                        for k, v in payload.items()
                        if k not in ("content",)
                    },
                }
            )

        return results

    # ── Upsert ────────────────────────────────────────────────────────────────

    async def upsert(
        self,
        collection: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 50,
    ) -> int:
        """
        Batch upsert documents into Qdrant collection.

        Each document dict must have:
            content    : str   — text content to embed + search
            metadata   : dict  — arbitrary payload (source, category, date, etc.)
            id         : str   — optional stable ID (generated if missing)

        Returns:
            Number of points successfully upserted.
        """
        if not self._available or not self._client:
            logger.warning(
                "qdrant_upsert_skipped",
                reason="qdrant_unavailable",
                doc_count=len(documents),
            )
            return 0

        if not documents:
            return 0

        total_upserted = 0
        start_ms = int(time.time() * 1000)

        # Process in batches
        for batch_start in range(0, len(documents), batch_size):
            batch = documents[batch_start : batch_start + batch_size]

            try:
                points = await self._build_points(batch)
                await self._upsert_with_retry(collection, points)
                total_upserted += len(points)

            except Exception as exc:
                logger.error(
                    "qdrant_upsert_batch_failed",
                    collection=collection,
                    batch_start=batch_start,
                    batch_size=len(batch),
                    error=str(exc),
                )
                # Continue with remaining batches
                continue

        latency_ms = int(time.time() * 1000) - start_ms
        logger.info(
            "qdrant_upsert_complete",
            collection=collection,
            total_documents=len(documents),
            total_upserted=total_upserted,
            latency_ms=latency_ms,
        )

        return total_upserted

    async def _build_points(self, documents: List[Dict[str, Any]]) -> List[PointStruct]:
        """Build Qdrant PointStructs with dense + sparse vectors from document list."""
        from hibiscus.knowledge.rag.embeddings import get_embeddings_batch

        contents = [doc["content"] for doc in documents]
        dense_embeddings = await get_embeddings_batch(contents)

        points = []
        for doc, dense_vec in zip(documents, dense_embeddings):
            content = doc["content"]
            metadata = doc.get("metadata", {})
            point_id = doc.get("id") or str(uuid.uuid4())

            sparse_vec = self._build_sparse_vector(content)

            payload = {"content": content, **metadata}

            point = PointStruct(
                id=point_id,
                vector={
                    DENSE_VECTOR_NAME: dense_vec,
                    SPARSE_VECTOR_NAME: sparse_vec,
                },
                payload=payload,
            )
            points.append(point)

        return points

    async def _upsert_with_retry(
        self,
        collection: str,
        points: List[PointStruct],
        max_retries: int = 3,
    ) -> None:
        """Upsert points with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                await self._client.upsert(
                    collection_name=collection,
                    points=points,
                    wait=True,  # Wait for indexing before returning
                )
                return
            except Exception as exc:
                if attempt == max_retries - 1:
                    raise
                wait_secs = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    "qdrant_upsert_retry",
                    attempt=attempt + 1,
                    wait_secs=wait_secs,
                    error=str(exc),
                )
                await asyncio.sleep(wait_secs)

    # ── Convenience ───────────────────────────────────────────────────────────

    @property
    def is_available(self) -> bool:
        """Whether Qdrant is connected and healthy."""
        return self._available

    async def count(self, collection: str) -> int:
        """Return the number of points in a collection."""
        if not self._available or not self._client:
            return 0
        try:
            result = await self._client.count(collection_name=collection)
            return result.count
        except Exception as exc:
            logger.warning("qdrant_count_failed", collection=collection, error=str(exc))
            return 0


# ── Module-level singleton ────────────────────────────────────────────────────
rag_client = QdrantRAGClient()


async def init_rag() -> None:
    """
    Initialize the RAG client. Call this at application startup.
    Connects to Qdrant and ensures all collections exist.
    Gracefully handles Qdrant being unavailable (returns, logs warning).
    """
    await rag_client.connect()
    if rag_client.is_available:
        await rag_client.init_collections()
        logger.info(
            "rag_initialized",
            collections=list(COLLECTIONS.keys()),
        )
    else:
        logger.warning(
            "rag_initialized_degraded",
            reason="qdrant_unavailable",
            impact="search_returns_empty_results",
        )


async def close_rag() -> None:
    """
    Close the RAG client. Call this at application shutdown.
    """
    await rag_client.close()
    logger.info("rag_closed")
