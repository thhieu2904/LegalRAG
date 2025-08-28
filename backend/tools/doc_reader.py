#!/usr/bin/env python3
"""
Script để đọc nội dung file .doc cũ (Office 97-2003)
"""

import os
import sys
import olefile
import re
from pathlib import Path

def read_doc_file(doc_path):
    """
    Đọc nội dung từ file .doc cũ
    """
    try:
        if not os.path.exists(doc_path):
            return f"❌ File không tồn tại: {doc_path}"

        # Kiểm tra định dạng file
        if not doc_path.lower().endswith('.doc'):
            return f"❌ File không phải định dạng .doc: {doc_path}"

        # Sử dụng olefile để đọc
        with olefile.OleFileIO(doc_path) as ole:
            # Tìm stream chứa text
            text_streams = []
            for stream in ole.listdir():
                if 'WordDocument' in str(stream) or 'Text' in str(stream):
                    text_streams.append(stream)

            if not text_streams:
                return "❌ Không tìm thấy stream text trong file .doc"

            # Đọc stream đầu tiên
            stream_name = text_streams[0]
            data = ole.openstream(stream_name).read()

            # Chuyển đổi bytes thành text (thử nghiệm)
            try:
                # Thử decode UTF-8
                text = data.decode('utf-8', errors='ignore')
            except:
                try:
                    # Thử decode UTF-16
                    text = data.decode('utf-16', errors='ignore')
                except:
                    try:
                        # Thử decode Latin-1
                        text = data.decode('latin-1', errors='ignore')
                    except:
                        return "❌ Không thể decode nội dung file"

            # Làm sạch text
            text = re.sub(r'[^\x20-\x7E\xA0-\xFF\u0100-\uFFFF]', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()

            return text

    except Exception as e:
        return f"❌ Lỗi khi đọc file: {str(e)}"

def extract_structured_content(text):
    """
    Trích xuất thông tin có cấu trúc từ text
    """
    content = {
        'raw_text': text,
        'sections': [],
        'fee_info': [],
        'form_info': [],
        'requirements': []
    }

    # Làm sạch text trước khi phân tích
    clean_text = re.sub(r'[^\x20-\x7E\xA0-\xFF\u0100-\uFFFF]', ' ', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    # Tìm các section theo pattern
    section_patterns = [
        r'THÀNH PHẦN.*?HỒ SƠ.*?:(.*?)(?=THỜI HẠN|$)',
        r'GIẤY TỜ PHẢI NỘP.*?:(.*?)(?=GIẤY TỜ PHẢI XUẤT TRÌNH|$)',
        r'GIẤY TỜ PHẢI XUẤT TRÌNH.*?:(.*?)(?=THỜI HẠN|$)',
        r'THỜI HẠN GIẢI QUYẾT.*?:(.*?)(?=ĐỐI TƯỢNG|$)',
        r'PHÍ.*?LỆ PHÍ.*?:(.*?)(?=QUY TRÌNH|$)',
        r'QUY TRÌNH XỬ LÝ.*?:(.*?)(?=KẾT QUẢ|$)',
        r'KẾT QUẢ THỰC HIỆN.*?:(.*?)(?=PHÍ|$)',
        r'CƠ QUAN THỰC HIỆN.*?:(.*?)(?=CƠ QUAN PHỐI HỢP|$)'
    ]

    for pattern in section_patterns:
        matches = re.findall(pattern, clean_text, re.IGNORECASE | re.DOTALL)
        if matches:
            for match in matches:
                if match.strip():
                    content['sections'].append(match.strip())

    # Tìm thông tin phí với pattern tốt hơn
    fee_patterns = [
        r'(\d{1,3}(?:\.\d{3})*|\d+)[\s]*(?:đồng|đ|vnd|vnđ)',
        r'miễn phí',
        r'không thu phí',
        r'(\d{1,3}(?:\.\d{3})*|\d+)[\s]*(?:đồng|đ).*?(?:trực tiếp|online|trực tuyến)',
        r'(\d{1,3}(?:\.\d{3})*|\d+)[\s]*(?:đồng|đ).*?(?:đúng hạn|không đúng hạn)'
    ]

    for pattern in fee_patterns:
        matches = re.findall(pattern, clean_text, re.IGNORECASE)
        content['fee_info'].extend(matches)

    # Tìm thông tin biểu mẫu
    form_patterns = [
        r'tờ khai',
        r'biểu mẫu',
        r'đơn',
        r'mẫu',
        r'form',
        r'mẫu đơn',
        r'tờ khai đăng ký'
    ]

    for pattern in form_patterns:
        if re.search(pattern, clean_text, re.IGNORECASE):
            content['form_info'].append(pattern)

    # Tìm yêu cầu/hồ sơ
    requirement_patterns = [
        r'(\d+\..*?)(?=\d+\.|THỜI HẠN|$)',
        r'([+-].*?)(?=[+-]|THỜI HẠN|$)'
    ]

    for pattern in requirement_patterns:
        matches = re.findall(pattern, clean_text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            if len(match.strip()) > 10:  # Chỉ lấy những item có ý nghĩa
                content['requirements'].append(match.strip())

    return content

def process_doc_file(doc_path, output_dir=None):
    """
    Xử lý một file .doc và trả về kết quả phân tích
    """
    print(f"🔄 Đang đọc file: {os.path.basename(doc_path)}")

    # Đọc nội dung
    raw_content = read_doc_file(doc_path)

    if raw_content.startswith("❌"):
        print(raw_content)
        return None

    # Phân tích cấu trúc
    structured_content = extract_structured_content(raw_content)

    # Lưu kết quả nếu có output_dir
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(doc_path))[0]

        # Lưu raw text
        with open(os.path.join(output_dir, f"{base_name}_raw.txt"), 'w', encoding='utf-8') as f:
            f.write(raw_content)

        # Lưu structured content
        with open(os.path.join(output_dir, f"{base_name}_structured.json"), 'w', encoding='utf-8') as f:
            import json
            json.dump(structured_content, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã xử lý xong: {os.path.basename(doc_path)}")
    print(f"   - Độ dài text: {len(raw_content)} ký tự")
    print(f"   - Số sections: {len(structured_content['sections'])}")
    print(f"   - Thông tin phí: {len(structured_content['fee_info'])}")
    print(f"   - Thông tin form: {len(structured_content['form_info'])}")

    return structured_content

def main():
    """
    Main function để test đọc file .doc
    """
    print("🚀 DOC READER - Đọc file .doc cũ")
    print("=" * 50)

    # Test với file mẫu
    test_files = [
        "d:/Personal/LegalRAG_Fixed/backend/data/storage/collections/quy_trinh_cap_ho_tich_cap_xa/documents/DOC_001/01. Đăng ký khai sinh.doc",
        "d:/Personal/LegalRAG_Fixed/backend/data/storage/collections/quy_trinh_chung_thuc/documents/DOC_001/1. Cấp bản sao từ sổ gốc.doc"
    ]

    output_dir = "d:/Personal/LegalRAG_Fixed/backend/doc_analysis_output"
    os.makedirs(output_dir, exist_ok=True)

    for doc_file in test_files:
        if os.path.exists(doc_file):
            result = process_doc_file(doc_file, output_dir)
            if result:
                print("\n📝 PREVIEW NỘI DUNG:")
                preview = result['raw_text'][:500] + "..." if len(result['raw_text']) > 500 else result['raw_text']
                print(preview)
                print("\n" + "="*50 + "\n")
        else:
            print(f"⚠️  File không tồn tại: {doc_file}")

if __name__ == "__main__":
    main()
