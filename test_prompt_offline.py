#!/usr/bin/env python3
"""
🧪 OFFLINE TEST: PROMPT SERVICE CHAT HISTORY FIX 
Test logic sửa chat history offline không cần server

TEST TARGET: Kiểm tra việc lưu trữ đầy đủ chat history (user + assistant) trong prompt_service.py
"""

import sys
import os

# Add the rag_service directory to path để import được
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag_service'))

try:
    from app.services.prompt_service import prompt_service
    print("✅ Successfully imported prompt_service")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)

def test_chat_history_improvement():
    """Test the improved chat history handling"""
    print("\n" + "="*80)
    print("🧪 TESTING CHAT HISTORY IMPROVEMENT")
    print("="*80)
    
    # Simulate a conversation history với cả user và assistant
    test_chat_history = [
        {"role": "user", "content": "đăng ký khai sinh cần giấy tờ gì?"},
        {"role": "assistant", "content": "Để đăng ký khai sinh, bạn cần: 1) Tờ khai đăng ký khai sinh, 2) Giấy chứng sinh, 3) Hộ khẩu của cha mẹ"},
        {"role": "user", "content": "có cần đóng phí không?"},
        {"role": "assistant", "content": "Đăng ký khai sinh miễn phí. Chỉ phải đóng phí 8.000 đồng nếu muốn cấp bản sao giấy khai sinh"},
    ]
    
    test_query = "ý là phí đó bao nhiêu tiền?"
    test_context = "Thông tin về phí đăng ký khai sinh: Miễn phí đăng ký. Phí cấp bản sao: 8.000 VND"
    
    # Generate prompt using new method
    complete_prompt = prompt_service.get_complete_rag_prompt(
        query=test_query,
        context=test_context,
        confidence_level="medium",
        chat_history=test_chat_history
    )
    
    print("📊 ANALYSIS:")
    print(f"   - Prompt length: {len(complete_prompt)} characters")
    print(f"   - Contains user messages: {'Người dùng:' in complete_prompt}")
    print(f"   - Contains assistant messages: {'Trợ lý:' in complete_prompt}")
    print(f"   - Proper format: {complete_prompt.count('### Câu hỏi:') == 1 and complete_prompt.count('### Trả lời:') == 1}")
    
    # Check for anti-hallucination rules
    anti_halluc_rules = [
        "KHÔNG đặt câu hỏi ngược lại",
        "KHÔNG tự suy luận",
        "KHÔNG tạo ra câu hỏi gợi ý"
    ]
    
    has_anti_halluc_rules = all(rule in complete_prompt for rule in anti_halluc_rules)
    print(f"   - Contains anti-hallucination rules: {has_anti_halluc_rules}")
    
    print("\n📝 GENERATED PROMPT:")
    print("-" * 80)
    print(complete_prompt)
    print("-" * 80)
    
    return {
        "has_user_messages": "Người dùng:" in complete_prompt,
        "has_assistant_messages": "Trợ lý:" in complete_prompt, 
        "proper_format": complete_prompt.count('### Câu hỏi:') == 1 and complete_prompt.count('### Trả lời:') == 1,
        "has_anti_hallucination": has_anti_halluc_rules,
        "prompt_length": len(complete_prompt)
    }

def test_empty_chat_history():
    """Test with empty chat history"""
    print("\n" + "="*80)
    print("🧪 TESTING EMPTY CHAT HISTORY")
    print("="*80)
    
    complete_prompt = prompt_service.get_complete_rag_prompt(
        query="đăng ký kết hôn cần gì?",
        context="Thông tin về đăng ký kết hôn...",
        confidence_level="high",
        chat_history=None
    )
    
    print(f"✅ Empty history handled correctly: {len(complete_prompt) > 0}")
    return len(complete_prompt) > 0

def test_long_chat_history():
    """Test với chat history dài để kiểm tra truncation"""
    print("\n" + "="*80)
    print("🧪 TESTING LONG CHAT HISTORY TRUNCATION")
    print("="*80)
    
    # Tạo chat history dài
    long_history = []
    for i in range(10):
        long_history.extend([
            {"role": "user", "content": f"Câu hỏi {i+1}"},
            {"role": "assistant", "content": f"Câu trả lời {i+1}"}
        ])
    
    complete_prompt = prompt_service.get_complete_rag_prompt(
        query="câu hỏi mới",
        context="context mới",
        confidence_level="medium",
        chat_history=long_history
    )
    
    # Chỉ nên giữ 4 messages gần nhất (2 cặp user-assistant)
    user_count = complete_prompt.count("Người dùng:")
    assistant_count = complete_prompt.count("Trợ lý:")
    
    print(f"   - Original history length: {len(long_history)} messages")
    print(f"   - User messages in prompt: {user_count}")
    print(f"   - Assistant messages in prompt: {assistant_count}")
    print(f"   - Proper truncation: {user_count <= 2 and assistant_count <= 2}")
    
    return user_count <= 2 and assistant_count <= 2

def run_all_offline_tests():
    """Run all offline tests"""
    print("🎯 PROMPT SERVICE OFFLINE TESTS")
    print("Testing improvements to fix hallucination and system prompt leakage")
    
    # Test 1: Chat history improvement
    history_result = test_chat_history_improvement()
    
    # Test 2: Empty history
    empty_result = test_empty_chat_history()
    
    # Test 3: Long history truncation
    truncation_result = test_long_chat_history()
    
    # Final summary
    print("\n" + "="*80)
    print("🎯 OFFLINE TEST SUMMARY")
    print("="*80)
    
    all_passed = all([
        history_result["has_user_messages"],
        history_result["has_assistant_messages"],
        history_result["proper_format"],
        history_result["has_anti_hallucination"],
        empty_result,
        truncation_result
    ])
    
    print(f"✅ Chat history includes user messages: {history_result['has_user_messages']}")
    print(f"✅ Chat history includes assistant messages: {history_result['has_assistant_messages']}")
    print(f"✅ Proper prompt format maintained: {history_result['proper_format']}")
    print(f"✅ Anti-hallucination rules added: {history_result['has_anti_hallucination']}")
    print(f"✅ Empty history handled: {empty_result}")
    print(f"✅ Long history truncated properly: {truncation_result}")
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED - Priority 1 improvements verified!")
        print("\n🔧 Key fixes implemented:")
        print("   1. Chat history now includes both user AND assistant messages")
        print("   2. Added strong anti-hallucination rules to base prompt")  
        print("   3. Prevented inappropriate question generation")
        print("   4. Maintained proper prompt format")
        print("   5. Smart truncation of long chat histories")
    else:
        print("\n❌ Some tests failed - need further investigation")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = run_all_offline_tests()
        print(f"\n🏁 Test result: {'SUCCESS' if success else 'FAILURE'}")
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)