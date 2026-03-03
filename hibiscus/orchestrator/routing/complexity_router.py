"""
Complexity Router
==================
Routes queries by complexity level:
- L1/L2 (simple) → direct_llm fast path (skip agent pipeline)
- L3/L4 (complex) → full agent pipeline (plan → dispatch → aggregate)

Used by the conditional edge in graph.py after intent classification.
"""
from hibiscus.orchestrator.state import HibiscusState


def route_by_complexity(state: HibiscusState) -> str:
    """
    Determine whether to use the direct LLM fast path or the full agent pipeline.

    L1 (FAQ): Direct LLM — no agents needed, sub-second.
    L2 (Single-agent): Direct LLM if no agents assigned, otherwise agent pipeline.
    L3 (Multi-agent): Full pipeline — plan → dispatch → aggregate.
    L4 (Deep research): Full pipeline with Tier 2 model.
    """
    complexity = state.get("complexity", "L1")
    agents_needed = state.get("execution_plan", [])

    # Fast path: L1/L2 with no specialized agents
    if complexity in ("L1", "L2") and not agents_needed:
        return "simple"

    # If agents are assigned (even for L2), use the pipeline
    if agents_needed:
        return "complex"

    # Default: simple for L1/L2, complex for L3/L4
    if complexity in ("L1", "L2"):
        return "simple"
    return "complex"


def is_fast_path(state: HibiscusState) -> bool:
    """Check if this request qualifies for the fast path (no agents)."""
    return route_by_complexity(state) == "simple"


def get_complexity_level(complexity: str) -> int:
    """Convert complexity string to numeric level for comparison."""
    return {"L1": 1, "L2": 2, "L3": 3, "L4": 4}.get(complexity, 1)
