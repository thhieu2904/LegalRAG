#!/usr/bin/env python3
"""
Test script để verify clarification mapping fix
"""

import requests
import json
import time

def test_unified_query_endpoint():
    """Test unified /query endpoint with clarification scenarios"""
    base_url = "http://localhost:8000"
    
    # Test cases with different confidence levels that should trigger clarification
    test_cases = [
        {
            "name": "Medium confidence query",
            "query": "thủ tục xin cấp giấy phép",
            "expected_type": "clarification_needed"
        },
        {
            "name": "Low confidence query", 
            "query": "tôi muốn làm giấy tờ",
            "expected_type": "clarification_needed"
        },
        {
            "name": "Ambiguous query",
            "query": "cần làm gì",
            "expected_type": "clarification_needed"
        }
    ]
    
    print("🧪 Testing Unified Query Endpoint Clarification Fix")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Query: '{test_case['query']}'")
        print("-" * 40)
        
        test_request = {
            "query": test_case["query"],
            "session_id": f"test_session_{int(time.time())}_{i}",
            "max_context_length": 8000,
            "use_ambiguous_detection": True,
            "use_full_document_expansion": True,
            "forced_collection": None
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/v1/query",
                json=test_request,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Check response type
                response_type = response_data.get("type", "unknown")
                print(f"✅ Response Type: {response_type}")
                
                # Critical check: clarification field
                clarification = response_data.get("clarification")
                if clarification is None:
                    print("❌ CRITICAL: clarification field is NULL!")
                    return False
                elif isinstance(clarification, dict):
                    print("✅ GOOD: clarification field is object")
                    
                    # Check required clarification fields
                    required_fields = ["message", "options"]
                    missing_fields = [field for field in required_fields if field not in clarification]
                    
                    if missing_fields:
                        print(f"⚠️  Missing clarification fields: {missing_fields}")
                    else:
                        print("✅ All required clarification fields present")
                        
                        # Check options array
                        options = clarification.get("options", [])
                        print(f"📋 Found {len(options)} clarification options")
                        
                        if len(options) > 0:
                            print("✅ FRONTEND WILL SHOW CLARIFICATION OPTIONS!")
                            
                            # Show first option as example
                            first_option = options[0]
                            print(f"   Example option: {first_option.get('title', 'No title')}")
                        else:
                            print("⚠️  No options available")
                else:
                    print(f"❌ WRONG: clarification field type: {type(clarification)}")
                
                # Check other required fields
                required_top_level = ["type", "session_id", "processing_time"]
                missing_top_level = [field for field in required_top_level if field not in response_data]
                
                if missing_top_level:
                    print(f"⚠️  Missing top-level fields: {missing_top_level}")
                else:
                    print("✅ All required top-level fields present")
                
                # Show processing time
                print(f"⏱️  Processing time: {response_data.get('processing_time', 0)} seconds")
                
            else:
                print(f"❌ FAILED! Status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection error - make sure RAG service is running on port 8000")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETED - Clarification mapping should be working!")
    return True

def show_sample_response():
    """Show a sample response for debugging"""
    base_url = "http://localhost:8000"
    
    test_request = {
        "query": "thủ tục làm giấy tờ",
        "session_id": f"debug_session_{int(time.time())}",
        "max_context_length": 8000,
        "use_ambiguous_detection": True,
        "use_full_document_expansion": True
    }
    
    print("\n🔍 SAMPLE RESPONSE FOR DEBUGGING:")
    print("=" * 50)
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/query",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🚀 Clarification Mapping Fix Verification")
    print("This script tests if the unified /query endpoint now properly returns clarification objects")
    print()
    
    # Run tests
    success = test_unified_query_endpoint()
    
    if success:
        print("\n🎉 SUCCESS: Clarification mapping appears to be fixed!")
        print("Frontend should now display clarification options properly.")
    else:
        print("\n💥 ISSUES DETECTED: Please check the fixes and try again.")
    
    # Show sample response for debugging
    show_sample_response()