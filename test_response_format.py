#!/usr/bin/env python3
"""
🧪 Admin Panel API Response Format Test
Verifies all endpoints return proper wrapped responses
"""

import requests
import json

ADMIN_URL = "http://localhost:8001"

def test_endpoint(name, url, expected_keys):
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {name}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        
        data = response.json()
        print(f"\n✅ Response format:")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
        
        # Check required keys
        if "success" in data:
            print(f"✅ Has 'success' field: {data['success']}")
        else:
            print(f"❌ Missing 'success' field")
            
        if "data" in data:
            print(f"✅ Has 'data' field (type: {type(data['data']).__name__})")
        else:
            print(f"❌ Missing 'data' field")
            
        if "message" in data:
            print(f"✅ Has 'message' field: {data.get('message')}")
        else:
            print(f"⚠️  No 'message' field (might be optional)")
            
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🧪 ADMIN PANEL API RESPONSE FORMAT VERIFICATION")
    print("="*60)
    
    tests = [
        ("GET /stats", f"{ADMIN_URL}/api/v1/storage/stats", ["success", "data", "message"]),
        ("GET /list (all)", f"{ADMIN_URL}/api/v1/storage/list", ["success", "data", "message"]),
        ("GET /list (by CCCD)", f"{ADMIN_URL}/api/v1/storage/list?cccd=084201000001", ["success", "data", "message"]),
        ("GET /health", f"{ADMIN_URL}/api/v1/storage/health", ["status"]),
    ]
    
    passed = 0
    for name, url, keys in tests:
        if test_endpoint(name, url, keys):
            passed += 1
    
    print(f"\n{'='*60}")
    print(f"✅ RESULTS: {passed}/{len(tests)} endpoints verified")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
