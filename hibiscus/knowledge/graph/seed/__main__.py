"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
KG seed CLI — python -m hibiscus.knowledge.graph.seed to populate Neo4j.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
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
