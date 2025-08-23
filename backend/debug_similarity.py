#!/usr/bin/env python3
"""
🔍 Debug Similarity Display
Kiểm tra xem similarity % có hiển thị đúng không
"""

import asyncio
import aiohttp
import json

async def debug_similarity():
    """Debug similarity display"""
    
    print("🔍 DEBUGGING SIMILARITY DISPLAY")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        query_data = {
            "query": "làm giấy khai sinh cần gì",
            "session_id": "debug_similarity"
        }
        
        try:
            async with session.post("http://localhost:8000/api/v1/query", json=query_data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    print("📊 FULL RESPONSE:")
                    print(json.dumps(result, indent=2, ensure_ascii=False)[:1500] + "...")
                    
                    print("\n🎯 KEY ANALYSIS:")
                    print(f"Confidence: {result.get('confidence', 'N/A')}")
                    print(f"Response Type: {result.get('response_type', 'N/A')}")
                    
                    routing_info = result.get('routing_info', {})
                    if routing_info:
                        print(f"Router Confidence: {routing_info.get('router_confidence', 'N/A')}")
                        print(f"Target Collection: {routing_info.get('target_collection', 'N/A')}")
                    
                    clarification = result.get('clarification', {})
                    if clarification:
                        message = clarification.get('message', '')
                        print(f"\n💬 CLARIFICATION MESSAGE:")
                        print(f"{message}")
                        
                        if '%' in message:
                            print("\n✅ SUCCESS: Similarity % found in message!")
                        else:
                            print("\n❌ ISSUE: No similarity % in message")
                    
                else:
                    print(f"❌ Query failed: {response.status}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_similarity())
