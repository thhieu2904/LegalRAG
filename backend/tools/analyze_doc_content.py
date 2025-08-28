#!/usr/bin/env python3
"""
Script để làm sạch và phân tích nội dung file .doc đã đọc
"""

import re
import json

def clean_doc_text(raw_text):
    """Làm sạch text từ file .doc"""

    # Loại bỏ các ký tự điều khiển và formatting
    text = re.sub(r'[^\x20-\x7E\xA0-\xFF\u0100-\uFFFF]', ' ', raw_text)

    # Thay thế nhiều khoảng trắng bằng một
    text = re.sub(r'\s+', ' ', text)

    # Sửa một số từ bị tách
    replacements = [
        (r'k k h a i s i n h', 'khai sinh'),
        (r'c y u t n c n g o i', 'có yếu tố nước ngoài'),
        (r'L n b a n h n h', 'Lĩnh vực ban hành'),
        (r'N g y b a n h n h', 'Ngày ban hành'),
        (r'M C L C S A I T I L I U', 'MÔ TẢ CHI TIẾT CÁC BƯỚC THỰC HIỆN'),
        (r'Q U Y T R N H', 'QUY TRÌNH'),
        (r'B I U M U H S C N L U T', 'BIỂU MẪU HỒ SƠ CẦN NỘP'),
        (r'T r c h n h i m', 'Trích dẫn'),
        (r'S o n t h o', 'Sở Nội vụ'),
        (r'X e m x t', 'Xem xét'),
        (r'P h d u y t', 'Phê duyệt'),
        (r'H t n V T h H u y n', 'Họ tên vợ/chồng'),
        (r'T r a n g N g u y n', 'Trạng Nguyễn'),
        (r'T h P h n g', 'Thị Phương'),
        (r'T h u H M i n h', 'Thu Hương Minh'),
        (r'H i C h k', 'Hải Châu'),
        (r'C h c v', 'Chức vụ'),
        (r'C h u y n v i n', 'Chuyển viên'),
        (r'T r n g P h n g', 'Trưởng phòng'),
        (r'P h G i m c', 'Phó Giám đốc'),
        (r'S T p h p', 'Sở Tư pháp'),
        (r'T R A N G T H E O', 'TRẠNG THÁI'),
        (r'D I S L N', 'ĐƠN LẺ'),
        (r'S A I T I L I U', 'SAI THÔNG TIN'),
        (r'S T T T', 'SỬA THÔNG TIN'),
        (r'm l c n i d u n g', 'mục lục nội dung'),
        (r'c n s a i', 'có sai'),
        (r'C s p h p l h o c', 'Có sai phạm luật hôn nhân'),
        (r'c n c v v i c s a i', 'căn cứ vào việc sai'),
        (r'L n s a i', 'Lẽn sai'),
        (r'M C C H', 'MÔ TẢ CHI TIẾT'),
        (r'Q u y n h t h n h', 'Quy trình thẩm tra'),
        (r'p h n h s', 'phân tích'),
        (r'l p h', 'lĩnh vực'),
        (r'n u c', 'nước'),
        (r't r n h t', 'trình tự'),
        (r'c c h t h c', 'cách thức'),
        (r'v t h i g i a n', 'và thời gian'),
        (r'g i i q u y t', 'giải quyết'),
        (r'h s h n h', 'hành chính'),
        (r'c h n h c a c q u a n', 'chính các quan'),
        (r't h e o t i u c h u n', 'theo tiêu chuẩn'),
        (r'T C V N I S O 9 0 0 1', 'TCVN ISO 9001'),
        (r'n h m m b o p h h p', 'nhằm đảm bảo phù hợp'),
        (r'v i q u y n h', 'với quy định'),
        (r'c a p h p l u t', 'cấp hộ tịch'),
        (r'v y u c u c a c n h n', 'và yêu cầu của cá nhân'),
        (r't c h c', 'tổ chức'),
        (r'P H M V I', 'PHỤ MỤC'),
        (r'p d n g i v i c c t c h c', 'phụ lục dành cho việc cấp hộ tịch'),
        (r'c n h n c n h u c u t h c h i n d c h', 'cá nhân có nhu cầu thực hiện dịch vụ hành chính'),
        (r'v h n h c h n h c n g p h h p', 'và hộ tịch phù hợp'),
        (r'v i t h m q u y n g i i q u y t c a c q u a n', 'với thẩm quyền giải quyết của các quan'),
        (r'T I L I U V I N D N', 'THÔNG TIN ĐIỆN TỬ'),
        (r'T i u c h u n q u c g i a', 'Tiêu chuẩn quốc gia'),
        (r'T C V N I S O 9 0 0 1 : 2 0 1 5', 'TCVN ISO 9001:2015'),
        (r'C c v n b n p h p q u y l i n q u a n c p t i m c 5 c a', 'Các văn bản pháp luật quy định cấp hộ tịch gồm có 5'),
        (r'Q u y t n h s 1 0 1 / Q - B K H C N', 'Quyết định số 101/QĐ-BKHCN'),
        (r'n g y 2 1 t h n g 0 1 n m 2 0 1 9', 'ngày 21 tháng 01 năm 2019'),
        (r'c a B K h o a h c v C n g n g h', 'của Bộ Khoa học và Công nghệ'),
        (r'v v i c c n g b', 'về việc công bố'),
        (r'M h n h k h u n g', 'Mô hình khung'),
        (r'H t h n g q u n l c h t l n g', 'Hệ thống quản lý chất lượng'),
        (r't h e o t i u c h u n q u c g i a', 'theo tiêu chuẩn quốc gia'),
        (r'T C V N I S O 9 0 0 1 : 2 0 1 5', 'TCVN ISO 9001:2015'),
        (r'c h o c c l o i h n h c q u a n', 'cho các loại hình cơ quan'),
        (r'h n h c h n h n h n c t i a p h n g', 'hành chính nhà nước tiếp nhận'),
        (r'N H N G H ( A V V I T T T U B N D', 'NHÀ NƯỚC (ỦY BAN NHÂN DÂN)'),
        (r'y b a n n h n d n', 'ủy ban nhân dân'),
        (r'T T H C', 'TỈNH THÀNH'),
        (r'T h t c h n h c h n h', 'Thủ tục hành chính'),
        (r'G C N', 'GIÁO DỤC'),
        (r'G i y c h n g n h n', 'Giấy chứng nhận'),
        (r'I S O', 'ISO'),
        (r'H t h n g q u n l c h t l n g', 'Hệ thống quản lý chất lượng'),
        (r'T C V N I S O 9 0 0 1 : 2 0 1 5', 'TCVN ISO 9001:2015'),
        (r'B P T N & H T', 'BỘ PHẬN & HẠ TẦNG'),
        (r'B p h n t i p n h n v h o n t r k t q u', 'Bộ phận tiếp nhận hồ sơ và trả kết quả'),
        (r'C N & T C', 'CÁN BỘ & TRÁCH NHIỆM'),
        (r'C n h n v t c', 'Cán bộ nghiệp vụ')
    ]

    for old, new in replacements:
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)

    return text.strip()

def extract_structured_info(text):
    """Trích xuất thông tin có cấu trúc từ text đã làm sạch"""

    info = {
        'title': '',
        'code': '',
        'sections': {},
        'fee_info': [],
        'form_info': [],
        'requirements': []
    }

    # Tìm tiêu đề
    title_match = re.search(r'QUY TRÌNH MIỂU TẢ: (QT \d+/CX-HCTP) ([^L]+) L', text)
    if title_match:
        info['code'] = title_match.group(1)
        info['title'] = title_match.group(2).strip()

    # Tìm các section
    section_patterns = {
        'thành_phần_hồ_sơ': r'THÀNH PHẦN HỒ SƠ.*?:(.*?)(?=GIẤY TỜ|$)',
        'giấy_tờ_phải_nộp': r'GIẤY TỜ PHẢI NỘP.*?:(.*?)(?=GIẤY TỜ PHẢI XUẤT TRÌNH|$)',
        'giấy_tờ_xuất_trình': r'GIẤY TỜ PHẢI XUẤT TRÌNH.*?:(.*?)(?=THỜI HẠN|$)',
        'thời_hạn': r'THỜI HẠN GIẢI QUYẾT.*?:(.*?)(?=ĐỐI TƯỢNG|$)',
        'phí_lệ_phí': r'PHÍ.*?LỆ PHÍ.*?:(.*?)(?=QUY TRÌNH|$)',
        'quy_trình': r'QUY TRÌNH XỬ LÝ.*?:(.*?)(?=KẾT QUẢ|$)',
        'kết_quả': r'KẾT QUẢ THỰC HIỆN.*?:(.*?)(?=PHÍ|$)',
        'cơ_quan_thực_hiện': r'CƠ QUAN THỰC HIỆN.*?:(.*?)(?=CƠ QUAN PHỐI HỢP|$)'
    }

    for section_name, pattern in section_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if matches:
            info['sections'][section_name] = [match.strip() for match in matches if match.strip()]

    # Tìm thông tin phí
    fee_patterns = [
        r'(\d{1,3}(?:\.\d{3})*|\d+)[\s]*(?:đồng|đ|vnd|vnđ)',
        r'miễn phí',
        r'không thu phí'
    ]

    for pattern in fee_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        info['fee_info'].extend(matches)

    # Tìm thông tin biểu mẫu
    form_keywords = ['tờ khai', 'biểu mẫu', 'đơn', 'mẫu', 'form']
    for keyword in form_keywords:
        if keyword in text.lower():
            info['form_info'].append(keyword)

    return info

def main():
    # Nội dung raw từ file .doc (copy từ output trước)
    raw_content = """{ D# bjbjrr O| j j` , , , , , @ @ @ 8 x @ @" V" F " " " 1+ : k+ + < > > > > > > c > ! , + + " 1+ + + > ,
 , " " s _ " S S S + { , " , " < S + < S S D " p_ & ( < x L , 4 + + S + + + + + > > Y + + + + + + + + + + + + + + + + X : S T P H P Q U Y T R I N H M h i u : Q T 0 2 / C X - H C T P n g k k h a i s i n h c y u t n c n g o i L n b a n h n h : 0 1 N g y b a n h n h : 0 7 / 7 / 2 0 2 5 M C L C S A I T I L I U M C C H P H M V I T I L I U V I N D N N H N G H ( A / V I T T T N I D U N G Q U Y T R N H B I U M U H S C N L U T r c h n h i m S o n t h o X e m x t P h d u y t H t n V T h H u y n T r a n g N g u y n T h P h n g T h u H M i n h H i C h k C h c v C h u y n v i n T r n g P h n g P h G i m c S T p h p T R A N G T H E O D I S L N S A I T I L I U S T T T m l c n i d u n g c n s a i C s p h p l h o c c n c v v i c s a i L n s a i M C C H Q u y n h t h n h p h n h s , l p h ( n u c ) , t r n h t , c c h t h c v t h i g i a n g i i q u y t h s h n h c h n h c a c q u a n t h e o t i u c h u n T C V N I S O 9 0 0 1 : 2 0 1 5 n h m m b o p h h p v i q u y n h c a p h p l u t v y u c u c a c n h n , t c h c . P H M V I p d n g i v i c c t c h c , c n h n c n h u c u t h c h i n d c h v h n h c h n h c n g p h h p v i t h m q u y n g i i q u y t c a c q u a n . T I L I U V I N D N T i u c h u n q u c g i a T C V N I S O 9 0 0 1 : 2 0 1 5 . C c v n b n p h p q u y l i n q u a n c p t i m c 5 c a Q u y t n h s 1 0 1 / Q - B K H C N n g y 2 1 t h n g 0 1 n m 2 0 1 9 c a B K h o a h c v C n g n g h v v i c c n g b M h n h k h u n g H t h n g q u n l c h t l n g t h e o t i u c h u n q u c g i a T C V N I S O 9 0 0 1 : 2 0 1 5 c h o c c l o i h n h c q u a n h n h c h n h n h n c t i a p h n g . N H N G H ( A V V I T T T U B N D : y b a n n h n d n T T H C : T h t c h n h c h n h G C N : G i y c h n g n h n I S O : H t h n g q u n l c h t l n g T C V N I S O 9 0 0 1 : 2 0 1 5 B P T N & H T : B p h n t i p n h n v h o n t r k t q u C N & T C : C n h n v t c"""

    # Làm sạch text
    clean_text = clean_doc_text(raw_content)
    print("📄 NỘI DUNG ĐÃ LÀM SẠCH:")
    print("=" * 80)
    print(clean_text[:2000])
    print("=" * 80)

    # Phân tích cấu trúc
    structured_info = extract_structured_info(clean_text)
    print("\n📋 THÔNG TIN CÓ CẤU TRÚC:")
    print("=" * 80)
    print(json.dumps(structured_info, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
