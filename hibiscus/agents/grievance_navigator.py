"""
GrievanceNavigatorAgent — Agent 12
=====================================
IRDAI complaint and ombudsman guide.

Guides users through the IRDAI complaint process and ombudsman
escalation with specific timelines, contact information, and
a clear statement of consumer rights.

Phase 1 stub — full implementation in Phase 2.
"""
from typing import Any, Dict

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.orchestrator.state import HibiscusState


class GrievanceNavigatorAgent(BaseAgent):
    name = "grievance_navigator"
    description = "IRDAI complaint and ombudsman guide"
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
                            "You are EAZR's grievance navigator. Guide user through IRDAI "
                            "complaint process and ombudsman escalation. Be specific about "
                            "timelines, contact info, and consumer rights.\n\n"
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


_agent = GrievanceNavigatorAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
