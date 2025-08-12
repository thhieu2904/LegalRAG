#!/usr/bin/env python3
"""
Test script cho VRAM-Optimized LegalRAG API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_ambiguous_query():
    """Test hệ thống phát hiện câu hỏi mơ hồ"""
    print("=== TEST 1: AMBIGUOUS QUERY DETECTION ===")
    
    response = requests.post(f'{BASE_URL}/api/v2/optimized-query', 
        json={'query': 'thủ tục như thế nào'})
    result = response.json()
    
    print(f"Type: {result.get('type')}")
    if result.get('type') == 'clarification_needed':
        print(f"Category: {result.get('category')}")  
        print(f"Confidence: {result.get('confidence'):.3f}")
        print("Clarification template:", result.get('clarification', {}).get('template'))
        print("Options:")
        for opt in result.get('clarification', {}).get('options', []):
            print(f"  - {opt}")
        
        print("\nGenerated questions:")
        for q in result.get('generated_questions', []):
            print(f"  - {q}")
    
    print()

def test_clear_query():
    """Test câu hỏi rõ ràng"""
    print("=== TEST 2: CLEAR QUERY PROCESSING ===")
    
    response = requests.post(f'{BASE_URL}/api/v2/optimized-query',
        json={'query': 'thủ tục đăng ký kết hôn cần giấy tờ gì'})
    result = response.json()
    
    print(f"Type: {result.get('type')}")
    if result.get('type') == 'answer':
        print(f"Processing time: {result.get('processing_time', 0):.2f}s")
        context_info = result.get('context_info', {})
        print(f"Nucleus chunks: {context_info.get('nucleus_chunks')}")
        print(f"Context length: {context_info.get('context_length')}")
        print(f"Source collections: {context_info.get('source_collections')}")
        print(f"Source documents: {len(context_info.get('source_documents', []))}")
        print("Answer:")
        print(result.get('answer', '')[:200] + "...")
    
    print()

def test_session_management():
    """Test session management"""
    print("=== TEST 3: SESSION MANAGEMENT ===")
    
    # Tạo session mới
    response = requests.post(f'{BASE_URL}/api/v2/session/create', json={})
    
    if response.status_code == 200:
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"Created session: {session_id}")
        
        # Query với session
        response = requests.post(f'{BASE_URL}/api/v2/optimized-query',
            json={
                'query': 'hồ sơ kết hôn cần những gì', 
                'session_id': session_id
            })
        result = response.json()
        
        print(f"Session query result type: {result.get('type')}")
        print(f"Processing time: {result.get('processing_time', 0):.2f}s")
        
        # Lấy thông tin session
        response = requests.get(f'{BASE_URL}/api/v2/session/{session_id}')
        if response.status_code == 200:
            session_info = response.json()
            print(f"Session history: {len(session_info.get('query_history', []))} queries")
        else:
            print(f"Failed to get session info: {response.status_code}")
    else:
        print(f"Failed to create session: {response.status_code} - {response.text}")
    
    print()

def get_health_status():
    """Lấy trạng thái hệ thống"""
    print("=== SYSTEM HEALTH STATUS ===")
    
    response = requests.get(f'{BASE_URL}/api/v2/health')
    health = response.json()
    
    print(f"Status: {health.get('status')}")
    print(f"Collections: {health.get('total_collections')}")
    print(f"Documents: {health.get('total_documents')}")
    print(f"Device allocation:")
    print(f"  - Embedding: {health.get('embedding_device')}")
    print(f"  - LLM: {health.get('llm_device')}")
    print(f"  - Reranker: {health.get('reranker_device')}")
    
    metrics = health.get('metrics', {})
    print(f"Metrics:")
    print(f"  - Total queries: {metrics.get('total_queries', 0)}")
    print(f"  - Ambiguous detected: {metrics.get('ambiguous_detected', 0)}")
    print(f"  - Context expansions: {metrics.get('context_expansions', 0)}")
    print(f"  - Avg response time: {metrics.get('avg_response_time', 0):.3f}s")
    
    print()

if __name__ == "__main__":
    print("🔥 VRAM-Optimized LegalRAG API Test Suite")
    print("=" * 50)
    
    try:
        # Kiểm tra server có chạy không
        requests.get(BASE_URL, timeout=5)
        
        # Chạy các test
        get_health_status()
        test_ambiguous_query() 
        test_clear_query()
        test_session_management()
        
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start the server first:")
        print("python optimized_main.py")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
