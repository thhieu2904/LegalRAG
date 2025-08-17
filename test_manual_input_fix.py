#!/usr/bin/env python3
"""
🔧 PHASE 1: Test Manual Input Fix
=================================

Test scenario: User chọn "Tôi muốn hỏi câu khác" → Session state được clear

Author: LegalRAG Team
"""

import requests
import json

def test_manual_input_fix():
    """Test manual input fix với scenario thực tế"""
    
    print("🔧 TESTING MANUAL INPUT FIX - PHASE 1")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    session_id = "test_manual_input_session"
    
    # === STEP 1: Query ban đầu về hộ tịch ===
    print("\n📝 STEP 1: Query ban đầu về hộ tịch")
    query1 = "làm giấy khai sinh"
    
    payload1 = {
        "query": query1,
        "session_id": session_id
    }
    
    response1 = requests.post(f"{base_url}/api/v2/optimized-query", json=payload1)
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"✅ Query 1 successful: {result1.get('type')}")
        
        if result1.get("type") == "clarification_needed":
            print("🤔 Got clarification request")
            clarification = result1.get("clarification", {})
            options = clarification.get("options", [])
            
            # Tìm option "manual_input"
            manual_input_option = None
            for option in options:
                if option.get('action') == 'manual_input':
                    manual_input_option = option
                    break
            
            if manual_input_option:
                print(f"✅ Found manual input option: {manual_input_option['title']}")
                
                # === STEP 2: User chọn "Tôi muốn hỏi câu khác" ===
                print(f"\n📝 STEP 2: User chọn '{manual_input_option['title']}'")
                
                payload2 = {
                    "session_id": session_id,
                    "selected_option": manual_input_option,
                    "original_query": query1
                }
                
                response2 = requests.post(f"{base_url}/api/v1/clarify", json=payload2)
                
                if response2.status_code == 200:
                    result2 = response2.json()
                    print(f"✅ Clarification response: {result2.get('type')}")
                    
                    # Check if session was cleared
                    session_cleared = result2.get('session_cleared', False)
                    if session_cleared:
                        print("✅ EXCELLENT: Session state was cleared!")
                    else:
                        print("❌ WARNING: Session state NOT cleared")
                    
                    # === STEP 3: Query mới về chứng thực ===
                    print(f"\n📝 STEP 3: Query mới về chủ đề khác (chứng thực)")
                    query3 = "chứng thực hợp đồng mua bán"
                    
                    payload3 = {
                        "query": query3,
                        "session_id": session_id
                    }
                    
                    response3 = requests.post(f"{base_url}/api/v2/optimized-query", json=payload3)
                    
                    if response3.status_code == 200:
                        result3 = response3.json()
                        print(f"✅ Query 3 successful: {result3.get('type')}")
                        
                        # Analyze routing
                        routing_info = result3.get('routing_info', {})
                        target_collection = routing_info.get('target_collection')
                        was_overridden = routing_info.get('was_overridden', False)
                        
                        print(f"Target collection: {target_collection}")
                        print(f"Was overridden: {was_overridden}")
                        
                        # SUCCESS CHECK
                        if target_collection and 'chung_thuc' in target_collection and not was_overridden:
                            print("🎉 SUCCESS: User có thể hỏi chủ đề mới!")
                            print("✅ Session state đã được clear thành công")
                            return True
                        else:
                            print("❌ FAIL: Hệ thống vẫn nhớ collection cũ")
                            print(f"   Expected: chung_thuc collection")
                            print(f"   Got: {target_collection}")
                            print(f"   Overridden: {was_overridden}")
                            return False
                    else:
                        print(f"❌ Query 3 failed: {response3.status_code}")
                        return False
                else:
                    print(f"❌ Clarification failed: {response2.status_code}")
                    return False
            else:
                print("❌ No manual input option found")
                return False
        elif result1.get("type") == "answer":
            print("⚠️  Got direct answer (high confidence). Testing với query khác...")
            # Try với query mơ hồ hơn
            return test_with_ambiguous_query()
        else:
            print(f"❌ Unexpected result type: {result1.get('type')}")
            return False
    else:
        print(f"❌ Query 1 failed: {response1.status_code}")
        return False

def test_with_ambiguous_query():
    """Test với query mơ hồ để trigger clarification"""
    print("\n🔧 TESTING WITH AMBIGUOUS QUERY")
    print("-" * 40)
    
    base_url = "http://localhost:8000"
    session_id = "test_ambiguous_session"
    
    ambiguous_queries = [
        "làm giấy tờ",
        "thủ tục gì",
        "cần làm gì"
    ]
    
    for query in ambiguous_queries:
        print(f"\n📝 Testing: {query}")
        
        payload = {
            "query": query,
            "session_id": session_id
        }
        
        response = requests.post(f"{base_url}/api/v2/optimized-query", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("type") == "clarification_needed":
                print(f"✅ Got clarification for: {query}")
                return test_manual_input_scenario(result, query, session_id)
        
    print("❌ Không tìm được query nào trigger clarification")
    return False

def test_manual_input_scenario(clarification_result, original_query, session_id):
    """Test manual input scenario từ clarification result"""
    
    clarification = clarification_result.get("clarification", {})
    options = clarification.get("options", [])
    
    # Tìm manual input option
    manual_input_option = None
    for option in options:
        if option.get('action') == 'manual_input':
            manual_input_option = option
            break
    
    if not manual_input_option:
        print("❌ Không tìm thấy manual input option")
        return False
    
    print(f"✅ Found manual input option: {manual_input_option.get('title')}")
    
    # Test clarification response
    base_url = "http://localhost:8000"
    
    payload = {
        "session_id": session_id,
        "selected_option": manual_input_option,
        "original_query": original_query
    }
    
    response = requests.post(f"{base_url}/api/v1/clarify", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        session_cleared = result.get('session_cleared', False)
        
        if session_cleared:
            print("🎉 SUCCESS: Manual input fix hoạt động!")
            return True
        else:
            print("❌ Session không được clear")
            return False
    else:
        print(f"❌ Clarification failed: {response.status_code}")
        return False

def check_server():
    """Check if server is running"""
    try:
        response = requests.get("http://localhost:8000/docs")
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🔧 PHASE 1: MANUAL INPUT FIX TEST")
    print("=" * 60)
    
    # Check server
    if not check_server():
        print("❌ Server không chạy. Hãy start backend server:")
        print("   cd backend && python -m uvicorn main:app --reload")
        exit(1)
    
    # Run test
    success = test_manual_input_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 PHASE 1 FIX: THÀNH CÔNG!")
        print("✅ User có thể chọn 'Tôi muốn hỏi câu khác' và hỏi chủ đề mới")
    else:
        print("❌ PHASE 1 FIX: THẤT BẠI!")
        print("🔧 Cần debug thêm...")
    print("=" * 60)
