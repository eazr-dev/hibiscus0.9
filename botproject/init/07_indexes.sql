-- ============================================================
-- 07_indexes.sql - All indexes for performance
-- ============================================================

SET search_path TO insurance, public;

-- Company indexes
CREATE INDEX idx_companies_type ON insurance.insurance_companies(company_type);
CREATE INDEX idx_companies_sector ON insurance.insurance_companies(sector);
CREATE INDEX idx_companies_name_trgm ON insurance.insurance_companies USING GIN (legal_name gin_trgm_ops);

-- Category indexes
CREATE INDEX idx_subcategories_category ON insurance.insurance_sub_categories(category_id);

-- Product indexes
CREATE INDEX idx_products_company ON insurance.insurance_products(company_id);
CREATE INDEX idx_products_subcategory ON insurance.insurance_products(sub_category_id);
CREATE INDEX idx_products_company_active ON insurance.insurance_products(company_id, is_active);
CREATE INDEX idx_products_subcategory_active ON insurance.insurance_products(sub_category_id, is_active);
CREATE INDEX idx_products_type ON insurance.insurance_products(product_type);
CREATE INDEX idx_products_active ON insurance.insurance_products(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_products_name_trgm ON insurance.insurance_products USING GIN (product_name gin_trgm_ops);
CREATE INDEX idx_products_eligibility ON insurance.insurance_products USING GIN (eligibility jsonb_path_ops);
CREATE INDEX idx_products_premium_info ON insurance.insurance_products USING GIN (premium_info jsonb_path_ops);

-- Full-text search on policy_summary
CREATE INDEX idx_products_summary_fts ON insurance.insurance_products
    USING GIN (to_tsvector('english', COALESCE(policy_summary, '')));

-- Document indexes
CREATE INDEX idx_documents_product ON insurance.policy_documents(product_id);
CREATE INDEX idx_documents_type ON insurance.policy_documents(doc_type);

-- Premium example indexes
CREATE INDEX idx_premiums_product ON insurance.premium_examples(product_id);

-- CSR indexes
CREATE INDEX idx_csr_company ON insurance.claim_settlement_ratios(company_id);
CREATE INDEX idx_csr_year ON insurance.claim_settlement_ratios(financial_year);
CREATE INDEX idx_csr_company_year ON insurance.claim_settlement_ratios(company_id, financial_year);

-- Citation indexes
CREATE INDEX idx_citations_entity ON insurance.source_citations(entity_type, entity_id);
CREATE INDEX idx_citations_url ON insurance.source_citations(source_url);
