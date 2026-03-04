"""
Tool Registry
=============
Central registry for all Hibiscus tools.

Tools register themselves via the @register decorator.
Agents call get_tool(name) to retrieve a callable by name.
Called once at startup via register_all().

Usage:
    from hibiscus.tools.registry import get_tool, list_tools, register_all

    await register_all()
    search_fn = get_tool("search_insurance_knowledge")
    result = await search_fn(query="deductible")
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Callable, Dict, List, Optional

_REGISTRY: Dict[str, Callable] = {}


def register(name: str) -> Callable:
    """Decorator to register a tool function by name."""
    def decorator(fn: Callable) -> Callable:
        _REGISTRY[name] = fn
        return fn
    return decorator


def get_tool(name: str) -> Optional[Callable]:
    """Retrieve a registered tool by name. Returns None if not found."""
    return _REGISTRY.get(name)


def list_tools() -> List[str]:
    """Return all registered tool names."""
    return list(_REGISTRY.keys())


def register_all() -> None:
    """
    Import and register all Hibiscus tools.

    Called once at startup in main.py lifespan.
    Each tool module must expose a single callable at the expected import path.
    """
    errors = []

    # ── RAG Search ─────────────────────────────────────────────────
    try:
        from hibiscus.tools.rag.search import search_insurance_knowledge
        _REGISTRY["search_insurance_knowledge"] = search_insurance_knowledge
    except Exception as e:
        errors.append(f"rag.search: {e}")

    # ── Knowledge Graph Tools ──────────────────────────────────────
    try:
        from hibiscus.tools.knowledge.insurer_lookup import get_insurer_profile
        _REGISTRY["get_insurer_profile"] = get_insurer_profile
    except Exception as e:
        errors.append(f"insurer_lookup: {e}")

    try:
        from hibiscus.tools.knowledge.product_lookup import get_product_details
        _REGISTRY["get_product_details"] = get_product_details
    except Exception as e:
        errors.append(f"product_lookup: {e}")

    try:
        from hibiscus.tools.knowledge.benchmark_lookup import get_benchmarks
        _REGISTRY["get_benchmarks"] = get_benchmarks
    except Exception as e:
        errors.append(f"benchmark_lookup: {e}")

    try:
        from hibiscus.tools.knowledge.regulation_lookup import get_regulation
        _REGISTRY["get_regulation"] = get_regulation
    except Exception as e:
        errors.append(f"regulation_lookup: {e}")

    # ── Web Search ─────────────────────────────────────────────────
    try:
        from hibiscus.tools.web.search import web_search
        _REGISTRY["web_search"] = web_search
    except Exception as e:
        errors.append(f"web.search: {e}")

    # ── Quote Comparison ───────────────────────────────────────────
    try:
        from hibiscus.tools.quote.compare import compare_quotes
        _REGISTRY["compare_quotes"] = compare_quotes
    except Exception as e:
        errors.append(f"quote.compare: {e}")

    # Log results
    from hibiscus.observability.logger import get_logger
    _logger = get_logger(__name__)
    _logger.info(
        "tool_registry_loaded",
        registered=list(_REGISTRY.keys()),
        errors=errors,
        total=len(_REGISTRY),
    )
