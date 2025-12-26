-- ====================================================
-- LEGAL RAG SCHEMA - INTEGRATED WITH ADMIN LINKS
-- OPTIMIZED FOR POWERDESIGNER 15
-- ====================================================

-- 1. QUẢN TRỊ VIÊN (Nên tạo trước để các bảng khác tham chiếu tới)
CREATE TABLE admin_users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(200) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(200),
    role VARCHAR(50) DEFAULT 'admin',
    is_active SMALLINT DEFAULT 1,
    is_superuser SMALLINT DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
);

-- 2. BỘ THỦ TỤC (COLLECTIONS)
CREATE TABLE collections (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(500) NOT NULL,
    description VARCHAR(2000),
    icon VARCHAR(100),
    color VARCHAR(20),
    document_count INTEGER,
    total_chunks INTEGER,
    is_active SMALLINT,
    created_at DATETIME,
    updated_at DATETIME,
    created_by VARCHAR(36) -- Cột mới bổ sung
);

-- 3. VĂN BẢN TÀI LIỆU (DOCUMENTS)
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY,
    collection_id VARCHAR(36) NOT NULL,
    title VARCHAR(1000) NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),
    file_size BIGINT,
    chunk_count INTEGER,
    created_at DATETIME,
    updated_at DATETIME,
    uploaded_by VARCHAR(36) -- Cột mới bổ sung
);

-- 4. CÁC ĐOẠN DỮ LIỆU (CHUNKS)
CREATE TABLE chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    chunk_index INTEGER NOT NULL,
    content VARCHAR(4000),
    section_title VARCHAR(500),
    source_reference VARCHAR(200),
    embedding VARCHAR(2000),
    metadata VARCHAR(2000),
    created_at DATETIME
);

-- 5. BIỂU MẪU (FORMS)
CREATE TABLE forms (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    form_name VARCHAR(500) NOT NULL,
    template_path VARCHAR(1000),
    description VARCHAR(2000),
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE form_submissions (
    id VARCHAR(36) PRIMARY KEY,
    form_id VARCHAR(36) NOT NULL,
    output_file_path VARCHAR(1000) NOT NULL,
    created_at DATETIME
);

-- 6. LOGS & SESSIONS
CREATE TABLE admin_logs (
    id VARCHAR(36) PRIMARY KEY,
    admin_id VARCHAR(36) NOT NULL,
    action VARCHAR(100),
    resource_type VARCHAR(100),
    created_at DATETIME
);

CREATE TABLE query_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_identifier VARCHAR(200),
    context VARCHAR(2000),
    created_at DATETIME
);

CREATE TABLE query_logs (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(100),
    query_text VARCHAR(2000),
    answer_text VARCHAR(2000),
    created_at DATETIME
);

-- ====================================================
-- ĐỊNH NGHĨA LIÊN KẾT (FOREIGN KEYS)
-- ====================================================

-- Liên kết Admin -> Collections & Documents
ALTER TABLE collections ADD CONSTRAINT FK_COL_ADMIN FOREIGN KEY (created_by) REFERENCES admin_users (id);
ALTER TABLE documents ADD CONSTRAINT FK_DOC_ADMIN FOREIGN KEY (uploaded_by) REFERENCES admin_users (id);

-- Các liên kết cũ
ALTER TABLE documents ADD CONSTRAINT FK_DOC_COL FOREIGN KEY (collection_id) REFERENCES collections (id);
ALTER TABLE chunks ADD CONSTRAINT FK_CHUNK_DOC FOREIGN KEY (document_id) REFERENCES documents (id);
ALTER TABLE forms ADD CONSTRAINT FK_FORM_DOC FOREIGN KEY (document_id) REFERENCES documents (id);
ALTER TABLE form_submissions ADD CONSTRAINT FK_SUB_FORM FOREIGN KEY (form_id) REFERENCES forms (id);
ALTER TABLE query_logs ADD CONSTRAINT FK_LOG_SESS FOREIGN KEY (session_id) REFERENCES query_sessions (session_id);
ALTER TABLE admin_logs ADD CONSTRAINT FK_ADLOG_ADUSER FOREIGN KEY (admin_id) REFERENCES admin_users (id);