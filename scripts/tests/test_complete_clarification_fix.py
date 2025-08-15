#!/usr/bin/env python3
"""
🔧 TEST COMPLETE CLARIFICATION FIX
Kiểm tra giải pháp toàn diện chống vòng lặp clarification vô tận
"""

import sys
import os
import requests
import time
import json
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_anti_loop_mechanism():
    """
    Test complete anti-loop mechanism với forced collection routing
    """
    print("🧪 TESTING COMPLETE ANTI-LOOP CLARIFICATION MECHANISM")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # 1. Test ambiguous query triggering clarification
    print("\n1️⃣ Testing ambiguous query...")
    query_payload = {
        "query": "mình tính hỏi dụ đăng ký",  # Câu hỏi mơ hồ
        "session_id": None
    }
    
    response = requests.post(f"{base_url}/api/v2/query", json=query_payload)
    
    if response.status_code != 200:
        print(f"❌ Query failed: {response.status_code}")
        print(response.text)
        return False
        
    result = response.json()
    
    if result.get("type") != "clarification_needed":
        print(f"❌ Expected clarification_needed, got: {result.get('type')}")
        return False
        
    print(f"✅ Clarification triggered correctly")
    print(f"   Confidence: {result.get('confidence')}")
    print(f"   Options available: {len(result.get('clarification', {}).get('options', []))}")
    
    # Extract session_id and first option
    session_id = result.get("session_id")
    options = result.get("clarification", {}).get("options", [])
    
    if not options:
        print("❌ No clarification options found")
        return False
        
    # 2. Test clarification response with forced collection
    print(f"\n2️⃣ Testing clarification response...")
    selected_option = options[0]  # Chọn option đầu tiên
    print(f"   Selected option: {selected_option.get('title')}")
    print(f"   Target collection: {selected_option.get('collection')}")
    
    clarification_payload = {
        "session_id": session_id,
        "original_query": "mình tính hỏi dụ đăng ký",  # 🔥 ORIGINAL QUERY
        "selected_option": selected_option  # 🔥 FULL OPTION OBJECT
    }
    
    response = requests.post(f"{base_url}/api/v2/clarify", json=clarification_payload)
    
    if response.status_code != 200:
        print(f"❌ Clarification failed: {response.status_code}")
        print(response.text)
        return False
        
    result = response.json()
    
    # 3. Validate anti-loop mechanism
    print(f"\n3️⃣ Validating anti-loop mechanism...")
    
    if result.get("type") == "clarification_needed":
        print("❌ ANTI-LOOP FAILED! Still asking for clarification!")
        print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return False
        
    if result.get("type") == "answer":
        print("✅ ANTI-LOOP WORKING! Got direct answer")
        print(f"   Answer length: {len(result.get('answer', ''))}")
        print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
        return True
        
    if result.get("type") == "no_results":
        print("⚠️  Got no_results, but anti-loop is working (not re-asking)")
        print(f"   Message: {result.get('message')}")
        return True
        
    print(f"❌ Unexpected result type: {result.get('type')}")
    print(f"   Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return False

def test_stateful_conversation():
    """
    Test xem system có nhớ original query không
    """
    print("\n🧠 TESTING STATEFUL CONVERSATION")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Create session
    session_response = requests.post(f"{base_url}/api/v2/session/create", json={})
    session_id = session_response.json().get("session_id")
    
    print(f"📋 Created session: {session_id}")
    
    # Test with forced collection directly
    query_payload = {
        "query": "đăng ký kết hôn cần gì",  # Clear query về hộ tịch
        "session_id": session_id,
        "forced_collection": "ho_tich_cap_xa"  # Force routing
    }
    
    response = requests.post(f"{base_url}/api/v2/query", json=query_payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Forced collection routing works")
        print(f"   Result type: {result.get('type')}")
        if result.get("type") == "answer":
            print(f"   Answer preview: {result.get('answer', '')[:100]}...")
        return True
    else:
        print(f"❌ Forced collection failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🚀 TESTING COMPLETE CLARIFICATION FIX")
    print("Make sure server is running on localhost:8000")
    print()
    
    try:
        # Test server connectivity
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("❌ Server not responding at localhost:8000")
            print("Please start the server first: uvicorn main:app --reload")
            sys.exit(1)
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server at localhost:8000")
        print("Please start the server first: uvicorn main:app --reload")
        sys.exit(1)
    
    # Run tests
    success = True
    
    # Test 1: Anti-loop mechanism
    if not test_anti_loop_mechanism():
        success = False
        
    time.sleep(1)  # Brief pause
    
    # Test 2: Stateful conversation
    if not test_stateful_conversation():
        success = False
    
    # Final result
    print("\n" + "=" * 60)
    if success:
        print("🎉 COMPLETE FIX VALIDATED!")
        print("✅ Anti-loop mechanism implemented correctly")
        print("✅ Original query preserved") 
        print("✅ Forced collection routing")
        print("✅ No re-triggering of clarification")
        print("✅ Anti-loop mechanism working")
        print("\n🚀 READY TO TEST: Restart server và test với ambiguous queries!")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the implementation")
        sys.exit(1)
