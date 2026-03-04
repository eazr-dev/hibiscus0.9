"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Shared schema models — Source, UploadedFile, ErrorResponse used across all API endpoints.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from hibiscus.config import ENGINE_NAME, ENGINE_VERSION, ENGINE_VENDOR, ENGINE_LABEL_INLINE


class Source(BaseModel):
    """A citation or data source backing a claim in the response."""
    type: str = Field(description="Source type: document_extraction | knowledge_graph | rag_retrieval | web_search | formula | regulation | llm_reasoning")
    reference: str = Field(default="", description="Human-readable source reference")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this source (0-1)")
    page: Optional[str] = Field(None, description="Page number in document (if applicable)")


class UploadedFile(BaseModel):
    """Reference to an uploaded policy document for analysis."""
    filename: Optional[str] = Field(None, description="Original filename of the uploaded PDF")
    doc_id: Optional[str] = Field(None, description="Document ID (auto-generated after upload)")
    analysis_id: Optional[str] = Field(None, description="Analysis ID to retrieve a previous analysis")
    mime_type: str = Field(default="application/pdf", description="MIME type of the uploaded file")
    s3_path: Optional[str] = Field(None, description="S3 storage path (internal)")


class EngineMetadata(BaseModel):
    """Engine identity included in API responses."""
    engine: str = Field(default=ENGINE_NAME.lower(), description="Engine identifier")
    version: str = Field(default=ENGINE_VERSION, description="Engine version")
    vendor: str = Field(default=ENGINE_VENDOR, description="Engine vendor")


class ErrorResponse(BaseModel):
    """Standard error response — prefixed with engine label for traceability."""
    error: str = Field(description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    engine: str = Field(default=ENGINE_NAME.lower(), description="Engine identifier")
    version: str = Field(default=ENGINE_VERSION, description="Engine version")
