"""
RAG Search Tools for Hibiscus Agents
======================================
Provides search functions that agents use to ground responses in the knowledge base.

These are the primary RAG interface for all 12 Hibiscus agents. Every factual claim
about insurance must trace to a source — these tools provide that grounding.

All functions:
  - Return [] on Qdrant unavailability (graceful degradation)
  - Log every search call with query, results, and latency
  - Apply category filtering where relevant to improve precision
  - Return structured dicts with content, source, confidence, metadata

Usage by agents:
    results = await search_insurance_knowledge("what is copay in health insurance")
    context = format_rag_context(results)
    # Pass context to LLM prompt
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
from typing import Any, Dict, List, Optional

from hibiscus.config import settings
from hibiscus.knowledge.rag.client import rag_client
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Category mapping for filter-based search ─────────────────────────────────
# Maps user-facing category names to metadata field values in Qdrant payload
CATEGORY_MAP: Dict[str, str] = {
    "health": "health_insurance",
    "health_insurance": "health_insurance",
    "life": "life_insurance",
    "life_insurance": "life_insurance",
    "motor": "motor_insurance",
    "motor_insurance": "motor_insurance",
    "travel": "travel_insurance",
    "travel_insurance": "travel_insurance",
    "tax": "tax_rules",
    "tax_rules": "tax_rules",
    "glossary": "glossary",
    "claims": "claims_process",
    "claims_process": "claims_process",
    "regulation": "regulation",
    "irdai": "regulation",
    "circular": "irdai_circular",
}


# ── Primary knowledge search ──────────────────────────────────────────────────

async def search_insurance_knowledge(
    query: str,
    category: Optional[str] = None,
    top_k: int = 5,
    collection: str = None,
) -> List[Dict[str, Any]]:
    """
    Search the Hibiscus insurance knowledge base.

    This is the primary RAG tool used by all agents. Searches the
    insurance_knowledge collection which contains: IRDAI circulars,
    glossary terms, claims processes, tax rules, and policy wordings.

    Args:
        query    : Natural language question or search query.
                   Examples:
                     "what is copay in health insurance"
                     "how to file cashless claim at star health"
                     "section 80D deduction limit for parents"
        category : Optional category filter. Narrows search to one domain.
                   Valid values: "health", "life", "motor", "travel", "tax",
                                 "glossary", "claims", "regulation"
        top_k    : Number of results to return (default 5, max 20).
        collection: Override collection name (defaults to insurance_knowledge).

    Returns:
        List of result dicts, sorted by relevance score:
        [
            {
                "content"  : str,   # The actual text chunk
                "source"   : str,   # Where this came from
                "score"    : float, # RRF relevance score (higher = more relevant)
                "metadata" : dict,  # doc_type, category, date, etc.
            },
            ...
        ]
        Returns empty list [] if Qdrant unavailable or query produces no results.

    Note:
        Every agent that makes factual claims MUST cite these results.
        The source field in each result is the citation.
    """
    if not query or not query.strip():
        logger.warning("search_knowledge_empty_query")
        return []

    target_collection = collection or settings.qdrant_collection_knowledge
    top_k = min(top_k, 20)  # Hard cap at 20

    # Build metadata filter for category
    filter_metadata: Optional[Dict[str, Any]] = None
    if category:
        normalized_category = CATEGORY_MAP.get(category.lower())
        if normalized_category:
            filter_metadata = {"category": normalized_category}
        else:
            logger.warning(
                "search_knowledge_unknown_category",
                category=category,
                known_categories=list(CATEGORY_MAP.keys()),
            )

    start_ms = int(time.time() * 1000)

    results = await rag_client.search(
        query=query,
        collection=target_collection,
        top_k=top_k,
        filter_metadata=filter_metadata,
    )

    latency_ms = int(time.time() * 1000) - start_ms

    logger.info(
        "rag_search_knowledge",
        query_preview=query[:60],
        category=category,
        collection=target_collection,
        results_count=len(results),
        latency_ms=latency_ms,
    )

    return results


# ── User conversation history search ─────────────────────────────────────────

async def search_user_history(
    user_id: str,
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search a user's past conversation history for relevant context.

    Used to provide personalized, contextually aware responses. Retrieves
    prior conversations semantically similar to the current query.

    Args:
        user_id : The user's unique identifier (from HibiscusState.user_id)
        query   : The current query (used to find semantically similar past conversations)
        top_k   : Number of past conversation snippets to retrieve (default 5)

    Returns:
        List of result dicts with past conversation context:
        [
            {
                "content"  : str,   # Past conversation snippet
                "source"   : str,   # "user_conversation"
                "score"    : float, # Relevance score
                "metadata" : {
                    "user_id"   : str,
                    "session_id": str,
                    "role"      : str,  # "user" or "assistant"
                    "timestamp" : float,
                }
            },
            ...
        ]
        Returns [] if no relevant history or Qdrant unavailable.
    """
    if not user_id or not query:
        return []

    start_ms = int(time.time() * 1000)

    # Filter by user_id to get only this user's history
    results = await rag_client.search(
        query=query,
        collection=settings.qdrant_collection_conversations,
        top_k=top_k,
        filter_metadata={"user_id": user_id},
    )

    latency_ms = int(time.time() * 1000) - start_ms

    logger.info(
        "rag_search_user_history",
        user_id=user_id,
        query_preview=query[:60],
        results_count=len(results),
        latency_ms=latency_ms,
    )

    return results


# ── User knowledge search ─────────────────────────────────────────────────────

async def search_user_knowledge(
    user_id: str,
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search per-user extracted policy insights and facts.

    This searches the user_knowledge collection which stores structured
    data extracted from the user's uploaded insurance documents: policy
    numbers, sum insured, exclusions, waiting periods, EAZR scores, etc.

    Args:
        user_id : The user's unique identifier
        query   : The query to search against stored user insights
        top_k   : Number of results to return

    Returns:
        List of user-specific knowledge snippets relevant to the query.
        Returns [] if no user insights stored or Qdrant unavailable.
    """
    if not user_id or not query:
        return []

    start_ms = int(time.time() * 1000)

    results = await rag_client.search(
        query=query,
        collection=settings.qdrant_collection_insights,
        top_k=top_k,
        filter_metadata={"user_id": user_id},
    )

    latency_ms = int(time.time() * 1000) - start_ms

    logger.info(
        "rag_search_user_knowledge",
        user_id=user_id,
        query_preview=query[:60],
        results_count=len(results),
        latency_ms=latency_ms,
    )

    return results


# ── Glossary term lookup ──────────────────────────────────────────────────────

async def lookup_glossary_term(term: str) -> List[Dict[str, Any]]:
    """
    Look up a specific insurance term in the glossary.

    Optimized search for glossary queries: searches only the glossary
    category for exact and semantically similar term definitions.

    Args:
        term: The insurance term to look up (e.g., "copay", "sum insured", "NCB")

    Returns:
        Up to 3 glossary definitions sorted by relevance.
        Returns [] if term not found or Qdrant unavailable.
    """
    return await search_insurance_knowledge(
        query=f"What is {term} in insurance?",
        category="glossary",
        top_k=3,
    )


# ── Regulation/circular search ────────────────────────────────────────────────

async def search_regulations(
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search IRDAI regulations and circulars.

    Used by the Regulation Engine agent and Compliance Guard to find
    applicable regulatory rules for a given scenario.

    Args:
        query: What regulation or right to find.
               E.g., "cashless claim authorization timeline"
                     "PED waiting period maximum"
                     "free look period rules"
        top_k: Number of regulation snippets to return

    Returns:
        List of regulation/circular snippets with circular numbers,
        dates, and key points.
    """
    return await search_insurance_knowledge(
        query=query,
        category="regulation",
        top_k=top_k,
    )


# ── Claims process search ─────────────────────────────────────────────────────

async def search_claims_process(
    query: str,
    insurer: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search claims process knowledge base.

    Used by the Claims Guide agent to provide step-by-step claim
    filing guidance for specific insurers and claim types.

    Args:
        query   : What claims process information to find.
                  E.g., "how to file cashless claim at Star Health"
                        "documents needed for reimbursement"
        insurer : Optional insurer name filter.
                  E.g., "star health", "niva bupa", "hdfc ergo"
        top_k   : Number of results to return

    Returns:
        List of claims process steps and guidance.
    """
    # Build query with insurer context if provided
    full_query = query
    if insurer:
        full_query = f"{query} {insurer}"

    results = await search_insurance_knowledge(
        query=full_query,
        category="claims",
        top_k=top_k,
    )

    # If insurer-specific results are empty, fall back to general claims knowledge
    if not results and insurer:
        results = await search_insurance_knowledge(
            query=query,
            category="claims",
            top_k=top_k,
        )

    return results


# ── Tax rules search ──────────────────────────────────────────────────────────

async def search_tax_rules(
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search insurance tax rules knowledge base.

    Used by the Tax Advisor agent to answer tax-related questions
    about insurance premiums, maturity, and deductions.

    Args:
        query: Tax question to search.
               E.g., "80D deduction limit for parents"
                     "ULIP maturity tax rules"
                     "is term plan maturity taxable"
        top_k: Number of results to return

    Returns:
        List of tax rule snippets with section references and examples.
    """
    return await search_insurance_knowledge(
        query=query,
        category="tax",
        top_k=top_k,
    )


# ── Multi-collection search ───────────────────────────────────────────────────

async def search_all_context(
    query: str,
    user_id: Optional[str] = None,
    top_k_knowledge: int = 5,
    top_k_history: int = 3,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search all relevant collections simultaneously for comprehensive context.

    Used by the Context Assembler to gather all relevant information
    before constructing the LLM prompt.

    Args:
        query          : The user's current query
        user_id        : Optional user ID for personalized history search
        top_k_knowledge: Results from insurance knowledge base
        top_k_history  : Results from user's conversation history

    Returns:
        Dict with keys:
        {
            "knowledge"      : List[dict],  # Insurance knowledge results
            "user_history"   : List[dict],  # Past conversation results
            "user_knowledge" : List[dict],  # User's policy data results
        }
    """
    import asyncio

    async def _empty() -> List[Dict[str, Any]]:
        return []

    knowledge_coro = search_insurance_knowledge(query, top_k=top_k_knowledge)

    if user_id:
        history_coro = search_user_history(user_id, query, top_k=top_k_history)
        user_kg_coro = search_user_knowledge(user_id, query, top_k=3)
    else:
        history_coro = _empty()
        user_kg_coro = _empty()

    results = await asyncio.gather(
        knowledge_coro,
        history_coro,
        user_kg_coro,
        return_exceptions=True,
    )

    return {
        "knowledge": results[0] if not isinstance(results[0], Exception) else [],
        "user_history": results[1] if not isinstance(results[1], Exception) else [],
        "user_knowledge": results[2] if not isinstance(results[2], Exception) else [],
    }


# ── Response formatting helpers ───────────────────────────────────────────────

def format_rag_context(
    results: List[Dict[str, Any]],
    header: str = "Relevant Knowledge:",
    max_chars: int = 4000,
) -> str:
    """
    Format RAG search results into a string for LLM prompt injection.

    Produces clean, numbered citations that the LLM can reference in its response.

    Args:
        results   : List of result dicts from search functions
        header    : Section header for the context block
        max_chars : Max total characters to include (prevents prompt overflow)

    Returns:
        Formatted string ready for LLM prompt injection.
        Empty string if results is empty.

    Example output:
        Relevant Knowledge:
        [1] Source: hibiscus_insurance_glossary | Category: glossary
        Term: Copay
        Definition: A cost-sharing arrangement where the policyholder pays...

        [2] Source: irdai.gov.in | Category: regulation
        ...
    """
    if not results:
        return ""

    lines = [header]
    total_chars = len(header) + 1

    for idx, result in enumerate(results, 1):
        content = result.get("content", "").strip()
        source = result.get("source", "unknown")
        metadata = result.get("metadata", {})
        category = metadata.get("category", "")
        score = result.get("score", 0.0)

        # Build the citation block
        citation_header = f"[{idx}] Source: {source}"
        if category:
            citation_header += f" | Category: {category}"
        if score:
            citation_header += f" | Relevance: {score:.3f}"

        block = f"\n{citation_header}\n{content}\n"

        if total_chars + len(block) > max_chars:
            # Truncate content if needed
            remaining = max_chars - total_chars - len(citation_header) - 20
            if remaining > 100:
                truncated_block = f"\n{citation_header}\n{content[:remaining]}...\n"
                lines.append(truncated_block)
            break

        lines.append(block)
        total_chars += len(block)

    return "\n".join(lines)


async def search_benchmarks(
    insurer: Optional[str] = None,
    metric: Optional[str] = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search insurer benchmark data (CSR, ICR, network hospitals, solvency).

    Used by the Policy Advisor and Comparison Engine agents when recommending
    insurers or comparing products. Grounds insurer quality claims in data.

    Args:
        insurer : Optional insurer name filter.
                  E.g., "Star Health", "LIC", "HDFC Life"
        metric  : Optional metric to focus search on.
                  E.g., "claim settlement ratio", "network hospitals",
                        "incurred claim ratio", "solvency"
        top_k   : Number of benchmark records to return

    Returns:
        List of insurer benchmark result dicts with ICR, CSR, network data.
        Returns [] if Qdrant unavailable.
    """
    if insurer and metric:
        query = f"{insurer} {metric} benchmark"
    elif insurer:
        query = f"{insurer} insurance benchmark claim settlement ratio ICR network hospitals"
    elif metric:
        query = f"{metric} comparison all insurers benchmark data"
    else:
        query = "insurer benchmark claim settlement ratio ICR network hospitals solvency"

    return await search_insurance_knowledge(
        query=query,
        top_k=top_k,
    )


async def search_knowledge(
    query: str,
    category: Optional[str] = None,
    corpus: Optional[str] = None,
    top_k: int = 5,
    min_score: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Alias for search_insurance_knowledge with extended signature.

    Hybrid semantic search over the RAG corpus.
    Returns list of relevant chunks with source info.
    Each result: {content, source, score, metadata}

    Args:
        query    : Natural language search query.
        category : Category filter — "health", "life", "motor", "tax", "all"
        corpus   : Corpus filter hint — "glossary", "circulars", "claims", "tax",
                   "benchmarks", "all" (informational — category is applied in practice)
        top_k    : Number of results to return (default 5).
        min_score: Minimum score threshold (applied post-search to filter low relevance).

    Returns:
        List of {content, source, score, metadata} dicts sorted by relevance.
    """
    # Derive effective category from corpus hint if category not set
    effective_category = category
    if not effective_category and corpus and corpus != "all":
        corpus_to_category = {
            "glossary": "glossary",
            "circulars": "regulation",
            "claims": "claims",
            "tax": "tax",
            "benchmarks": None,  # No single category for benchmarks
        }
        effective_category = corpus_to_category.get(corpus)

    results = await search_insurance_knowledge(
        query=query,
        category=effective_category,
        top_k=top_k,
    )

    # Apply min_score filter if specified
    if min_score > 0.0:
        results = [r for r in results if r.get("score", 0.0) >= min_score]

    return results


async def search_glossary(term: str) -> Optional[Dict[str, Any]]:
    """
    Look up a specific insurance term definition.

    Returns the single best matching glossary entry or None.

    Args:
        term: Insurance term to look up (e.g., "copay", "NCB", "sum insured")

    Returns:
        Best matching glossary entry dict, or None if not found.
    """
    results = await lookup_glossary_term(term)
    return results[0] if results else None


async def search_claim_process(claim_type: str) -> Optional[Dict[str, Any]]:
    """
    Get step-by-step claims process guide for a specific claim type.

    Args:
        claim_type: Type of claim — "cashless", "reimbursement", "death",
                    "maturity", "motor_od", "third_party", "critical_illness"

    Returns:
        Claims process guide dict, or None if not found.
    """
    query_map = {
        "cashless": "cashless claim process steps health insurance",
        "reimbursement": "reimbursement claim process steps documents health insurance",
        "death": "life insurance death claim process documents nominee",
        "maturity": "life insurance maturity claim process payment",
        "motor_od": "motor own damage OD claim process steps accident",
        "motor_third_party": "third party motor claim MACT tribunal process",
        "third_party": "third party motor claim MACT tribunal process",
        "critical_illness": "critical illness claim process diagnosis lump sum",
    }

    query = query_map.get(claim_type.lower(), f"{claim_type} claim process steps India")

    results = await search_insurance_knowledge(
        query=query,
        category="claims",
        top_k=3,
    )
    return results[0] if results else None


def format_rag_citations(results: List[Dict[str, Any]]) -> str:
    """
    Format a compact citation list from RAG results.

    For use at the end of agent responses to cite knowledge sources.

    Args:
        results: List of result dicts

    Returns:
        Compact citation string.
        Empty string if results is empty.

    Example output:
        Sources: hibiscus_glossary, irdai.gov.in, star_health_claims_guide
    """
    if not results:
        return ""

    sources = []
    seen = set()
    for result in results:
        source = result.get("source", "")
        if source and source not in seen:
            sources.append(source)
            seen.add(source)

    if not sources:
        return ""

    return "Sources: " + ", ".join(sources)
