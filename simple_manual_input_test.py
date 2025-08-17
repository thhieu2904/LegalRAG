#!/usr/bin/env python3
"""
🔧 Simple Manual     # Test 1: Tạo session trước
    print("\n📝 Test 1: Tạo session")
    
    session_payload = {}
    try:
        session_response = requests.post(f"{base_url}/api/v2/session/create", json=session_payload)
        if session_response.status_code == 200:
            session_result = session_response.json()
            session_id = session_result.get("session_id", "simple_test_session")
            print(f"   ✅ Session created: {session_id}")
        else:
            print(f"   ⚠️  Session creation failed, using static ID")
            session_id = "simple_test_session"
    except Exception as e:
        print(f"   ⚠️  Using static session ID due to error: {e}")
        session_id = "simple_test_session"
    
    # Test 2: Gửi query để trigger clarification
    print(f"\n📝 Test 2: Query để trigger clarification")put Test
=============================

Test đơn giản để verify manual input fix

Author: LegalRAG Team
"""

import requests
import json

def simple_test():
    """Test đơn giản"""
    print("🔧 SIMPLE MANUAL INPUT TEST")
    print("=" * 50)
    
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
    
    # Test 1: Tạo session trước
    print("\n📝 Test 1: Tạo session")
    
    session_payload = {}
    try:
        session_response = requests.post(f"{base_url}/api/v2/session/create", json=session_payload)
        if session_response.status_code == 200:
            session_result = session_response.json()
            session_id = session_result.get("session_id", "simple_test_session")
            print(f"   ✅ Session created: {session_id}")
        else:
            print(f"   ⚠️  Session creation failed, using static ID")
            session_id = "simple_test_session"
    except Exception as e:
        print(f"   ⚠️  Using static session ID due to error: {e}")
        session_id = "simple_test_session"
    
    # Test 2: Gửi query để trigger clarification
    print("\n📝 Test 2: Query để trigger clarification")
    
    test_queries = [
        "làm giấy tờ gì",
        "thủ tục như thế nào", 
        "cần làm gì"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        
        payload = {
            "query": query,
            "session_id": session_id
        }
        
        try:
            # Test endpoint optimized-query
            response = requests.post(f"{base_url}/api/v2/optimized-query", json=payload)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                result_type = result.get("type", "unknown")
                print(f"   Type: {result_type}")
                
                if result_type == "clarification_needed":
                    print("   ✅ Got clarification - Perfect!")
                    
                    # Check for manual_input option
                    clarification = result.get("clarification", {})
                    options = clarification.get("options", [])
                    
                    manual_option = None
                    for option in options:
                        if option.get('action') == 'manual_input':
                            manual_option = option
                            break
                    
                    if manual_option:
                        print(f"   ✅ Found manual input option: {manual_option.get('title', 'Unknown')}")
                        
                        # Test 3: Send manual input response
                        print(f"\n📝 Test 3: Send manual input response")
                        clarify_payload = {
                            "session_id": session_id,
                            "selected_option": manual_option,
                            "original_query": query
                        }
                        
                        clarify_response = requests.post(f"{base_url}/api/v2/clarify", json=clarify_payload)
                        print(f"   Clarify Status: {clarify_response.status_code}")
                        
                        if clarify_response.status_code == 200:
                            clarify_result = clarify_response.json()
                            print(f"   Clarify Type: {clarify_result.get('type', 'unknown')}")
                            
                            session_cleared = clarify_result.get('session_cleared', False)
                            if session_cleared:
                                print("   🎉 SUCCESS: Session cleared!")
                                return True
                            else:
                                print("   ⚠️  Session NOT cleared")
                        else:
                            print(f"   ❌ Clarify failed: {clarify_response.status_code}")
                            # Print response for debugging
                            try:
                                print(f"   Response: {clarify_response.text[:200]}...")
                            except:
                                pass
                    else:
                        print("   ❌ No manual input option found")
                        
                elif result_type == "answer":
                    print("   ⚠️  Got direct answer (high confidence)")
                else:
                    print(f"   ❓ Other type: {result_type}")
            else:
                print(f"   ❌ Query failed: {response.status_code}")
                # Print response for debugging
                try:
                    print(f"   Response: {response.text[:200]}...")
                except:
                    pass
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    return False

if __name__ == "__main__":
    success = simple_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 MANUAL INPUT FIX: SUCCESS!")
    else:
        print("❌ MANUAL INPUT FIX: FAILED!")
    print("=" * 50)
