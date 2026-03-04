"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Execution planning node — determines which agents and tools are needed for the query.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


# ── Agent dependency rules ────────────────────────────────────────────────
# Agents that must run BEFORE others (sequential dependencies)
_SEQUENTIAL_DEPENDENCIES = {
    "recommender": ["policy_analyzer"],   # Need analysis before recommending
    "risk_detector": ["policy_analyzer"], # Need analysis before detecting risks
    "surrender_calculator": ["policy_analyzer"],  # Need extracted data
}

# Agents that can always run in parallel (no output dependencies)
_ALWAYS_PARALLEL = {
    "regulation_engine",
    "researcher",
    "educator",
    "grievance_navigator",
}


def _build_execution_plan(agents: list, intent: str, category: str) -> list:
    """
    Build an ordered execution plan with parallel groups.

    Returns list of:
    {
        "agent": agent_name,
        "task": description,
        "priority": 1|2|3,
        "parallel_group": int  # same group = can run in parallel
    }
    """
    if not agents:
        return []

    plan = []
    group = 1
    scheduled = set()

    # First pass: agents with no dependencies (or whose deps are already scheduled)
    priority_agents = [a for a in agents if a not in _SEQUENTIAL_DEPENDENCIES]
    if priority_agents:
        for agent in priority_agents:
            plan.append({
                "agent": agent,
                "task": _agent_task(agent, intent, category),
                "priority": 1,
                "parallel_group": group,
            })
            scheduled.add(agent)
        group += 1

    # Second pass: agents that depend on first group
    dependent_agents = [a for a in agents if a in _SEQUENTIAL_DEPENDENCIES and a not in scheduled]
    for agent in dependent_agents:
        deps = _SEQUENTIAL_DEPENDENCIES.get(agent, [])
        deps_met = all(d in scheduled or d not in agents for d in deps)
        if deps_met:
            plan.append({
                "agent": agent,
                "task": _agent_task(agent, intent, category),
                "priority": 2,
                "parallel_group": group,
            })
            scheduled.add(agent)
    if dependent_agents:
        group += 1

    # Third pass: anything remaining
    remaining = [a for a in agents if a not in scheduled]
    for agent in remaining:
        plan.append({
            "agent": agent,
            "task": _agent_task(agent, intent, category),
            "priority": 3,
            "parallel_group": group,
        })

    return plan


def _agent_task(agent: str, intent: str, category: str) -> str:
    """Generate a task description for the agent."""
    task_templates = {
        "policy_analyzer": f"Analyze uploaded {category} policy document — extract all fields, score, identify gaps",
        "recommender": f"Recommend {category} insurance products based on user profile and gaps identified",
        "claims_guide": f"Provide step-by-step claims guidance for {category} insurance",
        "calculator": "Perform financial calculations with step-by-step working",
        "surrender_calculator": "Calculate surrender value, IRR, and hold vs surrender analysis",
        "researcher": f"Research current {category} insurance market data and insurer reputation",
        "regulation_engine": "Lookup applicable IRDAI regulations and consumer rights",
        "risk_detector": "Detect mis-selling patterns, coverage gaps, and risk flags",
        "educator": "Explain insurance concepts in simple, jargon-free language",
        "portfolio_optimizer": "Analyze full insurance portfolio for gaps and optimization",
        "tax_advisor": "Calculate insurance-specific tax benefits under 80C/80D/10(10D)",
        "grievance_navigator": "Guide user through IRDAI complaint and ombudsman process",
    }
    return task_templates.get(agent, f"Execute {intent} task for {category}")


async def run(state: HibiscusState) -> dict:
    """Create execution plan from classified intent."""
    plog = PipelineLogger(
        component="execution_planning",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    start = time.time()
    plog.step_start("execution_planning")

    agents = state.get("agents_needed", [])
    intent = state.get("intent", "general_chat")
    category = state.get("category", "general")

    plan = _build_execution_plan(agents, intent, category)

    latency_ms = int((time.time() - start) * 1000)
    plog.step_complete(
        "execution_planning",
        latency_ms=latency_ms,
        agents_planned=len(plan),
        parallel_groups=len(set(p["parallel_group"] for p in plan)) if plan else 0,
        plan_summary=[p["agent"] for p in plan],
    )

    return {"execution_plan": plan}
