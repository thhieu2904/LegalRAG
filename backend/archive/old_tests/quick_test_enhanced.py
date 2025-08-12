"""
Quick test script cho Enhanced RAG với câu hỏi cụ thể của user
"""

import requests
import json

def test_ambiguous_query():
    """Test câu hỏi mơ hồ của user"""
    print("🧪 Testing ambiguous query: 'mình muốn làm thủ tục nhận nuôi con thì cần làm gì?'")
    
    url = "http://localhost:8000/api/v1/query"
    payload = {
        "question": "mình muốn làm thủ tục nhận nuôi con thì cần làm gì?",
        "max_tokens": 1024,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            
            # Check if clarification is working
            if "Câu hỏi của bạn cần được làm rõ thêm" in answer:
                print("✅ CLARIFICATION WORKING!")
                print(f"Clarification message: {answer}")
            else:
                print("❌ NO CLARIFICATION - Direct answer provided")
                print(f"Answer: {answer[:200]}...")
                print(f"Sources: {len(result.get('sources', []))} files")
                
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_enhanced_query():
    """Test enhanced query endpoint"""
    print("\n🧪 Testing enhanced query endpoint:")
    
    url = "http://localhost:8000/api/v1/enhanced-query"
    payload = {
        "question": "mình muốn làm thủ tục nhận nuôi con thì cần làm gì?",
        "enable_clarification": True,
        "enable_context_synthesis": True,
        "clarification_threshold": "low",
        "max_tokens": 1024,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_type = result.get("type", "unknown")
            
            print(f"Response type: {response_type}")
            print(f"Processing steps: {result.get('preprocessing_steps', [])}")
            
            if response_type == "clarification_request":
                print("✅ ENHANCED CLARIFICATION WORKING!")
                questions = result.get('clarification_questions', [])
                print(f"Clarification questions ({len(questions)}):")
                for i, q in enumerate(questions, 1):
                    print(f"  {i}. {q}")
            else:
                print("❌ NO CLARIFICATION - Direct answer")
                print(f"Answer: {result.get('answer', '')[:200]}...")
                
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_clear_query():
    """Test với câu hỏi rõ ràng"""
    print("\n🧪 Testing clear query:")
    
    url = "http://localhost:8000/api/v1/enhanced-query"
    payload = {
        "question": "Công dân Việt Nam đã kết hôn muốn nhận nuôi con trong nước cần thủ tục gì?",
        "enable_clarification": True,
        "max_tokens": 1024,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_type = result.get("type", "unknown")
            
            print(f"Response type: {response_type}")
            print(f"Processing steps: {result.get('preprocessing_steps', [])}")
            
            if response_type == "answer":
                print("✅ CLEAR QUERY - Direct answer provided")
                print(f"Answer: {result.get('answer', '')[:300]}...")
                
                context_strategy = result.get('context_strategy', {})
                print(f"Context strategy: {context_strategy.get('strategy_used', 'unknown')}")
                print(f"Files used: {context_strategy.get('files_included', 0)}")
                print(f"Chunks used: {context_strategy.get('chunks_included', 0)}")
            else:
                print("❌ Unexpected response type")
                
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("="*60)
    print("🚀 ENHANCED RAG QUICK TEST")
    print("="*60)
    
    # Test 1: Legacy endpoint với câu hỏi mơ hồ
    test_ambiguous_query()
    
    # Test 2: Enhanced endpoint với câu hỏi mơ hồ
    test_enhanced_query()
    
    # Test 3: Enhanced endpoint với câu hỏi rõ ràng
    test_clear_query()
    
    print("\n" + "="*60)
    print("🏁 Test completed!")
    print("="*60)
