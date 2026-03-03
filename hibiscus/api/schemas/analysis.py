"""Analysis endpoint request/response schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from hibiscus.api.schemas.common import Source


class AnalysisRequest(BaseModel):
    document_id: Optional[str] = None       # MongoDB document ID (optional if analysis_id set)
    analysis_id: Optional[str] = None       # botproject analysis ID
    session_id: str
    user_id: str
    include_kg_comparison: bool = True      # Include KG benchmark comparison in analysis


class AnalysisResponse(BaseModel):
    document_id: Optional[str] = None
    session_id: str
    request_id: str
    response: str
    structured_data: Optional[Dict[str, Any]] = None
    eazr_score: Optional[float] = None
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[Source] = Field(default_factory=list)
    latency_ms: int
    cost_inr: float = 0.0
    agents_invoked: List[str] = Field(default_factory=list)
    error: Optional[str] = None
