"""
Memory Extractor
================
After every conversation turn, extracts:
1. Profile updates (age, family, city, income band, etc.)
2. Knowledge insights (preferences, concerns, facts, history, family)
3. Portfolio updates (new policy info mentioned in conversation)
4. Conversation summary (stored in L2 for cross-session recall)

Design principles:
  - Runs asynchronously — does NOT block response delivery.
  - Called via asyncio.create_task() from the memory_storage orchestrator node.
  - Uses DeepSeek V3.2 (cheap, fast, good enough for structured extraction).
  - Extraction prompt returns strict JSON; any parse failure is logged and
    dropped — never raises to the caller.
  - All extracted values go through the appropriate memory layer's validation
    before persistence; this module does not write to storage directly.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional

from hibiscus.config import settings
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Extraction prompt ─────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are a memory extraction assistant for Hibiscus, India's AI insurance engine.

Given the last portion of a conversation, extract structured information in JSON format.

Return ONLY a valid JSON object with these exact keys:

{
  "profile_updates": {
    // Any of: age (int), gender (string), city (string), city_tier (1|2|3),
    // state (string), occupation (string), income_band ("0-3L"|"3-7L"|"7-15L"|"15L+"),
    // family_structure ("single"|"married"|"married_with_children"),
    // num_dependents (int), smoker_status (bool), risk_tolerance ("low"|"medium"|"high"),
    // communication_preference ("formal"|"casual"), language_preference ("english"|"hindi"),
    // health_conditions_categories (list of strings: ["diabetes","hypertension"])
    // Only include fields that are EXPLICITLY stated in the conversation. Never infer.
  },
  "insights": [
    {
      "text": "One sentence plain-text fact about the user",
      "type": "preference"|"concern"|"fact"|"history"|"family",
      "confidence": 0.0 to 1.0
    }
    // Include up to 5 most important insights only
  ],
  "portfolio_updates": [
    {
      "doc_id": null,
      "policy_type": "health"|"life_term"|"life_endowment"|"life_ulip"|"motor"|"travel"|"pa"|null,
      "insurer": "insurer name or null",
      "product_name": "product name or null",
      "sum_insured": integer or null,
      "annual_premium": integer or null,
      "payment_status": "active"|"lapsed"|"paid_up"|"surrendered"|null,
      "notes": "brief note or null"
    }
    // Only include if the user mentions a REAL policy they actually have.
    // Empty array if no policy info was shared.
  ]
}

CRITICAL RULES:
- Do NOT invent data. If not stated, omit the field.
- For profile_updates, only include fields with concrete evidence from the conversation.
- For health_conditions_categories, use categories ONLY ("diabetes", "hypertension", "cardiac",
  "cancer", "respiratory", "mental_health", "orthopedic", "other") — never raw diagnoses.
- For sum_insured and premium, convert to integer rupees (e.g. "5 lakh" = 500000).
- For insights, confidence > 0.85 means explicitly stated; 0.6–0.85 means clearly implied.
- If nothing useful was extracted, return empty objects/arrays for each key.
"""

_EXTRACTION_MAX_TOKENS = 1024
_CONVERSATION_WINDOW = 15      # Last N messages to send to extractor


# ── Main entry point ──────────────────────────────────────────────────────────

async def extract_and_store_memories(
    user_id: str,
    session_id: str,
    conversation_id: str,
    messages: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Fire-and-forget memory extraction and storage.

    Designed to be called as:
        asyncio.create_task(extract_and_store_memories(...))

    Never raises exceptions to the caller.  All failures are logged.

    Args:
        user_id:         EAZR user identifier.
        session_id:      Current session ID.
        conversation_id: Conversation ID (for outcome tracing).
        messages:        Full list of {role, content} message dicts.
        context:         Optional additional context (e.g. active doc_id).
    """
    try:
        await _run_extraction(
            user_id=user_id,
            session_id=session_id,
            conversation_id=conversation_id,
            messages=messages,
            context=context or {},
        )
    except Exception as exc:
        # Final safety net — extraction must never crash the main pipeline
        logger.warning(
            "memory_extraction_crashed",
            user_id=user_id,
            session_id=session_id,
            error=str(exc),
        )


async def _run_extraction(
    user_id: str,
    session_id: str,
    conversation_id: str,
    messages: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> None:
    """Internal implementation — raises on error (caught by caller)."""
    if not messages:
        return

    t_start = time.time()

    # ── Step 1: Format recent messages for LLM ────────────────────────────────
    recent = messages[-_CONVERSATION_WINDOW:]
    conversation_text = "\n".join(
        f"{m.get('role', 'user').upper()}: {str(m.get('content', ''))[:600]}"
        for m in recent
    )

    prompt_messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Extract memory from this conversation:\n\n"
                f"{conversation_text}\n\n"
                f"Return ONLY the JSON object. No explanation."
            ),
        },
    ]

    # ── Step 2: Call DeepSeek V3.2 ────────────────────────────────────────────
    extracted: Dict[str, Any] = {}
    try:
        from hibiscus.llm.router import call_llm

        result = await call_llm(
            messages=prompt_messages,
            tier="deepseek_v3",
            extra_kwargs={"max_tokens": _EXTRACTION_MAX_TOKENS},
        )
        raw_text = result.get("content", "").strip()
        extracted = _parse_json_response(raw_text)
    except Exception as exc:
        logger.warning("memory_llm_call_failed", user_id=user_id, error=str(exc))
        return   # Nothing to store

    if not extracted:
        logger.info("memory_nothing_extracted", user_id=user_id, session_id=session_id)
        return

    # ── Step 3: Store profile updates (L3) ───────────────────────────────────
    profile_updates = extracted.get("profile_updates", {})
    if profile_updates:
        try:
            from hibiscus.memory.layers.profile import upsert_user_profile
            await upsert_user_profile(user_id, profile_updates)
            logger.info(
                "memory_profile_updated",
                user_id=user_id,
                fields=list(profile_updates.keys()),
            )
        except Exception as exc:
            logger.warning("memory_profile_update_failed", error=str(exc))

    # ── Step 4: Store knowledge insights (L4) ────────────────────────────────
    insights = extracted.get("insights", [])
    stored_insights = 0
    for ins in insights:
        if not isinstance(ins, dict):
            continue
        text = ins.get("text", "").strip()
        itype = ins.get("type", "fact")
        confidence = float(ins.get("confidence", 0.7))
        if not text or confidence < 0.50:   # Skip low-confidence extractions
            continue
        try:
            from hibiscus.memory.layers.knowledge import store_insight
            await store_insight(
                user_id=user_id,
                insight_text=text,
                insight_type=itype,
                confidence=confidence,
            )
            stored_insights += 1
        except Exception as exc:
            logger.warning("memory_insight_store_failed", error=str(exc))

    if stored_insights:
        logger.info("memory_insights_stored", user_id=user_id, count=stored_insights)

    # ── Step 5: Store portfolio updates (L3b) ────────────────────────────────
    portfolio_updates = extracted.get("portfolio_updates", [])
    stored_policies = 0
    active_doc_id = context.get("doc_id")
    for policy in portfolio_updates:
        if not isinstance(policy, dict):
            continue
        # Attach the active doc_id if extraction didn't produce one
        if not policy.get("doc_id") and active_doc_id:
            policy["doc_id"] = active_doc_id
        try:
            from hibiscus.memory.layers.portfolio import add_policy
            await add_policy(user_id, policy)
            stored_policies += 1
        except Exception as exc:
            logger.warning("memory_portfolio_update_failed", error=str(exc))

    if stored_policies:
        logger.info("memory_portfolio_updated", user_id=user_id, count=stored_policies)

    # ── Step 6: Generate and store conversation summary (L2) ──────────────────
    try:
        from hibiscus.memory.layers.conversation import extract_and_store_summary
        summary = await extract_and_store_summary(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
        )
        if summary:
            logger.info(
                "memory_summary_stored",
                user_id=user_id,
                session_id=session_id,
                length=len(summary),
            )
    except Exception as exc:
        logger.warning("memory_summary_failed", error=str(exc))

    elapsed = round(time.time() - t_start, 3)
    logger.info(
        "memory_extraction_complete",
        user_id=user_id,
        session_id=session_id,
        profile_fields=len(profile_updates),
        insights=stored_insights,
        policies=stored_policies,
        elapsed_s=elapsed,
    )


# ── JSON parsing helpers ──────────────────────────────────────────────────────

def _parse_json_response(raw: str) -> Dict[str, Any]:
    """Extract the first JSON object from an LLM response string.

    Handles cases where the model wraps JSON in markdown code fences.
    Returns empty dict on any parse failure.
    """
    if not raw:
        return {}

    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    cleaned = cleaned.rstrip("`").strip()

    # Try direct parse first
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # Try to extract the first {...} block with a regex
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    logger.warning("memory_json_parse_failed", raw_preview=raw[:200])
    return {}


# ── Convenience wrapper for fire-and-forget usage ─────────────────────────────

def schedule_extraction(
    user_id: str,
    session_id: str,
    conversation_id: str,
    messages: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Schedule memory extraction as a background task.

    Call from synchronous or async orchestrator nodes.  Uses
    asyncio.create_task() so it does not block the response path.

    Usage:
        schedule_extraction(user_id, session_id, conversation_id, messages)
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(
                extract_and_store_memories(
                    user_id=user_id,
                    session_id=session_id,
                    conversation_id=conversation_id,
                    messages=messages,
                    context=context,
                )
            )
        else:
            logger.warning(
                "memory_extraction_skipped",
                reason="no_running_event_loop",
                user_id=user_id,
            )
    except RuntimeError as exc:
        logger.warning("memory_extraction_schedule_failed", error=str(exc))
