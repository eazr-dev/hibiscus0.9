"""
5-Check Validation Engine.

Absorbs botproject's four_check_validator.py and adds KG cross-reference.

Checks:
1. Evidence Grounding — critical/important fields must have source_page
2. Cross-Field Logic — values make logical sense (dates, premium/SI ratio, PAN)
3. Format Validation — dates, currency, percentages in correct format
4. Range Validation — values within reasonable ranges per category
5. Confidence Scoring — weighted average using criticality map
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from hibiscus.extraction.schemas.common import (
    CRITICALITY_BY_TYPE,
    CRITICALITY_CRITICAL,
    CRITICALITY_IMPORTANT,
    CRITICALITY_STANDARD,
)
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationIssue:
    field: str
    check: str  # "evidence" | "logic" | "format" | "range" | "confidence"
    severity: str  # "error" | "warning" | "info"
    message: str


@dataclass
class ValidationResult:
    valid: bool = True
    score: int = 0  # 0-100
    confidence: str = "MEDIUM"  # HIGH | MEDIUM | LOW
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    field_scores: dict[str, dict] = field(default_factory=dict)
    weighted_confidence: float = 0.0
    fields_checked: int = 0
    fields_with_evidence: int = 0


# ── Range thresholds by category ──────────────────────────────────────

_RANGES = {
    "health": {
        "sumInsured": (100_000, 5_00_00_000),  # ₹1L - ₹5Cr
        "basePremium": (3_000, 5_00_000),  # ₹3K - ₹5L
        "totalPremium": (3_000, 6_00_000),
        "generalCopay": (0, 100),
        "ncbPercentage": (0, 100),
    },
    "life": {
        "sumAssured": (50_000, 50_00_00_000),  # ₹50K - ₹50Cr
        "premiumAmount": (1_000, 50_00_000),
        "totalPremium": (1_000, 60_00_000),
        "policyTerm": (1, 100),
        "premiumPayingTerm": (1, 100),
    },
    "motor": {
        "idv": (10_000, 1_00_00_000),  # ₹10K - ₹1Cr
        "totalPremium": (500, 10_00_000),
        "ncbPercentage": (0, 65),
        "paOwnerCover": (0, 1_00_00_000),
    },
    "travel": {
        "medicalExpenses": (10_000, 5_00_00_000),
        "totalPremium": (500, 5_00_000),
        "tripDuration": (1, 365),
    },
    "pa": {
        "paSumInsured": (10_000, 10_00_00_000),
        "totalPremium": (100, 5_00_000),
        "accidentalDeathBenefitPercentage": (0, 200),
    },
}

# Known insurer email domains (for entity confusion detection)
_INSURER_DOMAINS = {
    "icicilombard", "hdfcergo", "bajajallianz", "tataaia", "tataaiagic",
    "starhealth", "careinsurance", "nivabupa", "acko", "digit", "godigit",
    "sbilife", "sbisg", "newindia", "orientalinsurance", "uiic",
}

# PAN format: 5 letters + 4 digits + 1 letter
_PAN_RE = re.compile(r"^[A-Z]{5}\d{4}[A-Z]$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ValidationEngine:
    """5-check validation for extraction data."""

    MIN_WEIGHTED_CONFIDENCE = 0.6

    async def validate(
        self,
        extraction: dict[str, Any],
        category: str,
    ) -> ValidationResult:
        """Run all 5 validation checks on extraction data."""

        result = ValidationResult()
        criticality_map = CRITICALITY_BY_TYPE.get(category, {})

        # Check 1: Evidence grounding
        self._check_evidence(extraction, criticality_map, result)

        # Check 2: Cross-field logic
        self._check_logic(extraction, category, result)

        # Check 3: Format validation
        self._check_format(extraction, category, result)

        # Check 4: Range validation
        self._check_ranges(extraction, category, result)

        # Check 5: Confidence scoring
        self._check_confidence(extraction, criticality_map, result)

        # Compute overall score
        error_count = len(result.errors)
        warning_count = len(result.warnings)
        result.score = max(0, 100 - (error_count * 10) - (warning_count * 3))

        if result.weighted_confidence >= 0.8 and error_count == 0:
            result.confidence = "HIGH"
        elif result.weighted_confidence >= self.MIN_WEIGHTED_CONFIDENCE and error_count <= 2:
            result.confidence = "MEDIUM"
        else:
            result.confidence = "LOW"

        result.valid = error_count == 0 and result.weighted_confidence >= self.MIN_WEIGHTED_CONFIDENCE

        logger.info(
            "validation_complete",
            category=category,
            score=result.score,
            confidence=result.confidence,
            errors=error_count,
            warnings=warning_count,
            weighted_confidence=round(result.weighted_confidence, 3),
        )

        return result

    # ── Check 1: Evidence Grounding ──────────────────────────────────

    def _check_evidence(
        self,
        extraction: dict,
        criticality_map: dict,
        result: ValidationResult,
    ):
        """Critical/important fields must have source_page citation."""
        for field_name, val in extraction.items():
            if not isinstance(val, dict) or val.get("value") is None:
                continue

            result.fields_checked += 1
            crit = criticality_map.get(field_name, CRITICALITY_STANDARD)

            has_page = val.get("source_page") is not None
            if has_page:
                result.fields_with_evidence += 1

            if not has_page and crit >= CRITICALITY_IMPORTANT:
                severity = "error" if crit == CRITICALITY_CRITICAL else "warning"
                issue = ValidationIssue(
                    field=field_name,
                    check="evidence",
                    severity=severity,
                    message=f"{'Critical' if crit == CRITICALITY_CRITICAL else 'Important'} field missing source_page",
                )
                if severity == "error":
                    result.errors.append(issue)
                else:
                    result.warnings.append(issue)

    # ── Check 2: Cross-Field Logic ───────────────────────────────────

    def _check_logic(self, extraction: dict, category: str, result: ValidationResult):
        """Cross-field consistency checks."""

        def _val(field_name: str) -> Any:
            f = extraction.get(field_name, {})
            return f.get("value") if isinstance(f, dict) else None

        def _num(field_name: str) -> float:
            v = _val(field_name)
            if v is None:
                return 0.0
            try:
                return float(str(v).replace(",", "").replace("₹", ""))
            except (ValueError, TypeError):
                return 0.0

        # Coverage > 0
        coverage_field = {
            "health": "sumInsured", "life": "sumAssured",
            "motor": "idv", "travel": "medicalExpenses", "pa": "paSumInsured",
        }.get(category, "")
        coverage = _num(coverage_field)
        if coverage_field and _val(coverage_field) is not None and coverage <= 0:
            result.errors.append(ValidationIssue(
                field=coverage_field, check="logic", severity="error",
                message=f"Coverage amount must be > 0, got {coverage}",
            ))

        # Premium > 0 and < coverage
        premium = _num("totalPremium")
        if _val("totalPremium") is not None:
            if premium <= 0:
                result.warnings.append(ValidationIssue(
                    field="totalPremium", check="logic", severity="warning",
                    message=f"Premium should be > 0, got {premium}",
                ))
            elif coverage > 0 and premium >= coverage:
                result.warnings.append(ValidationIssue(
                    field="totalPremium", check="logic", severity="warning",
                    message=f"Premium ({premium}) >= coverage ({coverage})",
                ))

        # Date consistency: start < end
        start = _val("policyPeriodStart") or _val("tripStartDate")
        end = _val("policyPeriodEnd") or _val("tripEndDate")
        if start and end and str(start) > str(end):
            result.errors.append(ValidationIssue(
                field="policyPeriodEnd", check="logic", severity="error",
                message=f"End date ({end}) before start date ({start})",
            ))

        # Motor-specific: tpPremium vs paOwnerDriverPremium
        if category == "motor":
            product_type = str(_val("productType") or "").lower()
            tp = _num("tpPremium")
            if "standalone" in product_type and tp > 0:
                result.warnings.append(ValidationIssue(
                    field="tpPremium", check="logic", severity="warning",
                    message=f"Standalone OD should have tpPremium=0, got {tp}",
                ))

            # PAN check: 4th char must be 'P' for personal
            pan = str(_val("ownerPan") or "")
            if pan and _PAN_RE.match(pan) and pan[3] != "P":
                result.errors.append(ValidationIssue(
                    field="ownerPan", check="logic", severity="error",
                    message=f"PAN 4th char is '{pan[3]}' (not 'P') — likely insurer/company PAN",
                ))

        # Motor premium formula: grossPremium + GST ≈ totalPremium (3% tolerance)
        if category == "motor":
            gross = _num("grossPremium")
            gst = _num("gst")
            total = _num("totalPremium")
            if gross > 0 and gst >= 0 and total > 0:
                expected = gross + gst
                tolerance = max(total * 0.03, 500)
                if abs(expected - total) > tolerance:
                    result.warnings.append(ValidationIssue(
                        field="totalPremium", check="logic", severity="warning",
                        message=f"grossPremium({gross}) + GST({gst}) = {expected}, but totalPremium = {total}",
                    ))

        # Email entity confusion: check if policyholder email is an insurer domain
        if category == "motor":
            email = str(_val("ownerEmail") or "")
            if email:
                domain = email.split("@")[-1].split(".")[0].lower() if "@" in email else ""
                if domain in _INSURER_DOMAINS:
                    result.warnings.append(ValidationIssue(
                        field="ownerEmail", check="logic", severity="warning",
                        message=f"ownerEmail domain '{domain}' looks like insurer, not policyholder",
                    ))

        # Life-specific: maturityDate should match policyPeriodEnd
        if category == "life":
            maturity = _val("maturityDate")
            policy_end = _val("policyPeriodEnd")
            if maturity and policy_end and str(maturity) != str(policy_end):
                result.warnings.append(ValidationIssue(
                    field="maturityDate", check="logic", severity="warning",
                    message=f"maturityDate ({maturity}) differs from policyPeriodEnd ({policy_end}) — check rider vs base",
                ))

    # ── Check 3: Format Validation ───────────────────────────────────

    def _check_format(self, extraction: dict, category: str, result: ValidationResult):
        """Validate date, currency, percentage formats."""

        date_fields = {
            "policyPeriodStart", "policyPeriodEnd", "policyIssueDate",
            "maturityDate", "registrationDate", "tripStartDate", "tripEndDate",
            "policyholderDob", "lifeAssuredDob", "premiumDueDate",
            "firstEnrollmentDate", "insuredSinceDate",
        }

        pct_fields = {
            "generalCopay", "ncbPercentage", "maxNcbPercentage",
            "claimSettlementRatio", "accidentalDeathBenefitPercentage",
            "permanentTotalDisabilityPercentage",
        }

        for field_name, val in extraction.items():
            if not isinstance(val, dict):
                continue
            v = val.get("value")
            if v is None:
                continue

            # Date format check
            if field_name in date_fields:
                if isinstance(v, str) and v and not _DATE_RE.match(v):
                    result.warnings.append(ValidationIssue(
                        field=field_name, check="format", severity="warning",
                        message=f"Date not in YYYY-MM-DD format: {v}",
                    ))

            # Percentage range check
            if field_name in pct_fields:
                try:
                    pct = float(str(v).replace("%", ""))
                    if pct < 0 or pct > 100:
                        result.warnings.append(ValidationIssue(
                            field=field_name, check="format", severity="warning",
                            message=f"Percentage out of 0-100 range: {pct}",
                        ))
                except (ValueError, TypeError):
                    pass

            # UIN format check
            if field_name == "uin" and isinstance(v, str) and len(v) < 5:
                result.warnings.append(ValidationIssue(
                    field="uin", check="format", severity="warning",
                    message=f"UIN too short ({len(v)} chars), expected IRDAI format",
                ))

    # ── Check 4: Range Validation ────────────────────────────────────

    def _check_ranges(self, extraction: dict, category: str, result: ValidationResult):
        """Check values within reasonable ranges."""
        ranges = _RANGES.get(category, {})

        for field_name, (lo, hi) in ranges.items():
            val = extraction.get(field_name, {})
            if not isinstance(val, dict):
                continue
            v = val.get("value")
            if v is None:
                continue

            try:
                num = float(str(v).replace(",", "").replace("₹", ""))
            except (ValueError, TypeError):
                continue

            if num < lo:
                result.warnings.append(ValidationIssue(
                    field=field_name, check="range", severity="warning",
                    message=f"Value {num} below minimum {lo}",
                ))
            elif num > hi:
                result.warnings.append(ValidationIssue(
                    field=field_name, check="range", severity="warning",
                    message=f"Value {num} above maximum {hi}",
                ))

    # ── Check 5: Confidence Scoring ──────────────────────────────────

    def _check_confidence(
        self,
        extraction: dict,
        criticality_map: dict,
        result: ValidationResult,
    ):
        """Compute weighted confidence score."""
        total_weight = 0.0
        weighted_sum = 0.0
        low_conf_critical = []

        for field_name, val in extraction.items():
            if not isinstance(val, dict) or val.get("value") is None:
                continue

            conf = float(val.get("confidence", 0.0))
            weight = criticality_map.get(field_name, CRITICALITY_STANDARD)

            total_weight += weight
            weighted_sum += conf * weight

            result.field_scores[field_name] = {
                "confidence": conf,
                "criticality": weight,
                "issues": [],
            }

            if conf < 0.5 and weight >= CRITICALITY_CRITICAL:
                low_conf_critical.append(field_name)

        result.weighted_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0

        if low_conf_critical:
            for f in low_conf_critical:
                result.warnings.append(ValidationIssue(
                    field=f, check="confidence", severity="warning",
                    message=f"Critical field has low confidence ({result.field_scores[f]['confidence']})",
                ))


# Singleton
validation_engine = ValidationEngine()
