#!/usr/bin/env python3
"""
Debug response format to understand the API response structure
"""

import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

def debug_response_format():
    print("🔍 DEBUGGING API RESPONSE FORMAT")
    print("=" * 50)
    
    session_id = str(uuid.uuid4())
    
    payload = {
        "query": "Đăng ký kết hôn cần giấy tờ gì?",
        "session_id": session_id,
        "max_context_length": 8000,
        "use_ambiguous_detection": True,
        "use_full_document_expansion": True
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v2/optimized-query", json=payload)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Raw Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            print(f"📄 Full Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    debug_response_format()
