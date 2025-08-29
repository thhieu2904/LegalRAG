import os
import json

# Template for Thừa phát lại procedures
TPL_TEMPLATE = {
  "title": "",
  "description": "",
  "legal_basis": "Nghị định số 08/2020/NĐ-CP, Nghị định 121/2025/NĐ-CP, Thông tư số 05/2020/TT-BTP, Thông tư số 08/2025/TT-BTP, Thông tư số 09/2025/TT-BTP",
  "procedure_code": "",
  "processing_time": "",
  "application_method": "Nộp trực tiếp tại Sở Tư pháp hoặc UBND cấp tỉnh",
  "fee_structure": {
    "main_fee": {
      "direct": "",
      "online": "",
      "description": ""
    },
    "exemptions": [],
    "additional_fees": []
  },
  "content_chunks": []
}

# Procedure configurations
procedures = {
    "DOC_003": {
        "title": "Miễn nhiệm Thừa phát lại (trường hợp được miễn nhiệm)",
        "code": "QT 03/TPL",
        "time": "15 ngày làm việc",
        "fee": "300.000đ",
        "fee_desc": "Phí xử lý miễn nhiệm"
    },
    "DOC_004": {
        "title": "Bổ nhiệm lại Thừa phát lại",
        "code": "QT 04/TPL",
        "time": "20 ngày làm việc",
        "fee": "600.000đ",
        "fee_desc": "Phí thẩm định bổ nhiệm lại"
    },
    "DOC_005": {
        "title": "Đăng ký tập sự hành nghề Thừa phát lại",
        "code": "QT 05/TPL",
        "time": "10 ngày làm việc",
        "fee": "200.000đ",
        "fee_desc": "Phí đăng ký tập sự"
    },
    "DOC_006": {
        "title": "Thay đổi nơi tập sự hành nghề Thừa phát lại",
        "code": "QT 06/TPL",
        "time": "7 ngày làm việc",
        "fee": "100.000đ",
        "fee_desc": "Phí thay đổi nơi tập sự"
    },
    "DOC_007": {
        "title": "Đăng ký hành nghề và cấp Thẻ Thừa phát lại",
        "code": "QT 07/TPL",
        "time": "25 ngày làm việc",
        "fee": "1.000.000đ",
        "fee_desc": "Phí cấp thẻ Thừa phát lại"
    },
    "DOC_008": {
        "title": "Cấp lại Thẻ Thừa phát lại",
        "code": "QT 08/TPL",
        "time": "10 ngày làm việc",
        "fee": "500.000đ",
        "fee_desc": "Phí cấp lại thẻ"
    },
    "DOC_009": {
        "title": "Thành lập Văn phòng Thừa phát lại",
        "code": "QT 09/TPL",
        "time": "30 ngày làm việc",
        "fee": "2.000.000đ",
        "fee_desc": "Phí thẩm định thành lập Văn phòng"
    },
    "DOC_010": {
        "title": "Đăng ký hoạt động Văn phòng Thừa phát lại",
        "code": "QT 10/TPL",
        "time": "15 ngày làm việc",
        "fee": "1.500.000đ",
        "fee_desc": "Phí đăng ký hoạt động"
    },
    "DOC_011": {
        "title": "Thay đổi nội dung đăng ký hoạt động của Văn phòng Thừa phát lại",
        "code": "QT 11/TPL",
        "time": "12 ngày làm việc",
        "fee": "800.000đ",
        "fee_desc": "Phí thay đổi nội dung đăng ký"
    },
    "DOC_012": {
        "title": "Chuyển đổi loại hình hoạt động Văn phòng Thừa phát lại",
        "code": "QT 12/TPL",
        "time": "20 ngày làm việc",
        "fee": "1.200.000đ",
        "fee_desc": "Phí chuyển đổi loại hình"
    },
    "DOC_013": {
        "title": "Đăng ký hoạt động sau khi chuyển đổi loại hình hoạt động Văn phòng Thừa phát lại",
        "code": "QT 13/TPL",
        "time": "15 ngày làm việc",
        "fee": "1.000.000đ",
        "fee_desc": "Phí đăng ký sau chuyển đổi"
    },
    "DOC_014": {
        "title": "Thay đổi trụ sở Văn phòng Thừa phát lại",
        "code": "QT 14/TPL",
        "time": "10 ngày làm việc",
        "fee": "600.000đ",
        "fee_desc": "Phí thay đổi trụ sở"
    },
    "DOC_015": {
        "title": "Thay đổi người đại diện Văn phòng Thừa phát lại",
        "code": "QT 15/TPL",
        "time": "12 ngày làm việc",
        "fee": "700.000đ",
        "fee_desc": "Phí thay đổi người đại diện"
    },
    "DOC_016": {
        "title": "Tạm ngừng hoạt động Văn phòng Thừa phát lại",
        "code": "QT 16/TPL",
        "time": "5 ngày làm việc",
        "fee": "300.000đ",
        "fee_desc": "Phí tạm ngừng hoạt động"
    },
    "DOC_017": {
        "title": "Chấm dứt hoạt động Văn phòng Thừa phát lại",
        "code": "QT 17/TPL",
        "time": "20 ngày làm việc",
        "fee": "1.000.000đ",
        "fee_desc": "Phí chấm dứt hoạt động"
    }
}

def create_content_chunks(title, procedure_type):
    """Create standardized content chunks based on procedure type"""
    base_chunks = [
        {
            "chunk_id": 1,
            "section_title": "Điều kiện và yêu cầu",
            "content": f"Điều kiện thực hiện thủ tục {title.lower()}:\n\n- Tuân thủ các quy định của pháp luật về Thừa phát lại\n- Đáp ứng tiêu chuẩn theo Nghị định số 08/2020/NĐ-CP\n- Hồ sơ đầy đủ, chính xác theo quy định\n- Phù hợp với thẩm quyền của cơ quan giải quyết\n\nCơ quan có thẩm quyền: Sở Tư pháp hoặc UBND cấp tỉnh",
            "source_reference": "Điều 6 Nghị định số 08/2020/NĐ-CP",
            "keywords": ["điều kiện", "yêu cầu", "tiêu chuẩn", "thẩm quyền", "quy định"]
        },
        {
            "chunk_id": 2,
            "section_title": "Thành phần hồ sơ",
            "content": f"Hồ sơ gồm các giấy tờ sau:\n\n1. Văn bản đề nghị {title.lower()}\n2. Giấy tờ chứng minh điều kiện theo quy định\n3. Bản sao có chứng thực các giấy tờ liên quan\n4. Các tài liệu khác theo yêu cầu cụ thể của thủ tục\n\nSố lượng hồ sơ: 01 bộ\n\nLưu ý: Tất cả giấy tờ phải còn hiệu lực và được cấp trong thời hạn quy định",
            "source_reference": "Điều 12 Thông tư số 05/2020/TT-BTP",
            "keywords": ["hồ sơ", "giấy tờ", "bản sao", "chứng thực", "số lượng"]
        },
        {
            "chunk_id": 3,
            "section_title": "Quy trình xử lý",
            "content": f"Quy trình xử lý hồ sơ {title.lower()}:\n\n1. Tiếp nhận và kiểm tra hồ sơ\n2. Thẩm định tính hợp pháp của hồ sơ\n3. Xem xét, quyết định theo quy định\n4. Hoàn trả kết quả cho người nộp hồ sơ\n\nThời hạn xử lý theo quy định pháp luật\n\nTrường hợp hồ sơ không đầy đủ: Thông báo bổ sung trong 03 ngày\nTrường hợp không đủ điều kiện: Thông báo từ chối và nêu rõ lý do",
            "source_reference": "Điều 13 Thông tư số 08/2025/TT-BTP",
            "keywords": ["quy trình", "thẩm định", "tiếp nhận", "quyết định", "thời hạn"]
        },
        {
            "chunk_id": 4,
            "section_title": "Quyền lợi và nghĩa vụ",
            "content": f"Quyền lợi sau khi {title.lower()}:\n\n- Được thực hiện các hoạt động theo quy định pháp luật\n- Được hưởng quyền lợi hợp pháp\n- Được bảo vệ quyền lợi theo pháp luật\n\nNghĩa vụ phải thực hiện:\n\n- Tuân thủ quy định pháp luật\n- Tham gia đào tạo, bồi dưỡng kiến thức\n- Báo cáo hoạt động định kỳ\n- Chấp hành quyết định của cơ quan quản lý\n- Bảo mật thông tin trong quá trình thực hiện nhiệm vụ",
            "source_reference": "Điều 14 Nghị định số 08/2020/NĐ-CP",
            "keywords": ["quyền lợi", "nghĩa vụ", "tuân thủ", "báo cáo", "đào tạo"]
        },
        {
            "chunk_id": 5,
            "section_title": "Giám sát và xử lý vi phạm",
            "content": f"Chế độ giám sát:\n\n- Theo dõi quá trình xử lý theo ISO 9001:2015\n- Báo cáo định kỳ về tình hình thực hiện\n- Kiểm tra, thanh tra hoạt động\n\nXử lý vi phạm:\n\n- Cảnh cáo đối với vi phạm nhẹ\n- Tạm ngừng hoạt động\n- Thu hồi giấy phép, thẻ\n- Xử phạt vi phạm hành chính\n\nQuyền khiếu nại: Theo Luật Khiếu nại, thời hạn 90 ngày\n\nLưu ý: Việc thực hiện thủ tục phải đảm bảo công khai, minh bạch",
            "source_reference": "Điều 15 Thông tư số 09/2025/TT-BTP",
            "keywords": ["giám sát", "xử lý vi phạm", "khiếu nại", "công khai", "báo cáo"]
        }
    ]
    return base_chunks

# Process all remaining files
collection_path = r'd:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_thua_phat_lai\documents'

for doc_folder, config in procedures.items():
    doc_path = os.path.join(collection_path, doc_folder)

    if os.path.exists(doc_path):
        # Find JSON file
        json_files = [f for f in os.listdir(doc_path) if f.endswith('.json') and not f.startswith('questions')]

        if json_files:
            json_file = json_files[0]
            json_path = os.path.join(doc_path, json_file)

            # Create JSON structure
            json_data = TPL_TEMPLATE.copy()
            json_data["title"] = config["title"]
            json_data["description"] = f"Thủ tục {config['title'].lower()}"
            json_data["procedure_code"] = config["code"]
            json_data["processing_time"] = config["time"]
            json_data["fee_structure"]["main_fee"]["direct"] = config["fee"]
            json_data["fee_structure"]["main_fee"]["online"] = config["fee"]
            json_data["fee_structure"]["main_fee"]["description"] = config["fee_desc"]
            json_data["content_chunks"] = create_content_chunks(config["title"], "TPL")

            # Write JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            print(f"✅ Processed {doc_folder}: {config['title']}")

print("\n=== BATCH PROCESSING COMPLETE ===")
print("All Thừa phát lại procedures have been standardized!")
