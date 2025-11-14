# JSON Editor Modal - Integration Testing Guide
# ================================================
# Test the complete JSON editing workflow with modal UI

Write-Host "🧪 JSON EDITOR MODAL TESTING - Complete Workflow" -ForegroundColor Cyan
Write-Host "=" * 60

# Test Configuration
$ADMIN_BASE_URL = "http://localhost:8001"
$COLLECTION = "quy_trinh_cap_ho_tich_cap_xa"
$DOC_ID = "DOC_001"

Write-Host ""
Write-Host "📋 Test Plan:" -ForegroundColor Yellow
Write-Host "  1. Verify JSON document exists"
Write-Host "  2. Test Document Preview Page loads"
Write-Host "  3. Test Edit JSON button appears (JSON only)"
Write-Host "  4. Test JSON Editor Modal opens"
Write-Host "  5. Test Save Only (no rebuild)"
Write-Host "  6. Test Save & Rebuild (with rebuild)"
Write-Host "  7. Verify backup creation"
Write-Host "  8. Check rebuild status"
Write-Host ""

# ==============================================================================
# TEST 1: Verify Document Exists
# ==============================================================================
Write-Host "TEST 1: Verify JSON Document Exists" -ForegroundColor Green
Write-Host "-" * 60

try {
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE_URL/api/collections/$COLLECTION/documents/$DOC_ID/json" -Method GET
    Write-Host "✅ Document found: $COLLECTION/$DOC_ID" -ForegroundColor Green
    Write-Host "   Title: $($response.data.metadata.title)" -ForegroundColor Gray
    Write-Host "   Chunks: $($response.data.content_chunks.Count)" -ForegroundColor Gray
} catch {
    Write-Host "❌ FAILED: Document not found" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ==============================================================================
# TEST 2: Manual UI Testing Checklist
# ==============================================================================
Write-Host "TEST 2: UI Integration Checklist (Manual)" -ForegroundColor Green
Write-Host "-" * 60

Write-Host ""
Write-Host "📝 Manual Testing Steps:" -ForegroundColor Yellow
Write-Host ""

Write-Host "STEP 1: Navigate to Document Review Page" -ForegroundColor Cyan
Write-Host "  URL: http://localhost:5173/admin/documents/$COLLECTION/$DOC_ID/preview/json"
Write-Host "  Expected: Document preview loads with JSON content"
Write-Host ""

Write-Host "STEP 2: Verify Edit Button" -ForegroundColor Cyan
Write-Host "  Location: Top-right controls bar"
Write-Host "  Expected: Green 'Chỉnh sửa' button next to 'Tải xuống'"
Write-Host "  Icon: Edit/Pencil icon"
Write-Host "  Note: Should only appear for JSON type (not DOCX)"
Write-Host ""

Write-Host "STEP 3: Open JSON Editor Modal" -ForegroundColor Cyan
Write-Host "  Action: Click 'Chỉnh sửa' button"
Write-Host "  Expected:"
Write-Host "    - Modal opens with Monaco Editor"
Write-Host "    - JSON content loads with syntax highlighting"
Write-Host "    - Validation status shows '✅ Valid JSON'"
Write-Host "    - Buttons: Cancel, 💾 Save Only, 💾 Save & Rebuild"
Write-Host ""

Write-Host "STEP 4: Test JSON Editing" -ForegroundColor Cyan
Write-Host "  Action: Modify JSON content (e.g., change title)"
Write-Host "  Test Cases:"
Write-Host "    a) Valid edit: Change title value"
Write-Host "       Expected: ✅ Valid JSON status maintained"
Write-Host "    b) Invalid edit: Remove closing brace"
Write-Host "       Expected: ❌ Shows syntax error message"
Write-Host "       Expected: Save buttons disabled"
Write-Host "    c) Fix error: Restore valid JSON"
Write-Host "       Expected: ✅ Valid JSON, buttons enabled"
Write-Host ""

Write-Host "STEP 5: Test Save Only (No Rebuild)" -ForegroundColor Cyan
Write-Host "  Action: Click '💾 Save Only' button"
Write-Host "  Expected:"
Write-Host "    - Confirmation modal appears"
Write-Host "    - Message: 'Save changes without rebuilding cache?'"
Write-Host "    - Warning: 'You can rebuild manually later from Database tab'"
Write-Host "  Action: Click 'Save Only' in confirmation"
Write-Host "  Expected:"
Write-Host "    - Success message: '✅ JSON document saved successfully'"
Write-Host "    - NO rebuild notification"
Write-Host "    - Modal closes automatically"
Write-Host "    - Document preview refreshes"
Write-Host ""

Write-Host "STEP 6: Test Save & Rebuild" -ForegroundColor Cyan
Write-Host "  Action: Open editor again, make another change"
Write-Host "  Action: Click '💾 Save & Rebuild' button"
Write-Host "  Expected:"
Write-Host "    - Confirmation modal appears"
Write-Host "    - Message: 'Save changes and rebuild cache for $COLLECTION/$DOC_ID?'"
Write-Host "    - Warning: '⚠️ Rebuild will take 5-10 seconds'"
Write-Host "  Action: Click 'Save & Rebuild' in confirmation"
Write-Host "  Expected:"
Write-Host "    - Success message: '✅ JSON document saved successfully (Rebuild started)'"
Write-Host "    - Modal closes automatically"
Write-Host "    - Document preview refreshes"
Write-Host ""

Write-Host "STEP 7: Verify Backup Creation" -ForegroundColor Cyan
Write-Host "  Backend API Check:"
$backupsUrl = "$ADMIN_BASE_URL/api/collections/$COLLECTION/documents/$DOC_ID/json/backups"
Write-Host "  GET $backupsUrl"
try {
    $backups = Invoke-RestMethod -Uri $backupsUrl -Method GET
    Write-Host "  ✅ Backups found: $($backups.backups.Count)" -ForegroundColor Green
    if ($backups.backups.Count -gt 0) {
        Write-Host "  Latest backup: $($backups.backups[0].filename)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ⚠️ Could not fetch backups: $_" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "STEP 8: Check Rebuild Status (if triggered)" -ForegroundColor Cyan
$rebuildStatusUrl = "$ADMIN_BASE_URL/api/collections/$COLLECTION/documents/$DOC_ID/json/rebuild/status"
Write-Host "  GET $rebuildStatusUrl"
try {
    $status = Invoke-RestMethod -Uri $rebuildStatusUrl -Method GET
    Write-Host "  Status: $($status.status)" -ForegroundColor Gray
    if ($status.status -eq "completed") {
        Write-Host "  ✅ Rebuild completed successfully" -ForegroundColor Green
        Write-Host "  Processing time: $($status.processing_time)s" -ForegroundColor Gray
    } elseif ($status.status -eq "running") {
        Write-Host "  🔄 Rebuild in progress..." -ForegroundColor Yellow
    } elseif ($status.status -eq "no_rebuild") {
        Write-Host "  ℹ️ No rebuild triggered (Save Only was used)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ⚠️ Could not fetch rebuild status: $_" -ForegroundColor Yellow
}
Write-Host ""

# ==============================================================================
# TEST 3: Error Handling Tests
# ==============================================================================
Write-Host "TEST 3: Error Handling Scenarios" -ForegroundColor Green
Write-Host "-" * 60
Write-Host ""

Write-Host "Scenario A: Invalid JSON Syntax" -ForegroundColor Cyan
Write-Host "  Test: Remove closing bracket in editor"
Write-Host "  Expected: Red validation error, save buttons disabled"
Write-Host ""

Write-Host "Scenario B: Network Error" -ForegroundColor Cyan
Write-Host "  Test: Stop admin service, try to save"
Write-Host "  Expected: Alert with error message"
Write-Host ""

Write-Host "Scenario C: Cancel Actions" -ForegroundColor Cyan
Write-Host "  Test 1: Click 'Cancel' in main modal"
Write-Host "    Expected: Modal closes, no changes saved"
Write-Host "  Test 2: Click 'Cancel' in confirmation modal"
Write-Host "    Expected: Returns to editor, can continue editing"
Write-Host ""

# ==============================================================================
# DEVELOPER NOTES
# ==============================================================================
Write-Host "=" * 60
Write-Host "📚 DEVELOPER NOTES" -ForegroundColor Magenta
Write-Host "=" * 60
Write-Host ""

Write-Host "Component Files:" -ForegroundColor Yellow
Write-Host "  - Modal: frontend/src/components/admin/modals/JsonEditorModal.tsx"
Write-Host "  - Page: frontend/src/pages/DocumentPreviewPage.tsx"
Write-Host "  - API: frontend/src/api/json-documents-api.ts"
Write-Host ""

Write-Host "Key Features:" -ForegroundColor Yellow
Write-Host "  ✅ Monaco Editor (VSCode engine) for JSON editing"
Write-Host "  ✅ Real-time JSON validation"
Write-Host "  ✅ Syntax highlighting and auto-formatting"
Write-Host "  ✅ Two-step confirmation (like Questions modal)"
Write-Host "  ✅ Manual rebuild control (default: False)"
Write-Host "  ✅ Backup creation on every save"
Write-Host "  ✅ Error handling with user-friendly messages"
Write-Host ""

Write-Host "Workflow Sync with Questions:" -ForegroundColor Yellow
Write-Host "  - Questions CRUD: Manual rebuild only (trigger_rebuild: False)"
Write-Host "  - JSON Documents CRUD: Manual rebuild only (trigger_rebuild: False)"
Write-Host "  - Both use confirmation modal pattern"
Write-Host "  - Both create backups before modification"
Write-Host "  - Consistent UI/UX across admin features"
Write-Host ""

Write-Host "API Endpoints Used:" -ForegroundColor Yellow
Write-Host "  GET  /api/collections/{collection}/documents/{doc_id}/json"
Write-Host "  PUT  /api/collections/{collection}/documents/{doc_id}/json"
Write-Host "  GET  /api/collections/{collection}/documents/{doc_id}/json/backups"
Write-Host "  GET  /api/collections/{collection}/documents/{doc_id}/json/rebuild/status"
Write-Host ""

Write-Host "Monaco Editor Shortcuts:" -ForegroundColor Yellow
Write-Host "  Ctrl+Shift+F  - Format JSON"
Write-Host "  Ctrl+F        - Find"
Write-Host "  Ctrl+H        - Find and Replace"
Write-Host "  Alt+↑/↓       - Move line up/down"
Write-Host "  Ctrl+/        - Toggle comment"
Write-Host ""

Write-Host "=" * 60
Write-Host "🎯 TESTING COMPLETE - Ready for Manual UI Testing" -ForegroundColor Green
Write-Host "=" * 60
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Start services: docker-compose -f docker-compose.dev.yml up -d"
Write-Host "  2. Frontend accessible at: http://localhost:5173"
Write-Host "  3. Navigate to: http://localhost:5173/admin/documents/$COLLECTION/$DOC_ID/preview/json"
Write-Host "  4. Follow manual testing checklist above"
Write-Host "  5. Verify all scenarios work as expected"
Write-Host ""

Write-Host "💡 Pro Tip:" -ForegroundColor Cyan
Write-Host "   Open browser DevTools (F12) to see:"
Write-Host "   - API request/response in Network tab"
Write-Host "   - Console logs for debugging"
Write-Host "   - React component state in React DevTools"
Write-Host ""
