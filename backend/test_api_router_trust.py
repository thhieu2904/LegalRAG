"""
Test script để call API và verify router trust fix
"""

import requests
import json
import time

def test_api_router_trust():
    """Test API endpoint với marriage query"""
    
    print("🌐 TESTING API ROUTER TRUST FIX")
    print("="*50)
    
    # API endpoint
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/v1/query"
    
    # Test query
    query = "đăng ký kết hôn cần giấy tờ gì"
    
    payload = {
        "query": query,
        "session_id": "test_router_trust",
        "use_session": False
    }
    
    print(f"📝 Test Query: {query}")
    print(f"🌐 API Endpoint: {endpoint}")
    print()
    
    try:
        # Make API call
        print("🚀 Making API call...")
        start_time = time.time()
        
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️  Processing Time: {processing_time:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Analyze response
            print("✅ API CALL SUCCESS")
            print()
            print("📄 RESPONSE ANALYSIS:")
            
            # Check for router confidence info
            if 'router_confidence' in result:
                router_confidence = result['router_confidence']
                print(f"   🎯 Router Confidence: {router_confidence:.4f}")
                
                if router_confidence > 0.85:
                    print(f"   ✅ High confidence detected: {router_confidence:.4f} > 0.85")
                    print(f"   🎯 Router trust mode should be active")
                else:
                    print(f"   📊 Normal confidence: {router_confidence:.4f} <= 0.85")
            
            # Check document source
            if 'document_path' in result:
                doc_path = result['document_path']
                print(f"   📄 Document Path: {doc_path}")
                
                # Extract document ID
                import re
                match = re.search(r'DOC_(\d+)', doc_path)
                if match:
                    doc_id = f"DOC_{match.group(1)}"
                    print(f"   🆔 Document ID: {doc_id}")
                    
                    # Check if correct document
                    if doc_id == "DOC_011":
                        print(f"   🎉 SUCCESS: Correct document (normal marriage registration)")
                    elif doc_id == "DOC_031":
                        print(f"   ❌ WRONG: Got mobile marriage registration instead")
                    else:
                        print(f"   ⚠️  UNEXPECTED: Got different document {doc_id}")
            
            # Show answer preview
            if 'answer' in result:
                answer = result['answer']
                answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"   💬 Answer Preview: {answer_preview}")
            
            print()
            print("🔍 FULL RESPONSE:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ API CALL FAILED")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Server not running!")
        print("🔧 Please start server with: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("="*50)

def check_server_status():
    """Check if server is running"""
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print(f"⚠️  Server returned status {response.status_code}")
            return False
    except:
        print("❌ Server is not running!")
        return False

if __name__ == "__main__":
    print("🔍 CHECKING SERVER STATUS...")
    if check_server_status():
        print()
        test_api_router_trust()
    else:
        print()
        print("🔧 TO START SERVER:")
        print("conda activate LegalRAG_v1")
        print("cd D:\\Personal\\LegalRAG_Fixed\\backend")
        print("python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000")
