"""
Test script to verify form template cleaning logic
Uses actual PDF file from output folder
"""
import sys
sys.path.insert(0, 'd:/Personal/LegalRAG/storage-service/src')

from extractors.document_cleaner import LegalDocumentCleaner
from extractors.pdf_extractor import PDFExtractor

# Path to actual PDF file
PDF_PATH = r"d:\Personal\LegalRAG\scripts\data_import\output\01. Đăng ký khai sinh.pdf"

# Sample noisy text from the actual response
sample_noisy_text = """
- Tờ khai đăng ký khai sinh theo mẫu (nếu người yêu cầu lựa chọn nộp hồ sơ theo hình thức trực tiếp hoặc gửi hồ sơ qua hệ thống bưu chính);
- Mẫu hộ tịch điện tử tương tác đăng ký khai sinh (do người yêu cầu cung cấp thông tin theo hướng dẫn trên Cổng dịch vụ công, nếu người yêu cầu lựa chọn nộp hồ sơ theo hình thức trực tuyến);
- Giấy chứng sinh; trường hợp không có Giấy chứng sinh thì nộp văn bản của người làm chứng xác nhận về việc sinh; nếu không có người làm chứng thì phải có giấy cam đoan về việc sinh.
- Trường hợp trẻ em bị bỏ rơi thì phải có biên bản về việc trẻ bị bỏ rơi do cơ quan có thẩm quyền lập.
- Trường hợp khai sinh cho trẻ em sinh ra do mang thai hộ phải có văn bản xác nhận của cơ sở y tế đã thực hiện kỹ thuật hỗ trợ sinh sản cho việc mang thai hộ.

Thông tin về người cha của người được khai sinh
(20) Họ, chữ đệm, tên;
(21) Ngày, tháng, năm sinh (tách biệt riêng 03 trường thông tin ngày, tháng, năm);
(22) Số định danh cá nhân;
(23) Giấy tờ tùy thân: Loại giấy tờ sử dụng (CCCD/CMND/Hộ chiếu/Giấy tờ hợp lệ thay thế); số, ngày, tháng, năm cấp, cơ quan cấp; bản chụp đính kèm;
(24) Dân tộc;
(25) Quốc tịch;
(26) Nơi cư trú (nơi thường trú/nơi tạm trú/nơi đang sinh sống).

Số lượng bản sao yêu cầu: ...
(28) Hồ sơ đính kèm theo quy định.

* Người yêu cầu cam đoan các thông tin cung cấp, nội dung đề nghị đăng ký khai sinh cho trẻ em là đúng sự thật, đã có sự thỏa thuận nhất trí của cha, mẹ trẻ theo quy định pháp luật và chịu hoàn toàn trách nhiệm trước pháp luật về nội dung cam đoan của mình.

NỘI DUNG MẪU HỘ TỊCH ĐIỆN TỬ TƯƠNG TÁC ĐĂNG KÝ KHAI SINH
I. Thông tin về người yêu cầu đăng ký khai sinh
(1) Họ, chữ đệm, tên;
(2) Số định danh cá nhân;
(3) Giấy tờ tùy thân: Loại giấy tờ sử dụng (CCCD/CMND/Hộ chiếu/Giấy tờ hợp lệ thay thế); số, ngày, tháng, năm cấp, cơ quan cấp; bản chụp đính kèm;
(4) Nơi cư trú (nơi thường trú/nơi tạm trú/nơi đang sinh sống);
(5) Quan hệ với người được khai sinh.
"""

# Another sample - chunk 2 from response
sample_noisy_text_2 = """
STT Tên biểu mẫu/ hồ sơ Nơi lưu/ người lưu trữ Thời gian lưu
01 Bộ hồ sơ theo Mục 5.a Ủy ban nhân dân cấp xã/Công chức Tư pháp-Hộ tịch Vĩnh viễn
02 Sổ đăng ký khai sinh Ủy ban nhân dân cấp xã/Công chức Tư pháp-Hộ tịch Vĩnh viễn

CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc

Đề nghị cơ quan đăng ký khai sinh cho người dưới đây:
Thông tin về Giấy chứng nhận kết hôn của cha, mẹ trẻ (nếu cha, mẹ trẻ đã ĐKKH):
Tôi cam đoan nội dung đề nghị đăng ký khai sinh trên đây là đúng sự thật, được sự thỏa thuận nhất trí của các bên liên quan theo quy định pháp luật.

Đề nghị cấp bản sao(6): Có
Số lượng:…….bản

(1) Ghi rõ tên cơ quan đăng ký khai sinh.
(2) Chỉ ghi trong trường hợp người có yêu cầu đăng ký hộ tịch chưa có/không cung cấp số định danh cá nhân/căn cước công dân/thẻ căn cước/chứng minh nhân dân; không cung cấp đầy đủ thông tin ngày, tháng, năm sinh.
"""

def test_cleaning():
    cleaner = LegalDocumentCleaner()
    
    print("=" * 80)
    print("TEST 1: Form template detection (line by line)")
    print("=" * 80)
    
    test_lines = [
        "(20) Họ, chữ đệm, tên;",
        "(21) Ngày, tháng, năm sinh (tách biệt riêng 03 trường thông tin ngày, tháng, năm);",
        "Số lượng bản sao yêu cầu: ...",
        "- Giấy chứng sinh; trường hợp không có Giấy chứng sinh thì nộp văn bản",
        "Thông tin về người cha của người được khai sinh",
        "NỘI DUNG MẪU HỘ TỊCH ĐIỆN TỬ TƯƠNG TÁC",
        "I. Thông tin về người yêu cầu đăng ký khai sinh",
    ]
    
    for line in test_lines:
        is_form = cleaner.is_form_template_line(line)
        score = cleaner.calculate_line_score(line)
        status = "❌ FORM (loại bỏ)" if is_form else "✅ CONTENT (giữ lại)"
        print(f"{status} | Score: {score:+.2f} | '{line[:60]}...'")
    
    print("\n" + "=" * 80)
    print("TEST 2: Full text cleaning - Sample 1")
    print("=" * 80)
    
    cleaned_1 = cleaner.clean_text(sample_noisy_text)
    print(f"\n📥 Original length: {len(sample_noisy_text)} chars")
    print(f"📤 Cleaned length: {len(cleaned_1)} chars")
    print(f"📉 Reduction: {(1 - len(cleaned_1)/len(sample_noisy_text))*100:.1f}%")
    print("\n--- Cleaned text ---")
    print(cleaned_1)
    
    print("\n" + "=" * 80)
    print("TEST 3: Full text cleaning - Sample 2")
    print("=" * 80)
    
    cleaned_2 = cleaner.clean_text(sample_noisy_text_2)
    print(f"\n📥 Original length: {len(sample_noisy_text_2)} chars")
    print(f"📤 Cleaned length: {len(cleaned_2)} chars")
    print(f"📉 Reduction: {(1 - len(cleaned_2)/len(sample_noisy_text_2))*100:.1f}%")
    print("\n--- Cleaned text ---")
    print(cleaned_2)
    
    print("\n" + "=" * 80)
    print("TEST 4: detect_and_remove_form_template() directly")
    print("=" * 80)
    
    result = cleaner.detect_and_remove_form_template(sample_noisy_text)
    print(f"\n📥 Original length: {len(sample_noisy_text)} chars")
    print(f"📤 After form removal: {len(result)} chars")
    print("\n--- Result ---")
    print(result)

def test_real_pdf():
    """Test with actual PDF file"""
    print("\n" + "=" * 80)
    print("TEST 5: Real PDF file - 01. Đăng ký khai sinh.pdf")
    print("=" * 80)
    
    # Read PDF file
    with open(PDF_PATH, 'rb') as f:
        pdf_data = f.read()
    
    # Extract text
    extractor = PDFExtractor()
    raw_text = extractor.extract_text(pdf_data)
    
    print(f"\n📄 PDF extracted: {len(raw_text)} chars")
    print("\n--- RAW TEXT (first 2000 chars) ---")
    print(raw_text[:2000])
    
    # Clean text
    cleaner = LegalDocumentCleaner()
    cleaned_text = cleaner.clean_text(raw_text)
    
    print("\n" + "-" * 80)
    print(f"\n📥 Original length: {len(raw_text)} chars")
    print(f"📤 Cleaned length: {len(cleaned_text)} chars")
    print(f"📉 Reduction: {(1 - len(cleaned_text)/len(raw_text))*100:.1f}%")
    
    print("\n--- CLEANED TEXT (first 2000 chars) ---")
    print(cleaned_text[:2000])
    
    print("\n--- CLEANED TEXT (last 1500 chars - should NOT have form template) ---")
    print(cleaned_text[-1500:])
    
    # Check if form content still exists
    form_indicators = [
        "(20) Họ, chữ đệm, tên",
        "(21) Ngày, tháng, năm sinh",
        "Số lượng bản sao yêu cầu: ...",
        "Thông tin về người cha của người được khai sinh",
    ]
    
    print("\n" + "=" * 80)
    print("FORM CONTENT CHECK:")
    print("=" * 80)
    found_any = False
    for indicator in form_indicators:
        if indicator in cleaned_text:
            print(f"❌ STILL FOUND: '{indicator}'")
            found_any = True
        else:
            print(f"✅ REMOVED: '{indicator}'")
    
    if not found_any:
        print("\n🎉 SUCCESS! All form template content has been removed!")
    else:
        print("\n⚠️ WARNING: Some form content still exists. May need to tune cleaning logic.")

if __name__ == "__main__":
    test_cleaning()
    test_real_pdf()
