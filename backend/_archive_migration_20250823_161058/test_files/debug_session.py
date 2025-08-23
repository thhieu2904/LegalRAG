#!/usr/bin/env python3
"""
Simple debug test for session state
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_single_query():
    """Test single query to debug session update"""
    query = "thu tuc dang ky ket hon"
    
    print(f"🧪 Testing query: {query}")
    
    response = requests.post(f"{BASE_URL}/api/v1/query", json={
        "query": query
    })
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        print(f"Session ID: {session_id}")
        print(f"Response type: {data.get('type')}")
        
        # Check session state
        session_response = requests.get(f"{BASE_URL}/api/v1/session/{session_id}")
        if session_response.status_code == 200:
            session_data = session_response.json()
            print("\n📊 Session State:")
            print(f"  last_successful_collection: {session_data.get('last_successful_collection')}")
            print(f"  last_successful_confidence: {session_data.get('last_successful_confidence')}")
            print(f"  last_successful_timestamp: {session_data.get('last_successful_timestamp')}")
            
            if session_data.get('last_successful_collection'):
                print("✅ Session context established")
                return True
            else:
                print("❌ Session context NOT established")
                return False
    else:
        print(f"❌ Query failed: {response.status_code}")
        return False

if __name__ == "__main__":
    test_single_query()
