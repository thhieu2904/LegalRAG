#!/usr/bin/env python3
"""
TEST FIX CHO FOLLOW-UP QUESTION BUG
Test case: Câu hỏi follow-up về đăng ký kết hôn
"""

import requests
import json
import time

def test_followup_fix():
    """Test fix cho follow-up question"""
    print("🧪 TESTING FOLLOW-UP QUESTION FIX")
    print("=" * 60)
    
    api_base = "http://localhost:8000/api/v2"
    session_id = None
    
    # Test case 1: Query đầu tiên
    print("🧪 Test 1: Initial query về đăng ký kết hôn")
    print("-" * 40)
    
    payload1 = {
        "query": "Tôi muốn hỏi về thủ tục đăng ký kết hôn",
        "session_id": session_id,
        "max_context_length": 8000,
        "use_ambiguous_detection": True,
        "use_full_document_expansion": True
    }
    
    try:
        response1 = requests.post(f"{api_base}/optimized-query", json=payload1)
        if response1.status_code == 200:
            result1 = response1.json()
            session_id = result1.get('session_id')
            
            print(f"✅ Query 1 successful!")
            print(f"📋 Response Type: {result1.get('type', 'unknown')}")
            print(f"🆔 Session ID: {session_id}")
            
            answer1 = result1.get('answer', '')
            if answer1:
                print(f"💬 Answer: {answer1[:100]}...")
            
        else:
            print(f"❌ Query 1 failed: {response1.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error in query 1: {e}")
        return
    
    # Wait a bit
    time.sleep(1)
    
    # Test case 2: Follow-up query
    print(f"\n🧪 Test 2: Follow-up query về giấy tờ")
    print("-" * 40)
    
    payload2 = {
        "query": "Tôi muốn biết là đăng ký kết hôn cần giấy tờ gì vậy",
        "session_id": session_id,
        "max_context_length": 8000,
        "use_ambiguous_detection": True,
        "use_full_document_expansion": True
    }
    
    try:
        response2 = requests.post(f"{api_base}/optimized-query", json=payload2)
        if response2.status_code == 200:
            result2 = response2.json()
            
            print(f"✅ Query 2 successful!")
            print(f"📋 Response Type: {result2.get('type', 'unknown')}")
            
            response_type = result2.get('type', 'unknown')
            
            if response_type == 'answer':
                answer2 = result2.get('answer', '')
                print(f"💬 Answer: {answer2[:200]}...")
                
                # Check if contains relevant info
                has_documents = any(word in answer2.lower() for word in 
                                  ['giấy tờ', 'hồ sơ', 'chứng minh', 'căn cước', 'hộ khẩu'])
                print(f"📄 Contains document info: {'✅ YES' if has_documents else '❌ NO'}")
                
                print(f"\n🎉 SUCCESS: Follow-up question được trả lời trực tiếp!")
                
            elif response_type == 'clarification_request':
                questions = result2.get('clarification_questions', [])
                print(f"🤔 Still requesting clarification ({len(questions)} questions):")
                for q in questions[:2]:
                    print(f"  • {q}")
                    
                print(f"\n❌ FAILED: Follow-up question vẫn bị chuyển sang clarification")
                
            else:
                print(f"❓ Unknown response type: {response_type}")
                
        else:
            print(f"❌ Query 2 failed: {response2.status_code}")
            print(response2.text)
            
    except Exception as e:
        print(f"❌ Error in query 2: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 FIX TEST COMPLETED!")

if __name__ == "__main__":
    test_followup_fix()
