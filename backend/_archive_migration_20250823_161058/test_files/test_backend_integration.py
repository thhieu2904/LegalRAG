#!/usr/bin/env python3
"""
🧪 BACKEND INTEGRATION TEST

Tests new questions.json + document.json architecture với backend
"""

import requests
import json
import sys
import os

# Add parent directory to path để import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_backend_integration():
    """Test backend APIs với new structure"""
    
    print("🧪 BACKEND INTEGRATION TEST")
    print("=" * 50)
    
    # Test data
    test_cases = [
        {
            "collection": "quy_trinh_cap_ho_tich_cap_xa",
            "document": "DOC_001",
            "expected_question": "khai sinh"
        },
        {
            "collection": "quy_trinh_chung_thuc", 
            "document": "DOC_001",
            "expected_question": "chứng thực"
        }
    ]
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['collection']}/{test_case['document']}")
        
        try:
            # Test API endpoint (adjust URL as needed)
            url = f"http://localhost:8000/api/questions/{test_case['collection']}/{test_case['document']}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                required_fields = ["main_question", "question_variants", "metadata", "smart_filters"]
                has_all_fields = all(field in data for field in required_fields)
                
                if has_all_fields:
                    print(f"   ✅ API Response OK")
                    print(f"   📊 Fields: {list(data.keys())}")
                    print(f"   🎯 Main Question: {data['main_question'][:50]}...")
                    print(f"   📝 Variants Count: {len(data.get('question_variants', []))}")
                    print(f"   🔧 Smart Filters: {list(data.get('smart_filters', {}).keys())}")
                    
                    passed_tests += 1
                else:
                    print(f"   ❌ Missing required fields")
                    print(f"      Expected: {required_fields}")
                    print(f"      Found: {list(data.keys())}")
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Backend not running - Start backend first")
        except Exception as e:
            print(f"   ❌ Test Error: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"🎯 TEST RESULTS:")
    print(f"   Passed: {passed_tests}/{total_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("   ✅ ALL TESTS PASSED")
        return True
    else:
        print("   ⚠️  SOME TESTS FAILED")
        return False

def test_file_structure():
    """Test file structure integrity"""
    
    print("\n📁 TESTING FILE STRUCTURE...")
    
    # Check questions.json files
    questions_files = glob.glob("data/**/*questions.json", recursive=True)
    print(f"   Found {len(questions_files)} questions.json files")
    
    # Validate sample file
    if questions_files:
        sample_file = questions_files[0]
        with open(sample_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "main_question" in data and "question_variants" in data:
            print(f"   ✅ File structure valid")
            return True
        else:
            print(f"   ❌ Invalid file structure")
            return False
    else:
        print(f"   ❌ No questions.json files found")
        return False

if __name__ == "__main__":
    print("🚀 STARTING BACKEND INTEGRATION TESTS")
    print("Make sure backend is running on localhost:8000")
    print()
    
    # Test file structure first
    file_test_passed = test_file_structure()
    
    if file_test_passed:
        # Test backend integration
        api_test_passed = test_backend_integration()
        
        if api_test_passed:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        else:
            print("\n⚠️  INTEGRATION TESTS NEED ATTENTION")
    else:
        print("\n❌ FILE STRUCTURE TESTS FAILED")
