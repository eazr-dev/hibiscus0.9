"""
Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Shared schema models — Source, UploadedFile, ErrorResponse used across all API endpoints.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from hibiscus.config import ENGINE_NAME, ENGINE_VERSION, ENGINE_VENDOR, ENGINE_LABEL_INLINE


# ── File upload security constants ──────────────────────────────────────────
_ALLOWED_EXTENSIONS = {".pdf"}
_ALLOWED_MIME_TYPES = {"application/pdf"}
_MAX_FILENAME_LENGTH = 255
# Characters allowed in sanitized filenames: alphanumeric, hyphens, underscores, dots
_SAFE_FILENAME_RE = re.compile(r"[^\w.\-]")


def _sanitize_filename(name: str) -> str:
    """Sanitize a filename to prevent path traversal and injection attacks.

    - Strips directory components (path traversal: ../../etc/passwd)
    - Removes null bytes
    - Replaces unsafe characters with underscores
    - Truncates to max length
    """
    if not name:
        return name
    # Remove null bytes
    name = name.replace("\x00", "")
    # Take only the basename — strip any directory path
    name = os.path.basename(name)
    # Replace any remaining path separators (defense in depth)
    name = name.replace("/", "_").replace("\\", "_")
    # Replace unsafe characters
    name = _SAFE_FILENAME_RE.sub("_", name)
    # Truncate
    if len(name) > _MAX_FILENAME_LENGTH:
        base, ext = os.path.splitext(name)
        name = base[:_MAX_FILENAME_LENGTH - len(ext)] + ext
    return name


class Source(BaseModel):
    """A citation or data source backing a claim in the response."""
    type: str = Field(description="Source type: document_extraction | knowledge_graph | rag_retrieval | web_search | formula | regulation | llm_reasoning")
    reference: str = Field(default="", description="Human-readable source reference")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this source (0-1)")
    page: Optional[str] = Field(None, description="Page number in document (if applicable)")


class UploadedFile(BaseModel):
    """Reference to an uploaded policy document for analysis.

    Security:
    - Filenames are sanitized to prevent path traversal attacks
    - Only PDF files are accepted (extension + MIME type allowlist)
    - Filename length is capped at 255 characters
    """
    filename: Optional[str] = Field(None, description="Original filename of the uploaded PDF")
    doc_id: Optional[str] = Field(None, description="Document ID (auto-generated after upload)")
    analysis_id: Optional[str] = Field(None, description="Analysis ID to retrieve a previous analysis")
    mime_type: str = Field(default="application/pdf", description="MIME type of the uploaded file")
    s3_path: Optional[str] = Field(None, description="S3 storage path (internal)")

    @field_validator("filename", mode="before")
    @classmethod
    def validate_and_sanitize_filename(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Sanitize first
        sanitized = _sanitize_filename(v)
        if not sanitized:
            raise ValueError("Filename is empty after sanitization")
        # Enforce .pdf extension
        _, ext = os.path.splitext(sanitized)
        if ext.lower() not in _ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Only PDF files are accepted. Got extension: '{ext}'. "
                f"Allowed: {', '.join(_ALLOWED_EXTENSIONS)}"
            )
        return sanitized

    @field_validator("mime_type", mode="before")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        if v not in _ALLOWED_MIME_TYPES:
            raise ValueError(
                f"Only PDF files are accepted. Got MIME type: '{v}'. "
                f"Allowed: {', '.join(_ALLOWED_MIME_TYPES)}"
            )
        return v

    @field_validator("s3_path", mode="before")
    @classmethod
    def validate_s3_path(cls, v: Optional[str]) -> Optional[str]:
        """Prevent path traversal in S3 paths."""
        if v is None:
            return v
        # Block path traversal sequences
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid S3 path: must not contain '..' or start with '/'")
        return v


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
