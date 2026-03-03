"""Shared schema models used across Hibiscus API."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Source(BaseModel):
    type: str  # document_extraction | knowledge_graph | rag_retrieval | web_search | llm_reasoning
    reference: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    page: Optional[str] = None  # Page number in document


class UploadedFile(BaseModel):
    filename: str
    doc_id: Optional[str] = None
    analysis_id: Optional[str] = None
    mime_type: str = "application/pdf"
    s3_path: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
