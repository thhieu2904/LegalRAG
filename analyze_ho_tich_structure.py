import os
import win32com.client
import re

def read_doc_content_clean(doc_path):
    """Read and clean content from .doc file"""
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False

        doc = word.Documents.Open(doc_path)
        content = doc.Content.Text
        doc.Close()
        word.Quit()

        # Clean up the content
        content = content.replace('\r', '\n').replace('\t', ' ')
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        return content.strip()
    except Exception as e:
        return f"Error reading file: {e}"

def analyze_ho_tich_structure():
    """Analyze the logical structure of hộ tịch files"""

    base_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents"

    # Analyze one file in detail
    doc_path = os.path.join(base_path, "DOC_001", "01. Đăng ký khai sinh.doc")

    print("=== PHÂN TÍCH CHI TIẾT CẤU TRÚC FILE HỘ TỊCH ===")
    print(f"File: {doc_path}")
    print("=" * 60)

    content = read_doc_content_clean(doc_path)

    if content and not content.startswith("Error"):
        print(f"Tổng độ dài: {len(content)} ký tự")
        print()

        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        print("📋 CẤU TRÚC LOGIC CỦA FILE:")
        print()

        # Identify key sections based on common patterns
        key_sections = {
            "header": [],
            "purpose_scope": [],
            "documents": [],
            "procedures": [],
            "fees": [],
            "results": [],
            "other": []
        }

        for i, para in enumerate(paragraphs[:30]):  # Analyze first 30 paragraphs
            para_lower = para.lower()

            # Classify paragraphs
            if any(keyword in para_lower for keyword in ['mục đích', 'phạm vi', 'áp dụng']):
                key_sections["purpose_scope"].append((i, para))
            elif any(keyword in para_lower for keyword in ['thành phần hồ sơ', 'giấy tờ', 'tờ khai']):
                key_sections["documents"].append((i, para))
            elif any(keyword in para_lower for keyword in ['trình tự', 'cách thức', 'thời gian', 'bước']):
                key_sections["procedures"].append((i, para))
            elif any(keyword in para_lower for keyword in ['phí', 'lệ phí', 'miễn phí']):
                key_sections["fees"].append((i, para))
            elif any(keyword in para_lower for keyword in ['kết quả', 'giấy']):
                key_sections["results"].append((i, para))
            elif i < 5:
                key_sections["header"].append((i, para))
            else:
                key_sections["other"].append((i, para))

        # Display findings
        for section_name, items in key_sections.items():
            if items:
                print(f"🔸 {section_name.upper()}:")
                for idx, para in items[:3]:  # Show first 3 items
                    preview = para[:100] + "..." if len(para) > 100 else para
                    print(f"   [{idx}] {preview}")
                print()

        print("🎯 ĐỀ XUẤT CẤU TRÚC 5 CHUNKS LOGIC:")
        print("1. THÀNH PHẦN HỒ SƠ VÀ YÊU CẦU")
        print("2. THỜI HẠN VÀ ĐỐI TƯỢNG THỰC HIỆN")
        print("3. CƠ QUAN CÓ THẨM QUYỀN")
        print("4. TRÌNH TỰ THỰC HIỆN")
        print("5. KẾT QUẢ VÀ LƯU Ý QUAN TRỌNG")

    else:
        print(f"❌ Lỗi: {content}")

if __name__ == "__main__":
    analyze_ho_tich_structure()
