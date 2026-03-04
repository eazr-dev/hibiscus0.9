"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Agent dispatch node — fans out to specialist agents and collects structured outputs.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import time
from typing import Any, Dict, List

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


# ── Agent registry ────────────────────────────────────────────────────────
_AGENT_MAP = {
    "policy_analyzer": "hibiscus.agents.policy_analyzer",
    "recommender": "hibiscus.agents.recommender",
    "claims_guide": "hibiscus.agents.claims_guide",
    "calculator": "hibiscus.agents.calculator",
    "surrender_calculator": "hibiscus.agents.surrender_calculator",
    "researcher": "hibiscus.agents.researcher",
    "regulation_engine": "hibiscus.agents.regulation_engine",
    "risk_detector": "hibiscus.agents.risk_detector",
    "educator": "hibiscus.agents.educator",
    "portfolio_optimizer": "hibiscus.agents.portfolio_optimizer",
    "tax_advisor": "hibiscus.agents.tax_advisor",
    "grievance_navigator": "hibiscus.agents.grievance_navigator",
}

# ORCH-2: Module-level cache to avoid repeated importlib.import_module() calls
# in the hot path. Once an agent module is loaded, subsequent dispatches reuse it.
_AGENT_MODULE_CACHE: Dict[str, Any] = {}

# ORCH-3: Per-agent timeout in seconds. Individual agent calls that exceed this
# are cancelled to prevent a single slow agent from blocking the entire group.
_AGENT_TIMEOUT_SECONDS = 30


async def _get_agent(agent_name: str):
    """Lazy-load agent to avoid circular imports, with module-level caching."""
    if agent_name in _AGENT_MODULE_CACHE:
        return _AGENT_MODULE_CACHE[agent_name]

    module_path = _AGENT_MAP.get(agent_name)
    if not module_path:
        raise ValueError(f"Unknown agent: {agent_name}")
    import importlib
    module = importlib.import_module(module_path)
    _AGENT_MODULE_CACHE[agent_name] = module
    return module


async def _dispatch_agent(
    agent_name: str,
    task: Dict[str, Any],
    state: HibiscusState,
    plog: PipelineLogger,
) -> Dict[str, Any]:
    """Dispatch a single agent and return its output."""
    start = time.time()
    plog.agent_start(
        agent=agent_name,
        model=state.get("primary_model", "deepseek_v3"),
        task=task.get("task", ""),
    )

    try:
        module = await _get_agent(agent_name)
        # ORCH-3: Enforce per-agent timeout to prevent a single slow agent
        # from blocking the entire parallel group.
        result = await asyncio.wait_for(
            module.run(state),
            timeout=_AGENT_TIMEOUT_SECONDS,
        )

        latency_ms = int((time.time() - start) * 1000)
        confidence = result.get("confidence", 0.0)

        plog.agent_complete(
            agent=agent_name,
            confidence=confidence,
            tokens_in=result.get("tokens_in", 0),
            tokens_out=result.get("tokens_out", 0),
            latency_ms=latency_ms,
        )

        return {
            "agent": agent_name,
            "success": True,
            "latency_ms": latency_ms,
            **result,
        }

    except asyncio.TimeoutError:
        latency_ms = int((time.time() - start) * 1000)
        plog.error(f"agent_{agent_name}", error=f"Timed out after {_AGENT_TIMEOUT_SECONDS}s")
        return {
            "agent": agent_name,
            "success": False,
            "error": f"Agent timed out after {_AGENT_TIMEOUT_SECONDS}s",
            "confidence": 0.0,
            "latency_ms": latency_ms,
        }

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        plog.error(f"agent_{agent_name}", error=str(e))
        return {
            "agent": agent_name,
            "success": False,
            "error": str(e),
            "confidence": 0.0,
            "latency_ms": latency_ms,
        }


async def run(state: HibiscusState) -> dict:
    """Dispatch all agents per execution plan, respecting parallel groups."""
    plog = PipelineLogger(
        component="agent_dispatch",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    start = time.time()

    plan = state.get("execution_plan", [])
    if not plan:
        return {"agent_outputs": [], "agents_invoked": []}

    plog.step_start("agent_dispatch", total_agents=len(plan))

    # Group agents by parallel_group
    groups: Dict[int, List[Dict]] = {}
    for task in plan:
        g = task.get("parallel_group", 1)
        groups.setdefault(g, []).append(task)

    all_outputs: List[Dict[str, Any]] = []
    agents_invoked: List[str] = []

    # Execute each group (sequential groups, parallel within group)
    for group_id in sorted(groups.keys()):
        group_tasks = groups[group_id]
        plog.step_start(f"dispatch_group_{group_id}", agents=[t["agent"] for t in group_tasks])

        # Run all agents in this group in parallel
        coros = [
            _dispatch_agent(task["agent"], task, state, plog)
            for task in group_tasks
        ]
        results = await asyncio.gather(*coros, return_exceptions=True)

        for i, result in enumerate(results):
            agent_name = group_tasks[i]["agent"]
            agents_invoked.append(agent_name)
            if isinstance(result, Exception):
                all_outputs.append({
                    "agent": agent_name,
                    "success": False,
                    "error": str(result),
                    "confidence": 0.0,
                })
            else:
                all_outputs.append(result)

    latency_ms = int((time.time() - start) * 1000)
    plog.step_complete(
        "agent_dispatch",
        latency_ms=latency_ms,
        agents_invoked=agents_invoked,
        successful=sum(1 for o in all_outputs if o.get("success")),
        failed=sum(1 for o in all_outputs if not o.get("success")),
    )

    return {
        "agent_outputs": all_outputs,
        "agents_invoked": agents_invoked,
    }
