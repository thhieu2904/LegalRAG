# Get the directory path from the first argument
param([string]$docPath)

# If no path provided, use default
if (-not $docPath) {
    $docPath = "D:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents\DOC_001\01. Dang ky khai sinh.doc"
}

# Extract directory from the file path
$docDirectory = Split-Path $docPath -Parent

Write-Host "Looking for .doc files in: $docDirectory"

# Get the .doc file from the specified directory
$docFile = Get-ChildItem "$docDirectory\*.doc" | Select-Object -First 1

if ($docFile) {
    Write-Host "Found file: $($docFile.FullName)"

    $word = New-Object -ComObject Word.Application
    $word.Visible = $false

    try {
        $doc = $word.Documents.Open($docFile.FullName)
        $content = $doc.Content.Text
        Write-Host "=== Content from $($docFile.Name) ==="
        Write-Host $content
        Write-Host "=== End Content ==="
        $doc.Close([ref]$false)
    } catch {
        Write-Host "ERROR: $($_.Exception.Message)"
    } finally {
        if ($word) {
            $word.Quit()
            [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
            Remove-Variable word
        }
    }
} else {
    Write-Host "No .doc file found in $docDirectory"
}
