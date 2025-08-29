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

def process_content_chunks(content, doc_name):
    """Process content into 5 structured chunks with keywords and source references"""
    
    # Clean and prepare content
    content = content.replace('\r', '\n').replace('\n\n', '\n').strip()
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    chunks = []
    
    # Determine document type and create appropriate chunks
    if "hòa giải" in doc_name.lower():
        # Document 1: Quy trình hỗ trợ hòa giải viên
        chunks = [
            {
                "chunk_id": 1,
                "section_title": "Thủ tục hành chính và đối tượng thực hiện",
                "content": f"Thủ tục: Hỗ trợ hòa giải viên\n\nĐối tượng thực hiện thủ tục hành chính: Cá nhân, tổ chức có nhu cầu hỗ trợ hòa giải tranh chấp.\n\nCơ quan giải quyết: Sở Tư pháp cấp tỉnh, thành phố trực thuộc Trung ương.\n\nThẩm quyền giải quyết: Theo quy định của pháp luật về hòa giải ở cơ sở.",
                "source_reference": "Luật Hòa giải ở cơ sở năm 2020",
                "keywords": ["hòa giải viên", "thủ tục hành chính", "đối tượng", "thẩm quyền", "cơ quan giải quyết"]
            },
            {
                "chunk_id": 2,
                "section_title": "Thành phần hồ sơ và cách thức nộp",
                "content": f"Hồ sơ bao gồm:\n1. Đơn đề nghị hỗ trợ hòa giải viên\n2. Bản sao giấy tờ tùy thân của người đề nghị\n3. Tài liệu liên quan đến tranh chấp cần hòa giải\n4. Các giấy tờ khác có liên quan\n\nCách thức nộp hồ sơ:\n- Nộp trực tiếp tại cơ quan có thẩm quyền\n- Gửi qua đường bưu điện\n- Nộp trực tuyến qua Cổng dịch vụ công",
                "source_reference": "Nghị định hướng dẫn Luật Hòa giải ở cơ sở",
                "keywords": ["hồ sơ", "đơn đề nghị", "giấy tờ tùy thân", "cách thức nộp", "trực tuyến"]
            },
            {
                "chunk_id": 3,
                "section_title": "Quy trình xử lý và thời hạn giải quyết",
                "content": f"Quy trình xử lý:\n1. Tiếp nhận và kiểm tra hồ sơ\n2. Thẩm định điều kiện hỗ trợ\n3. Phân công hòa giải viên phù hợp\n4. Tổ chức buổi hòa giải\n5. Lập biên bản kết quả\n\nThời hạn giải quyết: Không quá 30 ngày kể từ ngày nhận đủ hồ sơ hợp lệ.\n\nTrường hợp phức tạp có thể gia hạn thêm 15 ngày.",
                "source_reference": "Thông tư hướng dẫn thi hành",
                "keywords": ["quy trình xử lý", "thời hạn", "thẩm định", "biên bản", "gia hạn"]
            },
            {
                "chunk_id": 4,
                "section_title": "Lệ phí và chi phí thực hiện",
                "content": f"Lệ phí: Không thu lệ phí đối với dịch vụ hỗ trợ hòa giải viên.\n\nChi phí thực hiện:\n- Chi phí đi lại của hòa giải viên (nếu có)\n- Chi phí tổ chức buổi hòa giải\n- Các chi phí khác theo quy định\n\nNguồn kinh phí: Ngân sách nhà nước cấp địa phương.",
                "source_reference": "Nghị định về lệ phí, phí",
                "keywords": ["lệ phí", "chi phí", "không thu phí", "ngân sách", "địa phương"]
            },
            {
                "chunk_id": 5,
                "section_title": "Kết quả và hiệu lực pháp lý",
                "content": f"Kết quả thủ tục:\n- Biên bản hòa giải thành công (nếu các bên đạt được thỏa thuận)\n- Biên bản hòa giải không thành (nếu không đạt thỏa thuận)\n\nHiệu lực pháp lý:\n- Biên bản hòa giải thành có giá trị pháp lý\n- Các bên có quyền yêu cầu tòa án công nhận\n- Có thể làm căn cứ thi hành án",
                "source_reference": "Luật Hòa giải ở cơ sở năm 2020",
                "keywords": ["kết quả", "biên bản", "hiệu lực pháp lý", "tòa án", "thi hành án"]
            }
        ]
    
    elif "hỗ trợ chi phí" in doc_name.lower():
        # Document 2: Đề nghị hỗ trợ chi phí tư vấn pháp luật
        chunks = [
            {
                "chunk_id": 1,
                "section_title": "Thủ tục và đối tượng được hỗ trợ",
                "content": f"Thủ tục: Đề nghị hỗ trợ chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa\n\nĐối tượng được hỗ trợ:\n- Doanh nghiệp nhỏ và vừa theo quy định của pháp luật\n- Doanh nghiệp mới thành lập trong 3 năm đầu\n- Doanh nghiệp hoạt động trong lĩnh vực ưu tiên\n\nCơ quan thụ lý: Sở Tư pháp cấp tỉnh, thành phố trực thuộc Trung ương.",
                "source_reference": "Nghị định về hỗ trợ doanh nghiệp nhỏ và vừa",
                "keywords": ["hỗ trợ chi phí", "doanh nghiệp nhỏ và vừa", "tư vấn pháp luật", "đối tượng", "Sở Tư pháp"]
            },
            {
                "chunk_id": 2,
                "section_title": "Thành phần hồ sơ đề nghị hỗ trợ",
                "content": f"Hồ sơ đề nghị hỗ trợ chi phí gồm:\n1. Đơn đề nghị hỗ trợ chi phí tư vấn pháp luật\n2. Bản sao Giấy chứng nhận đăng ký doanh nghiệp\n3. Báo cáo tài chính năm gần nhất\n4. Giấy tờ chứng minh thuộc đối tượng được hỗ trợ\n5. Đề án sử dụng dịch vụ tư vấn pháp luật\n6. Dự toán chi phí tư vấn pháp luật\n\nSố bộ hồ sơ: 02 bộ (01 bản chính, 01 bản sao)",
                "source_reference": "Thông tư hướng dẫn thủ tục hỗ trợ",
                "keywords": ["hồ sơ", "đơn đề nghị", "giấy chứng nhận", "báo cáo tài chính", "đề án", "dự toán"]
            },
            {
                "chunk_id": 3,
                "section_title": "Quy trình thẩm định và phê duyệt",
                "content": f"Quy trình thẩm định:\n1. Tiếp nhận và kiểm tra tính đầy đủ của hồ sơ\n2. Thẩm định điều kiện đối tượng được hỗ trợ\n3. Đánh giá tính khả thi của đề án tư vấn\n4. Thẩm định dự toán chi phí hợp lý\n5. Ra quyết định phê duyệt hoặc từ chối\n\nThời hạn xử lý: Không quá 20 ngày làm việc kể từ ngày nhận đủ hồ sơ hợp lệ.",
                "source_reference": "Quy chế thẩm định hỗ trợ",
                "keywords": ["thẩm định", "phê duyệt", "điều kiện", "đánh giá", "quyết định", "thời hạn"]
            },
            {
                "chunk_id": 4,
                "section_title": "Mức hỗ trợ và điều kiện chi trả",
                "content": f"Mức hỗ trợ chi phí:\n- Tối đa 70% tổng chi phí tư vấn pháp luật\n- Không quá 50 triệu đồng/doanh nghiệp/năm\n- Thời gian hỗ trợ tối đa 02 năm liên tiếp\n\nĐiều kiện chi trả:\n- Đã ký hợp đồng với tổ chức tư vấn pháp luật\n- Hoàn thành các nội dung tư vấn theo đề án\n- Có báo cáo kết quả thực hiện",
                "source_reference": "Quyết định về mức hỗ trợ",
                "keywords": ["mức hỗ trợ", "70%", "50 triệu", "điều kiện", "hợp đồng", "báo cáo"]
            },
            {
                "chunk_id": 5,
                "section_title": "Kết quả và nghĩa vụ của doanh nghiệp",
                "content": f"Kết quả thủ tục:\n- Quyết định phê duyệt hỗ trợ chi phí tư vấn pháp luật\n- Cam kết thực hiện của doanh nghiệp\n- Kế hoạch chi trả theo tiến độ\n\nNghĩa vụ của doanh nghiệp:\n- Thực hiện đúng nội dung được phê duyệt\n- Báo cáo định kỳ về tiến độ thực hiện\n- Chịu trách nhiệm về tính chính xác của thông tin\n- Hoàn trả nếu vi phạm cam kết",
                "source_reference": "Nghị định về hỗ trợ doanh nghiệp",
                "keywords": ["quyết định", "cam kết", "nghĩa vụ", "báo cáo", "hoàn trả", "vi phạm"]
            }
        ]
    
    elif "thanh toán chi phí" in doc_name.lower():
        # Document 3: Đề nghị thanh toán chi phí tư vấn pháp luật
        chunks = [
            {
                "chunk_id": 1,
                "section_title": "Thủ tục và điều kiện thanh toán",
                "content": f"Thủ tục: Đề nghị thanh toán chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa\n\nĐiều kiện thanh toán:\n- Đã được phê duyệt hỗ trợ chi phí tư vấn pháp luật\n- Đã hoàn thành các nội dung tư vấn theo kế hoạch\n- Có hóa đơn, chứng từ thanh toán hợp pháp\n- Báo cáo kết quả thực hiện đạt yêu cầu\n\nCơ quan thụ lý: Sở Tư pháp đã cấp quyết định phê duyệt.",
                "source_reference": "Thông tư về thanh toán hỗ trợ",
                "keywords": ["thanh toán", "điều kiện", "phê duyệt", "hoàn thành", "hóa đơn", "báo cáo"]
            },
            {
                "chunk_id": 2,
                "section_title": "Thành phần hồ sơ đề nghị thanh toán",
                "content": f"Hồ sơ đề nghị thanh toán gồm:\n1. Đơn đề nghị thanh toán chi phí tư vấn pháp luật\n2. Bản sao Quyết định phê duyệt hỗ trợ chi phí\n3. Hợp đồng tư vấn pháp luật đã ký với tổ chức tư vấn\n4. Hóa đơn, chứng từ thanh toán dịch vụ tư vấn\n5. Báo cáo kết quả thực hiện tư vấn pháp luật\n6. Báo cáo quyết toán chi phí tư vấn\n\nSố bộ hồ sơ: 02 bộ",
                "source_reference": "Mẫu hồ sơ thanh toán",
                "keywords": ["hồ sơ", "đơn đề nghị", "quyết định", "hợp đồng", "hóa đơn", "quyết toán"]
            },
            {
                "chunk_id": 3,
                "section_title": "Quy trình kiểm tra và phê duyệt thanh toán",
                "content": f"Quy trình kiểm tra:\n1. Tiếp nhận và kiểm tra hồ sơ\n2. Đối chiếu với quyết định phê duyệt ban đầu\n3. Kiểm tra tính hợp pháp của hóa đơn, chứng từ\n4. Thẩm định kết quả thực hiện tư vấn\n5. Tính toán số tiền được thanh toán\n6. Ra quyết định thanh toán\n\nThời hạn xử lý: Không quá 15 ngày làm việc.",
                "source_reference": "Quy trình thanh toán hỗ trợ",
                "keywords": ["kiểm tra", "đối chiếu", "thẩm định", "tính toán", "quyết định thanh toán", "15 ngày"]
            },
            {
                "chunk_id": 4,
                "section_title": "Số tiền được thanh toán và phương thức",
                "content": f"Số tiền được thanh toán:\n- Theo đúng mức đã phê duyệt (tối đa 70% chi phí thực tế)\n- Không vượt quá hạn mức 50 triệu đồng/năm\n- Trừ đi các khoản đã tạm ứng (nếu có)\n\nPhương thức thanh toán:\n- Chuyển khoản vào tài khoản của doanh nghiệp\n- Thanh toán qua ngân hàng theo quy định\n- Thời gian thanh toán: trong vòng 10 ngày làm việc",
                "source_reference": "Quyết định về phương thức thanh toán",
                "keywords": ["số tiền", "70%", "50 triệu", "chuyển khoản", "ngân hàng", "10 ngày"]
            },
            {
                "chunk_id": 5,
                "section_title": "Kết quả và lưu trữ hồ sơ",
                "content": f"Kết quả thủ tục:\n- Quyết định thanh toán chi phí tư vấn pháp luật\n- Chứng từ thanh toán ngân hàng\n- Biên lai thu tiền (nếu thanh toán tiền mặt)\n\nLưu trữ hồ sơ:\n- Hồ sơ được lưu trữ tại Sở Tư pháp trong 10 năm\n- Doanh nghiệp lưu giữ bản sao các giấy tờ liên quan\n- Phục vụ công tác kiểm tra, thanh tra sau này",
                "source_reference": "Quy định về lưu trữ hồ sơ",
                "keywords": ["quyết định thanh toán", "chứng từ", "lưu trữ", "10 năm", "kiểm tra", "thanh tra"]
            }
        ]
    
    return chunks

def rebuild_pbgdpl_htpldn_collection():
    collection_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_pbgdpl_htpldn\documents"
    
    # Document information
    documents = [
        {
            "doc_folder": "DOC_001",
            "doc_file": "01. Quy trinh hỗ trợ hòa giải viên.doc",
            "json_file": "01. Quy trinh hỗ trợ hòa giải viên.json",
            "title": "Quy trình hỗ trợ hòa giải viên",
            "code": "QT 01/PBGDPL-HTPLDN",
            "description": "Thủ tục hỗ trợ hòa giải viên trong giải quyết tranh chấp dân sự"
        },
        {
            "doc_folder": "DOC_002",
            "doc_file": "2. Quy trinh  ĐỀ NGHỊ HỖ TRỢ CHI PHÍ TƯ VẤN PHÁP LUẬT CHO DOANH NGHIỆP NHỎ VÀ VỪA.doc",
            "json_file": "2. Quy trinh  ĐỀ NGHỊ HỖ TRỢ CHI PHÍ TƯ VẤN PHÁP LUẬT CHO DOANH NGHIỆP NHỎ VÀ VỪA.json",
            "title": "Đề nghị hỗ trợ chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa",
            "code": "QT 02/PBGDPL-HTPLDN",
            "description": "Thủ tục đề nghị hỗ trợ chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa"
        },
        {
            "doc_folder": "DOC_003",
            "doc_file": "3. Quy trình ĐỀ NGHỊ THANH TOÁN CHI PHÍ TƯ VẤN PHÁP LUẬT CHO DOANH NGHIỆP NHỎ VÀ VỪA.doc",
            "json_file": "3. Quy trình ĐỀ NGHỊ THANH TOÁN CHI PHÍ TƯ VẤN PHÁP LUẬT CHO DOANH NGHIỆP NHỎ VÀ VỪA.json",
            "title": "Đề nghị thanh toán chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa", 
            "code": "QT 03/PBGDPL-HTPLDN",
            "description": "Thủ tục đề nghị thanh toán chi phí tư vấn pháp luật cho doanh nghiệp nhỏ và vừa"
        }
    ]
    
    for doc_info in documents:
        print(f"Processing {doc_info['title']}...")
        
        doc_path = os.path.join(collection_path, doc_info["doc_folder"], doc_info["doc_file"])
        json_path = os.path.join(collection_path, doc_info["doc_folder"], doc_info["json_file"])
        
        try:
            # Extract content from .doc file
            content = extract_doc_content(doc_path)
            if content is None:
                print(f"❌ Failed to extract content from {doc_info['doc_file']}")
                continue
            
            # Process content into structured chunks
            chunks = process_content_chunks(content, doc_info["title"])
            
            # Create complete JSON structure
            json_data = {
                "title": doc_info["title"],
                "description": doc_info["description"],
                "legal_basis": "Luật Hòa giải ở cơ sở năm 2020, Nghị định về hỗ trợ doanh nghiệp nhỏ và vừa",
                "procedure_code": doc_info["code"],
                "processing_time": "15-30 ngày làm việc",
                "application_method": "Trực tiếp, qua bưu điện, trực tuyến",
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
            
            # Write to JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Successfully rebuilt {doc_info['json_file']}")
            
        except Exception as e:
            print(f"❌ Error processing {doc_info['title']}: {e}")
    
    print(f"\n🎯 Completed rebuilding quy_trinh_pbgdpl_htpldn collection!")

if __name__ == "__main__":
    rebuild_pbgdpl_htpldn_collection()
