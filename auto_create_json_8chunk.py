#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tự động tạo JSON 8 chunk từ nội dung text của tài liệu quy trình chứng thực
"""

import json
import re
import os
from datetime import datetime

def load_template():
    """Load template JSON 8 chunk"""
    template_path = "json_template_8chunk.json"
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_basic_info(content):
    """Trích xuất thông tin cơ bản từ nội dung"""
    basic_info = {
        "title": "",
        "code": "",
        "issuing_authority": "Sở Tư pháp",
        "executing_agency": "",
        "processing_time_text": "",
        "fee_text": "",
        "applicant_type": ["Cá nhân"]
    }

    # Tìm tiêu đề
    title_match = re.search(r'S? TU PHAP.*?Th? t?c ch?ng th?c.*?[^\n]+', content, re.IGNORECASE)
    if title_match:
        basic_info["title"] = title_match.group(0).strip()

    # Tìm mã hiệu
    code_match = re.search(r'Ma hi?u:\s*([^\n]+)', content)
    if code_match:
        basic_info["code"] = code_match.group(1).strip()

    # Tìm cơ quan thực hiện
    agency_match = re.search(r'Co quan th?c hi?n th? t?c hnh chnh:\s*([^\n]+)', content)
    if agency_match:
        basic_info["executing_agency"] = agency_match.group(1).strip()

    # Tìm thời hạn
    time_match = re.search(r'Th?i h?n gi?i quy?t:\s*([^\n]+)', content)
    if time_match:
        basic_info["processing_time_text"] = time_match.group(1).strip()

    # Tìm phí
    fee_match = re.search(r'Ph:\s*([^\n]+)', content)
    if fee_match:
        basic_info["fee_text"] = fee_match.group(1).strip()

    # Tìm đối tượng
    applicant_match = re.search(r'D?i tu?ng th?c hi?n th? t?c hnh chnh:\s*([^\n]+)', content)
    if applicant_match:
        applicant_text = applicant_match.group(1).strip()
        if "tổ chức" in applicant_text.lower() or "tc" in applicant_text.lower():
            basic_info["applicant_type"] = ["Cá nhân", "Tổ chức"]
        else:
            basic_info["applicant_type"] = ["Cá nhân"]

    return basic_info

def extract_definitions(content):
    """Trích xuất định nghĩa và viết tắt"""
    definitions = []

    # Tìm phần định nghĩa
    def_section = re.search(r'D?NH NGHIA VA VI?T T?T.*?(?=|$)', content, re.DOTALL | re.IGNORECASE)
    if def_section:
        def_text = def_section.group(0)

        # Tìm các định nghĩa theo pattern
        def_patterns = [
            r'(\w+)\s*:\s*([^\n]+)',
            r'(\w+)\s*\(\s*([^)]+)\)\s*:\s*([^\n]+)'
        ]

        for pattern in def_patterns:
            matches = re.findall(pattern, def_text)
            for match in matches:
                if len(match) == 2:
                    definitions.append(f"{match[0]}: {match[1]}")
                elif len(match) == 3:
                    definitions.append(f"{match[0]} ({match[1]}): {match[2]}")

    return "\n".join(definitions) if definitions else "Không có định nghĩa cụ thể trong tài liệu"

def extract_documents(content):
    """Trích xuất thành phần hồ sơ"""
    docs = []

    # Tìm phần thành phần hồ sơ
    doc_section = re.search(r'Thnh ph?n, s? lu?ng h? so:.*?(?=b\.)', content, re.DOTALL | re.IGNORECASE)
    if doc_section:
        doc_text = doc_section.group(0)

        # Tìm các yêu cầu giấy tờ
        doc_matches = re.findall(r'[+-]\s*([^\n]+)', doc_text)
        docs.extend(doc_matches)

    return "\n".join(docs) if docs else "Không có thông tin cụ thể về thành phần hồ sơ"

def extract_time_info(content):
    """Trích xuất thông tin thời hạn"""
    time_info = []

    # Tìm phần thời hạn
    time_section = re.search(r'b\.\s*Th?i h?n gi?i quy?t:.*?(?=c\.)', content, re.DOTALL | re.IGNORECASE)
    if time_section:
        time_info.append(time_section.group(0).strip())

    return "\n".join(time_info) if time_info else "Không có thông tin cụ thể về thời hạn"

def extract_agency_info(content):
    """Trích xuất thông tin cơ quan và đối tượng"""
    agency_info = []

    # Tìm phần đối tượng
    applicant_section = re.search(r'c\.\s*D?i tu?ng th?c hi?n.*?(?=d\.)', content, re.DOTALL | re.IGNORECASE)
    if applicant_section:
        agency_info.append(applicant_section.group(0).strip())

    # Tìm phần cơ quan
    agency_section = re.search(r'd\.\s*Co quan th?c hi?n.*?(?=d\.)', content, re.DOTALL | re.IGNORECASE)
    if agency_section:
        agency_info.append(agency_section.group(0).strip())

    return "\n".join(agency_info) if agency_info else "Không có thông tin cụ thể về đối tượng và cơ quan"

def extract_result_fee(content):
    """Trích xuất kết quả và phí"""
    result_fee = []

    # Tìm phần kết quả
    result_section = re.search(r'd\.\s*K?t qu? th?c hi?n.*?(?=e\.)', content, re.DOTALL | re.IGNORECASE)
    if result_section:
        result_fee.append(result_section.group(0).strip())

    # Tìm phần phí
    fee_section = re.search(r'e\.\s*Ph:.*?(?=g\.)', content, re.DOTALL | re.IGNORECASE)
    if fee_section:
        result_fee.append(fee_section.group(0).strip())

    return "\n".join(result_fee) if result_fee else "Không có thông tin cụ thể về kết quả và phí"

def extract_conditions(content):
    """Trích xuất yêu cầu và điều kiện"""
    conditions = []

    # Tìm phần yêu cầu điều kiện
    cond_section = re.search(r'h\.\s*Yu c?u, di?u ki?n.*?(?=i\.)', content, re.DOTALL | re.IGNORECASE)
    if cond_section:
        conditions.append(cond_section.group(0).strip())

    return "\n".join(conditions) if conditions else "Không có thông tin cụ thể về yêu cầu và điều kiện"

def extract_legal_procedure(content):
    """Trích xuất căn cứ pháp lý và quy trình"""
    legal_procedure = []

    # Tìm phần căn cứ pháp lý
    legal_section = re.search(r'i\.\s*Can c? php ly.*?(?=Quy trnh|$)', content, re.DOTALL | re.IGNORECASE)
    if legal_section:
        legal_procedure.append(legal_section.group(0).strip())

    # Tìm phần quy trình
    procedure_section = re.search(r'Quy trnh x? ly cng vi?c:.*?(?=6\.|$)', content, re.DOTALL | re.IGNORECASE)
    if procedure_section:
        legal_procedure.append(procedure_section.group(0).strip())

    return "\n".join(legal_procedure) if legal_procedure else "Không có thông tin cụ thể về căn cứ pháp lý và quy trình"

def create_json_from_content(content, doc_number):
    """Tạo JSON từ nội dung text"""
    template = load_template()

    # Cập nhật metadata
    basic_info = extract_basic_info(content)
    template["metadata"].update(basic_info)
    template["metadata"]["source"] = f"data/documents/quy_trinh_chung_thuc/DOC_{doc_number}/[filename].doc"
    template["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    # Cập nhật content chunks
    chunks_data = [
        ("Thông tin cơ bản và tiêu đề", extract_basic_info(content)["title"] or "Không có thông tin tiêu đề"),
        ("Định nghĩa và viết tắt", extract_definitions(content)),
        ("Thành phần và số lượng hồ sơ", extract_documents(content)),
        ("Thời hạn giải quyết", extract_time_info(content)),
        ("Đối tượng và cơ quan thực hiện", extract_agency_info(content)),
        ("Kết quả thực hiện và lệ phí", extract_result_fee(content)),
        ("Yêu cầu và điều kiện thực hiện", extract_conditions(content)),
        ("Căn cứ pháp lý và quy trình chi tiết", extract_legal_procedure(content))
    ]

    for i, (title, content_text) in enumerate(chunks_data, 1):
        template["content_chunks"][i-1]["section_title"] = title
        template["content_chunks"][i-1]["content"] = content_text

    return template

def main():
    """Hàm chính"""
    print("=== TẠO JSON 8 CHUNK TỰ ĐỘNG ===")

    # Xử lý các file content có sẵn
    content_files = [
        ("doc_002_content.txt", "002"),
        ("doc_003_content.txt", "003"),
        ("doc_004_content.txt", "004")
    ]

    for content_file, doc_number in content_files:
        if os.path.exists(content_file):
            print(f"\n🔄 Đang xử lý {content_file}...")

            try:
                with open(content_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Tạo JSON
                json_data = create_json_from_content(content, doc_number)

                # Lưu file JSON
                output_file = f"quy_trinh_chung_thuc_doc_{doc_number}_8chunk.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)

                print(f"✅ Đã tạo: {output_file}")

            except Exception as e:
                print(f"❌ Lỗi xử lý {content_file}: {str(e)}")
        else:
            print(f"⚠️  Không tìm thấy file: {content_file}")

    print("\n🎉 Hoàn thành xử lý!")

if __name__ == "__main__":
    main()
