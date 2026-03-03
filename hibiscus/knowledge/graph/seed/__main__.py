"""
Knowledge Graph Seed — CLI Entry Point
========================================
Run the full KG seed pipeline from the command line.

Usage:
    python -m hibiscus.knowledge.graph.seed

This will:
  1. Connect to Neo4j (using settings from .env / environment)
  2. Create all schema constraints and indexes
  3. Seed all data: 30+ insurers, 50+ products, 14 regulations,
     19 benchmarks, 9 tax rules, 17 ombudsman offices
  4. Close connection cleanly

Requires:
  - Neo4j running (bolt://localhost:7687 by default)
  - NEO4J_PASSWORD set in .env or environment
"""
import asyncio
import sys
import time

from hibiscus.knowledge.graph.client import init_kg, close_kg, kg_client
from hibiscus.knowledge.graph.schema import create_schema
from hibiscus.knowledge.graph.seed import seed_all
from hibiscus.observability.logger import get_logger, configure_logging

logger = get_logger("hibiscus.kg.seed.__main__")


async def main() -> None:
    configure_logging("INFO")
    t_start = time.monotonic()

    print("\n" + "=" * 60)
    print("  Hibiscus Knowledge Graph Seed")
    print("=" * 60)

    # 1. Connect
    print("\n[1/3] Connecting to Neo4j...")
    await init_kg()

    if not kg_client.is_connected:
        print(
            "\n  ERROR: Could not connect to Neo4j.\n"
            "  Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in your .env file.\n"
            "  Is Neo4j running? Try: docker compose up -d neo4j\n"
        )
        sys.exit(1)

    print("  Connected.")

    # 2. Schema
    print("\n[2/3] Creating schema (constraints + indexes)...")
    await create_schema(kg_client)
    print("  Schema ready.")

    # 3. Seed
    print("\n[3/3] Seeding Knowledge Graph data...")
    await seed_all(kg_client)

    # Summary
    elapsed = time.monotonic() - t_start
    print(f"\n  Seeded in {elapsed:.1f}s")

    # Quick verification query
    result = await kg_client.query(
        """
        MATCH (n)
        RETURN labels(n)[0] AS label, count(n) AS count
        ORDER BY label
        """,
        query_name="seed_verification",
        use_cache=False,
    )

    print("\n  Node counts:")
    for row in result:
        label = row.get("label", "Unknown")
        count = row.get("count", 0)
        print(f"    {label:<20} {count:>4}")

    # Cleanup
    await close_kg()

    print("\n" + "=" * 60)
    print("  Knowledge Graph seeded successfully.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
