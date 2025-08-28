# Get the .doc file using wildcard
$docFile = Get-ChildItem "D:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents\DOC_007\*.doc" | Select-Object -First 1

if ($docFile) {
    Write-Host "Found file: $($docFile.FullName)"
    
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    
    try {
        $doc = $word.Documents.Open($docFile.FullName)
        $content = $doc.Content.Text
        Write-Host "=== DOC_007 Content ==="
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
    Write-Host "No .doc file found in DOC_007 directory"
}
