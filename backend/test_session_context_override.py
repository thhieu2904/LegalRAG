"""
Test script để verify session context override logic
"""

import requests
import json
import time

def test_session_context_override():
    """Test session context override với 2 câu hỏi liên tục"""
    
    print("🧪 TESTING SESSION CONTEXT OVERRIDE")
    print("="*50)
    
    base_url = "http://localhost:8000"
    session_id = f"test_session_override_{int(time.time())}"
    
    # Test sequence
    queries = [
        {
            "query": "đăng ký kết hôn cần giấy tờ gì",
            "expected": "High confidence, establish session context"
        },
        {
            "query": "mình có cần phải đóng phí gì hay không",
            "expected": "Session override should boost confidence"
        }
    ]
    
    for i, test in enumerate(queries, 1):
        print(f"\n{i}️⃣ Query {i}: {test['query']}")
        print(f"   Expected: {test['expected']}")
        
        try:
            payload = {
                "query": test['query'],
                "session_id": session_id,
                "use_session": True
            }
            
            response = requests.post(
                f"{base_url}/api/v1/query",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"   📄 Full response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
                
                # Extract routing info (handle None case)
                routing_info = result.get('routing_info') if result else None
                
                if routing_info:
                    confidence = routing_info.get('confidence', 0.0)
                    confidence_level = routing_info.get('confidence_level', 'unknown')
                    target_collection = routing_info.get('target_collection', 'None')
                    was_overridden = routing_info.get('was_overridden', False)
                    original_confidence = routing_info.get('original_confidence')
                    
                    print(f"   📊 Confidence: {confidence:.3f} ({confidence_level})")
                    print(f"   🎯 Collection: {target_collection}")
                    
                    if was_overridden:
                        print(f"   🔥 SESSION OVERRIDE: {original_confidence:.3f} → {confidence:.3f}")
                        print(f"   ✅ Override logic working!")
                    else:
                        print(f"   📋 No override applied")
                else:
                    print(f"   ⚠️  No routing_info in response")
                    confidence = 0.0
                    was_overridden = False
                
                # Check response type
                response_type = result.get('type', 'unknown')
                if response_type == 'answer':
                    print(f"   ✅ Got direct answer (good confidence)")
                elif response_type == 'clarification':
                    print(f"   ❌ Got clarification (low confidence)")
                    clarification = result.get('clarification', {})
                    action = clarification.get('action', 'unknown')
                    print(f"      Clarification action: {action}")
                
                # For second query, check if session context was used
                if i == 2:
                    if was_overridden:
                        print(f"   🎉 SUCCESS: Session context override working!")
                    else:
                        print(f"   ❌ FAILURE: Session context not used")
                
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Wait between queries
        if i < len(queries):
            time.sleep(1)
    
    print("\n" + "="*50)
    print("🎯 SESSION CONTEXT TEST SUMMARY")
    print("="*50)
    print("Expected behavior:")
    print("1. First query: High confidence → Save session context")
    print("2. Second query: Low confidence → Override with session confidence")
    print("3. Result: Both queries should get direct answers, no clarification")

if __name__ == "__main__":
    test_session_context_override()
