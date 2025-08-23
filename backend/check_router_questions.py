#!/usr/bin/env python3
"""
🔍 Router Questions Analysis
Kiểm tra các collection questions để tìm vấn đề với "kết hôn"
"""

import asyncio
import aiohttp
import json

async def analyze_router_questions():
    """Phân tích router questions để hiểu vấn đề confidence"""
    
    print("🔍 ROUTER QUESTIONS ANALYSIS")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Get all collections first
        try:
            async with session.get("http://localhost:8000/router/collections") as response:
                if response.status == 200:
                    collections = await response.json()
                    
                    for col in collections:
                        name = col.get('name', 'unknown')
                        title = col.get('title', 'unknown') 
                        print(f"\n📁 Collection: {title} ({name})")
                        
                        # Get questions for this collection
                        async with session.get(f"http://localhost:8000/router/collections/{name}/questions") as q_response:
                            if q_response.status == 200:
                                questions = await q_response.json()
                                
                                # Count marriage related keywords
                                marriage_keywords = ['kết hôn', 'hôn nhân', 'cưới', 'vợ chồng', 'đăng ký kết hôn']
                                marriage_questions = []
                                
                                for i, q in enumerate(questions):
                                    if isinstance(q, dict):
                                        text = q.get('question', str(q))
                                    else:
                                        text = str(q)
                                    
                                    text_lower = text.lower()
                                    found_keywords = [kw for kw in marriage_keywords if kw in text_lower]
                                    
                                    if found_keywords:
                                        marriage_questions.append({
                                            'index': i+1,
                                            'text': text,
                                            'keywords': found_keywords
                                        })
                                
                                print(f"   📊 Total questions: {len(questions)}")
                                print(f"   💒 Marriage questions: {len(marriage_questions)}")
                                
                                if marriage_questions:
                                    print(f"   ✅ Marriage keywords found:")
                                    for mq in marriage_questions[:5]:  # Show first 5
                                        print(f"      {mq['index']}. {mq['text'][:80]}...")
                                        print(f"         Keywords: {', '.join(mq['keywords'])}")
                                else:
                                    print(f"   ❌ NO marriage keywords found!")
                                    print(f"   📋 Sample questions:")
                                    for i, q in enumerate(questions[:5]):
                                        if isinstance(q, dict):
                                            text = q.get('question', str(q))
                                        else:
                                            text = str(q)
                                        print(f"      {i+1}. {text[:80]}...")
                            else:
                                print(f"   ❌ Failed to get questions: {q_response.status}")
                else:
                    print("❌ Failed to get collections")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS & RECOMMENDATIONS")
    print("=" * 60)
    
    print("\n💡 EXPECTED BEHAVIOR:")
    print("- 'đăng ký kết hôn' should have HIGH confidence (0.8)")
    print("- Should route to quy_trinh_cap_ho_tich_cap_xa collection")
    print("- Currently getting LOW confidence (0.3)")
    
    print("\n🔧 LIKELY SOLUTIONS:")
    print("1. Add 'kết hôn' keywords to ho_tich_cap_xa questions")
    print("2. Add training examples like:")
    print("   • 'đăng ký kết hôn cần giấy tờ gì?'")
    print("   • 'thủ tục kết hôn tại UBND xã'")
    print("   • 'hồ sơ đăng ký kết hôn'")
    print("3. Check if router cache needs rebuilding")

if __name__ == "__main__":
    asyncio.run(analyze_router_questions())
