import os
import win32com.client
import re
import json

def read_doc_content_clean_enhanced(doc_path):
    """Enhanced function to read and clean Word document content"""

    try:
        print("🔄 Đang mở Word Application...")
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False

        print("📖 Đang đọc file Word...")
        doc = word.Documents.Open(doc_path)

        print("📝 Đang trích xuất nội dung...")
        content = doc.Content.Text

        print("🔒 Đang đóng file...")
        doc.Close()
        word.Quit()

        print("✅ Đã đọc thành công!")
        print(f"📊 Độ dài nội dung thô: {len(content)} ký tự")

        # Enhanced cleaning
        print("🧹 Đang làm sạch nội dung...")

        # Replace special characters
        content = content.replace('\r', '\n')
        content = content.replace('\t', ' ')
        content = content.replace('\f', '\n')
        content = content.replace('\v', '\n')

        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r' \s+', ' ', content)

        # Remove control characters but keep newlines
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)

        # Clean up header/footer artifacts
        content = re.sub(r'SỞ TƯ PHÁP.*?QUY TRÌNH', 'QUY TRÌNH', content, flags=re.DOTALL)
        content = re.sub(r'Mã hiệu:.*?Lần ban hành:', '', content, flags=re.DOTALL)
        content = re.sub(r'Ngày ban hành:.*?\n', '', content)

        # Remove page numbers and artifacts
        content = re.sub(r'\n\d+\n', '\n', content)
        content = re.sub(r'\n\s*\d+\s*\n', '\n', content)

        # Clean up multiple spaces
        content = re.sub(r' +', ' ', content)

        # Remove empty lines at start and end
        content = content.strip()

        print(f"📊 Độ dài nội dung sau khi làm sạch: {len(content)} ký tự")

        return content

    except Exception as e:
        print(f"❌ Lỗi khi đọc file: {e}")
        return f"Error reading file: {e}"

def demo_enhanced_reading():
    """Demo enhanced Word reading"""

    doc_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents\DOC_001\01. Đăng ký khai sinh.doc"

    print("=== DEMO ĐỌC WORD CẢI TIẾN ===")
    print(f"📄 File: {os.path.basename(doc_path)}")
    print()

    if not os.path.exists(doc_path):
        print(f"❌ Không tìm thấy file: {doc_path}")
        return

    # Read with enhanced cleaning
    content = read_doc_content_clean_enhanced(doc_path)

    if content.startswith("Error"):
        print(f"❌ Lỗi: {content}")
        return

    print("\n" + "="*60)
    print("📋 NỘI DUNG ĐÃ LÀM SẠCH (500 ký tự đầu):")
    print("="*60)
    print(content[:500])
    print("="*60)

    print("\n" + "="*60)
    print("📋 NỘI DUNG GIỮA FILE (từ 2000-2500):")
    print("="*60)
    if len(content) > 2500:
        print(content[2000:2500])
    else:
        print("File quá ngắn")
    print("="*60)

    # Save cleaned content
    cleaned_path = r"d:\Personal\LegalRAG_Fixed\cleaned_content_demo.txt"
    with open(cleaned_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n💾 Đã lưu nội dung đã làm sạch vào: {cleaned_path}")
    print("📝 So sánh với file raw_content_demo.txt để thấy sự khác biệt")

    # Try to identify logical sections
    print("\n🔍 TÌM CÁC PHẦN LOGIC TRONG NỘI DUNG:")
    sections = content.split('\n\n')

    section_keywords = {
        "MỤC ĐÍCH": "Mục đích",
        "PHẠM VI": "Phạm vi áp dụng",
        "THÀNH PHẦN HỒ SƠ": "Thành phần hồ sơ",
        "TRÌNH TỰ": "Trình tự thực hiện",
        "THỜI HẠN": "Thời hạn",
        "CƠ QUAN": "Cơ quan thực hiện",
        "LỆ PHÍ": "Lệ phí",
        "KẾT QUẢ": "Kết quả"
    }

    found_sections = []
    for i, section in enumerate(sections[:20]):  # Check first 20 sections
        section_upper = section.upper()
        for keyword, description in section_keywords.items():
            if keyword in section_upper and len(section.strip()) > 10:
                found_sections.append(f"Section {i+1}: {description} - {section[:50]}...")
                break

    if found_sections:
        print("Các phần tìm thấy:")
        for section in found_sections:
            print(f"  • {section}")
    else:
        print("⚠️  Không tìm thấy các phần logic rõ ràng")

if __name__ == "__main__":
    demo_enhanced_reading()
