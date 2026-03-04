"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
RAG embeddings — fastembed (BAAI/bge-large-en-v1.5) with GLM fallback for vector generation.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
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

# -- Constants -----------------------------------------------------------------
EMBEDDING_MODEL_LOCAL = "BAAI/bge-large-en-v1.5"   # fastembed primary (1024 dims)
EMBEDDING_MODEL_GLM = "embedding-2"                  # GLM API fallback
EMBEDDING_MODEL_OAI = "text-embedding-3-small"       # OpenAI API fallback
EMBEDDING_DIMENSIONS = 1024                           # bge-large-en-v1.5 / GLM output dims
MAX_BATCH_SIZE = 32                                   # CPU-friendly batch size for fastembed
MAX_TEXT_TOKENS = 8191

# Module-level fastembed model instance (lazy-initialized)
_fastembed_model = None
_fastembed_lock = asyncio.Lock()


def _load_fastembed_model():
    """Load fastembed model synchronously (called once, cached at module level)."""
    global _fastembed_model
    if _fastembed_model is not None:
        return _fastembed_model
    try:
        from fastembed import TextEmbedding
        _fastembed_model = TextEmbedding(
            model_name=EMBEDDING_MODEL_LOCAL,
            cache_dir=None,     # use default ~/.cache/fastembed/
            threads=4,          # 4 ONNX threads — fast on modern CPUs
        )
        logger.info("fastembed_model_loaded", model=EMBEDDING_MODEL_LOCAL, dims=EMBEDDING_DIMENSIONS)
        return _fastembed_model
    except Exception as exc:
        logger.warning("fastembed_load_failed", error=str(exc), fallback="api_providers")
        return None


async def _get_fastembed_model():
    """Async lazy-init for fastembed model (thread-safe)."""
    global _fastembed_model
    if _fastembed_model is not None:
        return _fastembed_model
    async with _fastembed_lock:
        if _fastembed_model is not None:
            return _fastembed_model
        loop = asyncio.get_event_loop()
        model = await loop.run_in_executor(None, _load_fastembed_model)
        return model


async def _embed_fastembed(texts: List[str]) -> Optional[List[List[float]]]:
    """
    Get embeddings from local fastembed model.
    Returns list of float vectors, or None on failure.
    """
    try:
        model = await _get_fastembed_model()
        if model is None:
            return None
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: [emb.tolist() for emb in model.embed(texts)],
        )
        return embeddings
    except Exception as exc:
        logger.warning("fastembed_embed_failed", error=str(exc), fallback="api_providers")
        return None


# -- API clients (fallback only) -----------------------------------------------

def _get_glm_client() -> openai.AsyncOpenAI:
    """Lazy-create GLM async client (OpenAI-compatible API)."""
    return openai.AsyncOpenAI(
        api_key=settings.zhipu_api_key,
        base_url=settings.zhipu_base_url,
        timeout=30.0,
        max_retries=0,
    )


def _get_openai_client() -> openai.AsyncOpenAI:
    """Lazy-create OpenAI async client (fallback)."""
    return openai.AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=30.0,
        max_retries=0,
    )


@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=True,
)
async def _call_glm_embed(texts: List[str]) -> openai.types.CreateEmbeddingResponse:
    """GLM embedding API call with retry."""
    client = _get_glm_client()
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL_GLM,
        input=texts,
        encoding_format="float",
    )
    return response


@retry(
    retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(4),
    before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
    reraise=True,
)
async def _call_openai_embed(texts: List[str]) -> openai.types.CreateEmbeddingResponse:
    """OpenAI embedding API call (final fallback).

    Uses the `dimensions` parameter to request EMBEDDING_DIMENSIONS directly
    from the API, avoiding post-hoc truncation which discards information
    suboptimally. text-embedding-3-small supports Matryoshka dimensions.
    """
    client = _get_openai_client()
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL_OAI,
        input=texts,
        encoding_format="float",
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return response


# -- Single embedding ----------------------------------------------------------

async def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a single text string.

    Priority: fastembed (local) -> GLM API -> OpenAI API -> zero vector.

    Returns:
        List of 1024 floats.
        Returns zero vector on all failures (graceful degradation).
    """
    if not text or not text.strip():
        logger.warning("embedding_empty_text", fallback="zero_vector")
        return _zero_vector()

    text = text[:32000]
    start_ms = int(time.time() * 1000)

    # Try local fastembed first (no API key required)
    result = await _embed_fastembed([text])
    if result:
        latency_ms = int(time.time() * 1000) - start_ms
        logger.debug("embedding_fastembed_ok", latency_ms=latency_ms)
        return result[0]

    # Try GLM API
    if settings.zhipu_api_key:
        try:
            response = await _call_glm_embed([text])
            embedding = response.data[0].embedding
            latency_ms = int(time.time() * 1000) - start_ms
            _log_embedding_cost(
                tokens=response.usage.total_tokens,
                count=1,
                latency_ms=latency_ms,
                model="glm_embedding_2",
            )
            return embedding
        except openai.AuthenticationError as exc:
            logger.error("glm_embedding_auth_failed", error=str(exc))
        except Exception as exc:
            logger.warning("glm_embedding_failed", error=str(exc), fallback="try_openai")

    # Try OpenAI API
    if settings.openai_api_key:
        try:
            response = await _call_openai_embed([text])
            embedding = response.data[0].embedding
            latency_ms = int(time.time() * 1000) - start_ms
            _log_embedding_cost(
                tokens=response.usage.total_tokens,
                count=1,
                latency_ms=latency_ms,
                model="openai_text_embedding_3_small",
            )
            # No post-hoc truncation needed: dimensions parameter is set in the API call
            return embedding
        except Exception as exc:
            logger.warning("openai_embedding_failed", error=str(exc), fallback="zero_vector")

    logger.warning("embedding_no_provider_available", fallback="zero_vector")
    return _zero_vector()


# -- Batch embeddings ----------------------------------------------------------

async def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for a list of texts in batches.

    Priority per batch: fastembed (local) -> GLM API -> OpenAI API -> zero vectors.

    Returns:
        List of embedding vectors (1024 dims), same length as input.
        Positions with failures get zero vectors.
    """
    if not texts:
        return []

    results: List[Optional[List[float]]] = [None] * len(texts)
    start_ms = int(time.time() * 1000)

    # Identify empty texts early
    non_empty_indices = [i for i, t in enumerate(texts) if t and t.strip()]
    for i in range(len(texts)):
        if i not in non_empty_indices:
            results[i] = _zero_vector()

    if not non_empty_indices:
        return [_zero_vector() for _ in texts]

    # Process in batches
    for batch_start in range(0, len(non_empty_indices), MAX_BATCH_SIZE):
        batch_indices = non_empty_indices[batch_start : batch_start + MAX_BATCH_SIZE]
        batch_texts = [texts[i][:32000] for i in batch_indices]

        batch_ok = False

        # Try fastembed (local) first
        fastembed_result = await _embed_fastembed(batch_texts)
        if fastembed_result and len(fastembed_result) == len(batch_texts):
            for response_idx, global_idx in enumerate(batch_indices):
                results[global_idx] = fastembed_result[response_idx]
            batch_ok = True

        # Try GLM API if fastembed failed
        if not batch_ok and settings.zhipu_api_key:
            try:
                response = await _call_glm_embed(batch_texts)
                for response_idx, global_idx in enumerate(batch_indices):
                    results[global_idx] = response.data[response_idx].embedding
                batch_ok = True
            except Exception as exc:
                logger.warning(
                    "glm_batch_embed_failed",
                    batch_start=batch_start,
                    error=str(exc),
                    fallback="try_openai",
                )

        # Try OpenAI if GLM failed
        if not batch_ok and settings.openai_api_key:
            try:
                response = await _call_openai_embed(batch_texts)
                for response_idx, global_idx in enumerate(batch_indices):
                    # No post-hoc truncation: dimensions parameter is set in the API call
                    results[global_idx] = response.data[response_idx].embedding
                batch_ok = True
            except Exception as exc:
                logger.warning(
                    "openai_batch_embed_failed",
                    batch_start=batch_start,
                    error=str(exc),
                    fallback="zero_vectors_for_batch",
                )

        if not batch_ok:
            logger.error(
                "embedding_all_providers_failed",
                batch_start=batch_start,
                batch_size=len(batch_texts),
            )
            for global_idx in batch_indices:
                results[global_idx] = _zero_vector()

    # Fill any remaining Nones
    for i in range(len(results)):
        if results[i] is None:
            results[i] = _zero_vector()

    latency_ms = int(time.time() * 1000) - start_ms
    logger.info(
        "embedding_batch_complete",
        model="bge_large_en_v1.5",
        count=len(non_empty_indices),
        total=len(texts),
        latency_ms=latency_ms,
    )

    return results  # type: ignore[return-value]


# -- Helpers -------------------------------------------------------------------

def _zero_vector() -> List[float]:
    """Return a zero vector of the correct dimensionality."""
    return [0.0] * EMBEDDING_DIMENSIONS


def _log_embedding_cost(tokens: int, count: int, latency_ms: int, model: str = "bge_large") -> None:
    """Log API embedding cost for tracking (local fastembed has no cost)."""
    if model.startswith("glm"):
        cost_usd = tokens * 0.005 / 1_000_000
    else:
        cost_usd = tokens * 0.020 / 1_000_000
    cost_inr = cost_usd * 84

    logger.info(
        "embedding_cost",
        model=model,
        tokens=tokens,
        count=count,
        cost_usd=round(cost_usd, 8),
        cost_inr=round(cost_inr, 6),
        latency_ms=latency_ms,
    )


async def count_tokens(text: str) -> int:
    """Estimate token count for a text."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return len(text) // 4
    except Exception:
        return len(text) // 4
