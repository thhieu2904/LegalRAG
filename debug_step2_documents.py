#!/usr/bin/env python3
"""
Debug Step 2 - Document Selection Issue
"""

import requests
import json

BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def debug_step2():
    print("🔍 Debug Step 2 - Document Selection")
    print("=" * 50)
    
    # Step 1: Get clarification options
    response1 = requests.post(
        f"{BASE_URL}/api/v2/optimized-query",
        json={"query": "tôi muốn đăng ký"},
        headers=HEADERS,
        timeout=30
    )
    
    data1 = response1.json()
    session_id = data1["session_id"]
    options1 = data1["clarification"]["options"]
    
    print(f"Step 1 - Collections: {len(options1)}")
    for i, opt in enumerate(options1):
        print(f"  {i+1}. {opt['title']} (action: {opt['action']})")
    
    # Step 2: Select collection
    selected_option = options1[0]
    print(f"\nSelecting: {selected_option['title']}")
    
    response2 = requests.post(
        f"{BASE_URL}/api/v2/clarify",
        json={
            "session_id": session_id,
            "original_query": "tôi muốn đăng ký",
            "selected_option": selected_option
        },
        headers=HEADERS,
        timeout=30
    )
    
    data2 = response2.json()
    print(f"\nStep 2 Response:")
    print(f"  Type: {data2.get('type')}")
    print(f"  Has clarification: {bool(data2.get('clarification'))}")
    
    if data2.get('clarification'):
        clarification = data2['clarification']
        print(f"  Message: {clarification.get('message', 'No message')}")
        print(f"  Options count: {len(clarification.get('options', []))}")
        
        options2 = clarification.get('options', [])
        if options2:
            print("  Options:")
            for i, opt in enumerate(options2):
                print(f"    {i+1}. {opt.get('title', 'No title')} (action: {opt.get('action', 'No action')})")
        else:
            print("  ❌ NO OPTIONS FOUND!")
            
        # Check if we have document selection options
        doc_options = [opt for opt in options2 if opt.get("action") == "proceed_with_document"]
        manual_options = [opt for opt in options2 if opt.get("action") == "manual_input"]
        
        print(f"  Document options: {len(doc_options)}")
        print(f"  Manual input options: {len(manual_options)}")
        
    else:
        print("  ❌ NO CLARIFICATION OBJECT!")
    
    # Print full response for debugging
    print(f"\nFull Response JSON:")
    print(json.dumps(data2, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    debug_step2()
