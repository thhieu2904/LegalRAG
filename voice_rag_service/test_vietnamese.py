#!/usr/bin/env python3
"""Quick test Vietnamese TTS synthesis"""
import requests
import json

url = "http://localhost:8003/api/voice/synthesize"
payload = {
    "text": "Xin chào, đây là hệ thống tư vấn pháp luật bằng tiếng Việt.",
    "speed": 1.0
}

print("Testing Vietnamese TTS...")
print(f"Text: {payload['text']}")

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print(f"Size: {len(response.content)} bytes")

if response.status_code == 200:
    with open("test_vietnamese_python.wav", "wb") as f:
        f.write(response.content)
    print("✅ Saved to test_vietnamese_python.wav")
else:
    print(f"❌ Error: {response.text}")
