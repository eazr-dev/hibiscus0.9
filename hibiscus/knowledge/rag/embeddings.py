"""
Embedding Model Configuration
==============================
OpenAI text-embedding-3-small (1536 dims) — used for all RAG vector operations.

Design decisions:
  - Single embedding model across all collections for consistency
  - Batch API for ingestion (max 100 texts per call per OpenAI limits)
  - Tenacity retry for rate limit / transient failures
  - Cost tracking: log token usage so we can calculate embedding spend
  - Fallback: return zero vector (with warning) if OpenAI unavailable
    Consequence: those chunks will not match anything — acceptable for graceful degradation

Costs (as of 2025):
  - text-embedding-3-small: $0.020 per million tokens
  - Average chunk ~200 tokens → ~₹0.0003 per chunk
  - Full corpus of 10K chunks → ~₹3 total
"""
import asyncio
import time
from typing import List, Optional

import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
MAX_BATCH_SIZE = 100        # OpenAI batch limit
MAX_TEXT_TOKENS = 8191      # text-embedding-3-small context window


def _get_openai_client() -> openai.AsyncOpenAI:
    """Lazy-create OpenAI async client."""
    return openai.AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=30.0,
        max_retries=0,  # We handle retries with tenacity
    )


# ── Single embedding ──────────────────────────────────────────────────────────

@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=True,
)
async def _call_openai_embed(texts: List[str]) -> openai.types.CreateEmbeddingResponse:
    """Raw OpenAI embedding API call with retry on rate limit / connection errors."""
    client = _get_openai_client()
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
        dimensions=EMBEDDING_DIMENSIONS,
        encoding_format="float",
    )
    return response


async def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a single text string.

    Args:
        text: Text to embed. Truncated at 8000 chars (~2000 tokens) if too long.

    Returns:
        List of 1536 floats (cosine-normalized).
        Returns zero vector on OpenAI failure (graceful degradation).
    """
    if not text or not text.strip():
        logger.warning("embedding_empty_text", fallback="zero_vector")
        return _zero_vector()

    if not settings.openai_api_key:
        logger.warning(
            "embedding_no_api_key",
            model=EMBEDDING_MODEL,
            fallback="zero_vector",
        )
        return _zero_vector()

    # Truncate if very long (rough char limit — 1 token ~ 4 chars)
    text = text[:32000]

    start_ms = int(time.time() * 1000)
    try:
        response = await _call_openai_embed([text])
        embedding = response.data[0].embedding

        latency_ms = int(time.time() * 1000) - start_ms
        _log_embedding_cost(
            tokens=response.usage.total_tokens,
            count=1,
            latency_ms=latency_ms,
        )

        return embedding

    except openai.AuthenticationError as exc:
        logger.error(
            "embedding_auth_failed",
            error=str(exc),
            hint="check_openai_api_key",
        )
        return _zero_vector()

    except Exception as exc:
        latency_ms = int(time.time() * 1000) - start_ms
        logger.warning(
            "embedding_failed",
            error=str(exc),
            error_type=type(exc).__name__,
            fallback="zero_vector",
            latency_ms=latency_ms,
        )
        return _zero_vector()


# ── Batch embeddings ──────────────────────────────────────────────────────────

async def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for a list of texts in batches of max 100.

    Handles:
    - Empty texts: replaced with zero vector
    - Batching: splits into groups of MAX_BATCH_SIZE
    - Rate limits: exponential backoff via tenacity
    - Failures: individual batch failures fall back to zero vectors

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors, same length as input.
        Positions with failures get zero vectors.
    """
    if not texts:
        return []

    if not settings.openai_api_key:
        logger.warning(
            "embeddings_batch_no_api_key",
            count=len(texts),
            fallback="zero_vectors",
        )
        return [_zero_vector() for _ in texts]

    results: List[Optional[List[float]]] = [None] * len(texts)
    total_tokens = 0
    start_ms = int(time.time() * 1000)

    # Identify empty texts early — don't send to OpenAI
    non_empty_indices = [i for i, t in enumerate(texts) if t and t.strip()]
    for i in range(len(texts)):
        if i not in non_empty_indices:
            results[i] = _zero_vector()

    if not non_empty_indices:
        return [_zero_vector() for _ in texts]

    # Batch non-empty texts
    for batch_start in range(0, len(non_empty_indices), MAX_BATCH_SIZE):
        batch_indices = non_empty_indices[batch_start : batch_start + MAX_BATCH_SIZE]
        batch_texts = [texts[i][:32000] for i in batch_indices]  # truncate

        try:
            response = await _call_openai_embed(batch_texts)

            # OpenAI returns embeddings in same order as input
            for response_idx, global_idx in enumerate(batch_indices):
                results[global_idx] = response.data[response_idx].embedding

            total_tokens += response.usage.total_tokens

        except Exception as exc:
            logger.warning(
                "embeddings_batch_failed",
                batch_start=batch_start,
                batch_size=len(batch_texts),
                error=str(exc),
                fallback="zero_vectors_for_batch",
            )
            # Fill failed batch with zero vectors
            for global_idx in batch_indices:
                results[global_idx] = _zero_vector()

    # Fill any remaining Nones (shouldn't happen, defensive)
    for i in range(len(results)):
        if results[i] is None:
            results[i] = _zero_vector()

    latency_ms = int(time.time() * 1000) - start_ms
    _log_embedding_cost(
        tokens=total_tokens,
        count=len(non_empty_indices),
        latency_ms=latency_ms,
    )

    return results  # type: ignore[return-value]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _zero_vector() -> List[float]:
    """Return a zero vector of the correct dimensionality."""
    return [0.0] * EMBEDDING_DIMENSIONS


def _log_embedding_cost(tokens: int, count: int, latency_ms: int) -> None:
    """
    Log embedding cost for tracking.

    text-embedding-3-small: $0.020 per 1M tokens
    At USD/INR = 84 (approx): ₹1.68 per 1M tokens
    """
    # Cost in USD: tokens * (0.020 / 1_000_000)
    cost_usd = tokens * 0.020 / 1_000_000
    cost_inr = cost_usd * 84  # approximate

    logger.info(
        "embedding_cost",
        model=EMBEDDING_MODEL,
        tokens=tokens,
        count=count,
        cost_usd=round(cost_usd, 8),
        cost_inr=round(cost_inr, 6),
        latency_ms=latency_ms,
    )


async def count_tokens(text: str) -> int:
    """
    Estimate token count for a text using tiktoken.
    Used to ensure chunks are within embedding context window.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")  # Same as text-embedding-3-small
        return len(enc.encode(text))
    except ImportError:
        # Rough estimate: 1 token ~ 4 characters
        return len(text) // 4
    except Exception:
        return len(text) // 4
