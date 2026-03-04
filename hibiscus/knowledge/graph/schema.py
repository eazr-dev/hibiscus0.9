"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
KG schema — node types (Insurer, Product, Regulation) and relationship definitions.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from typing import List

from hibiscus.knowledge.graph.client import Neo4jClient
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.schema")

# ── Constraint / Index DDL statements ─────────────────────────────────────────

_CONSTRAINTS: List[str] = [
    # Unique node key constraints
    "CREATE CONSTRAINT insurer_name_unique IF NOT EXISTS "
    "FOR (n:Insurer) REQUIRE n.name IS UNIQUE",

    "CREATE CONSTRAINT product_name_unique IF NOT EXISTS "
    "FOR (n:Product) REQUIRE n.name IS UNIQUE",

    "CREATE CONSTRAINT regulation_circular_unique IF NOT EXISTS "
    "FOR (n:Regulation) REQUIRE n.circular_no IS UNIQUE",

    "CREATE CONSTRAINT tpa_name_unique IF NOT EXISTS "
    "FOR (n:TPA) REQUIRE n.name IS UNIQUE",

    "CREATE CONSTRAINT ombudsman_city_unique IF NOT EXISTS "
    "FOR (n:OmbudsmanOffice) REQUIRE n.city IS UNIQUE",

    "CREATE CONSTRAINT tax_rule_section_unique IF NOT EXISTS "
    "FOR (n:TaxRule) REQUIRE (n.section, n.subsection) IS UNIQUE",

    "CREATE CONSTRAINT csr_entry_unique IF NOT EXISTS "
    "FOR (n:CSREntry) REQUIRE (n.insurer_name, n.financial_year, n.csr_type) IS UNIQUE",

    "CREATE CONSTRAINT policy_document_unique IF NOT EXISTS "
    "FOR (n:PolicyDocument) REQUIRE (n.uin, n.title) IS UNIQUE",

    "CREATE CONSTRAINT premium_example_unique IF NOT EXISTS "
    "FOR (n:PremiumExample) REQUIRE (n.product_name, n.age, n.gender, n.sum_insured, n.plan_option) IS UNIQUE",

    "CREATE CONSTRAINT source_unique IF NOT EXISTS "
    "FOR (n:Source) REQUIRE (n.source_url, n.source_name) IS UNIQUE",
]

_INDEXES: List[str] = [
    # ── Insurer ──────────────────────────────────────────────────────────
    "CREATE INDEX insurer_type IF NOT EXISTS "
    "FOR (n:Insurer) ON (n.type)",

    "CREATE INDEX insurer_csr IF NOT EXISTS "
    "FOR (n:Insurer) ON (n.csr)",

    "CREATE INDEX insurer_icr IF NOT EXISTS "
    "FOR (n:Insurer) ON (n.icr)",

    "CREATE INDEX insurer_digital_score IF NOT EXISTS "
    "FOR (n:Insurer) ON (n.digital_score)",

    # ── Product ──────────────────────────────────────────────────────────
    "CREATE INDEX product_category IF NOT EXISTS "
    "FOR (n:Product) ON (n.category)",

    "CREATE INDEX product_type IF NOT EXISTS "
    "FOR (n:Product) ON (n.type)",

    "CREATE INDEX product_eazr_score IF NOT EXISTS "
    "FOR (n:Product) ON (n.eazr_score)",

    "CREATE INDEX product_sum_insured_min IF NOT EXISTS "
    "FOR (n:Product) ON (n.sum_insured_min)",

    "CREATE INDEX product_sum_insured_max IF NOT EXISTS "
    "FOR (n:Product) ON (n.sum_insured_max)",

    # ── Regulation ───────────────────────────────────────────────────────
    "CREATE INDEX regulation_category IF NOT EXISTS "
    "FOR (n:Regulation) ON (n.category)",

    "CREATE INDEX regulation_date IF NOT EXISTS "
    "FOR (n:Regulation) ON (n.date)",

    "CREATE INDEX regulation_effective_date IF NOT EXISTS "
    "FOR (n:Regulation) ON (n.effective_date)",

    # ── Benchmark ────────────────────────────────────────────────────────
    "CREATE INDEX benchmark_category IF NOT EXISTS "
    "FOR (n:Benchmark) ON (n.category)",

    "CREATE INDEX benchmark_metric IF NOT EXISTS "
    "FOR (n:Benchmark) ON (n.metric)",

    # ── TaxRule ──────────────────────────────────────────────────────────
    "CREATE INDEX tax_rule_section IF NOT EXISTS "
    "FOR (n:TaxRule) ON (n.section)",

    # ── Product UIN ────────────────────────────────────────────────────────
    "CREATE INDEX product_uin IF NOT EXISTS "
    "FOR (n:Product) ON (n.uin)",

    "CREATE INDEX product_source IF NOT EXISTS "
    "FOR (n:Product) ON (n.source)",

    # ── CSREntry ───────────────────────────────────────────────────────────
    "CREATE INDEX csr_insurer IF NOT EXISTS "
    "FOR (n:CSREntry) ON (n.insurer_name)",

    "CREATE INDEX csr_financial_year IF NOT EXISTS "
    "FOR (n:CSREntry) ON (n.financial_year)",

    # ── OmbudsmanOffice ──────────────────────────────────────────────────
    "CREATE INDEX ombudsman_jurisdiction IF NOT EXISTS "
    "FOR (n:OmbudsmanOffice) ON (n.jurisdiction)",

    # ── PolicyDocument ────────────────────────────────────────────────────
    "CREATE INDEX policydoc_uin IF NOT EXISTS "
    "FOR (n:PolicyDocument) ON (n.uin)",

    "CREATE INDEX policydoc_doc_type IF NOT EXISTS "
    "FOR (n:PolicyDocument) ON (n.doc_type)",

    # ── PremiumExample ────────────────────────────────────────────────────
    "CREATE INDEX premium_product_name IF NOT EXISTS "
    "FOR (n:PremiumExample) ON (n.product_name)",

    "CREATE INDEX premium_age IF NOT EXISTS "
    "FOR (n:PremiumExample) ON (n.age)",

    # ── Source ────────────────────────────────────────────────────────────
    "CREATE INDEX source_type IF NOT EXISTS "
    "FOR (n:Source) ON (n.source_type)",

    "CREATE INDEX source_entity_type IF NOT EXISTS "
    "FOR (n:Source) ON (n.entity_type)",
]

# Full-text search indexes (Neo4j 4.x+)
_FULLTEXT_INDEXES: List[str] = [
    "CREATE FULLTEXT INDEX insurer_fulltext IF NOT EXISTS "
    "FOR (n:Insurer) ON EACH [n.name]",

    "CREATE FULLTEXT INDEX product_fulltext IF NOT EXISTS "
    "FOR (n:Product) ON EACH [n.name, n.category, n.type]",

    "CREATE FULLTEXT INDEX regulation_fulltext IF NOT EXISTS "
    "FOR (n:Regulation) ON EACH [n.subject, n.category]",
]


async def create_schema(client: Neo4jClient) -> None:
    """
    Create all constraints and indexes.
    Idempotent — safe to run multiple times (uses IF NOT EXISTS).

    Args:
        client: Connected Neo4jClient instance.
    """
    logger.info("schema_creation_start")

    if not client.is_connected:
        logger.warning(
            "schema_creation_skipped",
            reason="Neo4j client not connected — schema will be created when connection is established",
        )
        return

    # Apply constraints first (required before indexes that rely on them)
    constraint_ok = 0
    for stmt in _CONSTRAINTS:
        try:
            await client.execute_write(stmt, query_name="create_constraint")
            constraint_ok += 1
        except Exception as exc:
            logger.warning(
                "schema_constraint_warning",
                statement_prefix=stmt[:80],
                error=str(exc),
            )

    # Apply standard indexes
    index_ok = 0
    for stmt in _INDEXES:
        try:
            await client.execute_write(stmt, query_name="create_index")
            index_ok += 1
        except Exception as exc:
            logger.warning(
                "schema_index_warning",
                statement_prefix=stmt[:80],
                error=str(exc),
            )

    # Apply full-text indexes (may not be supported on all Neo4j editions)
    ft_ok = 0
    for stmt in _FULLTEXT_INDEXES:
        try:
            await client.execute_write(stmt, query_name="create_fulltext_index")
            ft_ok += 1
        except Exception as exc:
            logger.warning(
                "schema_fulltext_index_warning",
                statement_prefix=stmt[:80],
                error=str(exc),
                note="Full-text indexes require Neo4j 4.x+ — safe to ignore on older versions",
            )

    logger.info(
        "schema_creation_complete",
        constraints_created=constraint_ok,
        indexes_created=index_ok,
        fulltext_indexes_created=ft_ok,
        total_statements=len(_CONSTRAINTS) + len(_INDEXES) + len(_FULLTEXT_INDEXES),
    )


async def drop_schema(client: Neo4jClient) -> None:
    """
    Drop all KG data and schema for a clean reseed.
    WARNING: Destructive — use only in development / CI.
    """
    logger.warning("schema_drop_start", warning="THIS WILL DELETE ALL KG DATA")

    drop_stmts = [
        # Drop full-text indexes
        "DROP INDEX insurer_fulltext IF EXISTS",
        "DROP INDEX product_fulltext IF EXISTS",
        "DROP INDEX regulation_fulltext IF EXISTS",
        # Drop standard indexes
        "DROP INDEX insurer_type IF EXISTS",
        "DROP INDEX insurer_csr IF EXISTS",
        "DROP INDEX insurer_icr IF EXISTS",
        "DROP INDEX insurer_digital_score IF EXISTS",
        "DROP INDEX product_category IF EXISTS",
        "DROP INDEX product_type IF EXISTS",
        "DROP INDEX product_eazr_score IF EXISTS",
        "DROP INDEX product_sum_insured_min IF EXISTS",
        "DROP INDEX product_sum_insured_max IF EXISTS",
        "DROP INDEX regulation_category IF EXISTS",
        "DROP INDEX regulation_date IF EXISTS",
        "DROP INDEX regulation_effective_date IF EXISTS",
        "DROP INDEX benchmark_category IF EXISTS",
        "DROP INDEX benchmark_metric IF EXISTS",
        "DROP INDEX tax_rule_section IF EXISTS",
        "DROP INDEX ombudsman_jurisdiction IF EXISTS",
        "DROP INDEX product_uin IF EXISTS",
        "DROP INDEX product_source IF EXISTS",
        "DROP INDEX csr_insurer IF EXISTS",
        "DROP INDEX csr_financial_year IF EXISTS",
        "DROP INDEX policydoc_uin IF EXISTS",
        "DROP INDEX policydoc_doc_type IF EXISTS",
        "DROP INDEX premium_product_name IF EXISTS",
        "DROP INDEX premium_age IF EXISTS",
        "DROP INDEX source_type IF EXISTS",
        "DROP INDEX source_entity_type IF EXISTS",
        # Drop constraints
        "DROP CONSTRAINT insurer_name_unique IF EXISTS",
        "DROP CONSTRAINT product_name_unique IF EXISTS",
        "DROP CONSTRAINT regulation_circular_unique IF EXISTS",
        "DROP CONSTRAINT tpa_name_unique IF EXISTS",
        "DROP CONSTRAINT ombudsman_city_unique IF EXISTS",
        "DROP CONSTRAINT tax_rule_section_unique IF EXISTS",
        "DROP CONSTRAINT csr_entry_unique IF EXISTS",
        "DROP CONSTRAINT policy_document_unique IF EXISTS",
        "DROP CONSTRAINT premium_example_unique IF EXISTS",
        "DROP CONSTRAINT source_unique IF EXISTS",
        # Delete all nodes and relationships
        "MATCH (n) DETACH DELETE n",
    ]

    for stmt in drop_stmts:
        try:
            await client.execute_write(stmt, query_name="drop_schema")
        except Exception as exc:
            logger.warning("schema_drop_warning", statement_prefix=stmt[:80], error=str(exc))

    logger.info("schema_drop_complete")
