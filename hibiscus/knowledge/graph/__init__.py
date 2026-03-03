"""
Hibiscus Knowledge Graph
=========================
Neo4j-backed knowledge graph with insurers, products, regulations,
benchmarks, tax rules, and ombudsman offices.

Quick start:
    from hibiscus.knowledge.graph import kg_client, init_kg, close_kg

    await init_kg()
    result = await kg_client.query(
        "MATCH (i:Insurer {name: $name}) RETURN i",
        params={"name": "HDFC Life Insurance"},
        query_name="get_hdfc_life",
    )
    await close_kg()
"""
from hibiscus.knowledge.graph.client import kg_client, init_kg, close_kg, Neo4jClient
from hibiscus.knowledge.graph.schema import create_schema

__all__ = [
    "kg_client",
    "init_kg",
    "close_kg",
    "Neo4jClient",
    "create_schema",
]
