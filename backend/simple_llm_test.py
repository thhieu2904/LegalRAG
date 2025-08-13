"""
Script đơn giản để kiểm tra system prompt và LLM behavior
"""

import os
import sys
import logging
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent
sys.path.append(str(backend_path))

from app.services.language_model import LLMService
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_llm_with_simple_context():
    """Test LLM với context đơn giản để kiểm tra hallucination"""
    
    print("🧪 TESTING LLM WITH SIMPLE CONTEXT")
    print("=" * 60)
    
    # Khởi tạo LLM service
    llm_service = LLMService()
    
    # Test case 1: Context rõ ràng về lệ phí
    test_context = """
📋 TIÊU ĐỀ: Đăng ký khai sinh
🏢 CƠ QUAN THỰC HIỆN: UBND cấp phường/xã
💰 LỆ PHÍ: MIỄN PHÍ (không phải đóng tiền)
⏰ THỜI GIAN XỬ LÝ: Ngay khi nhận đủ hồ sơ hợp lệ

📄 NỘI DUNG 1:
Thủ tục đăng ký khai sinh là MIỄN PHÍ theo quy định của pháp luật Việt Nam.
Người dân không phải đóng bất kỳ khoản phí nào khi làm thủ tục này.

📄 NỘI DUNG 2:
Hồ sơ bao gồm:
- Giấy chứng sinh (do bệnh viện cấp)
- Giấy tờ tùy thân của cha mẹ
"""

    queries = [
        "muốn đăng ký khai sinh thì có cần đóng tiền không",
        "mình muốn hỏi phí khi mà đăng ký khai sinh á",
        "đăng ký khai sinh có tốn phí gì không"
    ]
    
    # Test system prompt hiện tại
    current_system_prompt = """Bạn là trợ lý AI chuyên về pháp luật Việt Nam. Hãy trả lời câu hỏi dựa trên thông tin được cung cấp.

Hướng dẫn trả lời:
1. Trả lời chính xác dựa trên thông tin trong tài liệu
2. Nếu không tìm thấy thông tin, hãy nói rõ và cung cấp trích dẫn để hỗ trợ cho câu trả lời của bạn
3. Sử dụng ngữ điệu thân thiện và chuyên nghiệp khi giao tiếp với người dùng khác về các vấn đề pháp lý liên quan đến Việt Nam"""
    
    print(f"📝 Current System Prompt:")
    print(current_system_prompt)
    print("\n" + "=" * 60)
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 40)
        
        try:
            result = llm_service.generate_response(
                user_query=query,
                context=test_context,
                system_prompt=current_system_prompt,
                max_tokens=200,
                temperature=0.3
            )
            
            print(f"🤖 LLM Response:")
            response_text = result.get('response', 'No response')
            print(f"   {response_text}")
            
            # Phân tích response
            if "miễn phí" in response_text.lower() or "không phải đóng" in response_text.lower():
                print("✅ Correct: LLM hiểu đúng về miễn phí")
            else:
                print("❌ Wrong: LLM không hiểu đúng về lệ phí")
                print("🚨 POTENTIAL HALLUCINATION DETECTED!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

def test_improved_system_prompt():
    """Test với system prompt cải tiến để chặn hallucination"""
    
    print("\n" + "=" * 80)
    print("🔧 TESTING IMPROVED SYSTEM PROMPT")
    print("=" * 80)
    
    # LLM service
    llm_service = LLMService()
    
    # Context như trên
    test_context = """
📋 TIÊU ĐỀ: Đăng ký khai sinh
💰 LỆ PHÍ: MIỄN PHÍ (không phải đóng tiền)

📄 NỘI DUNG:
Thủ tục đăng ký khai sinh là MIỄN PHÍ theo quy định của pháp luật Việt Nam.
"""
    
    # IMPROVED system prompt - chặt chẽ hơn
    improved_system_prompt = """Bạn là trợ lý AI chuyên về pháp luật Việt Nam. 

QUAN TRỌNG - QUY TẮC BẮT BUỘC:
1. CHỈ trả lời dựa trên thông tin CÓ TRONG tài liệu được cung cấp
2. KHÔNG tự tạo thông tin không có trong tài liệu
3. Nếu câu hỏi về "phí" hoặc "tiền" - hãy TÌM CHÍNH XÁC thông tin "LỆ PHÍ" trong tài liệu
4. Trả lời NGẮN GỌN, TRỰC TIẾP vào vấn đề được hỏi
5. KHÔNG nêu thông tin về các trường hợp khác nếu không được hỏi

Cấu trúc trả lời:
- Trả lời trực tiếp câu hỏi (1-2 câu)
- Trích dẫn thông tin từ tài liệu"""
    
    query = "muốn đăng ký khai sinh thì có cần đóng tiền không"
    
    print(f"📝 Improved System Prompt:")
    print(improved_system_prompt[:200] + "...")
    print(f"\n🔍 Test Query: {query}")
    print("-" * 50)
    
    try:
        result = llm_service.generate_response(
            user_query=query,
            context=test_context,
            system_prompt=improved_system_prompt,
            max_tokens=150,
            temperature=0.1  # Giảm temperature để ít hallucination
        )
        
        print(f"🤖 Improved Response:")
        response_text = result.get('response', 'No response')
        print(f"   {response_text}")
        
        # Phân tích
        if len(response_text.split()) < 50:  # Kiểm tra độ dài
            print("✅ Good: Response ngắn gọn")
        else:
            print("⚠️  Warning: Response quá dài")
            
        if "miễn phí" in response_text.lower():
            print("✅ Correct: Trả lời đúng về miễn phí")
        else:
            print("❌ Wrong: Vẫn không trả lời đúng")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_llm_with_simple_context()
    test_improved_system_prompt()
