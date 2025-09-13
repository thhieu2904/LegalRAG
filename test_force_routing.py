#!/usr/bin/env python3
"""
Test Script: Force Debug Session Context
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_step_by_step():
    """Test từng bước và kiểm tra session metadata"""
    
    print("🧪 STEP-BY-STEP DEBUG")
    print("=" * 60)
    
    session_id = f"test-debug-{int(time.time())}"
    
    # Step 1: Initial query
    print("\n🔥 STEP 1: Initial Query")
    response1 = requests.post(f"{BASE_URL}/api/v1/query", json={
        "query": "hỏi để đăng ký kết hôn",
        "session_id": session_id
    })
    
    result1 = response1.json()
    print(f"📋 Type: {result1.get('type')}")
    print(f"📋 Session ID: {result1.get('session_id')}")
    
    # Step 2: Get session info before clarification
    print(f"\n🔥 STEP 2: Get Session Before Clarification")
    session_response = requests.get(f"{BASE_URL}/api/v1/session/{session_id}")
    if session_response.status_code == 200:
        session_data = session_response.json()
        print(f"📋 Session metadata before: {json.dumps(session_data.get('metadata', {}), indent=2)}")
    
    # Step 3: Send clarification
    print(f"\n🔥 STEP 3: Send Clarification")
    clarify_response = requests.post(f"{BASE_URL}/api/v1/clarify", json={
        "session_id": session_id,
        "selected_option": {
            "action": "manual_input",
            "collection": "quy_trinh_cap_ho_tich_cap_xa",
            "document": "DOC_011",
            "procedure": "Điều kiện để được đăng ký kết hôn là gì?"
        },
        "original_query": "hỏi để đăng ký kết hôn"
    })
    
    result3 = clarify_response.json()
    print(f"📋 Clarify Type: {result3.get('type')}")
    print(f"📋 Clarify Message: {result3.get('message', 'N/A')}")
    
    # Step 4: Get session info after clarification
    print(f"\n🔥 STEP 4: Get Session After Clarification")
    session_response2 = requests.get(f"{BASE_URL}/api/v1/session/{session_id}")
    if session_response2.status_code == 200:
        session_data2 = session_response2.json()
        print(f"📋 Session metadata after: {json.dumps(session_data2.get('metadata', {}), indent=2)}")
        
        # Check if routing_info was saved
        routing_info = session_data2.get('metadata', {}).get('routing_info', {})
        if routing_info:
            print(f"✅ ROUTING INFO SAVED: {json.dumps(routing_info, indent=2)}")
        else:
            print("❌ NO ROUTING INFO IN SESSION")
    
    # Step 5: Follow-up query
    print(f"\n🔥 STEP 5: Follow-up Query")
    followup_response = requests.post(f"{BASE_URL}/api/v1/query", json={
        "query": "phí là bao nhiêu khi làm thủ tục",
        "session_id": session_id
    })
    
    result5 = followup_response.json()
    print(f"📋 Follow-up Type: {result5.get('type')}")
    print(f"📋 Answer Length: {len(result5.get('answer', '')) if result5.get('answer') else 0}")
    print(f"📋 Processing Time: {result5.get('processing_time', 0):.3f}s")
    
    routing_info = result5.get('routing_info', {})
    if routing_info:
        print(f"📋 Routing: {json.dumps(routing_info, indent=2)}")
    
    context_info = result5.get('context_info', {})
    if context_info:
        print(f"📋 Context: {json.dumps(context_info, indent=2)}")

if __name__ == "__main__":
    test_step_by_step()