-- ============================================================
-- 04_product_tables.sql - Insurance products and related tables
-- ============================================================

SET search_path TO insurance, public;

CREATE TABLE insurance.insurance_products (
    id                      SERIAL PRIMARY KEY,
    company_id              INTEGER NOT NULL REFERENCES insurance.insurance_companies(id) ON DELETE CASCADE,
    sub_category_id         INTEGER NOT NULL REFERENCES insurance.insurance_sub_categories(id) ON DELETE CASCADE,
    product_name            VARCHAR(500) NOT NULL,
    uin                     VARCHAR(50),  -- IRDAI Unique Identification Number
    product_type            insurance.product_type_enum NOT NULL DEFAULT 'individual',
    linked_type             insurance.product_linked_enum DEFAULT 'not_applicable',
    par_type                insurance.par_enum DEFAULT 'not_applicable',
    financial_year_filed    VARCHAR(9),   -- e.g., '2023-2024'
    launch_date             DATE,
    withdrawal_date         DATE,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,

    -- Product details
    policy_summary          TEXT,
    key_benefits            TEXT,
    terms_conditions        TEXT,
    exclusions              TEXT,

    -- Eligibility as JSONB for flexibility
    eligibility             JSONB DEFAULT '{}',
    -- Example: {"min_entry_age": 18, "max_entry_age": 65, "min_sum_insured": 500000, "max_sum_insured": 50000000}

    -- Premium info as JSONB
    premium_info            JSONB DEFAULT '{}',
    -- Example: {"min_premium": 5000, "payment_modes": ["annual", "semi_annual", "quarterly", "monthly"]}

    -- Policy terms
    policy_term_options     TEXT,  -- e.g., "10, 15, 20, 25, 30 years" or "Whole Life"
    premium_payment_options TEXT,  -- e.g., "Regular, Limited Pay (5, 7, 10, 12 years), Single Premium"

    -- Metadata
    data_confidence         insurance.confidence_enum DEFAULT 'verified',
    source_url              VARCHAR(1000),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_date      DATE DEFAULT CURRENT_DATE,

    CONSTRAINT uq_product_uin UNIQUE (uin),
    CONSTRAINT chk_withdrawal_after_launch CHECK (withdrawal_date IS NULL OR launch_date IS NULL OR withdrawal_date >= launch_date)
);

COMMENT ON TABLE insurance.insurance_products IS 'All insurance products registered with IRDAI, identified by UIN';
COMMENT ON COLUMN insurance.insurance_products.uin IS 'IRDAI-assigned Unique Identification Number. Must appear on all product documents.';
COMMENT ON COLUMN insurance.insurance_products.eligibility IS 'JSONB: min/max entry age, sum insured range, etc.';
COMMENT ON COLUMN insurance.insurance_products.premium_info IS 'JSONB: min premium, payment modes, premium tables';

-- Policy documents (brochures, wordings, etc.)
CREATE TABLE insurance.policy_documents (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES insurance.insurance_products(id) ON DELETE CASCADE,
    title           VARCHAR(500) NOT NULL,
    doc_type        insurance.doc_type_enum NOT NULL,
    url             VARCHAR(2000) NOT NULL,
    file_format     insurance.file_format_enum DEFAULT 'pdf',
    source_name     VARCHAR(200),  -- e.g., "IRDAI Filing", "Company Website"
    data_confidence insurance.confidence_enum DEFAULT 'verified',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE insurance.policy_documents IS 'Policy wording PDFs, brochures, and other product documents with URLs';

-- Premium examples
CREATE TABLE insurance.premium_examples (
    id                  SERIAL PRIMARY KEY,
    product_id          INTEGER NOT NULL REFERENCES insurance.insurance_products(id) ON DELETE CASCADE,
    age                 INTEGER,
    gender              VARCHAR(10),
    sum_insured         NUMERIC(15, 2),
    annual_premium      NUMERIC(12, 2),
    premium_payment_term INTEGER,
    policy_term         INTEGER,
    smoker_status       VARCHAR(15),
    plan_option         VARCHAR(100),
    source_url          VARCHAR(1000),
    data_confidence     insurance.confidence_enum DEFAULT 'high',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE insurance.premium_examples IS 'Sample premium amounts for common age/sum insured combinations';

-- Product riders (linking rider products to base products)
CREATE TABLE insurance.product_riders (
    id              SERIAL PRIMARY KEY,
    base_product_id INTEGER NOT NULL REFERENCES insurance.insurance_products(id) ON DELETE CASCADE,
    rider_product_id INTEGER NOT NULL REFERENCES insurance.insurance_products(id) ON DELETE CASCADE,
    is_optional     BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_product_rider UNIQUE (base_product_id, rider_product_id),
    CONSTRAINT chk_no_self_rider CHECK (base_product_id != rider_product_id)
);

COMMENT ON TABLE insurance.product_riders IS 'Mapping of rider products to their base products';
