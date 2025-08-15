#!/usr/bin/env python3
"""
Test Enhanced Prompt for Multiple Questions Generation V2
==========================================================
"""

import sys
from pathlib import Path
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Add app to Python path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from tools.generate_router_with_llm_v2 import SmartRouterLLMGenerator
except ImportError as e:
    logger.error(f"❌ Cannot import SmartRouterLLMGenerator: {e}")
    sys.exit(1)

def test_enhanced_prompt():
    """Test the enhanced prompt with a sample document."""
    print("🧪 Testing Enhanced Prompt for Multiple Questions Generation V2")
    print("=" * 70)
    
    # Sample document for testing
    sample_doc = {
        "metadata": {
            "title": "Đăng ký khai sinh",
            "code": "DK_KS_001",
            "applicant_type": ["Cá nhân", "Tổ chức"],
            "executing_agency": "UBND cấp phường/xã",
            "processing_time_text": "Ngay khi nhận đủ hồ sơ hợp lệ",
            "fee_text": "Miễn phí",
            "submission_method": ["Trực tiếp", "Trực tuyến"],
            "result_delivery": ["Trực tiếp", "Bưu chính"]
        },
        "content_chunks": [
            {
                "section_title": "Thành phần hồ sơ",
                "content": "Đơn đăng ký khai sinh theo mẫu, Giấy chứng sinh hoặc giấy ra viện, Giấy tờ tùy thân của cha mẹ, Giấy chứng nhận kết hôn của cha mẹ..."
            }
        ]
    }
    
    try:
        # Initialize generator
        generator = SmartRouterLLMGenerator()
        
        # Generate summary for prompt
        document_summary = generator._summarize_document_for_prompt(sample_doc)
        
        # Create the actual prompt
        user_query = f"""NHIỆM VỤ: Tạo chính xác 10 câu hỏi về thủ tục "{sample_doc['metadata']['title']}"

THÔNG TIN: {document_summary}

YÊU CẦU: Tạo 10 câu hỏi ngắn gọn, mỗi câu một dòng, đánh số từ 1-10. Mỗi câu phải khác nhau hoàn toàn.

VÍ DỤ FORMAT:
1. Thủ tục này là gì?
2. Ai có thể làm?
3. Cần giấy tờ gì?
4. Chi phí bao nhiêu?
5. Làm ở đâu?
6. Mất bao lâu?
7. Làm online được không?
8. Nhận kết quả như thế nào?
9. Có điều kiện gì đặc biệt?
10. Lưu ý gì khi làm?

BẮT ĐẦU TẠO 10 CÂU HỎI:"""

        system_prompt = "Tạo chính xác 10 câu hỏi ngắn. Đánh số 1-10. Không giải thích thêm."
        
        print("📝 USER QUERY:")
        print(user_query)
        print("\n🧠 SYSTEM PROMPT:")
        print(system_prompt)
        
        # Call LLM
        print(f"\n🤖 LLM RESPONSE:")
        response_data = generator.llm_service.generate_response(
            user_query=user_query,
            max_tokens=500,
            temperature=0.3,
            system_prompt=system_prompt
        )
        
        response_text = response_data.get('response', '')
        print(response_text)
        
        # Extract questions
        print("\n" + "=" * 70)
        result = generator._extract_questions_from_llm_response(response_text, "Đăng ký khai sinh")
        
        if result:
            print("✅ QUESTIONS EXTRACTED SUCCESSFULLY:")
            print(f"📊 Total questions: {1 + len(result.get('question_variants', []))}")
            print(f"🎯 Main question: {result.get('main_question', 'N/A')}")
            print(f"🔢 Variants: {len(result.get('question_variants', []))}")
            
            print(f"\n📋 FULL RESULT:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("❌ FAILED TO EXTRACT QUESTIONS")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_prompt()
