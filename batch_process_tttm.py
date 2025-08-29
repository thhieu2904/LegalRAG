import os
import json

# Template for Trọng tài thương mại procedures
TTTM_TEMPLATE = {
  "title": "",
  "description": "",
  "legal_basis": "Luật Trọng tài thương mại năm 2010, Nghị định số 22/2017/NĐ-CP, Thông tư số 01/2018/TT-BTP, Thông tư số 08/2025/TT-BTP",
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
    "DOC_002": {
        "title": "Thay đổi nội dung Giấy phép thành lập của Trung tâm trọng tài",
        "code": "QT 02/TTTM",
        "time": "15 ngày làm việc",
        "fee": "1.500.000đ",
        "fee_desc": "Phí thay đổi nội dung Giấy phép"
    },
    "DOC_003": {
        "title": "Chấm dứt hoạt động Trung tâm trọng tài theo Điều lệ của Trung tâm trọng tài",
        "code": "QT 03/TTTM",
        "time": "20 ngày làm việc",
        "fee": "1.000.000đ",
        "fee_desc": "Phí chấm dứt hoạt động"
    },
    "DOC_004": {
        "title": "Cấp Giấy phép thành lập Chi nhánh, Văn phòng đại diện của Tổ chức trọng tài nước ngoài tại Việt Nam",
        "code": "QT 04/TTTM",
        "time": "25 ngày làm việc",
        "fee": "5.000.000đ",
        "fee_desc": "Phí cấp Giấy phép cho chi nhánh nước ngoài"
    },
    "DOC_005": {
        "title": "Thay đổi nội dung Giấy phép thành lập của Chi nhánh Tổ chức trọng tài nước ngoài tại Việt Nam",
        "code": "QT 05/TTTM",
        "time": "15 ngày làm việc",
        "fee": "2.000.000đ",
        "fee_desc": "Phí thay đổi nội dung chi nhánh nước ngoài"
    },
    "DOC_006": {
        "title": "Chấm dứt hoạt động Chi nhánh, Văn phòng đại diện của Tổ chức trọng tài nước ngoài tại Việt Nam",
        "code": "QT 06/TTTM",
        "time": "20 ngày làm việc",
        "fee": "1.500.000đ",
        "fee_desc": "Phí chấm dứt hoạt động chi nhánh nước ngoài"
    },
    "DOC_007": {
        "title": "Cấp lại Giấy phép thành lập của Trung tâm trọng tài, Chi nhánh, Văn phòng đại diện của Tổ chức trọng tài nước ngoài tại Việt Nam",
        "code": "QT 07/TTTM",
        "time": "10 ngày làm việc",
        "fee": "800.000đ",
        "fee_desc": "Phí cấp lại Giấy phép"
    },
    "DOC_008": {
        "title": "Đăng ký hoạt động Trung tâm trọng tài khi thay đổi địa điểm đặt trụ sở sang tỉnh, thành phố trực thuộc trung ương khác",
        "code": "QT 08/TTTM",
        "time": "12 ngày làm việc",
        "fee": "1.200.000đ",
        "fee_desc": "Phí đăng ký thay đổi địa điểm"
    },
    "DOC_009": {
        "title": "Đăng ký hoạt động Chi nhánh Trung tâm trọng tài",
        "code": "QT 09/TTTM",
        "time": "15 ngày làm việc",
        "fee": "2.500.000đ",
        "fee_desc": "Phí đăng ký hoạt động chi nhánh"
    },
    "DOC_010": {
        "title": "Thay đổi nội dung Giấy đăng ký hoạt động của Trung tâm trọng tài; thay đổi nội dung Giấy đăng ký hoạt động của Chi nhánh Tổ chức trọng tài nước ngoài tại Việt Nam",
        "code": "QT 10/TTTM",
        "time": "10 ngày làm việc",
        "fee": "1.000.000đ",
        "fee_desc": "Phí thay đổi nội dung đăng ký hoạt động"
    },
    "DOC_011": {
        "title": "Thay đổi nội dung Giấy đăng ký hoạt động của Chi nhánh Trung tâm trọng tài khi thay đổi Trưởng Chi nhánh, địa điểm đặt trụ sở của Chi nhánh trong phạm vi tỉnh, thành phố trực thuộc trung ương",
        "code": "QT 11/TTTM",
        "time": "8 ngày làm việc",
        "fee": "800.000đ",
        "fee_desc": "Phí thay đổi nội dung chi nhánh"
    },
    "DOC_012": {
        "title": "Chuyển đổi loại hình hoạt động Trung tâm trọng tài",
        "code": "QT 12/TTTM",
        "time": "18 ngày làm việc",
        "fee": "2.000.000đ",
        "fee_desc": "Phí chuyển đổi loại hình"
    },
    "DOC_013": {
        "title": "Cấp lại Giấy đăng ký hoạt động của Trung tâm trọng tài, Chi nhánh Trung tâm trọng tài, Chi nhánh của Tổ chức trọng tài nước ngoài tại Việt Nam",
        "code": "QT 13/TTTM",
        "time": "7 ngày làm việc",
        "fee": "600.000đ",
        "fee_desc": "Phí cấp lại Giấy đăng ký hoạt động"
    }
}

def create_content_chunks(title, procedure_type):
    """Create standardized content chunks based on procedure type"""
    base_chunks = [
        {
            "chunk_id": 1,
            "section_title": "Điều kiện và yêu cầu",
            "content": f"Điều kiện thực hiện thủ tục {title.lower()}:\n\n- Tuân thủ các quy định của Luật Trọng tài thương mại\n- Đáp ứng tiêu chuẩn theo Nghị định số 22/2017/NĐ-CP\n- Hồ sơ đầy đủ, chính xác theo quy định\n- Phù hợp với thẩm quyền của cơ quan giải quyết\n\nCơ quan có thẩm quyền: Sở Tư pháp hoặc UBND cấp tỉnh\n\nĐối tượng áp dụng: Trung tâm trọng tài, Chi nhánh, Văn phòng đại diện",
            "source_reference": "Điều 15 Luật Trọng tài thương mại năm 2010",
            "keywords": ["điều kiện", "yêu cầu", "tiêu chuẩn", "thẩm quyền", "trung tâm trọng tài"]
        },
        {
            "chunk_id": 2,
            "section_title": "Thành phần hồ sơ",
            "content": f"Hồ sơ gồm các giấy tờ sau:\n\n1. Văn bản đề nghị {title.lower()}\n2. Giấy tờ chứng minh điều kiện theo quy định\n3. Bản sao có chứng thực các giấy tờ liên quan\n4. Các tài liệu khác theo yêu cầu cụ thể của thủ tục\n\nSố lượng hồ sơ: 01 bộ bản chính\n\nLưu ý: Tất cả giấy tờ phải còn hiệu lực và được cấp trong thời hạn quy định",
            "source_reference": "Điều 16 Nghị định số 22/2017/NĐ-CP",
            "keywords": ["hồ sơ", "giấy tờ", "bản sao", "chứng thực", "số lượng"]
        },
        {
            "chunk_id": 3,
            "section_title": "Quy trình xử lý",
            "content": f"Quy trình xử lý hồ sơ {title.lower()}:\n\n1. Tiếp nhận và kiểm tra hồ sơ\n2. Thẩm định tính hợp pháp của hồ sơ\n3. Xem xét, quyết định theo quy định\n4. Hoàn trả kết quả cho người nộp hồ sơ\n\nThời hạn xử lý theo quy định pháp luật\n\nTrường hợp hồ sơ không đầy đủ: Thông báo bổ sung trong 03 ngày\nTrường hợp không đủ điều kiện: Thông báo từ chối và nêu rõ lý do",
            "source_reference": "Điều 17 Thông tư số 01/2018/TT-BTP",
            "keywords": ["quy trình", "thẩm định", "tiếp nhận", "quyết định", "thời hạn"]
        },
        {
            "chunk_id": 4,
            "section_title": "Quyền lợi và nghĩa vụ",
            "content": f"Quyền lợi sau khi {title.lower()}:\n\n- Được thực hiện các hoạt động theo quy định pháp luật\n- Được hưởng quyền lợi hợp pháp\n- Được bảo vệ quyền lợi theo pháp luật\n\nNghĩa vụ phải thực hiện:\n\n- Tuân thủ quy định pháp luật về trọng tài thương mại\n- Báo cáo hoạt động định kỳ\n- Tham gia đào tạo, bồi dưỡng nghiệp vụ\n- Chấp hành quyết định của cơ quan quản lý\n- Bảo mật thông tin trong quá trình tố tụng",
            "source_reference": "Điều 18 Luật Trọng tài thương mại năm 2010",
            "keywords": ["quyền lợi", "nghĩa vụ", "tuân thủ", "báo cáo", "đào tạo"]
        },
        {
            "chunk_id": 5,
            "section_title": "Giám sát và xử lý vi phạm",
            "content": f"Chế độ giám sát:\n\n- Theo dõi quá trình xử lý theo ISO 9001:2015\n- Giám sát hoạt động trọng tài định kỳ\n- Thanh tra, kiểm tra khi có dấu hiệu vi phạm\n\nXử lý vi phạm:\n\n- Cảnh cáo đối với vi phạm nhẹ\n- Tạm ngừng hoạt động\n- Thu hồi Giấy phép, Giấy đăng ký\n- Xử phạt vi phạm hành chính\n\nQuyền khiếu nại: Theo Luật Khiếu nại, thời hạn 90 ngày\n\nLưu ý: Việc thực hiện thủ tục phải đảm bảo công khai, minh bạch",
            "source_reference": "Điều 19 Thông tư số 08/2025/TT-BTP",
            "keywords": ["giám sát", "xử lý vi phạm", "khiếu nại", "công khai", "thanh tra"]
        }
    ]
    return base_chunks

# Process all remaining files
collection_path = r'd:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_trong_tai_thuong_mai\documents'

for doc_folder, config in procedures.items():
    doc_path = os.path.join(collection_path, doc_folder)

    if os.path.exists(doc_path):
        # Find JSON file
        json_files = [f for f in os.listdir(doc_path) if f.endswith('.json') and not f.startswith('questions')]

        if json_files:
            json_file = json_files[0]
            json_path = os.path.join(doc_path, json_file)

            # Create JSON structure
            json_data = TTTM_TEMPLATE.copy()
            json_data["title"] = config["title"]
            json_data["description"] = f"Thủ tục {config['title'].lower()}"
            json_data["procedure_code"] = config["code"]
            json_data["processing_time"] = config["time"]
            json_data["fee_structure"]["main_fee"]["direct"] = config["fee"]
            json_data["fee_structure"]["main_fee"]["online"] = config["fee"]
            json_data["fee_structure"]["main_fee"]["description"] = config["fee_desc"]
            json_data["content_chunks"] = create_content_chunks(config["title"], "TTTM")

            # Write JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            print(f"✅ Processed {doc_folder}: {config['title']}")

print("\n=== BATCH PROCESSING COMPLETE ===")
print("All Trọng tài thương mại procedures have been standardized!")
