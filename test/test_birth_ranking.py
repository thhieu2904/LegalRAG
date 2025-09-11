#!/usr/bin/env python3
"""
Test document ranking for birth vs death certificate queries
"""

import requests
import json
import time

def test_birth_certificate_ranking():
    """Test that birth certificate queries return birth documents first"""
    
    print("🧪 Testing birth certificate document ranking")
    print("="*60)
    
    # Test queries
    test_queries = [
        "tôi muốn làm giấy khai sinh cho con",
        "làm thủ tục khai sinh em bé", 
        "đăng ký khai sinh",
        "giấy tờ cần thiết để khai sinh",
        "quy trình khai sinh như thế nào"
    ]
    
    base_url = "http://localhost:8000/api/v1"
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 50)
        
        try:
            # Test query
            response = requests.post(
                f"{base_url}/query",
                json={
                    "query": query,
                    "session_id": "test_ranking_" + str(int(time.time())),
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
                    for i, option in enumerate(options[:5], 1):  # Show top 5
                        title = option.get('title', 'Unknown')
                        # Try both confidence and confidence_percent fields
                        confidence = option.get('confidence_percent', option.get('confidence', 'N/A'))
                        print(f"  {i}. {title[:60]}... → {confidence}%")
                        
                        # Check if death certificates appear before birth certificates
                        if "khai tử" in title.lower() and i <= 3:
                            print(f"    ⚠️  'Khai tử' document ranked high for birth query!")
                        elif "khai sinh" in title.lower() and i <= 3:
                            print(f"    ✅ 'Khai sinh' document correctly ranked high")
                            
                elif result.get('type') == 'answer':
                    print(f"✅ Got direct answer (high confidence)")
                    # Check source documents
                    context = result.get('context', {})
                    sources = context.get('source_documents', [])
                    if sources:
                        print(f"📚 Source documents:")
                        for doc in sources[:3]:
                            print(f"  - {doc}")
                else:
                    print(f"❓ Unexpected response type: {result.get('type')}")
                    
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Server not running! Start with: python main.py")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Birth certificate ranking test completed")

if __name__ == "__main__":
    test_birth_certificate_ranking()
