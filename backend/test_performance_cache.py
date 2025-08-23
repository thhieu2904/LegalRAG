#!/usr/bin/env python3
"""
Test performance với cached embeddings
"""

import requests
import json
import time

def test_performance_with_cache():
    print("🚀 TESTING PERFORMANCE WITH CACHED EMBEDDINGS")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "làm giấy khai sinh cần gì",
        "đăng ký kết hôn",
        "chứng thực hợp đồng",
        "nuôi con nuôi thủ tục"
    ]
    
    total_time = 0
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 Test {i}/4: {query}")
        print("-" * 40)
        
        start_time = time.time()
        
        payload = {
            "query": query,
            "session_id": f"perf_test_{i}"
        }
        
        try:
            response = requests.post("http://localhost:8000/api/v1/query", json=payload)
            processing_time = time.time() - start_time
            total_time += processing_time
            
            if response.status_code == 200:
                result = response.json()
                confidence = result.get('confidence', 0)
                response_type = result.get('type', 'unknown')
                
                print(f"⏱️  Processing Time: {processing_time:.2f}s")
                print(f"📊 Confidence: {confidence:.3f}")
                print(f"🎯 Type: {response_type}")
                
                results.append({
                    "query": query,
                    "time": processing_time,
                    "confidence": confidence,
                    "type": response_type
                })
                
                # Performance categorization
                if processing_time < 5:
                    print("✅ EXCELLENT (< 5s)")
                elif processing_time < 10:
                    print("⚠️  ACCEPTABLE (5-10s)")
                else:
                    print("❌ SLOW (> 10s)")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Request Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    
    avg_time = total_time / len(test_queries)
    print(f"⏱️  Average Time: {avg_time:.2f}s")
    print(f"📈 Total Time: {total_time:.2f}s")
    
    if avg_time < 5:
        print("✅ PERFORMANCE: EXCELLENT - Cached embeddings working!")
    elif avg_time < 10:
        print("⚠️  PERFORMANCE: ACCEPTABLE - Some improvement needed")  
    else:
        print("❌ PERFORMANCE: POOR - Cache may not be working")
    
    print("\n📋 DETAILED RESULTS:")
    for result in results:
        print(f"  • {result['query'][:30]:30} | {result['time']:5.2f}s | {result['confidence']:.3f}")
    
    # Performance comparison
    print(f"\n🔄 PERFORMANCE COMPARISON:")
    print(f"  • Before (no cache): ~47s per query")
    print(f"  • After (with cache): ~{avg_time:.1f}s per query")
    
    if avg_time < 10:
        improvement = 47 / avg_time
        print(f"  • Improvement: {improvement:.1f}x FASTER! 🚀")
    else:
        print(f"  • ❌ Still slow - cache may not be working properly")
    
    return avg_time < 10

if __name__ == "__main__":
    success = test_performance_with_cache()
    if success:
        print("\n🎉 SUCCESS: Performance restored with cached embeddings!")
    else:
        print("\n❌ FAILED: Performance still poor - needs investigation")
