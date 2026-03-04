"""
🌺 Hibiscus v0.9 | EAZR AI Insurance Intelligence Engine
KG seed: SQL parser — extracts insurer/product data from legacy botproject SQL dumps.
Copyright (c) 2026 EAZR Digipayments Pvt Ltd. All rights reserved.
"""
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from hibiscus.observability.logger import get_logger

logger = get_logger("hibiscus.kg.seed.botproject_parser")


# ── SQL Value Parsing Helpers ─────────────────────────────────────────────────


def _unescape_sql_string(s: str) -> str:
    """Unescape SQL single-quoted strings ('' → ')."""
    return s.replace("''", "'")


def _parse_sql_value(val: str) -> Any:
    """Parse a single SQL value token into a Python value."""
    val = val.strip()
    if val.upper() == "NULL":
        return None
    if val.upper() == "TRUE":
        return True
    if val.upper() == "FALSE":
        return False
    # Quoted string
    if val.startswith("'") and val.endswith("'"):
        return _unescape_sql_string(val[1:-1])
    # Numeric
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


# ── Categories & Sub-Categories ───────────────────────────────────────────────


def parse_categories(sql_text: str) -> Dict[int, str]:
    """
    Parse insurance_categories from 01_foundation.sql.
    Returns {category_id: category_name} — IDs are 1-indexed in insertion order.
    """
    # Match the multi-row VALUES block for categories
    pattern = re.compile(
        r"INSERT INTO insurance\.insurance_categories\s*\([^)]+\)\s*VALUES\s*\n((?:\s*\([^;]+;))",
        re.DOTALL,
    )
    match = pattern.search(sql_text)
    if not match:
        logger.warning("parse_categories_no_match")
        return {}

    block = match.group(1)
    # Each row: ('name', 'description', 'code'|NULL, ARRAY[...])
    row_pattern = re.compile(r"\(\s*'([^']*(?:''[^']*)*)'")
    categories = {}
    for idx, m in enumerate(row_pattern.finditer(block), start=1):
        categories[idx] = _unescape_sql_string(m.group(1))

    logger.info("parse_categories_complete", count=len(categories))
    return categories


def parse_sub_categories(sql_text: str) -> Dict[int, Dict[str, Any]]:
    """
    Parse insurance_sub_categories from 01_foundation.sql.
    Returns {sub_category_id: {"name": str, "category_id": int, "description": str}}.
    IDs are 1-indexed across ALL inserts in order.
    """
    # Find all sub-category INSERT blocks
    pattern = re.compile(
        r"INSERT INTO insurance\.insurance_sub_categories\s*\(category_id,\s*name,\s*description\)\s*VALUES\s*\n((?:.*?);)",
        re.DOTALL,
    )

    sub_categories = {}
    idx = 1
    for match in pattern.finditer(sql_text):
        block = match.group(1)
        # Each row: (category_id, 'name', 'description')
        row_pattern = re.compile(
            r"\(\s*(\d+)\s*,\s*'([^']*(?:''[^']*)*)'\s*,\s*'([^']*(?:''[^']*)*)'\s*\)"
        )
        for row in row_pattern.finditer(block):
            cat_id = int(row.group(1))
            name = _unescape_sql_string(row.group(2))
            desc = _unescape_sql_string(row.group(3))
            sub_categories[idx] = {
                "name": name,
                "category_id": cat_id,
                "description": desc,
            }
            idx += 1

    logger.info("parse_sub_categories_complete", count=len(sub_categories))
    return sub_categories


# ── Companies ─────────────────────────────────────────────────────────────────


def parse_companies(sql_text: str) -> List[Dict[str, Any]]:
    """
    Parse insurance_companies from 01_foundation.sql.
    Returns list of company dicts.
    """
    # Match all multi-row company INSERT blocks
    pattern = re.compile(
        r"INSERT INTO insurance\.insurance_companies\s*\([^)]+\)\s*VALUES\s*\n((?:.*?);)",
        re.DOTALL,
    )

    companies = []
    for match in pattern.finditer(sql_text):
        block = match.group(1)
        # Each row is a tuple. Parse with regex that handles quoted strings with commas.
        row_pattern = re.compile(
            r"\(\s*'([^']*(?:''[^']*)*)'\s*,"  # legal_name
            r"\s*'([^']*(?:''[^']*)*)'\s*,"      # short_name
            r"\s*'([^']*)'\s*,"                    # registration_number
            r"\s*'([^']*)'\s*,"                    # company_type
            r"\s*'([^']*)'\s*,"                    # sector
            r"\s*(?:'([^']*(?:''[^']*)*)'|NULL)\s*,"  # ceo_name (nullable)
            r"\s*'([^']*(?:''[^']*)*)'\s*,"      # website
            r"\s*'([^']*(?:''[^']*)*)'\s*,"      # irdai_page_url
            r"\s*'([^']*)'\s*,"                    # headquarters
            r"\s*(\d+)\s*,"                        # established_year
            r"\s*'([^']*)'\s*\)"                   # data_confidence
        )

        for row in row_pattern.finditer(block):
            companies.append({
                "legal_name": _unescape_sql_string(row.group(1)),
                "short_name": _unescape_sql_string(row.group(2)),
                "registration_number": row.group(3),
                "company_type": row.group(4),
                "sector": row.group(5),
                "ceo_name": _unescape_sql_string(row.group(6)) if row.group(6) else None,
                "website": _unescape_sql_string(row.group(7)),
                "irdai_page_url": _unescape_sql_string(row.group(8)),
                "headquarters": row.group(9),
                "established_year": int(row.group(10)),
                "data_confidence": row.group(11),
            })

    logger.info("parse_companies_complete", count=len(companies))
    return companies


# ── Products (cross-join INSERT pattern) ──────────────────────────────────────


def parse_products(sql_text: str) -> List[Dict[str, Any]]:
    """
    Parse insurance_products from product SQL files (02, 03, 04).
    Handles the cross-join INSERT..SELECT pattern:
        INSERT INTO insurance.insurance_products (cols...)
        SELECT c.id, sc.id, 'product_name', 'uin', ...
        FROM insurance.insurance_companies c, insurance.insurance_sub_categories sc
        WHERE c.legal_name = 'X' AND sc.name = 'Y';
    """
    products = []

    # Split on each INSERT INTO insurance.insurance_products
    insert_blocks = re.split(
        r"(?=INSERT INTO insurance\.insurance_products\s*\()",
        sql_text,
    )

    for block in insert_blocks:
        if not block.strip().startswith("INSERT INTO insurance.insurance_products"):
            continue

        # Extract column list
        col_match = re.search(
            r"INSERT INTO insurance\.insurance_products\s*\(([^)]+)\)",
            block,
        )
        if not col_match:
            continue
        columns = [c.strip() for c in col_match.group(1).split(",")]

        # Extract SELECT values and WHERE clause
        select_match = re.search(
            r"SELECT\s+c\.id\s*,\s*sc\.id\s*,\s*(.*?)FROM\s+insurance\.insurance_companies",
            block,
            re.DOTALL,
        )
        if not select_match:
            continue

        values_str = select_match.group(1).strip().rstrip(",")

        # Extract WHERE clause
        where_match = re.search(
            r"WHERE\s+c\.legal_name\s*=\s*'([^']*(?:''[^']*)*)'"
            r"\s+AND\s+sc\.name\s*=\s*'([^']*(?:''[^']*)*)'\s*;",
            block,
        )
        if not where_match:
            continue

        legal_name = _unescape_sql_string(where_match.group(1))
        sub_category = _unescape_sql_string(where_match.group(2))

        # Parse the SELECT values (skip first 2 cols which are c.id, sc.id)
        value_columns = columns[2:]  # Skip company_id, sub_category_id
        values = _parse_select_values(values_str)

        if len(values) < len(value_columns):
            logger.warning(
                "parse_product_value_count_mismatch",
                legal_name=legal_name,
                expected=len(value_columns),
                got=len(values),
            )
            continue

        product = {
            "legal_name": legal_name,
            "sub_category": sub_category,
        }
        for i, col in enumerate(value_columns):
            if i < len(values):
                product[col] = values[i]

        products.append(product)

    logger.info("parse_products_complete", count=len(products))
    return products


def _parse_select_values(values_str: str) -> List[Any]:
    """
    Parse a comma-separated list of SQL values from a SELECT clause.
    Handles: 'string', 'string with ''escapes''', NULL, TRUE, FALSE, numbers,
    and multi-line strings.
    """
    values = []
    i = 0
    s = values_str.strip()

    while i < len(s):
        # Skip whitespace and newlines
        while i < len(s) and s[i] in " \t\n\r":
            i += 1
        if i >= len(s):
            break

        # Quoted string
        if s[i] == "'":
            j = i + 1
            while j < len(s):
                if s[j] == "'" and j + 1 < len(s) and s[j + 1] == "'":
                    j += 2  # escaped quote
                elif s[j] == "'":
                    break
                else:
                    j += 1
            val = _unescape_sql_string(s[i + 1 : j])
            values.append(val)
            i = j + 1
        else:
            # Non-quoted value (NULL, TRUE, FALSE, number)
            j = i
            while j < len(s) and s[j] not in ",\n":
                j += 1
            token = s[i:j].strip()
            # Skip SQL type casts like ::insurance.xxx
            token = re.sub(r"::\S+", "", token).strip()
            if token:
                values.append(_parse_sql_value(token))
            i = j

        # Skip comma
        while i < len(s) and s[i] in " \t\n\r":
            i += 1
        if i < len(s) and s[i] == ",":
            i += 1

    return values


# ── CSR Data ──────────────────────────────────────────────────────────────────


def parse_csr_entries(sql_text: str) -> List[Dict[str, Any]]:
    """
    Parse claim_settlement_ratios from 05_supplementary.sql.
    Returns list of CSR dicts with company name, FY, value, type.
    """
    entries = []

    # Pattern 1: VALUES-based CSR blocks with (company_name, csr_value) tuples
    pattern = re.compile(
        r"INSERT INTO insurance\.claim_settlement_ratios\s*\([^)]+\)\s*"
        r"SELECT\s+c\.id\s*,\s*'([^']+)'\s*,\s*"  # financial_year
        r"csr_data\.csr_value\s*,\s*"
        r"'([^']+)'::insurance\.csr_type_enum"  # csr_type
        r".*?FROM\s*\(VALUES\s*\n(.*?)\)\s*AS\s+csr_data",
        re.DOTALL,
    )

    for match in pattern.finditer(sql_text):
        fy = match.group(1)
        csr_type = match.group(2)
        values_block = match.group(3)

        # Parse each (company_name, value) or (company_name, value, confidence) row
        row_pattern = re.compile(
            r"\(\s*'([^']*(?:''[^']*)*)'\s*,\s*([\d.]+)(?:\s*,\s*'([^']*)')?\s*\)"
        )
        for row in row_pattern.finditer(values_block):
            entries.append({
                "company_name": _unescape_sql_string(row.group(1)),
                "financial_year": fy,
                "csr_type": csr_type,
                "csr_value": float(row.group(2)),
                "data_confidence": row.group(3) or "verified",
            })

    logger.info("parse_csr_entries_complete", count=len(entries))
    return entries


# ── Policy Documents ──────────────────────────────────────────────────────────


def parse_policy_documents(sql_text: str) -> List[Dict[str, Any]]:
    """
    Parse policy_documents from 05_supplementary.sql.
    Returns list of document dicts with UIN, title, doc_type, URL.
    """
    documents = []

    # Find VALUES blocks for policy_documents
    pattern = re.compile(
        r"INSERT INTO insurance\.policy_documents\s*\([^)]+\)\s*"
        r"SELECT\s+p\.id.*?"
        r"FROM\s*\(VALUES\s*\n(.*?)\)\s*AS\s+doc",
        re.DOTALL,
    )

    for match in pattern.finditer(sql_text):
        values_block = match.group(1)
        # Each row: ('uin', 'title', 'doc_type', 'url', 'source_name')
        row_pattern = re.compile(
            r"\(\s*'([^']*(?:''[^']*)*)'\s*,"  # uin
            r"\s*'([^']*(?:''[^']*)*)'\s*,"     # title
            r"\s*'([^']*)'\s*,"                   # doc_type
            r"\s*'([^']*(?:''[^']*)*)'\s*,"     # url
            r"\s*'([^']*(?:''[^']*)*)'\s*\)"    # source_name
        )
        for row in row_pattern.finditer(values_block):
            documents.append({
                "uin": _unescape_sql_string(row.group(1)),
                "title": _unescape_sql_string(row.group(2)),
                "doc_type": row.group(3),
                "url": _unescape_sql_string(row.group(4)),
                "source_name": _unescape_sql_string(row.group(5)),
            })

    logger.info("parse_policy_documents_complete", count=len(documents))
    return documents


# ── Master Parse Function ─────────────────────────────────────────────────────


def parse_all_seed_files(
    seed_dir: Path,
) -> Dict[str, Any]:
    """
    Parse all botproject seed SQL files from the given directory.

    Returns:
        {
            "categories": {id: name},
            "sub_categories": {id: {name, category_id, description}},
            "companies": [company dicts],
            "products": [product dicts],
            "csr_entries": [csr dicts],
            "policy_documents": [doc dicts],
        }
    """
    result: Dict[str, Any] = {
        "categories": {},
        "sub_categories": {},
        "companies": [],
        "products": [],
        "csr_entries": [],
        "policy_documents": [],
    }

    # 01_foundation.sql
    foundation_path = seed_dir / "01_foundation.sql"
    if foundation_path.exists():
        text = foundation_path.read_text(encoding="utf-8")
        result["categories"] = parse_categories(text)
        result["sub_categories"] = parse_sub_categories(text)
        result["companies"] = parse_companies(text)

    # Product files (02, 03, 04)
    for fname in ["02_life_insurance.sql", "03_health_insurance.sql", "04_general_insurance.sql"]:
        fpath = seed_dir / fname
        if fpath.exists():
            text = fpath.read_text(encoding="utf-8")
            result["products"].extend(parse_products(text))

    # 05_supplementary.sql
    supp_path = seed_dir / "05_supplementary.sql"
    if supp_path.exists():
        text = supp_path.read_text(encoding="utf-8")
        result["csr_entries"] = parse_csr_entries(text)
        result["policy_documents"] = parse_policy_documents(text)

    logger.info(
        "parse_all_complete",
        categories=len(result["categories"]),
        sub_categories=len(result["sub_categories"]),
        companies=len(result["companies"]),
        products=len(result["products"]),
        csr_entries=len(result["csr_entries"]),
        policy_documents=len(result["policy_documents"]),
    )
    return result
