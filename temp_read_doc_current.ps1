param(
    [Parameter(Mandatory=$true)]
    [string]$DocFilePath
)

Write-Host "Reading file: $DocFilePath"

if (-not (Test-Path $DocFilePath)) {
    Write-Host "File not found: $DocFilePath"
    exit 1
}

if (-not $DocFilePath.EndsWith('.doc')) {
    Write-Host "File is not a .doc file: $DocFilePath"
    exit 1
}

Write-Host "=== Content from $(Split-Path $DocFilePath -Leaf) ==="
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $document = $word.Documents.Open($DocFilePath)
    $content = $document.Content.Text
    Write-Host $content
    $document.Close()
    $word.Quit()
} catch {
    Write-Host "Error reading file: $($_.Exception.Message)"
}
Write-Host "=== End Content ==="
