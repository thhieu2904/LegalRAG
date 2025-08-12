"""
Test API endpoints của VRAM-Optimized Server
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api_endpoint(endpoint, method="GET", data=None):
    """Test một API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        
        print(f"📡 {method} {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict):
                # Print key info only
                for key, value in list(result.items())[:5]:  # First 5 keys
                    if isinstance(value, str) and len(value) > 100:
                        print(f"   {key}: {value[:100]}...")
                    else:
                        print(f"   {key}: {value}")
            else:
                print(f"   Response: {result}")
        else:
            print(f"   Error: {response.text}")
        
        print()
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Connection error: {e}")
        return False

def main():
    print("🔥 Testing VRAM-Optimized LegalRAG API")
    print("="*50)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    # Test 1: Root endpoint
    print("🔍 Testing root endpoint...")
    test_api_endpoint("/")
    
    # Test 2: Health check
    print("🔍 Testing health check...")
    test_api_endpoint("/api/v1/health")
    
    # Test 3: Create session
    print("🔍 Testing session creation...")
    session_data = {"metadata": {"test": "api_test"}}
    success = test_api_endpoint("/api/v1/session/create", "POST", session_data)
    
    if success:
        # Test 4: Optimized query
        print("🔍 Testing optimized query...")
        query_data = {
            "query": "Thủ tục đăng ký kết hôn cần những giấy tờ gì?",
            "use_ambiguous_detection": True,
            "use_full_document_expansion": True
        }
        test_api_endpoint("/api/v1/optimized-query", "POST", query_data)
        
        # Test 5: Ambiguous query
        print("🔍 Testing ambiguous query...")
        ambiguous_data = {
            "query": "thủ tục như thế nào?",
            "use_ambiguous_detection": True
        }
        test_api_endpoint("/api/v1/optimized-query", "POST", ambiguous_data)
    
    # Test 6: Metrics
    print("🔍 Testing metrics...")
    test_api_endpoint("/api/v1/metrics")
    
    print("✅ API testing completed!")

if __name__ == "__main__":
    main()
