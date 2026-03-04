"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
KG seed: botproject loader — imports parsed SQL data into Neo4j graph nodes.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from hibiscus.knowledge.graph.client import Neo4jClient
from hibiscus.knowledge.graph.seed.botproject_parser import parse_all_seed_files
from hibiscus.knowledge.graph.seed.name_mapper import (
    legal_to_kg,
    get_insurer_type_from_company_type,
)
from hibiscus.knowledge.graph.seed.subcat_mapper import map_sub_category
from hibiscus.knowledge.graph.seed.csr_data import seed_csr_entries
from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.botproject_seed")


# ── Cypher Queries ────────────────────────────────────────────────────────────

_MERGE_NEW_INSURER = """
MERGE (i:Insurer {name: $name})
SET
  i.short_name                  = $short_name,
  i.type                        = $type,
  i.irdai_reg_no                = $irdai_reg_no,
  i.headquarters                = $headquarters,
  i.established_year            = $established_year,
  i.website                     = $website,
  i.ceo_name                    = $ceo_name,
  i.irdai_page_url              = $irdai_page_url,
  i.source                      = 'botproject_seed',
  i.updated_at                  = datetime()
RETURN i.name AS name
"""

_ENRICH_INSURER = """
MATCH (i:Insurer {name: $name})
SET
  i.website         = CASE WHEN $website IS NOT NULL THEN $website ELSE i.website END,
  i.ceo_name        = CASE WHEN $ceo_name IS NOT NULL THEN $ceo_name ELSE i.ceo_name END,
  i.irdai_page_url  = CASE WHEN $irdai_page_url IS NOT NULL THEN $irdai_page_url ELSE i.irdai_page_url END,
  i.updated_at      = datetime()
RETURN i.name AS name
"""

_MERGE_BOTPROJECT_PRODUCT = """
MERGE (p:Product {name: $name})
SET
  p.insurer_name        = $insurer_name,
  p.category            = $category,
  p.type                = $type,
  p.uin                 = $uin,
  p.product_scope       = $product_scope,
  p.linked_type         = $linked_type,
  p.par_type            = $par_type,
  p.is_active           = $is_active,
  p.launch_date         = $launch_date,
  p.policy_summary      = $policy_summary,
  p.key_features        = $key_features,
  p.source_url          = $source_url,
  p.data_confidence     = $data_confidence,
  p.source              = CASE WHEN p.source IS NULL OR p.source = 'botproject_seed' THEN 'botproject_seed' ELSE p.source END,
  p.updated_at          = datetime()
RETURN p.name AS name
"""

_MERGE_OFFERS_REL = """
MATCH (i:Insurer {name: $insurer_name})
MATCH (p:Product {name: $product_name})
MERGE (i)-[:OFFERS]->(p)
"""


# ── Core Logic ────────────────────────────────────────────────────────────────


def _build_product_params(
    product: Dict[str, Any],
    kg_insurer_name: str,
    category: str,
    product_type: str,
) -> Dict[str, Any]:
    """Convert a parsed SQL product dict into Neo4j MERGE params."""
    # Handle key_benefits — may be string or None
    key_benefits = product.get("key_benefits")
    if isinstance(key_benefits, str):
        # Split on periods or semicolons for list
        features = [s.strip() for s in key_benefits.split(".") if s.strip()]
        if len(features) <= 1:
            features = [key_benefits]
    elif isinstance(key_benefits, list):
        features = key_benefits
    else:
        features = []

    return {
        "name": product["product_name"],
        "insurer_name": kg_insurer_name,
        "category": category,
        "type": product_type,
        "uin": product.get("uin"),
        "product_scope": product.get("product_type"),  # individual/group/micro/standard
        "linked_type": product.get("linked_type"),
        "par_type": product.get("par_type"),
        "is_active": product.get("is_active", True),
        "launch_date": product.get("launch_date"),
        "policy_summary": product.get("policy_summary"),
        "key_features": features,
        "source_url": product.get("source_url"),
        "data_confidence": product.get("data_confidence"),
    }


async def seed_from_botproject(
    client: Neo4jClient,
    seed_dir: Optional[Path] = None,
) -> Dict[str, int]:
    """
    Parse botproject seed SQL files and merge into the Hibiscus KG.

    Args:
        client: Connected Neo4jClient instance.
        seed_dir: Path to botproject/seed/ directory. Defaults to auto-detect.

    Returns:
        Summary dict with counts of merged data.
    """
    # Auto-detect seed directory
    if seed_dir is None:
        candidates = [
            Path(__file__).parent / "sql",
            Path("/app/hibiscus/knowledge/graph/seed/sql"),
            Path("hibiscus/knowledge/graph/seed/sql"),
            Path("botproject/seed"),
        ]
        for candidate in candidates:
            if candidate.exists():
                seed_dir = candidate
                break

    if seed_dir is None or not seed_dir.exists():
        logger.info(
            "botproject_seed_skip",
            reason="botproject/seed/ directory not found — skipping botproject ingestion",
        )
        return {"skipped": True}

    logger.info("botproject_seed_start", seed_dir=str(seed_dir))

    # ── Step 1: Parse all SQL files ───────────────────────────────────────
    parsed = parse_all_seed_files(seed_dir)

    companies = parsed["companies"]
    products = parsed["products"]
    csr_entries = parsed["csr_entries"]

    # ── Step 2: Merge new insurers + enrich existing ──────────────────────
    # Build lookup of existing KG insurer names
    existing_insurers = set()
    try:
        result = await client.query(
            "MATCH (i:Insurer) RETURN i.name AS name",
            query_name="list_insurers",
            use_cache=False,
        )
        existing_insurers = {r["name"] for r in result}
    except Exception:
        logger.warning("botproject_seed_insurer_list_failed")

    new_insurer_params = []
    enrich_params = []

    for company in companies:
        kg_name = legal_to_kg(company["legal_name"])
        insurer_type = get_insurer_type_from_company_type(
            company["company_type"], company["sector"]
        )

        if kg_name in existing_insurers:
            # Enrich existing insurer with new fields
            enrich_params.append({
                "name": kg_name,
                "website": company.get("website"),
                "ceo_name": company.get("ceo_name"),
                "irdai_page_url": company.get("irdai_page_url"),
            })
        else:
            # Create new insurer
            new_insurer_params.append({
                "name": kg_name,
                "short_name": company["short_name"],
                "type": insurer_type,
                "irdai_reg_no": company.get("registration_number"),
                "headquarters": company.get("headquarters"),
                "established_year": company.get("established_year"),
                "website": company.get("website"),
                "ceo_name": company.get("ceo_name"),
                "irdai_page_url": company.get("irdai_page_url"),
            })

    new_insurers_ok = 0
    if new_insurer_params:
        new_insurers_ok = await client.execute_batch(
            _MERGE_NEW_INSURER,
            param_list=new_insurer_params,
            query_name="seed_new_insurers",
        )
        logger.info(
            "botproject_seed_new_insurers",
            succeeded=new_insurers_ok,
            total=len(new_insurer_params),
        )

    enrich_ok = 0
    if enrich_params:
        enrich_ok = await client.execute_batch(
            _ENRICH_INSURER,
            param_list=enrich_params,
            query_name="enrich_insurers",
        )
        logger.info(
            "botproject_seed_enrich_insurers",
            succeeded=enrich_ok,
            total=len(enrich_params),
        )

    # ── Step 3: Merge products ────────────────────────────────────────────
    # Deduplicate: if same product_name has different UINs, append UIN to name
    from collections import defaultdict

    name_uins: Dict[str, List[str]] = defaultdict(list)
    for product in products:
        uin = product.get("uin", "")
        name_uins[product["product_name"]].append(uin)

    # Names that have multiple different UINs
    ambiguous_names = {
        name
        for name, uins in name_uins.items()
        if len(set(uins)) > 1
    }

    product_params = []
    rel_params = []
    seen_names: set = set()

    for product in products:
        legal_name = product.get("legal_name", "")
        sub_category = product.get("sub_category", "")

        kg_insurer_name = legal_to_kg(legal_name)
        category, product_type = map_sub_category(sub_category)

        # Disambiguate products with same name but different UINs
        product_name = product["product_name"]
        if product_name in ambiguous_names and product.get("uin"):
            product_name = f"{product_name} ({product['uin']})"

        # Skip exact duplicates (same name after disambiguation)
        if product_name in seen_names:
            continue
        seen_names.add(product_name)

        product["product_name"] = product_name
        params = _build_product_params(product, kg_insurer_name, category, product_type)
        product_params.append(params)

        rel_params.append({
            "insurer_name": kg_insurer_name,
            "product_name": product_name,
        })

    products_ok = 0
    if product_params:
        products_ok = await client.execute_batch(
            _MERGE_BOTPROJECT_PRODUCT,
            param_list=product_params,
            query_name="seed_botproject_products",
        )
        logger.info(
            "botproject_seed_products",
            succeeded=products_ok,
            total=len(product_params),
        )

    rels_ok = 0
    if rel_params:
        rels_ok = await client.execute_batch(
            _MERGE_OFFERS_REL,
            param_list=rel_params,
            query_name="seed_botproject_offers",
        )
        logger.info(
            "botproject_seed_offers_rels",
            succeeded=rels_ok,
            total=len(rel_params),
        )

    # ── Step 4: CSR time-series ───────────────────────────────────────────
    # Remap company names to KG names in CSR entries
    for entry in csr_entries:
        entry["company_name"] = legal_to_kg(entry["company_name"])

    await seed_csr_entries(client, csr_entries)

    # ── Summary ───────────────────────────────────────────────────────────
    summary = {
        "new_insurers": new_insurers_ok,
        "enriched_insurers": enrich_ok,
        "products": products_ok,
        "offers_relationships": rels_ok,
        "csr_entries": len(csr_entries),
        "policy_documents_parsed": len(parsed.get("policy_documents", [])),
    }

    logger.info("botproject_seed_complete", **summary)
    return summary
