-- ============================================
-- LegalRAG Forms Table Simplification
-- Remove over-engineered fields
-- ============================================

-- Drop unused columns from forms table
ALTER TABLE forms 
DROP COLUMN IF EXISTS fields,
DROP COLUMN IF EXISTS validation_rules,
DROP COLUMN IF EXISTS preview_path,
DROP COLUMN IF EXISTS metadata;

-- Comment: Simplified forms table
-- Only keeps essential fields:
-- - id, document_id (relationship)
-- - form_code, form_name, form_type (identification)
-- - template_path (file path)
-- - description, instructions (optional text)
-- - created_at, updated_at (timestamps)

COMMENT ON TABLE forms IS 'Biểu mẫu (forms) - Simplified version without over-engineered fields';
