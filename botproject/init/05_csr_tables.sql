-- ============================================================
-- 05_csr_tables.sql - Claim Settlement Ratio tables
-- ============================================================

SET search_path TO insurance, public;

CREATE TABLE insurance.claim_settlement_ratios (
    id                  SERIAL PRIMARY KEY,
    company_id          INTEGER NOT NULL REFERENCES insurance.insurance_companies(id) ON DELETE CASCADE,
    financial_year      VARCHAR(9) NOT NULL,   -- e.g., '2023-2024'
    csr_value           NUMERIC(6, 2),         -- Percentage, e.g., 98.50
    csr_type            insurance.csr_type_enum NOT NULL DEFAULT 'overall',
    measurement_basis   insurance.measurement_basis_enum NOT NULL DEFAULT 'by_number',
    claims_received     INTEGER,
    claims_settled      INTEGER,
    claims_repudiated   INTEGER,
    claims_pending      INTEGER,
    amount_paid_crores  NUMERIC(12, 2),        -- In crores INR
    report_name         VARCHAR(300),
    source_url          VARCHAR(1000),
    data_confidence     insurance.confidence_enum DEFAULT 'verified',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_csr_per_company_year_type UNIQUE (company_id, financial_year, csr_type, measurement_basis),
    CONSTRAINT chk_csr_range CHECK (csr_value IS NULL OR (csr_value >= 0 AND csr_value <= 100))
);

COMMENT ON TABLE insurance.claim_settlement_ratios IS 'Yearly Claim Settlement Ratios per company, sourced from IRDAI Handbook/Annual Reports';
COMMENT ON COLUMN insurance.claim_settlement_ratios.csr_value IS 'Percentage of claims settled (0-100)';
COMMENT ON COLUMN insurance.claim_settlement_ratios.amount_paid_crores IS 'Total claims amount paid in crores INR';
