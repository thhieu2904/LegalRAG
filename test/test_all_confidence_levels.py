#!/usr/bin/env python3
"""
Comprehensive Clarification Test Script
Test all confidence levels from low to high with different query types
"""

import requests
import json
import time

def test_all_confidence_levels():
    """Test all confidence levels with appropriate queries"""
    
    print("🧪 Testing ALL Confidence Levels - Comprehensive Clarification Test")
    print("="*80)
    
    # Test cases organized by expected confidence level
    test_cases = [
        {
            "level": "insufficient_context",
            "expected_confidence": "<0.30",
            "queries": [
                "giúp tôi",
                "cần hỗ trợ", 
                "làm gì đây",
                "tư vấn"
            ]
        },
        {
            "level": "low_confidence", 
            "expected_confidence": "0.30-0.49",
            "queries": [
                "làm giấy tờ",
                "thủ tục gì",
                "cần hồ sơ",
                "đăng ký"
            ]
        },
        {
            "level": "medium_confidence",
            "expected_confidence": "0.50-0.64", 
            "queries": [
                "thủ tục hộ tịch",
                "làm chứng thực",
                "đăng ký con nuôi",
                "công chứng hợp đồng"
            ]
        },
        {
            "level": "medium_high_confidence",
            "expected_confidence": "0.65-0.79",
            "queries": [
                "làm thủ tục khai sinh em bé",
                "đăng ký khai sinh", 
                "quy trình khai sinh như thế nào",
                "chứng thực hợp đồng mua bán"
            ]
        },
        {
            "level": "high_confidence", 
            "expected_confidence": "≥0.80",
            "queries": [
                "tôi muốn làm giấy khai sinh cho con",
                "giấy tờ cần thiết để khai sinh",
                "thủ tục đăng ký kết hôn cần gì",
                "làm chứng thực bản sao CMND"
            ]
        }
    ]
    
    base_url = "http://localhost:8000/api/v1"
    
    for test_case in test_cases:
        level = test_case["level"]
        expected_conf = test_case["expected_confidence"]
        queries = test_case["queries"]
        
        print(f"\n🎯 TESTING {level.upper()} ({expected_conf})")
        print("="*60)
        
        for query in queries:
            print(f"\n🔍 Query: '{query}'")
            print("-" * 40)
            
            try:
                response = requests.post(
                    f"{base_url}/query",
                    json={
                        "query": query,
                        "session_id": f"test_{level}_{int(time.time())}",
                        "max_context_length": 3000
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    actual_confidence = result.get('confidence')
                    response_type = result.get('type')
                    
                    print(f"📍 Type: {response_type}")
                    print(f"📍 Confidence: {actual_confidence:.4f}" if actual_confidence else "📍 Confidence: N/A")
                    
                    # Validate confidence level
                    if actual_confidence:
                        if level == "insufficient_context" and actual_confidence >= 0.30:
                            print(f"⚠️  Expected <0.30 but got {actual_confidence:.3f}")
                        elif level == "low_confidence" and not (0.30 <= actual_confidence < 0.50):
                            print(f"⚠️  Expected 0.30-0.49 but got {actual_confidence:.3f}")
                        elif level == "medium_confidence" and not (0.50 <= actual_confidence < 0.65):
                            print(f"⚠️  Expected 0.50-0.64 but got {actual_confidence:.3f}")
                        elif level == "medium_high_confidence" and not (0.65 <= actual_confidence < 0.80):
                            print(f"⚠️  Expected 0.65-0.79 but got {actual_confidence:.3f}")
                        elif level == "high_confidence" and actual_confidence < 0.80:
                            print(f"⚠️  Expected ≥0.80 but got {actual_confidence:.3f}")
                        else:
                            print(f"✅ Confidence level matches expectation")
                    
                    # Show clarification details
                    if response_type == 'clarification_needed':
                        clarification = result.get('clarification', {})
                        options = clarification.get('options', [])
                        
                        print(f"📊 Clarification: {len(options)} options")
                        for i, option in enumerate(options[:5], 1):  # Show top 5
                            title = option.get('title', 'Unknown')
                            confidence_percent = option.get('confidence_percent', option.get('confidence', 'N/A'))
                            action = option.get('action', 'unknown')
                            
                            print(f"  {i}. {title[:45]}... → {confidence_percent}% [{action}]")
                            
                            # Check for birth vs death ranking issue
                            if "khai sinh" in query.lower() and "khai tử" in title.lower() and i <= 3:
                                print(f"    ⚠️  'Khai tử' ranked high for birth query!")
                            elif "khai sinh" in query.lower() and "khai sinh" in title.lower() and i <= 3:
                                print(f"    ✅ 'Khai sinh' correctly ranked high")
                    
                    elif response_type == 'answer':
                        context = result.get('context_info', {})
                        sources = context.get('source_documents', []) if context else []
                        print(f"✅ Direct answer with {len(sources)} source(s)")
                        
                    elif response_type == 'auto_route':
                        print(f"🚀 Auto-routed to: {result.get('target_collection')}")
                        
                    else:
                        print(f"❓ Unexpected response type: {response_type}")
                        
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                print("❌ Server not running! Start with: python main.py")
                return
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print(f"\n{'='*80}")
    print("✅ Comprehensive clarification test completed")
    print("\n📋 Summary:")
    print("- Test covers all 5 confidence levels")
    print("- Validates confidence ranges")  
    print("- Checks clarification option sorting")
    print("- Detects birth vs death ranking issues")

if __name__ == "__main__":
    test_all_confidence_levels()
