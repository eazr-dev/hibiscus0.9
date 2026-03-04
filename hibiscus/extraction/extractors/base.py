"""
Base Extractor — shared LLM extraction logic for all policy types.
Category-specific extractors inherit and customize.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from hibiscus.extraction.processor import ProcessedDocument
from hibiscus.extraction.classifier import ClassificationResult
from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# Prompt directory
_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")


class BaseExtractor:
    """Base class for category-specific LLM extraction."""

    category: str = ""  # Override in subclass
    prompt_file: str = ""  # e.g., "health.txt"
    max_tokens: int = 4000
    temperature: float = 0.0
    timeout: int = 45

    def __init__(self):
        self._system_prompt: Optional[str] = None

    @property
    def system_prompt(self) -> str:
        """Load system prompt from .txt file (cached)."""
        if self._system_prompt is None:
            path = os.path.join(_PROMPTS_DIR, self.prompt_file)
            with open(path, "r") as f:
                self._system_prompt = f.read()
        return self._system_prompt

    async def extract(
        self,
        document: ProcessedDocument,
        classification: ClassificationResult,
    ) -> dict[str, Any]:
        """
        Run LLM extraction on a processed document.

        Returns:
            Dict with all fields in ConfidenceField format:
            {field_name: {value, source_page, confidence}, ...}
        """
        logger.info(
            "extraction_start",
            category=self.category,
            total_pages=document.total_pages,
            total_chars=document.char_count,
        )

        # Build user message with full document text
        user_message = (
            f"POLICY TYPE: {classification.category} ({classification.sub_type})\n"
            f"CONFIDENCE: {classification.confidence}\n\n"
            f"DOCUMENT TEXT:\n{document.full_text}"
        )

        # Call DeepSeek V3.2 with JSON mode
        try:
            response = await call_llm(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message},
                ],
                tier="deepseek_v3",
                agent=f"extractor_{self.category}",
                extra_kwargs={
                    "max_tokens": self.max_tokens,
                    "timeout": self.timeout,
                    "temperature": self.temperature,
                },
            )

            content = response.get("content", "")
            extraction = self._parse_response(content)

            # Post-process: ensure all fields have CF structure
            extraction = self._normalize_fields(extraction)

            field_count = sum(
                1 for v in extraction.values()
                if isinstance(v, dict) and v.get("value") is not None
            )
            logger.info(
                "extraction_complete",
                category=self.category,
                fields_extracted=field_count,
                total_fields=len(extraction),
            )

            return extraction

        except Exception as e:
            logger.error("extraction_failed", category=self.category, error=str(e))
            return {}

    def _parse_response(self, content: str) -> dict:
        """
        3-tier JSON recovery (from botproject's response_parser):
        1. Strip markdown → parse JSON
        2. Syntax repair (trailing commas, unmatched brackets)
        3. Regex field extraction fallback
        """
        # Tier 1: Strip markdown and parse
        cleaned = re.sub(r"^```(?:json|JSON)?\s*\n?", "", content.strip())
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)

        # Try to find JSON object
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Tier 2: Syntax repair
        text = match.group() if match else cleaned
        # Remove trailing commas
        text = re.sub(r",\s*([}\]])", r"\1", text)
        # Fix unmatched brackets
        open_braces = text.count("{") - text.count("}")
        open_brackets = text.count("[") - text.count("]")
        if open_braces > 0:
            text += "}" * open_braces
        if open_brackets > 0:
            text += "]" * open_brackets

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Tier 3: Return empty on complete failure
        logger.warning("json_parse_failed", category=self.category)
        return {}

    def _normalize_fields(self, extraction: dict) -> dict:
        """Ensure every field has {value, source_page, confidence} structure."""
        normalized = {}
        for key, val in extraction.items():
            if isinstance(val, dict) and "value" in val:
                # Already in CF format
                normalized[key] = {
                    "value": val.get("value"),
                    "source_page": val.get("source_page"),
                    "confidence": float(val.get("confidence", 0.0)),
                }
            else:
                # Bare value — wrap in CF (low confidence, no page ref)
                normalized[key] = {
                    "value": val,
                    "source_page": None,
                    "confidence": 0.5,
                }
        return normalized
