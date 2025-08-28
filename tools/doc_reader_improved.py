import olefile
import re
import sys

def clean_text(text):
    """Làm sạch text từ .doc"""
    # Loại bỏ ký tự không in được và encoding issues
    text = re.sub(r'[^\x00-\x7F\x80-\xFF]', '', text)
    # Thay thế nhiều khoảng trắng bằng một
    text = re.sub(r'\s+', ' ', text)
    # Loại bỏ dòng trống liên tiếp
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def extract_doc_content(file_path):
    """Trích xuất nội dung từ file .doc"""
    if not olefile.isOleFile(file_path):
        print(f"File {file_path} không phải là file OLE hợp lệ")
        return ""

    ole = olefile.OleFileIO(file_path)
    text = ""

    # Thử đọc từ WordDocument stream
    if ole.exists('WordDocument'):
        stream = ole.openstream('WordDocument')
        data = stream.read()
        # Chuyển đổi sang text (đơn giản, có thể cần thư viện khác cho parsing đầy đủ)
        try:
            text = data.decode('utf-8', errors='ignore')
        except:
            text = data.decode('latin-1', errors='ignore')

    ole.close()
    return clean_text(text)

def analyze_structure(text):
    """Phân tích cấu trúc văn bản"""
    lines = text.split('\n')
    sections = {}

    current_section = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Phát hiện tiêu đề section
        if re.match(r'^(MỤC|Mục|PHỤ MỤC|THÔNG TIN|QUY TRÌNH|BIỂU MẪU|HỒ SƠ)', line.upper()):
            current_section = line
            sections[current_section] = []
        elif current_section and line:
            sections[current_section].append(line)

    return sections

if __name__ == "__main__":
    file_path = r"D:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents\DOC_002\02. ĐKKS có yếu tố nước ngoài.doc"

    print("📄 ĐANG ĐỌC NỘI DUNG .DOC...")
    raw_text = extract_doc_content(file_path)

    if raw_text:
        print("📋 NỘI DUNG ĐÃ LÀM SẠCH:")
        print("=" * 80)
        print(raw_text[:2000])  # Hiển thị 2000 ký tự đầu
        print("=" * 80)

        print("\n📋 CẤU TRÚC PHÂN TÍCH:")
        print("=" * 80)
        sections = analyze_structure(raw_text)
        for section, content in sections.items():
            print(f"\n🔹 {section}:")
            print(" ".join(content[:3]))  # Hiển thị 3 dòng đầu
    else:
        print("❌ Không thể trích xuất nội dung")
