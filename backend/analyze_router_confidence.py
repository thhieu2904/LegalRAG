#!/usr/bin/env python3
"""
🔍 Router Confidence Analysis
Kiểm tra tại sao query "đăng ký kết hôn" lại có confidence thấp (0.300)
"""

import asyncio
import aiohttp
import json
import sys

print("🚨 NHẮC NHỞ: Bạn cần khởi động backend trước!")
print("   cd backend && python main.py")
print("=" * 60)

async def test_router_confidence():
    """Test router confidence với các query khác nhau"""
    base_url = "http://localhost:8000"
    
    # Test queries với expected confidence
    test_cases = [
        {
            "query": "đăng ký kết hôn cần giấy tờ như nào",
            "expected_collection": "ho_tich_cap_xa", 
            "expected_confidence": "high",
            "reasoning": "Kết hôn là thủ tục hộ tịch rõ ràng"
        },
        {
            "query": "làm giấy khai sinh cần gì",
            "expected_collection": "ho_tich_cap_xa",
            "expected_confidence": "high", 
            "reasoning": "Khai sinh là thủ tục hộ tịch cơ bản"
        },
        {
            "query": "chứng thực hợp đồng mua bán nhà",
            "expected_collection": "chung_thuc",
            "expected_confidence": "high",
            "reasoning": "Chứng thực hợp đồng rõ ràng"
        },
        {
            "query": "nhận con nuôi cần thủ tục gì",
            "expected_collection": "nuoi_con_nuoi", 
            "expected_confidence": "high",
            "reasoning": "Nuôi con nuôi rõ ràng"
        },
        {
            "query": "tôi cần hỏi về thủ tục",
            "expected_collection": "unclear",
            "expected_confidence": "low",
            "reasoning": "Query mơ hồ, cần clarification"
        }
    ]
    
    print("🔍 ROUTER CONFIDENCE ANALYSIS")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        for i, test in enumerate(test_cases):
            print(f"\n{i+1}️⃣ Testing: '{test['query']}'")
            print(f"   Expected: {test['expected_confidence']} confidence → {test['expected_collection']}")
            print(f"   Reasoning: {test['reasoning']}")
            
            try:
                # Send query
                query_data = {
                    "query": test['query'],
                    "session_id": f"test_confidence_{i}"
                }
                
                async with session.post(f"{base_url}/api/v1/query", json=query_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        confidence = result.get('confidence', 'N/A')
                        response_type = result.get('response_type', 'unknown')
                        collection = result.get('collection', 'N/A')
                        
                        print(f"   📊 Actual: {confidence} confidence → {collection}")
                        print(f"   📋 Response type: {response_type}")
                        
                        # Analysis
                        if response_type == "clarification":
                            print("   ⚠️  Router triggered clarification (low confidence)")
                            if test['expected_confidence'] == 'high':
                                print("   ❌ ISSUE: Should be high confidence, not clarification!")
                        elif response_type == "answer":
                            print("   ✅ Router provided direct answer (high confidence)")
                            if test['expected_confidence'] == 'low':
                                print("   ⚠️  Unexpected: Should trigger clarification")
                        
                        # Check collection match
                        if collection != 'N/A' and test['expected_collection'] != 'unclear':
                            if collection == test['expected_collection'] or \
                               (collection == 'quy_trinh_cap_ho_tich_cap_xa' and test['expected_collection'] == 'ho_tich_cap_xa'):
                                print("   ✅ Collection routing correct")
                            else:
                                print(f"   ❌ Collection mismatch: expected {test['expected_collection']}")
                                
                    else:
                        print(f"   ❌ Query failed: {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 ROUTER CONFIDENCE ISSUES ANALYSIS")
        print("=" * 60)
        
        print("\n💡 POSSIBLE ROUTER ISSUES:")
        print("1. Router embedding không match keywords tốt")
        print("2. Confidence thresholds quá strict:")
        print("   • Min: 0.5, Medium-High: 0.65, High: 0.8")
        print("   • Query 'kết hôn' chỉ được 0.300 (< 0.5)")
        print("3. Collection example questions không đủ đa dạng")
        print("4. Router training có thể thiếu keywords về kết hôn")
        
        print("\n🔧 RECOMMENDED FIXES:")
        print("1. Kiểm tra collection questions có đủ về 'kết hôn' không")
        print("2. Điều chỉnh confidence thresholds xuống:")
        print("   • Min: 0.3 → 0.25")
        print("   • Medium-High: 0.65 → 0.45") 
        print("   • High: 0.8 → 0.65")
        print("3. Thêm keywords 'kết hôn' vào hộ tịch examples")

async def analyze_collection_coverage():
    """Kiểm tra collection có cover đủ keywords không"""
    base_url = "http://localhost:8000"
    
    print("\n🔍 COLLECTION COVERAGE ANALYSIS")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Get collections
            async with session.get(f"{base_url}/router/collections") as response:
                if response.status == 200:
                    collections = await response.json()
                    
                    for col in collections:
                        name = col.get('name', 'unknown')
                        title = col.get('title', 'unknown')
                        count = col.get('question_count', 0)
                        
                        print(f"\n📁 {title} ({name}): {count} questions")
                        
                        # Get sample questions
                        async with session.get(f"{base_url}/router/collections/{name}/questions") as q_response:
                            if q_response.status == 200:
                                questions_data = await q_response.json()
                                
                                if isinstance(questions_data, list) and len(questions_data) > 0:
                                    # Look for marriage-related keywords
                                    marriage_keywords = ['kết hôn', 'đăng ký kết hôn', 'hôn nhân', 'cưới', 'vợ chồng']
                                    found_keywords = []
                                    
                                    # Check first 20 questions for keywords
                                    for q in questions_data[:20]:
                                        question_text = str(q).lower()
                                        for keyword in marriage_keywords:
                                            if keyword in question_text:
                                                found_keywords.append(keyword)
                                    
                                    if found_keywords:
                                        print(f"   ✅ Contains marriage keywords: {set(found_keywords)}")
                                    else:
                                        print(f"   ⚠️  No marriage keywords found in sample")
                                        
                                    # Show sample questions
                                    print(f"   📋 Sample questions:")
                                    for j, q in enumerate(questions_data[:3]):
                                        if isinstance(q, dict):
                                            text = q.get('question', str(q))[:80]
                                        else:
                                            text = str(q)[:80]
                                        print(f"      {j+1}. {text}...")
                                        
                else:
                    print("❌ Cannot get collections")
                    
        except Exception as e:
            print(f"❌ Error analyzing coverage: {e}")

if __name__ == "__main__":
    print("🧪 COMPREHENSIVE ROUTER ANALYSIS")
    asyncio.run(test_router_confidence())
    asyncio.run(analyze_collection_coverage())
