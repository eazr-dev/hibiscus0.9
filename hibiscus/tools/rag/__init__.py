"""
RAG search tools for Hibiscus agents.

Primary knowledge retrieval interface — all agents that make factual claims
about insurance must use these tools to ground their responses.

Usage:
    from hibiscus.tools.rag import (
        search_knowledge,
        search_glossary,
        search_regulations,
        search_claim_process,
        search_benchmarks,
    )
"""
from .search import (
    # Primary search (alias with extended signature)
    search_knowledge,
    # Convenience wrappers
    search_glossary,
    search_regulations,
    search_claim_process,
    search_benchmarks,
    # Full-featured functions
    search_insurance_knowledge,
    lookup_glossary_term,
    search_claims_process,
    search_tax_rules,
    search_user_history,
    search_user_knowledge,
    search_all_context,
    # Formatting helpers
    format_rag_context,
    format_rag_citations,
)

__all__ = [
    # Standard API (as specified in blueprint)
    "search_knowledge",
    "search_glossary",
    "search_regulations",
    "search_claim_process",
    "search_benchmarks",
    # Extended API
    "search_insurance_knowledge",
    "lookup_glossary_term",
    "search_claims_process",
    "search_tax_rules",
    "search_user_history",
    "search_user_knowledge",
    "search_all_context",
    "format_rag_context",
    "format_rag_citations",
]
