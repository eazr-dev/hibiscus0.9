"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Analysis endpoint — PDF upload, extraction pipeline trigger, structured scoring response.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import time
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile

from hibiscus.api.schemas.analysis import AnalysisRequest, AnalysisResponse
from hibiscus.api.schemas.common import Source
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(
    http_request: Request,
    file: Optional[UploadFile] = File(None),
    user_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    document_id: Optional[str] = Form(None),
    analysis_id: Optional[str] = Form(None),
    request: Optional[AnalysisRequest] = None,
) -> AnalysisResponse:
    """
    Trigger a policy analysis.

    Accepts either:
      - Multipart form with PDF file upload + form fields
      - JSON body (AnalysisRequest) for stored document analysis

    Flow:
      1. Load/extract document (from upload or MongoDB)
      2. Build HibiscusState with document_context pre-populated
      3. Run policy_analyzer agent directly
      4. Run guardrail_check on result
      5. Return AnalysisResponse
    """
    start = time.time()
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))

    # Resolve params from either multipart form or JSON body
    _user_id = user_id or (request.user_id if request else "anonymous")
    _session_id = session_id or (request.session_id if request else str(uuid.uuid4()))
    _document_id = document_id or (request.document_id if request else None)
    _analysis_id = analysis_id or (request.analysis_id if request else None)

    logger.info(
        "analyze_request",
        request_id=request_id,
        user_id=_user_id,
        session_id=_session_id,
        document_id=_document_id,
        analysis_id=_analysis_id,
        has_file=file is not None,
    )

    # ── Step 1: Load document from upload or memory ─────────────────
    document_context = None

    # If a file was uploaded, process it through the extraction pipeline
    if file and file.filename:
        try:
            from hibiscus.extraction.processor import extract_text
            from hibiscus.extraction.classifier import classify_document

            file_bytes = await file.read()
            extracted = extract_text(file_bytes, file.filename)
            if extracted:
                doc_type = classify_document(extracted)
                document_context = {
                    "doc_id": f"upload_{_user_id}_{int(time.time())}",
                    "filename": file.filename,
                    "extraction": extracted,
                    "policy_type": doc_type,
                }
        except Exception as e:
            logger.warning("analyze_upload_extract_failed", error=str(e), request_id=request_id)

    if not document_context:
        try:
            from hibiscus.memory.layers.document import get_latest_document
            doc = await get_latest_document(_user_id)
            if doc:
                document_context = doc
        except Exception as e:
            logger.warning("analyze_doc_load_failed", error=str(e), request_id=request_id)

    # ── Step 2: Build state ────────────────────────────────────────
    state = {
        "request_id": request_id,
        "session_id": _session_id,
        "user_id": _user_id,
        "conversation_id": _session_id,
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
            session_id=_session_id,
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
        document_id=_document_id,
        session_id=_session_id,
        request_id=request_id,
        response=response_text,
        structured_data=structured_data,
        eazr_score=eazr_score,
        confidence=confidence,
        sources=source_objs,
        latency_ms=latency_ms,
        agents_invoked=agents_invoked,
    )
