import json
import os
from typing import Dict, List, Any

class LegalRAGResponseGenerator:
    """
    Class để tạo câu trả lời từ nội dung JSON sử dụng LLM
    """

    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.data = self._load_json()

    def _load_json(self) -> Dict[str, Any]:
        """Load JSON data từ file"""
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def create_context_prompt(self, question: str) -> str:
        """Tạo prompt context cho LLM dựa trên câu hỏi và nội dung JSON"""

        metadata = self.data.get('metadata', {})
        fee_structure = metadata.get('fee_structure', {})
        content_chunks = self.data.get('content_chunks', [])

        # Tạo context từ metadata
        context = f"""
Dựa trên thông tin từ quy trình: "{metadata.get('title', '')}"
Mã hiệu: {metadata.get('code', '')}
Cơ quan ban hành: {metadata.get('issuing_authority', '')}
Ngày ban hành: {metadata.get('effective_date', '')}
Cơ quan thực hiện: {metadata.get('executing_agency', '')}

THỜI HẠN GIẢI QUYẾT:
{metadata.get('processing_time_text', '')}

ĐỐI TƯỢNG THỰC HIỆN:
{', '.join(metadata.get('applicant_type', []))}

LỆ PHÍ CHI TIẾT:
"""

        # Thêm thông tin lệ phí
        if fee_structure:
            main_fee = fee_structure.get('main_fee', {})
            if main_fee:
                context += f"""
- Lệ phí trực tiếp: {main_fee.get('direct', 'N/A')}
- Lệ phí trực tuyến: {main_fee.get('online', 'N/A')}
- Mô tả: {main_fee.get('description', '')}
"""

            # Thêm lệ phí theo khu vực
            regional_fees = fee_structure.get('regional_fees', [])
            if regional_fees:
                context += "\nLỆ PHÍ THEO KHU VỰC:\n"
                for fee in regional_fees:
                    context += f"- {fee.get('area', '')}: Trực tiếp {fee.get('direct', 'N/A')}, Trực tuyến {fee.get('online', 'N/A')}\n"

            # Thêm miễn lệ phí
            exemptions = fee_structure.get('exemptions', [])
            if exemptions:
                context += f"\nMIỄN LỆ PHÍ CHO:\n" + "\n".join(f"- {ex}" for ex in exemptions)

            # Thêm phí bổ sung
            additional_fees = fee_structure.get('additional_fees', {})
            if additional_fees:
                context += f"\nPHÍ BỔ SUNG:\n"
                for key, value in additional_fees.items():
                    context += f"- {key}: {value}\n"

        # Thêm yêu cầu điều kiện
        requirements = metadata.get('requirements_conditions', '')
        if requirements:
            context += f"\nYÊU CẦU ĐIỀU KIỆN:\n{requirements}\n"

        # Thêm nội dung chunks quan trọng
        if content_chunks:
            context += "\nTHÔNG TIN CHI TIẾT:\n"
            for chunk in content_chunks[:3]:  # Lấy 3 chunks đầu tiên
                context += f"\n{chunk.get('section_title', '')}:\n{chunk.get('content', '')[:500]}...\n"

        # Tạo prompt cuối cùng
        prompt = f"""
{context}

CÂU HỎI: {question}

Hãy trả lời câu hỏi trên dựa trên thông tin quy trình hộ tịch ở trên.
Yêu cầu:
1. Trả lời chính xác, đầy đủ dựa trên thông tin có sẵn
2. Nếu thông tin không có trong dữ liệu, hãy nói rõ
3. Sử dụng ngôn ngữ dễ hiểu, thân thiện
4. Cung cấp thông tin về lệ phí, thời hạn, hồ sơ nếu liên quan
5. Đưa ra hướng dẫn cụ thể nếu cần thiết

TRẢ LỜI:
"""

        return prompt

    def generate_response(self, question: str) -> str:
        """Tạo câu trả lời cho câu hỏi (demo - trong thực tế sẽ gọi LLM API)"""

        prompt = self.create_context_prompt(question)

        # Trong thực tế, đây là nơi gọi LLM API như OpenAI, Claude, etc.
        # Ví dụ: response = openai.ChatCompletion.create(...)

        # Demo response với thông tin đầy đủ
        metadata = self.data.get('metadata', {})
        fee_structure = metadata.get('fee_structure', {})

        demo_response = f"""
Dựa trên thông tin từ quy trình "{metadata.get('title', '')}", tôi sẽ trả lời câu hỏi của bạn:

**Câu hỏi:** {question}

**Thông tin cơ bản:**
- **Thời hạn giải quyết:** {metadata.get('processing_time_text', '')}
- **Cơ quan thực hiện:** {metadata.get('executing_agency', '')}
- **Đối tượng:** {', '.join(metadata.get('applicant_type', []))}

**Lệ phí áp dụng:**
"""

        # Hiển thị lệ phí chi tiết
        if fee_structure:
            main_fee = fee_structure.get('main_fee', {})
            if main_fee and isinstance(main_fee, dict):
                demo_response += f"- **Lệ phí chính:**\n"
                demo_response += f"  - Trực tiếp: {main_fee.get('direct', 'N/A')}\n"
                demo_response += f"  - Trực tuyến: {main_fee.get('online', 'N/A')}\n"
                if main_fee.get('description'):
                    demo_response += f"  - Áp dụng: {main_fee.get('description')}\n"

            # Thêm lệ phí theo khu vực
            regional_fees = fee_structure.get('regional_fees', [])
            if regional_fees and isinstance(regional_fees, list):
                demo_response += "\n- **Lệ phí theo khu vực:**\n"
                for fee in regional_fees:
                    if isinstance(fee, dict):
                        demo_response += f"  - {fee.get('area', '')}: Trực tiếp {fee.get('direct', 'N/A')}, Trực tuyến {fee.get('online', 'N/A')}\n"

            # Thêm miễn lệ phí
            exemptions = fee_structure.get('exemptions', [])
            if exemptions and isinstance(exemptions, list):
                demo_response += f"\n- **Miễn lệ phí cho:**\n"
                for ex in exemptions:
                    demo_response += f"  - {ex}\n"

            # Thêm phí bổ sung
            additional_fees = fee_structure.get('additional_fees', {})
            if additional_fees and isinstance(additional_fees, dict):
                demo_response += f"\n- **Phí bổ sung:**\n"
                for key, value in additional_fees.items():
                    demo_response += f"  - {key}: {value}\n"

        # Thêm yêu cầu điều kiện
        requirements = metadata.get('requirements_conditions', '')
        if requirements:
            demo_response += f"\n**Yêu cầu và điều kiện:**\n{requirements}\n"

        demo_response += """
**Lưu ý quan trọng:**
- Hồ sơ cần chuẩn bị đầy đủ theo quy định
- Giấy tờ nước ngoài cần hợp pháp hóa lãnh sự
- Có thể nộp hồ sơ trực tuyến hoặc trực tiếp
- Nên liên hệ UBND cấp xã nơi cư trú để được tư vấn cụ thể

Để được hỗ trợ chi tiết hơn, bạn có thể liên hệ trực tiếp với UBND cấp xã nơi cư trú hoặc truy cập Cổng dịch vụ công quốc gia.
"""

        return demo_response

def demo_legal_rag_responses():
    """Demo function để show cách sử dụng"""

    # Đường dẫn đến file JSON
    json_path = r"d:\Personal\LegalRAG_Fixed\backend\data\storage\collections\quy_trinh_cap_ho_tich_cap_xa\documents\DOC_028\28. Ghi vào Sổ hộ tịch việc ly hôn, hủy việc kết hôn của công dân Việt Nam đã được giải quyết tại cơ quan có thẩm quyền của nước ngoài.json"

    # Khởi tạo generator
    generator = LegalRAGResponseGenerator(json_path)

    # Các câu hỏi mẫu
    sample_questions = [
        "Lệ phí cho thủ tục ghi vào sổ hộ tịch việc ly hôn từ nước ngoài là bao nhiêu?",
        "Tôi cần chuẩn bị những giấy tờ gì để ghi chú ly hôn từ nước ngoài?",
        "Thời hạn giải quyết thủ tục này là bao lâu?",
        "Tôi có được miễn lệ phí không nếu thuộc hộ nghèo?",
        "Tôi có thể nộp hồ sơ trực tuyến không?"
    ]

    print("=== DEMO LEGAL RAG RESPONSE GENERATOR ===\n")

    for i, question in enumerate(sample_questions, 1):
        print(f"--- Câu hỏi {i}: {question} ---")
        response = generator.generate_response(question)
        print(response)
        print("\n" + "="*80 + "\n")

    # Show prompt structure
    print("=== CẤU TRÚC PROMPT ĐƯỢC TẠO ===")
    sample_prompt = generator.create_context_prompt(sample_questions[0])
    print(f"Độ dài prompt: {len(sample_prompt)} ký tự")
    print("Preview prompt (1000 ký tự đầu):")
    print(sample_prompt[:1000] + "...")

if __name__ == "__main__":
    demo_legal_rag_responses()
