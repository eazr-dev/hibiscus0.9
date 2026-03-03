"""
Hibiscus LangGraph Supervisor — THE BRAIN
==========================================
Every user message flows through this graph.

Flow:
  assemble_context
    → classify_intent
    → [simple: direct_llm | complex: plan_execution → dispatch_agents → aggregate_response]
    → check_guardrails
    → store_memory
    → END
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from hibiscus.orchestrator.state import HibiscusState, Complexity
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


def _route_by_complexity(state: HibiscusState) -> str:
    """Route based on query complexity after intent classification."""
    complexity = state.get("complexity", Complexity.L1.value)
    emotional_state = state.get("emotional_state", "neutral")

    # Distressed users always go through agent pipeline for empathetic response
    if emotional_state in ("distressed", "urgent"):
        logger.info("routing_to_complex_emotional", emotional_state=emotional_state)
        return "complex"

    if complexity in (Complexity.L1.value, Complexity.L2.value):
        agents_needed = state.get("agents_needed", [])
        if not agents_needed:
            logger.info("routing_to_direct_llm", complexity=complexity)
            return "simple"

    logger.info("routing_to_agent_pipeline", complexity=complexity)
    return "complex"


def build_graph() -> StateGraph:
    """Build and compile the master Hibiscus orchestration graph."""
    from hibiscus.orchestrator.nodes import (
        context_assembly,
        intent_classification,
        execution_planning,
        agent_dispatch,
        response_aggregation,
        guardrail_check,
        memory_storage,
        direct_llm,
    )

    graph = StateGraph(HibiscusState)

    # ── Nodes ─────────────────────────────────────────────────────────────
    graph.add_node("assemble_context", context_assembly.run)
    graph.add_node("classify_intent", intent_classification.run)
    graph.add_node("plan_execution", execution_planning.run)
    graph.add_node("dispatch_agents", agent_dispatch.run)
    graph.add_node("aggregate_response", response_aggregation.run)
    graph.add_node("check_guardrails", guardrail_check.run)
    graph.add_node("store_memory", memory_storage.run)
    graph.add_node("direct_llm", direct_llm.run)

    # ── Edges ─────────────────────────────────────────────────────────────
    graph.set_entry_point("assemble_context")
    graph.add_edge("assemble_context", "classify_intent")

    # CONDITIONAL: Simple → direct LLM fast path, Complex → full agent pipeline
    graph.add_conditional_edges(
        "classify_intent",
        _route_by_complexity,
        {
            "simple": "direct_llm",
            "complex": "plan_execution",
        },
    )

    # Complex path
    graph.add_edge("plan_execution", "dispatch_agents")
    graph.add_edge("dispatch_agents", "aggregate_response")

    # Both paths converge at guardrails
    graph.add_edge("aggregate_response", "check_guardrails")
    graph.add_edge("direct_llm", "check_guardrails")

    # Post-guardrail: store memory, then done
    graph.add_edge("check_guardrails", "store_memory")
    graph.add_edge("store_memory", END)

    # ── Compile with in-memory checkpoint for conversation continuity ──────
    # In Phase 2, replace MemorySaver with Redis-backed checkpointer
    checkpointer = MemorySaver()
    compiled = graph.compile(checkpointer=checkpointer)

    logger.info("hibiscus_graph_compiled", nodes=8, edges=9)
    return compiled


# ── Singleton graph instance ───────────────────────────────────────────────
# Compiled once at module load; reused for all requests
try:
    hibiscus_graph = build_graph()
except Exception as e:
    logger.error("graph_compilation_failed", error=str(e))
    hibiscus_graph = None  # Will cause runtime error on first request — intended


async def run_graph(
    state: dict,
    config: dict,
) -> dict:
    """
    Execute the Hibiscus graph for a single request.

    Args:
        state: Initial HibiscusState dict
        config: LangGraph config (must include configurable.thread_id for persistence)

    Returns:
        Final state dict after all nodes execute
    """
    if hibiscus_graph is None:
        raise RuntimeError("Hibiscus graph failed to compile. Check startup logs.")

    final_state = await hibiscus_graph.ainvoke(state, config=config)
    return final_state
