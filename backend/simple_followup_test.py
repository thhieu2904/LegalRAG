#!/usr/bin/env python3
"""
Simple test for follow-up detection
"""

import requests

BASE_URL = "http://localhost:8000"

# Step 1: High confidence query to establish session
print("Step 1: High confidence query")
response1 = requests.post(f"{BASE_URL}/api/v1/query", json={
    "query": "Tôi cần biết về thủ tục đăng ký kết hôn"
})

if response1.status_code == 200:
    data1 = response1.json()
    session_id = data1.get("session_id")
    print(f"Session ID: {session_id}")
    print(f"Response type: {data1.get('type')}")
    
    # Step 2: Follow-up query with same session
    print(f"\nStep 2: Follow-up query with session {session_id}")
    response2 = requests.post(f"{BASE_URL}/api/v1/query", json={
        "query": "có cần đóng phí không",
        "session_id": session_id
    })
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"Response type: {data2.get('type')}")
        
        if data2.get('type') == 'answer':
            print("✅ SUCCESS: Follow-up worked!")
        else:
            print("❌ FAIL: Follow-up triggered clarification")
            
print("\nCheck backend logs for debug info about session state")
