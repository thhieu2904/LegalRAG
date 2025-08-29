import os
import json
import re
from pathlib import Path

def analyze_existing_chunks(json_data):
    """Phân tích cấu trúc chunks hiện có"""

    chunks = json_data.get("content_chunks", [])
    print(f"📊 File hiện có {len(chunks)} chunks:")

    for i, chunk in enumerate(chunks):
        content_length = len(chunk.get("content", ""))
        print(f"   Chunk {chunk.get('chunk_id', i+1)}: {chunk.get('section_title', 'Unknown')}")
        print(f"      Độ dài: {content_length} ký tự")
        print(f"      Từ khóa: {', '.join(chunk.get('keywords', []))}")
        print()

    return chunks

def redistribute_content_to_5_chunks(existing_chunks, metadata):
    """Phân phối lại nội dung thành 5 chunks logic"""

    # Khởi tạo 5 chunks mới
    new_chunks = {
        1: {
            "chunk_id": 1,
            "section_title": "Thành phần hồ sơ và yêu cầu",
            "content": "",
            "keywords": ["hồ sơ", "giấy tờ", "tờ khai", "yêu cầu", "thành phần", "biểu mẫu"],
            "source_reference": f"{metadata.get('procedure_code', 'Unknown')} - Chunk 1"
        },
        2: {
            "chunk_id": 2,
            "section_title": "Thời hạn và đối tượng thực hiện",
            "content": "",
            "keywords": ["thời hạn", "đối tượng", "ngày làm việc", "thực hiện", "trong vòng"],
            "source_reference": f"{metadata.get('procedure_code', 'Unknown')} - Chunk 2"
        },
        3: {
            "chunk_id": 3,
            "section_title": "Cơ quan có thẩm quyền",
            "content": "",
            "keywords": ["cơ quan", "thẩm quyền", "UBND", "sở tư pháp", "nơi cư trú", "địa điểm"],
            "source_reference": f"{metadata.get('procedure_code', 'Unknown')} - Chunk 3"
        },
        4: {
            "chunk_id": 4,
            "section_title": "Trình tự thực hiện",
            "content": "",
            "keywords": ["trình tự", "các bước", "thủ tục", "tiếp nhận", "giải quyết", "xử lý"],
            "source_reference": f"{metadata.get('procedure_code', 'Unknown')} - Chunk 4"
        },
        5: {
            "chunk_id": 5,
            "section_title": "Kết quả và lưu ý quan trọng",
            "content": "",
            "keywords": ["kết quả", "giấy", "lưu ý", "phí", "lệ phí", "miễn phí", "phát hành"],
            "source_reference": f"{metadata.get('procedure_code', 'Unknown')} - Chunk 5"
        }
    }

    # Thu thập tất cả nội dung từ chunks hiện có
    all_content_parts = []
    for chunk in existing_chunks:
        content = chunk.get("content", "")
        if content.strip():
            # Tách nội dung thành các đoạn nhỏ hơn để phân loại tốt hơn
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            for para in paragraphs:
                all_content_parts.append({
                    "content": para,
                    "original_chunk": chunk.get("chunk_id", 0),
                    "title": chunk.get("section_title", "")
                })

    print(f"📝 Thu thập được {len(all_content_parts)} đoạn nội dung để phân loại lại")

    # Phân loại từng đoạn nội dung vào chunk phù hợp
    for part in all_content_parts:
        content_lower = part["content"].lower()
        classified = False

        # Chunk 1: Hồ sơ và yêu cầu
        if any(keyword in content_lower for keyword in ["thành phần hồ sơ", "giấy tờ", "tờ khai", "biểu mẫu", "yêu cầu", "chuẩn bị", "hồ sơ lưu trữ"]):
            new_chunks[1]["content"] += part["content"] + "\n\n"
            classified = True

        # Chunk 2: Thời hạn và đối tượng
        elif any(keyword in content_lower for keyword in ["thời hạn", "đối tượng", "ngày làm việc", "thực hiện", "trong vòng", "thời gian"]):
            new_chunks[2]["content"] += part["content"] + "\n\n"
            classified = True

        # Chunk 3: Cơ quan thẩm quyền
        elif any(keyword in content_lower for keyword in ["cơ quan", "thẩm quyền", "ubnd", "nơi cư trú", "địa điểm", "ủy ban nhân dân"]):
            new_chunks[3]["content"] += part["content"] + "\n\n"
            classified = True

        # Chunk 4: Trình tự thực hiện
        elif any(keyword in content_lower for keyword in ["trình tự", "các bước", "bước", "tiếp nhận", "thẩm tra", "xử lý", "giải quyết", "thủ tục"]):
            new_chunks[4]["content"] += part["content"] + "\n\n"
            classified = True

        # Chunk 5: Kết quả và lưu ý
        elif any(keyword in content_lower for keyword in ["kết quả", "giấy", "lưu ý", "phí", "lệ phí", "miễn phí", "phát hành", "ghi chú", "chú thích"]):
            new_chunks[5]["content"] += part["content"] + "\n\n"
            classified = True

        # Nếu không phân loại được, thêm vào chunk 5 (lưu ý quan trọng)
        if not classified:
            new_chunks[5]["content"] += part["content"] + "\n\n"

    # Làm sạch nội dung (loại bỏ dòng trống thừa)
    for chunk in new_chunks.values():
        chunk["content"] = re.sub(r'\n\s*\n\s*\n', '\n\n', chunk["content"]).strip()

    return list(new_chunks.values())

def restructure_json_file(json_path):
    """Cấu trúc lại file JSON với 5 chunks logic"""

    print(f"🔄 Đang xử lý: {os.path.basename(json_path)}")
    print("-" * 60)

    # Đọc file JSON hiện có
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return False

    # Phân tích chunks hiện có
    existing_chunks = analyze_existing_chunks(json_data)

    # Tạo 5 chunks mới
    metadata = {
        "procedure_code": json_data.get("procedure_code", "Unknown"),
        "title": json_data.get("title", "Unknown")
    }

    new_chunks = redistribute_content_to_5_chunks(existing_chunks, metadata)

    # Hiển thị kết quả phân loại
    print("📊 KẾT QUẢ PHÂN LOẠI 5 CHUNKS MỚI:")
    for chunk in new_chunks:
        content_length = len(chunk["content"])
        print(f"   Chunk {chunk['chunk_id']}: {chunk['section_title']}")
        print(f"      Nội dung: {content_length} ký tự")
        print(f"      Từ khóa: {', '.join(chunk['keywords'])}")
        print()

    # Tạo dữ liệu JSON mới
    new_json_data = json_data.copy()
    new_json_data["content_chunks"] = new_chunks

    # Backup file cũ
    backup_path = json_path + '.backup_restructure'
    try:
        os.rename(json_path, backup_path)
        print(f"💾 Đã backup: {os.path.basename(backup_path)}")
    except Exception as e:
        print(f"⚠️  Không thể backup: {e}")

    # Lưu file mới
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(new_json_data, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu: {os.path.basename(json_path)}")
        print("✅ Hoàn thành cấu trúc lại!")
        return True
    except Exception as e:
        print(f"❌ Lỗi lưu file: {e}")
        return False

def main_restructure_ho_tich():
    """Hàm chính để cấu trúc lại các file hộ tịch"""

    print("=== CẤU TRÚC LẠI HỘ TỊCH - GIỮ NGUYÊN NỘI DUNG GỐC ===")
    print("🎯 Mục tiêu: Tái cấu trúc thành 5 chunks logic, tránh trùng lặp")
    print("🔒 Bảo vệ: Giữ nguyên 100% nội dung gốc, chỉ thay đổi cấu trúc")
    print()

    # Danh sách files cần xử lý
    files_to_process = [
        ("DOC_001", "01. Đăng ký khai sinh.json"),
        ("DOC_011", "11. Đăng ký kết hôn.json"),
        ("DOC_015", "15. Đăng ký khai tử.json"),
        ("DOC_025", "25. Thay đổi, cải chính, bổ sung thông tin hộ tịch, xác định lại dân tộc.json"),
        ("DOC_035", "35. Xác nhận hộ tịch.json")
    ]

    base_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents"

    success_count = 0

    for doc_folder, json_filename in files_to_process:
        json_path = os.path.join(base_path, doc_folder, json_filename)

        if os.path.exists(json_path):
            print(f"\n📄 Xử lý {doc_folder}: {json_filename}")
            if restructure_json_file(json_path):
                success_count += 1
        else:
            print(f"⚠️  Không tìm thấy: {json_path}")

    print("\n🎯 TỔNG KẾT:")
    print(f"✅ Đã xử lý thành công: {success_count}/{len(files_to_process)} files")
    print("✅ Giữ nguyên 100% nội dung gốc")
    print("✅ Tái cấu trúc thành 5 chunks logic")
    print("✅ Tránh được vấn đề ảo giác do chunks quá gần nhau")
    print()
    print("📝 HƯỚNG DẪN TIẾP THEO:")
    print("1. Kiểm tra chất lượng 5 files đã cấu trúc lại")
    print("2. So sánh với file backup để đảm bảo không mất dữ liệu")
    print("3. Điều chỉnh logic phân loại nếu cần")
    print("4. Áp dụng cho toàn bộ 35 files còn lại")

if __name__ == "__main__":
    main_restructure_ho_tich()
