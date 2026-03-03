"""
EducatorAgent — Agent 9
========================
Insurance concepts educator.

Explains insurance concepts in simple, jargon-free language
with Indian context and analogies. Assumes zero prior knowledge.

Phase 1 stub — full implementation in Phase 2.
"""
from typing import Any, Dict

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.orchestrator.state import HibiscusState


class EducatorAgent(BaseAgent):
    name = "educator"
    description = "Insurance concepts educator"
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
                            "You are EAZR's educator. Explain insurance concepts in simple, "
                            "jargon-free language with Indian context. Use analogies. "
                            "Assume zero prior knowledge.\n\n"
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


_agent = EducatorAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
