#!/bin/bash
# =============================================================
# PostgreSQL init for EAZR insurance_india DB
# Runs on first container start (when data volume is empty)
# =============================================================
set -e

INIT_DIR="/docker-init-sql/init"
SEED_DIR="/docker-init-sql/seed"
DB_NAME="${POSTGRES_DB:-insurance_india}"

echo "========================================"
echo "EAZR PostgreSQL Initialization"
echo "Database: $DB_NAME"
echo "========================================"

# ── Step 1: Schema creation ──
INIT_FILES=(
    "00_extensions.sql"
    "01_enums.sql"
    "02_company_tables.sql"
    "03_category_tables.sql"
    "04_product_tables.sql"
    "05_csr_tables.sql"
    "06_citation_tables.sql"
    "07_indexes.sql"
    "08_functions_triggers.sql"
)

echo ""
echo "── Step 1: Schema Creation ──"
for sql_file in "${INIT_FILES[@]}"; do
    filepath="$INIT_DIR/$sql_file"
    if [ -f "$filepath" ]; then
        echo "  Running: $sql_file"
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" -f "$filepath"
    else
        echo "  WARNING: $sql_file not found"
    fi
done
echo "  Schema creation complete."

# ── Step 2: Data seeding ──
SEED_FILES=(
    "01_foundation.sql"
    "02_life_insurance.sql"
    "03_health_insurance.sql"
    "04_general_insurance.sql"
    "05_supplementary.sql"
)

echo ""
echo "── Step 2: Data Seeding ──"
for sql_file in "${SEED_FILES[@]}"; do
    filepath="$SEED_DIR/$sql_file"
    if [ -f "$filepath" ]; then
        echo "  Running: $sql_file ..."
        # ON_ERROR_STOP=0 to skip duplicate inserts
        psql --username "$POSTGRES_USER" --dbname "$DB_NAME" -f "$filepath" 2>&1 | tail -3
    else
        echo "  WARNING: $sql_file not found"
    fi
done
echo "  Data seeding complete."

# ── Step 3: Verify ──
echo ""
echo "── Step 3: Verification ──"
PRODUCT_COUNT=$(psql -t --username "$POSTGRES_USER" --dbname "$DB_NAME" -c "SELECT COUNT(*) FROM insurance.insurance_products;" 2>/dev/null || echo "0")
COMPANY_COUNT=$(psql -t --username "$POSTGRES_USER" --dbname "$DB_NAME" -c "SELECT COUNT(*) FROM insurance.insurance_companies;" 2>/dev/null || echo "0")
CATEGORY_COUNT=$(psql -t --username "$POSTGRES_USER" --dbname "$DB_NAME" -c "SELECT COUNT(*) FROM insurance.insurance_categories;" 2>/dev/null || echo "0")
echo "  Categories: $CATEGORY_COUNT"
echo "  Companies:  $COMPANY_COUNT"
echo "  Products:   $PRODUCT_COUNT"

echo ""
echo "========================================"
echo "EAZR PostgreSQL initialization complete!"
echo "========================================"
