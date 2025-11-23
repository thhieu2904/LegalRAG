-- ============================================
-- Migration: Simplify Documents Table
-- Date: 2025-11-23
-- Purpose: Remove over-engineered pipeline fields
--   - Remove: status, error_message, metadata, processed_at
--   - Keep: Core fields (id, collection_id, title, filename, file_path, file_size, chunk_count)
--   - Reason: Local system không cần async pipeline tracking
-- ============================================

-- BEFORE:
-- 13 columns: id, collection_id, title, filename, file_path, file_size, 
--             status, chunk_count, error_message, metadata, 
--             created_at, updated_at, processed_at

-- AFTER:
-- 9 columns: id, collection_id, title, filename, file_path, file_size,
--            chunk_count, created_at, updated_at

-- ===== STEP 1: Drop indexes referencing status =====
DROP INDEX IF EXISTS idx_documents_status;

-- ===== STEP 2: Drop over-engineered columns =====
ALTER TABLE documents DROP COLUMN IF EXISTS status;
ALTER TABLE documents DROP COLUMN IF EXISTS error_message;
ALTER TABLE documents DROP COLUMN IF EXISTS metadata;
ALTER TABLE documents DROP COLUMN IF EXISTS processed_at;

-- ===== STEP 3: Verify final schema =====
-- Should have 9 columns remaining

SELECT 'Migration completed! Documents table simplified.' as status;

-- ===== VERIFICATION QUERY =====
-- Uncomment to verify:
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'documents' 
-- ORDER BY ordinal_position;
