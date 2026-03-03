"""
────────────────────────────────────────────────────────────────────────
│  EAZR Insurance Database Setup Script                                │
│                                                                      │
│  Creates the insurance_india PostgreSQL database and populates it    │
│  with the init/ (schema) and seed/ (data) SQL files.                │
│                                                                      │
│  Usage:                                                              │
│    python scripts/setup_insurance_db.py                              │
│    python scripts/setup_insurance_db.py --init-only                  │
│    python scripts/setup_insurance_db.py --seed-only                  │
│    python scripts/setup_insurance_db.py --drop-first                 │
│    python scripts/setup_insurance_db.py --dsn "postgresql://..."     │
────────────────────────────────────────────────────────────────────────
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# Ordered list of init files (schema creation)
INIT_FILES = [
    "00_extensions.sql",
    "01_enums.sql",
    "02_company_tables.sql",
    "03_category_tables.sql",
    "04_product_tables.sql",
    "05_csr_tables.sql",
    "06_citation_tables.sql",
    "07_indexes.sql",
    "08_functions_triggers.sql",
]

# Ordered list of seed files (data population)
SEED_FILES = [
    "01_foundation.sql",
    "02_life_insurance.sql",
    "03_health_insurance.sql",
    "04_general_insurance.sql",
    "05_supplementary.sql",
]


def get_dsn(override_dsn: str = None) -> str:
    """Build PostgreSQL DSN from env vars or use override."""
    if override_dsn:
        return override_dsn

    host = os.getenv("PG_INSURANCE_HOST", os.getenv("TYPEORM_HOST", "localhost"))
    port = os.getenv("PG_INSURANCE_PORT", os.getenv("TYPEORM_PORT", "5432"))
    user = os.getenv("PG_INSURANCE_USER", os.getenv("TYPEORM_USERNAME", "postgres"))
    password = os.getenv("PG_INSURANCE_PASSWORD", os.getenv("TYPEORM_PASSWORD", ""))
    database = os.getenv("PG_INSURANCE_DB", "insurance_india")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def ensure_database_exists(dsn: str):
    """Create the insurance_india database if it doesn't exist."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    # Parse DSN to get database name and connect to 'postgres' default DB
    parts = dsn.rsplit("/", 1)
    base_dsn = parts[0] + "/postgres"
    db_name = parts[1].split("?")[0] if len(parts) > 1 else "insurance_india"

    try:
        conn = psycopg2.connect(base_dsn)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if cur.fetchone():
            logger.info(f"Database '{db_name}' already exists")
        else:
            cur.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"Created database '{db_name}'")

        cur.close()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not auto-create database: {e}")
        logger.info("Make sure the database exists before running this script")


def run_sql_files(dsn: str, directory: Path, files: list, label: str):
    """Execute a list of SQL files in order against the database.

    For seed files (data population), individual statements are executed
    with savepoints so that duplicate-key errors skip only the
    offending row instead of rolling back the entire file.
    """
    import psycopg2
    import psycopg2.errors

    total = len(files)
    success = 0
    errors = []
    is_seed = "seed" in str(directory)

    for i, filename in enumerate(files, 1):
        filepath = directory / filename
        if not filepath.exists():
            logger.warning(f"[{i}/{total}] SKIP — {filename} not found")
            errors.append(f"{filename}: file not found")
            continue

        try:
            sql = filepath.read_text(encoding="utf-8")

            if is_seed and sql.upper().count("INSERT") > 5:
                # Statement-by-statement with savepoints for seed files
                conn = psycopg2.connect(dsn)
                conn.autocommit = False
                cur = conn.cursor()
                statements = _split_sql(sql)
                skipped = 0
                executed = 0
                for stmt in statements:
                    stripped = stmt.strip()
                    # Skip empty / comment-only statements
                    lines = [l for l in stripped.split("\n") if l.strip() and not l.strip().startswith("--")]
                    if not lines:
                        continue
                    try:
                        cur.execute("SAVEPOINT sp")
                        cur.execute(stmt)
                        cur.execute("RELEASE SAVEPOINT sp")
                        executed += 1
                    except (psycopg2.errors.UniqueViolation,
                            psycopg2.errors.IntegrityConstraintViolation):
                        cur.execute("ROLLBACK TO SAVEPOINT sp")
                        skipped += 1
                    except Exception as stmt_err:
                        try:
                            cur.execute("ROLLBACK TO SAVEPOINT sp")
                        except Exception:
                            pass
                        skipped += 1
                conn.commit()
                cur.close()
                conn.close()
                success += 1
                skip_msg = f" (skipped {skipped} duplicates)" if skipped else ""
                logger.info(f"[{i}/{total}] OK — {filename}: {executed} executed{skip_msg}")
            else:
                # Run entire file as one transaction (init files)
                conn = psycopg2.connect(dsn)
                conn.autocommit = False
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
                cur.close()
                conn.close()
                success += 1
                logger.info(f"[{i}/{total}] OK — {filename}")
        except Exception as e:
            error_msg = str(e).split("\n")[0]
            logger.error(f"[{i}/{total}] FAIL — {filename}: {error_msg}")
            errors.append(f"{filename}: {error_msg}")

    logger.info(f"\n{label} complete: {success}/{total} files succeeded")
    if errors:
        logger.warning(f"Errors ({len(errors)}):")
        for err in errors:
            logger.warning(f"  - {err}")

    return success == total


def _split_sql(sql: str) -> list:
    """Split SQL text into individual statements, respecting string literals.
    Handles PostgreSQL '' escape sequences and dollar-quoted strings.
    """
    statements = []
    current = []
    in_string = False
    i = 0
    chars = sql

    while i < len(chars):
        c = chars[i]

        if in_string:
            current.append(c)
            if c == "'" :
                # Check for '' (escaped quote in PostgreSQL)
                if i + 1 < len(chars) and chars[i + 1] == "'":
                    current.append(chars[i + 1])
                    i += 2
                    continue
                else:
                    in_string = False
            i += 1
        else:
            if c == "'":
                in_string = True
                current.append(c)
                i += 1
            elif c == ";":
                stmt = "".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
                i += 1
            else:
                current.append(c)
                i += 1

    stmt = "".join(current).strip()
    if stmt:
        statements.append(stmt)

    return statements


def drop_schema(dsn: str):
    """Drop the insurance schema (destructive!)."""
    import psycopg2

    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()

    logger.warning("Dropping insurance schema...")
    cur.execute("DROP SCHEMA IF EXISTS insurance CASCADE")
    logger.info("Schema dropped")

    cur.close()
    conn.close()


def verify_setup(dsn: str):
    """Quick verification that the database is properly set up."""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(dsn)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    checks = [
        ("Categories", "SELECT COUNT(*) AS cnt FROM insurance.insurance_categories"),
        ("Sub-categories", "SELECT COUNT(*) AS cnt FROM insurance.insurance_sub_categories"),
        ("Companies", "SELECT COUNT(*) AS cnt FROM insurance.insurance_companies"),
        ("Products", "SELECT COUNT(*) AS cnt FROM insurance.insurance_products"),
        ("Documents", "SELECT COUNT(*) AS cnt FROM insurance.policy_documents"),
        ("CSR entries", "SELECT COUNT(*) AS cnt FROM insurance.claim_settlement_ratios"),
        ("Citations", "SELECT COUNT(*) AS cnt FROM insurance.source_citations"),
    ]

    logger.info("\n=== Database Verification ===")
    for label, query in checks:
        try:
            cur.execute(query)
            row = cur.fetchone()
            count = row["cnt"] if row else 0
            status = "OK" if count > 0 else "EMPTY"
            logger.info(f"  {label}: {count} rows [{status}]")
        except Exception as e:
            logger.error(f"  {label}: ERROR — {e}")

    # Test the v_products_full view
    try:
        cur.execute("SELECT COUNT(*) AS cnt FROM insurance.v_products_full")
        row = cur.fetchone()
        logger.info(f"  v_products_full view: {row['cnt']} rows [OK]")
    except Exception as e:
        logger.error(f"  v_products_full view: ERROR — {e}")

    # Test trigram extension
    try:
        cur.execute("SELECT similarity('Star Health', 'Star Health and Allied Insurance') AS sim")
        row = cur.fetchone()
        logger.info(f"  pg_trgm extension: working (similarity={row['sim']:.2f})")
    except Exception as e:
        logger.error(f"  pg_trgm extension: ERROR — {e}")

    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Set up the EAZR insurance_india database")
    parser.add_argument("--dsn", help="PostgreSQL DSN override")
    parser.add_argument("--init-only", action="store_true", help="Run only init (schema) files")
    parser.add_argument("--seed-only", action="store_true", help="Run only seed (data) files")
    parser.add_argument("--drop-first", action="store_true", help="Drop insurance schema before init")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing setup")
    parser.add_argument("--skip-verify", action="store_true", help="Skip post-setup verification")
    args = parser.parse_args()

    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 is required. Install with: pip install psycopg2-binary")
        sys.exit(1)

    dsn = get_dsn(args.dsn)
    logger.info(f"Target database: {dsn.split('@')[-1] if '@' in dsn else dsn}")

    init_dir = PROJECT_ROOT / "init"
    seed_dir = PROJECT_ROOT / "seed"

    if args.verify_only:
        verify_setup(dsn)
        return

    # Ensure database exists
    ensure_database_exists(dsn)

    if args.drop_first:
        confirm = input("This will DROP the insurance schema. Type 'yes' to confirm: ")
        if confirm.strip().lower() != "yes":
            logger.info("Aborted")
            return
        drop_schema(dsn)

    run_init = not args.seed_only
    run_seed = not args.init_only

    if run_init:
        logger.info(f"\n{'='*60}")
        logger.info("STEP 1: Running init/ files (schema creation)")
        logger.info(f"{'='*60}")
        run_sql_files(dsn, init_dir, INIT_FILES, "Schema initialization")

    if run_seed:
        logger.info(f"\n{'='*60}")
        logger.info("STEP 2: Running seed/ files (data population)")
        logger.info(f"{'='*60}")
        run_sql_files(dsn, seed_dir, SEED_FILES, "Data seeding")

    if not args.skip_verify:
        verify_setup(dsn)

    logger.info("\nDone! The insurance_india database is ready.")
    logger.info("DatabaseMatcher DSN: " + dsn)


if __name__ == "__main__":
    main()
