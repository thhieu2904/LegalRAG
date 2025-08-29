import win32com.client as win32
import json
import os
import re

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

def parse_document_structure(content, doc_title):
    """Parse document content into structured sections"""

    # Clean content
    content = content.replace('\r', '\n').replace('\n\n', '\n').strip()

    # Split into sections based on common patterns
    sections = {}

    # Extract key information using regex patterns
    patterns = {
        'doi_tuong': r'Đối tượng thực hiện thủ tục hành chính[:\s]*(.*?)(?=\n[A-Z]|$)',
        'yeu_cau_dieu_kien': r'Yêu cầu, điều kiện thực hiện thủ tục hành chính[:\s]*(.*?)(?=\n[A-Z]|$)',
        'thanh_phan_ho_so': r'Thành phần hồ sơ[:\s]*(.*?)(?=\n[A-Z]|$)',
        'thoi_han': r'Thời hạn giải quyết[:\s]*(.*?)(?=\n[A-Z]|$)',
        'co_quan_thuc_hien': r'Cơ quan thực hiện thủ tục hành chính[:\s]*(.*?)(?=\n[A-Z]|$)',
        'cach_thuc_nop': r'Cách thức thực hiện[:\s]*(.*?)(?=\n[A-Z]|$)',
        'le_phi': r'Lệ phí[:\s]*(.*?)(?=\n[A-Z]|$)',
        'ket_qua': r'Kết quả thực hiện thủ tục hành chính[:\s]*(.*?)(?=\n[A-Z]|$)',
        'can_cu_phap_ly': r'Căn cứ pháp lý[:\s]*(.*?)(?=\n[A-Z]|$)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
        else:
            sections[key] = "Chưa xác định"

    return sections

def build_json_structure(doc_title, sections):
    """Build complete JSON structure based on parsed sections"""

    # Determine procedure code based on document
    if "hòa giải viên" in doc_title.lower():
        code = "QT 01/PBGDPL-HTPLDN"
        description = "Thủ tục hỗ trợ hòa giải viên khi gặp tai nạn hoặc rủi ro"
    elif "đề nghị hỗ trợ chi phí" in doc_title.lower():
        code = "QT 02/PBGDPL-HTPLDN"
        description = "Thủ tục đề nghị hỗ trợ chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa"
    elif "thanh toán chi phí" in doc_title.lower():
        code = "QT 03/PBGDPL-HTPLDN"
        description = "Thủ tục đề nghị thanh toán chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa"
    else:
        code = "QT XX/PBGDPL-HTPLDN"
        description = doc_title

    # Build content chunks based on sections
    chunks = []

    # Chunk 1: Đối tượng và điều kiện
    chunks.append({
        "chunk_id": 1,
        "section_title": "Đối tượng thực hiện và điều kiện",
        "content": f"Đối tượng thực hiện thủ tục: {sections.get('doi_tuong', 'Chưa xác định')}\n\nYêu cầu, điều kiện: {sections.get('yeu_cau_dieu_kien', 'Chưa xác định')}",
        "source_reference": "Nghị định số 55/2019/NĐ-CP, Nghị định số 121/2025/NĐ-CP",
        "keywords": ["đối tượng", "điều kiện", "yêu cầu", "thẩm quyền"]
    })

    # Chunk 2: Thành phần hồ sơ
    chunks.append({
        "chunk_id": 2,
        "section_title": "Thành phần hồ sơ",
        "content": f"Thành phần hồ sơ gồm:\n{sections.get('thanh_phan_ho_so', 'Chưa xác định')}\n\nCơ quan thực hiện: {sections.get('co_quan_thuc_hien', 'Chưa xác định')}",
        "source_reference": "Thông tư số 09/2025/TT-BTP",
        "keywords": ["hồ sơ", "thành phần", "cơ quan", "thẩm quyền"]
    })

    # Chunk 3: Quy trình và thời hạn
    chunks.append({
        "chunk_id": 3,
        "section_title": "Quy trình và thời hạn giải quyết",
        "content": f"Thời hạn giải quyết: {sections.get('thoi_han', 'Chưa xác định')}\n\nCách thức thực hiện: {sections.get('cach_thuc_nop', 'Chưa xác định')}\n\nQuy trình: Tiếp nhận hồ sơ → Thẩm tra → Xử lý → Trả kết quả",
        "source_reference": "Quyết định số 101/QĐ-BKHCN",
        "keywords": ["thời hạn", "quy trình", "cách thức", "thẩm tra"]
    })

    # Chunk 4: Lệ phí và chi phí
    chunks.append({
        "chunk_id": 4,
        "section_title": "Lệ phí và chi phí",
        "content": f"Lệ phí: {sections.get('le_phi', 'Không quy định lệ phí')}\n\nChi phí khác: Theo quy định của pháp luật về hỗ trợ pháp lý",
        "source_reference": "Nghị định về lệ phí, phí",
        "keywords": ["lệ phí", "chi phí", "hỗ trợ", "pháp lý"]
    })

    # Chunk 5: Kết quả và hiệu lực
    chunks.append({
        "chunk_id": 5,
        "section_title": "Kết quả và hiệu lực pháp lý",
        "content": f"Kết quả thủ tục: {sections.get('ket_qua', 'Chưa xác định')}\n\nCăn cứ pháp lý: {sections.get('can_cu_phap_ly', 'Chưa xác định')}\n\nHiệu lực: Theo quy định của pháp luật hiện hành",
        "source_reference": "Luật Hòa giải ở cơ sở, Luật Hỗ trợ doanh nghiệp nhỏ và vừa",
        "keywords": ["kết quả", "hiệu lực", "căn cứ pháp lý", "quy định"]
    })

    # Build complete JSON structure
    json_data = {
        "title": doc_title,
        "description": description,
        "legal_basis": "Luật Hòa giải ở cơ sở năm 2020, Luật Hỗ trợ doanh nghiệp nhỏ và vừa năm 2017, Nghị định số 55/2019/NĐ-CP",
        "procedure_code": code,
        "processing_time": sections.get('thoi_han', '03-30 ngày làm việc'),
        "application_method": sections.get('cach_thuc_nop', 'Trực tiếp, qua bưu điện, trực tuyến'),
        "fee_structure": {
            "main_fee": {
                "direct": "0đ",
                "online": "0đ",
                "description": "Không thu lệ phí"
            },
            "exemptions": [],
            "additional_fees": []
        },
        "content_chunks": chunks
    }

    return json_data

def rebuild_single_file():
    """Rebuild quy_trinh_pbgdpl_htpldn collection file by file"""

    collection_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_pbgdpl_htpldn\documents"

    documents = [
        {
            "doc_folder": "DOC_001",
            "doc_file": "01. Quy trinh hỗ trợ hòa giải viên.doc",
            "json_file": "01. Quy trinh hỗ trợ hòa giải viên.json",
            "title": "Quy trình hỗ trợ hòa giải viên"
        }
    ]

    for doc_info in documents:
        print(f"\n{'='*80}")
        print(f"🔄 PROCESSING: {doc_info['title']}")
        print(f"{'='*80}")

        doc_path = os.path.join(collection_path, doc_info["doc_folder"], doc_info["doc_file"])
        json_path = os.path.join(collection_path, doc_info["doc_folder"], doc_info["json_file"])

        # Extract content
        print("📖 Extracting content from .doc file...")
        content = extract_doc_content(doc_path)

        if content is None:
            print("❌ Failed to extract content")
            continue

        print(f"✅ Content extracted: {len(content)} characters")

        # Parse structure
        print("🔍 Parsing document structure...")
        sections = parse_document_structure(content, doc_info["title"])

        print("📋 Extracted sections:")
        for key, value in sections.items():
            print(f"  {key}: {value[:100]}{'...' if len(value) > 100 else ''}")

        # Build JSON
        print("🏗️ Building JSON structure...")
        json_data = build_json_structure(doc_info["title"], sections)

        # Save JSON
        print("💾 Saving JSON file...")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Successfully rebuilt: {doc_info['json_file']}")
        print(f"📊 JSON contains {len(json_data['content_chunks'])} content chunks")

        # Verify structure
        print("🔍 Verifying JSON structure...")
        required_fields = ['title', 'description', 'legal_basis', 'procedure_code', 'processing_time', 'application_method', 'fee_structure', 'content_chunks']
        missing_fields = [field for field in required_fields if field not in json_data]

        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
        else:
            print("✅ All required fields present")

        # Check content chunks
        for chunk in json_data['content_chunks']:
            required_chunk_fields = ['chunk_id', 'section_title', 'content', 'source_reference', 'keywords']
            missing_chunk_fields = [field for field in required_chunk_fields if field not in chunk]

            if missing_chunk_fields:
                print(f"❌ Chunk {chunk['chunk_id']} missing: {missing_chunk_fields}")
            else:
                print(f"✅ Chunk {chunk['chunk_id']}: {chunk['section_title']}")

        print(f"{'='*80}")

if __name__ == "__main__":
    rebuild_single_file()
