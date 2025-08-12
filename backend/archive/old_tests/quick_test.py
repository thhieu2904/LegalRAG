#!/usr/bin/env python3
"""
Quick test script for LegalRAG API
Test các endpoint cơ bản của API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test cơ bản các API endpoints"""
    print("🧪 Testing LegalRAG API...")
    
    # Test health
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check: OK")
        else:
            print("❌ Health check: FAILED")
            return
    except requests.exceptions.RequestException:
        print("❌ Server not running on http://localhost:8000")
        return
    
    # Test detailed health
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Detailed health: {result['status']}")
            print(f"   Model loaded: {result['model_loaded']}")
            print(f"   VectorDB: {result['vectordb_status']}")
        else:
            print("❌ Detailed health: FAILED")
    except requests.exceptions.RequestException as e:
        print(f"❌ Detailed health: {e}")
    
    # Test query
    test_question = "Thủ tục đăng ký khai sinh cần giấy tờ gì?"
    print(f"\n❓ Testing query: {test_question}")
    
    try:
        payload = {
            "question": test_question,
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_k": 3
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/v1/query", json=payload, timeout=60)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Query successful!")
            print(f"   Response time: {end_time - start_time:.2f}s")
            print(f"   Answer length: {len(result['answer'])} chars")
            print(f"   Sources found: {len(result['sources'])}")
            print(f"   Processing time: {result['processing_time']:.2f}s")
            print(f"   Answer preview: {result['answer'][:200]}...")
        else:
            print(f"❌ Query failed: {response.status_code}")
            print(response.text[:200])
    except requests.exceptions.RequestException as e:
        print(f"❌ Query error: {e}")
    
    print("\n🎯 Test completed!")
    print("📚 API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    test_api()
