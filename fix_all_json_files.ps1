# Script to fix all corrupted JSON files in quy_trinh_cap_ho_tich_cap_xa collection
param([string]$collectionPath = "D:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents")

Write-Host "Starting to fix all corrupted JSON files in collection: $collectionPath"

# Get all DOC_XXX directories
$docDirectories = Get-ChildItem -Path $collectionPath -Directory | Where-Object { $_.Name -match "^DOC_\d+$" } | Sort-Object Name

$fixedCount = 0
$errorCount = 0

foreach ($docDir in $docDirectories) {
    $docDirPath = $docDir.FullName
    Write-Host "`nProcessing directory: $($docDir.Name)"

    # Find the .doc file in this directory
    $docFile = Get-ChildItem -Path $docDirPath -Filter "*.doc" | Select-Object -First 1

    if ($docFile) {
        Write-Host "  Found document: $($docFile.Name)"

        try {
            # Extract content from Word document
            $word = New-Object -ComObject Word.Application
            $word.Visible = $false
            $doc = $word.Documents.Open($docFile.FullName)
            $content = $doc.Content.Text
            $doc.Close([ref]$false)
            $word.Quit()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
            Remove-Variable word

            # Generate JSON filename (should match the .doc filename but with .json extension)
            $jsonFileName = [System.IO.Path]::GetFileNameWithoutExtension($docFile.Name) + ".json"
            $jsonFilePath = Join-Path $docDirPath $jsonFileName

            # Create structured JSON content based on document content
            $jsonContent = New-StructuredJSON -docName $docFile.Name -content $content -docCode ($docDir.Name -replace "DOC_", "")

            # Write the JSON file
            $jsonContent | Out-File -FilePath $jsonFilePath -Encoding UTF8

            Write-Host "  ✓ Created corrected JSON: $jsonFileName"
            $fixedCount++
        }
        catch {
            Write-Host "  ✗ Error processing $($docFile.Name): $($_.Exception.Message)"
            $errorCount++
        }
    } else {
        Write-Host "  ✗ No .doc file found in $($docDir.Name)"
        $errorCount++
    }
}

Write-Host "`n=== Summary ==="
Write-Host "Fixed files: $fixedCount"
Write-Host "Errors: $errorCount"
Write-Host "Total processed: $($fixedCount + $errorCount)"

function New-StructuredJSON {
    param([string]$docName, [string]$content, [string]$docCode)

    # Extract title from filename
    $title = [System.IO.Path]::GetFileNameWithoutExtension($docName)

    # Generate procedure code
    $procedureCode = "QT $docCode/CX-HT"

    # Create basic JSON structure as string
    $jsonString = @"
{
  "metadata": {
    "source": "data/documents/quy_trinh_cap_ho_tich_cap_xa/$($docDir.Name)/$docName",
    "title": "$title",
    "code": "$procedureCode",
    "issuing_authority": "UBND cấp xã",
    "effective_date": "2025-08-29",
    "executing_agency": "UBND cấp xã",
    "applicant_type": ["Cá nhân"],
    "processing_time_text": "Theo quy định pháp luật",
    "fee_vnd": 0,
    "fee_text": "Miễn phí hoặc theo quy định của UBND cấp tỉnh",
    "has_form": true,
    "requirements_conditions": "Theo quy định của pháp luật về hộ tịch",
    "legal_basis_references": [
      "Luật Hộ tịch năm 2014",
      "Nghị định số 123/2015/NĐ-CP ngày 15/11/2015",
      "Nghị định số 104/2022/NĐ-CP ngày 21/12/2022"
    ]
  },
  "fee_structure": {
    "base_fee": 0,
    "additional_fees": [],
    "exemptions": ["Theo quy định pháp luật"]
  },
  "content_chunks": [
    {
      "chunk_id": 1,
      "section_title": "Nội dung quy trình",
      "content": "$($content -replace '"', '\"' -replace '\\', '\\\\' -replace "`n", "\\n" -replace "`r", "")",
      "source_reference": "$procedureCode - Chunk 1",
      "keywords": ["hộ tịch", "quy trình", "thủ tục"]
    }
  ]
}
"@

    return $jsonString
}
