"""
RegulationEngineAgent — Agent 7
=================================
IRDAI regulation lookup and compliance.

Looks up applicable IRDAI regulations, explains consumer rights,
cites circular numbers, and directs users to authoritative sources.

Phase 1 stub — full implementation in Phase 2.
"""
from typing import Any, Dict

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.orchestrator.state import HibiscusState


class RegulationEngineAgent(BaseAgent):
    name = "regulation_engine"
    description = "IRDAI regulation lookup and compliance"
    default_tier = "deepseek_v3"

    async def execute(self, state: HibiscusState) -> AgentResult:
        message = state.get("message", "")

        try:
            from hibiscus.llm.router import call_llm

            llm_response = await call_llm(
                messages=[
                    {"role": "system", "content": self._system_prompt},
                    {
                        "role": "user",
                        "content": (
                            "You are EAZR's regulation engine. Look up applicable IRDAI "
                            "regulations and explain consumer rights. Cite circular numbers "
                            "when available. Recommend verifying at irdai.gov.in.\n\n"
                            f"User request: {message}"
                        ),
                    },
                ],
                tier=self.default_tier,
                conversation_id=state.get("conversation_id", "?"),
                agent=self.name,
            )

            return AgentResult(
                response=llm_response["content"],
                confidence=0.75,
                sources=[{"type": "llm_reasoning", "confidence": 0.75}],
                tokens_in=llm_response.get("tokens_in", 0),
                tokens_out=llm_response.get("tokens_out", 0),
            )

        except Exception as e:
            return AgentResult(
                response=self._error_response(),
                confidence=0.0,
                sources=[],
            )


_agent = RegulationEngineAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
