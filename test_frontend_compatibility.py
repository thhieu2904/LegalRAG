#!/usr/bin/env python3
"""
Test Frontend Compatibility for 3-Step Clarification Flow
Verify that backend response format matches frontend expectations
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def test_frontend_compatibility():
    """Test that all clarification responses have correct type for frontend"""
    print("🧪 Frontend Compatibility Test for 3-Step Flow")
    print("=" * 60)
    
    session_id = None
    
    try:
        # Step 1: Initial ambiguous query
        print("\n📝 Step 1: Send ambiguous query")
        response1 = requests.post(
            f"{BASE_URL}/api/v2/optimized-query",
            json={"query": "tôi muốn đăng ký"},
            headers=HEADERS,
            timeout=30
        )
        
        if response1.status_code != 200:
            print(f"❌ Step 1 failed: {response1.status_code}")
            return False
            
        data1 = response1.json()
        session_id = data1.get("session_id")
        
        print(f"✅ Response type: {data1.get('type')}")
        print(f"✅ Session ID: {session_id}")
        
        # Verify frontend compatibility
        if data1.get("type") != "clarification_needed":
            print(f"❌ FRONTEND INCOMPATIBLE: Expected 'clarification_needed', got '{data1.get('type')}'")
            return False
            
        if not data1.get("clarification", {}).get("options"):
            print("❌ FRONTEND INCOMPATIBLE: No clarification options found")
            return False
            
        options1 = data1["clarification"]["options"]
        print(f"✅ Found {len(options1)} collection options")
        print(f"   First option: {options1[0]['title']}")
        
        # Step 2: Select collection (simulate frontend behavior)
        print("\n📂 Step 2: Select collection")
        selected_option = options1[0]  # Select first collection
        
        response2 = requests.post(
            f"{BASE_URL}/api/v2/clarify",
            json={
                "session_id": session_id,
                "original_query": "tôi muốn đăng ký",
                "selected_option": selected_option
            },
            headers=HEADERS,
            timeout=30
        )
        
        if response2.status_code != 200:
            print(f"❌ Step 2 failed: {response2.status_code}")
            return False
            
        data2 = response2.json()
        print(f"✅ Response type: {data2.get('type')}")
        
        # Verify frontend compatibility for step 2
        if data2.get("type") != "clarification_needed":
            print(f"❌ FRONTEND INCOMPATIBLE: Expected 'clarification_needed', got '{data2.get('type')}'")
            return False
            
        if not data2.get("clarification", {}).get("options"):
            print("❌ FRONTEND INCOMPATIBLE: No document options found")
            return False
            
        options2 = data2["clarification"]["options"]
        print(f"✅ Found {len(options2)} document options")
        print(f"   First document: {options2[0]['title']}")
        
        # Verify document selection works
        doc_options = [opt for opt in options2 if opt.get("action") == "proceed_with_document"]
        manual_option = [opt for opt in options2 if opt.get("action") == "manual_input"]
        
        print(f"✅ Document options: {len(doc_options)}")
        print(f"✅ Manual input option: {'YES' if manual_option else 'NO'}")
        
        if not doc_options:
            print("❌ FRONTEND INCOMPATIBLE: No document selection options found")
            return False
            
        # Step 3: Select document
        print("\n📄 Step 3: Select document")
        selected_doc = doc_options[0]  # Select first document
        
        response3 = requests.post(
            f"{BASE_URL}/api/v2/clarify",
            json={
                "session_id": session_id,
                "original_query": "tôi muốn đăng ký",
                "selected_option": selected_doc
            },
            headers=HEADERS,
            timeout=30
        )
        
        if response3.status_code != 200:
            print(f"❌ Step 3 failed: {response3.status_code}")
            return False
            
        data3 = response3.json()
        print(f"✅ Response type: {data3.get('type')}")
        
        # Verify frontend compatibility for step 3
        if data3.get("type") != "clarification_needed":
            print(f"❌ FRONTEND INCOMPATIBLE: Expected 'clarification_needed', got '{data3.get('type')}'")
            return False
            
        if not data3.get("clarification", {}).get("options"):
            print("❌ FRONTEND INCOMPATIBLE: No question options found")
            return False
            
        options3 = data3["clarification"]["options"]
        print(f"✅ Found {len(options3)} question options")
        
        # Verify question selection works
        question_options = [opt for opt in options3 if opt.get("action") == "answer_question"]
        manual_option3 = [opt for opt in options3 if opt.get("action") == "manual_input"]
        
        print(f"✅ Question options: {len(question_options)}")
        print(f"✅ Manual input option: {'YES' if manual_option3 else 'NO'}")
        
        if not question_options and not manual_option3:
            print("❌ FRONTEND INCOMPATIBLE: No question or manual input options found")
            return False
            
        print("\n🎯 FRONTEND COMPATIBILITY CHECK")
        print("=" * 40)
        print("✅ All response types are 'clarification_needed'")
        print("✅ All responses have clarification.options structure")
        print("✅ Document selection step works")
        print("✅ Question selection step works")
        print("✅ Manual input options available")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_response_structure():
    """Test detailed response structure for frontend compatibility"""
    print("\n🔍 Detailed Response Structure Test")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/optimized-query",
            json={"query": "tôi muốn đăng ký"},
            headers=HEADERS,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            return False
            
        data = response.json()
        
        # Check required fields for frontend
        required_fields = ["type", "clarification", "session_id", "processing_time"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
            
        print("✅ All required top-level fields present")
        
        # Check clarification structure
        clarification = data.get("clarification", {})
        clarification_fields = ["message", "options", "style"]
        missing_clarification = [field for field in clarification_fields if field not in clarification]
        
        if missing_clarification:
            print(f"❌ Missing clarification fields: {missing_clarification}")
            return False
            
        print("✅ All required clarification fields present")
        
        # Check option structure
        options = clarification.get("options", [])
        if not options:
            print("❌ No options in clarification")
            return False
            
        option = options[0]
        option_fields = ["id", "title", "description", "action"]
        missing_option = [field for field in option_fields if field not in option]
        
        if missing_option:
            print(f"❌ Missing option fields: {missing_option}")
            return False
            
        print("✅ All required option fields present")
        print(f"✅ Sample option structure:")
        print(f"   ID: {option.get('id')}")
        print(f"   Title: {option.get('title')}")
        print(f"   Action: {option.get('action')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Frontend Compatibility Tests")
    print("=" * 60)
    
    # Test 1: Response structure
    structure_ok = test_response_structure()
    
    # Test 2: Full 3-step flow
    flow_ok = test_frontend_compatibility()
    
    print("\n📊 FINAL RESULTS")
    print("=" * 30)
    print(f"Response Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"3-Step Flow: {'✅ PASS' if flow_ok else '❌ FAIL'}")
    
    if structure_ok and flow_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("Frontend should now display document selection correctly")
    else:
        print("\n💥 SOME TESTS FAILED!")
        print("Check the error messages above")
