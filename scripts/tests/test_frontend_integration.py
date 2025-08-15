#!/usr/bin/env python3
"""
🔧 MANUAL TEST CLARIFICATION ENDPOINT
Test trực tiếp endpoint clarification để verify backend logic
"""

import requests
import json

def test_clarification_endpoint():
    """
    Test clarification endpoint với exact format frontend cần gửi
    """
    print("🔧 TESTING CLARIFICATION ENDPOINT DIRECTLY")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Step 1: Get initial clarification
    print("\n1️⃣ Getting initial clarification...")
    query_payload = {
        "query": "mình tính hỏi dụ đăng ký",
        "session_id": None
    }
    
    response = requests.post(f"{base_url}/api/v2/optimized-query", json=query_payload)
    result = response.json()
    
    if result.get("type") != "clarification_needed":
        print("❌ No clarification received")
        return False
    
    session_id = result.get("session_id")
    options = result.get("clarification", {}).get("options", [])
    
    print(f"✅ Initial clarification received")
    print(f"   Session ID: {session_id}")
    print(f"   Options: {len(options)}")
    
    # Find the first collection option
    collection_option = None
    for opt in options:
        if opt.get("action") == "proceed_with_collection":
            collection_option = opt
            break
    
    if not collection_option:
        print("❌ No collection option found")
        return False
    
    print(f"   Selected option: {collection_option.get('title')}")
    
    # Step 2: Send CORRECT clarification request
    print(f"\n2️⃣ Sending CORRECT clarification request...")
    
    # 🔥 CORRECT FORMAT - Frontend should send this:
    clarification_payload = {
        "session_id": session_id,
        "original_query": "mình tính hỏi dụ đăng ký",  # ORIGINAL query
        "selected_option": collection_option  # FULL option object
    }
    
    print(f"📤 Sending payload:")
    print(json.dumps(clarification_payload, indent=2, ensure_ascii=False))
    
    response = requests.post(f"{base_url}/api/v2/clarify", json=clarification_payload)
    
    if response.status_code != 200:
        print(f"❌ Clarification failed: {response.status_code}")
        print(response.text)
        return False
    
    result = response.json()
    
    print(f"\n📥 Response received:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Check if we got question suggestions
    if result.get("type") != "clarification_needed":
        print(f"❌ Expected clarification_needed (question suggestions), got: {result.get('type')}")
        return False
    
    clarification = result.get("clarification", {})
    if clarification.get("style") != "question_suggestion":
        print(f"❌ Expected question_suggestion style, got: {clarification.get('style')}")
        return False
    
    print(f"\n✅ SUCCESS! Question suggestions received:")
    print(f"   Style: {clarification.get('style')}")
    print(f"   Stage: {clarification.get('stage')}")
    print(f"   Questions: {len(clarification.get('options', []))}")
    
    return True

def test_wrong_frontend_format():
    """
    Test what happens if frontend sends wrong format (like current issue)
    """
    print("\n🚨 TESTING WRONG FRONTEND FORMAT")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Simulate what frontend is currently doing wrong
    print("\n❌ Testing wrong format (text instead of API call)...")
    
    wrong_query = {
        "query": "Đã chọn: Hộ tịch cấp xã",  # This is what frontend is currently sending
        "session_id": None
    }
    
    response = requests.post(f"{base_url}/api/v2/optimized-query", json=wrong_query)
    result = response.json()
    
    print(f"📥 Wrong format result:")
    print(f"   Type: {result.get('type')}")
    print(f"   Style: {result.get('clarification', {}).get('style')}")
    
    if result.get("type") == "clarification_needed":
        print(f"❌ CONFIRMED: Wrong format triggers new clarification cycle!")
        print(f"   This is exactly the bug you're experiencing!")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 TESTING CLARIFICATION FRONTEND INTEGRATION")
    print("Server should be running on localhost:8000")
    print()
    
    # Test correct format
    success = test_clarification_endpoint()
    
    # Test wrong format to confirm the issue
    test_wrong_frontend_format()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ BACKEND WORKING CORRECTLY!")
        print("❌ FRONTEND NEEDS TO BE FIXED!")
        print()
        print("Frontend should:")
        print("1. NOT send text like 'Đã chọn: Hộ tịch cấp xã' as new query")
        print("2. Instead, send POST request to /api/v2/clarify")
        print("3. With payload: {session_id, original_query, selected_option}")
        print("4. selected_option should be full option object from clarification response")
    else:
        print("\n❌ BACKEND ISSUE FOUND")
