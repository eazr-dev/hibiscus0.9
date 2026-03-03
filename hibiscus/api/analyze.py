"""
Direct Policy Analysis Endpoint
================================
POST /hibiscus/analyze

Loads a stored document from MongoDB and runs the policy_analyzer agent
directly, bypassing the chat pipeline. Used for document-first analysis
flows triggered from botproject after PDF upload.
"""
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from hibiscus.api.schemas.analysis import AnalysisRequest, AnalysisResponse
from hibiscus.api.schemas.common import Source
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(request: AnalysisRequest, http_request: Request) -> AnalysisResponse:
    """
    Trigger a direct policy analysis for a stored document.

    Flow:
      1. Load document from MongoDB (by document_id or analysis_id)
      2. Build HibiscusState with document_context pre-populated
      3. Run policy_analyzer agent directly
      4. Run guardrail_check on result
      5. Return AnalysisResponse
    """
    start = time.time()
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))

    logger.info(
        "analyze_request",
        request_id=request_id,
        user_id=request.user_id,
        session_id=request.session_id,
        document_id=request.document_id,
        analysis_id=request.analysis_id,
    )

    # ── Step 1: Load document from memory ─────────────────────────
    document_context = None
    try:
        from hibiscus.memory.layers.document import get_latest_document
        doc = await get_latest_document(request.user_id)
        if doc:
            document_context = doc
    except Exception as e:
        logger.warning("analyze_doc_load_failed", error=str(e), request_id=request_id)

    # ── Step 2: Build state ────────────────────────────────────────
    state = {
        "request_id": request_id,
        "session_id": request.session_id,
        "user_id": request.user_id,
        "conversation_id": request.session_id,
        "message": "Analyze this policy and provide a full EAZR assessment.",
        "intent": "analyze",
        "category": "",
        "complexity": "L3",
        "emotional_state": "neutral",
        "primary_model": "deepseek_v3",
        "agents_needed": [],
        "has_document": document_context is not None,
        "document_context": document_context,
        "uploaded_files": [],
        "session_history": [],
        "response": "",
        "confidence": 0.0,
        "sources": [],
        "agents_invoked": [],
        "errors": [],
    }

    # ── Step 3: Run policy_analyzer agent ─────────────────────────
    result = {}
    try:
        from hibiscus.agents.policy_analyzer import PolicyAnalyzerAgent
        agent = PolicyAnalyzerAgent()
        result = await agent.run(state)
    except Exception as e:
        logger.error("analyze_agent_failed", error=str(e), request_id=request_id)
        latency_ms = int((time.time() - start) * 1000)
        return AnalysisResponse(
            session_id=request.session_id,
            request_id=request_id,
            response="Unable to complete policy analysis. Please try again.",
            confidence=0.0,
            sources=[],
            latency_ms=latency_ms,
            error=str(e),
        )

    response_text = result.get("response", "")
    confidence = result.get("confidence", 0.0)
    sources = result.get("sources", [])
    agents_invoked = result.get("agents_invoked", ["policy_analyzer"])
    structured_data = result.get("structured_data")
    eazr_score = None

    # Extract EAZR score if available
    if document_context and document_context.get("extraction"):
        extraction = document_context["extraction"]
        try:
            from hibiscus.knowledge.formulas.eazr_score import calculate_eazr_score
            category = extraction.get("policy_type", "health").lower().replace(" ", "_")
            score_result = calculate_eazr_score(extraction, category)
            eazr_score = score_result.total_score
        except Exception:
            pass

    # ── Step 4: Run guardrails ─────────────────────────────────────
    try:
        from hibiscus.orchestrator.nodes.guardrail_check import run as guardrail_run
        state["response"] = response_text
        state["confidence"] = confidence
        state["sources"] = sources
        state["intent"] = "analyze"
        guardrail_result = await guardrail_run(state)
        response_text = guardrail_result.get("response", response_text)
    except Exception as e:
        logger.warning("analyze_guardrail_failed", error=str(e), request_id=request_id)

    latency_ms = int((time.time() - start) * 1000)

    logger.info(
        "analyze_complete",
        request_id=request_id,
        latency_ms=latency_ms,
        confidence=confidence,
        eazr_score=eazr_score,
    )

    # Build Source objects
    source_objs = []
    for s in sources:
        if isinstance(s, dict):
            source_objs.append(Source(
                type=s.get("type", "llm_reasoning"),
                reference=s.get("reference", ""),
                confidence=s.get("confidence", confidence),
                page=s.get("page"),
            ))

    return AnalysisResponse(
        document_id=request.document_id,
        session_id=request.session_id,
        request_id=request_id,
        response=response_text,
        structured_data=structured_data,
        eazr_score=eazr_score,
        confidence=confidence,
        sources=source_objs,
        latency_ms=latency_ms,
        agents_invoked=agents_invoked,
    )
