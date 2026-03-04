# 🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
from hibiscus.knowledge.graph.client import Neo4jClient
from hibiscus.observability.logger import get_logger

# Re-export data constants and seed functions for convenience
from .insurers import INSURERS, seed_insurers
from .products import PRODUCTS, seed_products
from .regulations import REGULATIONS, seed_regulations
from .benchmarks import BENCHMARKS, seed_benchmarks
from .tax_rules import TAX_RULES, seed_tax_rules
from .ombudsman import OMBUDSMAN_OFFICES, seed_ombudsman
from .botproject_seed import seed_from_botproject, seed_rag_from_botproject
from .tpa import TPA_DATA, seed_tpas

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
    "TPA_DATA",
    "seed_tpas",
    "seed_from_botproject",
    "seed_rag_from_botproject",
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

    from hibiscus.knowledge.graph.seed.tpa import seed_tpas

    seeders = [
        ("insurers", seed_insurers),
        ("products", seed_products),
        ("regulations", seed_regulations),
        ("benchmarks", seed_benchmarks),
        ("tax_rules", seed_tax_rules),
        ("ombudsman", seed_ombudsman),
        ("tpas", lambda c: seed_tpas()),
        ("botproject", lambda c: seed_from_botproject(c)),
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

    # ── Create cross-entity relationships ────────────────────────────────
    logger.info("seed_all_creating_relationships")
    try:
        await _seed_relationships(client)
        logger.info("seed_all_relationships_ok")
    except Exception as exc:
        logger.error("seed_all_relationships_failed", error=str(exc))

    # ── RAG ingestion from botproject SQL (optional) ──────────────────
    try:
        rag_result = await seed_rag_from_botproject()
        logger.info("seed_all_rag_ok", **rag_result)
    except Exception as exc:
        logger.error(
            "seed_all_rag_failed",
            error=str(exc),
            note="RAG ingestion is optional — KG seed still complete",
        )

    logger.info("seed_all_complete")


async def _seed_relationships(client: Neo4jClient) -> None:
    """Create cross-entity relationships (GOVERNED_BY, BENCHMARKED_AGAINST, SUPERSEDES, COVERS).

    Uses MERGE for idempotency — safe to re-run.
    """
    relationship_queries = [
        # GOVERNED_BY: Products → Regulations (match by category)
        (
            "governed_by",
            """
            MATCH (p:Product), (r:Regulation)
            WHERE p.category = r.category
               OR (p.category = 'health' AND r.category = 'health_insurance')
               OR (p.category = 'life' AND r.category = 'life_insurance')
               OR (p.category = 'motor' AND r.category = 'motor_insurance')
               OR (p.category = 'travel' AND r.category = 'travel_insurance')
               OR (r.category = 'general')
            MERGE (p)-[:GOVERNED_BY]->(r)
            RETURN count(*) AS count
            """,
        ),
        # BENCHMARKED_AGAINST: Products → Benchmarks (match by category)
        (
            "benchmarked_against",
            """
            MATCH (p:Product), (b:Benchmark)
            WHERE p.category = b.category
               OR b.category = 'general'
            MERGE (p)-[:BENCHMARKED_AGAINST]->(b)
            RETURN count(*) AS count
            """,
        ),
        # SUPERSEDES: Newer regulations supersede older ones in the same category
        (
            "supersedes",
            """
            MATCH (newer:Regulation), (older:Regulation)
            WHERE newer.category = older.category
              AND newer.circular_no <> older.circular_no
              AND newer.effective_date > older.effective_date
              AND newer.legislation_type = older.legislation_type
            MERGE (newer)-[:SUPERSEDES]->(older)
            RETURN count(*) AS count
            """,
        ),
        # COVERS: Products → coverage categories (health products cover health risks)
        (
            "covers",
            """
            MATCH (p:Product)
            WHERE p.category IS NOT NULL
            MERGE (c:CoverageCategory {name: p.category})
            MERGE (p)-[:COVERS]->(c)
            RETURN count(*) AS count
            """,
        ),
        # HAS_DOCUMENT: Products → PolicyDocuments (match by UIN)
        (
            "has_document",
            """
            MATCH (p:Product), (d:PolicyDocument)
            WHERE p.uin = d.uin
            MERGE (p)-[:HAS_DOCUMENT]->(d)
            RETURN count(*) AS count
            """,
        ),
        # HAS_PREMIUM_EXAMPLE: Products → PremiumExamples (match by name)
        (
            "has_premium_example",
            """
            MATCH (p:Product), (pe:PremiumExample)
            WHERE p.name = pe.product_name
            MERGE (p)-[:HAS_PREMIUM_EXAMPLE]->(pe)
            RETURN count(*) AS count
            """,
        ),
    ]

    for name, query in relationship_queries:
        try:
            await client.execute_write(query, query_name=f"seed_rel_{name}")
            logger.info(f"seed_relationship_{name}_ok")
        except Exception as exc:
            logger.warning(f"seed_relationship_{name}_failed", error=str(exc))
