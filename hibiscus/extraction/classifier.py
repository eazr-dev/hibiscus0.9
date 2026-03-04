"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
Policy classifier — determines insurance type (health/life/motor/travel/PA) from PDF text.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from hibiscus.llm.router import call_llm
from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ClassificationResult:
    category: str  # health | life | motor | travel | pa
    sub_type: str = ""  # e.g., "family_floater", "term", "comprehensive"
    confidence: float = 0.0
    tier_used: int = 0  # 1, 2, or 3
    signals: list[str] = field(default_factory=list)


# ── Tier 1: UIN patterns ──────────────────────────────────────────────

_UIN_PATTERNS = {
    "health": [
        re.compile(r"\d{3}[A-Z]*HLIP", re.IGNORECASE),
        re.compile(r"IRDAN\d+[A-Z]*HL", re.IGNORECASE),
        re.compile(r"SHAHLIP|NBHIHLIP|RHEHLIP", re.IGNORECASE),
    ],
    "life": [
        re.compile(r"\d{3}[LN]\d{3}V\d{2}", re.IGNORECASE),
        re.compile(r"IRDAN\d+[A-Z]*L[A-Z]", re.IGNORECASE),
    ],
    "motor": [
        re.compile(r"IRDAN\d+[A-Z]*(?:RP|CP)(?:MC|MO|MT|CV)", re.IGNORECASE),
    ],
    "travel": [
        re.compile(r"IRDAN\d+[A-Z]*(?:RP|CP)(?:TV|TR)", re.IGNORECASE),
    ],
    "pa": [
        re.compile(r"IRDAN\d+[A-Z]*(?:RP|CP)PA", re.IGNORECASE),
    ],
}

# IRDAI standard products → guaranteed classification
_STANDARD_PRODUCTS = {
    "arogya sanjeevani": ("health", "arogya_sanjeevani"),
    "saral jeevan bima": ("life", "term"),
    "saral suraksha bima": ("pa", "standard"),
    "bharat yatra suraksha": ("travel", "domestic"),
    "bharat griha raksha": ("home", "bharat_griha_raksha"),
}

# Life-only insurers → strong prior for life classification
_LIFE_ONLY_INSURERS = {
    "lic", "hdfc life", "icici prudential life", "sbi life", "max life",
    "kotak mahindra life", "aditya birla sun life", "tata aia", "pnb metlife",
    "canara hsbc", "exide life", "edelweiss tokio", "aegon life", "aviva life",
    "bharti axa life", "indiafirst life", "pramerica life", "shriram life",
}

# Health-only insurers → strong prior for health
_HEALTH_ONLY_INSURERS = {
    "star health", "care health", "niva bupa", "max bupa",
    "aditya birla health", "manipalcigna", "manipal cigna",
}

# ── Tier 2: Weighted keyword scoring ─────────────────────────────────

# Weight: 1.0=definitive, 0.8=very strong, 0.6=strong, 0.4=moderate, -0.5=negative
_CATEGORY_FEATURES: dict[str, list[tuple[str, float]]] = {
    "health": [
        # Definitive (1.0)
        ("room rent", 1.0), ("cumulative bonus", 1.0), ("day care procedure", 1.0),
        ("ayush treatment", 1.0), ("domiciliary hospitalization", 1.0),
        ("restoration benefit", 1.0), ("moratorium period", 1.0),
        ("mediclaim", 1.0), ("sub-limit", 1.0), ("pre-existing disease", 0.8),
        # Very strong (0.8)
        ("co-payment", 0.8), ("copay", 0.8), ("sum insured", 0.8),
        ("cashless hospital", 0.8), ("network hospital", 0.8),
        ("pre hospitalization", 0.8), ("post hospitalization", 0.8),
        ("waiting period", 0.6), ("hospitalization", 0.6),
        # Strong (0.6)
        ("in-patient", 0.6), ("out-patient", 0.6), ("critical illness", 0.6),
        ("health insurance", 0.6), ("medical insurance", 0.6),
        # Negative
        ("trip cancellation", -0.5), ("baggage loss", -0.5), ("flight delay", -0.5),
        ("idv", -0.5), ("chassis number", -0.5), ("registration number", -0.5),
        ("sum assured", -0.5), ("maturity benefit", -0.5),
    ],
    "life": [
        # Definitive
        ("sum assured", 1.0), ("maturity benefit", 1.0), ("death benefit", 1.0),
        ("surrender value", 1.0), ("paid-up value", 1.0), ("reversionary bonus", 1.0),
        ("nominee", 0.8), ("life assured", 0.8), ("policy term", 0.6),
        # Very strong
        ("premium paying term", 0.8), ("bonus rate", 0.8), ("free look period", 0.6),
        ("suicide clause", 0.8), ("revival period", 0.6),
        # Type-specific
        ("term plan", 1.0), ("pure protection", 1.0), ("endowment", 1.0),
        ("ulip", 1.0), ("unit linked", 1.0), ("nav", 0.8), ("fund value", 0.8),
        ("money back", 1.0), ("whole life", 1.0), ("pension", 0.6),
        # Negative
        ("room rent", -0.5), ("copay", -0.5), ("hospitalization", -0.5),
        ("idv", -0.5), ("trip cancellation", -0.5),
    ],
    "motor": [
        # Definitive
        ("idv", 1.0), ("insured declared value", 1.0),
        ("own damage", 1.0), ("third party liability", 1.0),
        ("zero depreciation", 1.0), ("return to invoice", 1.0),
        ("engine protection", 1.0), ("ncb", 0.8),
        # Very strong
        ("registration number", 0.8), ("engine number", 0.8), ("chassis number", 0.8),
        ("vehicle make", 0.8), ("vehicle model", 0.8), ("rto", 0.6),
        ("roadside assistance", 0.6), ("consumables", 0.4),
        ("cpa", 0.6), ("compulsory pa", 0.6),
        # Negative
        ("room rent", -0.5), ("sum assured", -0.5), ("maturity", -0.5),
        ("hospitalization", -0.5), ("trip cancellation", -0.5),
    ],
    "travel": [
        # Definitive
        ("trip cancellation", 1.0), ("baggage loss", 1.0), ("baggage delay", 1.0),
        ("flight delay", 1.0), ("missed connection", 1.0),
        ("repatriation", 1.0), ("trip curtailment", 1.0),
        # Very strong
        ("passport", 0.8), ("destination", 0.8), ("schengen", 0.8),
        ("evacuation", 0.8), ("hijack distress", 0.8),
        # Strong
        ("travel insurance", 0.6), ("trip", 0.6), ("visa", 0.4),
        # Negative
        ("room rent", -0.5), ("cumulative bonus", -0.5),
        ("ncb", -0.5), ("idv", -0.5), ("sum assured", -0.5),
    ],
    "pa": [
        # Definitive
        ("accidental death", 1.0), ("permanent total disability", 1.0),
        ("permanent partial disability", 1.0), ("disability schedule", 1.0),
        ("capital sum insured", 1.0), ("loss of limb", 0.8),
        ("temporary total disability", 0.8), ("weekly benefit", 0.6),
        ("personal accident", 0.8), ("violent external", 0.8),
        # Negative
        ("room rent", -0.5), ("trip cancellation", -0.5),
        ("idv", -0.5), ("maturity benefit", -0.5),
    ],
}

# Sub-type keywords
_SUB_TYPES = {
    "health": {
        "family_floater": ["family floater", "floater", "family plan"],
        "individual": ["individual", "single person"],
        "senior": ["senior citizen", "senior", "elderly"],
        "critical_illness": ["critical illness", "ci plan", "critical care"],
        "top_up": ["super top-up", "top-up", "top up"],
        "arogya_sanjeevani": ["arogya sanjeevani"],
        "group": ["group health", "group mediclaim"],
    },
    "life": {
        "term": ["term plan", "term insurance", "pure protection", "death benefit only"],
        "endowment": ["endowment", "jeevan lakshya", "jeevan labh", "maturity benefit"],
        "ulip": ["ulip", "unit linked", "nav", "fund value", "market linked"],
        "whole_life": ["whole life", "sampurna", "lifetime", "age 99", "age 100"],
        "money_back": ["money back", "survival benefit", "periodic payout"],
        "pension": ["pension", "annuity", "retirement"],
    },
    "motor": {
        "comprehensive": ["comprehensive", "package", "bundled"],
        "third_party": ["third party only", "tp only", "liability only", "act only"],
        "standalone_od": ["standalone od", "own damage only", "od only"],
        "two_wheeler": ["two wheeler", "bike", "motorcycle", "scooter"],
        "commercial": ["commercial", "gcv", "pcv"],
    },
    "travel": {
        "international": ["international", "overseas", "abroad"],
        "domestic": ["domestic", "within india"],
        "student": ["student", "education", "study abroad"],
        "multi_trip": ["multi trip", "annual", "multi-trip"],
    },
    "pa": {
        "individual": ["individual", "personal"],
        "group": ["group", "employer"],
        "janata": ["janata", "pmsby", "pradhan mantri"],
    },
}


class PolicyClassifier:
    """3-tier cascading policy type classifier."""

    async def classify(self, text: str) -> ClassificationResult:
        """
        Classify policy type from document text.

        Args:
            text: First 2-3 pages of document text

        Returns:
            ClassificationResult with category, sub_type, confidence
        """
        text_lower = text.lower()

        # Tier 1: UIN + standard product + insurer prior
        result = self._tier1_rules(text, text_lower)
        if result and result.confidence >= 0.85:
            logger.info(
                "classification_tier1",
                category=result.category,
                confidence=result.confidence,
                signals=result.signals,
            )
            result.sub_type = self._detect_sub_type(result.category, text_lower)
            return result

        # Tier 2: Multi-signal weighted scoring
        result = self._tier2_scoring(text_lower)
        if result and result.confidence >= 0.50:
            logger.info(
                "classification_tier2",
                category=result.category,
                confidence=result.confidence,
            )
            result.sub_type = self._detect_sub_type(result.category, text_lower)
            return result

        # Tier 3: LLM chain-of-thought
        result = await self._tier3_llm(text)
        logger.info(
            "classification_tier3",
            category=result.category,
            confidence=result.confidence,
        )
        result.sub_type = self._detect_sub_type(result.category, text_lower)
        return result

    def _tier1_rules(self, text: str, text_lower: str) -> Optional[ClassificationResult]:
        """Tier 1: UIN patterns, standard products, insurer priors."""

        # Check UIN patterns
        for category, patterns in _UIN_PATTERNS.items():
            for pat in patterns:
                match = pat.search(text)
                if match:
                    return ClassificationResult(
                        category=category,
                        confidence=0.95,
                        tier_used=1,
                        signals=[f"UIN match: {match.group()}"],
                    )

        # Check IRDAI standard products
        for product_key, (cat, sub) in _STANDARD_PRODUCTS.items():
            if product_key in text_lower:
                return ClassificationResult(
                    category=cat,
                    sub_type=sub,
                    confidence=0.98,
                    tier_used=1,
                    signals=[f"Standard product: {product_key}"],
                )

        # Check deterministic fields
        motor_fields = sum(
            1 for kw in ["engine number", "chassis number", "registration number", "idv"]
            if kw in text_lower
        )
        if motor_fields >= 2:
            return ClassificationResult(
                category="motor",
                confidence=0.92,
                tier_used=1,
                signals=[f"Motor deterministic fields: {motor_fields}"],
            )

        travel_fields = sum(
            1 for kw in ["passport", "destination country", "visa", "trip cancellation"]
            if kw in text_lower
        )
        if travel_fields >= 2:
            return ClassificationResult(
                category="travel",
                confidence=0.90,
                tier_used=1,
                signals=[f"Travel deterministic fields: {travel_fields}"],
            )

        # Insurer prior (word-boundary match to avoid "lic" matching "policy")
        for insurer in _LIFE_ONLY_INSURERS:
            if re.search(r"\b" + re.escape(insurer) + r"\b", text_lower):
                return ClassificationResult(
                    category="life",
                    confidence=0.85,
                    tier_used=1,
                    signals=[f"Life-only insurer: {insurer}"],
                )

        for insurer in _HEALTH_ONLY_INSURERS:
            if re.search(r"\b" + re.escape(insurer) + r"\b", text_lower):
                return ClassificationResult(
                    category="health",
                    confidence=0.85,
                    tier_used=1,
                    signals=[f"Health-only insurer: {insurer}"],
                )

        return None

    def _tier2_scoring(self, text_lower: str) -> Optional[ClassificationResult]:
        """Tier 2: Weighted multi-signal keyword scoring."""
        scores: dict[str, float] = {}
        feature_counts: dict[str, int] = {}
        negative_counts: dict[str, int] = {}

        for category, features in _CATEGORY_FEATURES.items():
            score = 0.0
            count = 0
            neg = 0
            for keyword, weight in features:
                if keyword in text_lower:
                    score += weight
                    if weight > 0:
                        count += 1
                    else:
                        neg += 1
            scores[category] = score
            feature_counts[category] = count
            negative_counts[category] = neg

        if not scores:
            return None

        # Find best and second-best
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_cat, best_score = sorted_cats[0]
        second_score = sorted_cats[1][1] if len(sorted_cats) > 1 else 0.0

        if best_score <= 0:
            return None

        # Confidence based on margin and feature count
        margin = (best_score - second_score) / max(best_score, 1.0)
        confidence = 0.5 + (margin * 0.4) + min(best_score / 15.0, 0.1)

        # Boost for many features
        fc = feature_counts[best_cat]
        if fc >= 8:
            confidence += 0.10
        elif fc >= 5:
            confidence += 0.05

        # Reduce for negative signals
        nc = negative_counts[best_cat]
        if nc >= 3:
            confidence -= 0.15
        elif nc >= 1:
            confidence -= 0.05

        confidence = max(0.0, min(1.0, confidence))

        return ClassificationResult(
            category=best_cat,
            confidence=round(confidence, 3),
            tier_used=2,
            signals=[f"score={best_score:.1f}, features={fc}, margin={margin:.2f}"],
        )

    async def _tier3_llm(self, text: str) -> ClassificationResult:
        """Tier 3: LLM chain-of-thought classification."""
        prompt = (
            "Classify this insurance document into one of: health, life, motor, travel, pa.\n\n"
            "RULES:\n"
            "- health: mediclaim, hospitalization, room rent, copay, sum insured\n"
            "- life: sum assured, maturity, death benefit, nominee, surrender value\n"
            "- motor: IDV, vehicle, registration, own damage, third party\n"
            "- travel: trip, passport, destination, baggage, evacuation\n"
            "- pa: accidental death, permanent disability, weekly benefit\n\n"
            f"DOCUMENT (first 3000 chars):\n{text[:3000]}\n\n"
            'Return JSON: {"category": "...", "confidence": 0.0-1.0, "reasoning": "..."}'
        )

        try:
            response = await call_llm(
                messages=[{"role": "user", "content": prompt}],
                tier="tier1",
                extra_kwargs={"max_tokens": 150, "timeout": 8},
            )

            import json
            content = response.get("content", "")
            # Try to extract JSON
            match = re.search(r"\{[^}]+\}", content)
            if match:
                data = json.loads(match.group())
                category = data.get("category", "health").lower()
                if category not in ("health", "life", "motor", "travel", "pa"):
                    category = "health"
                return ClassificationResult(
                    category=category,
                    confidence=min(float(data.get("confidence", 0.5)), 0.85),
                    tier_used=3,
                    signals=[data.get("reasoning", "LLM classification")],
                )
        except Exception as e:
            logger.warning("tier3_llm_failed", error=str(e))

        # Ultimate fallback: health (most common)
        return ClassificationResult(
            category="health",
            confidence=0.3,
            tier_used=3,
            signals=["LLM fallback — low confidence"],
        )

    def _detect_sub_type(self, category: str, text_lower: str) -> str:
        """Detect sub-type within a category."""
        sub_types = _SUB_TYPES.get(category, {})
        for sub_name, keywords in sub_types.items():
            for kw in keywords:
                if kw in text_lower:
                    return sub_name
        return ""


# Singleton
policy_classifier = PolicyClassifier()
