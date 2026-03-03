"""
Hibiscus Base Agent
===================
ABC for all 12 specialist agents.

Every agent:
- Logs on entry, tool calls, and exit
- Returns: {response, confidence, sources, latency_ms, tokens_in, tokens_out}
- Has confidence scoring
- Handles timeouts and LLM failures gracefully
- Never invents numbers — only presents what tools provide
"""
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


class AgentResult:
    """Structured result from any agent."""

    def __init__(
        self,
        response: str,
        confidence: float,
        sources: Optional[List[Dict[str, Any]]] = None,
        latency_ms: int = 0,
        tokens_in: int = 0,
        tokens_out: int = 0,
        follow_up_suggestions: Optional[List[str]] = None,
        eazr_products_relevant: Optional[List[str]] = None,
        structured_data: Optional[Dict[str, Any]] = None,
    ):
        self.response = response
        self.confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        self.sources = sources or []
        self.latency_ms = latency_ms
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.follow_up_suggestions = follow_up_suggestions or []
        self.eazr_products_relevant = eazr_products_relevant or []
        self.structured_data = structured_data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "confidence": self.confidence,
            "sources": self.sources,
            "latency_ms": self.latency_ms,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "follow_up_suggestions": self.follow_up_suggestions,
            "eazr_products_relevant": self.eazr_products_relevant,
            "structured_data": self.structured_data,
        }


class BaseAgent(ABC):
    """Abstract base class for all Hibiscus specialist agents."""

    name: str = "base"
    description: str = "Base agent"
    default_tier: str = "deepseek_v3"  # LLM tier (override in subclass)

    # Path to prompt file (relative to hibiscus/llm/prompts/agents/)
    prompt_file: Optional[str] = None

    def __init__(self):
        self._prompt_dir = Path(__file__).parent.parent / "llm" / "prompts"
        self._system_prompt = self._load_system_prompt()
        self._agent_prompt = self._load_agent_prompt()

    def _load_system_prompt(self) -> str:
        path = self._prompt_dir / "system" / "hibiscus_core.txt"
        if path.exists():
            return path.read_text()
        return "You are Hibiscus, EAZR's AI insurance intelligence engine."

    def _load_agent_prompt(self) -> str:
        if not self.prompt_file:
            return ""
        path = self._prompt_dir / "agents" / self.prompt_file
        if path.exists():
            return path.read_text()
        return ""

    @abstractmethod
    async def execute(self, state: HibiscusState) -> AgentResult:
        """
        Core agent logic. Subclasses implement this.

        Rules:
        1. Call tools to get data — never invent numbers
        2. Compute confidence based on data sources
        3. Return AgentResult with all fields
        """

    async def __call__(self, state: HibiscusState) -> Dict[str, Any]:
        """Called by agent_dispatch. Wraps execute() with logging."""
        plog = PipelineLogger(
            component=f"agent.{self.name}",
            request_id=state.get("request_id", "?"),
            session_id=state.get("session_id", "?"),
            user_id=state.get("user_id", "?"),
        )
        start = time.time()
        plog.agent_start(
            agent=self.name,
            model=self.default_tier,
            task=state.get("intent", ""),
        )

        try:
            result = await self.execute(state)
            latency_ms = int((time.time() - start) * 1000)
            result.latency_ms = latency_ms

            plog.agent_complete(
                agent=self.name,
                confidence=result.confidence,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                latency_ms=latency_ms,
            )

            return {"success": True, **result.to_dict()}

        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            plog.error(f"agent_{self.name}", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "response": self._error_response(),
                "confidence": 0.0,
                "sources": [],
                "latency_ms": latency_ms,
            }

    def _error_response(self) -> str:
        return (
            f"I encountered an issue while processing your request with the "
            f"{self.description.lower()}. Please try again or rephrase your question."
        )

    def _format_currency(self, amount: float) -> str:
        """Format amount in Indian system: ₹ with lakhs/crores."""
        if amount >= 1_00_00_000:  # 1 crore
            return f"₹{amount / 1_00_00_000:.2f} crore"
        elif amount >= 1_00_000:  # 1 lakh
            return f"₹{amount / 1_00_000:.2f} lakh"
        else:
            return f"₹{amount:,.0f}"

    def _confidence_qualifier(self, confidence: float) -> str:
        """Return appropriate qualifier phrase based on confidence."""
        from hibiscus.config import settings
        if confidence >= settings.confidence_threshold_high:
            return ""  # State as fact, no qualifier needed
        elif confidence >= settings.confidence_threshold_medium:
            return "Based on available data, "
        elif confidence >= settings.confidence_threshold_low:
            return "I believe, though please verify: "
        else:
            return "I'm not certain, but: "
