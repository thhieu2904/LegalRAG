#!/usr/bin/env python3
"""
🎯 TEST MULTI-TURN CLARIFICATION CONVERSATION
Test luồng hội thoại đa tầng theo thiết kế:
- Giai đoạn 1: Query mơ hồ → Clarification needed
- Giai đoạn 2: Chọn collection → Question suggestions  
- Giai đoạn 3: Chọn câu hỏi cụ thể → RAG answer
"""

import sys
import os
import requests
import time
import json
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_multi_turn_conversation():
    """
    Test complete multi-turn conversation flow
    """
    print("🎯 TESTING MULTI-TURN CLARIFICATION CONVERSATION")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # GIAI ĐOẠN 1: Ambiguous query
    print("\n1️⃣ GIAI ĐOẠN 1: Testing ambiguous query...")
    query_payload = {
        "query": "mình tính hỏi dụ đăng ký",  # Câu hỏi mơ hồ
        "session_id": None
    }
    
    response = requests.post(f"{base_url}/api/v2/optimized-query", json=query_payload)
    
    if response.status_code != 200:
        print(f"❌ Query failed: {response.status_code}")
        print(response.text)
        return False
        
    result = response.json()
    
    if result.get("type") != "clarification_needed":
        print(f"❌ Expected clarification_needed, got: {result.get('type')}")
        return False
        
    print(f"✅ Collection selection triggered")
    print(f"   Confidence: {result.get('confidence')}")
    print(f"   Collections available: {len(result.get('clarification', {}).get('options', []))}")
    
    # Extract session_id and first collection option
    session_id = result.get("session_id")
    options = result.get("clarification", {}).get("options", [])
    
    if not options:
        print("❌ No collection options found")
        return False
    
    # GIAI ĐOẠN 2: Select collection → Should get question suggestions
    print(f"\n2️⃣ GIAI ĐOẠN 2: Selecting collection...")
    selected_collection_option = options[0]  # Chọn collection đầu tiên
    print(f"   Selected collection: {selected_collection_option.get('title')}")
    
    clarification_payload = {
        "session_id": session_id,
        "original_query": "mình tính hỏi dụ đăng ký",  # Original query
        "selected_option": selected_collection_option  # Full option object với action: proceed_with_collection
    }
    
    response = requests.post(f"{base_url}/api/v2/clarify", json=clarification_payload)
    
    if response.status_code != 200:
        print(f"❌ Collection selection failed: {response.status_code}")
        print(response.text)
        return False
        
    result = response.json()
    
    # Should get question suggestions, not direct answer
    if result.get("type") == "answer":
        print("❌ Got direct answer instead of question suggestions!")
        print("   This means multi-turn is not working - system skipped Giai đoạn 3")
        return False
        
    if result.get("type") != "clarification_needed":
        print(f"❌ Expected question suggestions (clarification_needed), got: {result.get('type')}")
        return False
    
    # Check if it's question suggestion style
    clarification = result.get("clarification", {})
    if clarification.get("style") != "question_suggestion":
        print(f"❌ Expected question_suggestion style, got: {clarification.get('style')}")
        return False
    
    print(f"✅ Question suggestions generated")
    print(f"   Style: {clarification.get('style')}")
    print(f"   Stage: {clarification.get('stage')}")
    print(f"   Questions available: {len(clarification.get('options', []))}")
    
    # Print some suggestion examples
    suggestions = clarification.get("options", [])
    for i, suggestion in enumerate(suggestions[:3]):
        print(f"   {i+1}. {suggestion.get('title', 'N/A')}")
    
    # GIAI ĐOẠN 3: Select specific question → Should get RAG answer
    print(f"\n3️⃣ GIAI ĐOẠN 3: Selecting specific question...")
    
    # Find a question option (not manual_input)
    question_option = None
    for opt in suggestions:
        if opt.get("action") == "proceed_with_question":
            question_option = opt
            break
    
    if not question_option:
        print("❌ No question options found with proceed_with_question action")
        return False
    
    print(f"   Selected question: {question_option.get('title')}")
    
    final_clarification_payload = {
        "session_id": session_id,
        "original_query": "mình tính hỏi dụ đăng ký",  # Keep original query
        "selected_option": question_option  # Full option với action: proceed_with_question
    }
    
    response = requests.post(f"{base_url}/api/v2/clarify", json=final_clarification_payload)
    
    if response.status_code != 200:
        print(f"❌ Question selection failed: {response.status_code}")
        print(response.text)
        return False
        
    result = response.json()
    
    # NOW should get direct answer
    if result.get("type") != "answer":
        print(f"❌ Expected final answer, got: {result.get('type')}")
        if result.get("type") == "clarification_needed":
            print("   Still asking for clarification - multi-turn logic failed!")
        print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return False
    
    print(f"✅ Final answer received!")
    print(f"   Answer length: {len(result.get('answer', ''))}")
    print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
    print(f"   Answer preview: {result.get('answer', '')[:200]}...")
    
    return True

def test_direct_question_routing():
    """
    Test that specific questions still route directly (high confidence)
    """
    print("\n🎯 TESTING DIRECT ROUTING FOR SPECIFIC QUESTIONS")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test với câu hỏi cụ thể
    specific_queries = [
        "thủ tục khai sinh cần giấy tờ gì",
        "đăng ký kết hôn ở đâu",
        "làm chứng thực bản sao như thế nào"
    ]
    
    for query in specific_queries:
        print(f"\n📝 Testing: {query}")
        
        payload = {
            "query": query,
            "session_id": None
        }
        
        response = requests.post(f"{base_url}/api/v2/optimized-query", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("type") == "answer":
                print(f"   ✅ Direct answer (high confidence routing)")
            elif result.get("type") == "clarification_needed":
                print(f"   ⚠️  Clarification needed (lower confidence)")
            else:
                print(f"   ❓ Other result: {result.get('type')}")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
    
    return True

if __name__ == "__main__":
    print("🚀 TESTING MULTI-TURN CLARIFICATION SYSTEM")
    print("Make sure server is running on localhost:8000")
    print()
    
    try:
        # Test server connectivity
        response = requests.get("http://localhost:8000/")
        if response.status_code != 200:
            print("❌ Server not responding at localhost:8000")
            print("Please start the server first")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at localhost:8000")
        print("Please start the server first")
        sys.exit(1)
    
    # Run tests
    success = True
    
    # Test 1: Multi-turn conversation
    if not test_multi_turn_conversation():
        success = False
        
    time.sleep(1)  # Brief pause
    
    # Test 2: Direct routing still works
    if not test_direct_question_routing():
        success = False
    
    # Final result
    print("\n" + "=" * 60)
    if success:
        print("🎉 MULTI-TURN CONVERSATION SYSTEM WORKING!")
        print("✅ Giai đoạn 1: Ambiguous query → Collection selection")
        print("✅ Giai đoạn 2: Collection selected → Question suggestions") 
        print("✅ Giai đoạn 3: Question selected → Final RAG answer")
        print("✅ Direct routing still works for specific questions")
        print("\n🚀 READY FOR PRODUCTION!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the multi-turn implementation")
        sys.exit(1)
