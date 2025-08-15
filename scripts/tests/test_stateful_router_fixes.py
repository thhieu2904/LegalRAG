"""
Test script để kiểm tra các sửa đổi Stateful Router
Ba vấn đề chính đã được sửa:
1. Logic ghi đè ngữ cảnh trong OptimizedChatSession
2. Ngưỡng tin cậy cao và lưu ngữ cảnh hội thoại 
3. Filter bị "đánh rơi" trong vector search

Test case: Đăng ký khai sinh + có tốn phí không?
"""

import requests
import json
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

def test_stateful_router_fixes():
    """Test các sửa đổi Stateful Router với câu hỏi liên tiếp"""
    
    print("🔥 TESTING STATEFUL ROUTER FIXES")
    print("="*60)
    
    # Test session
    session_id = f"test_stateful_{int(time.time())}"
    # http://localhost:8000/api/v2/optimized-query
    # Câu hỏi đầu tiên - Tạo ngữ cảnh
    print("\n📝 Test 1: Câu hỏi tạo ngữ cảnh")
    query1 = "Thủ tục đăng ký khai sinh cần giấy tờ gì?"

    response1 = requests.post(f"{BASE_URL}/api/v2/optimized-query", json={
        "query": query1,
        "session_id": session_id
    })
    
    print(f"Query 1: {query1}")
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"✅ Response 1: {result1.get('answer', '')[:200]}...")
        routing_info1 = result1.get('routing_info', {})
        print(f"📊 Routing confidence: {routing_info1.get('confidence', 0):.3f}")
        print(f"📊 Collection: {routing_info1.get('target_collection', 'Unknown')}")
        print(f"📊 Filters: {routing_info1.get('inferred_filters', {})}")
    else:
        print(f"❌ Error 1: {response1.status_code}")
        return
    
    # Chờ 2 giây
    print("\n⏱️ Chờ 2 giây...")
    time.sleep(2)
    
    # Câu hỏi thứ hai - Test Stateful Router
    print("\n📝 Test 2: Câu hỏi follow-up (test stateful router)")
    query2 = "có tốn phí không?"

    response2 = requests.post(f"{BASE_URL}/optimized-query", json={
        "query": query2,
        "session_id": session_id
    })
    
    print(f"Query 2: {query2}")
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"✅ Response 2: {result2.get('answer', '')[:200]}...")
        routing_info2 = result2.get('routing_info', {})
        print(f"📊 Routing confidence: {routing_info2.get('confidence', 0):.3f}")
        print(f"📊 Original confidence: {routing_info2.get('original_confidence', 0):.3f}")
        print(f"📊 Was overridden: {routing_info2.get('was_overridden', False)}")
        print(f"📊 Collection: {routing_info2.get('target_collection', 'Unknown')}")
        print(f"📊 Filters: {routing_info2.get('inferred_filters', {})}")
        
        # Kiểm tra các cải thiện
        was_overridden = routing_info2.get('was_overridden', False)
        has_filters = bool(routing_info2.get('inferred_filters', {}))
        confidence = routing_info2.get('confidence', 0)
        
        print(f"\n🔍 ANALYSIS:")
        print(f"   - Stateful Override Working: {'✅' if was_overridden else '❌'}")
        print(f"   - Filters Applied: {'✅' if has_filters else '❌'}")
        print(f"   - Good Confidence: {'✅' if confidence >= 0.7 else '❌'}")
        
        if was_overridden:
            print(f"   🔥 STATEFUL ROUTER SUCCESS: Đã ghi đè từ {routing_info2.get('original_confidence', 0):.3f} -> {confidence:.3f}")
        
        if has_filters:
            print(f"   🎯 FILTERS SUCCESS: {routing_info2.get('inferred_filters', {})}")
        
    else:
        print(f"❌ Error 2: {response2.status_code}")
        return
    
    # Test câu hỏi thứ ba - Test threshold mới
    print("\n📝 Test 3: Câu hỏi khác để test threshold mới")
    query3 = "Thủ tục chứng thực chữ ký như thế nào?"

    response3 = requests.post(f"{BASE_URL}/optimized-query", json={
        "query": query3,
        "session_id": session_id
    })
    
    print(f"Query 3: {query3}")
    if response3.status_code == 200:
        result3 = response3.json()
        routing_info3 = result3.get('routing_info', {})
        print(f"📊 Routing confidence: {routing_info3.get('confidence', 0):.3f}")
        print(f"📊 Collection: {routing_info3.get('target_collection', 'Unknown')}")
        
        # Kiểm tra ngưỡng mới (0.80 thay vì 0.85)
        confidence = routing_info3.get('confidence', 0)
        if confidence >= 0.80:
            print(f"   ✅ HIGH CONFIDENCE với ngưỡng mới (0.80): {confidence:.3f}")
        elif confidence >= 0.50:
            print(f"   ⚠️ MEDIUM CONFIDENCE: {confidence:.3f}")
        else:
            print(f"   ❌ LOW CONFIDENCE: {confidence:.3f}")
    else:
        print(f"❌ Error 3: {response3.status_code}")
    
    print(f"\n🎯 TEST COMPLETED - Session: {session_id}")

def test_specific_override_logic():
    """Test cụ thể logic override mới"""
    print("\n\n🔥 TESTING SPECIFIC OVERRIDE LOGIC")
    print("="*60)
    
    # Simulate các trường hợp khác nhau
    test_cases = [
        {
            "name": "Case 1: High context, medium current -> Should override",
            "last_confidence": 0.82,
            "current_confidence": 0.74,
            "expected_override": True
        },
        {
            "name": "Case 2: High context, very high current -> Should NOT override", 
            "last_confidence": 0.85,
            "current_confidence": 0.83,
            "expected_override": False
        },
        {
            "name": "Case 3: Medium context, low current -> Should NOT override",
            "last_confidence": 0.76,
            "current_confidence": 0.60,
            "expected_override": False
        },
        {
            "name": "Case 4: Good context, medium current -> Should override",
            "last_confidence": 0.79,
            "current_confidence": 0.70,
            "expected_override": True
        }
    ]
    
    for case in test_cases:
        print(f"\n📊 {case['name']}")
        print(f"   Last confidence: {case['last_confidence']}")
        print(f"   Current confidence: {case['current_confidence']}")
        print(f"   Expected override: {case['expected_override']}")
        
        # Logic mới được implement
        VERY_HIGH_CONFIDENCE_GATE = 0.82
        MIN_CONTEXT_CONFIDENCE = 0.78
        
        should_override = (
            case['current_confidence'] < VERY_HIGH_CONFIDENCE_GATE and 
            case['last_confidence'] >= MIN_CONTEXT_CONFIDENCE
        )
        
        result = "✅ CORRECT" if should_override == case['expected_override'] else "❌ WRONG"
        print(f"   Actual override: {should_override} {result}")

if __name__ == "__main__":
    print("🚀 Starting Stateful Router Fix Tests...")
    
    # Test logic trước
    test_specific_override_logic()
    
    # Test thực tế với backend
    try:
        test_stateful_router_fixes()
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        print("💡 Make sure backend is running on localhost:8000")
