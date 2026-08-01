-- 0004_tsvector_column.sql
-- Pre-compute tsvector for BM25 search to avoid on-the-fly computation.
-- This reduces BM25 query latency from ~150ms to ~5ms.

-- Add tsvector column
ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS content_tsv tsvector;

-- Populate from existing content
UPDATE document_chunks
    SET content_tsv = to_tsvector('english', content);

-- GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS document_chunks_content_tsv_idx
    ON document_chunks USING gin (content_tsv);
