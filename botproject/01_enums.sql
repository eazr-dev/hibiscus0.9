-- ============================================================
-- 01_enums.sql - ENUM type definitions
-- ============================================================

SET search_path TO insurance, public;

-- Company classification
CREATE TYPE insurance.company_type_enum AS ENUM (
    'life',
    'general',
    'health',
    'reinsurance',
    'specialized'
);

CREATE TYPE insurance.sector_enum AS ENUM (
    'public',
    'private',
    'specialized'
);

-- Product classification
CREATE TYPE insurance.product_type_enum AS ENUM (
    'individual',
    'group',
    'add_on',
    'rider',
    'standard',
    'micro'
);

CREATE TYPE insurance.product_linked_enum AS ENUM (
    'linked',        -- ULIP
    'non_linked',    -- Traditional
    'not_applicable' -- General/Health
);

CREATE TYPE insurance.par_enum AS ENUM (
    'participating',
    'non_participating',
    'not_applicable'
);

-- Document types
CREATE TYPE insurance.doc_type_enum AS ENUM (
    'brochure',
    'policy_wording',
    'prospectus',
    'claim_form',
    'benefit_illustration',
    'premium_chart',
    'proposal_form',
    'product_summary'
);

CREATE TYPE insurance.file_format_enum AS ENUM (
    'pdf',
    'html',
    'xlsx',
    'doc'
);

-- CSR classification
CREATE TYPE insurance.csr_type_enum AS ENUM (
    'individual_death',
    'group_death',
    'health',
    'maturity',
    'overall'
);

CREATE TYPE insurance.measurement_basis_enum AS ENUM (
    'by_number',
    'by_amount'
);

-- Citation entity types
CREATE TYPE insurance.entity_type_enum AS ENUM (
    'company',
    'product',
    'csr',
    'document',
    'category',
    'premium'
);

-- Data confidence
CREATE TYPE insurance.confidence_enum AS ENUM (
    'verified',      -- From official IRDAI/company source
    'high',          -- From reputable secondary source
    'medium',        -- From aggregator/news
    'low',           -- Unverified
    'not_available'  -- Could not find data
);
