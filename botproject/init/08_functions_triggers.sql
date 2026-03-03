-- ============================================================
-- 08_functions_triggers.sql - Trigger functions and triggers
-- ============================================================

SET search_path TO insurance, public;

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION insurance.fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all relevant tables
CREATE TRIGGER trg_companies_updated
    BEFORE UPDATE ON insurance.insurance_companies
    FOR EACH ROW EXECUTE FUNCTION insurance.fn_update_timestamp();

CREATE TRIGGER trg_categories_updated
    BEFORE UPDATE ON insurance.insurance_categories
    FOR EACH ROW EXECUTE FUNCTION insurance.fn_update_timestamp();

CREATE TRIGGER trg_subcategories_updated
    BEFORE UPDATE ON insurance.insurance_sub_categories
    FOR EACH ROW EXECUTE FUNCTION insurance.fn_update_timestamp();

CREATE TRIGGER trg_products_updated
    BEFORE UPDATE ON insurance.insurance_products
    FOR EACH ROW EXECUTE FUNCTION insurance.fn_update_timestamp();

CREATE TRIGGER trg_documents_updated
    BEFORE UPDATE ON insurance.policy_documents
    FOR EACH ROW EXECUTE FUNCTION insurance.fn_update_timestamp();

CREATE TRIGGER trg_premiums_updated
    BEFORE UPDATE ON insurance.premium_examples
    FOR EACH ROW EXECUTE FUNCTION insurance.fn_update_timestamp();

CREATE TRIGGER trg_csr_updated
    BEFORE UPDATE ON insurance.claim_settlement_ratios
    FOR EACH ROW EXECUTE FUNCTION insurance.fn_update_timestamp();

-- UIN format validation function (lenient - alphanumeric with some special chars)
CREATE OR REPLACE FUNCTION insurance.fn_validate_uin()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.uin IS NOT NULL AND NEW.uin !~ '^[A-Za-z0-9/_-]+$' THEN
        RAISE EXCEPTION 'Invalid UIN format: %. UIN must be alphanumeric with optional /, -, _ characters.', NEW.uin;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_product_uin
    BEFORE INSERT OR UPDATE ON insurance.insurance_products
    FOR EACH ROW EXECUTE FUNCTION insurance.fn_validate_uin();

-- Handy view: products with company and category info
CREATE OR REPLACE VIEW insurance.v_products_full AS
SELECT
    p.id AS product_id,
    p.product_name,
    p.uin,
    p.product_type,
    p.is_active,
    p.launch_date,
    p.policy_summary,
    p.key_benefits,
    p.terms_conditions,
    p.exclusions,
    p.eligibility,
    p.premium_info,
    p.source_url AS product_source_url,
    p.data_confidence,
    c.id AS company_id,
    c.legal_name AS company_name,
    c.company_type,
    c.sector,
    c.website AS company_website,
    c.registration_number,
    cat.id AS category_id,
    cat.name AS category_name,
    sc.id AS sub_category_id,
    sc.name AS sub_category_name
FROM insurance.insurance_products p
JOIN insurance.insurance_companies c ON p.company_id = c.id
JOIN insurance.insurance_sub_categories sc ON p.sub_category_id = sc.id
JOIN insurance.insurance_categories cat ON sc.category_id = cat.id;

COMMENT ON VIEW insurance.v_products_full IS 'Complete product view with company and category details joined';
