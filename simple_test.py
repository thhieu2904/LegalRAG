import requests
import json

print("🚀 Testing Stateful Router Fix...")

# Test data
session_id = None  # Let backend auto-generate
base_url = "http://localhost:8000/api/v2/optimized-query"

# Query 1: Tạo context
print("\n📝 Query 1: Tạo context với đăng ký kết hôn")
query1 = "đăng ký kết hôn cần giấy tờ gì"

try:
    response1 = requests.post(base_url, json={
        "query": query1
        # No session_id - let backend create one
    }, timeout=30)
    
    if response1.status_code == 200:
        result1 = response1.json()
        session_id = result1.get('session_id')  # Get session ID from response
        print(f"✅ Response 1 OK - Session: {session_id}")
        print(f"   Response type: {result1.get('type')}")
        print(f"   Answer length: {len(result1.get('answer', ''))}")
        print(f"   Error: {result1.get('error')}")
        
        routing_info1 = result1.get('routing_info', {}) or {}
        print(f"   Routing info: {routing_info1}")
        print(f"   Confidence: {routing_info1.get('confidence', 0):.3f}")
        print(f"   Collection: {routing_info1.get('target_collection', 'Unknown')}")
        print(f"   Filters: {routing_info1.get('inferred_filters', {})}")
    else:
        print(f"❌ Query 1 failed: {response1.status_code}")
        print(response1.text)
        exit(1)

    # Query 2: Test stateful override
    print(f"\n📝 Query 2: Test stateful router với phí")
    query2 = "có tốn phí không"
    
    response2 = requests.post(base_url, json={
        "query": query2,
        "session_id": session_id
    }, timeout=30)
    
    if response2.status_code == 200:
        result2 = response2.json()
        routing_info2 = result2.get('routing_info', {}) or {}
        print(f"✅ Response 2 OK")
        print(f"   Full response keys: {list(result2.keys())}")
        print(f"   Confidence: {routing_info2.get('confidence', 0):.3f}")
        print(f"   Original confidence: {routing_info2.get('original_confidence', 0):.3f}")
        print(f"   Was overridden: {routing_info2.get('was_overridden', False)}")
        print(f"   Collection: {routing_info2.get('target_collection', 'Unknown')}")
        print(f"   Filters: {routing_info2.get('inferred_filters', {})}")
        
        # Check success
        was_overridden = routing_info2.get('was_overridden', False)
        has_filters = bool(routing_info2.get('inferred_filters', {}))
        same_collection = routing_info1.get('target_collection') == routing_info2.get('target_collection')
        
        print(f"\n🎯 RESULTS:")
        print(f"   Stateful Override: {'✅' if was_overridden else '❌'}")
        print(f"   Filters Applied: {'✅' if has_filters else '❌'}")
        print(f"   Same Collection: {'✅' if same_collection else '❌'}")
        
        if was_overridden and has_filters and same_collection:
            print(f"\n🎉 SUCCESS! Stateful Router với adaptive threshold hoạt động!")
        else:
            print(f"\n❌ PARTIAL SUCCESS - Some issues remain")
    else:
        print(f"❌ Query 2 failed: {response2.status_code}")
        print(response2.text)

except Exception as e:
    print(f"❌ Test failed with error: {e}")
