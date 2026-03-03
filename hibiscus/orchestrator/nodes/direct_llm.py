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

    # Document context — inject full extraction so LLM can answer policy-specific questions
    if state.get("document_context"):
        doc = state["document_context"]
        extraction = doc.get("extraction") or {}
        if extraction:
            import json as _json
            parts.append("USER'S POLICY (full details):")
            parts.append(f"  File: {doc.get('filename', 'policy.pdf')}")
            for field, val in extraction.items():
                if val and field not in ("raw_text", "page_references", "_id"):
                    if isinstance(val, (dict, list)):
                        parts.append(f"  {field}: {_json.dumps(val, ensure_ascii=False)[:300]}")
                    else:
                        parts.append(f"  {field}: {val}")
        else:
            parts.append(f"USER'S POLICY: {extraction.get('policy_type', 'insurance')} policy"
                         f" from {extraction.get('insurer', 'unknown insurer')}")

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
    intent = state.get("intent", "general_chat")
    complexity = state.get("complexity", "L1")
    plog.step_start("direct_llm", complexity=complexity, intent=intent)

    message = state.get("message", "")
    context = _build_context_from_state(state)
    tier = state.get("primary_model", "deepseek_v3")

    # ── Response cache check (L1 educational/general only) ────────────────
    # Skip cache when user has document context or session history (personalized)
    from hibiscus.memory.layers.response_cache import (
        is_cacheable, get_cached_response, set_cached_response,
    )
    use_cache = is_cacheable(
        intent=intent,
        has_document=state.get("has_document", False),
        uploaded_files=state.get("uploaded_files", []),
        document_context=state.get("document_context"),
    )
    # Only serve from cache if there is no user-specific context in the prompt
    if use_cache and not context:
        cached = await get_cached_response(message)
        if cached:
            plog.step_complete("direct_llm", latency_ms=int((time.time() - start) * 1000),
                               cache_hit=True)
            return cached

    user_content = message
    if context:
        user_content = f"{context}\n\nUser question: {message}"

    try:
        from hibiscus.llm.router import call_llm
        # Cap tokens for L1/L2 — concise answers; users don't need 4096-token essays.
        max_tokens = 800 if complexity == "L1" else 1500
        llm_response = await call_llm(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            tier=tier,
            conversation_id=state.get("conversation_id", "?"),
            agent="direct_llm",
            extra_kwargs={"max_tokens": max_tokens},
        )

        content = llm_response["content"]
        latency_ms = int((time.time() - start) * 1000)

        plog.step_complete(
            "direct_llm",
            latency_ms=latency_ms,
            tokens_in=llm_response.get("tokens_in", 0),
            tokens_out=llm_response.get("tokens_out", 0),
            model=llm_response.get("model", tier),
            cache_hit=False,
        )

        # Generate follow-up suggestions
        follow_ups = _generate_follow_ups(intent, state.get("category", ""))

        result = {
            "response": content,
            "response_type": "text",
            "confidence": 0.75,  # Direct LLM confidence (no tool grounding)
            "sources": [{"type": "llm_reasoning", "confidence": 0.75}],
            "follow_up_suggestions": follow_ups,
            "total_tokens_in": llm_response.get("tokens_in", 0),
            "total_tokens_out": llm_response.get("tokens_out", 0),
            "agents_invoked": [],
        }

        # Store in cache for future identical queries (only for cacheable queries)
        if use_cache and not context:
            await set_cached_response(message, result)

        return result

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
