"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
TPA lookup tool — search Third-Party Administrators by insurer, city, or name.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import Any, Dict, List, Optional

from hibiscus.knowledge.graph.client import kg_client
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.tools.knowledge.tpa_lookup")


async def lookup_tpa(
    tpa_name: Optional[str] = None,
    insurer_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Look up TPAs by name or by insurer partnership.

    Args:
        tpa_name:     Full or partial TPA name (e.g., "Medi Assist").
        insurer_name: Insurer name to find associated TPAs (e.g., "Star Health").

    Returns:
        List of TPA dicts with properties and insurer partnerships.
    """
    if not kg_client.is_connected:
        await kg_client.connect()
    if not kg_client.is_connected:
        logger.warning("tpa_lookup_kg_unavailable")
        return []

    try:
        if insurer_name:
            results = await kg_client.query(
                """
                MATCH (i:Insurer)-[:USES_TPA]->(t:TPA)
                WHERE toLower(i.name) CONTAINS toLower($name)
                RETURN t, i.name AS insurer_name
                ORDER BY t.digital_score DESC
                """,
                params={"name": insurer_name.strip()},
                query_name="tpa_lookup_by_insurer",
            )
        elif tpa_name:
            results = await kg_client.query(
                """
                MATCH (t:TPA)
                WHERE toLower(t.name) CONTAINS toLower($name)
                OPTIONAL MATCH (i:Insurer)-[:USES_TPA]->(t)
                RETURN t, collect(i.name) AS partner_insurers
                """,
                params={"name": tpa_name.strip()},
                query_name="tpa_lookup_by_name",
            )
        else:
            # List all TPAs
            results = await kg_client.query(
                """
                MATCH (t:TPA)
                OPTIONAL MATCH (i:Insurer)-[:USES_TPA]->(t)
                RETURN t, collect(i.name) AS partner_insurers
                ORDER BY t.network_size DESC
                LIMIT 20
                """,
                params={},
                query_name="tpa_list_all",
            )

        tpas = []
        for record in results:
            tpa_data = dict(record["t"])
            if "partner_insurers" in record:
                tpa_data["partner_insurers"] = record["partner_insurers"]
            if "insurer_name" in record:
                tpa_data["queried_insurer"] = record["insurer_name"]
            tpas.append(tpa_data)

        logger.info("tpa_lookup_result", count=len(tpas), query_insurer=insurer_name, query_tpa=tpa_name)
        return tpas

    except Exception as exc:
        logger.error("tpa_lookup_error", error=str(exc))
        return []


async def get_tpa_contact(
    insurer_name: str,
) -> Dict[str, Any]:
    """
    Get TPA contact info for a specific insurer — useful for claims guidance.

    Returns the primary TPA with contact details, cashless approval times,
    and helpline numbers for the ClaimsGuide agent.

    Args:
        insurer_name: Insurer name (e.g., "Star Health").

    Returns:
        Dict with TPA contact details, or empty dict if not found.
    """
    tpas = await lookup_tpa(insurer_name=insurer_name)
    if not tpas:
        return {}

    primary = tpas[0]  # Highest digital score
    return {
        "tpa_name": primary.get("name"),
        "website": primary.get("website", ""),
        "network_size": primary.get("network_size", 0),
        "cashless_approval_hours": primary.get("cashless_approval_time_hours", 0),
        "avg_processing_days": primary.get("avg_processing_days", 0),
        "digital_score": primary.get("digital_score", 0),
        "key_features": primary.get("key_features", []),
    }
