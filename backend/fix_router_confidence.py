#!/usr/bin/env python3
"""
🔧 Router Cache Rebuild Fix
Rebuild router cache để fix confidence issue với "đăng ký kết hôn"
"""

import asyncio
import aiohttp
import json

async def fix_router_confidence():
    """Fix router confidence bằng cách rebuild cache"""
    
    print("🔧 ROUTER CONFIDENCE FIX")
    print("=" * 60)
    
    # Test current confidence
    print("\n1️⃣ Testing current confidence...")
    async with aiohttp.ClientSession() as session:
        query_data = {
            "query": "đăng ký kết hôn cần giấy tờ như nào", 
            "session_id": "confidence_test"
        }
        
        async with session.post("http://localhost:8000/api/v1/query", json=query_data) as response:
            if response.status == 200:
                result = await response.json()
                confidence = result.get('confidence', 'N/A')
                response_type = result.get('response_type', 'unknown')
                collection = result.get('collection', 'N/A')
                
                print(f"   Current: {confidence} confidence → {collection} ({response_type})")
                
                if confidence != 'N/A' and float(confidence) < 0.5:
                    print("   ❌ CONFIRMED: Low confidence issue!")
                else:
                    print("   ✅ Confidence seems OK")
            else:
                print(f"   ❌ Query failed: {response.status}")
    
    # Rebuild router cache 
    print("\n2️⃣ Rebuilding router cache...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Call router rebuild endpoint (if exists)
            async with session.post("http://localhost:8000/router/rebuild") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"   ✅ Cache rebuilt: {result}")
                else:
                    print(f"   ⚠️  Rebuild endpoint not available: {response.status}")
        except Exception as e:
            print(f"   ⚠️  Rebuild endpoint error: {e}")
    
    # Alternative: restart router service
    print("\n3️⃣ Checking router reload...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8000/router/collections") as response:
                if response.status == 200:
                    collections = await response.json()
                    print(f"   ✅ Router responsive, {len(collections)} collections")
                    
                    # Check if DOC_011 questions are loaded
                    for col in collections:
                        if col.get('name') == 'quy_trinh_cap_ho_tich_cap_xa':
                            count = col.get('question_count', 0)
                            print(f"   📋 ho_tich_cap_xa: {count} questions")
                            
                            # Get sample questions to verify DOC_011 is included
                            async with session.get("http://localhost:8000/router/collections/quy_trinh_cap_ho_tich_cap_xa/questions") as q_response:
                                if q_response.status == 200:
                                    questions = await q_response.json()
                                    
                                    # Look for DOC_011 questions  
                                    marriage_found = False
                                    for q in questions[:50]:  # Check first 50
                                        if isinstance(q, str):
                                            text = q
                                        elif isinstance(q, dict):
                                            text = q.get('question', str(q))
                                        else:
                                            text = str(q)
                                            
                                        if 'đăng ký kết hôn' in text and 'giấy tờ' in text:
                                            marriage_found = True
                                            print(f"   ✅ Found marriage question: {text[:60]}...")
                                            break
                                    
                                    if not marriage_found:
                                        print(f"   ❌ DOC_011 questions NOT found in router cache!")
                                    else:
                                        print(f"   ✅ DOC_011 questions are loaded")
                else:
                    print(f"   ❌ Router not responsive: {response.status}")
        except Exception as e:
            print(f"   ❌ Router check error: {e}")
    
    # Test confidence again
    print("\n4️⃣ Testing confidence after fixes...")
    await asyncio.sleep(1)  # Give time for cache refresh
    
    async with aiohttp.ClientSession() as session:
        query_data = {
            "query": "đăng ký kết hôn cần giấy tờ như nào",
            "session_id": "confidence_test_2"
        }
        
        async with session.post("http://localhost:8000/api/v1/query", json=query_data) as response:
            if response.status == 200:
                result = await response.json()
                confidence = result.get('confidence', 'N/A')
                response_type = result.get('response_type', 'unknown')
                collection = result.get('collection', 'N/A')
                
                print(f"   After fix: {confidence} confidence → {collection} ({response_type})")
                
                if confidence != 'N/A' and float(confidence) >= 0.65:
                    print("   🎉 SUCCESS: Confidence improved!")
                elif confidence != 'N/A' and float(confidence) >= 0.5:
                    print("   ✅ GOOD: Confidence acceptable")
                else:
                    print("   ❌ STILL LOW: Need manual intervention")
            else:
                print(f"   ❌ Query failed: {response.status}")
    
    print("\n" + "=" * 60)
    print("🎯 ROUTER CONFIDENCE RECOMMENDATIONS")
    print("=" * 60)
    
    print("\n🔧 IF STILL LOW CONFIDENCE:")
    print("1. Check router thresholds in config.py:")
    print("   • Lower MIN_CONFIDENCE from 0.5 to 0.4")
    print("   • Lower MEDIUM_HIGH from 0.65 to 0.55")
    print("2. Restart backend completely:")
    print("   • Ctrl+C to stop backend")
    print("   • python main.py to restart")
    print("3. Check embedding model quality")
    print("4. Add more specific training questions")

if __name__ == "__main__":
    asyncio.run(fix_router_confidence())
