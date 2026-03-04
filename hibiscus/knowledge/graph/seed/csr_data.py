"""
CSR Time-Series Seed Data
==========================
Seeds CSREntry nodes from botproject's claim_settlement_ratios table.
Each entry is (insurer_name, financial_year, csr_type) → csr_value.

This replaces the single `csr` float on Insurer with time-series data.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List

from hibiscus.knowledge.graph.client import Neo4jClient
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.csr_data")


_MERGE_CSR_ENTRY = """
MERGE (c:CSREntry {insurer_name: $insurer_name, financial_year: $financial_year, csr_type: $csr_type})
SET
  c.csr_value           = $csr_value,
  c.data_confidence     = $data_confidence,
  c.source              = 'botproject_seed',
  c.updated_at          = datetime()
RETURN c.insurer_name AS insurer_name, c.financial_year AS fy
"""

_MERGE_HAS_CSR_REL = """
MATCH (i:Insurer {name: $insurer_name})
MATCH (c:CSREntry {insurer_name: $insurer_name, financial_year: $financial_year, csr_type: $csr_type})
MERGE (i)-[:HAS_CSR]->(c)
"""


async def seed_csr_entries(client: Neo4jClient, entries: List[Dict[str, Any]]) -> None:
    """
    MERGE CSREntry nodes and HAS_CSR relationships into Neo4j.
    Idempotent — safe to re-run.

    Args:
        client: Connected Neo4jClient instance.
        entries: List of CSR dicts from botproject_parser.parse_csr_entries().
    """
    if not entries:
        logger.info("seed_csr_entries_skip", reason="no entries")
        return

    logger.info("seed_csr_entries_start", count=len(entries))

    # Prepare params
    csr_params = []
    for entry in entries:
        csr_params.append({
            "insurer_name": entry["company_name"],
            "financial_year": entry["financial_year"],
            "csr_type": entry["csr_type"],
            "csr_value": entry["csr_value"],
            "data_confidence": entry.get("data_confidence", "verified"),
        })

    # Merge CSR nodes
    succeeded = await client.execute_batch(
        _MERGE_CSR_ENTRY,
        param_list=csr_params,
        query_name="seed_csr_entries",
    )
    logger.info("seed_csr_entries_nodes_complete", succeeded=succeeded, total=len(csr_params))

    # Create HAS_CSR relationships
    rel_ok = await client.execute_batch(
        _MERGE_HAS_CSR_REL,
        param_list=csr_params,
        query_name="seed_csr_relationships",
    )
    logger.info("seed_csr_relationships_complete", succeeded=rel_ok, total=len(csr_params))
