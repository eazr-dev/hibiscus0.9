"""
Auto-KG Enrichment Service
===========================
Every policy Hibiscus analyzes makes the Knowledge Graph smarter.

Architecture:
- Queue-and-flush: extraction data is queued on analysis, flushed to Neo4j every 5 min
- Only high-confidence extractions (≥0.85) are accepted
- Validated before write: fuzzy match insurer names, check numeric ranges
- Enriched nodes tagged with source="enriched" for audit trail
- Never overwrites verified seed data (supplements only)

Usage:
    from hibiscus.services.kg_enrichment import kg_enrichment

    # In memory_storage node (fire-and-forget):
    kg_enrichment.enqueue(extraction_data, confidence, user_id)

    # In main.py lifespan:
    await kg_enrichment.start_flush_loop()
    # On shutdown:
    await kg_enrichment.stop()
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from hibiscus.observability.logger import get_logger

logger = get_logger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
_MIN_CONFIDENCE = 0.85
_FLUSH_INTERVAL_SECONDS = 300   # 5 minutes
_MAX_QUEUE_SIZE = 1000
_ENRICHMENT_SOURCE = "policy_extraction"


@dataclass
class EnrichmentItem:
    """A validated extraction ready for KG enrichment."""
    insurer_name: str
    product_name: Optional[str]
    category: Optional[str]
    data: Dict[str, Any]           # Cleaned extraction fields
    confidence: float
    user_id: str
    timestamp: float = field(default_factory=time.time)
    warnings: List[str] = field(default_factory=list)
    is_new_insurer: bool = False


class KGEnrichmentService:
    """
    Queue-and-flush KG enrichment from policy extractions.
    Thread-safe via asyncio.Lock. Graceful degradation if Neo4j unavailable.
    """

    def __init__(self, flush_interval: int = _FLUSH_INTERVAL_SECONDS):
        self._queue: List[EnrichmentItem] = []
        self._flush_interval = flush_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._audit_log: List[Dict[str, Any]] = []  # In-memory audit trail

    def enqueue(
        self,
        extraction: Dict[str, Any],
        confidence: float,
        user_id: str,
    ) -> bool:
        """
        Enqueue extraction data for KG enrichment.
        Validates before accepting. Returns True if accepted.

        Called from memory_storage._do_store() — must be non-blocking.
        """
        if confidence < _MIN_CONFIDENCE:
            return False

        if not extraction:
            return False

        # Validate
        from hibiscus.services.kg_enrichment_validator import enrichment_validator
        is_valid, cleaned, warnings = enrichment_validator.validate_extraction(extraction)

        if not is_valid:
            logger.info(
                "kg_enrichment_rejected",
                user_id=user_id,
                reason="validation_failed",
                warnings=warnings,
            )
            return False

        item = EnrichmentItem(
            insurer_name=cleaned["insurer_name"],
            product_name=cleaned.get("product_name"),
            category=cleaned.get("category"),
            data=cleaned,
            confidence=confidence,
            user_id=user_id,
            warnings=warnings,
            is_new_insurer=cleaned.get("insurer_is_new", False),
        )

        # Cap queue size
        if len(self._queue) >= _MAX_QUEUE_SIZE:
            self._queue.pop(0)  # Drop oldest
            logger.warning("kg_enrichment_queue_overflow", dropped=1)

        self._queue.append(item)
        logger.info(
            "kg_enrichment_queued",
            insurer=item.insurer_name,
            product=item.product_name,
            queue_size=len(self._queue),
        )
        return True

    async def _flush(self) -> int:
        """
        Flush queued items to Neo4j.
        Deduplicates by (insurer_name, product_name).
        Returns count of successful writes.
        """
        async with self._lock:
            if not self._queue:
                return 0

            items = list(self._queue)
            self._queue.clear()

        logger.info("kg_enrichment_flush_start", items=len(items))

        # Deduplicate: keep highest confidence per (insurer, product)
        deduped: Dict[str, EnrichmentItem] = {}
        for item in items:
            key = f"{item.insurer_name}|{item.product_name or 'unknown'}"
            if key not in deduped or item.confidence > deduped[key].confidence:
                deduped[key] = item

        success_count = 0
        try:
            from hibiscus.knowledge.graph.client import kg_client

            if not kg_client.is_connected:
                await kg_client.connect()
            if not kg_client.is_connected:
                logger.warning("kg_enrichment_flush_skipped", reason="neo4j_unavailable")
                return 0

            for item in deduped.values():
                try:
                    await self._enrich_item(kg_client, item)
                    success_count += 1
                    self._audit_log.append({
                        "timestamp": time.time(),
                        "action": "enriched",
                        "insurer": item.insurer_name,
                        "product": item.product_name,
                        "is_new_insurer": item.is_new_insurer,
                        "confidence": item.confidence,
                        "user_id": item.user_id,
                    })
                except Exception as e:
                    logger.warning(
                        "kg_enrichment_item_failed",
                        insurer=item.insurer_name,
                        error=str(e),
                    )

        except Exception as e:
            logger.error("kg_enrichment_flush_error", error=str(e))

        # Trim audit log (keep last 500)
        if len(self._audit_log) > 500:
            self._audit_log = self._audit_log[-500:]

        logger.info(
            "kg_enrichment_flush_complete",
            attempted=len(deduped),
            succeeded=success_count,
        )
        return success_count

    async def _enrich_item(self, kg_client: Any, item: EnrichmentItem) -> None:
        """Enrich KG with a single validated item."""

        # 1. MERGE insurer node (create stub if new, never overwrite existing)
        await kg_client.execute_write(
            """
            MERGE (i:Insurer {name: $name})
            ON CREATE SET
                i.source = 'enriched',
                i.enriched_at = datetime(),
                i.enrichment_confidence = $confidence
            """,
            params={
                "name": item.insurer_name,
                "confidence": item.confidence,
            },
            query_name="enrich_insurer",
        )

        # 2. MERGE product node if product name available
        if item.product_name:
            product_props = {
                "name": item.product_name,
                "insurer_name": item.insurer_name,
                "category": item.category or "unknown",
                "confidence": item.confidence,
            }
            # Add numeric fields if available
            if item.data.get("sum_insured"):
                product_props["sum_insured_observed"] = item.data["sum_insured"]
            if item.data.get("annual_premium"):
                product_props["premium_observed"] = item.data["annual_premium"]

            await kg_client.execute_write(
                """
                MERGE (p:Product {name: $name})
                ON CREATE SET
                    p.category = $category,
                    p.source = 'enriched',
                    p.enriched_at = datetime(),
                    p.enrichment_confidence = $confidence,
                    p.enrichment_source = 'policy_extraction'
                ON MATCH SET
                    p.last_seen = datetime(),
                    p.observation_count = COALESCE(p.observation_count, 0) + 1
                WITH p
                MATCH (i:Insurer {name: $insurer_name})
                MERGE (i)-[:OFFERS]->(p)
                """,
                params=product_props,
                query_name="enrich_product",
            )

            # 3. Update product features if more detailed than current
            feature_updates = {}
            for key in ("copay", "room_rent_limit", "deductible", "network_hospitals",
                         "waiting_period", "restoration_benefit", "no_claim_bonus"):
                if key in item.data:
                    feature_updates[key] = item.data[key]

            if feature_updates:
                # Only set properties that don't already exist (supplement, not replace)
                set_clauses = ", ".join(
                    f"p.{k} = COALESCE(p.{k}, ${k})"
                    for k in feature_updates
                )
                await kg_client.execute_write(
                    f"""
                    MATCH (p:Product {{name: $name}})
                    WHERE p.source = 'enriched'
                    SET {set_clauses}
                    """,
                    params={"name": item.product_name, **feature_updates},
                    query_name="enrich_product_features",
                )

    async def start_flush_loop(self) -> None:
        """Start the periodic flush loop. Call from app lifespan."""
        self._running = True
        logger.info("kg_enrichment_loop_started", interval_s=self._flush_interval)
        while self._running:
            await asyncio.sleep(self._flush_interval)
            if self._queue:
                await self._flush()

    async def stop(self) -> None:
        """Stop the flush loop and drain remaining queue."""
        self._running = False
        if self._queue:
            await self._flush()
        logger.info("kg_enrichment_stopped")

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent enrichment audit entries."""
        return self._audit_log[-limit:]

    @property
    def queue_size(self) -> int:
        return len(self._queue)


# ── Module-level singleton ──────────────────────────────────────────────────
kg_enrichment = KGEnrichmentService()
