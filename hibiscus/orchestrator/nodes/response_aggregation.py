"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Response aggregation node — merges multi-agent outputs into a single coherent response.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
from typing import Any, Dict, List

from hibiscus.observability.logger import PipelineLogger
from hibiscus.orchestrator.state import HibiscusState


def _get_language_rule(language: str) -> str:
    """Return language synthesis rule if non-English."""
    if language == "en":
        return ""
    from hibiscus.utils.language_detect import get_language_instruction
    instruction = get_language_instruction(language)
    return f"9. {instruction}" if instruction else ""


def _build_aggregation_prompt(
    message: str,
    agent_outputs: List[Dict[str, Any]],
    category: str,
    intent: str,
    user_profile: Dict | None,
    language: str = "en",
) -> str:
    """Build the prompt for response aggregation."""
    agent_sections = []
    for output in agent_outputs:
        if output.get("success") and output.get("response"):
            agent_name = output.get("agent", "unknown")
            confidence = output.get("confidence", 0.0)
            response_text = output.get("response", "")
            agent_sections.append(
                f"### From {agent_name} (confidence: {confidence:.0%}):\n{response_text}"
            )

    agents_text = "\n\n".join(agent_sections) if agent_sections else "No agent responses available."

    profile_text = ""
    if user_profile:
        profile_text = f"User profile: {user_profile.get('age', '?')} years, {user_profile.get('city', '?')}"

    return f"""Synthesize these specialist agent responses into ONE coherent response for the user.

USER'S QUESTION: {message}
CATEGORY: {category}
INTENT: {intent}
{profile_text}

AGENT RESPONSES:
{agents_text}

SYNTHESIS RULES:
1. Combine insights from all agents into a single, well-structured response
2. DO NOT repeat information — present it once, clearly
3. Maintain all source citations and page references from agent responses
4. If agents agree on a point, state it as confirmed
5. If agents have different confidence levels, use the higher confidence one
6. Keep all IRDAI disclaimers intact
7. Add 3 follow-up question suggestions at the end (JSON list)
8. Use Indian formats: ₹, lakhs/crores, DD/MM/YYYY
{_get_language_rule(language)}
OUTPUT FORMAT:
[Your synthesized response here]

---FOLLOW_UP_JSON---
["suggestion 1", "suggestion 2", "suggestion 3"]
"""


async def run(state: HibiscusState) -> dict:
    """Aggregate agent outputs into final response."""
    plog = PipelineLogger(
        component="response_aggregation",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    start = time.time()
    plog.step_start("response_aggregation")

    agent_outputs = state.get("agent_outputs", [])
    message = state.get("message", "")
    category = state.get("category", "general")
    intent = state.get("intent", "general_chat")
    user_profile = state.get("user_profile")

    # If only one successful agent, use its response directly
    successful = [o for o in agent_outputs if o.get("success") and o.get("response")]
    if len(successful) == 1:
        output = successful[0]
        sources = output.get("sources", [])
        latency_ms = int((time.time() - start) * 1000)
        plog.step_complete("response_aggregation", latency_ms=latency_ms, agents_combined=1)
        return {
            "response": output.get("response", ""),
            "confidence": output.get("confidence", 0.0),
            "sources": sources,
            "follow_up_suggestions": output.get("follow_up_suggestions", []),
            "products_relevant": output.get("products_relevant", []),
        }

    # Multiple agents → synthesize with LLM
    try:
        from hibiscus.llm.router import call_llm
        language = state.get("language", "en")
        prompt = _build_aggregation_prompt(message, agent_outputs, category, intent, user_profile, language)

        llm_response = await call_llm(
            messages=[
                {"role": "system", "content": "You are Hibiscus response synthesizer. Follow the output format exactly."},
                {"role": "user", "content": prompt},
            ],
            tier="deepseek_v3",
            conversation_id=state.get("conversation_id", "?"),
            agent="response_aggregation",
        )

        content = llm_response["content"]

        # ORCH-5: Extract follow-up suggestions with robust JSON parsing.
        # Use a greedy match for the JSON array to handle nested brackets and
        # multi-line content, then validate with json.loads().
        import json
        import re
        follow_ups = []
        json_match = re.search(r'---FOLLOW_UP_JSON---\s*(\[[\s\S]*\])', content)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                if isinstance(parsed, list) and all(isinstance(s, str) for s in parsed):
                    follow_ups = parsed
                content = content[:content.find("---FOLLOW_UP_JSON---")].strip()
            except (json.JSONDecodeError, ValueError):
                # Malformed JSON from LLM — strip the marker but leave follow_ups empty
                content = content[:content.find("---FOLLOW_UP_JSON---")].strip()

        # Aggregate confidence (weighted average), penalized by agent failure rate.
        confidences = [o.get("confidence", 0.0) for o in successful]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # ORCH-10: Penalize confidence when agents failed. If 2 of 3 agents
        # succeeded, completeness_ratio = 0.67, reducing overall confidence.
        total_agents = len(agent_outputs)
        if total_agents > 0:
            completeness_ratio = len(successful) / total_agents
            avg_confidence *= completeness_ratio

        # Merge sources from all agents
        all_sources = []
        for o in agent_outputs:
            all_sources.extend(o.get("sources", []))

        latency_ms = int((time.time() - start) * 1000)
        plog.step_complete(
            "response_aggregation",
            latency_ms=latency_ms,
            agents_combined=len(successful),
            avg_confidence=round(avg_confidence, 2),
        )

        return {
            "response": content,
            "confidence": avg_confidence,
            "sources": all_sources,
            "follow_up_suggestions": follow_ups,
            "total_tokens_in": llm_response.get("tokens_in", 0),
            "total_tokens_out": llm_response.get("tokens_out", 0),
        }

    except Exception as e:
        plog.error("response_aggregation", error=str(e))
        # Fallback: concatenate responses
        combined = "\n\n".join(
            f"**{o['agent']}**: {o.get('response', '')}"
            for o in successful
        )
        return {
            "response": combined or "I encountered an issue synthesizing the response. Please try again.",
            "confidence": 0.5,
            "sources": [],
            "errors": state.get("errors", []) + [f"aggregation_error: {str(e)}"],
        }
