"""
Knowledge Graph Seed Data
==========================
Orchestrates seeding of all KG node types in the correct order.

Order matters:
  1. Insurers    — base nodes referenced by Products
  2. Products    — creates OFFERS relationships to Insurers
  3. Regulations — standalone nodes
  4. Benchmarks  — standalone nodes
  5. Tax Rules   — standalone nodes
  6. Ombudsman   — standalone nodes

Usage:
    from hibiscus.knowledge.graph.seed import seed_all
    await seed_all(kg_client)

    # Or use individual seeders:
    from hibiscus.knowledge.graph.seed import (
        INSURERS, seed_insurers,
        PRODUCTS, seed_products,
        REGULATIONS, seed_regulations,
        BENCHMARKS, seed_benchmarks,
        TAX_RULES, seed_tax_rules,
        OMBUDSMAN_OFFICES, seed_ombudsman,
    )
"""
from hibiscus.knowledge.graph.client import Neo4jClient
from hibiscus.observability.logger import get_logger

# Re-export data constants and seed functions for convenience
from .insurers import INSURERS, seed_insurers
from .products import PRODUCTS, seed_products
from .regulations import REGULATIONS, seed_regulations
from .benchmarks import BENCHMARKS, seed_benchmarks
from .tax_rules import TAX_RULES, seed_tax_rules
from .ombudsman import OMBUDSMAN_OFFICES, seed_ombudsman

__all__ = [
    "INSURERS",
    "seed_insurers",
    "PRODUCTS",
    "seed_products",
    "REGULATIONS",
    "seed_regulations",
    "BENCHMARKS",
    "seed_benchmarks",
    "TAX_RULES",
    "seed_tax_rules",
    "OMBUDSMAN_OFFICES",
    "seed_ombudsman",
    "seed_all",
]

logger = get_logger("hibiscus.kg.seed")


async def seed_all(client: Neo4jClient) -> None:
    """
    Run all seed functions in dependency order.
    Idempotent — all seeders use MERGE, so running multiple times is safe.

    Args:
        client: Connected Neo4jClient instance.
    """
    from hibiscus.knowledge.graph.seed.insurers import seed_insurers
    from hibiscus.knowledge.graph.seed.products import seed_products
    from hibiscus.knowledge.graph.seed.regulations import seed_regulations
    from hibiscus.knowledge.graph.seed.benchmarks import seed_benchmarks
    from hibiscus.knowledge.graph.seed.tax_rules import seed_tax_rules
    from hibiscus.knowledge.graph.seed.ombudsman import seed_ombudsman

    seeders = [
        ("insurers", seed_insurers),
        ("products", seed_products),
        ("regulations", seed_regulations),
        ("benchmarks", seed_benchmarks),
        ("tax_rules", seed_tax_rules),
        ("ombudsman", seed_ombudsman),
    ]

    logger.info("seed_all_start", seeder_count=len(seeders))

    for name, seeder in seeders:
        logger.info(f"seed_all_running_{name}")
        try:
            await seeder(client)
            logger.info(f"seed_all_{name}_ok")
        except Exception as exc:
            logger.error(
                f"seed_all_{name}_failed",
                error=str(exc),
                note="Continuing with remaining seeders",
            )

    logger.info("seed_all_complete")
