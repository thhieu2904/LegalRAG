#!/usr/bin/env python3
"""
DEBUG ANSWER LENGTH: 0 ISSUE - DEEP INVESTIGATION
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.language_model import LLMService
from app.core.config import settings
import json

def debug_llm_generation():
    """Debug trực tiếp LLM generation"""
    
    print("🔍 DEEP DEBUG: LLM GENERATION ISSUE")
    print("=" * 60)
    
    # Tạo một LLMService instance
    llm_service = LLMService()
    
    # Test với prompt đơn giản
    simple_context = "Thông tin: Đăng ký kết hôn miễn lệ phí."
    simple_query = "Lệ phí là bao nhiêu?"
    simple_system = "Bạn là trợ lý pháp luật. Trả lời ngắn gọn."
    
    print("📝 Testing with simple inputs:")
    print(f"   Context: {simple_context}")
    print(f"   Query: {simple_query}")
    print(f"   System: {simple_system}")
    
    # Tạo prompt
    formatted_prompt = llm_service._format_prompt(
        system_prompt=simple_system,
        user_query=simple_query,
        context=simple_context,
        chat_history=None
    )
    
    print(f"\n📋 Generated ChatML prompt:")
    print("-" * 40)
    print(formatted_prompt)
    print("-" * 40)
    
    # Phân tích prompt
    prompt_length = len(formatted_prompt)
    estimated_tokens = prompt_length // 3
    
    print(f"\n📊 Prompt Analysis:")
    print(f"   Length: {prompt_length} chars")
    print(f"   Estimated tokens: {estimated_tokens}")
    print(f"   Context window: {settings.n_ctx}")
    print(f"   Max tokens: {settings.max_tokens}")
    
    # Tính toán space
    safety_buffer = 256
    available_space = settings.n_ctx - estimated_tokens - safety_buffer
    MINIMUM_RESPONSE_TOKENS = 64
    
    print(f"   Available space: {available_space}")
    print(f"   Minimum required: {MINIMUM_RESPONSE_TOKENS}")
    
    if available_space <= MINIMUM_RESPONSE_TOKENS:
        print(f"   🚨 INSUFFICIENT SPACE - would return default message")
        return
    
    dynamic_max_tokens = min(settings.max_tokens, available_space)
    if dynamic_max_tokens < MINIMUM_RESPONSE_TOKENS:
        dynamic_max_tokens = MINIMUM_RESPONSE_TOKENS
    
    print(f"   Dynamic max tokens: {dynamic_max_tokens}")
    
    # Kiểm tra model có load không
    print(f"\n🤖 Model Status:")
    print(f"   Model loaded: {llm_service.is_model_loaded()}")
    print(f"   Model path exists: {llm_service.model_path.exists()}")
    
    if not llm_service.model_path.exists():
        print(f"   ❌ MODEL FILE NOT FOUND!")
        print(f"   Path: {llm_service.model_path}")
        return
    
    # Test generate nếu có thể
    try:
        print(f"\n🧪 Testing LLM generation...")
        print(f"   Loading model (if not loaded)...")
        
        # Ensure model is loaded
        llm_service.ensure_loaded()
        
        if not llm_service.model:
            print(f"   ❌ MODEL FAILED TO LOAD!")
            return
            
        print(f"   ✅ Model loaded successfully")
        
        # Test với parameters đơn giản
        test_response = llm_service.model(
            formatted_prompt,
            max_tokens=100,  # Số nhỏ để test
            temperature=0.1,
            stop=["<|im_end|>"],
            echo=False,
            stream=False
        )
        
        print(f"\n📋 Raw model response:")
        print(f"   Type: {type(test_response)}")
        
        if isinstance(test_response, dict):
            print(f"   Keys: {list(test_response.keys())}")
            
            if 'choices' in test_response:
                choices = test_response['choices']
                print(f"   Choices count: {len(choices)}")
                
                if len(choices) > 0:
                    first_choice = choices[0]
                    text = first_choice.get('text', '')
                    print(f"   Generated text length: {len(text)}")
                    print(f"   Generated text: '{text}'")
                    
                    if len(text.strip()) == 0:
                        print(f"   🚨 EMPTY TEXT GENERATED!")
                        print(f"   Choice details: {first_choice}")
                else:
                    print(f"   ❌ NO CHOICES IN RESPONSE!")
            else:
                print(f"   ❌ NO 'choices' KEY IN RESPONSE!")
                print(f"   Response: {test_response}")
        else:
            print(f"   Response: {test_response}")
            
    except Exception as e:
        print(f"   ❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()

def test_context_expansion_issue():
    """Test context expansion có thể gây vấn đề"""
    
    print(f"\n🔍 TESTING CONTEXT EXPANSION ISSUE")
    print("=" * 60)
    
    # Simple test với context rỗng
    print("📝 Test 1: Empty context")
    llm_service = LLMService()
    
    empty_prompt = llm_service._format_prompt(
        system_prompt="Trả lời ngắn gọn.",
        user_query="Xin chào",
        context="",
        chat_history=None
    )
    
    print(f"   Empty context prompt length: {len(empty_prompt)}")
    print(f"   Prompt:\n{empty_prompt}")
    
    # Test với context có nội dung
    print(f"\n📝 Test 2: With context")
    
    with_context_prompt = llm_service._format_prompt(
        system_prompt="Trả lời ngắn gọn.",
        user_query="Lệ phí là bao nhiêu?",
        context="Đăng ký kết hôn miễn lệ phí.",
        chat_history=None
    )
    
    print(f"   With context prompt length: {len(with_context_prompt)}")
    print(f"   Prompt:\n{with_context_prompt}")

def main():
    """Chạy debug toàn diện"""
    
    print("🚀 COMPREHENSIVE DEBUG: ANSWER LENGTH: 0 ISSUE")
    print("=" * 70)
    
    try:
        debug_llm_generation()
        test_context_expansion_issue()
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "=" * 70)
    print("🎯 DEBUG COMPLETED")
    print("Check the output above for clues about the Answer length: 0 issue")

if __name__ == "__main__":
    main()
