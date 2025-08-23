#!/usr/bin/env python3
"""
Test live router behavior - gọi API trực tiếp
"""

import requests
import json

def test_live_router():
    print("🔍 TESTING LIVE ROUTER BEHAVIOR")
    print("=" * 50)
    
    test_query = "đăng ký kết hôn cần giấy tờ gì"
    
    print(f"🧪 Query: '{test_query}'")
    print()
    
    payload = {
        "query": test_query,
        "session_id": "debug_live_router"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/v1/query", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            print("📊 LIVE ROUTER RESULTS:")
            print("-" * 30)
            print(f"✅ Status: {response.status_code}")
            print(f"🎯 Type: {result.get('type', 'unknown')}")
            print(f"📊 Confidence: {result.get('confidence', 'N/A')}")
            
            # Check routing info
            routing_info = result.get('routing_info', {})
            if routing_info:
                print(f"📍 Target Collection: {routing_info.get('target_collection', 'N/A')}")
                print(f"🔍 Router Confidence: {routing_info.get('router_confidence', 'N/A')}")
                print(f"📋 Status: {routing_info.get('status', 'N/A')}")
            
            # Check for context info to see which document was actually selected
            context_info = result.get('context_info')
            if context_info and isinstance(context_info, dict):
                source_docs = context_info.get('source_documents', [])
                
                print(f"\n📄 ACTUAL DOCUMENT SELECTED:")
                print("-" * 30)
                
                if source_docs:
                    for i, doc in enumerate(source_docs[:3], 1):
                        if isinstance(doc, dict):
                            source = doc.get('source', 'unknown')
                        else:
                            source = str(doc)
                        
                        print(f"{i}. {source}")
                        
                        # Extract document ID from path
                        if 'DOC_' in source:
                            import re
                            doc_match = re.search(r'(DOC_\d+)', source)
                            if doc_match:
                                doc_id = doc_match.group(1)
                                print(f"   📍 Document ID: {doc_id}")
                                
                                if doc_id == 'DOC_031':
                                    print("   ❌ WRONG: Selected lưu động document!")
                                elif doc_id == 'DOC_011':
                                    print("   ✅ CORRECT: Selected normal marriage document!")
                else:
                    print("   ⚠️  No source documents found")
            
            # Check if answer contains "lưu động"
            answer = result.get('answer', '')
            if answer and 'lưu động' in answer.lower():
                print(f"\n❌ CONFIRMED WRONG ROUTING: Answer mentions 'lưu động'")
                print(f"📝 Answer preview: {answer[:200]}...")
            elif answer:
                print(f"\n📝 Answer preview: {answer[:200]}...")
            
            print(f"\n📋 Full response keys: {list(result.keys())}")
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Request Error: {e}")

if __name__ == "__main__":
    test_live_router()
