#!/usr/bin/env python3
"""
Test script để verify follow-up flow behavior
Kiểm tra xem tại sao query thứ 2 không được route trực tiếp mà lại show clarification
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_followup_flow():
    """Test the complete follow-up flow"""
    print("🧪 Testing Follow-up Flow...")
    print("=" * 60)
    
    # Query 1: High confidence query to establish session context
    print("\n1️⃣ QUERY 1: High confidence query (should establish session)")
    query1 = "Tôi cần biết về thủ tục đăng ký kết hôn"
    
    response1 = requests.post(f"{BASE_URL}/api/v1/query", json={
        "query": query1
    })
    
    print(f"Query: {query1}")
    print(f"Status: {response1.status_code}")
    
    if response1.status_code == 200:
        data1 = response1.json()
        session_id = data1.get("session_id")
        print(f"Session ID: {session_id}")
        print(f"Response type: {data1.get('type', 'N/A')}")
        
        if data1.get("type") == "answer":
            print("✅ Query 1: Got direct answer (high confidence)")
        elif data1.get("type") == "clarification":
            print("⚠️  Query 1: Got clarification (unexpected for high confidence)")
            print(f"Clarification action: {data1.get('clarification', {}).get('action')}")
        
        # Check session state
        session_response = requests.get(f"{BASE_URL}/api/v1/session/{session_id}")
        if session_response.status_code == 200:
            session_data = session_response.json()
            print(f"Session last_successful_collection: {session_data.get('last_successful_collection')}")
            print(f"Session confidence: {session_data.get('last_successful_confidence')}")
        
        # Query 2: Follow-up query (should use session context)
        print(f"\n2️⃣ QUERY 2: Follow-up query (should use session context)")
        query2 = "Tôi cũng muốn biết là có cần đóng phí gì không"
        
        response2 = requests.post(f"{BASE_URL}/api/v1/query", json={
            "query": query2,
            "session_id": session_id
        })
        
        print(f"Query: {query2}")
        print(f"Status: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Response type: {data2.get('type', 'N/A')}")
            
            if data2.get("type") == "answer":
                print("✅ Query 2: Got direct answer (session context used)")
            elif data2.get("type") == "clarification":
                print("❌ Query 2: Got clarification (session context NOT used)")
                clarification = data2.get('clarification', {})
                print(f"Clarification action: {clarification.get('action')}")
                print(f"Clarification confidence: {clarification.get('confidence')}")
                
        # Query 3: Another follow-up to test consistency  
        print(f"\n3️⃣ QUERY 3: Another follow-up (consistency test)")
        query3 = "phí là bao nhiêu"
        
        response3 = requests.post(f"{BASE_URL}/api/v1/query", json={
            "query": query3,
            "session_id": session_id
        })
        
        print(f"Query: {query3}")
        print(f"Status: {response3.status_code}")
        
        if response3.status_code == 200:
            data3 = response3.json()
            print(f"Response type: {data3.get('type', 'N/A')}")
            
            if data3.get("type") == "answer":
                print("✅ Query 3: Got direct answer (consistent behavior)")
            elif data3.get("type") == "clarification":
                print("❌ Query 3: Got clarification (inconsistent behavior)")
                
    else:
        print(f"❌ Query 1 failed: {response1.status_code}")
        
    print("\n" + "=" * 60)

def test_session_behavior():
    """Test session behavior specifically"""
    print("\n🔍 Testing Session Behavior...")
    print("=" * 60)
    
    # Create a direct session test
    query = "thủ tục đăng ký kết hôn"
    
    response = requests.post(f"{BASE_URL}/api/v1/query", json={
        "query": query
    })
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        
        # Check session immediately after creation
        session_response = requests.get(f"{BASE_URL}/api/v1/session/{session_id}")
        if session_response.status_code == 200:
            session_data = session_response.json()
            print(f"📊 Session Analysis:")
            print(f"  - Session ID: {session_id}")
            print(f"  - Last successful collection: {session_data.get('last_successful_collection')}")
            print(f"  - Last successful confidence: {session_data.get('last_successful_confidence')}")
            print(f"  - Last successful timestamp: {session_data.get('last_successful_timestamp')}")
            print(f"  - Consecutive low confidence: {session_data.get('consecutive_low_confidence_count')}")
            
            # Check if session context is properly established
            if session_data.get('last_successful_collection'):
                print("✅ Session context established")
            else:
                print("❌ Session context NOT established")

if __name__ == "__main__":
    try:
        print("🚀 LegalRAG Follow-up Flow Test")
        print("Testing follow-up query behavior...")
        
        # Test basic server connectivity
        health_response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            exit(1)
            
        # Run tests
        test_followup_flow()
        test_session_behavior()
        
        print("\n🎯 Test completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure backend is running on localhost:8000")
    except Exception as e:
        print(f"❌ Test failed: {e}")
