param(
    [string]$CollectionsPath = "d:\Personal\LegalRAG_Fixed\backend\data\storage\collections"
)

Write-Host "=== Checking JSON file structure across all collections ==="
Write-Host "Collections path: $CollectionsPath"
Write-Host "Date: $(Get-Date -Format 'MM/dd/yyyy HH:mm:ss')"
Write-Host ""

$totalFiles = 0
$validFiles = 0
$invalidFiles = 0
$missingMetadata = 0
$structureIssues = @()

# Get all collection directories
$collectionDirs = Get-ChildItem -Path $CollectionsPath -Directory | Where-Object { $_.Name -like "quy_trinh_*" }

foreach ($collectionDir in $collectionDirs) {
    $collectionName = $collectionDir.Name
    $collectionPath = $collectionDir.FullName
    $documentsPath = Join-Path $collectionPath "documents"

    if (!(Test-Path $documentsPath)) {
        Write-Host "Collection $collectionName - No documents folder found"
        continue
    }

    Write-Host "Checking collection: $collectionName"

    # Get all JSON files in the collection (excluding questions.json)
    $jsonFiles = Get-ChildItem -Path $documentsPath -Recurse -Filter "*.json" | Where-Object { $_.Name -ne "questions.json" }

    if ($jsonFiles.Count -eq 0) {
        Write-Host "  - No JSON files found"
        continue
    }

    Write-Host "  - Found $($jsonFiles.Count) JSON files"

    foreach ($jsonFile in $jsonFiles) {
        $totalFiles++
        $filePath = $jsonFile.FullName
        $relativePath = $filePath.Replace($CollectionsPath, "").TrimStart("\")

        try {
            $jsonContent = Get-Content $filePath -Raw | ConvertFrom-Json

            # Check if metadata object exists
            if (-not $jsonContent.metadata) {
                $missingMetadata++
                $structureIssues += "MISSING METADATA: $relativePath"
                Write-Host "  ❌ $relativePath - Missing metadata object"
                continue
            }

            # Check required metadata fields
            $requiredFields = @(
                "source", "title", "code", "issuing_authority",
                "effective_date", "executing_agency", "applicant_type",
                "processing_time_text", "fee_text", "has_form"
            )

            $missingFields = @()
            foreach ($field in $requiredFields) {
                if (-not (Get-Member -InputObject $jsonContent.metadata -Name $field -MemberType Properties)) {
                    $missingFields += $field
                }
            }

            if ($missingFields.Count -gt 0) {
                $invalidFiles++
                $structureIssues += "MISSING FIELDS ($($missingFields -join ', ')): $relativePath"
                Write-Host "  ❌ $relativePath - Missing fields: $($missingFields -join ', ')"
                continue
            }

            # Check if fee_structure exists
            if (-not $jsonContent.fee_structure) {
                $invalidFiles++
                $structureIssues += "MISSING FEE_STRUCTURE: $relativePath"
                Write-Host "  ❌ $relativePath - Missing fee_structure object"
                continue
            }

            # Check if content_chunks exists
            if (-not $jsonContent.content_chunks) {
                $invalidFiles++
                $structureIssues += "MISSING CONTENT_CHUNKS: $relativePath"
                Write-Host "  ❌ $relativePath - Missing content_chunks array"
                continue
            }

            $validFiles++
            Write-Host "  ✅ $relativePath - Valid structure"

        }
        catch {
            $invalidFiles++
            $structureIssues += "PARSE ERROR: $relativePath - $($_.Exception.Message)"
            Write-Host "  ❌ $relativePath - Parse error: $($_.Exception.Message)"
        }
    }
}

Write-Host ""
Write-Host "=== SUMMARY ==="
Write-Host "Total files checked: $totalFiles"
Write-Host "Valid files: $validFiles"
Write-Host "Invalid files: $invalidFiles"
Write-Host "Files missing metadata: $missingMetadata"
Write-Host ""

if ($structureIssues.Count -gt 0) {
    Write-Host "=== STRUCTURE ISSUES FOUND ==="
    foreach ($issue in $structureIssues) {
        Write-Host $issue
    }
} else {
    Write-Host "✅ All files have consistent structure!"
}

Write-Host ""
Write-Host "=== Check completed ==="
Write-Host "Date: $(Get-Date -Format 'MM/dd/yyyy HH:mm:ss')"
