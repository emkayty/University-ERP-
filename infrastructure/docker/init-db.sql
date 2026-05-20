-- Enable PostgreSQL extensions for UMIS
-- Required for: pgvector (embeddings), pgAudit (audit logging), pg_trgm (full-text search)

-- Vector extensions for ML/embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Audit logging for NDPA 2023 compliance
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Trigram extension for full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Unaccent for accent-insensitive search
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Create indexes for commonly used extensions
-- pg_trgm index for text search
CREATE INDEX IF NOT EXISTS idx_trgm_search ON pg_catalog.pg_class USING gin (relname gin_trgm_ops);

-- Enable row-level security (for multi-tenancy)
ALTER DATABASE university_mis SET row_security = ON;

-- Set default schema for new connections
SET search_path = public;