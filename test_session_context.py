#!/usr/bin/env python3

import requests
import json

# Test với session có routing_info từ clarification
session_id = 'test-debug-1757788451'  # Session từ test trước đã có routing_info

response = requests.post('http://localhost:8000/api/v1/query', json={
    'query': 'phí là bao nhiêu khi làm thủ tục',
    'session_id': session_id  # Không có force parameters, chỉ dựa vào session context
})

result = response.json()
print(f'Type: {result.get("type")}')
print(f'Answer: {len(result.get("answer", ""))} chars')
print(f'Time: {result.get("processing_time", 0):.3f}s')

if result.get('context_info'):
    print(f'Context: {json.dumps(result["context_info"], indent=2)}')
else:
    print('No context info')
    
if result.get('routing_info'):
    print(f'Routing: {json.dumps(result["routing_info"], indent=2)}')
else:
    print('No routing info')

print(f'\nAnswer text: "{result.get("answer", "N/A")}"')