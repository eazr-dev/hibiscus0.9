"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Chat request/response schemas — defines the contract between frontend and AI engine.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from hibiscus.config import ENGINE_NAME, ENGINE_VERSION, ENGINE_VENDOR
from hibiscus.api.schemas.common import Source, UploadedFile


class ChatRequest(BaseModel):
    """Send a message to the Hibiscus AI engine."""
    message: str = Field(
        ..., min_length=1, max_length=10000,
        description="The user's message or question about insurance",
    )
    session_id: str = Field(
        ..., min_length=1,
        description="Session identifier — maintains conversation context across turns",
    )
    user_id: str = Field(
        ..., min_length=1,
        description="Unique user identifier",
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Optional conversation ID for multi-turn threading. Auto-generated if omitted.",
    )
    uploaded_files: Optional[List[UploadedFile]] = Field(
        None,
        description="List of uploaded policy documents for analysis",
    )
    stream: bool = Field(
        False,
        description="If true, response is streamed as Server-Sent Events (SSE)",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "What is health insurance and why do I need it?",
                    "session_id": "sess_abc123",
                    "user_id": "user_456",
                    "stream": False,
                },
                {
                    "message": "Compare term life insurance plans for a 30 year old earning 15 lakh",
                    "session_id": "sess_abc123",
                    "user_id": "user_456",
                    "stream": True,
                },
            ]
        }
    }


class ChatResponse(BaseModel):
    """Structured response from the Hibiscus AI engine."""
    engine: str = Field(default=ENGINE_NAME.lower(), description="Engine identifier")
    version: str = Field(default=ENGINE_VERSION, description="Engine version")
    vendor: str = Field(default=ENGINE_VENDOR, description="Engine vendor")
    response: str = Field(description="The AI-generated response text (markdown)")
    session_id: str = Field(description="Echo of the session ID")
    request_id: str = Field(description="Unique request ID for tracing")
    confidence: float = Field(ge=0.0, le=1.0, description="Aggregated confidence score (0-1)")
    sources: List[Source] = Field(default=[], description="Citations and data sources used")
    follow_up_suggestions: List[str] = Field(default=[], description="Suggested follow-up questions")
    products_relevant: List[str] = Field(default=[], description="Relevant EAZR products (IPF, SVF)")
    agents_invoked: List[str] = Field(default=[], description="Which specialist agents were used")
    guardrail_results: Dict[str, bool] = Field(default={}, description="Guardrail pass/fail results")
    latency_ms: int = Field(default=0, description="Total processing time in milliseconds")
    cost_inr: float = Field(default=0.0, description="LLM cost for this request in INR")
    response_type: str = Field(default="text", description="Response type: text|analysis|comparison|calculation")
    structured_data: Optional[Dict[str, Any]] = Field(
        None, description="Structured extraction/scoring data (for policy analysis responses)",
    )


class StreamChunk(BaseModel):
    """Single chunk in a Server-Sent Events streaming response."""
    type: str = Field(description="Chunk type: token | metadata | done | error")
    content: str = Field(default="", description="Token text (for type=token) or error message (for type=error)")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Metadata payload (for type=metadata and type=done)",
    )
