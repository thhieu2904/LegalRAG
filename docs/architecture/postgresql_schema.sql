-- =====================================================
-- LegalRAG PostgreSQL Schema với pgvector Extension
-- =====================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- 1. BỘ LUẬT (Legal Code Categories)
-- =====================================================
CREATE TABLE bo_luat (
    id SERIAL PRIMARY KEY,
    ma_bo_luat VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'BL_DAN_SU'
    ten_bo_luat VARCHAR(255) NOT NULL,       -- e.g., 'Bộ Luật Dân Sự'
    mo_ta TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast lookup
CREATE INDEX idx_bo_luat_ma ON bo_luat(ma_bo_luat);

-- =====================================================
-- 2. VĂN BẢN LUẬT (Legal Documents)
-- =====================================================
CREATE TABLE van_ban_luat (
    id SERIAL PRIMARY KEY,
    bo_luat_id INTEGER REFERENCES bo_luat(id) ON DELETE CASCADE,
    
    -- Document metadata
    ma_van_ban VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'DOC_001'
    ten_van_ban VARCHAR(500) NOT NULL,        -- Document title
    loai_van_ban VARCHAR(50),                 -- Type: quy_trinh, mau_don, etc.
    
    -- Storage paths in MinIO
    minio_bucket VARCHAR(100),                -- MinIO bucket name
    minio_path VARCHAR(500),                  -- Path in MinIO: /bo_luat/van_ban/
    json_path VARCHAR(500),                   -- Path to JSON content
    original_path VARCHAR(500),               -- Path to original file
    
    -- Document content for RAG
    noi_dung_full TEXT,                       -- Full content (for backup/search)
    
    -- Router questions (denormalized for performance)
    router_questions JSONB,                   -- Router questions array
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Full text search index
    CONSTRAINT valid_minio_bucket CHECK (minio_bucket IS NOT NULL)
);

-- Indexes for performance
CREATE INDEX idx_van_ban_bo_luat ON van_ban_luat(bo_luat_id);
CREATE INDEX idx_van_ban_ma ON van_ban_luat(ma_van_ban);
CREATE INDEX idx_van_ban_loai ON van_ban_luat(loai_van_ban);
CREATE INDEX idx_router_questions_gin ON van_ban_luat USING gin(router_questions);

-- Full-text search index (Vietnamese support)
CREATE INDEX idx_van_ban_fulltext ON van_ban_luat USING gin(to_tsvector('simple', noi_dung_full));

-- =====================================================
-- 3. VECTOR EMBEDDINGS (pgvector)
-- =====================================================
CREATE TABLE van_ban_vectors (
    id SERIAL PRIMARY KEY,
    van_ban_id INTEGER REFERENCES van_ban_luat(id) ON DELETE CASCADE,
    
    -- Chunk information
    chunk_index INTEGER NOT NULL,             -- Thứ tự chunk trong văn bản
    chunk_text TEXT NOT NULL,                 -- Nội dung chunk
    chunk_size INTEGER,                       -- Độ dài chunk
    
    -- Vector embedding (1024 dimensions for Vietnamese_Embedding_v2)
    embedding vector(1024) NOT NULL,
    
    -- Context expansion pointers
    prev_chunk_id INTEGER REFERENCES van_ban_vectors(id),
    next_chunk_id INTEGER REFERENCES van_ban_vectors(id),
    
    -- Metadata for filtering
    metadata JSONB,                           -- Additional metadata
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_chunk UNIQUE (van_ban_id, chunk_index)
);

-- Vector similarity search index (HNSW for performance)
CREATE INDEX idx_vectors_embedding_hnsw ON van_ban_vectors 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Regular indexes
CREATE INDEX idx_vectors_van_ban ON van_ban_vectors(van_ban_id);
CREATE INDEX idx_vectors_chunk_idx ON van_ban_vectors(chunk_index);
CREATE INDEX idx_vectors_prev_chunk ON van_ban_vectors(prev_chunk_id);
CREATE INDEX idx_vectors_next_chunk ON van_ban_vectors(next_chunk_id);

-- GIN index for metadata filtering
CREATE INDEX idx_vectors_metadata_gin ON van_ban_vectors USING gin(metadata);

-- =====================================================
-- 4. MẪU ĐƠN/FORMS (Forms linked to documents)
-- =====================================================
CREATE TABLE mau_don (
    id SERIAL PRIMARY KEY,
    van_ban_id INTEGER REFERENCES van_ban_luat(id) ON DELETE CASCADE,
    
    -- Form metadata
    ten_mau_don VARCHAR(255) NOT NULL,        -- e.g., 'Khai sinh.docx'
    loai_mau_don VARCHAR(50),                 -- Type: khai_sinh, ho_khau, etc.
    
    -- Storage in MinIO
    minio_bucket VARCHAR(100),
    minio_path VARCHAR(500),                  -- Path to form file in MinIO
    
    -- Form mapping configuration (field mappings)
    mapping_config JSONB,                     -- Field mapping từ CCCD → form fields
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_mau_don_van_ban ON mau_don(van_ban_id);
CREATE INDEX idx_mau_don_loai ON mau_don(loai_mau_don);
CREATE INDEX idx_mau_don_mapping_gin ON mau_don USING gin(mapping_config);

-- =====================================================
-- 5. SESSION MANAGEMENT (Optional - for chat history)
-- =====================================================
CREATE TABLE chat_sessions (
    id VARCHAR(50) PRIMARY KEY,               -- Session ID (e.g., '20251114-001')
    user_id VARCHAR(100),                     -- User identifier (optional)
    
    -- Session state
    context_data JSONB,                       -- Session context (collection, document, etc.)
    conversation_history JSONB,               -- Chat history
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_sessions_last_active ON chat_sessions(last_active);
CREATE INDEX idx_sessions_expires ON chat_sessions(expires_at);

-- =====================================================
-- 6. HELPER FUNCTIONS
-- =====================================================

-- Function: Vector similarity search với filtering
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector(1024),
    p_bo_luat_id INTEGER DEFAULT NULL,
    p_van_ban_id INTEGER DEFAULT NULL,
    similarity_threshold FLOAT DEFAULT 0.3,
    max_results INTEGER DEFAULT 20
)
RETURNS TABLE (
    vector_id INTEGER,
    van_ban_id INTEGER,
    chunk_index INTEGER,
    chunk_text TEXT,
    similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        v.id,
        v.van_ban_id,
        v.chunk_index,
        v.chunk_text,
        1 - (v.embedding <=> query_embedding) AS similarity,
        v.metadata
    FROM van_ban_vectors v
    INNER JOIN van_ban_luat vb ON v.van_ban_id = vb.id
    WHERE 
        (p_bo_luat_id IS NULL OR vb.bo_luat_id = p_bo_luat_id)
        AND (p_van_ban_id IS NULL OR v.van_ban_id = p_van_ban_id)
        AND (1 - (v.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY v.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function: Get context expansion chunks (prev + current + next)
CREATE OR REPLACE FUNCTION get_expanded_context(
    p_chunk_id INTEGER,
    expansion_size INTEGER DEFAULT 1
)
RETURNS TABLE (
    chunk_id INTEGER,
    chunk_index INTEGER,
    chunk_text TEXT,
    position VARCHAR(10)  -- 'prev', 'current', 'next'
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE context_chain AS (
        -- Current chunk
        SELECT 
            v.id,
            v.chunk_index,
            v.chunk_text,
            'current'::VARCHAR(10) AS position,
            0 AS level
        FROM van_ban_vectors v
        WHERE v.id = p_chunk_id
        
        UNION ALL
        
        -- Previous chunks
        SELECT 
            v.id,
            v.chunk_index,
            v.chunk_text,
            'prev'::VARCHAR(10),
            cc.level - 1
        FROM van_ban_vectors v
        INNER JOIN context_chain cc ON v.id = cc.chunk_id - 1
        WHERE cc.level > -expansion_size
        
        UNION ALL
        
        -- Next chunks
        SELECT 
            v.id,
            v.chunk_index,
            v.chunk_text,
            'next'::VARCHAR(10),
            cc.level + 1
        FROM van_ban_vectors v
        INNER JOIN context_chain cc ON v.id = cc.chunk_id + 1
        WHERE cc.level < expansion_size
    )
    SELECT 
        id,
        chunk_index,
        chunk_text,
        position
    FROM context_chain
    ORDER BY chunk_index;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 7. TRIGGERS for updated_at
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_bo_luat_updated_at BEFORE UPDATE ON bo_luat
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_van_ban_luat_updated_at BEFORE UPDATE ON van_ban_luat
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mau_don_updated_at BEFORE UPDATE ON mau_don
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 8. SAMPLE DATA (for testing)
-- =====================================================

-- Insert sample Bộ Luật
INSERT INTO bo_luat (ma_bo_luat, ten_bo_luat, mo_ta) VALUES
('BL_DAN_SU', 'Bộ Luật Dân Sự', 'Các quy định về dân sự'),
('BL_HO_TICH', 'Bộ Luật Hộ Tịch', 'Các quy định về hộ tịch và giấy tờ tùy thân'),
('BL_BAO_HIEM', 'Bộ Luật Bảo Hiểm', 'Các quy định về bảo hiểm xã hội và y tế');

-- Note: Actual document and vector data will be populated by migration scripts

-- =====================================================
-- 9. USEFUL QUERIES (for reference)
-- =====================================================

-- Search documents by collection
-- SELECT * FROM van_ban_luat WHERE bo_luat_id = (SELECT id FROM bo_luat WHERE ma_bo_luat = 'BL_HO_TICH');

-- Get forms for a document
-- SELECT * FROM mau_don WHERE van_ban_id = 1;

-- Vector similarity search (example)
-- SELECT * FROM search_similar_chunks('[0.1, 0.2, ...]'::vector(1024), NULL, NULL, 0.5, 10);

-- Get expanded context
-- SELECT * FROM get_expanded_context(100, 2);
