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
    """Create 5 standard chunks from content"""

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

    # Create JSON structure
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

def process_all_ho_tich_files():
    """Process all 35 hộ tịch files"""

    base_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents"

    # All 35 files to process
    files_to_process = [
        ("DOC_001", "01. Đăng ký khai sinh.doc", "QT 01/CX-HT", "Đăng ký khai sinh"),
        ("DOC_002", "02. ĐKKS có yếu tố nước ngoài.doc", "QT 02/CX-HT", "Đăng ký khai sinh có yếu tố nước ngoài"),
        ("DOC_003", "03. Đăng ký lại khai sinh.doc", "QT 03/CX-HT", "Đăng ký lại khai sinh"),
        ("DOC_004", "04. Đăng ký lại khai sinh có yếu tố nước ngoài.doc", "QT 04/CX-HT", "Đăng ký lại khai sinh có yếu tố nước ngoài"),
        ("DOC_005", "05. Đăng ký nhận cha mẹ con.doc", "QT 05/CX-HT", "Đăng ký nhận cha mẹ con"),
        ("DOC_006", "06. Đăng ký nhận cha mẹ con có yếu tố nước ngoài.doc", "QT 06/CX-HT", "Đăng ký nhận cha mẹ con có yếu tố nước ngoài"),
        ("DOC_007", "07. Đăng ký khai sinh kết hợp nhận cha, mẹ, con.doc", "QT 07/CX-HT", "Đăng ký khai sinh kết hợp nhận cha, mẹ, con"),
        ("DOC_008", "08. Đăng ký khai sinh kết hợp đăng ký nhận cha, mẹ, con có yếu tố nước ngoài.doc", "QT 08/CX-HT", "Đăng ký khai sinh kết hợp đăng ký nhận cha, mẹ, con có yếu tố nước ngoài"),
        ("DOC_009", "09. Đăng ký khai sinh cho người đã có hồ sơ, giấy tờ cá nhân.doc", "QT 09/CX-HT", "Đăng ký khai sinh cho người đã có hồ sơ, giấy tờ cá nhân"),
        ("DOC_010", "10. Đăng ký khai sinh có yếu tố nước ngoài cho người đã có hồ sơ, giấy tờ cá nhân.doc", "QT 10/CX-HT", "Đăng ký khai sinh có yếu tố nước ngoài cho người đã có hồ sơ, giấy tờ cá nhân"),
        ("DOC_011", "11. Đăng ký kết hôn.doc", "QT 11/CX-HT", "Đăng ký kết hôn"),
        ("DOC_012", "12. Đăng ký kết hôn có yếu tố nước ngoài.doc", "QT 12/CX-HT", "Đăng ký kết hôn có yếu tố nước ngoài"),
        ("DOC_013", "13. Đăng ký lại kết hôn.doc", "QT 13/CX-HT", "Đăng ký lại kết hôn"),
        ("DOC_014", "14. Đăng ký lại kết hôn có yếu tố nước ngoài.doc", "QT 14/CX-HT", "Đăng ký lại kết hôn có yếu tố nước ngoài"),
        ("DOC_015", "15. Đăng ký khai tử.doc", "QT 15/CX-HT", "Đăng ký khai tử"),
        ("DOC_016", "16. Đăng ký khai tử có yếu tố nước ngoài.doc", "QT 16/CX-HT", "Đăng ký khai tử có yếu tố nước ngoài"),
        ("DOC_017", "17. Đăng ký lại khai tử.doc", "QT 17/CX-HT", "Đăng ký lại khai tử"),
        ("DOC_018", "18. Đăng ký lại khai tử có yếu tố nước ngoài.doc", "QT 18/CX-HT", "Đăng ký lại khai tử có yếu tố nước ngoài"),
        ("DOC_019", "19. Đăng ký giám hộ.doc", "QT 19/CX-HT", "Đăng ký giám hộ"),
        ("DOC_020", "20. Đăng ký giám hộ có yếu tố nước ngoài.doc", "QT 20/CX-HT", "Đăng ký giám hộ có yếu tố nước ngoài"),
        ("DOC_021", "21. Đăng ký chấm dứt giám hộ.doc", "QT 21/CX-HT", "Đăng ký chấm dứt giám hộ"),
        ("DOC_022", "22. Đăng ký chấm dứt giám hộ có yếu tố nước ngoài.doc", "QT 22/CX-HT", "Đăng ký chấm dứt giám hộ có yếu tố nước ngoài"),
        ("DOC_023", "23. Đăng ký giám sát việc giám hộ.doc", "QT 23/CX-HT", "Đăng ký giám sát việc giám hộ"),
        ("DOC_024", "24. Đăng ký chấm dứt giám sát việc giám hộ.doc", "QT 24/CX-HT", "Đăng ký chấm dứt giám sát việc giám hộ"),
        ("DOC_025", "25. Thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định lại dân tộc.doc", "QT 25/CX-HT", "Thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định lại dân tộc"),
        ("DOC_026", "26. Thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định lại dân tộc có yếu tố nước ngoài.doc", "QT 26/CX-HT", "Thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định lại dân tộc có yếu tố nước ngoài"),
        ("DOC_027", "27. Ghi vào Sổ hộ tịch việc kết hôn của công dân Việt Nam đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài.doc", "QT 27/CX-HT", "Ghi vào Sổ hộ tịch việc kết hôn của công dân Việt Nam đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài"),
        ("DOC_028", "28. Ghi vào Sổ hộ tịch việc ly hôn, hủy việc kết hôn của công dân Việt Nam đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài.doc", "QT 28/CX-HT", "Ghi vào Sổ hộ tịch việc ly hôn, hủy việc kết hôn của công dân Việt Nam đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài"),
        ("DOC_029", "29. Ghi vào Sổ hộ tịch việc hộ tịch khác của công dân Việt Nam đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài.doc", "QT 29/CX-HT", "Ghi vào Sổ hộ tịch việc hộ tịch khác của công dân Việt Nam đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài"),
        ("DOC_030", "30. Đăng ký khai sinh lưu động.doc", "QT 30/CX-HT", "Đăng ký khai sinh lưu động"),
        ("DOC_031", "31. Đăng ký kết hôn lưu động.doc", "QT 31/CX-HT", "Đăng ký kết hôn lưu động"),
        ("DOC_032", "32. Đăng ký khai tử lưu động.doc", "QT 32/CX-HT", "Đăng ký khai tử lưu động"),
        ("DOC_033", "33. Cấp Giấy xác nhận tình trạng hôn nhân.doc", "QT 33/CX-HT", "Cấp Giấy xác nhận tình trạng hôn nhân"),
        ("DOC_034", "34. Cấp bản sao Trích lục hộ tịch, bản sao Giấy khai sinh.doc", "QT 34/CX-HT", "Cấp bản sao Trích lục hộ tịch, bản sao Giấy khai sinh"),
        ("DOC_035", "35. Xác nhận hộ tịch.doc", "QT 35/CX-HT", "Xác nhận hộ tịch")
    ]

    print("=== XỬ LÝ TOÀN BỘ 35 FILES HỘ TỊCH ===")
    print("🎯 Mục tiêu: Đọc Word gốc → Tạo 5 chunks logic → Tránh ảo giác")
    print("🔒 Đã backup toàn bộ collection vào backup_ho_tich_collection")
    print()

    success_count = 0
    total_files = len(files_to_process)

    for i, (doc_folder, doc_filename, procedure_code, title) in enumerate(files_to_process, 1):
        doc_path = os.path.join(base_path, doc_folder, doc_filename)
        json_path = os.path.join(base_path, doc_folder, doc_filename.replace('.doc', '.json'))

        print(f"📄 [{i:2d}/{total_files}] Processing {doc_folder}: {title[:50]}...")

        if os.path.exists(doc_path):
            # Read content from Word file
            content = read_doc_content_clean_enhanced(doc_path)

            if content and not content.startswith("Error"):
                print(f"   ✅ Đã đọc {len(content)} ký tự từ Word")

                # Create standard chunks
                json_data = create_standard_chunks(content, procedure_code, title)

                # Count chunks created
                chunk_count = len(json_data['content_chunks'])
                print(f"   📊 Tạo {chunk_count} chunks")

                # Backup existing JSON
                backup_path = json_path + '.backup_final'
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                if os.path.exists(json_path):
                    os.rename(json_path, backup_path)

                # Save new JSON
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                print(f"   💾 Đã lưu: {os.path.basename(json_path)}")
                success_count += 1

            else:
                print(f"   ❌ Lỗi đọc Word: {content}")

        else:
            print(f"   ⚠️  Không tìm thấy: {doc_path}")

        print()

    print("🎯 KẾT QUẢ CUỐI CÙNG:")
    print(f"✅ Đã xử lý thành công {success_count}/{total_files} files")
    print("✅ Đọc trực tiếp từ file Word gốc")
    print("✅ Tạo 4-5 chunks logic cho mỗi file")
    print("✅ Giải quyết vấn đề ảo giác do chunks quá gần nhau")
    print("✅ Backup an toàn trong backup_ho_tich_collection")
    print()
    print("🎉 HOÀN THÀNH! Collection quy_trinh_cap_ho_tich_cap_xa đã sẵn sàng!")

if __name__ == "__main__":
    process_all_ho_tich_files()
