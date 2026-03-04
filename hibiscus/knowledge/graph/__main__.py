"""
Run all Knowledge Graph seeding.

Usage:
    python -m hibiscus.knowledge.graph

This script:
  1. Connects to Neo4j
  2. Creates schema (constraints + indexes)
  3. Seeds all node types in dependency order:
       Insurers -> Products -> Regulations -> Benchmarks -> TaxRules -> Ombudsman
  4. Closes connection

Safe to re-run — all seeders use MERGE (idempotent).
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import asyncio
import sys

from hibiscus.knowledge.graph.client import init_kg, close_kg, kg_client
from hibiscus.knowledge.graph.schema import create_schema
from hibiscus.knowledge.graph.seed import (
    seed_insurers,
    seed_products,
    seed_regulations,
    seed_benchmarks,
    seed_tax_rules,
    seed_ombudsman,
)
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.main")


async def main() -> None:
    """Connect, create schema, seed all KG data, disconnect."""
    print("Hibiscus Knowledge Graph — Seeding")
    print("=" * 45)

    # 1. Connect
    print("\n[1/9] Connecting to Neo4j...")
    await init_kg()
    if not kg_client.is_connected:
        print(
            "ERROR: Could not connect to Neo4j. "
            "Check NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD in .env"
        )
        sys.exit(1)
    print("      Connected.")

    # 2. Create schema
    print("[2/9] Creating schema (constraints + indexes)...")
    await create_schema(kg_client)
    print("      Schema ready.")

    # 3–8. Seed each node type
    seeders = [
        (3, "Insurers",    seed_insurers),
        (4, "Products",    seed_products),
        (5, "Regulations", seed_regulations),
        (6, "Benchmarks",  seed_benchmarks),
        (7, "Tax Rules",   seed_tax_rules),
        (8, "Ombudsman",   seed_ombudsman),
    ]

    failures = []
    for step, label, seeder in seeders:
        print(f"[{step}/9] Seeding {label}...")
        try:
            await seeder(kg_client)
            print(f"      {label} seeded.")
        except Exception as exc:
            print(f"      ERROR seeding {label}: {exc}")
            failures.append(label)

    # 9. Disconnect
    print("[9/9] Closing connection...")
    await close_kg()
    print("      Done.")

    # Summary
    print("\n" + "=" * 45)
    if failures:
        print(f"Seeding complete with errors in: {', '.join(failures)}")
        print("Check logs for details.")
        sys.exit(1)
    else:
        print("All KG seed data loaded successfully.")
        print(
            "\nVerify with:"
            "\n  MATCH (n) RETURN labels(n), count(n) ORDER BY labels(n)"
        )


if __name__ == "__main__":
    asyncio.run(main())
