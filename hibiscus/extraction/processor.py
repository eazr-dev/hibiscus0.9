"""
Document Processor — PDF intake, text extraction, page markers.

Pipeline:
1. PDF → text via pdfplumber (digital PDFs)
2. Fallback: PyPDF2 for encrypted/damaged PDFs
3. Fallback: OCR via pytesseract for scanned documents
4. Page boundary markers preserved: [PAGE 1], [PAGE 2], etc.
5. Text cleaning: remove headers/footers, fix encoding
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PageContent:
    page_num: int
    text: str


@dataclass
class ProcessedDocument:
    pages: list[PageContent] = field(default_factory=list)
    total_pages: int = 0
    extraction_method: str = "digital"  # "digital" | "ocr" | "fallback"
    raw_text: str = ""
    errors: list[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Full text with page markers."""
        if self.raw_text:
            return self.raw_text
        parts = []
        for page in self.pages:
            parts.append(f"[PAGE {page.page_num}]")
            parts.append(page.text)
        self.raw_text = "\n\n".join(parts)
        return self.raw_text

    @property
    def first_pages_text(self) -> str:
        """First 3 pages for classification."""
        parts = []
        for page in self.pages[:3]:
            parts.append(f"[PAGE {page.page_num}]")
            parts.append(page.text)
        return "\n\n".join(parts)

    @property
    def char_count(self) -> int:
        return sum(len(p.text) for p in self.pages)


class DocumentProcessor:
    """Processes PDF documents into structured text with page markers."""

    # Minimum chars per page to consider extraction successful
    MIN_CHARS_PER_PAGE = 50
    # Minimum total chars for the document
    MIN_TOTAL_CHARS = 200

    async def process(
        self,
        pdf_data: bytes,
        filename: Optional[str] = None,
    ) -> ProcessedDocument:
        """
        Process a PDF file into structured text.

        Args:
            pdf_data: Raw PDF bytes
            filename: Original filename (for logging)

        Returns:
            ProcessedDocument with page-marked text
        """
        logger.info(
            "document_processing_start",
            filename=filename,
            size_bytes=len(pdf_data),
        )

        result = ProcessedDocument()

        # Try pdfplumber first (best for digital PDFs)
        result = await self._extract_pdfplumber(pdf_data, result)

        # If pdfplumber yields sparse text, try PyPDF2
        if result.char_count < self.MIN_TOTAL_CHARS:
            logger.info("pdfplumber_sparse_trying_pypdf2", chars=result.char_count)
            result = await self._extract_pypdf2(pdf_data, result)

        # If still sparse, try OCR
        if result.char_count < self.MIN_TOTAL_CHARS:
            logger.info("text_sparse_trying_ocr", chars=result.char_count)
            result = await self._extract_ocr(pdf_data, result)

        # Clean extracted text
        result = self._clean_text(result)

        logger.info(
            "document_processing_complete",
            total_pages=result.total_pages,
            total_chars=result.char_count,
            method=result.extraction_method,
            errors=len(result.errors),
        )

        return result

    async def _extract_pdfplumber(
        self, pdf_data: bytes, result: ProcessedDocument
    ) -> ProcessedDocument:
        """Extract text using pdfplumber (best for digital PDFs)."""
        try:
            import pdfplumber

            pages = []
            with pdfplumber.open(io.BytesIO(pdf_data)) as pdf:
                result.total_pages = len(pdf.pages)
                for i, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    pages.append(PageContent(page_num=i, text=text))

            result.pages = pages
            result.extraction_method = "digital"
            return result

        except Exception as e:
            result.errors.append(f"pdfplumber failed: {e}")
            logger.warning("pdfplumber_failed", error=str(e))
            return result

    async def _extract_pypdf2(
        self, pdf_data: bytes, result: ProcessedDocument
    ) -> ProcessedDocument:
        """Fallback: Extract text using PyPDF2."""
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(io.BytesIO(pdf_data))
            result.total_pages = len(reader.pages)
            pages = []
            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text() or ""
                pages.append(PageContent(page_num=i, text=text))

            if sum(len(p.text) for p in pages) > result.char_count:
                result.pages = pages
                result.extraction_method = "fallback"

            return result

        except Exception as e:
            result.errors.append(f"PyPDF2 failed: {e}")
            logger.warning("pypdf2_failed", error=str(e))
            return result

    async def _extract_ocr(
        self, pdf_data: bytes, result: ProcessedDocument
    ) -> ProcessedDocument:
        """Fallback: OCR using pytesseract + pdf2image."""
        try:
            import pytesseract
            from PIL import Image
            from pdf2image import convert_from_bytes

            images = convert_from_bytes(pdf_data, dpi=300)
            result.total_pages = len(images)
            pages = []
            for i, img in enumerate(images, 1):
                text = pytesseract.image_to_string(img, lang="eng")
                pages.append(PageContent(page_num=i, text=text))

            if sum(len(p.text) for p in pages) > result.char_count:
                result.pages = pages
                result.extraction_method = "ocr"

            return result

        except ImportError:
            result.errors.append("OCR dependencies not available (pytesseract/pdf2image)")
            logger.warning("ocr_deps_missing")
            return result
        except Exception as e:
            result.errors.append(f"OCR failed: {e}")
            logger.warning("ocr_failed", error=str(e))
            return result

    def _clean_text(self, result: ProcessedDocument) -> ProcessedDocument:
        """Clean extracted text: normalize whitespace, fix encoding."""
        cleaned_pages = []
        for page in result.pages:
            text = page.text

            # Fix common encoding issues
            text = text.replace("\x00", "")
            text = text.replace("\ufeff", "")

            # Normalize whitespace (preserve newlines)
            text = re.sub(r"[ \t]+", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text)

            # Remove common headers/footers (page numbers, watermarks)
            text = re.sub(
                r"(?m)^.*Page\s+\d+\s+of\s+\d+.*$", "", text
            )
            text = re.sub(
                r"(?m)^.*Confidential.*$", "", text, flags=re.IGNORECASE
            )

            cleaned_pages.append(PageContent(page_num=page.page_num, text=text.strip()))

        result.pages = cleaned_pages
        result.raw_text = ""  # Reset cached full text
        return result


# Singleton
document_processor = DocumentProcessor()
