-- ============================================================
-- 06_citation_tables.sql - Source citations and audit trail
-- ============================================================

SET search_path TO insurance, public;

CREATE TABLE insurance.source_citations (
    id                      SERIAL PRIMARY KEY,
    entity_type             insurance.entity_type_enum NOT NULL,
    entity_id               INTEGER NOT NULL,
    source_url              VARCHAR(2000) NOT NULL,
    source_name             VARCHAR(300),            -- e.g., "IRDAI Official Website", "HDFC Life Product Page"
    source_type             VARCHAR(100),             -- e.g., "regulatory", "company_official", "annual_report"
    publication_date        DATE,
    access_date             DATE NOT NULL DEFAULT CURRENT_DATE,
    data_confidence         insurance.confidence_enum DEFAULT 'verified',
    notes                   TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE insurance.source_citations IS 'Source URLs and citations for every data record in the database';
COMMENT ON COLUMN insurance.source_citations.entity_type IS 'Which table this citation refers to (company, product, csr, etc.)';
COMMENT ON COLUMN insurance.source_citations.entity_id IS 'Primary key of the referenced record in the entity table';

-- Audit log for tracking data changes
CREATE TABLE insurance.data_audit_log (
    id              BIGSERIAL PRIMARY KEY,
    table_name      VARCHAR(100) NOT NULL,
    record_id       INTEGER NOT NULL,
    action          VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_values      JSONB,
    new_values      JSONB,
    changed_by      VARCHAR(100) DEFAULT CURRENT_USER,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE insurance.data_audit_log IS 'Audit trail for tracking all data modifications';
