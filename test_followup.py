#!/usr/bin/env python3
"""
Test script for follow-up detection
"""
import requests
import json
import time

def test_followup_detection():
    base_url = "http://localhost:8000/api/v1/query"
    session_id = "test_session_followup"

    # Test queries
    queries = [
        "đăng ký khai sinh cần giấy tờ gì?",
        "mình có cần phải đóng tiền gì không?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*50}")
        print(f"🧪 TEST QUERY {i}: {query}")
        print(f"{'='*50}")

        payload = {
            "query": query,
            "session_id": session_id,
            "max_context_length": 8000,
            "use_ambiguous_detection": True,
            "use_full_document_expansion": True
        }

        try:
            response = requests.post(base_url, json=payload, timeout=30)
            print(f"📡 Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"📝 Type: {result.get('type', 'unknown')}")

                if result.get('type') == 'answer':
                    print("✅ Got answer - routing successful")
                    print(f"📏 Answer length: {len(result.get('answer', ''))} chars")
                    print(f"📝 Answer: {result.get('answer', '')[:500]}...")
                    if len(result.get('answer', '')) > 500:
                        print("... (truncated)")
                else:
                    print(f"❓ Response: {result}")

            else:
                print(f"❌ Error: {response.text}")

        except Exception as e:
            print(f"💥 Exception: {e}")

        # Wait between requests
        if i < len(queries):
            print("⏳ Waiting 2 seconds...")
            time.sleep(2)

if __name__ == "__main__":
    test_followup_detection()
