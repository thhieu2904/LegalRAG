#!/usr/bin/env python3
"""
Test exact follow-up scenario from log
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_exact_scenario():
    """Test exact scenario from logs"""
    
    print("🧪 Testing exact scenario from logs...")
    print("="*60)
    
    # Query 1: From log - this got high confidence (0.834)
    query1 = "Tôi cần biết về thủ tục đăng ký kết hôn"
    print(f"\n1️⃣ Query 1: {query1}")
    
    response1 = requests.post(f"{BASE_URL}/api/v1/query", json={
        "query": query1
    })
    
    if response1.status_code == 200:
        data1 = response1.json()
        session_id = data1.get("session_id")
        response_type1 = data1.get('type')
        
        print(f"Response type: {response_type1}")
        print(f"Session ID: {session_id}")
        
        if response_type1 == "answer":
            # Check session state immediately after high confidence query
            session_response = requests.get(f"{BASE_URL}/api/v1/session/{session_id}")
            if session_response.status_code == 200:
                session_data = session_response.json()
                collection = session_data.get('last_successful_collection')
                confidence = session_data.get('last_successful_confidence')
                
                print(f"Session collection: {collection}")
                print(f"Session confidence: {confidence}")
                
                if collection:
                    print("✅ Session context established")
                    
                    # Query 2: From log - this should use session context  
                    query2 = "Tôi cũng muốn biết là có cần đóng phí gì không"
                    print(f"\n2️⃣ Query 2: {query2}")
                    
                    response2 = requests.post(f"{BASE_URL}/api/v1/query", json={
                        "query": query2,
                        "session_id": session_id
                    })
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        response_type2 = data2.get('type')
                        
                        print(f"Response type: {response_type2}")
                        
                        if response_type2 == "answer":
                            print("✅ SUCCESS: Follow-up query routed directly")
                        else:
                            print("❌ FAIL: Follow-up query triggered clarification")
                            clarification = data2.get('clarification', {})
                            print(f"Clarification action: {clarification.get('action')}")
                            print(f"Clarification confidence: {clarification.get('confidence')}")
                else:
                    print("❌ Session context NOT established after high confidence query")
        else:
            print("❌ Query 1 did not get high confidence")
    else:
        print(f"❌ Query 1 failed: {response1.status_code}")

if __name__ == "__main__":
    test_exact_scenario()
