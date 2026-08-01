-- 0002_document_chunks.sql
-- Searchable representation: document chunks with embedding vectors.

CREATE TABLE document_chunks (
    id                bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_id       text NOT NULL REFERENCES clinical_documents (id) ON DELETE CASCADE,
    practice_id       text NOT NULL REFERENCES practices (id) ON DELETE CASCADE,
    patient_id        text NOT NULL REFERENCES patients (id) ON DELETE CASCADE,
    document_type     document_type NOT NULL,
    chunk_index       smallint NOT NULL,
    content           text NOT NULL,
    embedding         vector(384) NOT NULL,
    source_updated_at timestamptz NOT NULL,
    created_at        timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT document_chunks_document_chunk_key
        UNIQUE (document_id, chunk_index)
);

-- Vector similarity search index (cosine distance, suited for L2-normalised vectors).
-- Note: IVFFlat benefits from existing data for list initialisation; at this dataset
-- scale (~10k chunks) the index is optional and exact search remains fast.
CREATE INDEX document_chunks_embedding_idx
    ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Practice isolation + document type filtering (search hot path).
CREATE INDEX document_chunks_practice_type_idx
    ON document_chunks (practice_id, document_type);

-- Patient-level aggregation.
CREATE INDEX document_chunks_patient_idx
    ON document_chunks (patient_id);
