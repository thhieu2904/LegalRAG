"""
Test script để kiểm tra fix clarification service
- Kiểm tra medium confidence query có trigger clarification không
- Kiểm tra response có target_collection đúng không
- Kiểm tra frontend có thể hiển thị clarification UI không
"""

import requests
import json
import time

def test_clarification_service():
    """Test clarification service với medium confidence query"""
    
    # Test query để trigger MEDIUM_CONFIDENCE (0.50-0.64) cho multiple choice
    test_query = "thủ tục"  # Query cực kỳ mơ hồ để lower confidence
    
    url = "http://localhost:8000/api/v1/query"  # 🔧 Fix: Correct API endpoint
    payload = {
        "query": test_query,
        "session_id": f"test_clarification_fix_{int(time.time())}",  # 🔧 New session ID mỗi lần test
        "stream": False
    }
    
    print(f"🧪 Testing clarification fix...")
    print(f"📝 Query: {test_query}")
    print(f"🎯 Expected: Medium confidence → clarification needed")
    print("-" * 60)
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"⏱️ Response time: {end_time - start_time:.2f}s")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Pretty print toàn bộ response
            print("\n📋 FULL RESPONSE:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check key fields
            print("\n🔍 ANALYSIS:")
            print(f"Type: {data.get('type', 'N/A')}")
            print(f"Confidence: {data.get('confidence', 'N/A')}")
            print(f"Confidence Level: {data.get('confidence_level', 'N/A')}")
            print(f"Target Collection: {data.get('target_collection', 'N/A')}")
            
            # Check clarification structure
            clarification = data.get('clarification', {})
            if clarification:
                print(f"Clarification Message: {clarification.get('message', 'N/A')}")
                options = clarification.get('options', [])
                print(f"Number of Options: {len(options)}")
                
                for i, option in enumerate(options[:3], 1):  # Show first 3 options
                    print(f"  Option {i}: {option.get('title', 'N/A')}")
                    print(f"    Collection: {option.get('collection', 'N/A')}")
            
            # Check routing info
            routing_info = data.get('routing_info', {})
            if routing_info:
                print(f"Routing Info Target Collection: {routing_info.get('target_collection', 'N/A')}")
                print(f"Router Confidence: {routing_info.get('router_confidence', 'N/A')}")
            
            # Validate fix
            print("\n✅ VALIDATION:")
            
            # 1. Check if clarification is triggered
            is_clarification = data.get('type') == 'clarification_needed'
            print(f"1. Clarification triggered: {'✅' if is_clarification else '❌'}")
            
            # 2. Check if target_collection exists at top level OR in routing_info
            has_target_collection = (
                'target_collection' in data and data.get('target_collection') is not None
            ) or (
                routing_info.get('target_collection') is not None
            )
            print(f"2. Has target_collection: {'✅' if has_target_collection else '❌'}")
            
            # 3. Check expected collection (accept both top level and routing_info)
            target_collection = data.get('target_collection') or routing_info.get('target_collection')
            is_correct_collection = target_collection == 'quy_trinh_nuoi_con_nuoi'  # Updated expected collection
            print(f"3. Correct collection (nuoi_con_nuoi): {'✅' if is_correct_collection else '❌'} (got: {target_collection})")
            
            # 4. Check if clarification has options
            has_options = clarification.get('options') and len(clarification.get('options', [])) > 0
            print(f"4. Has clarification options: {'✅' if has_options else '❌'}")
            
            # Overall result
            all_passed = is_clarification and has_target_collection and is_correct_collection and has_options
            print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
            
            if all_passed:
                print("🎉 Clarification service fix is working correctly!")
                print("🔗 Frontend should now be able to display clarification UI properly")
            else:
                print("🔧 Some issues still need to be fixed")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("🔧 Make sure RAG service is running on localhost:8001")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        try:
            print(f"Raw response: {response.text}")
        except:
            print("Could not access response text")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_clarification_service()
