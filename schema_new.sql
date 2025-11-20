-- ============================================
-- LegalRAG Database Schema v2.0
-- PostgreSQL 16 with pgvector extension
-- ============================================
-- Architecture:
--   Collections (bộ thủ tục) 1:N Documents (văn bản)
--     → Documents 1:N Chunks/Vectors (embeddings)
--     → Documents 1:N Forms (biểu mẫu - optional)
-- 
-- Access Control:
--   - Admin: Full CRUD on collections/documents/vectors
--            View logs/metrics (requires authentication)
--   - User: Read-only collections/documents/forms
--           Query execution (no authentication required)
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- CORE TABLES
-- ============================================

-- Collections: Bộ thủ tục (procedure sets)
-- Example: "quy_trinh_cap_ho_tich", "quy_trinh_boi_thuong_nn"
CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Collection identification
    name VARCHAR(200) UNIQUE NOT NULL,  -- Slug/identifier: "quy_trinh_cap_ho_tich"
    display_name VARCHAR(500) NOT NULL,  -- Display: "Quy trình cấp hộ tịch"
    description TEXT,
    
    -- UI styling (optional)
    icon VARCHAR(100) DEFAULT 'file-text',  -- Icon name (e.g., 'file-text', 'shield-check')
    color VARCHAR(20) DEFAULT '#3b82f6',   -- Hex color code for UI
    
    -- Statistics (cached for performance)
    document_count INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP
);

-- Create index on collection name for fast lookups
CREATE INDEX IF NOT EXISTS idx_collections_name ON collections(name) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_collections_active ON collections(is_active) WHERE is_deleted = FALSE;

-- Documents: Văn bản pháp luật (tài liệu pháp lý)
-- Mỗi tài liệu thuộc đúng 1 collection (bộ thủ tục)
-- 
-- NGUYÊN TẮC THIẾT KẾ:
-- - Chỉ lưu các field có thể auto-extract từ PDF (KHÔNG yêu cầu nhập thủ công)
-- - Dùng metadata JSONB để lưu dữ liệu được extract (linh hoạt, không cần migrate schema)
-- - Chỉ support PDF (cơ quan gửi PDF, không .doc hay .docx)
--
-- GIẢI THÍCH CÁC FIELD:
-- - id, collection_id: Quan hệ UUID (Collections → Documents)
-- - title, filename: Xác định tài liệu
-- - file_path, file_size: Metadata lưu trữ trong MinIO
-- - status: Trạng thái xử lý (pending → processing → completed hoặc failed)
-- - chunk_count: Số chunks được tạo (auto-update bằng trigger)
-- - error_message: Nếu status = failed, chứa chi tiết lỗi để debug
-- - metadata JSONB: Dữ liệu được extract tự động (TÙY CHỌN, linh hoạt, không lock schema)
--   * KHÔNG bắt buộc (nullable by design)
--   * KHÔNG nhập thủ công (tools extract hoặc để trống)
--   * Chứa dữ liệu extracted:
--     - document_code: "68/2018/NĐ-CP" (extract bằng regex)
--     - dates: ["15/5/2018"] (regex, tất cả các ngày tìm được)
--     - organizations: ["Bộ Tư pháp"] (pattern matching)
--     - sections: ["MỤC ĐÍCH", "PHẠM VI"] (regex extract)
--     - pages: 7 (metadata PDF)
--     - language: "vi" (language detection)
--     - extraction_confidence: 0.85 (điểm chất lượng, rất quan trọng!)
--     - extraction_notes: "..." (ghi chú những gì tool không extract được)
-- - Timestamps: created_at (lúc upload), updated_at (mỗi lần thay đổi), processed_at (lúc xong extract)
-- - is_deleted, deleted_at: Soft delete (giữ dữ liệu, không xóa vật lý)

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    
    -- XÁC ĐỊNH TÀI LIỆU (bắt buộc)
    title VARCHAR(1000) NOT NULL,  -- Tên tài liệu (extract từ PDF hoặc filename)
    
    -- THÔNG TIN FILE (bắt buộc cho lưu trữ)
    filename VARCHAR(500) NOT NULL,  -- Tên file gốc (vd: "Thủ tục xác định cơ quan.pdf")
    file_path VARCHAR(1000),  -- Đường dẫn MinIO: "collections/{collection_slug}/{uuid}_{filename}"
    file_size BIGINT,  -- Kích thước (bytes, dùng cho monitoring, UI)
    
    -- TRẠNG THÁI XỬ LÝ (bắt buộc cho pipeline)
    status VARCHAR(50) DEFAULT 'pending',  -- Enum: pending, processing, completed, failed
    chunk_count INTEGER DEFAULT 0,  -- Số chunks được tạo (auto-update bằng trigger)
    error_message TEXT,  -- Nếu status = failed, chi tiết lỗi để admin debug
    
    -- METADATA ĐƯỢC EXTRACT TỰ ĐỘNG (tùy chọn, bổ sung, KHÔNG nhập thủ công)
    -- QUAN TRỌNG: NULLABLE by design. Không phải tất cả tài liệu đều có tất cả field.
    -- Tools populate nếu extract được, để trống nếu không thể extract.
    -- Ví dụ khi extract hoàn toàn:
    -- {
    --   "document_code": "68/2018/NĐ-CP",           ← regex extract từ text
    --   "dates": ["15/5/2018", "12/6/2025"],        ← tất cả ngày tìm được bằng regex
    --   "organizations": ["Bộ Tư pháp", "UBND"],    ← pattern matching
    --   "sections": ["MỤC ĐÍCH", "PHẠM VI"],        ← cấu trúc tài liệu
    --   "pages": 7,                                  ← từ metadata PDF
    --   "language": "vi",                            ← language detection
    --   "word_count": 2500,                          ← độ dài text
    --   "has_tables": true,                          ← pattern detection
    --   "has_signatures": true,                      ← pattern detection
    --   "extraction_confidence": 0.85,               ← điểm 0-1 (QUAN TRỌNG cho chất lượng)
    --   "extraction_notes": "Thiếu ngày hiệu lực"   ← ghi chú những gì tool không extract
    -- }
    metadata JSONB DEFAULT '{}',
    
    -- TIMESTAMPS (bắt buộc cho audit trail)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Lúc upload tài liệu
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- Lúc bất kỳ field nào thay đổi
    processed_at TIMESTAMP,  -- Lúc extraction xong (null cho tới khi xong)
    
    -- SOFT DELETE (bắt buộc để bảo tồn dữ liệu)
    is_deleted BOOLEAN DEFAULT FALSE,  -- Đánh dấu xóa mà không xóa vật lý
    deleted_at TIMESTAMP  -- Lúc bị xóa
);

-- Indexes for documents
CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);

-- Chunks: Text chunks với vector embeddings để tìm kiếm semantics
-- Mỗi chunk thuộc đúng 1 tài liệu (document)
-- 
-- NGUYÊN TẮC THIẾT KẾ:
-- - Chia tài liệu thành semantic chunks để tìm kiếm tốt hơn + cung cấp context
-- - Giữ references đến section (Điều, Mục, Chương) để user hiểu được
-- - Lưu embeddings (vector) để tìm kiếm similarity semantics
-- - Metadata JSONB tùy chọn cho dữ liệu extracted ở level chunk
--
-- GIẢI THÍCH CÁC FIELD:
-- - id, document_id: Quan hệ UUID đến Documents (auto-delete nếu document bị xóa)
-- - chunk_index: Vị trí trong tài liệu (0, 1, 2, ...) - giữ thứ tự để reconstruct
-- - content: Đoạn text thực tế để embed và search
-- - section_title: Section Vietnamese được extract từ tài liệu
--   * Auto-extract bằng regex: "Điều \d+", "Mục \d+", "Chương"
--   * Giúp user hiểu context ("Cái này ở Điều 5")
--   * Có thể NULL nếu tài liệu không có section rõ ràng
-- - source_reference: Đường dẫn full reference được extract từ tài liệu
--   * Auto-extract bằng regex: "Điều 5, khoản 2, điểm a"
--   * Giúp user cite exact location (trích dẫn pháp lý)
--   * Có thể NULL nếu cấu trúc tài liệu không rõ
-- - embedding: Vector 384 chiều từ Vietnamese embedding model
--   * Dùng cho tìm kiếm similarity semantics
--   * Được tạo bởi embedding-service
--   * HNSW index cho tìm kiếm nhanh (O(log N) thay vì O(N))
-- - metadata JSONB: Optional dữ liệu extracted ở level chunk
--   * Ví dụ: {"page_number": 5, "confidence": 0.95, "language": "vi"}
--   * Có thể để trống {}
-- - created_at: Lúc chunk được tạo (trong quá trình extraction)
-- - UNIQUE(document_id, chunk_index): Đảm bảo không có duplicate chunk per document

CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- XÁC ĐỊNH CHUNK (bắt buộc)
    chunk_index INTEGER NOT NULL,  -- Thứ tự tuần tự trong tài liệu (0, 1, 2, ...)
    
    -- NỘI DUNG CHUNK (bắt buộc)
    content TEXT NOT NULL,  -- Text thực tế để search và embed
    
    -- THÔNG TIN SECTION (tùy chọn, auto-extract từ PDF)
    -- Các field này giúp user hiểu cấu trúc tài liệu + cite source
    section_title VARCHAR(500),  -- vd: "Điều 1", "Mục 2.3", "Chương III"
                                 -- NULL nếu tài liệu không có section rõ
                                 -- Auto-extract bằng regex pattern matching
    source_reference VARCHAR(200),  -- vd: "Điều 5, khoản 2, điểm a"
                                    -- Đường dẫn đầy đủ để trích dẫn pháp lý
                                    -- NULL nếu không thể extract rõ ràng
    
    -- VECTOR EMBEDDING (bắt buộc để search)
    -- Vector 768 chiều từ Vietnamese embedding model (dangvantuan/vietnamese-document-embedding)
    -- Dùng cho semantic similarity search (cosine distance)
    -- Được tạo bởi embedding-service (riêng biệt từ pipeline này)
    embedding vector(768),  -- UPDATED: 768-D for Vietnamese model
    
    -- METADATA CHUNK (tùy chọn, auto-extract)
    -- Ví dụ: {"page_number": 5, "confidence": 0.95, "language": "vi"}
    metadata JSONB DEFAULT '{}',
    
    -- TIMESTAMP (bắt buộc cho audit trail)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- CONSTRAINT (đảm bảo không có duplicate chunk)
    UNIQUE(document_id, chunk_index)
);

-- CRITICAL: Vector similarity search index (HNSW)
-- This is essential for fast similarity search performance
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Additional indexes for chunks
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);

-- Forms: Biểu mẫu (legal forms) associated with documents
-- Each form belongs to exactly one document (optional relationship)
CREATE TABLE IF NOT EXISTS forms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Form identification
    form_code VARCHAR(200),  -- e.g., "MẪU 01-HS", "Phụ lục II"
    form_name VARCHAR(500) NOT NULL,  -- Display name
    form_type VARCHAR(100),  -- Type: "application", "certificate", "report", etc.
    
    -- Form content
    template_path VARCHAR(1000),  -- Path to form template file (PDF, DOCX, etc.)
    preview_path VARCHAR(1000),  -- Path to preview image/PDF
    
    -- Form field definitions (JSON structure for dynamic form generation)
    fields JSONB DEFAULT '[]',  -- Array of field definitions
    -- Example: [{"name": "ho_ten", "type": "text", "label": "Họ và tên", "required": true}, ...]
    
    -- Validation rules
    validation_rules JSONB DEFAULT '{}',
    
    -- Form metadata
    description TEXT,
    instructions TEXT,  -- Instructions for filling out form
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    
    -- Constraints
    UNIQUE(document_id, form_code)
);

-- Indexes for forms
CREATE INDEX IF NOT EXISTS idx_forms_document ON forms(document_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_forms_type ON forms(form_type) WHERE is_deleted = FALSE;

-- ============================================
-- USER & SESSION MANAGEMENT
-- ============================================

-- Users: User information (primarily from CCCD scanning)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- CCCD (Vietnamese ID card) information
    cccd_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),  -- 'Nam', 'Nữ'
    address TEXT,
    
    -- Contact information (optional)
    phone VARCHAR(20),
    email VARCHAR(200),
    
    -- CCCD scan data
    cccd_front_image VARCHAR(1000),  -- Path to front image
    cccd_back_image VARCHAR(1000),  -- Path to back image
    qr_code_data TEXT,  -- Decoded QR code data
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE
);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_users_cccd ON users(cccd_number) WHERE is_deleted = FALSE;

-- Admin Users: Admin accounts for system management
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Authentication
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,  -- bcrypt hash
    
    -- Profile
    full_name VARCHAR(200),
    role VARCHAR(50) DEFAULT 'admin',  -- 'admin', 'superadmin'
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    
    -- Login tracking
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for admin users
CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users(username) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email) WHERE is_active = TRUE;

-- Query Sessions: Session tracking for conversational queries
CREATE TABLE IF NOT EXISTS query_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    
    -- User tracking (optional, for analytics)
    user_identifier VARCHAR(200),  -- IP address or anonymous ID
    user_agent TEXT,
    
    -- Session metadata
    conversation_turns INTEGER DEFAULT 0,
    topics TEXT[],  -- Array of discussed topics/collections
    
    -- Session data
    context JSONB DEFAULT '{}',  -- Conversation context
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- Session expiration
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'
);

-- Index for session lookups and cleanup
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON query_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_sessions_last_accessed ON query_sessions(last_accessed);

-- ============================================
-- LOGGING & METRICS TABLES
-- ============================================

-- Query Logs: Log all user queries for analytics and improvement
CREATE TABLE IF NOT EXISTS query_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) REFERENCES query_sessions(session_id),
    
    -- Query details
    query_text TEXT NOT NULL,
    query_type VARCHAR(50),  -- 'initial', 'clarification', 'follow_up'
    
    -- Processing results
    answer_text TEXT,
    sources_used JSONB DEFAULT '[]',  -- Array of chunk IDs and document IDs
    collection_routed VARCHAR(200),  -- Which collection was selected
    
    -- Performance metrics
    processing_time_ms INTEGER,
    tokens_used INTEGER,
    
    -- Quality metrics
    confidence_score FLOAT,
    similarity_scores JSONB DEFAULT '[]',  -- Array of similarity scores
    
    -- User feedback (optional)
    user_rating INTEGER,  -- 1-5 stars
    user_feedback TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes for query logs
CREATE INDEX IF NOT EXISTS idx_query_logs_session ON query_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_created ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_query_logs_collection ON query_logs(collection_routed);

-- Admin Logs: Audit trail for all admin actions
CREATE TABLE IF NOT EXISTS admin_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID REFERENCES admin_users(id),
    
    -- Action details
    action VARCHAR(100) NOT NULL,  -- 'create', 'update', 'delete', 'upload', 'rebuild'
    resource_type VARCHAR(100) NOT NULL,  -- 'collection', 'document', 'chunk', 'form'
    resource_id UUID,  -- ID of affected resource
    
    -- Change details
    old_values JSONB,  -- Previous values (for updates)
    new_values JSONB,  -- New values
    
    -- Request context
    ip_address VARCHAR(50),
    user_agent TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional details
    details JSONB DEFAULT '{}'
);

-- Indexes for admin logs
CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_resource ON admin_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_admin_logs_created ON admin_logs(created_at);

-- System Metrics: Performance and usage metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_type VARCHAR(100) NOT NULL,  -- 'query_count', 'avg_response_time', 'error_rate'
    metric_value FLOAT NOT NULL,
    
    -- Scope (optional)
    collection_id UUID REFERENCES collections(id),
    document_id UUID REFERENCES documents(id),
    
    -- Time aggregation
    aggregation_period VARCHAR(50),  -- 'hourly', 'daily', 'weekly', 'monthly'
    
    -- Timestamps
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'
);

-- Indexes for metrics
CREATE INDEX IF NOT EXISTS idx_metrics_type ON system_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_metrics_recorded ON system_metrics(recorded_at);
CREATE INDEX IF NOT EXISTS idx_metrics_collection ON system_metrics(collection_id);

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function: Update document count in collection
CREATE OR REPLACE FUNCTION update_collection_document_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE collections 
        SET document_count = document_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.collection_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE collections 
        SET document_count = document_count - 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.collection_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Automatically update collection document count
CREATE TRIGGER trigger_update_collection_document_count
AFTER INSERT OR DELETE ON documents
FOR EACH ROW
EXECUTE FUNCTION update_collection_document_count();

-- Function: Update chunk count in document
CREATE OR REPLACE FUNCTION update_document_chunk_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE documents 
        SET chunk_count = chunk_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.document_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE documents 
        SET chunk_count = chunk_count - 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.document_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Automatically update document chunk count
CREATE TRIGGER trigger_update_document_chunk_count
AFTER INSERT OR DELETE ON chunks
FOR EACH ROW
EXECUTE FUNCTION update_document_chunk_count();

-- Function: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at on all tables with that column
CREATE TRIGGER trigger_collections_updated_at BEFORE UPDATE ON collections
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_documents_updated_at BEFORE UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_forms_updated_at BEFORE UPDATE ON forms
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_admin_users_updated_at BEFORE UPDATE ON admin_users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function: Vector similarity search with metadata
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector(768),  -- UPDATED: 768-D for Vietnamese model
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    filter_collection_id uuid DEFAULT NULL
)
RETURNS TABLE (
    chunk_id uuid,
    document_id uuid,
    collection_id uuid,
    content text,
    section_title varchar,
    similarity float,
    document_title varchar,
    document_metadata jsonb,
    collection_name varchar
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id AS chunk_id,
        c.document_id,
        d.collection_id,
        c.content,
        c.section_title,
        1 - (c.embedding <=> query_embedding) AS similarity,
        d.title AS document_title,
        d.metadata AS document_metadata,
        col.name AS collection_name
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    JOIN collections col ON d.collection_id = col.id
    WHERE 
        (filter_collection_id IS NULL OR d.collection_id = filter_collection_id)
        AND d.is_deleted = FALSE
        AND d.status = 'completed'
        AND (1 - (c.embedding <=> query_embedding)) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function: Get collection statistics
CREATE OR REPLACE FUNCTION get_collection_stats(target_collection_id uuid)
RETURNS TABLE (
    collection_id uuid,
    collection_name varchar,
    document_count bigint,
    chunk_count bigint,
    total_file_size bigint,
    avg_chunks_per_document numeric
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        col.id AS collection_id,
        col.name AS collection_name,
        COUNT(DISTINCT d.id) AS document_count,
        COUNT(c.id) AS chunk_count,
        COALESCE(SUM(d.file_size), 0) AS total_file_size,
        CASE 
            WHEN COUNT(DISTINCT d.id) > 0 
            THEN ROUND(COUNT(c.id)::numeric / COUNT(DISTINCT d.id), 2)
            ELSE 0
        END AS avg_chunks_per_document
    FROM collections col
    LEFT JOIN documents d ON col.id = d.collection_id AND d.is_deleted = FALSE
    LEFT JOIN chunks c ON d.id = c.document_id
    WHERE col.id = target_collection_id
    GROUP BY col.id, col.name;
END;
$$;

-- ============================================
-- SAMPLE DATA (for development/testing)
-- ============================================

-- Insert sample collections
INSERT INTO collections (name, display_name, description, icon, color) VALUES
('quy_trinh_cap_ho_tich', 'Quy trình cấp hộ tịch', 'Thủ tục cấp giấy khai sinh, đăng ký kết hôn', 'file-text', '#3b82f6'),
('quy_trinh_boi_thuong_nn', 'Quy trình bồi thường nhà nước', 'Thủ tục bồi thường thiệt hại do nhà nước gây ra', 'shield-check', '#10b981')
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE collections IS 'Bộ thủ tục (procedure sets) - top-level grouping';
COMMENT ON TABLE documents IS 'Văn bản pháp luật - legal documents belonging to collections';
COMMENT ON TABLE chunks IS 'Text chunks with vector embeddings for semantic search';
COMMENT ON TABLE forms IS 'Biểu mẫu (forms) associated with documents';
COMMENT ON TABLE users IS 'User information from CCCD scanning';
COMMENT ON TABLE admin_users IS 'Admin accounts for system management';
COMMENT ON TABLE query_sessions IS 'Session tracking for conversational queries';
COMMENT ON TABLE query_logs IS 'Log of all user queries for analytics';
COMMENT ON TABLE admin_logs IS 'Audit trail for admin actions';
COMMENT ON TABLE system_metrics IS 'Performance and usage metrics';
