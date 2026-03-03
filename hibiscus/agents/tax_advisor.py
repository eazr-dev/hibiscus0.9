"""
TaxAdvisorAgent — Agent 11
============================
Insurance tax benefits advisor.

Calculates 80C, 80D, and 10(10D) tax benefits with step-by-step
working. States all conditions and exceptions. Recommends consulting
a qualified tax professional for binding advice.

Phase 1 stub — full implementation in Phase 2.
"""
from typing import Any, Dict

from hibiscus.agents.base import BaseAgent, AgentResult
from hibiscus.orchestrator.state import HibiscusState


class TaxAdvisorAgent(BaseAgent):
    name = "tax_advisor"
    description = "Insurance tax benefits advisor"
    default_tier = "deepseek_r1"

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
                            "You are EAZR's tax advisor. Calculate 80C, 80D, 10(10D) benefits. "
                            "Show step-by-step calculation. Note conditions and exceptions. "
                            "Include disclaimer about consulting tax professional.\n\n"
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


_agent = TaxAdvisorAgent()


async def run(state: HibiscusState) -> Dict[str, Any]:
    """Entry point for agent_dispatch."""
    return await _agent(state)
