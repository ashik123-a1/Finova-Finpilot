-- Migration 003: Document Chunks for Local-First RAG (Retrieval-Augmented Generation)
-- Enables tenant-isolated vector search, document citations, and context grounding

CREATE TABLE IF NOT EXISTS document_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    business_id INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    shop_id INTEGER REFERENCES shops(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    metadata_json TEXT,
    embedding_json TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_doc_chunks_biz ON document_chunks(business_id);
CREATE INDEX IF NOT EXISTS idx_doc_chunks_shop ON document_chunks(shop_id);
CREATE INDEX IF NOT EXISTS idx_doc_chunks_doc ON document_chunks(document_id);
