-- ============================================
-- Vector-Service Database Schema
-- PostgreSQL 16 with pgvector extension
-- Table: chunks (vector embeddings for LegalRAG)
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Chunks Table: Text chunks with vector embeddings
-- ============================================
-- Each chunk belongs to exactly one document
-- Used for semantic similarity search
--
-- DESIGN PRINCIPLES:
-- - Split documents into semantic chunks for better search + context
-- - Keep references to section (Điều, Mục, Chương) for user understanding
-- - Store embeddings (vector) for semantic similarity search
-- - Optional metadata JSONB for chunk-level extracted data
--
-- FIELD EXPLANATIONS:
-- - id, document_id: UUID relationship to Documents (auto-delete if document deleted)
-- - chunk_index: Position in document (0, 1, 2, ...) - preserve order for reconstruction
-- - content: Actual text to embed and search
-- - section_title: Vietnamese section extracted from document
--   * Auto-extract using regex: "Điều \d+", "Mục \d+", "Chương"
--   * Helps user understand context ("This is from Điều 5")
--   * Can be NULL if document doesn't have clear sections
-- - source_reference: Full reference path extracted from document
--   * Auto-extract using regex: "Điều 5, khoản 2, điểm a"
--   * Helps user cite exact location (legal citation)
--   * Can be NULL if document structure unclear
-- - embedding: 768-dimensional vector from Vietnamese embedding model
--   * Used for semantic similarity search
--   * Created by embedding-service (dangvantuan/vietnamese-document-embedding)
--   * HNSW index for fast search (O(log N) instead of O(N))
-- - token_count: Number of tokens in chunk content
--   * Used for context window management
--   * Calculated by embedding-service
-- - metadata: Optional JSONB for chunk-level extracted data
--   * Example: {"page_number": 5, "confidence": 0.95, "language": "vi"}
--   * Can be empty {}
-- - created_at: When chunk was created (during extraction)
-- - UNIQUE(document_id, chunk_index): Ensure no duplicate chunks per document

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL,  -- Foreign key to documents table (in main DB)
    
    -- CHUNK IDENTIFICATION (required)
    chunk_index INTEGER NOT NULL,  -- Sequential order in document (0, 1, 2, ...)
    
    -- CHUNK CONTENT (required)
    content TEXT NOT NULL,  -- Actual text to search and embed
    
    -- SECTION INFORMATION (optional, auto-extracted from PDF)
    -- These fields help user understand document structure + cite sources
    section_title VARCHAR(500),  -- e.g., "Điều 1", "Mục 2.3", "Chương III"
                                 -- NULL if document doesn't have clear sections
                                 -- Auto-extracted using regex pattern matching
    source_reference VARCHAR(200),  -- e.g., "Điều 5, khoản 2, điểm a"
                                    -- Full path for legal citation
                                    -- NULL if cannot extract clearly
    
    -- VECTOR EMBEDDING (required for search)
    -- 768-dimensional vector from Vietnamese embedding model
    -- Used for semantic similarity search (cosine distance)
    -- Created by embedding-service (separate from this pipeline)
    embedding vector(768),
    
    -- TOKEN COUNT (optional, for context management)
    token_count INTEGER,  -- Number of tokens in chunk content
                         -- Used for context window management
    
    -- CHUNK METADATA (optional, auto-extracted)
    -- Example: {"page_number": 5, "confidence": 0.95, "language": "vi"}
    metadata JSONB DEFAULT '{}',
    
    -- TIMESTAMP (required for audit trail)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- CONSTRAINT (ensure no duplicate chunks)
    UNIQUE(document_id, chunk_index)
);

-- ============================================
-- INDEXES
-- ============================================

-- CRITICAL: Vector similarity search index (HNSW)
-- This is ESSENTIAL for fast similarity search performance
-- Without this index, search will be O(N) instead of O(log N)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Index for document lookups (used in delete operations)
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);

-- Index for chunk ordering (used in reconstruction)
CREATE INDEX IF NOT EXISTS idx_chunks_document_index ON chunks(document_id, chunk_index);

-- ============================================
-- NOTES
-- ============================================
-- 1. This schema matches schema_new.sql chunks table from main LegalRAG project
-- 2. EMBEDDING_DIMENSION = 768 (Vietnamese model: dangvantuan/vietnamese-document-embedding)
-- 3. Hard delete used (no is_deleted flag) - relies on CASCADE DELETE from documents
-- 4. HNSW index parameters:
--    - m = 16: Number of connections per layer (higher = better recall, more memory)
--    - ef_construction = 64: Size of dynamic candidate list (higher = better quality, slower build)
-- 5. For production, consider tuning HNSW parameters based on dataset size:
--    - Small dataset (<100K): m=16, ef_construction=64
--    - Medium dataset (100K-1M): m=32, ef_construction=128
--    - Large dataset (>1M): m=64, ef_construction=200
