-- 0003_hnsw_index.sql
-- Replace IVFFlat with HNSW index for more stable recall.
-- HNSW provides better query performance without requiring manual probe tuning.

-- Drop the old IVFFlat index
DROP INDEX IF EXISTS document_chunks_embedding_idx;

-- Create HNSW index with recommended parameters
-- m = 16: max connections per layer (balanced for our data scale)
-- ef_construction = 128: search candidates during build (higher quality graph for better recall)
CREATE INDEX document_chunks_embedding_idx
    ON document_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 128);
