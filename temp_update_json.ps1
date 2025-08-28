$jsonPath = "D:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents\DOC_007\07. Đăng ký khai sinh kết hợp nhận cha, mẹ, con.json"
$content = Get-Content $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json

# Update processing time
$content.metadata.processing_time_text = "05 ngày làm việc."

# Update fee_text
$content.metadata.fee_text = "Đối với trường hợp đăng ký khai sinh không đúng hạn: Nộp trực tiếp 8.000 đồng; nộp trực tuyến (áp dụng đến 31/12/2025): 4.000 đồng (áp dụng tại 32 xã, phường tại Phụ lục 1 kèm theo). Nhận cha, mẹ, con nộp trực tiếp: 15.000 đồng; nhận cha, mẹ, con nộp trực tuyến: 7.500 đồng. Phí cấp bản sao Giấy khai sinh, bản sao Trích lục đăng ký nhận cha, mẹ, con (nếu có yêu cầu): 8.000 đồng/bản sao. Phí cấp Trích lục/sự kiện hộ tịch đã đăng ký: 5.000 đồng/trường hợp (nộp trực tiếp), 10.000 đồng/trường hợp (nộp trực tuyến). Miễn lệ phí đối với các trường hợp sau: Đăng ký hộ tịch cho người thuộc hộ nghèo; người cao tuổi; người khuyết tật; người có công với cách mạng; đồng bào dân tộc thiểu số ở xã có điều kiện kinh tế - xã hội đặc biệt khó khăn; đăng ký khai sinh đúng hạn; đăng ký khai tử đúng hạn; giám hộ, kết hôn của công dân Việt Nam."

# Save the updated JSON
$content | ConvertTo-Json -Depth 10 | Set-Content $jsonPath -Encoding UTF8
Write-Host "Updated DOC_007 JSON successfully"
