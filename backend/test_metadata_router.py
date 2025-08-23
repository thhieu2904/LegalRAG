#!/usr/bin/env python3
"""
🧪 Test Metadata-Based Router
Test router mới sử dụng metadata và keywords từ documents
"""

import asyncio
import aiohttp
import json

async def test_metadata_router():
    """Test router với metadata-based routing"""
    
    print("🧪 METADATA-BASED ROUTER TEST")
    print("=" * 60)
    
    test_cases = [
        {
            "query": "đăng ký kết hôn cần giấy tờ như nào",
            "expected": "quy_trinh_cap_ho_tich_cap_xa",
            "reason": "Should match 'kết hôn' keywords in DOC_011"
        },
        {
            "query": "làm giấy khai sinh cần gì", 
            "expected": "quy_trinh_cap_ho_tich_cap_xa",
            "reason": "Should match 'khai sinh' keywords"
        },
        {
            "query": "chứng thực hợp đồng mua bán nhà",
            "expected": "quy_trinh_chung_thuc",
            "reason": "Should match 'chứng thực' keywords"
        },
        {
            "query": "nhận con nuôi cần thủ tục gì",
            "expected": "quy_trinh_nuoi_con_nuoi", 
            "reason": "Should match 'con nuôi' keywords"
        },
        {
            "query": "hôn nhân và gia đình",
            "expected": "quy_trinh_cap_ho_tich_cap_xa",
            "reason": "Should match metadata legal_basis 'Luật Hôn nhân và gia đình'"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, test in enumerate(test_cases):
            print(f"\n{i+1}️⃣ Testing: '{test['query']}'")
            print(f"   Expected: {test['expected']}")
            print(f"   Reason: {test['reason']}")
            
            query_data = {
                "query": test['query'],
                "session_id": f"metadata_test_{i}"
            }
            
            try:
                async with session.post("http://localhost:8000/api/v1/query", json=query_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        confidence = result.get('confidence', 'N/A')
                        response_type = result.get('response_type', 'unknown')
                        collection = result.get('collection', 'N/A')
                        matching_details = result.get('matching_details', [])
                        
                        print(f"   📊 Result: {confidence} confidence → {collection}")
                        print(f"   📋 Type: {response_type}")
                        
                        if matching_details:
                            print(f"   🔍 Matching: {matching_details}")
                        
                        # Check if routing is correct
                        if collection == test['expected']:
                            print("   ✅ CORRECT: Routed to expected collection!")
                        elif collection != 'N/A':
                            print(f"   ⚠️  INCORRECT: Expected {test['expected']}, got {collection}")
                        else:
                            print("   ❌ FAILED: No collection routed")
                            
                        # Check confidence level
                        if isinstance(confidence, (int, float)) and confidence >= 0.5:
                            print("   ✅ GOOD: High enough confidence")
                        else:
                            print("   ⚠️  LOW: Confidence below threshold")
                            
                    else:
                        print(f"   ❌ Query failed: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 METADATA ROUTER ANALYSIS")
    print("=" * 60)
    
    print("\n💡 ADVANTAGES OF METADATA-BASED ROUTING:")
    print("✅ Scalable - automatically uses document metadata")
    print("✅ Reusable - works with any document structure")
    print("✅ Rich matching - title, keywords, requirements, questions")
    print("✅ No hardcoded mappings - dynamic based on content")
    
    print("\n🔧 SCORING ALGORITHM:")
    print("• Title matches: 40% weight")
    print("• Keywords matches: 30% weight")  
    print("• Requirements matches: 20% weight")
    print("• Question variants matches: 20% weight")
    print("• Total score determines confidence level")

if __name__ == "__main__":
    asyncio.run(test_metadata_router())
