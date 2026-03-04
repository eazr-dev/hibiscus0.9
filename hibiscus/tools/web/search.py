"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Web search tool — Tavily-powered real-time insurance market and news search.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import os
from typing import Optional
from ...observability.logger import get_logger

logger = get_logger("tools.web.search")

_tavily_client = None
_tavily_enabled = False


def _init_tavily() -> bool:
    """Initialize Tavily client. Returns True if enabled."""
    global _tavily_client, _tavily_enabled

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.info("Tavily web search disabled — no TAVILY_API_KEY set")
        return False

    try:
        from tavily import TavilyClient
        _tavily_client = TavilyClient(api_key=api_key)
        _tavily_enabled = True
        logger.info("Tavily web search enabled")
        return True
    except ImportError:
        logger.warning("tavily-python not installed. Run: pip install tavily-python")
        return False
    except Exception as e:
        logger.warning(f"Tavily init failed: {e}")
        return False


_tavily_enabled = _init_tavily()

# Allowed domains for insurance research
_TRUSTED_INSURANCE_DOMAINS = [
    "irdai.gov.in",
    "licindia.in",
    "policybazaar.com",
    "coverfox.com",
    "ibai.org",
    "moneycontrol.com",
    "economictimes.com",
    "livemint.com",
    "thehindu.com",
    "business-standard.com",
    "financialexpress.com",
    "bsebimabandhu.irdai.gov.in",
    "bimabharosaportal.irdai.gov.in",
]


async def web_search(
    query: str,
    max_results: int = 5,
    include_domains: Optional[list[str]] = None,
    search_depth: str = "basic",   # "basic" or "advanced"
) -> list[dict]:
    """
    Search the web for current insurance information.

    Args:
        query: Search query
        max_results: Max results to return (1-10)
        include_domains: Restrict to these domains (None = trusted domains list)
        search_depth: "basic" for speed, "advanced" for depth

    Returns:
        List of {title, url, content, published_date, score}
    """
    if not _tavily_enabled or not _tavily_client:
        logger.debug("web_search called but Tavily unavailable — returning empty")
        return []

    try:
        domains = include_domains or _TRUSTED_INSURANCE_DOMAINS
        response = _tavily_client.search(
            query=query,
            search_depth=search_depth,
            max_results=min(max_results, 10),
            include_domains=domains,
            include_answer=True,
        )

        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:1000],  # Truncate to 1000 chars
                "published_date": r.get("published_date", ""),
                "score": r.get("score", 0.0),
                "source": r.get("url", "").split("/")[2] if r.get("url") else "",  # Domain only
            })

        logger.info(
            "web_search completed",
            query=query[:50],
            results_count=len(results),
        )
        return results

    except Exception as e:
        logger.error(f"web_search failed: {e}")
        return []


async def search_irdai_news(topic: str = "", max_results: int = 5) -> list[dict]:
    """Search for IRDAI news and announcements."""
    query = f"IRDAI insurance regulation India 2025 {topic}".strip()
    return await web_search(
        query=query,
        max_results=max_results,
        include_domains=["irdai.gov.in", "economictimes.com", "business-standard.com", "livemint.com"],
    )


async def search_product_reviews(insurer: str, product: str = "", max_results: int = 5) -> list[dict]:
    """Search for product reviews and comparisons."""
    query = f"{insurer} {product} insurance review India 2025".strip()
    return await web_search(
        query=query,
        max_results=max_results,
        include_domains=["policybazaar.com", "coverfox.com", "moneycontrol.com", "economictimes.com"],
    )


async def search_claims_news(insurer: str = "", max_results: int = 3) -> list[dict]:
    """Search for recent claims and CSR news."""
    query = f"India health insurance claim settlement ratio 2024 2025 {insurer}".strip()
    return await web_search(query=query, max_results=max_results)


def is_available() -> bool:
    """Check if web search is available."""
    return _tavily_enabled
