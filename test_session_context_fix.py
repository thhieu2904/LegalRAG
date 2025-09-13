#!/usr/bin/env python3
"""
Test Script: Session Context Preservation Fix
==============================================

Test the exact sequence from the log to verify session context preservation works.

Sequence:
1. Query: "hỏi để đăng ký kết hôn" → Should trigger clarification
2. Clarification: Choose manual_input → Should preserve context
3. Query: "phí là bao nhiêu khi làm thủ tục" → Should route to preserved collection
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_session_context_preservation():
    """Test session context preservation for manual input clarification"""
    
    print("🧪 SESSION CONTEXT PRESERVATION - TEST")
    print("=" * 60)
    
    # Step 1: Initial query that triggers clarification
    print("\n🔥 STEP 1: Initial Query (should trigger clarification)")
    query1_data = {
        "query": "hỏi để đăng ký kết hôn",
        "session_id": f"test-session-{int(time.time())}"
    }
    
    response1 = requests.post(f"{BASE_URL}/api/v1/query", json=query1_data)
    print(f"✅ Status: {response1.status_code}")
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"📋 Response type: {result1.get('type')}")
        
        if result1.get("type") == "clarification_needed":
            print("✅ Clarification triggered as expected")
            session_id = result1.get("session_id")
            
            # Step 2: Choose manual input option
            print("\n🔥 STEP 2: Choose manual input option")
            clarify_data = {
                "session_id": session_id,
                "selected_option": {
                    "action": "manual_input",
                    "collection": "quy_trinh_cap_ho_tich_cap_xa",
                    "document": "DOC_011",
                    "procedure": "Điều kiện để được đăng ký kết hôn là gì?"
                },
                "original_query": "hỏi để đăng ký kết hôn"
            }
            
            response2 = requests.post(f"{BASE_URL}/api/v1/clarify", json=clarify_data)
            print(f"✅ Status: {response2.status_code}")
            
            if response2.status_code == 200:
                result2 = response2.json()
                print(f"📋 Clarification result type: {result2.get('type')}")
                
                # Step 3: Follow-up query (should preserve context)
                print("\n🔥 STEP 3: Follow-up query (should preserve collection context)")
                query3_data = {
                    "query": "phí là bao nhiêu khi làm thủ tục",
                    "session_id": session_id
                }
                
                response3 = requests.post(f"{BASE_URL}/api/v1/query", json=query3_data)
                print(f"✅ Status: {response3.status_code}")
                
                if response3.status_code == 200:
                    result3 = response3.json()
                    print(f"📋 Response type: {result3.get('type')}")
                    
                    # Check routing info
                    routing_info = result3.get("routing_info", {})
                    if routing_info:
                        target_collection = routing_info.get("target_collection")
                        
                        print(f"🎯 Target Collection: {target_collection}")
                        print(f"🎯 Expected: quy_trinh_cap_ho_tich_cap_xa")
                        
                        if target_collection == "quy_trinh_cap_ho_tich_cap_xa":
                            print("✅ SUCCESS: Session context preserved!")
                        else:
                            print(f"❌ FAILED: Session context not preserved")
                            print(f"   Expected: quy_trinh_cap_ho_tich_cap_xa")
                            print(f"   Got: {target_collection}")
                    else:
                        print("⚠️  No routing_info in response")
                        
                    # Check context info for source details
                    context_info = result3.get("context_info", {})
                    if context_info:
                        source_collections = context_info.get("source_collections", [])
                        source_documents = context_info.get("source_documents", [])
                        
                        print(f"📋 Source Collections: {source_collections}")
                        print(f"📋 Source Documents: {len(source_documents)} documents")
                        
                        # Check if preserved collection is used
                        if "quy_trinh_cap_ho_tich_cap_xa" in source_collections:
                            print("✅ CONTEXT: Preserved collection found in source_collections")
                        else:
                            print(f"❌ CONTEXT: Preserved collection not found. Collections: {source_collections}")
                    
                    # Check answer content
                    answer = result3.get("answer", "")
                    message = result3.get("message", "")
                    
                    if answer:
                        print(f"📝 Answer preview: {answer[:100]}...")
                        if "kết hôn" in answer.lower() or "hôn nhân" in answer.lower():
                            print("✅ ANSWER CONTEXT: Correctly about marriage")
                        elif "khai sinh" in answer.lower():
                            print("❌ ANSWER CONTEXT: Still about birth registration (failed)")
                        else:
                            print("⚠️  ANSWER CONTEXT: Unknown topic")
                    elif message:
                        print(f"📝 Message: {message}")
                    
                    # Print full response for debugging
                    print("\n🔍 FULL RESPONSE:")
                    print(json.dumps(result3, indent=2, ensure_ascii=False))
                        
                else:
                    print(f"❌ API Error: {response3.status_code}")
                    print(f"Response: {response3.text}")
                    
            else:
                print(f"❌ Clarification Error: {response2.status_code}")
                print(f"Response: {response2.text}")
        else:
            print(f"❌ Expected clarification, got: {result1.get('type')}")
    else:
        print(f"❌ API Error: {response1.status_code}")
        print(f"Response: {response1.text}")

if __name__ == "__main__":
    test_session_context_preservation()