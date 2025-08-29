import os
import win32com.client
from pathlib import Path

def read_doc_content(doc_path):
    """Read and display content from .doc file"""
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False

        doc = word.Documents.Open(doc_path)
        content = doc.Content.Text
        doc.Close()
        word.Quit()

        return content
    except Exception as e:
        return f"Error reading file: {e}"

def analyze_ho_tich_files():
    """Analyze a few sample files to understand content structure"""

    base_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents"

    # Sample files to analyze
    sample_files = [
        ("DOC_001", "01. Đăng ký khai sinh.doc"),  # Basic birth registration
        ("DOC_011", "11. Đăng ký kết hôn.doc"),    # Marriage registration
        ("DOC_015", "15. Đăng ký khai tử.doc"),    # Death registration
        ("DOC_025", "25. Thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định lại dân tộc.doc")  # Complex procedure
    ]

    print("=== PHÂN TÍCH NỘI DUNG FILES MẪU HỘ TỊCH CẤP XÃ ===")
    print()

    for doc_folder, doc_filename in sample_files:
        doc_path = os.path.join(base_path, doc_folder, doc_filename)

        if os.path.exists(doc_path):
            print(f"📄 {doc_folder}: {doc_filename}")
            print("-" * 60)

            content = read_doc_content(doc_path)

            if content and not content.startswith("Error"):
                # Show first 1000 characters to understand structure
                preview = content[:1000] + "..." if len(content) > 1000 else content
                print(f"Content length: {len(content)} characters")
                print(f"Content preview:\n{preview}")
                print()

                # Try to identify logical sections
                print("🔍 LOGICAL SECTIONS IDENTIFIED:")
                sections = content.split('\n\n')
                for i, section in enumerate(sections[:10]):  # Show first 10 sections
                    if section.strip():
                        print(f"  Section {i+1}: {section.strip()[:100]}...")
                print()
            else:
                print(f"❌ Error: {content}")
                print()
        else:
            print(f"⚠️  File not found: {doc_path}")
            print()

if __name__ == "__main__":
    analyze_ho_tich_files()
