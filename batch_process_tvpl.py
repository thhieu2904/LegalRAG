import os
import json
import win32com.client
from pathlib import Path

def extract_doc_content(doc_path):
    """Extract content from .doc file using win32com"""
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False

        doc = word.Documents.Open(doc_path)
        content = doc.Content.Text
        doc.Close()
        word.Quit()

        return content.strip()
    except Exception as e:
        print(f"Error extracting {doc_path}: {e}")
        return None

def create_standardized_json(doc_path, content, procedure_code):
    """Create standardized JSON structure for tư vấn pháp luật procedures"""

    # Extract title from filename
    filename = Path(doc_path).stem
    title = filename.replace("1 ", "").replace("2 ", "").replace("3 ", "").replace("4 ", "").replace("5 ", "").replace("6 ", "")

    # Create standardized structure
    json_data = {
        "title": title,
        "description": f"Quy trình {title.lower()}",
        "legal_basis": [
            "Luật Luật sư 2006",
            "Nghị định 123/2013/NĐ-CP",
            "Thông tư liên tịch số 09/2013/TTLT-BTP-BCA-BQP-BTC-TANDTC-VKSNDTC"
        ],
        "procedure_code": procedure_code,
        "processing_time": "30-45 ngày",
        "application_method": {
            "direct": "Nộp hồ sơ trực tiếp tại Sở Tư pháp",
            "online": "Nộp hồ sơ qua Cổng thông tin điện tử của Sở Tư pháp"
        },
        "fee_structure": {
            "direct": "1.000.000 - 3.000.000 VND",
            "online": "800.000 - 2.500.000 VND"
        },
        "content_chunks": []
    }

    # Split content into 5 chunks
    if content:
        words = content.split()
        chunk_size = len(words) // 5

        for i in range(5):
            start_idx = i * chunk_size
            end_idx = (i + 1) * chunk_size if i < 4 else len(words)

            chunk_content = " ".join(words[start_idx:end_idx])

            chunk = {
                "chunk_id": i + 1,
                "section_title": f"Phần {i + 1}: {title}",
                "content": chunk_content,
                "source_reference": f"{procedure_code} - Chunk {i + 1}",
                "keywords": [
                    "tư vấn pháp luật",
                    "trung tâm tư vấn",
                    "luật sư",
                    "đăng ký hoạt động",
                    "sở tư pháp"
                ]
            }
            json_data["content_chunks"].append(chunk)

    return json_data

def process_tvpl_collection():
    """Process quy_trinh_tu_van_phap_luat collection"""

    base_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_tu_van_phap_luat\documents"

    procedure_codes = {
        "DOC_001": "QT 01/TVPL",
        "DOC_002": "QT 02/TVPL",
        "DOC_003": "QT 03/TVPL",
        "DOC_004": "QT 04/TVPL",
        "DOC_005": "QT 05/TVPL",
        "DOC_006": "QT 06/TVPL"
    }

    print("=== PROCESSING QUY_TRINH_TU_VAN_PHAP_LUAT COLLECTION ===")
    print()

    for doc_folder in sorted(os.listdir(base_path)):
        if doc_folder.startswith("DOC_"):
            doc_path = os.path.join(base_path, doc_folder)

            # Find .doc file
            doc_files = [f for f in os.listdir(doc_path) if f.endswith('.doc')]
            if not doc_files:
                print(f"⚠️  No .doc file found in {doc_folder}")
                continue

            doc_file = doc_files[0]
            full_doc_path = os.path.join(doc_path, doc_file)

            print(f"📄 Processing {doc_folder}: {doc_file}")

            # Extract content
            content = extract_doc_content(full_doc_path)

            if content:
                content_length = len(content)
                print(f"   ✅ Extracted {content_length} characters")

                # Create standardized JSON
                procedure_code = procedure_codes.get(doc_folder, f"QT {doc_folder.split('_')[1]}/TVPL")
                json_data = create_standardized_json(full_doc_path, content, procedure_code)

                # Save JSON file
                json_filename = doc_file.replace('.doc', '.json')
                json_path = os.path.join(doc_path, json_filename)

                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                print(f"   💾 Saved standardized JSON: {json_filename}")
                print(f"   📊 Created {len(json_data['content_chunks'])} content chunks")
            else:
                print(f"   ❌ Failed to extract content from {doc_file}")

            print()

    print("=== COLLECTION PROCESSING COMPLETE ===")

if __name__ == "__main__":
    process_tvpl_collection()
