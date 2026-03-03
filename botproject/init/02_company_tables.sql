-- ============================================================
-- 02_company_tables.sql - Insurance company tables
-- ============================================================

SET search_path TO insurance, public;

CREATE TABLE insurance.insurance_companies (
    id                  SERIAL PRIMARY KEY,
    legal_name          VARCHAR(255) NOT NULL,
    short_name          VARCHAR(100),
    registration_number VARCHAR(20),  -- IRDAI registration number
    company_type        insurance.company_type_enum NOT NULL,
    sector              insurance.sector_enum NOT NULL DEFAULT 'private',
    ceo_name            VARCHAR(200),
    website             VARCHAR(500),
    irdai_page_url      VARCHAR(500),
    headquarters        VARCHAR(200),
    established_year    INTEGER,
    parent_company      VARCHAR(255),
    uin_prefix          VARCHAR(20),   -- Company-specific UIN prefix code
    data_confidence     insurance.confidence_enum DEFAULT 'verified',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_verified_date  DATE DEFAULT CURRENT_DATE,

    CONSTRAINT uq_company_legal_name UNIQUE (legal_name),
    CONSTRAINT chk_established_year CHECK (established_year >= 1818 AND established_year <= 2030)
);

COMMENT ON TABLE insurance.insurance_companies IS 'All IRDAI-registered insurance companies in India';
COMMENT ON COLUMN insurance.insurance_companies.registration_number IS 'IRDAI Certificate of Registration number';
COMMENT ON COLUMN insurance.insurance_companies.uin_prefix IS 'Company-specific prefix used in product UIN codes (e.g., HDFLIP for HDFC Life)';
