#!/usr/bin/env python3
"""
Test medium confidence queries to see multiple collection clarification
"""

import requests
import json
import time

def test_medium_confidence_queries():
    """Test queries that should trigger medium confidence (0.5-0.64)"""
    
    print("🧪 Testing medium confidence queries for multiple collection clarification")
    print("="*70)
    
    # Test queries that should have lower confidence
    test_queries = [
        "tôi cần hỗ trợ",
        "làm giấy tờ",
        "thủ tục gì đây", 
        "cần tư vấn",
        "làm hồ sơ"
    ]
    
    base_url = "http://localhost:8000/api/v1"
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{base_url}/query",
                json={
                    "query": query,
                    "session_id": "test_medium_" + str(int(time.time())),
                    "max_context_length": 3000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"📍 Response type: {result.get('type')}")
                print(f"📍 Confidence: {result.get('confidence', 'N/A')}")
                
                if result.get('type') == 'clarification_needed':
                    clarification = result.get('clarification', {})
                    options = clarification.get('options', [])
                    
                    print(f"📊 Clarification options ({len(options)} total):")
                    for i, option in enumerate(options[:8], 1):  # Show up to 8
                        title = option.get('title', 'Unknown')
                        confidence = option.get('confidence_percent', option.get('confidence', 'N/A'))
                        print(f"  {i}. {title[:50]}... → {confidence}%")
                        
                else:
                    print(f"💡 Got {result.get('type')} - not clarification")
                    
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Server not running!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*70}")
    print("✅ Medium confidence test completed")

if __name__ == "__main__":
    test_medium_confidence_queries()
