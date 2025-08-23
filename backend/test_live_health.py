#!/usr/bin/env python3
"""
🔬 Live System Health Checker - Kiểm tra trạng thái hệ thống real-time
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def check_api_health():
    """Kiểm tra health của API"""
    base_url = "http://localhost:8000"
    
    print("🏥 KIỂM TRA HEALTH HỆ THỐNG LEGALRAG")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Basic API health
        print("1️⃣ Testing basic API connectivity...")
        try:
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    print("   ✅ API server is running")
                else:
                    print(f"   ❌ API server error: {response.status}")
        except Exception as e:
            print(f"   ❌ Cannot connect to API: {e}")
            return
        
        # Test 2: Router collections
        print("\n2️⃣ Testing router collections...")
        try:
            async with session.get(f"{base_url}/router/collections") as response:
                if response.status == 200:
                    collections = await response.json()
                    print(f"   ✅ Router collections: {len(collections)} found")
                    for col in collections:
                        print(f"      • {col['name']}: {col['title']} ({col.get('file_count', 'N/A')} docs)")
                else:
                    print(f"   ❌ Router collections error: {response.status}")
        except Exception as e:
            print(f"   ❌ Router collections failed: {e}")
        
        # Test 3: Business API
        print("\n3️⃣ Testing new business API...")
        try:
            async with session.get(f"{base_url}/api/business/collections") as response:
                if response.status == 200:
                    business_data = await response.json()
                    print(f"   ✅ Business API: {len(business_data['collections'])} collections")
                    for col in business_data['collections']:
                        print(f"      • {col['id']}: {col['document_count']} docs, {col['question_count']} questions")
                else:
                    print(f"   ❌ Business API error: {response.status}")
        except Exception as e:
            print(f"   ❌ Business API failed: {e}")
        
        # Test 4: Query processing
        print("\n4️⃣ Testing query processing...")
        test_query = {
            "query": "Tôi muốn hỏi về thủ tục kết hôn",
            "session_id": f"test_session_{int(time.time())}"
        }
        
        try:
            async with session.post(f"{base_url}/api/v1/query", json=test_query) as response:
                if response.status == 200:
                    result = await response.json()
                    print("   ✅ Query processing works")
                    print(f"      • Response type: {result.get('response_type', 'unknown')}")
                    print(f"      • Confidence: {result.get('confidence', 'N/A')}")
                    print(f"      • Session: {result.get('session_id', 'N/A')}")
                else:
                    print(f"   ❌ Query processing error: {response.status}")
                    error_text = await response.text()
                    print(f"      Error: {error_text[:200]}...")
        except Exception as e:
            print(f"   ❌ Query processing failed: {e}")
        
        # Test 5: Health endpoint (if exists)
        print("\n5️⃣ Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print("   ✅ Health endpoint works")
                    print(f"      • Status: {health.get('status', 'unknown')}")
                    print(f"      • Collections: {health.get('total_collections', 'N/A')}")
                    print(f"      • Documents: {health.get('total_documents', 'N/A')}")
                    print(f"      • LLM: {health.get('llm_loaded', 'N/A')}")
                    print(f"      • Reranker: {health.get('reranker_loaded', 'N/A')}")
                else:
                    print(f"   ⚠️  Health endpoint not available: {response.status}")
        except Exception as e:
            print(f"   ⚠️  Health endpoint not available: {e}")
        
        print("\n" + "=" * 60)
        print(f"⏰ Health check completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def monitor_system(duration_minutes=5):
    """Monitor system cho một khoảng thời gian"""
    print(f"📊 MONITORING SYSTEM for {duration_minutes} minutes...")
    print("Press Ctrl+C to stop early")
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    
    try:
        while time.time() < end_time:
            await check_api_health()
            print(f"\n⏳ Waiting 30 seconds... (Ctrl+C to stop)")
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "monitor":
        duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        asyncio.run(monitor_system(duration))
    else:
        asyncio.run(check_api_health())
