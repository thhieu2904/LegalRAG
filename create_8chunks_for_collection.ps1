# Script tạo JSON 8 chunks cho collection quy_trinh_chung_thuc_v2
# Thực thi trong thư mục: d:/Personal/LegalRAG_Fixed

$templatePath = "d:/Personal/LegalRAG_Fixed/template_8chunks.json"
$collectionPath = "d:/Personal/LegalRAG_Fixed/backend/data/storage/collections/quy_trinh_chung_thuc_v2/documents"

# Mapping thông tin cho từng DOC
$docMapping = @{
    "DOC_01_CHUNG" = @{
        title = "Thủ tục cấp bản sao từ sổ gốc"
        code = "QT 01/CT-HCTP"
        keywords = @("cấp bản sao", "sổ gốc", "sở tư pháp", "hộ tịch")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Hộ tịch 2014")
    }
    "DOC_02_CHUNG" = @{
        title = "Thủ tục chứng thực bản sao từ bản chính giấy tờ, văn bản"
        code = "QT 02/CT-HCTP"
        keywords = @("chứng thực", "bản sao", "bản chính", "giấy tờ", "văn bản")
        references = @("Nghị định số 23/2015/NĐ-CP", "Nghị định số 07/2025/NĐ-CP")
    }
    "DOC_03_CHUNG" = @{
        title = "Thủ tục chứng thực chữ ký trong các giấy tờ, văn bản"
        code = "QT 03/CT-HCTP"
        keywords = @("chứng thực", "chữ ký", "giấy tờ", "văn bản", "ủy quyền")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Công chứng 2014")
    }
    "DOC_04" = @{
        title = "Thủ tục chứng thực hợp đồng, giao dịch liên quan đến tài sản là động sản, quyền sử dụng đất và nhà ở"
        code = "QT 04/CT-HCTP"
        keywords = @("chứng thực", "hợp đồng", "giao dịch", "động sản", "quyền sử dụng đất", "nhà ở")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Dân sự 2015")
    }
    "DOC_05" = @{
        title = "Thủ tục chứng thực di chúc"
        code = "QT 05/CT-HCTP"
        keywords = @("chứng thực", "di chúc", "tài sản", "thừa kế")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Dân sự 2015")
    }
    "DOC_06" = @{
        title = "Thủ tục chứng thực văn bản từ chối nhận di sản"
        code = "QT 06/CT-HCTP"
        keywords = @("chứng thực", "từ chối", "di sản", "thừa kế")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Dân sự 2015")
    }
    "DOC_07" = @{
        title = "Thủ tục chứng thực văn bản thỏa thuận phân chia di sản mà di sản là động sản, quyền sử dụng đất, nhà ở"
        code = "QT 07/CT-HCTP"
        keywords = @("chứng thực", "thỏa thuận", "phân chia", "di sản", "động sản", "quyền sử dụng đất", "nhà ở")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Dân sự 2015")
    }
    "DOC_08" = @{
        title = "Thủ tục chứng thực văn bản khai nhận di sản mà di sản là động sản, quyền sử dụng đất, nhà ở"
        code = "QT 08/CT-HCTP"
        keywords = @("chứng thực", "khai nhận", "di sản", "động sản", "quyền sử dụng đất", "nhà ở")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Dân sự 2015")
    }
    "DOC_09" = @{
        title = "Thủ tục chứng thực việc sửa đổi, bổ sung, hủy bỏ hợp đồng, giao dịch"
        code = "QT 09/CT-HCTP"
        keywords = @("chứng thực", "sửa đổi", "bổ sung", "hủy bỏ", "hợp đồng", "giao dịch")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Dân sự 2015")
    }
    "DOC_10" = @{
        title = "Thủ tục sửa lỗi sai sót trong hợp đồng, giao dịch"
        code = "QT 10/CT-HCTP"
        keywords = @("sửa lỗi", "sai sót", "hợp đồng", "giao dịch", "chứng thực")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Công chứng 2014")
    }
    "DOC_11" = @{
        title = "Thủ tục cấp bản sao có chứng thực từ bản chính hợp đồng, giao dịch đã được chứng thực"
        code = "QT 11/CT-HCTP"
        keywords = @("cấp bản sao", "chứng thực", "bản chính", "hợp đồng", "giao dịch")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Công chứng 2014")
    }
    "DOC_12" = @{
        title = "Chứng thực chữ ký người dịch mà người dịch là cộng tác viên dịch thuật của Ủy ban nhân dân cấp xã"
        code = "QT 12/CT-HCTP"
        keywords = @("chứng thực", "chữ ký", "người dịch", "cộng tác viên", "dịch thuật", "ủy ban nhân dân")
        references = @("Nghị định số 23/2015/NĐ-CP", "Luật Công chứng 2014")
    }
}

# Đọc template JSON
$template = Get-Content -Path $templatePath -Raw | ConvertFrom-Json

# Xử lý từng thư mục DOC
foreach ($docFolder in Get-ChildItem -Path $collectionPath -Directory) {
    $docId = $docFolder.Name
    $docPath = $docFolder.FullName

    Write-Host "Đang xử lý: $docId"

    # Kiểm tra xem có file DOC không
    $docFile = Get-ChildItem -Path $docPath -Filter "*.doc" | Select-Object -First 1

    if ($docFile) {
        Write-Host "  Có file DOC: $($docFile.Name)"

        # Lấy thông tin mapping
        $docInfo = $docMapping[$docId]

        if ($docInfo) {
            # Sao chép template và thay thế thông tin
            $jsonContent = $template | ConvertTo-Json -Depth 10

            # Thay thế placeholders
            $jsonContent = $jsonContent -replace "DOC_XX_CHUNG", $docId
            $jsonContent = $jsonContent -replace "QT XX/CT-HCTP", $docInfo.code
            $jsonContent = $jsonContent -replace "Tên thủ tục chứng thực", $docInfo.title

            # Thay thế keywords
            $keywordsJson = $docInfo.keywords | ConvertTo-Json
            $jsonContent = $jsonContent -replace '"chứng thực",\s*"bản sao",\s*"chữ ký",\s*"hợp đồng",\s*"di chúc",\s*"sở tư pháp",\s*"ủy ban nhân dân"', $keywordsJson

            # Thay thế references
            $referencesJson = $docInfo.references | ConvertTo-Json
            $jsonContent = $jsonContent -replace '"Nghị định số 23/2015/NĐ-CP",\s*"Nghị định số 07/2025/NĐ-CP",\s*"Thông tư số 01/2020/TT-BTP"', $referencesJson

            # Lưu file JSON
            $jsonPath = Join-Path -Path $docPath -ChildPath "8chunks.json"
            $jsonContent | Out-File -FilePath $jsonPath -Encoding UTF8

            Write-Host "  ✅ Đã tạo: 8chunks.json"
        } else {
            Write-Host "  ⚠️  Không có thông tin mapping cho $docId"
        }
    } else {
        Write-Host "  ⚠️  Không có file DOC trong thư mục $docId"

        # Tạo placeholder JSON với thông tin cơ bản
        $jsonContent = $template | ConvertTo-Json -Depth 10
        $jsonContent = $jsonContent -replace "DOC_XX_CHUNG", $docId
        $jsonContent = $jsonContent -replace "QT XX/CT-HCTP", "QT XX/CT-HCTP"
        $jsonContent = $jsonContent -replace "Tên thủ tục chứng thực", "Tên thủ tục chứng thực - $docId"

        $jsonPath = Join-Path -Path $docPath -ChildPath "8chunks_placeholder.json"
        $jsonContent | Out-File -FilePath $jsonPath -Encoding UTF8

        Write-Host "  📝 Đã tạo placeholder: 8chunks_placeholder.json"
    }
}

Write-Host "`n🎉 Hoàn thành tạo JSON 8 chunks cho tất cả thư mục!"
