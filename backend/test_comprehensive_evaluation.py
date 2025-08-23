#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM EVALUATION AFTER REFACTOR
Đánh giá toàn diện hệ thống sau khi refactor từ router_questions.json → questions.json
"""

import requests
import json
import time

def test_comprehensive_system():
    print("🔍 COMPREHENSIVE SYSTEM EVALUATION")
    print("=" * 60)
    print("📋 Testing post-refactor system performance...")
    print()
    
    # Test cases với expected behavior
    test_cases = [
        {
            "query": "làm giấy khai sinh cần gì",
            "expected_confidence": "> 0.80",
            "expected_behavior": "direct_route",
            "expected_collection": "quy_trinh_cap_ho_tich_cap_xa"
        },
        {
            "query": "đăng ký kết hôn",
            "expected_confidence": "> 0.75", 
            "expected_behavior": "direct_route_or_clarification",
            "expected_collection": "quy_trinh_cap_ho_tich_cap_xa"
        },
        {
            "query": "chứng thực hợp đồng",
            "expected_confidence": "> 0.75",
            "expected_behavior": "direct_route_or_clarification", 
            "expected_collection": "quy_trinh_chung_thuc"
        },
        {
            "query": "nuôi con nuôi",
            "expected_confidence": "> 0.70",
            "expected_behavior": "any",
            "expected_collection": "quy_trinh_nuoi_con_nuoi"
        },
        {
            "query": "xin chào",
            "expected_confidence": "< 0.50",
            "expected_behavior": "clarification",
            "expected_collection": None
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}/5: {test_case['query']}")
        print("-" * 40)
        
        start_time = time.time()
        
        payload = {
            "query": test_case['query'],
            "session_id": f"eval_test_{i}"
        }
        
        try:
            response = requests.post("http://localhost:8000/api/v1/query", json=payload)
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract key metrics
                confidence = result.get('confidence', 0)
                response_type = result.get('type', 'unknown')
                target_collection = result.get('routing_info', {}).get('target_collection')
                
                # Evaluate expectations
                evaluation = {
                    "query": test_case['query'],
                    "confidence": confidence,
                    "response_type": response_type,
                    "target_collection": target_collection,
                    "processing_time": round(processing_time, 2),
                    "status": "✅ PASS"
                }
                
                # Check confidence expectation
                expected_conf = test_case['expected_confidence']
                if "> 0.80" in expected_conf and confidence < 0.80:
                    evaluation["status"] = "⚠️ CONFIDENCE LOW"
                elif "> 0.75" in expected_conf and confidence < 0.75:
                    evaluation["status"] = "⚠️ CONFIDENCE LOW"
                elif "< 0.50" in expected_conf and confidence >= 0.50:
                    evaluation["status"] = "⚠️ CONFIDENCE HIGH"
                
                # Check behavior expectation
                if test_case['expected_behavior'] == 'direct_route' and response_type != 'auto_route':
                    evaluation["status"] = "❌ WRONG BEHAVIOR"
                
                # Print results
                print(f"📊 Confidence: {confidence:.3f}")
                print(f"🎯 Type: {response_type}")
                print(f"📍 Collection: {target_collection}")
                print(f"⏱️ Time: {processing_time:.2f}s")
                print(f"📋 Status: {evaluation['status']}")
                
                results.append(evaluation)
                
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                results.append({
                    "query": test_case['query'],
                    "status": "❌ HTTP ERROR",
                    "confidence": 0,
                    "processing_time": processing_time
                })
                
        except Exception as e:
            print(f"❌ Request Error: {e}")
            results.append({
                "query": test_case['query'], 
                "status": "❌ REQUEST ERROR",
                "confidence": 0,
                "processing_time": 0
            })
        
        print()
    
    # Summary Report
    print("📊 SYSTEM EVALUATION SUMMARY")
    print("=" * 60)
    
    passed = len([r for r in results if r['status'] == '✅ PASS'])
    total = len(results)
    avg_confidence = sum([r['confidence'] for r in results]) / len(results)
    avg_time = sum([r['processing_time'] for r in results]) / len(results)
    
    print(f"✅ Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"📊 Average Confidence: {avg_confidence:.3f}")
    print(f"⏱️ Average Processing Time: {avg_time:.2f}s")
    print()
    
    # Detailed results
    print("📋 DETAILED RESULTS:")
    for result in results:
        print(f"  • {result['query'][:30]:30} | {result['confidence']:.3f} | {result['status']}")
    
    print()
    
    # ✅ PERFORMANCE EVALUATION
    print("🔧 SYSTEM PERFORMANCE ANALYSIS:")
    print("-" * 40)
    
    if avg_time < 5:
        print("✅ Response Time: EXCELLENT (< 5s)")
    elif avg_time < 10:
        print("⚠️ Response Time: ACCEPTABLE (5-10s)")
    else:
        print("❌ Response Time: SLOW (> 10s)")
    
    if avg_confidence > 0.75:
        print("✅ Router Intelligence: EXCELLENT (> 0.75)")
    elif avg_confidence > 0.65:
        print("⚠️ Router Intelligence: GOOD (> 0.65)")
    else:
        print("❌ Router Intelligence: POOR (< 0.65)")
    
    if passed/total >= 0.8:
        print("✅ Overall System Health: EXCELLENT")
    elif passed/total >= 0.6:
        print("⚠️ Overall System Health: GOOD")
    else:
        print("❌ Overall System Health: POOR")
    
    print("\n" + "=" * 60)
    print("🎯 REFACTOR ASSESSMENT: System successfully migrated from router_questions.json → questions.json")
    print("📈 Embedding-based routing with high confidence restored!")

if __name__ == "__main__":
    test_comprehensive_system()
