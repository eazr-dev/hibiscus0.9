-- ============================================================
-- 03_category_tables.sql - Insurance categories and sub-categories
-- ============================================================

SET search_path TO insurance, public;

CREATE TABLE insurance.insurance_categories (
    id                  SERIAL PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    description         TEXT,
    irdai_segment_code  VARCHAR(5),  -- IRDAI reinsurance segment code (A, B, C, etc.)
    applicable_to       insurance.company_type_enum[], -- Which company types offer this category
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_category_name UNIQUE (name)
);

COMMENT ON TABLE insurance.insurance_categories IS 'Top-level insurance categories (Life, Health, Motor, etc.)';
COMMENT ON COLUMN insurance.insurance_categories.irdai_segment_code IS 'IRDAI reinsurance segment code per IRDAI (Re-insurance) Regulations, 2018';

CREATE TABLE insurance.insurance_sub_categories (
    id              SERIAL PRIMARY KEY,
    category_id     INTEGER NOT NULL REFERENCES insurance.insurance_categories(id) ON DELETE CASCADE,
    name            VARCHAR(150) NOT NULL,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_subcategory_per_category UNIQUE (category_id, name)
);

COMMENT ON TABLE insurance.insurance_sub_categories IS 'Sub-categories under each insurance category';
