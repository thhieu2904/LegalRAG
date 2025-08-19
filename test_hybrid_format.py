#!/usr/bin/env python3
"""
TEST: Hybrid Format Fix - Kiểm tra format đơn giản hơn với PhoGPT
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.language_model import LLMService

def test_hybrid_format():
    """Test hybrid format - format đơn giản hơn cho PhoGPT"""
    
    print("=== TEST HYBRID FORMAT FIX ===")
    
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
        if len(result['response']) > 20 and "miễn phí" in result['response'].lower():
            print("✅ RESPONSE LOOKS GOOD!")
        else:
            print("❌ Response still needs improvement")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hybrid_format()
