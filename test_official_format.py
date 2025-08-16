#!/usr/bin/env python3
"""
TEST: Official PhoGPT Format - Sử dụng template chính thức
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.language_model import LLMService

def test_official_format():
    """Test official PhoGPT format - ### Câu hỏi: ### Trả lời:"""
    
    print("=== TEST OFFICIAL PHOGPT FORMAT ===")
    
    # Initialize service
    llm_service = LLMService()
    
    # Test query
    query = "Thủ tục đăng ký kết hôn có tính phí không?"
    context = "Thông tin đăng ký kết hôn miễn phí."
    
    print(f"🔍 Query: {query}")
    print(f"📄 Context: {context}")
    
    try:
        # Generate response
        result = llm_service.generate_response(
            user_query=query,
            context=context
        )
        
        print(f"\n✅ Success!")
        print(f"📝 Response: '{result['response']}'")
        print(f"📊 Response length: {len(result['response'])} chars")
        print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
        print(f"🧮 Tokens - Prompt: {result['prompt_tokens']}, Completion: {result['completion_tokens']}")
        
        # Check if response is meaningful
        response_lower = result['response'].lower()
        if (len(result['response']) > 20 and 
            ("miễn phí" in response_lower or "không" in response_lower or "free" in response_lower)):
            print("✅ RESPONSE LOOKS GREAT! Using official format worked!")
        else:
            print("⚠️ Response could be improved")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_official_format()
