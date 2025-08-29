import os
import json
import win32com.client
import re
from pathlib import Path

def read_doc_content_clean_enhanced(doc_path):
    """Enhanced function to read and clean Word document content"""

    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False

        doc = word.Documents.Open(doc_path)
        content = doc.Content.Text
        doc.Close()
        word.Quit()

        # Enhanced cleaning
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

        return content

    except Exception as e:
        return f"Error reading file: {e}"

def create_standard_chunks(content, procedure_code, title):
    """Create 5 standard chunks from content - similar to other collections"""

    # Split content into sections
    sections = content.split('\n\n')
    sections = [s.strip() for s in sections if s.strip()]

    # Initialize 5 standard chunks
    chunks = {
        1: {"title": "Thành phần hồ sơ", "content": [], "keywords": ["hồ sơ", "giấy tờ", "tờ khai", "biểu mẫu"]},
        2: {"title": "Thời hạn giải quyết", "content": [], "keywords": ["thời hạn", "ngày làm việc", "trong vòng"]},
        3: {"title": "Cơ quan thực hiện", "content": [], "keywords": ["cơ quan", "UBND", "ủy ban nhân dân", "nơi"]},
        4: {"title": "Trình tự thực hiện", "content": [], "keywords": ["trình tự", "các bước", "thủ tục", "bước"]},
        5: {"title": "Lệ phí và kết quả", "content": [], "keywords": ["phí", "lệ phí", "kết quả", "giấy", "miễn phí"]}
    }

    # Simple classification based on keywords
    for section in sections:
        section_lower = section.lower()

        # Skip headers and administrative content
        if any(skip in section_lower for skip in ['sở tư pháp', 'mã hiệu:', 'lần ban hành', 'trách nhiệm']):
            continue

        # Classify sections
        classified = False

        if any(kw in section_lower for kw in ['thành phần hồ sơ', 'giấy tờ', 'tờ khai', 'biểu mẫu']):
            chunks[1]["content"].append(section)
            classified = True
        elif any(kw in section_lower for kw in ['thời hạn', 'ngày làm việc', 'trong vòng']):
            chunks[2]["content"].append(section)
            classified = True
        elif any(kw in section_lower for kw in ['cơ quan', 'ubnd', 'ủy ban', 'nơi']):
            chunks[3]["content"].append(section)
            classified = True
        elif any(kw in section_lower for kw in ['trình tự', 'các bước', 'bước', 'thủ tục']):
            chunks[4]["content"].append(section)
            classified = True
        elif any(kw in section_lower for kw in ['phí', 'lệ phí', 'kết quả', 'giấy', 'miễn phí']):
            chunks[5]["content"].append(section)
            classified = True

        # If not classified, add to chunk 5 (general information)
        if not classified and len(section) > 20:  # Only meaningful content
            chunks[5]["content"].append(section)

    # Create JSON structure similar to other collections
    json_data = {
        "title": title,
        "description": f"Quy trình {title.lower()} tại UBND cấp xã",
        "procedure_code": procedure_code,
        "processing_time": "Theo quy định pháp luật",
        "content_chunks": []
    }

    # Add chunks to JSON
    for chunk_id, chunk_info in chunks.items():
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

def process_ho_tich_simple():
    """Process hộ tịch files using simple approach like other collections"""

    base_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents"

    # Files to process (same as before)
    files_to_process = [
        ("DOC_001", "01. Đăng ký khai sinh.doc", "QT 01/CX-HT", "Đăng ký khai sinh"),
        ("DOC_011", "11. Đăng ký kết hôn.doc", "QT 11/CX-HT", "Đăng ký kết hôn"),
        ("DOC_015", "15. Đăng ký khai tử.doc", "QT 15/CX-HT", "Đăng ký khai tử"),
        ("DOC_025", "25. Thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định lại dân tộc.doc", "QT 25/CX-HT", "Thay đổi, cải chính, bổ sung thông tin hộ tịch"),
        ("DOC_035", "35. Xác nhận hộ tịch.doc", "QT 35/CX-HT", "Xác nhận hộ tịch")
    ]

    print("=== XỬ LÝ HỘ TỊCH - CÁCH ĐƠN GIẢN NHƯ CÁC COLLECTION KHÁC ===")
    print("🎯 Đã backup toàn bộ collection vào backup_ho_tich_collection")
    print("🔄 Quay lại cách đọc Word và xử lý như collection khác")
    print()

    success_count = 0

    for doc_folder, doc_filename, procedure_code, title in files_to_process:
        doc_path = os.path.join(base_path, doc_folder, doc_filename)
        json_path = os.path.join(base_path, doc_folder, doc_filename.replace('.doc', '.json'))

        print(f"📄 Processing {doc_folder}: {title}")
        print("-" * 60)

        if os.path.exists(doc_path):
            # Read content from Word file
            content = read_doc_content_clean_enhanced(doc_path)

            if content and not content.startswith("Error"):
                print(f"✅ Đã đọc {len(content)} ký tự từ Word")

                # Create standard chunks
                json_data = create_standard_chunks(content, procedure_code, title)

                # Show chunk summary
                print(f"📊 Tạo {len(json_data['content_chunks'])} chunks:")
                for chunk in json_data['content_chunks']:
                    content_preview = chunk['content'][:100] + "..." if len(chunk['content']) > 100 else chunk['content']
                    print(f"   Chunk {chunk['chunk_id']}: {chunk['section_title']}")
                    print(f"      Preview: {content_preview}")
                    print()

                # Backup existing JSON (handle existing backup)
                backup_path = json_path + '.backup_simple'
                if os.path.exists(backup_path):
                    os.remove(backup_path)  # Remove old backup
                if os.path.exists(json_path):
                    os.rename(json_path, backup_path)
                    print(f"💾 Đã backup JSON cũ: {os.path.basename(backup_path)}")

                # Save new JSON
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                print(f"💾 Đã lưu: {os.path.basename(json_path)}")
                print("✅ Hoàn thành xử lý file này")
                success_count += 1

            else:
                print(f"❌ Lỗi đọc Word: {content}")

        else:
            print(f"⚠️  Không tìm thấy: {doc_path}")

        print()

    print("🎯 KẾT QUẢ:")
    print(f"✅ Đã xử lý thành công {success_count}/{len(files_to_process)} files")
    print("✅ Sử dụng cách tiếp cận đơn giản như các collection khác")
    print("✅ Tạo 5 chunks tiêu chuẩn, tránh ảo giác")
    print("✅ Nội dung được trích xuất trực tiếp từ file Word gốc")
    print()
    print("📝 TIẾP THEO:")
    print("1. Kiểm tra chất lượng 5 files đã xử lý")
    print("2. Nếu ổn thì áp dụng cho toàn bộ 35 files")
    print("3. Nếu cần điều chỉnh logic thì sửa script và chạy lại")
    print("4. Backup đã có trong thư mục backup_ho_tich_collection")

if __name__ == "__main__":
    process_ho_tich_simple()
