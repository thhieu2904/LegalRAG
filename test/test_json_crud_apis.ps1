# JSON CRUD API Test Script
# Run this after starting both RAG Service (8000) and Admin Service (8001)

Write-Host "🧪 JSON CRUD API Testing Script" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Configuration
$RAG_BASE = "http://localhost:8000"
$ADMIN_BASE = "http://localhost:8001"
$COLLECTION = "Bo_thu_tuc"
$DOC_ID = "DOC_001"
$INTERNAL_API_KEY = "dev-internal-key"

# Test counter
$testCount = 0
$passCount = 0
$failCount = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [scriptblock]$TestCode
    )
    
    $script:testCount++
    Write-Host "`n[$script:testCount] Testing: $Name" -ForegroundColor Yellow
    
    try {
        & $TestCode
        $script:passCount++
        Write-Host "✅ PASSED" -ForegroundColor Green
        return $true
    }
    catch {
        $script:failCount++
        Write-Host "❌ FAILED: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test 1: RAG Service Health
Test-Endpoint "RAG Service Health Check" {
    $response = Invoke-RestMethod -Uri "$RAG_BASE/health"
    if ($response.status -ne "healthy") {
        throw "RAG Service not healthy"
    }
    Write-Host "   Status: $($response.status)" -ForegroundColor Gray
}

# Test 2: Admin Service Health
Test-Endpoint "Admin Service Health Check" {
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/health"
    if ($response.status -ne "healthy") {
        throw "Admin Service not healthy"
    }
    Write-Host "   Status: $($response.status)" -ForegroundColor Gray
}

# Test 3: List Collections (Admin API)
Test-Endpoint "List Collections" {
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections"
    if (-not $response.success) {
        throw "Failed to list collections"
    }
    Write-Host "   Found $($response.total) collections" -ForegroundColor Gray
}

# Test 4: List Documents (Admin API)
Test-Endpoint "List Documents in Collection" {
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections/$COLLECTION/documents"
    if (-not $response.success) {
        throw "Failed to list documents"
    }
    Write-Host "   Found $($response.total) documents" -ForegroundColor Gray
}

# Test 5: Get JSON Document (RAG Internal API)
Test-Endpoint "Get JSON (RAG Internal API)" {
    $headers = @{
        "X-Internal-API-Key" = $INTERNAL_API_KEY
    }
    $response = Invoke-RestMethod -Uri "$RAG_BASE/api/internal/json/collections/$COLLECTION/documents/$DOC_ID" -Headers $headers
    if (-not $response.success) {
        throw "Failed to get JSON from RAG Internal API"
    }
    Write-Host "   Document ID: $($response.data.id)" -ForegroundColor Gray
    Write-Host "   Document Title: $($response.data.title)" -ForegroundColor Gray
}

# Test 6: Get JSON Document (Admin API)
Test-Endpoint "Get JSON (Admin API)" {
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections/$COLLECTION/documents/$DOC_ID/json"
    if (-not $response.success) {
        throw "Failed to get JSON from Admin API"
    }
    Write-Host "   Document ID: $($response.data.id)" -ForegroundColor Gray
    Write-Host "   Document Title: $($response.data.title)" -ForegroundColor Gray
    
    # Store original for comparison
    $script:originalData = $response.data
}

# Test 7: Update JSON Document (Admin API)
Test-Endpoint "Update JSON Document" {
    $updateData = @{
        data = @{
            id = $DOC_ID
            title = "🧪 TEST UPDATED - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
            sections = $script:originalData.sections
            metadata = @{
                test_updated = $true
                updated_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
            }
        }
        trigger_rebuild = $false
    } | ConvertTo-Json -Depth 10
    
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections/$COLLECTION/documents/$DOC_ID/json" `
        -Method PUT `
        -ContentType "application/json" `
        -Body $updateData
    
    if (-not $response.success) {
        throw "Failed to update JSON"
    }
    Write-Host "   Backup created: $($response.backup_created)" -ForegroundColor Gray
    Write-Host "   Backup path: $($response.backup_path)" -ForegroundColor Gray
    
    # Store backup filename for restore test
    $script:backupFilename = Split-Path $response.backup_path -Leaf
}

# Test 8: Verify Update
Test-Endpoint "Verify JSON Updated" {
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections/$COLLECTION/documents/$DOC_ID/json"
    if (-not $response.data.title.StartsWith("🧪 TEST UPDATED")) {
        throw "JSON was not updated correctly"
    }
    Write-Host "   New Title: $($response.data.title)" -ForegroundColor Gray
}

# Test 9: List Backups
Test-Endpoint "List JSON Backups" {
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections/$COLLECTION/documents/$DOC_ID/json/backups"
    if (-not $response.success) {
        throw "Failed to list backups"
    }
    Write-Host "   Total backups: $($response.total)" -ForegroundColor Gray
    if ($response.total -gt 0) {
        Write-Host "   Latest backup: $($response.data[0].filename)" -ForegroundColor Gray
        Write-Host "   Backup size: $($response.data[0].size) bytes" -ForegroundColor Gray
    }
}

# Test 10: Restore from Backup
Test-Endpoint "Restore from Backup" {
    if (-not $script:backupFilename) {
        throw "No backup filename available"
    }
    
    $restoreData = @{
        backup_filename = $script:backupFilename
        trigger_rebuild = $false
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections/$COLLECTION/documents/$DOC_ID/json/restore" `
        -Method POST `
        -ContentType "application/json" `
        -Body $restoreData
    
    if (-not $response.success) {
        throw "Failed to restore from backup"
    }
    Write-Host "   Restored from: $($response.restored_from)" -ForegroundColor Gray
    Write-Host "   Safety backup created: $($response.safety_backup_created)" -ForegroundColor Gray
}

# Test 11: Verify Restore
Test-Endpoint "Verify JSON Restored" {
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections/$COLLECTION/documents/$DOC_ID/json"
    if ($response.data.title -eq $script:originalData.title) {
        Write-Host "   Title restored to original: $($response.data.title)" -ForegroundColor Gray
    } else {
        throw "JSON was not restored to original state"
    }
}

# Test 12: Trigger Rebuild (Optional - commented out by default)
# Uncomment if you want to test rebuild functionality
<#
Test-Endpoint "Trigger Manual Rebuild" {
    $rebuildData = @{
        scope = "document"
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections/$COLLECTION/documents/$DOC_ID/json/rebuild" `
        -Method POST `
        -ContentType "application/json" `
        -Body $rebuildData
    
    if (-not $response.success) {
        throw "Failed to trigger rebuild"
    }
    Write-Host "   Rebuild PID: $($response.pid)" -ForegroundColor Gray
    Write-Host "   Rebuild status: $($response.status)" -ForegroundColor Gray
}

# Test 13: Check Rebuild Status
Test-Endpoint "Check Rebuild Status" {
    Start-Sleep -Seconds 2
    $response = Invoke-RestMethod -Uri "$ADMIN_BASE/api/collections/$COLLECTION/documents/$DOC_ID/json/rebuild/status"
    Write-Host "   Status: $($response.data.status)" -ForegroundColor Gray
    Write-Host "   Progress: $($response.data.progress)%" -ForegroundColor Gray
}
#>

# Summary
Write-Host "`n" -NoNewline
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🎯 TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Total Tests: $testCount" -ForegroundColor White
Write-Host "✅ Passed: $passCount" -ForegroundColor Green
Write-Host "❌ Failed: $failCount" -ForegroundColor Red

if ($failCount -eq 0) {
    Write-Host "`n🎉 ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "JSON CRUD APIs are working correctly!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ SOME TESTS FAILED" -ForegroundColor Yellow
    Write-Host "Please check the errors above" -ForegroundColor Yellow
}

Write-Host "`n📚 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Review test results above" -ForegroundColor Gray
Write-Host "   2. Check service logs for any errors" -ForegroundColor Gray
Write-Host "   3. Verify backup files in: rag_service/data/storage/collections/$COLLECTION/documents/$DOC_ID/" -ForegroundColor Gray
Write-Host "   4. Test rebuild functionality (uncomment Tests 12-13)" -ForegroundColor Gray
Write-Host "`n"
