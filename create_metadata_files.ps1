param(
    [string]$CollectionsPath = "d:\Personal\LegalRAG_Fixed\backend\data\storage\collections"
)

Write-Host "=== Creating metadata.json files for all collections ==="
Write-Host "Collections path: $CollectionsPath"
Write-Host "Date: $(Get-Date -Format 'MM/dd/yyyy HH:mm:ss')"
Write-Host ""

# Get all collection directories
$collectionDirs = Get-ChildItem -Path $CollectionsPath -Directory | Where-Object { $_.Name -like "quy_trinh_*" }

foreach ($collectionDir in $collectionDirs) {
    $collectionName = $collectionDir.Name
    $collectionPath = $collectionDir.FullName
    $metadataPath = Join-Path $collectionPath "metadata.json"

    Write-Host "Processing collection: $collectionName"

    # Check if metadata.json exists and has documents array
    $needsUpdate = $false
    if (Test-Path $metadataPath) {
        try {
            $existingMetadata = Get-Content $metadataPath -Raw | ConvertFrom-Json
            if (-not $existingMetadata.documents) {
                $needsUpdate = $true
                Write-Host "  - metadata.json exists but missing documents array, will update..."
            } else {
                Write-Host "  - metadata.json already has documents array, skipping..."
            }
        }
        catch {
            $needsUpdate = $true
            Write-Host "  - metadata.json exists but invalid format, will recreate..."
        }
    } else {
        $needsUpdate = $true
        Write-Host "  - metadata.json not found, will create..."
    }

    if (-not $needsUpdate) {
        continue
    }

    # Get all JSON files in the collection
    $documentsPath = Join-Path $collectionPath "documents"
    if (!(Test-Path $documentsPath)) {
        Write-Host "  - No documents folder found, skipping..."
        continue
    }

    $jsonFiles = Get-ChildItem -Path $documentsPath -Recurse -Filter "*.json"

    if ($jsonFiles.Count -eq 0) {
        Write-Host "  - No JSON files found, skipping..."
        continue
    }

    Write-Host "  - Found $($jsonFiles.Count) JSON files"

    # Create documents array
    $documents = @()

    foreach ($jsonFile in $jsonFiles) {
        try {
            $jsonContent = Get-Content $jsonFile.FullName -Raw | ConvertFrom-Json

            if ($jsonContent.metadata) {
                $docId = Split-Path (Split-Path $jsonFile.FullName -Parent) -Leaf

                $document = @{
                    "id" = $docId
                    "title" = $jsonContent.metadata.title
                    "code" = $jsonContent.metadata.code
                    "source" = $jsonContent.metadata.source
                    "effective_date" = $jsonContent.metadata.effective_date
                    "executing_agency" = $jsonContent.metadata.executing_agency
                    "applicant_type" = $jsonContent.metadata.applicant_type
                    "processing_time_text" = $jsonContent.metadata.processing_time_text
                    "fee_text" = $jsonContent.metadata.fee_text
                    "has_form" = $jsonContent.metadata.has_form
                }

                $documents += $document
            }
        }
        catch {
            Write-Host "  - Error processing $($jsonFile.FullName): $($_.Exception.Message)"
        }
    }

    if ($documents.Count -eq 0) {
        Write-Host "  - No valid documents found, skipping..."
        continue
    }

    # Determine collection type and description
    $collectionType = $collectionName
    $description = switch ($collectionName) {
        "quy_trinh_boi_thuong_nn" { "Bộ sưu tập các quy trình bồi thường nhà nước" }
        "quy_trinh_cap_ho_tich_cap_xa" { "Bộ sưu tập các quy trình hộ tịch cấp xã" }
        "quy_trinh_chung_thuc" { "Bộ sưu tập các quy trình chứng thực giấy tờ và hợp đồng tại Sở Tư pháp" }
        "quy_trinh_cong_chung" { "Bộ sưu tập các quy trình công chứng" }
        "quy_trinh_dau_gia_tai_san" { "Bộ sưu tập các quy trình đấu giá tài sản" }
        "quy_trinh_ho_tich_cap_tp" { "Bộ sưu tập các quy trình hộ tịch cấp tỉnh" }
        "quy_trinh_luat_su" { "Bộ sưu tập các quy trình luật sư" }
        "quy_trinh_nuoi_con_nuoi" { "Bộ sưu tập các quy trình nuôi con nuôi" }
        "quy_trinh_pbgdpl_htpldn" { "Bộ sưu tập các quy trình hỗ trợ pháp lý cho doanh nghiệp nhỏ và vừa" }
        "quy_trinh_quan_tai_vien" { "Bộ sưu tập các quy trình quản tài viên" }
        "quy_trinh_thua_phat_lai" { "Bộ sưu tập các quy trình thừa phát lại" }
        "quy_trinh_trong_tai_thuong_mai" { "Bộ sưu tập các quy trình trọng tài thương mại" }
        "quy_trinh_tu_van_phap_luat" { "Bộ sưu tập các quy trình tư vấn pháp luật" }
        default { "Bộ sưu tập các quy trình $collectionName" }
    }

    # Determine issuing authority
    $issuingAuthority = switch ($collectionName) {
        "quy_trinh_boi_thuong_nn" { "Sở Tư pháp" }
        "quy_trinh_cap_ho_tich_cap_xa" { "Ủy ban nhân dân cấp xã" }
        "quy_trinh_chung_thuc" { "Sở Tư pháp" }
        "quy_trinh_cong_chung" { "Sở Tư pháp" }
        "quy_trinh_dau_gia_tai_san" { "Sở Tư pháp" }
        "quy_trinh_ho_tich_cap_tp" { "Ủy ban nhân dân cấp tỉnh" }
        "quy_trinh_luat_su" { "Sở Tư pháp" }
        "quy_trinh_nuoi_con_nuoi" { "Ủy ban nhân dân cấp xã, Sở Tư pháp" }
        "quy_trinh_pbgdpl_htpldn" { "Sở Tư pháp" }
        "quy_trinh_quan_tai_vien" { "Sở Tư pháp" }
        "quy_trinh_thua_phat_lai" { "Sở Tư pháp" }
        "quy_trinh_trong_tai_thuong_mai" { "Sở Tư pháp" }
        "quy_trinh_tu_van_phap_luat" { "Sở Tư pháp" }
        default { "Sở Tư pháp" }
    }

    # Create metadata object
    $metadata = @{
        "collection_name" = $collectionName
        "description" = $description
        "collection_type" = $collectionType
        "created_date" = (Get-Date -Format "yyyy-MM-dd")
        "last_updated" = (Get-Date -Format "yyyy-MM-dd")
        "issuing_authority" = $issuingAuthority
        "documents" = $documents
    }

    # Convert to JSON and save
    $metadataJson = $metadata | ConvertTo-Json -Depth 10
    $metadataJson | Out-File -FilePath $metadataPath -Encoding UTF8

    Write-Host "  - Created metadata.json with $($documents.Count) documents"
}

Write-Host ""
Write-Host "=== Metadata creation completed ==="
Write-Host "Date: $(Get-Date -Format 'MM/dd/yyyy HH:mm:ss')"
