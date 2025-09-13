#!/usr/bin/env python3

import requests
import json

def test_forced_routing_via_api():
    print("🧪 TESTING FORCED ROUTING VIA API")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    session_id = "test-api-forced-1757788046"
    
    # Step 1: Create session with routing info
    session_data = {
        "session_id": session_id,
        "metadata": {
            "routing_info": {
                "force_collection": "quy_trinh_cap_ho_tich_cap_xa",
                "force_document": "DOC_001"
            }
        }
    }
    
    print("🔥 STEP 1: Creating session with forced routing info")
    create_response = requests.post(f"{base_url}/api/v1/session/create", json=session_data)
    print(f"✅ Session creation status: {create_response.status_code}")
    
    # Step 2: Send query with forced routing
    query_data = {
        "query": "Những điều kiện gì để đăng ký khai sinh?",
        "session_id": session_id,
        "force_collection": "quy_trinh_cap_ho_tich_cap_xa",
        "force_document": "DOC_001"
    }
    
    print("\n🔥 STEP 2: Sending query with forced routing")
    response = requests.post(f"{base_url}/api/v1/query", json=query_data)
    
    print(f"✅ Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n🎯 Result type: {result.get('type')}")
        print(f"📝 Answer length: {len(result.get('answer', '')) if result.get('answer') else 0}")
        print(f"⏱️ Time: {result.get('processing_time', 0):.3f}s")
        
        if result.get('routing_info'):
            print(f"🚀 Routing: {json.dumps(result['routing_info'], indent=2)}")
        else:
            print("⚠️ No routing_info in result")
            
        if result.get('context_info'):
            print(f"📄 Context: {json.dumps(result['context_info'], indent=2)}")
        else:
            print("⚠️ No context_info in result")
            
        print(f"\n🔍 FULL RESPONSE:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_forced_routing_via_api()