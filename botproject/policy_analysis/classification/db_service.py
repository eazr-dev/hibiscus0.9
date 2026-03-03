"""
Database integration service for the Hibiscus Policy Classifier.
Provides a singleton DatabaseMatcher that lazily connects to the
insurance_india PostgreSQL database for product matching and validation.
"""

import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

_db_matcher_instance = None
_db_init_attempted = False


def _get_dsn() -> str:
    """Build DSN from environment, falling back to TYPEORM vars."""
    host = os.getenv("PG_INSURANCE_HOST", os.getenv("TYPEORM_HOST", "localhost"))
    port = os.getenv("PG_INSURANCE_PORT", os.getenv("TYPEORM_PORT", "5432"))
    user = os.getenv("PG_INSURANCE_USER", os.getenv("TYPEORM_USERNAME", "postgres"))
    password = os.getenv("PG_INSURANCE_PASSWORD", os.getenv("TYPEORM_PASSWORD", ""))
    database = os.getenv("PG_INSURANCE_DB", "insurance_india")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def get_db_matcher():
    """
    Get or create the singleton DatabaseMatcher instance.
    Returns None if the database is not available (graceful fallback).
    """
    global _db_matcher_instance, _db_init_attempted

    if _db_matcher_instance is not None:
        return _db_matcher_instance

    if _db_init_attempted:
        return None  # Already failed once, don't retry every call

    _db_init_attempted = True

    try:
        from policy_analysis.classification.hibiscus_policy_classifier import DatabaseMatcher
        dsn = _get_dsn()
        _db_matcher_instance = DatabaseMatcher(dsn)
        logger.info("DatabaseMatcher connected to insurance_india")
        return _db_matcher_instance
    except ImportError:
        logger.info("psycopg2 not installed — DatabaseMatcher disabled")
        return None
    except Exception as e:
        logger.warning(f"DatabaseMatcher connection failed: {e} — product matching disabled")
        return None


def match_product_from_db(classification_result, insurer_name: str = "", limit: int = 5) -> Dict[str, Any]:
    """
    Given a ClassificationResult, find matching products in the insurance_india DB.

    Returns:
        {
            "matched": True/False,
            "db_fields": { category_name, subcategory_name, ... },
            "validation": { valid, category_id, subcategory_id, ... },
            "products": [ { product_id, product_name, uin, company_name, sim_score, ... } ],
            "company_id": int or None,
        }
    """
    matcher = get_db_matcher()
    if matcher is None:
        return {"matched": False, "reason": "database_unavailable"}

    result = {
        "matched": False,
        "db_fields": classification_result.to_db_fields(),
        "validation": {},
        "products": [],
        "company_id": None,
    }

    try:
        # 1. Validate category/subcategory mapping exists in DB
        result["validation"] = matcher.validate_classification(classification_result)

        # 2. Find matching products
        result["products"] = matcher.find_matching_products(classification_result, limit=limit)

        # 3. Fuzzy-match company name
        if insurer_name:
            result["company_id"] = matcher.get_company_id(insurer_name)

        result["matched"] = result["validation"].get("valid", False)

    except Exception as e:
        logger.warning(f"DB product matching failed: {e}")
        result["matched"] = False
        result["reason"] = str(e)

    return result


def get_product_by_uin(uin: str) -> Optional[Dict[str, Any]]:
    """Look up a specific product by its UIN in the insurance_india database."""
    matcher = get_db_matcher()
    if matcher is None:
        return None

    try:
        import psycopg2.extras
        with matcher.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT product_id, product_name, uin, company_name, company_type,
                       category_name, sub_category_name, product_type, is_active,
                       policy_summary, key_benefits, eligibility, premium_info
                FROM insurance.v_products_full
                WHERE uin = %(uin)s
                LIMIT 1
            """, {"uin": uin})
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.warning(f"UIN lookup failed for {uin}: {e}")
        return None
