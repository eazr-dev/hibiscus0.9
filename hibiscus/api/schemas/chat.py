"""Chat request/response schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from hibiscus.api.schemas.common import Source, UploadedFile


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    uploaded_files: Optional[List[UploadedFile]] = None
    stream: bool = False  # Whether to stream the response


class ChatResponse(BaseModel):
    response: str
    session_id: str
    request_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[Source] = []
    follow_up_suggestions: List[str] = []
    eazr_products_relevant: List[str] = []
    agents_invoked: List[str] = []
    guardrail_results: Dict[str, bool] = {}
    latency_ms: int = 0
    cost_inr: float = 0.0
    response_type: str = "text"

    # Optional structured data (for analysis responses)
    structured_data: Optional[Dict[str, Any]] = None


class StreamChunk(BaseModel):
    """Single chunk in a streaming response."""
    type: str  # "token" | "metadata" | "done" | "error"
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None
