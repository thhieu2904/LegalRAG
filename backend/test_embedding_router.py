#!/usr/bin/env python3
"""
🧪 Test Embedding-Based Router
Test router với semantic similarity như design gốc
"""

import asyncio
import aiohttp
import json

async def test_embedding_router():
    """Test router với embedding-based similarity"""
    
    print("🧪 EMBEDDING-BASED ROUTER TEST")
    print("=" * 60)
    
    test_cases = [
        {
            "query": "đăng ký kết hôn cần giấy tờ như nào",
            "expected_high": True,
            "reason": "Exact match với main question trong DOC_011"
        },
        {
            "query": "làm giấy khai sinh cần gì", 
            "expected_high": True,
            "reason": "Similar to khai sinh questions"
        },
        {
            "query": "chứng thực hợp đồng mua bán nhà",
            "expected_high": True,
            "reason": "Close match với chứng thực questions"
        },
        {
            "query": "hôn nhân cần thủ tục gì",
            "expected_high": True,
            "reason": "Semantic similarity với kết hôn"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, test in enumerate(test_cases):
            print(f"\n{i+1}️⃣ Testing: '{test['query']}'")
            print(f"   Expected: {'High' if test['expected_high'] else 'Medium'} confidence")
            print(f"   Reason: {test['reason']}")
            
            query_data = {
                "query": test['query'],
                "session_id": f"embedding_test_{i}"
            }
            
            try:
                async with session.post("http://localhost:8000/api/v1/query", json=query_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        confidence = result.get('confidence', 0)
                        response_type = result.get('response_type', 'unknown')
                        routing_info = result.get('routing_info', {})
                        
                        router_confidence = routing_info.get('router_confidence', 0)
                        target_collection = routing_info.get('target_collection', 'N/A')
                        
                        print(f"   📊 Router Confidence: {router_confidence:.3f}")
                        print(f"   📋 Target: {target_collection}")
                        print(f"   🎯 Response Type: {response_type}")
                        
                        # Check if we have similarity info
                        if 'clarification' in result:
                            clarification = result['clarification']
                            print(f"   💭 Clarification: {clarification.get('message', 'N/A')[:80]}...")
                        
                        # Analyze confidence
                        if router_confidence >= 0.85:
                            print("   ✅ EXCELLENT: Very high confidence!")
                        elif router_confidence >= 0.75:
                            print("   ✅ GOOD: High confidence")
                        elif router_confidence >= 0.65:
                            print("   ⚠️  MEDIUM: Acceptable confidence")
                        else:
                            print("   ❌ LOW: Below expectations")
                            
                        # Check if direct answer vs clarification
                        if response_type == 'answer':
                            print("   🎉 SUCCESS: Direct answer provided!")
                        elif response_type == 'clarification':
                            print("   📝 CLARIFICATION: Smart clarification triggered")
                        
                    else:
                        print(f"   ❌ Query failed: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 EMBEDDING ROUTER ANALYSIS")
    print("=" * 60)
    
    print("\n💡 EXPECTED IMPROVEMENTS:")
    print("✅ High similarity scores (>0.85) for exact matches")
    print("✅ Confidence based on semantic similarity")  
    print("✅ % similarity displayed in clarification")
    print("✅ Better question matching vs text-only")
    
    print("\n🔧 SIMILARITY SCORING:")
    print("• Cosine similarity between query & cached questions")
    print("• High confidence: ≥85% similarity")
    print("• Medium-high: ≥75% similarity")
    print("• Medium: ≥65% similarity")
    print("• Low: <65% similarity")

if __name__ == "__main__":
    asyncio.run(test_embedding_router())
