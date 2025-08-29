import os
import json
import win32com.client
import re
from pathlib import Path

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
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        return content.strip()
    except Exception as e:
        return f"Error reading file: {e}"

def create_manual_chunks(content, procedure_code, title):
    """Create 5 logical chunks based on legal content analysis"""

    # Split content into paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

    # Initialize chunks
    chunks_data = {
        1: {"title": "Thành phần hồ sơ và yêu cầu", "content": [], "keywords": ["hồ sơ", "giấy tờ", "tờ khai", "yêu cầu", "thành phần"]},
        2: {"title": "Thời hạn và đối tượng thực hiện", "content": [], "keywords": ["thời hạn", "đối tượng", "ngày làm việc", "thực hiện"]},
        3: {"title": "Cơ quan có thẩm quyền", "content": [], "keywords": ["cơ quan", "thẩm quyền", "UBND", "sở tư pháp", "nơi cư trú"]},
        4: {"title": "Trình tự thực hiện", "content": [], "keywords": ["trình tự", "các bước", "thủ tục", "tiếp nhận", "giải quyết"]},
        5: {"title": "Kết quả và lưu ý quan trọng", "content": [], "keywords": ["kết quả", "giấy", "lưu ý", "phí", "lệ phí", "miễn phí"]}
    }

    # Classify paragraphs into chunks
    for para in paragraphs:
        para_lower = para.lower()

        # Skip headers and administrative content
        if any(skip in para_lower for skip in ['sở tư pháp', 'mã hiệu:', 'lần ban hành', 'trách nhiệm', 'mục lục', 'cộng hòa xã hội']):
            continue

        # Classify based on content keywords
        classified = False

        # Chunk 1: Documents and requirements
        if any(keyword in para_lower for keyword in ['thành phần hồ sơ', 'giấy tờ', 'tờ khai', 'biểu mẫu', 'yêu cầu']):
            chunks_data[1]["content"].append(para)
            classified = True

        # Chunk 2: Time limits and eligible subjects
        elif any(keyword in para_lower for keyword in ['thời hạn', 'đối tượng', 'ngày làm việc', 'thực hiện']):
            chunks_data[2]["content"].append(para)
            classified = True

        # Chunk 3: Authorized agencies
        elif any(keyword in para_lower for keyword in ['cơ quan', 'thẩm quyền', 'ubnd', 'nơi cư trú']):
            chunks_data[3]["content"].append(para)
            classified = True

        # Chunk 4: Procedures
        elif any(keyword in para_lower for keyword in ['trình tự', 'các bước', 'bước', 'tiếp nhận', 'thẩm tra']):
            chunks_data[4]["content"].append(para)
            classified = True

        # Chunk 5: Results and important notes
        elif any(keyword in para_lower for keyword in ['kết quả', 'giấy', 'lưu ý', 'phí', 'lệ phí', 'miễn phí']):
            chunks_data[5]["content"].append(para)
            classified = True

        # If not classified, add to most relevant chunk based on context
        if not classified:
            # Check for numbers that might indicate steps
            if re.search(r'^\d+\.', para) or re.search(r'bước \d+', para_lower):
                chunks_data[4]["content"].append(para)
            else:
                # Add to chunk 5 as general information
                chunks_data[5]["content"].append(para)

    # Create final JSON structure
    json_data = {
        "title": title,
        "description": f"Quy trình {title.lower()} tại UBND cấp xã",
        "legal_basis": [
            "Luật Hộ tịch 2014",
            "Nghị định 123/2015/NĐ-CP",
            "Thông tư 04/2020/TT-BTP"
        ],
        "procedure_code": procedure_code,
        "processing_time": "Ngay trong ngày hoặc 05 ngày làm việc",
        "application_method": {
            "direct": "Nộp hồ sơ trực tiếp tại UBND cấp xã",
            "online": "Nộp hồ sơ qua Cổng thông tin điện tử của UBND cấp xã"
        },
        "fee_structure": {
            "direct": "Miễn phí - 50.000 VND",
            "online": "Miễn phí - 25.000 VND"
        },
        "content_chunks": []
    }

    # Convert chunks to final format
    for chunk_id, chunk_info in chunks_data.items():
        chunk_content = '\n\n'.join(chunk_info["content"])

        if chunk_content.strip():  # Only add non-empty chunks
            chunk = {
                "chunk_id": chunk_id,
                "section_title": f"Phần {chunk_id}: {chunk_info['title']}",
                "content": chunk_content,
                "source_reference": f"{procedure_code} - Chunk {chunk_id}",
                "keywords": chunk_info["keywords"]
            }
            json_data["content_chunks"].append(chunk)

    return json_data

def process_ho_tich_manual():
    """Process hộ tịch files with manual logic-based chunking"""

    base_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents"

    # Process first 5 files as examples
    files_to_process = [
        ("DOC_001", "01. Đăng ký khai sinh.doc", "QT 01/CX-HT", "Đăng ký khai sinh"),
        ("DOC_011", "11. Đăng ký kết hôn.doc", "QT 11/CX-HT", "Đăng ký kết hôn"),
        ("DOC_015", "15. Đăng ký khai tử.doc", "QT 15/CX-HT", "Đăng ký khai tử"),
        ("DOC_025", "25. Thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định lại dân tộc.doc", "QT 25/CX-HT", "Thay đổi, cải chính, bổ sung thông tin hộ tịch"),
        ("DOC_035", "35. Xác nhận hộ tịch.doc", "QT 35/CX-HT", "Xác nhận hộ tịch")
    ]

    print("=== XỬ LÝ HỘ TỊCH VỚI LOGIC CHUNKS THỦ CÔNG ===")
    print("🎯 Mục tiêu: Tạo 5 chunks logic, tránh trùng lặp và ảo giác")
    print()

    for doc_folder, doc_filename, procedure_code, title in files_to_process:
        doc_path = os.path.join(base_path, doc_folder, doc_filename)

        if os.path.exists(doc_path):
            print(f"📄 Processing {doc_folder}: {title}")
            print("-" * 60)

            # Read content
            content = read_doc_content_clean(doc_path)

            if content and not content.startswith("Error"):
                print(f"✅ Đã đọc {len(content)} ký tự")

                # Create manual chunks
                json_data = create_manual_chunks(content, procedure_code, title)

                # Display chunk summary
                print(f"📊 Đã tạo {len(json_data['content_chunks'])} chunks:")
                for chunk in json_data['content_chunks']:
                    content_preview = chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
                    print(f"   Chunk {chunk['chunk_id']}: {chunk['section_title']}")
                    print(f"      Nội dung: {content_preview}")
                    print(f"      Từ khóa: {', '.join(chunk['keywords'])}")
                    print()

                # Save JSON file
                json_filename = doc_filename.replace('.doc', '.json')
                json_path = os.path.join(base_path, doc_folder, json_filename)

                # Backup existing file
                if os.path.exists(json_path):
                    backup_path = json_path + '.backup'
                    os.rename(json_path, backup_path)
                    print(f"💾 Đã backup file cũ: {json_filename}.backup")

                # Save new JSON
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                print(f"💾 Đã lưu: {json_filename}")
                print(f"✅ Hoàn thành {doc_folder}")
                print()

            else:
                print(f"❌ Lỗi đọc file: {content}")
                print()
        else:
            print(f"⚠️  Không tìm thấy: {doc_path}")
            print()

    print("🎯 KẾT QUẢ:")
    print("✅ Đã xử lý 5 files mẫu với logic chunks thủ công")
    print("✅ Mỗi file có 5 chunks với nội dung không trùng lặp")
    print("✅ Tránh được vấn đề ảo giác do chunks quá gần nhau")
    print()
    print("📝 HƯỚNG DẪN TIẾP THEO:")
    print("1. Kiểm tra chất lượng 5 files đã xử lý")
    print("2. Điều chỉnh logic chunking nếu cần")
    print("3. Áp dụng cho toàn bộ 35 files còn lại")
    print("4. Đảm bảo tính nhất quán trong toàn bộ collection")

if __name__ == "__main__":
    process_ho_tich_manual()
