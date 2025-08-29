import win32com.client as win32
import json
import os

def extract_doc_content(doc_path):
    """Extract content from .doc file using win32com"""
    try:
        word = win32.Dispatch("Word.Application")
        word.Visible = False

        doc = word.Documents.Open(doc_path)
        content = doc.Content.Text
        doc.Close()
        word.Quit()

        return content.strip()
    except Exception as e:
        print(f"Error extracting content from {doc_path}: {e}")
        return None

def analyze_doc_content():
    """Extract and analyze content from all 3 .doc files in quy_trinh_pbgdpl_htpldn"""

    collection_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_pbgdpl_htpldn\documents"

    documents = [
        {
            "doc_folder": "DOC_001",
            "doc_file": "01. Quy trinh hỗ trợ hòa giải viên.doc",
            "title": "Quy trình hỗ trợ hòa giải viên"
        },
        {
            "doc_folder": "DOC_002",
            "doc_file": "2. Quy trinh  ĐỀ NGHỊ HỖ TRỢ CHI PHÍ TƯ VẤN PHÁP LUẬT CHO DOANH NGHIỆP NHỎ VÀ VỪA.doc",
            "title": "Đề nghị hỗ trợ chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa"
        },
        {
            "doc_folder": "DOC_003",
            "doc_file": "3. Quy trình ĐỀ NGHỊ THANH TOÁN CHI PHÍ TƯ VẤN PHÁP LUẬT CHO DOANH NGHIỆP NHỎ VÀ VỪA.doc",
            "title": "Đề nghị thanh toán chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa"
        }
    ]

    for doc_info in documents:
        print(f"\n{'='*80}")
        print(f"📄 ANALYZING: {doc_info['title']}")
        print(f"{'='*80}")

        doc_path = os.path.join(collection_path, doc_info["doc_folder"], doc_info["doc_file"])

        if not os.path.exists(doc_path):
            print(f"❌ File not found: {doc_path}")
            continue

        content = extract_doc_content(doc_path)

        if content is None:
            print("❌ Failed to extract content")
            continue

        print(f"📊 Content Length: {len(content)} characters")
        print(f"📝 Content Preview (first 500 chars):")
        print("-" * 50)
        print(content[:500])
        print("-" * 50)

        # Analyze content structure
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        print(f"📋 Total lines: {len(lines)}")

        # Look for key sections
        print("🔍 Key sections found:")
        for i, line in enumerate(lines[:20]):  # First 20 lines
            if any(keyword in line.lower() for keyword in ['thủ tục', 'hồ sơ', 'thời hạn', 'lệ phí', 'quy trình', 'điều kiện']):
                print(f"  Line {i+1}: {line}")

        print("\n" + "="*80)

if __name__ == "__main__":
    analyze_doc_content()
