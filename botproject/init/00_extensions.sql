-- ============================================================
-- Indian Insurance Products Database
-- 00_extensions.sql - PostgreSQL extensions
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create the schema namespace
CREATE SCHEMA IF NOT EXISTS insurance;

-- Set search path
SET search_path TO insurance, public;

COMMENT ON SCHEMA insurance IS 'Indian Insurance Products Database - IRDAI registered companies, products, and regulatory data';
