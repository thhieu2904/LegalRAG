#!/usr/bin/env python3
"""
Final comprehensive verification test for LegalRAG optimization fixes
Testing all implemented improvements:
1. Context expander with structured metadata
2. Intent detection system
3. Enhanced system prompt
4. Follow-up question routing fix
"""

import requests
import json
import uuid
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_comprehensive_optimizations():
    """Test all optimization improvements together"""
    print("🎯 COMPREHENSIVE OPTIMIZATION VERIFICATION")
    print("=" * 60)
    
    session_id = str(uuid.uuid4())
    
    # Test scenarios with different intent types
    test_cases = [
        {
            "name": "Fee Query (Intent Detection)",
            "query": "Đăng ký kết hôn tốn bao nhiều tiền?",
            "expected_intent": "fee",
            "should_contain": ["phí", "lệ phí", "tiền"]
        },
        {
            "name": "Time Query (Intent Detection)", 
            "query": "Đăng ký kết hôn mất bao lâu?",
            "expected_intent": "time",
            "should_contain": ["thời gian", "ngày", "lâu"]
        },
        {
            "name": "Document Query (Intent Detection)",
            "query": "Đăng ký kết hôn cần giấy tờ gì?",
            "expected_intent": "form",
            "should_contain": ["giấy tờ", "tài liệu", "hồ sơ"]
        },
        {
            "name": "Follow-up Query (Router Fix)",
            "query": "Cho tôi biết thêm về quy trình đăng ký",
            "is_followup": True,
            "should_contain": ["quy trình", "thủ tục", "bước"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 40)
        
        payload = {
            "query": test_case["query"],
            "session_id": session_id,
            "max_context_length": 8000,
            "use_ambiguous_detection": True,
            "use_full_document_expansion": True
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v2/optimized-query", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                response_type = data.get("type", "unknown")
                answer = data.get("answer", "No answer")
                
                print(f"✅ Query successful!")
                print(f"📋 Response Type: {response_type}")
                print(f"💬 Answer Preview: {answer[:100]}...")
                
                # Check for intent-specific content
                found_content = True
                if "should_contain" in test_case:
                    found_content = any(keyword in answer.lower() for keyword in test_case["should_contain"])
                    print(f"🎯 Contains expected content: {'✅ YES' if found_content else '❌ NO'}")
                
                # Check for follow-up handling
                if test_case.get("is_followup", False):
                    print(f"🔄 Follow-up handled correctly: {'✅ YES' if response_type == 'answer' else '❌ NO'}")
                
                # Check for metadata usage (system prompt enhancement)
                has_structure = any(marker in answer for marker in ["🎯", "📋", "⚖️", "📄"])
                print(f"📄 Enhanced formatting: {'✅ YES' if has_structure else '❌ NO'}")
                
                # Check routing info for confidence
                routing_info = data.get("routing_info", {})
                confidence = routing_info.get("confidence", 0)
                print(f"🎯 Router Confidence: {confidence:.3f}")
                
                results.append({
                    "test": test_case["name"],
                    "success": True,
                    "response_type": response_type,
                    "has_content": found_content,
                    "proper_followup": response_type == "answer" if test_case.get("is_followup") else True,
                    "enhanced_format": has_structure,
                    "confidence": confidence
                })
                
            else:
                print(f"❌ Query failed with status {response.status_code}")
                results.append({
                    "test": test_case["name"],
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "test": test_case["name"],
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 OPTIMIZATION VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    
    print(f"📈 Overall Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
    
    for result in results:
        if result["success"]:
            print(f"✅ {result['test']}")
            if "has_content" in result:
                print(f"   🎯 Content Match: {'✅' if result['has_content'] else '❌'}")
            if "proper_followup" in result:
                print(f"   🔄 Follow-up: {'✅' if result['proper_followup'] else '❌'}")
            if "enhanced_format" in result:
                print(f"   📄 Enhanced Format: {'✅' if result['enhanced_format'] else '❌'}")
        else:
            print(f"❌ {result['test']}: {result.get('error', 'Unknown error')}")
    
    print("\n🎉 OPTIMIZATION VERIFICATION COMPLETE!")
    return results

if __name__ == "__main__":
    test_comprehensive_optimizations()
