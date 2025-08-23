#!/usr/bin/env python3
"""
Direct router test to check confidence scores
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_router_debug():
    """Test router confidence with different queries"""
    
    test_queries = [
        "thu tuc dang ky ket hon",
        "Tôi cần biết về thủ tục đăng ký kết hôn",
        "dang ky ket hon can gi",
        "thủ tục đăng ký kết hôn cần gì",
        "đăng ký kết hôn"
    ]
    
    for query in test_queries:
        print(f"\n🧪 Testing: '{query}'")
        
        response = requests.post(f"{BASE_URL}/api/v1/query", json={
            "query": query
        })
        
        if response.status_code == 200:
            data = response.json()
            response_type = data.get('type')
            
            if response_type == "answer":
                print(f"✅ ANSWER - Direct routing (high confidence)")
            elif response_type == "clarification" or response_type == "clarification_needed":
                clarification = data.get('clarification', {})
                action = clarification.get('action', 'unknown')
                confidence = clarification.get('confidence', 'unknown')
                
                if action == "select_collection":
                    print(f"❌ LOW CONFIDENCE - Select collection (confidence: {confidence})")
                elif action == "questions_in_document":
                    print(f"⚠️  MEDIUM-HIGH - Questions in document (confidence: {confidence})")
                elif action == "select_document":
                    print(f"⚠️  MEDIUM - Select document (confidence: {confidence})")
                else:
                    print(f"❓ CLARIFICATION - {action} (confidence: {confidence})")
        else:
            print(f"❌ Failed: {response.status_code}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_router_debug()
