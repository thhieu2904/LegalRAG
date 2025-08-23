#!/usr/bin/env python3
"""
🧪 Performance Fix Verification Test
Test reranker GPU usage and document count optimization
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

print("🚨 NHẮC NHỞ: Bạn cần RESTART backend sau khi apply fixes!")
print("   cd backend && python main.py")
print("=" * 60)

async def test_performance_fixes():
    """Test performance improvements sau khi apply fixes"""
    base_url = "http://localhost:8000"
    
    print("🔧 TESTING PERFORMANCE FIXES")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test query với timing measurement
        test_queries = [
            {
                "query": "Thủ tục đăng ký khai sinh ở cấp xã cần giấy tờ gì?",
                "expected_collection": "quy_trinh_cap_ho_tich_cap_xa",
                "expected_confidence": "high"
            }
        ]
        
        for i, test in enumerate(test_queries):
            print(f"\n🧪 TEST {i+1}: {test['query'][:50]}...")
            
            # Measure total time
            start_time = time.time()
            
            test_query = {
                "query": test['query'],
                "session_id": f"perf_test_{int(time.time())}_{i}"
            }
            
            try:
                async with session.post(f"{base_url}/api/v1/query", json=test_query) as response:
                    if response.status == 200:
                        result = await response.json()
                        end_time = time.time()
                        total_time = end_time - start_time
                        
                        print(f"✅ Query completed in {total_time:.2f}s")
                        print(f"   • Response type: {result.get('response_type', 'unknown')}")
                        print(f"   • Confidence: {result.get('confidence', 'N/A')}")
                        print(f"   • Collection: {result.get('collection', 'N/A')}")
                        
                        # Performance expectations
                        if total_time < 20:
                            print(f"   ✅ GOOD: Total time under 20s")
                        elif total_time < 30:
                            print(f"   ⚠️  ACCEPTABLE: Total time under 30s")
                        else:
                            print(f"   ❌ SLOW: Total time over 30s - optimization needed")
                            
                        # Check if forms were detected
                        if 'forms' in result and result['forms']:
                            print(f"   📎 Forms detected: {len(result['forms'])}")
                            
                    else:
                        print(f"   ❌ Query failed: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Query error: {e}")
        
        # Test health to check GPU status
        print(f"\n🏥 Checking system health after fixes...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print("   ✅ Health check passed")
                    print(f"      • LLM loaded: {health.get('llm_loaded', 'N/A')}")
                    print(f"      • Reranker loaded: {health.get('reranker_loaded', 'N/A')}")
                    print(f"      • Collections: {health.get('total_collections', 'N/A')}")
                    print(f"      • Documents: {health.get('total_documents', 'N/A')}")
                    
                    # Check if models are properly detected
                    if health.get('llm_loaded') and health.get('reranker_loaded'):
                        print("   ✅ Both LLM and Reranker are properly loaded")
                    else:
                        print("   ⚠️  Model loading detection may need adjustment")
                        
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")

async def analyze_backend_logs():
    """Hướng dẫn phân tích logs để verify fixes"""
    print(f"\n📊 LOG ANALYSIS GUIDE")
    print("=" * 60)
    
    print("🔍 Look for these IMPROVEMENTS in backend logs:")
    print()
    print("1️⃣ RERANKER GPU USAGE:")
    print("   BEFORE: '✅ Reranker model loaded from local cache on CPU'")
    print("   AFTER:  '✅ Reranker model loaded from local cache on GPU'")
    print("   BEFORE: 'RERANK COMPLETED in 49.31s'")
    print("   AFTER:  'RERANK COMPLETED in 3-5s'")
    print()
    print("2️⃣ DOCUMENT COUNT REDUCTION:")
    print("   BEFORE: '🎯 HIGH CONFIDENCE: Giảm broad_search_k xuống 16'")
    print("   AFTER:  '🎯 HIGH CONFIDENCE: Aggressive reduction to 6 docs'")
    print("   BEFORE: 'Found 26 candidate chunks'")
    print("   AFTER:  'Found 6-8 candidate chunks'")
    print()
    print("3️⃣ TOTAL PERFORMANCE:")
    print("   BEFORE: Total query time ~65s")
    print("   AFTER:  Total query time ~15s")
    print()
    print("⚠️  NOTE: You need to RESTART backend to see these changes!")

if __name__ == "__main__":
    import sys
    
    print("🎯 PERFORMANCE FIX VERIFICATION")
    print("=" * 60)
    print("✅ Applied fixes:")
    print("   1. Reranker GPU device detection")
    print("   2. Reduced broad_search_k: 20 → 12")
    print("   3. Aggressive high confidence: 16 → 6 docs")
    print()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_performance_fixes())
    else:
        asyncio.run(analyze_backend_logs())
        print("\n🧪 To run live performance test:")
        print("   python test_performance_fixes.py test")
