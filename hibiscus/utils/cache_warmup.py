"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Cache warmup — pre-populates Redis response cache with common insurance questions on startup.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import hashlib
import re
from typing import List

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Top 100 common L1 insurance queries ─────────────────────────────────────
# Sourced from HibiscusBench test categories + common customer questions
# Keep alphabetically sorted within each group for easy maintenance.

_WARMUP_QUERIES: List[str] = [
    # ── Core terminology (most common) ──────────────────────────────────
    "What is a deductible in insurance?",
    "What is a waiting period in health insurance?",
    "How does cashless hospitalization work?",
    "What is sum insured in health insurance?",
    "What is a premium in insurance?",
    "What is EAZR Score?",
    "What is co-payment in health insurance?",
    "What is room rent limit in health insurance?",
    "What is an ICU sub-limit?",
    "What is a pre-existing disease in insurance?",
    "What is a network hospital?",
    "What is reimbursement claim in health insurance?",
    "What is a no-claim bonus in insurance?",
    "What is a free look period?",
    "What is portability in health insurance?",
    # ── Health insurance ────────────────────────────────────────────────
    "What is a cumulative bonus in health insurance?",
    "What is OPD cover in health insurance?",
    "What is restoration benefit in health insurance?",
    "What is a super top-up health insurance plan?",
    "What is a base plan in health insurance?",
    "What is a top-up health insurance plan?",
    "What is mental health coverage in insurance?",
    "What is the moratorium period in health insurance?",
    "What is daycare treatment in health insurance?",
    "What is domiciliary treatment in health insurance?",
    "What is critical illness insurance?",
    "What is a maternity benefit in health insurance?",
    "What is AYUSH treatment coverage?",
    "What is annual aggregate deductible?",
    # ── Life insurance ──────────────────────────────────────────────────
    "What is term insurance?",
    "What is ULIP insurance?",
    "What is endowment insurance?",
    "What is whole life insurance?",
    "What is surrender value in insurance?",
    "What is paid-up value in life insurance?",
    "What is guaranteed surrender value?",
    "What is special surrender value?",
    "What is sum assured in life insurance?",
    "What is an insurance rider?",
    "What is accidental death benefit rider?",
    "What is waiver of premium rider?",
    "What is critical illness rider in life insurance?",
    "What is return of premium in term insurance?",
    "What is a death benefit in life insurance?",
    # ── Motor insurance ─────────────────────────────────────────────────
    "What is IDV in motor insurance?",
    "What is third party motor insurance?",
    "What is comprehensive motor insurance?",
    "What is zero depreciation cover in motor insurance?",
    "What is NCB in motor insurance?",
    "What is own damage cover in motor insurance?",
    "What is a consumables cover in motor insurance?",
    "What is roadside assistance cover?",
    "What is engine protection cover in motor insurance?",
    "What is return to invoice cover in motor insurance?",
    # ── Personal Accident insurance ─────────────────────────────────────
    "What is personal accident insurance?",
    "What is accidental death benefit?",
    "What is permanent total disability in insurance?",
    "What is permanent partial disability in insurance?",
    "What is temporary total disability in insurance?",
    "What is double indemnity in personal accident insurance?",
    "What is a group personal accident policy?",
    # ── Travel insurance ────────────────────────────────────────────────
    "What is travel insurance?",
    "What is trip cancellation cover in travel insurance?",
    "What is medical evacuation cover in travel insurance?",
    "What is baggage loss cover in travel insurance?",
    "What is flight delay cover in travel insurance?",
    "What is Schengen visa insurance?",
    "What is single trip vs multi trip travel insurance?",
    # ── Tax and financial ────────────────────────────────────────────────
    "What is Section 80D tax deduction for health insurance?",
    "What is Section 80C tax deduction for life insurance?",
    "What is Section 10 10D exemption in life insurance?",
    "What is Section 80CCC for pension plans?",
    "What is GST on insurance premium?",
    "How much can I save on taxes with health insurance?",
    "Is life insurance maturity amount taxable?",
    # ── Claims ──────────────────────────────────────────────────────────
    "How do I file a health insurance claim?",
    "What documents are needed for a health insurance claim?",
    "What is the claim settlement ratio?",
    "What is incurred claim ratio?",
    "How long does insurance company take to settle a claim?",
    "What is a cashless claim network hospital procedure?",
    "What is a pre-authorization in insurance?",
    "What happens if my claim is rejected?",
    # ── IRDAI and regulation ─────────────────────────────────────────────
    "What is IRDAI?",
    "What is the insurance ombudsman in India?",
    "How do I file a complaint against an insurance company?",
    "What is IGMS in insurance?",
    "What is Bima Bharosa?",
    "What are policyholder rights in India?",
    # ── Mis-selling and advisory ─────────────────────────────────────────
    "What is insurance mis-selling?",
    "How do I know if I was sold a wrong insurance policy?",
    "ULIP vs mutual fund — which is better?",
    "Should I invest in ULIP or term plan plus mutual fund?",
    # ── IPF/SVF (EAZR-specific) ──────────────────────────────────────────
    "What is Insurance Premium Financing?",
    "What is Surrender Value Financing?",
    "How does EAZR IPF work?",
    "Can I get a loan against my insurance policy?",
    # ── General ─────────────────────────────────────────────────────────
    "How much health insurance cover do I need?",
    "What is the difference between health and life insurance?",
    "Should I buy insurance online or through an agent?",
    "What is the right age to buy life insurance?",
    "What is family floater health insurance?",
    "What is individual health insurance vs family floater?",
]


def _cache_key(message: str) -> str:
    """Consistent with response_cache._cache_key()."""
    normalized = re.sub(r"\s+", " ", message.lower().strip())
    digest = hashlib.sha256(normalized.encode()).hexdigest()[:24]
    return f"hibiscus:resp_cache:{digest}"


async def _is_cached(message: str) -> bool:
    """Check if this query is already in the cache."""
    try:
        from hibiscus.memory.layers.session import _redis_client
        if _redis_client is None:
            return False
        key = _cache_key(message)
        exists = await _redis_client.exists(key)
        return bool(exists)
    except Exception:
        return False


async def _warm_query(query: str, system_prompt: str) -> bool:
    """
    Generate and cache a response for a single query.
    Returns True on success, False on failure.
    """
    try:
        from hibiscus.llm.router import call_llm
        from hibiscus.memory.layers.response_cache import set_cached_response

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]
        result = await call_llm(
            messages=messages,
            tier="deepseek_v3",
            agent="cache_warmup",
            extra_kwargs={"max_tokens": 800},
        )
        response_text = result.get("content", "")
        if response_text:
            payload = {
                "response": response_text,
                "confidence": 0.85,
                "intent": "educate",
                "agents_invoked": [],
                "sources": [],
                "cache_warmed": True,
            }
            await set_cached_response(query, payload)
            return True
    except Exception as e:
        logger.warning("cache_warmup_query_failed", query=query[:50], error=str(e))
    return False


async def warmup_response_cache(batch_size: int = 5, delay_between_batches: float = 2.0) -> None:
    """
    Pre-warm the Redis response cache with common L1 insurance queries.

    Args:
        batch_size: Number of queries to process concurrently per batch.
        delay_between_batches: Seconds to wait between batches (rate limit protection).

    Called from main.py lifespan as a fire-and-forget background task.
    """
    logger.info("cache_warmup_starting", total_queries=len(_WARMUP_QUERIES))

    system_prompt = (
        "You are Hibiscus, EAZR's AI insurance advisor for India. "
        "Answer this insurance question clearly and concisely in 2-4 sentences. "
        "Use Indian context (IRDAI regulations, INR amounts). "
        "End with a brief note that users should consult a licensed advisor for personal decisions."
    )

    # Check which queries need warming
    queries_to_warm = []
    for query in _WARMUP_QUERIES:
        if not await _is_cached(query):
            queries_to_warm.append(query)

    if not queries_to_warm:
        logger.info("cache_warmup_complete", warmed=0, reason="all_already_cached")
        return

    logger.info("cache_warmup_pending", count=len(queries_to_warm), total=len(_WARMUP_QUERIES))

    warmed = 0
    failed = 0

    # Process in batches to avoid rate limits
    for i in range(0, len(queries_to_warm), batch_size):
        batch = queries_to_warm[i : i + batch_size]
        results = await asyncio.gather(
            *[_warm_query(q, system_prompt) for q in batch],
            return_exceptions=True,
        )
        for result in results:
            if result is True:
                warmed += 1
            else:
                failed += 1

        logger.info(
            "cache_warmup_batch_done",
            batch_num=i // batch_size + 1,
            total_batches=(len(queries_to_warm) + batch_size - 1) // batch_size,
            warmed_so_far=warmed,
        )

        # Rate limit protection: pause between batches
        if i + batch_size < len(queries_to_warm):
            await asyncio.sleep(delay_between_batches)

    logger.info(
        "cache_warmup_complete",
        warmed=warmed,
        failed=failed,
        total=len(queries_to_warm),
    )
