"""
IRDAI Product Registry Ingestion — 8,524 products with PDF links.

Parses 3 IRDAI CSV files (health, life, non-life), normalizes insurer names,
product types, dates, deduplicates by UIN, and seeds into Neo4j KG.

Usage:
    python -m hibiscus.scripts.ingest_irdai_registry [--dry-run] [--csv-dir PATH]
"""
import argparse
import asyncio
import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# A. Insurer Name Resolution
# ---------------------------------------------------------------------------

_NAME_MAP: Optional[Dict[str, Any]] = None
_NAME_MAP_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "data" / "insurer_name_map.json"


def _load_name_map() -> Dict[str, Any]:
    global _NAME_MAP
    if _NAME_MAP is not None:
        return _NAME_MAP
    with open(_NAME_MAP_PATH) as f:
        _NAME_MAP = json.load(f)
    return _NAME_MAP


def _clean_insurer_name(raw: str) -> str:
    """Strip tabs, quotes, extra whitespace from corrupt CSV rows."""
    cleaned = raw.replace("\t", " ").strip().strip('"').strip("'").strip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned


def resolve_insurer_name(raw: str) -> str:
    """Resolve a raw CSV insurer name to its KG canonical name."""
    if not raw or not raw.strip():
        return ""
    cleaned = _clean_insurer_name(raw)
    name_map = _load_name_map()
    mappings = name_map.get("mappings", {})

    # Exact match in JSON map
    if cleaned in mappings:
        return mappings[cleaned]

    # Try with leading quote stripped (some CSV rows have stray quotes)
    stripped = cleaned.lstrip('"').strip()
    if stripped in mappings:
        return mappings[stripped]

    # Fallback to name_mapper.legal_to_kg
    try:
        from hibiscus.knowledge.graph.seed.name_mapper import legal_to_kg
        return legal_to_kg(cleaned)
    except ImportError:
        return cleaned


# ---------------------------------------------------------------------------
# B. Product Type Normalization
# ---------------------------------------------------------------------------

_HEALTH_TYPE_MAP = {
    "individual": "Individual",
    "group": "Group",
    "add-on": "Add-on",
    "add on": "Add-on",
    "addon": "Add-on",
    "rider": "Rider",
    "micro": "Micro",
    "micro individual": "Micro",
    "micro group": "Micro",
    "retail": "Retail",
    "revision": "Revision",
    "new": "New",
    "health": "Individual",
    "heath": "Individual",
    "health individual": "Individual",
    "group health": "Group",
    "group health rider": "Rider",
    "group rider": "Rider",
    "group health rider ": "Rider",
    "csc": "CSC",
    "ulip": "Individual",
}


def normalize_health_type(raw: str) -> str:
    if not raw or not raw.strip():
        return "Individual"
    cleaned = raw.strip().lower()
    # If value looks like a filename (contains .pdf), default
    if ".pdf" in cleaned or cleaned.startswith("20"):
        return "Individual"
    return _HEALTH_TYPE_MAP.get(cleaned, "Individual")


_LIFE_TYPE_MAP = {
    "ulip": "ULIP",
    "linked": "ULIP",
    "non-ulip": "Non-ULIP",
    "non ulip": "Non-ULIP",
    "non- ulip": "Non-ULIP",
    "non-linked": "Non-ULIP",
    "non linked": "Non-ULIP",
    "group": "Non-ULIP",
    "यूलिप": "ULIP",
    "गैर यूलिप": "Non-ULIP",
    "गैर लिंक्ड": "Non-ULIP",
}


def normalize_life_type(raw: str) -> str:
    if not raw or not raw.strip():
        return "Non-ULIP"
    cleaned = raw.strip().lower()
    # Check for UIN-like values that leaked into type column
    if re.match(r"^\d+[A-Z]", raw.strip()):
        return "Non-ULIP"
    return _LIFE_TYPE_MAP.get(cleaned, _LIFE_TYPE_MAP.get(raw.strip(), "Non-ULIP"))


_NONLIFE_TYPE_MAP = {
    "main product": "Main Product",
    "main produc": "Main Product",
    "add-on": "Add-on",
    "add on": "Add-on",
    "addon": "Add-on",
    "revision": "Revision",
    "general": "Main Product",
    "मुख्य उत्पाद": "Main Product",
    "ऐड ऑन": "Add-on",
    "ऐड-ऑन": "Add-on",
}


def normalize_nonlife_type(raw: str) -> str:
    if not raw or not raw.strip():
        return "Main Product"
    cleaned = raw.strip().lower()
    # If it looks like a truncated description or special value, default
    if len(cleaned) > 30 or cleaned.startswith('"'):
        return "Add-on"
    result = _NONLIFE_TYPE_MAP.get(cleaned)
    if result:
        return result
    result = _NONLIFE_TYPE_MAP.get(raw.strip())
    if result:
        return result
    # Partial match
    if "add" in cleaned:
        return "Add-on"
    if "main" in cleaned:
        return "Main Product"
    if "revision" in cleaned:
        return "Revision"
    return "Main Product"


# ---------------------------------------------------------------------------
# C. Non-Life Sub-Categorization
# ---------------------------------------------------------------------------

_MOTOR_KEYWORDS = [
    "motor", "vehicle", "car ", "two wheeler", "two-wheeler", "bike",
    "scooter", "commercial vehicle", "private car", "own damage",
    "third party", "gcv", "pcv", "wheeler", "automobile",
    "tractor", "taxi", "auto rickshaw", "e-rickshaw",
    "package policy", "bundled cover", "long term",
]
_TRAVEL_KEYWORDS = [
    "travel", "overseas", "visa", "trip", "journey", "tourist",
    "baggage", "passport", "flight",
]
_PA_KEYWORDS = [
    "personal accident", "pa ", "pa-", "accident benefit",
    "accidental death", "janata personal", "group personal",
]
_FIRE_KEYWORDS = [
    "fire", "special perils", "sfsp", "standard fire",
    "bharat griha", "bharat laghu", "bharat sookshma",
    "dwelling", "householder", "shopkeeper",
]
_MARINE_KEYWORDS = [
    "marine", "cargo", "hull", "inland transit",
    "open cover", "warehouse",
]
_LIABILITY_KEYWORDS = [
    "liability", "professional indemnity", "d&o", "directors",
    "errors & omissions", "e&o", "public liability",
    "product liability", "workmen", "workers compensation",
    "employer", "fidelity",
]
_ENGINEERING_KEYWORDS = [
    "engineering", "contractor", "erection", "machinery breakdown",
    "boiler", "pressure plant", "electronic equipment",
    "car insurance" if False else "contractors all risk",
    "cpm", "eei", "mbd", "iar",
]
_CROP_KEYWORDS = [
    "crop", "weather", "cattle", "livestock", "agriculture",
    "pradhan mantri fasal", "pmfby", "horticulture",
    "poultry", "aquaculture", "sericulture",
]
_HEALTH_KEYWORDS = [
    "health", "mediclaim", "critical illness", "hospital",
    "surgical", "cancer", "dengue", "corona", "covid",
    "hospicash", "super top up", "top-up",
]


def classify_nonlife_subcategory(product_name: str, uin: str) -> str:
    name_lower = (product_name or "").lower()
    uin_upper = (uin or "").upper()

    # UIN prefix patterns
    if uin_upper:
        # Health UINs from general insurers
        if "HL" in uin_upper[:20] or "PA" in uin_upper[:20]:
            if "PA" in uin_upper[:20]:
                return "pa"
            return "health"

    # Keyword matching (order matters — more specific first)
    for kw in _MOTOR_KEYWORDS:
        if kw in name_lower:
            return "motor"
    for kw in _TRAVEL_KEYWORDS:
        if kw in name_lower:
            return "travel"
    for kw in _PA_KEYWORDS:
        if kw in name_lower:
            return "pa"
    for kw in _HEALTH_KEYWORDS:
        if kw in name_lower:
            return "health"
    for kw in _FIRE_KEYWORDS:
        if kw in name_lower:
            return "fire"
    for kw in _MARINE_KEYWORDS:
        if kw in name_lower:
            return "marine"
    for kw in _LIABILITY_KEYWORDS:
        if kw in name_lower:
            return "liability"
    for kw in _ENGINEERING_KEYWORDS:
        if kw in name_lower:
            return "engineering"
    for kw in _CROP_KEYWORDS:
        if kw in name_lower:
            return "crop"

    # Cyber, burglary, money, aviation → misc
    return "misc"


# ---------------------------------------------------------------------------
# D. Date Parsing
# ---------------------------------------------------------------------------

def parse_life_date(raw: str) -> Optional[str]:
    """Parse life insurance dates like '2018-06-0404-06-2018' → '2018-06-04'."""
    if not raw or raw.strip() in ("", "----", "---", "--", "-"):
        return None
    cleaned = raw.strip()
    # Take first 10 chars if duplicated date pattern
    if len(cleaned) >= 20 and re.match(r"\d{4}-\d{2}-\d{2}", cleaned[:10]):
        return cleaned[:10]
    return parse_date(cleaned)


def parse_date(raw: str) -> Optional[str]:
    """Try multiple date formats, return YYYY-MM-DD or None."""
    if not raw or raw.strip() in ("", "----", "---", "--", "-"):
        return None
    cleaned = raw.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(cleaned, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Last resort: try first 10 chars
    if len(cleaned) >= 10:
        return parse_date(cleaned[:10])
    return None


# ---------------------------------------------------------------------------
# E. CSV Parsers
# ---------------------------------------------------------------------------

def _read_csv(path: Path) -> List[Dict[str, str]]:
    """Read CSV with flexible handling of messy data."""
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def parse_health_csv(path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Parse IRDAI health insurance CSV. Returns (products, stats)."""
    rows = _read_csv(path)
    products = []
    stats = {"total": len(rows), "skipped": 0, "type_fixes": 0, "name_fixes": 0}

    for row in rows:
        uin = (row.get("UIN") or "").strip()
        product_name = (row.get("Product Name") or "").strip()

        if not product_name and not uin:
            stats["skipped"] += 1
            continue

        raw_insurer = row.get("Name of the Insurer", "")
        canonical = resolve_insurer_name(raw_insurer)
        if canonical != _clean_insurer_name(raw_insurer):
            stats["name_fixes"] += 1

        raw_type = (row.get("Type Of Product") or "").strip()
        sub_type = normalize_health_type(raw_type)
        if sub_type != raw_type:
            stats["type_fixes"] += 1

        doc_link = (row.get("document_link") or "").strip()
        fy = (row.get("Financial Year") or "").strip()
        approval_date = parse_date((row.get("Date of Approval") or "").strip())

        products.append({
            "uin": uin,
            "product_name": product_name,
            "insurer_canonical": canonical,
            "category": "health",
            "sub_type": sub_type,
            "approval_date": approval_date,
            "financial_year": fy,
            "document_link": doc_link,
            "is_active": True,
            "status": "active",
        })

    return products, stats


def parse_life_csv(path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Parse IRDAI life insurance CSV. Returns (products, stats)."""
    rows = _read_csv(path)
    products = []
    stats = {"total": len(rows), "skipped": 0, "type_fixes": 0, "name_fixes": 0}

    for row in rows:
        uin = (row.get("UIN") or "").strip()
        product_name = (row.get("Product Name") or "").strip()

        if not product_name and not uin:
            stats["skipped"] += 1
            continue

        raw_insurer = row.get("Name of the Insurer", "")
        canonical = resolve_insurer_name(raw_insurer)
        if canonical != _clean_insurer_name(raw_insurer):
            stats["name_fixes"] += 1

        raw_type = (row.get("Type Of Product") or "").strip()
        sub_type = normalize_life_type(raw_type)
        if sub_type != raw_type:
            stats["type_fixes"] += 1

        launch_date = parse_life_date(
            (row.get("Date Of Launch/Effecting Modification") or "").strip()
        )
        close_date = parse_life_date(
            (row.get("Date Of Closing / Withdrawal") or "").strip()
        )

        protection_or_savings = (row.get("Protection/ Savings/ Retirement") or "").strip() or None
        par_or_nonpar = (row.get("Par/Non-par") or "").strip() or None
        individual_or_group = (row.get("Individual/Group") or "").strip() or None

        doc_link = (row.get("document_link") or "").strip()
        fy = (row.get("Financial Year") or "").strip()

        is_active = close_date is None
        status = "active" if is_active else "discontinued"

        products.append({
            "uin": uin,
            "product_name": product_name,
            "insurer_canonical": canonical,
            "category": "life",
            "sub_type": sub_type,
            "approval_date": launch_date,
            "financial_year": fy,
            "document_link": doc_link,
            "is_active": is_active,
            "status": status,
            "launch_date": launch_date,
            "close_date": close_date,
            "protection_or_savings": protection_or_savings,
            "par_or_nonpar": par_or_nonpar,
            "individual_or_group": individual_or_group,
        })

    return products, stats


def parse_nonlife_csv(path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Parse IRDAI non-life insurance CSV. Returns (products, stats)."""
    rows = _read_csv(path)
    products = []
    stats = {"total": len(rows), "skipped": 0, "type_fixes": 0, "name_fixes": 0}

    for row in rows:
        uin = (row.get("UIN") or "").strip()
        product_name = (row.get("Product Name") or "").strip()

        if not product_name and not uin:
            stats["skipped"] += 1
            continue

        raw_insurer = row.get("Name of the Insurer", "")
        canonical = resolve_insurer_name(raw_insurer)
        if canonical != _clean_insurer_name(raw_insurer):
            stats["name_fixes"] += 1

        raw_type = (row.get("Type Of Product") or "").strip()
        sub_type = normalize_nonlife_type(raw_type)
        if sub_type != raw_type:
            stats["type_fixes"] += 1

        sub_category = classify_nonlife_subcategory(product_name, uin)

        doc_link = (row.get("document_link") or "").strip()
        fy = (row.get("Financial Year") or "").strip()
        approval_date = parse_date((row.get("Date of Approval") or "").strip())

        products.append({
            "uin": uin,
            "product_name": product_name,
            "insurer_canonical": canonical,
            "category": sub_category,
            "sub_type": sub_type,
            "approval_date": approval_date,
            "financial_year": fy,
            "document_link": doc_link,
            "is_active": True,
            "status": "active",
        })

    return products, stats


# ---------------------------------------------------------------------------
# F. Deduplication
# ---------------------------------------------------------------------------

def deduplicate_products(
    all_products: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str, str]]]:
    """
    Group by UIN, mark latest financial_year as active, older as superseded.
    Returns (deduped_products, revision_pairs).
    """
    # Group products with UINs
    uin_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    no_uin: List[Dict[str, Any]] = []

    for p in all_products:
        uin = p.get("uin", "").strip()
        if uin:
            uin_groups[uin].append(p)
        else:
            no_uin.append(p)

    deduped = []
    revision_pairs: List[Tuple[str, str, str, str]] = []

    for uin, group in uin_groups.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        # Sort by financial_year descending (heuristic: longer string or lexicographic)
        group.sort(key=lambda x: x.get("financial_year", ""), reverse=True)

        # Latest is active, rest are superseded
        latest = group[0]
        latest["is_active"] = True
        latest["status"] = "active" if latest.get("status") != "discontinued" else "discontinued"
        deduped.append(latest)

        for older in group[1:]:
            older["is_active"] = False
            older["status"] = "superseded"
            deduped.append(older)
            revision_pairs.append((
                latest["product_name"],
                latest.get("uin", ""),
                older["product_name"],
                older.get("uin", ""),
            ))

    # Handle no-UIN products
    deduped.extend(no_uin)

    # Disambiguate product names
    name_counts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in deduped:
        name_counts[p["product_name"]].append(p)

    for name, group in name_counts.items():
        if len(group) <= 1:
            continue
        # Check if they have different UINs
        uins = {p.get("uin", "") for p in group}
        if len(uins) > 1:
            for p in group:
                if p.get("uin"):
                    p["product_name"] = f"{p['product_name']} ({p['uin']})"
                else:
                    insurer = p.get("insurer_canonical", "")
                    p["product_name"] = f"{p['product_name']} [{insurer}]"
        else:
            # Same UIN, same name — keep first only
            for p in group[1:]:
                p["_skip"] = True

    final = [p for p in deduped if not p.get("_skip")]
    return final, revision_pairs


# ---------------------------------------------------------------------------
# G. Cypher Queries
# ---------------------------------------------------------------------------

_MERGE_PRODUCT = """
MERGE (p:Product {name: $name})
SET
  p.uin                   = $uin,
  p.insurer_name          = COALESCE(p.insurer_name, $insurer_name),
  p.category              = COALESCE(p.category, $category),
  p.type                  = COALESCE(p.type, $type),
  p.sub_category          = COALESCE(p.sub_category, $sub_category),
  p.irdai_approval_date   = $approval_date,
  p.financial_year        = $financial_year,
  p.is_active             = $is_active,
  p.status                = $status,
  p.protection_or_savings = COALESCE(p.protection_or_savings, $protection_or_savings),
  p.par_or_nonpar         = COALESCE(p.par_or_nonpar, $par_or_nonpar),
  p.individual_or_group   = COALESCE(p.individual_or_group, $individual_or_group),
  p.launch_date           = COALESCE(p.launch_date, $launch_date),
  p.close_date            = $close_date,
  p.source                = CASE WHEN p.source IS NULL THEN 'irdai_registry' ELSE p.source END,
  p.irdai_source          = 'irdai_registry',
  p.data_confidence       = COALESCE(p.data_confidence, 'official'),
  p.updated_at            = datetime()
RETURN p.name AS name
"""

_MERGE_INSURER = """
MERGE (i:Insurer {name: $name})
SET
  i.source     = CASE WHEN i.source IS NULL THEN 'irdai_registry' ELSE i.source END,
  i.updated_at = datetime()
RETURN i.name AS name
"""

_MERGE_POLICY_DOCUMENT = """
MERGE (d:PolicyDocument {uin: $uin, title: $title})
SET
  d.doc_type    = 'irdai_filing',
  d.url         = $url,
  d.source_name = 'IRDAI Product Registry',
  d.updated_at  = datetime()
RETURN d.title AS title
"""

_MERGE_OFFERS_REL = """
MATCH (i:Insurer {name: $insurer_name})
MATCH (p:Product {name: $product_name})
MERGE (i)-[:OFFERS]->(p)
"""

_MERGE_HAS_DOCUMENT_REL = """
MATCH (p:Product) WHERE p.uin = $uin
MATCH (d:PolicyDocument {uin: $uin, title: $title})
MERGE (p)-[:HAS_DOCUMENT]->(d)
"""

_MERGE_SUPERSEDES_REL = """
MATCH (newer:Product {name: $newer_name})
MATCH (older:Product {name: $older_name})
MERGE (newer)-[:SUPERSEDES]->(older)
"""


# ---------------------------------------------------------------------------
# H. Seeding Functions
# ---------------------------------------------------------------------------

BATCH_SIZE = 500


def _build_product_params(product: Dict[str, Any]) -> Dict[str, Any]:
    """Build Neo4j parameters for a product MERGE."""
    return {
        "name": product["product_name"],
        "uin": product.get("uin") or None,
        "insurer_name": product.get("insurer_canonical") or None,
        "category": product.get("category") or None,
        "type": product.get("sub_type") or None,
        "sub_category": product.get("category") or None,
        "approval_date": product.get("approval_date") or None,
        "financial_year": product.get("financial_year") or None,
        "is_active": product.get("is_active", True),
        "status": product.get("status", "active"),
        "protection_or_savings": product.get("protection_or_savings") or None,
        "par_or_nonpar": product.get("par_or_nonpar") or None,
        "individual_or_group": product.get("individual_or_group") or None,
        "launch_date": product.get("launch_date") or None,
        "close_date": product.get("close_date") or None,
    }


async def seed_irdai_products(client: Any, products: List[Dict[str, Any]]) -> int:
    """Batch MERGE products into Neo4j."""
    params_list = [_build_product_params(p) for p in products]
    total = 0
    for i in range(0, len(params_list), BATCH_SIZE):
        batch = params_list[i : i + BATCH_SIZE]
        count = await client.execute_batch(
            _MERGE_PRODUCT, param_list=batch, query_name="seed_irdai_products"
        )
        total += count
    return total


async def seed_irdai_insurers(client: Any, insurer_names: List[str]) -> int:
    """MERGE any new Insurer nodes discovered from IRDAI CSVs."""
    params_list = [{"name": name} for name in insurer_names if name]
    total = 0
    for i in range(0, len(params_list), BATCH_SIZE):
        batch = params_list[i : i + BATCH_SIZE]
        count = await client.execute_batch(
            _MERGE_INSURER, param_list=batch, query_name="seed_irdai_insurers"
        )
        total += count
    return total


async def seed_irdai_documents(client: Any, products: List[Dict[str, Any]]) -> int:
    """Batch MERGE PolicyDocument nodes for products with PDF links."""
    params_list = []
    for p in products:
        doc_link = p.get("document_link", "").strip()
        uin = (p.get("uin") or "").strip()
        if doc_link and uin:
            params_list.append({
                "uin": uin,
                "title": f"IRDAI Filing - {p['product_name']}",
                "url": doc_link,
            })
    total = 0
    for i in range(0, len(params_list), BATCH_SIZE):
        batch = params_list[i : i + BATCH_SIZE]
        count = await client.execute_batch(
            _MERGE_POLICY_DOCUMENT, param_list=batch, query_name="seed_irdai_documents"
        )
        total += count
    return total


async def seed_irdai_relationships(
    client: Any,
    products: List[Dict[str, Any]],
    revision_pairs: List[Tuple[str, str, str, str]],
) -> Dict[str, int]:
    """Create OFFERS, HAS_DOCUMENT, and SUPERSEDES relationships."""
    # OFFERS
    offers_params = [
        {"insurer_name": p["insurer_canonical"], "product_name": p["product_name"]}
        for p in products
        if p.get("insurer_canonical")
    ]
    offers_ok = 0
    for i in range(0, len(offers_params), BATCH_SIZE):
        batch = offers_params[i : i + BATCH_SIZE]
        offers_ok += await client.execute_batch(
            _MERGE_OFFERS_REL, param_list=batch, query_name="seed_irdai_offers"
        )

    # HAS_DOCUMENT
    doc_params = []
    for p in products:
        doc_link = p.get("document_link", "").strip()
        uin = (p.get("uin") or "").strip()
        if doc_link and uin:
            doc_params.append({
                "uin": uin,
                "title": f"IRDAI Filing - {p['product_name']}",
            })
    docs_ok = 0
    for i in range(0, len(doc_params), BATCH_SIZE):
        batch = doc_params[i : i + BATCH_SIZE]
        docs_ok += await client.execute_batch(
            _MERGE_HAS_DOCUMENT_REL, param_list=batch, query_name="seed_irdai_has_doc"
        )

    # SUPERSEDES
    supersedes_params = [
        {"newer_name": pair[0], "older_name": pair[2]}
        for pair in revision_pairs
    ]
    supersedes_ok = 0
    for i in range(0, len(supersedes_params), BATCH_SIZE):
        batch = supersedes_params[i : i + BATCH_SIZE]
        supersedes_ok += await client.execute_batch(
            _MERGE_SUPERSEDES_REL, param_list=batch, query_name="seed_irdai_supersedes"
        )

    return {
        "offers": offers_ok,
        "has_document": docs_ok,
        "supersedes": supersedes_ok,
    }


# ---------------------------------------------------------------------------
# I. Report
# ---------------------------------------------------------------------------

def print_report(
    products: List[Dict[str, Any]],
    revision_pairs: List[Tuple[str, str, str, str]],
    stats: Dict[str, Dict[str, int]],
) -> None:
    """Print summary report of ingestion results."""
    print("\n" + "=" * 70)
    print("IRDAI PRODUCT REGISTRY — INGESTION REPORT")
    print("=" * 70)

    # Products per category
    cat_counts: Dict[str, int] = defaultdict(int)
    for p in products:
        cat_counts[p.get("category", "unknown")] += 1
    print(f"\n{'Category':<20} {'Count':>8}")
    print("-" * 30)
    for cat in sorted(cat_counts, key=lambda x: cat_counts[x], reverse=True):
        print(f"  {cat:<18} {cat_counts[cat]:>8}")
    print(f"  {'TOTAL':<18} {len(products):>8}")

    # Unique insurers
    insurers = {p.get("insurer_canonical", "") for p in products if p.get("insurer_canonical")}
    print(f"\nUnique canonical insurers: {len(insurers)}")

    # PDF links
    with_links = sum(1 for p in products if p.get("document_link"))
    print(f"Products with PDF links: {with_links}")

    # Active vs discontinued vs superseded
    active = sum(1 for p in products if p.get("status") == "active")
    discontinued = sum(1 for p in products if p.get("status") == "discontinued")
    superseded = sum(1 for p in products if p.get("status") == "superseded")
    print(f"\nActive: {active}  |  Discontinued: {discontinued}  |  Superseded: {superseded}")

    # Financial year distribution
    fy_counts: Dict[str, int] = defaultdict(int)
    for p in products:
        fy = p.get("financial_year", "unknown")
        if fy:
            fy_counts[fy] += 1
    print("\nProducts per financial year (top 10):")
    for fy in sorted(fy_counts, key=lambda x: fy_counts[x], reverse=True)[:10]:
        print(f"  {fy:<20} {fy_counts[fy]:>6}")

    # SUPERSEDES
    print(f"\nSUPERSEDES relationships: {len(revision_pairs)}")

    # Data quality
    print("\nData quality:")
    for source, s in stats.items():
        print(f"  {source}: total={s['total']}, skipped={s['skipped']}, "
              f"name_fixes={s['name_fixes']}, type_fixes={s['type_fixes']}")

    print("=" * 70)


# ---------------------------------------------------------------------------
# J. Entry Point
# ---------------------------------------------------------------------------

def _find_csv_dir() -> Optional[Path]:
    """Auto-detect CSV directory."""
    candidates = [
        Path("Seed"),
        Path("hibiscus/Seed"),
        Path("/app/Seed"),
        Path("/app/hibiscus/Seed"),
    ]
    for c in candidates:
        if c.exists() and any(c.glob("irdai_*.csv")):
            return c
    return None


async def main(csv_dir: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
    """
    Main ingestion pipeline.

    Args:
        csv_dir: Path to directory containing IRDAI CSV files.
        dry_run: If True, parse and report without writing to Neo4j.
    """
    # Resolve CSV directory
    if csv_dir:
        csv_path = Path(csv_dir)
    else:
        csv_path = _find_csv_dir()
    if csv_path is None or not csv_path.exists():
        print("ERROR: CSV directory not found. Tried auto-detection. Use --csv-dir.")
        return {"error": "csv_dir_not_found"}

    print(f"CSV directory: {csv_path}")

    # Parse all three CSVs
    health_path = csv_path / "irdai_health_insurance_data.csv"
    life_path = csv_path / "irdai_life_insurance_data.csv"
    nonlife_path = csv_path / "irdai_non_life_insurance_data.csv"

    all_products: List[Dict[str, Any]] = []
    all_stats: Dict[str, Dict[str, int]] = {}

    if health_path.exists():
        print("Parsing health CSV...")
        products, stats = parse_health_csv(health_path)
        all_products.extend(products)
        all_stats["health"] = stats
        print(f"  → {len(products)} health products ({stats['skipped']} skipped)")
    else:
        print(f"WARNING: {health_path} not found")

    if life_path.exists():
        print("Parsing life CSV...")
        products, stats = parse_life_csv(life_path)
        all_products.extend(products)
        all_stats["life"] = stats
        print(f"  → {len(products)} life products ({stats['skipped']} skipped)")
    else:
        print(f"WARNING: {life_path} not found")

    if nonlife_path.exists():
        print("Parsing non-life CSV...")
        products, stats = parse_nonlife_csv(nonlife_path)
        all_products.extend(products)
        all_stats["nonlife"] = stats
        print(f"  → {len(products)} non-life products ({stats['skipped']} skipped)")
    else:
        print(f"WARNING: {nonlife_path} not found")

    # Deduplicate
    print(f"\nDeduplicating {len(all_products)} products...")
    deduped, revision_pairs = deduplicate_products(all_products)
    print(f"  → {len(deduped)} after dedup, {len(revision_pairs)} revision pairs")

    # Collect unique insurers
    insurer_names = sorted({
        p["insurer_canonical"]
        for p in deduped
        if p.get("insurer_canonical")
    })
    print(f"  → {len(insurer_names)} unique canonical insurers")

    # Report
    print_report(deduped, revision_pairs, all_stats)

    if dry_run:
        print("\n[DRY RUN] No data written to Neo4j.")
        return {
            "products": len(deduped),
            "insurers": len(insurer_names),
            "revision_pairs": len(revision_pairs),
            "dry_run": True,
        }

    # Seed to Neo4j
    print("\nConnecting to Neo4j...")
    from hibiscus.knowledge.graph.client import Neo4jClient

    client = Neo4jClient()
    await client.connect()

    try:
        print("Seeding insurers...")
        insurers_ok = await seed_irdai_insurers(client, insurer_names)
        print(f"  → {insurers_ok} insurers merged")

        print("Seeding products...")
        products_ok = await seed_irdai_products(client, deduped)
        print(f"  → {products_ok} products merged")

        print("Seeding policy documents...")
        docs_ok = await seed_irdai_documents(client, deduped)
        print(f"  → {docs_ok} documents merged")

        print("Seeding relationships...")
        rel_counts = await seed_irdai_relationships(client, deduped, revision_pairs)
        print(f"  → OFFERS: {rel_counts['offers']}, HAS_DOCUMENT: {rel_counts['has_document']}, "
              f"SUPERSEDES: {rel_counts['supersedes']}")

        return {
            "products": products_ok,
            "insurers": insurers_ok,
            "documents": docs_ok,
            **rel_counts,
        }
    finally:
        await client.close()


def _main() -> None:
    """CLI entry point with argparse."""
    parser = argparse.ArgumentParser(
        description="Ingest IRDAI Product Registry into Neo4j KG"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report without writing to Neo4j",
    )
    parser.add_argument(
        "--csv-dir",
        type=str,
        default=None,
        help="Path to directory containing IRDAI CSV files",
    )
    args = parser.parse_args()
    asyncio.run(main(csv_dir=args.csv_dir, dry_run=args.dry_run))


if __name__ == "__main__":
    _main()
