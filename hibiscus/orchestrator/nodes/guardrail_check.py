"""
Guardrail Check Node
====================
Runs all active guardrails on the assembled response before sending.
Guardrails: hallucination, compliance, financial, PII.
"""
import time

from hibiscus.observability.logger import PipelineLogger
from hibiscus.observability.metrics import record_guardrail_failure as _metric_guardrail
from hibiscus.orchestrator.state import HibiscusState


async def run(state: HibiscusState) -> dict:
    """Run all guardrails on the current response."""
    plog = PipelineLogger(
        component="guardrail_check",
        request_id=state.get("request_id", "?"),
        session_id=state.get("session_id", "?"),
        user_id=state.get("user_id", "?"),
    )
    start = time.time()
    plog.step_start("guardrail_check")

    response = state.get("response", "")
    confidence = state.get("confidence", 0.0)
    sources = state.get("sources", [])
    intent = state.get("intent", "general_chat")
    guardrail_results = {}
    modified_response = response

    # ── Hallucination Guard ────────────────────────────────────────────
    try:
        from hibiscus.guardrails.hallucination import check_hallucination
        h_result = check_hallucination(
            response=response,
            sources=sources,
            confidence=confidence,
        )
        guardrail_results["hallucination"] = h_result.passed
        if not h_result.passed:
            plog.guardrail("hallucination", passed=False, reason=h_result.reason)
            _metric_guardrail("hallucination")
            modified_response = h_result.modified_response or modified_response
        else:
            plog.guardrail("hallucination", passed=True)
    except Exception as e:
        plog.error("hallucination_guardrail", error=str(e))
        guardrail_results["hallucination"] = True  # Don't block on guardrail error

    # ── Compliance Guard ───────────────────────────────────────────────
    try:
        from hibiscus.guardrails.compliance import check_compliance
        c_result = check_compliance(
            response=modified_response,
            intent=intent,
        )
        guardrail_results["compliance"] = c_result.passed
        if not c_result.passed:
            plog.guardrail("compliance", passed=False, reason=c_result.reason)
            _metric_guardrail("compliance")
        modified_response = c_result.modified_response  # Always use compliance-modified
        plog.guardrail("compliance", passed=c_result.passed)
    except Exception as e:
        plog.error("compliance_guardrail", error=str(e))
        guardrail_results["compliance"] = True

    # ── Financial Guard (basic range check) ────────────────────────────
    try:
        from hibiscus.guardrails.financial import check_financial
        f_result = check_financial(response=modified_response)
        guardrail_results["financial"] = f_result.passed
        if not f_result.passed:
            plog.guardrail("financial", passed=False, reason=f_result.reason)
            _metric_guardrail("financial")
    except Exception as e:
        plog.error("financial_guardrail", error=str(e))
        guardrail_results["financial"] = True

    # ── Emotional Guard ────────────────────────────────────────────────
    emotional_adapted = False
    try:
        from hibiscus.guardrails.emotional import check_emotional
        emotional_state = state.get("emotional_state", "neutral")
        e_result = check_emotional(
            response=modified_response,
            emotional_state=emotional_state,
            intent=intent,
        )
        guardrail_results["emotional"] = e_result.passed
        if e_result.empathy_prefix:
            modified_response = e_result.empathy_prefix + modified_response
            emotional_adapted = True
            plog.guardrail("emotional", passed=False, reason=e_result.reason,
                           escalate=e_result.escalate_to_claude)
            _metric_guardrail("emotional")
        else:
            plog.guardrail("emotional", passed=True)
    except Exception as e:
        plog.error("emotional_guardrail", error=str(e))
        guardrail_results["emotional"] = True

    # ── PII Guard ──────────────────────────────────────────────────────
    pii_check_passed = True
    try:
        from hibiscus.guardrails.pii import check_pii
        user_id = state.get("user_id", "")
        p_result = check_pii(response=modified_response, user_id=user_id)
        guardrail_results["pii"] = p_result.passed
        pii_check_passed = p_result.passed
        if not p_result.passed:
            plog.guardrail("pii", passed=False, reason=p_result.reason,
                           types_found=p_result.pii_types_found)
            _metric_guardrail("pii")
            modified_response = p_result.modified_response
        else:
            plog.guardrail("pii", passed=True)
    except Exception as e:
        plog.error("pii_guardrail", error=str(e))
        guardrail_results["pii"] = True

    latency_ms = int((time.time() - start) * 1000)
    plog.step_complete(
        "guardrail_check",
        latency_ms=latency_ms,
        all_passed=all(guardrail_results.values()),
        results=guardrail_results,
    )

    return {
        "response": modified_response,
        "guardrail_results": guardrail_results,
        "emotional_adapted": emotional_adapted,
        "pii_check_passed": pii_check_passed,
    }
