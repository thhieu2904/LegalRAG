-- ============================================
-- CLEANUP OLD TEST DATA
-- Run this BEFORE importing new data
-- ============================================
-- WARNING: This will DELETE all existing data!
-- Make sure to backup if needed.

-- Disable triggers temporarily for faster deletion
ALTER TABLE chunks DISABLE TRIGGER ALL;
ALTER TABLE documents DISABLE TRIGGER ALL;
ALTER TABLE forms DISABLE TRIGGER ALL;

-- Delete in correct order (respecting foreign keys)
TRUNCATE TABLE system_metrics CASCADE;
TRUNCATE TABLE admin_logs CASCADE;
TRUNCATE TABLE query_logs CASCADE;
TRUNCATE TABLE query_sessions CASCADE;
TRUNCATE TABLE forms CASCADE;
TRUNCATE TABLE chunks CASCADE;
TRUNCATE TABLE documents CASCADE;
TRUNCATE TABLE collections CASCADE;

-- Re-enable triggers
ALTER TABLE chunks ENABLE TRIGGER ALL;
ALTER TABLE documents ENABLE TRIGGER ALL;
ALTER TABLE forms ENABLE TRIGGER ALL;

-- Verify cleanup
SELECT 'collections' as table_name, COUNT(*) as count FROM collections
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks
UNION ALL
SELECT 'forms', COUNT(*) FROM forms;

-- Output message
DO $$
BEGIN
    RAISE NOTICE '✅ All test data has been cleaned up successfully!';
END $$;
