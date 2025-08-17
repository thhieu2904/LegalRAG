#!/usr/bin/env python3
"""
🔧 Test Context Preservation Fix
=================================

Test scenario: Manual input với context preservation thay vì clear session

Test Cases:
- Case 1: Query mơ hồ → Chọn collection → Manual input → Verify collection preserved
- Case 2: Query mơ hồ → Không chọn collection → Manual input → Verify session cleared (fallback)

Author: LegalRAG Team
"""

import requests
import json

def test_context_preservation():
    """Test context preservation trong manual input"""
    
    print("🔧 TESTING CONTEXT PRESERVATION FIX")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test server connection
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code != 200:
            print("❌ Server không chạy")
            return False
        print("✅ Server đang chạy")
    except Exception as e:
        print(f"❌ Không thể kết nối server: {e}")
        return False
    
    # ===== TEST CASE 1: Context Preservation =====
    print(f"\n{'='*60}")
    print("🧪 TEST CASE 1: CONTEXT PRESERVATION")
    print("Query mơ hồ → Chọn collection → Manual input → Verify preservation")
    print("="*60)
    
    # Step 1: Tạo session
    print("\n📝 Step 1: Tạo session")
    session_payload = {}
    try:
        session_response = requests.post(f"{base_url}/api/v2/session/create", json=session_payload)
        if session_response.status_code == 200:
            session_result = session_response.json()
            session_id = session_result.get("session_id", "test_session_1")
            print(f"   ✅ Session created: {session_id}")
        else:
            session_id = "test_session_1"
            print(f"   ⚠️  Using fallback session ID")
    except Exception as e:
        session_id = "test_session_1"
        print(f"   ⚠️  Using fallback session ID: {e}")
    
    # Step 2: Query mơ hồ để trigger clarification
    print(f"\n📝 Step 2: Query mơ hồ để trigger clarification")
    query1 = "tôi muốn hỏi về thủ tục đăng ký"
    
    payload1 = {
        "query": query1,
        "session_id": session_id
    }
    
    response1 = requests.post(f"{base_url}/api/v2/optimized-query", json=payload1)
    print(f"   Query: '{query1}'")
    print(f"   Status: {response1.status_code}")
    
    if response1.status_code != 200:
        print(f"   ❌ Query 1 failed: {response1.status_code}")
        print(f"   Response: {response1.text[:200]}...")
        return False
    
    result1 = response1.json()
    if result1.get("type") != "clarification_needed":
        print(f"   ❌ Expected clarification, got: {result1.get('type')}")
        return False
    
    print(f"   ✅ Got clarification with {len(result1.get('clarification', {}).get('options', []))} options")
    
    # Step 3: Chọn collection (ho_tich_cap_xa)
    print(f"\n📝 Step 3: User chọn collection ho_tich_cap_xa")
    
    clarification = result1.get("clarification", {})
    options = clarification.get("options", [])
    
    # Tìm option cho ho_tich_cap_xa
    ho_tich_option = None
    for option in options:
        if option.get('collection') == 'ho_tich_cap_xa':
            ho_tich_option = option
            break
    
    if not ho_tich_option:
        print("   ❌ Không tìm thấy option cho ho_tich_cap_xa")
        return False
    
    print(f"   ✅ Found option: {ho_tich_option.get('title', 'Unknown')}")
    
    # Send clarification với collection selection
    clarify_payload1 = {
        "session_id": session_id,
        "selected_option": ho_tich_option,
        "original_query": query1
    }
    
    clarify_response1 = requests.post(f"{base_url}/api/v2/clarify", json=clarify_payload1)
    print(f"   Collection selection status: {clarify_response1.status_code}")
    
    if clarify_response1.status_code != 200:
        print(f"   ❌ Collection selection failed: {clarify_response1.status_code}")
        return False
    
    clarify_result1 = clarify_response1.json()
    generated_questions = clarify_result1.get('generated_questions', [])
    if generated_questions:
        print(f"   ✅ Got {len(generated_questions)} suggested questions")
    else:
        print(f"   ✅ Collection selection successful (type: {clarify_result1.get('type', 'unknown')})")
    
    # Step 4: Manual input (với collection context)
    print(f"\n📝 Step 4: User chọn manual input (context should be preserved)")
    
    # Tìm manual input option từ clarification hoặc tạo synthetic
    manual_input_option = {
        "id": "manual",
        "title": "Tôi muốn mô tả rõ hơn",
        "action": "manual_input",
        "collection": "ho_tich_cap_xa"  # 🔧 KEY: Collection context
    }
    
    manual_payload = {
        "session_id": session_id,
        "selected_option": manual_input_option,
        "original_query": query1
    }
    
    manual_response = requests.post(f"{base_url}/api/v2/clarify", json=manual_payload)
    print(f"   Manual input status: {manual_response.status_code}")
    
    if manual_response.status_code != 200:
        print(f"   ❌ Manual input failed: {manual_response.status_code}")
        print(f"   Response: {manual_response.text[:200]}...")
        return False
    
    manual_result = manual_response.json()
    context_preserved = manual_result.get('context_preserved', False)
    preserved_collection = manual_result.get('preserved_collection')
    
    print(f"   Context preserved: {context_preserved}")
    print(f"   Preserved collection: {preserved_collection}")
    
    if not context_preserved or preserved_collection != "ho_tich_cap_xa":
        print("   ❌ Context preservation FAILED!")
        return False
    
    print("   ✅ Context preservation SUCCESS!")
    
    # Step 5: Next query để verify context được sử dụng
    print(f"\n📝 Step 5: Next query để verify context override")
    query2 = "kết hôn có tốn phí không"
    
    payload2 = {
        "query": query2,
        "session_id": session_id
    }
    
    response2 = requests.post(f"{base_url}/api/v2/optimized-query", json=payload2)
    print(f"   Query: '{query2}'")
    print(f"   Status: {response2.status_code}")
    
    if response2.status_code != 200:
        print(f"   ❌ Query 2 failed: {response2.status_code}")
        return False
    
    result2 = response2.json()
    routing_info = result2.get('routing_info', {})
    target_collection = routing_info.get('target_collection')
    was_overridden = routing_info.get('was_overridden', False)
    
    print(f"   Target collection: {target_collection}")
    print(f"   Was overridden: {was_overridden}")
    
    if target_collection == "ho_tich_cap_xa" and was_overridden:
        print("   ✅ EXCELLENT: Context override worked! Session preserved collection.")
        return True
    elif target_collection == "ho_tich_cap_xa":
        print("   ✅ GOOD: Routed to correct collection (may be natural match)")
        return True
    else:
        print(f"   ⚠️  Routed to different collection: {target_collection}")
        return False

def test_fallback_clear():
    """Test fallback clear khi không có collection context"""
    
    print(f"\n{'='*60}")
    print("🧪 TEST CASE 2: FALLBACK CLEAR (No Collection Context)")
    print("Query mơ hồ → Manual input ngay → Verify session cleared")
    print("="*60)
    
    base_url = "http://localhost:8000"
    
    # Step 1: Tạo session
    print("\n📝 Step 1: Tạo session")
    session_id = "test_session_2"
    
    # Step 2: Manual input không có collection context
    print(f"\n📝 Step 2: Manual input without collection context")
    
    manual_input_option = {
        "id": "manual",
        "title": "Tôi muốn mô tả rõ hơn",
        "action": "manual_input",
        "collection": None  # 🔧 KEY: No collection context
    }
    
    manual_payload = {
        "session_id": session_id,
        "selected_option": manual_input_option,
        "original_query": "câu hỏi mơ hồ"
    }
    
    manual_response = requests.post(f"{base_url}/api/v2/clarify", json=manual_payload)
    print(f"   Manual input status: {manual_response.status_code}")
    
    if manual_response.status_code != 200:
        print(f"   ❌ Manual input failed: {manual_response.status_code}")
        return False
    
    manual_result = manual_response.json()
    context_preserved = manual_result.get('context_preserved', True)  # Default True để test False
    
    print(f"   Context preserved: {context_preserved}")
    
    if context_preserved:
        print("   ❌ Fallback clear FAILED! Context should be cleared.")
        return False
    
    print("   ✅ Fallback clear SUCCESS!")
    return True

if __name__ == "__main__":
    print("🔧 CONTEXT PRESERVATION TEST SUITE")
    print("=" * 60)
    
    # Test Case 1: Context Preservation
    success1 = test_context_preservation()
    
    # Test Case 2: Fallback Clear  
    success2 = test_fallback_clear()
    
    print("\n" + "=" * 60)
    print("🏆 FINAL RESULTS:")
    print(f"   Case 1 (Context Preservation): {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"   Case 2 (Fallback Clear): {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED! Context preservation fix hoạt động hoàn hảo!")
    else:
        print("\n❌ SOME TESTS FAILED! Cần debug thêm...")
    print("=" * 60)
