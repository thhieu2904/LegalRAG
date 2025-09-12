#!/usr/bin/env python3
"""
Test script để verify clarification fixes
"""

import requests
import json
import time

def test_clarification_api():
    """Test clarification API endpoint"""
    base_url = "http://localhost:8000"
    
    # Test data - simulate a manual input action
    test_request = {
        "session_id": "test_session_123",
        "selected_option": {
            "action": "manual_input",
            "collection": "quy_trinh_xin_cap_cccd",
            "document": "test_document",
            "procedure": "xin cấp CCCD"
        },
        "original_query": "Tôi muốn hỏi về thủ tục xin cấp CCCD"
    }
    
    print("🧪 Testing clarification API with manual_input action...")
    print(f"Request: {json.dumps(test_request, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/clarify",
            json=test_request,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ SUCCESS! Response:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # Check required fields
            required_fields = ["type", "session_id", "processing_time"]
            missing_fields = [field for field in required_fields if field not in response_data]
            
            if missing_fields:
                print(f"⚠️  Missing required fields: {missing_fields}")
            else:
                print("✅ All required fields present")
                
            # Check processing_time
            if "processing_time" in response_data:
                print(f"⏱️  Processing time: {response_data['processing_time']} seconds")
            
        else:
            print(f"❌ FAILED! Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure RAG service is running on port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_proceed_with_question():
    """Test proceed_with_question action"""
    base_url = "http://localhost:8000"
    
    test_request = {
        "session_id": "test_session_123",
        "selected_option": {
            "action": "proceed_with_question",
            "collection": "quy_trinh_xin_cap_cccd",
            "question_text": "Thủ tục xin cấp CCCD cần giấy tờ gì?",
            "document": "test_document",
            "procedure": "xin cấp CCCD"
        },
        "original_query": "Tôi muốn hỏi về thủ tục xin cấp CCCD"
    }
    
    print("\n🧪 Testing clarification API with proceed_with_question action...")
    print(f"Request: {json.dumps(test_request, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/clarify",
            json=test_request,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ SUCCESS! Response:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ FAILED! Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Clarification API Fix Testing")
    print("=" * 50)
    
    # Test manual input
    test_clarification_api()
    
    # Small delay
    time.sleep(2)
    
    # Test proceed with question  
    test_proceed_with_question()
    
    print("\n✅ Testing completed!")