"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Orchestrator state — TypedDict defining the shared state flowing through LangGraph nodes.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import operator
from enum import Enum
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class Complexity(str, Enum):
    L1 = "L1"  # Simple FAQ — direct LLM fast path
    L2 = "L2"  # Single-agent task
    L3 = "L3"  # Multi-agent, tools required
    L4 = "L4"  # Deep research + complex math


class EmotionalState(str, Enum):
    NEUTRAL = "neutral"
    CURIOUS = "curious"
    CONCERNED = "concerned"
    DISTRESSED = "distressed"
    URGENT = "urgent"
    FRUSTRATED = "frustrated"


class HibiscusState(TypedDict, total=False):
    """
    Shared state across all nodes in a single request.
    total=False means all fields are optional (populated as pipeline runs).
    """

    # ── INPUT ────────────────────────────────────────────────────────────
    user_id: str
    session_id: str
    request_id: str
    conversation_id: str      # Unique per conversation (multiple turns)
    message: str              # Raw user message
    uploaded_files: List[Dict[str, Any]]  # [{filename, s3_path, mime_type, doc_id}]

    # ── ASSEMBLED CONTEXT (from memory layers) ────────────────────────────
    user_profile: Optional[Dict[str, Any]]
    policy_portfolio: List[Dict[str, Any]]
    session_history: List[Dict[str, Any]]      # Last N turns (session memory)
    document_context: Optional[Dict[str, Any]] # Extracted doc data from doc memory
    relevant_memories: List[Dict[str, Any]]    # Semantic search results (insights)
    relevant_conversations: List[Dict[str, Any]]  # Past relevant conversations
    renewal_alerts: str                           # Formatted renewal alert string (empty = none)
    outcome_followups: str                         # Pending outcome follow-ups (empty = none)

    # ── CLASSIFICATION ────────────────────────────────────────────────────
    language: str               # en|hi|hinglish|ta|te|mr (detected from user message)
    category: str           # health|life|motor|travel|pa|cross|general
    intent: str             # analyze|recommend|claim|calculate|surrender|...
    complexity: str         # L1|L2|L3|L4 (Complexity enum value)
    emotional_state: str    # neutral|curious|concerned|distressed|urgent|frustrated
    has_document: bool      # User has an uploaded/referenced document
    document_type: str      # health|life_term|life_endowment|life_ulip|motor|...
    agents_needed: List[str]  # From intent classifier
    requires_calculation: bool

    # ── EXECUTION ────────────────────────────────────────────────────────
    execution_plan: List[Dict[str, Any]]  # [{agent, task, priority, parallel_group}]
    # agent_outputs accumulates across parallel agent calls (using add operator)
    agent_outputs: Annotated[List[Dict[str, Any]], operator.add]

    # ── MODEL SELECTION ───────────────────────────────────────────────────
    primary_model: str      # Which LLM tier for this request

    # ── OUTPUT ────────────────────────────────────────────────────────────
    response: str
    response_type: str      # text|analysis|comparison|calculation|workflow
    confidence: float       # 0.0 - 1.0 (aggregated across all agents)
    sources: List[Dict[str, Any]]  # [{type, reference, confidence, page}]
    follow_up_suggestions: List[str]
    products_relevant: List[str]  # IPF/SVF if applicable

    # ── METADATA ─────────────────────────────────────────────────────────
    total_tokens_in: int
    total_tokens_out: int
    total_cost_usd: float
    total_latency_ms: int
    agents_invoked: List[str]
    guardrail_results: Dict[str, bool]  # {hallucination: True, compliance: True}
    fraud_alerts: List[Dict[str, Any]]  # From fraud detector [{alert_type, severity, evidence}]
    errors: List[str]


def initial_state(
    user_id: str,
    session_id: str,
    request_id: str,
    conversation_id: str,
    message: str,
    uploaded_files: Optional[List[Dict[str, Any]]] = None,
) -> HibiscusState:
    """Create the initial state for a new request."""
    return HibiscusState(
        user_id=user_id,
        session_id=session_id,
        request_id=request_id,
        conversation_id=conversation_id,
        message=message,
        uploaded_files=uploaded_files or [],
        # Defaults
        user_profile=None,
        policy_portfolio=[],
        session_history=[],
        document_context=None,
        relevant_memories=[],
        relevant_conversations=[],
        renewal_alerts="",
        outcome_followups="",
        language="en",
        category="general",
        intent="general_chat",
        complexity=Complexity.L1.value,
        emotional_state=EmotionalState.NEUTRAL.value,
        has_document=False,
        document_type="none",
        agents_needed=[],
        requires_calculation=False,
        execution_plan=[],
        agent_outputs=[],
        primary_model="deepseek_v3",
        response="",
        response_type="text",
        confidence=0.0,
        sources=[],
        follow_up_suggestions=[],
        products_relevant=[],
        total_tokens_in=0,
        total_tokens_out=0,
        total_cost_usd=0.0,
        total_latency_ms=0,
        agents_invoked=[],
        guardrail_results={},
        fraud_alerts=[],
        errors=[],
    )
