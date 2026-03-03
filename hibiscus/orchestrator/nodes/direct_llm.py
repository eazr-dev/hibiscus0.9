"""
Direct LLM Node — Fast Path
============================
For L1/L2 queries that don't need specialist agents.
Examples: "What is a deductible?", "How does copay work?"

Skips the full agent pipeline for speed and cost.
Still uses the hallucination and compliance guardrails.
"""
import time
from pathlib import Path

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState

_PROMPT_DIR = Path(__file__).parent.parent.parent / "llm" / "prompts"
_SYSTEM_PROMPT = (_PROMPT_DIR / "system" / "hibiscus_core.txt").read_text()


def _build_context_from_state(state: HibiscusState) -> str:
    """Build context string from available state."""
    parts = []

    # Document context
    if state.get("document_context"):
        doc = state["document_context"]
        parts.append(f"USER'S POLICY: {doc.get('policy_type', 'insurance')} policy from {doc.get('insurer', 'insurer')}")

    # Session history
    if state.get("session_history"):
        history = state["session_history"][-4:]  # Last 4 turns
        parts.append("RECENT CONVERSATION:")
        for turn in history:
            role = "User" if turn.get("role") == "user" else "Hibiscus"
            parts.append(f"  {role}: {turn.get('content', '')[:200]}")

    return "\n".join(parts) if parts else ""


async def run(state: HibiscusState) -> dict:
    """Handle L1/L2 queries directly without specialist agents."""
    plog = PipelineLogger(
        component="direct_llm",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    start = time.time()
    plog.step_start("direct_llm", complexity=state.get("complexity"), intent=state.get("intent"))

    message = state.get("message", "")
    context = _build_context_from_state(state)
    tier = state.get("primary_model", "deepseek_v3")

    user_content = message
    if context:
        user_content = f"{context}\n\nUser question: {message}"

    try:
        from hibiscus.llm.router import call_llm
        llm_response = await call_llm(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            tier=tier,
            conversation_id=state.get("conversation_id", "?"),
            agent="direct_llm",
        )

        content = llm_response["content"]
        latency_ms = int((time.time() - start) * 1000)

        plog.step_complete(
            "direct_llm",
            latency_ms=latency_ms,
            tokens_in=llm_response.get("tokens_in", 0),
            tokens_out=llm_response.get("tokens_out", 0),
            model=llm_response.get("model", tier),
        )

        # Generate follow-up suggestions
        follow_ups = _generate_follow_ups(state.get("intent", ""), state.get("category", ""))

        return {
            "response": content,
            "response_type": "text",
            "confidence": 0.75,  # Direct LLM confidence (no tool grounding)
            "sources": [{"type": "llm_reasoning", "confidence": 0.75}],
            "follow_up_suggestions": follow_ups,
            "total_tokens_in": llm_response.get("tokens_in", 0),
            "total_tokens_out": llm_response.get("tokens_out", 0),
            "agents_invoked": [],
        }

    except Exception as e:
        plog.error("direct_llm", error=str(e))
        return {
            "response": "I'm having trouble connecting to the AI service right now. Please try again in a moment.",
            "confidence": 0.0,
            "sources": [],
            "errors": state.get("errors", []) + [f"direct_llm_error: {str(e)}"],
        }


def _generate_follow_ups(intent: str, category: str) -> list:
    """Generate contextual follow-up suggestions."""
    suggestions = {
        "educate": [
            f"What are common {category} insurance exclusions?",
            f"How do I compare {category} insurance plans?",
            "What is the IRDAI's role in protecting policyholders?",
        ],
        "general_chat": [
            "How do I analyze my insurance policy?",
            "What is the EAZR Protection Score?",
            "How do I file a claim?",
        ],
        "claim": [
            "What documents are needed for claim filing?",
            "What is the claim settlement timeline?",
            "How do I escalate a rejected claim?",
        ],
    }
    return suggestions.get(intent, [
        "Would you like me to analyze your policy document?",
        "Do you want product recommendations for your profile?",
        "Do you have questions about claim filing?",
    ])
