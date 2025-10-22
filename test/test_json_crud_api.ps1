# JSON Document CRUD API - Test Script
# =====================================
# Test các endpoints của JSON Document CRUD

## Environment
$RAG_SERVICE = "http://localhost:8000"
$ADMIN_SERVICE = "http://localhost:8001"
$INTERNAL_API_KEY = "dev-internal-key"

# Test collection & document
$COLLECTION = "quy_trinh_cap_ho_tich_cap_xa"  # Real collection for testing
$DOC_ID = "DOC_001"  # Thay bằng doc_id thực tế

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "JSON DOCUMENT CRUD API - TESTING" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ============================================================================
# TEST 1: Get JSON Document (Admin API)
# ============================================================================
Write-Host "[TEST 1] Get JSON Document (Admin Service)" -ForegroundColor Yellow
Write-Host "GET $ADMIN_SERVICE/api/collections/$COLLECTION/documents/$DOC_ID/json`n" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "$ADMIN_SERVICE/api/collections/$COLLECTION/documents/$DOC_ID/json" `
        -Method GET `
        -ContentType "application/json"
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Document ID: $($response.doc_id)" -ForegroundColor Green
    Write-Host "Collection: $($response.collection)" -ForegroundColor Green
    Write-Host "Has data: $($response.data -ne $null)" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 1

# ============================================================================
# TEST 2: Get JSON Document (RAG Internal API - Direct)
# ============================================================================
Write-Host "[TEST 2] Get JSON Document (RAG Internal API)" -ForegroundColor Yellow
Write-Host "GET $RAG_SERVICE/api/internal/json/collections/$COLLECTION/documents/$DOC_ID`n" -ForegroundColor Gray

try {
    $headers = @{
        "X-Internal-API-Key" = $INTERNAL_API_KEY
    }
    
    $response = Invoke-RestMethod -Uri "$RAG_SERVICE/api/internal/json/collections/$COLLECTION/documents/$DOC_ID" `
        -Method GET `
        -Headers $headers `
        -ContentType "application/json"
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Document ID: $($response.doc_id)" -ForegroundColor Green
    Write-Host "File path: $($response.file_path)" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 1

# ============================================================================
# TEST 3: List JSON Backups (Admin API)
# ============================================================================
Write-Host "[TEST 3] List JSON Backups (Admin Service)" -ForegroundColor Yellow
Write-Host "GET $ADMIN_SERVICE/api/collections/$COLLECTION/documents/$DOC_ID/json/backups`n" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "$ADMIN_SERVICE/api/collections/$COLLECTION/documents/$DOC_ID/json/backups" `
        -Method GET `
        -ContentType "application/json"
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Backups found: $($response.total)" -ForegroundColor Green
    if ($response.total -gt 0) {
        Write-Host "Latest backup: $($response.data[0].filename)" -ForegroundColor Green
    }
    Write-Host ""
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 1

# ============================================================================
# TEST 4: Update JSON Document (Admin API) - Dry run without actual change
# ============================================================================
Write-Host "[TEST 4] Update JSON Document (Admin Service - Test mode)" -ForegroundColor Yellow
Write-Host "PUT $ADMIN_SERVICE/api/collections/$COLLECTION/documents/$DOC_ID/json`n" -ForegroundColor Gray
Write-Host "⚠️  This test requires existing JSON data. Skipping actual update." -ForegroundColor Yellow
Write-Host "   To test update, use manual Postman/curl with actual data.`n" -ForegroundColor Yellow

# Uncomment below to test actual update (requires valid JSON data)
<#
$testData = @{
    data = @{
        id = $DOC_ID
        title = "Test Document"
        sections = @()
    }
    trigger_rebuild = $false  # Set to false for testing to avoid rebuild
}

try {
    $response = Invoke-RestMethod -Uri "$ADMIN_SERVICE/api/collections/$COLLECTION/documents/$DOC_ID/json" `
        -Method PUT `
        -Body ($testData | ConvertTo-Json -Depth 10) `
        -ContentType "application/json"
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Backup created: $($response.backup_created)" -ForegroundColor Green
    Write-Host "Rebuild triggered: $($response.rebuild_triggered)" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
    Write-Host ""
}
#>

# ============================================================================
# TEST 5: Get Rebuild Status
# ============================================================================
Write-Host "[TEST 5] Get Rebuild Status" -ForegroundColor Yellow
Write-Host "GET $ADMIN_SERVICE/api/collections/$COLLECTION/documents/$DOC_ID/json/rebuild/status`n" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "$ADMIN_SERVICE/api/collections/$COLLECTION/documents/$DOC_ID/json/rebuild/status" `
        -Method GET `
        -ContentType "application/json"
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Status: $($response.data.status)" -ForegroundColor Green
    Write-Host "Is relevant: $($response.is_relevant)" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ FAILED: $_" -ForegroundColor Red
    Write-Host ""
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Tests completed" -ForegroundColor Green
Write-Host ""
Write-Host "📝 NOTES:" -ForegroundColor Yellow
Write-Host "   - Replace `$COLLECTION and `$DOC_ID with actual values" -ForegroundColor Gray
Write-Host "   - Test 4 (Update) requires manual testing with actual data" -ForegroundColor Gray
Write-Host "   - Use Swagger UI for interactive testing:" -ForegroundColor Gray
Write-Host "     * RAG Service: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "     * Admin Service: http://localhost:8001/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "🔗 API Endpoints:" -ForegroundColor Cyan
Write-Host "   Admin Service:" -ForegroundColor Gray
Write-Host "   - GET    /api/collections/{coll}/documents/{doc}/json" -ForegroundColor Gray
Write-Host "   - PUT    /api/collections/{coll}/documents/{doc}/json" -ForegroundColor Gray
Write-Host "   - GET    /api/collections/{coll}/documents/{doc}/json/backups" -ForegroundColor Gray
Write-Host "   - POST   /api/collections/{coll}/documents/{doc}/json/restore" -ForegroundColor Gray
Write-Host "   - POST   /api/collections/{coll}/documents/{doc}/json/rebuild" -ForegroundColor Gray
Write-Host "   - GET    /api/collections/{coll}/documents/{doc}/json/rebuild/status" -ForegroundColor Gray
Write-Host ""
Write-Host "   RAG Internal Service:" -ForegroundColor Gray
Write-Host "   - GET    /api/internal/json/collections/{coll}/documents/{doc}" -ForegroundColor Gray
Write-Host "   - PUT    /api/internal/json/collections/{coll}/documents/{doc}" -ForegroundColor Gray
Write-Host "   - GET    /api/internal/json/collections/{coll}/documents/{doc}/backups" -ForegroundColor Gray
Write-Host "   - POST   /api/internal/json/collections/{coll}/documents/{doc}/restore" -ForegroundColor Gray
Write-Host "   - DELETE /api/internal/json/collections/{coll}/documents/{doc}/backups/{backup}" -ForegroundColor Gray
Write-Host ""
