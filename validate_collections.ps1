param(
    [Parameter(Mandatory=$false)]
    [string]$CollectionPath = "d:\Personal\LegalRAG_Fixed\backend\data\storage\collections",
    [Parameter(Mandatory=$false)]
    [switch]$DetailedReport,
    [Parameter(Mandatory=$false)]
    [switch]$FixIssues
)

Write-Host "=== LegalRAG Collection Validation Script ===" -ForegroundColor Cyan
Write-Host "Validating collections in: $CollectionPath" -ForegroundColor Yellow
Write-Host "Date: $(Get-Date)" -ForegroundColor Yellow
Write-Host ""

# Validation results
$results = @{
    TotalCollections = 0
    ValidCollections = 0
    InvalidCollections = 0
    TotalDocuments = 0
    ValidDocuments = 0
    InvalidDocuments = 0
    Issues = @()
}

function Test-JsonFile {
    param([string]$FilePath)

    try {
        $content = Get-Content $FilePath -Raw -Encoding UTF8
        $json = ConvertFrom-Json $content
        return @{ Valid = $true; Data = $json; Error = $null }
    }
    catch {
        return @{ Valid = $false; Data = $null; Error = $_.Exception.Message }
    }
}

function Test-DocumentStructure {
    param([object]$doc, [string]$docPath)

    $issues = @()

    # Check required metadata fields
    $requiredMetadataFields = @(
        "source", "title", "code", "issuing_authority",
        "effective_date", "executing_agency", "applicant_type",
        "processing_time_text", "fee_vnd", "fee_text",
        "has_form", "requirements_conditions", "legal_basis_references"
    )

    foreach ($field in $requiredMetadataFields) {
        if (-not $doc.metadata.PSObject.Properties.Name.Contains($field)) {
            $issues += "Missing metadata field: $field"
        }
    }

    # Check content_chunks structure
    if (-not $doc.PSObject.Properties.Name.Contains("content_chunks")) {
        $issues += "Missing content_chunks"
    }
    else {
        # Check if collection has expected number of chunks
        $collectionName = Split-Path (Split-Path (Split-Path (Split-Path $docPath -Parent) -Parent) -Parent) -Leaf
        Write-Host "DEBUG: docPath=$docPath, collectionName=$collectionName" -ForegroundColor Yellow
        $expectedChunkCount = if ($collectionName -eq "quy_trinh_cap_ho_tich_cap_xa") { 6 } else { 5 }

        if ($doc.content_chunks.Count -ne $expectedChunkCount) {
            $issues += "Expected $expectedChunkCount content_chunks, found $($doc.content_chunks.Count)"
        }
        else {
            # Validate each chunk has required fields
            for ($i = 0; $i -lt $doc.content_chunks.Count; $i++) {
                $chunk = $doc.content_chunks[$i]
                if (-not $chunk.PSObject.Properties.Name.Contains("chunk_id")) {
                    $issues += "Chunk $($i+1): Missing chunk_id"
                }
                if (-not $chunk.PSObject.Properties.Name.Contains("section_title")) {
                    $issues += "Chunk $($i+1): Missing section_title"
                }
                if (-not $chunk.PSObject.Properties.Name.Contains("content")) {
                    $issues += "Chunk $($i+1): Missing content"
                }
                if (-not $chunk.PSObject.Properties.Name.Contains("source_reference")) {
                    $issues += "Chunk $($i+1): Missing source_reference"
                }
                if (-not $chunk.PSObject.Properties.Name.Contains("keywords")) {
                    $issues += "Chunk $($i+1): Missing keywords"
                }
            }
        }
    }

    # Check fee_structure
    if (-not $doc.PSObject.Properties.Name.Contains("fee_structure")) {
        $issues += "Missing fee_structure"
    }

    return $issues
}

function Test-Collection {
    param([string]$collectionName, [string]$collectionPath)

    Write-Host "Validating collection: $collectionName" -ForegroundColor Green

    $collectionIssues = @()
    $validDocuments = 0
    $invalidDocuments = 0

    # Check metadata.json
    $metadataPath = Join-Path $collectionPath "metadata.json"
    if (Test-Path $metadataPath) {
        $metadataResult = Test-JsonFile $metadataPath
        if (-not $metadataResult.Valid) {
            $collectionIssues += "Invalid metadata.json: $($metadataResult.Error)"
        }
        else {
            # Validate metadata structure
            $metadata = $metadataResult.Data
            if (-not $metadata.PSObject.Properties.Name.Contains("documents")) {
                $collectionIssues += "metadata.json missing documents array"
            }
        }
    }
    else {
        $collectionIssues += "Missing metadata.json"
    }

    # Check documents
    $documentsPath = Join-Path $collectionPath "documents"
    if (Test-Path $documentsPath) {
        $docFolders = Get-ChildItem $documentsPath -Directory

        foreach ($docFolder in $docFolders) {
            $docPath = Join-Path $documentsPath $docFolder.Name

            # Find JSON file (any .json file in the folder)
            $jsonFiles = Get-ChildItem $docPath -Filter "*.json" -File

            $jsonFile = $jsonFiles | Where-Object { $_.Name -notlike "*questions*" -and $_.Name -notlike "*forms*" } | Select-Object -First 1

            if ($jsonFile) {
                $jsonPath = $jsonFile.FullName
                $docResult = Test-JsonFile $jsonPath

                if (-not $docResult.Valid) {
                    $collectionIssues += "DOC $($docFolder.Name): Invalid JSON - $($docResult.Error)"
                    $invalidDocuments++
                }
                else {
                    $docIssues = Test-DocumentStructure $docResult.Data $jsonPath
                    if ($docIssues.Count -gt 0) {
                        foreach ($issue in $docIssues) {
                            $collectionIssues += "DOC $($docFolder.Name): $issue"
                        }
                        $invalidDocuments++
                    }
                    else {
                        $validDocuments++
                    }
                }
            }
            else {
                $collectionIssues += "DOC $($docFolder.Name): Missing JSON file"
                $invalidDocuments++
            }
        }
    }
    else {
        $collectionIssues += "Missing documents folder"
    }

    $results.TotalDocuments += ($validDocuments + $invalidDocuments)

    return @{
        Name = $collectionName
        ValidDocuments = $validDocuments
        InvalidDocuments = $invalidDocuments
        Issues = $collectionIssues
        IsValid = ($collectionIssues.Count -eq 0)
    }
}

# Main validation loop
if (Test-Path $CollectionPath) {
    $collections = Get-ChildItem $CollectionPath -Directory | Where-Object { $_.Name -ne "collection_scan_report.json" -and $_.Name -ne "structure_classification_report.json" }

    foreach ($collection in $collections) {
        $results.TotalCollections++

        $collectionResult = Test-Collection $collection.Name $collection.FullName

        if ($collectionResult.IsValid) {
            $results.ValidCollections++
            Write-Host "  ✓ Valid" -ForegroundColor Green
        }
        else {
            $results.InvalidCollections++
            Write-Host "  ✗ Invalid ($($collectionResult.Issues.Count) issues)" -ForegroundColor Red
        }

        $results.ValidDocuments += $collectionResult.ValidDocuments
        $results.InvalidDocuments += $collectionResult.InvalidDocuments

        if ($DetailedReport -or $collectionResult.Issues.Count -gt 0) {
            foreach ($issue in $collectionResult.Issues) {
                $results.Issues += "$($collection.Name): $issue"
                if ($DetailedReport) {
                    Write-Host "    - $issue" -ForegroundColor Yellow
                }
            }
        }
    }
}
else {
    Write-Host "Collection path not found: $CollectionPath" -ForegroundColor Red
    exit 1
}

# Summary report
Write-Host ""
Write-Host "=== VALIDATION SUMMARY ===" -ForegroundColor Cyan
Write-Host "Total Collections: $($results.TotalCollections)" -ForegroundColor White
Write-Host "Valid Collections: $($results.ValidCollections)" -ForegroundColor Green
Write-Host "Invalid Collections: $($results.InvalidCollections)" -ForegroundColor Red
Write-Host "Total Documents: $($results.TotalDocuments)" -ForegroundColor White
Write-Host "Valid Documents: $($results.ValidDocuments)" -ForegroundColor Green
Write-Host "Invalid Documents: $($results.InvalidDocuments)" -ForegroundColor Red
Write-Host ""

if ($results.Issues.Count -gt 0) {
    Write-Host "=== ISSUES FOUND ===" -ForegroundColor Red
    foreach ($issue in $results.Issues) {
        Write-Host "- $issue" -ForegroundColor Yellow
    }
    Write-Host ""

    # Export detailed report
    $reportPath = Join-Path $CollectionPath "validation_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $results | ConvertTo-Json -Depth 10 | Out-File $reportPath -Encoding UTF8
    Write-Host "Detailed report saved to: $reportPath" -ForegroundColor Cyan
}
else {
    Write-Host "✓ All collections and documents are valid!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Validation completed at $(Get-Date)" -ForegroundColor Cyan
