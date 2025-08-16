#!/usr/bin/env python3
"""
CONTEXT-AWARE ROUTER TEST VIA API
Test router memory throu        if routing_info2 and routing_info2.get('is_followup'):
            print("✅ EXCELLENT: Follow-up detection worked!")
        else:
            print("❌ Follow-up detection failed")
            
    except Exception as e:API calls
"""

import requests
import json
import time

def test_context_via_api():
    """Test context-aware router via API calls"""
    
    print("=== CONTEXT-AWARE ROUTER TEST VIA API ===")
    
    base_url = "http://localhost:8000/api/v2"
    
    # Query 1: Initial question
    print("\n--- QUERY 1: Initial Question ---")
    query1 = "đăng ký kết hôn có tốn phí không"
    
    payload1 = {"query": query1}
    
    try:
        response1 = requests.post(f"{base_url}/optimized-query", json=payload1)
        result1 = response1.json()
        
        print(f"Q1: {query1}")
        print(f"Status: {response1.status_code}")
        print(f"Type: {result1.get('type')}")
        print(f"Answer: {result1.get('answer', '')[:100]}...")
        
        # Check routing info
        routing_info = result1.get('routing_info', {})
        session_id = result1.get('session_id')
        
        print(f"Session ID: {session_id}")
        print(f"Collection: {routing_info.get('target_collection')}")
        print(f"Confidence: {routing_info.get('confidence', 0):.3f}")
        
        # Wait a moment
        time.sleep(1)
        
        # Query 2: Follow-up question (should use same session)
        print("\n--- QUERY 2: Follow-Up Question ---")
        query2 = "ủa vậy khi nào thì phải đóng phí"
        
        payload2 = {"query": query2, "session_id": session_id}
        
        response2 = requests.post(f"{base_url}/optimized-query", json=payload2)
        result2 = response2.json()

        print(f"Q2: {query2}")
        print(f"Status: {response2.status_code}")
        print(f"Type: {result2.get('type')}")
        
        # Debug: Print full response
        print(f"Full Response: {result2}")
        
        if result2.get('type') == 'answer':
            print(f"Answer: {result2.get('answer', '')[:100]}...")
        elif result2.get('type') == 'clarification_needed':
            print(f"Clarification: {result2.get('clarification', {}).get('message', '')}")
        
        # Check routing info for follow-up
        routing_info2 = result2.get('routing_info')
        
        if routing_info2:
            print(f"Collection: {routing_info2.get('target_collection')}")
            print(f"Confidence: {routing_info2.get('confidence', 0):.3f}")
            print(f"Is Follow-up: {routing_info2.get('is_followup', False)}")
            print(f"Confidence Level: {routing_info2.get('confidence_level', '')}")
        else:
            print("❌ No routing_info in response")
        
        # Analysis
        print(f"\n🔍 ANALYSIS:")
        collection1 = routing_info.get('target_collection')
        collection2 = routing_info2.get('target_collection') if routing_info2 else None
        
        print(f"Collection 1: {collection1}")
        print(f"Collection 2: {collection2}")
        
        if collection1 == collection2 and collection2 is not None:
            print("✅ SUCCESS: Router maintained context!")
        else:
            print("❌ FAILED: Router lost context")
            
        if routing_info2 and routing_info2.get('is_followup'):
            print("✅ EXCELLENT: Follow-up detection worked!")
        else:
            print("❌ Follow-up detection failed")
            
    except requests.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_context_via_api()
