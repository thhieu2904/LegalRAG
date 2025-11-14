#!/usr/bin/env pwsh
# Phase 2 Integration Verification Script
# Checks that all files are in place and ready for testing

Write-Host "🔍 Phase 2 Frontend Integration - Verification" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

$errors = @()
$warnings = @()
$successes = @()

# Check Frontend Files
Write-Host "`n📂 Checking Frontend Files..." -ForegroundColor Yellow

$filesToCheck = @(
    "frontend/src/hooks/useFormDownload.ts",
    "frontend/src/api/storage-api.ts",
    "frontend/src/components/forms/FormRenderer.tsx",
    "frontend/src/components/forms/FormRenderer.css"
)

foreach ($file in $filesToCheck) {
    $fullPath = Join-Path -Path "." -ChildPath $file
    if (Test-Path $fullPath) {
        $size = (Get-Item $fullPath).Length
        Write-Host "  ✅ $file ($size bytes)" -ForegroundColor Green
        $successes += $file
    } else {
        Write-Host "  ❌ $file NOT FOUND" -ForegroundColor Red
        $errors += "Missing file: $file"
    }
}

# Check Key Code Elements
Write-Host "`n🔧 Checking Code Elements..." -ForegroundColor Yellow

$checks = @(
    @{
        File = "frontend/src/components/forms/FormRenderer.tsx"
        Pattern = "import.*useFormDownload"
        Description = "useFormDownload import"
    },
    @{
        File = "frontend/src/components/forms/FormRenderer.tsx"
        Pattern = "handleDownloadForm"
        Description = "Download handler function"
    },
    @{
        File = "frontend/src/components/forms/FormRenderer.tsx"
        Pattern = "form-notification"
        Description = "Notification class name"
    },
    @{
        File = "frontend/src/components/forms/FormRenderer.tsx"
        Pattern = "download-button"
        Description = "Download button class"
    },
    @{
        File = "frontend/src/api/storage-api.ts"
        Pattern = "saveFormToStorage"
        Description = "Save form function"
    },
    @{
        File = "frontend/src/api/storage-api.ts"
        Pattern = "downloadSavedForm"
        Description = "Download form function"
    },
    @{
        File = "frontend/src/hooks/useFormDownload.ts"
        Pattern = "downloadForm"
        Description = "Download hook"
    },
    @{
        File = "frontend/src/components/forms/FormRenderer.css"
        Pattern = ".form-notification"
        Description = "Notification CSS"
    },
    @{
        File = "frontend/src/components/forms/FormRenderer.css"
        Pattern = ".download-button"
        Description = "Download button CSS"
    }
)

foreach ($check in $checks) {
    $fullPath = Join-Path -Path "." -ChildPath $check.File
    $content = Get-Content $fullPath -Raw
    
    if ($content -match $check.Pattern) {
        Write-Host "  ✅ $($check.Description)" -ForegroundColor Green
        $successes += $check.Description
    } else {
        Write-Host "  ❌ $($check.Description) NOT FOUND" -ForegroundColor Red
        $errors += "Missing: $($check.Description) in $($check.File)"
    }
}

# Summary
Write-Host "`n" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

Write-Host "`n✅ Successful Checks: $($successes.Count)" -ForegroundColor Green
Write-Host "❌ Errors: $($errors.Count)" -ForegroundColor Red
Write-Host "⚠️  Warnings: $($warnings.Count)" -ForegroundColor Yellow

if ($errors.Count -gt 0) {
    Write-Host "`nERRORS:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  • $_" -ForegroundColor Red }
}

if ($warnings.Count -gt 0) {
    Write-Host "`nWARNINGS:" -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "  • $_" -ForegroundColor Yellow }
}

# Next Steps
Write-Host "`n📋 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Start all services: docker-compose up -d" -ForegroundColor White
Write-Host "  2. Verify services: docker-compose ps" -ForegroundColor White
Write-Host "  3. Open browser: http://localhost:3000" -ForegroundColor White
Write-Host "  4. Load a form and test download functionality" -ForegroundColor White
Write-Host "  5. Follow testing checklist in PHASE_2_COMPLETION_SUMMARY.md" -ForegroundColor White

if ($errors.Count -eq 0) {
    Write-Host "`n🎉 All checks passed! Ready for testing!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n❌ Fix errors before proceeding!" -ForegroundColor Red
    exit 1
}
