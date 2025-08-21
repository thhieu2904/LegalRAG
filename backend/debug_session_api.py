#!/usr/bin/env python3
"""
Debug session API response
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def debug_session_api():
    """Debug session API response"""
    
    # Create a session with high confidence query
    query = "Tôi cần biết về thủ tục đăng ký kết hôn"
    
    response = requests.post(f"{BASE_URL}/api/v1/query", json={
        "query": query
    })
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        
        print(f"Query response type: {data.get('type')}")
        print(f"Session ID: {session_id}")
        
        # Get session info
        session_response = requests.get(f"{BASE_URL}/api/v1/session/{session_id}")
        print(f"\nSession API status: {session_response.status_code}")
        
        if session_response.status_code == 200:
            session_data = session_response.json()
            print(f"Raw session response: {json.dumps(session_data, indent=2)}")
        else:
            print(f"Session API error: {session_response.text}")
            
        # Try with follow-up using same session
        print(f"\n🧪 Follow-up query with session {session_id}")
        followup_query = "có cần đóng phí không"
        
        followup_response = requests.post(f"{BASE_URL}/api/v1/query", json={
            "query": followup_query,
            "session_id": session_id
        })
        
        if followup_response.status_code == 200:
            followup_data = followup_response.json()
            print(f"Follow-up response type: {followup_data.get('type')}")
            
            if followup_data.get('type') == 'answer':
                print("✅ SUCCESS: Follow-up routed directly!")
            else:
                print("❌ FAIL: Follow-up triggered clarification")
        else:
            print(f"Follow-up failed: {followup_response.status_code}")

if __name__ == "__main__":
    debug_session_api()
