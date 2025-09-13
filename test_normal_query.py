#!/usr/bin/env python3
import requests
import json

# Test normal query to see what collection is selected
url = 'http://localhost:8000/api/v1/query'
data = {
    'query': 'ket hon bao nhieu tuoi',
    'session_id': 'test-normal'
}

print('🔍 NORMAL QUERY (no force routing):')
print(json.dumps(data, indent=2, ensure_ascii=False))

response = requests.post(url, json=data)
print(f'\n📋 RESPONSE STATUS: {response.status_code}')
result = response.json()

print(f'📋 RESPONSE TYPE: {result.get("type")}')
print(f'📋 ROUTING INFO: {result.get("routing_info")}')

if result.get("routing_info"):
    routing = result["routing_info"]
    print(f'  - Collection: {routing.get("collection")}')
    print(f'  - Document: {routing.get("document_title")}')
    print(f'  - Score: {routing.get("score")}')