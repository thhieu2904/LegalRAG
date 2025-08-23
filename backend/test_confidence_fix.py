#!/usr/bin/env python3
"""
Test confidence level fix
"""

import requests
import json

def test_confidence_fix():
    print("🧪 Testing Confidence Level Fix...")
    print("=" * 50)
    
    # Test query với expected high confidence  
    test_query = "làm giấy khai sinh cần gì"
    
    print(f"🔍 Query: {test_query}")
    
    payload = {
        "query": test_query,
        "session_id": "test_confidence_fix"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/v1/query", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Status: {response.status_code}")
            print(f"🎯 Response Type: {result.get('response_type', 'unknown')}")
            print(f"📊 Router Confidence: {result.get('debug_info', {}).get('router_confidence', 'N/A')}")
            print(f"🔍 Confidence Level: {result.get('debug_info', {}).get('confidence_level', 'N/A')}")
            
            # Check if it routes directly instead of clarification
            if result.get('response_type') == 'auto_route':
                print("✅ SUCCESS: Direct routing (no clarification needed)")
                print(f"📍 Target Collection: {result.get('debug_info', {}).get('target_collection', 'N/A')}")
            elif result.get('response_type') == 'clarification':
                print("❌ STILL CLARIFYING: Should route directly with 0.825+ confidence")
                print(f"💬 Message: {result.get('message', 'N/A')}")
            
            print("\n" + "=" * 50)
            print("📋 Full Response Info:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request Error: {e}")

if __name__ == "__main__":
    test_confidence_fix()
